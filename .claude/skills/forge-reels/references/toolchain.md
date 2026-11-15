# Toolchain

Everything this skill uses, all free, with the reason each is safe to publish with. `setup/setup-mac.sh` installs all of it
(macOS, Apple Silicon recommended). Update this file whenever a tool changes (version, command, breakage).

Where things live (see `scripts/_paths.py`):
- `FORGE_REELS_HOME` (default `~/forge-reels`) holds tools, models, smoke tests and scratch files.
- `~/.forge-reels/config.json` overrides individual paths (written by the setup scripts).
- Executables are looked up on the PATH first.

## Skills this one routes to (installed by the setup scripts; see `setup/skills.txt`)

| Skills | Upstream repo | Licence |
|---|---|---|
| hyperframes, hyperframes-cli, hyperframes-registry, media-use, remotion-to-hyperframes, reverse-any-video, style-sampling, figma | heygen-com/hyperframes | Apache 2.0 |
| brand-intake, motion-brief-writer, reference-to-motion, animated-chart, milestone-reveal, motion-effects, title-sequence-3d, vox-explainer, reel-export | charlie947/motion-graphics-skills | MIT |
| motion-broll, sound-effects, explainer-high-energy, explainer-engaging, object-separation | Barty-Bart/motion-graphics | MIT (SFX CC0, fonts OFL) |
| animation-principles | iart-ai/motion-design-skills | see repo |
| disney-animation-rule-skill | vibe-motion/skills | see repo |
| svg-character-animation | calesthio/openmontage (only this MIT instruction skill; the toolkit itself is AGPL + paid providers) | MIT |
| gsap-core, gsap-timeline, gsap-plugins, gsap-utils, gsap-performance, gsap-react, gsap-scrolltrigger, gsap-frameworks (official) | greensock/gsap-skills | see repo |
| humanize (writing passes for on-screen text) | any de-AI writing skill you trust; optional | |

Install or update one: `npx skills add <repo> --skill <name> -g -y -a claude-code`. List a repo's skills with
`--list`. The HyperFrames CLI runs from npx at its latest version (checked against v0.9.52 on 2026-11-15: every command
and flag used here still exists). HyperFrames ships fast: re-run `bash setup/setup-mac.sh --minimal` to refresh its skills.

## MCP servers (optional, add them in Claude Code)

| Server | Use for | Gotchas |
|---|---|---|
| Playwright MCP | Driving ChatGPT (still images) and Gemini (Omni video) in the user's OWN logged-in accounts; screen captures for walkthroughs | "Playwright" means this MCP browser, never a script. See `references/browser-ai.md` |
| video-analyzer | Transcripts, frames, bursts and metadata of reference reels | Local audio must be wrapped as MP4 first (ffmpeg, black video). Instagram needs `YTDLP_COOKIES_FROM_BROWSER=chrome` |
| mcp-video (Kinocut) | Editing existing footage, subtitles, QC (`sound_qa_loudness`, `video_quality_check`, `shorts_review`, `video_hook_candidates`) | Its transcription needs `pip install "kinocut[transcribe]"` |

## Local tools

