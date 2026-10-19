"""A curator no_merge evicts a member that was already absorbed.

2026-10-18: absorb ran without the Schou-ambiguity guard and folded KMM
«1 Krone» records carrying only a Schou number into the Frederik III Krone
final dk-tid-97152. Two of them (1651 Schou 43, 1660 Schou 39) belong to no
Hede type of their year. The curator separated them with no_merges, but
absorb is sticky: a member already in a final's composed_of was never
re-checked against no_merges. `_revalidate_composed_of` now evicts it.
"""
from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "maintenance"))
_spec = importlib.util.spec_from_file_location(
    "absorb_seeds_into_final_v2",
    ROOT / "scripts" / "maintenance" / "absorb_seeds_into_final_v2.py")
AB = importlib.util.module_from_spec(_spec)
sys.modules["absorb_seeds_into_final_v2"] = AB
_spec.loader.exec_module(AB)


def scene(pairs):
    host = {"id": "dk-tid-97152", "nominal": "1 Krone", "catalog": {"hede": "95"},
            "composed_of": ["unified-dk-hede-f3h95ab", "unified-kmk-149286"]}
    unified = {
        "unified-dk-hede-f3h95ab": {"id": "unified-dk-hede-f3h95ab", "nominal": "1 Krone",
                                    "composed_of": ["dk-hede-f3h95ab"]},
        "unified-kmk-149286": {"id": "unified-kmk-149286", "nominal": "1 Krone",
                               "composed_of": ["kmk-149286"]},
    }
    return AB._revalidate_composed_of({host["id"]: host}, unified, "danish_realm",
                                      None, pairs)


class TestNoMergeEvictsAbsorbed(unittest.TestCase):
    def test_evicted(self):
        ev = scene({frozenset({"kmk-149286", "dk-tid-97152"})})
        self.assertEqual(ev, {"dk-tid-97152": {"unified-kmk-149286"}})

    def test_without_no_merge_stays(self):
        self.assertEqual(scene(set()), {})


if __name__ == "__main__":
    unittest.main()
