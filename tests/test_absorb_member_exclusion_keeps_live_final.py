"""A `scope: member` exclusion removes ONE record, never a final with live members.

A final's id is the class it was first built from. When the merger isolates an
excluded record and that record keeps the old class id, the final still carries
the id while composing other, live classes. `_coin_exclusion_hit` matched the
final's own id against the member exclusion and dropped the whole final — 146
non-stub seeds (Hede Norge 67, Hede f3h133, Galster 37 …) lost their final in a
trial run of the 2026-11-05 KMM stub exclusions.

Pinned: own id excluded + a live member → no hit; own id excluded and nothing
else → hit; a plain (whole-coin) exclusion on a member still hits.
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
    "absorb_for_member_excl_test", ROOT / "scripts" / "maintenance" / "absorb_seeds_into_final_v2.py")
ab = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ab)


class MemberExclusion(unittest.TestCase):
    def setUp(self):
        self._orig = ab._seed_of
        ab._seed_of = lambda uid: {"c-own": "kmk-1", "c-live": "dk-hede-x"}.get(uid, uid)

    def tearDown(self):
        ab._seed_of = self._orig

    def test_live_member_keeps_final(self):
        entry = {"id": "c-own", "composed_of": ["c-own", "c-live"]}
        self.assertEqual(ab._coin_exclusion_hit(entry, {"kmk-1"}, {"kmk-1"}), set())

    def test_only_the_excluded_record_drops(self):
        entry = {"id": "c-own", "composed_of": ["c-own"]}
        self.assertEqual(ab._coin_exclusion_hit(entry, {"kmk-1"}, {"kmk-1"}), {"kmk-1"})

    def test_plain_exclusion_still_drops_the_coin(self):
        entry = {"id": "c-live", "composed_of": ["c-own", "c-live"]}
        self.assertEqual(ab._coin_exclusion_hit(entry, {"kmk-1"}, set()), {"kmk-1"})


if __name__ == "__main__":
    unittest.main()
