#!/usr/bin/env python3
"""Generate one still image with the Codex CLI's built-in image generation (needs `codex` installed and logged in).

  python -I gen_image.py "flat paper-collage of a red alarm clock on cream" -o assets/img/clock.png \
         [--ref brand-frame.jpg ...] [--aspect 9:16]

Use it for what HTML/SVG cannot draw: AI plates, collage stills (references/collage-broll.md), textures,
backdrops. One image per call, ~1 min. It runs `codex exec` in the output folder with a workspace-write sandbox,
so Codex can only write there. Exit 1 when no image appears. Rights and disclosure: references/ai-broll.md.
"""
import argparse
import pathlib
import shutil
import subprocess
import sys

MAGIC = (b"\x89PNG", b"\xff\xd8\xff", b"RIFF")                    # png, jpeg, webp


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("prompt")
    ap.add_argument("-o", "--output", required=True, help="where to save the image (.png)")
    ap.add_argument("--ref", nargs="*", default=[], help="reference images (style, brand, layout)")
    ap.add_argument("--aspect", default="9:16", help="aspect ratio, e.g. 9:16 (reels), 16:9, 1:1")
    a = ap.parse_args()
    codex = shutil.which("codex")
    if not codex:
        sys.exit("codex not found: install the Codex CLI (`npm i -g @openai/codex`) and run `codex login` once")
    out = pathlib.Path(a.output).expanduser().resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.unlink(missing_ok=True)
    task = (f"Use your image generation tool to create exactly ONE image, aspect ratio {a.aspect}. "
            f"Image description: {a.prompt}. "
            + ("Use the attached image(s) as reference for style and content. " if a.ref else "")
            + f"Save it as {out} and reply with only that path.")
    cmd = [codex, "exec", "--skip-git-repo-check", "--sandbox", "workspace-write", "-C", str(out.parent)]
    for r in a.ref:
        cmd += ["-i", str(pathlib.Path(r).expanduser().resolve())]
    r = subprocess.run(cmd + [task], stdin=subprocess.DEVNULL, capture_output=True, text=True)
    if not out.exists() or not out.read_bytes()[:4].startswith(MAGIC):
        sys.exit(f"codex saved no image at {out} (exit {r.returncode}): {(r.stdout + r.stderr)[-600:]}")
    print(out)


if __name__ == "__main__":
    main()
