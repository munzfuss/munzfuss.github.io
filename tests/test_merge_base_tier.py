"""Two records to which Hede, Galster or a volume-scoped KM give one base number
are one coin (§9.4); a Krause letter is a separate type, a Krause decimal is not.

Before 2026-11-12 a year or mint difference voted against the merge, so the
sub-letters of one Hede number (Hede 2B / 2C / 2D, printed on one danskmoent
page) fell into separate classes. The base-tier rule (`_base_tier_agrees`)
makes the shared base carry the merge while any shared type catalogue that
gives two different bases still refuses it (KM 66 = Hede 118 against KM 67 =
Hede 119). Bare KM restarts per Krause volume and so can refuse but never
carry; Sieg is left out, its Christian VII numbering changed between editions
(SOURCES §13.12).
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "maintenance"))

import merge_seeds_cross_source as M  # noqa: E402


class KmTypeBases(unittest.TestCase):
    def test_decimal_dropped_letter_kept(self):
        self.assertEqual(M._km_type_bases("340.2"), {"340"})
        self.assertEqual(M._km_type_bases("39a"), {"39A"})
        self.assertEqual(M._km_type_bases("A433"), {"A433"})
        self.assertEqual(M._km_type_bases("237|237a"), {"237", "237A"})


class BaseTierAgrees(unittest.TestCase):
    def test_hede_sub_letters_carry(self):
        self.assertTrue(M._base_tier_agrees({"hede": "2B"}, {"hede": "2D"}))

    def test_galster_carries(self):
        self.assertTrue(M._base_tier_agrees({"galster": "95A"}, {"galster": "95B"}))

    def test_scoped_km_carries(self):
        self.assertTrue(M._base_tier_agrees({"km/dk": "340.1"}, {"km/dk": "340.2"}))

    def test_bare_km_alone_does_not_carry(self):
        self.assertFalse(M._base_tier_agrees({"km": "340"}, {"km": "340"}))

    def test_other_shared_catalogue_refuses(self):
        """Hede agrees on the base, KM disagrees: two types."""
        self.assertFalse(M._base_tier_agrees({"hede": "118", "km": "66"},
                                             {"hede": "118", "km": "67"}))

    def test_krause_letter_is_another_type(self):
        self.assertFalse(M._base_tier_agrees({"hede": "39", "km": "39"},
                                             {"hede": "39", "km": "39a"}))

    def test_different_hede_bases(self):
        self.assertFalse(M._base_tier_agrees({"hede": "118"}, {"hede": "119"}))

    def test_sieg_is_ignored(self):
        self.assertTrue(M._base_tier_agrees({"hede": "25", "sieg": "19"},
                                            {"hede": "25", "sieg": "26"}))


class SharesLoadBase(unittest.TestCase):
    def test_load_base_regardless_of_other_disagreement(self):
        self.assertTrue(M._shares_load_base({"hede": "118", "km": "66"},
                                            {"hede": "118", "km": "67"}))

    def test_bare_km_is_not_a_load_register(self):
        self.assertFalse(M._shares_load_base({"km": "340"}, {"km": "340"}))


if __name__ == "__main__":
    unittest.main()
