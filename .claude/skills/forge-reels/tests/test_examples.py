"""Regression: every example's visual plan uses actions and objects the scene library really has.
(The full regression is `build_explainer.py --project examples/<name> --render --frames`.)"""
import json
import pathlib
import shutil
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts" / "pipeline"))
import visual_plan as vp  # noqa: E402

EXAMPLES = sorted(p for p in (ROOT.parents[2] / "references" / "examples").iterdir() if (p / "visual_plan.json").exists())


@unittest.skipUnless(shutil.which("node"), "needs node")
class ExamplesTest(unittest.TestCase):
    def test_the_reference_projects(self):
        self.assertEqual([p.name for p in EXAMPLES], ["ai-tokens", "git-at-ai-scale", "kit-gallery", "touchscreen", "web-cookies"])

    def test_every_event_targets_a_real_part_with_a_real_action(self):
        for ex in EXAMPLES:
            parts, dur = vp.runtime_info(ex / "scene.json")
            for n, e in enumerate(json.loads((ex / "visual_plan.json").read_text())["events"], 1):
                with self.subTest(example=ex.name, event=n):
                    self.assertIn(e["action"], dur)
                    objs = e.get("object") if isinstance(e.get("object"), list) else [e.get("object")]
                    for o in objs:
                        if not (e["action"] == "wide" and o is None):
                            self.assertIn(o, parts)
                    self.assertTrue((ex / "facts.md").exists())


if __name__ == "__main__":
    unittest.main()
