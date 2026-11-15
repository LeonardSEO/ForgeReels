# Visual explainer: one world, every key word on screen

The format for "explain how X works" reels. The voice is written and recorded FIRST; every visual event is then
tied to a spoken word in a machine-readable plan, so the picture changes exactly when the word is said, and a
re-recorded voice re-times every animation with one command. One continuous world, one camera, no slide cuts.

Proven projects (they double as regression tests), in the workspace: `references/examples/touchscreen/`
(hardware), `references/examples/web-cookies/` (software UI), `references/examples/ai-tokens/` (AI process, dark theme).

## The rules (non-negotiable in this format)

1. **Voice first.** Script -> voice -> `vo_check.py` -> word timing. Animations come after, from the words.
2. **Every key word has a visual meaning.** A noun appears, a verb happens, a number counts. A spoken line with
   no event is a sentence the picture ignores: `semantic_sync.py` warns about it.
3. **One world.** Objects persist and transform; the camera travels between them. Never swap the whole picture
   per sentence. Keep later objects hidden (`"hidden": true` in scene.json, or a first `reveal`) until their word,
   so nothing waits under the captions.
4. **Real objects, not icons.** Rebuild the actual thing (a phone and its sensor grid, the real UI, the chip) with
   the scene library; screenshots of a real product go in an `image` component.
5. **Captions use the same word times** as the animations (built in; the spoken word lights up).
6. **Everything a viewer must see sits in 168-1330 px.** Default "headline" captions sit at 270-420 px and the camera
   frames pictures in 450-1300 px; with `"captions": "pill"` in scene.json the captions move to 1135-1310 px and the
   pictures to 200-1080 px. Below 1330 px is decoration only (`platform-specs.md`).
7. **Facts first.** Every claim and number in `facts.md` with a source; illustrations are labelled as such.

## Project folder (`reels/<yyyy-mm-dd>-<slug>/` in the workspace)

```
<project>/
  script.txt          one spoken line per row (optional "[speed=1.1] " prefix); say.json for respellings
  facts.md            claim -> source, written before the script is final
  scene.json          the world: theme, world size, camera start, components
  visual_plan.json    the events, each tied to a word
  (built) vo/  assets/events.js  fr/  index.html  out/<project>.mp4  out/<project>-master.mp4  out/sync_sheet.jpg
  (final) <workspace>/output/<slug>.mp4   (--deliver, or the sound pass's final mix copied there; then qc_reel.py)
```

Build, check and render in one command (re-run after every edit; unchanged voice lines are reused):

```
python -I .claude/skills/forge-reels/scripts/pipeline/build_explainer.py --project reels/<date>-<slug> [--lang nl --engine pocket] --render --frames
```

Drafts stay in `out/`. `output/` is for finished videos only: the Stop hook holds each new one there until
`qc_reel.py` passes on it (`<video>.qc-pass`). An explainer without a sound pass: add `--deliver`.

Sound after the picture is approved: `scripts/pipeline/explainer_cues.py --project <p> --anchors <hook word> <turn word>`
(events -> cues.json on the same words), then beatgrid / score / beatmix as in `sound.md`.

Steps it runs: `build_vo` -> `vo_check` -> `words --align` -> `visual_plan` -> assemble -> `semantic_sync`
-> HyperFrames draft render -> `semantic_sync --frames`. It stops at the first failing gate. Then READ
`out/sync_sheet.jpg` (before | after of every event) and a contact sheet of the render, and run
`npx hyperframes check` in the project (it runs offline: the runtime needs no CDN).

## scene.json

```json
{"theme": "light", "world": {"w": 1080, "h": 2050}, "camera": {"start": ["title", "phone"]},
 "colors": {"accent": "#ff5a1f"},
 "components": [
   {"type": "text",  "id": "title", "x": 90,  "y": 110, "w": 900, "size": 76, "text": "How your screen finds your finger"},
   {"type": "phone", "id": "phone", "x": 330, "y": 330, "w": 420, "touch": {"x": 0.62, "y": 0.47}},
   {"type": "chip",  "id": "ic",    "x": 190, "y": 1460, "w": 700, "h": 620, "label": "TOUCH IC", "hidden": true}]}
```

