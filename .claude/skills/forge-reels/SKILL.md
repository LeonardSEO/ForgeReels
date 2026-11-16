---
name: forge-reels
description: The entry point for making ANY video with Claude, for any brand or project - short-form Reels / Shorts / TikToks above all, plus explainers, screen walkthroughs, promos, motion graphics, 3D, talking cartoon avatar presenters, kinetic type, captions, AI b-roll, voiceover (English, Dutch or Hindi), music and sound design. Knows every video tool it relies on and routes each job to the right one, holds the retention playbook (hook, re-hooks, climax, loop, shareability, eyebrow-raisers, topics), the per-video pipeline, the QC gate and the lessons, and improves itself after every video. Use whenever someone wants to make, plan, script, edit, animate, voice, score or review a video or reel, starts a new video chat, or names a brand pack (a skill called <brand>-reels). Load the brand pack too when one exists.
---

# ForgeReels

The single entry point for video work. Read this file first in every video chat, then the brand pack (if any),
then `lessons-learned.md` and `lessons.md`. Everything else loads on demand. macOS only (Apple Silicon recommended);
every script finds its tools through `scripts/_paths.py` (see `references/toolchain.md`).

**Workspace.** ForgeReels is a folder the user cloned and works in (see `CLAUDE.md` at its root):
- each video gets `reels/<yyyy-mm-dd>-<slug>/` and every file for it stays there (brief, sources, script, voice,
  scenes, drafts, QC);
- the finished video goes to `output/<slug>.mp4`;
- brand packs are in `brand/<name>/`; reference reels and the example explainers in `references/`;
- scripts run as `~/forge-reels/venv/bin/python -I .claude/skills/forge-reels/scripts/<script>` from the workspace
  root (`scripts/_paths.py` finds the workspace, the output folder and the other skills).

**Standing rule: this skill gets better after every video, for its whole lifetime.** See "Self-improvement" at
the bottom. A video is not done until that step is done.

**Quality rule: each new video must beat the last finished one** in every aspect of what is on screen (look,
depth, motion, graphics, transitions, sound, polish). Before building, list what the previous video did and write
down concrete upgrades per aspect. After delivery, record the new baseline in `lessons.md`.

## Start of every video chat (2 minutes)

1. Read `lessons-learned.md` (distilled rules) and `lessons.md` (your own dated entries, newest first;
   they override older text in the references).
2. Find the brand pack: `brand/<name>/` in the workspace (or a skill named `<brand>-reels`), with `brand.md` + `MOTION.md`. No pack and a
   new brand: make one with `references/brand-packs.md` (template in `templates/brand-pack-template/`) before
   designing anything.
3. Check the machine (`references/machine-limits.md`). On a small laptop: one render at a time, `--workers 2`,
   close the browser after use.
4. Confirm only what is missing: topic, language, length, platform. Defaults: 9:16 1080x1920 30 fps, 20-45 s,
   the brand pack's language rule.
5. First time on this machine? Run `python -I scripts/smoke_test.py`; it must print SMOKE PASS.

## Route the job

