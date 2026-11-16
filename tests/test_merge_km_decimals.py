"""Two decimals of one Krause number are one coin unless Hede or Galster
separates them.

6aad28c kept every pair of Krause decimals apart («172.1» against «172.2»),
because in the Danish volumes they can be different Hede types (KM 32.1 =
Hede 91, KM 32.4 = Hede 96). That split coins nothing separates: the
Osnabrück 1/14 Thaler KM 172.1 / 172.2 (curator 2026-11-16, review P31:
«правило не повинно бути абсолютним»). Now decimals agree in a Krause volume
Hede does not cover; in the dk / nor / sh volumes only when both records
carry a Hede or Galster number of the same base, because a record without one
cannot show which Hede type its decimal is. Other registers (Friedberg, Dav)
keep their old reading: allowing Fr 64.1 = 64.2 moved a Portugaløser from
Hede 7 to Hede 3 in the first measurement.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "maintenance"))

import merge_seeds_cross_source as M  # noqa: E402


def state(a, b):
    return M._catalog_chain_consistent(a, b)[0]


class KmDecimals(unittest.TestCase):
    def test_german_volume_decimals_agree(self):
        self.assertEqual(state({"km/de-osnabr": "172.1"}, {"km/de-osnabr": "172.2"}), "agree")

    def test_danish_volume_without_hede_stays_apart(self):
        self.assertEqual(state({"km/dk": "32.1"}, {"km/dk": "32.4"}), "disagree")

    def test_danish_volume_same_hede_base_agrees(self):
        self.assertEqual(state({"km/nor": "179.1", "hede/nc5h": "74"},
                               {"km/nor": "179.2", "hede/nc5h": "74"}), "agree")

    def test_different_hede_bases_stay_apart(self):
        self.assertEqual(state({"km/dk": "32.1", "hede/c4h": "91"},
                               {"km/dk": "32.4", "hede/c4h": "96"}), "disagree")

    def test_friedberg_decimals_unchanged(self):
        self.assertEqual(state({"fr": "64.1"}, {"fr": "64.2"}), "disagree")


if __name__ == "__main__":
    unittest.main()
