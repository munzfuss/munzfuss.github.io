"""§9a thinning, at the layer the rule is written for: a merged coin's own
weight list.

`CLAUDE.md` §9a states the condition as «one coin entry has ≥5
`weight_rough_g` entries from a single resource», and the retired
`thin_intra_subvariant_specimens.py` implemented exactly that — it ran on the
V1 curated yamls and said so: «After §9a multi-specimen merge, all of those
weights live in `weight_rough_g` and all of their citations live in
`sources[]`. The intermediate values between the lightest and heaviest
specimens carry no additional information about the standard's variance
envelope.» It trimmed a LIST inside one coin.

When V1 was torn down (2026-06-24) the replacement was rebuilt at the SEED
layer instead, and the relocation was never recorded as a change of meaning.
At seed level the rule's unit does not exist — each record carries one scalar
weight, so «≥5 entries from a single resource» cannot be evaluated — and the
seed implementation had to reinterpret it as «≥5 records in a bucket», which
is a different rule with different consequences:

  * the thinner grouped by its own `_subvariant_key` BEFORE the cross-source
    merge, so its buckets were not the merger's classes. Keeping a bucket's
    true extremes sent them to other unified entries than the intermediate
    readings had come from, and the coin the reader actually sees lost its
    envelope: measured on ikmk, 6 of 8 affected entries came out NARROWER,
    five of them collapsed to a single reading;
  * it DELETED seed records rather than trimming a list, so every re-seed
    removed coins from `final/` — 859 for kmk, 66 for ikmk — and tripped
    `verify_reflow` each time;
  * which records survived depended on the selection rule, so changing that
    rule churned the corpus even when the count stayed identical (ikmk:
    1312 -> 1312, and still 66 coins gone).

This runs after absorb, on `data/v2/final/<entity>.yml`, and none of the three
can arise: the unit is the merged coin, so the envelope is computed where it is
read; nothing is deleted but redundant readings inside one list; and the input
is the merger's own grouping rather than a second opinion about it.

What it keeps, per resource with ≥5 readings on one coin: the lightest, the
entry at position `len // 2` of the weight-sorted list, and the heaviest —
§9a's «min / middle by list position / max», the middle taken by position so
tied weights stay deterministic.

What it never drops:
  * a reading carrying an `erroneous` or `suspect` mark — a curator's
    judgement about a source, which §4 keeps visible rather than deleting;
  * anything when the coin's readings disagree on `fineness` (§9a: «If the
    bucket includes multiple fineness readings, do not thin: the variance is
    informative»);
  * `sources[]`. The retired script dropped the matching citations too, but a
    weight entry carries only (value, source) and cannot be mapped back to a
    specific citation row without the inventory number the V1 entries had. So
    the citations stay — which is also the safer side of §9a's own «merge, not
    drop» headline, and keeps `audit_lost_citations` clean.

Idempotent: re-running finds every list already at ≤3 per resource. It is a
pipeline phase rather than a one-off, because absorb re-derives the lists from
`seed_unified` on every run.
"""
from __future__ import annotations

import argparse
import glob
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from lib.seed_merge import _make_yaml_loader  # noqa: E402

FINAL_DIR = ROOT / "data" / "v2" / "final"
MIN_READINGS = 5
KEEP = 3


def _value(entry) -> float | None:
    if not isinstance(entry, dict):
        return None
    v = entry.get("value")
    return float(v) if isinstance(v, (int, float)) and v > 0 else None


def _is_marked(entry) -> bool:
    return isinstance(entry, dict) and bool(
        entry.get("erroneous") or entry.get("suspect"))


def _fineness_disagrees(coin: dict) -> bool:
    """True when the coin carries more than one distinct fineness reading."""
    f = coin.get("fineness")
    if not isinstance(f, list):
        return False
    vals = {round(float(e["value"]), 6) for e in f
            if isinstance(e, dict) and isinstance(e.get("value"), (int, float))}
    return len(vals) > 1


def thin_coin(coin: dict) -> int:
    """Trim one coin's `weight_rough_g` in place. Returns readings dropped."""
    weights = coin.get("weight_rough_g")
    if not isinstance(weights, list) or len(weights) <= KEEP:
        return 0
    if _fineness_disagrees(coin):
        return 0

    by_source: dict[str, list] = {}
    for e in weights:
        by_source.setdefault(str((e or {}).get("source", "?")), []).append(e)

    keep_ids: set[int] = set()
    dropped = 0
    for _src, entries in by_source.items():
        marked = [e for e in entries if _is_marked(e)]
        plain = [e for e in entries if not _is_marked(e)]
        keep_ids.update(id(e) for e in marked)
        if len(plain) < MIN_READINGS:
            keep_ids.update(id(e) for e in plain)
            continue
        ordered = sorted(plain, key=lambda e: (_value(e) is None, _value(e) or 0.0))
        idx = sorted({0, len(ordered) // 2, len(ordered) - 1})
        for i, e in enumerate(ordered):
            if i in idx:
                keep_ids.add(id(e))
            else:
                dropped += 1
    if not dropped:
        return 0
    coin["weight_rough_g"] = [e for e in weights if id(e) in keep_ids]
    return dropped


def run(dry_run: bool) -> int:
    yaml = _make_yaml_loader()
    total_coins = total_dropped = touched = 0
    for path in sorted(glob.glob(str(FINAL_DIR / "*.yml"))):
        doc = yaml.load(Path(path).read_text())
        coins = (doc or {}).get("coins") or []
        if not coins:
            continue
        dropped_here = coins_here = 0
        for c in coins:
            if not isinstance(c, dict):
                continue
            n = thin_coin(c)
            if n:
                dropped_here += n
                coins_here += 1
        total_coins += coins_here
        total_dropped += dropped_here
        if dropped_here:
            touched += 1
            print(f"  {Path(path).name}: {coins_here} coin(s), "
                  f"{dropped_here} redundant reading(s)")
            if not dry_run:
                with open(path, "w") as fh:
                    yaml.dump(doc, fh)
    verb = "would drop" if dry_run else "dropped"
    print(f"\nTOTAL: {verb} {total_dropped} reading(s) on {total_coins} coin(s) "
          f"across {touched} file(s)")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--apply", action="store_true", help="persist (default: dry-run)")
    ap.add_argument("--dry-run", action="store_true", help="report only (default)")
    args = ap.parse_args()
    return run(dry_run=not args.apply)


if __name__ == "__main__":
    raise SystemExit(main())
