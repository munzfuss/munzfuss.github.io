"""Galster per-coin pages that discovery never reached (found 2026-10-20).

`fetch_galster.py` walked only the three reign indexes and matched hrefs with
a substring regex. Pages linked only from a denomination overview — the
Rigsrådet page (Galster 22) from hvid.htm, the Gotland pages from hvid.htm /
skilling.htm, norge/nc3g176.htm (no Christian III index exists) — were never
fetched, and c2g39.htm, linked root-relative from c2galst.htm, matched no
pattern because the patterns required a chr/ folder. The same substring search
manufactured phantom paths (`/hansg151.htm` out of `norge/hansg151.htm`) that
404'd silently. Nothing announced the gap: a page that is never fetched leaves
no error, only a coin missing from the table.

Behind discovery, the parser had to learn the same root-level filename
(Galster number and ruler volume came from a `_c2g…` regex that needs an
underscore) and the page shapes the new pages brought: letter variants with
their own years (c2g39), «U.år» before a commentary year (gotlg145 «lensmand
(1517-25)»), an elided century «(15)35», three coins on one page (rigsraad).
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "maintenance"))

import fetch_galster as fg  # noqa: E402
import parse_galster as pg  # noqa: E402
from lib.galster_parsers import classify, standard  # noqa: E402
import build_galster_denmark_seed as bg  # noqa: E402


class DiscoveryPatterns(unittest.TestCase):
    def test_new_page_shapes_are_coin_pages(self):
        html = ('<A HREF="c2g39.htm">39</A> <a href="rigsraad.htm">x</a> '
                '<a href="norge/nc3g176.htm">176</a> <a href="gotlg143.htm">143</a> '
                '<a href="https://www.danskmoent.dk/norge/nc2g173.htm">173</a>')
        self.assertEqual(fg._extract_links(html), {
            "/c2g39.htm", "/rigsraad.htm", "/norge/nc3g176.htm",
            "/gotlg143.htm", "/norge/nc2g173.htm"})

    def test_no_phantom_root_path_from_subfolder_link(self):
        """`norge/hansg151.htm` must not also yield `/hansg151.htm`."""
        links = fg._extract_links('<a href="norge/hansg151.htm">151</a> '
                                  '<a href="chr/c2g37.htm">37</a>')
        self.assertEqual(links, {"/norge/hansg151.htm", "/chr/c2g37.htm"})

    def test_overview_and_article_links_are_not_coin_pages(self):
        self.assertFalse(fg._is_percoin_path("/hvid.htm"))
        self.assertFalse(fg._is_percoin_path("/myst/aag1.htm"))
        self.assertFalse(fg._is_percoin_path("/hbg4.htm"))

    def test_pre_1481_pages_are_out_of_scope(self):
        for path in ("/c1g23.htm", "/chr/c1g214.htm", "/sc1g215.htm",
                     "/bajg18.htm", "/epomg2.htm", "/spomg202.htm", "/m1g1.htm",
                     "/gotlg134.htm", "/gotlg138.htm"):
            self.assertTrue(fg._is_out_of_scope(path), path)

    def test_in_scope_pages_are_kept(self):
        for path in ("/c2g39.htm", "/rigsraad.htm", "/norge/nc3g176.htm",
                     "/gotlg139.htm", "/gotlg147.htm", "/chr/c3g246.htm"):
            self.assertFalse(fg._is_out_of_scope(path), path)

    def test_fantasy_coin_is_out_of_scope(self):
        """fr/hg253.htm: «støbt fantasimønt», never a coin."""
        self.assertTrue(fg._is_out_of_scope("/fr/hg253.htm"))


class FilenameHandling(unittest.TestCase):
    def test_root_level_reign_page_is_a_coin_page(self):
        self.assertEqual(classify.detect_page_shape(Path("c2g39.htm"), ""),
                         "standard")
        self.assertEqual(classify.detect_page_shape(Path("rigsraad.htm"), ""),
                         "rigsraad")
        # A root-level overview stays a non-coin page.
        self.assertEqual(classify.detect_page_shape(Path("hvid.htm"), ""),
                         "reign_index")

    def test_galster_number_from_filename(self):
        self.assertEqual(standard._galster_number_from_filename("c2g39.htm"), "39")
        self.assertEqual(standard._galster_number_from_filename("chr_c2g37.htm"), "37")
        self.assertEqual(
            standard._galster_number_from_filename("norge_nc3g176.htm"), "176")

    def test_root_page_url_keeps_no_folder(self):
        text = ("## Christian 2.\n\n1 Skilling u.år, Malmø\n\n"
                "Malmø. Forside: x, bagside: y\n")
        d = standard.parse_page(Path("c2g39.htm"), text)
        self.assertEqual(d["source_url_hint"], "https://www.danskmoent.dk/c2g39.htm")
        self.assertEqual(d["galster_number"], "39")
        self.assertEqual(d["ruler_volume"], "c2g")
        d = standard.parse_page(Path("norge_nc3g176.htm"), text)
        self.assertEqual(d["source_url_hint"],
                         "https://www.danskmoent.dk/norge/nc3g176.htm")


class YearAndVariantShapes(unittest.TestCase):
    def _parse(self, name: str, text: str) -> dict:
        return standard.parse_page(Path(name), text)

    def test_letter_variants_carry_their_own_years(self):
        text = (
            "## Christian 2.\n\n1 Skilling u.år, Malmø\n\n"
            "Malmø. Forside: stående konge, bagside: våbenskjold \n\n"
            "• A) 1514, U.år (Unik). Kongen med glorie. (Galster 39A, Schou hhv. 1-2 og 16)\n\n"
            "• B) 1514, 1515, U.år. Kongen uden glorie. (Galster 39B, Schou 3-4)\n\n"
            "• C) 1515. Oldenborgs våben under fødderne. (Galster 39C, Schou 16-19)\n\n"
            "• Bruttovægt: 2,61g\n")
        d = self._parse("c2g39.htm", text)
        self.assertEqual(d["year_label"], "u.år")
        self.assertEqual(d["denomination"], "1 Skilling")
        self.assertEqual([(v["galster"], v["year_label"]) for v in d["variants"]],
                         [("39A", "1514"), ("39B", "1514, 1515"), ("39C", "1515")])

    def test_undated_line_ignores_commentary_year(self):
        text = ("## Søren Norby, Hvid, Visby (Gotland)\n\n"
                "U.år. Forside våben, bagside: agnus dei (Galster 145, Schou 16-27)\n\n"
                "Mønten er slået af Christian 2.s lensmand (1517-25) på Gotland.\n")
        d = self._parse("gotlg145.htm", text)
        self.assertEqual(d["year_label"], "u.år")
        self.assertEqual(d["ruler"], "Søren Norby")
        self.assertNotIn("year_hint", d)

    def test_questioned_year_is_a_hint_only(self):
        text = ("## Søren Norby, Skilling, Visby (Gotland)\n\n"
                "U.år (1523?). Forside Søren Norbys våben (Galster 144, Schou 1-15)\n")
        d = self._parse("gotlg144.htm", text)
        self.assertEqual(d["year_label"], "u.år")
        self.assertEqual(d["year_hint"], "1523")

    def test_elided_century(self):
        text = ("## Christian 3., Skilling, Visby (Gotland)\n\n"
                "(15)35, (15)36, (15)37. Forside: agnus dei (Galster 147)\n")
        self.assertEqual(self._parse("gotlg147.htm", text)["year_label"],
                         "1535, 1536, 1537")

    def test_plain_year_bullets_still_date_the_type(self):
        """fr_f1g63: years only in «• 1524 (Schou …)» bullets after Forside."""
        text = ("## Frederik 1., Søsling, Malmø\n\nForside: Oldenborgs våben,\n"
                "bagside: Danmarks våbenskjold (Galster 63)\n\n"
                "• 1524 (Schou 113-125)\n\n• 1525 (Schou 25-38)\n")
        self.assertEqual(self._parse("fr_f1g63.htm", text)["year_label"],
                         "1524, 1525")


class RigsraadPage(unittest.TestCase):
    TEXT = (
        "## Rigsrådet\n\n Rigsrådet 1448 \n\n"
        "• Hvid U.år, Malmø. Henførtes tidligere til 1448, men regnes nu for præget 1481-1483, se nedenfor.\n\n"
        "• Skilling U.år, Malmø. Forside: Danmarks våben, bagside: kors på skjold (Galster 21)\n\n"
        " Rigsrådet 1481-83 \n\n"
        "• Hvid U.år, Malmø. Forside: lebard, bagside: kors på skjold (Galster 22)\n\n"
        " Rigsrådet 1533 \n\n"
        "• Toskilling, Malmø (S); Forside Danmarks våben, bagside: skjold (Galster 81, Schou 1-2, Sieg 1)\n")

    def test_one_record_per_galster_bullet(self):
        d = pg._PARSERS["rigsraad"](Path("rigsraad.htm"), self.TEXT)
        got = [(c["galster_number"], c["denomination"], c["year_label"],
                c.get("year_hint")) for c in d["coins"]]
        self.assertEqual(got, [("21", "Skilling", "u.år", "1448"),
                               ("22", "Hvid", "u.år", "1481-1483"),
                               ("81", "Toskilling", "1533", None)])

    def test_seed_dates_and_ids(self):
        d = pg._PARSERS["rigsraad"](Path("rigsraad.htm"), self.TEXT)
        entries = [bg.build_entry(c) for c in d["coins"]]
        self.assertIsNone(entries[0])                  # Galster 21, 1448: before 1481
        g22, g81 = entries[1], entries[2]
        self.assertEqual(g22["id"], "dk-galster-rigsraad-22")
        self.assertEqual((g22["year_first"], g22["year_last"],
                          g22["year_verified"]), (1481, 1483, False))
        self.assertEqual(g81["id"], "dk-galster-rigsraad-81")
        self.assertTrue(g81["year_verified"])


class HansIndexRows(unittest.TestCase):
    """hans.htm rows without a link are the only record of that coin
    (Galster 148, 150, 152, …); linked rows and nested variants are not."""
    HTML = (
        '<A HREF="hvid.htm">Hvid</A>\n<UL>\n'
        '<LI><A HREF="hansg31.htm">U.&aring;r, Malm&oslash;. Forside: kronet h</A> (Galster 31, Schou 124-167)\n'
        '<LI>U.&aring;r (Unik), Bergen (Norge). Meget slidt eksemplar '
        '(Galster 154, mangler hos Schou og Schive, Ernst 1940 side 77 fig. 3)\n'
        '</UL>\n<P>\n'
        '<A HREF="1penning.htm">Hulpenning</A>\n<UL>\n'
        '<LI>Oslo (Norge). Hulpenning: l&oslash;ve (Galster 156, Schou 226, Schive XIV.37)\n'
        '</UL>\n<P>\n')

    def test_only_unlinked_rows(self):
        from lib.galster_parsers import hans_index
        coins = hans_index.parse_coins(self.HTML)
        self.assertEqual([(c["galster_number"], c["denomination"], c["mint"],
                           c["sub_realm"]) for c in coins],
                         [("154", "Hvid", "Bergen", "norway"),
                          ("156", "Hulpenning", "Oslo", "norway")])
        self.assertNotIn("schou", coins[0]["catalog_refs"])   # «mangler hos»

    def test_hans_index_is_its_own_shape(self):
        self.assertEqual(classify.detect_page_shape(Path("hans.htm"), ""),
                         "hans_index")


class NumberAnchoredPages(unittest.TestCase):
    """A reign-index number linked to a page named after the coin
    (f1galst «114» → husumdal.htm) is that number's coin page."""

    def test_number_anchor_links(self):
        html = ('<TD><A HREF="husumdal.htm">114</A></TD>'
                '<TD><A HREF="fr/f1g118.htm">118A</A></TD><A HREF="x.htm">Husum</A>')
        self.assertEqual(fg._number_anchor_links(html, "/f1galst.htm"), {
            "/husumdal.htm": {"numbers": ["114"], "volume": "f1g"},
            "/fr/f1g118.htm": {"numbers": ["118A"], "volume": "f1g"}})

    def test_article_page_identity(self):
        from lib.galster_parsers import named_page
        text = ("Husumdaler\n\n## Husumdaler\n\nDen senere Frederik 1. slog 1514-1522 "
                "som hertug af Gottorp\nmønt i Husum i Slesvig.\nSærlig kendt er en "
                "sølvgylden slået i 1522,\nden såkaldte Husumdaler (Galster 114, Schou 1).\n")
        d = named_page.parse_page(Path("husumdal.htm"), text,
                                  {"numbers": ["114"], "volume": "f1g"})
        self.assertEqual((d["ruler"], d["denomination"], d["year_label"], d["mint"],
                          d["galster_number"], d["ruler_volume"]),
                         ("Frederik I", "Sølvgylden", "1522", "Husum", "114", "f1g"))
        self.assertEqual(d["catalog_refs"].get("schou"), "1")


