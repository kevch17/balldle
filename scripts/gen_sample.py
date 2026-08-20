"""Generate the labelled PLACEHOLDER pitch set for the Balldle prototype.

Writes data/pitches.json. Run `npm run data:sample` to regenerate and rebuild.


The zone math and coordinates are real physics; the games, players and at-bat
results are invented. build_pitches.py emits this same schema from real
Statcast data.
"""
import json, math, pathlib

FT = 12.0
PLATE_HALF_IN = 8.5
BALL_R_IN = 1.45

def abs_zone(h):
    "MLB ABS challenge zone: 17in wide, top 53.5% / bottom 27% of batter height."
    return dict(left=-PLATE_HALF_IN/FT, right=PLATE_HALF_IN/FT,
                bot=0.27*h/FT, top=0.535*h/FT)

def rulebook_zone(sz_bot, sz_top):
    "Rulebook zone as Statcast frames it: plate width + ball radius, operator top/bottom."
    e = (PLATE_HALF_IN + BALL_R_IN)/FT
    return dict(left=-e, right=e, bot=sz_bot - BALL_R_IN/FT, top=sz_top + BALL_R_IN/FT)

def signed_dist_in(px, pz, z):
    "Inches from boundary; + inside, - outside."
    dx = min(px - z['left'], z['right'] - px)
    dz = min(pz - z['bot'], z['top'] - pz)
    if dx >= 0 and dz >= 0:
        return min(dx, dz)*FT
    return -math.hypot(max(0.,-dx), max(0.,-dz))*FT

# Each pitch is placed by its offset from the ABS zone edge, so borderline/clear
# is exact rather than eyeballed.  off_x/off_z are inches: + = inside that edge.
# Statcast physics per pitch type, in that library's own conventions:
#   spin_axis  degrees, 180 = pure backspin, 0 = pure topspin (values given for a RHP)
#   pfx_arm    horizontal movement in feet, POSITIVE = toward the pitcher's ARM side
#   pfx_z      vertical movement in feet vs a spinless ball, positive = rides
# A left-hander mirrors: spin_axis -> 360-axis, and pfx_x flips with arm side.
TYPE_PHYS = {
 "FF": dict(rpm=2320, axis=205, pfx_arm= 0.60, pfx_z= 1.35, slot=52),
 "SI": dict(rpm=2180, axis=232, pfx_arm= 1.40, pfx_z= 0.60, slot=42),
 "FC": dict(rpm=2480, axis=152, pfx_arm=-0.20, pfx_z= 0.60, slot=54),
 "SL": dict(rpm=2600, axis=118, pfx_arm=-1.05, pfx_z= 0.05, slot=38),
 "CU": dict(rpm=2760, axis= 42, pfx_arm=-0.65, pfx_z=-0.90, slot=61),
 "CH": dict(rpm=1800, axis=224, pfx_arm= 1.25, pfx_z= 0.45, slot=46),
}

SPECS = [
 # id  h   edge_x        off_x  edge_z        off_z  sz_top%  sz_bot%  pitch  mph   stand throws ump tier
 ("p1", 73, "center",     0.0,  "center",      0.0,  0.556,   0.262, "FF","4-Seam Fastball",96.4,"R","R","S","clear"),
 ("p2", 70, "right",    -10.5,  "center",      0.0,  0.559,   0.259, "SL","Slider",         86.1,"L","R","B","clear"),
 ("p3", 76, "left",       5.2,  "center",      0.0,  0.553,   0.264, "SI","Sinker",         94.9,"R","L","S","clear"),
 ("p4", 68, "right",     -7.1,  "bot",        -4.4,  0.561,   0.257, "CH","Changeup",       88.0,"L","L","B","clear"),
 ("p5", 74, "right",     -1.2,  "center",      0.0,  0.555,   0.263, "SL","Slider",         87.3,"R","R","S","borderline"),
 ("p6", 66, "left",       0.9,  "center",      0.0,  0.558,   0.260, "SI","Sinker",         94.2,"R","R","B","borderline"),
 ("p7", 79, "center",     0.0,  "bot",         1.3,  0.551,   0.266, "CU","Curveball",      80.6,"L","R","S","borderline"),
 ("p8", 72, "center",     0.0,  "top",        -1.1,  0.557,   0.261, "FF","4-Seam Fastball",98.1,"R","R","B","borderline"),
 ("p9", 71, "right",      0.6,  "center",      0.0,  0.554,   0.263, "FC","Cutter",         91.5,"L","L","S","borderline"),
 ("p10",75, "left",      -0.9,  "bot",         2.8,  0.556,   0.259, "CU","Curveball",      78.9,"R","L","S","borderline"),
]

