import json
import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "scripts" / "pipeline"))
import build_explainer as be  # noqa: E402


class BuildExplainerTest(unittest.TestCase):
    def test_output_name_drops_the_date_prefix(self):
        self.assertEqual(be.slug("2026-11-15-liquid-glass-react"), "liquid-glass-react")
        self.assertEqual(be.slug("touchscreen"), "touchscreen")

    @unittest.skipUnless(shutil.which("ffmpeg"), "needs ffmpeg")
    def test_master_brings_a_quiet_voice_to_about_minus_14_lufs(self):
        tmp = pathlib.Path(tempfile.mkdtemp()); src, dst = tmp / "in.mp4", tmp / "out.mp4"
        subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i", "color=c=black:s=270x480:d=4:r=30", "-f", "lavfi",
                        "-i", "sine=f=330:d=4", "-af", "volume=0.05", "-c:v", "libx264", "-pix_fmt", "yuv420p",
                        "-c:a", "aac", "-shortest", str(src)], check=True)
        be.master(src, dst)
        r = subprocess.run(["ffmpeg", "-i", str(dst), "-af", "ebur128", "-f", "null", "-"], capture_output=True, text=True)
        lufs = float(r.stderr.rsplit("I:", 1)[1].split("LUFS")[0])
        self.assertAlmostEqual(lufs, -14, delta=1.5)

    def test_brief_must_cite_three_reference_techniques_with_our_own_version(self):
        ok = """# Brief
## Learned from references
| Technique | From (file, time) | Our own version in this video |
|---|---|---|
| Theme flip | day01-karpathy-skills.mp4, 30.5 s | light section on "Instead" |
| Preview words | day01-modern-web-guidance.mp4, captions | coming words at 35% |
| Persistent world | paper-isometric-rederive.mp4, whole reel | the chip returns ghosted |

Not taken: their series format.
"""
        self.assertEqual(be.reference_rows(ok), 3)
        self.assertEqual(be.reference_problems(ok), [])
        two = ok.replace('| Persistent world | paper-isometric-rederive.mp4, whole reel | the chip returns ghosted |\n', "")
        self.assertTrue(be.reference_problems(two))
        empty_ours = ok.replace("light section on \"Instead\"", " ")
        self.assertTrue(be.reference_problems(empty_ours))
        self.assertTrue(be.reference_problems("# Brief\nno table\n"))
        no_source = ok.replace("day01-karpathy-skills.mp4, 30.5 s", "somewhere")
        self.assertTrue(be.reference_problems(no_source))


if __name__ == "__main__":
    unittest.main()
