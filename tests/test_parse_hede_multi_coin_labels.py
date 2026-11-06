"""Hede pages describing several coins: which label belongs to which spec.

Three faults of `_extract_specs` (curator 2026-11-06, subgroup B1 of the
Hede-base refusals):
- «Som Hede 61B (Hede 62 …)»: the bare comparison came first, so the
  2 Speciedaler took no nominal (c5h61);
- a table block labelled with the bare number («Hede 61») did not meet the
  letters of the description («Hede 61A … 61C»);
- a repeated block further down the page overwrote the number's own block
  (f3h68: Hede 70, the 3 Speciedaler, got the 1-Speciedaler weight);
plus Hede's «Bruttovægt: ca. 35g», read as a weight with its reservation.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import parse_hede as p  # noqa: E402

C5H61 = """Christian 5., Hede 61
Christian 5., 1 speciedaler, København
1 Speciedaler
A) 1670. (Hede 61A, Schou 7-8, Sieg 58.1)
B) U.år (RR), uden randskrift (Hede 61B, Schou 43, Sieg 58.2)
Desuden blev der med samme stempler præget et antal 2 Speciedaler på blanketter af dobbelt tykkelse:
2 Speciedaler
U.år (unik); Som Hede 61B (Hede 62, Schou 42, Sieg 59)

1 Speciedaler
Hede 61
Bruttovægt: 28,775g
Finhed: 0,875
2 Speciedaler
Hede 62
Bruttovægt: 57,550g
Finhed: 0,875
"""

PORTUGALOSER = """Christian 4., 1 og 1/2 Portugaløser, Haderslev
1 Portugaløser
(15)91 (RR). (Hede 1, Schou hhv. 1-5 og 2, Sieg 6)
1/2 Portugaløser
(15)91 (Unik). Som Hede 1. (Hede 2, Schou hhv. 6 og 5, Sieg 5)

1 Portugaløser 1591 og 1592
Hede 1, Schou hhv. 1-5 og 2, Sieg 159
Bruttovægt: ca. 35g
1/2 Portugaløser 1591 og 1592
Hede 2, Schou hhv. 6 og 5, Sieg 158
Bruttovægt: ca. 17g
"""


class MultiCoinLabels(unittest.TestCase):
    def test_parenthesised_number_wins(self):
        by = p._extract_specs(C5H61, "c5h61")["by_hede"]
        self.assertEqual(by["61"]["nominal"], "1 speciedaler")
        self.assertEqual((by["62"]["nominal"], by["62"]["bruttovægt_g"]), ("2 speciedaler", 57.55))

    def test_circa_weight(self):
        by = p._extract_specs(PORTUGALOSER, "c4h1")["by_hede"]
        self.assertEqual((by["1"]["nominal"], by["1"]["bruttovægt_g"]), ("1 portugaløser", 35.0))
        self.assertEqual(by["1"]["bruttovægt_circa"], "Bruttovægt: ca. 35g")
        self.assertEqual((by["2"]["nominal"], by["2"]["bruttovægt_g"]), ("1/2 portugaløser", 17.0))

    def test_plain_weight_has_no_circa(self):
        by = p._extract_specs(C5H61, "c5h61")["by_hede"]
        self.assertNotIn("bruttovægt_circa", by["61"])


if __name__ == "__main__":
    unittest.main()
