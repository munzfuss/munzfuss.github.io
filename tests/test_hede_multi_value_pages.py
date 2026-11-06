"""Hede numbers whose letters are values, not variants (curator 2026-11-06).

Hede 63A-F and 64A-D are the Breddaler of Christian IV, struck «i værdierne
1, 1-1/2, 2, 3, 4 og 6 speciedalere» / «1, 1-1/2, 2 og 3». The seed builder
splits each page into one seed per letter, with the value other sources print
for that letter; the merger compares the full letter for these numbers, so
63D and 63F are different coins while 134A and 134B stay one coin.
"""
from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "scripts"), str(ROOT / "scripts" / "maintenance")]

import merge_seeds_cross_source as m  # noqa: E402

_spec = importlib.util.spec_from_file_location(
    "build_hede_for_multi_value_test",
    ROOT / "scripts" / "maintenance" / "build_hede_denmark_seed.py")
bh = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(bh)


def _coin(hede, **kw):
    return {"id": "x", "ruler": "Christian IV.", "metal": "silver",
            "catalog": {"hede": hede, "hede_volume": "c4h"}, **kw}


class LetterIsValue(unittest.TestCase):
    def chain(self, a, b):
        ra = m._catalog_refs(_coin(a), "danish_realm")
        rb = m._catalog_refs(_coin(b), "danish_realm")
        return m._catalog_chain_consistent(ra, rb)[0]

    def test_breddaler_letters_differ(self):
        self.assertEqual(self.chain("63D", "63F"), "disagree")
        self.assertEqual(self.chain("64B", "64C"), "disagree")
        self.assertEqual(self.chain("63D", "63D"), "agree")

    def test_other_letters_stay_one_coin(self):
        self.assertEqual(self.chain("134A", "134B"), "agree")


class SplitPage(unittest.TestCase):
    def test_split(self):
        page = {"id": "dk-hede-c4h64", "nominal": "1 Breddaler",
                "catalog": {"hede": "64", "hede_volume": "c4h",
                            "schou": "18-28", "sieg": "103-106"},
                "sources": [{"url": "https://www.danskmoent.dk/chr/c4h64.htm"}]}
        other = {"id": "dk-hede-c4h65", "nominal": "1 Speciedaler"}
        coins = [page, other]
        n, gone = bh._split_multi_value_pages(coins)
        self.assertEqual((n, gone), (1, {"dk-hede-c4h64"}))
        by = {c["id"]: c for c in coins}
        self.assertEqual(sorted(by), ["dk-hede-c4h64a", "dk-hede-c4h64b", "dk-hede-c4h64c",
                                      "dk-hede-c4h64d", "dk-hede-c4h65"])
        b = by["dk-hede-c4h64b"]
        self.assertEqual(b["nominal"], "2 Speciedaler")
        self.assertFalse(b["nominal_verified"])
        self.assertEqual(dict(b["catalog"]), {"hede": "64B", "hede_volume": "c4h"})
        self.assertEqual({e["how"] for e in b["uncertainty"]["nominal"]}, {"other_source"})
        self.assertEqual(by["dk-hede-c4h64a"]["nominal"], "Breddaler")
        self.assertNotIn("uncertainty", by["dk-hede-c4h64a"])


if __name__ == "__main__":
    unittest.main()
