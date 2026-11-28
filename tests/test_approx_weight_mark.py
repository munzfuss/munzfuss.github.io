"""«ca.» weights render with the approximate «(~)» mark (curator 2026-11-28).

A weight a source prints with «ca.» is an attested, approximate figure: it
carries «(~)» (curation-mark kind `approximate`) instead of the hedged «(?)»
and the «ca.» suffix in the source label.

Run via:
    .venv/bin/python -m unittest tests.test_approx_weight_mark -v
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from lib.weight_range import approx_reason, range_marks, range_pairs  # noqa: E402


class ApproxWeightMark(unittest.TestCase):
    def test_range_label_has_no_ca(self):
        r = [{"min": 0.14, "max": None, "approx": True, "source": "danskmoent.dk halvpenn.htm"}]
        self.assertEqual(range_pairs(r), [(0.14, "danskmoent.dk halvpenn.htm")])

    def test_range_marks_every_bound(self):
        r = [{"min": 0.21, "max": 0.37, "approx": True, "source": "S"}]
        marks = range_marks(r)
        self.assertEqual({lab for _v, lab in range_pairs(r)}, set(marks))
        self.assertTrue(all(k == "approximate" for k, _w in marks.values()))

    def test_plain_range_unmarked(self):
        self.assertEqual(range_marks([{"min": 1.0, "max": 2.0, "approx": False, "source": "S"}]), {})

    def test_hede_printed_quoted_and_translated(self):
        why = approx_reason("danskmoent.dk (Hede 1)", "Bruttovægt: ca. 8,58g")
        self.assertIn("«Bruttovægt: ca. 8,58g»", why["da"])
        self.assertNotIn("перекл.", why["da"])
        self.assertIn("близько 8,58 г", why["uk"])
        self.assertIn("c. 8.58 g", why["en"])
        self.assertIn("Rauhgewicht: ca. 8,58 g", why["de"])

    def test_generic_reason_without_printed(self):
        why = approx_reason("S")
        self.assertEqual(set(why), {"de", "en", "uk", "da"})
        self.assertTrue(all("[b]S[/b]" in v for v in why.values()))


if __name__ == "__main__":
    unittest.main()
