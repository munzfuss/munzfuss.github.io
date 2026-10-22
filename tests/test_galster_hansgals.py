"""hansgals.htm (Hans, «oversigt efter Galster») as a catalogue-column source.

`galst_table` reads every row of the Hans table, linked or not, but skips the
«Falske mønter» table; the seed builder folds a row's catalogue into the entry
the coin already has (its page, its hans.htm row, or a page named for the
denomination such as 2nobel.htm), filling registers the entry lacks and adding
cross-references without duplicating one spelled differently. Synthetic HTML,
so the test does not depend on the harvest cache.

Run: .venv/bin/python -m unittest tests.test_galster_hansgals -v
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
sys.path.insert(0, str(PROJECT_ROOT / "scripts" / "maintenance"))

from lib.galster_parsers.galst_table import parse_coins  # noqa: E402
from build_galster_denmark_seed import _fold_catalogue_rows  # noqa: E402

_HEAD = ("<TR><TD>Galster</TD><TD>Schou</TD><TD>Sømod</TD><TD>Prægested</TD>"
         "<TD>Nominal</TD><TD>Materiale</TD><TD>År</TD><TD>Bemærkninger</TD></TR>")
_HTML = (
    "<H2>Norge</H2><TABLE>" + _HEAD +
    "<TR><TD><A HREF='norge/hansg155.htm'>155</A></TD><TD>187-213</TD><TD>125</TD>"
    "<TD>Oslo eller Akershus</TD><TD>Hvid</TD><TD>Sølv</TD><TD>u.år</TD>"
    "<TD>Schive XIV,12-25; Ernst 3-13</TD></TR></TABLE>"
    "<H2>Sverige</H2><TABLE>" + _HEAD +
    "<TR><TD>230</TD><TD>2</TD><TD>175</TD><TD>Stockholm</TD><TD>Ørtug</TD>"
    "<TD>Sølv</TD><TD>u.år</TD><TD>Hildebrand 712; Rasmusson bild 13</TD></TR></TABLE>"
    "<H2>Falske m&oslash;nter</H2><TABLE>"
    "<TR><TD>Galster</TD><TD>Schou</TD><TD>Nominal</TD></TR>"
    "<TR><TD>252</TD><TD>1508 side 13</TD><TD>Nobel</TD></TR></TABLE>"
)


def _entry(eid, url, catalog, ruler="Hans"):
    return {"id": eid, "ruler": ruler, "catalog": catalog,
            "sources": [{"type": "literature", "url": url, "ref": eid}]}


class HansgalsTable(unittest.TestCase):
    def test_rows_read_and_forgeries_skipped(self) -> None:
        rows = {c["galster_number"]: c for c in parse_coins(_HTML, "hansgals.htm")}
        self.assertEqual(set(rows), {"155", "230"})
        self.assertTrue(rows["155"]["index_has_page"])
        self.assertEqual(rows["155"]["catalog_refs"]["Ernst"], "1940 3-13")
        self.assertEqual(rows["230"]["catalog_refs"],
                         {"galster": "230", "schou": "2", "Sømod": "175",
                          "Hildebrand": "712", "Rasmusson": "ill. 13"})

    def test_other_tables_keep_unlinked_rows_only(self) -> None:
        self.assertEqual([c["galster_number"] for c in parse_coins(_HTML, "c2galst.htm")],
                         ["230"])

    def test_fold_fills_and_dedupes(self) -> None:
        page = _entry("dk-galster-hg-152", "https://www.danskmoent.dk/hans.htm",
                      {"galster": "152", "schou": "170", "others": ["Ernst# 1940.1"]})
        row = _entry("dk-galster-hg-152", "https://www.danskmoent.dk/hansgals.htm",
                     {"galster": "152", "schou": "999",
                      "others": ["Sømod# 123B", "Ernst# 1940 1"]})
        out = _fold_catalogue_rows([page, row])
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["catalog"]["schou"], "170")       # never replaced
        self.assertEqual(out[0]["catalog"]["others"], ["Ernst# 1940.1", "Sømod# 123B"])
        self.assertEqual(len(out[0]["sources"]), 2)

    def test_fold_finds_denomination_named_page_by_number(self) -> None:
        page = _entry("dk-galster-2nobel", "https://www.danskmoent.dk/2nobel.htm",
                      {"galster": "26", "schou": "1"})
        row = _entry("dk-galster-hg-26", "https://www.danskmoent.dk/hansgals.htm",
                     {"galster": "26", "others": ["Sømod# 5"]})
        out = _fold_catalogue_rows([page, row])
        self.assertEqual([e["id"] for e in out], ["dk-galster-2nobel"])
        self.assertEqual(out[0]["catalog"]["others"], ["Sømod# 5"])


if __name__ == "__main__":
    unittest.main()
