"""Galster pages of the Union kings before Hans (harvested 2026-10-25).

The Lybsk Møntfod reaches back to Galster 1, the Ribe hvid of c. 1380, so the
pages of Margrethe I (m1g1), Erik af Pommern (epomg, Swedish spomg), Christoffer
af Bayern (bajg, sbajg, fbajg) and Christian I (c1g) are now parsed and seeded.
Their headers differ from the Hans-era pages: the ruler is named by his house
(«Erik af Pommern»), the H1 can be the ruler alone with the type on the next
line, or the type alone with the ruler in the page title (m1g1); dates are «ca.
1380», «u. år (1440-1442)», «1400-tallet»; the Gotland gote before Hans give
their window only in a list of the three series. The literature list must not
supply a mint («Flensborg, Peter: …»), and the Galster scope must match the one
the 2016:1 metal analyses already carry (galster1972-erik7 …).
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "maintenance"))

from lib.galster_parsers import classify, standard  # noqa: E402
import build_galster_denmark_seed as bg  # noqa: E402
import merge_seeds_cross_source as msc  # noqa: E402


def _parse(name: str, text: str) -> dict:
    return standard.parse_page(Path(name), text)


class UnionPageHeaders(unittest.TestCase):
    def test_ruler_h1_then_type_line(self):
        d = _parse("epomg7.htm",
                   "Erik af Pommern Kobbersterling Næstved\n\n## Erik af Pommern\n\n"
                   "Kobbersterling, Næstved, ca. 1422\n\nForside: kronet\n\n"
                   " Litteratur: \n\n• Flensborg, Peter: Erik af Pommerns kobbersterling\n")
        self.assertEqual((d["ruler"], d["denomination"], d["mint"], d["year_label"]),
                         ("Erik VII", "Kobbersterling", "Næstved", "1422"))
        self.assertTrue(d["year_approx"])
        self.assertEqual((d["galster_number"], d["ruler_volume"]), ("7", "epomg"))

    def test_type_h1_with_ruler_in_title(self):
        d = _parse("m1g1.htm", "Margrethe 1. \n\n## Hvid, Ribe, ca. 1380\n\n"
                               "Denne mønt (Galster 1) er slået i Ribe ca. 1380\n")
        self.assertEqual((d["ruler"], d["denomination"], d["mint"], d["year_label"]),
                         ("Margrethe I", "Hvid", "Ribe", "1380"))

    def test_undated_with_window_in_parentheses(self):
        d = _parse("bajg17.htm", "Christoffer af Bajern, Galster 17 \n\n"
                                 "## Christoffer af Bajern\n\n"
                                 "Søsling u. år (1440-1442), Lund\n\n"
                                 "Forside: Regenten (Galster 17)\n")
        self.assertEqual((d["ruler"], d["denomination"], d["year_label"],
                          d["year_hint"]),
                         ("Christoffer III", "Søsling", "u.år", "1440-1442"))

    def test_every_undated_dating_is_a_hint(self):
        """A year in parentheses after «u. år» is the page's tentative dating
        in every form, never the coin's own year (curator 2026-11-10)."""
        d = _parse("norge_nc2g174.htm",
                   "Christian 2., Galster 174 \n\n## Christian 2. Hamar (Norge) eller "
                   "København, Søsling(?) (klipping), u. år (1531-32)?\n\n"
                   "A) Forside: kronet C (Galster 174; Schou 1)\n")
        self.assertEqual((d["year_label"], d["year_hint"]), ("u.år", "1531-1532"))
        self.assertNotIn("u. år", d["denomination"])
        d = _parse("chr_c3g130.htm", "Christian 3., Galster 130 \n\n"
                                     "## Christian 3., 1 Rhinsk gylden, u.år (1534) Gottorp\n\n"
                                     "Forside: våbenskjolde (Galster 130, Schou 1-2)\n")
        self.assertEqual((d["year_label"], d["year_hint"], d["denomination"]),
                         ("u.år", "1534", "1 Rhinsk gylden"))

    def test_decade_in_prose_is_a_window(self):
        """epomg13: «indførtes af Erik af Pommern i 1430erne» is no year."""
        d = _parse("epomg13.htm", "## Erik af Pommern, Gros (9 penning), Lund\n\n"
                                  "Forside: krone, bagside: (Galster 13)\n\n"
                                  "Denne mønttype … indførtes af Erik af Pommern i 1430erne.\n")
        self.assertEqual((d["year_label"], d["year_hint"]), ("u.år", "1430-1439"))

    def test_single_year_in_parentheses_is_a_hint(self):
        """chr/c3g130 «u.år (1534)»: the year is the page's tentative dating,
        not an attested one (curator 2026-11-10; it used to stay the year)."""
        h = standard._parse_header_h1("## Christian 3., 1 Rhinsk gylden, u.år (1534) Gottorp\n")
        self.assertEqual((h["year_label"], h["year_hint"]), ("u.år", "1534"))

    def test_joint_mint_kept_whole(self):
        d = _parse("epomg5.htm", "## Erik af Pommern\n\n"
                                 "Hulpenning, Næstved og Lund, ca. 1400-1420\n\nx\n")
        self.assertEqual((d["denomination"], d["mint"]), ("Hulpenning", "Næstved og Lund"))

    def test_gotland_window_from_the_series_list(self):
        d = _parse("gotlg135.htm",
                   "Gotland Galster 135 \n\n## Gote u. år, Visby (Gotland)\n\n"
                   "Forside: ranke (Galster 135, Hauberg 33-46)\n\n"
                   "Mellem Valdemar Atterdag s erobring af\n Gotland 1361 og Erik\n"
                   "Visby ca. 1320-1380 (Galster 134, Hauberg 8-32)\n"
                   "Visby ca. 1380-1420 (Galster 135, Hauberg 33-46)\n")
        self.assertEqual((d["year_label"], d["year_hint"], d["mint"]),
                         ("u.år", "1380-1420", "Visby"))

    def test_swedish_page_routes_to_sweden(self):
        d = _parse("spomg198.htm", "## Erik af Pommern\n\nØrtug u. år, Vesterås\n\n"
                                   "Type I (Galster 198, Hildebrand 681)\n")
        self.assertEqual(d["sub_realm"], "sweden")
        self.assertEqual(bg.detect_issuing_entity(d["sub_realm"], d["mint"], 1420), "sweden")

    def test_reign_pages_are_not_coins(self):
        for name in ("m1.htm", "erikpomm.htm", "bajern.htm", "c1.htm"):
            self.assertEqual(classify.detect_page_shape(Path(name), "## x\n"),
                             "reign_index", name)