Lay stations out top to bottom with **at least ~450 world px between them**: the camera frames by width, so a
narrow station shows a lot of world above and below it, and a neighbour half in frame looks like an error.
`camera.start` and focus targets take one id or a list (framed together). Themes: `light`, `dark`; override any
token in `colors` (bg, ink, card, accent, accent2, marker, cap-bg, ...).

### Components and their parts (`assets/scene-library/`)

| type | spec | parts (object ids are `<id>.<part>`) |
|---|---|---|
| `phone` | w, title, items[], touch{x,y}, notification, rows, cols | body, screen, ui, grid, rows, cols, field, finger, glass, notification (grid, field, finger, notification start hidden) |
| `browser` | w, h, tabs[], url, title, results[], cursor{x,y} | window, address, page, title, cursor, tab1..N, r1..N |
| `terminal` | w, lines[] ("$ " = command, "✓" = success) | window, cursor, l1..N |
| `nodes` | w, h, nodes[{id,label,sub,icon,x,y,color}], links[[a,b]] | n_<id>, l_<a>_<b> (flow sends a packet along the link) |
| `chart` | w, h, title, bars[{label,value,decimals,hot}], max, prefix, suffix | title, axis, b1..N (grow), v1..N (count) |
| `document` | w, h, title, lines[], source | page, title, source, l1..N (highlight marks the line) |
| `chip` | w, h, label, traces | chip, label, pins, t1..N (flow along each trace) |
| `stack` | w, layers[{label,color}], gap, step | L1..N (explode / collapse on the stack id) |
| `text` | w, text, size, weight, color, align | (the id itself; type types it) |
| `counter` | value, prefix, suffix, decimals, label | label (count on the id) |
| `callout` | text, to{dx,dy} | arrow (draw), label |
| `image` | src, w, h, card | (the id itself): real screenshots and product photos |
| `steps` | w, steps[] | s1..N: a chapter rail; `highlight` on sN marks that chapter reached |
| `frames` | src ("seq/%04d.jpg"), count, fps, first (1), w, device ("phone") | (the id itself): a captured screen recording; `play` on its word (dur = count / fps) |
| `lens` | w, h, label | glass, centre, rim, label: how a curved glass edge bends light (draw each) |
| `agent` | w, folder, prompt, steps[], model | prompt (type), input, s1..N (start hidden; reveal one per word): a coding agent at work |

Add a component: a `parts`/`hidden` entry in `core.js` FR.COMPONENTS and a builder in `renderer.js` FR.BUILD that
marks every part with `data-obj`; `tests/scene_core.test.js` checks the two agree.

## visual_plan.json

```json
{"events": [
  {"word_ref": {"line": 2, "expected": "grid"},  "action": "draw",  "object": "phone.rows"},
  {"word_ref": {"line": 4, "index": 6, "expected": "charge"}, "action": "pulse", "object": "phone.grid",
   "args": {"repeat": 2}, "dur": 1.0},
  {"word_ref": {"line": 6, "expected": "chip"},  "action": "focus", "object": "ic", "args": {"pad": 30}}]}
```

- `word_ref`: `line` (1-based) + `index` (0-based script word) + `expected`, or `expected` (+ `line`, + `nth`). A
  word that does not match is an ERROR, never a silent shift.
- `at`: `start` (default) or `end` of the word; `offset`: seconds (stagger a group by 0.08-0.1 s).
- Actions (default length): reveal 0.5, hide 0.35, focus 0.9, wide 1.0 (camera), draw 0.8, type 0.9, pulse 0.7,
  highlight 0.45, count 1.0 (`args.to` required), grow 0.7, explode 0.8, collapse 0.6, flow 1.2 (`args.repeat`),
  move 0.7 (`args.dx/dy`), morph 0.6, play 4.0 (frames), strike 0.4 (a red cross over a component: "no templates"),
  scan 0.6 (a bright line sweeps across and leaves the object behind: "all of this is code").
