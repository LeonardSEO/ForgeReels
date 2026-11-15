import pathlib
import sys
import unittest

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "scripts"))
try:
    import beatmix  # noqa: E402
except ImportError as e:                                        # earshot lives in the AUDIO venv
    beatmix = None
    REASON = str(e)


@unittest.skipIf(beatmix is None, "beatmix imports need the audio venv")
class SpeechMaskTest(unittest.TestCase):
    def test_mask_is_as_long_as_the_voice_when_the_length_is_not_a_whole_number_of_windows(self):
        vo = np.zeros((2220800, 2), np.float32)
        vo[48000:96000] = 0.3
        spk, _ = beatmix.speech_mask(vo)
        self.assertEqual(len(spk), len(vo))
        self.assertTrue(spk[60000] and not spk[200000])


if __name__ == "__main__":
    unittest.main()
