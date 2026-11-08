"""Hede header «<nominal>. <Mint> og <Mint>»: the mint after a full stop.

f7h12 «1 Rigsbankskilling. København og Altona» carried no year and no comma,
so the whole line became the nominal and the coin had no mint (2026-11-08).
The split happens only when every part after the stop is a known mint.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import parse_hede as ph  # noqa: E402


def _h(line2: str) -> dict:
    return ph._parse_header(f"<H1>Frederik 7.<BR>{line2}</H1>")


class HeaderStopMint(unittest.TestCase):
    def test_two_mints(self):
        out = _h("1 Rigsbankskilling. København og Altona")
        self.assertEqual(out["nominal"], "1 Rigsbankskilling")
        self.assertEqual(out["mint"], "København og Altona")

    def test_one_mint(self):
        out = _h("16 Skilling rigsmønt. København")
        self.assertEqual(out["nominal"], "16 Skilling rigsmønt")
        self.assertEqual(out["mint"], "København")

    def test_stop_without_mint_stays_whole(self):
        out = _h("2 Skilling. Kobber")
        self.assertEqual(out["nominal"], "2 Skilling. Kobber")
        self.assertNotIn("mint", out)


if __name__ == "__main__":
    unittest.main()
