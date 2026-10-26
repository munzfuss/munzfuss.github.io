"""A curator `year_window` (merge_decisions) sets a class's year and its
reader-facing explanation (curator 2026-10-26, Galster 1: 1373-1381 compiled
from Ernst 1948 and Horsnæs, Moesgaard and Märcher 2018).
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "maintenance"))

import merge_seeds_cross_source as M  # noqa: E402

NOTE = {"de": "d", "en": "e", "uk": "u", "da": "a"}
WIN = [{"members": ["dk-galster-m1g-1", "lindahl-1955-ribe-witten"],
        "years": [1373, 1381], "note": NOTE}]


class YearWindow(unittest.TestCase):
    def test_window_sets_year_and_note(self):
        u = {"year_first": 1373, "year_last": 1396, "year_ranges": [[1373, 1396]],
             "year_label": "1373-1396", "year_verified": True}
        M._apply_year_window(u, {"dk-galster-m1g-1", "lindahl-1955-ribe-witten"}, WIN)
        self.assertEqual((u["year_first"], u["year_last"], u["year_label"]),
                         (1373, 1381, "1373-1381"))
        self.assertEqual(u["year_ranges"], [[1373, 1381]])
        self.assertIs(u["year_verified"], False)
        self.assertEqual(u["year_note"], NOTE)

    def test_other_class_untouched(self):
        u = {"year_first": 1400, "year_last": 1400, "year_label": "1400"}
        M._apply_year_window(u, {"dk-galster-c1g-23"}, WIN)
        self.assertEqual(u, {"year_first": 1400, "year_last": 1400, "year_label": "1400"})

    def test_validation(self):
        errs = M.validate_decisions_doc({"year_window": [
            {"members": ["x"], "years": [1381, 1373], "note": NOTE},
            {"members": ["x"], "years": [1373, 1381], "note": {"de": "d"}},
            {"members": ["x"], "years": [1373, 1381], "note": NOTE},
        ]}, "f.yml")
        self.assertEqual(len(errs), 2)


if __name__ == "__main__":
    unittest.main()
