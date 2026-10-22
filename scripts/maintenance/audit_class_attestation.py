#!/usr/bin/env python3
"""READ-ONLY: final values that the final's own classes no longer attest.

Lists, per final, the `sources` and the readings (weight_rough_g / fineness /
diameter_mm) that no class of the final attests, grouped by cause — see
`scripts/lib/class_attestation.py`:

    moved     attested by a class of ANOTHER final (stale leftover of a seed
              that left; absorb drops these)
    twin      as moved, but this final is on a page and every such final
              is in seed_unsorted — kept; usually one coin split in two
              finals, a merge candidate
    orphan    attested only by classes that reach no final (kept; curator)
    unseeded  attested by no class (curator / fold / V1 citation; kept)

    .venv/bin/python scripts/maintenance/audit_class_attestation.py
    .venv/bin/python scripts/maintenance/audit_class_attestation.py --entity danish_norway --examples 5
    .venv/bin/python scripts/maintenance/audit_class_attestation.py --json out.json

Also lists, reported only (absorb drops neither): list-form `mint` values
and `catalog` values (register, value) that no class of the final carries —
the same stale-union mechanism (2026-10-22: «Ernst 1940# 3-13» stayed on the
Galster 158/160/161 finals after an erratum removed it from their seeds).
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import yaml  # noqa: E402

from lib.class_attestation import READING_FIELDS, AttestationIndex, source_key  # noqa: E402

_L = getattr(yaml, "CSafeLoader", yaml.SafeLoader)
V2 = ROOT / "data" / "v2"


def _mints(c) -> set[str]:
    m = c.get("mint")
    return {str(x) for x in (m if isinstance(m, list) else [m]) if x}


def _cat(c) -> set[tuple[str, str]]:
    out = set()
    for reg, v in (c.get("catalog") or {}).items():
        vals = list(v.values()) if isinstance(v, dict) else (v if isinstance(v, list) else [v])
        out |= {(reg, str(x).strip()) for x in vals if x not in (None, "") and not isinstance(x, dict)}
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--entity")
    ap.add_argument("--examples", type=int, default=3)
    ap.add_argument("--json")
    a = ap.parse_args()

    unified, finals = [], []
    for p in sorted((V2 / "seed_unified").glob("*.yml")):
        unified += [c for c in (yaml.load(p.read_text(), Loader=_L) or {}).get("coins") or []
                    if isinstance(c, dict)]
    ent_of: dict[str, str] = {}
    for p in sorted((V2 / "final").glob("*.yml")):
        for c in (yaml.load(p.read_text(), Loader=_L) or {}).get("coins") or []:
            if isinstance(c, dict) and c.get("id"):
                finals.append(c)
                ent_of[c["id"]] = p.stem
    idx = AttestationIndex.build(unified, finals)
    cls_mint = {u["id"]: _mints(u) for u in unified if u.get("id")}
    cls_cat = {u["id"]: _cat(u) for u in unified if u.get("id")}

    report = []
    totals: Counter = Counter()
    finals_hit: Counter = Counter()
    for fc in finals:
        fid = fc["id"]
        if a.entity and ent_of[fid] != a.entity:
            continue
        row = {"final": fid, "entity": ent_of[fid], "label": fc.get("label"),
               "origin": fc.get("origin"), "fields": {}}
        for fld in ("sources",) + READING_FIELDS:
            r = idx.classify(fc, fld)
            if any(r.values()):
                row["fields"][fld] = r
                for cause, vals in r.items():
                    if vals:
                        totals[(fld, cause)] += len(vals)
                        finals_hit[(fld, cause)] += 1
        own = idx.final_classes.get(fid, set())
        if own and isinstance(fc.get("mint"), list):
            cm = set().union(*(cls_mint.get(c, set()) for c in own))
            extra = sorted(_mints(fc) - cm)
            if extra and cm:
                row["fields"]["mint"] = {"unattested": extra, "class": sorted(cm)}
                totals[("mint", "unattested")] += len(extra)
                finals_hit[("mint", "unattested")] += 1
        held = fc.get("_curation_holds")
        held = set(held.keys() if isinstance(held, dict) else (held or []))
        if own and "catalog" not in held:
            cc = set().union(*(cls_cat.get(c, set()) for c in own))
            extra = sorted(_cat(fc) - cc)
            if extra and cc:
                row["fields"]["catalog"] = {"unattested": [f"{r}={v}" for r, v in extra]}
                totals[("catalog", "unattested")] += len(extra)
                finals_hit[("catalog", "unattested")] += 1
        if row["fields"]:
            report.append(row)

    print(f"{'field':16} {'cause':11} {'values':>7} {'finals':>7}")
    for (fld, cause), n in sorted(totals.items()):
        print(f"{fld:16} {cause:11} {n:7} {finals_hit[(fld, cause)]:7}")

    # examples: biggest offenders per (field, cause)
    for fld, cause in sorted(totals):
        rows = [r for r in report if r["fields"].get(fld, {}).get(cause)]
        if fld in ("mint", "catalog"):
            print(f"\n== {fld} / {cause}: top finals")
            for r in rows[:a.examples]:
                print(f"  {r['final']} [{r['entity']}] {r['label']}: {r['fields'][fld][cause]}")
            continue
        rows.sort(key=lambda r: -len(r["fields"][fld][cause]))
        print(f"\n== {fld} / {cause}: top finals")
        for r in rows[:a.examples]:
            vals = r["fields"][fld][cause]
            print(f"  {r['final']} [{r['entity']}] {r['label']} ({r['origin']}): {len(vals)}")
            for v in vals[:2]:
                if isinstance(v, tuple):
                    v, where = v
                    print(f"      {source_key(v) if fld == 'sources' else v}  → {where}")
                else:
                    print(f"      {source_key(v) if fld == 'sources' else v}")
    if a.json:
        Path(a.json).write_text(json.dumps(report, ensure_ascii=False, indent=1, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
