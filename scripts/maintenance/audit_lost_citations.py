#!/usr/bin/env python3
"""Detect (and optionally heal) final entries that LOST source citations.

WHY THIS EXISTS — a manual final reconciliation that sets
`final.sources = cluster.sources` (REPLACE) instead of unioning drops any
citation the final carried from an earlier fold/merge but the current
seed_unified cluster doesn't re-attest. Caught 2026-06-28: a c7h13 cross-entity
reconcile dropped «Bruun Part III, lot 11295, p. 147» — the SOLE source for KM
651.1 (from a dedup-folded km-651-1). A project-wide sweep then found 5 such
finals (c4h118/c4h119a from the same session + c5h57 dk-tid-97535 + historical
c8h8bb/c8h4a). The normal absorb path unions sources via `_collect_sources`, so
this only bites MANUAL reconciliations — but those happen, so this gate guards
against silent §9a citation loss.

The check: for every final entry, the union of its `composed_of` members'
source URLs (resolved against seed_unified) should be ⊆ the final's own source
URLs. Any member-source URL the final is MISSING is a lost citation.

Museum specimen URLs (natmus.dk / samlinger) are EXCLUDED — those are
photo-record specimens legitimately thinned per §9a (intra-sub-variant
thinning), not substantive catalogue citations.

Usage:
    .venv/bin/python scripts/maintenance/audit_lost_citations.py          # report
    .venv/bin/python scripts/maintenance/audit_lost_citations.py --apply  # heal (union back)
Exit 0 = clean; exit 1 = lost citations found (report mode).
"""
from __future__ import annotations

import argparse
import glob
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from lib import yaml_io  # noqa: E402

_L = getattr(yaml, "CSafeLoader", yaml.SafeLoader)
_MUSEUM = ("natmus", "samlinger")


def _load_unified() -> dict:
    out = {}
    for f in glob.glob(str(ROOT / "data/v2/seed_unified/*.yml")):
        for c in (yaml.load(open(f), Loader=_L) or {}).get("coins", []):
            if c.get("id"):
                out[c["id"]] = c
    return out


def _urls(coin: dict) -> set:
    return {s.get("url") for s in (coin.get("sources") or []) if s.get("url")}


def _missing_for(coin: dict, uni: dict) -> set:
    """member-source URLs (non-museum) absent from the final."""
    have = _urls(coin)
    member = set()
    for m in coin.get("composed_of") or []:
        mu = uni.get(m)
        if mu:
            member |= _urls(mu)
    miss = member - have
    return {u for u in miss if not any(t in u for t in _MUSEUM)}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true",
                    help="union the missing member-sources back into the finals")
    args = ap.parse_args()

    uni = _load_unified()
    total_finals = 0
    flagged: list[tuple[str, str, int]] = []
    healed = 0

    for path in sorted(glob.glob(str(ROOT / "data/v2/final/*.yml"))):
        ent = Path(path).stem
        ctx, doc = yaml_io.load(Path(path))
        changed = False
        for c in doc.get("coins") or []:
            total_finals += 1
            miss = _missing_for(c, uni)
            if not miss:
                continue
            flagged.append((ent, c.get("id"), len(miss)))
            if args.apply:
                have = _urls(c)
                for m in c.get("composed_of") or []:
                    mu = uni.get(m)
                    if not mu:
                        continue
                    for s in mu.get("sources") or []:
                        u = s.get("url") or ""
                        if u in miss and u not in have:
                            c.setdefault("sources", []).append(s)
                            have.add(u)
                            healed += 1
                changed = True
        if changed and args.apply:
            yaml_io.save(ctx, Path(path), doc)

    print(f"finals scanned:           {total_finals}")
    print(f"finals missing citations: {len(flagged)}")
    for ent, cid, n in sorted(flagged, key=lambda x: -x[2])[:30]:
        print(f"  [{ent}] {cid}: {n} lost")
    if args.apply:
        print(f"\nhealed: {healed} citations unioned back.")
        return 0
    return 1 if flagged else 0


if __name__ == "__main__":
    raise SystemExit(main())
