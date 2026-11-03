"""Three ways the weight gate kept a record out of the type its catalogue names.

Found 2026-11-03 while closing cases 14 and 16 of the reign-gate review: KMM
«H 151B» at 0.31 g (a weight the curator had already marked suspect) failed
the 2.5x gate against Hede 151; KMM «H:99D; Sch:20» failed the 5 % gate
against Hede 99D because «Schou 20» was compared as a string with Hede's
«20-21», and Hede 99D against a bare «99» counted as a disagreement. A corpus
count put ~116 records outside the class of their own number. The curator
ruled (2026-11-03): a suspect weight does not stand for the type; a number
inside the other side's range agrees; a same-base sub-variant is a weaker
agreement, refused only when another shared index really disagrees
(Hede 999A = KM 999 against Hede 999B = KM 998). None of this surfaced as an
error — the records simply sat in seed_unsorted next to their type.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "maintenance"))

import merge_seeds_cross_source as m  # noqa: E402


class SuspectWeightDoesNotStandForTheType(unittest.TestCase):
    def test_suspect_reading_is_left_out(self):
        coin = {"weight_rough_g": [{"value": 0.31, "source": "kmk",
                                    "suspect": {"en": "clipped"}}]}
        self.assertIsNone(m._weight_repr(coin))

    def test_unmarked_readings_still_count(self):
        coin = {"weight_rough_g": [{"value": 0.31, "source": "kmk", "suspect": {"en": "x"}},
                                   {"value": 1.2, "source": "kmk"}]}
        self.assertEqual(m._weight_repr(coin), 1.2)


class RangesAndSubVariants(unittest.TestCase):
    def test_schou_inside_range_agrees(self):
        self.assertTrue(m._catalog_strongly_agrees(
            {"hede/c4": "99D", "schou/c4": "20"},
            {"hede/c4": "99D", "schou/c4": "14-42|2-8|20-21|5-21|84-88"}))

    def test_same_base_subvariant_plus_sieg_base_agrees(self):
        self.assertTrue(m._catalog_strongly_agrees(
            {"hede/c4": "99A", "sieg/c4": "75.1"},
            {"hede/c4": "99", "sieg/c4": "75"}))

    def test_subvariant_alone_does_not_carry(self):
        self.assertFalse(m._catalog_strongly_agrees(
            {"hede/c4": "99A"}, {"hede/c4": "99B"}))

    def test_correlated_disagreement_refuses(self):
        self.assertFalse(m._catalog_strongly_agrees(
            {"hede/c4": "999A", "km/dk": "999"},
            {"hede/c4": "999B", "km/dk": "998"}))

    def test_index_bases(self):
        self.assertEqual(m._index_bases("99D"), {"99"})
        self.assertEqual(m._index_bases("340.2"), {"340"})
        self.assertEqual(m._index_bases("92AB|93"), {"92", "93"})


if __name__ == "__main__":
    unittest.main()
