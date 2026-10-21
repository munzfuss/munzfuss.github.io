"""Catalogue type weight ranges (`Coin.weight_range_g`) from Galster captions.

danskmoent.dk's Galster pages show an illustration GIF whose caption, printed
inside the image and absent from the HTML, gives metal, diameter and a weight
range for the TYPE — «Hvid (G:142) / Ag, 15 mm, 0,65–0,80 gr». The harvest
never read it. Curator decision 2026-10-21: carry it as a separate range
field, never as two readings in `weight_rough_g` (a range printed for a type
is not two weighed specimens), and only for pages whose text gives no weight.

Guards: the schema field and its ordering check; the builder rule «text
weight wins, caption only fills a gap»; the union in merger/absorb that keeps
every source's range (data-accumulation principle).
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "maintenance"))

from pydantic import ValidationError  # noqa: E402

import build_galster_denmark_seed as galster  # noqa: E402
from lib import schema  # noqa: E402
from lib.weight_range import collect_weight_ranges  # noqa: E402

CAP = {"142": [{"galster": "142", "image": "gif/gothans_g142.gif",
                "page": "gotlg142.htm", "metal": "Ag", "weight_min": 0.65,
                "weight_max": 0.80, "approx": False}]}


class SchemaTest(unittest.TestCase):
    def test_range_and_single(self):
        r = schema.WeightRange(min=0.65, max=0.8, source="s")
        self.assertEqual((r.min, r.max, r.approx), (0.65, 0.8, False))
        self.assertIsNone(schema.WeightRange(min=28.9, approx=True, source="s").max)

    def test_inverted_range_rejected(self):
        with self.assertRaises(ValidationError):
            schema.WeightRange(min=2.9, max=2.67, source="s")

    def test_coin_accepts_field(self):
        self.assertIn("weight_range_g", schema.Coin.model_fields)


class BuilderRuleTest(unittest.TestCase):
    def test_fills_only_without_text_weight(self):
        no_w = {"catalog": {"galster": "142"}, "weight_rough_g": None}
        with_w = {"catalog": {"galster": "142"}, "weight_rough_g": 0.7}
        n = galster.apply_caption_ranges([no_w, with_w], CAP)
        self.assertEqual(n, 1)
        self.assertEqual(no_w["weight_range_g"][0]["min"], 0.65)
        self.assertEqual(no_w["weight_range_g"][0]["max"], 0.80)
        self.assertNotIn("weight_range_g", with_w)
        self.assertTrue(no_w["weight_rough_verified"])
        # never turned into specimen readings
        self.assertIsNone(no_w["weight_rough_g"])

    def test_other_number_untouched(self):
        e = {"catalog": {"galster": "141"}, "weight_rough_g": None}
        self.assertEqual(galster.apply_caption_ranges([e], CAP), 0)
        self.assertNotIn("weight_range_g", e)


class MatchingTest(unittest.TestCase):
    """One drawing can carry two coins under one number in two metals
    (G 69 Nobel Au + ½ Sølvgylden Ag); a bare seed number takes a sub-letter
    caption («126» ← «126A»)."""
    def test_metal_picks_caption(self):
        caps = {"69": [{"galster": "69", "image": "i", "page": "p", "metal": "Au", "weight_min": 14.375},
                       {"galster": "69", "image": "i", "page": "p", "metal": "Ag", "weight_min": 14.20}]}
        gold = {"catalog": {"galster": "69"}, "metal": "gold", "weight_rough_g": None}
        galster.apply_caption_ranges([gold], caps)
        self.assertEqual([r["min"] for r in gold["weight_range_g"]], [14.375])

    def test_sub_letter_caption(self):
        caps = {"126A": [{"galster": "126A", "image": "i", "page": "p", "metal": "Ag", "weight_min": 1.12}]}
        e = {"catalog": {"galster": "126"}, "metal": "billon", "weight_rough_g": None}
        self.assertEqual(galster.apply_caption_ranges([e], caps), 1)


class DiameterRuleTest(unittest.TestCase):
    def test_only_without_diameter_and_not_vetoed(self):
        caps = {"142": [dict(CAP["142"][0], diameter_mm=15)],
                "114": [{"galster": "114", "page": "husumdal.htm", "metal": "Ag",
                         "diameter_mm": 38, "diameter_use": False}]}
        a = {"catalog": {"galster": "142"}, "diameter_mm": None}
        b = {"catalog": {"galster": "142"}, "diameter_mm": [{"value": 15.5, "source": "x"}]}
        c = {"catalog": {"galster": "114"}, "diameter_mm": None}
        self.assertEqual(galster.apply_caption_diameters([a, b, c], caps), 1)
        self.assertEqual(a["diameter_mm"], [{"value": 15.0, "source": "danskmoent.dk gotlg142.htm"}])
        self.assertEqual(b["diameter_mm"][0]["value"], 15.5)
        self.assertIsNone(c["diameter_mm"])


class ExpansionTest(unittest.TestCase):
    """Curator 2026-10-21: a range counts as two readings (lower + upper
    bound, the tooltip says which); a single figure as one ordinary one."""
    def test_range_two_readings(self):
        from lib.weight_range import range_pairs, ui_key
        p = range_pairs([{"min": 0.65, "max": 0.8, "source": "S"}])
        self.assertEqual([v for v, _ in p], [0.65, 0.8])
        self.assertIn(ui_key("weight_range.lower"), p[0][1])
        self.assertIn(ui_key("weight_range.upper"), p[1][1])

    def test_single_is_plain(self):
        from lib.weight_range import range_pairs
        self.assertEqual(range_pairs([{"min": 0.8, "max": None, "source": "S"}]), [(0.8, "S")])

    def test_tooltip_resolves_key(self):
        from lib.render import resolve_tips
        from lib.weight_range import range_pairs
        ui = {"weight_range.lower": {"uk": "нижня межа"}, "weight_range.upper": {"uk": "верхня межа"}}
        p = range_pairs([{"min": 0.65, "max": 0.8, "source": "S"}])
        self.assertEqual(resolve_tips([p[0][1]], ui, "uk"), "S (нижня межа)")

    def test_compute_uses_both_bounds(self):
        from lib.compute import normalise_field, range_pairs as rp
        coin = schema.Coin.model_fields  # field exists
        self.assertIn("weight_range_g", coin)
        self.assertEqual(len(normalise_field(None) + rp([{"min": 1, "max": 2, "source": "S"}])), 2)


class AccumulationTest(unittest.TestCase):
    def test_union_dedups_and_keeps_all_sources(self):
        a = {"min": 0.65, "max": 0.8, "approx": False, "source": "A"}
        b = {"min": 0.7, "max": 0.8, "approx": False, "source": "B"}
        out = collect_weight_ranges([{"weight_range_g": [a]},
                                     {"weight_range_g": [a, b]}, {}])
        self.assertEqual([r["source"] for r in out], ["A", "B"])


if __name__ == "__main__":
    unittest.main()
