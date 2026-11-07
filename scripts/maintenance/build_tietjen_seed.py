#!/usr/bin/env python3
"""Tietjen + Co. auction lots — Phase 3 SEED.

From the parsed lot lists `scripts/cache/auctions/tietjen/auktion_<n>_lots.json`
(`scripts/parse_tietjen.py`) one seed entry per lot named in `LOTS` below. A
catalogue holds thousands of lots of every country; a lot enters the seed
only when it is listed here, with the entity its catalogue section maps to,
so a new lot is one line in this table (curator decides which lots matter).

Fields as printed: denomination, years, mint mark (→ `mintmaster`), weight,
catalogue numbers (Behr. → behrens, Dav. → dav, J. → «Jaeger# N» in
others, Lange, Hede, KM, Kunzel, Friedb. → fr), grade not used. Metal and
fineness are not printed.

First lot: Auktion 110 (Hamburg, 17 December 2012), lot 88, Lübeck 48
Schilling Courant 1752 (curator 2026-11-07: the source of the Behrens 291a
/ Jaeger 22 the pre-V2 record km-168-1-1752 carried).

Usage::

    python scripts/maintenance/build_tietjen_seed.py [--dry-run]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lib.paths import HARVEST_ROOT  # noqa: E402
from lib.v2_seed_writer import write_v2_seed  # noqa: E402

SOURCE = "tietjen"
CACHE = HARVEST_ROOT / "auctions" / "tietjen"

# auction → {lot: entity}
LOTS: dict[str, dict[int, str]] = {
    "110": {88: "hanseatic_lubeck"},
}

# auction → (date as printed on the title page, catalogue URL)
AUCTIONS = {
    "110": ("17. Dezember 2012",
            "https://www.yumpu.com/de/document/view/7817078/auktion-110-auktionshaus-tietjen-co"),
}

_TYPED = {"Behr": "behrens", "Dav": "dav", "Lange": "lange", "Hede": "hede",
          "KM": "km", "Friedb": "fr"}
_OTHERS = {"J": "Jaeger", "Gaed": "Gaedechens", "Kunzel": "Kunzel", "Gaett": "Gaettens"}


def _ranges(years: list[int]) -> list[list[int]]:
    out: list[list[int]] = []
    for y in sorted(set(years)):
        if out and y == out[-1][1] + 1:
            out[-1][1] = y
        else:
            out.append([y, y])
    return out


def build_entry(auction: str, lot: dict, entity: str) -> dict | None:
    if not lot.get("denomination") or not lot.get("years"):
        return None
    rngs = _ranges(lot["years"])
    catalog: dict = {}
    others: list[str] = []
    for cat, nums in (lot.get("refs") or {}).items():
        nums = [n for n in nums if n != "–"]
        if not nums:
            continue
        if cat in _TYPED:
            catalog[_TYPED[cat]] = nums[0] if len(nums) == 1 else nums
        elif cat in _OTHERS:
            others += [f"{_OTHERS[cat]}# {n}" for n in nums]
    if others:
        catalog["others"] = others
    date, url = AUCTIONS[auction]
    label = f"Tietjen {auction}, lot {lot['lot']}"
    entry = {
        "id": f"{SOURCE}-{auction}-{lot['lot']}",
        "fuss": "seed_unsorted",
        "phase": SOURCE,
        "kind": "kurant",
        "nominal": lot["denomination"],
        "year_label": ", ".join(f"{a}" if a == b else f"{a}-{b}" for a, b in rngs),
        "year_first": rngs[0][0],
        "year_last": rngs[-1][1],
        "year_ranges": rngs,
        "catalog": catalog,
        "weight_rough_g": [{"value": w, "source": label} for w in lot.get("weights_g") or []] or None,
        "weight_rough_verified": bool(lot.get("weights_g")),
        "issuing_entity": entity,
        "verified": False,
        "sources": [{"type": "auction", "url": url,
                     "ref": f"Tietjen + Co., Auktion {auction} ({date}), Los {lot['lot']}"}],
    }
    if lot.get("mint_mark"):
        entry["mintmaster"] = lot["mint_mark"]
    return entry


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    coins = []
    for auction, wanted in LOTS.items():
        data = json.loads((CACHE / f"auktion_{auction}_lots.json").read_text("utf-8"))
        by_no = {x["lot"]: x for x in data["lots"]}
        for no, entity in wanted.items():
            lot = by_no.get(no)
            if lot is None:
                print(f"  ⚠ Auktion {auction} lot {no} not in the parsed list")
                continue
            e = build_entry(auction, lot, entity)
            if e:
                coins.append(e)
                print(f"  {e['id']:<18} {e['nominal']:<24} {e['year_label']:<8} {entity} {e['catalog']}")
    stats = write_v2_seed(
        coins, SOURCE,
        "Tietjen + Co. (Hamburg) auction catalogues, lots listed in the builder: "
        "denomination, years, mint mark, weight and catalogue numbers as printed.",
        source_label="Tietjen + Co.",
        dry_run=args.dry_run,
    )
    for ent, s in sorted(stats["per_entity"].items()):
        print(f"  {ent:<20} {s}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