CONTEXT = {
 "p1": dict(game="2019-06-14 · Athletics at Mariners", venue="T-Mobile Park", inning=3, half="Bot",
            outs=1, balls=1, strikes=1, away_score=2, home_score=0, pitch_of_ab=3,
            pitcher="R. Vandersloot", batter="C. Mireles",
            ab_result="Strikeout (swinging)",
            ab_des="Mireles goes down swinging two pitches later on a 96 mph fastball up and away."),
 "p2": dict(game="2022-08-30 · Cardinals at Reds", venue="Great American Ball Park", inning=6, half="Top",
            outs=2, balls=2, strikes=1, away_score=4, home_score=4, pitch_of_ab=4,
            pitcher="T. Falkenrath", batter="H. Oyelaran",
            ab_result="Walk",
            ab_des="Oyelaran walks on four straight sliders off the plate, loading the bases."),
 "p3": dict(game="2017-10-09 · ALDS Game 4 · Yankees at Guardians", venue="Progressive Field", inning=8, half="Bot",
            outs=0, balls=0, strikes=0, away_score=3, home_score=2, pitch_of_ab=1,
            pitcher="M. Ashbury", batter="D. Krivosheev",
            ab_result="Flyout to center field",
            ab_des="Krivosheev flies out to deep center on the next pitch; the runner holds at second."),
 "p4": dict(game="2021-05-02 · Rays at Blue Jays", venue="Rogers Centre", inning=2, half="Top",
            outs=1, balls=1, strikes=2, away_score=0, home_score=1, pitch_of_ab=5,
            pitcher="S. Delacroix", batter="B. Nakashima",
            ab_result="Single to right field",
            ab_des="Nakashima lines the next changeup into right for a single."),
 "p5": dict(game="2016-07-21 · Giants at Padres", venue="Petco Park", inning=5, half="Bot",
            outs=2, balls=3, strikes=2, away_score=1, home_score=1, pitch_of_ab=7,
            pitcher="A. Bergstrom", batter="L. Quintanilla",
            ab_result="Strikeout (called)",
            ab_des="This pitch ends it — Quintanilla is rung up looking to strand two runners."),
 "p6": dict(game="2023-09-12 · Braves at Phillies", venue="Citizens Bank Park", inning=7, half="Top",
            outs=0, balls=2, strikes=2, away_score=5, home_score=3, pitch_of_ab=6,
            pitcher="J. Okonjo", batter="R. Sandvik",
            ab_result="Double to left-center",
            ab_des="Given new life at 3-2, Sandvik doubles into the left-center gap on the next pitch."),
 "p7": dict(game="2015-04-19 · Twins at Royals", venue="Kauffman Stadium", inning=1, half="Bot",
            outs=1, balls=3, strikes=0, away_score=0, home_score=0, pitch_of_ab=4,
            pitcher="C. Petrosyan", batter="W. Abernathy",
            ab_result="Groundout to shortstop",
            ab_des="Abernathy grounds the 3-1 sinker to short two pitches later, ending the threat."),
 "p8": dict(game="2018-06-03 · Dodgers at Rockies", venue="Coors Field", inning=9, half="Bot",
            outs=2, balls=1, strikes=2, away_score=6, home_score=5, pitch_of_ab=5,
            pitcher="E. Thibodeaux", batter="M. Larrañaga",
            ab_result="Strikeout (swinging)",
            ab_des="Larrañaga chases the next fastball up for the final out of the game."),
 "p9": dict(game="2024-04-28 · Astros at Rangers", venue="Globe Life Field", inning=4, half="Top",
            outs=1, balls=0, strikes=1, away_score=1, home_score=2, pitch_of_ab=2,
            pitcher="V. Marchetti", batter="P. Osgood",
            ab_result="Home run (2-run)",
            ab_des="Osgood turns on a cutter three pitches later for a two-run homer to right."),
 "p10":dict(game="2020-09-05 · Brewers at Cubs", venue="Wrigley Field", inning=6, half="Bot",
            outs=0, balls=2, strikes=1, away_score=3, home_score=3, pitch_of_ab=4,
            pitcher="N. Halvorsen", batter="I. Braithwaite",
            ab_result="Hit by pitch",
            ab_des="Braithwaite takes the next curveball off the elbow guard; benches jaw briefly."),
}

