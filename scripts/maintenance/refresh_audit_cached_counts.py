#!/usr/bin/env python3
"""Refresh stale cached_count / cached_tids / gap_tids in ucoin + Numista
audit manifests from the actual on-disk cache state.

WHY
---
The harvest audit manifests (``scripts/cache/{ucoin,numista}/_*.json``) record,
per bucket, which catalogue ids are already cached vs. still a gap. They are
generated once (e.g. BR-audit-4 on 2026-05-24) and then go stale as the hourly
harvest routine caches more ids without rewriting the whole audit. The routine's
bucket picker reads these counts, so a stale ``cached_count: 0`` on an already-
fully-cached bucket makes the picker re-offer it and burn a run on defensive
sampling (anomaly ``audit_manifest_scope_drift:field=cached_count`` in
``docs/anomaly_log.yml``: ``brunswick_luneburg_p1082`` was 61/61 on disk but the
audit still said 0/61).

WHAT
----
For every bucket whose schema carries an enumerable id list, recompute:
  * cached set  = bucket ids that have a ``<id>.json`` file in the cache dir
  * gap list    = bucket ids without a cache file (ORIGINAL ORDER preserved —
                  the picker takes the head first, so order is load-bearing)
  * cached_count / cached_tids (where those fields exist)
``oos_excluded_tids`` (out-of-mission ids parked by a scope split, e.g. the
osnabruck_p3057 1482-1558 TIDs) are NOT part of the harvestable universe and are
left untouched.

Schemas handled (auto-detected):
  * ucoin flat  — ``buckets.<name>`` with gap_tids [+ cached_tids/cached_count]
                  (BR-audit-4; BR-audit-3 has gap_tids only → gap trimmed)
  * numista flat — ``in_scope_buckets.<name>`` with in_scope_nids/gap_nids/
                  cached_count (BO.7)
  * numista nested — ``in_scope_buckets.<country>.<period>`` leaves with the
                  same fields (BO.6)
Prose-style audits with no per-bucket id lists (BR-audit-2, the 2026-05-18
audits, BO.1, BO.5) are reported as skipped.

USAGE
-----
    python scripts/maintenance/refresh_audit_cached_counts.py            # dry-run, report only
    python scripts/maintenance/refresh_audit_cached_counts.py --write    # persist changes
    python scripts/maintenance/refresh_audit_cached_counts.py --write --only ucoin/_BR_audit-4_2026-05-24.json

Files are rewritten with ``json.dumps(ensure_ascii=False, indent=2)`` and the
original file's trailing-newline state preserved (BO.6 has none, the rest do),
so a no-op run produces a zero-byte diff.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CACHE = ROOT / "scripts" / "cache"
UCOIN_DIR = CACHE / "ucoin"
NUMISTA_DIR = CACHE / "numista"

# Audit manifests to consider (glob-discovered, then schema-filtered).
AUDIT_GLOBS = [
    ("ucoin", "_BR_audit*.json"),
    ("numista", "_BO*_audit*.json"),
]


def _cache_has(cache_dir: Path, ident) -> bool:
    return (cache_dir / f"{ident}.json").exists()


def _split(ids: list, cache_dir: Path) -> tuple[list, list]:
    """Return (cached, gap) preserving the input order in each."""
    cached = [i for i in ids if _cache_has(cache_dir, i)]
    gap = [i for i in ids if not _cache_has(cache_dir, i)]
    return cached, gap


def _refresh_ucoin_bucket(b: dict) -> dict | None:
    """ucoin flat bucket. Returns a change-record dict if anything changed."""
    if "gap_tids" not in b:
        return None
    oos = set(str(k) for k in (b.get("oos_excluded_tids") or {}).keys())
    # Harvestable universe = current gap ∪ already-cached, minus oos-excluded.
    universe: list = []
    seen = set()
    for t in list(b.get("gap_tids") or []) + list(b.get("cached_tids") or []):
        if str(t) in oos:
            continue
        if t not in seen:
            seen.add(t)
            universe.append(t)
    cached, gap = _split(universe, UCOIN_DIR)
    before = (len(b.get("cached_tids") or []) if "cached_tids" in b else b.get("cached_count"),
              len(b.get("gap_tids") or []))
    changed = False
    if "cached_tids" in b and list(b.get("cached_tids") or []) != cached:
        b["cached_tids"] = cached
        changed = True
    if "cached_count" in b and b.get("cached_count") != len(cached):
        b["cached_count"] = len(cached)
        changed = True
    if list(b.get("gap_tids") or []) != gap:
        b["gap_tids"] = gap
        changed = True
    if not changed:
        return None
    return {"cached": len(cached), "gap": len(gap), "before_cached": before[0], "before_gap": before[1]}


def _refresh_numista_bucket(b: dict) -> dict | None:
    """numista bucket (flat or nested leaf)."""
    if "in_scope_nids" not in b:
        return None
    universe = list(b.get("in_scope_nids") or [])
    cached, gap = _split(universe, NUMISTA_DIR)
    before_cached = b.get("cached_count")
    before_gap = len(b.get("gap_nids") or [])
    changed = False
    if b.get("cached_count") != len(cached):
        b["cached_count"] = len(cached)
        changed = True
    if "gap_nids" in b and list(b.get("gap_nids") or []) != gap:
        b["gap_nids"] = gap
        changed = True
    if not changed:
        return None
    return {"cached": len(cached), "gap": len(gap), "before_cached": before_cached, "before_gap": before_gap}


def _walk_numista_buckets(container: dict):
    """Yield (label, leaf_bucket) for flat or nested numista in_scope_buckets."""
    for name, val in container.items():
        if not isinstance(val, dict):
            continue
        if "in_scope_nids" in val:
            yield name, val
        else:
            # nested: country → period → leaf
            for period, leaf in val.items():
                if isinstance(leaf, dict) and "in_scope_nids" in leaf:
                    yield f"{name}.{period}", leaf


def process(path: Path) -> dict:
    raw = path.read_text()
    data = json.loads(raw)
    trailing_nl = raw.endswith("\n")
    changes: list[tuple[str, dict]] = []
    schema = None
    if isinstance(data.get("buckets"), dict) and any(
        isinstance(v, dict) and "gap_tids" in v for v in data["buckets"].values()
    ):
        schema = "ucoin"
        for name, b in data["buckets"].items():
            if isinstance(b, dict):
                rec = _refresh_ucoin_bucket(b)
                if rec:
                    changes.append((name, rec))
    elif isinstance(data.get("in_scope_buckets"), dict):
        schema = "numista"
        for label, leaf in _walk_numista_buckets(data["in_scope_buckets"]):
            rec = _refresh_numista_bucket(leaf)
            if rec:
                changes.append((label, rec))
    return {"path": path, "schema": schema, "changes": changes, "data": data,
            "trailing_nl": trailing_nl}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--write", action="store_true", help="persist changes (default: dry-run report)")
    ap.add_argument("--only", help="process only this audit file (path relative to scripts/cache)")
    args = ap.parse_args()

    files: list[Path] = []
    if args.only:
        files = [CACHE / args.only]
    else:
        for sub, pat in AUDIT_GLOBS:
            files.extend(sorted((CACHE / sub).glob(pat)))

    total_changed = 0
    for path in files:
        if not path.exists():
            print(f"  ✗ {path.relative_to(CACHE)} — not found", file=sys.stderr)
            continue
        res = process(path)
        rel = path.relative_to(CACHE)
        if res["schema"] is None:
            print(f"  – {rel} — no recomputable per-bucket id lists (skipped)")
            continue
        if not res["changes"]:
            print(f"  ✓ {rel} [{res['schema']}] — already current")
            continue
        print(f"  ● {rel} [{res['schema']}] — {len(res['changes'])} bucket(s) stale:")
        for name, rec in res["changes"]:
            print(f"      {name:42s} cached {rec['before_cached']}→{rec['cached']}  gap {rec['before_gap']}→{rec['gap']}")
        total_changed += len(res["changes"])
        if args.write:
            out = json.dumps(res["data"], ensure_ascii=False, indent=2)
            path.write_text(out + ("\n" if res["trailing_nl"] else ""))

    verb = "updated" if args.write else "stale (dry-run; pass --write to persist)"
    print(f"\n{total_changed} bucket(s) {verb} across {len(files)} audit file(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
