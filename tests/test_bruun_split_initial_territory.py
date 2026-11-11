"""A territory heading whose initial capital the PDF text layer splits off
(«S chleswig-Holstein-Schaumburg-Pinneberg», Bruun Part II lots 14262 and
14269) is still a territory, not the denomination (curator 2026-11-11).

Before the fix the strip loop failed to recognise «S chleswig-…» and kept it
as the nominal («1 S chleswig-Holstein-Schaumburg-Pinneberg»), dropping the
printed «Double Taler».

Run:
    .venv/bin/python -m unittest tests.test_bruun_split_initial_territory -v
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "maintenance"))

import build_bruun_denmark_seed as b  # noqa: E402


class SplitInitialTerritory(unittest.TestCase):
    def test_split_initial_heading_is_a_territory(self):
        meta = ("GERMANY . S chleswig-Holstein-Schaumburg-Pinneberg. Double Taler, "
                "1603. Ernst III. NGC AU Details—Mount Removed.")
        self.assertEqual(b.parse_denomination(meta, None), "Double Taler")

    def test_whole_heading_unchanged(self):
        meta = "GERMANY . Schleswig-Holstein-Schaumburg-Pinneberg. Taler, 1589. x"
        self.assertEqual(b.parse_denomination(meta, None), "Taler")

    def test_denomination_first_lot_unchanged(self):
        self.assertEqual(b.parse_denomination(
            "DENMARK. Skilling. Mint Error — x, 1600", None), "Skilling")


if __name__ == "__main__":
    unittest.main()
