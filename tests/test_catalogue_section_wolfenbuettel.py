"""Christian IV's Wolfenbüttel coinage numbers Hede and Schou on its own
(curator 2026-10-18; danskmoent «Hede Wolfenbüttel 3A / 3B / 5», Schou 4-16).

`_catalog_refs` scopes its Hede and Schou keys to the section, so a
Wolfenbüttel «Hede 5» no longer collides with Hede Norge 5; and because the
scoped keys can no longer DISAGREE with a Danish number, `match_pair` treats
«one side in the section, the other not, both citing Hede/Schou» as no_match
(KMM «H 55», København, had slid into Hede W3 on nominal + year).
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
sys.path.insert(0, str(PROJECT_ROOT / "scripts" / "maintenance"))

import merge_seeds_cross_source as M  # noqa: E402

W5 = {"id": "dk-bruun-5536", "ruler": "Christian IV.", "mint": "Wolfenbüttel",
      "metal": "silver", "nominal": "1 Speciedaler", "year_first": 1627,
      "year_last": 1627, "catalog": {"hede": "5", "schou": "11", "sieg": "196"}}
NORGE5 = {"id": "dk-bruun-9319", "ruler": "Christian IV", "mint": "Christiania",
          "metal": "silver", "nominal": "1 Speciedaler", "year_first": 1629,
          "year_last": 1629, "catalog": {"hede": "5A", "km": "12"}}
KMM_H55 = {"id": "kmk-348808", "ruler": "Christian 4", "mint": None,
           "metal": "silver", "nominal": "1 Daler", "year_first": 1627,
           "year_last": 1627, "catalog": {"hede": "55"}}


class Section(unittest.TestCase):
    def test_wolfenbuettel_keys_are_scoped(self):
        refs = M._catalog_refs(W5, "danish_realm")
        self.assertIn("hede/christian iv/wolfenbüttel", refs)
        self.assertIn("schou/christian iv/wolfenbüttel", refs)
        self.assertIn("sieg/christian iv", refs)          # Sieg runs on

    def test_other_mints_unscoped(self):
        self.assertIn("hede/christian iv", M._catalog_refs(NORGE5, "danish_norway"))
        self.assertIsNone(M._catalogue_section(NORGE5))

    def test_hede_volume_marks_the_section(self):
        c = {"id": "x", "ruler": None, "mint": None,
             "catalog": {"hede": "3", "hede_volume": "c4wolfh"}}
        self.assertEqual(M._catalogue_section(c), "wolfenbüttel")

    def test_section_vs_main_is_no_match(self):
        r = M.match_pair(W5, KMM_H55, "danish_realm")
        self.assertEqual(r["decision"], "no_match")
        self.assertIn("catalogue section differs", r["why"][0])


if __name__ == "__main__":
    unittest.main()
