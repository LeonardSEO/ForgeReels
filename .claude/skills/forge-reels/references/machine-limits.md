# Machine limits: heavy video work on a small laptop

This skill was built on a 6 GB RAM laptop with an integrated GPU, and everything here was learned the hard way.
On a bigger machine the rules still prevent lost renders. Measure your own machine once and write the numbers into
`references/toolchain.md`.

## Before a heavy job
- Check free memory: `memory_pressure` or Activity Monitor. Check free disk too: a full disk fails the render.
- Close the Playwright MCP browser when you are done with it.
- One heavy job at a time: a render, an avatar track or a browser session, never two.
- Never kill a process you did not start. If memory is short, list the big users and ask the user what to close.
  Restart anything you stopped with their OK when you are done.

## Rendering
- HyperFrames: `--workers 2` (each worker is a headless Chrome, ~256 MB). `--workers 1` for very long 1080p
  walkthroughs.
- Long renders run in the FOREGROUND, chunked:
  - HyperFrames: `HF_SEGMENTED_CAPTURE=true npx hyperframes render ... --resume --keep-segments`. Segments survive
    a crash and are reused.
  - Avatar track: `scripts/pipeline/render_chunks.py --chunk N` (~12 s per chunk), then `--join`.
  - A background job was killed when memory ran low and an idle session's shells were reaped: a 45-min render was
    lost.
- If a tool call times out and moves a render to the background, do not start a second copy. Wait for it to
  finish.
- Draft first (`--quality draft`), QC every frame, then `--quality delivery` once. Compare the delivery render with
  the approved draft by PSNR: every frame should match apart from compression (e.g. >= 35 dB).

## Python
- `export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1` before
  numpy-heavy scripts when memory is tight.
- avatar_track.py loads every pose in its plan up front: give it a plan holding only the poses in its range.
- Keep decoded video frames JPEG-compressed in RAM. Six raw 10 s clips ran a 6 GB machine out of memory.
- Cache expensive per-clip analysis (eye tracking, transcripts) next to the clip.
- Build composites from CROPS, in float32, not full-canvas float64 images.

## What not to run locally on a small laptop
- Blender renders, local music models, voice cloning or lip-sync diffusion models. Use a free cloud GPU notebook
  in the user's own account if needed. Some home routers refuse the notebook's runtime domain; switching the
  machine's DNS to a public resolver fixed it.
- More than one browser tab per AI image: 13 tabs froze the machine for 20 minutes.

## Timings measured on the 6 GB laptop (for planning)
| Job | Time |
|---|---|
| 15 s kinetic-type clip with footage, `--quality looks` | ~2 min 45 s |
| 80 s one-take reel with a placed avatar, draft / delivery | ~10-11 min / ~23 min |
| Avatar track, 12 s chunk (26-pose plan) | ~4 min |
| 4.5 min 1080p30 screen walkthrough, `--workers 1` | ~23 min |
| Rhubarb lip-sync, per line | ~10 s |
| Pace check, 80 s reel | ~1 min |

## Mac M4 16 GB (MacBook Air, measured 2026-11-15, `scripts/bench.py`)
Baseline before the v2 audio changes. Peak = largest single process (see `bench.py`).
Scripts: `templates/bakeoff/en_30s.txt` and `nl_30s.txt` (8 lines each). Kokoro has no Dutch voice: the NL row
is `af_heart` with the English phonemizer, a worst case, not a usable voice.
| Job | Wall | Peak |
|---|---|---|
| `build_vo.py`, EN, 8 lines, 26 s of audio (one `npx hyperframes tts` per line) | 16.5 s | 549 MB |
| `build_vo.py`, NL, 8 lines, 32 s of audio | 15.9 s | 585 MB |
| `words.py`, EN, faster-whisper `small.en` CPU int8 (incl. first model load) | 41.2 s | 883 MB |
| `words.py`, NL, faster-whisper `small` `--language nl` | 42.6 s | 777 MB |
| `words.py` re-run with transcripts present (reused by existence, not content) | 0.1 s | 31 MB |
| Smoke test, full | 16.4 s | 546 MB |
| Draft render, 3 s 1080x1920, `--workers 2` | 5.4 s | 200 MB (node only) |

### After v2 (same M4, same scripts, 2026-11-15)
| Job | Before | After |
|---|---|---|
| `build_vo.py`, EN, 8 lines, Kokoro (in-process instead of one `npx` per line) | 16.5 s | 6.4 s / 593 MB |
| `build_vo.py` re-run, nothing changed (content cache) | 16.5 s (all regenerated) | 0.1 s |
| `build_vo.py --engine pocket`, NL, 8 lines | - | 6.1 s / 993 MB |
| `words.py --align`, EN / NL (CTC alignment, model cached) | 41-43 s (Whisper) | 13.9 / 15.5 s, ~1.9 GB |
| Line-start error of word times, NL Pocket voice | 0.24 s mean (Whisper) | 0.022 s mean (alignment) |
| `vo_check.py`, NL, `--engine parakeet` / EN Whisper | - | 4.4 s / 1.7 GB; 10.6 s / 0.9 GB |
| `build_vo.py --engine voxcpm`, NL, 3 lines (VoxCPM2 8-bit, MLX) | - | 14.3 s, worker ~3.3 GB, exits after the batch |
First runs download models once: wav2vec2 aligner ~1.2 GB per language, Parakeet ~1.2 GB, VoxCPM2 8-bit ~2.5 GB,
Pocket ~0.3 GB. Keep 10 GB free on the disk: a full disk fails the render (`Low disk space`).
