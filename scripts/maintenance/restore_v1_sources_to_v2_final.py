#!/usr/bin/env python3
"""One-time recovery: restore V1-curated source citations into V2 final
foundation entries.

Background
----------
The V1 → V2 bootstrap migrated curated coin entries from
`data/locations/*.yml` (V1, frozen) into `data/v2/final/*.yml` (V2
entity-keyed). Catalogue refs were preserved during migration, but
`sources` lists got overwritten by subsequent `absorb_seeds_into_final_v2`
runs that used `_collect_sources(..., skip_first_list=True)` — dropping
the foundation's own sources list to re-derive purely from `composed_of`
seed_unified members.

This dropped V1-curator-added citations that had no seed equivalent —
typically Numista per-coin URLs, ucoin tids, raw auction URLs, and
hand-collected web references. Audit on 2026-05-24: 233 of 248
V2-mirrored SH entries had V1 sources missing in their V2 counterparts
(166 Numista, 99 auction, 20 web, 13 ucoin, 45 misc).

Recovery rule
-------------
For each V1 entry with an `id` that matches a V2 final entry's `id`:

  1. Read V1 entry's `sources` list.
  2. Compute the URL-set already present in V2 final entry's `sources`.
  3. For each V1 source whose URL is NOT in V2's URL-set, APPEND it
     to V2 final entry's `sources` list.
  4. Save V2 final file.

Dedup is URL-based for single-page hosts (en.numista.com, en.ucoin.net,
danskmoent.dk, numismaster.com, ikmk.smb.museum) and (url, ref, type)
otherwise. This mirrors `_collect_sources`'s dedup behavior in the
cross-source merger / absorb pipelines.

V1 source `type` labels (numista / ucoin / web / auction) are PRESERVED
verbatim. V2's existing 'literature' entries are NOT renamed — the V1
and V2 entries coexist in the merged list, each with its own type.

Going-forward: `absorb_seeds_into_final_v2.py` was updated 2026-05-24
to drop `skip_first_list=True`, so future absorb runs will preserve
foundation sources alongside seed sources. This recovery script only
needs to run once.

Usage
-----
    .venv/bin/python scripts/maintenance/restore_v1_sources_to_v2_final.py --dry-run
    .venv/bin/python scripts/maintenance/restore_v1_sources_to_v2_final.py --apply

Idempotent — re-runs after the first --apply produce no further changes.
"""
from __future__ import annotations

import argparse
import pathlib
import sys
from collections import Counter, defaultdict

from ruamel.yaml import YAML

PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[2]
V1_DIR = PROJECT_ROOT / "data" / "locations"
V2_FINAL_DIR = PROJECT_ROOT / "data" / "v2" / "final"

SINGLE_PAGE_HOSTS = (
    "danskmoent.dk",
    "en.numista.com",
    "en.ucoin.net",
    "numismaster.com",
    "ikmk.smb.museum",
)


def _source_key(source: dict) -> tuple:
    """Return a hashable dedup key. For single-page hosts, use URL alone;
    otherwise use (url, ref, type) triple."""
    url = source.get("url", "") or ""
    if any(host in url for host in SINGLE_PAGE_HOSTS):
        return ("url", url)
    return ("trip", url, source.get("ref", "") or "", source.get("type", "") or "")


def load_v1_entries() -> dict[str, dict]:
    """Return `{coin_id → v1_entry}` across all V1 location yamls. References
    files (`*-references.yml`) are skipped."""
    yaml = YAML(typ="safe")
    out: dict[str, dict] = {}
    for path in sorted(V1_DIR.glob("*.yml")):
        if path.stem.endswith("-references"):
            continue
        doc = yaml.load(path) or {}
        for c in doc.get("coins") or []:
            cid = c.get("id")
            if cid:
                out[cid] = c
    return out


def restore_for_file(v2_path: pathlib.Path, v1_entries: dict[str, dict]) -> tuple[int, int]:
    """Process one V2 final file, restoring missing V1 sources to matching
    foundations. Returns (entries_touched, sources_added)."""
    yaml = YAML()
    yaml.preserve_quotes = True
    yaml.width = 100000
    yaml.indent(mapping=2, sequence=4, offset=2)

    with open(v2_path) as f:
        doc = yaml.load(f)
    coins = doc.get("coins") or []

    entries_touched = 0
    sources_added = 0
    for c in coins:
        cid = c.get("id")
        if not cid or cid not in v1_entries:
            continue
        v1 = v1_entries[cid]
        v1_sources = v1.get("sources") or []
        if not v1_sources:
            continue
        v2_sources = list(c.get("sources") or [])
        seen_keys = {_source_key(s) for s in v2_sources}

        appended_here = 0
        for s in v1_sources:
            if not isinstance(s, dict):
                continue
            key = _source_key(s)
            if key in seen_keys:
                continue
            v2_sources.append(dict(s))
            seen_keys.add(key)
            appended_here += 1

        if appended_here:
            c["sources"] = v2_sources
            entries_touched += 1
            sources_added += appended_here

    return entries_touched, sources_added, doc if entries_touched else None, yaml


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                  formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--apply", action="store_true",
                    help="Write changes back to V2 final yamls (default: dry-run)")
    ap.add_argument("--dry-run", action="store_true",
                    help="Report what WOULD change without writing")
    args = ap.parse_args()

    if not args.apply and not args.dry_run:
        # Default to dry-run for safety
        args.dry_run = True

    if args.apply and args.dry_run:
        print("ERROR: --apply and --dry-run are mutually exclusive", file=sys.stderr)
        return 2

    v1_entries = load_v1_entries()
    print(f"Loaded {len(v1_entries)} V1 entries from {V1_DIR}")
    print()

    totals = Counter()
    per_type = Counter()

    for v2_path in sorted(V2_FINAL_DIR.glob("*.yml")):
        # restore_for_file returns 4-tuple; unpack
        entries_touched, sources_added, doc, yaml_obj = restore_for_file(v2_path, v1_entries)
        if entries_touched:
            print(f"  {v2_path.name:30s}  entries:{entries_touched:4d}  sources_added:{sources_added:4d}")
            totals["entries"] += entries_touched
            totals["sources"] += sources_added
            if args.apply:
                with open(v2_path, "w") as f:
                    yaml_obj.dump(doc, f)

    print()
    print(f"Total entries touched:  {totals['entries']}")
    print(f"Total sources added:    {totals['sources']}")
    print()
    if args.dry_run:
        print("--- DRY RUN — no files written. Re-run with --apply to commit. ---")
    else:
        print(f"✓ Wrote restored V2 final yamls to {V2_FINAL_DIR}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
