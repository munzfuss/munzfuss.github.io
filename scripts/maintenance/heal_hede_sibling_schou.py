#!/usr/bin/env python3
"""Strip Schou values that belong to a SIBLING Hede on the same danskmoent page.

WHY A HEAL AND NOT JUST A RE-SEED
---------------------------------
`catalog` is in the hede builder's DEEP_MERGE_FIELDS and `schou` is
list-capable, so a regeneration UNIONS the fresh value with whatever the seed
already holds. It can add, never subtract. The contaminated values therefore
survive every re-seed — verified 2026-08-07: a full builder run changed nothing
but the `generated_at` timestamp, and dk-hede-nc5h11 still read `['2', '5']`.

WHAT WAS CONTAMINATED
---------------------
A danskmoent page that documents several Hede numbers carries a page-level
`catalog_refs` roll-up alongside the correct per-Hede breakdown in
`specs.by_hede`. Seeds built before the parser emitted the per-Hede refs took
the roll-up, so each sub-Hede got the union of its siblings' Schou numbers:

    nc5h11.json  by_hede 11 → Schou 5   ·  by_hede 12 → Schou 2
    page-level   Schou ['5', '2']
    both seeds   Schou ['2', '5']       ← wrong on both

That matters beyond display: `schou/<ruler>` is a matching key in the
cross-source merger (measured cross-reign collision 64 %), so a borrowed value
is a FALSE unifying edge — exactly the §9.4 evidence a merge is allowed to rest
on. dk-hede-nc5h11 and dk-hede-nc5h12 are two different coins that appeared to
share Schou 2 and 5.

The builder is already correct for these pages — it passes
`sub_spec["catalog_refs"]` as an override — so once the stale value is gone the
union of (healed seed, fresh emission) is correct and stays correct.

SCOPE — deliberately narrow
---------------------------
Only removes a value that is BOTH absent from the sub-Hede's own
`catalog_refs` AND present in a sibling's on the same page. Values that are
merely unexplained (not the sub's, not a sibling's — 11 seeds, mostly
comma-joined parse artefacts and Zincksamlingen afslag rows) are LEFT ALONE
and listed at the end for review; guessing at those is how a heal turns into
data loss.

Single-Hede pages have their own contamination shape — a Schou scraped from a
prose cross-reference to an off-strike, e.g. c7h25 «Findes også i guld …
Schou 7a» — which this script does NOT touch. `by_hede` is empty there, so
there is no per-Hede truth to compare against; that one has to be fixed in
parse_hede.py and needs a re-parse.

RE-RUNNING IT
-------------
After the 2026-08-07 pass, a dry run still reports ONE seed: dk-hede-c5h40,
Schou ['3'] where the cache says 2. Do NOT keep applying it there. That value
is not sibling contamination the heal can settle — the BUILDER re-emits ['3']
for c5h40 on the very next run (and c5h39 carries ['4'], a number that appears
nowhere on the page). Applying and re-seeding in a loop just alternates the two
states. It belongs with the parse_hede.py work, not here.

Usage:  heal_hede_sibling_schou.py [--apply]
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from lib.paths import HARVEST_ROOT  # noqa: E402

from lib import yaml_io  # noqa: E402

CACHE = HARVEST_ROOT / "hede"
SEED = ROOT / "data" / "v2" / "seed" / "hede"


def norm(v) -> set[str]:
    """Split the parser's comma/«og»-joined ref strings into single values."""
    out: set[str] = set()
    for x in (v if isinstance(v, list) else [v] if v else []):
        for part in str(x).replace(" og ", ",").split(","):
            part = part.strip()
            if part:
                out.add(part)
    return out


def page_truth() -> tuple[dict[str, set[str]], dict[str, set[str]]]:
    """(own Schou per seed id, sibling Schou per seed id) for multi-Hede pages."""
    own: dict[str, set[str]] = {}
    sibling: dict[str, set[str]] = {}
    for path in sorted(glob.glob(str(CACHE / "*.json"))):
        pid = os.path.basename(path)[:-5]
        if pid.startswith("_"):
            continue
        try:
            d = json.load(open(path))
        except Exception:
            continue
        by_hede = (d.get("specs") or {}).get("by_hede") or {}
        if len(by_hede) < 2:
            continue
        vol = d.get("ruler_volume") or ""
        per = {h: norm((s.get("catalog_refs") or {}).get("Schou"))
               for h, s in by_hede.items()}
        for h, mine in per.items():
            if not mine:
                continue          # no per-Hede truth → nothing to compare to
            sid = f"dk-hede-{vol}{h}"
            own[sid] = mine
            sibling[sid] = set().union(
                *[v for k, v in per.items() if k != h]) if len(per) > 1 else set()
    return own, sibling


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--apply", action="store_true",
                    help="write the seeds (default: report only)")
    args = ap.parse_args()

    own, sibling = page_truth()
    healed, unexplained = [], []

    for seed_path in sorted(glob.glob(str(SEED / "*.yml"))):
        # Round-trip through yaml_io so the file keeps its own formatting.
        # A safe_load + canonical dump reformats everything it touches, and
        # these seeds carry curator `_source_errata` blocks (§CN) whose block
        # scalars and flow sequences would come back as escaped one-liners —
        # identical data, much worse to read, on the surface where readability
        # is the point. (Caught on the first attempt at this heal, 2026-08-07.)
        ctx, doc = yaml_io.load(seed_path)
        changed = False
        for coin in doc.get("coins") or []:
            sid = coin.get("id")
            if sid not in own:
                continue
            cat = coin.get("catalog") or {}
            got = norm(cat.get("schou"))
            if not got:
                continue
            borrowed = (got - own[sid]) & sibling[sid]
            leftover = (got - own[sid]) - sibling[sid]
            if leftover:
                unexplained.append((sid, sorted(own[sid]), sorted(leftover)))
            if not borrowed:
                continue
            kept = sorted(got - borrowed)
            healed.append((sid, sorted(got), kept, sorted(borrowed)))
            if kept:
                cat["schou"] = kept[0] if len(kept) == 1 else kept
            else:
                # Everything the seed held belonged to a sibling — c5h40 is the
                # one such case (own Schou 2, seed carried only Schou 3). Drop
                # the key rather than leave an empty list: the very next builder
                # run repopulates it from `by_hede`, and an absent field is an
                # honest «not stated here» while `[]` reads as «none exists».
                cat.pop("schou", None)
            changed = True
        if changed and args.apply:
            yaml_io.save(ctx, seed_path, doc)

    print(f"seeds carrying a sibling's Schou: {len(healed)}\n")
    for sid, before, after, borrowed in healed:
        print(f"  {sid:24} {before} → {after}   (dropped {borrowed}, the sibling's)")

    if unexplained:
        print(f"\nLEFT ALONE — Schou values that are neither the sub-Hede's own nor a "
              f"sibling's ({len(unexplained)}). Review, do not guess:")
        for sid, mine, extra in unexplained:
            print(f"  {sid:24} own={mine}  unexplained={extra}")

    print("\n--- DRY RUN — nothing written. Re-run with --apply. ---"
          if not args.apply else "\n✓ seeds written.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