class TableRowsAndSharedPages(unittest.TestCase):
    def test_unlinked_reign_table_row(self):
        from lib.galster_parsers import galst_table
        html = ("<TABLE><TR><TD>Galster</TD><TD>Schou</TD><TD>Sømod</TD><TD>Prægested</TD>"
                "<TD>Nominal</TD><TD>Materiale</TD><TD>År</TD><TD>Bemærkninger</TD></TR>"
                '<TR><TD><A HREF="chr/c2g37.htm">37</A></TD><TD>1</TD><TD>18</TD><TD>Malmø</TD>'
                "<TD>1 Nobel</TD><TD>Guld</TD><TD>1516</TD><TD></TD></TR>"
                "<TR><TD>163</TD><TD>17</TD><TD>135</TD><TD>Ukendt sted</TD><TD>Skilling</TD>"
                "<TD>Sølv</TD><TD>u.år</TD><TD>Schive XV, 6, side 138</TD></TR></TABLE>")
        coins = galst_table.parse_coins(html, "c2galst.htm")
        self.assertEqual(len(coins), 1)
        c = coins[0]
        self.assertEqual((c["galster_number"], c["ruler"], c["mint"], c["sub_realm"],
                          c["catalog_refs"]),
                         ("163", "Christian II", None, "norway",
                          {"galster": "163", "schou": "17", "schive": "XV.6"}))

    def test_two_numbers_one_grevens_fejde_page(self):
        text = ("• 1534 (Unik), Klipping, Malmø eller København (Galster 82, af Schou "
                "henført til Christian 3, 1534-1, Sieg 3)\n\n"
                "• 1535 (RRR), Klipping, Malmø eller København (Galster 83, af Schou "
                "henført til Christian 3, 1535-17, Sieg 4; ligeledes Reynold Junge)\n")
        data = {"galster_number": "82", "year_label": "1534, 1535", "ruler": "Christian II"}
        old = pg._numbers_for
        try:
            pg._numbers_for = lambda name: ["82", "83"]
            pg._split_numbered_bullets(data, text, "chr_c2g82.htm")
        finally:
            pg._numbers_for = old
        self.assertEqual((data["year_label"], data["catalog_refs"]),
                         ("1534", {"galster": "82", "sieg": "3"}))
        (c83,) = data["extra_coins"]
        self.assertEqual((c83["galster_number"], c83["year_label"], c83["catalog_refs"]),
                         ("83", "1535", {"galster": "83", "sieg": "4"}))


