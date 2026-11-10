"""The KMM builder applies data/v2/entity_routing_rules.yml itself.

Before, the Gottorp / Sonderburg ducal relocations of 66f1eb5 existed only in
the seed data, applied after the seed by audit_entity_misclassifications, so a
plain KMM re-seed sent 147 ducal coins back to the Danish pages. The record
below is the cached KMM 368442 (Johan Adolph, «dobbelt specie/breddaler», no
place, nation «Holsten»): only the ruler rule can send it to the duchy.

The first fixture, KMM 353471 (1 Sechsling, no mint), is dropped by the KMM
stub scope rule since 2026-11-05 (no weight, no image), so `build_entry`
returns None for it; the test ran only where the cache was present and failed
there unseen (2026-11-10).
"""
from __future__ import annotations

import importlib.util
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from lib.paths import HARVEST_ROOT  # noqa: E402
sys.path.insert(0, str(ROOT / "scripts" / "maintenance"))

_spec = importlib.util.spec_from_file_location(
    "build_kmk_seed_for_routing_test", ROOT / "scripts" / "maintenance" / "build_kmk_seed.py")
bk = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(bk)


_SRC = HARVEST_ROOT / "kmk" / "368442.json"


# scripts/cache is a private submodule; CI checks out without it.
@unittest.skipUnless(_SRC.exists(), "kmk cache submodule not present")
class DucalLineageRouting(unittest.TestCase):
    def test_gottorp_ruler_without_mint_routes_to_the_duchy(self):
        src = json.load(open(_SRC))
        e = bk.build_entry(bk._enrich_from_raadata(src))
        self.assertIsNotNone(e, "fixture dropped by a scope rule — pick another")
        self.assertIsNone(e.get("mint"))
        self.assertEqual(e["issuing_entity"], "gottorp_duchy")
        self.assertTrue(e["_entity_routing_hint"]["active"])


if __name__ == "__main__":
    unittest.main()
