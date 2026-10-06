"""The KMM builder applies data/v2/entity_routing_rules.yml itself.

Before, the Gottorp / Sonderburg ducal relocations of 66f1eb5 existed only in
the seed data, applied after the seed by audit_entity_misclassifications, so a
plain KMM re-seed sent 147 ducal coins back to the Danish pages. The record
below is verbatim from scripts/cache/kmk/353471.json (Johan Adolph, 1 Sechsling,
no mint).
"""
from __future__ import annotations

import importlib.util
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "maintenance"))

_spec = importlib.util.spec_from_file_location(
    "build_kmk_seed_for_routing_test", ROOT / "scripts" / "maintenance" / "build_kmk_seed.py")
bk = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(bk)


class DucalLineageRouting(unittest.TestCase):
    def test_gottorp_ruler_without_mint_routes_to_the_duchy(self):
        src = json.load(open(ROOT / "scripts" / "cache" / "kmk" / "353471.json"))
        e = bk.build_entry(bk._enrich_from_raadata(src))
        self.assertEqual(e["issuing_entity"], "gottorp_duchy")
        self.assertTrue(e["_entity_routing_hint"]["active"])


if __name__ == "__main__":
    unittest.main()
