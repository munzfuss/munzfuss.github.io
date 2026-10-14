"""A `year_mark` on a seed's own year becomes a `year_alts` entry on the merged
class (merger) and survives absorb as a union of the live members' alts.

Founding case: the Münzkabinett Berlin's «um 1506» on the Frederik I Gottorp
Goldgulden (Galster 122) — held out of the displayed year by a year_demote and
shown beside it with «(*)» (docs/research/frederik_i_gottorp_goldgulden_dating.md).
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

REASON = {"de": "Grund.", "en": "Reason.", "uk": "Причина.", "da": "Grund."}


class YearAltsMerger(unittest.TestCase):
    def test_marked_member_yields_one_alt_labelled_by_source(self):
        members = [
            {"id": "dk-bruun-14741", "year_label": "1531"},
            {"id": "ikmk-18239610", "year_label": "1506",
             "year_mark": {"kind": "suspect", "reason": REASON}},
        ]
        alts = merger._collect_year_alts(members)
        self.assertEqual(alts, [{"value": "1506", "source": "ikmk",
                                 "kind": "suspect", "reason": REASON}])

    def test_unmarked_members_yield_nothing(self):
        self.assertEqual(merger._collect_year_alts(
            [{"id": "dk-bruun-14741", "year_label": "1531"}]), [])

    def test_malformed_mark_is_ignored(self):
        members = [{"id": "ikmk-1", "year_label": "1506",
                    "year_mark": {"kind": "odd", "reason": REASON}},
                   {"id": "ikmk-2", "year_label": "1507",
                    "year_mark": {"kind": "suspect", "reason": "not a dict"}}]
        self.assertEqual(merger._collect_year_alts(members), [])

    def test_existing_alts_pass_through_without_duplicates(self):
        alt = {"value": "1506", "source": "ikmk", "kind": "suspect", "reason": REASON}
        members = [{"id": "unified-x", "year_label": "1531", "year_alts": [alt]},
                   {"id": "ikmk-18239610", "year_label": "1506",
                    "year_mark": {"kind": "suspect", "reason": REASON}}]
        self.assertEqual(merger._collect_year_alts(members), [alt])


class YearAltsSchema(unittest.TestCase):
    def test_coin_accepts_year_mark_and_year_alts(self):
        schema.YearMark(kind="suspect", reason=REASON)
        a = schema.YearAlt(value="1506", source="ikmk", kind="suspect", reason=REASON)
        self.assertEqual(a.value, "1506")
        with self.assertRaises(Exception):
            schema.YearAlt(value="1506", source="ikmk", kind="guess", reason=REASON)


if __name__ == "__main__":
    unittest.main()
