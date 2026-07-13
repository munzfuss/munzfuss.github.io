"""Numista king-name canonicalisation — «John (Hans)» family → «Hans».

Numista writes the Danish-Norwegian king Hans (John I, r. 1481-1513) with the
English exonym «John» in several shapes («John», «John I», «John (Hans)»,
«John I (Hans I)», optionally with a « (reign-dates)» tail). The hardcoded
`_NUMISTA_RULER_CANON` only carried «John I (Hans I)» / «John I», so «John (Hans)»
(the Norway Bergen Goldgulden N#444264, 2026-07-13) flowed through un-normalised
and rendered as «John (Hans)» beside the Danish peer's «Hans». `_canon_numista_ruler`
adds a regex fallback — any leading «John» → «Hans» (Hans is the only DK-NO «John»).

Run: .venv/bin/python -m unittest tests.test_numista_ruler_canon -v
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
sys.path.insert(0, str(PROJECT_ROOT / "scripts" / "maintenance"))

from build_numista_seed import _canon_numista_ruler  # noqa: E402


class NumistaRulerCanon(unittest.TestCase):
    def test_john_hans_parenthetical(self) -> None:
        self.assertEqual(_canon_numista_ruler("John (Hans)"), "Hans")

    def test_john_i_hans_i(self) -> None:
        self.assertEqual(_canon_numista_ruler("John I (Hans I)"), "Hans")

    def test_john_bare(self) -> None:
        self.assertEqual(_canon_numista_ruler("John"), "Hans")

    def test_john_with_reign_dates(self) -> None:
        self.assertEqual(_canon_numista_ruler("John (Hans) (1483-1513)"), "Hans")

    def test_non_john_unchanged(self) -> None:
        self.assertEqual(_canon_numista_ruler("Christian IV"), "Christian IV")
        self.assertEqual(_canon_numista_ruler("Frederik III"), "Frederik III")


if __name__ == "__main__":
    unittest.main()
