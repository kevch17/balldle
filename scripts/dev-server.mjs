#!/usr/bin/env node
/**
 * dev-server.mjs — local-only dev server with a "New game (real Statcast)" button.
 *
 *   npm run dev
 *
 * Serves dist/ and exposes POST /api/new-game, which:
 *   1. picks a random ~4-day window inside a real MLB regular season (2015-today)
 *   2. runs scripts/build_pitches.py against that window — real Baseball Savant
 *      data, not the sample set
 *   3. rebuilds dist/index.html from the fresh data/pitches.json
 * The browser then reloads and you get a brand new set of 10 real pitches.
 *
 * This is local/dev only. It is NOT how the deployed game works — that's the
 * daily-puzzle.yml GitHub Actions workflow committing a static pitches.json once
 * a day. This script is never part of `npm run build` and never ships.
 *
 * Needs: `pip install -r requirements.txt` once, and a working internet
 * connection to baseballsavant.mlb.com (and statsapi.mlb.com if you add
 * --with-video below).
 */
import { createServer } from 'node:http';
import { spawn } from 'node:child_process';
import { readFileSync, existsSync } from 'node:fs';
import { resolve, extname } from 'node:path';

const root = resolve(import.meta.dirname, '..');
const PORT = process.env.PORT || 8080;

const MIME = {
  '.html': 'text/html', '.js': 'text/javascript', '.json': 'application/json',
  '.png': 'image/png', '.svg': 'image/svg+xml', '.css': 'text/css',
};

function run(cmd, args) {
  return new Promise((res, rej) => {
    const p = spawn(cmd, args, { cwd: root, stdio: 'inherit' });
    p.on('close', code => (code === 0 ? res() : rej(new Error(`${cmd} ${args.join(' ')} exited ${code}`))));
    p.on('error', rej);
  });
}

/* Statcast tracking starts 2015-03-01. Pick a random regular-season window
   (Apr 1 – Sep 20) from a past season, rather than any random calendar date, so
   we don't land in the off-season and pull zero games. */
function randomWindow() {
  const thisYear = new Date().getFullYear();
  const year = 2015 + Math.floor(Math.random() * (thisYear - 1 - 2015 + 1)); // 2015..thisYear-1
  const seasonStart = new Date(Date.UTC(year, 3, 1));   // Apr 1
  const seasonEnd = new Date(Date.UTC(year, 8, 20));    // Sep 20, leaves room for a 4-day span
  const t = seasonStart.getTime() + Math.random() * (seasonEnd.getTime() - seasonStart.getTime());
  const d0 = new Date(t);
  const d1 = new Date(t + 4 * 86400000);
  const iso = d => d.toISOString().slice(0, 10);
  return { start: iso(d0), end: iso(d1) };
}

async function newGame() {
  const { start, end } = randomWindow();
  const tiers = ['easy', 'medium', 'hard'];
  const tier = tiers[Math.floor(Math.random() * tiers.length)];
  console.log(`\n[dev] generating a new game: ${start} → ${end}, tier=${tier}`);
  await run('python3', [
    'scripts/build_pitches.py',
    '--start', start, '--end', end,
    '--tier', tier,
    '--seed', String(Date.now()),
    '--out', 'data/pitches.json',
  ]);
  await run('node', ['scripts/build.mjs']);
}

const server = createServer(async (req, res) => {
  if (req.method === 'POST' && req.url === '/api/new-game') {
    try {
      await newGame();
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ ok: true }));
    } catch (err) {
      console.error('[dev] new-game failed:', err.message);
      res.writeHead(500, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ ok: false, error: err.message }));
    }
    return;
  }

  const path = req.url === '/' ? '/index.html' : req.url;
  const distRoot = resolve(root, 'dist');
  const file = resolve(distRoot, '.' + path);
  if (!file.startsWith(distRoot) || !existsSync(file) || !file.includes('.')) {
    res.writeHead(404);
    res.end('not found');
    return;
  }
  res.writeHead(200, { 'Content-Type': MIME[extname(file)] || 'application/octet-stream' });
  res.end(readFileSync(file));
});

console.log('[dev] building once before serving …');
await run('node', ['scripts/build.mjs']);
server.listen(PORT, () => {
  console.log(`[dev] http://localhost:${PORT} — the "New game (real Statcast)" button pulls live data`);
});
