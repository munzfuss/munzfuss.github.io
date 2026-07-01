"""Regression: the absorber drops CROSS-ENTITY relocation orphans.

When `_cross_entity.yml` pulls a coin's seeds from a SOURCE entity into a
different TARGET entity, the merger excludes them from the source's seed
processing — but a stale source-side FINAL (the pre-move foundation) used to
survive the `_is_vanished_stale_final` gate whenever it carried curation (a real
`fuss`/`phase`), because the per-entity `seed_to_unified` map can't see that the
seed moved to another entity's bucket. That left two orphan shapes on the source
page:
  A. a same-id duplicate (audit_v2 I3 catches it, forcing manual cleanup);
  B. a folded orphan under a now-unique id (I3 does NOT catch it — a silent
     phantom row).
Both are now dropped by `_final_is_relocated` in the absorber's stale-foundation
purge (Shape X), driven directly by `_cross_entity.yml`. Caught + fixed 2026-07-01
while consolidating KM 761 «2 Rigsdaler» (f7h6a/f7h6c relocated danish_realm ->
royal_holstein).

Run:
    .venv/bin/python -m unittest tests.test_absorb_cross_entity_relocation -v
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
sys.path.insert(0, str(PROJECT_ROOT / "scripts" / "maintenance"))

import absorb_seeds_into_final_v2 as A  # noqa: E402


class TestCrossEntityRelocatedOut(unittest.TestCase):
    """`_cross_entity_relocated_out` reads the real _cross_entity.yml."""

    def test_km761_members_relocated_out_of_danish_realm(self):
        # KM 761 cross-entity entry has target_entity=royal_holstein, so its
        # danish_realm-sourced members are relocated OUT of danish_realm.
        reloc = A._cross_entity_relocated_out("danish_realm")
        for m in ("dk-hede-f7h6a", "dk-hede-f7h6c", "km-761-fr-vi-1854"):
            self.assertIn(m, reloc, f"{m} should be relocated out of danish_realm")

    def test_target_entity_keeps_its_members(self):
        # For the TARGET entity (royal_holstein) the KM 761 members are NOT
        # "relocated out" — they belong there.
        reloc = A._cross_entity_relocated_out("royal_holstein")
        self.assertNotIn("dk-hede-f7h6a", reloc)
        self.assertNotIn("dk-hede-f7h6b", reloc)


class TestFinalIsRelocated(unittest.TestCase):
    RELOC = {"dk-hede-f7h6a", "dk-hede-f7h6c", "km-761-fr-vi-1854"}

    def test_shape_a_same_id_dup(self):
        # unified-dk-hede-f7h6a survives in danish_realm as a same-id dup
        fe = {"id": "unified-dk-hede-f7h6a",
              "composed_of": ["unified-dk-hede-f7h6a"], "fuss": "18_5_thaler"}
        self.assertTrue(A._final_is_relocated(fe, self.RELOC))

    def test_shape_b_folded_orphan_unique_id(self):
        # unified-dk-hede-f7h6c folded into f7h6a but kept its own unique id
        fe = {"id": "unified-dk-hede-f7h6c",
              "composed_of": ["unified-dk-hede-f7h6c"], "fuss": "pistolenfuss"}
        self.assertTrue(A._final_is_relocated(fe, self.RELOC))

    def test_unrelated_coin_not_dropped(self):
        fe = {"id": "unified-dk-hede-c4h62",
              "composed_of": ["unified-dk-hede-c4h62"], "fuss": "9_25_thaler"}
        self.assertFalse(A._final_is_relocated(fe, self.RELOC))

    def test_non_unified_foundation_not_touched(self):
        # a V1 foundation (no `unified-` prefix) is never dropped by this gate
        fe = {"id": "km-761-fr-vi-1854", "composed_of": [], "fuss": "18_5_thaler"}
        self.assertFalse(A._final_is_relocated(fe, self.RELOC))

    def test_composed_member_match(self):
        # matches a relocated seed that appears as a composed_of member
        fe = {"id": "unified-dk-something",
              "composed_of": ["dk-hede-f7h6a", "denmark-numismaster-66090"]}
        self.assertTrue(A._final_is_relocated(fe, self.RELOC))


if __name__ == "__main__":
    unittest.main(verbosity=2)
