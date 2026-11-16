# Lessons (newest first)

Your own lessons go here, one dated entry per video. `lessons-learned.md` holds the distilled rules this skill
shipped with; this file is for what YOUR videos teach. Entries here override older text in the references.

Format for each entry:

```
## YYYY-MM-DD · <project / video title>
- What worked, with numbers (render times, LUFS, frame counts).
- What failed and why, and the rule it gives.
- What the user changed or rejected (their words, quoted).
- Tool quirks (versions, broken commands, workarounds).
- The new quality baseline the next video must beat.
```

When a lesson appears twice, promote it into the right reference file (or a script) and say so here ("promoted").

## 2026-11-16 · Brand logos from the web (`logo.py` + `logo` component, no new video)
- The user: when a video is about "Instagram vs Facebook" it must fetch the real logos and use them. Built
  `scripts/logo.py` (Simple Icons -> Wikimedia Commons -> web search by hand) and the `logo` component (app-icon
  tile, logo inlined as a data URI by visual_plan.py, so nothing loads at render time).
- Tested: Instagram, Facebook, Hugging Face from Simple Icons; LinkedIn and Microsoft from Commons. The first
  Commons rule took "Microsoft Office logos" for Microsoft: now the title closest to "<brand> logo" wins, and the
  script says to look at a Commons file before using it.
- Simple Icons files are one colour (Instagram is a flat pink mark, not the gradient). For the full-colour mark,
  take the file from the brand's own press page.
- Logos live in `art/logos/` of the video, never in the shared examples: they are other companies' trademarks.

## 2026-11-16 · Scene library rebuilt around drawn objects (17 reference reels studied, no new video)
- Studied all 17 reference reels for WHAT they draw: every one draws its topic's own objects (an earbud cut open,
  lockers, a key ring, a wafer), uses dot crowds for anything there is a lot of (agents, requests, air), waves,
  maps, gauges, calendars and real UI cards. Our use count told the same story from the other side: `text` 32x,
  `nodes` 10x, `stack` and `image` 0x. We made diagrams with text; they draw things.
