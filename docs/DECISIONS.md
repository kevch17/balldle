# Balldle prototype — what got built, and what it decides

A single-file, throwaway prototype of the "recommended first build step" in the spec:
one 10-pitch round, no backend, no daily rotation, no accounts. The point is to find
out whether *see pitch → call it → find out* is fun before building any of the
pipeline machinery.

Open `balldle.html` in a browser. Nothing to install, works offline.

## Is anything randomized?

No. All ten pitches — type, velocity, location, umpire call, context — are fixed
values in the `PITCHES` array, identical on every load. The only randomness in the
whole system lives in `build_pitches.py`'s sampling, and it is seeded (by date, by
default) precisely so every player gets the same puzzle, Wordle-style.

## v0.4 — Real infrastructure: GitHub, daily cron, a dev button

**The repo is finally on GitHub.** Everything up to v0.3.1 existed only as a local
checkout. Getting it pushed surfaced a real constraint worth recording: file-bridge
tools that mount a machine's folders read/write can still be unable to *delete*
anything on that mount, and git's own commit process needs to delete its own lock
files as a normal part of committing — not just recover from a crash. When that
delete is blocked, git fails with a "stale lock" error that looks identical to an
actual orphaned lock from a crashed process, which is a trap: retrying the delete
through the same restricted channel never works, no matter how many times the
message says to. The fix was running the remaining git commands in a real local
terminal instead of through the bridge, where delete is unrestricted.

**The daily workflow is switched on**, not just present. `daily-puzzle.yml.example`
existed since v0.3.1 but was inert. It's now `daily-puzzle.yml`, live on a
`09:15 UTC` cron and on `workflow_dispatch`. First live run against Baseball Savant
is still unverified — see "the data is fake" below, which is still true.

**Dev mode exists because there was no fast loop for real data.** `build_pitches.py`
works but pulling live Statcast, rebuilding, and refreshing by hand is slow enough
that it discourages actually doing it. `scripts/dev-server.mjs` (`npm run dev`) is a
small local-only Node server that does the pull/build/reload on a button click inside
the page itself, gated to `localhost`/`?dev` so it's invisible on the deployed static
site — there's no server on GitHub Pages to answer `/api/new-game`, so the button
just doesn't render there. It picks a random ~4-day window from within a real
regular season (Apr 1 – Sep 20, a past year) rather than any random calendar date,
specifically to avoid landing in the off-season and pulling zero games. Each click is
a real network round-trip to Baseball Savant, so it's minutes-slow by design, not
instant — that's the actual cost of "real," not a bug to fix.

## v0.3 — Statcast wiring, and a pitcher you can read

**The glove is now obvious.** The pitcher wears a grey road uniform instead of being
a black silhouette, so the limbs separate: brown mitt on the off hand, bare skin-toned
throwing hand, cap with the bill facing you. The ball sits in the throwing hand from
the first frame of the windup.

**Arm side vs glove side, settled and tested.** A right-hander faces home, so his
throwing hand is on the third-base side — negative `plate_x`, screen-LEFT to us.
Sinkers, changeups and four-seamers run arm-side; sliders, cutters and curveballs
break glove-side. From where the batter stands every one of those reads the other
way, which is the confusing part, so the direction is asserted in the test suite for
all six pitch types and both handednesses, and the reveal card labels its movement
readout "pitcher's POV" so it can never be ambiguous.

**The ball leaves the hand when it leaves the hand.** The windup carries the ball in
the throwing hand and the flight picks it up from the same coordinate — measured gap
is 0.000 px on all ten pitches, so there is no teleport. The arm easing was also
changed: it used to decelerate into release (smoothstep), which read as a placement
rather than a throw. It now lags through the first half and whips, still accelerating
at the moment the ball goes.

**Statcast physics fields are initialized end to end.** Schema, sample data and
pipeline all carry them, and the renderer reads each one if present and quietly
defaults if not, so partial data still draws:

| field | status |
|---|---|
| `release_pos_x` / `release_pos_z` | **live** — places the hand on screen; the arm solves to reach it, so a 69° slot and a 34° slot look different |
| `release_extension` | **live** — sets true flight distance (60.5 − extension) instead of a flat 55 ft |
| `pfx_x` / `pfx_z` | **live** — drives break; chord deviation is pfx/4 with gravity subtracted vertically |
| `release_spin_rate` | **live** — drives how fast the seams turn |
| `spin_axis` | **live** — Statcast's 180 = pure backspin, folded into a visual tilt plus a tumble direction |
| `arm_angle` | read and displayed; the arm slot itself comes from release position |
| `vx0 vy0 vz0 ax ay az` | carried, not yet drawn — these are the real 9-parameter trajectory, and swapping the prototype's parabola for them is the next fidelity step |

