import pathlib
import sys
import tempfile
import unittest

SCRIPTS = pathlib.Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))
import voice_bakeoff as vb  # noqa: E402


class WerTest(unittest.TestCase):
    def test_wer_identical_is_zero(self):
        self.assertEqual(vb.wer("Stop scrolling, now.", "stop scrolling now"), 0.0)

    def test_wer_one_sub_of_four_is_quarter(self):
        self.assertAlmostEqual(vb.wer("one two three four", "one two tree four"), 0.25)

    def test_wer_empty_hypothesis_is_one(self):
        self.assertEqual(vb.wer("one two", ""), 1.0)

    def test_wer_keeps_dutch_diaeresis(self):
        self.assertEqual(vb.wer("drieën één", "drieën één"), 0.0)


class SpecTest(unittest.TestCase):
    def test_parse_spec_with_reference_wav(self):
        self.assertEqual(vb.parse_spec("pocket:/tmp/my voice.wav"), ("pocket", "/tmp/my voice.wav"))
        self.assertEqual(vb.parse_spec("kokoro:af_heart"), ("kokoro", "af_heart"))

    def test_kokoro_skips_dutch(self):
        self.assertFalse(vb.supports("kokoro", "nl"))
        self.assertTrue(vb.supports("pocket", "nl"))
        self.assertTrue(vb.supports("kokoro", "en"))


class PickPageTest(unittest.TestCase):
    def test_pick_page_is_blind_and_lists_every_take(self):
        out = pathlib.Path(tempfile.mkdtemp())
        rows = [{"script": "en_hook", "file": "en_hook_kokoro_af_heart.wav", "key": "A"},
                {"script": "en_hook", "file": "en_hook_pocket_alba.wav", "key": "B"}]
        vb.write_pick_page(rows, out)
        html = (out / "pick.html").read_text(encoding="utf-8")
        self.assertIn("en_hook_pocket_alba.wav", html)
        self.assertNotIn('"pocket', html.split("const GROUPS")[1].split("];")[0].replace("en_hook_pocket", ""))
        self.assertNotIn("word1_A.wav", html)


if __name__ == "__main__":
    unittest.main()
