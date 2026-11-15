#!/usr/bin/env python3
"""Per-line TTS voice-over, assembled at MEASURED starts (concatenating lines with a fixed gap drifts).

  python -I build_vo.py --lines vo/lines.txt --out vo [--engine kokoro] [--voice af_heart] [--speed 1.0] [--lang en-us]
                        [--gap 0.4] [--gaps 0.45,0.35,...] [--only 3 5]

lines.txt: one spoken line per row (blank rows ignored), optionally prefixed "[speed=1.1] " for that line
(Kokoro; faster hooks, slower climax). --say say.json respells words for the TTS only ({"AI": "A.I."}); starts.json
"lines" keeps the caption text and "spoken" what the voice was given. Write numbers the way they must be SAID.

Writes <out>/lines/NN.wav (trimmed of silence), <out>/vo.wav and <out>/starts.json
({starts, durs, total, lines}). Feed starts.json to words.py (word timings) and to
../mouth_rhubarb.py --lines-dir <out>/lines --starts <out>/starts.json (lip-sync).
TTS = --engine kokoro (default, local, Apache 2.0) | pocket | voxcpm, see scripts/tts_engines.py. Pick voice + speed BY EAR with the user
(templates/reel-project/pick.html).
"""
import argparse
import json
import pathlib
import sys

import numpy as np
import soundfile as sf

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
import tts_engines  # noqa: E402
import vo_cache  # noqa: E402

LEAD = 0.15           # silence before the first line (s)
TRIM = 0.01           # |x| threshold for silence trimming (keep 0.03 s before, 0.08 s after the sound)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--lines", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--engine", default="kokoro", choices=tts_engines.ENGINES)
    ap.add_argument("--voice", help="kokoro voice id (default af_heart), pocket voice (default by language: daan "
                                    "for nl, else alba) or reference audio, voxcpm description or reference audio")
    ap.add_argument("--speed", type=float, default=1.0)
    ap.add_argument("--lang", default=None, help="pass e.g. hi for Hindi voices")
    ap.add_argument("--say", help='JSON {"word": "how TTS says it"}; captions keep the word')
    ap.add_argument("--gap", type=float, default=0.4, help="silence after each line (s)")
    ap.add_argument("--gaps", help="comma list overriding --gap per line")
    ap.add_argument("--only", type=int, nargs="*", help="re-generate only these line numbers (1-based); 0 = none. Default: every line whose text or voice changed")
    a = ap.parse_args()
    a.voice = a.voice or tts_engines.default_voice(a.engine, a.lang)
    say = json.loads(pathlib.Path(a.say).read_text(encoding="utf-8")) if a.say else {}
    rows = [tts_engines.parse_line(l, say) for l in pathlib.Path(a.lines).read_text(encoding="utf-8").splitlines()
            if l.strip()]
    lines = [r[0] for r in rows]                                   # caption text (starts.json "lines")
    spoken = [r[1] for r in rows]
    speeds = {i: r[2] or a.speed for i, r in enumerate(rows, 1)}
    gaps = [float(g) for g in a.gaps.split(",")] if a.gaps else [a.gap] * len(lines)
    gaps = (gaps + [a.gap] * len(lines))[:len(lines)]
    gaps[-1] = 0.0
    out = pathlib.Path(a.out); ld = out / "lines"; ld.mkdir(parents=True, exist_ok=True)
    keys = {i: vo_cache.key(engine=a.engine, model=tts_engines.MODEL_ID[a.engine], voice=a.voice, speed=speeds[i],
                            lang=a.lang, text=t) for i, t in enumerate(spoken, 1)}
    if a.only is not None:     # manual override: exactly these lines, plus any that do not exist yet
        todo = {i: spoken[i - 1] for i in keys if i in a.only or not (ld / f"{i:02d}.wav").exists()}
    else:                      # content cache: only lines whose text or voice settings changed
        todo = {i: spoken[i - 1] for i, k in keys.items() if not vo_cache.fresh(ld / f"{i:02d}.wav", k)}
    if todo and len(todo) < len(lines) and tts_engines.needs_full_batch(a.engine, a.voice):
        todo = dict(enumerate(spoken, 1))                          # one speaker per run: rebuild them all
    for i, path in tts_engines.synth(a.engine, todo, ld, a.voice, speeds, a.lang).items():
        vo_cache.stamp(path, keys[i])
    print(f"generated {len(todo)} of {len(lines)} lines ({len(lines) - len(todo)} reused)")
    clips, sr = [], None
    for i in range(len(lines)):
        y, s = sf.read(ld / f"{i + 1:02d}.wav", dtype="float32")
        y = y.mean(1) if y.ndim > 1 else y
        sr = sr or s
        nz = np.flatnonzero(np.abs(y) > TRIM)
        clips.append(y[max(0, nz[0] - int(0.03 * sr)): nz[-1] + int(0.08 * sr)])
    starts, t = [], LEAD
    for y, g in zip(clips, gaps):
        starts.append(round(t, 3)); t += len(y) / sr + g
    mix = np.zeros(int(np.ceil(t * sr)) + sr, np.float32)          # +1 s of headroom (rounding)
    for y, st in zip(clips, starts):
        k = int(round(st * sr)); mix[k:k + len(y)] += y
    sf.write(out / "vo.wav", mix[:int(np.ceil(t * sr))], sr)
    json.dump({"sr": sr, "engine": a.engine, "voice": a.voice, "speed": a.speed, "starts": starts,
               "durs": [round(len(y) / sr, 3) for y in clips], "total": round(t, 3), "lines": lines,
               "spoken": spoken, "lang": a.lang or (tts_engines.kokoro_lang(a.voice, None) if a.engine == "kokoro" else "en"),
               "speeds": [speeds[i] for i in range(1, len(lines) + 1)]},
              open(out / "starts.json", "w"), indent=1)
    for i, (st, y) in enumerate(zip(starts, clips), 1):
        print(f"{i:02d}  start {st:6.2f}  dur {len(y) / sr:5.2f}  {lines[i - 1][:60]}")
    print(f"VO total {t:.2f} s -> {out / 'vo.wav'}")


if __name__ == "__main__":
    main()