| Need | Use | Notes |
|---|---|---|
| Author / render any video | `/hyperframes` (+ `/hyperframes-cli`) | Default renderer. HTML + GSAP/Three.js, seek-exact, Apache 2.0. Read its `references/types/vertical.md` for reels |
| Ready-made blocks: transitions, captions, charts, 3D, camera moves, overlays | `/hyperframes-registry` | Search the registry BEFORE hand-building any named effect |
| Voice, music, SFX, transcripts, cutouts, grades | `/media-use` | Free local paths only (Kokoro, Openverse). Never its MusicGen fallback for published work, see `references/sound.md` |
| Brand system (brand.md + MOTION.md) | `/brand-intake` | Feeds every charlie947 skill below |
| Turn an idea into a precise build brief | `/motion-brief-writer` | Never invents a figure |
| Copy the moves of a reel you admire | `/reference-to-motion` (+ video-analyzer MCP for frames) | |
| Animated chart / count-up / before-after | `/animated-chart`, `/milestone-reveal` | Values stay exactly as given |
| Premium effects (chart morph, masked type, particles, glass focus, perspective shift, flowing paths) | `/motion-effects` | 16 effects, seek-exact |
| Cinematic 3D opener / hook | `/title-sequence-3d` | Three.js camera through a lit scene |
| Documentary explainer look | `/vox-explainer` | Torn paper, halftone, condensed type |
| Explain how something works (a device, a process, software, AI): one world, every key word animated on its word | **Visual explainer**: `references/visual-explainer.md` + `scripts/pipeline/build_explainer.py` | DEFAULT for explainers. scene.json + visual_plan.json, voice first, `semantic_sync.py` gate. Examples: `references/examples/` |
| Product UI / app demo: the real interface rebuilt and used up close (typing, clicks, results, zooms) | `/explainer-default` (calm 45-90 s demo), `/explainer-engaging` (10-30 s one-take) | FIRST choice for showing a product working; 9:16 via its vertical size or `/reel-export`. Real screenshots instead: `templates/screen-walkthrough/` |
| One-take story explainer (camera follows a hero element) | `/explainer-engaging`, or `templates/reel-project/` (a proven 80 s one-take world with a talking avatar) | |
| Hype / teaser, beat-locked kinetic type | `/explainer-high-energy` | |
| Motion b-roll over a talking head | `/motion-broll` | One morphing shape, timed to words |
| Beat-synced reel: grid, cue check, original score, pro SFX mix | `scripts/beatgrid.py`, `cuecheck.py`, `score.py`, `beatmix.py` (`references/sound.md`) | DEFAULT for every reel with music. Score = real CC0/CC BY instruments via lemo-opuscar's sampler; SFX = earshot's audited bank placed by its launch preset. Optional install: `setup/setup-audio.*` |
| Sound pass with the bundled CC0 kit / a finished edit | `/sound-effects` + `scripts/pipeline/mix.py` | Older route, still fine |
| A named film style (66: glass product, tilt-shift, paper pop-up, spy titles, dark keynote...), cinematic or 3D | `references/film-styles.md` + `toolchain.md` "Engine chooser" | Styles and techniques from lemo-opuscar (MIT); their demo films are CC BY, never copied |
| Does it flow or read like a slideshow? (carry per transition, rhythm, strobing fast moves) | `scripts/flow_check.py` (`references/qc.md`, visual-grammar "Carry every boundary") | Our own optical-flow checker (2026-11-04). Approved avatar explainers scored 0.40-0.42; beat your last reel |
| Cut a subject out of footage | `/object-separation` | SAM 2 local; pick the smallest model on a small machine |
| Make a 16:9 into a clean 9:16 upload | `/reel-export` | |
| Port Remotion / Lottie / Three.js / AE work | `/remotion-to-hyperframes` | |
| Screen walkthrough / how-to guide for a web app (16:9) | `templates/screen-walkthrough/` (README there) | Real screenshots + rings + cursor + Kokoro VO + chapter lane. Tall pages: capture in slices; Whisper-check every line |
| Edit existing footage (trim, crop, speed, merge, subtitles, QC) | mcp-video (Kinocut) MCP | `video_*`, `sound_qa_loudness`, `shorts_review`, `video_hook_candidates` |
| Remake a reference video as an editable project, checked frame by frame | `/reverse-any-video` | HyperFrames' own; only footage the user may reuse |
| A new episode in a proven style (collage, finance, science, 3D brand, true-crime explainer) | `/style-sampling` | |
| Use a Figma design, frame, logo or tokens in a video | `/figma` | |
| Study a reference reel (frames, transcript, timing) | `scripts/study_reference.py` + `references/reference-study.md` (video-analyzer MCP or /watch to fetch one) | Writes sheet, cuts, dark/light switches, timed transcript, a NOTES template. Instagram needs `YTDLP_COOKIES_FROM_BROWSER=chrome` |
| Cartoon avatar presenter that talks | `references/avatars.md` | Recommended: the ChatGPT pose library (image avatar, `scripts/avatar_track.py`). The HTML/SVG drawn character animated by GSAP works and is kept as an alternative. The video avatar (AI video body + our face, AI lip-sync) is dropped |
| Make character / avatar motion feel alive (acting, anticipation, overlap, weight) | `/disney-animation-rule-skill` (block event poses, pick the few principles that fix it) + `/animation-principles` (concrete durations, curves, springs, stagger) | Read both before animating any avatar gesture |
| Animate an SVG character rig (pivots, timelines, acting beats) | `/svg-character-animation` + `/gsap-core` + `/gsap-timeline` | Deterministic: one pure `render(t)` driven by a GSAP clock tween; never `.to()` or overlapping tweens on one property (frames render out of order) |
| Hand-painted look: brush strokes, watercolour washes, hatching, ink, a brush wipe inside a reel | p5.brush standalone build in a HyperFrames canvas (`references/painted-animation.md`, route A) | MIT. No npm needed: `dist/brush.js` from the kit. Redraw from `t`, seed per element, boil 12x/s |
| A short hand-painted cartoon (acted story beat, opener, loop) | ClaudeAnimationBase engine with OUR characters (`references/painted-animation.md`, route B) | MIT. Storyboard with reads first; contact sheet / strip / crop review loop. Clawd is Anthropic's mascot: see the trademark note in the reference |
| Editorial paper-collage b-roll that assembles from empty under one VO line | `references/collage-broll.md` | Three gates: metaphor, still (`scripts/gen_image.py`, Codex), motion (HyperFrames assembly by default; Gemini Omni web optional) |
| AI-generated cinematic b-roll (optional garnish) | `references/ai-broll.md` + `references/browser-ai.md` | Gemini Omni via the Playwright MCP, the user presses Send, ~4 clips/day |
| Still images: AI plates, backdrops, textures, collage stills | `scripts/gen_image.py` (Codex CLI image generation) | DEFAULT. One image per call (~1 min), `--ref` for brand/style frames, `--aspect 9:16`. Needs `codex` installed and logged in |
| Character sheets and pose libraries (one character across many images) | ChatGPT image gen via the Playwright MCP (`references/browser-ai.md`) | Keeps one chat's character memory. One tab, new chat per prompt, sends >= 60 s apart |
| Copy an audience will read (script, caption, hook text) | a de-AI writing skill (e.g. `/humanize`), one light pass for short text | |

