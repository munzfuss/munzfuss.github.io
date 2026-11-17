"""Hede index rows without a deep page — the Norge sections (2026-11-17).

The reign indices (`c5hede2.htm` …) print the Norwegian coins in their own
section, rows prefixed «N» and, in c4hede3 / c5hede2 / f3hede3, without a Sieg
column. The index-stub pass read neither, so a row like «N47 · 1 Skilling ·
Sølv · 1670 · Christiania» (no type page) produced no record at all.

Run:
    .venv/bin/python -m unittest tests.test_hede_index_norge_rows -v
"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "scripts")]

import parse_hede as hede  # noqa: E402
from lib.seed_merge import merge_seed  # noqa: E402

_PAGE = """
<TABLE>
<TR><TD><A HREF="norge/nc5h13.htm">N13</A></TD><TD>2 Dukat</TD><TD>Guld</TD>
<TD>1673</TD><TD>Christiania</TD><TD></TD></TR>
<TR><TD><A HREF="norge/nc5h13.htm">N14</A></TD><TD>3 Dukat</TD><TD>Guld</TD>
<TD>1678</TD><TD>Christiania</TD><TD>Som N13.</TD></TR>
<TR><TD>N14A</TD><TD>2 Dukat</TD><TD>Guld</TD>
<TD>1678</TD><TD>Christiania</TD><TD>Som N14</TD></TR>
<TR><TD>N22</TD><TD>Afslag</TD><TD>S&oslash;lv</TD>
<TD>1676</TD><TD>Christiania</TD><TD>S&oslash;lvafslag af p&aring;t&aelig;nkt guldm&oslash;nt?</TD></TR>
<TR><TD>N31AB</TD><TD>3 Speciedaler</TD><TD>S&oslash;lv</TD>
<TD>N31A: 1674<BR>N31B: 1678-1680</TD><TD>Christiania</TD><TD>N31A: FG</TD></TR>
<TR><TD><A HREF="norge/nc5h41.htm">N41A-C</A></TD><TD>1 Krone</TD><TD>S&oslash;lv</TD>
<TD>1670</TD><TD>Christiania</TD><TD></TD></TR>
<TR><TD>N47</TD><TD>1 Skilling</TD><TD>S&oslash;lv</TD>
<TD>1670</TD><TD>Christiania</TD><TD></TD></TR>
<TR><TD><A HREF="8skilybs.htm">175A-C</A></TD><TD>170.1-3</TD><TD>8 Skilling lybsk</TD>
<TD>S&oslash;lv</TD><TD>1641</TD><TD>Gl&uuml;ckstadt</TD><TD></TD></TR>
</TABLE>
"""


class NorgeIndexRows(unittest.TestCase):
    def setUp(self):
        self.stubs = {s["id"]: s for s in hede._extract_index_stubs(_PAGE, "c5hede2")}

    def test_pageless_norge_row_becomes_a_stub(self):
        s = self.stubs["nc5h47"]
        self.assertEqual(s["ruler_volume"], "nc5h")
        self.assertEqual(s["catalog_refs"], {"Hede": ["47"]})
        self.assertEqual((s["nominal"], s["metal_from_index"], s["mint"]),
                         ("1 Skilling", "silver", "Christiania"))
        self.assertEqual([y["year"] for y in s["years"]], [1670])
        self.assertEqual(s["specs"]["default"]["finhed"], None)

    def test_own_norge_page_is_not_stubbed(self):
        self.assertNotIn("nc5h41abc", self.stubs)
        self.assertNotIn("nc5h13", self.stubs)

    def test_per_letter_years_kept(self):
        s = self.stubs["nc5h31ab"]
        self.assertEqual([y["year"] for y in s["years_by_letter"]["B"]], [1678, 1679, 1680])

    def test_letter_range_spelt_out(self):
        s = self.stubs["c5h175abc"]
        self.assertEqual(s["catalog_refs"]["Hede"], ["175ABC"])
        self.assertEqual(s["hede_as_printed"], "175A-C")

    def test_offstrike_flagged(self):
        self.assertEqual(self.stubs["nc5h22"]["_exclude_reason"], "offstrike")
        self.assertIsNone(self.stubs["nc5h47"]["_exclude_reason"])

    def test_letter_beside_its_bare_row_is_separate(self):
        self.assertTrue(self.stubs["nc5h14a"]["_bare_row_printed"])
        self.assertFalse(self.stubs["nc5h31ab"]["_bare_row_printed"])


class TitleOnlyHedeNumber(unittest.TestCase):
    """A Hede number only the <TITLE> carries is dropped — unless it is the
    page's own file number (c4h90: the slip there is in the text)."""

    def test_title_number_absent_from_text_dropped(self):
        html = ("<HTML><HEAD><TITLE>Frederik 3., Hede 15</TITLE></HEAD><BODY>"
                "<H1>Frederik 3.<BR>1/2 Dukat u.&aring;r (ca. 1669), Christiania</H1>"
                "Forside: portr&aelig;t; bagside: norske l&oslash;ve "
                "(Hede Norge 7, Schou 10)</BODY></HTML>")
        out = hede.parse_one(html, "nf3h7")
        self.assertEqual(out["hede_title_ignored"], ["15"])
        self.assertEqual(out.get("hede_numbers_title"), [])
        self.assertNotIn("15", out["catalog_refs"]["Hede"])

    def test_own_file_number_in_title_kept(self):
        html = ("<HTML><HEAD><TITLE>Christian 4., Hede 90</TITLE></HEAD><BODY>"
                "<H1>Christian 4.<BR>1 Hvid 1607, Helsing&oslash;r</H1>"
                "Forside: C, bagside: kors (Hede 86, Schou 11-17, Sieg 16)</BODY></HTML>")
        out = hede.parse_one(html, "c4h90")
        self.assertNotIn("hede_title_ignored", out)
        self.assertEqual(out["hede_numbers_title"], ["90"])


class SeparateNumberNotSuperseding(unittest.TestCase):
    def test_bare_kept_beside_separate_number(self):
        coins = [{"id": "dk-hede-nc5h14", "fuss": "seed_unsorted", "catalog": {"hede": "14"}},
                 {"id": "dk-hede-nc5h14a", "fuss": "seed_unsorted", "catalog": {"hede": "14a"},
                  "_separate_number": True}]
        with tempfile.TemporaryDirectory() as d:
            out, _ = merge_seed(coins, Path(d) / "absent.yml")
        self.assertEqual({c["id"] for c in out}, {"dk-hede-nc5h14", "dk-hede-nc5h14a"})


if __name__ == "__main__":
    unittest.main()
