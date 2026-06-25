"""§9.1 / §9.3 exclusion of pattern + off-metal strikes in the Numista builder.

CLAUDE.md §9 excludes pattern strikes (§9.1) and off-metal / off-strikes (§9.3)
from the coin table — they were never struck for circulation. build_hede_denmark_seed
filters these structurally; the Numista builder had no such filter, so a Bremen
«½ Groten (Gold pattern strike)» (KM# Pn 30) and a Frederik IV «16 Skilling
(Gold, 2 ducat equivalent)» off-metal strike (KM# 505 (OM), gold off-strike of the
silver KM#505) slipped into the seed (caught 2026-06-25). The filter keys on the
Krause marker on the KM ref («Pn N» / «N (OM)») and the Numista title.

Run via:
    .venv/bin/python -m unittest tests.test_numista_strike_exclusion -v
"""
from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

_spec = importlib.util.spec_from_file_location(
    "build_numista_seed",
    str(PROJECT_ROOT / "scripts" / "maintenance" / "build_numista_seed.py"),
)
_bns = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_bns)
_reason = _bns._excluded_strike_reason


class TestPatternExclusion(unittest.TestCase):
    def test_km_pn_marker(self):
        r = _reason("½ Groten (Gold pattern strike) - City of Bremen", {"km": "Pn 30"})
        self.assertTrue(r and r.startswith("§9.1"))

    def test_km_pn_no_space(self):
        r = _reason("1 Schwaren - City of Bremen", {"km": "Pn19"})
        self.assertTrue(r and r.startswith("§9.1"))

    def test_title_pattern_strike(self):
        r = _reason("1 Thaler - William (Pattern) - Duchy of Brunswick", {"km": "X1"})
        self.assertTrue(r and r.startswith("§9.1"))


class TestOffMetalExclusion(unittest.TestCase):
    def test_km_om_marker(self):
        r = _reason("16 Skilling (Gold, 2 ducat equivalent) Dansk - Frederik IV",
                    {"km": "505 (OM)"})
        self.assertTrue(r and r.startswith("§9.3"))

    def test_title_off_metal(self):
        r = _reason("1 Daler off-metal strike", {"km": "12"})
        self.assertTrue(r and r.startswith("§9.3"))

    def test_title_afslag(self):
        r = _reason("2 Speciedaler Guldafslag", {"km": "240"})
        self.assertTrue(r and r.startswith("§9.3"))


class TestCirculationKept(unittest.TestCase):
    """A normal circulation coin (incl. the silver KM#505 mother) is NOT excluded."""

    def test_silver_mother_kept(self):
        self.assertIsNone(_reason("16 Skilling - Frederik IV", {"km": "505"}))

    def test_plain_km_kept(self):
        self.assertIsNone(_reason("1 Speciedaler - Frederik VI", {"km": "505"}))

    def test_no_refs_kept(self):
        self.assertIsNone(_reason("4 Skilling - Christian VII", {}))

    def test_register_dict_km_om_excluded(self):
        # km may be a register-keyed dict by the time it is checked
        r = _reason("16 Skilling Dansk", {"km": {"dk": "505 (OM)"}})
        self.assertTrue(r and r.startswith("§9.3"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
