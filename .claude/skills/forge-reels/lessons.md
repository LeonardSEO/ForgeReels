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
