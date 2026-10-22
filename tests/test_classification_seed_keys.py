"""Classification decisions keyed by a class id went dead on every re-merge.

A `unified-<top-authority member>` id renames when a higher-authority member
joins, a §9a fold is re-cut or the class splits; on 2026-10-22 238 of 498
`classification_decisions` assignments pointed at ids in no final and absorb
had reported them only as a count (ASSIGN-MISS) for months. D49 stage 1 keys
decisions by a SEED id and resolves it to the class at apply time — a bare
Hede code and a specimen folded into a representative (`_thinned_from`)
included. These tests pin the resolver, the conflict rule, and the two audit
checks that must accept the new key forms.
"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "maintenance"))

import absorb_seeds_into_final_v2 as ab  # noqa: E402
import audit_v2  # noqa: E402

SEED_CLASS = {
    "dk-hede-c4h112a": "unified-dk-hede-c4h112a",
    "dk-hede-c4h112b": "unified-dk-hede-c4h112a",
    "kmk-292019": "unified-dk-hede-c4h112a",
    "ngc-1050065": "unified-ngc-1050065",
}
SUB = {"dk-hede-c4h112": ["dk-hede-c4h112a", "dk-hede-c4h112b"]}
THINNED = {"kmk-132095": ["kmk-292019"]}
CLS = "unified-dk-hede-c4h112a"


def _resolve(cid):
    return ab._resolve_decision_key(cid, SEED_CLASS, lambda b: SUB.get(b, []), THINNED)


class Resolver(unittest.TestCase):
    def test_seed_key_reaches_its_class(self):
        self.assertEqual(_resolve("kmk-292019"), {"kmk-292019", CLS})

    def test_bare_hede_code_reaches_the_sub_letters_class(self):
        self.assertEqual(_resolve("dk-hede-c4h112"), {"dk-hede-c4h112", CLS})

    def test_folded_specimen_reaches_the_representatives_class(self):
        """kmk-132095 is no seed record any more — only `_thinned_from` on
        kmk-292019 remembers it; the decision still lands on the class."""
        self.assertEqual(_resolve("kmk-132095"), {"kmk-132095", CLS})

    def test_class_id_still_matches_itself(self):
        self.assertEqual(_resolve("unified-ngc-1050065"), {"unified-ngc-1050065"})

    def test_unknown_key_resolves_to_nothing_but_itself(self):
        self.assertEqual(_resolve("kmk-0"), {"kmk-0"})


class ConflictRule(unittest.TestCase):
    def setUp(self):
        self._saved = (ab._SEED_CLASS_INDEX, ab._SUB_LETTER_INDEX, ab._THINNED_REP_INDEX)
        ab._SEED_CLASS_INDEX = dict(SEED_CLASS)
        ab._SUB_LETTER_INDEX = dict(SUB)
        ab._THINNED_REP_INDEX = dict(THINNED)

    def tearDown(self):
        ab._SEED_CLASS_INDEX, ab._SUB_LETTER_INDEX, ab._THINNED_REP_INDEX = self._saved

    def test_agreeing_duplicates_are_fine_and_disagreeing_ones_conflict(self):
        same = [{"coin_id": "kmk-292019", "fuss": "f", "phase": "I", "kind": "kurant"},
                {"coin_id": "dk-hede-c4h112", "fuss": "f", "phase": "I", "kind": "kurant"}]
        by_key, conflicts = ab._index_assignments(same)
        self.assertEqual(conflicts, [])
        self.assertEqual(len(by_key[CLS]), 2)
        other = same + [{"coin_id": "kmk-132095", "fuss": "g", "phase": "I", "kind": "kurant"}]
        _, conflicts = ab._index_assignments(other)
        self.assertEqual([c["key"] for c in conflicts].count(CLS), 1)

    def test_superseded_entry_is_a_record_not_a_decision(self):
        a = [{"coin_id": "kmk-292019", "fuss": "f", "phase": "I", "kind": "kurant"},
             {"coin_id": "kmk-132095", "fuss": "f", "phase": "I", "kind": "tarif",
              "superseded_by": "kmk-292019 (danish_realm)"}]
        by_key, conflicts = ab._index_assignments(a)
        self.assertEqual(conflicts, [])
        self.assertEqual(len(by_key[CLS]), 1)

    def test_dict_valued_phase_is_comparable(self):
        a = [{"coin_id": "kmk-292019", "fuss": "f", "phase": {"denmark": "III"}, "kind": "k"},
             {"coin_id": "kmk-132095", "fuss": "f", "phase": {"denmark": "III"}, "kind": "k"}]
        _, conflicts = ab._index_assignments(a)
        self.assertEqual(conflicts, [])


SEEDS = [
    ("hede", "danish_realm", {"id": "dk-hede-c4h112a"}),
    ("kmk", "danish_realm", {"id": "kmk-292019", "_thinned_from": ["kmk-132095"]}),
]
UNIFIED = [("danish_realm", {"id": CLS, "composed_of": ["dk-hede-c4h112a", "kmk-292019"]})]
FINAL = [("danish_realm", {"id": CLS, "composed_of": [CLS]})]


class AuditChecks(unittest.TestCase):
    def test_i6_accepts_folded_specimen_and_bare_hede_code(self):
        with tempfile.TemporaryDirectory() as tmp:
            d = Path(tmp)
            (d / "danish_realm.yml").write_text(
                "assignments:\n  - coin_id: kmk-132095\n    fuss: f\n"
                "  - coin_id: dk-hede-c4h112\n    fuss: f\n  - coin_id: kmk-0\n    fuss: f\n")
            (d / "merge").mkdir()
            saved = (audit_v2.V2_CLASSIFICATION_DECISIONS, audit_v2.V2_MERGE_DECISIONS)
            audit_v2.V2_CLASSIFICATION_DECISIONS = d
            audit_v2.V2_MERGE_DECISIONS = d / "merge"
            try:
                errs = audit_v2.check_i6_decision_refs(UNIFIED, SEEDS, FINAL)
            finally:
                audit_v2.V2_CLASSIFICATION_DECISIONS, audit_v2.V2_MERGE_DECISIONS = saved
        self.assertEqual(len(errs), 1)
        self.assertIn("kmk-0", errs[0])

    def test_i13_locates_a_seed_keyed_decision_by_its_seeds_final(self):
        with tempfile.TemporaryDirectory() as tmp:
            t = Path(tmp)
            for sub in ("merge", "cls", "excl"):
                (t / sub).mkdir()
            (t / "cls" / "royal_holstein.yml").write_text(
                "assignments:\n  - coin_id: kmk-132095\n    fuss: f\n")
            errs = audit_v2.check_i13_decision_entity(
                FINAL, UNIFIED, SEEDS, t / "merge", t / "cls", t / "excl")
        self.assertEqual(len(errs), 1)
        self.assertIn("danish_realm", errs[0])


if __name__ == "__main__":
    unittest.main()
