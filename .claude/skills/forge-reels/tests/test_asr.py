import importlib.util
import pathlib
import sys
import tempfile
import unittest

import numpy as np
import soundfile as sf

SCRIPTS = pathlib.Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))
import asr  # noqa: E402
import tts_engines  # noqa: E402

HAVE_MMS = all(importlib.util.find_spec(m) for m in ("torchaudio", "transformers"))
HAVE_KOKORO = tts_engines.kokoro_files()[0].exists()


class ScriptWordsTest(unittest.TestCase):
    def test_script_words_keep_caption_spelling(self):
        self.assertEqual(asr.script_words("Tot slot: tien, twee en vijf uur."),
                         ["Tot", "slot:", "tien,", "twee", "en", "vijf", "uur."])

    def test_align_key_strips_diacritics_and_punctuation(self):
        self.assertEqual(asr.align_key("één,"), "een")
        self.assertEqual(asr.align_key("drieën"), "drieen")
        self.assertEqual(asr.align_key("30.000"), "")


class FillTest(unittest.TestCase):
    def test_missing_word_is_guessed_between_neighbours(self):
        items = [{"text": "a", "start": 0.1, "end": 0.4}, {"text": "30.000", "start": None, "end": None},
                 {"text": "euro", "start": 1.0, "end": 1.3}]
        out = asr.fill_guesses(items, 2.0)
        self.assertTrue(out[1]["guessed"])
        self.assertEqual((out[1]["start"], out[1]["end"]), (0.4, 1.0))
        self.assertNotIn("guessed", out[0])

    def test_guess_at_edges_uses_clip_bounds(self):
        out = asr.fill_guesses([{"text": "1", "start": None, "end": None}, {"text": "b", "start": 0.5, "end": 0.9},
                                {"text": "2", "start": None, "end": None}], 1.5)
        self.assertEqual((out[0]["start"], out[0]["end"]), (0.0, 0.5))
        self.assertEqual((out[2]["start"], out[2]["end"]), (0.9, 1.5))


class ParakeetWordsTest(unittest.TestCase):
    def test_subword_tokens_merge_into_words(self):
        toks = [(" De", 0.0, 0.32), (" me", 0.32, 0.56), ("este", 0.56, 0.72), (" ", 1.44, 1.76),
                ("9", 1.76, 2.0), ("6", 2.0, 2.16), (" ke", 2.16, 2.32), ("er", 2.32, 2.4)]
        self.assertEqual(asr.merge_tokens(toks), [{"text": "De", "start": 0.0, "end": 0.32},
                                                  {"text": "meeste", "start": 0.32, "end": 0.72},
                                                  {"text": "96", "start": 1.76, "end": 2.16},
                                                  {"text": "keer", "start": 2.16, "end": 2.4}])


@unittest.skipUnless(HAVE_MMS and HAVE_KOKORO, "needs torchaudio + transformers and the Kokoro model")
class AlignTest(unittest.TestCase):
    def test_align_gives_one_item_per_script_word_on_time(self):
        tmp = pathlib.Path(tempfile.mkdtemp())
        text = "Second, keep one app on your home screen."
        wav = tts_engines.synth("kokoro", {1: text}, tmp, "af_heart", 1.0, None)[1]
        y, sr = sf.read(str(wav), dtype="float32")
        onset = np.flatnonzero(np.abs(y) > 0.01)[0] / sr
        items = asr.align(wav, asr.script_words(text), "en")
        self.assertEqual([i["text"] for i in items], asr.script_words(text))
        self.assertLess(abs(items[0]["start"] - onset), 0.06)
        self.assertTrue(all(a["end"] <= b["start"] + 1e-6 for a, b in zip(items, items[1:])))


if __name__ == "__main__":
    unittest.main()
