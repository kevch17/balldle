import { launch, PAGE, shot, report } from './_harness.mjs';
const b = await launch();

// --- geometry unit tests, run against the shipped page ---------------------
const pg = await b.newPage();
await pg.goto(PAGE);
const cases = [
  ["dead centre, 72in batter",      0,      2.415,  72,  8.50, "S"],
  ["1.2in off the outside corner",  0.8083, 2.415,  72, -1.20, "B"],
  ["2in above the letters",         0,      3.3767, 72, -2.00, "B"],
  ["3-4-5 corner miss",             0.9583, 3.5433, 72, -5.00, "B"],
  ["knee-high on the black",       -0.6883, 1.6367, 72,  0.20, "S"],   // vertical is the tighter edge
  ["tall batter, same pitch",       0,      3.3767, 79,  1.75, "S"],   // 6ft7 zone reaches 3.52ft
];
const res = await pg.evaluate(cs => cs.map(([n,x,z,h,exp,c]) => {
  const d = dist(x, z, absZone(h));
  return { n, got: +d.toFixed(2), exp, call: call(d), c, ok: Math.abs(d-exp) < 0.02 && call(d) === c };
}), cases);
let bad = 0;
for (const r of res) { if (!r.ok) bad++;
  console.log(`${r.ok?'PASS':'FAIL'}  ${r.n.padEnd(30)} ${String(r.got).padStart(6)}in exp ${r.exp}  ${r.call}/${r.c}`); }
console.log(bad ? `${bad} FAILURES` : 'geometry: all pass');

// the last two cases are the point of the whole game: same pitch, different batter
console.log('\nsame 3.38ft pitch: 6ft batter ->', res[2].call, '| 6ft7 batter ->', res[5].call);

// --- mobile viewport -------------------------------------------------------
const m = await b.newPage({ viewport:{width:390,height:844}, deviceScaleFactor:2 });
await m.goto(PAGE);
await m.click('.scene');
await m.waitForSelector('button:has-text("STRIKE")', {timeout:9000});
await m.keyboard.press('b');
await m.click('button:has-text("Skip the bonus")');
await m.waitForSelector('button:has-text("Next pitch")', {timeout:9000});
await m.screenshot({ path: shot('shot_mobile.png'), fullPage:true });
const overflow = await m.evaluate(() => document.documentElement.scrollWidth > window.innerWidth+1);
console.log('mobile horizontal overflow:', overflow ? 'YES (bad)' : 'none');
await b.close();
