#!/usr/bin/env python3
"""flow_check.py: does the film flow, or does it read like a slideshow? Measured on the finished MP4.

  python -I flow_check.py film.mp4 [--json out.json] [--sheet sheet.jpg] [--width 270]

Written 2026-11-04 for this skill from published DESCRIPTIONS of the idea (onetake's README / SKILL.md: "at every
boundary something on screen survives and visibly becomes the next beat"; rhythm and blur thresholds). No onetake
code was read or used; this is our own method and code (MIT, like the rest of the skill).

How it works (dense optical flow, OpenCV DIS, on a small grey copy of every frame):
  per frame   change     = pixels that differ from the previous frame
              explained  = the part of that change that the previous frame, MOVED along the flow, accounts for
              new        = changed pixels the motion does not explain (new content: a cut, a fade, a pop-in)
  boundaries  windows (0.5 s) where new content covers a large share of the frame: the film's section changes
  carry       per boundary: explained change / all change in that window. A hard cut or a cross-fade is ~0
              (content replaced); a morph, push, zoom-through or slide is high (content carried)
  rhythm      shot lengths between boundaries: longest / shortest (want >= 4x); still stretches (want at least
              one run >= 0.5 s where almost nothing changes); a metronome (all shots within 25% of each other)
  speed       95th-percentile flow speed per frame in full-frame px; > 80 px/frame strobes without motion blur
              (HyperFrames: data-motion-blur="on" on the root; "-events" for render(t) scenes)

Verdicts are guides, calibrated on synthetic tests and our own reels (see references/visual-grammar.md
"Carry every boundary"); READ the contact sheet at each boundary before acting on a number.
"""
import argparse, json, sys
import cv2
import numpy as np

ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
ap.add_argument("video"); ap.add_argument("--json"); ap.add_argument("--sheet")
ap.add_argument("--width", type=int, default=270, help="analysis width (px); flow speed is rescaled to full size")
ap.add_argument("--diff", type=float, default=14.0, help="grey-level change that counts as 'changed'")
ap.add_argument("--boundary", type=float, default=0.18, help="share of the frame that must be NEW content in a window to call it a boundary")
ap.add_argument("--window", type=float, default=0.5, help="boundary window (s)")
ap.add_argument("--stride", type=int, default=2, help="measure the window every Nth frame (2 halves the time; 1 = every frame)")
ap.add_argument("--frames", action="store_true", help="also write every frame's measures into --json")
a = ap.parse_args()

cap = cv2.VideoCapture(a.video)
if not cap.isOpened():
    sys.exit(f"cannot open {a.video}")
fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
W0 = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)); H0 = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
w = a.width; h = int(round(H0 * w / W0)); k_full = W0 / w
dis = cv2.DISOpticalFlow_create(cv2.DISOPTICAL_FLOW_PRESET_MEDIUM)
gx, gy = np.meshgrid(np.arange(w, dtype=np.float32), np.arange(h, dtype=np.float32))

win = max(2, int(round(a.window * fps)))          # frames per window (0.5 s)
def cdiff(x, y):                                   # colour difference (max over B, G, R): sees equal-brightness colour changes
    return np.abs(x.astype(np.int16) - y.astype(np.int16)).max(2)
