#!/usr/bin/env python3
"""Study a reference reel the same way every time, so a new video LEARNS from it instead of copying it.

  ~/forge-reels/venv/bin/python -I study_reference.py references/<folder>/<reel>.mp4 [--lang en]

Writes next to the video, in <reel>.study/:
  sheet.jpg        40 frames in a grid (read it: layout, type, colour, density)
  study.json       duration, cuts, light/dark scene switches, words per second, hook words, timed transcript
  transcript.txt   the voice, one timed line per sentence
and creates <folder>/NOTES.md from a template when the folder has none (fill it in: techniques, why they work,
OUR version, what we never take). The brief of every new video cites these notes (references/reference-study.md).
"""
import argparse
import json
import pathlib
import re
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

DARK, LIGHT = 80, 170          # mean grey level of a frame: below = dark scene, above = light scene


def theme_segments(lumas, step):
    """[(start_s, end_s, 'dark'|'light'|'mid')] from mean grey levels sampled every `step` s; runs are merged."""
    out = []
    for i, v in enumerate(lumas):
        kind = "dark" if v < DARK else "light" if v > LIGHT else "mid"
        if out and out[-1][2] == kind:
            out[-1][1] = round((i + 1) * step, 2)
        else:
            out.append([round(i * step, 2), round((i + 1) * step, 2), kind])
    return [tuple(s) for s in out]


def sentences(words):
    """Timed sentences from [{'word', 'start', 'end'}]."""
    out, cur = [], []
    for w in words:
        cur.append(w)
        if re.search(r"[.?!]$", w["word"].strip()):
            out.append((cur[0]["start"], " ".join(x["word"].strip() for x in cur)))
            cur = []
    if cur:
        out.append((cur[0]["start"], " ".join(x["word"].strip() for x in cur)))
    return out


def probe_duration(video):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(video)],
                       capture_output=True, text=True, check=True)
    return float(r.stdout.strip())


def has_audio(video):
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries", "stream=index", "-of", "csv=p=0",
                        str(video)], capture_output=True, text=True)
    return bool(r.stdout.strip())


def cuts(video, threshold=12):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(video), "-vf", f"scdet=threshold={threshold}", "-an",
                        "-f", "null", "-"], capture_output=True, text=True)
    return [round(float(t), 2) for t in re.findall(r"lavfi\.scd\.time: ([0-9.]+)", r.stderr)]


def lumas(video, step):
    r = subprocess.run(["ffmpeg", "-v", "error", "-i", str(video), "-vf", f"fps=1/{step},scale=32:57,format=gray",
                        "-f", "rawvideo", "-"], capture_output=True, check=True)
    n = 32 * 57
    return [sum(r.stdout[i:i + n]) / n for i in range(0, len(r.stdout) - n + 1, n)]


NOTES = """# Study notes: {folder}

Local notes (media here is not committed). Fill in per reel; `study_reference.py` made the sheet and the numbers.
Learn the WHY, then build our own version. Never copy a layout, a character, a series format, a brand or a phrase.

## {name}
- Numbers: {facts}
- Said (structure): hook -> ... -> CTA
- Shown: ...

| Technique | Where (time) | Why it works | Our own version |
|---|---|---|---|
| | | | |

Never take: their branding, characters, series name, wording, colour scheme as a whole.
"""


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("video")
    ap.add_argument("--lang", default="en")
    a = ap.parse_args()
    video = pathlib.Path(a.video).resolve()
    out = video.with_suffix(".study")
    out.mkdir(exist_ok=True)
    dur = probe_duration(video)
    step = max(1.0, dur / 40)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(video), "-vf",
                    f"fps=1/{step:.3f},scale=180:-1,tile=8x5:padding=3:color=white", "-frames:v", "1",
                    str(out / "sheet.jpg")], check=True)
    themes = theme_segments(lumas(video, 0.5), 0.5)
    words = []
    if has_audio(video):                         # silent loops (product shots) have no voice to transcribe
        wav = out / "voice.wav"
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(video), "-ac", "1", "-ar", "16000", str(wav)], check=True)
        import asr
        words = [{"word": w.get("word", w.get("text", "")), "start": w["start"], "end": w["end"]}
                 for w in asr.transcribe(str(wav), language=a.lang)]
        wav.unlink()
    sent = sentences(words)
    study = {
        "file": video.name, "duration": round(dur, 2), "cuts": cuts(video),
        "themes": themes, "theme_switches": sum(1 for x, y in zip(themes, themes[1:]) if {x[2], y[2]} == {"dark", "light"}),
        "words": len(words), "words_per_s": round(len(words) / dur, 2) if dur else 0,
        "hook_words_first_3s": " ".join(w["word"].strip() for w in words if w["start"] < 3.0),
        "sentences": [{"t": round(t, 2), "text": s} for t, s in sent],
    }
    (out / "study.json").write_text(json.dumps(study, indent=1, ensure_ascii=False), encoding="utf-8")
    (out / "transcript.txt").write_text("\n".join(f"{t:6.1f}  {s}" for t, s in sent) + "\n", encoding="utf-8")
    notes = video.parent / "NOTES.md"
    if not notes.exists():
        facts = (f"{study['duration']} s, {len(study['cuts'])} hard cuts, {study['theme_switches']} dark/light switches, "
                 f"{study['words_per_s']} words/s")
        notes.write_text(NOTES.format(folder=video.parent.name, name=video.name, facts=facts), encoding="utf-8")
    print(f"{video.name}: {study['duration']} s, {len(study['cuts'])} cuts, {study['theme_switches']} theme switches, "
          f"{study['words_per_s']} words/s -> {out}/ (sheet.jpg, study.json, transcript.txt)")
    print(f"hook (first 3 s): {study['hook_words_first_3s']}")


if __name__ == "__main__":
    main()
