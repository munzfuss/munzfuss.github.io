"""One-shot migration: route Denmark's 1873-1914 Krone-Mønt coinage
from the old tagging-convention buckets (`reichsgoldmuenzfuss` for
gold and `30_thaler` for silver/copper) onto the dedicated
`kronefod` (gold) and `kronefod_silver` (auxiliaries) Müntzfüße
added to `data/shared/fuesse.yml`.

Per `docs/dk_kronefod_1873_research.md`. The German Reichsgold-
münzfuß (1871) and the Krone-fod (1873) are mathematically linked
by the fixed 8 Kroner = 9 Mark gold parity, but legally and
denomination-laddered they are distinct standards. Likewise the
30-Thaler-Fuß is Vereinsmünze (1857-1873), NOT Krone-Mønt.

Routing rules (applied to coins currently under the old buckets):

  fuss: reichsgoldmuenzfuss     metal: gold     → kronefod
  fuss: reichsgoldmuenzfuss     metal: silver*  → kronefod_silver
  fuss: 30_thaler               metal: silver   → kronefod_silver
  fuss: 30_thaler               metal: copper   → kronefod_silver
  fuss: 30_thaler               metal: billon   → kronefod_silver

  * Silver coins mis-bucketed under reichsgoldmuenzfuss/A were
    visible in the pre-refactor data as «2 Kroner @ .8, metal=gold»
    (parser confused .8 fineness as gold-fineness — these are
    silver 2-Kr Kurant pieces) plus a couple of metal=silver
    entries Numista-style.

Phase: all routed to `A` (1873-1914). Existing fraction values
preserve cleanly because both old buckets used the same fraction
set as the new ones (5/10/20 for gold; 2/1 + 1/4/1/10 + 1/20/etc.
for silver).

Idempotent: re-running after a follow-up bulk import re-routes any
fresh entries that landed in the old buckets, leaving the rest
untouched.

Run:
    python scripts/maintenance/migrate_dk_kronefod_refactor.py [--dry-run]
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


def _new_bucket(coin: dict) -> str | None:
    old_fuss = coin.get("fuss")
    metal = coin.get("metal")
    nominal = (coin.get("nominal") or "").lower()
    # Gold under the old reichsgoldmuenzfuss bucket → kronefod
    if old_fuss == "reichsgoldmuenzfuss":
        # Krone-fod gold ladder is 5/10/20 Kroner. Anything else
        # at this bucket (silver mistag) routes to kronefod_silver.
        # Detect mistag by metal=silver OR by fineness < 0.9 (silver
        # 2 Kr at .800).
        fineness = coin.get("fineness")
        if metal == "gold":
            # Sanity-check the fineness: if it's < .85 the coin is
            # actually silver despite the metal tag — route accordingly.
            if isinstance(fineness, (int, float)) and fineness < 0.85:
                return "kronefod_silver"
            return "kronefod"
        if metal == "silver" or metal == "billon" or metal == "copper":
            return "kronefod_silver"
        # No metal — route by nominal token.
        if any(t in nominal for t in ("10 kroner", "20 kroner", "5 kroner")):
            return "kronefod"
        return "kronefod_silver"
    if old_fuss == "30_thaler":
        # 30_thaler bucket on the Denmark page is the silver / copper
        # Krone-Mønt auxiliary tier (1/2 Kroner Kurant + 25/10 øre
        # Scheide + 5/2/1 øre copper). All routes to kronefod_silver.
        return "kronefod_silver"
    return None


def _new_fraction(coin: dict, new_bucket: str) -> str | None:
    """Adjust fraction value if needed. The old buckets used the same
    fraction strings as the new ones, but the silver-mistag-under-
    reichsgoldmuenzfuss case has fraction 10 / 20 (the gold value
    of the silver «10 Kroner» piece). For kronefod_silver, the silver
    Krone-Mønt fractions cap at «2» — anything higher is a tag bug.
    """
    fraction = coin.get("fraction")
    if not fraction:
        return None
    if new_bucket == "kronefod":
        # gold ladder: 5/10/20 — pass through
        return None
    if new_bucket == "kronefod_silver":
        # silver/aux ladder: 2/1/1/4/1/10/1/20/1/50/1/100
        # «10» or «20» on silver = mistag (the 2 Kroner at .800 was
        # bucketed as gold 10 Kroner). Re-derive from nominal.
        if fraction in ("10", "20", "5"):
            nominal = (coin.get("nominal") or "").lower()
            if "2 kroner" in nominal:
                return "2"
            if "1 krone" in nominal:
                return "1"
            if "10 kroner" in nominal or "20 kroner" in nominal:
                # silver «10 / 20 Kroner» entries with .9 fineness might
                # be mis-classified silver-of-gold-coin; reroute to kronefod
                # via a None signal — the caller falls back to old bucket.
                return None
        return None
    return None


def _process(path: Path, dry_run: bool) -> dict:
    y = YAML()
    y.preserve_quotes = True
    y.width = 4096
    y.indent(mapping=2, sequence=4, offset=2)
    with path.open() as f:
        doc = y.load(f)
    coins = doc.get("coins") or []

    counts = {
        "to_kronefod_gold": 0,
        "to_kronefod_silver_from_rgm": 0,
        "to_kronefod_silver_from_30t": 0,
        "unchanged": 0,
        "skipped_no_route": 0,
    }
    for coin in coins:
        old_fuss = coin.get("fuss")
        if old_fuss not in ("reichsgoldmuenzfuss", "30_thaler"):
            counts["unchanged"] += 1
            continue
        new_bucket = _new_bucket(coin)
        if new_bucket is None:
            counts["skipped_no_route"] += 1
            continue
        # Apply new fuss
        coin["fuss"] = new_bucket
        coin["phase"] = "A"
        # Re-fraction if needed
        new_frac = _new_fraction(coin, new_bucket)
        if new_frac:
            coin["fraction"] = new_frac
        # Track counters
        if new_bucket == "kronefod":
            counts["to_kronefod_gold"] += 1
        elif new_bucket == "kronefod_silver":
            if old_fuss == "reichsgoldmuenzfuss":
                counts["to_kronefod_silver_from_rgm"] += 1
            else:
                counts["to_kronefod_silver_from_30t"] += 1

    if not dry_run and any(v for k, v in counts.items() if k != "unchanged"):
        with path.open("w") as f:
            y.dump(doc, f)

    return {"path": path, "total": len(coins), **counts}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    for path in TARGETS:
        if not path.exists():
            continue
        result = _process(path, args.dry_run)
        print(f"=== {result['path'].relative_to(PROJECT)} ({result['total']} coins) ===")
        for k, v in result.items():
            if k in ("path", "total"):
                continue
            print(f"  {k:35s} {v:4d}")
        print()
    if args.dry_run:
        print("(dry-run — no files written)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
