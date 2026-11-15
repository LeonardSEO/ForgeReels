import json
import os
import pathlib
import subprocess
import sys
import tempfile
import time
import unittest

HOOK = pathlib.Path(__file__).resolve().parents[3] / "hooks" / "forge_hooks.py"


def run(cmd, payload, root):
    env = dict(os.environ, CLAUDE_PROJECT_DIR=str(root))
    r = subprocess.run([sys.executable, "-I", str(HOOK), cmd], input=json.dumps(payload), capture_output=True,
                       text=True, env=env)
    return r.returncode, (json.loads(r.stdout) if r.stdout.strip() else None)


class Hooks(unittest.TestCase):
    def setUp(self):
        self.root = pathlib.Path(tempfile.mkdtemp())
        (self.root / "reels" / "2026-01-01-demo" / "out").mkdir(parents=True)
        (self.root / "output").mkdir()

    def test_stop_blocks_unchecked_render_once(self):
        v = self.root / "output" / "demo.mp4"
        v.write_bytes(b"x")
        code, out = run("stop", {}, self.root)
        self.assertEqual((code, out["decision"]), (0, "block"))
        self.assertIn("demo.mp4", out["reason"])
        self.assertEqual(run("stop", {"stop_hook_active": True}, self.root), (0, None))

    def test_stop_passes_with_fresh_stamp_and_ignores_old_renders(self):
        v = self.root / "output" / "demo.mp4"
        v.write_bytes(b"x")
        pathlib.Path(str(v) + ".qc-pass").write_text("{}")
        old = self.root / "output" / "old.mp4"
        old.write_bytes(b"x")
        t = time.time() - 2 * 86400
        os.utime(old, (t, t))
        self.assertEqual(run("stop", {}, self.root), (0, None))

    def test_post_edit_rejects_broken_json_and_ignores_other_files(self):
        p = self.root / "reels" / "2026-01-01-demo" / "visual_plan.json"
        p.write_text("{bad")
        code, out = run("post-edit", {"tool_input": {"file_path": str(p)}}, self.root)
        self.assertEqual(out["decision"], "block")
        self.assertEqual(run("post-edit", {"tool_input": {"file_path": str(self.root / "a.txt")}}, self.root), (0, None))

    def test_session_start_lists_reels_in_progress(self):
        code, out = run("session-start", {}, self.root)
        self.assertIn("2026-01-01-demo", out["hookSpecificOutput"]["additionalContext"])


if __name__ == "__main__":
    unittest.main()
