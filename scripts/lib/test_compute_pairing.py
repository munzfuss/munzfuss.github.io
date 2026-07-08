"""Unit tests for compute.py source-coherent (weight, fineness) pairing.

Guards the Phase-1 fix (2026-07): a weight source that publishes its OWN
fineness pairs with THAT fineness — never cross-mixed with another
source's — so no spurious extra Feingewicht surfaces; and a weight-only
source's derived Feingewicht tooltip names BOTH the weight source and the
fallback fineness source it actually used.

Regression case: Hede c3h14 «1 Rhinsk Gylden» (galster weight 3.19 + own
fineness .764; hede weight 3.278 + own fineness .75; bruun/numista weight
only). The old naive weight[0]×fineness[0] primary produced a spurious
galster-weight × hede-fineness = 2.3925.

Run: .venv/bin/python scripts/lib/test_compute_pairing.py
"""
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(_HERE))  # scripts/

from lib import compute  # noqa: E402
from lib.schema import Coin, Fuss  # noqa: E402


def _fuss():
    return Fuss.model_validate({
        "name": {"de": "T", "en": "T", "uk": "T"},
        "metal": "gold",
        "grid_unit_g": 233.856,
        "grid_stops": 72,
        "fineness_standard": 0.75,
        "fractions": {},
    })


def _coin(weights, finenesses):
    return Coin.model_validate({
        "id": "test-c3h14",
        "fuss": "test",
        "phase": "A",
        "kind": "kurant",
        "nominal": "1 Rhinsk Gylden",
        "year_label": "1536",
        "year_first": 1536,
        "weight_rough_g": weights,
        "fineness": finenesses,
    })


def _groups(cc):
    return {round(g.value, 5): " / ".join(g.sources) for g in cc.weight_fein_groups}


def test_own_pair_no_cross_mix():
    cc = compute._compute_coin(_coin(
        weights=[{"value": 3.19, "source": "galster"},
                 {"value": 3.23, "source": "numista"},
                 {"value": 3.278, "source": "hede"},
                 {"value": 3.37, "source": "bruun"}],
        finenesses=[{"value": 0.75, "source": "hede"},
                    {"value": 0.764, "source": "galster"}],
    ), _fuss())
    g = _groups(cc)
    assert 2.3925 not in g, f"spurious galster-w × hede-f present: {sorted(g)}"
    assert 2.43716 in g, sorted(g)   # galster own-pair 3.19 × .764
    assert 2.4585 in g, sorted(g)    # hede own-pair 3.278 × .75
    assert 2.4225 in g, sorted(g)    # numista weight × fallback .75
    assert 2.5275 in g, sorted(g)    # bruun weight × fallback .75
    assert len(g) == 4, f"expected 4 values, got {sorted(g)}"


def test_tooltip_own_pair_single_source():
    cc = compute._compute_coin(_coin(
        weights=[{"value": 3.19, "source": "galster"},
                 {"value": 3.278, "source": "hede"}],
        finenesses=[{"value": 0.75, "source": "hede"},
                    {"value": 0.764, "source": "galster"}],
    ), _fuss())
    g = _groups(cc)
    assert "вагою × пробою з" in g[2.43716], g[2.43716]
    assert "galster" in g[2.43716]


def test_tooltip_weight_only_names_both_sources():
    cc = compute._compute_coin(_coin(
        weights=[{"value": 3.278, "source": "hede"},
                 {"value": 3.37, "source": "bruun"}],
        finenesses=[{"value": 0.75, "source": "hede"}],
    ), _fuss())
    g = _groups(cc)
    tip = g[2.5275]                       # bruun 3.37 × fallback .75 (hede)
    assert "bruun" in tip and "hede" in tip, f"must name both: {tip!r}"
    assert "з пробою з" in tip, tip


def test_single_source_scalar_unchanged():
    # a plain single-source coin still computes one own-pair value
    cc = compute._compute_coin(_coin(
        weights=[{"value": 3.44, "source": "hede"}],
        finenesses=[{"value": 0.986, "source": "hede"}],
    ), _fuss())
    g = _groups(cc)
    assert len(g) == 1 and 3.39184 in g, sorted(g)


# ---- per-phase soll target (rhinsk-style phase-varying de-jure fineness) ----
def _fuss_phased():
    return Fuss.model_validate({
        "name": {"de": "T", "en": "T", "uk": "T"},
        "metal": "gold",
        "grid_unit_g": 233.856,
        "grid_stops": 72,
        "fineness_standard": 0.77,
        "fractions": {"1": {"soll_rau_g": 3.248, "soll_fein_g": 2.501,
                            "soll_fein_by_phase": {"0": 2.436, "I": 2.501, "II": 2.469}}},
    })


def _phased_coin(phase):
    return Coin.model_validate({
        "id": f"test-ph-{phase}", "fuss": "test", "phase": phase, "kind": "kurant",
        "nominal": "1 Rhinsk Gylden", "year_label": "1536", "year_first": 1536,
        "fraction": "1",
        "weight_rough_g": [{"value": 3.248, "source": "hede"}],
        "fineness": [{"value": 0.75, "source": "hede"}],
    })


def test_per_phase_soll_target():
    assert compute._compute_coin(_phased_coin("0"), _fuss_phased()).soll_fein_g == 2.436
    assert compute._compute_coin(_phased_coin("I"), _fuss_phased()).soll_fein_g == 2.501
    assert compute._compute_coin(_phased_coin("II"), _fuss_phased()).soll_fein_g == 2.469


def test_unknown_phase_falls_back_to_scalar_soll():
    # a phase absent from soll_fein_by_phase → the scalar soll_fein_g
    assert compute._compute_coin(_phased_coin("Z"), _fuss_phased()).soll_fein_g == 2.501


if __name__ == "__main__":
    test_own_pair_no_cross_mix()
    test_tooltip_own_pair_single_source()
    test_tooltip_weight_only_names_both_sources()
    test_single_source_scalar_unchanged()
    test_per_phase_soll_target()
    test_unknown_phase_falls_back_to_scalar_soll()
    print("all pairing + per-phase-soll tests passed ✓")
