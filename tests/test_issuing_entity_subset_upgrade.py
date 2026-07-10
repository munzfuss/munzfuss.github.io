"""Unit tests for the issuing_entity subset-scalar → joint upgrade in the absorb
step (`_enrich_final_entry`, 2026-07-10).

A foundation freezes `issuing_entity` verbatim (it is in
`_FOUNDATION_IMMUTABLE_FIELDS`), so a foundation-reset final can carry a STALE
SCALAR left over from before the coin's second mint / cross-entity joint was
resolved (e.g. `unified-dk-hede-c3h14` «1 Rhinsk Gylden» struck at Flensburg
[royal_holstein] AND Roskilde [danish_realm], whose final was frozen at scalar
`royal_holstein` while the merger correctly derived the joint on the
seed_unified bridge). The guard adopts a composed_of member's list-form (joint)
issuing_entity when the frozen scalar is a SUBSET of it — the merger's
mint-derived joint is authoritative and strictly richer. It fires ONLY for the
subset case, so a genuine commission strike (issuer ≠ mint, scalar ∉ list) and
an explicit `issuing_entity` curation-hold are both left untouched.
"""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "maintenance"))

from absorb_seeds_into_final_v2 import _enrich_final_entry  # noqa: E402

JOINT = ["danish_realm", "royal_holstein"]


def _ie(final, members):
    out, _ = _enrich_final_entry(final, members, "royal_holstein")
    return out.get("issuing_entity")


class IssuingEntitySubsetUpgrade(unittest.TestCase):
    def test_subset_scalar_upgrades_to_joint(self):
        # the c3h14 case: frozen scalar royal_holstein ⊂ joint → adopt joint
        f = {"id": "x", "issuing_entity": "royal_holstein", "composed_of": ["x"]}
        m = [f, {"id": "x", "issuing_entity": list(JOINT)}]
        self.assertEqual(_ie(f, m), JOINT)

    def test_other_subset_element_upgrades(self):
        # danish_realm ⊂ joint upgrades too (the c8h4a / c8h8b class)
        f = {"id": "x", "issuing_entity": "danish_realm", "composed_of": ["x"]}
        m = [f, {"id": "x", "issuing_entity": list(JOINT)}]
        self.assertEqual(_ie(f, m), JOINT)

    def test_non_subset_scalar_kept(self):
        # commission strike: issuer ∉ mint-derived joint → keep the scalar
        f = {"id": "y", "issuing_entity": "gottorp_duchy", "composed_of": ["y"]}
        m = [f, {"id": "y", "issuing_entity": list(JOINT)}]
        self.assertEqual(_ie(f, m), "gottorp_duchy")

    def test_curation_hold_opts_out(self):
        # an explicit issuing_entity hold freezes the scalar even when subset
        f = {"id": "z", "issuing_entity": "royal_holstein", "composed_of": ["z"],
             "_curation_holds": {"issuing_entity": "curator froze this scalar"}}
        m = [f, {"id": "z", "issuing_entity": list(JOINT)}]
        self.assertEqual(_ie(f, m), "royal_holstein")

    def test_list_curation_hold_opts_out(self):
        # legacy list-form _curation_holds also opts out
        f = {"id": "z2", "issuing_entity": "royal_holstein", "composed_of": ["z2"],
             "_curation_holds": ["issuing_entity"]}
        m = [f, {"id": "z2", "issuing_entity": list(JOINT)}]
        self.assertEqual(_ie(f, m), "royal_holstein")

    def test_already_joint_unchanged(self):
        f = {"id": "w", "issuing_entity": list(JOINT), "composed_of": ["w"]}
        m = [f, {"id": "w", "issuing_entity": list(JOINT)}]
        self.assertEqual(_ie(f, m), JOINT)

    def test_no_member_list_keeps_scalar(self):
        # no composed_of member carries a joint → nothing to upgrade to
        f = {"id": "s", "issuing_entity": "royal_holstein", "composed_of": ["s"]}
        m = [f, {"id": "s", "issuing_entity": "royal_holstein"}]
        self.assertEqual(_ie(f, m), "royal_holstein")

    def test_single_element_list_not_treated_as_joint(self):
        # a member list of length 1 is not a joint — do not overwrite the scalar
        f = {"id": "u", "issuing_entity": "royal_holstein", "composed_of": ["u"]}
        m = [f, {"id": "u", "issuing_entity": ["royal_holstein"]}]
        self.assertEqual(_ie(f, m), "royal_holstein")


if __name__ == "__main__":
    unittest.main()