Two constants near the top of the script are the knobs: `BREAK_GAIN` (2.2) exaggerates
movement for visibility — set it to 1.0 for true scale — and `SPIN_VIS` (0.13) is the
share of real rpm actually drawn, because 2,300 rpm across a one-second animation is a
blur, not a spin.

**Linking to Statcast.** Two levels, both wired:

- *Game level* — every real pitch carries `game_pk`, and the reveal links to
  `baseballsavant.mlb.com/gamefeed?gamePk=…`. This works the moment you run the
  pipeline; no extra step.
- *Pitch level* — `baseballsavant.mlb.com/sporty-videos?playId=<uuid>` plays the video
  of one specific pitch. That `playId` is **not** in the Statcast CSV. It lives in
  MLB's live game feed (`statsapi.mlb.com/api/v1.1/game/<gamePk>/feed/live`), one per
  pitch event. `build_pitches.py --with-video` fetches the feed for each selected game
  and joins on `(game_pk, at_bat_number, pitch_number)`, giving each reveal a "Watch
  this exact pitch" link. The join assumes Statcast's `at_bat_number` equals the feed's
  `atBatIndex + 1`; if that ever drifts the join misses and pitches fall back to the
  game-level link rather than breaking.

Sample pitches carry `play_id: null`, and the reveal says so with the instructions
rather than showing a dead link.

## v0.2 — what changed

**The batter now matches his own strike zone.** This was the real bug, and the cause
was subtler than bad drawing. ABS's 53.5% / 27% are fractions of *standing* height,
but they describe the zone as it appears in the batter's *stance*. Draw an upright
figure and the zone lands at hip-to-knee — 13 inches too low on the body. The
silhouette is now built from stance landmarks in thousandths of standing height and
scaled to each batter's real height, pinned by two constraints:

    knee hollow 275                  == ABS bottom (270)
    midpoint(shoulder 628, belt 442) == ABS top    (535)

which is the rulebook definition, drawn. Torso length 186 is a real 200-unit torso
leaning ~22 degrees; the thigh and shin keep their true lengths and take up the slack
by bending, because that is what a crouch is. Measured on the shipped page: zone top
lands exactly on the shoulder/belt midpoint and zone bottom within 0.4 inches of the
knee, for a 5'6" batter and a 6'7" one alike. The zone visibly grows and shrinks
with the man standing in it.

**The pitcher throws.** Full delivery — leg lift, stride, arm swinging back and over,
release, follow-through that keeps going while the ball is on its way. The ball leaves
from the pitcher's actual hand position at the end of the delivery, not a hardcoded
point, so the release lines up with the arm by construction. A right-hander releases
from screen-left, because you are facing him; a lefty from screen-right.

**Seams, spinning correctly for the pitch.** The spin is split into the two components
you can actually see from behind the plate: *tumble* (axis across the flight path, so
the seams foreshorten as the ball rolls over) and *gyro* (axis pointing at you, so
they turn in the picture plane). A four-seamer is nearly pure backspin tumble; a
curveball is the same but reversed; a slider is mostly gyro and gets the **red dot** —
the stationary spot on the spin axis that hitters hunt for. Axis tilt mirrors with
handedness. The seams are drawn by transforming the control points rather than the
group, because squashing the group squashes the stroke with it.

**Break, and speed that matches the pitch.** Flight time is derived from the pitch's
own velocity — 55 feet of travel at that speed, stretched to something watchable. A
98 mph fastball arrives in 994 ms, a 78.9 mph curveball in 1235 ms. Each type also
bends off the release-to-plate chord by a type-appropriate amount: measured on the
shipped page, the curveball drops 4.6x the fastball, the sinker runs 5.6" arm-side,
the slider sweeps 6.2" the other way. The deviation is parabolic and zero at both
ends, so **every pitch still lands exactly on its real plate_x / plate_z** — verified
to 0.000 px. The path is dressed up; the data is not.

**Replay before you call.** "See it again" (or `R`) during the call phase re-runs the
whole delivery and returns you to the buttons, and the count of looks used is shown
next to the prompt so you can see whether you are leaning on it. The post-reveal
Replay is still there. Neither one re-scores. Worth deciding later whether a real
umpire gets a second look — right now you do.

## The three things you asked for

**Catcher's mitt.** In. The catcher sets a target in the middle of the zone before
the pitch, holds it while the ball is in the air, adjusts late to where the pitch is
actually going, and then *tugs it back toward the middle of the zone* on the catch —
about 30% of the way, with a wrist rotation. That last bit is framing, and it is the
argument for keeping the glove: on a borderline pitch you watch the catcher try to
steal it, and you have to decide whether to buy it. Some of that pull is still visible
at the reveal, faded behind the ball, so you can see how far he moved it.

