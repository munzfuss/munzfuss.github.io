"""A reign window is a placeholder: a narrower date in the same class wins.

KMM tags most undated pieces with the king's reign — Hans «1483-1513»,
Christian II «1513-1523» — in the same creation-event field that elsewhere
holds a real date. Merged into a class, that range widened the class year to
the whole reign. Galster 43 (Hvid 1513, the only type of Christian II's first
ordinance) showed 1513-1523 because three KMM specimens carried the reign;
Galster 41 (Skilling 1516-1517) the same. Found 2026-10-19 while checking
which coins Galster's specimen lists could date more precisely.

Curator direction (2026-10-19): the reign stays visible when it is all a class
has, but any narrower date takes precedence. The merger had the means — a
curator `year_demote` holds a member back to a last-resort pass — only by
hand, per member. `is_reign_span` now recognises the reign automatically, with
slack for the cataloguer's choice of accession year (KMM writes Hans with 1481,
1482 and 1483) capped at a tenth of the reign, so a real issue span on a short
reign (Christian VIII «1841-1847») is not mistaken for it.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "maintenance"))

from lib.ruler_reigns import is_reign_span  # noqa: E402
from merge_seeds_cross_source import _union_year_ranges  # noqa: E402


class IsReignSpan(unittest.TestCase):
    def test_kmm_hans_variants(self):
        for a, b in ((1481, 1513), (1482, 1513), (1483, 1513), (1481, 1512)):
            self.assertTrue(is_reign_span("Hans", "danish_realm", a, b), (a, b))

    def test_christian_ii_exact(self):
        self.assertTrue(is_reign_span("Christian 2", "danish_realm", 1513, 1523))

    def test_short_reign_issue_span_is_not_reign(self):
        self.assertFalse(is_reign_span("Christian VIII", "danish_realm", 1841, 1847))
        self.assertFalse(is_reign_span("Frederik VIII", "danish_realm", 1908, 1912))

    def test_single_year_and_narrow_range(self):
        self.assertFalse(is_reign_span("Hans", "danish_realm", 1512, 1512))
        self.assertFalse(is_reign_span("Christian 2", "danish_realm", 1516, 1517))

    def test_foreign_issuer_has_no_kings_window(self):
        self.assertFalse(is_reign_span("Hans", "sweden", 1483, 1513))


class UnionPrefersNarrowerDate(unittest.TestCase):
    def _demote(self, members):
        out = []
        for m in members:
            m = dict(m)
            if is_reign_span(m.get("ruler"), m.get("issuing_entity"),
                             m.get("year_first"), m.get("year_last")):
                m["_year_demoted"] = True
            out.append(m)
        return out

    def test_galster_43(self):
        members = [
            {"ruler": "Christian II", "issuing_entity": "danish_realm",
             "year_first": 1513, "year_last": 1513},
            {"ruler": "Christian 2", "issuing_entity": "danish_realm",
             "year_first": 1513, "year_last": 1523},
        ]
        self.assertEqual(_union_year_ranges(members), [[1513, 1523]])
        self.assertEqual(_union_year_ranges(self._demote(members)), [[1513, 1513]])

    def test_reign_kept_when_nothing_better(self):
        members = [{"ruler": "Hans", "issuing_entity": "danish_realm",
                    "year_first": 1483, "year_last": 1513}] * 2
        self.assertEqual(_union_year_ranges(self._demote(members)), [[1483, 1513]])



class ClassShowsTableReign(unittest.TestCase):
    """Curator 2026-10-20: Rigsrådet 1481-1483, Hans 1483-1513. A class whose
    every member gives only Hans's reign shows the table's 1483-1513, not a
    cataloguer's 1481 accession year; the members keep their own years."""

    def _unify(self, *ranges):
        import merge_seeds_cross_source as M
        members = []
        for i, (a, b) in enumerate(ranges):
            members.append({"id": f"kmk-{i}", "ruler": "Hans", "nominal": "Hvid",
                            "issuing_entity": "danish_realm", "year_first": a,
                            "year_last": b, "year_ranges": [[a, b]],
                            "_year_demoted": True,
                            "_year_reign_window": (1483, 1513)})
        return M.build_unified(members, "unified-kmk-0", "danish_realm")

    def test_all_reign_members_take_the_table_window(self):
        out = self._unify((1481, 1513), (1482, 1513), (1481, 1512))
        out = out[0] if isinstance(out, tuple) else out
        self.assertEqual((out["year_first"], out["year_last"]), (1483, 1513))

    def test_undated_members_do_not_block_it(self):
        import merge_seeds_cross_source as M
        members = [{"id": "kmk-1", "ruler": "Hans", "nominal": "Hvid",
                    "issuing_entity": "danish_realm", "year_first": 1481,
                    "year_last": 1513, "year_ranges": [[1481, 1513]],
                    "_year_demoted": True, "_year_reign_window": (1483, 1513)},
                   {"id": "kmk-2", "ruler": "Hans", "nominal": "Hvid",
                    "issuing_entity": "danish_realm"}]
        out = M.build_unified(members, "unified-kmk-1", "danish_realm")
        out = out[0] if isinstance(out, tuple) else out
        self.assertEqual((out["year_first"], out["year_last"]), (1483, 1513))

    def test_rule_is_hans_only(self):
        import merge_seeds_cross_source as M
        self.assertEqual(M._HANS_REIGN_START, 1483)

    def test_hans_reign_starts_1483(self):
        from lib.ruler_reigns import reign_window_placeholder
        self.assertEqual(reign_window_placeholder("Hans", "danish_realm"), (1483, 1513))
        self.assertEqual(reign_window_placeholder("Rigsrådet", "danish_realm"), (1481, 1483))


if __name__ == "__main__":
    unittest.main()
