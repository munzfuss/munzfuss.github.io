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

  4. **`_curation_holds`** — per-entry escape hatch. Field names whose
     EXISTING state (present-or-absent) is frozen across regen. Stronger than
     CURATED_FIELDS — used when the curator REMOVED a default field, or
     REPLACED a parser-output verbatim.

     **Two accepted shapes** (both yield the same set of frozen field
     names via `set(...)` parsing; freeze semantics identical):

       List form (legacy, bare field list — backward-compatible):
         _curation_holds: [fineness, fineness_verified, verification_note]

       Dict form (PREFERRED — carries «why» rationale per field):
         _curation_holds:
           fineness: "Wilcke 1950 places c4h120 at .8889, not Hede's later .875"
           fineness_verified: ~                     # null = freeze without commentary
           verification_note: "removed — see fineness reason"

     The dict-form values are documentary only (free-text or `null`);
     `merge_seed` consumes only the keys via `set(_curation_holds)`.
     Curator authoring a NEW hold SHOULD use dict-form with a reason
     so future sessions understand the manual override without
     archaeological reconstruction.

Reference implementation: `scripts/maintenance/build_hede_denmark_seed.py`. This
module extracts the same logic for sibling builders (bruun / galster /
numismaster / numista) so the 4 mechanisms stay in sync across the seed pipeline
without 4× copy-paste.

Usage (in a builder):

    from lib.seed_merge import merge_seed

    entries, stats = merge_seed(entries, OUT_PATH)
    print(f"merge: merged={stats['merged_existing']}, "
          f"new={stats['added_new']}, orphan={stats['orphan_curated']}")

    # ... existing yaml.dump(out, f) path unchanged
