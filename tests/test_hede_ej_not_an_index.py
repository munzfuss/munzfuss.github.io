"""«Hede ej» is not a Hede number.

danskmoent names a page `f3hej.htm` / `c7hej.htm` and heads it «Hede ej» when
Hede gives the coin no number of its own — «ej» is Danish «not» («(Hede ej,
Schou ej)» on c7hej). The seed builder used the page code as the index, so the
rendered row read «Hede# 72, ej». The seed keeps the page as a source; only the
index is dropped (curator 2026-11-10).
"""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "maintenance"))
import build_hede_denmark_seed as b  # noqa: E402


class HedeEj(unittest.TestCase):
    def test_ej_is_no_index(self):
        for v in ("ej", "EJ", " ej "):
            self.assertIsNone(b._hede_index_or_none(v))

    def test_real_numbers_kept(self):
        for v in ("72", "68A", "113C", "12AB"):
            self.assertEqual(b._hede_index_or_none(v), v)

    def test_none_stays_none(self):
        self.assertIsNone(b._hede_index_or_none(None))


if __name__ == "__main__":
    unittest.main()
