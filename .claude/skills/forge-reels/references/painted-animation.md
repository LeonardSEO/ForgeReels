# Painted animation: p5.brush strokes and hand-painted cartoons

Added 2026-11-04 from two MIT repos:

- **p5.brush** (github.com/acamposuribe/p5.brush, MIT, @d56350a): natural media in the browser: pencils, charcoal,
  markers, ink, watercolour fills with bleeding edges, hatching, vector fields.
- **ClaudeAnimationBase** (github.com/JohnHeibel/ClaudeAnimationBase, MIT): a starter kit that paints a
  whole cartoon with p5.brush, frame = pure function of time, with a headless renderer, a review loop and an animation
  guide written from what the model got wrong.

Clone them into a kits folder of your own (for example `~/forge-reels/kits/`). Treat downloaded code as untrusted:
read it first, and run its install scripts only when you mean to.

## Two ways to use it

| Use | How | When |
|---|---|---|
| **A. Paint inside a HyperFrames scene** (default) | p5.brush **standalone build** `dist/brush.js` (no p5, no npm, WebGL2 only) on a `<canvas>` in the composition; redraw the whole canvas from `t` in the seek handler | painted backgrounds, watercolour washes behind type, a brush-stroke reveal, hatching on a chart, a brush wipe between scenes, ink underlines. Keeps captions, avatar and VO in our normal pipeline |
| **B. A whole hand-painted cartoon** | ClaudeAnimationBase engine (p5 build + puppeteer renderer `render.mjs`) with OUR characters, then the MP4 goes into the reel like b-roll | a 5-20 s acted story beat (a character wants, tries, fails, reacts), an opener, a loop. Needs `npm install` in the kit folder (Claude Code's auto mode may block it as code from outside: run it yourself with `! cd <kit> && npm install`) |

**Clawd is the Claude Code mascot (Anthropic's character).** The kit's MIT licence covers its author's code, not the
character. Anthropic's trademark guidelines (anthropic.com/legal/trademark-guidelines) require prior approval,
forbid alterations and forbid implying sponsorship or endorsement. Use the engine to paint your own characters;
decide for yourself, with those guidelines in hand, whether and how Clawd may appear in your own videos.

## p5.brush essentials (standalone build, route A)

- Load `brush.js` from the kit's `dist/` (copy it into the project; never hotlink a CDN in a render).
- `brush.createCanvas(w, h)` creates the canvas; transforms are `brush.push/pop/translate/rotate/scale`; angles via
  `brush.angleMode(brush.DEGREES)`; seed with `brush.seed(n)` / `brush.noiseSeed(n)`; clear with `brush.clear(col)`;
  **call `brush.render()` at the end of every frame**. Never mix p5 calls into the standalone build (it breaks silently).
- The p5 build is the other way round (`createCanvas(w, h, WEBGL)`, p5's push/pop/randomSeed, no `brush.render()`).
  Check which build a snippet assumes before copying it (the kit's `llms.txt` has the full split).
- Strokes: `brush.set(name, colour, weight)` then `brush.line/stroke/spline/flowLine`. Built-in brushes: `2B`, `HB`,
  `charcoal`, `marker`, `pen`, `cpencil`, `rotring`, `spray` (+ the kit's `ink`, `inkfine`, `dry`).
- Fills: `brush.fill(colour, opacity)` + `brush.fillBleed(k, 'out'|'in')` (~.05-.3) + `brush.fillTexture(tex, border,
  scatter, split)` for real watercolour (wet-in-wet where fills touch; the paper dries at each `brush.render()`);
  `brush.wash(colour, opacity)` is the FAST flat fill (no simulation); `brush.hatch(dist, angle, {rand, continuous,
  gradient})` for hatching. Watercolour fills are the expensive part; a full-canvas fill at pixel density 2 is worst.
- Standalone frame: `brush.clear(bg)`, `brush.push()`, `brush.translate(-W/2, -H/2)` (WEBGL origin is the centre),
  draw, `brush.pop()`, `brush.render()`. Forgetting `render()` = nothing appears.
- `brush.scaleBrushes(k)` to match the canvas size (3 is right for 600x600; scale up for 1080x1920).
- Colours mix like pigment: yellow over blue goes green, thin washes go grey. Light over dark = full-opacity wash or
  an additive glow drawn under the paper grain.

## Determinism (both routes, from ClaudeAnimationBase)

Frames render in parallel and out of order (same as HyperFrames). So:
- Draw the WHOLE frame from `t` every time. No state between frames, no counters, no `Math.random()`, no physics.
- **Boil**: re-seed the jitter ~12 times a second so still drawings wobble like hand-drawn animation; that's the look.
  Use a stable `hash(i)` for anything that must stay put (star positions, tuft heights).
- **Seed each element separately** (`boilSeed(key)` in the kit): one moving thing uses more randomness and shifts the
  stream, so everything drawn after it re-boils every frame and jitters. Reseed per layer / prop / effect.
- In HyperFrames: compute `boil = Math.floor(t * 12)` and call `brush.seed(hash(boil, elementKey))` before each element.

## The rules that make it look handmade (ClaudeAnimationBase guide, in short)

Three goals: **handmade** (brush strokes, boiling ink, flat 2D), **alive** (something always moves and happens),
**one piece** (plan first, link every scene). Underneath: the viewer must be able to follow it.

1. **Medium**: everything painted (`paint()` / `inkLine()` in the kit); no plain p5 shapes or CSS gradients mixed into
   the paint (looks like 2000s Flash). Flat 2D only: turns go through drawn key views (front, 3/4, side, back), depth
   from overlap, scale and colour, never a 3D projection. Soft palette, no pure black or white.
2. **Text**: painted cartoons carry no captions or labels; reactions are painted marks (`!`, `?`, sweat, hearts, bulb).
   In OUR reels the captions/VO layer sits outside the painted plate, so this rule applies to the painting itself.
3. **An event in every shot**: something changes between the first and last frame; one focal action at a time;
   cause, then reaction (give the reaction time); pay off every setup.
4. **Timing = model the viewer** (the one models get wrong most): see "Reads" below. Fast actions, slow meanings.
5. **Alive**: idle motion per emotion, the camera drifts or pushes, faces act (anticipation, squint, take, overshoot)
   and never snap; characters big enough to feel; everything on one beat (`bpm`).
6. **Transitions always**: into the first shot, every seam, out of the last. Brush wipe, iris / shaped iris, whip pan
   with smear, match cut, cut on action, a camera move carried across. Props arrive and leave on arcs.
7. **One piece**: storyboard before code; one world and palette with a colour arc; one emotional thread; the ending
   rhymes with the opening; motion and screen direction continue across cuts.

Animation principles it leans on (see also `/disney-animation-rule-skill`, `/animation-principles`): anticipation,
squash and stretch, slow in / slow out, weight, arcs, overlap and follow-through, **avoid twinning** (code copies
values: both arms, both blinks, a whole crowd in sync), exaggeration, strong key poses, show the thought, secondary
action.

## Reads: the timing sheet (applies to EVERY video, promoted to visual-grammar.md)

For each shot, list in order what the viewer must understand: each item is a **read** with a start and end time.
Each read needs time for the eye to find it, time to understand it, and a beat to register before the next starts.
No two important reads overlap. If a shot's reads don't fit, lengthen the shot or cut a read; never squeeze.
Lead the eye before each read (a look, a camera move, motion or light first). The last read needs time to land
before the video ends. Their demo's ending first packed six reads into 1.3 s and "nobody could tell what had happened";
the fixed version gives them 4 s.

Storyboard format (write before any scene code):
```
Logline: X wants ___, but ___, so ___.
World: setting, small palette, light, colour change across the video.
Motif: what recurs and pays off.
Arc: the emotion keys across the whole video.
Shots:
  A  start-end  [transition in: ___]  what's seen · the EVENT · the reaction · camera
     reads:  start-end  first thing the viewer must understand
             start-end  next one (where is the eye when it starts?)
  [transition out: ___]
```

## Review loop (route B; the same idea works in HyperFrames with `hyperframes snapshot`)

You can't see motion by reading code. Render and look, at three zooms:
```bash
node render.mjs --sheet=0.1,0.8,1.6,2.4 --cols=6 --w=320 --out=out/check/sheet.jpg   # contact sheet: whole piece
node render.mjs --strip=2.1:2.6 --cols=6 --w=320 --out=out/check/strip.jpg          # every frame of a moment
node render.mjs --sheet=2.3 --crop=760,420,500,400 --w=500 --out=out/check/face.jpg  # full-res detail
node render.mjs --clip --out=out/video.mp4                                           # final MP4
node render.mjs --frames --workers=2 ; node render.mjs --encode --out=out/video.mp4    # resumable on this laptop
```
Check reads (event clear from the sheet alone), timing (sheet at a fixed 0.1-0.15 s step, count frames per read),
motion (anticipation, follow-through, pops, constant speeds, mirrored arms), boil (still things must not change between
paired frames), contacts (feet on ground, held props touch the hand), transitions at every seam, no text, no 3D,
no muddy glows. Budget: one sheet per shot, a strip per key motion and transition, a crop per story face.

## Proven (2026-11-04): `templates/painted-proof/index.html` is the working template

A 4 s 1080x1920 HyperFrames scene: a watercolour wash blooming in, a 2B pencil line drawing itself, a hatched card
arriving on an arc with overshoot, a painted brush wipe out. Results:
- On a Ryzen 5 3500U / Vega 8 laptop it renders at **~1 m 20 s - 1 m 45 s per 4 s** (`--workers 2`, hardware GPU, pixelDensity 1): about 0.7-0.9 s per
  frame. Budget ~10 min per 30 s of fully painted frames; paint only the shots that need it.
- **Deterministic**: two renders compared frame by frame, max pixel difference 0.
- Template pattern: `brush.createCanvas(W, H, {parent, pixelDensity: 1})`, `brush.scaleBrushes(5)` at 1080 wide,
  `renderAt(t)` guarded by `lastT`, driven by BOTH a paused GSAP clock tween registered on
  `window.__timelines["main"]` (onUpdate) and an `hf-seek` listener.
- `hyperframes lint` reports 2 errors that are FALSE POSITIVES for brush.js: `Math.random()` (only seeds the
  library's default PRNG at load; every element calls `brush.seed()`) and `requestAnimationFrame` (only a
  "render() was never called" warning helper). Any other lint error is real.

Lessons from the proof:
- **Never boil a watercolour fill.** Re-seeding a fill reshuffles its whole pigment pattern, so the wash flickers 12x
  a second (430k px changed between boil frames). Seed fills with a FIXED key; boil only ink lines and hatching
  (measured after the fix: 0 px changed inside the wash, lines still boil).
- **A brush wipe is painted polygons, not fat strokes.** `brush.line` with a marker at weight 70 threw and blanked the
  whole frame. Use the kit's recipe: 5-6 ragged bands (straight-ish top and bottom, a ragged leading edge from
  `hash`), each `brush.wash(colour, 255)` + `brush.hatch(44, 0, {rand: .6, gradient: .5})` +
  `brush.hatchStyle('charcoal', cream, .8)` + `brush.polygon(pts)`, staggered delays `[0, .14, .06, .18, .1]`.
  Cut to the next scene under full cover, then drag the bands off.
- One thrown error inside `renderAt` blanks the frame silently in the render. Check a contact sheet at the seams.

Route B (the full ClaudeAnimationBase engine), measured 2026-11-04 on the same laptop: the demo's
contact sheet rendered (6 frames, 30 s) at **0.6-4.1 s per 1920x1080 frame**; the slow ones are the watercolour
night sky. Budget ~10-15 min for its 11 s demo; use flat washes for long shots. `npm audit` reports 3 "high"
(zod memory exhaustion via puppeteer-core / chromium-bidi): only matters for validating hostile oversized input,
not a local renderer; don't run `npm audit fix --force` (it would change the pinned puppeteer).

## Known p5.brush gotchas (from the kit)

- Under a zoomed camera, strokes far from the origin collapse to a dot: draw each shape around its own centre; draw
  long edges as lines no bigger than the canvas.
- Outline weight is in world units: scale `sw` down with zoom or small shapes become dark blobs in close-ups.
- A NaN in a point list throws `Failed to construct 'OffscreenCanvas'...` pointing at your scene: guard geometry
  (`Math.acos` of a ratio > 1).
- Five `WebGL: INVALID_OPERATION ... not from the associated program` warnings once per page are harmless.
