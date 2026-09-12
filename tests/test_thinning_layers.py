"""§9a thinning ran at the wrong layer for two and a half months.

The rule states its own unit: «one coin entry has ≥5 `weight_rough_g` entries
from a single resource». That unit exists only AFTER the cross-source merge,
and the retired thin_intra_subvariant_specimens.py said so plainly — «After
§9a multi-specimen merge, all of those weights live in `weight_rough_g` and
all of their citations live in `sources[]`». It trimmed a LIST inside one coin.

When V1 was torn down (2026-06-24) the replacement was rebuilt at the SEED
layer, and the relocation was never recorded as a change of meaning. At seed
level each record carries one scalar weight, so «≥5 entries from a single
resource» cannot be evaluated; the implementation reinterpreted it as «≥5
records in a bucket» and grouped by its own key, which is not the merger's.
Consequences, all measured: keeping a bucket's true extremes sent them to
other unified entries than the intermediate readings had come from, so the
coin the reader sees lost its envelope (6 of 8 affected ikmk entries came out
narrower, five collapsed to a single reading); and because it deleted records
rather than trimming a list, every re-seed removed coins from final/.

Dropping seed thinning altogether was worse in a different way: the merger's
pairwise pass went from ~20 minutes to 2 entities in 20 minutes on a kmk seed
of 41 490 records against 14 152.

So the two layers now do different jobs, and these tests pin the boundary.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "maintenance"))

from lib.seed_thin import thin_safe  # noqa: E402
from thin_final_weight_lists import thin_coin  # noqa: E402


def rec(cid, weight=None, **kw):
    c = {"id": cid, "nominal": "2 Skilling", "ruler": "Christian 4",
         "year_first": 1625, "metal": "silver", "catalog": {"hede": "134a"}}
    if weight is not None:
        c["weight_rough_g"] = weight
    c.update(kw)
    return c


def reading(v, source="kmk", **kw):
    return {"value": v, "source": source, **kw}


class TestSeedLayerRemovesOnlyWhatCannotMoveAWeight(unittest.TestCase):
    def test_every_distinct_weight_survives(self) -> None:
        recs = [rec(f"kmk-{i}", w) for i, w in
                enumerate([1.11, 1.35, 0.27, 1.5, 1.07, 0.53])]
        kept, _ = thin_safe(recs)
        self.assertEqual({1.11, 1.35, 0.27, 1.5, 1.07, 0.53},
                         {c["weight_rough_g"] for c in kept})

    def test_same_weight_twins_collapse_to_one(self) -> None:
        recs = [rec("kmk-1", 1.11), rec("kmk-2", 1.11), rec("kmk-3", 1.11)]
        kept, stats = thin_safe(recs)
        self.assertEqual(1, len(kept))
        self.assertEqual(2, stats["dropped"])

    def test_the_bucket_extremes_are_never_candidates(self) -> None:
        recs = [rec(f"kmk-{i}", w) for i, w in enumerate([0.27, 0.9, 0.9, 1.35])]
        kept, _ = thin_safe(recs)
        ws = sorted(c["weight_rough_g"] for c in kept)
        self.assertEqual(0.27, ws[0])
        self.assertEqual(1.35, ws[-1])

    def test_weightless_excess_goes_but_three_stay(self) -> None:
        recs = [rec(f"kmk-{i}") for i in range(139)]
        kept, _ = thin_safe(recs)
        self.assertEqual(3, len(kept))

    def test_a_curated_record_is_never_dropped(self) -> None:
        recs = [rec("kmk-1", 1.11), rec("kmk-2", 1.11),
                rec("kmk-held", 1.11, _curation_holds={"mint": "curator call"})]
        kept, _ = thin_safe(recs)
        self.assertIn("kmk-held", {c["id"] for c in kept})


class TestMergedLayerComputesTheEnvelope(unittest.TestCase):
    def test_min_middle_max_of_one_resource(self) -> None:
        coin = {"id": "unified-x", "weight_rough_g":
                [reading(v) for v in (1.0, 1.1, 1.2, 1.3, 1.4, 1.5)]}
        dropped = thin_coin(coin)
        ws = sorted(e["value"] for e in coin["weight_rough_g"])
        self.assertEqual(3, dropped)
        self.assertEqual(1.0, ws[0])
        self.assertEqual(1.5, ws[-1])

    def test_resources_are_counted_separately(self) -> None:
        coin = {"id": "unified-x", "weight_rough_g":
                [reading(v) for v in (1.0, 1.1, 1.2, 1.3, 1.4)]
                + [reading(2.0, "bruun"), reading(2.1, "bruun")]}
        thin_coin(coin)
        srcs = [e["source"] for e in coin["weight_rough_g"]]
        self.assertEqual(2, srcs.count("bruun"), "a resource under 5 is untouched")
        self.assertEqual(3, srcs.count("kmk"))

    def test_a_marked_reading_is_kept(self) -> None:
        """§4 keeps a curator's disbelief visible instead of deleting it."""
        coin = {"id": "unified-x", "weight_rough_g":
                [reading(v) for v in (1.0, 1.1, 1.2, 1.3, 1.4)]
                + [reading(813.0, erroneous={"en": "decimal shift"})]}
        thin_coin(coin)
        vals = [e["value"] for e in coin["weight_rough_g"]]
        self.assertIn(813.0, vals)

    def test_divergent_fineness_blocks_thinning(self) -> None:
        """§9a: «If the bucket includes multiple fineness readings, do not
        thin: the variance is informative»."""
        coin = {"id": "unified-x",
                "fineness": [{"value": 0.281, "source": "hede"},
                             {"value": 0.375, "source": "numista"}],
                "weight_rough_g": [reading(v) for v in (1.0, 1.1, 1.2, 1.3, 1.4)]}
        self.assertEqual(0, thin_coin(coin))
        self.assertEqual(5, len(coin["weight_rough_g"]))

    def test_it_is_idempotent(self) -> None:
        coin = {"id": "unified-x", "weight_rough_g":
                [reading(v) for v in (1.0, 1.1, 1.2, 1.3, 1.4, 1.5)]}
        thin_coin(coin)
        self.assertEqual(0, thin_coin(coin), "a trimmed list is already at three")


if __name__ == "__main__":
    unittest.main()
