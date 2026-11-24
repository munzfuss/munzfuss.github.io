"""Krause's own sections of the Schleswig-Holstein houses as KM registers
(curator 2026-11-23): one register per section, named sections that differ
never match, a bare number still meets any section of its group."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "maintenance"))

from lib.km_registers import (  # noqa: E402
    KRAUSE_SECTIONS, display_register, entity_match_scope, match_group)
from lib.v2_resolver import km_for_location  # noqa: E402
import build_ngc_seed as ngc  # noqa: E402
import build_numista_seed as bns  # noqa: E402
import merge_seeds_cross_source as mg  # noqa: E402


class RegisterTables(unittest.TestCase):
    def test_every_section_in_group_sh(self):
        for code in set(KRAUSE_SECTIONS.values()):
            self.assertEqual(match_group(code), "sh", code)
        self.assertEqual(match_group("dk"), "dk")

    def test_entity_scope(self):
        self.assertEqual(entity_match_scope("gottorp_duchy"), "sh")
        self.assertEqual(entity_match_scope("norburg_plon_duchy"), "sh")
        self.assertEqual(entity_match_scope("danish_realm"), "dk")

    def test_display(self):
        self.assertEqual(display_register("ploen"), "PLÖN")
        self.assertEqual(display_register("hgr"), "HGR")


class SectionConflict(unittest.TestCase):
    def c(self, km):
        return {"catalog": {"km": km}}

    def test_named_sections_differ(self):
        # Glückstadt KM 5 Denning 1619 vs Rendsborg KM 5 Skilling 1719
        self.assertIsNotNone(mg._km_section_conflict(self.c({"glu": "5"}), self.c({"hgr": "5"})))

    def test_bare_meets_named(self):
        self.assertIsNone(mg._km_section_conflict(self.c({"glu": "5"}), self.c("5")))

    def test_same_section(self):
        self.assertIsNone(mg._km_section_conflict(self.c({"ploen": "5"}), self.c({"ploen": "5"})))

    def test_cross_listed_coin(self):
        # Hede 120 = Glückstadt KM 73 = S-H KM 105
        self.assertIsNone(mg._km_section_conflict(self.c({"glu": "73", "sh": "105"}),
                                                  self.c({"sh": "105"})))

    def test_no_shared_number(self):
        self.assertIsNone(mg._km_section_conflict(self.c({"glu": "5"}), self.c({"hgr": "6"})))

    def test_dk_is_not_a_section(self):
        self.assertIsNone(mg._km_section_conflict(self.c({"dk": "5"}), self.c({"hgr": "5"})))

    def test_scope_key_is_group(self):
        refs = mg._catalog_refs({"catalog": {"km": {"gott": "199"}}}, "gottorp_duchy", fresh=True)
        self.assertEqual(refs.get("km/sh"), "199")
        refs = mg._catalog_refs({"catalog": {"km": "199"}}, "gottorp_duchy", fresh=True)
        self.assertEqual(refs.get("km/sh"), "199")


class Builders(unittest.TestCase):
    def test_ngc_german_states_section(self):
        cat = ngc._km_volume({"km": "6"}, "german_states",
                             "German States SCHLESWIG-HOLSTEIN-GOTTORP 1/32 Thaler KM# 6")
        self.assertEqual(cat["km"], {"gott": "6"})

    def test_ngc_denmark_rendsborg(self):
        cat = ngc._km_volume({"km": "5"}, "denmark",
                             "Denmark HOLSTEIN-GOTTORP-RENDSBORG Skilling KM# 5")
        self.assertEqual(cat["km"], {"hgr": "5"})

    def test_ngc_unmapped_german_section_bare(self):
        cat = ngc._km_volume({"km": "154"}, "german_states", "German States LÜBECK 2 Schilling KM# 154")
        self.assertEqual(cat["km"], "154")

    def test_numista_gottorp_issuer(self):
        cat = {"km": "155"}
        bns._apply_km_country_register(cat, "gottorp_duchy", "Schleswig-Holstein-Gottorp, Duchy of")
        self.assertEqual(cat["km"], {"gott": "155"})

    def test_numista_norburg_ploen_left_bare(self):
        cat = {"km": "16"}
        bns._apply_km_country_register(cat, "norburg_plon_duchy",
                                       "Schleswig-Holstein-Norburg-Plön, Duchy of")
        self.assertEqual(cat["km"], "16")


class Display(unittest.TestCase):
    def test_gottorp_bare_on_sh_page(self):
        self.assertEqual(km_for_location("199", "SH", "gottorp_duchy"),
                         [{"value": "199", "register": "GOTT", "register_inferred": True}])

    def test_royal_bare_on_sh_page_plain(self):
        self.assertEqual(km_for_location("105", "SH", "royal_holstein"), "105")


if __name__ == "__main__":
    unittest.main()