rows, thumbs, cols, greys, flows = [], [], [], [], []
i = 0
while True:
    ok, fr = cap.read()
    if not ok:
        break
    small = cv2.GaussianBlur(cv2.resize(fr, (w, h), interpolation=cv2.INTER_AREA), (3, 3), 0)
    g = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
    thumbs.append(small if a.sheet else None)
    flows.append(dis.calc(g, greys[-1], None) if greys else np.zeros((h, w, 2), np.float32))   # backward: cur -> prev
    greys.append(g); cols.append(small)
    if len(greys) > win + 1:                          # keep only what the window needs
        greys[-win - 2] = None; cols[-win - 2] = None; flows[-win - 2] = None
    mag = np.hypot(flows[-1][..., 0], flows[-1][..., 1]); moving = mag > 0.5
    spd = float(np.percentile(mag[moving], 95)) * k_full if moving.sum() > 0.002 * w * h else 0.0
    row = {"f": i, "t": i / fps, "speed": spd, "changed": 0.0, "new": 0.0, "entered": 0.0, "disp": 0.0}
    row["changed1"] = float((cdiff(small, cols[-2]) > a.diff).mean()) if len(cols) > 1 and cols[-2] is not None else 0.0
    if i >= win and (i - win) % max(1, a.stride) and rows:
        for kk in ("changed", "new", "entered", "disp"):
            row[kk] = rows[-1][kk]        # between measured frames: hold the last window's measures
    elif i >= win:
        # chain the per-frame flows back over the window: where was each pixel of frame t at frame t-win?
        cx, cy = gx.copy(), gy.copy()
        for j in range(i, i - win, -1):
            fl = flows[j]
            dx = cv2.remap(fl[..., 0], cx, cy, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
            dy = cv2.remap(fl[..., 1], cx, cy, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
            cx += dx; cy += dy
        old = cols[i - win]
        pred = cv2.remap(old, cx, cy, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)
        outside = (cx < 0) | (cx > w - 1) | (cy < 0) | (cy > h - 1)      # came in from off-screen: carried by motion
        changed = (cdiff(small, old) > a.diff) | outside
        newc = changed & (cdiff(small, pred) > a.diff) & ~outside
        disp = np.hypot(cx - gx, cy - gy)
        row["changed"] = float(changed.mean()); row["new"] = float(newc.mean()); row["entered"] = float(outside.mean())
        row["disp"] = float(np.median(disp[changed])) / w if changed.any() else 0.0
    rows.append(row)
    i += 1
cap.release()
n = i
if n < win + 2:
    sys.exit("video too short")
dur = n / fps
ch = np.array([r["changed"] for r in rows]); nw = np.array([r["new"] for r in rows])
ch1 = np.array([r["changed1"] for r in rows]); sp = np.array([r["speed"] for r in rows])
ent = np.array([r["entered"] for r in rows]); dsp = np.array([r["disp"] for r in rows])

# ---- transitions: a window where most of the frame changes. Either it is REPLACED (new content: cut, fade,
# pop-in) or CARRIED (the change is motion: a push, slide, zoom-through, morph). carry = 1 - new / changed ----
big = (nw > a.boundary) | ((ch > 0.25) & ((dsp > 0.07) | (ent > 0.15)))
bounds, j = [], win
while j < n:
    if big[j]:
        k = j
        while k + 1 < n and big[k + 1]:
            k += 1
        pk = j + int(np.argmax(nw[j:k + 1] + 1e-3 * ch[j:k + 1]))
        carry = float(1 - nw[j:k + 1].max() / max(ch[j:k + 1].max(), 1e-6))
        seg1 = ch1[max(0, pk - win + 1):pk + 1]
        hard = bool(seg1.size and seg1.max() > 0.35 and seg1.max() > 0.6 * seg1.sum())
        t_mid = rows[max(0, pk - win + 1) + int(np.argmax(seg1))]["t"] if (seg1.size and nw[pk] > a.boundary) else rows[(j + k) // 2]["t"] - a.window / 2
        bounds.append({"t": round(max(0.0, t_mid), 2), "span": [round(rows[max(0, j - win)]["t"], 2), round(rows[k]["t"], 2)],
                       "carry": round(max(0.0, carry), 2), "hard_cut": hard, "new_share": round(float(nw[j:k + 1].max()), 2)})
        j = k + win
    else:
        j += 1

# ---- rhythm ----
cuts = [0.0] + [b["t"] for b in bounds] + [dur]
shots = [round(cuts[j + 1] - cuts[j], 2) for j in range(len(cuts) - 1) if cuts[j + 1] - cuts[j] >= 0.2]
ratio = round(max(shots) / min(shots), 2) if len(shots) >= 2 else None
metronome = bool(len(shots) >= 4 and (np.std(shots) / np.mean(shots)) < 0.25)
still = ch1 < 0.004
runs, run = [], 0
for s in still:
    run = run + 1 if s else 0
    runs.append(run)
longest_still = round(max(runs) / fps, 2) if runs else 0.0
still_share = round(float(still.mean()), 3)

# ---- speed ----
fast = sp > 80
fast_runs, j = [], 0
while j < len(sp):
    if fast[j]:
        k = j
        while k + 1 < len(sp) and fast[k + 1]:
            k += 1
        fast_runs.append({"from": round(rows[j]["t"], 2), "to": round(rows[k]["t"], 2), "peak_px_per_frame": round(float(sp[j:k + 1].max()), 1)})
        j = k + 1
    else:
        j += 1

carries = [b["carry"] for b in bounds]
film_carry = round(float(np.mean(carries)), 2) if carries else None
verdict = []
if bounds:
    weak = [b for b in bounds if b["carry"] < 0.5]
    if film_carry is not None and film_carry < 0.5:
        verdict.append(f"SLIDESHOW RISK: mean carry {film_carry} < 0.5 ({len(weak)} of {len(bounds)} boundaries replace instead of carry)")
    elif weak:
        verdict.append(f"{len(weak)} of {len(bounds)} boundaries replace content (carry < 0.5): {', '.join(str(b['t']) + 's' for b in weak)}")
else:
    verdict.append("no transitions found (a very static film, or changes too small to register)")
if ratio is not None and ratio < 4:
    verdict.append(f"shot lengths vary only {ratio}x (want >= 4x: short hits next to long holds)")
if metronome:
    verdict.append("METRONOME: shot lengths within 25% of each other")
if longest_still < 0.5:
    verdict.append(f"no still stretch (longest {longest_still} s; rests make the moves land)")
if fast_runs:
    verdict.append(f"{len(fast_runs)} fast move(s) over 80 px/frame: need motion blur (data-motion-blur) or a slower move")

report = {"video": a.video, "fps": round(fps, 3), "duration_s": round(dur, 2), "size": [W0, H0],
          "carry_mean": film_carry, "boundaries": bounds, "shots_s": shots, "shot_ratio": ratio, "metronome": metronome,
          "still_share": still_share, "longest_still_s": longest_still, "fast_moves": fast_runs,
          "verdict": verdict or ["flows: boundaries carry, rhythm varies, nothing strobes"]}
if a.frames:
    report["frames"] = [{k: (round(v, 4) if isinstance(v, float) else v) for k, v in r.items()} for r in rows]
print(f"{a.video}: {dur:.1f} s, {len(bounds)} boundaries, carry mean {film_carry}, shot ratio {ratio}, "
      f"still {still_share * 100:.0f}% (longest {longest_still} s), fast moves {len(fast_runs)}")
for b in bounds:
    print(f"  boundary {b['t']:6.2f} s  carry {b['carry']:.2f}  {'HARD CUT' if b['hard_cut'] else ''}")
for v in report["verdict"]:
    print("  -", v)
if a.json:
    with open(a.json, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=1)
if a.sheet and bounds:
    tiles = []
    for b in bounds[:24]:
        fi = int(round(b["span"][0] * fps)); fo = min(n - 1, int(round(b["span"][1] * fps))); fm = int(round(b["t"] * fps))
        trip = [thumbs[min(n - 1, x)].copy() for x in (fi, fm, fo)]
        cv2.putText(trip[0], f"{b['t']}s carry {b['carry']}", (4, 16), cv2.FONT_HERSHEY_SIMPLEX, 0.45,
                    (0, 0, 255) if b["carry"] < 0.5 else (0, 160, 0), 1)
        tiles.append(np.hstack(trip))
    cv2.imwrite(a.sheet, np.vstack(tiles), [cv2.IMWRITE_JPEG_QUALITY, 85])
