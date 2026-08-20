import { launch, PAGE, shot, report } from './_harness.mjs';
const b = await launch();
const pg = await b.newPage({ viewport:{width:760,height:1400}, deviceScaleFactor:2 });
const errs = [];
pg.on('pageerror', e => errs.push('PAGEERROR: ' + e.message));
pg.on('console', m => { if (m.type()==='error') errs.push('CONSOLE: ' + m.text()); });
await pg.goto(PAGE);
await pg.waitForTimeout(400);
await pg.screenshot({ path: shot('shot1_ready.png'), fullPage:true });

const waitCall   = () => pg.waitForSelector('button:has-text("STRIKE")', {timeout:8000});
const waitReveal = () => pg.waitForSelector('button:has-text("Next pitch"), button:has-text("See your card")', {timeout:8000});
const grab = () => pg.evaluate(() => ({
  score:+hudScore.textContent, abs:+hudAbs.textContent, ump:+hudUmp.textContent,
  pitch:hudPitch.textContent.trim(), replays: window.replays }));

// pitch 1 (96.4 mph 4-seamer): windup, mid-flight, call, bonus
await pg.click('.scene');
await pg.waitForTimeout(430); await pg.screenshot({ path: shot('shot2_windup.png'), fullPage:true });
await pg.waitForTimeout(700); await pg.screenshot({ path: shot('shot2b_flight.png'), fullPage:true });
await waitCall();
await pg.screenshot({ path: shot('shot3_call.png'), fullPage:true });

// replay before calling must return to the call buttons and not score anything
await pg.click('button:has-text("See it again")');
await waitCall();
console.log('replay-before-call returned to the call:', JSON.stringify(await grab()));

await pg.keyboard.press('s');
await pg.click('#t_FF');
await waitReveal();
await pg.screenshot({ path: shot('shot4_reveal.png'), fullPage:true });
console.log('after p1 (STRIKE + FF):', JSON.stringify(await grab()));
await pg.click('button.ghost:has-text("Replay")');
await waitReveal();
console.log('replay-after-reveal, unchanged: ', JSON.stringify(await grab()));

// flight duration should track velocity
const times = [];
for (let n = 2; n <= 10; n++) {
  await pg.click('button:has-text("Next pitch"), button:has-text("See your card")');
  await pg.waitForTimeout(100);
  const t0 = Date.now();
  await pg.keyboard.press(' ');
  await waitCall();
  times.push(Date.now() - t0);
  await pg.keyboard.press('s');
  await pg.click('button:has-text("Skip the bonus")');
  await waitReveal();
  if (n === 5) await pg.screenshot({ path: shot('shot5_umpmiss.png'), fullPage:true });
  if (n === 7) await pg.screenshot({ path: shot('shot7_curve.png'), fullPage:true });
}
console.log('after 10 (STRIKE on all):', JSON.stringify(await grab()));
const rows = await pg.evaluate(() => PITCHES.map(p => {
  const F = physics(p);
  const side = F.pfxX * F.arm > 0 ? 'arm' : 'glove';
  return [p.pitch_name, p.p_throws, p.release_speed, F.durMs,
          +(F.pfxX*12).toFixed(1), side, F.relFtX, F.relFtZ, F.slot,
          +F.rel.x.toFixed(1), +F.rel.y.toFixed(1)];
}));
console.log('\npitch                thr   mph   ms    pfx_x      side    release ft     hand px');
for (const r of rows)
  console.log(`  ${r[0].padEnd(17)} ${r[1]}  ${String(r[2]).padStart(5)} ${String(r[3]).padStart(5)}`
    + ` ${String(r[4]).padStart(6)}"  ${r[5].padEnd(6)} (${r[6]},${r[7]}) ${String(r[8]).padStart(4)}deg`
    + `  (${r[9]},${r[10]})`);
const bad = rows.filter(r => {
  const t = r[0]; const side = r[5];
  if (/Sinker|Changeup|Fastball/.test(t)) return side !== 'arm';
  if (/Slider|Cutter|Curveball/.test(t))  return side !== 'glove';
  return false;
});
console.log(bad.length ? `WRONG BREAK SIDE: ${bad.map(r=>r[0]).join(', ')}`
  : 'break side correct for every pitch (sinker/change/fastball arm-side, slider/cutter/curve glove-side)');

await pg.click('button:has-text("See your card")');
await pg.waitForTimeout(400);
await pg.screenshot({ path: shot('shot6_summary.png'), fullPage:true });
console.log('\ncard:', await pg.evaluate(() => window._card));
console.log(errs.length ? errs.join('\n') : 'no JS errors');
await b.close();
