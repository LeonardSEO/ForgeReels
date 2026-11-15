"""Local TTS engines behind one call. The model loads ONCE per call and speaks every line.

    from tts_engines import synth
    paths = synth("kokoro", {1: "First line.", 2: "Second."}, out_dir, voice="af_heart", speed=1.0, lang=None)
    # -> {1: out_dir/01.wav, 2: out_dir/02.wav}

Engines:
  kokoro  kokoro-onnx in this process, the same model files and call as `npx hyperframes tts`
          (~/.cache/hyperframes/tts), so an approved Kokoro voice sounds the same. EN/HI/ES/FR/IT/PT/JA/ZH, no NL.
  pocket  Kyutai Pocket TTS (MIT code, CC BY 4.0 weights), CPU. EN, FR, DE, PT, IT, ES, NL.
          voice = a built-in name ("alba"; Dutch "daan"), or to clone: a reference .wav or an exported
          .safetensors voice state (cloning needs the gated kyutai/pocket-tts weights: accept + `hf auth login`).
          No speed control: speed other than 1.0 is ignored with a warning (never speed a voice up, see voice.md).
  voxcpm  VoxCPM2 through mlx-audio in its own venv (scripts/tts_worker_voxcpm.py), one subprocess per call.
"""
import importlib.util
import json
import os
import pathlib
import re
import subprocess
import sys

import numpy as np
import soundfile as sf

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import _paths  # noqa: E402

ENGINES = ("kokoro", "pocket", "voxcpm")
# part of the voice cache key (vo_cache): bump when an engine's model files change
MODEL_ID = {"kokoro": "kokoro-v1.0", "pocket": "pocket-tts-4", "voxcpm": "VoxCPM2-8bit"}
INSTALL = {
    "kokoro": "~/forge-reels/venv/bin/python -m pip install kokoro-onnx   (model: run `npx hyperframes tts hi` once)",
    "pocket": "~/forge-reels/venv/bin/python -m pip install pocket-tts",
    "voxcpm": "bash setup/setup-voxcpm.sh",
}
# Kokoro voice-id prefix -> phonemizer language (same table as hyperframes' inferLangFromVoiceId)
KOKORO_LANG = {"a": "en-us", "b": "en-gb", "e": "es", "f": "fr-fr", "h": "hi", "i": "it", "j": "ja", "p": "pt-br",
               "z": "zh"}
POCKET_LANG = {"en": "english", "nl": "dutch", "fr": "french", "de": "german", "pt": "portuguese", "it": "italian",
               "es": "spanish"}


# Pocket's built-in voice per language (pocket_tts/default_parameters.py); "daan" is its Dutch voice
POCKET_VOICE = {"nl": "daan", "it": "giovanni", "es": "lola", "de": "juergen", "pt": "rafael", "fr": "estelle"}
AUDIO = (".wav", ".mp3", ".flac", ".ogg", ".m4a")


def default_voice(engine, lang):
    if engine == "pocket":
        return POCKET_VOICE.get((lang or "en").split("-")[0], "alba")
    return {"kokoro": "af_heart", "voxcpm": "default"}.get(engine, "af_heart")


def needs_full_batch(engine, voice):
    """VoxCPM without a reference audio keeps one speaker only within one run (lines 2+ clone line 1), so a
    partial rebuild must regenerate every line."""
    return engine == "voxcpm" and not str(voice).lower().endswith(AUDIO)


class EngineMissing(SystemExit):
    """An engine that is unknown or not installed; the message says how to install it."""


def kokoro_files():
    d = pathlib.Path(os.environ.get("KOKORO_DIR") or pathlib.Path.home() / ".cache" / "hyperframes" / "tts")
    return d / "models" / "kokoro-v1.0.onnx", d / "voices" / "voices-v1.0.bin"


def kokoro_lang(voice, lang):
    """espeak language for a Kokoro voice: an explicit espeak name wins, a bare ISO code ("en", "fr") maps to the
    voice's own accent when they match, else to espeak's name for it."""
    own = KOKORO_LANG.get(voice[:1], "en-us")
    if not lang or lang in KOKORO_LANG.values():
        return lang or own
    if own.split("-")[0] == lang:
        return own
    return next((v for v in KOKORO_LANG.values() if v.split("-")[0] == lang), lang)


def pocket_language(lang):
    if not lang:
        return "english"
    return POCKET_LANG.get(lang.split("-")[0].lower(), lang)


