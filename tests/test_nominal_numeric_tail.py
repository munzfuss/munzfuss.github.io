"""The seed writer strips Numista's bare-number value tail from a nominal —
«1½ Gulden (1.5)», «¼ Ducat (0.875)», «1 Ducat (3.5)» (44 seeds, 2026-10-23)
— as it already stripped the category number «(7)». A number with a
denomination word, «(3 Mark)», is a dual denomination and stays (§9.5).

    .venv/bin/python -m unittest tests.test_nominal_numeric_tail -v
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from lib.v2_seed_writer import _normalise_nominal  # noqa: E402


class NumericTail(unittest.TestCase):
    def test_decimal_tail_is_stripped(self):
        self.assertEqual(_normalise_nominal("1½ Gulden (1.5)"), "1½ Gulden")
        self.assertEqual(_normalise_nominal("¼ Ducat (0.875)"), "¼ Ducat")
        self.assertEqual(_normalise_nominal("1 Ducat (3.5)"), "1 Ducat")
        self.assertEqual(_normalise_nominal("1 Goldgulden (3,25)"), "1 Goldgulden")

    def test_category_number_still_stripped(self):
        self.assertEqual(_normalise_nominal("2 Ducats (7)"), "2 Ducats")

    def test_dual_denomination_stays(self):
        self.assertEqual(_normalise_nominal("¼ Ducat (3 Mark)"), "¼ Ducat (3 Mark)")
        self.assertEqual(_normalise_nominal("1 Krone (4 Mark)"), "1 Krone (4 Mark)")


if __name__ == "__main__":
    unittest.main(verbosity=2)
