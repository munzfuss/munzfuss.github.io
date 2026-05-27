#!/usr/bin/env python3
"""Phase 2 driver — Numista cache → canonical sidecars.

Walks every Numista cache file across the THREE harvest paths and emits
a unified canonical JSON sidecar per coin into
`scripts/cache/numista/parsed/<NID>.json`.

Input paths:

  1. scripts/cache/numista/<NID>.json
     • API v3 raw response (from `scripts/fetch_numista_api.py`), OR
     • chrome_mcp_html scrape (from `/tmp/save_numista.py` per
       docs/HARVEST_ROUTINE.md).
     Shape disambiguated via `_harvested_via` marker + `min_year` +
     `object_type` keys.

  2. scripts/cache/numista/denmark_pre_1541/n<NID>.json
     • Already in canonical form (parse_numista_pre1541.py is its
       own Phase 2). Files copied as-is into parsed/<NID>.json so
       downstream consumers don't need to walk multiple roots.

Output:

  scripts/cache/numista/parsed/<NID>.json — canonical schema per
  `scripts/lib/numista_canonical.py` module docstring. One file per
  Numista N#. Re-running is idempotent; --force re-emits even when
  the sidecar already exists.

CLI:
    .venv/bin/python scripts/parse_numista.py             # all uncached
    .venv/bin/python scripts/parse_numista.py --force     # rebuild all
    .venv/bin/python scripts/parse_numista.py --nid 313521 --dry-run
    .venv/bin/python scripts/parse_numista.py --report-only  # stats, no writes

Closes the second half of TODO §BO.5 step 5 (Phase 2 for chrome_mcp_html
+ API entries — Phase 3 seed builder lands in a separate commit).
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from parse_numista_api import is_api_shape, parse_api_to_canonical  # noqa: E402
from parse_numista_chrome import is_chrome_shape, parse_chrome_to_canonical  # noqa: E402

CACHE_DIR = PROJECT_ROOT / "scripts" / "cache" / "numista"
PARSED_DIR = CACHE_DIR / "parsed"
PRE_1541_DIR = CACHE_DIR / "denmark_pre_1541"


def detect_and_parse(raw: dict[str, Any], source_path: Path) -> dict[str, Any] | None:
    """Dispatch one raw cache entry to its sub-parser based on shape.

    Returns canonical sidecar dict or None for unparseable / OOS-shaped
    entries.
    """
    if not isinstance(raw, dict):
        return None
    if is_chrome_shape(raw):
        out = parse_chrome_to_canonical(raw)
    elif is_api_shape(raw):
        out = parse_api_to_canonical(raw)
    else:
        return None
    if out is not None:
        out["_source_path"] = str(source_path.relative_to(PROJECT_ROOT))
    return out


def _copy_pre1541(json_path: Path) -> dict[str, Any] | None:
    """The pre_1541 parse output is already in canonical form. Load it,
    stamp `_source_shape` + `_source_path` for traceability, and return
    it as-is for emission to parsed/<NID>.json.

    The pre_1541 parser predates this driver — it doesn't carry
    `_source_shape` markers natively. We add them on the way through so
    the unified parsed/ output is internally homogeneous."""
    try:
        d = json.loads(json_path.read_text())
    except json.JSONDecodeError:
        return None
    if not isinstance(d, dict):
        return None
    nid = d.get("numista_id")
    if nid is None:
        return None
    d.setdefault("_source_shape", "html_pre1541")
    d["_source_path"] = str(json_path.relative_to(PROJECT_ROOT))
    return d


def _write_sidecar(canonical: dict[str, Any], nid: int) -> None:
    PARSED_DIR.mkdir(parents=True, exist_ok=True)
    out_path = PARSED_DIR / f"{nid}.json"
    out_path.write_text(json.dumps(canonical, ensure_ascii=False, indent=2))


def collect_files() -> list[tuple[Path, str]]:
    """Return [(path, route)] over all input sources. `route` is one
    of 'top' (raw top-level cache) or 'pre1541' (canonical pre-parsed).
    """
    out: list[tuple[Path, str]] = []
    for p in CACHE_DIR.glob("*.json"):
        if p.name.startswith("_"):
            continue
        out.append((p, "top"))
    if PRE_1541_DIR.exists():
        for p in PRE_1541_DIR.glob("n*.json"):
            out.append((p, "pre1541"))
    return out


def process_one(path: Path, route: str, force: bool,
                stats: Counter, dry_run: bool) -> tuple[str, str | None]:
    """Parse one input file. Returns (outcome_tag, sidecar_path).
    `outcome_tag` is one of:
      written      — fresh sidecar emitted
      skipped      — sidecar already exists and --force not set
      unparseable  — file shape not recognised
      malformed    — JSON parse error
    """
    try:
        d = json.loads(path.read_text())
    except json.JSONDecodeError:
        stats["malformed"] += 1
        return "malformed", None

    if route == "pre1541":
        canonical = _copy_pre1541(path)
    else:
        canonical = detect_and_parse(d, path)

    if canonical is None:
        stats["unparseable"] += 1
        stats[f"unparseable_{route}"] += 1
        return "unparseable", None

    nid = canonical.get("numista_id")
    if nid is None:
        stats["no_nid"] += 1
        return "unparseable", None

    out_path = PARSED_DIR / f"{nid}.json"
    if out_path.exists() and not force:
        stats["skipped"] += 1
        return "skipped", str(out_path)

    if not dry_run:
        _write_sidecar(canonical, int(nid))
    stats["written"] += 1
    stats[f"written_{canonical.get('_source_shape', '?')}"] += 1
    return "written", str(out_path)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--force", action="store_true",
                    help="Re-emit sidecars even when they already exist")
    ap.add_argument("--dry-run", action="store_true",
                    help="Compute stats; don't write any files")
    ap.add_argument("--nid", help="Process only this single NID")
    ap.add_argument("--report-only", action="store_true",
                    help="Walk inputs, report stats, do not write")
    args = ap.parse_args()

    if args.report_only:
        args.dry_run = True

    files = collect_files()
    if args.nid:
        files = [(p, r) for p, r in files
                 if p.stem == args.nid or p.stem == f"n{args.nid}"]
        if not files:
            print(f"No cache file found for NID {args.nid}", file=sys.stderr)
            return 1

    stats: Counter = Counter()
    for p, route in files:
        outcome, _ = process_one(p, route, args.force, stats, args.dry_run)

    print(f"\nNumista Phase 2 — driver report")
    print(f"  Inputs scanned: {len(files)}")
    print(f"  Output dir: {PARSED_DIR}")
    print(f"  Stats:")
    for k, v in stats.most_common():
        print(f"    {k}: {v}")
    if args.dry_run:
        print("  (dry-run — no files written)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
