#!/usr/bin/env python3
"""Visual plan -> timed events: every animation is tied to a SPOKEN WORD, never to a hand-typed second.

  python -I visual_plan.py --project <explainer project>      (reads scene.json, visual_plan.json, vo/words.json)

visual_plan.json:
  {"events": [
     {"word_ref": {"line": 2, "index": 3, "expected": "glass"}, "action": "reveal", "object": "phone.glass"},
     {"word_ref": {"line": 2, "expected": "grid"},              "action": "draw",   "object": "phone.rows"},
     {"word_ref": {"expected": "charge", "nth": 1},             "action": "pulse",  "object": "phone.field",
      "at": "start", "offset": -0.05, "dur": 0.8, "args": {"repeat": 2}},
     {"word_ref": {"line": 5, "expected": "screen"},            "action": "focus",  "object": "phone.screen"}]}
  word_ref: line (1-based) + index (0-based script word, as in words.json from `words.py --align`) + expected; or
            expected (+ line, + nth) to find it. A mismatch is an error, so a re-recorded voice can never silently
            move an animation onto the wrong word.
  at: "start" (default) or "end" of the word. offset: seconds (a small negative offset anticipates the word).
  Actions and default lengths: assets/scene-library/core.js (FR.DUR). Objects: FR.parts(scene).

Writes <project>/assets/events.js (window.__FR = {scene, events, captions, duration}) and prints every event.
Re-run it after every re-voice: the times follow the words. Exit 1 on any error.
"""
import argparse
import difflib
import json
import pathlib
import re
import subprocess
import sys
import unicodedata

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from build_timing import caption_groups  # noqa: E402

CORE = pathlib.Path(__file__).resolve().parents[2] / "assets" / "scene-library" / "core.js"
TAIL = 1.2                                       # seconds of picture after the last word


def norm(word):
    w = unicodedata.normalize("NFKD", word.lower())
    return re.sub(r"[^\w]", "", "".join(c for c in w if not unicodedata.combining(c)))


def runtime_info(scene_path):
    """(parts, default durations) from the JS runtime itself, so Python and the browser never disagree."""
    js = ("const FR=require(process.argv[1]);const s=JSON.parse(require('fs').readFileSync(process.argv[2],'utf8'));"
          "console.log(JSON.stringify({parts:FR.parts(s),dur:FR.DUR}))")
    r = subprocess.run(["node", "-e", js, str(CORE), str(scene_path)], capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit(f"scene.json rejected by the runtime: {r.stderr.strip().splitlines()[-1]}")
    d = json.loads(r.stdout)
    return d["parts"], d["dur"]


def find_word(ref, words):
    """-> (word, error). index refs must match `expected`; otherwise search by expected (+ line, + nth)."""
    want = norm(ref.get("expected", ""))
    line = ref.get("line")
    if "index" in ref:
        hit = next((w for w in words if w["line"] == line and w["i"] == ref["index"]), None)
        if hit is None:
            return None, f"no word at line {line} index {ref['index']}"
        if want and norm(hit["text"]) != want:
            alt = [w["i"] for w in words if w["line"] == line and norm(w["text"]) == want]
            hint = f"; '{ref['expected']}' is at index {alt[0]}" if alt else ""
            return None, f"line {line} index {ref['index']} is '{hit['text']}', not '{ref['expected']}'{hint}"
        return hit, None
    hits = [w for w in words if norm(w["text"]) == want and (line is None or w["line"] == line)]
    k = ref.get("nth", 1)
    if len(hits) < k:
        where = f" in line {line}" if line else ""
        return None, f"'{ref.get('expected')}' (occurrence {k}) is not spoken{where}"
    return hits[k - 1], None


def resolve(plan, words, parts, dur):
    """Events with absolute times. -> (events, errors)."""
    out, errors = [], []
    for n, e in enumerate(plan.get("events", []), 1):
        tag = f"event {n} ({e.get('action')} {e.get('object')})"
        action, obj, args = e.get("action"), e.get("object"), e.get("args") or {}
        if action not in dur:
            errors.append(f"{tag}: unknown action '{action}'; use one of {', '.join(sorted(dur))}")
            continue
        if isinstance(obj, list):
            if action not in ("focus", "wide"):
                errors.append(f"{tag}: only focus and wide take a list of objects (the camera frames the group)")
                continue
            bad = [o for o in obj if o not in parts]
            if bad:
                errors.append(f"{tag}: no object {', '.join(map(repr, bad))} in scene.json")
                continue
        elif action == "wide" and obj is None:
            pass
        elif obj not in parts:
            close = difflib.get_close_matches(str(obj), parts, n=3)
            errors.append(f"{tag}: no object '{obj}' in scene.json" + (f"; did you mean {', '.join(close)}?" if close else ""))
            continue
        if action == "count" and "to" not in args:
            errors.append(f"{tag}: count needs args.to (the number to land on)")
            continue
        w, err = find_word(e.get("word_ref") or {}, words)
        if err:
            errors.append(f"{tag}: {err}")
            continue
        t = (w["end"] if e.get("at") == "end" else w["start"]) + e.get("offset", 0)
        out.append({"t": round(max(0.0, t), 3), "dur": e.get("dur", dur[action]), "action": action, "object": obj,
                    "args": args, "word": w["text"], "line": w["line"], "i": w["i"]})
    return sorted(out, key=lambda x: x["t"]), errors


def caption_data(words, events):
    """Caption groups for the runtime: text + times, and key=True on every word that triggers a visual event (the
    headline captions box it, so the viewer sees which word moved the picture)."""
    keys = {(e["line"], e["i"]) for e in events}
    out = []
    for g in caption_groups(words):
        first = next(((w["line"], w["i"]) for w in g if (w["line"], w["i"]) in keys), None)   # one box per phrase
        out.append([dict({k: w[k] for k in ("text", "start", "end")}, **({"key": True} if (w["line"], w["i"]) == first else {}))
                    for w in g])
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--project", required=True)
    a = ap.parse_args()
    pj = pathlib.Path(a.project)
    scene = json.loads((pj / "scene.json").read_text(encoding="utf-8"))
    plan = json.loads((pj / "visual_plan.json").read_text(encoding="utf-8"))
    words = json.loads((pj / "vo" / "words.json").read_text(encoding="utf-8"))
    parts, dur = runtime_info(pj / "scene.json")
    events, errors = resolve(plan, words, parts, dur)
    for e in events:
        print(f"{e['t']:6.2f}  {e['action']:9} {str(e['object']):24} on '{e['word']}' (line {e['line']}, word {e['i']})")
    if errors:
        print("\n".join(["", "PLAN ERRORS:"] + errors))
        return 1
    groups = caption_data(words, events)
    duration = round(max(w["end"] for w in words) + TAIL, 2)
    (pj / "assets").mkdir(parents=True, exist_ok=True)
    data = {"scene": scene, "events": events, "captions": groups, "duration": duration}
    (pj / "assets" / "events.js").write_text("window.__FR_DATA = " + json.dumps(data, ensure_ascii=False) + ";\n",
                                             encoding="utf-8")
    print(f"{len(events)} events, {len(groups)} caption groups, {duration} s -> {pj / 'assets' / 'events.js'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
