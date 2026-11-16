"""A description line that opens with the mint list gives the mint.

The Rigsbanktegn pages f6h18-f6h23 had no mint in our data although danskmoent
names two or three: the mint stands at the head of a description line,
«København og Altona. Forside: …», not in the H1 and not on the years line.
Found 2026-11-13 when the Numista refresh brought Hede numbers to those types
and the merger had no mint to compare. Every name in the list must be a mint
the registry knows, so a description line that starts with a capitalised word
is never read as a mint.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from lib.paths import HARVEST_ROOT  # noqa: E402

import parse_hede as P  # noqa: E402


class MintListLine(unittest.TestCase):
    def test_two_mints(self):
        m = P._MINT_LIST_LINE_RE.search("Rigsbanktegn\nKøbenhavn og Altona. Forside: våbenskjold")
        self.assertEqual(m.group(1), "København og Altona")

    def test_three_mints(self):
        m = P._MINT_LIST_LINE_RE.search("x\nKøbenhavn, Altona og Kongsberg. Forside: tekst")
        self.assertEqual(m.group(1), "København, Altona og Kongsberg")

    def test_a_description_word_is_not_a_mint(self):
        """«Forside.» matches the shape but is not a registered mint."""
        m = P._MINT_LIST_LINE_RE.search("x\nForside. Bagside: kors")
        names = [t.strip() for t in m.group(1).replace(" og ", ",").split(",")]
        self.assertFalse(all(P.canon_for_alias(t) is not None for t in names))

    def test_cached_pages(self):
        for page in ("f6h18", "f6h19"):
            p = HARVEST_ROOT / "hede" / f"{page}.htm"
            if not p.exists():
                self.skipTest("harvest cache not checked out")
            d = P.parse_one(p.read_text(encoding="latin-1"), page)
            self.assertTrue(d.get("mint"), page)
            self.assertIn("København", d["mint"], page)


if __name__ == "__main__":
    unittest.main()
