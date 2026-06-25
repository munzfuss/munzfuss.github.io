"""Thin-line metal consensus (curator decision 2026-06-25).

A {silver,billon} or {bronze,copper} spread across sources is an umbrella-vs-
precise labelling ambiguity, not a real conflict. `_thin_line_consensus_metal`
resolves it by:
  1. hard guard: silver/billon fineness ≥ 0.50 → silver;
  2. per-resource collapsed, authority-weighted vote (Hede 5 > Bruun 4 > Numista
     2 > Galster 1 > loose 1), verified-preferred;
  3. the vote decides only if a precise source (hede/numista/bruun/galster) voted
     AND there is a clear weighted winner;
  4. else (no precise / tie) → fineness tiebreak (<0.30 billon, ≥0.40 silver,
     0.30-0.40 → billon) / bronze.

Run via:
    .venv/bin/python -m unittest tests.test_thin_line_metal_consensus -v
"""
from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "maintenance"))
_spec = importlib.util.spec_from_file_location(
    "merge_seeds_cross_source",
    str(ROOT / "scripts" / "maintenance" / "merge_seeds_cross_source.py"))
_M = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_M)
_consensus = _M._thin_line_consensus_metal


def _s(rid, metal, verified=True, fineness=None):
    return {"id": rid, "metal": metal, "metal_verified": verified,
            "fineness": fineness}


BC = {"bronze", "copper"}
SB = {"silver", "billon"}


class TestBronzeCopper(unittest.TestCase):
    def test_precise_majority_bronze_beats_one_kmk_copper(self):
        # c9h18b: 4 bronze resources (incl. hede+numista precise) vs 1 kmk copper
        spec = [_s("denmark-numismaster-1", "bronze"), _s("dk-hede-2", "bronze"),
                _s("dk-numista-3", "bronze"), _s("dk-tid-4", "bronze"),
                _s("kmk-5", "copper")]
        self.assertEqual(_consensus(spec, BC), "bronze")

    def test_kmk_collapses_to_one_vote(self):
        # 5 kmk copper specimens collapse to ONE kmk vote; one precise bronze wins
        spec = [_s(f"kmk-{i}", "copper") for i in range(5)] + [_s("dk-hede-9", "bronze")]
        self.assertEqual(_consensus(spec, BC), "bronze")

    def test_no_precise_source_refinement_wins(self):
        # only loose numismaster copper + kmk split → no precise → bronze (refine)
        spec = [_s("denmark-numismaster-1", "copper"), _s("kmk-2", "bronze"),
                _s("kmk-3", "copper")]
        self.assertEqual(_consensus(spec, BC), "bronze")


class TestSilverBillonFinenessGuard(unittest.TestCase):
    def test_hard_guard_high_fineness_silver(self):
        # fineness ≥ 0.50 → silver even if all sources say billon
        spec = [_s("dk-hede-1", "billon", fineness=0.6),
                _s("dk-numista-2", "billon", fineness=0.6)]
        self.assertEqual(_consensus(spec, SB), "silver")

    def test_hede_silver_at_0406_wins(self):
        # Hede (weight 5) silver beats Numista (2) billon; also 0.406 ≥ 0.40
        spec = [_s("dk-hede-1", "silver", fineness=0.406),
                _s("dk-numista-2", "billon", fineness=0.406)]
        self.assertEqual(_consensus(spec, SB), "silver")

    def test_low_fineness_tiebreak_billon(self):
        # no precise majority, fineness 0.25 (<0.30) → billon
        spec = [_s("denmark-numismaster-1", "silver", fineness=0.25),
                _s("dk-bruun-2", "billon", fineness=0.25)]
        self.assertEqual(_consensus(spec, SB), "billon")

    def test_mid_band_no_precise_billon(self):
        # 0.30-0.40 band, no precise source → billon (refinement default)
        spec = [_s("denmark-numismaster-1", "silver", fineness=0.35),
                _s("kmk-2", "billon", fineness=0.35)]
        self.assertEqual(_consensus(spec, SB), "billon")


class TestAuthorityWeighting(unittest.TestCase):
    def test_hede_outweighs_numista(self):
        # Hede (5) silver vs Numista (2) billon, mid-band fineness → Hede silver
        spec = [_s("dk-hede-1", "silver", fineness=0.343),
                _s("dk-numista-2", "billon", fineness=0.343)]
        self.assertEqual(_consensus(spec, SB), "silver")

    def test_loose_silver_cannot_override_precise_billon(self):
        # bruun+numista billon (precise, weight 6) vs numismaster+ucoin silver
        # (loose, weight 2) → billon, even with no fineness
        spec = [_s("dk-bruun-1", "billon"), _s("dk-numista-2", "billon"),
                _s("denmark-numismaster-3", "silver"), _s("dk-tid-4", "silver")]
        self.assertEqual(_consensus(spec, SB), "billon")


if __name__ == "__main__":
    unittest.main(verbosity=2)
