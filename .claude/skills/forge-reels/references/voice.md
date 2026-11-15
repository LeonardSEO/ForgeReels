# Voice (English, Dutch, Hindi)

## Engines (all local; `scripts/pipeline/build_vo.py --engine ...`, code in `scripts/tts_engines.py`)
Licence matters: videos are commercial. Measured on a Mac M4 16 GB (2026-11-15, `scripts/voice_bakeoff.py`);
rtf = seconds of audio per second of compute, model load included.

| Engine | Languages | Licence | M4 speed / peak | Use |
|---|---|---|---|---|
| `kokoro` (Kokoro-82M, in-process kokoro-onnx) | EN (US/GB), HI, ES, FR, IT, PT, JA, ZH. **No Dutch** | Apache 2.0 | rtf 2.5 / 0.56 GB | Default for English. Approved `af_heart` unchanged (same model files as `npx hyperframes tts`) |
| `pocket` (Kyutai Pocket TTS) | EN, NL, FR, DE, PT, IT, ES | MIT code, CC BY 4.0 weights | rtf 1.5-2.4 / 1.0 GB, CPU | Fast Dutch. Built-in Dutch voice `daan` (the default for `--lang nl`). Cloning a reference `.wav` needs the gated `kyutai/pocket-tts` weights (below). No speed control |
| `voxcpm` (VoxCPM2 2B, 8-bit MLX via mlx-audio) | 30 incl. NL, EN | Apache 2.0 code + weights | rtf 0.3-0.7 / 3.3 GB, GPU | Premium: voice design from a description, cloning, 48 kHz. Own venv: `sh setup/setup-voxcpm.sh`. Never during a render |

Which engine is the default per language is the user's pick by ear (bake-off below), recorded in the brand pack.
Until a pick exists: English `kokoro af_heart`, Dutch `pocket` with `daan` (`--engine pocket --lang nl`).

Cloud or grey-area options (only when the user asks): Gemini TTS (AI Studio key; free tier may train on input),
edge-tts (unofficial use of a consumer service), AI4Bharat Indic Parler-TTS (Indian EN/HI, gated, slow on CPU).
A human recording is still the most trusted voice for advice-style content.

## Cloning and voice licences
Free models now allow commercial cloning (Pocket TTS: MIT + CC BY 4.0 weights; VoxCPM2: Apache 2.0). The model
licence is not the voice's licence:
- Clone a real person only with their written permission for this use; keep it with the brand pack.
- Pocket built-in voices: `alba` (Alba MacKenna) and the `vctk` voices (anna, vera, fantine, charles, paul,
  eponine, azelma, george, mary, jane, michael, eve) are CC BY 4.0, so credit them; `marius`, `javert`
  (voice donations) and the `voice-zero` voices are CC0. `cosette` (Expresso) and `jean` (EARS) are
  **non-commercial: never in client work**. Source: huggingface.co/kyutai/tts-voices.
- Record the voice, its source and licence in the brand pack's `brand.md` under "Voices".
- Pocket `daan` (Dutch) is a clip from the CML-TTS dataset, CC BY 4.0: credit CML-TTS.
- Pocket cloning (a reference `.wav` as `--voice`) needs the GATED `kyutai/pocket-tts` weights: accept their terms
  on Hugging Face and run `hf auth login` once; without that only the built-in voices work. Then export the
  reference once to a `.safetensors` voice state (fast to load) and pass that path as `--voice`.

## Dutch
- Bake-off scripts: `templates/bakeoff/nl_explain.txt`, `nl_numbers.txt` (plus `en_hook.txt`).
- Whisper writes Dutch numbers as digits ("25ste", "150", "200 .000"): a word-error rate on number lines is not a
  pronunciation error. Listen to number lines; never respell a number because the read-back shows digits.
- Write numbers the way they are said ("honderdvijftig euro", "zes komma vijf procent"); captions keep digits.

## Hindi and Hinglish (from the original finance-brand work)

### Results of a real bake-off (a finance brand, Indian audience; the user's verdicts)
- Kokoro: English `af_heart` (female, American accent) GOOD, picked. Every other Kokoro English
  voice "bad". Kokoro Hindi all to be retried. Kokoro Hinglish (romanised) "fully broken".
- en-IN edge-tts voices skip Devanagari words entirely (a Hinglish line came out half
  length). Use hi-IN voices for Hinglish: they read Devanagari Hindi and Latin English words
  both correctly (verified by transcribing back: "invest", "habit", "Simple, right").
