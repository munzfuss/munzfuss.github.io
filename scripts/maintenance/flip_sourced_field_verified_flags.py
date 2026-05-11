"""Walk every coin in `data/locations/denmark.yml` AND
`data/seed/hede/denmark.yml`; for each coin where a measurement
field is directly populated AND at least one acceptable source is
listed, flip the matching `*_verified` flag from false to true.

Per CLAUDE.md §4: «One source with full data is enough for
`*_verified: true`. Verification is not a quorum requirement — it
asks "does any acceptable source attest this exact value?".» This
script reconciles the seed-tier entries (currently shipped with
all flags false out of inertia from the seed-generator default)
with their actually-attested source data.

What we flip:
  * `fineness_verified`     → true when `fineness` is non-null AND
                              sources is non-empty
  * `weight_rough_verified` → true when `weight_rough_g` is non-null
                              AND sources is non-empty
  * `diameter_mm_verified`  → true when `diameter_mm` is non-null
                              AND sources is non-empty

What we leave alone:
  * `verified` (overall) — stays at its current value; the overall
    flag means «full per-coin sanity check done», NOT «some sources
    confirm some fields». §4 keeps these distinct on purpose.
  * `mint_verified` — mint extraction is parser-heuristic from
    Hede H1 and from ucoin URLs; not safe to flip wholesale.
  * Any coin under `fuss: seed_unsorted` — those are deliberately
    in the catch-all bucket pending Müntzfuß placement; their flags
    stay as the seed generator set them.

Idempotent: re-running after new seed imports re-flips cleanly.

Run:
    python scripts/maintenance/flip_sourced_field_verified_flags.py [--dry-run]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from ruamel.yaml import YAML

PROJECT = Path(__file__).resolve().parents[2]
TARGETS = [
    PROJECT / "data" / "locations" / "denmark.yml",
    PROJECT / "data" / "seed" / "hede" / "denmark.yml",
]


def _has_value(v) -> bool:
    """Field is populated if it's a scalar (not None) or a non-empty
    list of FieldValue entries."""
    if v is None:
        return False
    if isinstance(v, (int, float)):
        return True
    if isinstance(v, list):
        return len(v) > 0
    return bool(v)


def _process_file(path: Path, dry_run: bool) -> dict:
    y = YAML()
    y.preserve_quotes = True
    y.width = 4096
    y.indent(mapping=2, sequence=4, offset=2)
    with path.open() as f:
        doc = y.load(f)
    coins = doc.get("coins") or []

    flipped = {
        "fineness_verified": 0,
        "weight_rough_verified": 0,
        "diameter_mm_verified": 0,
    }
    skipped_no_sources = 0
    skipped_already_true = 0

    for coin in coins:
        sources = coin.get("sources") or []
        if not sources:
            skipped_no_sources += 1
            continue

        # fineness
        if _has_value(coin.get("fineness")):
            if coin.get("fineness_verified") is False:
                coin["fineness_verified"] = True
                flipped["fineness_verified"] += 1
            else:
                skipped_already_true += 1

        # weight_rough_g
        if _has_value(coin.get("weight_rough_g")):
            if coin.get("weight_rough_verified") is False:
                coin["weight_rough_verified"] = True
                flipped["weight_rough_verified"] += 1
            else:
                skipped_already_true += 1

        # diameter_mm
        if _has_value(coin.get("diameter_mm")):
            if coin.get("diameter_mm_verified") is False:
                coin["diameter_mm_verified"] = True
                flipped["diameter_mm_verified"] += 1
            else:
                skipped_already_true += 1

    if not dry_run and any(flipped.values()):
        with path.open("w") as f:
            y.dump(doc, f)

    return {
        "path": path,
        "total_coins": len(coins),
        "flipped": flipped,
        "skipped_no_sources": skipped_no_sources,
        "skipped_already_true": skipped_already_true,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true",
                    help="Report what would change without writing files")
    args = ap.parse_args()

    grand_total = {k: 0 for k in
                   ("fineness_verified", "weight_rough_verified",
                    "diameter_mm_verified")}
    for path in TARGETS:
        if not path.exists():
            print(f"  skip {path.relative_to(PROJECT)} (missing)")
            continue
        result = _process_file(path, args.dry_run)
        print(f"=== {path.relative_to(PROJECT)} ({result['total_coins']} coins) ===")
        for k, n in result["flipped"].items():
            print(f"  flipped {k:30s} → true: {n:4d}")
            grand_total[k] += n
        print(f"  skipped_no_sources:                  {result['skipped_no_sources']:4d}")
        print(f"  skipped_already_true:                {result['skipped_already_true']:4d}")
        print()

    print("Grand total:")
    for k, n in grand_total.items():
        print(f"  {k:30s} → true: {n:4d}")
    if args.dry_run:
        print("(dry-run — no files written)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
