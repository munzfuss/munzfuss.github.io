"""MB numbers date ruler-less medieval pennies through the Hauberg/MB concordance.

Curator 2026-10-17 (docs/undated_coins_denmark.md row 3): KMM pennies with an
MB (Mansfeld-Bülow) number but no ruler sat off the Denmark page for lack of a
year. danskmoent's concordance (konkord.htm) gives, per row, a ruler WITH his
years and a mint, and the MB numbers that belong to it — so an MB number pins
the period the source itself states. Two traps are pinned here: the source
misprint «2/224-427» in Erik Menved's Nørrejylland row (taken literally it
claims MB 224-427 and makes half of Erik Klipping ambiguous), and KMM's short
range «541-46». The same row-3 analysis found the concordance contradicting
one KMM attribution: MB 640 is «Skåne under Magnus Smek», not Christoffer II.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from lib.mb_concordance import mb_lookup, mb_window, nominal_window  # noqa: E402


class TestMbConcordance(unittest.TestCase):
    def test_numbers_resolve_to_the_rows_own_years(self):
        self.assertEqual(mb_lookup("261")[:2], (1259, 1286))   # Erik Klipping, Slesvig
        self.assertEqual(mb_lookup("285")[:2], (1286, 1319))   # Erik Menved, Lund
        self.assertEqual(mb_lookup("083")[:2], (1252, 1259))   # Christoffer 1., Roskilde

    def test_misprint_range_is_dropped_not_repaired(self):
        # «2/224-427» after «1/423»: not a claim on MB 224-427.
        self.assertEqual(mb_lookup("261")[2], "Erik Klipping")
        self.assertIsNone(mb_lookup("424"))

    def test_mb_640_is_magnus_smek(self):
        self.assertEqual(mb_lookup("640"), (1332, 1360, "Skåne under Magnus Smek", "Lund"))

    def test_kmm_short_range_and_lists(self):
        self.assertEqual(mb_window(["541", "541-46"]), (1319, 1332))
        self.assertEqual(mb_window("266-269"), (1259, 1286))

    def test_two_rulers_stay_undated(self):
        # The thinning-salvage record kmk-138263 (Erik Menved + Christoffer II).
        self.assertIsNone(mb_window(["285", "500", "566-567"]))

    def test_gap_in_the_concordance_is_not_filled(self):
        # Lund under Erik Menved lists 22/318 then 24/321: no 319-320.
        self.assertIsNone(mb_window(["285", "287", "319-320"]))

    def test_kobbersterling(self):
        self.assertEqual(nominal_window("1 Kobbersterling"), (1420, 1435))
        self.assertEqual(nominal_window("1 Kobbersterling?"), (1420, 1435))
        self.assertIsNone(nominal_window("1 Hvid"))


if __name__ == "__main__":
    unittest.main()
