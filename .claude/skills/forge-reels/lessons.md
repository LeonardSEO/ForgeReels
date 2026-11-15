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
