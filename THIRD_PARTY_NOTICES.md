# Third-party notices

ForgeReels is MIT licensed (see `LICENSE`). This file lists the notices that the licences of incorporated material
require, and the licences of the tools ForgeReels runs. Tools and skills are installed from their own sources by
`setup/` and are not part of this repository.

## Incorporated material (MIT)

Portions of the scripts and reference documents are derived from, or adapted from, the projects below. Each is
distributed under the MIT License, reproduced once at the end of this file, with these copyright notices:

| Project | Copyright notice | Where |
|---|---|---|
| Video Studio skill | Copyright (c) 2026 the Video Studio skill authors | parts of `forge-reels/scripts/` and `forge-reels/references/` |
| bang-motion | Copyright (c) 2026 Bang Tutorial | `forge-reels/references/visual-grammar.md` ("Video, not slides") |
| gbro-collage-broll | Copyright (c) 2026 狗哥笔记 | `forge-reels/references/collage-broll.md` (gates, visual spec, prompts) |
| ClaudeAnimationBase | Copyright (c) 2026 John Heibel | `forge-reels/references/painted-animation.md` (animation guide) |
| lemo-opuscar | Copyright (c) 2026 Lemomo (LemoLab) | directing rules in `visual-grammar.md`, `qc.md`, `sound.md`; style index in `film-styles.md` |

## Bundled fonts (SIL Open Font License 1.1)

Inter, Mukta, Noto Sans Devanagari (`forge-reels/assets/fonts/`) and Archivo, IBM Plex Mono, Instrument Serif
(`forge-reels/templates/screen-walkthrough/assets/fonts/`). Each font's licence file sits beside it and must stay
with it.

## Tools and models ForgeReels runs (not bundled)

| Tool / model | Licence |
|---|---|
| HyperFrames CLI and skills (heygen-com/hyperframes) | Apache 2.0 |
| Motion skills: charlie947/motion-graphics-skills, Barty-Bart/motion-graphics | MIT |
| GSAP skills (greensock/gsap-skills), GSAP | GSAP standard licence |
| Kokoro-82M, kokoro-onnx | Apache 2.0, MIT |
| Pocket TTS (kyutai-labs/pocket-tts) | MIT code, CC BY 4.0 weights; built-in voices per `forge-reels/references/voice.md` |
| VoxCPM2 (OpenBMB), mlx-audio | Apache 2.0, MIT |
| Parakeet TDT 0.6B v3 (NVIDIA) | CC BY 4.0 |
| wav2vec2-large-xlsr-53 English / Dutch (jonatasgrosman) | Apache 2.0 |
| faster-whisper, whisper.cpp | MIT |
| Rhubarb Lip Sync | MIT |
| MediaPipe and its models | Apache 2.0 |
| earshot | MIT |
| PyTorch, torchaudio, transformers | BSD-3, BSD-2, Apache 2.0 |
| ffmpeg | LGPL/GPL (installed by Homebrew) |
| Sampled instruments used by `scripts/score.py`: VSCO 2 CE, VCSL, FreePats (CC0); Salamander Grand Piano V3 (CC BY 3.0); MuldjordKit (CC BY 4.0) | credit lines are written to `CREDITS_music.txt` when a CC BY instrument is used |

## MIT License (for the incorporated material above)

```
Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```
