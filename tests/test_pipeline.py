"""Exercise build_pitches.py's logic against a synthetic Statcast frame
(Baseball Savant is unreachable from this sandbox, so the network call is stubbed)."""
import sys, json, random, pathlib
import pandas as pd
import pybaseball

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

rng = random.Random(7)
TEAMS = ["NYY","BOS","LAD","SF","CHC","STL","HOU","TEX","ATL","PHI"]
rows = []
for g in range(60):
    for ab in range(1, 12):
        h = rng.choice([66,70,73,76,79])
        szt, szb = round(0.556*h/12,3), round(0.262*h/12,3)
        n = rng.randint(1,6)
        for pn in range(1, n+1):
            last = pn == n
            desc = "hit_into_play" if last else rng.choice(["called_strike","ball","foul","swinging_strike"])
            rows.append(dict(
                game_pk=700000+g, at_bat_number=ab, pitch_number=pn,
                game_date=f"2024-05-{1+g%7:02d}",
                description=desc, type="X" if last else "S",
                plate_x=round(rng.gauss(0,0.75),3), plate_z=round(rng.gauss(2.4,0.7),3),
                sz_top=szt, sz_bot=szb,
                pitch_type=rng.choice(["FF","SL","CU","CH","SI","FC"]),
                pitch_name=rng.choice(["4-Seam Fastball","Slider","Curveball","Changeup","Sinker","Cutter"]),
                release_speed=round(rng.uniform(78,100),1),
                stand=rng.choice("RL"), p_throws=rng.choice("RL"),
                home_team=TEAMS[g%10], away_team=TEAMS[(g+3)%10],
                inning=rng.randint(1,9), inning_topbot=rng.choice(["Top","Bot"]),
                outs_when_up=rng.randint(0,2), balls=rng.randint(0,3), strikes=rng.randint(0,2),
                home_score=rng.randint(0,7), away_score=rng.randint(0,7),
                batter=600000+ab, pitcher=500000+g, player_name=f"Pitcher, G{g}",
                events="single" if last else None,
                des="Batter singles on a line drive to left field." if last else None,
            ))
df = pd.DataFrame(rows)
print(f"synthetic frame: {len(df):,} pitches, "
      f"{(df.description.isin(['called_strike','ball'])).sum():,} called")

pybaseball.statcast = lambda start_dt, end_dt: df
pybaseball.playerid_reverse_lookup = lambda ids, key_type=None: pd.DataFrame(
    [dict(key_mlbam=i, name_first="test", name_last=f"batter{i%97}") for i in ids])

sys.argv = ["build_pitches.py","--start","2024-05-01","--end","2024-05-07",
            "--tier","medium","--out",str(ROOT/"tests"/"__out.json"),"--seed","1"]
import build_pitches
build_pitches.main()

got = json.load(open(ROOT/"tests"/"__out.json"))
ref = json.load(open(ROOT/"data"/"pitches.json"))
gk, rk = set(got[0]), set(ref[0])
print("\nschema vs the sample file:")
print("  missing from pipeline output:", sorted(rk-gk) or "none")
print("  extra (fine, HTML ignores):  ", sorted(gk-rk) or "none")
print("  count:", len(got),
      "| borderline:", sum(1 for p in got if p['tier']=='borderline'),
      "| clear:", sum(1 for p in got if p['tier']=='clear'),
      "| distinct games:", len({p['game_pk'] for p in got}))
assert not (rk-gk), "pipeline output is missing keys the prototype reads"
assert len(got)==10 and len({p['game_pk'] for p in got})==10
d = build_pitches.signed_dist_in
z = build_pitches.abs_zone
for p in got:
    assert (build_pitches.classify(d(p['plate_x'],p['plate_z'],z(p['batter_height_in'])))
            == p['tier'])
print("\nall assertions passed")
