"""Regression: the merger's cross-entity COMPLETENESS guard flags forgotten
members.

When `_cross_entity.yml` lists SOME seeds of a joint-mint coin but the curator
forgets others (e.g. extra KMM museum specimens of the same Hede type), the
unlisted seeds stay in the source entity and fragment/phantom there — and the
absorber's relocation filter can't see them (they're not in `relocated_out`).
The merger now warns (per run) about any seed that shares a member's KM/Hede
base + nominal + metal but is neither listed nor in the entry's `excludes:`.
Added 2026-07-01 after the guard found 16 real cases (KMM specimens not pulled
into c7h33 / f6h14 / c7h13).

Run:
    .venv/bin/python -m unittest tests.test_cross_entity_completeness -v
"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
sys.path.insert(0, str(PROJECT_ROOT / "scripts" / "maintenance"))

import merge_seeds_cross_source as M  # noqa: E402


def _coin(hede, metal, nominal, ruler="Frederik VII.", vol="f7h"):
    return {"catalog": {"hede": hede, "hede_volume": vol},
            "ruler": ruler, "metal": metal, "nominal": nominal}


class TestCompletenessHelpers(unittest.TestCase):
    def test_base_strip(self):
        # hede 6A / 6 both reduce to base 6 under the same ruler scope
        a = M._completeness_base_keys(_coin("6A", "silver", "2 Rigsdaler"), "danish_realm")
        b = M._completeness_base_keys(_coin("6", "silver", "2 Rigsdaler"), "danish_realm")
        self.assertTrue(a & b, "6A and 6 should share a base key")

    def test_different_ruler_no_collision(self):
        fv = M._completeness_base_keys(_coin("6", "silver", "x", ruler="Frederik VII."), "danish_realm")
        c7 = M._completeness_base_keys(_coin("6", "silver", "x", ruler="Christian VII."), "danish_realm")
        self.assertFalse(fv & c7, "Hede 6 of different rulers must NOT collide")

    def test_norm_nominal(self):
        self.assertEqual(M._norm_nominal_key("2 Skilling"), M._norm_nominal_key("2-skilling"))
        self.assertEqual(M._norm_nominal_key("2 Skilling"), M._norm_nominal_key("2skilling"))
        self.assertNotEqual(M._norm_nominal_key("2 Skilling"), M._norm_nominal_key("4 Skilling"))


class TestCompletenessCheck(unittest.TestCase):
    def setUp(self):
        self.all_by_id = {
            "kmk-A": _coin("6", "silver", "2 Rigsdaler"),   # listed member 1
            "kmk-A2": _coin("6A", "silver", "2 Rigsdaler"),  # listed member 2 (>=2 required)
            "kmk-B": _coin("6", "silver", "2 Rigsdaler"),   # forgotten member -> FLAG
            "kmk-C": _coin("6", "gold", "2 Rigsdaler"),     # metal mismatch -> skip
            "kmk-D": _coin("6", "silver", "4 Skilling"),    # nominal mismatch -> skip
            "kmk-E": _coin("6", "silver", "2 Rigsdaler"),   # excluded -> skip
            "kmk-F": _coin("7", "silver", "2 Rigsdaler"),   # different base -> skip
        }
        self.home = {k: "danish_realm" for k in self.all_by_id}

    _MEMBERS = "      - kmk-A\n      - kmk-A2\n"

    def _run(self, doc_text):
        with tempfile.NamedTemporaryFile("w", suffix=".yml", delete=False) as fh:
            fh.write(doc_text)
            path = Path(fh.name)
        orig = M.V2_CROSS_ENTITY_DECISIONS
        try:
            M.V2_CROSS_ENTITY_DECISIONS = path
            return M._check_cross_entity_completeness(self.all_by_id, self.home)
        finally:
            M.V2_CROSS_ENTITY_DECISIONS = orig
            path.unlink()

    def test_flags_only_forgotten_member(self):
        flagged = self._run(
            "merges:\n"
            "  - target_entity: royal_holstein\n"
            "    members:\n"
            + self._MEMBERS
        )
        ids = {row[1] for row in flagged}
        self.assertIn("kmk-B", ids)                 # forgotten member flagged
        self.assertNotIn("kmk-C", ids)              # metal mismatch
        self.assertNotIn("kmk-D", ids)              # nominal mismatch
        self.assertNotIn("kmk-F", ids)              # different base
        self.assertNotIn("kmk-A", ids)              # the member itself

    def test_excludes_suppresses(self):
        flagged = self._run(
            "merges:\n"
            "  - target_entity: royal_holstein\n"
            "    members:\n"
            + self._MEMBERS
            + "    excludes:\n"
            "      - kmk-B\n"      # now curator-confirmed NOT a member
        )
        ids = {row[1] for row in flagged}
        self.assertNotIn("kmk-B", ids)              # excluded -> not flagged


if __name__ == "__main__":
    unittest.main(verbosity=2)
