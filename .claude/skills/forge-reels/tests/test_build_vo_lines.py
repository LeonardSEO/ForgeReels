import json
import pathlib
import subprocess
import sys
import tempfile
import unittest

SCRIPTS = pathlib.Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))
import tts_engines  # noqa: E402

KOKORO = tts_engines.kokoro_files()[0].exists()


class ParseLineTest(unittest.TestCase):
    def test_prefix_speed(self):
        self.assertEqual(tts_engines.parse_line("[speed=1.1] Hallo", {}), ("Hallo", "Hallo", 1.1))

    def test_no_prefix(self):
        self.assertEqual(tts_engines.parse_line("Hallo daar", {}), ("Hallo daar", "Hallo daar", None))

    def test_say_replaces_whole_words_only(self):
        caption, spoken, _ = tts_engines.parse_line("AI writes MAIL", {"AI": "A.I."})
        self.assertEqual(spoken, "A.I. writes MAIL")
        self.assertEqual(caption, "AI writes MAIL")


@unittest.skipUnless(KOKORO, "needs the Kokoro model")
class BuildVoTest(unittest.TestCase):
    def test_build_vo_keeps_caption_text_and_per_line_speed(self):
        tmp = pathlib.Path(tempfile.mkdtemp())
        (tmp / "lines.txt").write_text("[speed=1.2] The AI is fast.\nThe AI is slow.\n")
        (tmp / "say.json").write_text(json.dumps({"AI": "A.I."}))
        subprocess.run([sys.executable, "-I", str(SCRIPTS / "pipeline" / "build_vo.py"), "--lines", str(tmp / "lines.txt"),
                        "--out", str(tmp / "vo"), "--say", str(tmp / "say.json")], check=True, capture_output=True)
        S = json.loads((tmp / "vo" / "starts.json").read_text())
        self.assertEqual(S["lines"], ["The AI is fast.", "The AI is slow."])
        self.assertEqual(S["spoken"], ["The A.I. is fast.", "The A.I. is slow."])
        self.assertLess(S["durs"][0], S["durs"][1])          # same words, line 1 at speed 1.2


if __name__ == "__main__":
    unittest.main()
