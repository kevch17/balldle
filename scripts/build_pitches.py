#!/usr/bin/env python3
"""
build_pitches.py — turn real Statcast data into a Balldle puzzle file.

    pip install pybaseball pandas
    python build_pitches.py --start 2024-05-01 --end 2024-05-07 --tier medium

Writes pitches.json in the schema balldle.html expects, then paste it into the
PITCHES constant in the HTML (or serve it and fetch it).

Only pitches the batter took and the umpire ruled on are eligible
(description == called_strike | ball). 2015+ only — that is where Statcast's
tracking begins.

Optional, for exact ABS zones:  pip install MLB-StatsAPI
Without it, batter height is estimated from the Statcast zone, which is close
but not exact.

--with-video attaches a per-pitch play_id so each reveal can link straight to the
video of that pitch on Baseball Savant. play_id is not in the Statcast CSV, so it
comes from MLB's live game feed and is joined on (game_pk, at_bat_number,
pitch_number). Needs `requests` and network access to statsapi.mlb.com.
"""
import argparse, json, math, random, sys

FT = 12.0
PLATE_HALF_IN = 8.5      # home plate half-width
BALL_R_IN = 1.45         # baseball radius

# how far from the ABS boundary counts as what, in inches
BORDERLINE_MAX = 1.5
CLEAR_MIN = 4.0

# borderline / clear mix per difficulty, straight from the spec
TIERS = {"easy": (4, 6), "medium": (6, 4), "hard": (8, 2)}

PARKS = {
    "ARI":"Chase Field","ATL":"Truist Park","BAL":"Oriole Park at Camden Yards",
    "BOS":"Fenway Park","CHC":"Wrigley Field","CWS":"Guaranteed Rate Field",
    "CIN":"Great American Ball Park","CLE":"Progressive Field","COL":"Coors Field",
    "DET":"Comerica Park","HOU":"Minute Maid Park","KC":"Kauffman Stadium",
    "LAA":"Angel Stadium","LAD":"Dodger Stadium","MIA":"loanDepot park",
    "MIL":"American Family Field","MIN":"Target Field","NYM":"Citi Field",
    "NYY":"Yankee Stadium","OAK":"Oakland Coliseum","PHI":"Citizens Bank Park",
    "PIT":"PNC Park","SD":"Petco Park","SF":"Oracle Park","SEA":"T-Mobile Park",
    "STL":"Busch Stadium","TB":"Tropicana Field","TEX":"Globe Life Field",
    "TOR":"Rogers Centre","WSH":"Nationals Park","AZ":"Chase Field",
}

# ---------------------------------------------------------------- geometry --

def abs_zone(height_in):
    """MLB ABS challenge zone: 17in wide, top 53.5% / bottom 27% of batter height,
    read at a single plane in the middle of the plate."""
    return dict(left=-PLATE_HALF_IN/FT, right=PLATE_HALF_IN/FT,
                bot=0.27*height_in/FT,  top=0.535*height_in/FT)

def signed_dist_in(px, pz, z):
    """Inches from the zone boundary. Positive inside, negative outside."""
    dx = min(px - z["left"], z["right"] - px)
    dz = min(pz - z["bot"],  z["top"]  - pz)
    if dx >= 0 and dz >= 0:
        return min(dx, dz) * FT
    return -math.hypot(max(0.0, -dx), max(0.0, -dz)) * FT

def classify(d):
    a = abs(d)
    if a <= BORDERLINE_MAX: return "borderline"
    if a >= CLEAR_MIN:      return "clear"
    return None                       # deliberately unused: the mushy middle

# ------------------------------------------------------------ player height --

_height_cache = {}

def batter_height_in(mlbam_id, sz_top, sz_bot):
    """Real height if MLB-StatsAPI is installed, otherwise inferred from the
    Statcast zone (operators set sz_top near 55-56% of height)."""
    if mlbam_id in _height_cache:
        return _height_cache[mlbam_id]
    h = None
    try:
        import statsapi
        raw = statsapi.get("person", {"personId": int(mlbam_id)})["people"][0]["height"]
        ft, inch = raw.replace('"', "").split("'")
        h = int(ft.strip())*12 + int(inch.strip() or 0)
    except Exception:
        h = round((sz_top * FT) / 0.556)          # fallback estimate
    _height_cache[mlbam_id] = h
    return h

