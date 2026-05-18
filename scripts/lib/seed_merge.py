"""Manual-override preservation for seed builders — shared module (§BL).

Per `docs/ARCHITECTURE.md §«Manual-override preservation»` + CLAUDE.md §«Project
state — pipeline overview»: when a curator manually edits a field on an existing
seed entry, the seed-regenerator MUST preserve that edit on subsequent runs.

Pattern: existing-seed entries identified by `id` field; `merge_one(existing,
fresh)` applies the 4-mechanism merge:

  1. **CURATED_FIELDS** — soft-curated. Existing wins if present; absence means
     the field hasn't been curated yet, so fresh's default value (typically a
     sentinel like `seed_unsorted`) is taken.

  2. **DEEP_MERGE_FIELDS** — dict deep-merge. Keys present in existing win;
     fresh's keys fill gaps. `catalog` is the only such field in practice
     (curation often adds Bruun citation keys on top of the parser's KM/Hede/
     Sieg keys).

  3. **_VERIFIABLE_FIELDS** — verified-wins-over-unverified. Per CLAUDE.md §4,
     when both candidates have a value for a measurement field (fineness /
     weight_rough_g / diameter_mm / mint), and EXISTING is source-attested
     (`*_verified: true`) while FRESH is unverified (`(?)` marker — absent flag
     or false), the source-attested existing value wins.

  4. **`_curation_holds`** — per-entry escape hatch. List of field names whose
     EXISTING state (present-or-absent) is frozen across regen. Stronger than
     CURATED_FIELDS — used when the curator REMOVED a default field, or
     REPLACED a parser-output verbatim.

Reference implementation: `scripts/maintenance/build_hede_denmark_seed.py`. This
module extracts the same logic for sibling builders (bruun / galster /
numismaster / numista) so the 4 mechanisms stay in sync across the seed pipeline
without 4× copy-paste.

Usage (in a builder):

    from lib.seed_merge import merge_seed

    if not args.no_merge:
        entries, stats = merge_seed(entries, OUT_PATH)
        print(f"merge: merged={stats['merged_existing']}, "
              f"new={stats['added_new']}, orphan={stats['orphan_curated']}")

    # ... existing yaml.dump(out, f) path unchanged
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import ruamel.yaml
from ruamel.yaml.comments import CommentedMap

# Soft-curated fields: existing wins when present.
CURATED_FIELDS = frozenset({
    "fuss",
    "phase",
    "fraction",
    "issuing_entity",
    "kind",
    "note",
    "mint_verified",
    "verified",
    # V2 bidirectional seed↔curated link (Phase 6) — both fields are
    # curator-maintained or relink-script-derived audit trail of the
    # §9a multi-specimen merge. They MUST persist across regen so that:
    #   - a curated coin with `composed_of: [seed_a, seed_b]` keeps that
    #     list when V2 curated regen runs;
    #   - a seed coin with `promoted_to: <curated_id>` keeps the pointer
    #     when V2 seed regroup runs (build assembly drops it from
    #     rendering, so losing the pointer would re-surface the seed as
    #     duplicate of its curated host).
    "composed_of",
    "promoted_to",
})

# Deep-merged dict fields: existing keys win, fresh fills gaps.
DEEP_MERGE_FIELDS = frozenset({
    "catalog",
})

# Per-entry meta-field listing additional frozen fields. Stripped from output
# entry (private to merge logic; survives via existing across regen).
_CURATION_HOLDS_KEY = "_curation_holds"

# Verifiable measurement fields paired with their boolean «is source-attested?»
# flag. Verified-wins rule applies (CLAUDE.md §4).
_VERIFIABLE_FIELDS = {
    "fineness": "fineness_verified",
    "weight_rough_g": "weight_rough_verified",
    "diameter_mm": "diameter_mm_verified",
    "mint": "mint_verified",
}


def _make_yaml_loader() -> ruamel.yaml.YAML:
    """Round-trip YAML loader. Matches the dumper config used in the builders so
    style + comments + key order survive the merge cycle."""
    yaml = ruamel.yaml.YAML()
    yaml.preserve_quotes = True
    yaml.width = 200
    yaml.indent(mapping=2, sequence=4, offset=2)
    return yaml


def load_existing_seed(out_path: Path) -> tuple[Any, dict[str, CommentedMap]]:
    """Read the existing on-disk seed at `out_path` if any. Returns
    (full_doc_or_None, id → coin map). When the file doesn't exist or has no
    `coins` list, returns (None, {})."""
    if not out_path.exists():
        return None, {}
    yaml = _make_yaml_loader()
    doc = yaml.load(out_path.read_text())
    if doc is None:
        return None, {}
    coins = doc.get("coins") if isinstance(doc, dict) else None
    if not coins:
        return doc, {}
    by_id: dict[str, CommentedMap] = {}
    for c in coins:
        cid = c.get("id") if isinstance(c, dict) else None
        if cid:
            by_id[cid] = c
    return doc, by_id


def merge_one(existing: CommentedMap, fresh: CommentedMap) -> CommentedMap:
    """Apply the 4-mechanism merge: fresh values flow into existing, preserving
    curated decisions. Mutates and returns `existing`."""
    holds = set(existing.get(_CURATION_HOLDS_KEY) or [])
    fresh_keys = set(fresh.keys())
    existing_keys = set(existing.keys())

    for key in fresh_keys:
        if key == _CURATION_HOLDS_KEY:
            continue  # never flows from fresh; survives via existing
        if key in holds:
            # Frozen field: existing state wins (present-or-absent).
            continue
        if key in CURATED_FIELDS:
            # Soft-curated: existing wins if present, fresh fills gaps.
            if key in existing_keys:
                continue
            existing[key] = fresh[key]
            continue
        if key in DEEP_MERGE_FIELDS:
            ex_v = existing.get(key)
            fr_v = fresh.get(key)
            if isinstance(ex_v, dict) and isinstance(fr_v, dict):
                for sub_k, sub_v in fr_v.items():
                    if sub_k not in ex_v:
                        ex_v[sub_k] = sub_v
            elif ex_v is None and fr_v is not None:
                existing[key] = fr_v
            continue
        if key in _VERIFIABLE_FIELDS:
            # Verified-wins-over-unverified rule (CLAUDE.md §4).
            verified_flag = _VERIFIABLE_FIELDS[key]
            existing_verified = bool(existing.get(verified_flag))
            fresh_verified = bool(fresh.get(verified_flag))
            if (
                key in existing_keys
                and existing_verified
                and not fresh_verified
            ):
                continue
        # Default: fresh wins.
        existing[key] = fresh[key]

    # Drop existing-only keys that are NEITHER curated NOR in the holds set.
    # Curated absences must persist; un-curated stale keys go away when the
    # parser stops emitting them.
    drop_candidates = existing_keys - fresh_keys
    for key in drop_candidates:
        if key == _CURATION_HOLDS_KEY:
            continue
        if key in CURATED_FIELDS or key in holds:
            continue
        del existing[key]

    return existing


def merge_seed(
    coins_fresh: list, out_path: Path
) -> tuple[list, dict[str, int]]:
    """Merge fresh-generated coins against the on-disk seed at `out_path`.

    Returns (merged_coins, stats). Stats keys:
      merged_existing — fresh entries merged into existing curated entries
      added_new       — fresh entries with no existing match
      orphan_curated  — existing entries the parser no longer produces; kept
                        verbatim to avoid silent data loss
    """
    _, existing_by_id = load_existing_seed(out_path)
    fresh_by_id: dict[str, Any] = {c["id"]: c for c in coins_fresh if c.get("id")}

    stats = {"merged_existing": 0, "added_new": 0, "orphan_curated": 0}
    out: list = []

    # 1. For every fresh entry, merge into existing or take fresh.
    for cid, fresh in fresh_by_id.items():
        if cid in existing_by_id:
            merged = merge_one(existing_by_id[cid], fresh)
            out.append(merged)
            stats["merged_existing"] += 1
        else:
            out.append(fresh)
            stats["added_new"] += 1

    # 2. Orphan curated entries (in existing but not fresh) — keep verbatim.
    orphan_ids = set(existing_by_id) - set(fresh_by_id)
    for cid in sorted(orphan_ids):
        out.append(existing_by_id[cid])
        stats["orphan_curated"] += 1

    return out, stats
