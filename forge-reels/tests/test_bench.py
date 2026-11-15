import json
import pathlib
import subprocess
import sys
import unittest

SCRIPTS = pathlib.Path(__file__).resolve().parent.parent / "scripts"


class BenchTest(unittest.TestCase):
    @unittest.skipUnless(sys.platform == "darwin", "uses /usr/bin/time -l (macOS)")
    def test_reports_peak_rss(self):
        r = subprocess.run([sys.executable, "-I", str(SCRIPTS / "bench.py"), "--",
                            sys.executable, "-c", "x = bytearray(200_000_000)"],
                           capture_output=True, text=True, check=True)
        out = json.loads(r.stdout.strip().splitlines()[-1])
        self.assertGreaterEqual(out["peak_rss_mb"], 190)
        self.assertGreater(out["wall_s"], 0)
        self.assertIn("bytearray", out["cmd"])

    @unittest.skipUnless(sys.platform == "darwin", "uses /usr/bin/time -l (macOS)")
    def test_failing_command_exits_nonzero(self):
        r = subprocess.run([sys.executable, "-I", str(SCRIPTS / "bench.py"), "--",
                            sys.executable, "-c", "raise SystemExit(3)"], capture_output=True, text=True)
        self.assertEqual(r.returncode, 3)


if __name__ == "__main__":
    unittest.main()