def fnum(v):
    """float or None — Statcast leaves gaps, and the renderer expects null not NaN."""
    try:
        f = float(v)
        return None if f != f else round(f, 4)
    except (TypeError, ValueError):
        return None


def attach_play_ids(rows):
    """Join Savant's per-pitch video id onto each pitch.

    play_id is absent from the Statcast CSV but present in MLB's live game feed, one
    per pitch event. Statcast's at_bat_number is 1-based within the game and lines up
    with the feed's atBatIndex + 1; if a future season breaks that, the join simply
    misses and the pitches keep their game-level link.
    """
    import requests
    got = 0
    for pk in sorted({r["game_pk"] for r in rows}):
        try:
            feed = requests.get(
                f"https://statsapi.mlb.com/api/v1.1/game/{pk}/feed/live", timeout=30).json()
        except Exception as e:
            print(f"  game {pk}: feed unavailable ({e})", file=sys.stderr)
            continue
        ids = {}
        for play in feed["liveData"]["plays"]["allPlays"]:
            ab = play["about"]["atBatIndex"] + 1
            for ev in play.get("playEvents", []):
                if ev.get("isPitch") and ev.get("playId"):
                    ids[(ab, ev.get("pitchNumber"))] = ev["playId"]
        for r in rows:
            if r["game_pk"] == pk:
                r["play_id"] = ids.get((r["at_bat_number"], r["pitch_of_ab"]))
                got += bool(r["play_id"])
    print(f"attached play_id to {got}/{len(rows)} pitches", file=sys.stderr)