def solve(h, edge_x, off_x, edge_z, off_z, top_pct, bot_pct):
    az = abs_zone(h)
    if edge_x == "center": px = 0.0
    elif edge_x == "right": px = az['right'] - off_x/FT
    else:                   px = az['left'] + off_x/FT
    if edge_z == "center": pz = (az['top'] + az['bot'])/2
    elif edge_z == "top":  pz = az['top'] - off_z/FT
    else:                  pz = az['bot'] + off_z/FT
    return round(px, 3), round(pz, 3)

def physics(pt, throws, jitter):
    """Statcast-shaped release and movement fields for one pitch."""
    T = TYPE_PHYS[pt]
    arm = -1 if throws == "R" else 1        # arm side in plate_x terms (catcher's view)
    slot = T["slot"] + jitter*4             # arm angle, degrees above horizontal
    ext  = round(6.4 + jitter*0.35, 2)
    return dict(
        release_pos_x = round(arm * (2.35 - slot*0.011), 2),   # higher slot, closer to centre
        release_pos_z = round(4.55 + slot*0.026, 2),
        release_pos_y = round(60.5 - ext, 2),
        release_extension = ext,
        release_spin_rate = int(T["rpm"] + jitter*70),
        spin_axis = int(T["axis"] if throws == "R" else (360 - T["axis"]) % 360),
        pfx_x = round(T["pfx_arm"] * arm + jitter*0.06, 3),
        pfx_z = round(T["pfx_z"] + jitter*0.05, 3),
        arm_angle = round(slot, 1),
    )

out = []
for n, (pid,h,ex,ox,ez,oz,tp,bp,pt,pn,mph,stand,throws,ump,tier) in enumerate(SPECS):
    px, pz = solve(h, ex, ox, ez, oz, tp, bp)
    sz_top, sz_bot = round(tp*h/FT, 3), round(bp*h/FT, 3)
    az, rz = abs_zone(h), rulebook_zone(sz_bot, sz_top)
    d_abs, d_rb = signed_dist_in(px,pz,az), signed_dist_in(px,pz,rz)
    out.append(dict(id=pid, plate_x=px, plate_z=pz, batter_height_in=h,
        sz_bot=sz_bot, sz_top=sz_top, pitch_type=pt, pitch_name=pn,
        release_speed=mph, stand=stand, p_throws=throws, ump_call=ump,
        tier=tier, sample=True,
        **physics(pt, throws, (n % 5) - 2),
        play_id=None, game_pk=None, at_bat_number=None,
        **CONTEXT[pid]))
    miss = "  <-- UMP MISSED IT" if (d_abs >= 0) != (ump == "S") else ""
    o = out[-1]
    side = "arm " if o["pfx_x"]*(-1 if throws=="R" else 1) > 0 else "glove"
    print(f"{pid:4} {tier:10} ABS={'S' if d_abs>=0 else 'B'}({d_abs:+6.2f}in) "
          f"ump={ump}  {pt} {throws}HP rel({o['release_pos_x']:+.2f},{o['release_pos_z']:.2f}) "
          f"slot {o['arm_angle']:.0f}deg  pfx_x {o['pfx_x']:+.2f} -> {side} side{miss}")

n_s = sum(1 for p,(s) in zip(out,[signed_dist_in(p['plate_x'],p['plate_z'],abs_zone(p['batter_height_in'])) for p in out]) if s>=0)
print(f"\nABS: {n_s} strikes / {len(out)-n_s} balls | "
      f"borderline {sum(1 for p in out if p['tier']=='borderline')} / clear {sum(1 for p in out if p['tier']=='clear')}")
OUT = pathlib.Path(__file__).resolve().parent.parent / "data" / "pitches.json"
OUT.parent.mkdir(exist_ok=True)
json.dump(out, open(OUT, "w"), indent=1)
print(f"wrote {OUT} ({len(out)} pitches)")
