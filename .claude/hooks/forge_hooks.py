#!/usr/bin/env python3
"""ForgeReels Claude Code hooks (registered in .claude/settings.json). Reads the hook JSON on stdin.

  forge_hooks.py post-edit      PostToolUse Write|Edit: a changed visual_plan.json / scene.json is resolved at once
                                (visual_plan.py); plan errors go straight back to Claude.
  forge_hooks.py stop           Stop: a video in output/ made in the last 12 h without a newer QC pass stamp
                                (<video>.qc-pass, written by qc_reel.py) keeps Claude from calling the video done.
  forge_hooks.py session-start  SessionStart: the newest lessons.md entry and the reels still in progress.

Stdlib only; every failure of the hook itself exits 0 so a broken hook never blocks work.
"""
import json
import os
import pathlib
import re
import subprocess
import sys
import time

ROOT = pathlib.Path(os.environ.get("CLAUDE_PROJECT_DIR") or pathlib.Path(__file__).resolve().parents[2])
SKILL = ROOT / ".claude" / "skills" / "forge-reels"
PLAN_FILES = {"visual_plan.json", "scene.json"}
RECENT_S = 12 * 3600


def python():
    venv = pathlib.Path.home() / "forge-reels" / "venv" / "bin" / "python"
    return str(venv) if venv.exists() else sys.executable


def emit(obj):
    print(json.dumps(obj))
    return 0


def post_edit(payload):
    f = (payload.get("tool_input") or {}).get("file_path") or (payload.get("tool_response") or {}).get("filePath")
    if not f:
        return 0
    p = pathlib.Path(f)
    if p.name not in PLAN_FILES:
        return 0
    try:
        json.loads(p.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        return emit({"decision": "block", "reason": f"{p.name} is not valid JSON: {e}"})
    pj = p.parent
    if not (pj / "vo" / "words.json").exists():
        return 0                                  # no voice yet: nothing to resolve the plan against
    r = subprocess.run([python(), "-I", str(SKILL / "scripts" / "pipeline" / "visual_plan.py"), "--project", str(pj)],
                       capture_output=True, text=True, timeout=110)
    if r.returncode == 0:
        return emit({"hookSpecificOutput": {"hookEventName": "PostToolUse",
                                            "additionalContext": "visual_plan.py: " + r.stdout.strip().splitlines()[-1]}})
    tail = "\n".join((r.stdout + r.stderr).strip().splitlines()[-15:])
    return emit({"decision": "block", "reason": f"visual_plan.py failed for {pj.name} after this edit:\n{tail}"})


def unchecked_renders(now=None):
    now = now or time.time()
    vids = ROOT.glob("output/*.mp4")             # finished videos; drafts in reels/*/out are not mastered yet
    out = []
    for v in vids:
        m = v.stat().st_mtime
        stamp = v.with_name(v.name + ".qc-pass")
        if now - m < RECENT_S and not (stamp.exists() and stamp.stat().st_mtime >= m):
            out.append(v)
    return sorted(out)


def stop(payload):
    if payload.get("stop_hook_active"):
        return 0                                  # already reminded once this turn: never loop
    vids = unchecked_renders()
    if not vids:
        return 0
    qc = f"~/forge-reels/venv/bin/python -I {SKILL.relative_to(ROOT)}/scripts/qc_reel.py"
    lines = [f"- {v.relative_to(ROOT)}" for v in vids]
    reason = ("These finished videos have no passing QC since they were made:\n" + "\n".join(lines) +
              f"\nBefore calling a video done, run `{qc} <video> --sheet <dir>/qc.png` (writes <video>.qc-pass on a "
              "pass), and for explainers `semantic_sync.py --project <reel> --frames <video>` and "
              "`npx hyperframes check --json` in the reel folder. If this turn was not about finishing a video, "
              "say so in one line and stop.")
    return emit({"decision": "block", "reason": reason})


def latest_lesson():
    try:
        text = (SKILL / "lessons.md").read_text(encoding="utf-8")
    except OSError:
        return ""
    m = re.search(r"^## \d{4}-\d\d-\d\d.*?(?=^## |\Z)", text, re.S | re.M)
    return m.group(0).strip() if m else ""


def session_start(_payload):
    done = {p.stem for p in ROOT.glob("output/*.mp4")}
    wip = [d.name for d in sorted(ROOT.glob("reels/*/")) if d.name.split("-", 3)[-1] not in done]
    ctx = ["ForgeReels workspace: video work starts with /forge-reels; one folder per video in reels/, "
           "finished videos in output/<slug>.mp4."]
    if wip:
        ctx.append("Reels in progress (no output yet): " + ", ".join(wip))
    lesson = latest_lesson()
    if lesson:
        ctx.append("Newest lesson (lessons.md):\n" + lesson)
    return emit({"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": "\n\n".join(ctx)}})


def main():
    try:
        payload = json.loads(sys.stdin.read() or "{}")
        return {"post-edit": post_edit, "stop": stop, "session-start": session_start}[sys.argv[1]](payload)
    except Exception as e:                        # a broken hook must never block work
        print(f"forge_hooks: {e}", file=sys.stderr)
        return 0


if __name__ == "__main__":
    sys.exit(main())
