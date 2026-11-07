"""A Hede note page numbered from Hede's supplement (curator 2026-11-07, B5).

danskmoent's `f3h134n.htm` («Frederik 3., Hede 134 note») describes the
1 Skilling 1661 and numbers it «(Hede 134a (tillæg, side 223), Schou 62,
Sieg 10)». The file name's «134n» is not a Hede number, and a bare «134a»
would read as the main volume's Hede 134A — the 2 Skilling 1664-1667, a
different coin, since catalogue indices compare case-insensitively.

Run:
    .venv/bin/python -m unittest tests.test_parse_hede_supplement_number -v
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import parse_hede as p  # noqa: E402

F3H134N = """<html><body>
<p>Frederik 3., Hede 134 note</p>
<p>Frederik 3.</p>
<p>1 Skilling, København 1661</p>
<p>Forside: aflangt, indadbuet våbenskjold; årstal ved skjold.<br>
Bagside: værdiangivelse<br>
(Hede 134a (tillæg, side 223), Schou 62, Sieg 10)</p>
<p>Bruttovægt: 0,913g<br>Finhed: 0,156<br>Finvægt: 0,142g</p>
</body></html>"""


class SupplementNumber(unittest.TestCase):
    def test_note_page_takes_the_supplement_number(self):
        d = p.parse_one(F3H134N, "f3h134n")
        self.assertEqual(d["hede_numbers_filename"], ["134a (tillæg)"])

    def test_supplement_number_has_no_bare_hede_base(self):
        """The Hede-base rule reads «<digits><letters>» only; the labelled
        supplement number must stay out of the base-134 group."""
        sys.path.insert(0, str(ROOT / "scripts" / "maintenance"))
        import merge_seeds_cross_source as m
        self.assertIsNone(m._HEDE_BASE_TOKEN.match("134a (tillæg)"))

    def test_ordinary_page_unchanged(self):
        html = F3H134N.replace("Hede 134 note", "Hede 134").replace(
            "(Hede 134a (tillæg, side 223)", "(Hede 134A")
        d = p.parse_one(html, "f3h134")
        self.assertEqual(d["hede_numbers_filename"], ["134"])


if __name__ == "__main__":
    unittest.main()
