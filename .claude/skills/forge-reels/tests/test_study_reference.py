import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))
from study_reference import sentences, theme_segments  # noqa: E402


class StudyReference(unittest.TestCase):
    def test_theme_runs_are_merged_and_switches_are_visible(self):
        segs = theme_segments([20, 25, 30, 200, 210, 120, 15], 0.5)
        self.assertEqual(segs, [(0.0, 1.5, "dark"), (1.5, 2.5, "light"), (2.5, 3.0, "mid"), (3.0, 3.5, "dark")])

    def test_sentences_split_on_end_punctuation_and_keep_the_start_time(self):
        words = [{"word": "This", "start": 0.1, "end": 0.3}, {"word": "works.", "start": 0.3, "end": 0.6},
                 {"word": "Really", "start": 1.0, "end": 1.3}, {"word": "well", "start": 1.3, "end": 1.6}]
        self.assertEqual(sentences(words), [(0.1, "This works."), (1.0, "Really well")])


if __name__ == "__main__":
    unittest.main()
