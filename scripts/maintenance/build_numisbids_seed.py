#!/usr/bin/env python3
"""NumisBids lots — Phase 3 SEED.

One seed entry per lot from the parsed sidecars
`scripts/cache/numisbids/<sale>_<lot>.json` (`scripts/parse_numisbids.py`).
A lot of several pieces (Emporium «2 Stk.») stays one entry — one type — with
one weight reading per piece (§9a); the lot names no weight-to-year mapping,
so the readings carry the lot only.

Fields taken as printed: denomination (a Roman figure as a number, «IIII
Schilling» → «4 Schilling»), years, mint, weights, catalogue numbers (Lange,
Hede, KM, …), ruler from the lot heading. Metal and fineness are not printed
and stay empty. Entity: the heading's territory (table below), else the mint
via the gazetteer.

First source: Emporium Hamburg Auction 69, lot 1676 (curator 2026-11-07, to
carry a lot of the pre-V2 record km-x009-fr-iv-1701 into the pipeline).

Usage::

    python scripts/maintenance/build_numisbids_seed.py [--dry-run]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lib.paths import NUMISBIDS_CACHE  # noqa: E402
from lib.v2_seed_writer import write_v2_seed  # noqa: E402
from lib.mint_registry import canon_for_alias, display_for_alias, entity_for_alias  # noqa: E402

SOURCE = "numisbids"

# Lot-heading territory → project entity.
_TERRITORY_ENTITY = {
    "SCHLESWIG-HOLSTEIN-GOTTORP": "gottorp_duchy",
}

_CATALOG_KEY = {"Lange": "lange", "Hede": "hede", "KM": "km", "Schou": "schou",
                "Sieg": "sieg", "Dav": "dav"}


def _ranges(years: list[int]) -> list[list[int]]:
    out: list[list[int]] = []
    for y in sorted(set(years)):
        if out and y == out[-1][1] + 1:
            out[-1][1] = y
        else:
            out.append([y, y])
    return out


def _label(rec: dict) -> str:
    house = rec.get("auction_house") or "NumisBids"
    no = rec.get("auction_no")
    return f"{house} {no}, lot {rec['lot_no']}" if no else f"{house}, lot {rec['lot_no']}"


def build_entry(rec: dict) -> dict | None:
    if not rec.get("denomination") or not rec.get("years"):
        return None
    years = rec["years"]
    rngs = _ranges(years)
    mint_raw = rec.get("mint_printed")
    mint = display_for_alias(mint_raw) or mint_raw if mint_raw else None
    entity = (_TERRITORY_ENTITY.get((rec.get("territory") or "").upper())
              or (entity_for_alias(mint_raw) if mint_raw else None))
    label = _label(rec)
    catalog: dict = {}
    for cat, nums in (rec.get("refs") or {}).items():
        key = _CATALOG_KEY.get(cat)
        if key and nums:
            catalog[key] = nums[0] if len(nums) == 1 else list(nums)
    weights = [{"value": w, "source": label} for w in rec.get("weights_g") or []]
    date = rec.get("auction_date")
    ref = f"{rec.get('auction_house')} {rec.get('auction_no')}" + (f" ({date})" if date else "") \
        + f", lot {rec['lot_no']}"
    return {
        "id": f"{SOURCE}-{rec['sale_id']}-{rec['lot_no']}",
        "fuss": "seed_unsorted",
        "phase": SOURCE,
        "kind": "kurant",
        "nominal": rec["denomination"],
        "year_label": ", ".join(f"{a}" if a == b else f"{a}-{b}" for a, b in rngs),
        "year_first": rngs[0][0],
        "year_last": rngs[-1][1],
        "year_ranges": rngs,
        "ruler": rec.get("ruler"),
        "mint": mint,
        "mint_verified": bool(mint and canon_for_alias(mint_raw)),
        "catalog": catalog,
        "weight_rough_g": weights or None,
        "weight_rough_verified": bool(weights),
        "issuing_entity": entity,
        "verified": False,
        "sources": [{"type": "auction", "url": rec["url"], "ref": ref}],
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    coins = []
    for p in sorted(NUMISBIDS_CACHE.glob("[0-9]*_[0-9]*.json")):
        e = build_entry(json.loads(p.read_text("utf-8")))
        if e:
            coins.append(e)
            print(f"  {e['id']:<24} {e['nominal']:<14} {e['year_label']:<12} "
                  f"{str(e['mint']):<10} {e['issuing_entity']} {e['catalog']}")
    stats = write_v2_seed(
        coins, SOURCE,
        "NumisBids lot pages (numisbids.com), one entry per lot: denomination, "
        "years, mint, weights and catalogue numbers as the auction house prints "
        "them; page text captured in a browser session (Cloudflare blocks "
        "scripted fetches).",
        source_label="NumisBids",
        dry_run=args.dry_run,
    )
    for ent, s in sorted(stats["per_entity"].items()):
        print(f"  {ent:<20} {s}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
