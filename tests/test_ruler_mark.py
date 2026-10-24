"""An «erroneous» `ruler_mark` is presentational only (curator 2026-10-24).

The ruler-column analogue of `test_mint_mark`: `seed_merge.apply_ruler_mark`
moves the printed ruler into `ruler_mark.value` and clears `ruler`, so the
merger never matches on it and the page shows «—» with the printed ruler
beside it as «(!)». A ruler that a `_source_errata` already replaced (the
kmk «Hans» → «?» pattern) is the curator's value and stays.

Founding case: Bruun Part III lot 12128 (dk-bruun-10726) prints «Christian VI»
for a 24 Skilling 1753 Kongsberg, struck under Frederik V (Hede Norge 2A).

Run:
    .venv/bin/python -m unittest tests.test_ruler_mark -v
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
sys.path.insert(0, str(PROJECT_ROOT / "scripts" / "maintenance"))

import merge_seeds_cross_source as merger  # noqa: E402
from lib.seed_merge import apply_ruler_mark  # noqa: E402

REASON = {"de": "Grund.", "en": "Reason.", "uk": "Причина.", "da": "Grund."}


def marked(**kw):
    e = {"id": "dk-bruun-10726", "ruler": "Christian VI.",
         "ruler_mark": {"kind": "erroneous", "reason": dict(REASON)}}
    e.update(kw)
    return e


class ApplyRulerMark(unittest.TestCase):
    def test_erroneous_ruler_moves_into_the_mark(self):
        e = marked()
        apply_ruler_mark(e)
        self.assertIsNone(e["ruler"])
        self.assertEqual(e["ruler_mark"]["value"], "Christian VI.")

    def test_idempotent(self):
        e = marked()
        apply_ruler_mark(e)
        apply_ruler_mark(e)
        self.assertIsNone(e["ruler"])
        self.assertEqual(e["ruler_mark"]["value"], "Christian VI.")

    def test_suspect_ruler_stays_in_play(self):
        e = marked()
        e["ruler_mark"]["kind"] = "suspect"
        apply_ruler_mark(e)
        self.assertEqual(e["ruler"], "Christian VI.")

    def test_ruler_replaced_by_an_erratum_is_kept(self):
        e = {"id": "kmk-331973", "ruler": "?",
             "ruler_mark": {"kind": "erroneous", "value": "Hans", "reason": dict(REASON)}}
        apply_ruler_mark(e)
        self.assertEqual(e["ruler"], "?")
        self.assertEqual(e["ruler_mark"]["value"], "Hans")

    def test_shown_as_an_alt(self):
        e = marked()
        apply_ruler_mark(e)
        self.assertEqual(merger._collect_ruler_alts([e]),
                         [{"value": "Christian VI.", "source": "bruun",
                           "kind": "erroneous", "reason": REASON}])


if __name__ == "__main__":
    unittest.main()
