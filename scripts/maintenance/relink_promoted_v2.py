#!/usr/bin/env python3
"""V2 Phase 6 — materialise the bidirectional seed↔curated link.

Per V2_PIPELINE.md §3.3:
  - CURATED side carries `composed_of: [seed_id, ...]` — list of seed
    entries the curator absorbed into this canonical curated coin.
  - SEED side carries `promoted_to: <curated_id>` — pointer back to the
    curated entry that subsumes this seed entry.

`composed_of` is the AUTHORITATIVE side (curator writes it on the curated
coin during Phase 4 / §9a multi-specimen merge). This script derives
`promoted_to` on each referenced seed entry across all sources.

The bidirectional link IS the audit trail of every merge:
  - Records WHAT got absorbed WHERE (the parent entry's `composed_of`
    list names each absorbed seed; the seed's `promoted_to` points
    back to its canonical home).
  - Re-runs are safe: this script reads `composed_of` and only ADDS /
    UPDATES `promoted_to`; it never overwrites curator edits or drops
    data. The seed entry itself stays on disk (build assembly drops it
    from rendering via `promoted_to != None`, but the data is
    preserved for orphan-detection + integrity audits).
  - Data-loss invariant: a curated entry that absorbs a seed MUST
    carry the seed's measurement + source data (otherwise the merge
    was lossy). This script's integrity audit flags suspected losses.

Usage:
  scripts/maintenance/relink_promoted_v2.py --dry-run    # report only
  scripts/maintenance/relink_promoted_v2.py --apply      # update seed yamls
  scripts/maintenance/relink_promoted_v2.py --audit      # integrity only

Idempotent — re-runs produce zero file changes when the link state is
already consistent. Safe to add to a routine «after harvest update» chain.
"""

from __future__ import annotations

import argparse
import sys
from collections import defaultdict
from pathlib import Path

import yaml
import ruamel.yaml

ROOT = Path(__file__).resolve().parents[2]
V2_FINAL = ROOT / "data" / "v2" / "final"
V2_SEED = ROOT / "data" / "v2" / "seed"

sys.path.insert(0, str(ROOT / "scripts"))


def _rt_yaml() -> ruamel.yaml.YAML:
    """Round-trip YAML — preserves comments, key order, scalar styles.
    Used for seed yaml writes so the regroup-emitted file header survives
    a relink modification (otherwise the next seed_v2_regroup run would
    re-add the header → flap → not idempotent across the chain)."""
    y = ruamel.yaml.YAML()
    y.preserve_quotes = True
    y.width = 120
    y.indent(mapping=2, sequence=2, offset=0)
    return y


def _load_yaml(p: Path) -> dict:
    return yaml.safe_load(p.read_text(encoding="utf-8")) or {}


def _ruamel_to_dict(c):
    """Delegate to lib.v2_resolver.ruamel_to_plain."""
    from lib.v2_resolver import ruamel_to_plain
    return ruamel_to_plain(c)


def _build_composed_of_index() -> dict[str, str]:
    """Walks data/v2/final/*.yml and returns {seed_id: curated_id}
    for every (curated, seed) pair declared via `composed_of`."""
    seed_to_curated: dict[str, str] = {}
    duplicates: list[tuple[str, str, str]] = []  # seed_id, curated_a, curated_b

    for path in sorted(V2_FINAL.glob("*.yml")):
        doc = _load_yaml(path)
        for c in doc.get("coins") or []:
            cid = c.get("id")
            composed = c.get("composed_of") or []
            if not cid or not composed:
                continue
            for seed_id in composed:
                if seed_id in seed_to_curated and seed_to_curated[seed_id] != cid:
                    duplicates.append((seed_id, seed_to_curated[seed_id], cid))
                    continue
                seed_to_curated[seed_id] = cid

    if duplicates:
        print(f"⚠  WARN: {len(duplicates)} seed id(s) referenced from "
              f"multiple curated entries — first-seen wins per entry:")
        for sid, ca, cb in duplicates[:10]:
            print(f"     {sid!r} in composed_of of BOTH {ca!r} and {cb!r}")

    return seed_to_curated


def _walk_seed_yamls_rt() -> dict[Path, object]:
    """Returns {path: round-trip-loaded doc} for every seed yaml. Round-trip
    mode preserves comments + key order, so a `promoted_to` add doesn't
    erase the regroup-emitted header. Used for the apply path."""
    out: dict[Path, object] = {}
    if not V2_SEED.exists():
        return out
    rt = _rt_yaml()
    for src_dir in sorted(V2_SEED.iterdir()):
        if not src_dir.is_dir():
            continue
        for p in sorted(src_dir.glob("*.yml")):
            out[p] = rt.load(p.read_text(encoding="utf-8"))
    return out


