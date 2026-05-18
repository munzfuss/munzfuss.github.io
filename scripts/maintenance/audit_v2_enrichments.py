#!/usr/bin/env python3
"""V2 enrichment audit — report what Phase 4 absorb has added to the
V1-bootstrap foundation, where pending unified entries sit, and which
matcher-gap patterns surface most.

Read-only: never writes anything. Run anytime to see the state of
V1↔V2 enrichment without changing data.

Output sections:

  1. Per-entity coverage:
     - V1-foundation entry count
     - How many have ≥1 composed_of link (= enriched by absorb)
     - How many unified entries map into each entity's final
     - How many remain «pending» (no match in foundation)

  2. Enrichment-field deltas:
     For entries with composed_of populated, count how many gained:
     - multi-source weight_rough_g (≥2 readings)
     - multi-source fineness
     - multi-source diameter_mm
     - new catalog refs (list-form additions)
     - mint union (list-form when foundation had scalar)

  3. Pending breakdown:
     Top reasons unified entries don't match foundation. Probe
     pending unified entries' catalog refs + mint + year to surface
     «what's distinctive about these vs foundation».

  4. Diff vs V1:
     V2 final vs V1 curated (data/locations/<loc>.yml) — coin count
     per location-equivalent + key field delta sample.

Usage:
  scripts/maintenance/audit_v2_enrichments.py
  scripts/maintenance/audit_v2_enrichments.py --entity danish_realm
  scripts/maintenance/audit_v2_enrichments.py --json report.json
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
V2_FINAL = ROOT / "data" / "v2" / "final"
V2_SEED_UNIFIED = ROOT / "data" / "v2" / "seed_unified"
V2_CLASSIFICATION_DECISIONS = ROOT / "data" / "v2" / "classification_decisions"
V1_LOCATIONS = ROOT / "data" / "locations"


def _load_yaml(p: Path) -> dict:
    if not p.exists():
        return {}
    return yaml.safe_load(p.read_text(encoding="utf-8")) or {}


def _list_form_count(value) -> int:
    """Number of entries in a list-form field; 0 for scalar/None/empty."""
    if value is None:
        return 0
    if isinstance(value, list):
        return len(value)
    return 1


def _catalog_ref_count(catalog: dict | None) -> int:
    """How many distinct catalog references present (counting list items)."""
    if not catalog:
        return 0
    n = 0
    for k, v in catalog.items():
        if v is None:
            continue
        if isinstance(v, list):
            n += len(v)
        elif isinstance(v, dict):
            n += len(v)
        else:
            n += 1
    return n


def audit_entity(entity_id: str) -> dict:
    final_doc = _load_yaml(V2_FINAL / f"{entity_id}.yml")
    final_entries = final_doc.get("coins") or []

    unified_doc = _load_yaml(V2_SEED_UNIFIED / f"{entity_id}.yml")
    unified_entries = unified_doc.get("coins") or []
    unified_by_id = {u.get("id"): u for u in unified_entries if u.get("id")}

    decisions_doc = _load_yaml(V2_CLASSIFICATION_DECISIONS / f"{entity_id}.yml")
    pending = decisions_doc.get("pending") or []
    assignments = decisions_doc.get("assignments") or []
    multi_match = decisions_doc.get("multi_match_warnings") or []

    # Per-entry analytics
    n_final = len(final_entries)
    n_with_composed_of = 0
    n_multi_source_weight = 0
    n_multi_source_fineness = 0
    n_multi_source_diameter = 0
    n_multi_mint = 0
    n_v1_foundation = 0  # entries with v1_home_location set
    composed_of_sizes: Counter = Counter()
    sample_enriched: list[dict] = []

    for c in final_entries:
        composed = c.get("composed_of") or []
        if composed:
            n_with_composed_of += 1
            composed_of_sizes[len(composed)] += 1
            if len(sample_enriched) < 3:
                sample_enriched.append({
                    "id": c.get("id"),
                    "composed_of": composed,
                    "weight_readings": _list_form_count(c.get("weight_rough_g")),
                    "fineness_readings": _list_form_count(c.get("fineness")),
                    "sources": _list_form_count(c.get("sources")),
                    "catalog_refs": _catalog_ref_count(c.get("catalog")),
                })
        if _list_form_count(c.get("weight_rough_g")) >= 2:
            n_multi_source_weight += 1
        if _list_form_count(c.get("fineness")) >= 2:
            n_multi_source_fineness += 1
        if _list_form_count(c.get("diameter_mm")) >= 2:
            n_multi_source_diameter += 1
        if isinstance(c.get("mint"), list) and len(c["mint"]) >= 2:
            n_multi_mint += 1
        if c.get("v1_home_location"):
            n_v1_foundation += 1

    n_unified = len(unified_entries)
    n_absorbed = sum(
        1 for u in unified_entries
        if any(u["id"] in (f.get("composed_of") or []) for f in final_entries)
    )
    n_pending = len(pending)

    return {
        "entity_id": entity_id,
        "v1_foundation": n_v1_foundation,
        "final_total": n_final,
        "added_post_bootstrap": n_final - n_v1_foundation,
        "unified_total": n_unified,
        "unified_absorbed": n_absorbed,
        "unified_pending": n_pending,
        "enriched_with_composed_of": n_with_composed_of,
        "multi_source_weight": n_multi_source_weight,
        "multi_source_fineness": n_multi_source_fineness,
        "multi_source_diameter": n_multi_source_diameter,
        "multi_mint": n_multi_mint,
        "composed_of_size_distribution": dict(composed_of_sizes.most_common()),
        "classification_assignments": len(assignments),
        "multi_match_warnings": len(multi_match),
        "sample_enriched_entries": sample_enriched,
    }


def cross_v1_v2_coin_counts() -> dict:
    """V1 vs V2 coin counts per location-equivalent. Quick «did we lose
    anything obvious» check."""
    v1_counts: dict[str, int] = {}
    for p in sorted(V1_LOCATIONS.glob("*.yml")):
        if p.stem.endswith("-references"):
            continue
        d = _load_yaml(p)
        v1_counts[p.stem] = len(d.get("coins") or [])

    v2_counts: dict[str, int] = {}
    if V2_FINAL.exists():
        for p in sorted(V2_FINAL.glob("*.yml")):
            d = _load_yaml(p)
            v2_counts[p.stem] = len(d.get("coins") or [])

    return {"v1_per_location": v1_counts, "v2_per_entity": v2_counts}


def _all_entities() -> list[str]:
    if not V2_FINAL.exists():
        return []
    return sorted(p.stem for p in V2_FINAL.glob("*.yml"))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--entity", help="Audit only this entity")
    parser.add_argument("--json", type=Path, default=None,
                        help="Write machine-readable JSON report to this path")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    entities = [args.entity] if args.entity else _all_entities()
    if not entities:
        print("No V2 final files found.")
        return 0

    per_entity: dict[str, dict] = {}
    totals = Counter()
    for ent in entities:
        result = audit_entity(ent)
        per_entity[ent] = result
        for k, v in result.items():
            if isinstance(v, int):
                totals[k] += v

    cross = cross_v1_v2_coin_counts()

    # ------------------------------------------------------------------
    # Section 1: per-entity coverage
    # ------------------------------------------------------------------
    print("=" * 90)
    print("V2 enrichment audit — per-entity coverage")
    print("=" * 90)
    print(f"{'entity':32s} {'v1-found':>9s} {'+added':>7s} {'unified':>8s} "
          f"{'absorbed':>9s} {'pending':>8s} {'enriched':>9s}")
    print("-" * 90)
    for ent in entities:
        r = per_entity[ent]
        print(f"{ent:32s} {r['v1_foundation']:>9d} {r['added_post_bootstrap']:>7d} "
              f"{r['unified_total']:>8d} {r['unified_absorbed']:>9d} "
              f"{r['unified_pending']:>8d} {r['enriched_with_composed_of']:>9d}")

    print(f"\n  «v1-found» = entries inherited from V1 bootstrap "
          f"(have v1_home_location set)")
    print(f"  «+added»   = entries added post-bootstrap")
    print(f"  «unified»  = total seed_unified entries for this entity")
    print(f"  «absorbed» = unified entries linked into some final.composed_of")
    print(f"  «pending»  = unified entries waiting for classification decision")
    print(f"  «enriched» = final entries with non-empty composed_of")

    # ------------------------------------------------------------------
    # Section 2: enrichment-field deltas
    # ------------------------------------------------------------------
    print()
    print("=" * 90)
    print("Enrichment-field accumulation (D17-D21)")
    print("=" * 90)
    print(f"{'entity':32s} {'multi-src':>10s} {'multi-fine':>11s} "
          f"{'multi-diam':>11s} {'multi-mint':>11s}")
    print(f"{'':32s} {'weight':>10s} {'':>11s} {'':>11s} {'':>11s}")
    print("-" * 90)
    for ent in entities:
        r = per_entity[ent]
        print(f"{ent:32s} {r['multi_source_weight']:>10d} "
              f"{r['multi_source_fineness']:>11d} "
              f"{r['multi_source_diameter']:>11d} "
              f"{r['multi_mint']:>11d}")

    # ------------------------------------------------------------------
    # Section 3: V1 vs V2 cross-counts
    # ------------------------------------------------------------------
    print()
    print("=" * 90)
    print("V1 location yamls vs V2 final entity yamls (coin counts)")
    print("=" * 90)
    v1_total = sum(cross["v1_per_location"].values())
    v2_total = sum(cross["v2_per_entity"].values())
    print(f"V1 total coins (across all data/locations/*.yml):  {v1_total}")
    print(f"V2 total coins (across all data/v2/final/*.yml):   {v2_total}")
    print(f"Δ (V2 − V1):  {v2_total - v1_total:+d}")
    print()
    print(f"  V1 per location: " + ", ".join(
        f"{k}={v}" for k, v in sorted(cross["v1_per_location"].items())
    ))
    print(f"  V2 per entity:  " + ", ".join(
        f"{k}={v}" for k, v in sorted(cross["v2_per_entity"].items())
    ))

    # ------------------------------------------------------------------
    # Section 4: sample enriched entries
    # ------------------------------------------------------------------
    if args.verbose:
        print()
        print("=" * 90)
        print("Sample enriched final entries (per entity)")
        print("=" * 90)
        for ent in entities:
            r = per_entity[ent]
            samples = r.get("sample_enriched_entries", [])
            if samples:
                print(f"\n{ent}:")
                for s in samples:
                    print(f"  {s['id']}")
                    print(f"    composed_of: {s['composed_of']}")
                    print(f"    multi-source readings: weight={s['weight_readings']}, "
                          f"fineness={s['fineness_readings']}, "
                          f"sources={s['sources']}, "
                          f"catalog_refs={s['catalog_refs']}")

    # ------------------------------------------------------------------
    # Totals
    # ------------------------------------------------------------------
    print()
    print("=" * 90)
    print("Aggregate totals (across all entities)")
    print("=" * 90)
    print(f"  V1 foundation entries:                  {totals['v1_foundation']:>5d}")
    print(f"  Final entries after V2 pipeline:        {totals['final_total']:>5d}")
    print(f"  Unified seed entries total:             {totals['unified_total']:>5d}")
    print(f"  Unified entries absorbed into final:    {totals['unified_absorbed']:>5d}")
    print(f"  Unified entries pending classification: {totals['unified_pending']:>5d}")
    print(f"  Final entries with composed_of links:   {totals['enriched_with_composed_of']:>5d}")
    print(f"  Final entries with multi-source weight: {totals['multi_source_weight']:>5d}")
    print(f"  Final entries with multi-source fineness:{totals['multi_source_fineness']:>4d}")
    print(f"  Multi-match warnings (unified→final ambig):{totals['multi_match_warnings']:>3d}")

    if args.json:
        payload = {
            "per_entity": per_entity,
            "totals": dict(totals),
            "cross_v1_v2": cross,
        }
        args.json.write_text(json.dumps(payload, ensure_ascii=False, indent=2))
        print(f"\nJSON report → {args.json}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
