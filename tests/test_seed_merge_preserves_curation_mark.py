"""A curator suspect/erroneous mark must survive a re-seed of the same source.

Guards the clobber caught 2026-09-13: the 5.62 g KMM reading of the 1531 Ungersk
Gylden (danish_realm) was marked `suspect` last session by converting the scalar
`weight_rough_g: 5.62` into list-form + a trilingual `suspect:` block. A later
re-seed of the kmk source re-emitted the bare verified scalar; `weight_rough_g`
is a `_VERIFIABLE_FIELD`, both sides were verified, so the verified-wins branch
fell through to fresh-wins and the scalar overwrote the curated list — silently
stripping the mark (no `_curation_holds` had frozen the field).

The mark lives INSIDE the value and no parser ever emits it, so `merge_one` now
keeps existing whenever it carries a `suspect`/`erroneous` mark the fresh value
lacks. This holds without any `_curation_holds`, so the mark is durable by
default rather than only when a curator remembered to freeze the field.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from lib.seed_merge import merge_one  # noqa: E402
from ruamel.yaml.comments import CommentedMap  # noqa: E402


def _suspect_weight():
    return [CommentedMap({
        "value": 5.62,
        "source": "kmk",
        "suspect": {"de": "…", "en": "…", "uk": "…"},
    })]


class TestSeedMergePreservesCurationMark(unittest.TestCase):
    def test_reseed_scalar_does_not_strip_suspect(self):
        """The canonical 5.62 g KMM case: list+suspect vs a fresh verified scalar."""
        existing = CommentedMap({
            "id": "kmk-575432",
            "weight_rough_g": _suspect_weight(),
            "weight_rough_verified": True,
        })
        fresh = CommentedMap({
            "id": "kmk-575432",
            "weight_rough_g": 5.62,          # parser re-emission, no mark
            "weight_rough_verified": True,   # KMM publishes the weight
        })
        merge_one(existing, fresh)
        self.assertIsInstance(existing["weight_rough_g"], list)
        self.assertTrue(existing["weight_rough_g"][0].get("suspect"))

    def test_mark_preserved_even_when_fresh_value_differs(self):
        """A corrected re-seed value must not silently override a marked reading —
        the curator has examined it; changing it is a curator edit, not a re-seed."""
        existing = CommentedMap({
            "id": "x",
            "weight_rough_g": _suspect_weight(),
            "weight_rough_verified": True,
        })
        fresh = CommentedMap({
            "id": "x",
            "weight_rough_g": 5.60,
            "weight_rough_verified": True,
        })
        merge_one(existing, fresh)
        self.assertIsInstance(existing["weight_rough_g"], list)
        self.assertEqual(existing["weight_rough_g"][0]["value"], 5.62)
        self.assertTrue(existing["weight_rough_g"][0].get("suspect"))

    def test_unmarked_field_still_fresh_wins(self):
        """No mark → ordinary fresh-wins semantics are unchanged."""
        existing = CommentedMap({
            "id": "y",
            "weight_rough_g": [CommentedMap({"value": 3.49, "source": "kmk"})],
            "weight_rough_verified": True,
        })
        fresh = CommentedMap({
            "id": "y",
            "weight_rough_g": 3.50,
            "weight_rough_verified": True,
        })
        merge_one(existing, fresh)
        self.assertEqual(existing["weight_rough_g"], 3.50)


if __name__ == "__main__":
    unittest.main()
