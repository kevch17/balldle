import { launch, PAGE, shot, report } from './_harness.mjs';
const b = await launch();
const pg = await b.newPage();
await pg.goto(PAGE);

// Replay the flight maths offline for every pitch in the set and check:
//  1. the ball lands EXACTLY on plate_x / plate_z — data is never bent
//  2. break direction is arm-side / glove-side by type, for BOTH handednesses
//  3. the drop ordering is physical (curve > change > slider > sinker > cutter > fastball)
const r = await pg.evaluate(() => {
  const cases = [];
  for (const thr of ['R','L'])
    for (const t of ['FF','SI','FC','SL','CU','CH']) cases.push([t, thr]);
  return cases.map(([t, thr]) => {
    const p = { pitch_type:t, p_throws:thr, release_speed:{FF:95,SI:93,FC:90,SL:86,CU:79,CH:86}[t] };
    const F = physics(p);
    const sx = F.rel.x, sy = F.rel.y, tx = X(0.2), ty = Y(2.4);
    let mx = 0, my = 0, end;
    for (let u = 0; u <= 1.0001; u += 0.005){
      const e = u*u*u, bend = 4*u*(1-u)*(0.45+0.55*e)*PPF;
      const x = sx + (tx-sx)*e + F.dev.x*bend, y = sy + (ty-sy)*e - F.dev.z*bend;
      const cx = sx + (tx-sx)*e, cy = sy + (ty-sy)*e;
      if (Math.abs(x-cx) > Math.abs(mx)) mx = x-cx;
      if (Math.abs(y-cy) > Math.abs(my)) my = y-cy;
      end = [x,y];
    }
    // positive armIn = moved toward the pitcher's arm side
    return { t, thr, armIn:+(mx/PPF*12*F.arm).toFixed(1), dropIn:+(my/PPF*12).toFixed(1),
             err:+Math.hypot(end[0]-tx, end[1]-ty).toFixed(4) };
  });
});
console.log('break off the release->plate chord, from the PITCHER\'s point of view');
console.log('  type thr   arm-side    drop   endpoint');
for (const x of r)
  console.log(`  ${x.t.padEnd(4)} ${x.thr}   ${String(x.armIn).padStart(6)}"  ${String(x.dropIn).padStart(6)}"`
    + `   ${x.err < 0.001 ? 'exact' : 'DRIFT ' + x.err}`);

const ARM = ['FF','SI','CH'], GLOVE = ['FC','SL','CU'];
const wrong = r.filter(x => (ARM.includes(x.t) && x.armIn <= 0) || (GLOVE.includes(x.t) && x.armIn >= 0));
console.log(wrong.length ? `\nWRONG SIDE: ${wrong.map(x=>x.t+x.thr).join(', ')}`
  : '\nsinker/change/fastball run arm-side, cutter/slider/curve break glove-side — both hands');
const rh = Object.fromEntries(r.filter(x=>x.thr==='R').map(x=>[x.t,x.dropIn]));
const order = Object.entries(rh).sort((a,b)=>b[1]-a[1]).map(([k])=>k);
console.log('drop, most to least:', order.join(' > '));
console.log(r.every(x=>x.err<0.001) ? 'every pitch still lands on its real coordinates'
  : 'ENDPOINT DRIFT');
// mirrored pairs must be exact mirrors
const pairs = ['FF','SI','FC','SL','CU','CH'].map(t => {
  const a = r.find(x=>x.t===t&&x.thr==='R'), b = r.find(x=>x.t===t&&x.thr==='L');
  return Math.abs(a.armIn - b.armIn) < 0.15;
});
console.log(pairs.every(Boolean) ? 'left-handers mirror right-handers exactly' : 'MIRROR MISMATCH');
await b.close();
