# Painted proof (p5.brush standalone inside HyperFrames)

A 4 s 1080x1920 scene: a watercolour wash blooming in, a pencil line drawing itself, a hatched card arriving on an
arc, a painted brush wipe out. Every frame is drawn from `t` alone.

1. `npx hyperframes init my-painted --resolution portrait --skip-skills --non-interactive`
2. Copy this `index.html` over the project's one.
3. Copy `dist/brush.js` from p5.brush (https://github.com/acamposuribe/p5.brush, MIT, Copyright (c) 2023-2026
   Alejandro Campos Uribe) into `lib/brush.js`, keeping its licence with it. It is not bundled here.
4. `npx hyperframes render --quality draft --workers 2 --output painted.mp4`

`hyperframes lint` reports `Math.random()` and `requestAnimationFrame` inside brush.js: both are false positives
(see `references/painted-animation.md`).