**Post-pitch context.** Every reveal names the game, the ballpark, the inning, the
outs, the score, both players, the count, which pitch of the at-bat it was, the pitch
type and the velocity — and then how the at-bat actually ended, in a sentence.

**Your call vs. ABS vs. the umpire.** Three rows, every pitch. The ABS call is
*computed live* from the coordinates and the batter's height; it is not stored in the
data. The umpire's call is the historical fact. When they split, the reveal says so.

## Decisions I had to make to get it running

- **Both zones are drawn, and they are different shapes.** Solid cyan is the ABS
  challenge zone as MLB defined it for 2026: 17″ wide, top at 53.5% and bottom at 27%
  of that batter's height, read at a single plane in the middle of the plate. Dashed
  grey is the rulebook zone the human is actually working — plate width *plus a ball's
  radius*, with Statcast's stance-based top and bottom. The dashed box is visibly
  bigger in every direction. That gap is why ABS shrinks the zone, and it is the most
  interesting thing on the reveal screen.
- **No zone box before the call.** Judging it unaided is the game. The batter gives you
  the vertical reference and the plate gives you the horizontal one, which is exactly
  what the umpire gets.
- **Scoring keeps both answers.** +10 for matching ABS, +5 for matching the umpire,
  +5 for the pitch type. You end with two separate tallies and a line telling you, on
  the pitches where the human and the machine split, which side you took. That's the
  open question in your spec answered with data instead of a coin flip — play it a few
  times and you'll know which one should be "correct."
- **Share card is spoiler-free.** 🟩 both agreed with you, 🟨 one did, ⬛ neither.
  No pitch specifics, no locations.
- **Difficulty:** the shipped set is the medium mix — 6 borderline, 4 clear. Borderline
  is defined as within 1.5″ of the ABS boundary, clear as 4″ or more. The mushy middle
  is thrown away rather than assigned.

## The data is fake, and that is the one real gap

Baseball Savant and the MLB StatsAPI are both blocked from the sandbox this was built
in, so the ten pitches ship as **placeholder data**: the coordinates are physically
realistic and the zone math on them is real, but the games, players and at-bat results
are invented. Every reveal card is stamped accordingly and there's a banner on the
scene.

`build_pitches.py` is the real thing, and it writes the exact schema the prototype
reads:

    pip install pybaseball pandas
    pip install MLB-StatsAPI          # optional, for exact batter heights
    python build_pitches.py --start 2024-05-01 --end 2024-05-07 --tier medium

Then paste the resulting `pitches.json` into the `PITCHES` constant near the top of
the `<script>` block in `balldle.html`, and drop the `SAMPLE DATA` banner.

It filters to `description in (called_strike, ball)`, drops rows with tracking gaps in
`sz_top`/`sz_bot`, classifies each pitch by distance from the ABS boundary, takes the
tier's borderline/clear mix with one pitch per game so the ten come from ten different
nights, and joins each at-bat's outcome from the `events`/`des` on that at-bat's final
pitch. Seed it with the date and every player gets the same puzzle.

It runs against the live API, which I could not reach — the logic is tested against a
synthetic Statcast frame (`test_pipeline.py`), so expect to fix a column name or two
the first time you run it for real.

## Verified

- Zone geometry unit-tested against hand-computed cases, including the one that
  matters: a pitch at 3.38 ft is a **ball** to a 6'0" batter and a **strike** to a
  6'7" one.
- Full 10-pitch playthrough in a headless browser: scoring, tallies, share card and
  both replay paths check out, no JS errors, no horizontal overflow on a 390px phone.
- Zone-to-silhouette alignment measured directly off the rendered page for the
  shortest and tallest batters in the set.
- Every pitch type's trajectory replayed offline: break differs by type in the right
  direction, and all six land on their exact coordinates.
- Release point matches the throwing hand for both handednesses.
- Break direction asserted for all six pitch types x both handednesses; left-handers
  mirror right-handers exactly; drop ordering comes out curve > slider > change >
  cutter > sinker > fastball.
- Ball position at the end of the windup equals the flight's start, to 0.000 px, on
  every pitch.
- Every physics field round-trips: pipeline output schema is asserted against what
  the prototype reads.

## If it's fun, the next three things

1. Real data through `build_pitches.py`, and tune the 1.5″ borderline threshold by
   eye against what actually feels hard.
2. Move the answer key server-side — right now `PITCHES` is in the page, so
   view-source spoils it. The spec already calls for the once-daily static JSON write.
3. Sound. A called strike with no umpire voice is missing most of its personality,
   and it's the cheapest thing on the whole list.
