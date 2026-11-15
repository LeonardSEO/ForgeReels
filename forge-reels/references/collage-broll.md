# Collage b-roll: halftone paper-collage that assembles from empty

Method notice: `THIRD_PARTY_NOTICES.md`.

What it is: one ~5 s voiceover line pressed into ONE sharp visual metaphor, shown as a premium editorial paper collage
(flat bold colour field, black-and-white halftone photo cut-outs, a few coloured cardstock accents, cream keylines,
soft paper shadows) that **assembles piece by piece from an empty field**, stop-motion style. Not a fade, not a slow
zoom. Sits under the VO as b-roll. Default 9:16, 5 s, silent.

**How we run it.** `scripts/gen_image.py` (Codex image generation) makes the still and, by default, HyperFrames
assembles it (exact layers, free, repeatable). Gemini Omni on the web is the optional garnish route (`ai-broll.md`: the
user presses Send).

## The three gates (keep them: they put the user's taste first and stop wasted generations)

1. **Gate 1, metaphor only.** No images, no video. For each line give: core meaning · mood · the one-sentence visual
   proposition · 3-6 key objects · background colour + accent · assembly order. Then STOP for "ok / approved /
   changes per item". Only approved items move on.
2. **Gate 2, still only.** Write `visual-spec.json` + the image prompt, generate, QA, show a numbered contact sheet,
   STOP again. Regenerated stills get `still-contact-sheet-v2.jpg` (never overwrite the old sheet).
3. **Gate 3, motion.** Only approved stills are animated, then QA'd.

Batch mode: partial approval is fine; each item moves through the gates on its own.

Gate 1 example:
```
1. Core meaning: experience gets spent again and again
   Metaphor: a skilled editor cuts frame by frame around a giant film-reel clock; a full turn yields one short strip
   Objects: film clock, editor, scissors, short strip
   Colour: burnt orange field, cream and light teal accents
   Order: clock -> editor and scissors -> film -> the short output
```

## Rules for the metaphor

- One line = one metaphor; 3-6 key objects (more weakens the meaning and breaks the assembly).
- Never put the script words in the picture. Verbs to look for: open, connect, leak, bind, file, light up, compress,
  fork, assemble. Objects that work: machines, clocks, film, filing cabinets, consoles, rule books, funnels, tracks,
  chess pieces.
