# Visual explainer: one world, every key word on screen

The format for "explain how X works" reels. The voice is written and recorded FIRST; every visual event is then
tied to a spoken word in a machine-readable plan, so the picture changes exactly when the word is said, and a
re-recorded voice re-times every animation with one command. One continuous world, one camera, no slide cuts.

Proven projects (they double as regression tests): `examples/touchscreen/` (hardware), `examples/web-cookies/`
(software UI), `examples/ai-tokens/` (AI process, dark theme).

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
6. **Everything a viewer must see sits in 168-1330 px.** The runtime frames pictures in 200-1080 px and captions in
   1135-1310 px; below is decoration only (`platform-specs.md`).
7. **Facts first.** Every claim and number in `facts.md` with a source; illustrations are labelled as such.

## Project folder

```
<project>/
  script.txt          one spoken line per row (optional "[speed=1.1] " prefix); say.json for respellings
  facts.md            claim -> source, written before the script is final
  scene.json          the world: theme, world size, camera start, components
  visual_plan.json    the events, each tied to a word
  (built) vo/  assets/events.js  fr/  index.html  out/<project>.mp4  out/sync_sheet.jpg
```

Build, check and render in one command (re-run after every edit; unchanged voice lines are reused):

```
python -I scripts/pipeline/build_explainer.py --project <project> [--lang nl --engine pocket] --render --frames
```

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
  move 0.7 (`args.dx/dy`), morph 0.6.
- An object whose first event is `reveal` or `count` is hidden until it; `draw`, `type`, `grow` start empty.
- A camera move every 1-2 lines; a smaller event (pulse, flow, highlight) on most key words in between.

## Rhythm and length

- Explainers may run longer than the 20-45 s reel default (60-110 s) when every line shows something new; the
  hook rules of `retention.md` still apply to the first 3 s. Judge length by `performance.md`, not by habit.
- Aim for a visible change at least every ~1.5 s (the touchscreen example: 35 events in 24 s).

## Lessons from building the three examples (2026-11-15)

- Values that count up must not sit on screen as "0.00" first (fixed in the runtime: hidden until counted).
- An object that appears before its word ends up under the captions: hide it until its line.
- A title that is on screen for 0.5 s cannot be read (`hyperframes check` "line_unread"): hold ~0.5 s + 0.3 s/word.
- An event in the last frames after the voice is not tied to a word: `semantic_sync` rejects it.
