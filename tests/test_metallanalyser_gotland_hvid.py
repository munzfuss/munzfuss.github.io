"""Lindblad 2017:3 Gotland — which rows reach the seed (2026-10-25).

Only the hvid enters beside the one printed Galster concordance (LL 7b =
G 142): Lindblad s. 4 places the change to the Danish reckoning at c. 1450
(«den nya valören hvid introducerades och ersatte gotarna … En hvid motsvarade
fyra penningar»), and the curator takes from this issue only what fits the
Lybsk Møntfod. Gote (ørtug) and W-brakteat penning stay out; each LL number is
its own row, carrying the LL number and Lindblad's period as an unverified year.
Live cache test: reads the parsed appendix in scripts/cache.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "maintenance"))

import build_metallanalyser_seed as bm  # noqa: E402


class GotlandRows(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        coins, _ = bm.collect()
        cls.gotland = {c["id"]: c for c in coins if c["id"].startswith("metallanalyser-2017-3-")}

    def test_only_hvid(self):
        self.assertTrue(self.gotland)
        self.assertEqual({c["nominal"] for c in self.gotland.values()}, {"1 Hvid"})

    def test_window_1450_1520(self):
        for c in self.gotland.values():
            if c["year_first"] is None:          # G 142: undated as before
                continue
            self.assertGreaterEqual(c["year_first"], 1450, c["id"])
            self.assertLessEqual(c["year_last"], 1520, c["id"])

    def test_lagerqvist_rows_are_unverified_and_carry_no_galster(self):
        c = self.gotland["metallanalyser-2017-3-ll4a-gotland"]
        self.assertEqual(c["catalog"], {"others": ["Lagerqvist# 4a"]})
        self.assertEqual((c["year_label"], c["year_verified"]), ("1455-1480", False))

    def test_doubtful_numbers_stay_apart(self):
        self.assertIn("metallanalyser-2017-3-ll4aq-gotland", self.gotland)
        self.assertIn("metallanalyser-2017-3-ll4aqq-gotland", self.gotland)

    def test_printed_concordance_unchanged(self):
        self.assertEqual(self.gotland["metallanalyser-2017-3-g142-gotland"]["catalog"]["galster"],
                         "142")


if __name__ == "__main__":
    unittest.main()
