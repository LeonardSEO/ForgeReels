import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "scripts"))
from logo import commons_choice, pick, slugify  # noqa: E402

ICONS = [{"title": "Instagram", "hex": "FF0069"}, {"title": "Hugging Face", "hex": "FFD21E"},
         {"title": "Node.js", "hex": "5FA04E"}, {"title": "C++", "hex": "00599C", "slug": "cplusplus"}]


class Logo(unittest.TestCase):
    def test_slug_rule_spells_out_symbols(self):
        self.assertEqual([slugify(t) for t in ("Hugging Face", "Node.js", "C++", "AT&T")],
                         ["huggingface", "nodedotjs", "cplusplus", "atandt"])

    def test_pick_matches_by_title_or_slug_whatever_the_case(self):
        self.assertEqual(pick("hugging face", ICONS)["hex"], "FFD21E")
        self.assertEqual(pick("NodeDotJS", ICONS)["title"], "Node.js")
        self.assertEqual(pick("c++", ICONS)["slug"], "cplusplus")
        self.assertIsNone(pick("Not A Brand", ICONS))

    def test_commons_prefers_the_plain_brand_logo_over_a_product_logo(self):
        svg = {"imageinfo": [{"mime": "image/svg+xml", "url": "u"}]}
        pages = [dict(svg, title="File:Microsoft Office logos (2013-2019).svg", index=1),
                 dict(svg, title="File:Microsoft logo (2012).svg", index=2),
                 dict(title="File:Microsoft logo.jpg", index=3, imageinfo=[{"mime": "image/jpeg"}]),
                 dict(svg, title="File:Windows wordmark.svg", index=4)]
        self.assertEqual(commons_choice("Microsoft", pages)[0], "File:Microsoft logo (2012).svg")
        self.assertIsNone(commons_choice("Sony", pages))


if __name__ == "__main__":
    unittest.main()
