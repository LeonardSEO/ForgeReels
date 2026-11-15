import pathlib
import sys
import unittest

import cv2
import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))
from pace_check import moving_frames  # noqa: E402


def blob(scale, size=(480, 270)):
    """A dark scene with a soft-edged glass shape (like the Liquid Glass hook), the camera zoomed by `scale`."""
    h, w = size
    y, x = np.mgrid[0:h, 0:w].astype(np.float32)
    r = np.hypot((x - w / 2) / scale, (y - h / 2) / scale)
    return (15 + 100 / (1 + np.exp((r - 80) / 3))).astype(np.float32)      # edge about 12 px soft


class PaceCheck(unittest.TestCase):
    def test_slow_push_over_a_soft_gradient_counts_as_motion(self):
        frames = [blob(1 + 0.004 * i) for i in range(60)]           # 2 s at 30 fps, 0.4 % zoom per frame
        moving = moving_frames(frames, fps=30, keep=np.ones(frames[0].shape, bool))
        # once a quarter second of the push has passed, every frame reads as motion (the old per-frame rule: none)
        self.assertTrue(moving[8:].all(), f"{(~moving[8:]).sum()} frames read as still")

    def test_a_real_hold_stays_still(self):
        rng = np.random.default_rng(0)
        frames = [blob(1.0) + rng.normal(0, 1.5, (480, 270)).astype(np.float32) for _ in range(60)]  # grain only
        moving = moving_frames(frames, fps=30, keep=np.ones(frames[0].shape, bool))
        self.assertEqual(moving[1:].sum(), 0)


if __name__ == "__main__":
    unittest.main()
