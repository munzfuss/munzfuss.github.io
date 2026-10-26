"""The Galster page mint scan (curator 2026-10-26): a mint named only as a
possibility, or a holding museum's town on a specimen line, is not the page's
mint — fr/f1g79 «… kunne være slået i hertugdømmerne (Gottorp)», whose overview
gives «ukendt møntsted».
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from lib.galster_parsers.standard import _parse_mint_line  # noqa: E402


class MintLine(unittest.TestCase):
    def test_hedged_sentence_is_not_a_mint(self):
        t = ("Den er på grund af det kronede F henført til kongeriget, skønt den ligeså\n"
             "godt kunne være slået i hertugdømmerne (Gottorp). Da vægten ligger …")
        self.assertIsNone(_parse_mint_line(t))

    def test_specimen_line_is_not_a_mint(self):
        self.assertIsNone(_parse_mint_line("## Eksemplar fra Kulturhistorisk Museum, Oslo:\n U. år"))

    def test_plain_mint_still_read(self):
        self.assertEqual(_parse_mint_line("1 Hvid 1524, Malmø\nForside: kronet F"), "Malmø")


if __name__ == "__main__":
    unittest.main()
