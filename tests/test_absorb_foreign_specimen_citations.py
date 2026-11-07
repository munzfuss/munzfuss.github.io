"""Absorb's foreign-specimen-citation prune covers IKMK as well as KMM
(curator 2026-11-07): a citation names the specimen's seed by object number."""
from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "maintenance"))
_spec = importlib.util.spec_from_file_location(
    "absorb_for_specimen_test", ROOT / "scripts" / "maintenance" / "absorb_seeds_into_final_v2.py")
AB = importlib.util.module_from_spec(_spec)
sys.modules["absorb_for_specimen_test"] = AB
_spec.loader.exec_module(AB)


class SpecimenSeed(unittest.TestCase):
    def test_kmm_and_ikmk(self):
        self.assertEqual(AB._specimen_seed_of({"url": "https://samlinger.natmus.dk/KMM/object/150153"}),
                         "kmk-150153")
        self.assertEqual(AB._specimen_seed_of({"url": "https://ikmk.smb.museum/object?id=18306115"}),
                         "ikmk-18306115")
        self.assertEqual(AB._specimen_seed_of({"url": "https://ikmk.smb.museum/object?lang=en&id=18200855"}),
                         "ikmk-18200855")
        self.assertIsNone(AB._specimen_seed_of({"url": "https://en.numista.com/114189"}))


if __name__ == "__main__":
    unittest.main()
