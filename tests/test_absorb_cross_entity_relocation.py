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
        # NB: the ucoin member is `dk-tid-70693`. Its V1-legacy twin
        # `km-761-fr-vi-1854` was dropped from the corpus in 6893067 ("drop 129
        # V1-legacy ucoin twins") and is no longer a seed — it survives only in
        # this entry's `reason` prose and in the synthetic fixture below.
        for m in ("dk-hede-f7h6a", "dk-hede-f7h6c", "dk-tid-70693"):
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
        fe = {"id": "unified-dk-hede-f7h6a", "origin": "promoted",
              "composed_of": ["unified-dk-hede-f7h6a"], "fuss": "18_5_thaler"}
        self.assertTrue(A._final_is_relocated(fe, self.RELOC))

    def test_shape_b_folded_orphan_unique_id(self):
        # unified-dk-hede-f7h6c folded into f7h6a but kept its own unique id
        fe = {"id": "unified-dk-hede-f7h6c", "origin": "promoted",
              "composed_of": ["unified-dk-hede-f7h6c"], "fuss": "pistolenfuss"}
        self.assertTrue(A._final_is_relocated(fe, self.RELOC))

    def test_unrelated_coin_not_dropped(self):
        fe = {"id": "unified-dk-hede-c4h62", "origin": "promoted",
              "composed_of": ["unified-dk-hede-c4h62"], "fuss": "9_25_thaler"}
        self.assertFalse(A._final_is_relocated(fe, self.RELOC))

    def test_non_unified_foundation_not_touched(self):
        # a V1 foundation (no `unified-` prefix) is never dropped by this gate
        fe = {"id": "km-761-fr-vi-1854", "composed_of": [], "fuss": "18_5_thaler"}
        self.assertFalse(A._final_is_relocated(fe, self.RELOC))

    def test_composed_member_match(self):
        # matches a relocated seed that appears as a composed_of member
        fe = {"id": "unified-dk-something", "origin": "promoted",
              "composed_of": ["dk-hede-f7h6a", "denmark-numismaster-66090"]}
        self.assertTrue(A._final_is_relocated(fe, self.RELOC))


class TestRelocationCarry(unittest.TestCase):
    """The TARGET gap-fills a relocated coin's curator fields from the source
    final, and the SOURCE keeps its copy until the target can (2026-10-15,
    MB 57: the Note lived only on the royal_holstein final and was lost)."""

    SRC_FINAL = {"id": "unified-s1", "origin": "promoted", "composed_of": ["unified-s1"],
                 "fuss": "rhinsk_gylden_fod", "phase": {"denmark": "III.b"},
                 "kind": "kurant", "note": {"de": "N"},
                 "issuing_entity": "src"}
    SHELL = {"id": "unified-s9", "origin": "promoted", "composed_of": ["unified-s9"],
             "fuss": "x_fod", "note": {"de": "shell"}}

    def setUp(self):
        self._saved = (A._FINAL_SNAPSHOT, A._cross_entity_relocated_out,
                       A._final_is_routed_away, A._target_holds_relocated,
                       set(A._RUN_ENTITIES))
        A._FINAL_SNAPSHOT = {"src": [self.SRC_FINAL, self.SHELL], "tgt": []}
        A._cross_entity_relocated_out = (
            lambda e: {"s1"} if e == "src" else set())
        A._final_is_routed_away = lambda fe, e: False
        A._RUN_ENTITIES.clear()

    def tearDown(self):
        (A._FINAL_SNAPSHOT, A._cross_entity_relocated_out,
         A._final_is_routed_away, A._target_holds_relocated, run) = self._saved
        A._RUN_ENTITIES.clear()
        A._RUN_ENTITIES.update(run)

    def test_target_finds_the_relocated_source_final(self):
        got = A._cross_entity_carry_in(
            "tgt", [{"id": "unified-s1", "origin": "promoted", "composed_of": ["s1", "s2"]},
                    {"id": "unified-s9x", "origin": "promoted", "composed_of": ["s9"]}])
        self.assertEqual([(h, e, f["id"]) for h, e, f in got],
                         [("unified-s1", "src", "unified-s1")])

    def test_kept_shell_carries_nothing(self):
        # unified-s9 is not relocated (only kept for review) — even though its
        # seed now lives in the target, it must not seed the target's fields.
        got = A._cross_entity_carry_in(
            "tgt", [{"id": "unified-s9x", "origin": "promoted", "composed_of": ["s9"]}])
        self.assertEqual(got, [])

    def test_source_keeps_copy_until_target_holds_it(self):
        A._target_holds_relocated = lambda tgt, keys: False
        self.assertFalse(A._relocation_drop_is_safe(self.SRC_FINAL, {"tgt"}))
        A._target_holds_relocated = lambda tgt, keys: True
        self.assertTrue(A._relocation_drop_is_safe(self.SRC_FINAL, {"tgt"}))

    def test_target_in_this_run_makes_drop_safe(self):
        A._target_holds_relocated = lambda tgt, keys: False
        A._RUN_ENTITIES.add("tgt")
        self.assertTrue(A._relocation_drop_is_safe(self.SRC_FINAL, {"tgt"}))


if __name__ == "__main__":
    unittest.main(verbosity=2)