def _walk_seed_yamls() -> dict[Path, dict]:
    """Plain-load version for read-only scans (composed_of audit etc.)."""
    out: dict[Path, dict] = {}
    if not V2_SEED.exists():
        return out
    for src_dir in sorted(V2_SEED.iterdir()):
        if not src_dir.is_dir():
            continue
        for p in sorted(src_dir.glob("*.yml")):
            out[p] = _load_yaml(p)
    return out


def _relink(
    seed_to_curated: dict[str, str], apply_changes: bool
) -> dict:
    """Walks all seed yamls; for each seed coin whose id is referenced
    by some curated composed_of, set `promoted_to: <curated_id>`. Also
    detects and removes stale promoted_to (pointing at a curated entry
    that no longer composes-of this seed)."""

    stats: dict = {
        "seeds_total": 0,
        "set_promoted_to": [],       # (seed_id, curated_id) — newly linked
        "updated_promoted_to": [],    # (seed_id, old, new) — re-pointed
        "cleared_promoted_to": [],    # (seed_id, stale_curated_id) — orphaned
        "already_correct": 0,
        "files_modified": [],
        "missing_seed_ids": [],       # composed_of refs a non-existent seed
    }

    # Use round-trip loader when applying (preserves headers + comments
    # + key order); plain loader is enough for dry-run.
    docs = _walk_seed_yamls_rt() if apply_changes else _walk_seed_yamls()

    # Index seeds by id for missing-ref detection.
    seed_id_index: dict[str, tuple[Path, int]] = {}
    for path, doc in docs.items():
        for i, c in enumerate(doc.get("coins") or []):
            sid = c.get("id")
            if sid:
                seed_id_index[sid] = (path, i)

    # Detect composed_of refs that don't resolve to any seed.
    for sid, cid in seed_to_curated.items():
        if sid not in seed_id_index:
            stats["missing_seed_ids"].append((sid, cid))

    # Process every seed coin.
    rt = _rt_yaml() if apply_changes else None
    for path, doc in docs.items():
        coins = doc.get("coins") or []
        modified = False
        for c in coins:
            stats["seeds_total"] += 1
            sid = c.get("id")
            if not sid:
                continue
            target = seed_to_curated.get(sid)
            current = c.get("promoted_to")

            if target is None and current is None:
                continue
            if target == current:
                stats["already_correct"] += 1
                continue
            if target is None and current is not None:
                # Stale link — composed_of no longer references this seed
                stats["cleared_promoted_to"].append((sid, current))
                if apply_changes:
                    c.pop("promoted_to", None)
                    modified = True
                continue
            if current is None:
                stats["set_promoted_to"].append((sid, target))
            else:
                stats["updated_promoted_to"].append((sid, current, target))
            if apply_changes:
                c["promoted_to"] = target
                modified = True
        if modified and apply_changes:
            stats["files_modified"].append(path)
            with path.open("w", encoding="utf-8") as f:
                rt.dump(doc, f)

    return stats


