"""Hede builder: metal from the reign index, and a page split per letter by mint
(curator 2026-11-07, Hede-base type Ж).

- A deep page that names no metal took «silver» by default and was marked
  verified because it printed a weight; Hede Norge 6 (1 Skilling 1812) is
  «Kobber» in the index (f6hede.htm, row N6).
- f6h15: «A) … (Altona; Hede 15A …) B) … (Kongsberg; Hede Danmark 15B …)»,
  15B «må nu anses for norsk … Hede Norge 6»: one seed per letter, each routed
  by its own mint.

The overview test reads the harvest cache (MUNZFUSS_HARVEST_DIR); it is
skipped when the cache is absent.

Run:
    .venv/bin/python -m unittest tests.test_hede_overview_metal_and_letter_split -v
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "scripts"), str(ROOT / "scripts" / "maintenance")]

import build_hede_denmark_seed as b  # noqa: E402


class OverviewMetal(unittest.TestCase):
    def setUp(self):
        if not any(b.HEDE_CACHE.glob("f6hede*.htm")):
            self.skipTest("harvest cache not available")

    def test_norwegian_row_and_danish_row(self):
        self.assertEqual(b._overview_metal("nf6h", "6"), "copper")
        self.assertEqual(b._overview_metal("f6h", "6"), "silver")
        self.assertEqual(b._overview_metal("c4h", "19"), "gold")

    def test_lauenborg_row(self):
        self.assertEqual(b._overview_metal("f6hl", "1"), "silver")


class LetterSplit(unittest.TestCase):
    def test_f6h15_split_by_mint(self):
        coins = [{"id": "dk-hede-f6h15", "year_first": 1812, "nominal": "1 Skilling",
                  "catalog": {"hede": "15", "hede_volume": "f6h"},
                  "mint": ["Altona", "Kongsberg"], "issuing_entity": ["danish_norway", "royal_holstein"]}]
        n, gone = b._split_letter_pages(coins)
        self.assertEqual(n, 1)
        self.assertEqual(gone, {"dk-hede-f6h15"})
        by = {c["id"]: c for c in coins}
        self.assertEqual(by["dk-hede-f6h15a"]["mint"], "Altona")
        self.assertEqual(by["dk-hede-f6h15a"]["catalog"]["schou"], "7")
        self.assertEqual(by["dk-hede-f6h15b"]["mint"], "Kongsberg")
        self.assertEqual(by["dk-hede-f6h15b"]["issuing_entity"], "danish_norway")
        self.assertEqual(by["dk-hede-f6h15b"]["catalog"]["hede"], "15B")


if __name__ == "__main__":
    unittest.main()
