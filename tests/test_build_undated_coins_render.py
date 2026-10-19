"""Undated coins are shown on the page, not dropped (curator 2026-10-19).

Until then `_assemble_v2_location` dropped every coin with no year at all
(«no year information»), so after the undated-coins plan (docs/
undated_coins_denmark.md) 66 coins still never reached the Denmark page. They
now render in their source's seed_unsorted pen. A coin that carries a real
fuss cannot stand in it without a year (the schema refuses it), so on the page
it is shown in that pen too — the data keeps its classification.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import build  # noqa: E402


class TestUndatedToSeedUnsorted(unittest.TestCase):
    def test_classified_undated_coin_moves_to_its_source_pen(self):
        c = {"id": "unified-kmk-150268", "fuss": "luebischer_muenzfuss", "phase": "I"}
        out, moved = build._undated_to_seed_unsorted([c])
        self.assertEqual((out[0]["fuss"], out[0]["phase"]), ("seed_unsorted", "kmk"))
        self.assertEqual(moved, [("unified-kmk-150268", "luebischer_muenzfuss/I")])
        # The cached dict is not mutated.
        self.assertEqual(c["fuss"], "luebischer_muenzfuss")

    def test_source_tag_from_id(self):
        for cid, src in (("unified-dk-hede-c4h28", "hede"), ("unified-dk-tid-163034", "ucoin"),
                         ("unified-ngc-65873", "ngc")):
            out, _ = build._undated_to_seed_unsorted([{"id": cid, "fuss": "9_thaler", "phase": "I"}])
            self.assertEqual(out[0]["phase"], src, cid)

    def test_dated_and_unsorted_coins_untouched(self):
        dated = {"id": "a", "fuss": "9_thaler", "phase": "I", "year_first": 1625}
        pen = {"id": "b", "fuss": "seed_unsorted", "phase": "kmk"}
        out, moved = build._undated_to_seed_unsorted([dated, pen])
        self.assertIs(out[0], dated)
        self.assertIs(out[1], pen)
        self.assertEqual(moved, [])

    def test_year_label_alone_counts_as_dated(self):
        self.assertFalse(build._is_undated({"year_label": "1625"}))
        self.assertTrue(build._is_undated({"year_ranges": []}))


if __name__ == "__main__":
    unittest.main()
