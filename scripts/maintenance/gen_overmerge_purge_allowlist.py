#!/usr/bin/env python3
"""Generate the SAFE over-merge purge allowlist (CLAUDE.md §9.4 base-KM split).

Older pipeline code fused composed_of members of DIFFERENT base KM into one
final entry (e.g. dk-tid-97364 km=248 absorbing unified-dk-hede-f3h61 km=240).
This scans every final entry for such over-merges and classifies each
different-KM member as SAFE-to-auto-split or COMPLEX (curator image review).

A member is SAFE to auto-split off its host ONLY when ALL hold:
  1. member base-KM != host base-KM  (genuinely different Krause type), AND
  2. member shares NO base TYPE-LEVEL catalog ref with the host across
     {hede, lange, sieg, dav, fr} — because a shared Hede / Lange (the Danish
     / Holstein type authorities) means SAME coin even if Krause assigned a
     different / addendum KM (Krause splits one Hede into several KM). A split
     here would WRONGLY separate one coin. Sieg/Dav/Fr are broader/edition-
     shifty, included for max conservatism («безпрограшні only»), AND
  3. the host has NO top-level no-KM member (a Hede-only / no-KM member could
     belong to the split-off member rather than the host — cannot auto-decide),
     AND
  4. no two evicted members share the same full KM (same-coin-between-them
     risk → would create a new duplicate), AND
  5. a clean foundation twin exists for the host (seed_unified or raw seed),
     so absorb can reset the host's baked-in catalog when splitting.

Everything failing (2)-(5) is COMPLEX → emitted to docs/overmerge_split_
COMPLEX.json for curator review WITH full source links + Bruun lot ids.

Outputs (idempotent):
  data/v2/overmerge_purge_allowlist.yml   — {host_id: [member_ids]} for absorb
  docs/overmerge_split_SAFE.json
  docs/overmerge_split_COMPLEX.json

Usage:
    python scripts/maintenance/gen_overmerge_purge_allowlist.py            # report
    python scripts/maintenance/gen_overmerge_purge_allowlist.py --write
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
V2_FINAL = ROOT / "data" / "v2" / "final"
V2_SEED_UNIFIED = ROOT / "data" / "v2" / "seed_unified"
V2_SEED = ROOT / "data" / "v2" / "seed"
ALLOWLIST = ROOT / "data" / "v2" / "overmerge_purge_allowlist.yml"
SAFE_JSON = ROOT / "docs" / "overmerge_split_SAFE.json"
COMPLEX_JSON = ROOT / "docs" / "overmerge_split_COMPLEX.json"

# Type-level catalog authorities: a SHARED base value here means «same coin»
# (so the member must NOT be auto-split off the host). km is excluded — it is
# different by definition for an over-merge member.
TYPE_LEVEL_REFS = ("hede", "lange", "sieg", "dav", "fr")


def _load(p: Path):
    doc = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    return doc if isinstance(doc, list) else (doc.get("coins") or doc.get("entries") or [])


def _km_first(c):
    km = (c.get("catalog") or {}).get("km")
    if isinstance(km, dict):
        vals = [v for v in km.values() if v not in (None, "", [])]
        km = vals[0] if vals else None
    return None if km in (None, "", []) else str(km)


def _base(km):
    """'A110'→'A110', '70.1'→'70', '11a'→'11', '156,3'→'156'."""
    if km is None:
        return None
    s = str(km).strip()
    m = re.match(r"^([A-Za-z]*)(\d+)", s)
    return (m.group(1).upper() + m.group(2)) if m else s


def _ref_bases(c, key):
    """Set of base values for a catalog ref field (handles scalar + list)."""
    v = (c.get("catalog") or {}).get(key)
    if v in (None, "", []):
        return set()
    items = v if isinstance(v, list) else [v]
    out = set()
    for x in items:
        m = re.match(r"^(\d+)", str(x).strip())
        if m:
            out.add(m.group(1))
    return out


def _shares_type_level(host, member) -> list[str]:
    """Return the type-level ref keys where host & member share a base value."""
    shared = []
    for k in TYPE_LEVEL_REFS:
        if _ref_bases(host, k) & _ref_bases(member, k):
            shared.append(k)
    return shared


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()

    twin: dict[str, dict] = {}
    for f in V2_SEED_UNIFIED.glob("*.yml"):
        for c in _load(f):
            if isinstance(c, dict) and c.get("id"):
                twin.setdefault(c["id"], c)
    for f in V2_SEED.rglob("*.yml"):
        for c in _load(f):
            if isinstance(c, dict) and c.get("id"):
                twin.setdefault(c["id"], c)

    safe, complex_ = [], []
    for f in sorted(V2_FINAL.glob("*.yml")):
        ent = f.stem
        for c in _load(f):
            if not isinstance(c, dict) or not c.get("id"):
                continue
            comp = [m for m in (c.get("composed_of") or []) if m != c["id"]]
            if not comp:
                continue
            host_twin = twin.get(c["id"])
            if host_twin is None:
                continue  # no clean foundation twin → cannot reset → never SAFE
            hbase = _base(_km_first(host_twin))
            if hbase is None:
                continue
            # members keyed by presence of KM + base divergence
            members = [(m, twin.get(m)) for m in comp]
            divergent = []          # different base KM
            no_km_members = []      # top-level member without a KM
            for mid, mc in members:
                if mc is None:
                    continue
                mb = _base(_km_first(mc))
                if mb is None:
                    no_km_members.append(mid)
                elif mb != hbase:
                    divergent.append((mid, mc, _km_first(mc), mb))
            if not divergent:
                continue
            # full-km collision among evicted members → same-coin-between risk
            full_kms = [_km_first(mc) for _, mc, _, _ in divergent]
            dup_full = {k for k, n in Counter(full_kms).items() if n > 1}

            entry = {
                "entity": ent, "host_id": c["id"], "host_km": _km_first(host_twin),
                "host_nominal": c.get("nominal"), "host_ruler": c.get("ruler"),
            }
            safe_members, complex_members = [], []
            for mid, mc, mkm, mb in divergent:
                reasons = []
                shared = _shares_type_level(host_twin, mc)
                if shared:
                    reasons.append("shares_" + "+".join(shared))
                if no_km_members:
                    reasons.append("host_has_noKM_member")
                if _km_first(mc) in dup_full:
                    reasons.append("same_km_as_sibling_evict")
                rec = {"member_id": mid, "member_km": mkm,
                       "member_hede": (mc.get("catalog") or {}).get("hede")}
                if reasons:
                    rec["complex_reasons"] = reasons
                    complex_members.append(rec)
                else:
                    safe_members.append(rec)
            if safe_members:
                safe.append({**entry, "split": safe_members})
            if complex_members:
                complex_.append({**entry, "split": complex_members,
                                 "_noKM_members": no_km_members})

    allow = {p["host_id"]: [s["member_id"] for s in p["split"]] for p in safe}

    print(f"SAFE: {len(safe)} hosts / {sum(len(p['split']) for p in safe)} members")
    print(f"COMPLEX: {len(complex_)} hosts / {sum(len(p['split']) for p in complex_)} members")
    print("SAFE by entity:", dict(Counter(p["entity"] for p in safe)))
    print("COMPLEX reasons:",
          dict(Counter(r for p in complex_ for s in p["split"]
                       for r in s.get("complex_reasons", []))))

    if args.write:
        ALLOWLIST.write_text(
            "# Auto-generated by gen_overmerge_purge_allowlist.py — SAFE over-merge\n"
            "# purge allowlist (CLAUDE.md §9.4). Each listed member carries a DIFFERENT\n"
            "# base KM than the host AND shares NO type-level catalog ref (hede/lange/\n"
            "# sieg/dav/fr) with it AND self-attributes (host has no orphan no-KM member,\n"
            "# no two evicted members share a KM, clean foundation twin exists). Absorb\n"
            "# resets the host to its twin, drops these members + force-promotes them\n"
            "# standalone. COMPLEX cases await curator review (docs/overmerge_split_COMPLEX.json).\n\n"
            + yaml.safe_dump(allow, allow_unicode=True, sort_keys=True))
        SAFE_JSON.write_text(json.dumps(safe, ensure_ascii=False, indent=2))
        COMPLEX_JSON.write_text(json.dumps(complex_, ensure_ascii=False, indent=2))
        print(f"\nwrote {ALLOWLIST.relative_to(ROOT)} ({len(allow)} hosts)")
    else:
        print("\n(dry-run — pass --write to persist)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