class UnionSeedEntries(unittest.TestCase):
    def test_approximate_year_is_unverified(self):
        e = bg.build_entry({"ruler": "Margrethe I", "ruler_volume": "m1g",
                            "galster_number": "1", "year_label": "1380",
                            "year_approx": True, "denomination": "Hvid",
                            "mint": "Ribe", "source_file": "m1g1.htm",
                            "catalog_refs": {"galster": "1"}})
        self.assertEqual((e["year_first"], e["year_verified"]), (1380, False))
        self.assertEqual(e["catalog"]["galster_volume"], "galster1972-margrethe1")

    def test_joint_mint_becomes_a_list(self):
        e = bg.build_entry({"ruler": "Erik VII", "ruler_volume": "epomg",
                            "galster_number": "5", "year_label": "1400-1420",
                            "denomination": "Hulpenning", "mint": "Næstved og Lund",
                            "source_file": "epomg5.htm",
                            "catalog_refs": {"galster": "5"}})
        self.assertEqual(sorted(e["mint"]), ["Lund", "Næstved"])
        self.assertEqual(e["issuing_entity"], "danish_realm")

    def test_before_1370_stays_out(self):
        e = bg.build_entry({"ruler": None, "ruler_volume": "hg",
                            "galster_number": "134", "year_label": "u.år",
                            "year_hint": "1320-1380", "denomination": "Gote",
                            "mint": "Visby", "source_file": "gotlg134.htm",
                            "catalog_refs": {"galster": "134"}})
        self.assertIsNone(e)


class MergerGalsterScope(unittest.TestCase):
    def test_union_kings_share_the_metal_analysis_scope(self):
        for ruler, vol in (("Erik VII", "galster1972-erik7"),
                           ("Erik VII of Pomerania", "galster1972-erik7"),
                           ("Christopher III of Bavaria", "galster1972-christoffer3"),
                           ("Christoffer III", "galster1972-christoffer3")):
            refs = msc._catalog_refs({"ruler": ruler, "catalog": {"galster": "2"}})
            self.assertIn(f"galster/{vol}", refs, ruler)

    def test_later_kings_unchanged(self):
        refs = msc._catalog_refs({"ruler": "Christian III", "catalog": {"galster": "92"}})
        self.assertIn("galster/c3g", refs)


if __name__ == "__main__":
    unittest.main()
