"""Regression test for the `_curation_holds` measurement-freeze union in
`absorb_seeds_into_final_v2._enrich_final_entry`.

Bug (2026-07-12, coins unified-dk-hede-f2h7g / unified-dk-bruun-3839): a coin
whose foundation carries a SCALAR fineness anchor (curator hold, verified:false,
no source) got a schema-INVALID mixed list `[0.77, {value:0.77, source:"hede"}]`.
`_collect_field_list` round-trips the foundation scalar into a FieldValue whose
source it SYNTHESISES from the coin id (`_source_label_from_id`); the freeze then
double-counted it (the (value, source) dedup can't collapse a bare scalar with
its own synthesised FieldValue). The fix drops the round-trip and keeps a scalar
hold verbatim, unioning only genuinely-new peer values.

Run: .venv/bin/python scripts/maintenance/test_absorb_fineness_freeze.py
"""
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(_HERE))  # scripts/

from maintenance.absorb_seeds_into_final_v2 import _enrich_final_entry


def _coin(**kw):
    base = dict(id="unified-dk-hede-testcoin", nominal="1 Goldgulden", metal="gold",
                fuss="seed_unsorted", phase="hede", kind="kurant",
                composed_of=["unified-dk-hede-testcoin"], issuing_entity="danish_realm")
    base.update(kw)
    return base


def test_scalar_fineness_hold_stays_scalar():
    # Foundation-only re-derive: the scalar anchor 0.77 is re-synthesised by
    # _collect_field_list as {value:0.77, source:"hede"} (source from the id).
    # The freeze must recognise the round-trip and keep the hold SCALAR — not
    # emit the schema-invalid [0.77, {value:0.77, source:"hede"}].
    fe = _coin(fineness=0.77, fineness_verified=False,
               _curation_holds={"fineness": "canonical anchor, no source attests it (§4)"})
    out, _ = _enrich_final_entry(fe, [fe], "danish_realm")
    assert out["fineness"] == 0.77, f"expected scalar 0.77, got {out['fineness']!r}"


def test_scalar_hold_unions_genuine_peer_value():
    # A genuinely-different peer reading (different value + real source) DOES
    # union in — as a homogeneous FieldValue list (scalar hold normalised).
    fe = _coin(id="unified-dk-hede-testcoin2",
               composed_of=["unified-dk-hede-testcoin2", "unified-dk-bruun-9999"],
               fineness=0.875, fineness_verified=False,
               _curation_holds={"fineness": "anchor"})
    peer = {"id": "unified-dk-bruun-9999", "nominal": "1 Goldgulden", "metal": "gold",
            "fineness": [{"value": 0.870, "source": "bruun"}]}
    out, _ = _enrich_final_entry(fe, [fe, peer], "danish_realm")
    fin = out["fineness"]
    assert isinstance(fin, list) and all(isinstance(e, dict) for e in fin), \
        f"must be a homogeneous FieldValue list, got {fin!r}"
    assert sorted(e["value"] for e in fin) == [0.870, 0.875], f"both values kept: {fin!r}"


if __name__ == "__main__":
    test_scalar_fineness_hold_stays_scalar()
    test_scalar_hold_unions_genuine_peer_value()
    print("absorb fineness-freeze tests passed ✓")