- Camera args (focus / wide): `pad`, `zoom`, `max`, and `ease`: `inOut` (default), `out` (full speed on frame 1,
  then settles: the hook's first move and any "look at this" snap), `linear`, `back`. The first camera move of a
  reel uses `"ease": "out"` with `"offset"` pulling it to t = 0, so the opening frame is already moving.
- A counting number rolls like an odometer: digits lock from the left, only the ones still rolling are blurred;
  counters size their font to the landed number.
- Ambient particles drift behind the world on every frame (`"ambient": "none"` to switch off, `"particles": 70`).
- An object whose first event is `reveal` or `count` is hidden until it; `draw`, `type`, `grow` start empty.
- A camera move every 1-2 lines; a smaller event (pulse, flow, highlight) on most key words in between.

## Look (measured on professional explainer reels, 2026-11-15)

Studied: five long explainers (82-150 s) and two shorter ones, frame by frame. What they all do, and what the
runtime now does by default:

- **Headline captions at the top**: the phrase appears word by word as it is spoken; earlier words grey, the spoken
  word bold, and the ONE word per phrase that moves the picture sits in a selection box with corner handles.
  The runtime boxes the first event word of each caption group automatically, so the box always means "this word
  just changed the picture".
- **The camera never parks**: between moves it keeps pushing in (1.5 %/s, at most 6 %; `camera.push` in scene.json,
  0 to switch off). Their reels never hold a still frame longer than 0.1-1.1 s.
- **Depth of field**: while the camera is on a target, every other component blurs and dims (`camera.dof: false` to
  switch off). Objects behind the captions are then soft, so the words stay readable.
- **Chapter rail** (`steps`): the story's stops, each lit on its word. Viewers see how far along they are.
- **Honest labels**: small "Magnified illustration", "Values illustrative", "Not to scale" notes in a corner, as a
  `text` component (size ~24, muted colour). Use them whenever the picture is a model, not the real thing.
- **Real subjects**: their hero objects are photoreal (a fingertip, glass, glowing field lines, a real dashboard).
  For that level, make the subject with `scripts/gen_image.py` (Codex) and animate it as an `image` component with
  library parts on top (fields, labels, flows). The CSS components are the diagram layer.
- **Pace**: visible change on most 0.1 s steps (46-94 % in theirs); a new visual idea every ~2 s; 80-150 s long
  when every line shows something new.

### From a 34 s promo reel (same idea as ForgeReels: a folder where Claude makes videos), 2026-11-15
Measured: 3.4 words/s, picture moving 75 % of the time, a big change every 0.7 s, no still over 0.4 s.
- **Cold open on proof**: frame 0 is the best shot of their best reel plus its view count, with their code scrolling
  behind it. Open on the finished result, explain after.
- **A spoken number is a rolling counter**: "thirty-nine million" boxed in the captions while the digits roll
  (blurred) to the exact figure. Every number still needs its source.
- **Show the agent working**: the folder, the prompt being typed, then each step appearing with its file
  (`facts.md`, `voice`, `scenes/...`, "Rendered ... 5,070 frames"). Use the `agent` component.
- **Negation is a picture**: "no templates" = a template card crossed out; "no camera, no drawing, no editing" =
  three icons, each struck on its word (`strike`).
- **Scale made human**: "18 million views, like 180 full stadiums" = a grid of 180 stadiums with a counter.
- **Show the checking**: a wall of frame thumbnails, a magnifier, a red box on the error, then a green check.
- **How such a system is built** (read from the code on screen): every scene is bespoke code, a pure function of the
  frame and a typed object of NAMED WORD CUES (a word not said yet = never); motion comes from small physics-like
  functions (follow, squeeze, smear) of those cues; particles have depth (speed, size and opacity scale with it) and
  do not move with the hero, so the eye measures the hero's motion against them; the plan is long (hundreds of lines
  for one reel): one decision per spoken phrase.
- **CTA as real UI**: "Comment FOLDER" big, then a share sheet picking a friend and "Sent"; the last frame returns
  to the opening shot so the loop is seamless.

## Rhythm and length

- Explainers may run longer than the 20-45 s reel default (60-110 s) when every line shows something new; the
  hook rules of `retention.md` still apply to the first 3 s. Judge length by `performance.md`, not by habit.
- Aim for a visible change at least every ~1.5 s (the touchscreen example: 35 events in 24 s), and no still frame
  longer than 0.5 s.

## Lessons from building the three examples (2026-11-15)

- Values that count up must not sit on screen as "0.00" first (fixed in the runtime: hidden until counted).
- An object that appears before its word ends up under the captions: hide it until its line.
- A title that is on screen for 0.5 s cannot be read (`hyperframes check` "line_unread"): hold ~0.5 s + 0.3 s/word.
- An event in the last frames after the voice is not tied to a word: `semantic_sync` rejects it.
