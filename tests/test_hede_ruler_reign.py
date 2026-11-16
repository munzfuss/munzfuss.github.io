"""An undated Hede coin whose page names another king than the volume's.

The crowned-C Blaffert sits on Christian III's page (c3h23) but the page names
«Christian 2. (?)». Before 2026-11-14 the builder anchored the year to the
volume's reign (1534-1559) and kept the ruler as printed. Now the ruler is
normalised, the «(?)» travels as a hedged ruler uncertainty, and the year is
the named king's reign.
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "maintenance"))

import build_hede_denmark_seed as b  # noqa: E402


class RulerReign(unittest.TestCase):
    def test_hedged_ruler_is_normalised(self):
        self.assertEqual(b._normalise_ruler("Christian 2. (?)."), "Christian II.")
        self.assertEqual(b._normalise_ruler("Christian 3."), "Christian III.")

    def test_hedge_text_is_kept(self):
        self.assertEqual(b._ruler_hedge("Christian 2. (?)."), "Christian 2. (?)")
        self.assertIsNone(b._ruler_hedge("Christian 3."))

    def test_named_king_reign_wins_over_volume(self):
        self.assertEqual(b._reign_for_ruler("Christian II."), (1513, 1523))
        self.assertIsNone(b._reign_for_ruler("Christian III."))
        self.assertIsNone(b._reign_for_ruler(None))


if __name__ == "__main__":
    unittest.main()
