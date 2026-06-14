#!/usr/bin/env python3
"""Scoped application of the absorb «non-None member wins over None foundation»
rule to the already-saved V2 final layer — WITHOUT a full absorb re-derivation
(which would also run the stale-foundation purge / self-foundation fold /
re-validate eviction churn and conflict with manual curation).

The rule itself lives in the pipeline: `absorb_seeds_into_final_v2.py`
gap-fills `_FOUNDATION_GAPFILL_FIELDS` (foundation-immutable minus
fuss/phase/kind) on every absorb run (commit 5df1c1e). This pass applies the
SAME rule, surgically, to the existing data: for each final entry whose
descriptive field is None, adopt the first composed_of member's (seed_unified)
non-None value. fuss/phase/kind are never touched; a non-None foundation value
is never overridden.

Affected fields in the current corpus: ruler (67 entries) + mintmaster (258).

Final is re-dumped with absorb's serializer (yaml.dump, sort_keys=False,
default_flow_style=False, width=120), so the diff is the gap-fills only.

Usage:
    python scripts/maintenance/apply_foundation_gapfill.py            # dry-run
    python scripts/maintenance/apply_foundation_gapfill.py --apply
"""
from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "lib"))
sys.path.insert(0, str(ROOT / "scripts" / "maintenance"))

# Single source of truth for the rule's field set (the pipeline's own constant).
from absorb_seeds_into_final_v2 import _FOUNDATION_GAPFILL_FIELDS  # noqa: E402

V2_FINAL = ROOT / "data" / "v2" / "final"
V2_SEED_UNIFIED = ROOT / "data" / "v2" / "seed_unified"


def _load_seed_unified_index() -> dict[str, dict]:
    """{id: unified-entry} across all seed_unified/<entity>.yml — the bridge a
    final entry's composed_of points into."""
    by_id: dict[str, dict] = {}
    for path in sorted(V2_SEED_UNIFIED.glob("*.yml")):
        doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        for c in doc.get("coins") or []:
            if isinstance(c, dict) and c.get("id"):
                by_id[c["id"]] = c
    return by_id


def _gapfill_coin(coin: dict, su: dict[str, dict]) -> list[str]:
    """Apply the gap-fill rule to one final entry in place. Returns the list of
    fields filled (for reporting)."""
    members = [su[cid] for cid in (coin.get("composed_of") or []) if cid in su]
    if not members:
        return []
    filled: list[str] = []
    for fld in _FOUNDATION_GAPFILL_FIELDS:
        if coin.get(fld) is None:
            mv = next((m.get(fld) for m in members
                       if m.get(fld) not in (None, [])), None)
            if mv is not None:
                coin[fld] = mv
                filled.append(fld)
    return filled


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--apply", action="store_true",
                    help="write changes (default: dry-run)")
    args = ap.parse_args()

    su = _load_seed_unified_index()
    field_counts: Counter = Counter()
    samples: dict[str, tuple] = {}
    total_entries = 0

    for path in sorted(V2_FINAL.glob("*.yml")):
        doc = yaml.safe_load(path.read_text(encoding="utf-8"))
        changed = 0
        for coin in doc.get("coins", []):
            filled = _gapfill_coin(coin, su)
            if filled:
                changed += 1
                for f in filled:
                    field_counts[f] += 1
                    samples.setdefault(f, (coin.get("id"), coin.get(f)))
        if not changed:
            continue
        total_entries += changed
        print(f"{path.name:28} {changed:4d} entr{'y' if changed == 1 else 'ies'}")
        if args.apply:
            out = yaml.dump(doc, sort_keys=False, allow_unicode=True,
                            default_flow_style=False, width=120)
            path.write_text(out, encoding="utf-8")

    print("\nfields filled:")
    for f, n in field_counts.most_common():
        ex = samples[f]
        print(f"  {f:12} {n:4}   e.g. {ex[0]} → {ex[1]!r}")
    print(f"\n{'APPLIED' if args.apply else 'DRY-RUN'}: {total_entries} entries"
          f"{' written' if args.apply else ' would change'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
