"""Bruun mint (2026-11-07): the parser reads the cataloguer's «<X> Mint» at its
fixed place in the meta line, with no town list; the seed builder takes that
field. The builder's own town search had found «Gottorp» inside the territory
«Schleswig-Holstein-Gottorp» on 49 lots struck elsewhere (Tönning, Schleswig,
Steinbeck, Eutin, Stade, Mannheim, Bremervörde) and kept only the first town
of «Malmö or Copenhagen».
"""
from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "maintenance"))


def _load(name, rel):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


PL = _load("bruun_parse_lots_t", "scripts/bruun_parser/02_parse_lots.py")
BB = _load("bruun_seed_builder_t", "scripts/maintenance/build_bruun_denmark_seed.py")


def meta_mint(t):
    m = PL.META_MINT_RE.search(t)
    return m.group(1) if m else None


class ParserMint(unittest.TestCase):
    def test_any_town_before_mint(self):
        self.assertEqual(meta_mint("GERMANY . Schleswig-Holstein-Gottorp. Ducat, 1705-BH. "
                                   "Tönning Mint. Karl Friedrich."), "Tönning")

    def test_bracketed_other_form_and_joint_and_misprint(self):
        self.assertEqual(meta_mint("NORW AY . Skilling, ND. Nidaros (Trondheim) Mint. Olav"),
                         "Nidaros (Trondheim)")
        self.assertEqual(meta_mint("SWEDEN. 1/4 Riksdaler, 1641/0. Stockholm & Sala Mint. Kristina"),
                         "Stockholm & Sala")
        self.assertEqual(meta_mint("DENMARK. 8 Skilling (?), 1565. Visby MInt. Frederik II."), "Visby")

    def test_bare_segment_only_a_whole_registered_segment_after_the_year(self):
        self.assertEqual(PL.bare_segment_mint("DENMARK. Skilling, 1525. Landskrona. Christian II."),
                         "Landskrona")
        self.assertIsNone(PL.bare_segment_mint(
            "GERMANY . Schleswig-Holstein-Gottorp. Ducat, 1664. Christian Albrecht."))
        self.assertIsNone(PL.bare_segment_mint("SWEDEN. Peace in Lund Restrike Silver Medal, ND (1679)."))


class BuilderMint(unittest.TestCase):
    def pm(self, mint):
        return BB.parse_mint({"mint": mint, "meta_line": "GERMANY . Schleswig-Holstein-Gottorp. X"})

    def test_takes_parser_field_not_the_territory(self):
        self.assertEqual(self.pm("Tönning Mint"), "Tönning")
        self.assertIsNone(self.pm(None))

    def test_bracketed_form_picks_registered_name(self):
        self.assertEqual(self.pm("Nidaros (Trondheim) Mint"), "Nidaros")
        self.assertEqual(self.pm("Nidarnes (Trondheim) Mint"), "Trondheim")

    def test_joint_is_a_list_alternatives_stay_verbatim(self):
        self.assertEqual(self.pm("Stockholm & Sala Mint"), ["Stockholm", "Sala"])
        self.assertEqual(self.pm("Malmö or Copenhagen Mint"), "Malmö or Copenhagen")
        self.assertEqual(self.pm("Altona / Poppenbüttel Mint"), "Altona / Poppenbüttel")


if __name__ == "__main__":
    unittest.main()

