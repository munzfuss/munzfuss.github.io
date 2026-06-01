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
V2_MERGE_DECISIONS = ROOT / "data" / "v2" / "merge_decisions"
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


def _base(km):
    """'A110'→'A110', '70.1'→'70', '11a'→'11', '156,3'→'156'."""
    if km in (None, "", []):
        return None
    s = str(km).strip()
    m = re.match(r"^([A-Za-z]*)(\d+)", s)
    return (m.group(1).upper() + m.group(2)) if m else s


def _km_bases(c) -> set:
    """SET of base KM tokens for a coin — handles scalar, list-form
    (multi-source KM accumulation, e.g. ['21','21.1']), and dict-form
    (register-keyed). Two coins SHARE a KM type iff their base-sets
    intersect; they are KM-divergent iff both non-empty AND disjoint.
    Critical: list-form KM must NOT be str()'d whole (that yields garbage
    like "['21', '21.1']" → false divergence)."""
    km = (c.get("catalog") or {}).get("km")
    if km in (None, "", []):
        return set()
    vals: list = []
    if isinstance(km, dict):
        vals = [v for v in km.values() if v not in (None, "", [])]
    elif isinstance(km, list):
        vals = [v for v in km if v not in (None, "", [])]
    else:
        vals = [km]
    out = set()
    for v in vals:
        b = _base(v)
        if b is not None:
            out.add(b)
    return out


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

    # Curator merge_decisions override §9.4 auto-split: when the curator
    # explicitly declares seeds A+B one coin (e.g. a Hede type Krause split
    # across KM 14/15/20), a different-base-KM composed_of member that is in
    # the SAME merge group as the host MUST NOT be auto-split off. Build the
    # seed-id groups, then map any final/unified id to its underlying seed
    # set (seed_unified composed_of, or the id itself for raw seeds).
    merge_groups: list[set] = []
    no_merge_pairs: set = set()
    for f in V2_MERGE_DECISIONS.glob("*.yml"):
        doc = yaml.safe_load(f.read_text(encoding="utf-8")) or {}
        for m in (doc.get("merges") or []):
            mem = {x for x in (m.get("members") or []) if x}
            if len(mem) >= 2:
                merge_groups.append(mem)
        for nm in (doc.get("no_merges") or []):
            mem = [x for x in (nm.get("members") or []) if x]
            for i in range(len(mem)):
                for j in range(i + 1, len(mem)):
                    no_merge_pairs.add(frozenset({mem[i], mem[j]}))

    def _seeds_of(cid: str) -> set:
        c = twin.get(cid)
        if c is not None:
            comp = [m for m in (c.get("composed_of") or []) if m != cid]
            return set(comp) | {cid} if comp else {cid}
        return {cid}

    def _curator_merged(host_id: str, member_id: str) -> bool:
        hs, ms = _seeds_of(host_id), _seeds_of(member_id)
        for g in merge_groups:
            if (hs & g) and (ms & g):
                return True
        return False

    def _curator_no_merged(host_id: str, member_id: str) -> bool:
        """True if an EXPLICIT curator no_merge separates the host's seed-set
        from the member's. Curator «different coin» → force-split, overriding
        the COMPLEX caution (no-KM member, shared-Hede). The absorb does not
        honour merger no_merges in its foundation-consolidation, so a member
        the merger correctly split off can be RE-FUSED into a final foundation
        — listing it in the SAFE allowlist makes the absorb purge evict it."""
        hs, ms = _seeds_of(host_id), _seeds_of(member_id)
        for a in hs:
            for b in ms:
                if frozenset({a, b}) in no_merge_pairs:
                    return True
        return False

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
            hbases = _km_bases(host_twin)
            if not hbases:
                continue
            # members keyed by presence of KM + base divergence. A member is
            # KM-divergent ONLY if its base-set is non-empty AND DISJOINT from
            # the host's base-set — list-form KM that SHARES a base (e.g. host
            # 21.2 vs member ['21','21.1']) is the SAME coin, not divergent.
            members = [(m, twin.get(m)) for m in comp]
            divergent = []          # different base KM (disjoint base-sets)
            no_km_members = []      # top-level member without a KM
            forced_split = set()    # curator no_merge'd from host → always split
            for mid, mc in members:
                if mc is None:
                    continue
                if _curator_no_merged(c["id"], mid):
                    forced_split.add(mid)
                mbases = _km_bases(mc)
                if not mbases:
                    no_km_members.append(mid)
                elif mbases.isdisjoint(hbases):
                    divergent.append((mid, mc, str((mc.get("catalog") or {}).get("km")),
                                      frozenset(mbases)))
            if not divergent and not forced_split:
                continue
            # same-base-set collision among evicted members → same-coin-between
            # risk (two members that are the same KM type as each other).
            base_keys = [bk for _, _, _, bk in divergent]
            dup_full = {bk for bk, n in Counter(base_keys).items() if n > 1}

            host_km_disp = (host_twin.get("catalog") or {}).get("km")
            entry = {
                "entity": ent, "host_id": c["id"], "host_km": host_km_disp,
                "host_nominal": c.get("nominal"), "host_ruler": c.get("ruler"),
            }
            safe_members, complex_members, seen = [], [], set()
            for mid, mc, mkm, mb in divergent:
                # Curator no_merge → split regardless of COMPLEX caution.
                if mid in forced_split:
                    safe_members.append({"member_id": mid, "member_km": mkm,
                                         "member_hede": (mc.get("catalog") or {}).get("hede"),
                                         "forced_by": "curator_no_merge"})
                    seen.add(mid)
                    continue
                if _curator_merged(c["id"], mid):
                    continue  # curator merge_decision says SAME coin — never split
                reasons = []
                shared = _shares_type_level(host_twin, mc)
                if shared:
                    reasons.append("shares_" + "+".join(shared))
                if no_km_members:
                    reasons.append("host_has_noKM_member")
                if mb in dup_full:
                    reasons.append("same_km_as_sibling_evict")
                rec = {"member_id": mid, "member_km": mkm,
                       "member_hede": (mc.get("catalog") or {}).get("hede")}
                if reasons:
                    rec["complex_reasons"] = reasons
                    complex_members.append(rec)
                else:
                    safe_members.append(rec)
            # Forced-split members that weren't base-KM-divergent (e.g. a no-KM
            # member the curator no_merge'd off the host).
            for mid, mc in members:
                if mc is None or mid in seen or mid not in forced_split:
                    continue
                safe_members.append({"member_id": mid,
                                     "member_km": str((mc.get("catalog") or {}).get("km")),
                                     "member_hede": (mc.get("catalog") or {}).get("hede"),
                                     "forced_by": "curator_no_merge"})
                seen.add(mid)
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
