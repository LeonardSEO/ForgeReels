import json
import pathlib
import shutil
import sys
import tempfile
import unittest

SCRIPTS = pathlib.Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS / "pipeline"))
import visual_plan as vp  # noqa: E402

WORDS = [{"line": 1, "i": 0, "text": "Your", "start": 0.15, "end": 0.4},
         {"line": 1, "i": 1, "text": "screen", "start": 0.4, "end": 0.8},
         {"line": 1, "i": 2, "text": "is", "start": 0.8, "end": 0.9},
         {"line": 1, "i": 3, "text": "glass.", "start": 0.95, "end": 1.4},
         {"line": 2, "i": 0, "text": "Under", "start": 1.8, "end": 2.0},
         {"line": 2, "i": 1, "text": "the", "start": 2.0, "end": 2.1},
         {"line": 2, "i": 2, "text": "glass,", "start": 2.1, "end": 2.5},
         {"line": 2, "i": 3, "text": "a", "start": 2.5, "end": 2.6},
         {"line": 2, "i": 4, "text": "grid.", "start": 2.6, "end": 3.0}]
PARTS = ["phone", "phone.glass", "phone.grid", "phone.rows"]
DUR = {"reveal": 0.5, "draw": 0.8, "focus": 0.9, "wide": 1.0, "count": 1.0}


def ev(word_ref, action="reveal", obj="phone.glass", **kw):
    return dict({"word_ref": word_ref, "action": action, "object": obj}, **kw)


class ResolveTest(unittest.TestCase):
    def resolve(self, events):
        return vp.resolve({"events": events}, WORDS, PARTS, DUR)

    def test_index_ref_lands_on_the_word_start(self):
        out, errors = self.resolve([ev({"line": 1, "index": 3, "expected": "glass"})])
        self.assertEqual(errors, [])
        self.assertEqual(out[0]["t"], 0.95)
        self.assertEqual(out[0]["dur"], 0.5)
        self.assertEqual(out[0]["word"], "glass.")

    def test_at_end_and_offset(self):
        out, _ = self.resolve([ev({"line": 1, "index": 3, "expected": "glass"}, at="end", offset=-0.1)])
        self.assertAlmostEqual(out[0]["t"], 1.3)

    def test_search_by_expected_with_nth(self):
        out, errors = self.resolve([ev({"line": 2, "expected": "grid"}, action="draw", obj="phone.rows")])
        self.assertEqual((errors, out[0]["t"]), ([], 2.6))
        out, errors = self.resolve([ev({"expected": "glass", "nth": 2})])      # second "glass" in the voice-over
        self.assertEqual((errors, out[0]["t"]), ([], 2.1))

    def test_wrong_word_is_an_error_with_a_suggestion(self):
        _, errors = self.resolve([ev({"line": 2, "index": 3, "expected": "grid"})])
        self.assertEqual(len(errors), 1)
        self.assertIn("'a'", errors[0])
        self.assertIn("index 4", errors[0])

    def test_unknown_object_and_action(self):
        _, errors = self.resolve([ev({"line": 1, "index": 3, "expected": "glass"}, obj="phone.glas"),
                                  ev({"line": 1, "index": 3, "expected": "glass"}, action="spin")])
        self.assertIn("phone.glass", errors[0])                                 # close match offered
        self.assertIn("spin", errors[1])

    def test_count_needs_a_target_and_wide_needs_no_object(self):
        _, errors = self.resolve([ev({"line": 1, "index": 3, "expected": "glass"}, action="count", obj="phone")])
        self.assertIn("args.to", errors[0])
        out, errors = self.resolve([{"word_ref": {"line": 2, "index": 4, "expected": "grid"}, "action": "wide"}])
        self.assertEqual((errors, out[0]["object"]), ([], None))


@unittest.skipUnless(shutil.which("node"), "needs node")
class SceneTest(unittest.TestCase):
    def test_parts_and_durations_come_from_the_runtime(self):
        tmp = pathlib.Path(tempfile.mkdtemp())
        (tmp / "scene.json").write_text(json.dumps({"components": [{"type": "phone", "id": "phone", "x": 0, "y": 0}]}))
        parts, dur = vp.runtime_info(tmp / "scene.json")
        self.assertIn("phone.glass", parts)
        self.assertEqual(dur["reveal"], 0.5)



class GroupTest(unittest.TestCase):
    def test_camera_may_target_a_group_and_rejects_unknown_members(self):
        ref = {"line": 1, "index": 3, "expected": "glass"}
        out, errors = vp.resolve({"events": [ev(ref, action="focus", obj=["phone", "phone.glass"])]}, WORDS, PARTS, DUR)
        self.assertEqual((errors, out[0]["object"]), ([], ["phone", "phone.glass"]))
        _, errors = vp.resolve({"events": [ev(ref, action="focus", obj=["phone", "nope"])]}, WORDS, PARTS, DUR)
        self.assertIn("nope", errors[0])
        _, errors = vp.resolve({"events": [ev(ref, action="reveal", obj=["phone"])]}, WORDS, PARTS, DUR)
        self.assertIn("only focus and wide", errors[0])


if __name__ == "__main__":
    unittest.main()
