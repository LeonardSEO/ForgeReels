import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "scripts" / "pipeline"))
import explainer_cues as ec  # noqa: E402

EV = [{"t": 0.0, "dur": 1.6, "action": "focus", "object": "hero", "word": "This"},
      {"t": 0.1, "dur": 6.0, "action": "play", "object": "hero", "word": "Liquid"},
      {"t": 4.5, "dur": 0.5, "action": "reveal", "object": "note", "word": "glass"},
      {"t": 4.6, "dur": 0.3, "action": "reveal", "object": "note.l1", "word": "glass"},
      {"t": 8.2, "dur": 0.4, "action": "strike", "object": "note", "word": "Real"},
      {"t": 9.0, "dur": 0.7, "action": "highlight", "object": "doc.l1", "word": "rim"}]


class CuesTest(unittest.TestCase):
    def test_actions_become_sound_roles_and_parts_stay_quiet(self):
        cues = ec.cues_from_events(EV, anchors=["Real"])
        roles = {(c["t"], c["role"]) for c in cues}
        self.assertIn((0.0, "whoosh.short"), roles)
        self.assertIn((4.5, "land.light"), roles)
        self.assertIn((8.2, "hit"), roles)
        self.assertNotIn(0.1, [c["t"] for c in cues])            # play has no sound
        self.assertNotIn(4.6, [c["t"] for c in cues])            # a part's reveal is not a new object

    def test_anchor_words_lock_to_the_beat_and_others_follow_the_word(self):
        cues = ec.cues_from_events(EV, anchors=["Real"])
        lock = {c["t"]: c["lock"] for c in cues}
        self.assertEqual(lock[8.2], "anchor")
        self.assertEqual(lock[4.5], "word")

    def test_sounds_closer_than_the_minimum_gap_are_thinned(self):
        cues = ec.cues_from_events([dict(EV[2], t=1.0), dict(EV[2], t=1.1, object="x")], anchors=[], min_gap=0.3)
        self.assertEqual(len(cues), 1)


if __name__ == "__main__":
    unittest.main()