# ------------------------------------------------------------------- build --

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", required=True, help="YYYY-MM-DD (2015-03-01 or later)")
    ap.add_argument("--end",   required=True, help="YYYY-MM-DD")
    ap.add_argument("--tier",  default="medium", choices=list(TIERS))
    ap.add_argument("--out",   default="pitches.json")
    ap.add_argument("--seed",  type=int, default=None,
                    help="fix this per calendar day so everyone gets the same puzzle")
    ap.add_argument("--with-video", action="store_true",
                    help="attach a per-pitch play_id for Baseball Savant video links")
    a = ap.parse_args()

    if a.start < "2015-01-01":
        sys.exit("Statcast tracking starts in 2015 — pick a later start date.")

    from pybaseball import statcast, playerid_reverse_lookup
    import pandas as pd

    rng = random.Random(a.seed if a.seed is not None else a.start)

    print(f"pulling Statcast {a.start} → {a.end} …", file=sys.stderr)
    df = statcast(start_dt=a.start, end_dt=a.end)
    if df is None or df.empty:
        sys.exit("no rows came back — check the dates")

    # every at-bat's outcome lives on that at-bat's final pitch
    finals = (df.sort_values("pitch_number")
                .groupby(["game_pk", "at_bat_number"])
                .tail(1)
                .set_index(["game_pk", "at_bat_number"])[["events", "des"]])

    # only pitches the batter took and the umpire ruled on
    called = df[df["description"].isin(["called_strike", "ball"])].copy()
    called = called.dropna(subset=["plate_x", "plate_z", "sz_top", "sz_bot", "pitch_type"])
    called = called[(called["sz_top"] > 2.0) & (called["sz_top"] < 5.0) &
                    (called["sz_bot"] > 0.5) & (called["sz_bot"] < 3.0)]
    print(f"{len(called):,} called pitches after cleaning", file=sys.stderr)

    rows = []
    for r in called.to_dict("records"):
        h  = batter_height_in(r["batter"], r["sz_top"], r["sz_bot"])
        d  = signed_dist_in(r["plate_x"], r["plate_z"], abs_zone(h))
        t  = classify(d)
        if t is None:
            continue
        rows.append((r, h, d, t))

    n_border, n_clear = TIERS[a.tier]
    pool = {"borderline": [x for x in rows if x[3] == "borderline"],
            "clear":      [x for x in rows if x[3] == "clear"]}
    rng.shuffle(pool["borderline"]); rng.shuffle(pool["clear"])

    # one pitch per game, so the ten come from ten different nights
    picked, used_games = [], set()
    for tier_name, want in (("borderline", n_border), ("clear", n_clear)):
        got = 0
        for x in pool[tier_name]:
            gp = x[0]["game_pk"]
            if gp in used_games:
                continue
            used_games.add(gp); picked.append(x); got += 1
            if got == want:
                break
        if got < want:
            sys.exit(f"only found {got}/{want} {tier_name} pitches — widen the date range")
    rng.shuffle(picked)

    # batter names in one lookup
    ids = list({int(x[0]["batter"]) for x in picked})
    names = playerid_reverse_lookup(ids, key_type="mlbam")
    name_of = {int(r.key_mlbam): f"{r.name_first.title()} {r.name_last.title()}"
               for r in names.itertuples()}

    out = []
    for n, (r, h, d, tier) in enumerate(picked, 1):
        fin = finals.loc[(r["game_pk"], r["at_bat_number"])]
        date = str(r["game_date"])[:10]
        out.append(dict(
            id=f"p{n}",
            plate_x=round(float(r["plate_x"]), 3),
            plate_z=round(float(r["plate_z"]), 3),
            batter_height_in=int(h),
            sz_bot=round(float(r["sz_bot"]), 3),
            sz_top=round(float(r["sz_top"]), 3),
            pitch_type=r["pitch_type"],
            pitch_name=r.get("pitch_name") or r["pitch_type"],
            release_speed=round(float(r["release_speed"]), 1),
            stand=r["stand"], p_throws=r["p_throws"],
            ump_call="S" if r["description"] == "called_strike" else "B",
            tier=tier, sample=False,
            game=f'{date} · {r["away_team"]} at {r["home_team"]}',
            venue=PARKS.get(r["home_team"], r["home_team"]),
            inning=int(r["inning"]),
            half="Top" if r["inning_topbot"] == "Top" else "Bot",
            outs=int(r["outs_when_up"]),
            balls=int(r["balls"]), strikes=int(r["strikes"]),
            away_score=int(r["away_score"]), home_score=int(r["home_score"]),
            pitch_of_ab=int(r["pitch_number"]),
            pitcher=r["player_name"],
            batter=name_of.get(int(r["batter"]), str(r["batter"])),
            ab_result=(fin["events"] or "").replace("_", " ").title() or "—",
            ab_des=fin["des"] or "",
            game_pk=int(r["game_pk"]), at_bat_number=int(r["at_bat_number"]),

            # --- release and movement, straight off Statcast -----------------
            # The prototype reads these when present and falls back to per-type
            # defaults when they are missing, so partial data still renders.
            release_pos_x=fnum(r.get("release_pos_x")),      # ft, catcher's view
            release_pos_z=fnum(r.get("release_pos_z")),      # ft above the ground
            release_pos_y=fnum(r.get("release_pos_y")),      # ft from home at release
            release_extension=fnum(r.get("release_extension")),
            release_spin_rate=fnum(r.get("release_spin_rate")),
            spin_axis=fnum(r.get("spin_axis")),              # 180 = pure backspin
            pfx_x=fnum(r.get("pfx_x")), pfx_z=fnum(r.get("pfx_z")),   # ft of movement
            arm_angle=fnum(r.get("arm_angle")),              # 2024+ only; may be null

            # --- full trajectory, carried but not yet drawn ------------------
            # These nine define the real 9-parameter flight model. Swapping the
            # prototype's parabola for them is the next fidelity step.
            vx0=fnum(r.get("vx0")), vy0=fnum(r.get("vy0")), vz0=fnum(r.get("vz0")),
            ax=fnum(r.get("ax")),   ay=fnum(r.get("ay")),    az=fnum(r.get("az")),
            zone=fnum(r.get("zone")),
            play_id=None,
        ))

    if a.with_video:
        attach_play_ids(out)

    json.dump(out, open(a.out, "w"), indent=1)
    strikes = sum(1 for p in out
                  if signed_dist_in(p["plate_x"], p["plate_z"],
                                    abs_zone(p["batter_height_in"])) >= 0)
    misses = sum(1 for p in out
                 if (signed_dist_in(p["plate_x"], p["plate_z"],
                     abs_zone(p["batter_height_in"])) >= 0) != (p["ump_call"] == "S"))
    print(f"wrote {a.out}: {len(out)} pitches · ABS {strikes} strikes/{len(out)-strikes} balls "
          f"· {n_border} borderline/{n_clear} clear · umpire and ABS split on {misses}",
          file=sys.stderr)

if __name__ == "__main__":
    main()
