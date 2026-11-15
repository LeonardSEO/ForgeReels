import importlib.util
import os
import pathlib
import subprocess
import sys
import tempfile
import unittest

import soundfile as sf

SCRIPTS = pathlib.Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))
import tts_engines  # noqa: E402

KOKORO = tts_engines.kokoro_files()[0].exists()


def dur(p):
    i = sf.info(str(p))
    return i.frames / i.samplerate


class EngineTest(unittest.TestCase):
    def setUp(self):
        self.tmp = pathlib.Path(tempfile.mkdtemp())

    def test_unknown_engine_raises(self):
        with self.assertRaises(tts_engines.EngineMissing):
            tts_engines.synth("nope", {1: "hi"}, self.tmp, "x", 1.0, None)

    def test_missing_engine_message(self):
        real = importlib.util.find_spec
        importlib.util.find_spec = lambda name, *a: None if name == "pocket_tts" else real(name, *a)
        try:
            with self.assertRaises(tts_engines.EngineMissing) as cm:
                tts_engines.synth("pocket", {1: "hi"}, self.tmp, "alba", 1.0, "en")
        finally:
            importlib.util.find_spec = real
        self.assertIn("pip install pocket-tts", str(cm.exception))

    @unittest.skipUnless(KOKORO, "kokoro model not in ~/.cache/hyperframes/tts")
    def test_kokoro_writes_one_wav_per_line(self):
        out = tts_engines.synth("kokoro", {1: "Hello there.", 2: "Second line."}, self.tmp, "af_heart", 1.0, None)
        self.assertEqual(sorted(p.name for p in out.values()), ["01.wav", "02.wav"])
        for p in out.values():
            self.assertGreater(dur(p), 0.3)

    @unittest.skipUnless(KOKORO, "kokoro model not in ~/.cache/hyperframes/tts")
    def test_kokoro_matches_cli(self):
        text = "Most people check their phone ninety-six times a day."
        cli = self.tmp / "cli.wav"
        env = dict(os.environ, HYPERFRAMES_PYTHON=sys.executable)
        subprocess.run(["npx", "hyperframes", "tts", text, "-v", "af_heart", "-s", "1.0", "-o", str(cli)],
                       check=True, capture_output=True, env=env)
        out = tts_engines.synth("kokoro", {1: text}, self.tmp / "inproc", "af_heart", 1.0, None)
        self.assertAlmostEqual(dur(out[1]), dur(cli), delta=0.05)

    def test_kokoro_lang_from_voice_prefix(self):
        self.assertEqual(tts_engines.kokoro_lang("af_heart", None), "en-us")
        self.assertEqual(tts_engines.kokoro_lang("bf_emma", None), "en-gb")
        self.assertEqual(tts_engines.kokoro_lang("hf_alpha", None), "hi")
        self.assertEqual(tts_engines.kokoro_lang("af_heart", "hi"), "hi")
        # bare ISO codes (as used by scripts and Pocket) map to espeak names; "en" follows the voice's accent
        self.assertEqual(tts_engines.kokoro_lang("bf_emma", "en"), "en-gb")
        self.assertEqual(tts_engines.kokoro_lang("af_heart", "en"), "en-us")
        self.assertEqual(tts_engines.kokoro_lang("ff_siwis", "fr"), "fr-fr")

    def test_pocket_language_names(self):
        self.assertEqual(tts_engines.pocket_language("nl"), "dutch")
        self.assertEqual(tts_engines.pocket_language("en-us"), "english")
        self.assertEqual(tts_engines.pocket_language(None), "english")
        self.assertEqual(tts_engines.pocket_language("dutch_24l"), "dutch_24l")


if __name__ == "__main__":
    unittest.main()
