#!/usr/bin/env python3
"""Pace check: find the stretches where the reel sits still (2026-10-29;
rule: something on screen changes at least every second, and the first 2 s never sit still).

A talking avatar's mouth always moves, so the whole-frame difference never reads as "still". Pass the
avatar box with --mask (and the caption box too if you want captions not to count) and only the rest of
the frame is measured. A frame counts as "changed" when at least --min-px pixels of the measured area
(on a 1/4-size grey copy) differ by more than --thresh grey levels from the previous frame, or from the frame --window s back (2026-11-15: a
smooth push over dark, soft gradients changes less than 14 levels per frame and read as "still"). Counting
changed pixels, not the mean difference, is what catches a small moving coin or a ticking number: the
first version used the mean and called nearly a whole 80 s reel "still".

  python -I pace_check.py reel.mp4 [--mask x,y,w,h ...] [--max-still 1.0] [--thresh 14] [--min-px 40] [--window 0.25] [--json out.json]

Prints changes per second, every still stretch longer than --max-still, and whether the first 2 s are
clean. Exit code 0 always: a long still can be a deliberate hold (a chart under a key line); judge it.
"""
import argparse
import json

import cv2
import numpy as np


def moving_frames(grays, fps, keep, thresh=14, min_px=40, window=0.25):
    """Per frame: does the picture change? Measured against the previous frame AND the frame `window` s back, so a
    smooth camera push (under `thresh` per frame, clearly moving over a quarter second) is motion, not a still."""
    lag = max(1, round(window * fps))
    def changed(a, b):
        return int((np.abs(a - b)[keep] > thresh).sum()) >= min_px
    moving = np.array([i == 0 or changed(grays[i], grays[i - 1]) or changed(grays[i], grays[max(0, i - lag)])
                       for i in range(len(grays))], bool)
    return moving


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("video")
    ap.add_argument("--mask", action="append", default=[], help="x,y,w,h in source pixels to ignore (repeatable)")
    ap.add_argument("--max-still", type=float, default=1.0)
    ap.add_argument("--thresh", type=float, default=14, help="grey-level change that counts for one pixel")
    ap.add_argument("--min-px", type=int, default=40, help="changed pixels (1/4-size) that make a frame count as changed")
    ap.add_argument("--window", type=float, default=0.25,
                    help="also compare with the frame this many seconds back (slow pushes and drifts count as motion)")
    ap.add_argument("--json")
    a = ap.parse_args()
    cap = cv2.VideoCapture(a.video)
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    W, H = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)), int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    k = 4                                                   # downscale factor (speed, and ignores grain)
    keep = np.ones((H // k, W // k), bool)
    for m in a.mask:
        x, y, w, h = [int(v) for v in m.split(",")]
        keep[y // k:(y + h) // k + 1, x // k:(x + w) // k + 1] = False
    grays = []
    while True:
        ok, f = cap.read()
        if not ok:
            break
        g = cv2.resize(cv2.cvtColor(f, cv2.COLOR_BGR2GRAY), (W // k, H // k), interpolation=cv2.INTER_AREA).astype(np.float32)
        grays.append(cv2.GaussianBlur(g, (3, 3), 0))     # film grain must not count as motion
    n = len(grays)
    moving = moving_frames(grays, fps, keep, a.thresh, a.min_px, a.window)
    stills, i = [], 0
    while i < n:
        if not moving[i]:
            j = i
            while j < n and not moving[j]:
                j += 1
            if (j - i) / fps > a.max_still:
                stills.append((round(i / fps, 2), round(j / fps, 2), round((j - i) / fps, 2)))
            i = j
        else:
            i += 1
    first2 = [s for s in range(1, min(n, int(2 * fps))) if not moving[s]]
    rep = {"length_s": round(n / fps, 2), "changes_per_s": round(moving.sum() / (n / fps), 1),
           "still_stretches": stills, "first_2s_still_frames": len(first2)}
    print(f"length {rep['length_s']}s, frames that change per second {rep['changes_per_s']}")
    print(f"first 2 s: {len(first2)} still frames" + (" (OK)" if not first2 else " <- fix: the hook must move"))
    if stills:
        print(f"STILL STRETCHES over {a.max_still}s (add a pop, a count, a zoom, or confirm the hold is deliberate):")
        for s in stills:
            print(f"  {s[0]:7.2f}s -> {s[1]:7.2f}s  ({s[2]}s)")
    else:
        print(f"no still stretch over {a.max_still}s")
    if a.json:
        json.dump(rep, open(a.json, "w"), indent=1)


if __name__ == "__main__":
    main()
