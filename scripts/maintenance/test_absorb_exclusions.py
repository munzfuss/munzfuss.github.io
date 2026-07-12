"""Unit tests for the curator per-coin exclusion mechanism in
`absorb_seeds_into_final_v2` (data/v2/exclusions/<entity>.yml).

Guards the 2026-07-12 mechanism: a coin the curator lists is dropped from final
(never renders in seed_unsorted) when its OWN unified id OR any composed_of
member resolves to an excluded seed id; the seed survives for provenance.

Run: .venv/bin/python scripts/maintenance/test_absorb_exclusions.py
"""
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(_HERE))  # scripts/

from maintenance.absorb_seeds_into_final_v2 import _coin_exclusion_hit, _load_exclusions


def test_hit_by_own_id():
    ex = {"kmk-122102"}
    assert _coin_exclusion_hit({"id": "unified-kmk-122102",
                                "composed_of": ["unified-kmk-122102"]}, ex) == {"kmk-122102"}


def test_hit_by_composed_of_member():
    # excluded seed folded into a multi-member coin still matches
    ex = {"kmk-999"}
    hit = _coin_exclusion_hit({"id": "unified-dk-hede-x",
                               "composed_of": ["unified-dk-hede-x", "unified-kmk-999"]}, ex)
    assert hit == {"kmk-999"}


def test_no_hit():
    ex = {"kmk-122102"}
    assert _coin_exclusion_hit({"id": "unified-dk-bruun-3831",
                                "composed_of": ["unified-dk-bruun-3831"]}, ex) == set()


def test_empty_exclusions_never_hits():
    assert _coin_exclusion_hit({"id": "unified-kmk-122102"}, set()) == set()


def test_load_danish_realm_exclusions():
    # the shipped danish_realm file lists the two 2026-07-12 exclusions
    ex = _load_exclusions("danish_realm")
    assert "kmk-122102" in ex and ex["kmk-122102"]["category"] == "pattern"
    assert "kmk-354200" in ex and ex["kmk-354200"]["category"] == "undocumented_stub"


def test_load_missing_entity_is_empty():
    assert _load_exclusions("no_such_entity_zzz") == {}


if __name__ == "__main__":
    test_hit_by_own_id()
    test_hit_by_composed_of_member()
    test_no_hit()
    test_empty_exclusions_never_hits()
    test_load_danish_realm_exclusions()
    test_load_missing_entity_is_empty()
    print("absorb exclusion tests passed ✓")