def parse_line(raw, say):
    """One lines.txt row -> (caption text, spoken text, speed or None).
    An optional "[speed=1.1]" prefix sets this line's speed; `say` maps whole words to how the TTS should say them
    ({"AI": "A.I."}); captions keep the written words."""
    m = re.match(r"\s*\[speed=([\d.]+)\]\s*", raw)
    caption = raw[m.end():].strip() if m else raw.strip()
    spoken = caption
    for k, v in say.items():
        spoken = re.sub(rf"(?<!\w){re.escape(k)}(?!\w)", v, spoken)
    return caption, spoken, float(m.group(1)) if m else None


def _need(engine, module):
    if importlib.util.find_spec(module) is None:
        raise EngineMissing(f"TTS engine '{engine}' is not installed. Install it with:\n  {INSTALL[engine]}")


def _kokoro(lines, out, voice, speed, lang):
    _need("kokoro", "kokoro_onnx")
    model, voices = kokoro_files()
    if not model.exists():
        raise EngineMissing(f"Kokoro model missing at {model}. Install it with:\n  {INSTALL['kokoro']}")
    from kokoro_onnx import Kokoro
    k = Kokoro(str(model), str(voices))
    # shortcut: no split-and-retry for lines over Kokoro's 510-token limit (one spoken line is far shorter)
    for n, text in lines.items():
        samples, sr = k.create(text, voice=voice, speed=_speed(speed, n), lang=kokoro_lang(voice, lang))
        sf.write(out[n], samples, sr)


def _pocket(lines, out, voice, speed, lang):
    _need("pocket", "pocket_tts")
    if any(_speed(speed, n) != 1.0 for n in lines):
        print(f"[pocket] speed {speed} ignored: Pocket TTS has no speed control", file=sys.stderr)
    from pocket_tts import TTSModel
    m = TTSModel.load_model(language=pocket_language(lang))
    try:
        state = m.get_state_for_audio_prompt(voice)
    except (ValueError, FileNotFoundError) as e:
        raise SystemExit(f"Pocket voice '{voice}' could not be loaded: {e}\n"
                         f"Use a built-in voice (Dutch: daan) or, for cloning, accept the terms of the gated "
                         f"kyutai/pocket-tts weights on Hugging Face and run `hf auth login` first.") from None
    for n, text in lines.items():
        sf.write(out[n], m.generate_audio(state, text).numpy().astype(np.float32), m.sample_rate)


def _voxcpm(lines, out, voice, speed, lang):
    py = _paths.voxcpm_python()
    if not pathlib.Path(py).exists():
        raise EngineMissing(f"TTS engine 'voxcpm' is not installed. Install it with:\n  {INSTALL['voxcpm']}")
    speed = max((_speed(speed, n) for n in lines), key=lambda v: abs(v - 1.0))   # worker warns when != 1
    job = {"lines": {str(n): t for n, t in lines.items()}, "out": {str(n): str(p) for n, p in out.items()},
           "voice": voice, "speed": speed, "lang": lang}
    worker = pathlib.Path(__file__).resolve().parent / "tts_worker_voxcpm.py"
    r = subprocess.run([py, "-I", str(worker)], input=json.dumps(job), text=True, capture_output=True)
    if r.returncode != 0:
        sys.exit(f"voxcpm worker failed: {(r.stdout + r.stderr)[-800:]}")


def _speed(speed, n):
    return speed.get(n, 1.0) if isinstance(speed, dict) else speed


def synth(engine, lines, out_dir, voice, speed, lang):
    """Speak {line_number: text} into out_dir/NN.wav with one loaded model. Returns {line_number: path}.
    speed: one float, or {line_number: speed} for per-line speeds (Kokoro only)."""
    run = {"kokoro": _kokoro, "pocket": _pocket, "voxcpm": _voxcpm}.get(engine)
    if run is None:
        raise EngineMissing(f"unknown TTS engine '{engine}'; choose one of {', '.join(ENGINES)}")
    out_dir = pathlib.Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out = {n: out_dir / f"{n:02d}.wav" for n in lines}
    if lines:
        run(lines, out, voice, speed, lang)
    missing = [n for n, p in out.items() if not p.exists()]
    if missing:
        sys.exit(f"TTS ({engine}) wrote no audio for line(s) {missing}")
    return out
