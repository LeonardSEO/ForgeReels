# Learning from reference reels (learn, never copy)

Every new video learns from the reels in the workspace's `references/` folder. This file is the method; the
per-folder `NOTES.md` files hold what was learned. A render is blocked until the brief says what this video takes
from them and how it makes each technique its own.

## 1. Study a new reference (once per reel, about 5 minutes)

```
~/forge-reels/venv/bin/python -I .claude/skills/forge-reels/scripts/study_reference.py references/<folder>/<reel>.mp4
```

It writes `<reel>.study/` (sheet.jpg, study.json with cuts, dark/light switches, words per second, hook words, and a
timed transcript) and a `NOTES.md` template for the folder. Then LOOK:
- read `sheet.jpg`, then 3-6 full-size frames at the moments that matter (hook, turns, the climax, the CTA);
- read the transcript as a structure: hook type, the turn words, how the CTA asks;
- for each technique write: where (time), WHY it works on a viewer, and OUR own version in our scene library.
  "Why" is the lesson; the look is theirs.

## 2. Use it in every brief (`reels/<date>-<slug>/brief.md`)

```
## Learned from references
| Technique | From (file, time) | Our own version in this video |
|---|---|---|
| Theme flip on the turn word | day01-karpathy-skills.mp4, 30.5 s | light section on "Instead", our palette, our cards |
| ... (at least 3 rows) | | |

Not taken: <what we deliberately leave out of each reference>
```

`build_explainer.py` refuses to build a project under `reels/` whose brief has fewer than three such rows with a
source file and our own version filled in. Pick techniques from at least two different references when the folder
has them, and never the same three as the previous video (lessons.md lists what the last reel used).

## 3. Learn, never copy

- Take the WHY (a re-hook that means a turn, reading ahead in captions, one world that persists), never the WHAT:
  their layout, characters or presenter, series format and name ("Day 01"), wording, CTA phrasing, brand colours.
- Combine: one technique from a reel is a copy risk; a technique applied to a different subject, in our palette,
  with our components, next to techniques from other reels, is ours.
- Numbers on screen still come from OUR facts.md, never from a reference.
- After the video, `lessons.md` records which techniques worked, so the next brief can promote or drop them.

## Techniques learned so far (details and times in the NOTES.md files)

| Technique | Reference folder | Status in ForgeReels |
|---|---|---|
| Proof hook: open on the best result, then reveal how it was made | keyframes | used (ForgeReels promo, Liquid Glass) |
| Agent panel at work, steps with file names | keyframes | `agent` component |
| Odometer counter, scan reveal, strike | keyframes | built |
| One persistent world that changes (ghosting, cards standing up in front of the model) | styles | world persists; "ghost" focus and returning objects: build when a brief picks it |
| Progress HUD pinned to the screen, ticking per chapter | styles | built: `hud` (pinned to the screen), `pinned: true` on any component |
| Theme flip (dark <-> light) on the turn word | styles | built: `theme` action (Git at AI scale) |
| Blur dissolve instead of a cut | styles | build when picked |
| Captions that show the coming words blurred; serif italic key word | styles | build when picked |
| Number as an event: ring gauge, +delta, context pill | styles | chart + counter used (Git at AI scale); `gauge` built |
| Limits line before the CTA; CTA as a question about the viewer | styles | used (Git at AI scale) |