- Added: `svg` (a drawn SVG file per topic, its `<g id>` groups animate: the main way to draw a topic's objects),
  `swarm`, `wave`, `space`, `map` (live: redrawn every frame from t), `hud` (pinned to the screen; `pinned: true`
  works on any component), `gauge`, `waffle`, `code`, `social`, `hand`, `calendar`, `cutaway`.
- Changed: `phone` lost its old red-circle `finger`/`field` parts (use the `finger` component), got side buttons;
  `chip` glows; `text` takes `serif: true`. Removed: `stack` (never used; `cutaway` replaces it) and `lens` (the
  Liquid Glass reel now loads the same drawing as `assets/lens.svg`).
- Examples: `touchscreen` is now the macro version; new `kit-gallery` shows every new component on its word and is
  the regression test for them.
- HyperFrames rejects `querySelector` with a template literal (its bundler's CSS parser crashes) and any font
  family without a @font-face it can resolve ("Iowan Old Style"): look parts up in `els[...]`, and use a Google
  font it fetches itself (EB Garamond for the serif).
- Honest limits: `hand` is simple (four fingers as capsules), `map` is a coarse hand-made land mask (fine as a dot
  grid, not for borders), the migrated lens was checked by plan + semantic sync, not by a new render.
- Topic list for the next videos (20, ranked) is in `docs/topics-2026-11.md`.

## 2026-11-16 · Touchscreen macro remake (test of the macro illustration kit), 24 s
- The user: "compared with the KeyFrames touchscreen video ours is really mediocre in illustrations". Side by side,
  the gap was scale, light and depth: our phone diagram filled ~15 % of the frame, flat lines, no finger; theirs
  is a lit close-up per key word. Measured with the new `fill_check.py`: ours 0.14, theirs 0.56.
- Built the macro kit: `finger` (skin as a lit cylinder, nail gloss, creases, rim light, free charges, contact
  glow), `section` (magnified cross-section: cover glass, glowing electrodes and fringe field, RGB pixel row, charge
  meters that drain near the touch, "not to scale"), `mesh` (sensor grid in perspective with a light per crossing,
  a scan light that walks the rows, a ring on the touched crossing), plus particle parallax by depth.
- First pass still scored 0.16: dark surfaces on a dark stage count (and read) as empty, and the camera framed
  each component whole. Fixes: lighter panels and a soft light pool behind the cross-section, `zoom` 1.35-1.7 with
  `pad: 0` per focus, and the cross-section placed right under the phone ("Under the glass" = a short move). Result
  0.48 median, pace 0 still frames in the first 2 s (a push-in from frame 0, offset -0.17 on the first word),
  semantic sync pass, master -14.1 LUFS. Draft only (VO, no score): a visual test.
- New baseline for illustrated explainers: the subject itself on screen, lit, filling the frame; fill >= 0.30.
  Next: a hand holding the phone, blur dissolves between close-ups, and the same kit for other hardware topics.

## 2026-11-16 · Git at AI scale (Anthropic Scion vs OpenAI Pando), 66 s explainer
- Facts: the Anthropic page was read with web tools; OpenAI's page sits behind a Cloudflare bot check (403 for
  fetch, the browser pane stuck on "Just a moment..."). We do not pass bot checks: the user pasted the text. Two
  corrections to the user's summary went into facts.md and the reel: Anthropic does not credit Claude Code for the
  growth (the reel says "agents"), and OpenAI's -80% is the MEDIAN push, not the average.
- Learned from references (first reel under the new gate): theme flip on the turn words ("But OpenAI", "So, is Git
  finished?"), A/B as two diagrams built from the same parts (agents -> middle -> backend; only the middle differs),
  number as an event (bar chart + odometer), limits line before a CTA that asks about the viewer. The A/B wide shot
  at 59 s is the strongest frame of the reel (used as cover).
- New runtime: `theme` action on object `stage` (FR.themeAt, colour-mix of the two palettes, 0.45 s); explainer_cues
  maps it to a "hit" that wins its word, so score.py rests the drums before each turn. `nodes` takes `scale`.
- Respellings break vo_check: it compares the ASR against the RESPELLED text ("Sy-on" vs heard "Sion", "Open A.I."
  vs "OpenAI"). Kokoro said Scion, OpenAI and monorepo right without say.json; try without respellings first.
- Draft 1 eye check (all gates passed): document cards at 450 px wide read at ~25 px on screen in the hook, and a
  860 px quote card too. Fixed with big text components in the hook and a 560 px card for the quote (41 px lines).
  Rule: text inside a component is fixed in world px, so its width decides the on-screen size.
- Counters and big numbers slid under the headline captions while the camera left them: hide them 0.15 s before the
  move (`hide` with a negative offset) on "But" and "So,".
- Anchor only the turn words: 5 anchors (including a repeated "Anthropic") fitted 129 bpm with 108 ms off; the 3
  turns alone fitted 91.25 bpm within 8 ms.
- Numbers: 66.0 s VO at speed 1.08 (176 words), 2013 frames rendered in 46 s (2 workers), 44 SFX cues, voice gate
  median 18.3 dB / p5 5.8 dB, qc_reel pass (-14 LUFS), pace 0 still frames, final-mix read-back WER 0.023
  (Scion heard as "cyan").
- New baseline: an argument with a turn shown by the whole frame, both answers comparable in one wide shot, an
  honest limits line. Next reel: try the screen-pinned progress HUD or preview-blurred captions (not built yet).

## 2026-11-15 · Learning from references (method, no video)
- The user: "het moet beter leren van de reference video's (Leren, niet kopiëren (wees uniek))". Before this, the
  briefs named a benchmark in one line and nothing checked it. Now: `scripts/study_reference.py` studies each
  reference the same way, `references/reference-study.md` is the method, and `build_explainer.py` refuses to build a
  reel whose brief.md lacks a "Learned from references" table (3+ techniques, source reel + time, OUR version).
- Three new style references in `references/styles/` (local): a paper-white isometric line-art explainer (145 s, one
  persistent world, progress HUD) and two dark/light "Day 01" repo reels (no hard cuts, blur dissolves, preview
  captions, serif italic emphasis). The measurement that matters: their dark <-> light flips sit exactly on the
  turns of the argument (series slot, problem, benefit): a re-hook that means something.

## 2026-11-15 · ForgeReels promo (EN, 37.8 s, visual explainer + real output footage)
- Hook: meta before/after ("Claude Code made this entire video") over real ForgeReels output; three hook options
  and three structures written in `brief.md` before the script (chosen by the rubric, not skipped this time).
- Camera moves now take `"ease"` (`core.js`, test first): the first move uses `"ease": "out"` pulled to t = 0.
  pace_check: 0 still frames in the first 2 s (last reel 17, then 5 after the checker fix); no still stretch.
- Voice: Kokoro af_heart, 9 lines, 36.7 s. Kokoro says "per-minute fees" as "permanent fees" even respelled
  "per minute": vo_check caught it (WER 0.29); rewritten as "no paying by the minute" (same README claim).
- Three drafts. Draft 1 failed the eye check, not the gates (sync pass, check clean): footage of a finished reel
  inside a phone bezel = phone-in-phone with its own captions under ours; 900-wide agent/terminal/rail = text far too
  small; sections 200-400 px apart slid under the captions. Rules: crop reused reel footage to its picture area
  (no captions, no bezel) and tight to the UI; diagram components 560-700 wide so the camera zooms to about 1.3x
  (terminal text then reads at about 38 px); keep 600+ px between sections in the world.
- Reused footage: the source camera keeps moving, so check the first, middle and last frame of the crop (only the
  first 3 s of the Liquid Glass reel stayed on the UI).
- Document highlight was a half-height band that read as a STRIKETHROUGH at phone size (a checklist that looked
  crossed out). Now a full-height highlighter (styles.css).
- Hooks worked: the Stop hook flagged every draft in output/. Cause: build_explainer.py wrote each draft master
  there. Drafts now stay in out/ (`<name>-master.mp4`); `--deliver` writes output/.
- Sound: explainer_cues 30 cues, 127.5 bpm with 2 anchors on the beat (0 ms), score calm in D (20 bars, 8 hits),
  beatmix 30 SFX, voice gate median 16.3 dB / p5 7.0 dB; final -14.1 LUFS, -1.4 dBTP, final-mix read-back WER 0.
- Quality baseline now: QC pass, 56 events on their words, 0 still frames in the hook, every text at least 30 px on
  screen, nothing under the captions. Next reel: fill the empty terminal before its first line (10-13 s here sat
  on a bare prompt) and give the loop diagram bigger nodes.

## 2026-11-15 · Liquid Glass for React, finished (score, SFX, delivery)
- Sound for an explainer: `scripts/pipeline/explainer_cues.py` turns the visual events into cues.json (camera move =
  whoosh.short, new component = land.light, strike = hit, type = text, highlight/pulse/count = tick, 0.3 s minimum
  gap; anchors = the hook word, the turn, the CTA word). beatgrid fitted 110 bpm with the 3 anchors within 21 ms;
  score.py --style calm --key D (22 bars, 8 hits); beatmix placed 26 SFX, voice gate median 18 dB / p5 6.6 dB;
  final -14.0 LUFS, -1.4 dBTP, final-mix read-back WER 0.
- Bug fixed (test first): beatmix's speech mask dropped the last partial 50 ms window and crashed whenever the voice
  length was not a whole number of windows.
- pace_check counted a smooth camera push over dark, soft gradients as "still" (under 14 grey levels per frame):
  "17 still frames" in a hook that visibly pushes. FIXED (test first, `tests/test_pace_check.py`): a frame now also
  counts as motion when it differs from the frame 0.25 s back (`--window`). Same reel: 17 -> 5, and those 5
  (frames 1-5) really are near-identical to frame 0 (under 20 changed pixels): the push eases in for 0.17 s. Next
  reel: the camera moves from frame 1 at full speed.
- Hook fixes that worked: capture loops at constant speed from frame 0 (no ease-in), open wide and push into the
  subject on the first word, strike the claim the voice contradicts ("blur in a box" on "Real glass"), scan-reveal
  the technical diagram.
- Delivery set in output/: mp4, cover png, caption txt (CC BY credit line included), music credits.

## 2026-11-15 · Liquid Glass for React (first real reel in the workspace, EN, 46 s, visual explainer)
- Route: visual explainer + REAL product footage. The live demo was captured frame by frame with puppeteer-core and
  HyperFrames' own headless Chrome (`reels/<..>/capture.mjs`: drag a glass lens, scroll the components page), then
  played inside the world as a `frames` component (phone bezel) with a `play` event on its word. Real refraction in
  motion beats any redrawn imitation; capture the user's own product whenever it has a demo.
- Voice: Kokoro af_heart, 10 lines, 45.2 s, `vo_check` 10/10 with Parakeet. Script uses US spelling ("center") to
  match the US voice and the captions.
- Bugs found by this reel (all fixed, each with a test): image sequences are numbered from 0001 by ffmpeg, the
  runtime asked for 0000 (`FR.frameSrc`, scene key `first`); `semantic_sync --frames` crashed on an event running
  past the video end (grabs now clamp); the draft was -19.4 LUFS (delivery to `output/` is now mastered to -14 LUFS,
  -1.5 dBTP).
- New gate: `build_explainer.py` runs `npx hyperframes check` after assembling and stops on lint or runtime errors.
  The missing-frame 404s were invisible to semantic_sync and only `check` saw them.
- Still weak (next reel must beat it): `pace_check` flags 30 still frames in the first 2 s (the capture opens on a
  loading page: start captures already moving); diagram text (document, terminal, nodes) reads small; the lower
  third of the frame is mostly empty. Quality baseline: QC pass, 41 events on their words, no still stretch > 1 s.
