"""Attributions (data/v2/attributions/<entity>.yml, D52, curator 2026-10-29):
a class's value from scholarly works, found by the type's catalogue number."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "maintenance"))

import merge_seeds_cross_source as M  # noqa: E402

ATTR = {"type": {"galster": "27", "galster_volume": "hg"}, "field": "year",
        "basis": "given", "value": 1497,
        "works": [{"work": "Zinck I", "page": 9, "how": "circa",
                   "quote": "blev formentlig slået omkring 1497",
                   "translation": {"de": "d", "en": "e", "uk": "u"}}]}


class Attributions(unittest.TestCase):
    def test_found_by_scoped_type_number_including_sub_letter(self):
        members = [{"id": "dk-bruun-3839", "ruler": "Hans",
                    "catalog": {"galster": "27A", "schou": "2"}}]
        self.assertTrue(M._attribution_matches(ATTR, members, "danish_realm"))

    def test_other_volume_does_not_match(self):
        members = [{"id": "x", "ruler": "Christian III",
                    "catalog": {"galster": "27", "galster_volume": "c3g"}}]
        self.assertFalse(M._attribution_matches(ATTR, members, "danish_realm"))

    def test_apply_sets_year_records_work_not_source(self):
        u = {"year_first": 1496, "year_last": 1497, "year_label": "1496-1497",
             "year_ranges": [[1496, 1497]], "sources": []}
        M.apply_attribution(u, ATTR)
        self.assertEqual((u["year_label"], u["year_verified"]), ("1497", False))
        e = u["uncertainty"]["year"][0]
        self.assertEqual((e["kind"], e["source"], e["as_printed"]),
                         ("hedged", "Zinck I, s. 9", "blev formentlig slået omkring 1497"))
        # a work that dates the type is not a source of specimen data (curator 2026-11-02)
        self.assertEqual(u["sources"], [])

    def test_compiled_basis_is_inferred(self):
        a = dict(ATTR, basis="compiled", value=[1373, 1381])
        u = {"sources": []}
        M.apply_attribution(u, a)
        self.assertEqual(u["uncertainty"]["year"][0]["kind"], "inferred")

    def test_several_spans_each_work_its_own_dating(self):
        # Galster 174: Schive 1865 dates the type 1518, Galster 1531-32 (curator 2026-11-10)
        a = dict(ATTR, value=[[1531, 1532], [1518, 1518]], works=[
            {"work": "Schive 1865", "page": 140, "how": "possibly", "value": 1518, "quote": "q1"},
            {"work": "danskmoent.dk (Galster 174)", "how": "query", "value": [1531, 1532],
             "quote": "u. år (1531-32)?"}])
        self.assertEqual(M.validate_attributions_doc({"attributions": [a]}), [])
        u = {"sources": []}
        M.apply_attribution(u, a)
        self.assertEqual((u["year_label"], u["year_first"], u["year_last"], u["year_ranges"]),
                         ("1518, 1531-1532", 1518, 1532, [[1518, 1518], [1531, 1532]]))
        self.assertFalse(u["year_verified"])
        self.assertEqual([e["value"] for e in u["uncertainty"]["year"]], ["1518", "1531-1532"])

    def test_malformed_spans_rejected(self):
        for v in ([[1532, 1531]], [1518, [1531]], [], True):
            self.assertTrue(M.validate_attributions_doc(
                {"attributions": [dict(ATTR, value=v)]}), v)

    def test_validation(self):
        self.assertEqual(M.validate_attributions_doc({"attributions": [ATTR]}), [])
        bad = dict(ATTR, works=[{"work": "X", "how": "guess", "quote": "q"}])
        self.assertTrue(M.validate_attributions_doc({"attributions": [bad]}))
        self.assertTrue(M.validate_decisions_doc({"year_window": [{"members": ["a"]}]}, "x.yml"))


if __name__ == "__main__":
    unittest.main()
