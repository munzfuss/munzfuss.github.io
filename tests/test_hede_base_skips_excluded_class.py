"""The Hede-base rule leaves out a class that holds ANY curator-excluded seed.

A plain exclusion removes the whole class its seed sits in (absorb
`_coin_exclusion_hit`). A class with one excluded Bruun record and an NGC
record of the same gold off-strike is therefore already gone from final; the
rule must not report it as a refused group, and must never join it to the
silver mother coin's class, which absorb would then drop with it
(curator 2026-11-10).
"""
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "maintenance"))
import merge_seeds_cross_source as m  # noqa: E402


def seed(sid, nominal, metal, hede):
    return {"id": sid, "nominal": nominal, "metal": metal,
            "ruler": "Frederik III", "catalog": {"hede": hede}}


SEEDS = {
    "silver-a": seed("silver-a", "1 Krone", "silver", "98"),
    "silver-b": seed("silver-b", "1 Krone", "silver", "98"),
    "gold-bruun": seed("gold-bruun", "1/2 Portugaløser", "gold", "98"),
    "gold-ngc": seed("gold-ngc", "1/2 Portugaløser", "gold", None),
}


def build(excluded):
    uf = m.UnionFind()
    for s in SEEDS:
        uf.add(s) if hasattr(uf, "add") else uf.find(s)
    uf.union("gold-bruun", "gold-ngc")
    with mock.patch.object(m, "_all_excluded_seed_ids", lambda: frozenset(excluded)):
        groups, info = m._hede_base_groups(uf, SEEDS, "danish_realm")
    return uf, groups, info


class ExcludedClassLeftOut(unittest.TestCase):
    def test_class_with_one_excluded_member_is_no_group_member(self):
        uf, groups, info = build({"gold-bruun"})
        gold_root = uf.find("gold-bruun")
        self.assertNotIn(gold_root, info)
        self.assertFalse(any(gold_root in g for g in groups))

    def test_silver_classes_still_grouped(self):
        uf, groups, _ = build({"gold-bruun"})
        roots = {uf.find("silver-a"), uf.find("silver-b")}
        self.assertTrue(any(roots <= set(g) for g in groups))

    def test_without_exclusion_gold_class_takes_part(self):
        uf, _, info = build(set())
        self.assertIn(uf.find("gold-bruun"), info)


if __name__ == "__main__":
    unittest.main()
