#!/usr/bin/env python3
"""Semantic sync gate: does every animation happen ON its word, and does it visibly change the picture?

  python -I semantic_sync.py --project <explainer project> [--frames out/draft.mp4] [--fps 30]

Static (always):
  - every visual_plan.json event resolves to its spoken word (visual_plan.resolve: word, action, object);
  - assets/events.js still matches the voice: an event more than 2 frames (~67 ms at 30 fps) from its word means the
    voice was re-recorded without re-running visual_plan.py -> "stale";
  - no event starts after the voice ends;
  - warnings: a spoken line with no visual event (a sentence the picture ignores), camera moves that start before
    the previous one has landed.
Frames (--frames, after a render): one frame just before and one just after each event; an event whose before and
after frames are (nearly) identical changes nothing a viewer can see -> error. Writes <project>/out/sync_sheet.jpg
(before | after, labelled with the word) for a visual review: does the picture show what the word says?
Exit 1 on any error.
"""
import argparse
import json
import pathlib
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import visual_plan  # noqa: E402

FRAMES_TOLERANCE = 2
MIN_CHANGE = 0.6           # mean absolute grey-level change (0-255) on a 270x480 frame; a caption alone gives ~1-3


def load_events_js(pj):
    raw = (pj / "assets" / "events.js").read_text(encoding="utf-8")
    return json.loads(raw.split("=", 1)[1].rstrip().rstrip(";"))


def check_static(pj, fps=30):
    pj = pathlib.Path(pj)
    plan = json.loads((pj / "visual_plan.json").read_text(encoding="utf-8"))
    words = json.loads((pj / "vo" / "words.json").read_text(encoding="utf-8"))
    parts, dur = visual_plan.runtime_info(pj / "scene.json")
    fresh, errors = visual_plan.resolve(plan, words, parts, dur)
    warnings, rows = [], []
    built = load_events_js(pj)["events"]
    tol = FRAMES_TOLERANCE / fps
    if not errors:
        if len(built) != len(fresh):
            errors.append(f"stale: events.js has {len(built)} events, the plan {len(fresh)}: re-run visual_plan.py")
        for f, b in zip(fresh, built):
            off = b["t"] - f["t"]
            rows.append((f, off))
            if (b["action"], b["object"]) != (f["action"], f["object"]) or abs(off) > tol:
                errors.append(f"stale: {f['action']} {f['object']} plays at {b['t']:.2f}s but '{f['word']}' is spoken at "
                              f"{f['t']:.2f}s ({off * 1000:+.0f} ms): re-run visual_plan.py")
    vo_end = json.loads((pj / "vo" / "starts.json").read_text(encoding="utf-8"))["total"]
    for e in fresh:
        if e["t"] > vo_end:
            errors.append(f"{e['action']} {e['object']} at {e['t']:.2f}s starts after the voice ends ({vo_end:.2f}s)")
    covered = {e["line"] for e in fresh}
    for line in sorted({w["line"] for w in words} - covered):
        text = " ".join(w["text"] for w in words if w["line"] == line)
        warnings.append(f"line {line} has no visual event: \"{text}\"")
    cam = [e for e in fresh if e["action"] in ("focus", "wide")]
    for a, b in zip(cam, cam[1:]):
        if b["t"] < a["t"] + a["dur"]:
            warnings.append(f"camera: {b['action']} on '{b['word']}' starts before the {a['action']} on '{a['word']}' lands")
    return errors, warnings, rows


def grab(mp4, t, w=270, h=480):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", f"{max(t, 0):.3f}", "-i", str(mp4), "-frames:v", "1",
                          "-vf", f"scale={w}:{h},format=gray", "-f", "rawvideo", "-"], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(h, w)


def frame_diff(a, b):
    return float(np.abs(a.astype(np.int16) - b.astype(np.int16)).mean())


def check_frames(events, mp4, out_dir):
    """-> (errors, sheet path). Before = 0.1 s before the event, after = 0.15 s after it ends."""
    errors, tiles = [], []
    for e in events:
        before, after = grab(mp4, e["t"] - 0.1), grab(mp4, e["t"] + e["dur"] + 0.15)
        d = frame_diff(before, after)
        label = f"{e['t']:.2f}s '{e['word']}' {e['action']} {e['object'] or 'all'}  change {d:.1f}"
        if d < MIN_CHANGE:
            errors.append(f"{e['action']} {e['object']} on '{e['word']}' at {e['t']:.2f}s changes nothing visible "
                          f"(change {d:.2f} < {MIN_CHANGE})")
        tiles.append((before, after, label, d < MIN_CHANGE))
    w, h, lab = 270, 480, 34
    sheet = Image.new("RGB", (2 * w + 30, max(1, len(tiles)) * (h + lab + 10)), "white")
    dr = ImageDraw.Draw(sheet)
    for k, (b, a, label, bad) in enumerate(tiles):
        y = k * (h + lab + 10)
        dr.text((8, y + 8), label, fill=(200, 30, 30) if bad else (20, 20, 20))
        sheet.paste(Image.fromarray(b).convert("RGB"), (10, y + lab))
        sheet.paste(Image.fromarray(a).convert("RGB"), (20 + w, y + lab))
    path = pathlib.Path(out_dir) / "sync_sheet.jpg"
    path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(path, quality=85)
    return errors, path


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--project", required=True)
    ap.add_argument("--frames", help="rendered MP4 to check event by event")
    ap.add_argument("--fps", type=int, default=30)
    a = ap.parse_args()
    pj = pathlib.Path(a.project)
    errors, warnings, rows = check_static(pj, a.fps)
    for f, off in rows:
        print(f"{f['t']:6.2f}  {f['action']:9} {str(f['object']):24} '{f['word']}'  {off * 1000:+4.0f} ms")
    if a.frames and not errors:
        ferr, sheet = check_frames(load_events_js(pj)["events"], a.frames, pj / "out")
        errors += ferr
        print(f"frames: {sheet}  (READ it: does each 'after' show what its word says?)")
    for w in warnings:
        print("warning:", w)
    for e in errors:
        print("ERROR:", e)
    print("semantic sync:", "FAIL" if errors else "pass")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
