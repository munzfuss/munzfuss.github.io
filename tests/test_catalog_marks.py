"""Curation marks on catalogue numbers (schema Coin.catalog_marks).

A «suspect» / «erroneous» number a source printed is shown muted with
«(*)» / «(!)» beside the class's numbers (`catalog_alts`) and takes part in
nothing else: `seed_merge.apply_catalog_marks` takes it out of the seed's
catalog, so it neither justifies nor refutes a merge. An «unverified» number
is the coin's attribution without a source printing it; it shows «(?)» until
another member of the class carries the same number unmarked (§4
verified-wins, applied to catalogue numbers).

Founding case (curator 2026-10-20): Numista 476697 / 476698 print «Galster
48» for the ½ Sølvgylden 1532 — Galster 48 is the whole Sølvgylden, Galster
49 the half.
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
from lib.compute import _apply_catalog_value_marks  # noqa: E402
from lib.seed_merge import CURATED_FIELDS, apply_catalog_marks  # noqa: E402

REASON = {"de": "Grund.", "en": "Reason.", "uk": "Причина.", "da": "Grund."}
MARKS = [{"register": "galster", "value": "48", "kind": "suspect", "reason": dict(REASON)},
         {"register": "galster", "value": "49", "kind": "unverified"}]


def _half():
    e = {"id": "dk-numista-476697",
         "catalog": {"numista": "476697", "galster": "48"},
         "catalog_marks": [dict(m) for m in MARKS]}
    apply_catalog_marks(e)
    return e


class ApplyCatalogMarks(unittest.TestCase):
    def test_marked_number_leaves_the_catalog(self):
        self.assertEqual(_half()["catalog"], {"numista": "476697"})

    def test_list_form_keeps_the_other_numbers(self):
        e = {"catalog": {"galster": ["48", "50"], "galster_volume": "f1g"},
             "catalog_marks": [MARKS[0]]}
        apply_catalog_marks(e)
        self.assertEqual(e["catalog"], {"galster": "50", "galster_volume": "f1g"})

    def test_idempotent(self):
        e = _half()
        apply_catalog_marks(e)
        self.assertEqual(e["catalog"], {"numista": "476697"})

    def test_survives_reseed(self):
        self.assertIn("catalog_marks", CURATED_FIELDS)


class ClassSynthesis(unittest.TestCase):
    def test_alone_the_half_shows_48_star_and_49_query(self):
        out = {"catalog": {"numista": "476697"}}
        merger._apply_catalog_marks_to_class([_half()], out)
        self.assertEqual(out["catalog"]["galster"], "49")
        self.assertEqual(out["catalog_unverified"],
                         [{"register": "galster", "value": "49", "source": "numista"}])
        self.assertEqual(out["catalog_alts"],
                         [{"register": "galster", "value": "48", "source": "numista",
                           "kind": "suspect", "reason": REASON}])

    def test_galster_page_member_confirms_49(self):
        page = {"id": "dk-galster-f1g-49", "catalog": {"galster": "49"}}
        out = {"catalog": {"galster": "49", "numista": "476697"}}
        merger._apply_catalog_marks_to_class([page, _half()], out)
        self.assertNotIn("catalog_unverified", out)
        self.assertEqual(out["catalog"]["galster"], "49")
        self.assertEqual(len(out["catalog_alts"]), 1)

    def test_a_re_merged_class_does_not_confirm_its_own_query(self):
        prior = {"id": "unified-dk-numista-476697",
                 "catalog": {"galster": "49"},
                 "catalog_unverified": [{"register": "galster", "value": "49",
                                         "source": "numista"}]}
        out = {"catalog": {"galster": "49"}}
        merger._apply_catalog_marks_to_class([prior], out)
        self.assertEqual(len(out["catalog_unverified"]), 1)


class Render(unittest.TestCase):
    def test_groups_carry_both_marks(self):
        coin = schema.Coin.model_construct(
            catalog_alts=[schema.CatalogAlt(register="galster", value="48",
                                            source="numista", kind="suspect",
                                            reason=REASON)],
            catalog_unverified=[schema.CatalogUnverified(
                register="galster", value="49", source="numista")],
            catalog_marks=None)
        groups = [("Galster", ["49"], None), ("N", ["476697"], None)]
        marks = _apply_catalog_value_marks(coin, groups)
        self.assertEqual(groups[0][1], ["49", "48"])
        self.assertEqual(marks["Galster|48"][0], "suspect")
        self.assertEqual(marks["Galster|49"], ("unverified", None))

    def test_schema_accepts_the_fields(self):
        schema.CatalogMark.model_validate(MARKS[0])
        schema.CatalogMark.model_validate(MARKS[1])
        with self.assertRaises(Exception):
            schema.CatalogMark.model_validate({"register": "galster", "value": "48",
                                               "kind": "template"})


if __name__ == "__main__":
    unittest.main()
