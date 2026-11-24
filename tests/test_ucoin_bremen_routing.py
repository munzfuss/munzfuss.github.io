"""ucoin's `bremen-` URL holds the city and the archbishopric; the `period`
series tells them apart (`build_ucoin_seed._resolve_target_entity`, 2026-11-24)."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "maintenance"))
import build_ucoin_seed as bus  # noqa: E402
from lib.km_registers import ENTITY_TO_KM_REGISTER  # noqa: E402

URL = "https://en.ucoin.net/coin/bremen-1-grote-1623-1627/?tid=101125"


def _ent(period):
    return bus._resolve_target_entity({"url": URL, "period": period, "min_year": 1623})


class TestBremenRouting(unittest.TestCase):
    def test_city_series_go_to_the_city(self):
        self.assertEqual(_ent("Free Imperial City of Bremen (1541 - 1810)"), "hanseatic_bremen")
        self.assertEqual(_ent("Free Hanseatic City of Bremen (1813 - 1871)"), "hanseatic_bremen")

    def test_archbishopric_stays(self):
        self.assertEqual(_ent("Archbishopric of Bremen (1350 - 1648)"), "erzbisthum_bremen_verden")

    def test_city_has_its_own_km_register(self):
        self.assertEqual(ENTITY_TO_KM_REGISTER["hanseatic_bremen"], "de-hb")
        self.assertIn("hanseatic_bremen", bus.ENTITY_WINDOW)


if __name__ == "__main__":
    unittest.main()
