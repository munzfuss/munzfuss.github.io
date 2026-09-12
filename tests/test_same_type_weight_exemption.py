"""One Christian IV «2 Skilling lybsk» came out of the merger as three unified
entries. The four KMM specimens behind it were identical on every field the
merger reads — nominal, ruler, 1616-1625, Glückstadt, silver, Hede 168 — and
differed only in what they weighed: 0.81, 0.948, 0.995, 1.11 g.

The >5%-divergence gate did it. That gate (curator direction 2026-05-22) asks
for two shared agreeing catalogue refs before it will accept a weight spread,
and it was written for the cross-source case: Bruun's 8 Skilling at 2.72 g
citing «Galster 93» against Galster's own 3.32 g is not one coin. But a KMM
record carries a single Hede number and nothing else, so two specimens of one
type can never reach two shared refs, and 1.11 against 0.948 is 17% — ordinary
wear on a sub-gram billon Skilling.

Nothing looked broken: each fragment was a well-formed entry. It surfaced only
because the §9a thinning keeps a bucket's weight extremes, which are precisely
the specimens most likely to trip the gate — so the two subsystems worked
against each other, and a final entry lost its own envelope. Measured over the
corpus, 191 types whose every catalogue field agreed had been split this way.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "maintenance"))

from merge_seeds_cross_source import _same_type_but_for_weight  # noqa: E402

KMM = {"nominal": "2 Skilling lybsk", "ruler": "Christian 4",
       "year_first": 1616, "year_last": 1625, "mint": "Glückstadt",
       "metal": "silver", "catalog": {"hede": "168"}}


def spec(weight, **kw):
    return {**KMM, "weight_rough_g": weight, **kw}


class TestExemptionFires(unittest.TestCase):
    def test_wear_alone_does_not_make_two_coins(self) -> None:
        self.assertTrue(_same_type_but_for_weight(spec(1.11), spec(0.948)))

    def test_it_holds_across_the_whole_observed_spread(self) -> None:
        for w in (0.81, 0.948, 0.995, 1.11):
            self.assertTrue(_same_type_but_for_weight(spec(w), spec(1.11)))


class TestExemptionCannotBecomeAnOverMerge(unittest.TestCase):
    """It must never let weight similarity stand in for catalogue evidence."""

    def test_a_different_catalogue_base_is_refused(self) -> None:
        """Hede 1 / Schou 24 against Hede 5A / Schou 3 — §9.4 distinct coins,
        and 1.13x apart, so a widened tolerance would have merged them."""
        a = spec(28.9, catalog={"hede": "1", "schou": "24"})
        b = spec(25.6, catalog={"hede": "5A", "schou": "3"})
        self.assertFalse(_same_type_but_for_weight(a, b))

    def test_no_shared_catalogue_at_all_is_refused(self) -> None:
        a = spec(1.0, catalog={"galster": "155"})
        b = spec(1.33, catalog={"schou": "170"})
        self.assertFalse(_same_type_but_for_weight(a, b))

    def test_an_empty_catalogue_proves_nothing(self) -> None:
        self.assertFalse(_same_type_but_for_weight(spec(1.0, catalog={}),
                                                   spec(1.2, catalog={})))
        self.assertFalse(_same_type_but_for_weight(spec(1.0, catalog=None),
                                                   spec(1.2, catalog=None)))

    def test_every_type_field_still_has_to_agree(self) -> None:
        for field, other in (("nominal", "1 Skilling"), ("ruler", "Frederik 3"),
                             ("year_first", 1667), ("year_last", 1670),
                             ("mint", "Altona"), ("metal", "billon")):
            with self.subTest(field=field):
                self.assertFalse(
                    _same_type_but_for_weight(spec(1.11), spec(0.948, **{field: other})))


if __name__ == "__main__":
    unittest.main()
