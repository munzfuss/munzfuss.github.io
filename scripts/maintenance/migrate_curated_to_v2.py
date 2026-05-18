#!/usr/bin/env python3
"""V2 Phase 1.2 — migrate V1 curated coins → entity-keyed V2 files.

Reads every `data/locations/<loc>.yml`, applies the §3.1 decision tree
from `docs/V2_PIPELINE.md`, and writes per-political-entity files to
`data/v2/curated/<entity>.yml`.

§3.1 decision tree summary:
  1. `issuing_entity` already set to something OTHER than `gesamtstaat`
     → preserve verbatim (scalar stays scalar, list stays list).
  2. `issuing_entity == 'gesamtstaat'` → apply mint→entity lookup:
        Altona*           → royal_holstein   (single mint)
        Kopenhagen*       → danish_realm     (single mint)
        Kongsberg* / Christiania* → danish_norway
        multi-mint        → alphabetically-sorted list of resolved entities
        unknown mint      → `_deprecated_gesamtstaat` + flag
  3. Multi-entity list ordering: alphabetical by entity id (deterministic).
  4. Home-file rule (§3.10): coin lives in the entity file matching the
     FIRST element of the list (alphabetically-first); other consumers
     pick the coin up via the build assembly's inverse-index pass.

Migration report categories:
  - Coins re-mapped `gesamtstaat → <scalar>`
  - Coins re-mapped `gesamtstaat → [list]`
  - Coins left `_deprecated_gesamtstaat` (unknown mint, manual review)
  - Coins with mint=list but non-`gesamtstaat` scalar `issuing_entity`
    (consistency-pass candidates — NOT auto-converted)
  - Coin-id collisions across V1 locations (manual reconciliation needed)

Usage:
  scripts/maintenance/migrate_curated_to_v2.py --dry-run     # report only
  scripts/maintenance/migrate_curated_to_v2.py --apply       # write V2 files

The --apply step WIPES `data/v2/curated/*.yml` before writing. Designed to
be re-runnable: edit V1, re-run migration, regenerate V2.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
LOCATIONS = ROOT / "data" / "locations"
V2_CURATED = ROOT / "data" / "v2" / "curated"
I18N_ENTITIES = ROOT / "data" / "i18n" / "issuing_entities.yml"


# §3.1 mint→entity lookup. Keys are normalised mint prefixes (after stripping
# parenthesised mintmaster annotations).
MINT_TO_ENTITY: dict[str, str] = {
    "Altona": "royal_holstein",
    "Kopenhagen": "danish_realm",
    "Kongsberg": "danish_norway",
    "Christiania": "danish_norway",
}

# Unresolvable mint markers (e.g. Tower Hill outsourced contract minting).
# These get _deprecated_gesamtstaat fallback per §3.1 step 4.
UNRESOLVABLE_MINT_PATTERNS = (
    "Royal Mint",
    "Tower Hill",
)


def _strip_mint_suffix(mint: str) -> str:
    """`Altona (FK VS)` → `Altona`; `Kopenhagen (683.1 M)` → `Kopenhagen`."""
    return re.sub(r"\s*\([^)]*\)\s*$", "", mint).strip()


def _normalise_mint(mint) -> list[str]:
    """Normalise raw mint field (scalar or list) into a list of stripped mint
    prefixes. Returns empty list when mint is None/missing/unparseable."""
    if mint is None:
        return []
    items = mint if isinstance(mint, list) else [mint]
    out: list[str] = []
    for m in items:
        if not isinstance(m, str):
            continue
        out.append(_strip_mint_suffix(m))
    return out


def _resolve_mint_to_entity(mint_prefix: str) -> str | None:
    """Map a stripped mint prefix to a §3.1 entity tag. Returns None when
    the mint is unresolvable per §3.1."""
    if mint_prefix in MINT_TO_ENTITY:
        return MINT_TO_ENTITY[mint_prefix]
    for pat in UNRESOLVABLE_MINT_PATTERNS:
        if pat in mint_prefix:
            return None
    return None


def _migrate_issuing_entity(
    issuing_entity, mint
) -> tuple[str | list[str], str | None]:
    """Apply §3.1 decision tree. Returns (new_entity, migration_note).
    new_entity is `_deprecated_gesamtstaat` for unresolvable cases."""

    # Step 1: preserve non-gesamtstaat verbatim.
    if isinstance(issuing_entity, list):
        return (issuing_entity, None)
    if issuing_entity != "gesamtstaat":
        return (issuing_entity, None)

    # Step 2: gesamtstaat — apply mint lookup.
    mints = _normalise_mint(mint)
    if not mints:
        return ("_deprecated_gesamtstaat", "auto-mapped from gesamtstaat (no mint to resolve)")

    resolved = set()
    unresolvable = False
    for m in mints:
        ent = _resolve_mint_to_entity(m)
        if ent is None:
            unresolvable = True
        else:
            resolved.add(ent)

    if unresolvable or not resolved:
        return (
            "_deprecated_gesamtstaat",
            f"auto-mapped from gesamtstaat (unresolvable mint: {mints})",
        )

    if len(resolved) == 1:
        ent = next(iter(resolved))
        return (ent, "auto-mapped from gesamtstaat")

    # Multi-entity — alphabetical sort for determinism per §3.1 step 3.
    return (sorted(resolved), "auto-mapped from gesamtstaat (joint-mint)")


def _home_entity_for(issuing_entity) -> str:
    """First alphabetical element of a list-form `issuing_entity`, or the
    scalar itself. Per §3.10 home-file rule."""
    if isinstance(issuing_entity, list):
        return sorted(issuing_entity)[0]
    return issuing_entity


def _load_locations() -> dict[str, dict]:
    """Returns {loc_id: raw_yaml_dict} for every curated location yaml."""
    out = {}
    for p in sorted(LOCATIONS.glob("*.yml")):
        if p.name.endswith("-references.yml"):
            continue
        out[p.stem] = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    return out


def _build_entity_files(
    locations: dict[str, dict]
) -> tuple[dict[str, list[dict]], list[dict], list[dict]]:
    """Walks V1 locations, applies migration, returns:
      - by_entity: {entity_id: [coin_dict, ...]}  (home-file grouped)
      - dup_collisions: [{id, locs, ...}, ...]   (same-id across locations)
      - joint_mint_scalar_candidates: per §3.1 step 4 report-only flag
    """
    by_entity: dict[str, list[dict]] = defaultdict(list)
    seen_ids: dict[str, list[tuple[str, dict]]] = defaultdict(list)
    joint_mint_scalar_candidates: list[dict] = []

    for loc_id, doc in locations.items():
        for coin in doc.get("coins", []) or []:
            cid = coin.get("id")
            if cid is None:
                continue
            seen_ids[cid].append((loc_id, coin))

    dup_collisions: list[dict] = []

    for cid, entries in seen_ids.items():
        if len(entries) == 1:
            loc_id, coin = entries[0]
            new_coin, target_entity = _process_coin(
                coin, loc_id, joint_mint_scalar_candidates
            )
            by_entity[target_entity].append(new_coin)
        else:
            # Cross-location duplication of the same coin id.
            # Process each side independently, give them suffixed ids,
            # and report collision for manual reconciliation.
            dup_record = {
                "id": cid,
                "locations": [e[0] for e in entries],
                "v2_suffixed_ids": [],
                "home_entities": [],
            }
            for loc_id, coin in entries:
                new_coin, target_entity = _process_coin(
                    coin, loc_id, joint_mint_scalar_candidates
                )
                suffixed_id = f"{cid}__v1from_{loc_id}"
                new_coin["id"] = suffixed_id
                new_coin["_migration_dup_origin_id"] = cid
                existing_note = new_coin.get("_migration_note", "")
                dup_note = (
                    f"V1 coin-id collision with locations {dup_record['locations']}; "
                    f"this entry retains the data sourced from {loc_id}.yml. "
                    f"Manual merge needed per §9a multi-specimen rule."
                )
                new_coin["_migration_note"] = (
                    f"{existing_note}; {dup_note}" if existing_note else dup_note
                )
                by_entity[target_entity].append(new_coin)
                dup_record["v2_suffixed_ids"].append(suffixed_id)
                dup_record["home_entities"].append(target_entity)
            dup_collisions.append(dup_record)

    # Deterministic order inside each entity file: sort by id.
    for ent, coins in by_entity.items():
        coins.sort(key=lambda c: c.get("id", ""))

    return dict(by_entity), dup_collisions, joint_mint_scalar_candidates


def _process_coin(
    coin: dict, loc_id: str, joint_mint_scalar_candidates: list[dict]
) -> tuple[dict, str]:
    """Apply migration to one coin. Returns (new_coin_dict, home_entity)."""
    raw_ie = coin.get("issuing_entity")
    mint = coin.get("mint")
    new_ie, migration_note = _migrate_issuing_entity(raw_ie, mint)

    # §3.1 step 4 reporting: mint=list but non-gesamtstaat scalar issuing_entity
    if (
        isinstance(mint, list)
        and len(mint) >= 2
        and isinstance(raw_ie, str)
        and raw_ie != "gesamtstaat"
        and not isinstance(new_ie, list)
    ):
        joint_mint_scalar_candidates.append({
            "loc": loc_id,
            "id": coin.get("id"),
            "mint": mint,
            "issuing_entity_v1": raw_ie,
            "issuing_entity_v2": new_ie,
        })

    # Build new coin: preserve all V1 fields verbatim except
    # `issuing_entity` (rewritten), then add v2 bookkeeping.
    new_coin = dict(coin)
    new_coin["issuing_entity"] = new_ie
    new_coin["v1_home_location"] = loc_id
    new_coin.setdefault("composed_of", [])
    if migration_note:
        new_coin["_migration_note"] = migration_note

    return new_coin, _home_entity_for(new_ie)


def _emit_entity_file(entity_id: str, coins: list[dict], source_locations: list[str]) -> str:
    """Render one `data/v2/curated/<entity>.yml`."""
    today = date.today().isoformat()
    payload = {
        "id": entity_id,
        "source_locations": sorted(set(source_locations)),
        "migrated_from_v1": today,
        "coins": coins,
    }
    return yaml.dump(
        payload,
        sort_keys=False,
        allow_unicode=True,
        default_flow_style=False,
        width=120,
    )


def _summary_table(by_entity: dict[str, list[dict]]) -> str:
    rows = []
    for ent, coins in sorted(by_entity.items()):
        scalar = sum(1 for c in coins if not isinstance(c.get("issuing_entity"), list))
        list_form = sum(1 for c in coins if isinstance(c.get("issuing_entity"), list))
        gs_migrated = sum(
            1 for c in coins
            if (c.get("_migration_note") or "").startswith("auto-mapped from gesamtstaat")
        )
        rows.append((ent, len(coins), scalar, list_form, gs_migrated))
    lines = [
        f"{'Entity':36s} {'Coins':>6s} {'Scalar':>7s} {'List':>5s} {'From-gs':>8s}",
        "-" * 70,
    ]
    for r in rows:
        lines.append(f"{r[0]:36s} {r[1]:>6d} {r[2]:>7d} {r[3]:>5d} {r[4]:>8d}")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", default=True,
                        help="Report only — do NOT write V2 files (default)")
    parser.add_argument("--apply", action="store_true",
                        help="WIPE data/v2/curated/ and write fresh V2 files")
    parser.add_argument("--json-report", type=Path, default=None,
                        help="Write machine-readable migration report to this path")
    args = parser.parse_args()

    if args.apply:
        args.dry_run = False

    locations = _load_locations()
    print(f"Loaded {len(locations)} V1 locations from {LOCATIONS}")
    print(f"  total coins: {sum(len(d.get('coins') or []) for d in locations.values())}")

    by_entity, dup_collisions, joint_mint_scalar_candidates = _build_entity_files(locations)

    print("\n=== Migration summary ===\n")
    print(_summary_table(by_entity))

    print(f"\n=== gesamtstaat → multi-entity list cases ===")
    for ent, coins in sorted(by_entity.items()):
        for c in coins:
            if isinstance(c.get("issuing_entity"), list) and (
                (c.get("_migration_note") or "").startswith("auto-mapped from gesamtstaat (joint-mint)")
            ):
                print(f"  {c['id']:>40s}  home={ent}  list={c['issuing_entity']}  mint={c.get('mint')}")

    print(f"\n=== _deprecated_gesamtstaat (manual review) ===")
    for ent, coins in by_entity.items():
        for c in coins:
            if c.get("issuing_entity") == "_deprecated_gesamtstaat":
                print(f"  {c['id']:>40s}  v1_home={c.get('v1_home_location')}  mint={c.get('mint')}  note={c.get('_migration_note')}")

    print(f"\n=== Coin-id collisions across V1 locations ({len(dup_collisions)}) ===")
    for d in dup_collisions:
        print(f"  {d['id']!r} appears in {d['locations']}")
        print(f"    → V2 ids: {d['v2_suffixed_ids']}")
        print(f"    → home entities: {d['home_entities']}")

    print(f"\n=== Joint-mint scalar candidates (§3.1 step 4 report-only, {len(joint_mint_scalar_candidates)}) ===")
    print("  Coins with mint=list but non-gesamtstaat scalar issuing_entity.")
    print("  Migration preserves the curator's scalar choice verbatim.")
    print("  Listed for a separate consistency-pass decision.")
    for c in joint_mint_scalar_candidates[:40]:
        print(f"  {c['id']:>40s}  loc={c['loc']:>22s}  ie={c['issuing_entity_v2']}  mint={c['mint']}")
    if len(joint_mint_scalar_candidates) > 40:
        print(f"  ... and {len(joint_mint_scalar_candidates) - 40} more")

    # --- JSON report --------------------------------------------------------

    if args.json_report:
        report = {
            "summary_by_entity": {
                ent: {
                    "coin_count": len(coins),
                    "scalar_count": sum(1 for c in coins if not isinstance(c.get("issuing_entity"), list)),
                    "list_count": sum(1 for c in coins if isinstance(c.get("issuing_entity"), list)),
                    "from_gesamtstaat": sum(
                        1 for c in coins
                        if (c.get("_migration_note") or "").startswith("auto-mapped from gesamtstaat")
                    ),
                }
                for ent, coins in sorted(by_entity.items())
            },
            "dup_collisions": dup_collisions,
            "joint_mint_scalar_candidates": joint_mint_scalar_candidates,
            "deprecated_gesamtstaat": [
                {
                    "id": c["id"], "v1_home": c.get("v1_home_location"),
                    "mint": c.get("mint"), "note": c.get("_migration_note"),
                }
                for ent, coins in by_entity.items()
                for c in coins
                if c.get("issuing_entity") == "_deprecated_gesamtstaat"
            ],
        }
        args.json_report.write_text(json.dumps(report, ensure_ascii=False, indent=2))
        print(f"\nJSON report → {args.json_report}")

    # --- Write phase --------------------------------------------------------

    if args.dry_run:
        print("\n--- DRY RUN — no files written. Re-run with --apply to commit. ---")
        return 0

    V2_CURATED.mkdir(parents=True, exist_ok=True)
    # Wipe any existing v2 curated yaml (regenerable artefact).
    for p in V2_CURATED.glob("*.yml"):
        p.unlink()

    # Group source-locations per entity for the header field.
    source_locs_per_entity: dict[str, list[str]] = defaultdict(list)
    for ent, coins in by_entity.items():
        for c in coins:
            source_locs_per_entity[ent].append(c.get("v1_home_location"))

    for ent, coins in by_entity.items():
        path = V2_CURATED / f"{ent}.yml"
        path.write_text(
            _emit_entity_file(ent, coins, source_locs_per_entity[ent]),
            encoding="utf-8",
        )

    print(f"\n✓ Wrote {len(by_entity)} entity file(s) to {V2_CURATED}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
