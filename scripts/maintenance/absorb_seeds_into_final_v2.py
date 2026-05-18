#!/usr/bin/env python3
"""V2 Phase 4 — absorb seed_unified entries into existing V2 final foundation.

Input  : data/v2/seed_unified/<entity>.yml  (cross-source merged per coin)
         data/v2/final/<entity>.yml          (V1-bootstrap foundation, frozen
                                              per D3 except for additive
                                              enrichment from this script)
Output : updated data/v2/final/<entity>.yml
         data/v2/classification_decisions/<entity>.yml  (pending genuinely-new
                                                         coins for curator)

For each entry in seed_unified, find a matching entry in final via the
§5.2 match hierarchy (D10). When matched, ENRICH the final entry:
  - Add unified.id to final.composed_of (D9)
  - UNION year_ranges across final + all composed_of members (D19)
  - Multi-source merge of weight_rough_g / fineness / diameter_mm (D17, §9a)
  - Union sources / mint
  - Accumulate catalog refs to list-form on conflict (D18)
  - OR-merge verification flags (D20)
  - Gap-fill scalar fields when final lacks (D21)

Foundation-immutable fields per DF1 (current default — strict):
  fuss, phase, kind, fraction, nominal, ruler, mintmaster, issuing_entity

If no match found → genuinely new physical coin. Two paths:
  1. Auto-classify via CLAUDE.md §8a (Müntzfuß-disambiguation pipeline) —
     to-be-built; for MVP, surface to classification_decisions/<entity>.yml
     pending list.
  2. Curator declares in classification_decisions/<entity>.yml::assignments
     {coin_id: {fuss, phase, kind}}; on next run, absorb adds the entry
     to final with the declared classification.

The script is IDEMPOTENT (D25):
  - already-absorbed unified entries (in some final.composed_of) skipped
  - re-derived enrichment fields stable across runs given stable input
  - merge_seed write preserves curator edits on final entries

Usage:
  scripts/maintenance/absorb_seeds_into_final_v2.py --dry-run    # report
  scripts/maintenance/absorb_seeds_into_final_v2.py --apply      # write
  scripts/maintenance/absorb_seeds_into_final_v2.py --entity X   # one entity
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
V2_SEED_UNIFIED = ROOT / "data" / "v2" / "seed_unified"
V2_FINAL = ROOT / "data" / "v2" / "final"
V2_CLASSIFICATION_DECISIONS = ROOT / "data" / "v2" / "classification_decisions"

sys.path.insert(0, str(ROOT / "scripts"))
from lib.seed_merge import merge_seed  # noqa: E402

# Reuse match-strategy + enrichment helpers from Phase 3.2.
# Both files share the same data-accumulation conventions (D17-D21).
from maintenance.merge_seeds_cross_source import (  # noqa: E402
    match_pair,
    _collect_field_list,
    _collect_sources,
    _collect_mints,
    _deep_merge_catalog,
    _union_year_ranges,
    _take_first_non_none,
    _or_merge_verified,
)


# ---------------------------------------------------------------------------
# I/O
# ---------------------------------------------------------------------------


def _load_yaml(p: Path) -> dict:
    if not p.exists():
        return {}
    return yaml.safe_load(p.read_text(encoding="utf-8")) or {}


def _ruamel_to_dict(c):
    """ruamel.yaml round-trip types → plain Python (mirrors helpers in
    other V2 scripts so merge_seed-returned CommentedMap entries serialise
    cleanly via pyyaml.dump)."""
    from ruamel.yaml.comments import CommentedMap, CommentedSeq
    from ruamel.yaml.scalarstring import ScalarString
    if isinstance(c, CommentedMap):
        return {str(k): _ruamel_to_dict(v) for k, v in c.items()}
    if isinstance(c, CommentedSeq):
        return [_ruamel_to_dict(v) for v in c]
    if isinstance(c, ScalarString):
        return str(c)
    if isinstance(c, dict):
        return {k: _ruamel_to_dict(v) for k, v in c.items()}
    if isinstance(c, list):
        return [_ruamel_to_dict(v) for v in c]
    return c


def _entities_with_seed_unified() -> list[str]:
    if not V2_SEED_UNIFIED.exists():
        return []
    return sorted(p.stem for p in V2_SEED_UNIFIED.glob("*.yml"))


# ---------------------------------------------------------------------------
# Foundation-immutable rule (per DF1, current default)
# ---------------------------------------------------------------------------

# Fields that NEVER change on an existing final entry. V1 bootstrap set
# these via curator decisions baked into V1; V2 doesn't second-guess
# until DF1 is resolved.
_FOUNDATION_IMMUTABLE_FIELDS = frozenset({
    "fuss", "phase", "kind", "fraction", "nominal",
    "ruler", "mintmaster", "issuing_entity",
})


def _enrich_final_entry(final_entry: dict, members: list[dict],
                        entity_id: str | None) -> tuple[dict, list]:
    """Re-derive enrichment fields on a final entry from itself + members
    listed in composed_of. Foundation-immutable fields stay untouched.

    `members` includes the final entry itself FIRST (highest authority —
    foundation wins on scalar gap-fill) and every composed_of member
    after (from seed_unified). Authority sort within members preserves
    foundation-first ordering.
    """
    conflicts: list = []
    # Foundation-immutable fields: copy from final_entry verbatim
    out = {k: v for k, v in final_entry.items()
           if k in _FOUNDATION_IMMUTABLE_FIELDS}
    out["id"] = final_entry["id"]

    # year_ranges UNION across members (D19)
    union_yr = _union_year_ranges(members)
    if union_yr is not None:
        if len(union_yr) == 1 and union_yr[0][0] == union_yr[0][1]:
            out["year_first"] = union_yr[0][0]
            out["year_last"] = union_yr[0][1]
        else:
            out["year_first"] = min(r[0] for r in union_yr)
            out["year_last"] = max(r[1] for r in union_yr)
            out["year_ranges"] = union_yr
    # year_label — foundation wins (preserves V1 display formatting)
    if final_entry.get("year_label") is not None:
        out["year_label"] = final_entry["year_label"]
    elif "year_first" in out and "year_last" in out:
        out["year_label"] = (str(out["year_first"]) if out["year_first"] == out["year_last"]
                              else f"{out['year_first']}-{out['year_last']}")

    # year_verified OR-merge (any source attests counts)
    yv = _or_merge_verified(members, "year_verified")
    if yv is not None:
        out["year_verified"] = yv

    # mint UNION across members (D17 list-form when multi-mint)
    mint = _collect_mints(members)
    if mint is not None:
        out["mint"] = mint

    # Catalog: accumulate list-form on conflict (D18). Foundation entries
    # come first → their values take authority position in the list.
    cat, cat_conflicts = _deep_merge_catalog(members, entity_id)
    if cat:
        out["catalog"] = cat
    conflicts.extend(cat_conflicts)

    # Metal — foundation wins (gap-fill from unified if final lacks)
    metal = _take_first_non_none(members, "metal")
    if metal:
        out["metal"] = metal

    # Verification flags: OR-merge (D20)
    for field in ("metal_verified", "fineness_verified", "weight_rough_verified",
                  "diameter_mm_verified", "mint_verified", "verified"):
        v = _or_merge_verified(members, field)
        if v is not None:
            out[field] = v

    # Multi-source measurement lists (D17 / §9a)
    fine = _collect_field_list(members, "fineness")
    if fine:
        out["fineness"] = fine
    weights = _collect_field_list(members, "weight_rough_g")
    if weights:
        out["weight_rough_g"] = weights
    diameters = _collect_field_list(members, "diameter_mm")
    if diameters:
        out["diameter_mm"] = diameters

    # Sources union
    sources = _collect_sources(members)
    if sources:
        out["sources"] = sources

    # Inscriptions — gap-fill (foundation primary)
    for field in ("inscription_obv", "inscription_rev", "weight_rough_label"):
        v = _take_first_non_none(members, field)
        if v is not None:
            out[field] = v

    # Note / verification_note — gap-fill from foundation
    for field in ("note", "verification_note"):
        v = _take_first_non_none(members, field)
        if v is not None:
            out[field] = v

    # composed_of: union of final's existing + new members (deterministic order)
    existing_composed = list(final_entry.get("composed_of") or [])
    member_ids = [m["id"] for m in members if m.get("id") and m["id"] != final_entry["id"]]
    composed = sorted(set(existing_composed) | set(member_ids))
    out["composed_of"] = composed

    # Preserve other V2 bookkeeping fields from foundation
    for k in ("v1_home_location", "_migration_note", "_migration_dup_origin_id",
              "promoted_to"):
        if k in final_entry:
            out[k] = final_entry[k]

    return out, conflicts


# ---------------------------------------------------------------------------
# Per-entity processing
# ---------------------------------------------------------------------------


def process_entity(entity_id: str) -> dict:
    """Returns:
      {
        'entity_id': str,
        'unified_total': int,
        'final_total_before': int,
        'final_total_after': int,
        'already_absorbed': int,
        'newly_absorbed': int,
        'genuinely_new': int,
        'unmatched_unified_ids': [...],
        'multi_match_warnings': [{unified_id, candidates}, ...],
        'enrichment_conflicts': [{final_id, members, conflicts}, ...],
        'enriched_final_entries': [...] (dicts ready to write),
      }
    """
    unified_doc = _load_yaml(V2_SEED_UNIFIED / f"{entity_id}.yml")
    unified_entries: list[dict] = unified_doc.get("coins") or []
    unified_by_id = {u["id"]: u for u in unified_entries if u.get("id")}

    final_path = V2_FINAL / f"{entity_id}.yml"
    final_doc = _load_yaml(final_path)
    final_entries: list[dict] = final_doc.get("coins") or []
    final_by_id = {f["id"]: f for f in final_entries if f.get("id")}

    # Build: already-absorbed unified ids (across all final composed_of lists)
    already_absorbed: dict[str, str] = {}
    for fid, fc in final_by_id.items():
        for cid in fc.get("composed_of") or []:
            already_absorbed[cid] = fid

    # Iterate unified entries, find matches in final
    new_links: dict[str, list[str]] = defaultdict(list)
    unmatched: list[str] = []
    multi_match: list[dict] = []
    already_in = 0

    for unified in unified_entries:
        uid = unified.get("id")
        if not uid:
            continue
        if uid in already_absorbed:
            already_in += 1
            continue
        # Find match against final entries (per §5.2 hierarchy)
        candidates = []
        for fid, fc in final_by_id.items():
            result = match_pair(unified, fc, entity_id)
            if result["decision"] == "confident":
                candidates.append(fid)
        if not candidates:
            unmatched.append(uid)
        elif len(candidates) == 1:
            new_links[candidates[0]].append(uid)
        else:
            # Multi-match — ambiguous; flag for review, link to first
            new_links[candidates[0]].append(uid)
            multi_match.append({"unified_id": uid, "candidates": candidates})

    # Re-derive enrichment on each final entry whose composed_of CHANGED
    # OR re-derive on all (idempotent — same output for stable input).
    # We choose «re-derive on all» so the data-accumulation invariant is
    # always enforced fresh: every final's multi-source lists reflect
    # the current composed_of state without growing or shrinking
    # accidentally.
    enriched_entries: list[dict] = []
    enrichment_conflicts: list[dict] = []
    for fid, fc in final_by_id.items():
        # Compose member list: final itself (foundation, top priority) +
        # any unified entries in composed_of (after new links applied)
        full_composed = sorted(set(fc.get("composed_of") or []) | set(new_links.get(fid, [])))
        members = [fc]
        for mid in full_composed:
            if mid in unified_by_id:
                members.append(unified_by_id[mid])
        enriched, conflicts = _enrich_final_entry(fc, members, entity_id)
        enriched_entries.append(enriched)
        if conflicts:
            enrichment_conflicts.append({
                "final_id": fid,
                "members": full_composed,
                "conflicts": [
                    {"field": f, "foundation_value": t, "absorbed_value": o}
                    for f, t, o in conflicts
                ],
            })

    return {
        "entity_id": entity_id,
        "unified_total": len(unified_entries),
        "final_total_before": len(final_entries),
        "final_total_after": len(enriched_entries),
        "already_absorbed": already_in,
        "newly_absorbed": sum(len(v) for v in new_links.values()),
        "genuinely_new": len(unmatched),
        "unmatched_unified_ids": unmatched,
        "multi_match_warnings": multi_match,
        "enrichment_conflicts": enrichment_conflicts,
        "enriched_final_entries": enriched_entries,
    }


# ---------------------------------------------------------------------------
# Output writers
# ---------------------------------------------------------------------------


def _emit_final_yaml(entity_id: str, coins: list[dict],
                     prior_doc: dict | None) -> str:
    """Render `data/v2/final/<entity>.yml`. Preserve prior doc-level
    metadata (id, source_locations, migrated_from_v1, …) while replacing
    the coins[] list with the re-derived enriched entries."""
    payload = {
        "id": entity_id,
        "source_locations": (prior_doc or {}).get("source_locations") or [],
        "migrated_from_v1": (prior_doc or {}).get("migrated_from_v1") or "",
        "coins": coins,
    }
    return yaml.dump(payload, sort_keys=False, allow_unicode=True,
                     default_flow_style=False, width=120)


def _emit_classification_decisions(entity_id: str, unmatched_ids: list[str],
                                    multi_match: list[dict]) -> str:
    today = date.today().isoformat()
    header = (
        f"# Classification decisions for entity `{entity_id}` (Phase 4).\n"
        f"# Curator-authoritative file (committed). Two sections:\n"
        f"#\n"
        f"# 1. `assignments:` — explicit fuss/phase for ambiguous coins.\n"
        f"#    Each entry adds a NEW final entry on next absorb run.\n"
        f"#    Example:\n"
        f"#      assignments:\n"
        f"#        - coin_id: unified-dk-numismaster-12345\n"
        f"#          fuss: 9_25_thaler\n"
        f"#          phase: A\n"
        f"#          kind: kurant\n"
        f"#          reason: 'specimen Δ ambiguous; per Hede assignment'\n"
        f"#\n"
        f"# 2. `pending:` — auto-populated diagnostic list of unified\n"
        f"#    entries with no match in current final. Curator either:\n"
        f"#    moves an entry to `assignments:` with classification,\n"
        f"#    OR fixes the matcher rules so the coin gets absorbed,\n"
        f"#    OR confirms it's a genuinely new coin needing addition\n"
        f"#    (will be auto-routed by §8a once that's built).\n"
        f"#\n"
        f"# This file is REGENERATED on every absorb run for the\n"
        f"# `pending:` section; existing `assignments:` entries are\n"
        f"# preserved.\n\n"
    )
    # Try to preserve existing assignments
    existing = _load_yaml(V2_CLASSIFICATION_DECISIONS / f"{entity_id}.yml")
    existing_assignments = existing.get("assignments") or []
    payload = {
        "entity_id": entity_id,
        "generated_at": today,
        "assignments": existing_assignments,
        "pending": [{"unified_id": uid, "status": "no_match_in_final"}
                     for uid in unmatched_ids],
        "multi_match_warnings": multi_match,
    }
    return header + yaml.dump(payload, sort_keys=False, allow_unicode=True,
                              default_flow_style=False, width=120)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", default=True,
                        help="Report only — do NOT write outputs (default)")
    parser.add_argument("--apply", action="store_true",
                        help="Write data/v2/final/ + data/v2/classification_decisions/")
    parser.add_argument("--entity", help="Process only this entity")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()
    if args.apply:
        args.dry_run = False

    entities = [args.entity] if args.entity else _entities_with_seed_unified()
    if not entities:
        print("No V2 seed_unified files found.")
        return 0

    print(f"Processing {len(entities)} entit(y/ies)...\n")

    totals = Counter()
    for ent in entities:
        result = process_entity(ent)
        totals["unified_total"] += result["unified_total"]
        totals["final_total_after"] += result["final_total_after"]
        totals["already_absorbed"] += result["already_absorbed"]
        totals["newly_absorbed"] += result["newly_absorbed"]
        totals["genuinely_new"] += result["genuinely_new"]
        totals["multi_match"] += len(result["multi_match_warnings"])
        totals["enrichment_conflicts"] += len(result["enrichment_conflicts"])

        line = (
            f"{ent:36s}  "
            f"unified:{result['unified_total']:4d}  "
            f"final:{result['final_total_before']:>4d}→{result['final_total_after']:>4d}  "
            f"abs(prev):{result['already_absorbed']:3d}  "
            f"abs(new):{result['newly_absorbed']:3d}  "
            f"new_coins:{result['genuinely_new']:3d}"
        )
        if result["multi_match_warnings"]:
            line += f"  multi:{len(result['multi_match_warnings'])}"
        if result["enrichment_conflicts"]:
            line += f"  conflicts:{len(result['enrichment_conflicts'])}"
        print(line)

        if args.verbose and result["unmatched_unified_ids"]:
            print(f"    pending (no match in final):")
            for uid in result["unmatched_unified_ids"][:5]:
                print(f"      • {uid}")
            if len(result["unmatched_unified_ids"]) > 5:
                print(f"      • ... and {len(result['unmatched_unified_ids']) - 5} more")

        if args.apply:
            # Write enriched final yaml directly (not via merge_seed):
            # `_enrich_final_entry` already preserves V1-foundation
            # immutable fields verbatim from each existing final entry,
            # so the enriched list IS the canonical state. Going through
            # merge_seed would re-trigger CURATED_FIELDS preservation —
            # which would block composed_of updates (existing empty list
            # is treated as «present» and wins over the fresh non-empty
            # list per the «existing wins when present» rule). Direct
            # write is correct here because we read+enrich every existing
            # entry — no orphan curator data possible.
            V2_FINAL.mkdir(parents=True, exist_ok=True)
            final_path = V2_FINAL / f"{ent}.yml"
            prior_doc = _load_yaml(final_path)
            final_path.write_text(
                _emit_final_yaml(ent, result["enriched_final_entries"],
                                  prior_doc),
                encoding="utf-8",
            )

            # Write classification_decisions pending list (always — regenerated)
            if result["unmatched_unified_ids"] or result["multi_match_warnings"]:
                V2_CLASSIFICATION_DECISIONS.mkdir(parents=True, exist_ok=True)
                (V2_CLASSIFICATION_DECISIONS / f"{ent}.yml").write_text(
                    _emit_classification_decisions(
                        ent,
                        result["unmatched_unified_ids"],
                        result["multi_match_warnings"],
                    ),
                    encoding="utf-8",
                )

    print()
    print(f"=== Totals ===")
    print(f"  Unified entries total:           {totals['unified_total']:>5d}")
    print(f"  Final entries after run:         {totals['final_total_after']:>5d}")
    print(f"  Already absorbed (prev runs):    {totals['already_absorbed']:>5d}")
    print(f"  Newly absorbed this run:         {totals['newly_absorbed']:>5d}")
    print(f"  Genuinely new (pending):         {totals['genuinely_new']:>5d}")
    print(f"  Multi-match warnings:            {totals['multi_match']:>5d}")
    print(f"  Enrichment conflicts (logged):   {totals['enrichment_conflicts']:>5d}")

    if args.dry_run:
        print("\n--- DRY RUN — no files written. Re-run with --apply to commit. ---")
    else:
        print(f"\n✓ Wrote enriched final yamls to {V2_FINAL}/")

    return 0


if __name__ == "__main__":
    sys.exit(main())
