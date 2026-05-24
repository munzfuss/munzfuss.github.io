"""Re-route orphan unified-X final entries into matching foundations.

CAUSE: bulk_promote_pending mode auto-promotes unified entries to
standalone final entries when match_pair (at promotion time) returns
no_match. Subsequent matcher improvements (D32 weight-tier-1, D40
no_match_primary_disagrees, +catalog-overlap tolerance refinements)
may make the same pair NOW return `confident` — but absorb's
`already_absorbed[uid] = fid` skip-lock prevents re-evaluation.

This maintenance utility re-routes orphans:
  - For each entity, find standalone unified-X final entries
    (id starts with `unified-`, fuss=seed_unsorted, AND the unified
    id exists in seed_unified — confirms it's a bulk-promote artifact)
  - For each orphan, run match_pair against ALL classified foundations
    in same entity (fuss not in {None, seed_unsorted}, id not starting
    with `unified-`)
  - If exactly ONE confident match found:
    - Union orphan.composed_of (resolved to seed_unified ids) into
      foundation.composed_of (sorted, deduped)
    - Drop the standalone orphan entry from the coin list
  - Skip 0-match (genuinely new) and >1-match (curator decides)

After re-routing, run absorb script (`absorb_seeds_into_final_v2.py
--apply`) to re-enrich the now-linked foundations: pulls weight,
year_ranges, sources, multi-source catalog refs from the newly-
composed-of unified members.

Run:
  .venv/bin/python scripts/maintenance/reroute_orphan_unified_into_foundation.py
  .venv/bin/python scripts/maintenance/reroute_orphan_unified_into_foundation.py --apply
  .venv/bin/python scripts/maintenance/reroute_orphan_unified_into_foundation.py --entity danish_realm --apply
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, "scripts/maintenance")
sys.path.insert(0, "scripts")

import yaml  # type: ignore  # noqa: E402

from merge_seeds_cross_source import match_pair  # type: ignore  # noqa: E402


def _load_seed_unified_ids(entity_id: str) -> set[str]:
    """Set of unified ids that EXIST in seed_unified for this entity."""
    path = Path(f"data/v2/seed_unified/{entity_id}.yml")
    if not path.exists():
        return set()
    with path.open() as f:
        d = yaml.safe_load(f) or {}
    return {c.get("id") for c in (d.get("coins") or []) if c.get("id")}


def reroute_entity(entity_path: Path, apply: bool) -> dict:
    """Returns a stats dict for the entity."""
    entity_id = entity_path.stem
    with entity_path.open() as f:
        d = yaml.safe_load(f)
    if not isinstance(d, dict):
        return {"entity": entity_id, "error": "not a dict"}
    coins = list(d.get("coins") or [])
    seed_unified_ids = _load_seed_unified_ids(entity_id)

    # Partition: orphans (standalone bulk-promoted) vs classified foundations
    orphans: list[dict] = []
    foundations: list[dict] = []
    for c in coins:
        cid = c.get("id") or ""
        if (
            cid.startswith("unified-")
            and c.get("fuss") == "seed_unsorted"
            and cid in seed_unified_ids
        ):
            orphans.append(c)
        elif c.get("fuss") not in (None, "seed_unsorted"):
            foundations.append(c)

    # For each orphan, find confident matches in foundations
    rerouted: list[tuple[str, str]] = []  # (orphan_id, foundation_id)
    multi_skipped: list[tuple[str, list[str]]] = []
    not_matched: list[str] = []

    # year-span safety filter: only reroute when the orphan's year span
    # falls WITHIN the foundation's year span (or matches exactly).
    # Prevents over-aggregated unifieds (e.g. Hede 25A+25C merged) from
    # expanding a sub-variant foundation's year_ranges via absorb's
    # union pass when re-enriching.
    def _safe_year_overlap(orphan: dict, fnd: dict) -> bool:
        f_first = fnd.get("year_first")
        f_last = fnd.get("year_last")
        o_first = orphan.get("year_first")
        o_last = orphan.get("year_last")
        if not all(isinstance(v, int) for v in (f_first, f_last, o_first, o_last)):
            return True  # missing year data — don't block on it
        # Orphan must span ≤ foundation by ≥-2-year tolerance on either side
        # (covers Hede sub-variants with 1-2yr drift) but not more.
        TOLERANCE = 2
        return (
            o_first >= f_first - TOLERANCE
            and o_last <= f_last + TOLERANCE
        )

    year_filtered: list[tuple[str, str]] = []
    for orphan in orphans:
        oid = orphan.get("id")
        matches: list[str] = []
        for fnd in foundations:
            r = match_pair(orphan, fnd, entity_id=entity_id)
            if r.get("decision") == "confident":
                matches.append(fnd.get("id"))
        if len(matches) == 1:
            # Apply year-span safety filter
            fnd = next(f for f in foundations if f.get("id") == matches[0])
            if _safe_year_overlap(orphan, fnd):
                rerouted.append((oid, matches[0]))
            else:
                year_filtered.append((oid, matches[0]))
        elif len(matches) > 1:
            multi_skipped.append((oid, matches))
        else:
            not_matched.append(oid)

    stats = {
        "entity": entity_id,
        "orphans_total": len(orphans),
        "rerouted": len(rerouted),
        "multi_skipped": len(multi_skipped),
        "year_filtered": len(year_filtered),
        "not_matched": len(not_matched),
        "rerouted_pairs": rerouted,
        "year_filtered_pairs": year_filtered,
    }

    if not apply or not rerouted:
        return stats

    # Apply: build new coin list with re-routing
    orphan_ids_to_drop = {oid for oid, _ in rerouted}
    # For each foundation that's a re-route target, collect orphans + their
    # composed_of members
    foundation_additions: dict[str, set[str]] = {}
    for oid, fid in rerouted:
        # Find the orphan dict to read its composed_of
        orphan_obj = next(o for o in orphans if o.get("id") == oid)
        # The orphan's composed_of references unified ids — keep only those
        # that exist in seed_unified (filter stale)
        orphan_composed = orphan_obj.get("composed_of") or []
        valid_composed = [c for c in orphan_composed if c in seed_unified_ids]
        # Always include the orphan's own id (it IS a unified id)
        members = set(valid_composed) | {oid}
        foundation_additions.setdefault(fid, set()).update(members)

    new_coins: list[dict] = []
    for c in coins:
        cid = c.get("id") or ""
        if cid in orphan_ids_to_drop:
            continue  # drop standalone orphan
        if cid in foundation_additions:
            existing = set(c.get("composed_of") or [])
            merged = sorted(existing | foundation_additions[cid])
            c["composed_of"] = merged
        new_coins.append(c)

    d["coins"] = new_coins
    # Write back preserving overall structure
    with entity_path.open("w") as f:
        yaml.safe_dump(
            d, f, allow_unicode=True, sort_keys=False,
            default_flow_style=False, width=120,
        )
    return stats


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--apply", action="store_true",
                    help="Apply changes (default: dry-run)")
    p.add_argument("--entity", default=None,
                    help="Restrict to one entity (e.g. danish_realm)")
    args = p.parse_args()

    final_dir = Path("data/v2/final")
    paths = sorted(final_dir.glob("*.yml"))
    if args.entity:
        paths = [p for p in paths if p.stem == args.entity]
        if not paths:
            print(f"No entity {args.entity!r} found under {final_dir}/", file=sys.stderr)
            return 2

    total_orphans = 0
    total_rerouted = 0
    total_multi = 0
    total_year_filtered = 0
    total_new = 0
    for path in paths:
        stats = reroute_entity(path, apply=args.apply)
        total_orphans += stats["orphans_total"]
        total_rerouted += stats["rerouted"]
        total_multi += stats["multi_skipped"]
        total_year_filtered += stats.get("year_filtered", 0)
        total_new += stats["not_matched"]
        if stats["rerouted"] or stats["multi_skipped"] or stats.get("year_filtered", 0):
            print(
                f"{stats['entity']:<28} "
                f"orphans={stats['orphans_total']:<5} "
                f"rerouted={stats['rerouted']:<4} "
                f"yr-filt={stats.get('year_filtered', 0):<3} "
                f"multi={stats['multi_skipped']:<3} "
                f"new={stats['not_matched']}"
            )
            for oid, fid in stats["rerouted_pairs"][:8]:
                print(f"  ✓ {oid}  →  {fid}")
            if len(stats["rerouted_pairs"]) > 8:
                print(f"  ... +{len(stats['rerouted_pairs']) - 8} rerouted")
            for oid, fid in stats.get("year_filtered_pairs", [])[:3]:
                print(f"  ⚠ {oid}  →  {fid} (year-span mismatch — filtered)")

    print()
    print(f"Totals: orphans={total_orphans}  rerouted={total_rerouted}  "
          f"yr-filtered={total_year_filtered}  multi-skip={total_multi}  "
          f"genuinely-new={total_new}")
    if not args.apply:
        print()
        print("--- DRY RUN — pass --apply to commit changes. ---")
        print("Next step after --apply: run absorb to re-enrich foundations:")
        print("  .venv/bin/python scripts/maintenance/absorb_seeds_into_final_v2.py --apply")
    return 0


if __name__ == "__main__":
    sys.exit(main())
