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
import words  # noqa: E402


class WordsTest(unittest.TestCase):
    def test_asr_word_never_starts_before_its_line(self):
        """ASR engines put the first word at 0.0 even after leading silence; the word must not land before the
        line's own start in vo.wav."""
        vo = pathlib.Path(tempfile.mkdtemp())
        (vo / "lines").mkdir()
        sr = 24000
        y = np.concatenate([np.zeros(int(0.4 * sr)), 0.3 * np.sin(np.arange(sr) * 0.05)]).astype(np.float32)
        sf.write(str(vo / "lines" / "01.wav"), y, sr)
        (vo / "starts.json").write_text(json.dumps({"starts": [0.15], "lines": ["hi"]}))
        real = words.faster_whisper_words
        words.faster_whisper_words = lambda w, m, l: [{"text": "hi", "start": 0.0, "end": 0.6}]
        argv, sys.argv = sys.argv, ["words.py", "--vo", str(vo)]
        try:
            words.main()
        finally:
            words.faster_whisper_words, sys.argv = real, argv
        w = json.loads((vo / "words.json").read_text())
        self.assertGreaterEqual(w[0]["start"], 0.15)
        self.assertGreater(w[0]["end"], w[0]["start"])


if __name__ == "__main__":
    unittest.main()
