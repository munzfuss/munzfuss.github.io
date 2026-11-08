"""A mint at the end of the year line, not in the H1, is read
(danskmoent c8h5 «1842, 1843, Altona. Forside: …», c4h137, f6h29)."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import parse_hede as P  # noqa: E402


class YearsLineMint(unittest.TestCase):
    def test_regex_takes_registered_mint_after_years(self):
        m = P._YEARS_LINE_MINT_RE.search("32 Rigsbankskilling\n1842, 1843, Altona. Forside: portræt,")
        self.assertEqual(m.group(1), "Altona")

    def test_line_must_open_with_a_year(self):
        self.assertIsNone(P._YEARS_LINE_MINT_RE.search("Forside: portræt, Altona. 1842"))

    def test_cached_pages(self):
        for page, mint in (("c8h5", "Altona"), ("c4h137", "København"), ("f6h29", "Altona")):
            p = ROOT / "scripts" / "cache" / "hede" / f"{page}.htm"
            if not p.exists():
                self.skipTest("harvest cache not checked out")
            d = P.parse_one(p.read_text(encoding="latin-1"), page)
            self.assertEqual(d.get("mint"), mint, page)


if __name__ == "__main__":
    unittest.main()
