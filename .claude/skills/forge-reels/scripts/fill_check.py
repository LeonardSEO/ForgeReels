#!/usr/bin/env python3
"""How much of the frame do the illustrations fill? Flags shots where the subject is too small.

  ~/forge-reels/venv/bin/python -I fill_check.py out.mp4 [--floor 0.30] [--step 0.5]

Per sampled frame: the share of the picture area (below the headline captions, above the bottom UI) whose colour
differs clearly from the background (the median colour of the frame's edge). A small phone on an empty stage scores
~0.15; a close-up that fills the frame 0.5+. Exit 1 when the median is under --floor or over a third of the frames are.
"""
import argparse
import subprocess
import sys

import numpy as np

W, H = 108, 192
TOP, BOTTOM = 0.22, 0.88        # skip the headline caption band and the platform UI at the bottom


def fill_fraction(rgb, tol=22):
    """Share of the picture band whose colour differs from the edge-median background by more than tol."""
    edge = np.concatenate([rgb[:, 0], rgb[:, -1]])
    bg = np.median(edge, axis=0)
    band = rgb[int(TOP * rgb.shape[0]):int(BOTTOM * rgb.shape[0])].astype(int)
    return float((np.abs(band - bg).max(axis=2) > tol).mean())


def frames(video, step):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(video), "-vf", f"fps=1/{step},scale={W}:{H}",
                          "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True, check=True).stdout
    n = W * H * 3
    return [np.frombuffer(raw[i:i + n], np.uint8).reshape(H, W, 3) for i in range(0, len(raw) - n + 1, n)]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("video")
    ap.add_argument("--floor", type=float, default=0.30)
    ap.add_argument("--step", type=float, default=0.5)
    a = ap.parse_args()
    fills = [fill_fraction(f) for f in frames(a.video, a.step)]
    if not fills:
        sys.exit("no frames read")
    low = [(round(i * a.step, 1), round(f, 2)) for i, f in enumerate(fills) if f < a.floor]
    med = float(np.median(fills))
    print(f"fill: median {med:.2f}, min {min(fills):.2f}, {len(low)}/{len(fills)} frames under {a.floor}")
    for t, f in low:
        print(f"  {t:6.1f}s  {f:.2f}")
    ok = med >= a.floor and len(low) <= len(fills) / 3
    print("fill check: " + ("pass" if ok else "FAIL (make the subject bigger: zoom in, or a close-up component)"))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
