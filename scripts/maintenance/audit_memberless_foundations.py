#!/usr/bin/env python3
"""READ-ONLY: the V1 foundations with no live class — does any harvested
class look like the same coin (a shared type-level catalogue number, per the
merger's own `_shares_type_level_catalog`), and does a curator decision
already speak to the pair?

The curator's expectation (2026-10-23): the harvests made after V1 cover the
V1 data in full, so a V1 foundation should always have a class to be built
from. A foundation with no class and no candidate is the counter-example
(a V1-only coin); one with a candidate is a merge the pipeline never made
(absorb matches finals by `match_pair`, which also needs nominal / metal /
ruler to agree).

    .venv/bin/python scripts/maintenance/audit_memberless_foundations.py [--json out.json]
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

_L = getattr(yaml, "CSafeLoader", yaml.SafeLoader)
V2 = ROOT / "data" / "v2"


def _coins(p: Path, base: str | None = None) -> list[dict]:
    """Coins of a data file — at revision `base` when given (the working tree
    may hold a rebuild that already stripped the foundations)."""
    if base:
        import subprocess
        text = subprocess.run(["git", "show", f"{base}:{p.relative_to(ROOT)}"], cwd=ROOT,
                              capture_output=True, text=True).stdout
    else:
        text = p.read_text() if p.exists() else ""
    return [c for c in (yaml.load(text, Loader=_L) or {}).get("coins") or []
            if isinstance(c, dict) and c.get("id")]


def _seed_twin(fid: str, seed_ids: set) -> str | None:
    """The seed a V1 foundation id was bootstrapped from, when the id is that
    seed's id under a V1 prefix (`hs-ikmk-123` → `ikmk-123`; `dk-tid-7` is a
    ucoin id as is)."""
    if fid in seed_ids:
        return fid
    for pre in ("hs-", "dk-", "hb-", "lu-"):
        if fid.startswith(pre) and fid[len(pre):] in seed_ids:
            return fid[len(pre):]
    return None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--json")
    ap.add_argument("--base", default="HEAD")
    a = ap.parse_args()
    with contextlib.redirect_stdout(io.StringIO()):
        from maintenance import merge_seeds_cross_source as mg
    classes: list[tuple[str, dict]] = []
    class_final: dict[str, str] = {}
    for p in sorted((V2 / "seed_unified").glob("*.yml")):
        for u in _coins(p, a.base):
            classes.append((p.stem, u))
    seed_class = {s: u["id"] for _, u in classes for s in (u.get("composed_of") or [])}
    memberless: list[tuple[str, dict]] = []
    for p in sorted((V2 / "final").glob("*.yml")):
        for c in _coins(p, a.base):
            for cid in c.get("composed_of") or []:
                class_final.setdefault(cid, c["id"])
            if c.get("origin") == "foundation" and not c.get("composed_of"):
                memberless.append((p.stem, c))
    refs_cache = {}
    rows = []
    kinds: Counter = Counter()
    for ent, fc in memberless:
        fr = mg._catalog_refs(fc, ent)
        cands = []
        for cent, u in classes:
            key = u["id"]
            ur = refs_cache.get(key)
            if ur is None:
                ur = refs_cache[key] = mg._catalog_refs(u, cent)
            if fr and ur and mg._shares_type_level_catalog(fr, ur):
                same_metal = (not fc.get("metal") or not u.get("metal") or fc.get("metal") == u.get("metal"))
                cands.append({"class": key, "entity": cent, "label": u.get("label"),
                              "final": class_final.get(key), "nominal": u.get("nominal"),
                              "ruler": u.get("ruler"), "years": f"{u.get('year_first')}-{u.get('year_last')}",
                              "same_metal": same_metal, "same_entity": cent == ent})
        twin = _seed_twin(fc["id"], set(seed_class))
        if twin:
            tc = seed_class[twin]
            cands.insert(0, {"class": tc, "entity": "?", "label": "(seed twin)", "final": class_final.get(tc),
                             "nominal": None, "ruler": None, "years": "", "same_metal": True, "same_entity": True,
                             "seed_twin": twin})
        kind = ("V1 twin of a harvested seed" if twin else
                "no catalogue on the foundation" if not fr else
                ("no candidate" if not cands else
                 ("candidate, same entity" if any(x["same_entity"] for x in cands) else "candidate elsewhere")))
        kinds[kind] += 1
        rows.append({"final": fc["id"], "entity": ent, "nominal": fc.get("nominal"), "ruler": fc.get("ruler"),
                     "years": f"{fc.get('year_first')}-{fc.get('year_last')}", "metal": fc.get("metal"),
                     "refs": fr, "kind": kind, "candidates": cands[:5]})
    print(f"memberless foundations: {len(memberless)}")
    for k, n in kinds.most_common():
        print(f"   {n:4}  {k}")
    print()
    for r in rows:
        if r["candidates"]:
            c = r["candidates"][0]
            print(f"  {r['final']:34} [{r['entity']}] {str(r['nominal'])[:22]:22} {str(r['ruler'])[:16]:16} {r['years']:10} "
                  f"→ {c['class']} «{c['label']}» [{c['entity']}] {str(c['nominal'])[:22]} {c['years']} "
                  f"{'metal≠' if not c['same_metal'] else ''} +{len(r['candidates']) - 1}")
    print("\nno candidate:")
    for r in rows:
        if not r["candidates"]:
            print(f"  {r['final']:34} [{r['entity']}] {str(r['nominal'])[:24]:24} {str(r['ruler'])[:18]:18} {r['years']:10} refs={sorted(r['refs'].items())[:3]}")
    if a.json:
        Path(a.json).write_text(json.dumps(rows, ensure_ascii=False, indent=1, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
