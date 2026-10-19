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
from unittest import mock

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
        self.assertEqual(normalise_date("(16)19"), "1619")


class AttributedSpan(unittest.TestCase):
    """An undated coin the catalogue attributes to a span («(1618-22)») kept
    only the span's first year, as if dated — 1618, verified. The span is
    carried whole and the record is marked attributed (→ '(?)', §3a)."""

    def test_span_carried_whole(self):
        out = years("(1618-22)")
        self.assertEqual(out["years_all"], [1618, 1619, 1620, 1621, 1622])
        self.assertTrue(out["year_attributed"])
        self.assertEqual(years("(1590-1616)")["year_last"], 1616)
        self.assertEqual(years("(ca1566-70) (d)")["years_all"],
                         [1566, 1567, 1568, 1569, 1570])

    def test_approximate_year(self):
        for cell in ("(ca1611)", "(c.1620)", "(ca.1640) Rare"):
            out = years(cell)
            self.assertEqual(len(out["years_all"]), 1, cell)
            self.assertTrue(out["year_attributed"], cell)

    def test_dated_cell_keeps_record_dated(self):
        """MB 10: «(ca1523)» beside dated cells — the record is dated."""
        out = years("(15)Z5", "(ca1523)", "1514")
        self.assertNotIn("year_attributed", out)
        self.assertIn(1523, out["years_all"])

    def test_mintmark_is_not_a_span(self):
        self.assertNotIn("year_attributed", years("1651 (c)"))


class AfterBound(unittest.TestCase):
    """«(after 1620)», Schaumburg Kipper 12 Pfennig KM 93-95 (Ernst III): read
    as a verified 1620. Curator, 2026-10-17: close it on the ruler's reign end
    when known, else 1620 with '(?)'."""

    REC = {"cuid": "1153429", "heading": "German States SCHAUMBURG-PINNEBERG"
           " 12 Pfennig KM# 93", "ruler": "Ernst III",
           "dates": [{"year_mint": "(after 1620)"}]}

    def test_parser_keeps_the_bound(self):
        out = years("(after 1620)")
        self.assertEqual(out["years_all"], [1620])
        self.assertEqual(out["year_after"], 1620)
        self.assertTrue(out["year_attributed"])

    def _entry(self, reign):
        import build_ngc_seed as b
        from parse_ngc import parse_record
        rec = parse_record(self.REC)
        with mock.patch.object(b, "reign_window", return_value=reign), \
                mock.patch.object(b, "route_entity_with_rules",
                                  side_effect=lambda e, default_entity: (default_entity, None)):
            return b.build_entry(rec, "schaumburg_pinneberg")

    def test_closed_on_reign_end(self):
        e = self._entry((1601, 1622))
        self.assertEqual((e["year_first"], e["year_last"]), (1621, 1622))
        self.assertEqual(e["year_label"], "1621–1622")
        self.assertFalse(e["year_verified"])

    def test_fallback_without_reign(self):
        e = self._entry(None)
        self.assertEqual(e["year_label"], "1620")
        self.assertFalse(e["year_verified"])


class DoubledPrefix(unittest.TestCase):
    def test_prefix_before_complete_year(self):
        """«(1)1604 (c)», Schaumburg KM 7: read nothing; it is 1604."""
        self.assertEqual(normalise_date("(1)1604 (c)"), "1604 (c)")
        self.assertEqual(years("(1)1604 (c)")["years_all"], [1604])


class StillUnread(unittest.TestCase):
    def test_no_guessing(self):
        for cell in ("16xx", "160(0?) (aa)", "ND", "Rare", "166z"):
            self.assertIsNone(years(cell)["year_first"], cell)
        self.assertTrue(years("166z").get("year_partially_illegible"))

    def test_plain_years_not_marked_rewritten(self):
        self.assertNotIn("dates_as_printed", years("1624", "1651 (c)"))


if __name__ == "__main__":
    unittest.main()