"""
from __future__ import annotations

import json
import re
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

# §CN — inline source-index errata. A curator-recorded list, on the seed entry
# itself, of catalogue-index values a SOURCE mis-printed:
#   _source_errata:
#     - field: km          # the (catalog or top-level) field
#       printed: "48"      # what the source faithfully printed (provenance)
#       correct: "40"      # curator-verified correct value
#       reason: |          # why (evidence; survives without the chat)
#         Bruun Part III lot 12073 prints KM-48 on a Hede-14 coin; KM 48 = Hede 17.
#       curator: serg
# The block is curator-input, co-located with the source's own data (not a
# separate file), and is PRESERVED across regen exactly like _curation_holds.
# `apply_source_errata` overwrites the mis-printed value with `correct` AFTER
# the merge (so it wins over the parser, which keeps re-emitting the wrong
# value from the immutable cache), and records what it changed in
# `_errata_applied` for audit. Both keys are `_`-prefixed → auto-stripped
# before Coin validation + not rendered (build.py strips all `_`-keys).
_SOURCE_ERRATA_KEY = "_source_errata"
_ERRATA_APPLIED_KEY = "_errata_applied"

# Meta keys that NEVER flow from fresh and are NEVER dropped as stale — they
# carry curator intent that must survive every regen.
_PRESERVE_ALWAYS_KEYS = frozenset({_CURATION_HOLDS_KEY, _SOURCE_ERRATA_KEY})


def apply_source_errata(entry) -> None:
    """Apply the entry's `_source_errata` corrections in place (§CN).

    For each record, overwrite the mis-printed source value (catalog sub-field
    when `field` is a CatalogRefs field, else a top-level field) with the
    curator-verified `correct` value, and append a `{field, printed, correct}`
    record to `_errata_applied`. Idempotent. Must run LAST in the build so the
    correction wins over the parser/merge value (the source keeps printing the
    wrong index from the immutable harvest cache)."""
    errata = entry.get(_SOURCE_ERRATA_KEY)
    if not errata or not isinstance(errata, (list, tuple)):
        return
    try:
        from lib.catalog_codes import schema_catalog_fields
        cat_fields = schema_catalog_fields()
    except Exception:
        cat_fields = set()
    applied = []
    for e in errata:
        if not isinstance(e, dict):
            continue
        field = e.get("field")
        if not field or "correct" not in e:
            continue
        correct = e.get("correct")
        if field in cat_fields:
            cat = entry.get("catalog")
            if not isinstance(cat, dict):
                cat = {}
                entry["catalog"] = cat
            before = cat.get(field)
            cat[field] = correct
        else:
            before = entry.get(field)
            entry[field] = correct
        applied.append({
            "field": field,
            "printed": e.get("printed", before),
            "correct": correct,
        })
    if applied:
        entry[_ERRATA_APPLIED_KEY] = applied

# Verifiable measurement fields paired with their boolean «is source-attested?»
# flag. Verified-wins rule applies (CLAUDE.md §4).
_VERIFIABLE_FIELDS = {
    "fineness": "fineness_verified",
    "weight_rough_g": "weight_rough_verified",
    "diameter_mm": "diameter_mm_verified",
    "mint": "mint_verified",
    # Ruler attribution joined the verified set 2026-05-22 (after the
    # ucoin reign-window check landed). Per §4 generalisation: «any
    # `<field>` paired with a `<field>_verified` flag follows the
    # same precedence pattern». A reign-window-flagged unverified
    # ucoin ruler value defers to a verified Hede / NumisMaster /
    # Bruun attestation during merge.
    "ruler": "ruler_verified",
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


def _union_cat_values(existing_v, fresh_v):
    """Union two catalogue-field values (each scalar or list) into a
    deduped, order-preserving result; collapses a singleton back to
    scalar. String values dedup case-insensitively («406.1» vs «406.1»);
    non-string entries (e.g. KMRef dicts) pass through without string
    de-dup so dict-form km is never corrupted. Structured entries
    (KMRef dicts, nested lists) are deduped by normalised content so a
    repeated re-seed stays idempotent (a re-run must not append a second
    identical `{register: value}` dict to a list-form km). Existing
    values lead."""
    items: list = []
    for src in (existing_v, fresh_v):
        for v in (src if isinstance(src, list) else [src]):
            if v is not None:
                items.append(v)
    out: list = []
    seen: set = set()
    seen_struct: set = set()
    for v in items:
        if isinstance(v, (dict, list)):
            # Content-key dedup for structured entries (KMRef dicts etc.):
            # a stable JSON serialisation with sorted keys so
            # {'nor': '260', 'dk': '645'} == {'dk': '645', 'nor': '260'}.
            try:
                sk = json.dumps(v, sort_keys=True, ensure_ascii=False, default=str)
            except TypeError:  # pragma: no cover — unserialisable, keep as-is
                out.append(v)
                continue
            if sk not in seen_struct:
                seen_struct.add(sk)
                out.append(v)
            continue
        k = str(v).strip().lower()
        if k not in seen:
            seen.add(k)
            out.append(v)
    if not out:
        return existing_v
    return out[0] if len(out) == 1 else out


def merge_one(
    existing: CommentedMap, fresh: CommentedMap,
    extra_curated: frozenset = frozenset(),
) -> CommentedMap:
    """Apply the 4-mechanism merge: fresh values flow into existing, preserving
    curated decisions. Mutates and returns `existing`.

    `extra_curated` — per-builder field names treated as soft-curated for THIS
    call only (existing wins if present), on top of the global CURATED_FIELDS.
    Used e.g. by the Bruun builder to preserve `nominal` (its display
    normalisation lives outside the current parser; a naive regen would degrade
    «½ Portugaløser» → «1/2 Portugaloser»). Existing wins; fresh fills gaps."""
    holds = set(existing.get(_CURATION_HOLDS_KEY) or [])
    curated = CURATED_FIELDS | extra_curated
    fresh_keys = set(fresh.keys())
    existing_keys = set(existing.keys())

    for key in fresh_keys:
        if key in _PRESERVE_ALWAYS_KEYS:
            continue  # never flows from fresh; survives via existing
        if key in holds:
            # Frozen field: existing state wins (present-or-absent).
            continue
        if key in curated:
            # Soft-curated: existing wins if present, fresh fills gaps.
            if key in existing_keys:
                continue
            existing[key] = fresh[key]
            continue
        if key in DEEP_MERGE_FIELDS:
            ex_v = existing.get(key)
            fr_v = fresh.get(key)
            if isinstance(ex_v, dict) and isinstance(fr_v, dict):
                # List-capable catalogue sub-fields (km + every schema
                # list-field: hede/sieg/schou/lange/fr/dav/…) UNION their
                # existing + fresh values (§9a data-accumulation: a single
                # Numista type can cite multiple KM, e.g. mint sub-variants
                # 406.1/406.2 or the same coin across two Krause editions
                # 106/56). Scalar-only sub-fields keep existing-wins. A
                # curator who deliberately pruned a value freezes the whole
                # `catalog` via _curation_holds, which skips this branch
                # entirely (the `key in holds` guard above).
                try:
                    from lib.catalog_codes import schema_list_catalog_fields
                except Exception:  # pragma: no cover
                    from catalog_codes import schema_list_catalog_fields
                _list_cap = schema_list_catalog_fields() | {"km"}
                for sub_k, sub_v in fr_v.items():
                    if sub_k not in ex_v:
                        ex_v[sub_k] = sub_v
                    elif sub_k in _list_cap:
                        ex_v[sub_k] = _union_cat_values(ex_v[sub_k], sub_v)
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
        if key in _PRESERVE_ALWAYS_KEYS:
            continue
        if key in CURATED_FIELDS or key in holds:
            continue
        del existing[key]

    # §9.4 index hygiene on the MERGED catalog (post deep-merge). The
    # deep-merge keeps existing sub-keys verbatim, so a stale scalar
    # `schou: "20-21"` + `others: [schou# N]` shape survives the merge
    # even though the fresh builder now emits clean list-form. Fold the
    # `others: <code># N` overflow into its typed list-field (case-
    # insensitive code) and de-dup list values case-insensitively
    # («55C» / «55c» → one «55C»). Skipped when the curator froze
    # `catalog` via `_curation_holds`.
    if "catalog" not in holds and isinstance(existing.get("catalog"), dict):
        try:
            from lib.catalog_codes import normalise_catalog as _fold_cat
        except Exception:  # pragma: no cover
            from catalog_codes import normalise_catalog as _fold_cat
        _fold_cat(existing["catalog"])

    return existing


def merge_seed(
    coins_fresh: list, out_path: Path,
    extra_curated: frozenset = frozenset(),
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
            merged = merge_one(existing_by_id[cid], fresh, extra_curated)
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

    # 2b. Drop an UNCURATED bare base entry that FRESH sub-entries now supersede:
    #     a fresh id = bare id + an alpha sub-letter suffix (e.g. «…c4h117»
    #     superseded by fresh «…c4h117a»/«…c4h117b» once the parser learns to
    #     break out the sub-variants). Applies to orphan-kept AND freshly-built
    #     bare entries, so the seed never carries both the bare page AND its
    #     sub-letters. The sibling must be FRESH (not a stale orphan), so a bare
    #     whose only sub-letter is itself a stale orphan is left untouched.
    #     Curated bases (real fuss / `_curation_holds`) are always kept.
    #     NB: merge_decisions that reference a dropped bare id are resolved by
    #     the cross-source merger's `_expand_member` (bare → sub-letters), so
    #     dropping the bare here does NOT dangle those references.
    fresh_ids = set(fresh_by_id)

    def _is_curated(c) -> bool:
        if not isinstance(c, dict):
            return True
        if c.get("_curation_holds"):
            return True
        return c.get("fuss") not in (None, "seed_unsorted")

    def _own_cat_has_subletter(c) -> bool:
        """True if the entry's OWN-source catalogue value already carries a
        sub-letter (e.g. galster «66A-B», hede «117A»). Such an entry is
        itself a sub-VARIANT page, not a bare PARENT that fresh sub-letters
        supersede — so it must NOT be dropped. The catalogue field is found
        from the id's source token («dk-galster-f1g-66» → galster «66A-B»;
        «dk-hede-c4h117» → hede «117»). Without this guard the id-string
        pattern alone («66» + fresh «66c») wrongly drops Galster 66A-B as if
        66C superseded it, when 66A-B and 66C are DISTINCT sub-variants of the
        same coin (both worth keeping). Caught 2026-06-10."""
        if not isinstance(c, dict):
            return False
        cat = c.get("catalog") or {}
        for tok in (c.get("id") or "").split("-"):
            if tok in cat:
                vals = cat[tok]
                vals = vals if isinstance(vals, list) else [vals]
                return any(re.search(r"[A-Za-z]", str(v)) for v in vals if v)
        return False

    kept = []
    for c in out:
        cid = c.get("id") if isinstance(c, dict) else None
        superseded = bool(
            cid and re.search(r"\d$", cid) and not _is_curated(c)
            and not _own_cat_has_subletter(c)
            and any(fid != cid and fid.startswith(cid) and fid[len(cid):].isalpha()
                    for fid in fresh_ids)
        )
        if superseded:
            stats["superseded_dropped"] = stats.get("superseded_dropped", 0) + 1
            if cid not in fresh_ids:
                stats["orphan_curated"] -= 1
            continue
        kept.append(c)
    out = kept

    # 3. Apply curator-recorded source-index errata (§CN) LAST — after the
    # merge so the correction wins over the parser value, on every output
    # entry (merged, freshly-added, or orphan-preserved).
    for c in out:
        if isinstance(c, dict):
            apply_source_errata(c)

    return out, stats
