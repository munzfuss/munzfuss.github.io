"""Regression: a reading whose `specimen` tag went away is not a re-flow loss
when the final that holds the seed now shows the same source and value.

The merger tags a reading with its seed (`specimen: <seed>`) only when one
source gives a class several readings. Split a class so that each source gives
one reading (Hede 93 / Hede 96, 2026-11-09) and the tags vanish — on the coin
the seed left for, and on the coin it stayed in. `verify_reflow` keys readings
on the whole entry, so it read both as «LIST SHRANK» and blocked the commit.

The tests pin the narrowness: a seed in no final, a changed value, another
source and a reading gone from the seed's own final all still block.
"""
from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

_spec = importlib.util.spec_from_file_location(
    "verify_reflow", str(ROOT / "scripts" / "maintenance" / "verify_reflow.py"))
VR = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(VR)


def coin(cid, members, **over):
    base = {"id": cid, "nominal": "8 Skilling", "year_label": "1608",
            "metal": "silver", "fuss": "9_thaler", "phase": "I",
            "composed_of": list(members),
            "sources": [{"type": "literature", "url": f"https://example/{cid}", "ref": "X"}]}
    base.update(over)
    return base


def w(source, value, specimen=None):
    e = {"source": source, "value": value}
    if specimen:
        e["specimen"] = specimen
    return e


class TestSpecimenTag(unittest.TestCase):
    def setUp(self):
        VR._SEED_CLASS = {}          # no live seed_unified lookup in these tests

    def _losses(self, head, cur):
        r = VR.compare_coins("test_entity", {c["id"]: c for c in head},
                             {c["id"]: c for c in cur})
        return [x for x in r["losses"] if "weight_rough_g" in x]

    HEAD = [coin("a", ["s1", "s2"], weight_rough_g=[w("numista", 2.923, "s1"),
                                                   w("numista", 2.9, "s2")]),
            coin("b", ["s9"], weight_rough_g=[w("hede", 2.923)])]

    def test_moved_and_stayed_readings_are_not_losses(self):
        cur = [coin("a", ["s2"], weight_rough_g=[w("numista", 2.9)]),
               coin("b", ["s9", "s1"], weight_rough_g=[w("hede", 2.923), w("numista", 2.923)])]
        self.assertEqual(self._losses(self.HEAD, cur), [])

    def test_seed_still_here_but_reading_gone_blocks(self):
        cur = [coin("a", ["s1", "s2"], weight_rough_g=[w("numista", 2.9)]),
               self.HEAD[1]]
        self.assertTrue(self._losses(self.HEAD, cur))

    def test_value_changed_on_the_way_blocks(self):
        cur = [coin("a", ["s2"], weight_rough_g=[w("numista", 2.9)]),
               coin("b", ["s9", "s1"], weight_rough_g=[w("hede", 2.923), w("numista", 2.92)])]
        self.assertTrue(self._losses(self.HEAD, cur))

    def test_only_another_source_on_the_target_blocks(self):
        cur = [coin("a", ["s2"], weight_rough_g=[w("numista", 2.9)]),
               coin("b", ["s9", "s1"], weight_rough_g=[w("hede", 2.923)])]
        self.assertTrue(self._losses(self.HEAD, cur))

    def test_seed_in_no_final_blocks(self):
        cur = [coin("a", ["s2"], weight_rough_g=[w("numista", 2.9)]),
               self.HEAD[1]]
        self.assertTrue(self._losses(self.HEAD, cur))

    def test_untagged_reading_keeps_the_old_strict_behaviour(self):
        head = [coin("a", ["s1"], weight_rough_g=[w("numista", 2.923)])]
        cur = [coin("a", ["s1"], weight_rough_g=[])]
        self.assertTrue(self._losses(head, cur))


if __name__ == "__main__":
    unittest.main()
