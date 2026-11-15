import json
import pathlib
import subprocess
import sys
import tempfile
import unittest

import soundfile as sf

SCRIPTS = pathlib.Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))
import tts_engines  # noqa: E402
import vo_check  # noqa: E402

KOKORO = tts_engines.kokoro_files()[0].exists()


class ScoreTest(unittest.TestCase):
    def test_digits_heard_for_spelled_numbers_are_not_errors(self):
        self.assertEqual(vo_check.spoken_wer("Wie elke maand honderdvijftig euro inlegt",
                                             "Wie elke maand 150 euro inlegt"), 0.0)
        self.assertEqual(vo_check.spoken_wer("ruim tweehonderdduizend euro", "ruim 200 .000 euro"), 0.0)

    def test_number_spanning_words_and_separate_numbers(self):
        # found by the final verification on Kokoro EN: both lines are spoken correctly
        self.assertEqual(vo_check.spoken_wer("check their phone ninety-six times a day",
                                             "check their phone 96 times a day"), 0.0)
        self.assertEqual(vo_check.spoken_wer("check messages at ten, two, and five.",
                                             "check messages at 10, 2, and 5."), 0.0)

    def test_split_dutch_compound_is_not_an_error(self):
        # Whisper small heard "daartussen" as "daar tussen" on a correct Pocket take (final verification)
        self.assertEqual(vo_check.spoken_wer("Daartussen niets.", "Daar tussen niets."), 0.0)
        self.assertGreater(vo_check.spoken_wer("Daartussen niets.", "Daar binnen niets."), 0.0)

    def test_digits_never_cover_ordinary_words(self):
        self.assertGreater(vo_check.spoken_wer("Try it for seven days.", "Try it for 7."), 0.08)
        self.assertTrue(vo_check.is_number_word("vijfentwintigste"))
        self.assertTrue(vo_check.is_number_word("tweehonderdduizend"))
        self.assertFalse(vo_check.is_number_word("days"))
        self.assertFalse(vo_check.is_number_word("de"))

    def test_real_word_errors_still_count(self):
        self.assertAlmostEqual(vo_check.spoken_wer("een indexfonds volgt de markt", "een index volgens de markt"),
                               0.4)

    def test_last_word_missing(self):
        heard = [{"text": "Try", "start": 0.1, "end": 0.3}, {"text": "it", "start": 0.3, "end": 0.4}]
        self.assertTrue(vo_check.last_word_missing("Try it today.", heard, 1.0))
        heard.append({"text": "today.", "start": 0.5, "end": 0.9})
        self.assertFalse(vo_check.last_word_missing("Try it today.", heard, 1.0))


@unittest.skipUnless(KOKORO, "needs the Kokoro model")
class VoCheckRunTest(unittest.TestCase):
    def make_vo(self, text, cut_last_word):
        vo = pathlib.Path(tempfile.mkdtemp())
        wav = tts_engines.synth("kokoro", {1: text}, vo / "lines", "af_heart", 1.0, None)[1]
        if cut_last_word:
            y, sr = sf.read(str(wav), dtype="float32")
            sf.write(str(wav), y[:int(len(y) * 0.62)], sr)          # "...for seven" without "days"
        (vo / "starts.json").write_text(json.dumps({"starts": [0.15], "lines": [text]}))
        return vo

    def run_check(self, vo):
        return subprocess.run([sys.executable, "-I", str(SCRIPTS / "vo_check.py"), "--vo", str(vo)],
                              capture_output=True, text=True)

    def test_clean_line_passes(self):
        r = self.run_check(self.make_vo("Try it for seven days.", False))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr[-500:])

    def test_clipped_last_word_fails(self):
        r = self.run_check(self.make_vo("Try it for seven days.", True))
        self.assertEqual(r.returncode, 1, r.stdout)
        self.assertIn("01", r.stdout)


if __name__ == "__main__":
    unittest.main()
