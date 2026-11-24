"""ucoin `period` names the Krause section of a bare KM on an S-H-group coin
(`build_ucoin_seed._apply_km_period_register`, 2026-11-24)."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "maintenance"))
import build_ucoin_seed as bus  # noqa: E402


def _apply(km, issuing, period, url="https://en.ucoin.net/coin/denmark-4-skilling-1807/?tid=79557"):
    cat = {"km": km}
    bus._apply_km_period_register(cat, issuing, {"period": period, "url": url})
    return cat["km"]


class TestUcoinPeriodRegister(unittest.TestCase):
    def test_denmark_era_on_royal_holstein_is_dk(self):
        # tid 79557: 4 Skilling 1807 Altona, KM 661 = Denmark KM 661 (MC_65105)
        self.assertEqual(_apply("661", "royal_holstein", "Rigsdaler (1750 - 1812)"), {"dk": "661"})
        self.assertEqual(_apply("689", "royal_holstein", "Rigsbankdaler (1813 - 1854)"), {"dk": "689"})

    def test_territorial_series(self):
        self.assertEqual(_apply("8", "royal_holstein", "Glückstadt (1617 - 1773)"), {"glu": "8"})
        self.assertEqual(_apply("6", "royal_holstein", "Holstein-Gottorp-Rendsburg (1716 - 1720)"),
                         {"hgr": "6"})
        self.assertEqual(_apply("116", "royal_holstein", "Duchy of Schleswig-Holstein (1787 - 1839)",
                                url="https://en.ucoin.net/coin/schleswig_holstein-1-dreiling-1787/?tid=90498"),
                         {"sh": "116"})

    def test_era_needs_denmark_url(self):
        self.assertEqual(_apply("150", "royal_holstein", "Speciedaler",
                                url="https://en.ucoin.net/coin/norway-2-mark-1685/?tid=1"), "150")

    def test_other_entity_unchanged(self):
        self.assertEqual(_apply("661", "danish_realm", "Rigsdaler (1750 - 1812)"), "661")
        self.assertEqual(_apply("8", "danish_realm", "Glückstadt (1617 - 1773)"), "8")

    def test_joint_list_with_sh_entity(self):
        self.assertEqual(_apply("663", ["danish_realm", "royal_holstein"], "Rigsdaler (1750 - 1812)"),
                         {"dk": "663"})

    def test_unknown_series_and_shapes_unchanged(self):
        self.assertEqual(_apply("661", "royal_holstein", ""), "661")
        self.assertEqual(_apply(["640", "640.1"], "royal_holstein", "Rigsdaler"), ["640", "640.1"])
        self.assertEqual(_apply({"dk": "661"}, "royal_holstein", "Rigsdaler"), {"dk": "661"})


if __name__ == "__main__":
    unittest.main()
