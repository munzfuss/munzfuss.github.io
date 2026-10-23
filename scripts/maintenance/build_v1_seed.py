#!/usr/bin/env python3
"""DRY RUN (stage D1 prototype): the V1 corpus as a seed source.

A V1 foundation (`origin: foundation`, 687 finals) holds data no class
carries — the V1 curator's scalars, citations, catalogue numbers, readings,
years — and a final rebuilt from its members loses them. This writes, per
foundation, ONE seed entry `v1-<foundation id>` carrying exactly the values
the --no-self-union rebuild removed and stage C did NOT mark stale (buckets
L*, R*, D-foundation and FLAG; never S*, never H-stale-v1-twin), with the
foundation's descriptive scalars, so the merger can hold them in the
foundation's class and the rebuild keeps them.

Output goes to the directory given, NOT to data/v2/seed (the curator decides
D1 first — docs/plans/rebuild_final_from_members.md). Member `merge_decisions`
rows are printed as a draft too.

    .venv/bin/python scripts/maintenance/build_v1_seed.py B_classified.json OUT_DIR [--base HEAD]
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import yaml  # noqa: E402

from lib.final_derivation import items  # noqa: E402

_L = getattr(yaml, "CSafeLoader", yaml.SafeLoader)
V2 = ROOT / "data" / "v2"

SCALARS = ("nominal", "ruler", "mintmaster", "issuing_entity", "fraction",
           "year_is_reign_span", "metal", "mint", "inscription_obv", "inscription_rev",
           "year_first", "year_last", "year_label", "year_ranges", "year_verified",
           "verification_note")
LISTS = ("sources", "weight_rough_g", "fineness", "diameter_mm")
FLAGS = ("metal_verified", "fineness_verified", "weight_rough_verified",
         "diameter_mm_verified", "mint_verified", "verified", "ruler_verified")
KEEP_BUCKETS = ("L", "R", "D-foundation", "FLAG")


def _git(args):
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True).stdout


def _coins(text):
    return {c["id"]: c for c in (yaml.load(text, Loader=_L) or {}).get("coins") or []
            if isinstance(c, dict) and c.get("id")}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("classified")
    ap.add_argument("out_dir")
    ap.add_argument("--base", default="HEAD")
    a = ap.parse_args()
    rows = json.load(open(a.classified))
    out_dir = Path(a.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    keep: dict[tuple, set] = defaultdict(set)      # (entity, final) -> fields with kept removed values
    keep_vals: dict[tuple, set] = defaultdict(set)  # (entity, final, field) -> kept value strings
    dropped: Counter = Counter()
    for r in rows:
        if r.get("origin") != "foundation" or r.get("direction") != "removed":
            continue
        b = r.get("bucket", "")
        if b.startswith(KEEP_BUCKETS):
            keep[(r["entity"], r["final"])].add(r["field"])
            keep_vals[(r["entity"], r["final"], r["field"])].add(r["value"])
        else:
            dropped[(r["field"], b)] += 1

    def _only_kept(fc, ent, fid, f):
        """The field's value reduced to the items stage C kept (a stale
        citation or catalogue number in the same list stays out)."""
        kept = keep_vals.get((ent, fid, f), set())
        v = fc.get(f)
        if f == "catalog" and isinstance(v, dict):
            out = {}
            for reg, rv in v.items():
                if isinstance(rv, dict):
                    sub = {vol: x for vol, x in rv.items() if str(("%s" % reg, f"{vol}:{x}")) in kept}
                    if sub:
                        out[reg] = sub
                    continue
                vals = rv if isinstance(rv, list) else [rv]
                k = [x for x in vals if str((reg, str(x))) in kept]
                if k:
                    out[reg] = k if isinstance(rv, list) else k[0]
            return out or None
        if isinstance(v, list):
            k = [x for x in v if any(str(i) in kept for i in items(f, [x]))]
            return k or None
        return v

    stats: Counter = Counter()
    decisions: dict[str, list] = defaultdict(list)
    for ent in sorted({e for e, _ in keep}):
        base = _coins(_git(["show", f"{a.base}:data/v2/final/{ent}.yml"]))
        uni = _coins(_git(["show", f"{a.base}:data/v2/seed_unified/{ent}.yml"]))
        entries = []
        for (e, fid), fields in sorted(keep.items()):
            if e != ent:
                continue
            fc = base.get(fid)
            if not fc:
                continue
            seed = {"id": f"v1-{fid}", "issuing_entity": fc.get("issuing_entity") or ent}
            # the foundation's descriptive scalars always travel (they are the
            # V1 curator's choice — the skeleton keeps them too)
            for f in SCALARS:
                if f in fc and (f in fields or f in ("nominal", "ruler", "mintmaster", "fraction",
                                                       "year_is_reign_span", "issuing_entity")):
                    seed[f] = fc[f]
            for f in LISTS:
                if f in fields and f in fc:
                    v = _only_kept(fc, ent, fid, f)
                    if v:
                        seed[f] = v
            if "catalog" in fields and isinstance(fc.get("catalog"), dict):
                v = _only_kept(fc, ent, fid, "catalog")
                if v:
                    seed["catalog"] = v
            for f in FLAGS:
                if f in fields and f in fc:
                    seed[f] = fc[f]
            seed["phase"] = "v1"
            seed["fuss"] = "seed_unsorted"
            seed["_origin"] = f"V1 foundation {fid} (data/v2/final at {a.base}); fields the rebuild removed: {sorted(fields)}"
            entries.append(seed)
            stats["entries"] += 1
            for f in fields:
                stats[f"field:{f}"] += 1
            members = [f"v1-{fid}"]
            for cid in fc.get("composed_of") or []:
                u = uni.get(cid)
                if u:
                    members += list(u.get("composed_of") or [])[:1]
            decisions[ent].append({"members": members,
                                   "reason": f"V1 foundation {fid} joins its own class (stage D1)"})
        if entries:
            (out_dir / f"{ent}.yml").write_text(
                yaml.safe_dump({"id": ent, "source": "v1", "coins": entries},
                               sort_keys=False, allow_unicode=True, width=120))
            (out_dir / f"merge_decisions_{ent}.yml").write_text(
                yaml.safe_dump({"merges": decisions[ent]}, sort_keys=False, allow_unicode=True, width=120))
    print("V1 seed entries:", stats["entries"], "in", len(decisions), "entities ->", out_dir)
    for k, n in sorted(stats.items()):
        if k.startswith("field:"):
            print(f"   {k[6:]:24} {n:5} foundations")
    print("\nfoundation values NOT carried (stale per stage C):")
    for (f, b), n in sorted(dropped.items()):
        print(f"   {f:24} {b:22} {n:5}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
