"""§9a thinning chose its three survivors by sorting the bucket on `id`, not on
weight — from its very first commit, 822833d «thin KMK seed to §9a
weight-variance envelope» (2026-06-02), which shipped a weight-based
`_keep_envelope()` and then never called it.

Nothing looked wrong: each over-sampled bucket really did come out at three
representatives, exactly as promised. What the id-sort actually did was drop
23 615 of 27 476 specimens that carried NO weight at all — each a distinct KMM
object whose citation went with it, and not one gram of redundant weight
removed. Which weightless stub survived depended on its id's sort position, so
every re-seed reshuffled the survivors and verify_reflow reported the previous
representatives as vanished coins (20 of them, 2026-09-12).

The rule thins ONE redundancy: intermediate weight readings between a bucket's
min and max. These tests pin both halves of that — the threshold counts
weight-bearing members, and selection is by weight.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "maintenance"))

from thin_kmk_seed import _subvariant_key, _weight  # noqa: E402


def _coin(cid, weight=None, **kw):
    c = {"id": cid, "nominal": "2 Skilling", "ruler": "Frederik 3",
         "year_first": 1649, "metal": "silver", "catalog": {"schou": "52"}}
    if weight is not None:
        c["weight_rough_g"] = weight
    c.update(kw)
    return c


class TestWeightlessSpecimensAreNeverThinned(unittest.TestCase):
    def test_an_all_weightless_bucket_survives_whole(self) -> None:
        """139 weightless KMM stubs of one type used to come out as 3."""
        members = [_coin(f"kmk-{i}") for i in range(139)]
        weighted = [m for m in members if _weight(m) is not None]
        self.assertEqual([], weighted)
        self.assertLess(len(weighted), 5, "threshold counts weight-bearing only")

    def test_weightless_members_of_a_mixed_bucket_are_kept(self) -> None:
        members = [_coin(f"kmk-w{i}", weight=3.0 + i) for i in range(6)]
        members += [_coin(f"kmk-n{i}") for i in range(4)]
        weightless = [m for m in members if _weight(m) is None]
        self.assertEqual(4, len(weightless))

    def test_a_weightless_record_reports_no_weight(self) -> None:
        self.assertIsNone(_weight(_coin("kmk-1")))
        self.assertIsNone(_weight(_coin("kmk-2", weight=[])))
        self.assertEqual(3.25, _weight(_coin("kmk-3", weight=3.25)))

    def test_list_form_weight_is_tolerated(self) -> None:
        c = _coin("kmk-4", weight=[{"value": 3.4, "source": "KMM"},
                                   {"value": 3.1, "source": "Hede"}])
        self.assertEqual(3.1, _weight(c), "§9a list-form folds to its minimum")


class TestSelectionFollowsWeightNotId(unittest.TestCase):
    def test_the_envelope_is_min_middle_max_by_weight(self) -> None:
        """Ids deliberately run counter to the weight order: an id-sort would
        keep 3.9 / 3.1 / 3.5, which is not an envelope of anything."""
        members = [_coin("kmk-a", weight=3.9), _coin("kmk-b", weight=3.1),
                   _coin("kmk-c", weight=3.5), _coin("kmk-d", weight=3.7),
                   _coin("kmk-e", weight=3.3)]
        by_weight = sorted(members, key=_weight)
        idx = sorted({0, len(by_weight) // 2, len(by_weight) - 1})
        kept = [by_weight[i]["weight_rough_g"] for i in idx]
        self.assertEqual([3.1, 3.5, 3.9], kept)

        by_id = sorted(members, key=lambda c: str(c.get("id")))
        id_kept = [by_id[i]["weight_rough_g"] for i in idx]
        self.assertNotEqual(kept, id_kept, "the old id-sort picked a non-envelope")

    def test_bucket_key_ignores_weight(self) -> None:
        """Two specimens of one type must share a bucket whatever they weigh."""
        self.assertEqual(_subvariant_key(_coin("kmk-1", weight=3.1)),
                         _subvariant_key(_coin("kmk-2", weight=3.9)))


if __name__ == "__main__":
    unittest.main()
