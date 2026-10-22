"""A class id that renamed with its composition lost every consumer keyed on it.

`unified-<top-authority member>` changes when a higher-authority member joins,
a §9a fold is re-cut or the class splits (D49: 238 of 498 classification
decisions dead, ~400 lines of rename hand-over in absorb). The registry's
`inherit` recognises the merger's fresh partition as the classes it knows, by
specimen overlap — these tests pin the recognition rule on a synthetic tree:
single candidate, merge (larger wins, tie → older), split, relocation across
two shards, a fold re-cut, idempotence, and the hash collision suffix.
"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from lib.class_registry import (ACTIVE, RETIRED, Record, Registry, make_id,  # noqa: E402
                                specimens_of)


def _reg(*recs: tuple[str, str, list[str], str]) -> Registry:
    r = Registry()
    for rid, ent, members, created in recs:
        r.records[rid] = Record(id=rid, entity=ent, members=sorted(members),
                                created=created, label="unified-" + members[0])
    return r


class Inherit(unittest.TestCase):
    def test_single_candidate_inherits_and_grows(self):
        r = _reg(("c-a", "dr", ["s1", "s2"], "2026-01-01"))
        got = r.inherit({"dr": [(frozenset({"s1", "s2", "s3"}), "unified-s1")]}, "2026-02-01")
        self.assertEqual(got[("dr", frozenset({"s1", "s2", "s3"}))], "c-a")
        self.assertEqual(r.records["c-a"].members, ["s1", "s2", "s3"])
        self.assertEqual(r.records["c-a"].status, ACTIVE)

    def test_merge_larger_overlap_wins_other_retired(self):
        r = _reg(("c-big", "dr", ["s1", "s2", "s3"], "2026-01-02"),
                 ("c-small", "dr", ["s9"], "2026-01-01"))
        spec = frozenset({"s1", "s2", "s3", "s9"})
        got = r.inherit({"dr": [(spec, "unified-s1")]}, "2026-02-01")
        self.assertEqual(got[("dr", spec)], "c-big")
        self.assertEqual(r.records["c-small"].status, RETIRED)
        self.assertEqual(r.records["c-small"].merged_into, "c-big")

    def test_merge_tie_goes_to_the_older_record(self):
        r = _reg(("c-new", "dr", ["s1"], "2026-01-05"),
                 ("c-old", "dr", ["s2"], "2026-01-01"))
        spec = frozenset({"s1", "s2"})
        got = r.inherit({"dr": [(spec, "unified-s1")]})
        self.assertEqual(got[("dr", spec)], "c-old")
        self.assertEqual(r.records["c-new"].merged_into, "c-old")

    def test_split_largest_piece_keeps_the_id(self):
        r = _reg(("c-a", "dr", ["s1", "s2", "s3"], "2026-01-01"))
        big, small = frozenset({"s1", "s2"}), frozenset({"s3"})
        got = r.inherit({"dr": [(big, "unified-s1"), (small, "unified-s3")]}, "2026-02-01")
        self.assertEqual(got[("dr", big)], "c-a")
        nid = got[("dr", small)]
        self.assertNotEqual(nid, "c-a")
        self.assertEqual(r.records["c-a"].split_into, [nid])
        self.assertEqual(r.records[nid].members, ["s3"])
        self.assertEqual(r.records[nid].created, "2026-02-01")

    def test_relocation_keeps_the_id_and_touches_both_shards(self):
        r = _reg(("c-a", "royal_holstein", ["s1"], "2026-01-01"))
        spec = frozenset({"s1"})
        got = r.inherit({"royal_holstein": [], "royal_slesvig": [(spec, "unified-s1")]})
        self.assertEqual(got[("royal_slesvig", spec)], "c-a")
        self.assertEqual(r.records["c-a"].entity, "royal_slesvig")
        self.assertEqual(r.touched, {"royal_holstein", "royal_slesvig"})

    def test_fold_recut_is_invisible(self):
        """Specimens, not representatives: kmk-2 folded under kmk-1 yesterday,
        under kmk-3 today — the same specimen set, the same id."""
        r = _reg(("c-a", "dr", ["kmk-1", "kmk-2", "kmk-3"], "2026-01-01"))
        spec = specimens_of(["kmk-1", "kmk-3"], {"kmk-3": ["kmk-2"]})
        got = r.inherit({"dr": [(spec, "unified-kmk-1")]})
        self.assertEqual(got[("dr", spec)], "c-a")
        self.assertEqual(r.touched, set())

    def test_idempotent(self):
        r = _reg(("c-a", "dr", ["s1", "s2"], "2026-01-01"))
        parts = {"dr": [(frozenset({"s1", "s2"}), "unified-s1"),
                        (frozenset({"s7"}), "unified-s7")]}
        r.inherit(parts, "2026-02-01")
        first = {k: v.to_yaml() for k, v in r.records.items()}
        r.touched.clear()
        r.inherit(parts, "2026-02-02")
        self.assertEqual({k: v.to_yaml() for k, v in r.records.items()}, first)
        self.assertEqual(r.touched, set())

    def test_vanished_class_is_retired_not_deleted(self):
        r = _reg(("c-a", "dr", ["s1"], "2026-01-01"))
        r.inherit({"dr": []}, "2026-02-01")
        self.assertEqual(r.records["c-a"].status, RETIRED)
        self.assertIn("c-a", r.records)

    def test_unprocessed_entity_is_left_alone(self):
        r = _reg(("c-a", "other", ["s1"], "2026-01-01"))
        r.inherit({"dr": []})
        self.assertEqual(r.records["c-a"].status, ACTIVE)


class Ids(unittest.TestCase):
    def test_hash_is_order_independent_and_collision_suffixed(self):
        a = make_id(["s2", "s1"])
        self.assertEqual(a, make_id(["s1", "s2"]))
        self.assertTrue(a.startswith("c-") and len(a) == 10)
        self.assertEqual(make_id(["s1", "s2"], {a}), a + "-2")
        self.assertEqual(make_id(["s1", "s2"], {a, a + "-2"}), a + "-3")


class RoundTrip(unittest.TestCase):
    def test_save_and_load_shards(self):
        r = _reg(("c-a", "dr", ["s1"], "2026-01-01"), ("c-b", "rh", ["s2"], "2026-01-01"))
        r.records["c-b"].status, r.records["c-b"].merged_into = RETIRED, "c-a"
        with tempfile.TemporaryDirectory() as tmp:
            written = r.save(Path(tmp), entities=["dr", "rh"])
            self.assertEqual(written, ["dr", "rh"])
            back = Registry.load_all(Path(tmp))
            self.assertEqual({k: v.to_yaml() for k, v in back.records.items()},
                             {k: v.to_yaml() for k, v in r.records.items()})
            self.assertEqual(back.resolve("c-b").id, "c-a")
            # unchanged content → nothing rewritten
            self.assertEqual(back.save(Path(tmp), entities=["dr", "rh"]), [])


if __name__ == "__main__":
    unittest.main()
