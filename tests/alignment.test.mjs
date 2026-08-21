import { launch, PAGE, shot, report } from './_harness.mjs';
const b = await launch();
const pg = await b.newPage({ viewport:{width:900,height:900}, deviceScaleFactor:2 });
await pg.goto(PAGE);

// show the zone against the silhouette at full brightness for the shortest and
// tallest batters in the set, and measure where the landmarks actually land
const out = await pg.evaluate(() => {
  const idx = [5, 6];                       // p6 = 66in RHB, p7 = 79in LHB
  const rows = [];
  for (const j of idx){
    const p = PITCHES[j], az = absZone(p.batter_height_in);
    const k = (p.batter_height_in/12)*PPF/1000;
    rows.push({
      h: p.batter_height_in, stand: p.stand,
      zoneTopPx: +Y(az.top).toFixed(1), zoneBotPx: +Y(az.bot).toFixed(1),
      shoulderPx: +(GY - STANCE.shoulder*k).toFixed(1),
      beltPx:     +(GY - STANCE.belt*k).toFixed(1),
      kneePx:     +(GY - STANCE.knee*k).toFixed(1),
      helmetPx:   +(GY - STANCE.helmet*k).toFixed(1),
      feetPx: GY,
    });
  }
  return rows;
});
for (const r of out){
  const mid = (r.shoulderPx + r.beltPx)/2;
  console.log(`${r.h}in ${r.stand}HB  feet ${r.feetPx}`);
  console.log(`   zone top ${r.zoneTopPx}  vs midpoint(shoulder ${r.shoulderPx}, belt ${r.beltPx}) = ${mid.toFixed(1)}`
    + `   -> off by ${Math.abs(mid-r.zoneTopPx).toFixed(1)}px`);
  console.log(`   zone bot ${r.zoneBotPx}  vs knee ${r.kneePx}`
    + `   -> off by ${Math.abs(r.kneePx-r.zoneBotPx).toFixed(1)}px`);
  console.log(`   helmet top ${r.helmetPx}`);
}

// render p6 (66in) and p7 (79in) with zones forced on, world at full brightness
for (const [j,name] of [[5,'align_66in'],[6,'align_79in']]){
  await pg.evaluate(n => { i = n; scene(P()); zones.setAttribute('opacity','1'); }, j);
  await pg.waitForTimeout(150);
  await pg.locator('.scene').screenshot({ path: shot(`${name}.png`) });
}
await b.close();
