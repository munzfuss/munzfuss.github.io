#!/usr/bin/env python3
"""Drop seed catalogue values the danskmoent parser has RETRACTED.

WHY THIS IS NEEDED AT ALL
-------------------------
`catalog` is in the hede builder's DEEP_MERGE_FIELDS and its sub-fields are
list-capable, so a regeneration UNIONS the fresh emission with whatever the
seed already holds. It can add, never subtract. A parser fix that stops
emitting a wrong value therefore changes nothing on its own — verified twice
now, most recently after the 2026-08-07 off-strike-aside fix, where a re-seed
moved only the `generated_at` timestamp.

WHAT IT REMOVES, AND WHY THAT IS SAFE
-------------------------------------
Only a value that is ALL THREE of:

  1. present in the seed,
  2. absent from the CURRENT parser output for that page,
  3. present in the PREVIOUS parser output (read from the cache submodule's
     git HEAD).

(3) is the safeguard. It means the parser itself used to emit the value and
has now retracted it — so the removal follows a deliberate parser change and
cannot touch a curator's own addition, a value contributed by another source,
or anything the parser never claimed. A plain «sync the seed to the parser»
would delete all three of those.

Run it right after a `parse_hede.py --force` + `build_hede_denmark_seed.py`
pair, while the submodule still holds the pre-fix parse at HEAD.

Usage:  heal_hede_retracted_refs.py [--apply]
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from lib.paths import HARVEST_ROOT  # noqa: E402

from lib import yaml_io  # noqa: E402

CACHE = HARVEST_ROOT / "hede"
SEED = ROOT / "data" / "v2" / "seed" / "hede"

# parser ref name -> seed catalog field
FIELD = {"Schou": "schou", "Sieg": "sieg", "Fr": "fr", "Dav": "dav",
         "Galster": "galster", "Km": "km"}


def norm(v) -> list[str]:
    out: list[str] = []
    for x in (v if isinstance(v, list) else [v] if v else []):
        for part in str(x).replace(" og ", ",").split(","):
            part = part.strip()
            if part:
                out.append(part)
    return out


def retracted() -> dict[str, dict[str, set[str]]]:
    """{seed_id: {seed_field: {values the parser dropped}}}.

    Keyed by the SEED ids a page produces, resolved from the page's own
    `by_hede` keys (a multi-Hede page emits one seed per sub-number, so
    nc5h13 yields dk-hede-nc5h13 AND dk-hede-nc5h14). Prefix matching was
    tried first and is wrong: «c4h91».startswith(«c4h9») is true, so c4h91
    silently inherited c4h9's retraction. In a ledger that EXCUSES values,
    a loose key is a hole in the gate."""
    out: dict[str, dict[str, set[str]]] = {}
    for path in sorted(glob.glob(str(CACHE / "*.json"))):
        pid = os.path.basename(path)[:-5]
        if pid.startswith("_"):
            continue
        r = subprocess.run(["git", "show", f"HEAD:hede/{pid}.json"],
                           capture_output=True, text=True, cwd=CACHE.parent)
        if r.returncode:
            continue                      # new page, nothing to retract
        try:
            old = json.loads(r.stdout)
            new = json.load(open(path))
        except Exception:
            continue
        ob, nb = old.get("catalog_refs") or {}, new.get("catalog_refs") or {}
        drops: dict[str, set[str]] = {}
        for cat, field in FIELD.items():
            gone = set(norm(ob.get(cat))) - set(norm(nb.get(cat)))
            if gone:
                drops[field] = gone
        if not drops:
            continue
        vol = new.get("ruler_volume") or ""
        nums = list(((new.get("specs") or {}).get("by_hede") or {}).keys())
        if not nums:
            nums = new.get("hede_numbers_title") or new.get("hede_numbers_filename") or []
        seeds = [f"dk-hede-{vol}{n}" for n in nums] or [f"dk-hede-{pid}"]
        for sid in seeds:
            out.setdefault(sid, {}).update(drops)
    return out


LEDGER = ROOT / "data" / "v2" / "_retracted_refs.yml"

_LEDGER_HEADER = """\
# Catalogue values the danskmoent parser RETRACTED, and the heal then removed
# from the seeds.
#
# Written by scripts/maintenance/heal_hede_retracted_refs.py; read by
# scripts/maintenance/verify_reflow.py.
#
# WHY IT EXISTS. `catalog` is deep-merged and its sub-fields are list-capable,
# so the seed layer ACCUMULATES: a parser fix that stops emitting a wrong value
# cannot remove it, only a heal can. But a heal makes the register shrink, and
# a shrinking register is exactly what verify_reflow is built to block — three
# separate times in one day (KM in the finals, the sibling-Schou heal, then
# this one) a correct, verified cleanup was stopped by the gate with no way to
# tell it apart from real loss.
#
# This file is that record, and it is the same shape as data/v2/exclusions/:
# a deliberate removal, written down, so the gate can distinguish it from data
# falling on the floor. Without it the only way through is --no-verify, and a
# gate routinely bypassed protects nothing.
#
# An entry excuses ONE value of ONE register on the coins that carry the named
# seed. It excuses nothing else — a field emptied elsewhere, a citation
# dropped, a coin gone, all still block.
"""


def _write_ledger(ledger: list) -> None:
    from datetime import datetime, timezone
    seen, entries = set(), []
    for cid, field, gone in ledger:
        key = (cid, field)
        if key in seen:
            continue
        seen.add(key)
        entries.append({"seed": cid, "field": field, "dropped": gone})
    entries.sort(key=lambda e: (e["seed"], e["field"]))
    payload = {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "reason": ("danskmoent off-strike asides: an aside cites the number of a "
                   "coin struck from the same dies, which the parser used to "
                   "harvest onto the mother. Fixed in parse_hede.py "
                   "(_mask_afslag_spans); these are the values it retracted."),
        "retractions": entries,
    }
    LEDGER.write_text(_LEDGER_HEADER + yaml_io.dump_v2_canonical(payload))
    print(f"\n✓ ledger → {LEDGER.relative_to(ROOT)} ({len(entries)} retractions)")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    drops = retracted()
    if not drops:
        print("nothing retracted — parser output matches the previous parse.")
        return 0

    healed, ledger = [], []
    for seed_path in sorted(glob.glob(str(SEED / "*.yml"))):
        ctx, doc = yaml_io.load(seed_path)     # round-trip: keep the file's own
        changed = False                         # formatting, incl. §CN errata
        for coin in doc.get("coins") or []:
            cid = coin.get("id") or ""
            if not cid.startswith("dk-hede-"):
                continue
            cand = drops.get(cid)
            if not cand:
                continue
            cat = coin.get("catalog") or {}
            for field, gone in cand.items():
                # The LEDGER records what the parser retracted for this seed,
                # whether or not the seed still holds it. Keying it on «what
                # this run changed» would make it empty on a re-run — and the
                # gate needs the record to survive the heal, not to describe it.
                ledger.append((cid, field, sorted(gone)))
                have = norm(cat.get(field))
                keep = [v for v in have if v not in gone]
                if len(keep) == len(have):
                    continue
                healed.append((cid, field, have, keep,
                               sorted(set(have) - set(keep))))
                if keep:
                    cat[field] = keep[0] if len(keep) == 1 else keep
                else:
                    cat.pop(field, None)
                changed = True
        if changed and args.apply:
            yaml_io.save(ctx, seed_path, doc)

    if args.apply and ledger:
        _write_ledger(ledger)

    print(f"pages with retracted refs: {len(drops)}")
    print(f"seed fields healed: {len(healed)}\n")
    for cid, field, before, after, gone in healed:
        print(f"  {cid:24} {field:7} {before} → {after or '(dropped)'}   "
              f"(parser retracted {gone})")
    print("\n--- DRY RUN — nothing written. Re-run with --apply. ---"
          if not args.apply else "\n✓ seeds written.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
