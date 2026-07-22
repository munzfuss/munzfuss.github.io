"""Companion `<field>_verified` flag must not go stale when its value changes.

Guards the field-consistency bug caught 2026-07-22: when a fresh seed entry
corrected `mint` (None → «Christiania», source-attested) but the existing
on-disk entry carried `mint: None` + `mint_verified: false`, `merge_one` took
the new mint value yet PRESERVED the stale `mint_verified: false` (because
`mint_verified` sits in CURATED_FIELDS). Pre-write hygiene's sources-imply-mint
rule ran BEFORE merge so it could not re-fire — leaving a correct value marked
as an unverified curator guess.

The rule generalises: whenever `merge_one` replaces a `<field>` value with a
differing fresh value, the paired `<field>_verified` flag must follow fresh
(which already carries the hygiene-derived state), never be preserved from the
old value.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from lib.seed_merge import merge_one  # noqa: E402
from ruamel.yaml.comments import CommentedMap  # noqa: E402


class TestVerifiedFlagFollowsValue(unittest.TestCase):
    def test_mint_backfill_flips_verified_flag(self):
        """The canonical Christiania-dukat case: None→value + false→true."""
        existing = CommentedMap({
            "id": "dk-numista-117110",
            "mint": None,
            "mint_verified": False,
        })
        fresh = CommentedMap({
            "id": "dk-numista-117110",
            "mint": "Christiania",
            "mint_verified": True,  # hygiene-derived on fresh
        })
        merge_one(existing, fresh)
        self.assertEqual(existing["mint"], "Christiania")
        self.assertTrue(existing["mint_verified"])

    def test_mint_verified_preserved_when_value_unchanged(self):
        """No replacement → mint_verified stays curated (existing wins)."""
        existing = CommentedMap({
            "id": "x", "mint": "Altona", "mint_verified": True,
        })
        fresh = CommentedMap({
            "id": "x", "mint": "Altona", "mint_verified": False,
        })
        merge_one(existing, fresh)
        self.assertEqual(existing["mint"], "Altona")
        # value identical → not replaced → curated existing wins (stays True).
        self.assertTrue(existing["mint_verified"])

    def test_verified_wins_keeps_existing_value_and_flag(self):
        """§4 verified-wins: existing source-attested, fresh unverified —
        both value AND flag stay existing (no stale-flag override)."""
        existing = CommentedMap({
            "id": "x", "mint": "Helsingør", "mint_verified": True,
        })
        fresh = CommentedMap({
            "id": "x", "mint": "Kopenhagen", "mint_verified": False,
        })
        merge_one(existing, fresh)
        self.assertEqual(existing["mint"], "Helsingør")
        self.assertTrue(existing["mint_verified"])

    def test_fineness_flag_follows_replaced_value(self):
        """Generalises beyond mint: fineness/fineness_verified pair."""
        existing = CommentedMap({
            "id": "x", "fineness": 0.75, "fineness_verified": True,
        })
        fresh = CommentedMap({
            "id": "x", "fineness": 0.875, "fineness_verified": True,
        })
        merge_one(existing, fresh)
        self.assertEqual(existing["fineness"], 0.875)
        self.assertTrue(existing["fineness_verified"])

    def test_flag_dropped_when_fresh_omits_it(self):
        """Value replaced but fresh carries no flag key → stale curated flag
        is dropped, not preserved, so downstream hygiene re-derives it."""
        existing = CommentedMap({
            "id": "x", "mint": None, "mint_verified": False,
        })
        fresh = CommentedMap({
            "id": "x", "mint": "Christiania",  # no mint_verified key
        })
        merge_one(existing, fresh)
        self.assertEqual(existing["mint"], "Christiania")
        self.assertNotIn("mint_verified", existing)

    def test_curation_hold_freezes_flag(self):
        """A curator freeze on mint_verified via _curation_holds still wins —
        the follow-fresh override never overrides an explicit hold."""
        existing = CommentedMap({
            "id": "x", "mint": None, "mint_verified": False,
            "_curation_holds": ["mint", "mint_verified"],
        })
        fresh = CommentedMap({
            "id": "x", "mint": "Christiania", "mint_verified": True,
        })
        merge_one(existing, fresh)
        # mint frozen → stays None; flag frozen → stays False.
        self.assertIsNone(existing["mint"])
        self.assertFalse(existing["mint_verified"])


if __name__ == "__main__":
    unittest.main()
