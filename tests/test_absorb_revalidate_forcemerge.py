"""Tests for the re-validate force-merge exemption in absorb_seeds_into_final_v2.

Function under test:
    scripts/maintenance/absorb_seeds_into_final_v2.py :: _revalidate_composed_of

Context — the bug this guards against (2026-06-20):
The absorb's re-validate pass evicts a composed_of member whose nominal
GENUINELY differs from the host AND shares no type-level catalogue
(`_nominal_genuinely_differs` + not `_shares_type_level_catalog`). That is
correct for accidental mis-groupings — but it ALSO evicted *curator-confirmed*
§9a merges where the museum specimen's nominal differs from the host and it
carries no Hede/KM index (e.g. «1 Dobbelt ungarsk gylden» merged into
«2 Ungersk Gylden», «1 Goldgulden» into «1 Rhinsk Gylden»). I.e. a re-absorb
silently undid those merges. The fix: the re-validate now honours
`merge_decisions::merges` (+ `_cross_entity::merges`) — a member pair the
curator explicitly merged is NEVER evicted, whatever the nominal / catalogue
signals say. This mirrors the existing `no_merges` authority (the negative
direction); the positive direction was the gap.

Run via:
    .venv/bin/python -m unittest tests.test_absorb_revalidate_forcemerge -v
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

import importlib.util
_spec = importlib.util.spec_from_file_location(
    "absorb_seeds_into_final_v2",
    str(PROJECT_ROOT / "scripts" / "maintenance"
        / "absorb_seeds_into_final_v2.py"),
)
_absorb = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_absorb)

_revalidate = _absorb._revalidate_composed_of
_seed_of = _absorb._seed_of


def _scenario():
    """A host with a genuinely-nominal-mismatched member that shares no
    type-level catalogue — the exact eviction-trigger shape. The merger's own
    «8 Skilling» vs «1 Denning» genuine-mismatch example from the docstring."""
    host = {
        "id": "unified-km-42-test",
        "nominal": "8 Skilling",
        "catalog": {"km": "42"},
        "composed_of": ["unified-km-42-test", "unified-kmk-99-test"],
    }
    member = {"id": "unified-kmk-99-test", "nominal": "1 Denning", "catalog": {}}
    final_by_id = {host["id"]: host}
    unified_by_id = {host["id"]: host, member["id"]: member}
    return final_by_id, unified_by_id


class TestSeedOf(unittest.TestCase):
    def test_strips_unified_prefix(self):
        self.assertEqual(_seed_of("unified-kmk-99"), "kmk-99")

    def test_passes_through_seed_id(self):
        self.assertEqual(_seed_of("dk-hede-c3h2"), "dk-hede-c3h2")


class TestRevalidateForceMergeExempt(unittest.TestCase):
    def test_mismatch_evicted_without_exemption(self):
        # Baseline: a genuine mismatch + no catalogue tie IS evicted.
        fb, ub = _scenario()
        ev = _revalidate(fb, ub, "danish_realm")
        self.assertEqual(ev.get("unified-km-42-test"), {"unified-kmk-99-test"})

    def test_mismatch_exempt_when_curator_forced(self):
        # The fix: same pair, but curator-forced → NOT evicted.
        fb, ub = _scenario()
        forced = {frozenset({"km-42-test", "kmk-99-test"})}
        ev = _revalidate(fb, ub, "danish_realm", forced)
        self.assertEqual(ev, {})

    def test_unrelated_force_pair_does_not_exempt(self):
        # Regression guard: a force-merge entry for a DIFFERENT pair must NOT
        # exempt this mismatch — eviction still fires.
        fb, ub = _scenario()
        forced = {frozenset({"foo-1", "bar-2"})}
        ev = _revalidate(fb, ub, "danish_realm", forced)
        self.assertEqual(ev.get("unified-km-42-test"), {"unified-kmk-99-test"})

    def test_none_force_pairs_is_backward_compatible(self):
        # Default param (None) preserves the pre-fix behaviour exactly.
        fb, ub = _scenario()
        ev = _revalidate(fb, ub, "danish_realm", None)
        self.assertEqual(ev.get("unified-km-42-test"), {"unified-kmk-99-test"})


if __name__ == "__main__":
    unittest.main(verbosity=2)
