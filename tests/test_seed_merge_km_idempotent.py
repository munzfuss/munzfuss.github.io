"""Re-seed idempotency for list-of-dict (KMRef) catalog.km entries.

Guards the non-idempotency bug caught 2026-07-22: a merge-aware re-run of
`build_numista_seed` appended a duplicate `{register: value}` dict to a
list-form `catalog.km` on every pass, so cross-volume KMs grew to 3-4
identical copies purely from repeated seeding (numista 82693: `- dk: '479'`
×4; numista 119248: `- {nor: '260', dk: '645'}` ×4).

`_union_cat_values` must dedup structured entries by normalised content so a
double-merge produces exactly one copy of each distinct KMRef dict, regardless
of key order.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from lib.seed_merge import _union_cat_values, merge_one  # noqa: E402
from ruamel.yaml.comments import CommentedMap  # noqa: E402


class TestUnionCatValuesStructured(unittest.TestCase):
    # A deduped singleton collapses back to a scalar dict — the canonical
    # KMRef form that `_apply_km_country_register` itself emits.
    def test_identical_single_key_dict_deduped(self):
        km = [{"dk": "479"}]
        self.assertEqual(_union_cat_values(km, [{"dk": "479"}]), {"dk": "479"})

    def test_identical_multi_key_dict_deduped_key_order_insensitive(self):
        existing = [{"nor": "260", "dk": "645"}]
        fresh = [{"dk": "645", "nor": "260"}]  # same content, different order
        out = _union_cat_values(existing, fresh)
        self.assertEqual(out, {"nor": "260", "dk": "645"})

    def test_distinct_dicts_both_kept(self):
        out = _union_cat_values([{"dk": "479"}], [{"nor": "260"}])
        self.assertEqual(out, [{"dk": "479"}, {"nor": "260"}])

    def test_scalar_dedup_still_works(self):
        self.assertEqual(_union_cat_values("406.1", "406.1"), "406.1")
        self.assertEqual(_union_cat_values(["406.1"], ["406.2"]), ["406.1", "406.2"])

    def test_double_merge_is_idempotent(self):
        """merge_one applied twice must not grow list-form km."""
        def _entry():
            return CommentedMap({
                "id": "dk-numista-119248",
                "catalog": CommentedMap({
                    "numista": "119248",
                    "km": [CommentedMap({"nor": "260", "dk": "645"})],
                }),
            })

        existing = _entry()
        merge_one(existing, _entry())
        km_after_first = existing["catalog"]["km"]
        merge_one(existing, _entry())
        km_after_second = existing["catalog"]["km"]
        # Single distinct KMRef → deduped singleton collapses to scalar dict,
        # and stays that way on every subsequent re-merge (idempotent).
        self.assertEqual(dict(km_after_first), {"nor": "260", "dk": "645"})
        self.assertEqual(dict(km_after_second), {"nor": "260", "dk": "645"})


if __name__ == "__main__":
    unittest.main()
