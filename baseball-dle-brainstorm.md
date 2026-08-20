# Ball-or-Strike -dle: Open Questions and Ideas

A running brainstorm of questions worth thinking through before you commit to a direction. Organized by theme, not by priority — skim for whatever grabs you.

## Content and pitch selection

**Should pitches come from a real at-bat, or be cherry-picked individually?** There are two very different design directions here. One is to take a real, complete at-bat pitch-by-pitch (all 4, 6, 9 pitches thrown to one batter in one plate appearance) — this gives you built-in narrative and stakes ("bases loaded, full count, here's the payoff pitch") and lets a bonus round ask what happened to the at-bat as a whole. The other is to hand-curate a themed set of pitches pulled from anywhere in that day's (or history's) games — more control over difficulty and variety, but loses the story. A real at-bat is more interesting narratively but you're at the mercy of whatever variety that specific sequence happened to contain; a curated set gives you design control but takes more manual or algorithmic effort to assemble well.

**How do you keep the difficulty consistent day to day?** If pitch selection is fully random, some days will be a gimme (all pitches obviously in or out of the zone) and others brutally close. You'll probably want a rule of thumb — e.g., always include a mix of "clearly a ball," "clearly a strike," and 1–2 borderline pitches within an inch or two of the zone edge — so every day feels comparably fair and comparably hard.

**Do you show the count, inning, or score?** Real umpires are famously (if imperfectly) not supposed to be influenced by situation, but plenty of research suggests they are — for instance, calls skew toward the pitcher on 3-0 counts and toward the hitter on 0-2. Showing context makes the game feel more authentic and gives sharp players a "meta" edge, but it also invites bias into what's supposed to be a pure zone judgment. You could offer it as a toggle or a "hard mode" variant.

**Should the catcher's glove be visible?** Pitch framing (catchers subtly moving their glove to make a ball look like a strike) is one of the more fascinating real skills in baseball, and including a catcher would let your game capture that authentically. It's also a legitimate source of visual noise/misdirection that would make close calls feel more true-to-life — worth prototyping both with and without.

**Real umpire's call, or the true physical zone?** Worth deciding explicitly and stating it somewhere in the game (maybe in an "about" or "how to play" screen): are you scoring against what the actual home-plate umpire called that day, or against the rulebook-defined zone using tracked coordinates? They disagree on a real percentage of pitches. Scoring against the real ump's call is arguably more fun (you're recreating history, and "wrong" answers can be defended as "well, the real ump agreed with me") — scoring against the true zone is more "objectively fair" but means you're occasionally telling players they're wrong when a real MLB umpire made the same call.

## Audience and onboarding

**Who is this actually for?** Wordle's genius was being playable by literally anyone regardless of language or expertise. A baseball ball/strike game is inherently narrower — non-fans may not know what a strike zone even looks like or why a 2-2 slider that drops out of the zone is a legitimately hard call. Deciding whether you're building for hardcore fans (who'll appreciate nuance and pitch-type detail) or casual puzzle players (who need a lot more onboarding) will shape almost every other decision, from difficulty to how much explanation you put on screen.

**What does a first-time player need to be taught, and how fast?** If you want casual players too, you probably need a very fast, visual explanation of the strike zone (not a rules paragraph) before their first pitch — something like a one-time animated overlay showing the box, rather than an FAQ nobody reads.

**Is there an offline/non-digital pitch-recognition problem you're solving, or is this purely for entertainment?** Not a trick question — just worth being honest that this is a fun/casual product, not a training tool, which affects how forgiving vs. rigorous you want the "correct answer" logic to be.

## Feel, presentation, and tone

**Sound?** A lot of -dles are silent, but a crowd murmur, bat crack, or umpire's "STEE-RIKE" call on a correct guess could add a lot of personality for very little effort, and it reinforces the umpire fantasy your whole concept is built around.

**How do you signal "close pitch" vs "obvious pitch" in the reveal?** After a guess, showing *how* close the pitch was (not just right/wrong) adds a lot of satisfaction — "you said ball, it was a strike by half an inch" feels very different from "you said ball, it was a strike down the middle." This is a small UI detail but probably one of the most important feelings in the whole game.

**Historical vs. current-season pitches?** Pulling only from live/current games ties you to the MLB season (roughly April–October) and means you need a plan for the offseason. Pulling from any point in Statcast's history (back to 2015) gives you a much bigger pool to draw from and lets you build in themes (a specific pitcher's nastiest slider, a famous playoff at-bat) — at the cost of feeling less "live."

## Business, legal, and naming

**What happens in the MLB offseason (roughly November–March)?** If your data source is tied to live daily games, you'll run out of "today's" pitches for nearly half the year. You'll likely want your engine to pull from any past date regardless of when it's played, so the "daily" cadence is about your release schedule, not about a live game happening that day.

**Are you allowed to use Statcast data itself?** Using team names, MLB logos, or player likenesses in branding is a clear no without a license, but the underlying tracking data (pitch location, velocity, type) that's already public via Baseball Savant is used all over the fan-analytics world (blogs, apps, research). It's still worth reading MLB Advanced Media's actual terms of use for that data before you lean on it heavily, rather than assuming precedent from other sites means you're automatically fine.

**What's the actual name going to signal?** Whatever you land on, avoid anything that sounds officially affiliated with MLB or a specific team — both for legal safety and because "clearly an indie fan project" is part of the -dle genre's charm anyway (Wordle wasn't made by a dictionary company).

**Is there a monetization path, or is this just for fun/portfolio?** Doesn't need an answer now, but it's worth knowing which you're optimizing for — a pure passion project can tolerate more scope creep and slower timelines than something you eventually want to support itself (via light ads, a "supporter" tier, cosmetic themes, etc.).

## Growth, retention, and community

**What makes someone come back day two?** Wordle's answer was streaks plus the social share card. Yours could be the same, but you also have a built-in second hook baseball fans specifically love: bragging about a good "call accuracy" percentage over time, almost like a batting average for umpiring.

**How do you prevent spoilers from spreading before everyone's day has started?** Because time zones mean someone in Tokyo finishes their puzzle while someone in Toronto hasn't started, Wordle-likes generally rely on share cards being spoiler-free by design (grids without pitch details) rather than trying to prevent people from posting early — worth designing your share card the same way from day one.

**Is there a natural community aspect (Discord, subreddit, comments) worth planning for, or is this a solo-play experience only?** Not urgent, but worth a placeholder thought since sports fans especially like arguing about close calls.

## A grounding question to close on

**What's the smallest version of this that's still fun?** Given how many directions this list opens up, it's worth periodically returning to: could you playtest the core loop — pitch appears, you call it, you find out if you were right — with just five hardcoded pitches and zero backend, zero accounts, zero daily rotation? That'd tell you fast whether the fundamental judgment-call mechanic is actually fun before investing in any of the surrounding systems above.
