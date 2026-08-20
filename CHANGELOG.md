# Changelog

Newest first. One line per change — if an entry needs a paragraph, it belongs in
`docs/DECISIONS.md` instead.

---

## 0.3.1 — Packaged as a repo · 20 Aug 2026

**Structure**
- Game split into a template plus a build step; pitch data now lives only in `data/pitches.json` and is injected at build time instead of pasted into the HTML.
- Build checks every pitch and fails loudly rather than rendering a broken one.

**Added**
- Five browser test suites plus a pipeline test, all behind `npm test`.
- README, license, screenshots, ignore files.
- GitHub Actions: tests on every push, auto-publish to GitHub Pages on `main`.
- Optional daily workflow that pulls fresh pitches on a schedule — rename the file to switch it on.

---

## 0.3.0 — A pitcher you can read · 20 Aug 2026

**Pitcher**
- Grey uniform, cap and brown glove, so his glove hand and throwing hand are now obvious.
- The ball sits in his hand through the whole windup and leaves exactly where the hand is — it used to pop into existence at release.
- His arm speeds up through release instead of slowing into it, so it reads as a throw rather than a placement.

**Data**
- Release height, arm slot, extension, spin rate, spin axis and movement are all read from the pitch data when present, with fallbacks when absent. A high arm slot and a low one now look different on screen.
- Full trajectory numbers are carried in the data but not yet drawn — that's the next realism step.
- Reveal card gained spin rate, movement (labelled "pitcher's POV") and release height.

**Statcast links**
- Each reveal can link to the game on Baseball Savant, or to the video of that exact pitch when the pipeline is run with `--with-video`.

**Verified**
- Break direction is now locked down by tests: sinkers, changeups and fastballs run arm-side; cutters, sliders and curveballs break glove-side — for both left- and right-handers.

---

## 0.2.0 — Realism pass · 20 Aug 2026

**Fixed — the big one**
- The batter's body now lines up with his own strike zone. ABS's percentages are fractions of *standing* height but describe the zone as it looks in the batter's *crouch*, so drawing him upright put the zone 13 inches too low, down at hip-to-knee. He's now drawn in a stance and scaled to his real height — the zone runs knees to mid-torso for a 5'6" hitter and a 6'7" one alike.

**Added**
- The pitcher actually throws: leg lift, stride, arm over the top, follow-through. Right-handers release from screen-left, lefties from screen-right.
- Seams on the ball, spinning differently by pitch type — sliders get the red "dot" hitters hunt for.
- Pitch speed now comes from each pitch's own velocity: a 98 mph fastball arrives noticeably sooner than a 79 mph curve.
- Each pitch type now bends the right way and the right amount, while still landing on its exact real coordinates.
- "See it again" (or press `R`) replays a pitch before you call it, and shows how many looks you've used.

---

## 0.1.0 — First playable · 20 Aug 2026

**The game**
- Ten hand-picked pitches from the umpire's point of view: batter, plate, catcher, night-game backdrop.
- Catcher's mitt, with framing — he sets a target, adjusts late, then tugs the ball back toward the middle of the zone.
- Call each pitch ball or strike, then an optional bonus guess at the pitch type.
- Reveal shows how close it was in inches, draws both zones, and puts your call against **both** the ABS zone and the umpire's real call.
- Reveal also names the game, ballpark, inning, count, both players, and how the at-bat actually ended.
- Scoring keeps both tallies instead of picking a winner, and the summary tells you which side you took when the human and the machine disagreed.
- Spoiler-free share card.

**Behind it**
- `build_pitches.py`: pulls real Statcast pitches, sorts them borderline vs clear, and writes the file the game reads.
- Baseball Savant and MLB's API are blocked from the environment this was built in, so the shipped pitches are placeholder — real physics and real zone math, invented games and players. The game says so on screen. Running the pipeline replaces them.

---

Roadmap and open questions: `README.md`. Why each choice was made: `docs/DECISIONS.md`.
