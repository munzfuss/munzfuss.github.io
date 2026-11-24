"""Krause's HOLSTEIN-GOTTORP-RENDSBORG section is Frederik IV's coinage at
Rendsburg 1716-1720 (Hede 60-63): NGC and NumisMaster records of it route to
royal_holstein (curator ruling 2026-07-29, routing fixed 2026-11-24)."""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "maintenance"))

import build_ngc_seed as ngc  # noqa: E402
import build_numismaster_seed as nm  # noqa: E402
from lib.paths import NGC_CACHE, NUMISMASTER_CACHE  # noqa: E402


class Tables(unittest.TestCase):
    def test_ngc_subsection(self):
        sub = ngc._subsection("Denmark HOLSTEIN-GOTTORP-RENDSBORG Skilling KM# 5")
        self.assertEqual(ngc._ENTITY_BY_SUBSECTION.get(sub), "royal_holstein")

    def test_ngc_german_states_not_routed(self):
        sub = ngc._subsection("German States SCHLESWIG-HOLSTEIN-GOTTORP 1/32 Thaler KM# 6")
        self.assertIsNone(ngc._ENTITY_BY_SUBSECTION.get(sub))

    def test_numismaster_country(self):
        self.assertEqual(nm.COUNTRY_TO_ISSUING_ENTITY["HOLSTEIN-GOTTORP-RENDSBORG"],
                         "royal_holstein")


class CachedRecords(unittest.TestCase):
    def test_ngc_1051156(self):
        p = NGC_CACHE / "denmark" / "cuid_1051156.parsed.json"
        if not p.exists():
            self.skipTest("harvest cache not available")
        e = ngc.build_entry(json.loads(p.read_text(encoding="utf-8")), "denmark")
        self.assertEqual(e["issuing_entity"], "royal_holstein")
        self.assertEqual(e["catalog"]["km"], {"hgr": "5"})

    def test_numismaster_66636(self):
        p = NUMISMASTER_CACHE / "schleswig_holstein" / "MC_66636.parsed.json"
        if not p.exists():
            self.skipTest("harvest cache not available")
        e = nm.build_entry(json.loads(p.read_text(encoding="utf-8")),
                           "schleswig_holstein", 1500, 1914)
        self.assertEqual(e["issuing_entity"], "royal_holstein")


if __name__ == "__main__":
    unittest.main()