class NorbyRouting(unittest.TestCase):
    """Norby's own Visby coins (own name and arms) → norby_gotland; his
    Ronneby søslinge in Frederik I's name and anything else are untouched."""

    def test_routing(self):
        from lib.mint_registry import norby_gotland_entity as f
        self.assertEqual(f("danish_realm", "Visby", "Søren Norby"), "norby_gotland")
        self.assertEqual(f("danish_realm", "Visby", "Søren Nordby"), "norby_gotland")
        self.assertEqual(f("danish_realm", "Ronneby", "Frederik I"), "danish_realm")
        self.assertEqual(f("danish_realm", "Visby", "Christian III"), "danish_realm")
        self.assertEqual(f("christian_ii_supporters", "Landskrona", "Christian II"),
                         "christian_ii_supporters")


class BuilderGuards(unittest.TestCase):
    def test_fantasy_coin_is_not_seeded(self):
        """fr/f1g257: «1 Sølvgylden - støbt fantasimønt» (curator 2026-10-20)."""
        import json, tempfile
        d = {"source_file": "fr_f1g257.htm", "ruler": "Frederik I",
             "ruler_volume": "f1g", "galster_number": "257", "year_label": "u.år",
             "denomination": "1 Sølvgylden",
             "raw_text_excerpt": "## Frederik 1, 1 Sølvgylden - støbt fantasimønt"}
        with tempfile.TemporaryDirectory() as tmp:
            Path(tmp, "fr_f1g257.json").write_text(json.dumps(d))
            old = bg.GALSTER_CACHE
            try:
                bg.GALSTER_CACHE = Path(tmp)
                self.assertEqual(bg.collect_entries(), [])
            finally:
                bg.GALSTER_CACHE = old

    def test_named_ruler_does_not_inherit_the_filename_reign(self):
        """Christian I's Gotland gote sit in Hans's «hg» file series."""
        e = bg.build_entry({"ruler": "Christian I", "ruler_volume": "hg",
                            "year_label": "u.år", "galster_number": "139",
                            "source_file": "gotlg139.htm", "denomination": "Gote"})
        self.assertIsNone(e)                           # 1448-1481 → before scope

    def test_foreign_hhv_list_stays_with_its_catalogue(self):
        cat = {"galster": "147, Hauberg hhv. 132-140, 141-144 og 145"}
        bg._clean_catalogue_refs(cat)
        self.assertEqual(cat["galster"], "147")
        self.assertEqual(cat["others"], ["Hauberg# hhv. 132-140, 141-144 og 145"])

    def test_two_mint_prefix_leaves_the_denomination(self):
        nominal, mint, shape = bg._split_nominal_mint(
            "Hamar/Oslo, 2 mark klipping", "Hamar eller Oslo")
        self.assertEqual((nominal, mint, shape), ("2 mark", "Hamar eller Oslo", "klipping"))


if __name__ == "__main__":
    unittest.main()
