#!/usr/bin/env python3
"""§BJ NumisMaster Phase 3+4 — scope filter + bulk raw-HTML cache fetch.

Phase 3 (--filter-scope): read scripts/cache/numismaster/mc_index.json
(produced by §BI) → write scripts/cache/numismaster/<sub_scope>/mc_to_fetch.json
per sub-scope, applying year-window narrowing where user direction requires
stricter than mc_index.json.

Phase 4 (--fetch <sub_scope>): for each MC_ID in mc_to_fetch.json, urllib-fetch
https://numismaster.com/MC_<N>.html with ASCII-only User-Agent + 30s pacing.
Writes:
  - <sub_scope>/MC_<N>.html (byte-for-byte body; NO parsing, NO stripping)
  - <sub_scope>/MC_<N>.meta.json (HTTP status + headers + fetched_at)
  - <sub_scope>/_manifest.json (incremental — crash-safe resume).

Sub-scope topology (per docs/research/numismaster_dk_sh_1514_1914_harvest_surface.md):
  A. schleswig_holstein   — 9 SH cluster filters, all MCs (year filter applied
                            in Phase BK after per-coin year is parsed from HTML)
  B. denmark              — DENMARK filter, year_first <= 1914
  C. norway               — NORWAY filter, year_first <= 1814 (Danish-rule era
                            only; post-1814 Sweden-Norwegian-Union out of scope)
  D. sweden_christian_ii  — empty (§BI negative finding); not implemented

Usage:
  python scripts/fetch_numismaster.py --filter-scope
  python scripts/fetch_numismaster.py --fetch schleswig_holstein
  python scripts/fetch_numismaster.py --fetch denmark
  python scripts/fetch_numismaster.py --fetch norway
  python scripts/fetch_numismaster.py --fetch schleswig_holstein --limit 50
  python scripts/fetch_numismaster.py --fetch schleswig_holstein --pacing 30
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib.paths import NUMISMASTER_CACHE  # noqa: E402

MC_INDEX = NUMISMASTER_CACHE / "mc_index.json"

# Sub-scope → list of (filter_name, year_cutoff_or_None) tuples.
# year_cutoff narrows beyond mc_index.json's own year filter.
SUB_SCOPES: dict[str, list[tuple[str, int | None]]] = {
    "schleswig_holstein": [
        ("HOLSTEIN-GOTTORP-RENDSBORG", None),
        ("GLUCKSTADT", None),
        ("SCHLESWIG-HOLSTEIN-GLUCKSBURG", None),
        ("SCHLESWIG-HOLSTEIN-NORBURG", None),
        ("SCHLESWIG-HOLSTEIN-PLOEN", None),
        ("SCHLESWIG-HOLSTEIN-SONDERBURG", None),
        ("SCHLESWIG-HOLSTEIN", None),
        ("SCHAUMBURG-PINNEBERG", None),
        ("SCHLESWIG-HOLSTEIN-GOTTORP", None),
    ],
    "denmark": [("DENMARK", 1914)],
    "norway": [("NORWAY", 1814)],
    # sweden_christian_ii intentionally absent (§BI closed as 0-entry neg finding)
}

# ASCII-only User-Agent — mandatory per docs/HARVEST_GUIDE.md «Common pitfalls»
# (Python urllib's default 'Python-urllib/3.x' is often blocked; em-dashes
# anywhere in UA crash on encoding).
USER_AGENT = "Mozilla/5.0 (compatible; muentzfuesse-research/1.0; non-commercial scholarly use)"
FETCH_URL_TEMPLATE = "https://numismaster.com/MC_{mc_id}"
DEFAULT_PACING_S = 30.0
DEFAULT_TIMEOUT_S = 60


def phase3_filter_scope() -> None:
    """Read mc_index.json → write per-sub-scope mc_to_fetch.json."""
    idx = json.loads(MC_INDEX.read_text())
    filters = idx["filters"]

    summary: dict[str, int] = {}
    for sub_scope, filter_specs in SUB_SCOPES.items():
        sub_dir = NUMISMASTER_CACHE / sub_scope
        sub_dir.mkdir(parents=True, exist_ok=True)

        mc_to_fetch: dict[int, dict] = {}  # mc_id → {mc_id, source_filters, …}

        for filter_name, year_cutoff in filter_specs:
            if filter_name not in filters:
                print(f"  [{sub_scope}] WARN: filter '{filter_name}' not in mc_index.json — skipping")
                continue
            entries = filters[filter_name].get("entries", [])
            for e in entries:
                mc_id = e["mc_id"]
                yf = e.get("year_first")
                if year_cutoff is not None and yf is not None and yf > year_cutoff:
                    continue  # post-cutoff, out of scope
                if mc_id not in mc_to_fetch:
                    mc_to_fetch[mc_id] = {
                        "mc_id": mc_id,
                        "source_filters": [filter_name],
                        "year_first": yf,
                        "year_last": e.get("year_last"),
                        "km": e.get("km"),
                        "denom": e.get("denom"),
                    }
                else:
                    # MC_ID seen under multiple filters — union the source_filters list
                    if filter_name not in mc_to_fetch[mc_id]["source_filters"]:
                        mc_to_fetch[mc_id]["source_filters"].append(filter_name)

        out_path = sub_dir / "mc_to_fetch.json"
        out_data = {
            "_schema": "Phase 3 (§BJ) scope-filtered MC_ID list. Each entry "
                       "carries the union of filter contexts where the MC appeared "
                       "in mc_index.json (an MC can be tagged by multiple filters "
                       "when SH cadet lines overlap).",
            "_generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "_sub_scope": sub_scope,
            "_source_filters": [f for f, _ in filter_specs],
            "_year_cutoff_applied": {f: y for f, y in filter_specs if y is not None},
            "count": len(mc_to_fetch),
            "entries": sorted(mc_to_fetch.values(), key=lambda x: x["mc_id"]),
        }
        out_path.write_text(json.dumps(out_data, indent=2, ensure_ascii=False))
        summary[sub_scope] = len(mc_to_fetch)
        print(f"  [{sub_scope}] wrote {out_path.relative_to(NUMISMASTER_CACHE.parent.parent)} ({len(mc_to_fetch)} unique MCs)")

    total = sum(summary.values())
    print(f"\nPhase 3 complete. Total unique MCs to fetch across sub-scopes: {total}")
    for k, v in summary.items():
        print(f"  {k}: {v}")


def _manifest_path(sub_scope: str) -> Path:
    return NUMISMASTER_CACHE / sub_scope / "_manifest.json"


def _load_manifest(sub_scope: str) -> dict:
    p = _manifest_path(sub_scope)
    if p.exists():
        return json.loads(p.read_text())
    return {
        "_schema": "Phase 4 (§BJ) per-MC fetch record. Updated incrementally so the fetcher can resume after crash. Each entry: mc_id → {status, fetched_at, html_bytes, error?}.",
        "sub_scope": sub_scope,
        "fetched": {},  # mc_id (str) → {status, fetched_at, html_bytes}
        "errors": {},   # mc_id (str) → {error_class, error_msg, attempted_at}
    }


def _save_manifest(sub_scope: str, manifest: dict) -> None:
    p = _manifest_path(sub_scope)
    p.write_text(json.dumps(manifest, indent=2, ensure_ascii=False))


def _fetch_one(mc_id: int, sub_dir: Path, timeout_s: int = DEFAULT_TIMEOUT_S) -> tuple[bool, dict]:
    """Fetch one MC; return (success, meta_dict_or_error_dict)."""
    url = FETCH_URL_TEMPLATE.format(mc_id=mc_id)
    html_path = sub_dir / f"MC_{mc_id}.html"
    meta_path = sub_dir / f"MC_{mc_id}.meta.json"

    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=timeout_s) as resp:
            status = resp.status
            headers = dict(resp.headers.items())
            body = resp.read()  # bytes — write byte-for-byte
    except urllib.error.HTTPError as e:
        return False, {
            "error_class": "HTTPError",
            "error_msg": f"HTTP {e.code} — {e.reason}",
            "attempted_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
    except urllib.error.URLError as e:
        return False, {
            "error_class": "URLError",
            "error_msg": str(e.reason),
            "attempted_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        }
    except Exception as e:
        return False, {
            "error_class": e.__class__.__name__,
            "error_msg": str(e),
            "attempted_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        }

    html_path.write_bytes(body)
    meta = {
        "mc_id": mc_id,
        "url": url,
        "status": status,
        "headers": headers,
        "html_bytes": len(body),
        "fetched_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    meta_path.write_text(json.dumps(meta, indent=2, ensure_ascii=False))
    return True, meta


def phase4_fetch(sub_scope: str, limit: int | None, pacing_s: float) -> None:
    """Bulk-fetch MC HTML pages for a sub-scope with crash-safe resume."""
    if sub_scope not in SUB_SCOPES:
        print(f"ERROR: unknown sub-scope '{sub_scope}'. Valid: {list(SUB_SCOPES.keys())}", file=sys.stderr)
        sys.exit(2)

    sub_dir = NUMISMASTER_CACHE / sub_scope
    mc_list_path = sub_dir / "mc_to_fetch.json"
    if not mc_list_path.exists():
        print(f"ERROR: {mc_list_path} not found. Run --filter-scope first.", file=sys.stderr)
        sys.exit(2)

    plan = json.loads(mc_list_path.read_text())
    entries: list[dict] = plan["entries"]
    manifest = _load_manifest(sub_scope)

    already_fetched = set(manifest["fetched"].keys())
    pending = [e for e in entries if str(e["mc_id"]) not in already_fetched]
    if limit is not None:
        pending = pending[:limit]

    print(f"[{sub_scope}] mc_to_fetch.json: {len(entries)} total")
    print(f"[{sub_scope}] already fetched: {len(already_fetched)}; pending: {len(pending)} (limit={limit})")
    if pending:
        print(f"[{sub_scope}] pacing={pacing_s}s between requests "
              f"→ est ~{int(len(pending)*pacing_s/60)} min for this batch")
    print()

    success_count = 0
    error_count = 0
    for i, entry in enumerate(pending, 1):
        mc_id = entry["mc_id"]
        # Skip if HTML file already on disk (defensive — manifest should already exclude it)
        html_path = sub_dir / f"MC_{mc_id}.html"
        if html_path.exists() and str(mc_id) in already_fetched:
            continue

        ok, result = _fetch_one(mc_id, sub_dir)
        if ok:
            manifest["fetched"][str(mc_id)] = {
                "status": result["status"],
                "fetched_at": result["fetched_at"],
                "html_bytes": result["html_bytes"],
            }
            # Clear any prior error for this MC
            manifest["errors"].pop(str(mc_id), None)
            success_count += 1
            print(f"[{sub_scope}] [{i}/{len(pending)}] MC_{mc_id} OK ({result['html_bytes']} bytes)")
        else:
            manifest["errors"][str(mc_id)] = result
            error_count += 1
            print(f"[{sub_scope}] [{i}/{len(pending)}] MC_{mc_id} FAIL: {result['error_msg']}")

        # Save manifest every fetch — crash-safe resume
        _save_manifest(sub_scope, manifest)

        # Pacing — but not after the final fetch
        if i < len(pending):
            time.sleep(pacing_s)

    print()
    print(f"[{sub_scope}] Batch complete: {success_count} fetched, {error_count} errors")
    print(f"[{sub_scope}] Cumulative on disk: {len(manifest['fetched'])} / {len(entries)} "
          f"({100 * len(manifest['fetched']) / max(1, len(entries)):.1f}%)")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--filter-scope", action="store_true",
                   help="Phase 3 — generate per-sub-scope mc_to_fetch.json from mc_index.json")
    g.add_argument("--fetch", metavar="SUB_SCOPE",
                   help="Phase 4 — urllib bulk fetch (sub_scope: schleswig_holstein | denmark | norway)")
    ap.add_argument("--limit", type=int, default=None,
                    help="Max MCs to fetch in this run (for batch-pacing). Default: all pending.")
    ap.add_argument("--pacing", type=float, default=DEFAULT_PACING_S,
                    help=f"Seconds between requests (default: {DEFAULT_PACING_S}s)")
    args = ap.parse_args()

    if args.filter_scope:
        phase3_filter_scope()
    else:
        phase4_fetch(args.fetch, args.limit, args.pacing)
    return 0


if __name__ == "__main__":
    sys.exit(main())