def _integrity_audit(
    seed_to_curated: dict[str, str], stats: dict
) -> dict:
    """Checks the merge invariant: a curated entry that absorbs a seed
    MUST carry the seed's measurement + source data (otherwise the merge
    was lossy).

    For each (seed_id, curated_id) pair, compare:
      - weight_rough_g values: every seed reading must appear in curated
        (as a list entry or scalar match)
      - fineness: same
      - sources: at minimum the seed's URL should appear in curated's
        sources list (curator may have rewritten the ref string)
    Reports suspected losses; user resolves manually.
    """
    audit: dict = {
        "weight_loss_suspects": [],
        "fineness_loss_suspects": [],
        "source_url_loss_suspects": [],
    }

    # Pre-load curated by id
    curated_by_id: dict[str, dict] = {}
    for path in sorted(V2_FINAL.glob("*.yml")):
        doc = _load_yaml(path)
        for c in doc.get("coins") or []:
            cid = c.get("id")
            if cid:
                curated_by_id[cid] = c

    # Pre-load seed by id
    seed_by_id: dict[str, dict] = {}
    docs = _walk_seed_yamls()
    for path, doc in docs.items():
        for c in doc.get("coins") or []:
            sid = c.get("id")
            if sid:
                seed_by_id[sid] = c

    def _weights(coin: dict) -> set[float]:
        w = coin.get("weight_rough_g")
        if w is None:
            return set()
        if isinstance(w, (int, float)):
            return {round(float(w), 3)}
        if isinstance(w, list):
            out = set()
            for item in w:
                if isinstance(item, dict) and isinstance(item.get("value"), (int, float)):
                    out.add(round(float(item["value"]), 3))
                elif isinstance(item, (int, float)):
                    out.add(round(float(item), 3))
            return out
        return set()

    def _fineness(coin: dict) -> set[float]:
        f = coin.get("fineness")
        if f is None:
            return set()
        if isinstance(f, (int, float)):
            return {round(float(f), 4)}
        if isinstance(f, list):
            out = set()
            for item in f:
                if isinstance(item, dict) and isinstance(item.get("value"), (int, float)):
                    out.add(round(float(item["value"]), 4))
                elif isinstance(item, (int, float)):
                    out.add(round(float(item), 4))
            return out
        return set()

    def _source_urls(coin: dict) -> set[str]:
        out = set()
        for s in coin.get("sources") or []:
            if isinstance(s, dict) and s.get("url"):
                out.add(s["url"])
        return out

    for seed_id, curated_id in seed_to_curated.items():
        seed = seed_by_id.get(seed_id)
        curated = curated_by_id.get(curated_id)
        if not seed or not curated:
            continue

        sw = _weights(seed)
        cw = _weights(curated)
        missing_w = sw - cw
        if missing_w:
            audit["weight_loss_suspects"].append({
                "seed_id": seed_id,
                "curated_id": curated_id,
                "missing_weights": sorted(missing_w),
            })

        sf = _fineness(seed)
        cf = _fineness(curated)
        missing_f = sf - cf
        if missing_f:
            audit["fineness_loss_suspects"].append({
                "seed_id": seed_id,
                "curated_id": curated_id,
                "missing_fineness": sorted(missing_f),
            })

        su = _source_urls(seed)
        cu = _source_urls(curated)
        missing_u = su - cu
        if missing_u:
            audit["source_url_loss_suspects"].append({
                "seed_id": seed_id,
                "curated_id": curated_id,
                "missing_urls": sorted(missing_u),
            })

    return audit


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", default=True,
                        help="Report only (default)")
    parser.add_argument("--apply", action="store_true",
                        help="Write promoted_to changes into seed yamls")
    parser.add_argument("--audit", action="store_true",
                        help="Run merge-integrity audit (data-loss detection)")
    args = parser.parse_args()
    if args.apply:
        args.dry_run = False

    print("V2 Phase 6 — bidirectional seed↔curated link materialiser\n")

    seed_to_curated = _build_composed_of_index()
    print(f"composed_of pairs across V2 curated: {len(seed_to_curated)}")

    if not seed_to_curated:
        print("\nNo composed_of entries yet — nothing to relink. ✓")
        if args.audit:
            print("\n(audit skipped — no pairs)")
        return 0

    stats = _relink(seed_to_curated, apply_changes=args.apply)

    print(f"\nSeed coins scanned: {stats['seeds_total']}")
    print(f"  already correct:        {stats['already_correct']}")
    print(f"  set promoted_to (new):  {len(stats['set_promoted_to'])}")
    print(f"  updated promoted_to:    {len(stats['updated_promoted_to'])}")
    print(f"  cleared stale link:     {len(stats['cleared_promoted_to'])}")
    print(f"  files modified:         {len(stats['files_modified'])}")

    for sid, cid in stats["set_promoted_to"][:5]:
        print(f"    + {sid!r} → promoted_to: {cid!r}")
    if len(stats["set_promoted_to"]) > 5:
        print(f"    + ... and {len(stats['set_promoted_to']) - 5} more")
    for sid, old, new in stats["updated_promoted_to"][:5]:
        print(f"    ~ {sid!r}: {old!r} → {new!r}")
    for sid, stale in stats["cleared_promoted_to"][:5]:
        print(f"    - {sid!r} cleared (was → {stale!r}; no longer in composed_of)")

    if stats["missing_seed_ids"]:
        print(f"\n⚠  composed_of references {len(stats['missing_seed_ids'])} non-existent seed id(s):")
        for sid, cid in stats["missing_seed_ids"][:10]:
            print(f"     {cid!r} → composed_of: [{sid!r}, ...]")
        if len(stats["missing_seed_ids"]) > 10:
            print(f"     ... and {len(stats['missing_seed_ids']) - 10} more")

    if args.audit:
        audit = _integrity_audit(seed_to_curated, stats)
        print("\n=== Merge-integrity audit ===")
        for cat, label in [
            ("weight_loss_suspects", "Weight values present in seed but not curated"),
            ("fineness_loss_suspects", "Fineness values present in seed but not curated"),
            ("source_url_loss_suspects", "Source URLs present in seed but not curated"),
        ]:
            entries = audit[cat]
            print(f"\n{label}: {len(entries)}")
            for e in entries[:5]:
                print(f"  {e}")
            if len(entries) > 5:
                print(f"  ... and {len(entries) - 5} more")

    if args.dry_run:
        print("\n--- DRY RUN — no files written. Re-run with --apply to commit. ---")

    return 0


if __name__ == "__main__":
    sys.exit(main())
