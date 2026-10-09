"""Curator decisions filed under an entity their coin has since left.

Every V2 decision surface is per entity — classification_decisions/<e>.yml,
merge_decisions/<e>.yml, exclusions/<e>.yml — and each pipeline run reads only
its own entity's file. When the royal_slesvig entity was introduced
(~2026-08-26) the Christian IV Haderslev gold moved out of royal_holstein, but
five fuss/phase assignments stayed in classification_decisions/royal_holstein.yml.
Absorb for royal_holstein never met those coins, absorb for royal_slesvig never
read that file, and the coins fell to seed_unsorted with no warning anywhere.
The same sweep (2026-10-09) found year_demote entries stranded in gottorp_duchy
and exclusions stranded in royal_holstein / danish_realm whose coins kept
rendering. audit_v2 I13 now fails on that shape; these tests pin it per surface
on a synthetic tree.
"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import audit_v2  # noqa: E402

SEEDS = [
    ("hede", "royal_slesvig", {"id": "dk-hede-c4h8a"}),
    ("bruun", "royal_holstein", {"id": "dk-bruun-1"}),
    ("kmk", "gottorp_duchy", {"id": "kmk-1"}),
]
UNIFIED = [
    ("royal_slesvig", {"id": "unified-dk-hede-c4h8a", "composed_of": ["dk-hede-c4h8a"]}),
    ("royal_slesvig", {"id": "unified-dk-bruun-1", "composed_of": ["dk-bruun-1"]}),
    ("gottorp_duchy", {"id": "unified-kmk-1", "composed_of": ["kmk-1"]}),
]
FINAL = [
    ("royal_slesvig", {"id": "unified-dk-hede-c4h8a", "composed_of": ["unified-dk-hede-c4h8a"]}),
    ("royal_slesvig", {"id": "unified-dk-bruun-1", "composed_of": ["unified-dk-bruun-1"]}),
    ("gottorp_duchy", {"id": "unified-kmk-1", "composed_of": ["unified-kmk-1"]}),
]


class DecisionEntityDrift(unittest.TestCase):
    def _run(self, files: dict[str, str]) -> list[str]:
        with tempfile.TemporaryDirectory() as tmp:
            t = Path(tmp)
            for sub in ("merge", "cls", "excl"):
                (t / sub).mkdir()
            for rel, text in files.items():
                (t / rel).write_text(text)
            return audit_v2.check_i13_decision_entity(
                FINAL, UNIFIED, SEEDS, t / "merge", t / "cls", t / "excl")

    def test_assignment_left_in_old_entity(self):
        errs = self._run({"cls/royal_holstein.yml":
                          "assignments:\n  - coin_id: unified-dk-hede-c4h8a\n    fuss: x\n"})
        self.assertEqual(len(errs), 1)
        self.assertIn("royal_slesvig", errs[0])

    def test_year_demote_left_in_old_entity(self):
        errs = self._run({"merge/gottorp_duchy.yml":
                          "year_demote:\n  - member_id: dk-hede-c4h8a\n    reason: r\n"})
        self.assertEqual(len(errs), 1)
        self.assertIn("merge_decisions/royal_slesvig.yml", errs[0])

    def test_cross_entity_target_is_the_effective_home(self):
        """dk-bruun-1 is seeded in royal_holstein but routed to royal_slesvig."""
        files = {"merge/_cross_entity.yml":
                 "merges:\n  - target_entity: royal_slesvig\n    members: [dk-bruun-1]\n"}
        ok = self._run({**files, "merge/royal_slesvig.yml":
                        "no_merges:\n  - members: [dk-bruun-1, dk-hede-c4h8a]\n"})
        self.assertEqual(ok, [])
        bad = self._run({**files, "merge/royal_holstein.yml":
                         "no_merges:\n  - members: [dk-bruun-1]\n"})
        self.assertEqual(len(bad), 1)

    def test_exclusion_of_coin_rendering_elsewhere(self):
        errs = self._run({"excl/royal_holstein.yml": "exclusions:\n  - id: kmk-1\n"})
        self.assertEqual(len(errs), 1)
        self.assertIn("gottorp_duchy", errs[0])

    def test_correctly_filed_and_unresolved_pass(self):
        """Right file passes; an id nowhere in final is I6's job, not I13's."""
        errs = self._run({
            "cls/royal_slesvig.yml": "assignments:\n  - coin_id: unified-dk-hede-c4h8a\n",
            "cls/royal_holstein.yml": "assignments:\n  - coin_id: unified-gone\n",
            "excl/gottorp_duchy.yml": "exclusions:\n  - id: kmk-1\n",
            "merge/royal_slesvig.yml": "year_demote:\n  - member_id: dk-hede-c4h8\n",
        })
        self.assertEqual(errs, [])


if __name__ == "__main__":
    unittest.main()
