#!/usr/bin/env python3
"""One-off: audit every Numista-sourced multi-year coin in schleswig.yml,
fetch its actual struck-year list via Numista API v3
`/v3/types/{id}/issues` (which returns the per-specimen list shown in the
struck-year table on the HTML page — exactly what the API summary
`min_year`/`max_year` flattens out), and populate `year_ranges` for coins
with discontinuous mintage. Also rewrites `year_label` to match the
actual struck-year structure.

Cached responses live at `scripts/cache/numista/<nid>_issues.json`.

Run:
    .venv/bin/python scripts/oneoff/audit_numista_year_ranges.py            # apply
    .venv/bin/python scripts/oneoff/audit_numista_year_ranges.py --dry-run  # preview
    .venv/bin/python scripts/oneoff/audit_numista_year_ranges.py --force    # refetch
"""
from __future__ import annotations
import argparse
import json
import pathlib
import sys
import time
import urllib.error
import urllib.request

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from lib.env import load_local_env, require  # noqa: E402

from ruamel.yaml import YAML  # noqa: E402
from ruamel.yaml.comments import CommentedSeq  # noqa: E402

CACHE_DIR = pathlib.Path("scripts/cache/numista")
CACHE_DIR.mkdir(parents=True, exist_ok=True)
SCHLESWIG_YML = pathlib.Path("data/locations/schleswig.yml")
API_BASE = "https://api.numista.com/v3"
RATE_LIMIT_S = 1.0  # seconds between live calls; free tier = 200/day


def fetch_issues(nid: str, key: str, force: bool = False) -> tuple[list, bool]:
    """Returns (issues_list, was_live_fetch)."""
    cache = CACHE_DIR / f"{nid}_issues.json"
    if cache.exists() and not force:
        return json.loads(cache.read_text()), False
    url = f"{API_BASE}/types/{nid}/issues?lang=en"
    req = urllib.request.Request(url, headers={
        "Numista-API-Key": key,
        "Accept": "application/json",
    })
    with urllib.request.urlopen(req, timeout=20) as r:
        data = json.loads(r.read())
    cache.write_text(json.dumps(data, ensure_ascii=False, indent=2))
    return data, True


def collapse_runs(years: list[int]) -> list[list[int]]:
    """Sort + collapse consecutive years to [first, last] runs."""
    if not years:
        return []
    s = sorted(set(years))
    runs: list[list[int]] = []
    start = prev = s[0]
    for y in s[1:]:
        if y == prev + 1:
            prev = y
        else:
            runs.append([start, prev])
            start = prev = y
    runs.append([start, prev])
    return runs


def fmt_year_label(runs: list[list[int]]) -> str:
    parts = []
    for f, l in runs:
        parts.append(str(f) if f == l else f"{f}-{l}")
    return ", ".join(parts)


def make_year_ranges_seq(runs: list[list[int]]) -> CommentedSeq:
    """Outer block-style list of inner flow-style [f, l] pairs."""
    outer = CommentedSeq()
    for f, l in runs:
        inner = CommentedSeq([f, l])
        inner.fa.set_flow_style()
        outer.append(inner)
    return outer


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true",
                    help="Print planned changes; do NOT modify the YAML")
    ap.add_argument("--force", action="store_true",
                    help="Refetch /issues even if cached (uses API quota)")
    args = ap.parse_args()

    load_local_env()
    key = require("NUMISTA_API_KEY")

    yaml = YAML()
    yaml.preserve_quotes = True
    yaml.indent(mapping=2, sequence=4, offset=2)
    yaml.width = 4096

    with open(SCHLESWIG_YML) as f:
        doc = yaml.load(f)

    targets: list[tuple] = []
    for c in doc["coins"]:
        cat = c.get("catalog") or {}
        nid = cat.get("numista")
        if not nid:
            continue
        yf = c.get("year_first")
        yl = c.get("year_last")
        if yl is None or yl == yf:
            continue
        if c.get("year_ranges"):
            continue  # already audited / hand-set
        targets.append((c, str(nid)))

    print(f"Auditing {len(targets)} numista-sourced multi-year coins…")

    live = 0
    sparse_changed = 0
    bounds_changed = 0
    no_change = 0
    no_data = 0
    errors: list[str] = []

    for c, nid in targets:
        try:
            issues, was_live = fetch_issues(nid, key, force=args.force)
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace")[:160]
            errors.append(f"N#{nid}: HTTP {e.code} — {body}")
            print(f"  ! N#{nid}: HTTP {e.code} — {body}")
            if e.code == 429:
                print("  Rate limit hit; aborting further fetches.")
                break
            continue
        except Exception as e:
            errors.append(f"N#{nid}: {e}")
            print(f"  ! N#{nid}: {e}")
            continue

        if was_live:
            live += 1
            time.sleep(RATE_LIMIT_S)

        if not issues:
            no_data += 1
            continue

        years = []
        for issue in issues:
            y = issue.get("gregorian_year") or issue.get("year")
            if isinstance(y, int) and y > 0:
                years.append(y)

        if not years:
            no_data += 1
            continue

        runs = collapse_runs(years)
        rmin = min(r[0] for r in runs)
        rmax = max(r[1] for r in runs)
        cur_first = c["year_first"]
        cur_last = c.get("year_last")
        is_sparse = len(runs) > 1
        bounds_diff = (rmin != cur_first) or (rmax != cur_last)

        if not is_sparse and not bounds_diff:
            no_change += 1
            continue

        new_label = fmt_year_label(runs)
        cid = c["id"]
        flag = "SPARSE" if is_sparse else "bounds"
        print(f"  {flag:6} {cid:42} N#{nid:>8} "
              f"cur=[{cur_first}-{cur_last}] new={new_label}")
        if is_sparse:
            sparse_changed += 1
        else:
            bounds_changed += 1

        if not args.dry_run:
            if is_sparse:
                c["year_ranges"] = make_year_ranges_seq(runs)
            c["year_label"] = new_label
            if rmin != cur_first:
                c["year_first"] = rmin
            if rmax != cur_last:
                c["year_last"] = rmax

    print()
    print("Summary:")
    print(f"  total audited      : {len(targets)}")
    print(f"  sparse (multi-run) : {sparse_changed}")
    print(f"  bounds-only diff   : {bounds_changed}")
    print(f"  no change          : {no_change}")
    print(f"  no data from API   : {no_data}")
    print(f"  errors             : {len(errors)}")
    print(f"  live API calls     : {live}")

    if errors:
        print("\nErrors:")
        for e in errors[:20]:
            print(f"  - {e}")

    if not args.dry_run:
        yaml.dump(doc, SCHLESWIG_YML)
        print(f"\n✓ Wrote {SCHLESWIG_YML}")
    else:
        print("\n(dry-run; no file modified)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
