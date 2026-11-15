#!/usr/bin/env python3
"""Build a visual explainer from its project folder, voice first: one command, every gate in order.

  python -I build_explainer.py --project <dir> [--engine kokoro|pocket|voxcpm] [--voice V] [--lang en|nl]
                               [--render] [--frames] [--skip-voice]

<dir> holds what you write (see references/visual-explainer.md and examples/):
  script.txt          one spoken line per row (optional "[speed=1.1] " prefix); say.json for respellings
  scene.json          the one continuous world: components, positions, theme, camera start
  visual_plan.json    every visual event tied to a spoken word
  facts.md            a source for every claim and number (number_check.py reads it)
Steps: build_vo -> vo_check -> words --align -> visual_plan -> assemble index.html -> semantic_sync
       [-> HyperFrames draft render -> semantic_sync --frames]. Re-run after any edit; unchanged voice lines are reused.
"""
import argparse
import json
import pathlib
import shutil
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
SKILL = HERE.parents[1]
LIB = SKILL / "assets" / "scene-library"
sys.path.insert(0, str(SKILL / "scripts"))
import _paths  # noqa: E402


def run(name, cmd, cwd=None):
    print(f"\n==> {name}", flush=True)
    r = subprocess.run(cmd, cwd=cwd)
    if r.returncode != 0:
        sys.exit(f"STOP at {name} (exit {r.returncode}): fix the reported problem and run this again")


def py(script, *args):
    return [sys.executable, "-I", str(script), *args]


def assemble(pj):
    """Copy the runtime + font into <project>/fr/ and write index.html with the real durations."""
    fr = pj / "fr"
    (fr / "fonts").mkdir(parents=True, exist_ok=True)
    for f in ("core.js", "renderer.js", "styles.css"):
        shutil.copy2(LIB / f, fr / f)
    shutil.copy2(SKILL / "assets" / "fonts" / "InterVariable.woff2", fr / "fonts" / "InterVariable.woff2")
    data = json.loads((pj / "assets" / "events.js").read_text(encoding="utf-8").split("=", 1)[1].rstrip().rstrip(";"))
    vo = json.loads((pj / "vo" / "starts.json").read_text(encoding="utf-8"))["total"]
    html = (SKILL / "templates" / "explainer" / "index.html").read_text(encoding="utf-8")
    html = html.replace("{{DURATION}}", f"{data['duration']:.2f}").replace("{{VO_DURATION}}", f"{vo:.2f}")
    (pj / "index.html").write_text(html, encoding="utf-8")
    if not (pj / "hyperframes.json").exists():
        shutil.copy2(SKILL / "templates" / "explainer" / "hyperframes.json", pj / "hyperframes.json")
    print(f"assembled {pj / 'index.html'} ({data['duration']:.2f} s)")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--project", required=True)
    ap.add_argument("--engine", default="kokoro")
    ap.add_argument("--voice")
    ap.add_argument("--lang", default="en")
    ap.add_argument("--render", action="store_true", help="draft render to <project>/out/<name>.mp4")
    ap.add_argument("--frames", action="store_true", help="after the render: before/after frames of every event")
    ap.add_argument("--skip-voice", action="store_true", help="reuse vo/ as it is (no TTS, no voice check)")
    a = ap.parse_args()
    pj = pathlib.Path(a.project).resolve()
    if not a.skip_voice:
        vo = ["--lines", str(pj / "script.txt"), "--out", str(pj / "vo"), "--engine", a.engine, "--lang", a.lang]
        vo += ["--voice", a.voice] if a.voice else []
        vo += ["--say", str(pj / "say.json")] if (pj / "say.json").exists() else []
        run("voice", py(HERE / "build_vo.py", *vo))
        asr = ["--engine", "parakeet"] if pathlib.Path(_paths.voxcpm_python()).exists() else []   # more accurate
        run("voice = script", py(SKILL / "scripts" / "vo_check.py", "--vo", str(pj / "vo"), "--language", a.lang, *asr))
    run("word timing", py(HERE / "words.py", "--vo", str(pj / "vo"), "--align", "--language", a.lang))
    run("visual plan", py(HERE / "visual_plan.py", "--project", str(pj)))
    print("\n==> assemble")
    assemble(pj)
    run("semantic sync", py(HERE / "semantic_sync.py", "--project", str(pj)))
    if a.render:
        out = pj / "out" / f"{pj.name}.mp4"
        out.parent.mkdir(exist_ok=True)
        run("draft render", ["npx", "hyperframes", "render", "--quality", "draft", "--workers", "2", "--output", str(out)],
            cwd=pj)
        if a.frames:
            run("semantic sync (frames)", py(HERE / "semantic_sync.py", "--project", str(pj), "--frames", str(out)))
        final = _paths.output_dir() / out.name                       # the workspace's output/ folder
        shutil.copy2(out, final)
        print(f"\nDONE: {final}  (draft and QC sheets in {out.parent})")


if __name__ == "__main__":
    main()
