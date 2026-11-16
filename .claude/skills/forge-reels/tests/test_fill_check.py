import pathlib
import sys
import unittest

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))
from fill_check import fill_fraction  # noqa: E402


class FillCheck(unittest.TestCase):
    def test_empty_stage_is_zero_and_a_big_subject_counts(self):
        f = np.full((192, 108, 3), 12, np.uint8)
        self.assertEqual(fill_fraction(f), 0.0)
        f[60:150, 10:98] = (200, 160, 140)            # a lit subject across most of the picture band
        self.assertGreater(fill_fraction(f), 0.5)

    def test_caption_band_and_faint_noise_do_not_count(self):
        f = np.full((192, 108, 3), 240, np.uint8)
        f[5:35] = 20                                  # captions at the top
        f[100:110] = 230                              # within tolerance of the background
        self.assertEqual(fill_fraction(f), 0.0)


if __name__ == "__main__":
    unittest.main()
