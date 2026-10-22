#!/usr/bin/env python3
"""READ-ONLY: every value that differs between the finals at HEAD and the
finals on disk, one row per (final, field, value, direction), keyed to the
final's seeds — the candidate list of docs/plans/rebuild_final_from_members.md
stage B, and the per-value gate of every later stage.

    .venv/bin/python scripts/maintenance/final_diff_candidates.py --json out.json
    .venv/bin/python scripts/maintenance/final_diff_candidates.py --entity danish_norway --examples 5

`verify_reflow` is the hook's judge (gain / loss / moved); this tool keeps
EVERY change, including scalar changes and `note`, which that judge lets
through, so the diff of a run can be read value by value and compared with
the list the curator approved.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import yaml  # noqa: E402

from lib.final_derivation import items  # noqa: E402

_L = getattr(yaml, "CSafeLoader", yaml.SafeLoader)
V2 = ROOT / "data" / "v2"

FIELDS = (
    "sources", "weight_rough_g", "fineness", "diameter_mm", "catalog", "mint",
    "year_ranges", "year_first", "year_last", "year_label", "year_verified",
    "nominal", "ruler", "ruler_verified", "mintmaster", "issuing_entity",
    "fraction", "metal", "metal_verified", "fineness_verified",
    "weight_rough_verified", "diameter_mm_verified", "mint_verified",
    "verified", "note", "verification_note", "inscription_obv",
    "inscription_rev", "fuss", "phase", "kind", "composed_of",
)


def _coins(text: str) -> dict[str, dict]:
    doc = yaml.load(text, Loader=_L) or {}
    return {c["id"]: c for c in doc.get("coins") or [] if isinstance(c, dict) and c.get("id")}


def _git_show(rel: str, rev: str) -> str:
    r = subprocess.run(["git", "show", f"{rev}:{rel}"], cwd=ROOT, capture_output=True, text=True)
    return r.stdout if r.returncode == 0 else ""


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--entity")
    ap.add_argument("--base", default="HEAD", help="git revision of the baseline finals")
    ap.add_argument("--json")
    ap.add_argument("--examples", type=int, default=3)
    a = ap.parse_args()

    rows = []
    tot: Counter = Counter()
    fin: Counter = Counter()
    coins_gone = coins_new = 0
    for fp in sorted((V2 / "final").glob("*.yml")):
        ent = fp.stem
        if a.entity and ent != a.entity:
            continue
        base = _coins(_git_show(f"data/v2/final/{ent}.yml", a.base))
        cur = _coins(fp.read_text())
        base_uni = _coins(_git_show(f"data/v2/seed_unified/{ent}.yml", a.base))

        def seeds_of(c):
            out = []
            for m in c.get("composed_of") or []:
                u = base_uni.get(m)
                out += list(u.get("composed_of") or []) if u else [m]
            return sorted(set(out))

        for cid in sorted(set(base) | set(cur)):
            b, c = base.get(cid), cur.get(cid)
            if b is None:
                coins_new += 1
                rows.append({"final": cid, "entity": ent, "field": "*coin*", "direction": "new",
                             "value": None, "origin": c.get("origin"), "seeds": seeds_of(c)})
                continue
            if c is None:
                coins_gone += 1
                rows.append({"final": cid, "entity": ent, "field": "*coin*", "direction": "gone",
                             "value": None, "origin": b.get("origin"), "seeds": seeds_of(b)})
                continue
            org = b.get("origin") or "?"
            seeds = None
            for f in FIELDS:
                ib, ic = items(f, b.get(f)), items(f, c.get(f))
                if ib == ic:
                    continue
                if seeds is None:
                    seeds = seeds_of(b)
                for v in sorted(ib - ic, key=str):
                    rows.append({"final": cid, "entity": ent, "origin": org, "field": f,
                                 "direction": "removed", "value": str(v), "seeds": seeds})
                    tot[(f, org, "removed")] += 1
                for v in sorted(ic - ib, key=str):
                    rows.append({"final": cid, "entity": ent, "origin": org, "field": f,
                                 "direction": "added", "value": str(v), "seeds": seeds})
                    tot[(f, org, "added")] += 1
                fin[(f, org)] += 1

    print(f"coins gone: {coins_gone}   coins new: {coins_new}   finals changed: "
          f"{len({(r['entity'], r['final']) for r in rows if r['field'] != '*coin*'})}")
    print(f"\n{'field':24} {'origin':10} {'removed':>8} {'added':>8} {'finals':>7}")
    for (f, org) in sorted(fin):
        print(f"{f:24} {org:10} {tot[(f, org, 'removed')]:8} {tot[(f, org, 'added')]:8} {fin[(f, org)]:7}")
    if a.examples:
        print()
        seen: Counter = Counter()
        for r in rows:
            k = (r["field"], r["origin"], r["direction"])
            if r["field"] == "*coin*" or seen[k] >= a.examples:
                continue
            seen[k] += 1
            print(f"  {r['field']}/{r['origin']}/{r['direction']}: {r['final']} [{r['entity']}] "
                  f"{r['value'][:110]}")
    if a.json:
        Path(a.json).write_text(json.dumps(rows, ensure_ascii=False, indent=0))
    return 0


if __name__ == "__main__":
    sys.exit(main())
