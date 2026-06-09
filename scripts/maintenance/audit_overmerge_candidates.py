#!/usr/bin/env python3
"""Audit V2 final entries for STALE over-merges (CLAUDE.md §9.4).

The absorb stage is additive + sticky: members fused into a final's
`composed_of` by an OLDER matcher are never re-validated, so a since-hardened
matcher would reject pairs that still sit in one final entry. This audit
re-runs the CURRENT `match_pair` PAIRWISE among each final entry's unified
composed_of members and flags any final whose members no longer all agree —
i.e. the entry bundles ≥2 coins the matcher would today keep apart.

Read-only. Emits a triaged report; fixing a flagged entry is a per-case
curator decision (merge_decisions + overmerge_purge_allowlist), exactly like
the dk-tid-173642 split (2026-06-09).

Reason buckets (severity high→low):
  metal     — different metal on the SAME nominal: usually a Guldafslag /
              Sølvafslag off-strike (§9.3, arguably shouldn't be a row at all)
              OR a genuinely different-metal coin. Eyeball.
  nominal   — different denomination. Watch for FALSE positives: accounting
              equivalents (6 Pfennig ≡ 1 Sechsling, 1 Groschen ≡ 1/24 Thaler,
              2 Mark ≡ ½ Krone) and un-folded synonyms (2 Ducats ≡ 2 Dukaten,
              Kurantdaler ≡ Kurant Daler) read as «different» here.
  catalog   — different type-level catalogue index (§9.4 core signal).
  ruler     — different reign attribution.

Usage:
  .venv/bin/python scripts/maintenance/audit_overmerge_candidates.py
  .venv/bin/python scripts/maintenance/audit_overmerge_candidates.py --entity danish_realm
  .venv/bin/python scripts/maintenance/audit_overmerge_candidates.py --json out.json
"""
from __future__ import annotations

import argparse
import glob
import itertools
import json
import os
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "maintenance"))

from maintenance.merge_seeds_cross_source import match_pair  # noqa: E402

FINAL_DIR = ROOT / "data" / "v2" / "final"
UNIFIED_DIR = ROOT / "data" / "v2" / "seed_unified"

# Primary signals whose explicit `False` (disagreement) marks an over-merge.
# Ordered by severity for ranking.
_PRIMARY = ("metal", "nominal", "catalog", "ruler")


def _load(p: Path) -> dict:
    if not p.exists():
        return {}
    return yaml.safe_load(p.read_text()) or {}


def audit_entity(entity_id: str) -> list[dict]:
    uni = {
        e["id"]: e
        for e in (_load(UNIFIED_DIR / f"{entity_id}.yml").get("coins") or [])
        if isinstance(e, dict)
    }
    out: list[dict] = []
    for e in (_load(FINAL_DIR / f"{entity_id}.yml").get("coins") or []):
        if not isinstance(e, dict):
            continue
        members = [
            uni[c]
            for c in (e.get("composed_of") or [])
            if c != e.get("id") and c in uni
        ]
        if len(members) < 2:
            continue
        # Pairwise — collect every disagreeing pair, keep the strongest.
        worst = None
        worst_sev = 99
        for a, b in itertools.combinations(members, 2):
            r = match_pair(a, b, entity_id, None)
            p = r.get("primary") or {}
            bad = [k for k in _PRIMARY if p.get(k) is False]
            if not bad:
                continue
            sev = min(_PRIMARY.index(k) for k in bad)
            if sev < worst_sev:
                worst_sev, worst = sev, (a, b, bad)
                if sev == 0:  # metal — strongest, stop early
                    break
        if worst:
            a, b, bad = worst
            out.append({
                "entity": entity_id,
                "final_id": e.get("id"),
                "nominal": e.get("nominal"),
                "year": f"{e.get('year_first')}-{e.get('year_last')}",
                "n_members": len(members),
                "reason": ",".join(bad),
                "severity": worst_sev,
                "member_a": a.get("id"),
                "nominal_a": a.get("nominal"),
                "member_b": b.get("id"),
                "nominal_b": b.get("nominal"),
            })
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--entity", help="Audit only this entity")
    ap.add_argument("--json", help="Write full candidate list to this JSON path")
    args = ap.parse_args()

    entities = (
        [args.entity]
        if args.entity
        else sorted(os.path.basename(f)[:-4] for f in glob.glob(str(FINAL_DIR / "*.yml")))
    )
    cands: list[dict] = []
    for ent in entities:
        cands.extend(audit_entity(ent))
    cands.sort(key=lambda c: (c["severity"], c["entity"], c["final_id"]))

    from collections import Counter
    print(f"=== OVER-MERGE CANDIDATES: {len(cands)} ===")
    print("  by reason: ", dict(Counter(c["reason"] for c in cands)))
    print("  by entity: ", dict(Counter(c["entity"] for c in cands)))
    print()
    for c in cands:
        print(
            f"  [{c['reason']:14}] {c['entity']:22} {c['final_id']:30} "
            f"«{c['nominal']}» {c['year']} ({c['n_members']}m)"
        )
        print(
            f"       {c['nominal_a']!r} ({c['member_a']})  ✗  "
            f"{c['nominal_b']!r} ({c['member_b']})"
        )
    if args.json:
        Path(args.json).write_text(json.dumps(cands, ensure_ascii=False, indent=2))
        print(f"\nWrote {len(cands)} candidates to {args.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
