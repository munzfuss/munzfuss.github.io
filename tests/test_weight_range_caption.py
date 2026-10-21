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

CAP = {"142": {"galster": "142", "image": "gif/gothans_g142.gif",
               "page": "gotlg142.htm", "weight_min": 0.65,
               "weight_max": 0.80, "approx": False}}


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
        # never turned into specimen readings
        self.assertIsNone(no_w["weight_rough_g"])

    def test_other_number_untouched(self):
        e = {"catalog": {"galster": "141"}, "weight_rough_g": None}
        self.assertEqual(galster.apply_caption_ranges([e], CAP), 0)
        self.assertNotIn("weight_range_g", e)


class DiameterRuleTest(unittest.TestCase):
    def test_only_without_diameter_and_not_vetoed(self):
        caps = {"142": dict(CAP["142"], diameter_mm=15),
                "114": {"galster": "114", "page": "husumdal.htm",
                        "diameter_mm": 38, "diameter_use": False}}
        a = {"catalog": {"galster": "142"}, "diameter_mm": None}
        b = {"catalog": {"galster": "142"}, "diameter_mm": [{"value": 15.5, "source": "x"}]}
        c = {"catalog": {"galster": "114"}, "diameter_mm": None}
        self.assertEqual(galster.apply_caption_diameters([a, b, c], caps), 1)
        self.assertEqual(a["diameter_mm"], [{"value": 15.0, "source": "danskmoent.dk gotlg142.htm"}])
        self.assertEqual(b["diameter_mm"][0]["value"], 15.5)
        self.assertIsNone(c["diameter_mm"])


class AccumulationTest(unittest.TestCase):
    def test_union_dedups_and_keeps_all_sources(self):
        a = {"min": 0.65, "max": 0.8, "approx": False, "source": "A"}
        b = {"min": 0.7, "max": 0.8, "approx": False, "source": "B"}
        out = collect_weight_ranges([{"weight_range_g": [a]},
                                     {"weight_range_g": [a, b]}, {}])
        self.assertEqual([r["source"] for r in out], ["A", "B"])


if __name__ == "__main__":
    unittest.main()
