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


def test_weight_only_borrows_highest_authority_fineness():
    # c3h2 (2 Goldgulden): kmk publishes weight only; finenesses are
    # [.968 numista FIRST-listed, .986 hede]. The weight-only kmk must borrow
    # the HIGHEST-authority fineness (.986 hede/danskmoent), NOT the arbitrary
    # first-listed .968 — so no source latches onto the stray numista reading.
    cc = compute._compute_coin(_coin(
        weights=[{"value": 6.98, "source": "kmk"},
                 {"value": 6.981, "source": "hede"},
                 {"value": 6.981, "source": "numista"}],
        finenesses=[{"value": 0.968, "source": "numista"},
                    {"value": 0.986, "source": "hede"}],
    ), _fuss())
    g = _groups(cc)
    assert 6.88228 in g, f"kmk must use .986 (6.98x.986): {sorted(g)}"
    assert 6.75664 not in g, f"kmk must NOT borrow stray .968: {sorted(g)}"
    assert 6.75761 in g, f"numista OWN .968 reading must stay: {sorted(g)}"
    assert "hede" in g[6.88228] and "kmk" in g[6.88228], g[6.88228]


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


# ---- N/Marck columns (stop_rough / stop_fine), fraction-normalised ----
def test_stop_groups_single_reading():
    # single reading, fraction 1 (default): N = grid_unit_g / weight
    cc = compute._compute_coin(_coin(
        weights=[{"value": 3.44, "source": "hede"}],
        finenesses=[{"value": 0.986, "source": "hede"}],
    ), _fuss())
    assert len(cc.stop_rough_groups) == 1
    assert cc.stop_rough_groups[0].value == round(233.856 / 3.44, 2)          # 67.98
    # fine N from weight_fein (3.44 × .986 = 3.39184)
    assert cc.stop_fine_groups[0].value == round(233.856 / 3.39184, 2)        # 68.95
    assert cc.stop_rough_groups[0].display_decimals == 2


def test_stop_fraction_normalised():
    # fraction 2 → N normalised by k: grid_unit_g / (weight / 2) → ~16.76
    coin = Coin.model_validate({
        "id": "t2n", "fuss": "test", "phase": "A", "kind": "kurant",
        "nominal": "2 Nobel", "year_label": "1502", "year_first": 1502,
        "fraction": "2",
        "weight_rough_g": [{"value": 27.90, "source": "hede"}],
        "fineness": [{"value": 0.979, "source": "hede"}],
    })
    cc = compute._compute_coin(coin, _fuss())
    assert cc.stop_rough_groups[0].value == round(233.856 / (27.90 / 2), 2)   # 16.76


def test_stop_msr_segs_per_specimen():
    # two weights, one fineness → msr_n == 2, one N seg per specimen; the seg
    # values transform the weight, and `anchor` carries the weight source so
    # per-specimen markers propagate exactly as on the weight columns.
    cc = compute._compute_coin(_coin(
        weights=[{"value": 14.75, "source": "bruun"},
                 {"value": 14.67, "source": "galster"}],
        finenesses=[{"value": 0.979, "source": "hede"}],
    ), _fuss())
    assert cc.msr_n == 2
    want = sorted([round(233.856 / 14.75, 2), round(233.856 / 14.67, 2)])     # 15.85, 15.94
    got = sorted(round(s["value"], 2) for s in cc.msr_stop_rough_segs)
    assert got == want, got
    anchors = {a for s in cc.msr_stop_rough_segs for a in s["anchor"]}
    assert {"bruun", "galster"} <= anchors, anchors
    # fine segs exist and transform the fein weight
    assert len(cc.msr_stop_fine_segs) == 2, cc.msr_stop_fine_segs


if __name__ == "__main__":
    test_own_pair_no_cross_mix()
    test_tooltip_own_pair_single_source()
    test_tooltip_weight_only_names_both_sources()
    test_weight_only_borrows_highest_authority_fineness()
    test_single_source_scalar_unchanged()
    test_per_phase_soll_target()
    test_unknown_phase_falls_back_to_scalar_soll()
    test_stop_groups_single_reading()
    test_stop_fraction_normalised()
    test_stop_msr_segs_per_specimen()
    print("all pairing + per-phase-soll + N/Marck tests passed ✓")
