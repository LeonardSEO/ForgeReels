import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "scripts" / "pipeline"))
import build_timing  # noqa: E402


def w(line, i, text, start):
    return {"line": line, "i": i, "text": text, "start": start, "end": start + 0.3}


class CaptionGroupsTest(unittest.TestCase):
    def test_groups_keep_order_and_limits(self):
        words = [w(1, i, t, i * 0.32) for i, t in enumerate("Most people check their phone ninety-six times a day.".split())]
        words += [w(2, i, t, 4 + i * 0.32) for i, t in enumerate("But only three matter.".split())]
        groups = build_timing.caption_groups(words, maxc=30, maxw=4)
        flat = [x for g in groups for x in g]
        self.assertEqual(flat, words)                                  # every word once, in order
        self.assertTrue(all(len(g) <= 5 for g in groups))
        self.assertTrue(all(len({x["line"] for x in g}) == 1 for g in groups))   # never across lines


if __name__ == "__main__":
    unittest.main()
