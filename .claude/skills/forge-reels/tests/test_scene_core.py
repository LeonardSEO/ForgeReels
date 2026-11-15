import pathlib
import shutil
import subprocess
import unittest

HERE = pathlib.Path(__file__).resolve().parent


@unittest.skipUnless(shutil.which("node"), "needs node")
class SceneCoreTest(unittest.TestCase):
    def test_node_suite(self):
        r = subprocess.run(["node", "--test", str(HERE / "scene_core.test.js")], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout[-3000:] + r.stderr[-1000:])


if __name__ == "__main__":
    unittest.main()
