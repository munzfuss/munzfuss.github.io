#!/usr/bin/env python3
"""READ-ONLY: which values of each final exist only because the final carried
them, and which member values the self-union suppresses.

For every final, runs absorb's enrichment twice (`lib/final_derivation.py`):
as absorb does (`[final] + classes`) and from a skeleton (identity,
fuss / phase / kind, `_curation_holds` + held values) plus the classes.

    own       only the final supplies it — candidates (stage 2 sorts
              them into legitimate own data and stale leftovers)
    relabel   same url / reading value, the final keeps an older label
    diverged  single-valued field: the final froze a value the members no
              longer give
    hidden    a member value the self-run does not show

    .venv/bin/python scripts/maintenance/audit_final_only.py
    .venv/bin/python scripts/maintenance/audit_final_only.py --entity danish_norway --json out.json

Plan: docs/plans/rebuild_final_from_members.md, stage 1.
"""
from __future__ import annotations

import argparse
import contextlib
import io
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import yaml  # noqa: E402

from lib import final_derivation as fd  # noqa: E402

_L = getattr(yaml, "CSafeLoader", yaml.SafeLoader)
V2 = ROOT / "data" / "v2"


def _coins(p: Path) -> list[dict]:
    if not p.exists():
        return []
    return [c for c in (yaml.load(p.read_text(), Loader=_L) or {}).get("coins") or []
            if isinstance(c, dict) and c.get("id")]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--entity")
    ap.add_argument("--json")
    ap.add_argument("--examples", type=int, default=3)
    a = ap.parse_args()

    with contextlib.redirect_stdout(io.StringIO()):
        from maintenance import absorb_seeds_into_final_v2 as ab

    tot: Counter = Counter()      # (field, origin, category) -> values
    fin: Counter = Counter()      # (field, origin, category) -> finals
    report = []
    n = 0
    for fp in sorted((V2 / "final").glob("*.yml")):
        ent = fp.stem
        if a.entity and ent != a.entity:
            continue
        unified = {u["id"]: u for u in _coins(V2 / "seed_unified" / f"{ent}.yml")}
        ab._LIVE_UNIFIED.clear()
        ab._LIVE_UNIFIED.update(unified)
        for fc in _coins(fp):
            n += 1
            classes = [unified[m] for m in fc.get("composed_of") or [] if m in unified]
            with contextlib.redirect_stdout(io.StringIO()):
                A, B = fd.derive_pair(ab, fc, classes, ent)
            d = fd.diff(A, B)
            if not d:
                continue
            org = fc.get("origin") or "?"
            row = {"final": fc["id"], "entity": ent, "label": fc.get("label"),
                   "origin": org, "classes": len(classes), "fields": {}}
            for f, (o, g) in d.items():
                cl = fd.classify(f, o, g)
                for cat, vals in cl.items():
                    if vals:
                        tot[(f, org, cat)] += len(vals)
                        fin[(f, org, cat)] += 1
                row["fields"][f] = {k: [list(map(str, v)) if isinstance(v, tuple)
                                        and k in ("relabel", "diverged") else str(v)
                                        for v in vals] for k, vals in cl.items() if vals}
            report.append(row)

    print(f"finals scanned: {n}   finals with any difference: {len(report)}")
    for cat in ("own", "relabel", "diverged", "hidden"):
        rows = sorted((k, v) for k, v in tot.items() if k[2] == cat)
        if not rows:
            continue
        print(f"\n== {cat}")
        print(f"   {'field':26} {'origin':10} {'values':>7} {'finals':>7}")
        for (f, org, _), k in rows:
            print(f"   {f:26} {org:10} {k:7} {fin[(f, org, cat)]:7}")
        ex = [r for r in report if any(cat in v for v in r["fields"].values())]
        for r in ex[:a.examples]:
            for f, v in r["fields"].items():
                if cat in v:
                    print(f"     e.g. {r['final']} [{r['entity']}] {f}: {v[cat][:2]}")
                    break
    if a.json:
        Path(a.json).write_text(json.dumps(report, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
