"""UnionFind keeps a per-id index of no_merges (2026-10-24, speed). The
cross-class check must refuse exactly the unions the old member×member scan
refused and report the SAME first conflicting pair; force_union must clear
the same auto no_merges. Compared against a brute-force reference on random
operation sequences.

    .venv/bin/python -m unittest tests.test_unionfind_index -v
"""
from __future__ import annotations

import random
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts" / "maintenance"))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from merge_seeds_cross_source import UnionFind  # noqa: E402


class Reference(UnionFind):
    """The pre-index algorithm: scan every member pair."""

    def union(self, x, y):
        rx, ry = self.find(x), self.find(y)
        if rx == ry:
            return (False, None)
        if x in self.isolated or y in self.isolated:
            return (False, frozenset({x, y}))
        if not self.can_union(x, y):
            return (False, frozenset({x, y}))
        if self.no_merge:
            for mx in self._class_members(rx):
                for my in self._class_members(ry):
                    if frozenset({mx, my}) in self.no_merge:
                        return (False, frozenset({mx, my}))
        self._link(rx, ry)
        return (True, None)

    def force_union(self, x, y):
        rx, ry = self.find(x), self.find(y)
        if rx == ry:
            return (True, None)
        if x in self.isolated or y in self.isolated:
            return (False, frozenset({x, y}))
        mx_, my_ = list(self._class_members(rx)), list(self._class_members(ry))
        for mx in mx_:
            for my in my_:
                if frozenset({mx, my}) in self.explicit_no_merge:
                    return (False, frozenset({mx, my}))
        for mx in mx_:
            for my in my_:
                self.no_merge.discard(frozenset({mx, my}))
        self._link(rx, ry)
        return (True, None)


class Equivalence(unittest.TestCase):
    def test_random_sequences(self):
        for seed in range(200):
            rnd = random.Random(seed)
            ids = [f"s{i}" for i in range(rnd.randint(5, 40))]
            new, ref = UnionFind(), Reference()
            for _ in range(rnd.randint(10, 120)):
                op = rnd.random()
                a, b = rnd.sample(ids, 2)
                if op < 0.3:
                    ex = rnd.random() < 0.3
                    new.add_no_merge(a, b, explicit=ex)
                    ref.add_no_merge(a, b, explicit=ex)
                elif op < 0.9:
                    self.assertEqual(new.union(a, b), ref.union(a, b), seed)
                else:
                    self.assertEqual(new.force_union(a, b), ref.force_union(a, b), seed)
                self.assertEqual(new.no_merge, ref.no_merge, seed)
            self.assertEqual({k: sorted(v) for k, v in new.classes().items()},
                             {k: sorted(v) for k, v in ref.classes().items()}, seed)


if __name__ == "__main__":
    unittest.main()
