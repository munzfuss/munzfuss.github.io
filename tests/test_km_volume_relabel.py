"""A KM number whose Krause volume changes upstream leaves its old volume.

Two layers kept the old volume beside the new one (2026-11-22):

* the seed — `merge_seed` unioned an existing `{dk: '26'}` with a fresh
  `{sh: '26'}` into `[{dk: '26'}, {sh: '26'}]`, read as two volumes;
* the final — its self-union kept `sh: [696 …]` on the Rigsbankdaler 1826
  while every member gives the same numbers under `dk`.

A number no member gives at all stays on the final (its removal is a curator
decision, recorded in `_recorded_removals.yml`), and so does a number a
member gives without a resolvable volume.
"""
from __future__ import annotations

import contextlib
import io
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "maintenance"))

from lib.seed_merge import _km_bare_superseded  # noqa: E402

with contextlib.redirect_stdout(io.StringIO()):
    from maintenance import absorb_seeds_into_final_v2 as ab  # noqa: E402


class TestSeedKmSuperseded(unittest.TestCase):
    def test_bare_replaced_by_volume(self):
        self.assertTrue(_km_bare_superseded(["603", "603.1"], {"dk": ["603", "603.1"]}))

    def test_other_volume_replaced(self):
        self.assertTrue(_km_bare_superseded({"dk": "26"}, {"sh": "26"}))

    def test_mixed_list_replaced(self):
        self.assertTrue(_km_bare_superseded([{"dk": "26"}, "26.1"], {"sh": ["26", "26.1"]}))

    def test_number_not_covered_keeps_union(self):
        self.assertFalse(_km_bare_superseded({"dk": ["26", "27"]}, {"sh": "26"}))

    def test_fresh_bare_replaces_dropped_volume(self):
        # NGC HOLSTEIN-GOTTORP-RENDSBORG: {dk: '5'} -> bare '5', not [{dk}, '5']
        self.assertTrue(_km_bare_superseded({"dk": "5"}, "5"))

    def test_bare_over_bare_keeps_union(self):
        self.assertFalse(_km_bare_superseded("5", ["5", "6"]))

    def test_fresh_bare_not_covering_keeps_union(self):
        self.assertFalse(_km_bare_superseded({"dk": ["5", "6"]}, "5"))


def _final(km, holds=None):
    f = {"id": "f", "catalog": {"km": km}}
    if holds:
        f["_curation_holds"] = holds
    return f


def _member(km, entity="royal_holstein"):
    return {"id": "u", "issuing_entity": entity, "catalog": {"km": km}}


class TestFinalRelabel(unittest.TestCase):
    def km_after(self, members, entity="royal_holstein"):
        out = ab._drop_relabelled_km(members, entity)
        return (out[0].get("catalog") or {}).get("km")

    def test_stale_volume_dropped(self):
        km = self.km_after([_final({"sh": ["696", "706"], "dk": ["696", "706"]}),
                            _member({"dk": ["696", "706"]})])
        self.assertEqual(km, {"dk": ["696", "706"]})

    def test_bare_member_reads_entity_volume(self):
        # members give 77/83 bare in royal_holstein = sh, so dk goes
        km = self.km_after([_final({"dk": ["77", "83"], "sh": ["77", "83", "108"]}),
                            _member(["77", "83", "108"])])
        self.assertEqual(km, {"sh": ["77", "83", "108"]})

    def test_orphan_number_kept(self):
        km = self.km_after([_final({"dk": "607", "sh": "608"}),
                            _member({"dk": "607"}, "danish_realm")])
        self.assertEqual(km, {"dk": "607", "sh": "608"})

    def test_unresolvable_member_volume_keeps(self):
        km = self.km_after([_final({"dk": "5", "sh": "5"}),
                            _member("5", ["danish_realm", "royal_holstein"])])
        self.assertEqual(km, {"dk": "5", "sh": "5"})

    def test_hold_wins(self):
        km = self.km_after([_final({"dk": "73", "sh": "105"}, {"catalog.km": "why"}),
                            _member({"sh": ["73", "105"]})])
        self.assertEqual(km, {"dk": "73", "sh": "105"})

    def test_stored_final_not_mutated(self):
        f = _final({"sh": "1", "dk": "1"})
        ab._drop_relabelled_km([f, _member({"dk": "1"})], "royal_holstein")
        self.assertEqual(f["catalog"]["km"], {"sh": "1", "dk": "1"})


if __name__ == "__main__":
    unittest.main()