Not used on purpose (do not add without asking): Remotion skills (company licence above 3 employees), the
OpenMontage toolchain (AGPL + paid providers; only its MIT `svg-character-animation` instruction skill),
paid inference wrappers, Blender (too heavy for a small laptop), MusicGen (CC-BY-NC), the lemo-opuscar plugin
itself (its rules, sampler and style index are used from a reference clone; the plugin would compete with this
skill), earshot's Gemini critique (uploads audio) and its forge search (needs licensed reference recordings).

## The pipeline (every video)

1. **Brief**: topic, audience, one-line promise, platform, language, length. Every number that will appear on
   screen gets a source in `sources.md` before scripting. No source, no number (illustrative values are labelled
   "illustrative" on screen).
2. **Learn from the references, then benchmark + hook + structure** (`references/reference-study.md`): any reel in
   the workspace's `references/` without a `<reel>.study/` folder gets `scripts/study_reference.py` first; read the
   `NOTES.md` files. Write `brief.md` with a "## Learned from references" table: at least 3 techniques, each with
   its source reel + time and OUR own version (from 2+ references, not the last video's three), plus "Not taken".
   `build_explainer.py` will not build without it. Learn the why, never copy the look. Pick a hook archetype, fill the retention grid (`references/retention.md`), write
   three hook options and three candidate structures; choose by the rubric. A strong look (cinematic, 3D, a brand
   style): choose from `references/film-styles.md` and the engine from `toolchain.md` "Engine chooser".
3. **Script**: spoken lines with beat timestamps. Dutch: numbers as words. Hindi: Devanagari, acronyms spelled phonetically for TTS
   (`references/voice.md`). One light de-AI pass on on-screen text.
4. **Voice**: record or TTS (`scripts/pipeline/build_vo.py --engine kokoro|pocket|voxcpm`: per line, placed at
   measured starts, unchanged lines reused; engines and licences in `references/voice.md`). Then
   `scripts/vo_check.py --vo vo` must exit 0 before anyone listens (spoken = script, no clipped last word). Tricky words,
   voice speed and music are picked BY EAR by the user on a pick page (`templates/reel-project/pick.html`).
   Measure the real duration: the VO length sets the edit, not the other way round.
5. **Beat grid + beat sheet** (`references/sound.md` "The beat pipeline"): `cues.json` (every cut, pop, landing
   and key word with its lock and SFX role), `scripts/beatgrid.py` (grid fitted to the anchor words, or a stock
   track seeked onto the cues), `scripts/cuecheck.py --snap` (every movable event onto a beat). Then the beat
   sheet, plus a sound design table (ambience, foley, music state per section), one row per 1.5-3 s: time, VO words, visual mode, graphic, SFX, music event, avatar pose (one
   pose per line, chosen to illustrate the line). Pick visuals from `references/visual-grammar.md`; change visual
   mode every 5-7 s at least (re-hook). With it, write the one-line-each STYLE BRIEF (`visual-grammar.md` "The style
   brief") and plan shot sizes, one new element per phrase, and the entity list (everything the VO names gets an image).
6. **Build**: HyperFrames project (start from `templates/reel-project/` or the brand pack's starter). Registry
   blocks first, then the specialist skills above, hand-built last. Word timings: `scripts/pipeline/words.py --align` (script words, forced alignment);
   named cues + captions: `scripts/pipeline/build_timing.py`. Avatar mouth cues: `scripts/mouth_rhubarb.py`
   (Rhubarb + the script text, all 9 shapes; Hindi or no Rhubarb: `mouth_phonemes.py`, same arguments;
   `mouth_from_audio.py` only with no script). A new face rig
   must pass its lip-seal gate (`references/avatars.md`). Avatar track: `scripts/pipeline/render_chunks.py`.
7. **Draft render**: `npx hyperframes check --json`, fix all errors, then
   `npx hyperframes render --quality draft --workers 2` (long reels: segmented capture, foreground).
8. **QC gate** (`references/qc.md`): `python -I scripts/qc_reel.py out.mp4 --sheet qc.png`,
   `python -I scripts/pace_check.py out.mp4 --mask <avatar box>`, READ EVERY FRAME as contact sheets
   (`scripts/pipeline/sheets.py`) plus the automatic avatar scan (`scripts/pipeline/scan_avatar.py`), watch the
   first 3 s and the climax frame by frame, self-score. Nothing goes to the user before this passes.
9. **Sound**: `scripts/score.py` (original score on the grid) + `scripts/beatmix.py` (earshot SFX on every cue,
   stop-downs, ambience, -14 LUFS mux); `scripts/cuecheck.py` must exit 0; Whisper on the final mix. Older route:
   `scripts/pipeline/mix.py`. Optional judge (run alone): `earshot critique out.mp4`.
10. **User review on a phone**, then the delivery render (`--quality delivery`) and a final QC run. Hand over: MP4
    (with and without music), cover frame, caption text, music credit line, `sources.md`, `licences.md`.
11. **Self-improvement** (below).

## Hard rules

- Never fabricate data, quotes, testimonials or results. Every on-screen claim traces to `sources.md`.
  Illustrative visuals are labelled.
- No em dashes in on-screen text or captions (they read as machine-written).
- Music must have a licence that allows the use (see `references/sound.md`) and is logged in the project's
  `licences.md`. Business accounts cannot use Instagram's trending library.
- Text and faces stay inside the safe box (`references/platform-specs.md`). Every hand and prop stays inside the
  frame.
- Real people as avatars only with their OK; cartoon caricatures, never deceptive photo-real fakes. Stock TTS
  voices are never presented as the person's real voice. AI footage that looks real gets the platform's AI label.
- The brand pack's compliance notes are followed; regulated brands keep a disclaimer slot that their compliance
  team fills, and its wording goes on screen VERBATIM (never rewritten or "fixed").
- Never kill a running render, server or app you did not start without asking.

## References (load on demand)

| File | What is in it |
|---|---|
| `references/toolchain.md` | Every tool: what it is, install, commands, licences, licence traps |
| `references/machine-limits.md` | Running heavy video work on a small laptop |
| `references/retention.md` | Hook, retention grid, re-hooks, open loops, climax, loop endings, shareability, eyebrow-raisers, topic engine, scoring rubrics |
| `references/visual-grammar.md` | Which graphic for which beat; the premium look; video-not-slides checks, shot sizes, one element per phrase, background menu, living type, minimum text sizes, style brief; pacing; effect ideas |
| `references/sound.md` | The beat pipeline (grid, cues, score, mix), music licence ladder, pro SFX roles, sound design rules, mix targets |
| `references/film-styles.md` | 66 named film styles (lemo-opuscar) by category, engine and use, "make a style your own" |
| `references/voice.md` | TTS options and how to pick; Hindi/Hinglish rules; voice bake-off; by-ear pick pages; Kokoro blending |
| `references/avatars.md` | Cartoon avatar pipeline: pose library, face rig, mouths (Rhubarb + lip seal), placement, gestures, QC |
| `references/browser-ai.md` | ChatGPT image gen + Gemini Omni through the Playwright MCP: queue, rate limits, saving, QA |
| `references/visual-explainer.md` | The visual-explainer format: rules, scene library components and parts, word-tied visual plan, build + sync gates |
| `references/collage-broll.md` | Halftone paper-collage b-roll: three approval gates, visual spec, colour-by-meaning, still prompt (Codex), HyperFrames assembly, Omni first/last-frame option, QA |
| `references/ai-broll.md` | Gemini Omni clips: when, prompts, user-sends flow, saving, watermark scrub, vertical framing |
| `references/platform-specs.md` | IG Reels / YT Shorts / TikTok specs, safe zones, covers, captions, export |
| `references/qc.md` | The QC gate checklist and the self-score rubric |
| `references/reference-study.md` | Learning from reference reels: study tool, the brief table and its gate, techniques learned so far |
| `references/brand-packs.md` | How to make a brand pack for a new brand or project |
| `lessons-learned.md` | Distilled rules from many real videos, by topic. Read at start |
| `references/reference-ranges.json` | Measured ranges per format from 71 reference reels; read by `motion_score.py` |
| `lessons.md` | Your own dated lessons (newest first). Read at start, append after every video |

Scripts (run Python helpers with `python -I`):
- `scripts/qc_reel.py` (measured QC + safe-zone contact sheet), `scripts/pace_check.py` (still stretches)
- `scripts/avatar_track.py` (placed corner avatar, one transparent track), `scripts/face_rig.py` +
  `face_paint.py` + `face_patch.py` (face rig, lip seal, long-hair patch), `scripts/pose_consistency.py`
  (pose library gate)
- `scripts/mouth_rhubarb.py` (DEFAULT lip-sync), `scripts/mouth_phonemes.py` (Hindi / no-Rhubarb, same arguments),
  `scripts/mouth_from_audio.py` (no-script fallback)
- `scripts/motion_score.py` + `study_motion.py` (how a reel moves vs 71 measured reference reels),
  `scripts/number_check.py` (every spoken / on-screen number must be in sources.md)
- `scripts/archive.py` (CC0 / public-domain images with licence sidecars), `scripts/photo_treat.py` (filmed-photo
  look), `scripts/tighten_vo.py` (shorten long VO pauses), `scripts/hf_get.py` (SHA-256-verified model downloads)
- `scripts/pipeline/`: `build_vo.py`, `words.py`, `build_timing.py`, `mix.py`, `sheets.py`, `render_chunks.py`,
  `scan_avatar.py`
- `scripts/smoke_test.py` (proves the toolchain works; must print SMOKE PASS)
- Older avatar routes kept for reference: `puppet_*`, `cutout_*`, `chain_*`, `build_*_scene.py`, `mocap_*`,
  `hybrid_head.py`, `pose_reel.py`, `gesture_plan.py`

## Self-improvement (standing rule, every video)

Before calling any video done:

1. Append a dated entry to `lessons.md`: what worked, what failed, what the user changed or rejected (their
   words), render times, any tool quirk, and the new quality baseline. Be specific enough that a future chat
   avoids the mistake without context.
2. Promote anything that will recur into the right reference file (or a script), and remove text it makes wrong.
   A lesson that appears twice in `lessons.md` must be promoted.
3. When the user reports how a posted video performed (views, watch %, sends, saves, follows), log it in the
   brand pack's `performance.md` and re-rank that pack's hook and topic lists by real results. Real numbers beat
   every heuristic here.
4. Tool changed (new version, new skill, broken command)? Update `references/toolchain.md` and the routing table.
5. Run `python -I scripts/smoke_test.py` and confirm SMOKE PASS.
6. Tell the user in 1-2 lines what the skill learned.

Back up before large rewrites to a folder OUTSIDE `~/.claude/skills/` (e.g. `~/.claude/skills-archive/<date>-forge-reels/`):
a copy inside the skills folder registers as a second skill.
