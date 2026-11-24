"""«U.år» (undated) in a Hede variant's year list.

Hede writes «U.år» beside the dated years when the variant also exists
without a date — «A) 1566, U.år» (f2h30), «A) 1660 (R), 1661 (RR), U.år (R)»
(f3h16), each with its own rarity — or alone, when the variant is undated
(«B) U.år», f2h31). Before 2026-11-18 the parser dropped the token: the dated
years looked like the whole story, and an undated-only letter inherited the
page's years (Hede 31B took 31A's 1566, Hede 102A/B/D/E/F took 102C's 1619).
The seed now keeps the dated years and records the undated pieces; an
undated-only variant gets the reign (inferred), or Hede's attribution in the
parenthesis («U.år (1611)», «U.år (1609 (Hede) eller 1611 (Harck))»).

Run:  .venv/bin/python -m unittest tests.test_parse_hede_undated -v
"""
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from lib.paths import HARVEST_ROOT  # noqa: E402

import parse_hede as ph  # noqa: E402

CACHE = HARVEST_ROOT / "hede"


def _parse(basename: str) -> dict:
    html = (CACHE / f"{basename}.htm").read_text(encoding="utf-8", errors="replace")
    return ph.parse_one(html, basename)


class UndatedAsPrinted(unittest.TestCase):
    def test_forms(self):
        f = ph._undated_as_printed
        self.assertEqual(f("A) 1566, U.år; Møntmærke"), "1566, U.år")
        self.assertEqual(f("B) U.år; Uden møntmærke (Hede 31B"), "U.år")
        self.assertEqual(f("A) 1660 (R), 1661 (RR), U.år (R): møntmærke"),
                         "1660 (R), 1661 (RR), U.år (R)")
        self.assertEqual(f("A) U.år (1609 (Hede) eller 1611 (Harck)); Mønt"),
                         "U.år (1609 (Hede) eller 1611 (Harck))")
        self.assertEqual(f("C) U.år (RRR), (Hede 21C, Schou 1"), "U.år (RRR)")
        self.assertIsNone(f("A) 1566 (R), 1567; Møntmærke"))

    def test_last_list_wins(self):
        # The heading's «u. år» is not the variant's list (nf3h39).
        self.assertEqual(
            ph._undated_as_printed("1 og 2 Speciedaler u. år, Christiania "
                                   "1 Speciedaler; U.år (1661) (RRR). ("),
            "U.år (1661) (RRR)")


@unittest.skipUnless((CACHE / "f2h31.htm").exists(), "harvest cache not present")
class UndatedOnPages(unittest.TestCase):
    def test_letters(self):
        d = _parse("f2h31")
        self.assertEqual(d["by_letter"]["A"].get("undated"), "1566 (R), U.år")
        self.assertEqual(d["by_letter"]["B"].get("undated"), "U.år")
        self.assertEqual(d["by_letter"]["B"]["years"], [])

    def test_by_hede(self):
        d = _parse("f3h82")
        bh = d["specs"]["by_hede"]
        self.assertEqual(bh["81"].get("undated"), "1669, U.år (RRR)")
        self.assertEqual(bh["83"].get("undated"), "U.år (Unik)")

    def test_no_undated_on_dated_letter(self):
        d = _parse("f2h30")
        self.assertNotIn("undated", d["by_letter"]["B"])


if __name__ == "__main__":
    unittest.main()
