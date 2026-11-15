import os
import pathlib
import stat
import subprocess
import sys
import tempfile
import unittest

SCRIPTS = pathlib.Path(__file__).resolve().parent.parent / "scripts"
PNG = b"\x89PNG\r\n\x1a\n" + b"\0" * 64


def fake_codex(bin_dir, writes_png):
    """A stand-in `codex` that records its arguments and (optionally) writes the PNG named in the prompt."""
    code = f'''#!{sys.executable}
import pathlib, re, sys
pathlib.Path({str(bin_dir / "args.txt")!r}).write_text("\\n".join(sys.argv[1:]))
m = re.search(r"Save it as (\\S+\\.png)", sys.argv[-1])
if {writes_png} and m:
    pathlib.Path(m.group(1)).write_bytes({PNG!r})
'''
    p = bin_dir / "codex"
    p.write_text(code)
    p.chmod(p.stat().st_mode | stat.S_IEXEC)


def run(bin_dir, *args):
    env = dict(os.environ, PATH=f"{bin_dir}:{os.environ['PATH']}")
    return subprocess.run([sys.executable, "-I", str(SCRIPTS / "gen_image.py"), *args], capture_output=True,
                          text=True, env=env)


class GenImageTest(unittest.TestCase):
    def setUp(self):
        self.bin = pathlib.Path(tempfile.mkdtemp())
        self.out = pathlib.Path(tempfile.mkdtemp()) / "plates" / "clock.png"

    def test_writes_image_and_passes_prompt_and_refs(self):
        fake_codex(self.bin, True)
        ref = self.bin / "brand.jpg"
        ref.write_bytes(b"x")
        r = run(self.bin, "a red alarm clock", "-o", str(self.out), "--ref", str(ref), "--aspect", "1:1")
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.out.read_bytes()[:8], PNG[:8])
        args = (self.bin / "args.txt").read_text()
        self.assertIn("exec", args)
        self.assertIn(str(ref), args)
        self.assertIn("a red alarm clock", args)
        self.assertIn("1:1", args)

    def test_fails_when_codex_saves_nothing(self):
        fake_codex(self.bin, False)
        r = run(self.bin, "a red alarm clock", "-o", str(self.out))
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("no image", r.stderr.lower())

    def test_missing_codex_says_how_to_install(self):
        empty = pathlib.Path(tempfile.mkdtemp())
        env = dict(os.environ, PATH=f"{empty}:/usr/bin:/bin")
        r = subprocess.run([sys.executable, "-I", str(SCRIPTS / "gen_image.py"), "x", "-o", str(self.out)],
                           capture_output=True, text=True, env=env)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn("codex", r.stderr.lower())
        self.assertNotIn("Traceback", r.stderr)


if __name__ == "__main__":
    unittest.main()
