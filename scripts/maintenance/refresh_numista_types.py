#!/usr/bin/env python3
"""Re-fetch Numista types whose cached record has gone stale, and stitch
the fresh data onto the parsed sidecars with a full audit log.

Why: Numista is user-edited. A type harvested in spring 2026 may since
have gained catalogue references (Hede, SIEG, Galster, DNF) — e.g. N#90574
was cached with KM + Dav only, the live page now also gives Hede 11B, 11C.
Without those references the merger cannot tie the record to its Hede /
Galster class.

What it does, per NID (one API ``getType`` call each):

1. saves the response verbatim to ``refresh/<date>/<NID>.json`` — the
   harvested raw file is never touched;
2. lays it over ``parsed/<NID>.json`` (policy in ``lib/numista_refresh``);
3. appends one line to ``refresh/<date>/_log.jsonl`` holding the OLD
   sidecar, the NEW canonical record, the RESULT and the field-level
   CHANGES — so a removal or correction by Numista stays visible.

Selection (default): Numista seeds of the Danish-crown entities — every
one dated before 1541 (before Hede's coverage; Galster's period), and
those dated 1541–1814 that carry no Hede reference. ``--nid`` overrides it.

Quota: the free plan allows 2000 requests per calendar month (checked on
numista.com/api/pricing.php, 2026-11-12). Runs are resumable — a NID
already fetched under ``--date`` is skipped — and stop at the first 429.

Usage:
    .venv/bin/python scripts/maintenance/refresh_numista_types.py --list
    .venv/bin/python scripts/maintenance/refresh_numista_types.py --nid 90574
    .venv/bin/python scripts/maintenance/refresh_numista_types.py --limit 200
    .venv/bin/python scripts/maintenance/refresh_numista_types.py --report
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import subprocess
import sys
import time
import urllib.error
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import yaml  # noqa: E402

from fetch_numista_api import fetch_type  # noqa: E402
from lib.env import load_local_env, require  # noqa: E402
from lib.numista_refresh import REFRESH_DIR, overlay  # noqa: E402
from lib.paths import NUMISTA_CACHE  # noqa: E402
from parse_numista_api import parse_api_to_canonical  # noqa: E402

PARSED = NUMISTA_CACHE / "parsed"
ROYAL = {"danish_realm", "danish_norway", "royal_holstein", "royal_slesvig",
         "christian_ii_reconquest", "flensborg_medieval"}
RATE_S = 1.0


def select_stale() -> dict[str, str]:
    """NID -> reason, from the Numista seeds."""
    out: dict[str, str] = {}
    for p in sorted((ROOT / "data/v2/seed/numista").glob("*.yml")):
        ent = p.stem
        for c in (yaml.safe_load(p.read_text()) or {}).get("coins") or []:
            cat = c.get("catalog") or {}
            y = c.get("year_first") or 0
            reason = None
            if ent in ROYAL and y and y < 1541:
                reason = "before Hede"
            elif ent in ROYAL and y <= 1814 and not cat.get("hede"):
                reason = "no hede"
            if not reason:
                continue
            for nid in str(cat.get("numista") or "").split("|"):
                if nid.strip():
                    out.setdefault(nid.strip(), f"{reason} ({ent})")
    return out


def _old_sidecar(nid: str) -> dict:
    """The sidecar as committed in the harvest repo — the state before any
    refresh — so a re-applied refresh always diffs against the harvest,
    not against an earlier overlay. Falls back to the file on disk for a
    sidecar that was never committed."""
    rel = f"numista/parsed/{nid}.json"
    r = subprocess.run(["git", "-C", str(NUMISTA_CACHE.parent), "show", f"HEAD:{rel}"],
                       capture_output=True, text=True)
    if r.returncode == 0:
        return json.loads(r.stdout)
    side = PARSED / f"{nid}.json"
    return json.loads(side.read_text()) if side.exists() else {}


def stitch(nid: str, fresh: dict, date: str, why: str, fetched_at: str) -> dict:
    """Lay one saved response over the harvest sidecar, write the result,
    return the log entry."""
    raw_path = REFRESH_DIR / date / f"{nid}.json"
    old = _old_sidecar(nid)
    new = parse_api_to_canonical(fresh) or {}
    result, changes = overlay(old, new, date=date,
                              raw_path=str(raw_path.relative_to(NUMISTA_CACHE.parent)))
    (PARSED / f"{nid}.json").write_text(json.dumps(result, ensure_ascii=False, indent=2))
    return {"nid": nid, "why": why, "fetched_at": fetched_at,
            "old_shape": old.get("_source_shape"),
            "changes": changes, "old": old, "new": new, "result": result}


def _append(date: str, entry: dict) -> None:
    with (REFRESH_DIR / date / "_log.jsonl").open("a") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False) + "\n")


def refresh_one(nid: str, key: str, date: str, why: str) -> dict:
    day = REFRESH_DIR / date
    day.mkdir(parents=True, exist_ok=True)
    fresh = fetch_type(nid, key)
    (day / f"{nid}.json").write_text(json.dumps(fresh, ensure_ascii=False, indent=2))
    entry = stitch(nid, fresh, date, why, dt.datetime.now().isoformat(timespec="seconds"))
    _append(date, entry)
    return entry


def reapply(date: str) -> None:
    """Re-stitch every saved response of one batch with the current rules
    (no API calls) and rewrite the log. Keeps each NID's reason and fetch
    time from the existing log."""
    day = REFRESH_DIR / date
    log = day / "_log.jsonl"
    meta = {}
    if log.exists():
        for line in log.open():
            r = json.loads(line)
            meta[r["nid"]] = (r.get("why"), r.get("fetched_at"))
    entries = []
    for raw in sorted(day.glob("[0-9]*.json"), key=lambda p: int(p.stem)):
        why, at = meta.get(raw.stem, ("?", None))
        entries.append(stitch(raw.stem, json.loads(raw.read_text()), date, why, at))
    log.write_text("".join(json.dumps(e, ensure_ascii=False) + "\n" for e in entries))
    print(f"re-applied {len(entries)} saved responses")


def report(date: str) -> None:
    log = REFRESH_DIR / date / "_log.jsonl"
    if not log.exists():
        print("no log for", date)
        return
    rows = [json.loads(line) for line in log.open()]
    st: Counter = Counter()
    for r in rows:
        for reg, d in (r["changes"].get("references") or {}).items():
            st[f"ref {d['status']}: {reg}"] += 1
        for k, d in r["changes"].items():
            if k == "confirmed_absent":
                for reg, vals in d.items():
                    st[f"ref confirmed_absent: {reg}"] += len(vals)
            elif k != "references":
                st[f"field {d['status']}: {k}"] += 1
    print(f"{len(rows)} NIDs refreshed on {date}")
    for k, v in sorted(st.items()):
        print(f"  {v:4d}  {k}")
    print("\nreferences absent from the response or changed (review these):")
    for r in rows:
        for reg, d in (r["changes"].get("references") or {}).items():
            if d["status"] in ("absent_in_response", "changed"):
                print(f"  N#{r['nid']:>7}  {reg:12s} {d['status']:8s} "
                      f"{d.get('old')!s:>14} -> {d.get('new')!s}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--nid", action="append", help="refresh only these NIDs")
    ap.add_argument("--limit", type=int, default=200,
                    help="max live calls in this run (default 200)")
    ap.add_argument("--date", default=dt.date.today().isoformat(),
                    help="refresh batch name (default today)")
    ap.add_argument("--list", action="store_true", help="print the selection")
    ap.add_argument("--report", action="store_true", help="summarise the log")
    ap.add_argument("--reapply", action="store_true",
                    help="re-stitch the saved responses of --date (no API calls)")
    args = ap.parse_args()

    if args.reapply:
        reapply(args.date)
        return 0

    if args.report:
        report(args.date)
        return 0

    todo = {n: "requested" for n in args.nid} if args.nid else select_stale()
    done = {p.stem for p in (REFRESH_DIR / args.date).glob("[0-9]*.json")}
    pending = [n for n in sorted(todo, key=int) if n not in done]
    print(f"selected {len(todo)}, already fetched {len(todo) - len(pending)}, "
          f"pending {len(pending)}")
    if args.list:
        for n in pending:
            print(f"  {n}  {todo[n]}")
        return 0

    load_local_env()
    key = require("NUMISTA_API_KEY")
    live = 0
    for nid in pending[: args.limit]:
        try:
            e = refresh_one(nid, key, args.date, todo[nid])
        except urllib.error.HTTPError as err:
            print(f"  ! N#{nid}: HTTP {err.code}")
            if err.code == 429:
                print("  rate limit hit — stopping")
                break
            continue
        live += 1
        refs = e["changes"].get("references") or {}
        if refs:
            print(f"  N#{nid}: " + ", ".join(f"{k} {v['status']}" for k, v in refs.items()))
        time.sleep(RATE_S)
    print(f"live calls: {live}; still pending: {max(len(pending) - live, 0)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
