#!/usr/bin/env python3
"""Gate: is what the voice SAID what the script says? Run it after build_vo.py, before anyone listens.

  python -I vo_check.py --vo vo [--language nl] [--engine parakeet] [--max-wer 0.08]

Reads <vo>/starts.json ("lines") and <vo>/lines/NN.wav, reads every line back with ASR (scripts/asr.py) and
prints one row per line: `NN ok|FAIL wer=0.00 last=ok|MISSING  heard: ...`. Exit 1 when a line's word error
rate is above --max-wer, when the line's last script word is not heard in its last 1.5 s, or when the take does
not end in silence (cut inside a word): a take can stop early or clip its last word with exit 0 and no error
(references/voice.md). It checks against starts.json "spoken" (the text after --say respellings).
Numbers the ASR writes as digits ("150", "200 .000") count as matching the spelled-out script word, so a
Dutch number line is not failed for formatting. Parakeet (Apple Silicon) is faster and more accurate than
the default Whisper small on Dutch; use --engine parakeet when setup/setup-voxcpm.sh ran.
"""
import argparse
import json
import pathlib
import re
import sys
import unicodedata

import soundfile as sf

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import asr  # noqa: E402

TAIL = 1.5
NUM = "#"                                     # a token the ASR wrote with digits ("96", "10", "000")
SPAN = 4                                      # one digit token may stand for up to 4 spoken words


def words_of(text):
    return re.findall(r"[\w']+", text.lower().replace("\u2019", "'"))


# number words (EN + NL) built from these parts: "ninety", "vijfentwintigste", "tweehonderdduizend", "drieënhalf"
_CORE = ("zero|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thir|fif|eigh|twenty|thirty|forty|"
         "fifty|sixty|seventy|eighty|ninety|hundred|thousand|million|billion|half|nul|een|twee|drie|vier|vijf|zes|"
         "zeven|acht|negen|tien|elf|twaalf|der|veer|twin|dertig|veertig|vijftig|zestig|zeventig|tachtig|negentig|"
         "honderd|duizend|miljoen|miljard|anderhalf")
_PART = rf"(?:{_CORE}|teen|ty|tig|th|en|ste|de)"
_NUMBER = re.compile(rf"{_PART}*(?:{_CORE}){_PART}*")
CONNECT = {"and", "en", "point", "komma", "percent", "procent"}   # said inside a number: "zes komma vijf procent"


def is_number_word(w):
    w = unicodedata.normalize("NFKD", w)
    w = "".join(c for c in w if not unicodedata.combining(c))       # drieën -> drieen, één -> een
    return w in CONNECT or bool(_NUMBER.fullmatch(w))


def heard_tokens(text):
    return [NUM if any(c.isdigit() for c in w) else w for w in words_of(text)]


def spoken_wer(script, heard):
    """Word error rate of `heard` against `script`. A digit token on either side ("96", "2026", "000") freely
    covers 0..SPAN NUMBER words on the other side: "96" = "ninety-six", "200 .000" = "tweehonderdduizend",
    "3 ,5" = "drieënhalf", "10, 2, and 5" = "ten, two, and five". It never covers an ordinary word, so a clipped
    "for 7" still misses "days". Two heard words that join to one script word count as that word
    ("daar tussen" = "daartussen")."""
    r, h = heard_tokens(script), heard_tokens(heard)
    if not r:
        return 0.0 if not h else 1.0
    INF = float("inf")
    d = [[INF] * (len(h) + 1) for _ in range(len(r) + 1)]
    d[0][0] = 0
    for i in range(len(r) + 1):
        for j in range(len(h) + 1):
            if i == j == 0:
                continue
            best = INF
            if i:
                best = min(best, d[i - 1][j] + 1)                           # word not heard
            if j:
                best = min(best, d[i][j - 1] + 1)                           # extra word heard
            if i and j:
                best = min(best, d[i - 1][j - 1] + (r[i - 1] != h[j - 1]))
            if i and j > 1 and h[j - 2] + h[j - 1] == r[i - 1]:
                best = min(best, d[i - 1][j - 2])
            if j and h[j - 1] == NUM:                                        # heard digits cover script number words
                k = 0
                while True:
                    best = min(best, d[i - k][j - 1])
                    if k == SPAN or k == i or not is_number_word(r[i - k - 1]):
                        break
                    k += 1
            if i and r[i - 1] == NUM:                                        # script digits cover heard number words
                k = 0
                while True:
                    best = min(best, d[i - 1][j - k])
                    if k == SPAN or k == j or not is_number_word(h[j - k - 1]):
                        break
                    k += 1
            d[i][j] = best
    return round(d[len(r)][len(h)] / len(r), 4)


def last_word_missing(script, heard, dur):
    """True when the script's last word is not among the last 3 heard words ending in the clip's last TAIL s
    (a split compound counts; digits stand for a number word and the other way round)."""
    want = (heard_tokens(script)[-1:] or [""])[0]
    tail = [t for w in heard if w["end"] >= dur - TAIL for t in heard_tokens(w["text"])][-3:]
    joined = ["".join(tail[k:]) for k in range(len(tail) - 1)]
    for t in tail + joined:
        if t == want or (t == NUM and is_number_word(want)) or (want == NUM and (t == NUM or is_number_word(t))):
            return False
    return True


def ends_in_silence(y, sr, win=0.03, floor=0.01):
    """A clean take ends in silence (measured on the M4: >= 0.07 s for Kokoro, Pocket and VoxCPM). Sound in the
    last `win` s means the take was cut inside a word, which ASR often still "hears" as complete."""
    y = y.mean(1) if y.ndim > 1 else y
    return float(abs(y[-max(1, int(win * sr)):]).max(initial=0.0)) < floor


def script_lines(S):
    """What the voice was given: starts.json "spoken" (after --say respellings), else the caption lines."""
    return S.get("spoken") or S["lines"]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--vo", required=True)
    ap.add_argument("--language", help="default: starts.json \"lang\", else en")
    ap.add_argument("--engine", default="faster-whisper", choices=asr.ENGINES)
    ap.add_argument("--model")
    ap.add_argument("--max-wer", type=float, default=0.08)
    a = ap.parse_args()
    vo = pathlib.Path(a.vo)
    S = json.loads((vo / "starts.json").read_text(encoding="utf-8"))
    lines = script_lines(S)
    lang = asr.language_for(a.language, S)
    wavs = [vo / "lines" / f"{i:02d}.wav" for i in range(1, len(lines) + 1)]
    heard = asr.transcribe_many(wavs, a.engine, a.model, lang)
    bad = 0
    for i, (text, wav, h) in enumerate(zip(lines, wavs, heard), 1):
        said = " ".join(w["text"] for w in h)
        e = spoken_wer(text, said)
        y, sr = sf.read(str(wav), dtype="float32")
        missing = last_word_missing(text, h, len(y) / sr)
        clipped = not ends_in_silence(y, sr)
        ok = e <= a.max_wer and not missing and not clipped
        bad += not ok
        print(f"{i:02d} {'ok  ' if ok else 'FAIL'} wer={e:.2f} last={'MISSING' if missing else 'ok'} "
              f"end={'CLIPPED' if clipped else 'ok'}  heard: {said}")
    print(f"{len(lines) - bad}/{len(lines)} lines pass" + ("" if not bad else ": regenerate the FAIL lines "
                                                        "(build_vo.py --only N) or rewrite them"))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