- Indian-accent English candidates: edge-tts en-IN Neerja / Prabhat; Gemini TTS (needs AI
  Studio key); Indic Parler-TTS (Apache 2.0, gated on Hugging Face: needs an HF token,
  heavy on a laptop CPU).

### Rules learned
- Kokoro Hindi reads Latin acronyms badly ("SIP" came out as "इन इस आईपी"). In Hindi
  scripts write acronyms the way they are said: एस-आई-पी, ई-एम-आई, पी-पी-एफ. Numbers as
  words when the reading is ambiguous (₹2,00,000 → "दो लाख रुपये").
- NEVER write Hinglish romanised. Hindi words in Devanagari, English words in Latin, and a
  Hindi (hi-IN) voice reads it. Romanised Hinglish broke completely in Kokoro.
- Always transcribe the TTS output back (video-analyzer `get_transcript` on an MP4 wrap)
  and compare with the script: wrong words show up immediately.
- Speed 0.95-1.1. Faster for hooks, slower for the climax line.
- Pace (48 measured reference reels): 2.6-3.3 words a second, median 2.95. A reviewer called 3.09 with tight pauses
  "too fast"; for proud or emotional stories about 2.75 w/s at the voice's natural speed, 0.2-0.46 s between
  lines. NEVER speed a voice up to hit a length: cut words. Long pauses only: `scripts/tighten_vo.py in out --max .3`
  shortens gaps over 0.3 s without touching words.
- A take can stop early or clip its last word with exit 0 and no error: transcribe the last 7 s of every take
  before anyone listens.
- Whisper traps (a finance reel): it splits numbers and acronyms ("30" ",000", "eye," "PO,"), hears "crore" as
  "core" and adds "$" to bare amounts. Build captions from the script, and check phonemes before respelling a
  word (espeak/Kokoro already say kɹɔːɹ; "karor" was worse). Never pass the script as Whisper's initial_prompt:
  it repeats the sentence past the audio.
- Acronyms as words in English scripts: "IPO", never "I.P.O." (the dots made it enunciate), but "A.I." reads right where "A I" fails: test each
  acronym by ear with a Whisper read-back. Never respell a name
  to help a voice ("Jee-oh" made it spell J-I-O): force phonemes instead (below).

## Kokoro voice blending (option for NEW voices)
kokoro-onnx can mix voice styles, which gives more options than the 54 stock voices:
```python
from kokoro_onnx import Kokoro
k = Kokoro("kokoro-v1.0.onnx", "voices-v1.0.bin")
v = 0.6 * k.get_voice_style("af_heart") + 0.4 * k.get_voice_style("af_nicole")
audio, sr = k.create(text, voice=v, speed=1.0, lang="en-us")
```
Use it in a voice bake-off (the user picks by ear), never on an approved voice: keep an approved
voice exactly as it was. Speed 0.95 sounds calmer and 1.1 punchier.

## By-ear picks
- Every tricky word (names, "lakh", acronyms) gets 3-4 spellings rendered and the USER picks by ear.
  Present them on a local HTML pick page: a player and a radio button per option, a "None of these"
  text box, and "Copy my picks". Users found this far easier than a list of file names. Template:
  `templates/reel-project/pick.html`. The same page works
  for voice speed and music.
- Kokoro af_heart: write lakh numbers in words ("forty-nine lakh"); "SIP" as written is fine.
- Whisper read-back first, to drop broken options before the user hears them.

## Voice bake-off (once per brand, per language)
1. Same 2-3 test lines (a hook, an explanation, a number-heavy line) through every candidate voice:
   `python -I scripts/voice_bakeoff.py --engines kokoro:af_heart pocket:<ref.wav> "voxcpm:<description>" --out <brand>/voice-bakeoff`.
   It writes `<script>_<engine>_<voice>.wav`, `results.csv` (speed, peak memory, Whisper read-back error) and a
   blind `pick.html` (Option A/B/C; `key` in results.csv maps a pick back).
2. The user picks by ear. Record the pick, settings (voice id, speed, lang) and licence in
   the brand pack's `brand.md` under "Voices".
3. Re-run when a new engine appears in `toolchain.md`.

Kokoro command:
`npx hyperframes tts "<text>" -v hm_omega -l hi -s 1.0 -o assets/vo/line01.wav --json`
(a `.txt` path works as input for long scripts).

## Captions from the script, not from ASR
We write the script, so caption text comes from it. Timing comes from word timestamps
(`npx hyperframes transcribe` with whisper.cpp, see `toolchain.md`) or from the per-line TTS durations
(generate one file per line and place each at its measured start).
