"""A Hede letter's mint is read from the letter's own line, not from the
prose after its «(Hede …)» reference (curator 2026-11-11).

danskmoent c4h5 (Christian IV, 1 Portugaløser 1592, Haderslev): the prose
«Det eneste kendte eksemplar bortkom 1922 fra Odense Museum» and «Det viste
eksemplar (Hede 5B) befinder sig i Den Kgl. Mønt- og Medaillesamling,
København» name where the specimens were kept, yet gave 5A «Odense» and 5B
«København». f6h24 keeps its real per-letter mints («A) 1813 , København.»,
«C) 1813 , Altona.»), whose stripped text breaks lines at every tag.

Run:
    .venv/bin/python -m unittest tests.test_hede_letter_mint_own_line -v
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import parse_hede as P  # noqa: E402

C4H5 = """A) (Unik) Bagside: Midterste våben Ditmarsken (Hede 5A, Schou 3, Sieg 8). Det eneste kendte eksemplar bortkom 1922 fra Odense Museum.
B) (Unik) Bagside: Midterste våbenskjold Oldenborg og Delmenhorst (Hede 5B, Schou 4, Sieg 8)
Det viste eksemplar (Hede 5B) befinder sig i
Den Kgl. Mønt- og Medaillesamling, København.
Bruttovægt: 34,88g
"""

F6H24 = """A) 1813
, København. Forside
M
, bagsiden uden mærke (Hede 24A, Schou 1, Sieg 26.1)
C) 1813
, Altona. Forside
IC
, bagside
MF
. (Hede 24C, Schou 3, Sieg 26.3)
Bruttovægt: 1,0g
"""


class LetterMintOwnLine(unittest.TestCase):
    def test_prose_after_the_reference_names_no_mint(self):
        self.assertEqual(P._mint_per_letter_block(C4H5), {})

    def test_mint_on_the_letter_line_is_kept(self):
        self.assertEqual(P._mint_per_letter_block(F6H24),
                         {"A": "København", "C": "Altona"})


if __name__ == "__main__":
    unittest.main()
