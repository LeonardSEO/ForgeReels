import json
import pathlib
import subprocess
import sys
import tempfile
import time
import unittest

import soundfile as sf

SCRIPTS = pathlib.Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))
import _paths  # noqa: E402

VPY = pathlib.Path(_paths.voxcpm_python())


@unittest.skipUnless(VPY.exists(), "VoxCPM venv not set up (setup/setup-voxcpm.sh)")
class VoxcpmWorkerTest(unittest.TestCase):
    def test_voxcpm_worker_exits_after_batch(self):
        tmp = pathlib.Path(tempfile.mkdtemp())
        out = {"1": str(tmp / "01.wav"), "2": str(tmp / "02.wav")}
        job = {"lines": {"1": "Goedemorgen.", "2": "Dit is de tweede regel."}, "out": out,
               "voice": "A calm adult male narrator", "speed": 1.0, "lang": "nl"}
        r = subprocess.run([str(VPY), "-I", str(SCRIPTS / "tts_worker_voxcpm.py")], input=json.dumps(job),
                           text=True, capture_output=True, timeout=900)
        done = time.time()
        self.assertEqual(r.returncode, 0, r.stderr[-800:])
        last = max(pathlib.Path(p).stat().st_mtime for p in out.values())
        self.assertLess(done - last, 5.0)
        for p in out.values():
            self.assertGreater(sf.info(p).duration, 0.3)
            self.assertEqual(sf.info(p).samplerate, 48000)


if __name__ == "__main__":
    unittest.main()
