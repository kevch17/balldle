/** Shared setup for the browser tests: where the built page is, where shots go. */
import { chromium } from 'playwright';
import { mkdirSync, existsSync } from 'node:fs';
import { resolve } from 'node:path';

export const ROOT  = resolve(import.meta.dirname, '..');
export const BUILT = resolve(ROOT, 'dist/index.html');
export const PAGE  = 'file://' + BUILT;
export const SHOTS = resolve(ROOT, 'tests/__screens__');

if (!existsSync(BUILT))
  throw new Error('dist/index.html not found — run `npm run build` first');
mkdirSync(SHOTS, { recursive: true });

export const shot = name => resolve(SHOTS, name);

/** Chromium, using the system browser when PLAYWRIGHT_CHROMIUM points at one. */
export async function launch(){
  const exe = process.env.PLAYWRIGHT_CHROMIUM;
  return chromium.launch(exe ? { executablePath: exe } : {});
}

/** Every test prints PASS/FAIL lines; this makes the exit code match. */
export function report(name, ok){
  console.log(`${ok ? 'PASS' : 'FAIL'}  ${name}`);
  if (!ok) process.exitCode = 1;
}
