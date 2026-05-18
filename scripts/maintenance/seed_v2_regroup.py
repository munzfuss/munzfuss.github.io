#!/usr/bin/env python3
"""V2 Phase 3 — regroup V1 location-keyed seed yamls into V2 entity-keyed seed yamls.

Pragmatic shortcut over the V2_PIPELINE.md §6 plan's «add `--v2` flag to
every builder» recipe: V1 seed yamls are already the «classified
intermediate» distilled from raw parsed caches. Rather than duplicating
the classification logic in 5 builders (hede / bruun / galster /
numista / numismaster_pre1541 / numismaster), we treat V1 seed yamls
as input here and group by political entity per the §3.1 mint→entity
table — producing `data/v2/seed/<source>/<entity>.yml`.

Trade-off: V2 seeds become a SECOND-derivative artefact (cache → V1 seed
→ V2 seed) rather than first-derivative (cache → V2 seed). Acceptable
until V2 promotes to main (Phase 9), at which point the V1 builders
become V2 builders proper.

Usage:
  scripts/maintenance/seed_v2_regroup.py --dry-run    # report only (default)
  scripts/maintenance/seed_v2_regroup.py --apply      # merge into V2 seed files

The --apply step is IDEMPOTENT — it folds fresh regrouped coins against
existing `data/v2/seed/<source>/<entity>.yml` via
`lib.seed_merge.merge_seed`. CURATED_FIELDS ({fuss, phase, fraction,
issuing_entity, kind, note, mint_verified, verified}) survive across
re-runs, so curator triage on seed entries (e.g. moving from
`seed_unsorted` to a real fuss/phase) persists when V1 seeds get
re-harvested. Orphan curated entries (in V2 but no longer in V1)
stay verbatim — no silent data loss. Per-entry escape hatch: add
`_curation_holds: [field, …]` to any V2 seed entry.

Outputs one yaml per (source, entity) pair:
  data/v2/seed/hede/danish_realm.yml
  data/v2/seed/hede/royal_holstein.yml
  …

Unclassified coins (mint missing or unknown) go to
`data/v2/seed/<source>/_unclassified.yml` for curator review.

Joint-mint coins receive list-form `issuing_entity` per §3.10; their
home file is the alphabetically-first entity in the list. Build assembly's
§3.10 inverse-index pass surfaces them on every consumer page whose
`consumes_entities` intersects with the list.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
SEED_V1 = ROOT / "data" / "seed"
SEED_V2 = ROOT / "data" / "v2" / "seed"
LOCATIONS_V1 = ROOT / "data" / "locations"

sys.path.insert(0, str(ROOT / "scripts"))
from lib.v2_entity_classify import (  # noqa: E402
    classify_mint_to_entity,
    classify_mint_diagnostics,
)
from lib.schema import Coin, CatalogRefs  # noqa: E402
from lib.seed_merge import merge_seed  # noqa: E402


def _ruamel_to_dict(c):
    """ruamel.yaml round-trip types → plain Python equivalents (recursive).
    Mirrors the helper in migrate_curated_to_v2; needed because seed_merge
    returns CommentedMap entries that pyyaml.dump can't serialise.
    """
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

# Canonical schema field sets — sanitisation rejects everything else.
_COIN_FIELDS: set[str] = set(Coin.model_fields.keys())
_CATALOG_FIELDS: set[str] = set(CatalogRefs.model_fields.keys())

# V2-side bookkeeping keys that the regroup script adds. Must survive
# sanitisation; matches `lib.v2_resolver.V2_MIGRATION_BREADCRUMB_KEYS`.
_V2_BREADCRUMBS: set[str] = {
    "v1_seed_location",
    "_migration_note",
    "_migration_dup_origin_id",
}


_BRUUN_PART_ROMAN = {1: "I", 2: "II", 3: "III", 4: "IV", 5: "V", 6: "VI"}


def _coerce_top_level_value_types(coin: dict, report: dict) -> None:
    """In-place per-field coercion for Coin-level fields that V1 seeds
    sometimes emit in non-canonical shape:

      - `year_label: None` (numista pre-1541 seeds) → synthesise from
        `year_first` / `year_last` when those are set, else drop coin
        (caller detects via empty year_label).
      - `fineness: '0,312,5,'` (galster c3g-95) → try to parse as Danish-
        comma float; on failure drop fineness to None.
    """
    if coin.get("nominal") is None:
        coin["nominal"] = "(?)"  # placeholder; Phase 8 curation fills real value
        report["sanitised_nominal_null_to_placeholder"] = report.get(
            "sanitised_nominal_null_to_placeholder", 0
        ) + 1

    if coin.get("year_label") is None:
        yf = coin.get("year_first")
        yl = coin.get("year_last")
        if yf is not None and yl is not None and yf != yl:
            coin["year_label"] = f"{yf}-{yl}"
            report["sanitised_year_label_synthesised"] = report.get(
                "sanitised_year_label_synthesised", 0
            ) + 1
        elif yf is not None:
            coin["year_label"] = str(yf)
            report["sanitised_year_label_synthesised"] = report.get(
                "sanitised_year_label_synthesised", 0
            ) + 1

    fine = coin.get("fineness")
    if isinstance(fine, str):
        # Try Danish-comma decimal "0,3125" first.
        s = fine.rstrip(",").replace(",", ".")
        # Multiple decimal points after de-comma → malformed.
        if s.count(".") > 1:
            # Keep first decimal segment only: "0.312.5" → "0.312"
            parts = s.split(".")
            s = parts[0] + "." + parts[1]
        try:
            coin["fineness"] = float(s)
            report["sanitised_fineness_str_to_float"] = report.get(
                "sanitised_fineness_str_to_float", 0
            ) + 1
        except (ValueError, TypeError):
            coin["fineness"] = None
            report["sanitised_fineness_unparseable_drop"] = report.get(
                "sanitised_fineness_unparseable_drop", 0
            ) + 1


def _coerce_catalog_value_types(cat: dict, report: dict) -> dict:
    """Per-field type coercion for catalog values that V1 builders sometimes
    emit in non-canonical form (e.g. `bruun_part: 3` instead of `'III'`).
    Returns a new dict with coerced values; non-canonical drops counted."""
    out = dict(cat)
    bp = out.get("bruun_part")
    if isinstance(bp, int) and bp in _BRUUN_PART_ROMAN:
        out["bruun_part"] = _BRUUN_PART_ROMAN[bp]
        report["sanitised_bruun_part_int_to_roman"] = report.get(
            "sanitised_bruun_part_int_to_roman", 0
        ) + 1
    return out


def _sanitise_coin(coin: dict, report: dict) -> dict:
    """Return a copy of `coin` with non-schema fields removed.

    V1 seed yamls (especially pre-1541 drafts from bruun/galster/numista)
    carry generator-internal annotation fields and orphan top-level
    fields (`bruun_collection_id` at coin root instead of under
    `catalog:`) that the V2 Coin schema rejects. This step:

      1. Strips top-level underscore-prefixed fields (V1's seed_merge
         convention — `_curation_holds`, `_political_period`, etc.).
      2. Moves top-level fields that ARE valid CatalogRefs members
         (`bruun_collection_id`, `hede`, etc.) into the `catalog:` dict.
      3. Drops top-level fields that aren't in Coin schema or the v2
         breadcrumb set.
      4. Drops catalog subdict fields that aren't in CatalogRefs schema.

    Each drop is counted in `report` for the diagnostic summary.
    """
    out: dict = {}
    # Step 1+3: filter top-level
    for k, v in coin.items():
        if k.startswith("_"):
            if k in _V2_BREADCRUMBS:
                out[k] = v
            else:
                report["sanitised_top_drop"][k] += 1
            continue
        if k in _COIN_FIELDS or k in _V2_BREADCRUMBS:
            out[k] = v
        elif k in _CATALOG_FIELDS:
            # Step 2: move into catalog
            cat = dict(out.get("catalog") or {})
            cat[k] = v
            out["catalog"] = cat
            report["sanitised_top_moved_to_catalog"][k] += 1
        else:
            report["sanitised_top_drop"][k] += 1

    # Step 4: catalog subdict sanitisation + type coercion
    catalog = out.get("catalog")
    if isinstance(catalog, dict):
        clean_cat = {}
        for k, v in catalog.items():
            if k in _CATALOG_FIELDS:
                clean_cat[k] = v
            else:
                report["sanitised_catalog_drop"][k] += 1
        clean_cat = _coerce_catalog_value_types(clean_cat, report)
        out["catalog"] = clean_cat

    # Top-level field coercions (year_label / fineness shape repair).
    _coerce_top_level_value_types(out, report)

    return out


def _load_yaml(p: Path) -> dict:
    return yaml.safe_load(p.read_text(encoding="utf-8")) or {}


def _home_entity_for(issuing_entity) -> str:
    if isinstance(issuing_entity, list):
        return sorted(issuing_entity)[0]
    return issuing_entity


# Seed-side issuing_entity tags that need V2-canonical remapping. V1
# seed builders historically use a slightly different naming + the
# deprecated `gesamtstaat` umbrella tag. The remapping below normalises
# them; the `_RESOLVE_VIA_MINT` set forces mint-driven re-classification
# regardless of what the seed claims (used for `gesamtstaat` and
# `schleswig_holstein_duchy`, which are catch-alls — actual entity
# depends on the coin's mint).
_SEED_ENTITY_REMAP: dict[str, str] = {
    "norwegian_realm": "danish_norway",
}

_RESOLVE_VIA_MINT: set[str] = {
    "gesamtstaat",            # § 3.1 — mint determines royal_holstein vs danish_realm vs joint
    "schleswig_holstein_duchy",   # umbrella tag, refine by mint when possible
}


def _normalise_entity_for_coin(coin: dict) -> tuple[str | list[str] | None, dict]:
    """Decide V2 entity tag for one coin. Preference:
      1. Coin's `issuing_entity`, if already a canonical V2 tag (curator's
         choice wins). Seed-side aliases (`norwegian_realm`) are remapped.
      2. Catch-all seed tags (`gesamtstaat`, `schleswig_holstein_duchy`)
         → mint-driven classification per §3.1.
      3. Otherwise → mint-driven classification.
      4. Unresolvable → None (caller routes to `_unclassified`).
    Also returns a per-coin diagnostic dict for the report.
    """
    explicit = coin.get("issuing_entity")

    # Step 1: remap seed alias if applicable.
    if isinstance(explicit, str) and explicit in _SEED_ENTITY_REMAP:
        canonical = _SEED_ENTITY_REMAP[explicit]
        return canonical, {"source": "explicit_remap", "from": explicit, "to": canonical}

    # Step 2: force mint resolution for catch-all tags.
    if isinstance(explicit, str) and explicit in _RESOLVE_VIA_MINT:
        diag = classify_mint_diagnostics(coin.get("mint"))
        entity = classify_mint_to_entity(coin.get("mint"))
        diag["source"] = "catch_all_via_mint"
        diag["seed_tag"] = explicit
        diag["resolved"] = entity
        return entity, diag

    # Step 3: real canonical V2 tag from V1 — preserve verbatim.
    if explicit:
        return explicit, {"source": "explicit", "raw_mint": coin.get("mint")}

    # Step 4: no explicit tag → mint classifier.
    diag = classify_mint_diagnostics(coin.get("mint"))
    entity = classify_mint_to_entity(coin.get("mint"))
    diag["source"] = "mint_classifier"
    diag["resolved"] = entity
    return entity, diag


def _build_v2_seed_groups(
    src_dir: Path,
) -> tuple[dict[str, list[dict]], dict]:
    """Walks every `data/seed/<source>/<location>.yml` for one source dir
    and groups its coins by V2 home entity.

    Returns:
      (by_entity, report)
      by_entity: {entity_id: [coin_dict, …]}  — entity-keyed coin lists
                 (each coin dict has v2 fields injected: issuing_entity,
                  v1_seed_location for backtrace; original fields preserved)
      report   : per-source stats + diagnostic samples
    """
    by_entity: dict[str, list[dict]] = defaultdict(list)
    report: dict = {
        "total_coins": 0,
        "by_entity_count": Counter(),
        "by_v1_location": Counter(),
        "unclassified_count": 0,
        "unknown_mints": Counter(),
        "out_of_scope_mints": Counter(),
        "scalar_count": 0,
        "list_count": 0,
        "explicit_entity_count": 0,
        "sanitised_top_drop": Counter(),
        "sanitised_catalog_drop": Counter(),
        "sanitised_top_moved_to_catalog": Counter(),
    }
    seen_ids: set[str] = set()
    id_collisions: list[tuple[str, str]] = []

    # V2 consumes ALL seed yamls — including pre-1541 drafts that V1
    # never promoted (per V2_PIPELINE.md §3.2: pre_1541 files merge into
    # the regular entity-keyed V2 files). Field sanitisation below
    # handles the non-schema-clean shape of those drafts.
    for yml_path in sorted(src_dir.glob("*.yml")):
        v1_loc = yml_path.stem
        doc = _load_yaml(yml_path)
        coins = doc.get("coins", []) or []
        report["by_v1_location"][v1_loc] += len(coins)

        for coin in coins:
            report["total_coins"] += 1
            cid = coin.get("id")
            if not cid:
                continue
            if cid in seen_ids:
                id_collisions.append((cid, v1_loc))
                # Per §9a these would deserve merge; for V2 seed we just
                # keep the first occurrence and log. Most likely the
                # parser already deduplicated; collisions across location
                # files would be rare in practice.
                continue
            seen_ids.add(cid)

            entity, diag = _normalise_entity_for_coin(coin)

            if diag.get("source") == "explicit":
                report["explicit_entity_count"] += 1
            else:
                for u in diag.get("unknown_raw", []):
                    report["unknown_mints"][u] += 1
                for o in diag.get("out_of_scope_canon", []):
                    report["out_of_scope_mints"][o] += 1

            if entity is None:
                report["unclassified_count"] += 1
                home = "_unclassified"
            else:
                if isinstance(entity, list):
                    report["list_count"] += 1
                    report["by_entity_count"]["[" + ",".join(sorted(entity)) + "]"] += 1
                else:
                    report["scalar_count"] += 1
                    report["by_entity_count"][entity] += 1
                home = _home_entity_for(entity)

            # Sanitise: strip generator-internal fields, move catalog-ref
            # fields into the catalog subdict, drop non-schema keys.
            sanitised = _sanitise_coin(coin, report)
            if entity is not None:
                sanitised["issuing_entity"] = entity
            sanitised["v1_seed_location"] = v1_loc
            by_entity[home].append(sanitised)

    if id_collisions:
        report["id_collisions"] = id_collisions

    # Deterministic order inside each entity file.
    for ent, lst in by_entity.items():
        lst.sort(key=lambda c: c.get("id", ""))

    return dict(by_entity), report


def _emit_v2_seed_file(
    source: str, entity_id: str, coins: list[dict],
) -> str:
    """Render one `data/v2/seed/<source>/<entity>.yml`."""
    today = date.today().isoformat()
    header = (
        f"# V2 seed for political entity `{entity_id}` from source `{source}`.\n"
        f"# Generated {today} by scripts/maintenance/seed_v2_regroup.py from\n"
        f"# `data/seed/{source}/*.yml`. Each coin retains its V1 seed-id;\n"
        f"# `v1_seed_location` records the V1 location-yaml it lived in;\n"
        f"# `issuing_entity` is added by the regrouper (scalar or list per §3.10).\n"
        f"#\n"
        f"# Coins: {len(coins)}\n\n"
    )
    payload = {
        "id": entity_id,
        "source": source,
        "regrouped_from_v1": today,
        "coins": coins,
    }
    return header + yaml.dump(
        payload,
        sort_keys=False,
        allow_unicode=True,
        default_flow_style=False,
        width=120,
    )


def _summarise_source(src: str, report: dict) -> str:
    rows = [
        f"\n=== {src} ===",
        f"  total coins read: {report['total_coins']}",
        f"  classified scalar entity: {report['scalar_count']}",
        f"  classified list-form (joint-mint): {report['list_count']}",
        f"  preserved explicit issuing_entity: {report['explicit_entity_count']}",
        f"  unclassified (no mint / unknown): {report['unclassified_count']}",
    ]
    if report["by_entity_count"]:
        rows.append("  entity distribution (top 15):")
        for ent, n in report["by_entity_count"].most_common(15):
            rows.append(f"    {n:>5d}  {ent}")
    if report["unknown_mints"]:
        rows.append("  unknown mints (top 10):")
        for m, n in report["unknown_mints"].most_common(10):
            rows.append(f"    {n:>5d}  {m!r}")
    if report["out_of_scope_mints"]:
        rows.append("  out-of-scope mints (top):")
        for m, n in report["out_of_scope_mints"].most_common(10):
            rows.append(f"    {n:>5d}  {m!r}")
    if report.get("id_collisions"):
        rows.append(f"  id collisions: {len(report['id_collisions'])}")
    if report.get("sanitised_top_moved_to_catalog"):
        rows.append("  top-level → catalog: moves:")
        for k, n in report["sanitised_top_moved_to_catalog"].most_common(10):
            rows.append(f"    {n:>5d}  {k}")
    if report.get("sanitised_top_drop"):
        rows.append("  top-level dropped (non-schema):")
        for k, n in report["sanitised_top_drop"].most_common(10):
            rows.append(f"    {n:>5d}  {k}")
    if report.get("sanitised_catalog_drop"):
        rows.append("  catalog subkeys dropped (non-schema):")
        for k, n in report["sanitised_catalog_drop"].most_common(10):
            rows.append(f"    {n:>5d}  {k}")
    return "\n".join(rows)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", default=True,
                        help="Report only — do NOT write V2 files (default)")
    parser.add_argument("--apply", action="store_true",
                        help="WIPE data/v2/seed/ and write fresh files")
    parser.add_argument("--source", help="Process only this source (e.g. hede); "
                                          "default: all sources under data/seed/")
    parser.add_argument("--json-report", type=Path, default=None)
    args = parser.parse_args()

    if args.apply:
        args.dry_run = False

    if not SEED_V1.exists():
        print(f"❌ V1 seed dir not found: {SEED_V1}")
        return 1

    # Process each per-source subdirectory.
    sources = [
        d for d in sorted(SEED_V1.iterdir())
        if d.is_dir() and not d.name.startswith("_")
        and (not args.source or d.name == args.source)
    ]
    if not sources:
        print("Nothing to do.")
        return 0

    overall_report: dict[str, dict] = {}
    overall_groups: dict[str, dict[str, list[dict]]] = {}

    for src_dir in sources:
        src = src_dir.name
        by_entity, report = _build_v2_seed_groups(src_dir)
        overall_report[src] = report
        overall_groups[src] = by_entity
        print(_summarise_source(src, report))

    if args.json_report:
        # Convert Counter → dict for JSON.
        serialisable = {
            src: {
                **{k: (dict(v) if isinstance(v, Counter) else v)
                   for k, v in r.items()},
            }
            for src, r in overall_report.items()
        }
        args.json_report.write_text(json.dumps(serialisable, ensure_ascii=False, indent=2))
        print(f"\nJSON report → {args.json_report}")

    if args.dry_run:
        print("\n--- DRY RUN — no files written. Re-run with --apply to commit. ---")
        return 0

    # IDEMPOTENT MERGE: per-(source, entity), fold fresh-regrouped coins
    # against existing data/v2/seed/<source>/<entity>.yml via
    # `lib.seed_merge.merge_seed`. CURATED_FIELDS survive across re-runs —
    # curator's triage on seed entries (moving from `seed_unsorted` to a
    # real fuss/phase) persists when V1 seeds get re-harvested. Orphan
    # curated entries (in V2 seed but no longer in V1) stay verbatim —
    # no silent data loss. Per-entry escape hatch: `_curation_holds`.
    # See `docs/ARCHITECTURE.md §«Manual-override preservation»`.
    files_written = 0
    merge_totals = {"merged_existing": 0, "added_new": 0, "orphan_curated": 0}
    for src, by_entity in overall_groups.items():
        out_dir = SEED_V2 / src
        out_dir.mkdir(parents=True, exist_ok=True)
        for entity_id, coins in sorted(by_entity.items()):
            out_path = out_dir / f"{entity_id}.yml"
            merged_coins, stats = merge_seed(coins, out_path)
            for k in merge_totals:
                merge_totals[k] += stats.get(k, 0)
            plain_coins = [_ruamel_to_dict(c) for c in merged_coins]
            out_path.write_text(
                _emit_v2_seed_file(src, entity_id, plain_coins),
                encoding="utf-8",
            )
            files_written += 1

    print(f"\n✓ Wrote {files_written} V2 seed file(s) under {SEED_V2}")
    print(f"  merge: merged_existing={merge_totals['merged_existing']}, "
          f"added_new={merge_totals['added_new']}, "
          f"orphan_curated={merge_totals['orphan_curated']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
