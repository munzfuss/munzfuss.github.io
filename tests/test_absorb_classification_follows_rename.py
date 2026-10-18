"""A classified coin whose class is renamed keeps its classification.

Caught 2026-10-17 while re-flowing the merger's scoped-index rules: the
Christian V 1 Krone Hede 41A (danish_norway) sat in final
`unified-kmk-345581` as 9_25_thaler; the merger regrouped its seeds, the old
final retired into the host `unified-kmk-394032` — a seed_unsorted KMM
singleton — and the coin dropped to seed_unsorted. The retired foundation's
classification was snapshotted, but the replace-shaped fields were applied on
the bulk-promote path only, and an existing host is never bulk-promoted.

Rule: the classification travels onto an UNCLASSIFIED host when every retired
peer agrees on it; a classified host keeps its own, and two disagreeing peers
leave the host alone.
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

CLS = ("9_25_thaler", "I", "kurant")


def apply(entry, classes):
    AB._apply_migrated_merge_fields(entry, "host", [], {"host": {"__classes__": classes}})
    return entry


class TestClassificationFollowsRename(unittest.TestCase):
    def test_unclassified_host_inherits(self):
        e = apply({"fuss": "seed_unsorted", "phase": "kmk", "kind": "kurant"}, [CLS])
        self.assertEqual((e["fuss"], e["phase"], e["kind"]), CLS)

    def test_classified_host_keeps_its_own(self):
        e = apply({"fuss": "kronemont", "phase": "I", "kind": "kurant"}, [CLS])
        self.assertEqual(e["fuss"], "kronemont")

    def test_disagreeing_peers_leave_host_alone(self):
        e = apply({"fuss": "seed_unsorted", "phase": "kmk"}, [CLS, ("9_thaler", "I", "kurant")])
        self.assertEqual(e["fuss"], "seed_unsorted")


if __name__ == "__main__":
    unittest.main()