| Tool | Install / run | Notes |
|---|---|---|
| ffmpeg / ffprobe | `brew install ffmpeg` | Everything uses it |
| Node 20+ | `brew install node` | HyperFrames CLI via npx |
| Python 3.10-3.12 | `brew install python@3.12` | `pip install -r setup/requirements.txt` |
| Codex CLI (image generation) | `npm i -g @openai/codex`, then `codex login` | `scripts/gen_image.py`. Optional: without it, still images come from ChatGPT via Playwright |
| HyperFrames CLI | `npx hyperframes` | `npx hyperframes doctor`. Headless Chrome is cached in `~/.cache/hyperframes/chrome` |
| Kokoro TTS (Apache 2.0) | `npx hyperframes tts "<text>" -v af_heart -o out.wav` | 54 voices incl. Hindi (`hf_alpha hf_beta hm_omega hm_psi`, pass `-l hi`). Needs `kokoro-onnx` + `soundfile` in the Python that `HYPERFRAMES_PYTHON` points at |
| Whisper (word timings) | `npx hyperframes transcribe file --model small.en` | Builds whisper.cpp on first use. Hindi: `--model small --language hi` |
| faster-whisper | pip | Line-by-line voice read-back checks (templates/screen-walkthrough/tools/check_vo.py) |
| Rhubarb Lip Sync 1.14 (MIT) | release zip `Rhubarb-Lip-Sync-1.14.0-macOS.zip` | From github.com/DanielSWolf/rhubarb-lip-sync. DEFAULT lip-sync via `scripts/mouth_rhubarb.py`: per line, `-d` script text, `--extendedShapes GHX`, 1-frame lead, ~10 s per line. Wants 16-bit PCM WAV (the script converts). macOS: clear quarantine with `xattr -dr com.apple.quarantine <folder>` |
| MediaPipe models | `face_landmarker.task`, `pose_landmarker_heavy.task`, `hand_landmarker.task` | Downloaded by setup into `<home>/tools/mediapipe` (Google's storage URLs in the setup scripts) |
| Fonts | bundled in `assets/fonts` | Inter, Mukta, Noto Sans Devanagari (OFL). Point `FORGE_REELS_FONTS` at a brand's own fonts |
| Pace check | `python -I scripts/pace_check.py reel.mp4 --mask <avatar box> --mask <caption box>` | Lists still stretches over 1 s and still frames in the first 2 s. ~1 min for 80 s |
| edge-tts (optional) | `pip install edge-tts` | Microsoft neural voices incl. Indian English. GREY licence (unofficial use of a consumer read-aloud service): only if the user accepts the risk |
| Parakeet ASR (optional) | `npx hyperframes models install parakeet` | English/European only |
| **Beat + sound pipeline (2026-11-01)** | `scripts/beatgrid.py`, `cuecheck.py` (system Python `-I`); `score.py`, `beatmix.py` (AUDIO venv) | See `sound.md` "The beat pipeline". Grid fit on a 97 s track ~20 s; score 10 s ~11 s; mix + mux ~2 min first run (kit render), cached after |
| AUDIO venv | `<FORGE_REELS_HOME>/tools/earshot/.venv` (setup/setup-audio.sh) | Python 3.12 + earshot 0.4.0 (editable), torch 2.15 CPU, librosa 1.0, soxr. |
| earshot 0.4.0 (MIT) | `<FORGE_REELS_HOME>/tools/earshot` (clone @591fa3e) | `sfx list/render/check`, `kit init/render/check/audition`, `measure`: no models. `critique/timeline/sheet/describe/match`: CLAP + AST models (1.1 GB, `.cache/hf` in the tool folder; `doctor --fetch`). MCP server exists (`pip install -e .[mcp]`), not registered |
| lemo-opuscar (MIT code, CC BY demos) | `<FORGE_REELS_HOME>/tools/lemo-opuscar` (clone @bebbbe1, reference only: never build inside it) | Sampler + pluck + sfx (`core/audio`), three.js post (`core/three/post.js`), CRT pass, readcheck, 66 styles (`references/film-styles.md`). Sample libraries in `core/audio/instruments/` (1.28 GB): vsco2ce, vcsl, freepats (CC0), salamander (CC BY 3.0). Fetch more: `python -X utf8 -I <fetch logic from tools/fetch.sh>`. Karoryfer (erhu, jazz bass, alto sax) not fetched |

## Engine chooser: which tool makes which kind of video (2026-11-01)

Compare before every new kind of video; the user plans 3D and cinematic work. Times measured on this laptop.

| Need | Best engine here | Quality ceiling | Render cost (a 6 GB laptop) | Licence |
|---|---|---|---|---|
| Reels: kinetic type, cards, charts, one-take worlds, avatar compositing | **HyperFrames** (HTML + GSAP render(t)) | high; seek-exact; registry blocks | 10 s 1080x1920 draft ≈ 1.5 min (`--workers 2`) | Apache 2.0 |
| 3D shots inside a reel (product hero, diorama, isometric world, title) | **three.js inside HyperFrames** (`/title-sequence-3d`, `/threejs-webgl`) + opuscar's `core/three/post.js` ideas: physical DOF, GTAO, bloom, colour grade, 2x supersample, a Poly Haven HDRI at low intensity + soft area lights | near "rendered" look with post; hardware WebGL via ANGLE/D3D11 | heavy: budget 2-4x a 2D reel; render 2x then downsample only for hero shots | MIT / CC0 assets |
| Full cinematic film in one named style (66 styles) | **opuscar's method in our stack**: their `STYLE.md` + techniques, our HyperFrames render, our beat grid | their gallery is the bar (`references/film-styles.md`) | as above | MIT code; demos CC BY (never copy) |
| Real-looking b-roll (people, places, nature) | **Gemini Omni via Playwright** (`ai-broll.md`) | photoreal, 8 s clips, watermark scrub | ~4 clips/day, user presses Send | platform terms; AI label when it looks real |
| Still plates, backdrops, textures, collage stills | **Codex image generation** (`scripts/gen_image.py`) | one call per image, scriptable, brand refs via `--ref` | ~1 min per image | user's Codex account |
| Character sheets, pose libraries (one character across many images) | **ChatGPT image gen via Playwright** | best character consistency we have | 60 s between sends | user's account |
| Hand-painted look (brush, watercolour, hatching, boiling ink) | **p5.brush standalone in HyperFrames**; whole painted cartoons: **ClaudeAnimationBase** (p5 + puppeteer `render.mjs`) | real natural-media look | measured 2026-11-04: on a Vega 8 laptop: route A 4 s fully painted ≈ 1.5 min (~0.8 s/frame, deterministic); route B 0.6-4 s per 1080p frame; fills are the cost, keep them few | MIT |
| Paper-collage b-roll under a VO line | **HyperFrames assembly** of a Codex collage still (`collage-broll.md`); Gemini Omni first/last frame as garnish | premium editorial | still ~60 s + 5 s assembly render ≈ 1 min | MIT method; your Codex account |
| Rigged true 3D characters | not here (Blender rendering too heavy; VRM only after 2D is proven) | n/a | n/a | n/a |
| Editing existing footage | mcp-video (Kinocut) | n/a | fast | MIT |
| Music | `scripts/score.py` (original, beat-locked) > platform library > Mixkit (seeked by `beatgrid.py`) | real sampled instruments | 10 s ≈ 11 s | CC0 / CC BY credit lines |
| SFX | earshot bank via `beatmix.py` | pro-measured placement | seconds | MIT |

Reviewed 2026-11-04: p5.brush and ClaudeAnimationBase (MIT, adopted as optional engines); onetake (PolyForm
NONCOMMERCIAL: not adopted, its code never read).
Rule: pick the cheapest engine that reaches the look; one 3D hero shot inside a 2D reel beats a whole 3D reel
that renders for an hour. Every new engine or style gets a row here and a line in `lessons.md`.

## Machine limits (measure YOUR machine and write the numbers here)

The skill was built on a 6 GB RAM laptop with an integrated GPU. What worked there and still helps on bigger machines:

- Render with `--workers 2`. Each worker is a Chrome (~256 MB). Budget ~5-6 min per 30 s reel at draft quality,
  more with heavy Three.js. An 80 s one-take reel took ~10-11 min (draft) and ~23 min (delivery).
- Run ONE heavy job at a time: render, avatar track or browser session. Close the Playwright browser after use.
- Long renders run as FOREGROUND chunks (`--only` / segmented capture with `HF_SEGMENTED_CAPTURE=true --resume`).
  When RAM ran low, long background jobs were killed and a 45 min render was lost.
- `export OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1` before numpy-heavy scripts when memory is tight.
- Give avatar_track.py a plan holding only the poses in the range: it loads every pose up front
  (`scripts/pipeline/render_chunks.py` does this).
- If memory still fails, ask the user what to close. Never kill a process you did not start.
- No local Blender rendering and no local music or voice-clone models on a small laptop. Use a free cloud GPU
  (e.g. Colab) if needed.
- See `references/machine-limits.md` for the full checklist.

## Licence traps (why some free things are banned)

- MusicGen weights: CC-BY-NC. It is media-use's local music fallback; do NOT install its deps, so media-use skips
  generated music instead of using it.
- XTTS-v2 (CPML), F5-TTS weights, Fish Speech: non-commercial. No free commercial voice cloning exists, so brand
  voices are stock TTS voices, not clones of real people.
- Remotion: free only for individuals and companies up to 3 people.
- Mixkit music: allowed on social and ads, but never register it with Content ID.
- Instagram's trending music library: personal accounts only. Business accounts get Meta Sound Collection.
- Brand fonts (e.g. ITF FFL fonts): embedding in rendered video is usually fine, sharing the font files is not.
- Licence reads (2026-11): CoTracker (non-commercial demo), Depth Anything V2 Base and Large (CC-BY-NC; only Small
  is Apache-2.0), RMBG-2.0 (own gated licence), BBC Sound Effects (non-commercial), Voxtral TTS (CC-BY-NC). Sonniss
  GDC bundles: fine inside videos, AI training forbidden. LTX-2 weights: community licence, read it first; Wan 2.2
  is Apache-2.0.

## Tool safety gate (before installing anything new)
1. Licence allows commercial use, read from the actual licence file, for the code AND the weights.
2. Official source, maintained, real community use. 3. Dependency scan (OSV) and a read of install scripts.
4. Own environment, pinned versions, no auto-update. 5. Safetensors or safe loading, checksum recorded, telemetry
off; big downloads through `scripts/hf_get.py` (SHA-256 checked; an interrupted hub download once left a
zero-filled model file at its final name). 6. Measured on your machine: speed, peak RAM, disk. 7. Scored on known
answers before it is trusted. 8. Losers deleted and written down so nobody retries them blindly.

## Heavier local tools (measured on a 16 GB M-series Mac)
ACE-Step 1.5 turbo music (30 s in ~50 s, peak 10.6 GB); Blender EEVEE paper dioramas (0.36 s/frame at 540x960);
mlx-audio voices (Qwen3-TTS, Ming-3.0, VoxCPM2, Chatterbox; Apple-only runtime; lines made one by one drift in
voice unless each is cloned from one reference clip); BiRefNet-lite ONNX cut-outs (224 MB, 6 s/image on CPU);
Depth Anything V2 Small for 2.5D layers. On a 6 GB laptop use a cloud notebook for the first three.
