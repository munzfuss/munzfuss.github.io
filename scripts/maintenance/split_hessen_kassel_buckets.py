#!/usr/bin/env python3
"""Split the overlapping Hesse-Kassel BO.7 buckets by the 1803 Landgraviate→
Electorate transition so each NID lands in exactly one bucket.

Problem (logged anomaly audit_manifest_scope_drift:bucket=hessen_kassel_electorate,
occ=6): ``hessen_kassel_landgraviate`` in_scope_nids is a strict subset of
``hessen_kassel_electorate`` (255 shared NIDs) — Numista enumerated the full
Hesse-Cassel dynastic coinage (1572-1866) into the electorate bucket and a
copy into the landgraviate bucket, so landgraviate-era pieces double-count.

Fix (the anomaly's own proposed_fix): Hesse-Kassel was raised from Landgraviate
to Electorate in 1803 (Reichsdeputationshauptschluss). Partition the UNION of
both buckets by ``year_first`` (§ year_first determines placement):
  - yf  < 1803  → hessen_kassel_landgraviate
  - yf >= 1803  → hessen_kassel_electorate
Each NID then appears in exactly one bucket. ``oos_excluded_nids`` per bucket
is preserved untouched (separate from in_scope partitioning).

Idempotent: re-running on an already-split manifest is a no-op.

Usage:
    python scripts/maintenance/split_hessen_kassel_buckets.py            # dry-run
    python scripts/maintenance/split_hessen_kassel_buckets.py --write    # persist
"""
from __future__ import annotations

import argparse
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
MANIFEST = ROOT / "scripts/cache/numista/_BO7_audit_2026-05-24.json"
NUMISTA_DIR = ROOT / "scripts/cache/numista"
BOUNDARY = 1803
LANDGR = "hessen_kassel_landgraviate"
ELECT = "hessen_kassel_electorate"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()

    manifest = json.loads(MANIFEST.read_text())
    B = manifest["in_scope_buckets"]
    L, E = B[LANDGR], B[ELECT]

    # Merged year_meta over the union (both buckets carry the same per-nid meta).
    ym: dict[int, dict] = {}
    for b in (E, L):
        for m in b.get("in_scope_year_meta") or []:
            ym.setdefault(m["nid"], m)

    union = sorted(set(L.get("in_scope_nids") or []) | set(E.get("in_scope_nids") or []))
    missing = [n for n in union if n not in ym or ym[n].get("yf") is None]
    if missing:
        print(f"ABORT: {len(missing)} union NIDs lack year_first ({missing[:10]}…) — "
              f"cannot place by date. Resolve year_meta first.")
        return 2

    def yf(n: int) -> int:
        return ym[n]["yf"]

    landg_new = sorted((n for n in union if yf(n) < BOUNDARY), key=lambda n: (yf(n), n))
    elect_new = sorted((n for n in union if yf(n) >= BOUNDARY), key=lambda n: (yf(n), n))

    before = (len(L["in_scope_nids"]), len(E["in_scope_nids"]))
    if list(L.get("in_scope_nids") or []) == landg_new and \
       list(E.get("in_scope_nids") or []) == elect_new:
        print("Already split — no change.")
        return 0

    for bucket, ids, lo_hi in ((L, landg_new, f"1559-{BOUNDARY - 1}"),
                               (E, elect_new, f"{BOUNDARY}-1866")):
        bucket["in_scope_nids"] = ids
        bucket["in_scope_year_meta"] = [ym[n] for n in ids]
        bucket["in_scope_total"] = len(ids)
        cached = [n for n in ids if (NUMISTA_DIR / f"{n}.json").exists()]
        bucket["cached_count"] = len(cached)
        bucket["gap_nids"] = [n for n in ids if n not in set(cached)]

    print(f"Hesse-Kassel split at {BOUNDARY} (year_first rule):")
    print(f"  landgraviate: {before[0]} → {len(landg_new)}  (yf < {BOUNDARY})")
    print(f"  electorate  : {before[1]} → {len(elect_new)}  (yf ≥ {BOUNDARY})")
    print(f"  union {len(union)} NIDs, each now in exactly one bucket (overlap 0).")
    if args.write:
        MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
        print(f"\nWROTE {MANIFEST}")
    else:
        print("\n(dry-run — pass --write to persist)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
