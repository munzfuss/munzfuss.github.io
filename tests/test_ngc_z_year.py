"""NGC dates printed with a Z-shaped 2 («16Z4») or implied century («(16)19»).

NGC 1050065 — Christian IV, 24 Skilling, KM 93 — has a single date cell
«16Z4(a)». The parser treated the Z as an unreadable digit and read no year,
so the seed carried none and the coin fell off the Denmark page («no year
information»). Z is the coin's own Z-shaped 2, as Krause prints it (curator,
2026-10-17); NumisMaster heads KM 101's date table «1624 - 1634» over rows
«16Z4 … 16Z7», and Numista issues pair `"year": 1622` with «(16)ZZ».

The same parser expanded only «(1)604»; «(16)19», «(15)93 (cc)», «(160)9»
— the same convention, more digits — read nothing either. Together the two
forms left 113 of the NGC records with no year at all and cost 39 more some
of their year cells (measured 2026-10-17). Nothing announced either loss:
a missing year is a legitimate state, so the coin simply went undated.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "maintenance"))

from parse_ngc import normalise_date, parse_years  # noqa: E402


def years(*cells):
    return parse_years({"dates": [{"year_mint": c} for c in cells]})


class ZShapedTwo(unittest.TestCase):
    def test_km93_single_cell(self):
        out = years("16Z4(a)")
        self.assertEqual((out["year_first"], out["year_last"]), (1624, 1624))
        self.assertNotIn("year_partially_illegible", out)
        self.assertEqual(out["dates_as_printed"], ["16Z4(a)"])

    def test_every_digit_slot(self):
        self.assertEqual(normalise_date("16ZZ"), "1622")
        self.assertEqual(normalise_date("165Z(h)"), "1652(h)")
        self.assertEqual(normalise_date("15Z5"), "1525")

    def test_mintmaster_z_is_not_a_digit(self):
        """«BZ» after the year is a mintmaster, not a date digit."""
        self.assertEqual(normalise_date("16Z7 BZ"), "1627 BZ")
        self.assertEqual(normalise_date("1711IW"), "1711IW")


class ImpliedCentury(unittest.TestCase):
    def test_parenthesised_leading_digits(self):
        self.assertEqual(years("(16)19")["years_all"], [1619])
        self.assertEqual(years("(15)93 (cc)")["years_all"], [1593])
        self.assertEqual(years("(160)9 (b)")["years_all"], [1609])
        self.assertEqual(years("(1)604 (a)")["years_all"], [1604])

    def test_both_conventions_together(self):
        self.assertEqual(years("(16)ZZ ST")["years_all"], [1622])
        self.assertEqual(years("(15)9Z CJ")["years_all"], [1592])

    def test_mintmark_and_range_untouched(self):
        self.assertEqual(normalise_date("1651 (c)"), "1651 (c)")
        self.assertEqual(normalise_date("(1618-22)"), "(1618-22)")


class StillUnread(unittest.TestCase):
    def test_no_guessing(self):
        for cell in ("16xx", "160(0?) (aa)", "ND", "Rare", "166z"):
            self.assertIsNone(years(cell)["year_first"], cell)
        self.assertTrue(years("166z").get("year_partially_illegible"))

    def test_plain_years_not_marked_rewritten(self):
        self.assertNotIn("dates_as_printed", years("1624", "1651 (c)"))


if __name__ == "__main__":
    unittest.main()
