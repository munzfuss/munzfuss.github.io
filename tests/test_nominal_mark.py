"""An «erroneous» `nominal_mark` is presentational only (curator 2026-11-06).

The nominal-column analogue of `test_ruler_mark`: `seed_merge.apply_nominal_mark`
moves the printed nominal into `nominal_mark.value` and clears `nominal`, so
the merger never matches on it and the class takes its nominal from the other
members; the page shows the printed nominal beside it as «(!)». A nominal that
a `_source_errata` already replaced is the curator's value and stays.

Founding case: danskmoent's page for Hede 59 (Christian V, dk-hede-c5h59)
heads «1 Dukat»; the image caption, the Hede overview row and Hede's own
article («dobbeltdukat») name the coin a 2 Dukat (6,981 g).

Run:
    .venv/bin/python -m unittest tests.test_nominal_mark -v
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
sys.path.insert(0, str(PROJECT_ROOT / "scripts" / "maintenance"))

import merge_seeds_cross_source as merger  # noqa: E402
from lib.schema import Coin  # noqa: E402
from lib.seed_merge import apply_nominal_mark  # noqa: E402

REASON = {"de": "Grund.", "en": "Reason.", "uk": "Причина.", "da": "Grund."}


def marked(**kw):
    e = {"id": "dk-hede-c5h59", "nominal": "1 Dukat",
         "nominal_mark": {"kind": "erroneous", "reason": dict(REASON)}}
    e.update(kw)
    return e


class ApplyNominalMark(unittest.TestCase):
    def test_erroneous_nominal_moves_into_the_mark(self):
        e = marked()
        apply_nominal_mark(e)
        self.assertIsNone(e["nominal"])
        self.assertEqual(e["nominal_mark"]["value"], "1 Dukat")

    def test_idempotent(self):
        e = marked()
        apply_nominal_mark(e)
        apply_nominal_mark(e)
        self.assertIsNone(e["nominal"])
        self.assertEqual(e["nominal_mark"]["value"], "1 Dukat")

    def test_suspect_nominal_stays_in_play(self):
        e = marked()
        e["nominal_mark"]["kind"] = "suspect"
        apply_nominal_mark(e)
        self.assertEqual(e["nominal"], "1 Dukat")

    def test_nominal_replaced_by_an_erratum_is_kept(self):
        e = marked(nominal="2 Dukat")
        e["nominal_mark"]["value"] = "1 Dukat"
        apply_nominal_mark(e)
        self.assertEqual(e["nominal"], "2 Dukat")

    def test_hedged_mark_matches_the_builders_count_of_one(self):
        # Galster 174: the page prints «Søsling(?)», the builder writes «1 Søsling(?)»
        e = {"nominal": "1 Søsling(?)",
             "nominal_mark": {"kind": "hedged", "value": "Søsling", "reason": {}}}
        apply_nominal_mark(e)
        self.assertIsNone(e["nominal"])
        e = {"nominal": "2 Skilling(?)",
             "nominal_mark": {"kind": "hedged", "value": "Skilling", "reason": {}}}
        apply_nominal_mark(e)
        self.assertEqual(e["nominal"], "2 Skilling(?)")

    def test_shown_as_an_alt(self):
        e = marked()
        apply_nominal_mark(e)
        self.assertEqual(merger._collect_nominal_alts([e]),
                         [{"value": "1 Dukat", "source": "hede",
                           "kind": "erroneous", "reason": REASON}])

    def test_marked_nominal_does_not_refute_a_match(self):
        """With the printed nominal gone the pair is compared on its other
        signals; the nominal no longer says «different coin»."""
        a = marked(metal="gold", ruler="Christian V.",
                   catalog={"hede": "59", "schou": "7", "sieg": "126"})
        apply_nominal_mark(a)
        b = {"id": "dk-bruun-7240", "nominal": "2 Ducats", "metal": "gold",
             "ruler": "Christian V.",
             "catalog": {"hede": "59", "schou": "7", "sieg": "126", "km": "460"}}
        r = merger.match_pair(a, b, "danish_realm")
        self.assertIsNone(r["primary"]["nominal"])
        self.assertNotEqual(r["decision"], "no_match")
        unmarked = merger.match_pair(marked(metal="gold", ruler="Christian V.",
                                            catalog=dict(a["catalog"])), b, "danish_realm")
        self.assertFalse(unmarked["primary"]["nominal"])


class SchemaAcceptsTheFields(unittest.TestCase):
    def test_coin_with_nominal_alts(self):
        Coin.model_validate({
            "id": "x", "fuss": "seed_unsorted", "phase": "hede", "kind": "kurant",
            "nominal": "2 Ducats",
            "nominal_alts": [{"value": "1 Dukat", "source": "hede",
                              "kind": "erroneous", "reason": REASON}],
        })


if __name__ == "__main__":
    unittest.main()
