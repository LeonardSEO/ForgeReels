#!/usr/bin/env python3
"""Explainer events -> cues.json for the beat pipeline (references/sound.md): the sound lands on the same words as
the picture.

  python -I explainer_cues.py --project <explainer project> [--anchors Liquid Real] [--min-gap 0.3]

Reads <project>/assets/events.js (visual_plan.py) and writes <project>/sound/cues.json:
  focus / wide -> whoosh.short   reveal / scan of a whole component -> land.light   strike -> hit
  type -> text   highlight / pulse -> tick   count -> tick   (play, draw, flow and parts of components: no sound)
--anchors: spoken words that must also land on a beat (the hook word, the turn); the grid is fitted to them
(lock "anchor"); every other cue follows its word (lock "word"). Cues closer than --min-gap are thinned (first wins)
so the reel never chatters.
Then: beatgrid.py --fit-bpm 90 130 --cues sound/cues.json, score.py, beatmix.py (references/sound.md).
"""
import argparse
import json
import pathlib

ROLE = {"focus": "whoosh.short", "wide": "whoosh.short", "reveal": "land.light", "scan": "whoosh.short",
        "strike": "hit", "type": "text", "highlight": "tick", "pulse": "tick", "count": "tick"}
WHOLE_ONLY = {"reveal", "scan"}                         # a part appearing inside a component makes no sound of its own


def norm(w):
    return "".join(c for c in w.lower() if c.isalnum())


def cues_from_events(events, anchors, min_gap=0.3):
    want = {norm(a) for a in anchors}
    out = []
    for e in sorted(events, key=lambda e: e["t"]):
        role = ROLE.get(e["action"])
        obj = e.get("object")
        if not role or (e["action"] in WHOLE_ONLY and isinstance(obj, str) and "." in obj):
            continue
        if out and e["t"] - out[-1]["t"] < min_gap:
            continue
        out.append({"t": round(e["t"], 3), "type": e["action"], "desc": f"{e['action']} {obj} on '{e.get('word', '')}'",
                    "lock": "anchor" if norm(e.get("word", "")) in want else "word", "role": role})
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--project", required=True)
    ap.add_argument("--anchors", nargs="*", default=[])
    ap.add_argument("--min-gap", type=float, default=0.3)
    a = ap.parse_args()
    pj = pathlib.Path(a.project)
    raw = (pj / "assets" / "events.js").read_text(encoding="utf-8")
    events = json.loads(raw.split("=", 1)[1].rstrip().rstrip(";"))["events"]
    cues = cues_from_events(events, a.anchors, a.min_gap)
    (pj / "sound").mkdir(exist_ok=True)
    (pj / "sound" / "cues.json").write_text(json.dumps(cues, indent=1), encoding="utf-8")
    print(f"{len(cues)} cues ({sum(c['lock'] == 'anchor' for c in cues)} anchors) -> {pj / 'sound' / 'cues.json'}")


if __name__ == "__main__":
    main()
