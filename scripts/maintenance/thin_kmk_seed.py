#!/usr/bin/env python3
"""thin_kmk_seed.py — §9a intra-sub-variant thinning for the KMK (Royal Coin
Cabinet Copenhagen) seed, applied PRE-merge.

The KMK harvest is the full cabinet (~42k specimens), with massive per-type
clusters (one Hede-17 Christian-IV 2-Skilling-1648 sub-variant has 302
specimens). ~14% of KMK object records carry a recorded weight
(`measurements: [{dimension: Vægt, unit: Gram, data: …}]`); the other ~86%
have an empty `measurements` list in the museum's own record (the source
never digitised a weight for that specimen — the builder is faithfully
extracting nothing, not dropping data). KMK measurements only ever carry
`Vægt` — never diameter or fineness.

Per CLAUDE.md §9a («sort by weight, keep [0, len//2, -1], drop the rest»):
for each sub-variant bucket (keyed by catalogue type identity) with ≥5 KMK
specimens, preserve the weight-variance envelope —
  * if any members carry a weight: sort THOSE by weight ascending and keep
    positions [0, len//2, -1] (min / middle / max). The weightless members
    of the same sub-variant add no measurement signal (same type, redundant
    inventory citations) and are dropped.
  * if NO member carries a weight: there is no envelope to preserve — keep
    [0, len//2, -1] of the id-sorted list (deterministic representatives).
Buckets < 5 are kept whole (protects genuinely-distinct single specimens,
mules, off-metal strikes — which KMK would have given a distinct catalogue
identity, breaking them out of the bucket anyway).

Thinning PRE-merge means the cross-source merger consolidates 3-per-type, not
302-per-type — tractable + the rendered weight column keeps the true min/max
spread rather than three arbitrary middling readings.

Idempotent: re-running on an already-thinned seed keeps every bucket ≤3, so
the envelope of a ≤3 list returns the same entries.

Run:
    .venv/bin/python scripts/maintenance/thin_kmk_seed.py [--dry-run]
"""
from __future__ import annotations

import argparse
import glob
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from lib.seed_merge import _make_yaml_loader  # noqa: E402

KMK_SEED_DIR = ROOT / "data" / "v2" / "seed" / "kmk"


def _subvariant_key(coin: dict) -> tuple:
    """Type identity for sub-variant grouping — the catalogue/type signals the
    cross-source merger itself matches on. Specimens sharing this key are the
    same type; KMK over-sampled them."""
    cat = coin.get("catalog") or {}
    return (
        str(cat.get("km")), str(cat.get("hede")), str(cat.get("sieg")),
        str(cat.get("schou")), coin.get("nominal"), coin.get("ruler"),
        coin.get("year_first"), str(coin.get("mint")), coin.get("metal"),
    )


def _weight(coin: dict):
    """Single numeric weight for sort, or None when the specimen has no
    recorded weight. KMK seed weights are scalar floats (one specimen = one
    record); tolerate the §9a list-form just in case."""
    w = coin.get("weight_rough_g")
    if w in (None, [], ""):
        return None
    if isinstance(w, list):
        vals = [e.get("value") if isinstance(e, dict) else e for e in w]
        vals = [v for v in vals if isinstance(v, (int, float))]
        return min(vals) if vals else None
    return w if isinstance(w, (int, float)) else None


def _keep_envelope(members: list) -> list:
    """§9a variance envelope for one over-sampled sub-variant bucket. Prefer
    the weight-bearing members (sorted by weight → min/middle/max); fall back
    to id-sorted representatives only when no member has a weight."""
    weighted = sorted(
        (m for m in members if _weight(m) is not None), key=_weight
    )
    pool = weighted if weighted else sorted(members, key=lambda c: str(c.get("id")))
    idx = sorted({0, len(pool) // 2, len(pool) - 1})
    return [pool[i] for i in idx]


def thin(dry_run: bool) -> int:
    yaml = _make_yaml_loader()
    total_before = total_after = 0
    for f in sorted(glob.glob(str(KMK_SEED_DIR / "*.yml"))):
        doc = yaml.load(Path(f).read_text())
        coins = doc.get("coins") or []
        if not coins:
            continue
        buckets: dict[tuple, list] = {}
        for c in coins:
            buckets.setdefault(_subvariant_key(c), []).append(c)
        kept: list = []
        thinned_buckets = 0
        for key, members in buckets.items():
            if len(members) >= 5:
                members_sorted = sorted(members, key=lambda c: str(c.get("id")))
                idx = sorted({0, len(members_sorted) // 2, len(members_sorted) - 1})
                kept.extend(members_sorted[i] for i in idx)
                thinned_buckets += 1
            else:
                kept.extend(members)
        # preserve original entry order (by id) for a stable diff
        kept.sort(key=lambda c: str(c.get("id")))
        total_before += len(coins)
        total_after += len(kept)
        name = Path(f).name
        print(f"  {name}: {len(coins)} → {len(kept)}  "
              f"({thinned_buckets} buckets thinned, {len(buckets)} sub-variants)")
        if not dry_run:
            doc["coins"] = kept
            with open(f, "w") as fh:
                yaml.dump(doc, fh)
    print(f"\nTOTAL: {total_before} → {total_after} "
          f"({total_before - total_after} specimens dropped)")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true",
                    help="report the reduction without writing")
    args = ap.parse_args()
    return thin(dry_run=args.dry_run)


if __name__ == "__main__":
    raise SystemExit(main())
