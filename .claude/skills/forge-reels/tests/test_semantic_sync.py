import json
import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest

import numpy as np
from PIL import Image

SCRIPTS = pathlib.Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS / "pipeline"))
import semantic_sync as ss  # noqa: E402

WORDS = [{"line": 1, "i": 0, "text": "Your", "start": 0.2, "end": 0.4}, {"line": 1, "i": 1, "text": "glass.", "start": 0.5, "end": 0.9},
         {"line": 2, "i": 0, "text": "Then", "start": 1.2, "end": 1.4}, {"line": 2, "i": 1, "text": "nothing.", "start": 1.5, "end": 1.9}]
SCENE = {"components": [{"type": "phone", "id": "phone", "x": 0, "y": 0}]}
PLAN = {"events": [{"word_ref": {"line": 1, "index": 1, "expected": "glass"}, "action": "reveal", "object": "phone.glass"}]}


def project(events_js_events=None):
    pj = pathlib.Path(tempfile.mkdtemp())
    (pj / "vo").mkdir(); (pj / "assets").mkdir()
    (pj / "scene.json").write_text(json.dumps(SCENE)); (pj / "visual_plan.json").write_text(json.dumps(PLAN))
    (pj / "vo" / "words.json").write_text(json.dumps(WORDS))
    (pj / "vo" / "starts.json").write_text(json.dumps({"total": 2.0}))
    ev = events_js_events if events_js_events is not None else [
        {"t": 0.5, "dur": 0.5, "action": "reveal", "object": "phone.glass", "args": {}}]
    (pj / "assets" / "events.js").write_text("window.__FR_DATA = " + json.dumps({"events": ev}) + ";\n")
    return pj


@unittest.skipUnless(shutil.which("node"), "needs node")
class StaticTest(unittest.TestCase):
    def test_in_sync_project_passes_and_warns_about_a_line_without_events(self):
        errors, warnings, _ = ss.check_static(project())
        self.assertEqual(errors, [])
        self.assertTrue(any("line 2" in w for w in warnings))

    def test_stale_events_after_a_revoice_fail(self):
        errors, _, _ = ss.check_static(project([{"t": 0.9, "dur": 0.5, "action": "reveal", "object": "phone.glass", "args": {}}]))
        self.assertTrue(any("stale" in e for e in errors), errors)

    def test_event_after_the_voice_ends_fails(self):
        pj = project([{"t": 0.5, "dur": 0.5, "action": "reveal", "object": "phone.glass", "args": {}}])
        (pj / "vo" / "starts.json").write_text(json.dumps({"total": 0.4}))
        errors, _, _ = ss.check_static(pj)
        self.assertTrue(any("after the voice" in e for e in errors), errors)


class FramesTest(unittest.TestCase):
    def test_frame_diff(self):
        a = np.zeros((480, 270), np.uint8); b = a.copy(); b[100:300, 50:200] = 255
        self.assertEqual(ss.frame_diff(a, a), 0.0)
        self.assertGreater(ss.frame_diff(a, b), ss.MIN_CHANGE)

    @unittest.skipUnless(shutil.which("ffmpeg"), "needs ffmpeg")
    def test_event_that_changes_nothing_on_screen_fails(self):
        tmp = pathlib.Path(tempfile.mkdtemp()); mp4 = tmp / "v.mp4"
        subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i", "color=c=red:s=270x480:d=1:r=30", "-f", "lavfi",
                        "-i", "color=c=blue:s=270x480:d=1:r=30", "-filter_complex", "[0][1]concat=n=2:v=1",
                        "-pix_fmt", "yuv420p", str(mp4)], check=True)
        events = [{"t": 0.95, "dur": 0.1, "action": "reveal", "object": "a", "word": "blue"},
                  {"t": 0.2, "dur": 0.3, "action": "reveal", "object": "b", "word": "red"}]
        errors, sheet = ss.check_frames(events, mp4, tmp)
        self.assertEqual(len(errors), 1)
        self.assertIn("'red'", errors[0])
        self.assertTrue(sheet.exists())
        self.assertEqual(Image.open(sheet).size[1] > 0, True)

    @unittest.skipUnless(shutil.which("ffmpeg"), "needs ffmpeg")
    def test_event_running_past_the_end_of_the_video_is_checked_not_crashed(self):
        tmp = pathlib.Path(tempfile.mkdtemp()); mp4 = tmp / "v.mp4"
        subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i", "color=c=red:s=270x480:d=1:r=30", "-f", "lavfi",
                        "-i", "color=c=blue:s=270x480:d=1:r=30", "-filter_complex", "[0][1]concat=n=2:v=1",
                        "-pix_fmt", "yuv420p", str(mp4)], check=True)
        errors, _ = ss.check_frames([{"t": 0.9, "dur": 3.0, "action": "play", "object": "a", "word": "end"}], mp4, tmp)
        self.assertEqual(errors, [])


if __name__ == "__main__":
    unittest.main()
