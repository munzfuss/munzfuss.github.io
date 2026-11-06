#!/usr/bin/env python3
"""Guard: a final may not GAIN a value that no class of it carries.

The pipeline builds every final from its members (`seed_unified` classes)
and the curator's decisions. A value written onto a final by hand or by a
one-off pass — the June 2026 ruler re-spellings, the September note
backfills — is invisible to every re-flow and silently reverts when the
final is rebuilt (docs/plans/rebuild_final_from_members.md, stage F). This
check reads the finals as STAGED (or on disk) against the seed_unified of
the same state and lists every value that is new since HEAD and attested by
no class of the final, outside the fields a final legitimately owns.

    .venv/bin/python scripts/maintenance/audit_final_only_edits.py            # working tree vs HEAD
    .venv/bin/python scripts/maintenance/audit_final_only_edits.py --staged   # index vs HEAD (pre-commit)

Exit 1 when such a value exists. Fields a final owns (not checked): fuss,
phase, kind, note, _curation_holds and the held fields, bookkeeping, and the
descriptive scalars of a V1 foundation (`origin: foundation`).
"""
from __future__ import annotations

import argparse
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

OWN_ALWAYS = frozenset({
    "id", "label", "origin", "composed_of", "legacy_id", "class_id", "fuss", "phase",
    "kind", "_curation_holds", "note", "_weights_thinned", "_entity_routing_hint",
    "_migration_note", "_migration_dup_origin_id", "v1_home_location", "promoted_to",
    "mintmasters", "verification_note", "fraction", "catalog_alts", "catalog_unverified",
    "ruler_alts", "mint_alts", "year_alts", "nominal_alts", "weight_range_g", "hede_muentzfuss_yield",
})
FOUNDATION_OWN = frozenset({"nominal", "ruler", "mintmaster", "issuing_entity",
                            "year_is_reign_span", "inscription_obv", "inscription_rev"})
CHECKED = ("sources", "weight_rough_g", "fineness", "diameter_mm", "catalog", "mint",
           "year_ranges", "nominal", "ruler", "mintmaster", "metal", "issuing_entity",
           "inscription_obv", "inscription_rev")


def _git(args):
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True).stdout


def _coins(text):
    return {c["id"]: c for c in (yaml.load(text, Loader=_L) or {}).get("coins") or []
            if isinstance(c, dict) and c.get("id")}


def _text(rel: str, staged: bool) -> str:
    if staged:
        return _git(["show", f":{rel}"])
    p = ROOT / rel
    return p.read_text() if p.exists() else ""


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--staged", action="store_true")
    ap.add_argument("--entity")
    ap.add_argument("--examples", type=int, default=5)
    a = ap.parse_args()
    if a.staged:
        changed = [f for f in _git(["diff", "--cached", "--name-only", "--", "data/v2/final"]).split() if f.endswith(".yml")]
    else:
        changed = [f for f in _git(["diff", "--name-only", "--", "data/v2/final"]).split() if f.endswith(".yml")]
    if a.entity:
        changed = [f for f in changed if Path(f).stem == a.entity]
    if not changed:
        print("no final changed")
        return 0
    bad: Counter = Counter()
    ex = []
    for rel in sorted(changed):
        ent = Path(rel).stem
        head = _coins(_git(["show", f"HEAD:{rel}"]))
        cur = _coins(_text(rel, a.staged))
        uni = _coins(_text(f"data/v2/seed_unified/{ent}.yml", a.staged))
        for fid, c in cur.items():
            h = head.get(fid, {})
            holds = c.get("_curation_holds")
            held = set(holds.keys() if isinstance(holds, dict) else (holds or []))
            classes = [uni[m] for m in c.get("composed_of") or [] if m in uni]
            for f in CHECKED:
                if f in OWN_ALWAYS or f in held or (c.get("origin") != "promoted" and f in FOUNDATION_OWN):
                    continue
                new = items(f, c.get(f)) - items(f, h.get(f))
                if not new:
                    continue
                attested = set()
                for u in classes:
                    attested |= items(f, u.get(f))
                for v in new - attested:
                    bad[(ent, f)] += 1
                    if len(ex) < a.examples:
                        ex.append((ent, fid, f, str(v)[:100]))
    if not bad:
        print(f"✓ {len(changed)} final file(s): every new value is attested by a class of its final")
        return 0
    print("✗ values new on a final that NO class of it carries (final-only edit — put it in a seed, a decision or a hold):")
    for (ent, f), n in sorted(bad.items()):
        print(f"   {ent:34} {f:16} {n}")
    for ent, fid, f, v in ex:
        print(f"     e.g. {fid} [{ent}] {f}: {v}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
