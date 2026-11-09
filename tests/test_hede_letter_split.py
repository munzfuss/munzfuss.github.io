"""Hede parser: a combined spec block «Hede 12AB, Schou 17-18, 19, Sieg 73,1
og 76» gives one entry per letter, values in letter order (curator 2026-11-09)."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import parse_hede as P  # noqa: E402


class LetterGroups(unittest.TestCase):
    def test_groups_in_letter_order(self):
        g = P._label_letter_groups(
            "1 Dukat\nHede 12AB, Schou 17-18, 19, Sieg 73,1 og 76\n", "12AB")
        self.assertEqual(g, {"Schou": ["17-18", "19"], "Sieg": ["73.1", "76"]})

    def test_sieg_comma_list_vs_decimal(self):
        self.assertEqual(P._split_ref_groups("Sieg", "81,83"), ["81", "83"])
        self.assertEqual(P._split_ref_groups("Sieg", "73,1 og 76"), ["73.1", "76"])
        self.assertEqual(P._split_ref_groups("Schou", "7,9"), ["7", "9"])

    def test_single_letter_tag_not_grouped(self):
        self.assertEqual(P._label_letter_groups("Hede 13A, Schou 8, Sieg 74", "13A"), {})

    def test_split_only_on_matching_count(self):
        spec = {"bruttovægt_g": 1.745,
                "_letter_groups": {"Schou": ["36-37"], "Sieg": ["72", "75"]}}
        out = P._split_combined_letter_keys({"14AB": spec}, {})
        self.assertEqual(sorted(out), ["14A", "14B"])
        self.assertEqual(out["14A"]["catalog_refs"], {"Schou": ["36-37"], "Sieg": ["72"]})
        self.assertEqual(out["14B"]["catalog_refs"], {"Schou": ["36-37"], "Sieg": ["75"]})
        self.assertNotIn("_letter_groups", out["14A"])
        keep = {"bruttovægt_g": 1, "_letter_groups": {"Schou": ["36-37"]}}
        self.assertEqual(sorted(P._split_combined_letter_keys({"14AB": keep}, {})), ["14AB"])

    def test_page_c5h12(self):
        html = (ROOT / "scripts/cache/hede/c5h12.htm").read_text(encoding="latin-1")
        bh = P.parse_one(html, "c5h12")["specs"]["by_hede"]
        self.assertEqual(bh["12A"]["catalog_refs"], {"Schou": ["17-18"], "Sieg": ["73.1"]})
        self.assertEqual(bh["12B"]["catalog_refs"], {"Schou": ["19"], "Sieg": ["76"]})
        self.assertEqual(bh["12B"]["bruttovægt_g"], 3.49)


if __name__ == "__main__":
    unittest.main()
