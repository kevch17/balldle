import { launch, PAGE, shot, report } from './_harness.mjs';
const b = await launch();
const pg = await b.newPage({ viewport:{width:900,height:900}, deviceScaleFactor:3 });
await pg.goto(PAGE);

// the hand at the end of the windup must be exactly where the flight begins
const r = await pg.evaluate(() => PITCHES.map((p,n) => {
  i = n; scene(p);
  const F = physics(p), hs = p.p_throws === "R" ? -1 : 1;
  const hand = setPitcher(1, hs, F.rel);
  return { t:p.pitch_type, thr:p.p_throws, slot:p.arm_angle,
           gap:+Math.hypot(hand.x-F.rel.x, hand.y-F.rel.y).toFixed(3),
           relZ:p.release_pos_z, y:+F.rel.y.toFixed(1) };
}));
console.log('hand at release vs where the ball starts:');
for (const x of r) console.log(`  ${x.t} ${x.thr}HP slot ${String(x.slot).padStart(4)}deg`
  + `  release ${x.relZ}ft -> y ${x.y}px   gap ${x.gap}px ${x.gap<0.5?'':'<-- JUMP'}`);
console.log(r.every(x=>x.gap<0.5) ? 'ball leaves the hand with no jump' : 'DISCONTINUITY');
const hi = r.reduce((a,x)=>x.slot>a.slot?x:a), lo = r.reduce((a,x)=>x.slot<a.slot?x:a);
console.log(`\nhighest slot ${hi.slot}deg renders at y=${hi.y}px, lowest ${lo.slot}deg at y=${lo.y}px`
  + ` -> ${(lo.y-hi.y).toFixed(1)}px of arm-slot spread on screen`);

// pitcher art through the delivery
await pg.evaluate(() => { i=0; scene(P()); });
for (const u of [0,0.35,0.7,1.0,1.3]){
  await pg.evaluate(v => setPitcher(v,-1, physics(P()).rel), u);
  await pg.waitForTimeout(50);
  await pg.locator('.scene').screenshot({ path: shot(`pu_${String(u).replace('.','_')}.png`) });
}
await b.close();
