"""Tests for the verified-vs-verified metal-conflict guard in
merge_seeds_cross_source._collect_metal (shipped 2026-06-20).

Two members both `metal_verified: True` disagreeing on metal is a genuine
divergence the curator must resolve — the merger must NOT silently pick one
(it once shipped KMM museum «soelv» over Hede «copper» on f6h17). The guard:
  - thin-line alloy pairs (silver<->billon, bronze<->copper) → WARN, pick by
    authority (same metal under looser-vs-tighter labels).
  - any other (copper/silver, gold/silver, …) → raise MetalConflictError.
Unverified disagreements do NOT trip it (only one verified side wins normally).

Run via:
    .venv/bin/python -m unittest tests.test_metal_conflict_guard -v
"""
from __future__ import annotations

import io
import sys
import unittest
from contextlib import redirect_stderr
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

import importlib.util
_spec = importlib.util.spec_from_file_location(
    "merge_seeds_cross_source",
    str(PROJECT_ROOT / "scripts" / "maintenance"
        / "merge_seeds_cross_source.py"),
)
_mg = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mg)

_collect_metal = _mg._collect_metal
MetalConflictError = _mg.MetalConflictError


def _m(mid, metal, verified):
    return {"id": mid, "metal": metal, "metal_verified": verified}


class TestMetalConflictGuard(unittest.TestCase):
    def test_copper_vs_silver_raises(self):
        members = [_m("dk-hede-f6h17", "copper", True),
                   _m("kmk-175835", "silver", True)]
        with self.assertRaises(MetalConflictError):
            _collect_metal(members)

    def test_bronze_vs_copper_warns_picks_authority(self):
        # bronze<->copper is a thin alloy line (bronze ≈ 95% Cu; museums tag a
        # bronze coin «kobber»). c9h18b: Hede=bronze (auth 5) beats KMM=copper
        # (auth 0) → warn, pick bronze. (Must NOT raise — user-set 2026-06-22.)
        members = [_m("dk-hede-c9h18b", "bronze", True),
                   _m("kmk-569264", "copper", True)]
        err = io.StringIO()
        with redirect_stderr(err):
            out = _collect_metal(members)  # must NOT raise
        self.assertEqual(out, "bronze")
        self.assertIn("bronze<->copper", err.getvalue())

    def test_copper_vs_gold_raises(self):
        # A cross-pair conflict (copper in {bronze,copper}, gold in neither) is
        # NOT within any single thin-line pair → still raises.
        members = [_m("dk-hede-x", "copper", True),
                   _m("kmk-y", "gold", True)]
        with self.assertRaises(MetalConflictError):
            _collect_metal(members)

    def test_silver_vs_billon_warns_no_raise(self):
        members = [_m("dk-hede-x", "silver", True),
                   _m("kmk-y", "billon", True)]
        err = io.StringIO()
        with redirect_stderr(err):
            out = _collect_metal(members)  # must NOT raise
        self.assertIn(out, {"silver", "billon"})
        self.assertIn("billon<->silver", err.getvalue())

    def test_same_metal_no_conflict(self):
        members = [_m("a", "copper", True), _m("b", "copper", True)]
        self.assertEqual(_collect_metal(members), "copper")

    def test_only_one_verified_no_conflict(self):
        # copper(verified) vs silver(UNVERIFIED) → verified wins, no raise
        members = [_m("dk-hede-z", "copper", True),
                   _m("kmk-w", "silver", False)]
        self.assertEqual(_collect_metal(members), "copper")

    def test_unverified_disagreement_no_conflict(self):
        members = [_m("a", "copper", False), _m("b", "silver", False)]
        self.assertIsNotNone(_collect_metal(members))  # Tier-2 pick, no raise


if __name__ == "__main__":
    unittest.main(verbosity=2)
