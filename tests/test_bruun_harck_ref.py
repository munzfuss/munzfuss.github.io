"""Bruun lots cite Anders Harck's Christian IV catalogue — capture the number.

The Bruun PDFs print a Harck index in the reference chain of Christian IV lots:

    lot 17052   «… Schou-1; Harck-15.1.2; Bruun-5272»
    lot 11201   «… Harck-29.1 …»

`REF_PATTERNS` had no Harck entry, so the number never reached the lot cache or
the seeds. The index is a dotted number of one to three levels, printed with a
hyphen, a hyphen and a space, a hyphen and a line break, or a bare space. The
name also appears WITHOUT an index — the bibliography line «Harck – Anders
Harck. …», the prose «(Harck)» and «recorded by Anders Harck.» — and those
must not yield a value.

Run:
    .venv/bin/python -m unittest tests.test_bruun_harck_ref -v
"""
from __future__ import annotations

import importlib.util
import re
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location(
    "bruun_parse_lots", PROJECT_ROOT / "scripts" / "bruun_parser" / "02_parse_lots.py"
)
_mod = importlib.util.module_from_spec(_spec)
sys.modules["bruun_parse_lots"] = _mod
_spec.loader.exec_module(_mod)

HARCK = _mod.REF_PATTERNS["Harck"]


def harck(text: str) -> str | None:
    # The parser collapses whitespace before matching refs; do the same.
    m = HARCK.search(re.sub(r"\s+", " ", text))
    return m.group(1) if m else None


class TestBruunHarckRef(unittest.TestCase):
    def test_dotted_shapes(self):
        self.assertEqual(harck("Schou-1; Harck-15.1.2; Bruun-5272"), "15.1.2")
        self.assertEqual(harck("Sieg-80.1; Harck-29.1; Bruun-5542"), "29.1")
        self.assertEqual(harck("Harck-4.12.1; Schou-3"), "4.12.1")
        self.assertEqual(harck("Harck-27.16.1; Lange-34"), "27.16.1")
        self.assertEqual(harck("Harck-3; Bruun-5100. Weight"), "3")

    def test_whitespace_after_hyphen(self):
        self.assertEqual(harck("Sieg-119.1; Harck- 6.13.1; Schou-22"), "6.13.1")
        self.assertEqual(harck("Sieg-92.2; Harck-\n32.8.1;Schou-9"), "32.8.1")
        self.assertEqual(harck("Schou-21; Harck 2.2.2; Lange-41"), "2.2.2")

    def test_sentence_final_dot_not_captured(self):
        self.assertEqual(harck("Harck-4.4. Weight 6.79 gms."), "4.4")

    def test_bare_mentions_carry_no_value(self):
        self.assertIsNone(harck("Harck – Anders Harck. Christian IV’s mønter, online catalogue."))
        self.assertIsNone(harck("According to the most recent research (Harck) this is"))
        self.assertIsNone(harck("pieces have been recorded by Anders Harck.\n€8,000-€10,000"))


def ref(key: str, text: str) -> str | None:
    m = _mod.REF_PATTERNS[key].search(re.sub(r"\s+", " ", text))
    return m.group(1) if m else None


class TestBruunBibliographyRefs(unittest.TestCase):
    """The other catalogues of the Bruun bibliography that the parser now reads."""

    def test_value_shapes(self):
        self.assertEqual(ref("Kold", "Schou-1; Kold-145a; Bruun-7090."), "145a")
        self.assertEqual(ref("Poulsen", "Poulsen-SK3.a; Ramus-XXXXI;"), "SK3.a")
        self.assertEqual(ref("Malmer", "Malmer-9.217.1114; Bruun-1315;"), "9.217.1114")
        self.assertEqual(ref("Llt", "Delzanno-4; Llt- 1A:1a; Frösell-8;"), "1A:1a")
        self.assertEqual(ref("LS", "JS-877; LS-2-002; Bruun-16020."), "2-002")
        self.assertEqual(ref("Dav-LS", "KM- 148; Dav-LS533; Hede-64B;"), "533")
        self.assertEqual(ref("Becker", "C. J. Becker-H 46/174; Hildebrand-139"), "H 46/174")
        self.assertEqual(ref("Aagaard & Märcher", "Schou-8; Aagaard & Märcher-72.10; Bruun-4523."), "72.10")

    def test_compound_names_stay_apart(self):
        text = "Hauberg-4; Hauberg Collection-39; Malmer-9.217.1114;"
        self.assertEqual(ref("Hauberg", text), "4")
        self.assertEqual(ref("Hauberg Collection", text), "39")
        self.assertIsNone(ref("Hild", "Hildebrand-139; Bruun-14"))
        self.assertIsNone(ref("SM", "SMH-30; Bruun-11139."))
        self.assertIsNone(ref("Dav", "Dav-LS533; Hede-64B"))

    def test_cf_is_not_this_coins_index(self):
        self.assertIsNone(ref("Hild", "North-781; cf. Hild-20; Bruun-3."))
        self.assertEqual(ref("Hauberg Collection",
                             "Hauberg-7; cf. Hauberg Collection-1318; Bruun-1."), None)
        self.assertIsNone(ref("LS", "Bergsøe-599; cf. LS-2-136;"))

    def test_series_letter_of_another_catalogue_is_not_seaby(self):
        self.assertIsNone(ref("S", "Jensen & Skjoldager-S-01/S-05; Schou-4;"))
        self.assertEqual(ref("S", "type; S-1157; North-781;"), "1157")


class TestBruunHedeShortForm(unittest.TestCase):
    """«H-N» is Hede when the lot prints no «Hede-» (lots 13116, 12060, …)."""

    def h(self, text: str) -> str | None:
        m = _mod.HEDE_SHORT_RE.search(re.sub(r"\s+", " ", text))
        return m.group(1) if m else None

    def test_shapes(self):
        self.assertEqual(self.h("KM-133.1; H-150; Sieg-47.2; Schou-89;"), "150")
        self.assertEqual(self.h("KM-26; H-14B; Sieg-5.3; NMD-124B;"), "14B")

    def test_not_inside_other_tokens(self):
        self.assertIsNone(self.h("C. J. Becker-H 46/174; Hildebrand-139"))
        self.assertIsNone(self.h("Hede-150; Sieg-53"))
        self.assertIsNone(self.h("NGC MS-64. KM-133.1; Sieg-47.2;"))
        self.assertIsNone(self.h("Jensen & Skjoldager-T-22/H-26;"))


if __name__ == "__main__":
    unittest.main()
