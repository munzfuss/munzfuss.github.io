"""The 14th-century town coinages on the Denmark page (Flensborg, Ribe) have
their own issuing entity and show no ruler, even where a source files the
coin under a reign (Galster 1 under Margrethe I) — curator 2026-11-03."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "maintenance"))

from lib.v2_entity_classify import classify_mint_to_entity  # noqa: E402
import merge_seeds_cross_source as M  # noqa: E402


class Routing(unittest.TestCase):
    def test_ribe_before_1397_is_the_town(self):
        self.assertEqual(classify_mint_to_entity("Ribe", year=1380), "ribe_medieval")
        self.assertEqual(classify_mint_to_entity("Ribe", year=1397), "danish_realm")
        self.assertEqual(classify_mint_to_entity("Ribe", year=1500), "danish_realm")


class Ruler(unittest.TestCase):
    def test_town_class_names_no_ruler(self):
        out = {"ruler": "Margrethe I", "ruler_verified": False}
        M._canonical_ruler_out(out, [{"ruler": "Margrethe I"}], "ribe_medieval")
        self.assertNotIn("ruler", out)
        self.assertNotIn("ruler_verified", out)

    def test_crown_class_keeps_its_ruler(self):
        out = {"ruler": "Margrethe I"}
        M._canonical_ruler_out(out, [{"ruler": "Margrethe I"}], "danish_realm")
        self.assertTrue(out.get("ruler"))


class Nominal(unittest.TestCase):
    def test_viertelwitten_is_one_penning_on_the_denmark_page(self):
        from lib.nominal_synonyms import danish_display_nominal
        self.assertEqual(danish_display_nominal("1 Viertelwitten", "flensborg_medieval"),
                         "1 Penning")
        self.assertEqual(danish_display_nominal("1 Witten", "flensborg_medieval"), "1 Hvid")
        self.assertEqual(danish_display_nominal("1 Viertelwitten", "hanseatic_lubeck"),
                         "1 Viertelwitten")


if __name__ == "__main__":
    unittest.main()
