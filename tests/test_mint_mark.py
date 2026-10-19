"""An «erroneous» `mint_mark` is presentational only (curator 2026-10-18).

The printed mint is shown muted with «(!)» beside the real mint (`mint_alts`)
and takes part in nothing else: `seed_merge.apply_mint_mark` clears the seed's
`mint`, so the merger's mint union, matching and entity routing never see it.
A «suspect» mint mark keeps the value in play, like a suspect reading.

Founding case: Bruun Part V lot 14206 prints «Copenhagen Mint» for the Altona
Rejsedaler 1788 (Hede 25; L. E. Bruuns Mønt- og Medaillesamling 1928, p. 239).
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
sys.path.insert(0, str(PROJECT_ROOT / "scripts" / "maintenance"))

import merge_seeds_cross_source as merger  # noqa: E402
from lib import schema  # noqa: E402
from lib.seed_merge import apply_mint_mark  # noqa: E402

REASON = {"de": "Grund.", "en": "Reason.", "uk": "Причина.", "da": "Grund."}


class ApplyMintMark(unittest.TestCase):
    def test_erroneous_mint_moves_into_the_mark(self):
        e = {"id": "dk-bruun-7892", "mint": "Kopenhagen", "mint_verified": True,
             "mint_mark": {"kind": "erroneous", "reason": dict(REASON)}}
        apply_mint_mark(e)
        self.assertIsNone(e["mint"])
        self.assertEqual(e["mint_mark"]["value"], "Kopenhagen")
        self.assertTrue(e["mint_verified"])   # nothing else touched

    def test_idempotent(self):
        e = {"id": "x", "mint": "Kopenhagen",
             "mint_mark": {"kind": "erroneous", "reason": dict(REASON)}}
        apply_mint_mark(e)
        apply_mint_mark(e)
        self.assertIsNone(e["mint"])
        self.assertEqual(e["mint_mark"]["value"], "Kopenhagen")

    def test_suspect_mint_stays_in_play(self):
        e = {"id": "x", "mint": "Kopenhagen",
             "mint_mark": {"kind": "suspect", "reason": dict(REASON)}}
        apply_mint_mark(e)
        self.assertEqual(e["mint"], "Kopenhagen")

    def test_list_mint_is_kept_whole_in_value(self):
        e = {"id": "x", "mint": ["Altona", "Kopenhagen"],
             "mint_mark": {"kind": "erroneous", "reason": dict(REASON)}}
        apply_mint_mark(e)
        self.assertEqual(e["mint_mark"]["value"], "Altona, Kopenhagen")


class MintAltsMerger(unittest.TestCase):
    def _members(self):
        marked = {"id": "dk-bruun-7892", "mint": "Kopenhagen", "mint_verified": True,
                  "mint_mark": {"kind": "erroneous", "reason": dict(REASON)}}
        apply_mint_mark(marked)
        return [{"id": "dk-hede-c7h25", "mint": "Altona", "mint_verified": True},
                {"id": "dk-bruun-7893", "mint": "Altona", "mint_verified": True},
                marked]

    def test_erroneous_mint_is_not_in_the_class_mints(self):
        self.assertEqual(merger._collect_mints(self._members()), "Altona")

    def test_erroneous_mint_is_shown_as_an_alt(self):
        self.assertEqual(merger._collect_mint_alts(self._members()),
                         [{"value": "Kopenhagen", "source": "bruun",
                           "kind": "erroneous", "reason": REASON}])

    def test_schema_accepts_mark_and_alts(self):
        schema.YearMark.model_validate({"kind": "erroneous", "value": "Kopenhagen",
                                        "reason": REASON})
        schema.YearAlt.model_validate({"value": "Kopenhagen", "source": "bruun",
                                       "kind": "erroneous", "reason": REASON})


if __name__ == "__main__":
    unittest.main()
