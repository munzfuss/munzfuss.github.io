"""build_galster_denmark_seed._clean_catalogue_refs — danskmoent cell hygiene.

danskmoent packs cross-refs, prose and rarity notes into one catalogue cell
(comma- or «;»-joined). A real Galster/Sieg/Schive/Schou/J-S index never contains
a comma, a semicolon, or a Danish word. The cleaner:
  * «hhv. X og mangler» → X (two-year row, only year 1 catalogued);
  * foreign cross-refs (Hildebrand/Lagerqvist/Rasmusson/Hauberg/Ernst) → `others`;
  * Danish prose / negative markers («mangler hos», «adskillige katalognumre, se
    side …», «; unik») → dropped;
  * a register left with no real index is removed.

Run via:
    .venv/bin/python -m unittest tests.test_galster_catalogue_clean -v
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
import unittest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

_spec = importlib.util.spec_from_file_location(
    "build_galster_denmark_seed",
    str(PROJECT_ROOT / "scripts" / "maintenance" / "build_galster_denmark_seed.py"),
)
_bg = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_bg)
_clean = _bg._clean_catalogue_refs


def _c(cat):
    _clean(cat)
    return cat


class TestProseDrop(unittest.TestCase):
    def test_mangler_hos_dropped_index_kept(self):
        self.assertEqual(_c({"galster": ["168", "mangler hos"]}), {"galster": "168"})

    def test_adskillige_katalognumre_drops_field(self):
        self.assertEqual(
            _c({"jensen_skjoldager": "adskillige katalognumre, se side 218ff"}), {})

    def test_unik_rarity_note_dropped(self):
        self.assertEqual(_c({"schou": "13; unik"}), {"schou": "13"})
        self.assertEqual(_c({"schou": "3; unik"}), {"schou": "3"})


class TestHhvExtraction(unittest.TestCase):
    def test_hhv_x_og_mangler_keeps_x(self):
        self.assertEqual(_c({"schive": "hhv. XV.5 og mangler"}), {"schive": "XV.5"})
        self.assertEqual(_c({"schou": "hhv. 2 og mangler"}), {"schou": "2"})


class TestForeignReroute(unittest.TestCase):
    def test_ernst_routed_to_others_schive_kept(self):
        self.assertEqual(
            _c({"schive": ["Ernst 1940 21", "XIV.32-33"]}),
            {"schive": "XIV.32-33", "others": ["Ernst 1940 21"]})

    def test_existing_swedish_catalogues_still_route(self):
        self.assertEqual(
            _c({"galster": ["233", "Hildebrand 715", "Lagerqvist 4"]}),
            {"galster": "233", "others": ["Hildebrand 715", "Lagerqvist 4"]})


class TestLegitValuesUntouched(unittest.TestCase):
    def test_bracketed_sieg_yearbook_kept(self):
        self.assertEqual(_c({"sieg": "[2018] 29"}), {"sieg": "[2018] 29"})

    def test_dash_ranges_kept(self):
        self.assertEqual(
            _c({"schou": "187-213", "schive": "XIV.12-25",
                "jensen_skjoldager": "F-51 - F-58"}),
            {"schou": "187-213", "schive": "XIV.12-25",
             "jensen_skjoldager": "F-51 - F-58"})

    def test_plain_index_kept(self):
        self.assertEqual(_c({"galster": "159", "schou": "220"}),
                         {"galster": "159", "schou": "220"})


if __name__ == "__main__":
    unittest.main(verbosity=2)