- A batch tells a little story across items (first the waste, then the system that fixes it).
- Colour by meaning, same design language, different field per item: burnt orange / red = time spent, labour, urgency;
  mustard = tools, warnings, lost experience; deep green = cognition, taste, reset; deep purple = rules, settling,
  long memory; teal = judgement, collaboration, automation. Colour accents serve hierarchy, never decoration.
  (Brand packs may override the palette: use the brand's colours as the fields.)

## visual-spec.json

```json
{
  "script_meaning": "", "visual_metaphor": "",
  "style_signature": "flat bold color field, mixed black-and-white halftone cut-outs and colored cardstock accents, crisp cut edges, cream keylines, soft paper shadows, editorial paper collage",
  "aspect_ratio": "9:16",
  "color_field": {"background_hex": "", "accent_colors": [], "paper_grain": "fine uncoated-paper fiber"},
  "elements": [{"what": "", "role": "", "motion": "", "placement": ""}],
  "composition": {"layout": "", "negative_space": "", "final_frame": ""},
  "motion_plan": "structure first, subject or cards second, action and result last",
  "avoid": "typography, readable letters, numerals, logos, watermark, UI, subtitles, glossy 3D, photoreal environment"
}
```

## Still prompt (`python -I scripts/gen_image.py "<prompt below>" -o stills/NN.png --aspect 9:16`)

```
Create a finished editorial paper-collage image expressing [visual proposition]. Vertical 9:16.
Scene: a perfectly flat [colour] paper field [hex] with subtle uncoated paper fibre.
Style: premium editorial stop-motion paper collage; black-and-white halftone photographic cut-outs mixed with
selective [accent] coloured cardstock.
Composition: locked vertical poster frame; the subject inside the middle 70 percent; generous clean colour-field
negative space; 3 to 6 LARGE paper groups that do not overlap each other, each with a clear cream keyline, so each
group can be cut out and animated on its own.
Materials: visible printed halftone dots, crisp machine-cut edges, thin warm-cream keylines, soft low-opacity drop
shadows.
Must read at a glance: [the relationship this metaphor depends on].
No typography, no readable letters, no numerals, no logos, no watermark, no UI, no subtitles, no glossy 3D, no
photoreal environment, no clutter.
```
The "groups do not overlap" line is ours: it lets route A cut the groups apart by colour.

Still QA: metaphor reads at a glance · subject concentrated · no fake text, logos, watermark, UI · enough empty
colour field to assemble from · 3-6 clear groups, not confetti · same texture across the batch, colours varied.
Write the verdicts to `gate2-qa.md`. Fake text in a still = regenerate the still, never patch it in video.

## Gate 3, route A (default): assemble in HyperFrames

1. Key the flat field out: plate colour = median of the corners, background = within a colour distance of it (a colour-
   distance test, not a hue test). Keep the cut-out shadows by keying only the field colour.
2. Split the foreground into connected groups (OpenCV components, merge specks into the nearest group, drop tiny
   ones). Too few groups (pieces touch) = use `/object-separation` (SAM 2) on the still, or regenerate with more
   space between groups. Save each group as a PNG with its bounding box; order them by the approved assembly order.
3. HyperFrames composition: the flat field fills the frame from frame 0 (check: the first frame is the empty field).
   Each group slides / drops / flips in from off-frame or from its own edge on an arc, **steps on twos** (12 fps
   holds) for stop-motion, overshoots 2-4 px and snaps into place with a tiny rotation settle; its shadow lands a
   frame after the paper. Order: structure -> subject or cards -> connectors -> the action -> the result. Hold the
   finished composition for the last ~1 s (it must match the approved still exactly).
4. Optional: a light paper-grain overlay and a 1-2 px frame jitter on the held pieces (boil, see
   `painted-animation.md`); a paper-slide SFX per landing from the earshot bank, on the beat grid.

## Gate 3, route B (garnish): Gemini Omni first/last frame

First frame = a flat field of the same hex (`ffmpeg -f lavfi -i color=c=0xHEX:s=1080x1920 -frames:v 1 first.png`),
last frame = the approved still cropped to 1080x1920. Through the Gemini web app per `ai-broll.md` (the user presses
Send; scrub the sparkle watermark). Prompt:
```
Paper-collage stop-motion assembly, using Image 1 as the exact empty first frame and Image 2 as the exact completed
last frame. In one continuous locked-off vertical shot, open on the empty flat [colour] paper field. Assemble the
scene piece by piece with crisp physical stop-motion timing: [the 3-6 elements in order: slide in, snap into place,
connect, complete the action]. End by holding the supplied completed composition. Preserve the exact 9:16 framing,
[hex] colour field, coloured cardstock accents, paper grain, halftone dots, cream keylines, crisp cut edges and soft
shadows. Restrained tactile 2D paper craft only. No scene cuts, no camera movement, no zoom, no morphing, no new
objects, no text, no letters, no numbers, no logos, no watermark, no UI, no sound.
```
Always strip the audio track (`-map 0:v:0 -c:v copy -an`). Weak assembly = fewer elements and an explicit
"slide in / snap into place" order; end-frame drift = stress "Image 2 is the exact completed last frame".

## Video QA (both routes)

- Contact sheet one frame per second (`fps=1,scale=270:480,tile=5x1`), plus the real first frame and a side-by-side
  of the last frame vs the approved still.
- First frame is the empty field (a sliver of paper at an edge is fine); the middle shows pieces arriving one by one,
  not a global fade; no cuts, zoom, 3D or photoreal drift; no fake text; last frame matches the still (small pose
  drift that keeps the meaning is a pass, don't re-run for it); silent; 9:16.
- Write verdicts (and why a flawed one passed) to `gate3-qa.md`.

## When not to use it

Real people, product ads, a talking actor; when every layer must stay editable later (build the scene in HyperFrames
from scratch instead); text-heavy beats (numbers belong to the chart tools, see `visual-grammar.md`).
