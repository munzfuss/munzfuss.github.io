"""V2-native seed writer — shared helper for seed builders.

Replaces the V1→V2 indirection that runs every V1 builder through
`seed_v2_regroup.py` to translate location-keyed output into entity-
keyed V2 seed yamls. Each builder calls `write_v2_seed(coins, source)`
directly and the result lands in `data/v2/seed/<source>/<entity>.yml`
ready for the cross-source merger.

Per V2_PIPELINE.md §3.10: when a coin has list-form `issuing_entity`
(joint mint, e.g. `[danish_realm, royal_holstein]` for Altona+Kopenhagen),
the HOME FILE is the alphabetically-first entity. Build assembly's
inverse-index pass surfaces the coin on every consumer page whose
`consumes_entities` intersects with the list.

Per CLAUDE.md «V2 entity-keyed pipeline»: V1 is FROZEN; new builders
write V2 directly. The previous `data/seed/<source>/<location>.yml`
output path is no longer touched by these builders.

Curation preservation: each per-entity write goes through
`lib.seed_merge.merge_seed`, so existing curator-set `fuss`/`phase`/
`issuing_entity`/`note`/`*_verified` flags survive regeneration.
Orphan curated entries (in V2 seed but no longer in the fresh build)
stay verbatim — no silent data loss.
"""
from __future__ import annotations

import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

import ruamel.yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from lib.paths import PROJECT_ROOT  # noqa: E402
from lib.seed_merge import merge_seed  # noqa: E402

V2_SEED_ROOT = PROJECT_ROOT / "data" / "v2" / "seed"


def _home_entity(coin: dict) -> str | None:
    """Return the home-file entity for a coin.

    - Scalar `issuing_entity`: that entity.
    - List-form `issuing_entity` (joint mint): alphabetically-first
      entity, per V2_PIPELINE.md §3.10.
    - Missing / empty: None (caller routes to `_unclassified.yml`).
    """
    ie = coin.get("issuing_entity")
    if isinstance(ie, str) and ie:
        return ie
    if isinstance(ie, list) and ie:
        return sorted(str(e) for e in ie if e)[0]
    return None


def write_v2_seed(
    coins: list[dict],
    source_name: str,
    scope_note: str,
    *,
    source_label: str | None = None,
    dry_run: bool = False,
    no_merge: bool = False,
    extra_top_level: dict | None = None,
) -> dict:
    """Group `coins` by `issuing_entity` → write
    `data/v2/seed/<source_name>/<entity>.yml` per entity.

    Parameters
    ----------
    coins : list of Coin-schema dicts. Each must carry `issuing_entity`
        (scalar or list-form). Coins with missing/empty issuing_entity
        route to `_unclassified.yml` for curator review.
    source_name : subdirectory under `data/v2/seed/` to write into.
        E.g. "hede" → `data/v2/seed/hede/`.
    scope_note : human-readable string describing the source + scope.
        Emitted as the `scope_note` header in every output yaml.
    source_label : optional value for the `source` header (defaults
        to source_name).
    dry_run : if True, only logs stats and skips writes.
    no_merge : if True, wholesale-overwrites existing seed yamls
        without `merge_seed` curation preservation. Destructive — use
        only for verification or fresh-build scenarios.
    extra_top_level : optional dict of extra header keys to merge into
        every output yaml's top level (e.g. {"scope_year_from": 1514}).

    Returns
    -------
    dict with summary stats:
      {
        "entities_written": [...],
        "per_entity": {entity: {merged_existing, added_new, orphan_curated, total}},
        "unclassified_count": N,
      }
    """
    by_entity: dict[str, list[dict]] = defaultdict(list)
    unclassified: list[dict] = []
    for c in coins:
        home = _home_entity(c)
        if home is None:
            unclassified.append(c)
            continue
        by_entity[home].append(c)

    src_dir = V2_SEED_ROOT / source_name
    src_dir.mkdir(parents=True, exist_ok=True)

    stats = {
        "entities_written": [],
        "per_entity": {},
        "unclassified_count": len(unclassified),
    }

    print(f"\n[{source_name}] grouping → {len(by_entity)} entities, "
          f"{len(unclassified)} unclassified")
    for entity in sorted(by_entity.keys()):
        ents = by_entity[entity]
        # Sort stable for clean diffs
        ents.sort(key=lambda e: (e.get("year_first") or 9999, e.get("id") or ""))
        out_path = src_dir / f"{entity}.yml"
        merge_stats = {"merged_existing": 0, "added_new": len(ents), "orphan_curated": 0}
        if not dry_run and not no_merge:
            ents, merge_stats = merge_seed(ents, out_path)

        print(f"  [{entity}] {len(ents)} entries  "
              f"(merged={merge_stats['merged_existing']}, "
              f"added={merge_stats['added_new']}, "
              f"orphan_curated={merge_stats['orphan_curated']})")

        if dry_run:
            stats["per_entity"][entity] = {**merge_stats, "total": len(ents)}
            continue

        yaml = ruamel.yaml.YAML(typ="rt")
        yaml.preserve_quotes = True
        yaml.width = 200
        yaml.indent(mapping=2, sequence=4, offset=2)
        out = {
            "status": "seed",
            "source": source_label or source_name,
            "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "entity": entity,
            "scope_note": scope_note,
        }
        if extra_top_level:
            for k, v in extra_top_level.items():
                if k not in out:
                    out[k] = v
        out["coins"] = ents
        with out_path.open("w") as f:
            yaml.dump(out, f)
        stats["entities_written"].append(entity)
        stats["per_entity"][entity] = {**merge_stats, "total": len(ents)}

    # Unclassified bucket — keep coins that the entity classifier failed
    # to resolve so curators can triage them without losing source data.
    if unclassified:
        unclass_path = src_dir / "_unclassified.yml"
        unclassified.sort(key=lambda e: (e.get("year_first") or 9999, e.get("id") or ""))
        merge_stats = {"merged_existing": 0, "added_new": len(unclassified), "orphan_curated": 0}
        if not dry_run and not no_merge:
            unclassified, merge_stats = merge_seed(unclassified, unclass_path)
        print(f"  [_unclassified] {len(unclassified)} entries")
        if not dry_run:
            yaml = ruamel.yaml.YAML(typ="rt")
            yaml.preserve_quotes = True
            yaml.width = 200
            yaml.indent(mapping=2, sequence=4, offset=2)
            out = {
                "status": "seed",
                "source": source_label or source_name,
                "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                "entity": "_unclassified",
                "scope_note": (
                    f"{scope_note} — entries the mint→entity classifier "
                    "could not resolve. Curator triage required: assign "
                    "`issuing_entity` per coin, then re-run the builder."
                ),
                "coins": unclassified,
            }
            with unclass_path.open("w") as f:
                yaml.dump(out, f)
        stats["per_entity"]["_unclassified"] = {**merge_stats, "total": len(unclassified)}

    # Summary
    by_realm = Counter(e for entity, ents in by_entity.items() for e in [entity] for _ in ents)
    print(f"\n[{source_name}] wrote V2 seed: "
          f"{len(stats['entities_written'])} entity file(s)"
          f"{', 1 unclassified file' if unclassified else ''}")
    return stats
