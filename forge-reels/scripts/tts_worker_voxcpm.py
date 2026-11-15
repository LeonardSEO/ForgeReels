"""VoxCPM2 worker (runs in the mlx-audio venv, setup/setup-voxcpm.sh). Called by tts_engines.synth("voxcpm", ...).

stdin: {"lines": {"1": text, ...}, "out": {"1": wav_path, ...}, "voice": V, "speed": 1.0, "lang": "nl"}
  V = a reference audio (.wav/.mp3/.flac/.ogg/.m4a) -> every line clones that voice
  V = "default" or ""   -> zero-shot voice for line 1
  V = any other text    -> voice design from that description for line 1
Without a reference the model picks a new voice per line, so lines 2+ clone line 1: one speaker per run.
The model loads once, every line is written, then the process exits so its memory is freed before a render.
VoxCPM2 detects the language from the text; `lang` is not needed. Speed is not controllable here: other than 1.0
is ignored with a warning (never speed a voice up, see references/voice.md).
"""
import json
import os
import sys

MODEL = os.environ.get("VOXCPM_MODEL", "mlx-community/VoxCPM2-8bit")


def main():
    job = json.load(sys.stdin)
    import numpy as np
    import soundfile as sf
    from mlx_audio.tts.utils import load
    if float(job.get("speed", 1.0)) != 1.0:
        print(f"[voxcpm] speed {job['speed']} ignored: no speed control", file=sys.stderr)
    model = load(MODEL)
    voice = job.get("voice") or ""
    ref = voice if voice.lower().endswith((".wav", ".mp3", ".flac", ".ogg", ".m4a")) else None
    instruct = None if ref or voice in ("", "default") else voice
    for n in sorted(job["lines"], key=int):
        kw = {"ref_audio": ref} if ref else ({"instruct": instruct} if instruct else {})
        result = next(model.generate(text=job["lines"][n], **kw))
        sf.write(job["out"][n], np.array(result.audio, dtype=np.float32), model.sample_rate)
        if ref is None:
            ref = job["out"][n]                     # lines 2+ keep line 1's speaker
    return 0


if __name__ == "__main__":
    sys.exit(main())
