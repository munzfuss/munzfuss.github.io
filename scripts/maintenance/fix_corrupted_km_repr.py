#!/usr/bin/env python3
"""Repair `catalog.km` lists corrupted by the 2026-05-31 «44-false-positive
bug», where a km value that was a proper KMRef-list (`['63', KMRef('103','DK')]`)
got `str()`'d WHOLE into a single string element — yielding garbage like

    km:
    - "['63', {'value': '103', 'register': 'DK'}]"   # str-repr of the real list
    - '63'                                            # plus duplicated bare token

The render then leaks the str-repr verbatim («KM-SH# 63, ['63', {'value':
'103', 'register': 'DK'}]»). The bug that PRODUCED this is long fixed
(`_km_bases` no longer str()'s a list whole; the merger's `_merge_km_field`
emits clean register-keyed output), but the corrupted entries baked into
`data/v2/final/*.yml` were never cleaned up — only ~6 coins, all carrying a
cross-volume KM (one number per Krause register).

REPAIR — faithful restoration of the pre-corruption value (no register
re-adjudication):

  1. EXPLODE every list element that is a string whose `ast.literal_eval`
     yields a list (the str-repr), replacing it with its members.
  2. FLATTEN + DEDUP exactly: bare strings keyed by value; KMRef dicts keyed
     by (value, register).
  3. DROP a KMRef dict that is redundant with a bare twin — i.e. its register
     (lower-cased) equals the entity's DEFAULT km register AND a bare string of
     the same value already exists (so the bare token already renders to the
     same «KM-<default>#» span). This removes the only redundancy the explode
     introduces; it never changes a register assignment.
  4. ORDER: bare strings first (first-seen order), then KMRef dicts.

A KMRef whose register differs from the entity default is preserved verbatim
(e.g. royal_holstein default `sh`, KMRef `{value:'103', register:'DK'}` stays —
renders «KM-DK# 103»). Whether a bare token «should» have carried a non-default
register is a SEPARATE data-quality question and is deliberately NOT touched.

Final is re-dumped with absorb's serializer (yaml.dump, sort_keys=False,
allow_unicode=True, default_flow_style=False, width=120) so the diff is the km
repairs only.

Usage:
    python scripts/maintenance/fix_corrupted_km_repr.py            # dry-run
    python scripts/maintenance/fix_corrupted_km_repr.py --apply
"""
from __future__ import annotations

import argparse
import ast
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "maintenance"))

# Single source of truth for the entity → default Krause register map.
from merge_seeds_cross_source import _ENTITY_TO_KM_REGISTER  # noqa: E402
# Form-#2 str-repr detection now lives in the build-path hygiene module
# (normalise_catalog heals it on every absorb/merge); share the predicate so
# the one-shot repairer and the hygiene net never drift. See plan / §13.x.
from lib.catalog_codes import _is_str_repr_list  # noqa: E402

V2_FINAL = ROOT / "data" / "v2" / "final"


def _repair_km(km, default_register: str | None):
    """Return (repaired_km, changed:bool). `km` is a list that may contain a
    str-repr element. Non-corrupt input returns (km, False)."""
    if not isinstance(km, list) or not any(_is_str_repr_list(el) for el in km):
        return km, False

    # 1. explode + flatten
    flat: list = []
    for el in km:
        if _is_str_repr_list(el):
            flat.extend(ast.literal_eval(el))
        else:
            flat.append(el)

    # 2. dedup exactly; split into bare strings vs KMRef dicts
    bare: list[str] = []
    bare_seen: set[str] = set()
    refs: list[dict] = []
    ref_seen: set[tuple] = set()
    for v in flat:
        if isinstance(v, dict):
            key = (str(v.get("value")), str(v.get("register")))
            if key not in ref_seen:
                ref_seen.add(key)
                refs.append({"value": v.get("value"), "register": v.get("register")})
        else:
            s = str(v).strip()
            if s and s not in bare_seen:
                bare_seen.add(s)
                bare.append(s)

    # 3. drop a KMRef redundant with a bare twin under the entity default
    kept_refs = []
    for r in refs:
        reg = (r.get("register") or "").lower()
        if reg and reg == (default_register or "") and str(r.get("value")) in bare_seen:
            continue  # redundant — bare token already renders this span
        kept_refs.append(r)

    # 4. order: bare first, then KMRefs
    repaired = bare + kept_refs
    # collapse a single bare value back to scalar (V1-compat shape)
    if len(repaired) == 1 and isinstance(repaired[0], str):
        repaired = repaired[0]
    return repaired, True


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--apply", action="store_true", help="write changes (default: dry-run)")
    args = ap.parse_args()

    total = 0
    for path in sorted(V2_FINAL.glob("*.yml")):
        entity = path.stem
        default_reg = _ENTITY_TO_KM_REGISTER.get(entity)
        doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        changed = 0
        for coin in doc.get("coins") or []:
            if not isinstance(coin, dict):
                continue
            cat = coin.get("catalog") or {}
            km = cat.get("km")
            new_km, did = _repair_km(km, default_reg)
            if did:
                changed += 1
                total += 1
                print(f"{entity}  {coin.get('id')}  (default reg: {default_reg})")
                print(f"   OLD km = {km}")
                print(f"   NEW km = {new_km}")
                cat["km"] = new_km
        if changed and args.apply:
            out = yaml.dump(doc, sort_keys=False, allow_unicode=True,
                            default_flow_style=False, width=120)
            path.write_text(out, encoding="utf-8")

    print(f"\n{'APPLIED' if args.apply else 'DRY-RUN'}: {total} entr"
          f"{'y' if total == 1 else 'ies'} repaired"
          f"{' written' if args.apply else ' would change'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
