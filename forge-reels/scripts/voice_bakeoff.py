#!/usr/bin/env python3
"""Voice bake-off: the same short scripts through every candidate engine, measured and set up for a BLIND
listening test.

  python -I voice_bakeoff.py --engines kokoro:af_heart pocket:alba pocket:refs/anna.wav voxcpm:default \
         --out ~/forge-reels/bakeoff [--scripts ../templates/bakeoff/en_hook.txt ...] [--asr-model small]

A spec is ENGINE:VOICE (VOICE may be a reference .wav to clone). Scripts are named <lang>_<name>.txt; an engine
that has no model for that language is skipped (Kokoro has no Dutch). Every take runs in its own process, one at
a time, so peak memory is that engine's alone. After all takes, Whisper reads each one back.

Writes <out>/<script>_<engine>_<voice>.wav, <out>/results.csv
(script, file, engine, voice, key, audio_s, gen_s, rtf, peak_rss_mb, wer) and <out>/pick.html with options A, B,
C... per script and no engine names, so the user judges by ear. `key` in results.csv maps a pick back.
gen_s includes loading the model; rtf = audio_s / gen_s (above 1 = faster than real time).
"""
import argparse
import csv
import json
import pathlib
import re
import string
import subprocess
import sys

import numpy as np
import soundfile as sf

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import tts_engines  # noqa: E402

DEFAULT_SCRIPTS = sorted((HERE.parent / "templates" / "bakeoff").glob("*_*.txt"))
DEFAULT_SCRIPTS = [p for p in DEFAULT_SCRIPTS if "_30s" not in p.name]    # the 30 s scripts are for bench runs
LANGS = {"kokoro": {"en", "hi", "es", "fr", "it", "pt", "ja", "zh"},
         "pocket": {"en", "nl", "fr", "de", "pt", "it", "es"},
         "voxcpm": None}                                                   # None = every script language
GAP = 0.35


def words_of(text):
    return re.findall(r"[\w']+", text.lower())


def wer(ref, hyp):
    """Word error rate on lower-cased words without punctuation (Levenshtein over words)."""
    r, h = words_of(ref), words_of(hyp)
    if not r:
        return 0.0 if not h else 1.0
    d = list(range(len(h) + 1))
    for i, rw in enumerate(r, 1):
        prev, d[0] = d[0], i
        for j, hw in enumerate(h, 1):
            prev, d[j] = d[j], min(d[j] + 1, d[j - 1] + 1, prev + (rw != hw))
    return round(d[len(h)] / len(r), 4)


def parse_spec(spec):
    engine, _, voice = spec.partition(":")
    return engine, voice


def supports(engine, lang):
    langs = LANGS.get(engine, set())
    return langs is None or lang in langs


def safe(voice):
    return re.sub(r"[^\w.-]+", "-", pathlib.Path(voice).stem if voice.endswith(".wav") else voice)


def one(engine, voice, lang, script, wav):
    """Child process: speak every line of `script`, join them with GAP s of silence into `wav`."""
    lines = [l.strip() for l in pathlib.Path(script).read_text(encoding="utf-8").splitlines() if l.strip()]
    tmp = pathlib.Path(wav).with_suffix(".lines")
    paths = tts_engines.synth(engine, dict(enumerate(lines, 1)), tmp, voice, 1.0, lang)
    parts, sr = [], None
    for n in sorted(paths):
        y, s = sf.read(str(paths[n]), dtype="float32")
        sr = sr or s
        parts += [y.mean(1) if y.ndim > 1 else y, np.zeros(int(GAP * sr), np.float32)]
    sf.write(str(wav), np.concatenate(parts[:-1]), sr)


def write_pick_page(rows, out):
    groups = []
    for script in sorted({r["script"] for r in rows}):
        opts = [[r["key"], f"Option {r['key']}", r["file"]] for r in rows if r["script"] == script]
        groups.append({"id": script, "title": script.replace("_", " "),
                       "note": "Same text, different voices. Pick the most natural one.", "opts": opts})
    page = (HERE.parent / "templates" / "reel-project" / "pick.html").read_text(encoding="utf-8")
    start = page.index("const GROUPS = [")
    end = page.index("];", start) + 2
    page = page[:start] + "const GROUPS = " + json.dumps(groups, ensure_ascii=False, indent=1) + ";" + page[end:]
    (pathlib.Path(out) / "pick.html").write_text(page, encoding="utf-8")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--engines", nargs="+", required=True, help="ENGINE:VOICE, e.g. kokoro:af_heart pocket:alba")
    ap.add_argument("--scripts", nargs="+", default=[str(p) for p in DEFAULT_SCRIPTS])
    ap.add_argument("--out", required=True)
    ap.add_argument("--asr-engine", default="faster-whisper", choices=["faster-whisper", "parakeet"])
    ap.add_argument("--asr-model", default="small")
    ap.add_argument("--one", nargs=5, metavar=("ENGINE", "VOICE", "LANG", "SCRIPT", "WAV"), help=argparse.SUPPRESS)
    a = ap.parse_args()
    if a.one:
        return one(*a.one)
    out = pathlib.Path(a.out).expanduser()
    out.mkdir(parents=True, exist_ok=True)
    rows = []
    for script in map(pathlib.Path, a.scripts):
        lang = script.stem.split("_")[0]
        for n, spec in enumerate(a.engines):
            engine, voice = parse_spec(spec)
            if not supports(engine, lang):
                print(f"skip {engine} on {script.name}: no {lang} model")
                continue
            wav = out / f"{script.stem}_{engine}_{safe(voice)}.wav"
            r = subprocess.run([sys.executable, "-I", str(HERE / "bench.py"), "--", sys.executable, "-I", __file__,
                                "--out", str(out), "--engines", spec, "--one", engine, voice, lang, str(script), str(wav)],
                               capture_output=True, text=True)
            m = json.loads(r.stdout.strip().splitlines()[-1])
            if m["exit"] != 0:
                print(f"FAIL {engine}:{voice} on {script.name}: {r.stderr[-600:]}")
                continue
            audio_s = sf.info(str(wav)).duration
            rows.append({"script": script.stem, "file": wav.name, "engine": engine, "voice": voice,
                         "audio_s": round(audio_s, 2), "gen_s": m["wall_s"], "rtf": round(audio_s / m["wall_s"], 2),
                         "peak_rss_mb": m["peak_rss_mb"], "text": script.read_text(encoding="utf-8"), "lang": lang})
            print(f"{wav.name}: {audio_s:.1f} s audio in {m['wall_s']} s, peak {m['peak_rss_mb']} MB")
    # blind keys per script, in a fixed order that does not follow the engine list
    for script in {r["script"] for r in rows}:
        mine = sorted((r for r in rows if r["script"] == script), key=lambda r: hash(r["file"]) % 997)
        for k, r in zip(string.ascii_uppercase, mine):
            r["key"] = k
    import asr                                                       # read-back after every TTS model is gone
    for r in rows:
        heard = " ".join(w["text"] for w in asr.transcribe(out / r["file"], a.asr_engine, a.asr_model, r["lang"]))
        r["wer"] = wer(r["text"], heard)
        r["heard"] = heard
    cols = ["script", "file", "engine", "voice", "key", "audio_s", "gen_s", "rtf", "peak_rss_mb", "wer", "heard"]
    with open(out / "results.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(sorted(rows, key=lambda r: (r["script"], r["key"])))
    write_pick_page(rows, out)
    print(f"{len(rows)} takes -> {out / 'results.csv'} and {out / 'pick.html'}")


if __name__ == "__main__":
    main()
