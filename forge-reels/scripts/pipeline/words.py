#!/usr/bin/env python3
"""Word timings for the whole voice-over, per line, shifted by each line's start in vo.wav.

  python -I words.py --vo vo --align [--language nl]                         (recommended: script words, exact times)
  python -I words.py --vo vo [--engine faster-whisper|parakeet|hyperframes] [--model small.en] [--language hi]
                     [--fix fixes.json]

--align: every SCRIPT word (starts.json "lines", as the captions spell them) gets its time from forced alignment
         (scripts/asr.py, Apache 2.0 wav2vec2 per language: en, nl). On a Mac M4 its line starts were ~0.025 s off,
         against ~0.24 s for Whisper on Dutch Pocket voices, and Whisper's misspellings cannot reach the captions.
         Words with nothing to align (digits such as "30.000") get the gap between their neighbours and
         "guessed": true. Indexes in words.json are then script-word indexes, stable across re-records.
default: what an ASR engine HEARD, with its own spellings (fixes.json maps them: {"lack": "lakh"}).
         faster-whisper (venv), parakeet (Parakeet v3 via mlx-audio, setup/setup-voxcpm.sh) or hyperframes
         (`npx hyperframes transcribe`, needs whisper.cpp). Whisper times can run ~0.4 s late after a pause.

Needs <vo>/lines/NN.wav and <vo>/starts.json from build_vo.py. Writes <vo>/tr/NN/transcript.json (or
aligned.json with --align), reused while the audio and settings are unchanged, and <vo>/words.json
[{line, i, text, start, end, guessed?}].
"""
import argparse
import json
import pathlib
import subprocess
import sys

import numpy as np
import soundfile as sf

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import _paths  # noqa: E402
import asr  # noqa: E402
import vo_cache  # noqa: E402

TRIM = 0.01


def faster_whisper_words(wav, model, language):
    """Kept for callers that import it from here; see asr.transcribe."""
    return asr.transcribe(wav, "faster-whisper", model, language)


def trim_offset(wav):
    y, sr = sf.read(str(wav), dtype="float32")
    y = y.mean(1) if y.ndim > 1 else y
    nz = np.flatnonzero(np.abs(y) > TRIM)
    return max(0, nz[0] - int(0.03 * sr)) / sr                     # same trim as build_vo.py


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--vo", required=True)
    ap.add_argument("--fix")
    ap.add_argument("--align", action="store_true", help="times from forced alignment of the script lines")
    ap.add_argument("--model", default="small.en")
    ap.add_argument("--language", help="e.g. nl, hi; default: starts.json \"lang\", else en for *.en models and --align")
    ap.add_argument("--engine", choices=["faster-whisper", "parakeet", "hyperframes"], default="faster-whisper")
    a = ap.parse_args()
    vo = pathlib.Path(a.vo); S = json.loads((vo / "starts.json").read_text(encoding="utf-8"))
    # --language, else the language build_vo.py wrote into starts.json, else the old defaults
    lang = (asr.language_for(a.language, S) if a.language or S.get("lang") else
            ("en" if a.model.endswith(".en") or a.align else None))
    if a.engine == "faster-whisper" and lang and lang != "en" and a.model.endswith(".en"):
        a.model = a.model[:-3]                                    # small.en cannot hear Dutch
    fix = json.loads(pathlib.Path(a.fix).read_text(encoding="utf-8")) if a.fix else {}
    n = len(S["starts"])
    wavs = [vo / "lines" / f"{i:02d}.wav" for i in range(1, n + 1)]
    dirs = [vo / "tr" / f"{i:02d}" for i in range(1, n + 1)]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
    if a.align:
        texts = S.get("lines") or sys.exit("--align needs the line texts in starts.json (re-run build_vo.py)")
        files = [d / "aligned.json" for d in dirs]
        keys = [vo_cache.key(audio=vo_cache.file_hash(w), text=t, aligner=asr.ALIGN_MODELS.get(lang), language=lang)
                for w, t in zip(wavs, texts)]
        for w, t, f, k in zip(wavs, texts, files, keys):
            if not vo_cache.fresh(f, k):
                f.write_text(json.dumps(asr.align(w, asr.script_words(t), lang), ensure_ascii=False), encoding="utf-8")
                vo_cache.stamp(f, k)
    else:
        files = [d / "transcript.json" for d in dirs]
        keys = [vo_cache.key(audio=vo_cache.file_hash(w), engine=a.engine, model=a.model, language=lang) for w in wavs]
        stale = [j for j in range(n) if not vo_cache.fresh(files[j], keys[j])]
        if stale and a.engine == "hyperframes":
            for j in stale:
                (dirs[j] / "line.wav").write_bytes(wavs[j].read_bytes())
                cmd = [_paths.npx(), "hyperframes", "transcribe", "line.wav", "--model", a.model, "--json"]
                subprocess.run(cmd + (["--language", lang] if lang else []), cwd=dirs[j], capture_output=True,
                               check=True)
                vo_cache.stamp(files[j], keys[j])
        elif stale:
            heard = (asr.transcribe_many([wavs[j] for j in stale], "parakeet", None, lang) if a.engine == "parakeet"
                     else [faster_whisper_words(wavs[j], a.model, lang) for j in stale])
            for j, h in zip(stale, heard):
                files[j].write_text(json.dumps(h, ensure_ascii=False), encoding="utf-8")
                vo_cache.stamp(files[j], keys[j])
    words = []
    for i, (st, wav, f) in enumerate(zip(S["starts"], wavs, files), 1):
        off = trim_offset(wav)
        w = json.loads(f.read_text(encoding="utf-8")); w = w if isinstance(w, list) else w["words"]
        for j, x in enumerate(w):
            # ASR puts a clip's first word at 0.0 even after leading silence: no word starts before its line
            s0 = max(st, round(st + x["start"] - off, 3))
            item = {"line": i, "i": j, "text": fix.get(x["text"], x["text"]),
                    "start": s0, "end": max(s0 + 0.01, round(st + x["end"] - off, 3))}
            if x.get("guessed"):
                item["guessed"] = True
            words.append(item)
        print(f"line {i:02d}: {len(w)} words")
    (vo / "words.json").write_text(json.dumps(words, indent=0, ensure_ascii=False), encoding="utf-8")
    print(f"{len(words)} words -> {vo / 'words.json'}")


if __name__ == "__main__":
    main()
