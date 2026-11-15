import json
import pathlib
import sys
import tempfile
import unittest

import numpy as np
import soundfile as sf

SCRIPTS = pathlib.Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(SCRIPTS / "pipeline"))
import vo_cache  # noqa: E402
import words  # noqa: E402


def tone(path, secs, freq=220.0, sr=24000):
    t = np.arange(int(secs * sr)) / sr
    sf.write(str(path), (0.3 * np.sin(2 * np.pi * freq * t)).astype(np.float32), sr)


class CacheTest(unittest.TestCase):
    def setUp(self):
        self.tmp = pathlib.Path(tempfile.mkdtemp())

    def test_same_parts_same_key(self):
        self.assertEqual(vo_cache.key(a=1, b="x"), vo_cache.key(b="x", a=1))
        self.assertNotEqual(vo_cache.key(a=1), vo_cache.key(a=2))

    def test_text_change_invalidates(self):
        wav = self.tmp / "01.wav"
        tone(wav, 0.5)
        vo_cache.stamp(wav, vo_cache.key(text="hello", voice="af_heart"))
        self.assertTrue(vo_cache.fresh(wav, vo_cache.key(text="hello", voice="af_heart")))
        self.assertFalse(vo_cache.fresh(wav, vo_cache.key(text="hello there", voice="af_heart")))

    def test_missing_sidecar_is_stale(self):
        wav = self.tmp / "01.wav"
        tone(wav, 0.5)
        self.assertFalse(vo_cache.fresh(wav, vo_cache.key(text="hello")))

    def test_missing_file_is_stale(self):
        self.assertFalse(vo_cache.fresh(self.tmp / "nope.wav", vo_cache.key(text="x")))

    def test_words_rebuilds_transcript_when_wav_changes(self):
        vo = self.tmp / "vo"
        (vo / "lines").mkdir(parents=True)
        tone(vo / "lines" / "01.wav", 1.0)
        (vo / "starts.json").write_text(json.dumps({"starts": [0.15]}))
        calls = []

        def fake_asr(wav, model, language):
            calls.append(wav)
            return [{"text": "hi", "start": 0.0, "end": 0.4}]

        real, words.faster_whisper_words = words.faster_whisper_words, fake_asr     # words.py's ASR hook
        argv = sys.argv
        try:
            sys.argv = ["words.py", "--vo", str(vo)]
            words.main()
            words.main()                      # unchanged audio: transcript reused
            self.assertEqual(len(calls), 1)
            tone(vo / "lines" / "01.wav", 1.0, freq=330.0)
            words.main()                      # new audio: transcript rebuilt
            self.assertEqual(len(calls), 2)
        finally:
            words.faster_whisper_words, sys.argv = real, argv


if __name__ == "__main__":
    unittest.main()
