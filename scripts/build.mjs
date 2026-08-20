/**
 * build.mjs — inject a pitch set into the page template and write dist/index.html.
 *
 *   node scripts/build.mjs [dataFile] [outFile]
 *
 * The template keeps a single `__PITCHES__` placeholder so the answer key is never
 * hand-pasted into markup. Swap data/pitches.json for the output of
 * scripts/build_pitches.py and rebuild; nothing in the template changes.
 *
 * NOTE ON SPOILERS: this inlines the answer key into the page, which is fine for a
 * prototype and NOT fine for a daily puzzle — view-source gives it away. The fix is
 * in the README under "Before this is a real daily game".
 */
import { readFileSync, writeFileSync, mkdirSync } from 'node:fs';
import { dirname, resolve } from 'node:path';

const root = resolve(import.meta.dirname, '..');
const dataFile = resolve(root, process.argv[2] ?? 'data/pitches.json');
const outFile  = resolve(root, process.argv[3] ?? 'dist/index.html');
const tplFile  = resolve(root, 'src/index.template.html');

const tpl  = readFileSync(tplFile, 'utf8');
const data = JSON.parse(readFileSync(dataFile, 'utf8'));

if (!tpl.includes('__PITCHES__'))
  throw new Error(`${tplFile} has no __PITCHES__ placeholder`);
if (!Array.isArray(data) || data.length === 0)
  throw new Error(`${dataFile} is not a non-empty array`);

// fail loudly here rather than rendering a broken pitch in the browser
const REQUIRED = ['plate_x','plate_z','sz_top','sz_bot','batter_height_in',
                  'pitch_type','release_speed','stand','p_throws','ump_call'];
data.forEach((p, n) => {
  const missing = REQUIRED.filter(k => p[k] === undefined || p[k] === null);
  if (missing.length) throw new Error(`pitch ${n} (${p.id ?? '?'}) missing: ${missing.join(', ')}`);
  if (!'SB'.includes(p.ump_call)) throw new Error(`pitch ${n}: ump_call must be "S" or "B"`);
});

const html = tpl.replace('__PITCHES__', JSON.stringify(data, null, 1));
mkdirSync(dirname(outFile), { recursive: true });
writeFileSync(outFile, html);

const sample = data.some(p => p.sample);
console.log(`built ${outFile}`);
console.log(`  ${data.length} pitches · ${new Set(data.map(p => p.game)).size} games`
  + ` · ${data.filter(p => p.tier === 'borderline').length} borderline`
  + ` · ${sample ? 'SAMPLE data' : 'real Statcast data'}`);
