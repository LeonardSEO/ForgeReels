"""Tests for the final-review findings (Important 1-8)."""
import json
import os
import pathlib
import subprocess
import sys
import tempfile
import time
import unittest

import numpy as np
import soundfile as sf

SCRIPTS = pathlib.Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))
import asr  # noqa: E402
import mouth_phonemes  # noqa: E402
import tts_engines  # noqa: E402
import vo_check  # noqa: E402

KOKORO = tts_engines.kokoro_files()[0].exists()


class ClippedTailTest(unittest.TestCase):                       # Important 1
    def test_ends_in_silence(self):
        sr = 24000
        speech = (0.3 * np.sin(np.arange(sr) * 0.05)).astype(np.float32)
        self.assertTrue(vo_check.ends_in_silence(np.concatenate([speech, np.zeros(int(0.1 * sr), np.float32)]), sr))
        self.assertFalse(vo_check.ends_in_silence(speech, sr))

    @unittest.skipUnless(KOKORO, "needs the Kokoro model")
    def test_partly_clipped_last_word_fails(self):
        vo = pathlib.Path(tempfile.mkdtemp())
        text = "Try it for seven days."
        wav = tts_engines.synth("kokoro", {1: text}, vo / "lines", "af_heart", 1.0, None)[1]
        y, sr = sf.read(str(wav), dtype="float32")
        nz = np.flatnonzero(np.abs(y) > 0.01)
        sf.write(str(wav), y[:nz[-1] - int(0.2 * sr)], sr)        # 0.2 s of speech cut off the end
        (vo / "starts.json").write_text(json.dumps({"starts": [0.15], "lines": [text]}))
        r = subprocess.run([sys.executable, "-I", str(SCRIPTS / "vo_check.py"), "--vo", str(vo)],
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 1, r.stdout)


class ScriptDigitsTest(unittest.TestCase):                      # Important 2
    def test_script_digits_match(self):
        self.assertEqual(vo_check.spoken_wer("We launched in 2026.", "We launched in 2026."), 0.0)
        self.assertEqual(vo_check.spoken_wer("Het kost 49 euro.", "Het kost negenenveertig euro."), 0.0)
        heard = [{"text": "launched", "start": 0.1, "end": 0.4}, {"text": "2026.", "start": 0.5, "end": 0.9}]
        self.assertFalse(vo_check.last_word_missing("We launched in 2026.", heard, 1.0))

    def test_checks_against_spoken_text(self):
        S = {"lines": ["The AI is fast."], "spoken": ["The A.I. is fast."]}
        self.assertEqual(vo_check.script_lines(S), ["The A.I. is fast."])
        self.assertEqual(vo_check.script_lines({"lines": ["x"]}), ["x"])


class DutchWordsTest(unittest.TestCase):                        # Important 3
    def test_drieenhalf_is_a_number(self):
        self.assertEqual(vo_check.spoken_wer("nog drieënhalf jaar", "nog 3 ,5 jaar"), 0.0)

    def test_split_compound_as_last_word(self):
        heard = [{"text": "niets", "start": 0.1, "end": 0.3}, {"text": "daar", "start": 0.4, "end": 0.6},
                 {"text": "tussen.", "start": 0.6, "end": 0.9}]
        self.assertFalse(vo_check.last_word_missing("Niets daartussen.", heard, 1.0))

    def test_curly_apostrophe(self):
        self.assertEqual(vo_check.spoken_wer("It’s fine.", "It's fine."), 0.0)


class DefaultsTest(unittest.TestCase):                          # Important 4, 5, 6, 7
    def test_default_voice_per_engine(self):
        self.assertEqual(tts_engines.default_voice("kokoro", None), "af_heart")
        self.assertEqual(tts_engines.default_voice("pocket", "nl"), "daan")
        self.assertEqual(tts_engines.default_voice("pocket", "en"), "alba")
        self.assertEqual(tts_engines.default_voice("voxcpm", "nl"), "default")

    def test_bad_pocket_voice_is_a_clean_error(self):
        with self.assertRaises(SystemExit) as cm:
            tts_engines.synth("pocket", {1: "Hallo."}, tempfile.mkdtemp(), "no_such_voice_xyz", 1.0, "nl")
        self.assertIn("no_such_voice_xyz", str(cm.exception))

    def test_voxcpm_without_reference_rebuilds_every_line(self):
        self.assertTrue(tts_engines.needs_full_batch("voxcpm", "A calm narrator"))
        self.assertTrue(tts_engines.needs_full_batch("voxcpm", "default"))
        self.assertFalse(tts_engines.needs_full_batch("voxcpm", "/refs/me.wav"))
        self.assertFalse(tts_engines.needs_full_batch("kokoro", "af_heart"))

    def test_language_comes_from_starts_json(self):
        self.assertEqual(asr.language_for(None, {"lang": "nl"}), "nl")
        self.assertEqual(asr.language_for("en", {"lang": "nl"}), "en")
        self.assertEqual(asr.language_for(None, {"lang": "en-us"}), "en")
        self.assertEqual(asr.language_for(None, {}), "en")


class StaleTranscriptTest(unittest.TestCase):                   # Important 8
    def test_transcript_older_than_wav_is_ignored(self):
        d = pathlib.Path(tempfile.mkdtemp())
        tj, wav = d / "transcript.json", d / "01.wav"
        tj.write_text(json.dumps([{"text": "old", "start": 0, "end": 1}]))
        sf.write(str(wav), np.zeros(2400, np.float32), 24000)
        os.utime(tj, (time.time() - 60, time.time() - 60))
        self.assertIsNone(mouth_phonemes.load_transcript(tj, wav))
        os.utime(tj, None)
        self.assertIsNotNone(mouth_phonemes.load_transcript(tj, wav))


if __name__ == "__main__":
    unittest.main()
