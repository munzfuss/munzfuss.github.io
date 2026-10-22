#!/usr/bin/env python3
"""Re-key data/v2/classification_decisions/<entity>.yml assignments to SEED ids
(V2_DECISIONS D49, stage 1).

WHY. An assignment's `coin_id` was the class id `unified-<top-authority
member>`, which the merger renames the moment a higher-authority member joins
the class, a §9a fold is re-cut, or the class splits — so the decision silently
stopped applying (238 of 498 pointed at ids in no final on 2026-10-22, absorb
printed them as ASSIGN-MISS). A seed id never changes. Absorb now resolves a
seed-keyed decision to the class holding the seed (`_decision_keys`), a bare
Hede code and a specimen folded by thinning (`_thinned_from`) included.

WHAT IT DOES, per assignment:
  * `unified-x`            → `x` (the head member IS a seed id, live or folded)
  * a seed id              → unchanged
  * a legacy final id (`km-…`, `hs-…`) whose final has `composed_of` members
                           → the top-authority seed of those classes
                             (`merge_seeds_cross_source._authority_score`)
  * a legacy final id with no members → kept (it matches the final exactly)
Then the seed is resolved globally (same expansion as validate_decisions
--check-classification); an assignment whose coin now lives in ANOTHER
entity's class is MOVED to that entity's file (absorb reads only its own
entity's file — audit_v2 I13 semantics). A key that resolves to nothing is
left in place and listed for the curator. Two assignments that end up on one
key in one file are collapsed when they agree and reported when they do not.
A moved entry that would land on a class already carrying a LIVE decision with
other values does not displace it (the live decision is the one in force; the
stranded one was never applied): it stays in its source file as a record with
`superseded_by: <live key>`, which absorb and validate_decisions ignore.
Likewise a REVIVED decision — dead at HEAD, now resolving — whose values differ
from the classification the final stores is held (`superseded_by: <final id>
(stored classification)`) and listed: the stored values are what the page shows,
and a decision nobody saw applied is not activated by a key migration.

A rewritten entry keeps the old key in `was:`; a moved entry carries
`moved_from:`. Both are provenance for `trace_coin why`; absorb preserves
assignments verbatim.

Usage:
    .venv/bin/python scripts/maintenance/migrate_classification_keys.py            # dry-run
    .venv/bin/python scripts/maintenance/migrate_classification_keys.py --apply
    … --entity danish_realm
After --apply run absorb --apply (it re-emits the files in canonical form) and
`validate_decisions.py --check-classification`.
"""
from __future__ import annotations

import argparse
import importlib.util
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "maintenance"))

_spec = importlib.util.spec_from_file_location(
    "validate_decisions", str(ROOT / "scripts" / "maintenance" / "validate_decisions.py"))
_V = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_V)
_M = _V._M

from lib import yaml_io  # noqa: E402

CLS_DIR = ROOT / "data" / "v2" / "classification_decisions"
SEED_UNIFIED = ROOT / "data" / "v2" / "seed_unified"
FINAL = ROOT / "data" / "v2" / "final"


def _coins(path: Path) -> list[dict]:
    import yaml
    if not path.exists():
        return []
    d = yaml.safe_load(path.read_text()) or {}
    return [c for c in ((d.get("coins") if isinstance(d, dict) else d) or [])
            if isinstance(c, dict) and c.get("id")]


class World:
    """Global indices: every seed id, the thinned index, {seed → (entity,
    class)} over all seed_unified files, {final id → composed_of} per entity."""

    def __init__(self) -> None:
        self.seed_ids: set[str] = set()
        for f in sorted((ROOT / "data" / "v2" / "seed").glob("*/*.yml")):
            self.seed_ids |= {c["id"] for c in _coins(f)}
        self.thinned = _V._thinned_index()
        self.seed_home: dict[str, tuple[str, str]] = {}
        for f in sorted(SEED_UNIFIED.glob("*.yml")):
            for c in _coins(f):
                for m in c.get("composed_of") or []:
                    self.seed_home.setdefault(str(m), (f.stem, c["id"]))
        self.final_members: dict[str, dict[str, list[str]]] = {}
        self.final_cls: dict[str, dict[str, tuple]] = {}      # entity → {id: value}
        self.final_of_key: dict[str, dict[str, str]] = {}     # entity → {id|member: final id}
        for f in sorted(FINAL.glob("*.yml")):
            cs = _coins(f)
            self.final_members[f.stem] = {c["id"]: list(c.get("composed_of") or []) for c in cs}
            self.final_cls[f.stem] = {c["id"]: _V._cls_value(c) for c in cs}
            self.final_of_key[f.stem] = {}
            for c in cs:
                for k in [c["id"]] + list(c.get("composed_of") or []):
                    self.final_of_key[f.stem].setdefault(str(k), c["id"])
        self.class_seeds: dict[str, list[str]] = defaultdict(list)
        for s, (_, cls) in self.seed_home.items():
            self.class_seeds[cls].append(s)

    def expand(self, key: str) -> list[str]:
        return _M._expand_member_against(key, self.seed_ids, self.thinned)

    def new_key(self, entity: str, key: str) -> tuple[str, str]:
        """(new coin_id, how). how ∈ unified / seed / legacy-composed /
        legacy-kept / unresolved."""
        if key.startswith("unified-"):
            return key[len("unified-"):], "unified"
        if self.expand(key):
            return key, "seed"
        members = self.final_members.get(entity, {}).get(key)
        if members is None:
            return key, "unresolved"
        seeds = sorted({s for m in members for s in self.class_seeds.get(m, [])
                        if m != key} | {m for m in members if m in self.seed_ids})
        if not seeds:
            return key, "legacy-kept"
        seeds.sort(key=lambda s: (-_M._authority_score(s), s))
        return seeds[0], "legacy-composed"

    def final_for(self, entity: str, key: str) -> str | None:
        """The final in `entity` that a (possibly seed) key reaches, via its class."""
        fk = self.final_of_key.get(entity, {})
        if key in fk:
            return fk[key]
        for s in self.expand(key):
            cls = self.seed_home.get(s, (None, None))[1]
            if cls and cls in fk:
                return fk[cls]
        return None

    def home_of(self, seed_key: str) -> set[str]:
        return {self.seed_home[s][0] for s in self.expand(seed_key)
                if s in self.seed_home}


def migrate(world: World, entities: list[str], apply: bool) -> int:
    today = date.today().isoformat()
    docs: dict[str, tuple] = {}          # entity → (ctx, doc)
    moves: list[tuple[str, str, dict]] = []   # (from, to, entry)
    report: dict[str, list[str]] = defaultdict(list)
    for ent in entities:
        path = CLS_DIR / f"{ent}.yml"
        if not path.exists():
            continue
        ctx, doc = yaml_io.load(path)
        docs[ent] = (ctx, doc)
        keep = []
        for a in list(doc.get("assignments") or []):
            if not isinstance(a, dict) or not a.get("coin_id"):
                keep.append(a)
                continue
            old = str(a["coin_id"])
            new, how = world.new_key(ent, old)
            if how == "unresolved" or (how != "legacy-kept" and not world.expand(new)
                                       and how != "seed"):
                report["unresolved"].append(f"[{ent}] {old} — {a.get('reason', '')!s:.80}")
                keep.append(a)
                continue
            was_dead = old not in world.final_of_key.get(ent, {})
            if new != old:
                a["coin_id"] = new
                a["was"] = old
            report[how].append(f"[{ent}] {old} → {new}" if new != old else f"[{ent}] {old}")
            homes = world.home_of(new) if how != "legacy-kept" else {ent}
            # A REVIVED decision (dead at HEAD — its old key reached no final)
            # whose values differ from what the final holding the coin stores
            # is not activated by this migration: the stored classification is
            # the one in force on the rendered page, and the revived text may
            # be a stale copy (the NGC «phase repair, not a new classification»
            # entries carried kind kurant onto scheide / tarif coins). Kept as
            # a record, `superseded_by`, listed for the curator.
            tgt_ent = next(iter(homes)) if len(homes) == 1 else ent
            fid = world.final_for(tgt_ent, new) if was_dead else None
            if fid and world.final_cls[tgt_ent].get(fid) != _V._cls_value(a):
                a["superseded_by"] = f"{fid} ({tgt_ent}, stored classification)"
                report["revived-held"].append(
                    f"[{ent}] {new} (was {old}) → final {fid} in {tgt_ent} stores "
                    f"{world.final_cls[tgt_ent][fid]}, decision says {_V._cls_value(a)}")
                keep.append(a)
                continue
            if homes and ent not in homes:
                if len(homes) == 1:
                    tgt = next(iter(homes))
                    a["moved_from"] = f"{ent} {today}"
                    moves.append((ent, tgt, a))
                    report["moved"].append(f"[{ent}] {new} → {tgt}.yml")
                    continue
                report["spans-entities"].append(f"[{ent}] {new} → {sorted(homes)} (left)")
            keep.append(a)
        doc["assignments"] = keep
    def _keys(k: str) -> set[str]:
        return {k} | {world.seed_home[s][1] for s in world.expand(k) if s in world.seed_home}

    for src, tgt, a in moves:
        if tgt not in docs:
            path = CLS_DIR / f"{tgt}.yml"
            if path.exists():
                docs[tgt] = yaml_io.load(path)
            else:
                docs[tgt] = (None, {"entity_id": tgt, "assignments": []})
        # A stranded decision (never applied: filed under the wrong entity)
        # moving onto a class that already carries a LIVE decision with other
        # values does not displace it — the live one is the decision in force.
        live = next((b for b in docs[tgt][1].get("assignments") or []
                     if isinstance(b, dict) and b.get("coin_id")
                     and not b.get("superseded_by")
                     and _keys(str(b["coin_id"])) & _keys(str(a["coin_id"]))
                     and _V._cls_value(b) != _V._cls_value(a)), None)
        if live is not None:
            a.pop("moved_from", None)
            a["superseded_by"] = f"{live['coin_id']} ({tgt})"
            docs[src][1].setdefault("assignments", []).append(a)
            report["superseded"].append(
                f"[{src}] {a['coin_id']} — live decision {live['coin_id']} in {tgt} "
                f"has other values {_V._cls_value(live)} vs {_V._cls_value(a)}; kept inert")
            continue
        docs[tgt][1].setdefault("assignments", []).append(a)
    # collapse agreeing duplicates, report disagreeing ones
    for ent, (_, doc) in docs.items():
        seen: dict[str, dict] = {}
        out = []
        for a in doc.get("assignments") or []:
            if not isinstance(a, dict) or not a.get("coin_id"):
                out.append(a)
                continue
            k = str(a["coin_id"])
            if k in seen:
                if _V._cls_value(seen[k]) == _V._cls_value(a):
                    report["collapsed"].append(f"[{ent}] {k} (duplicate, same values)")
                    continue
                report["CONFLICT"].append(f"[{ent}] {k}: {_V._cls_value(seen[k])} vs {_V._cls_value(a)}")
            seen[k] = a
            out.append(a)
        doc["assignments"] = out

    for kind in ("unified", "seed", "legacy-composed", "legacy-kept", "moved",
                 "superseded", "revived-held", "collapsed", "spans-entities",
                 "unresolved", "CONFLICT"):
        lines = report.get(kind) or []
        print(f"{kind:16s} {len(lines)}")
        if kind in ("legacy-composed", "moved", "superseded", "revived-held",
                    "spans-entities", "unresolved", "CONFLICT", "collapsed"):
            for ln in lines:
                print(f"    {ln}")
    if not apply:
        print("\n--- DRY RUN — nothing written. Re-run with --apply. ---")
        return 0
    for ent, (ctx, doc) in docs.items():
        path = CLS_DIR / f"{ent}.yml"
        if ctx is None:
            path.write_text(yaml_io.dump_v2_canonical(doc), encoding="utf-8")
        else:
            yaml_io.save(ctx, path, doc)
    print(f"\n✓ wrote {len(docs)} file(s); now run absorb --apply and "
          "validate_decisions.py --check-classification")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--entity")
    args = ap.parse_args()
    ents = [args.entity] if args.entity else sorted(p.stem for p in CLS_DIR.glob("*.yml")
                                                   if not p.stem.startswith("_"))
    return migrate(World(), ents, args.apply)


if __name__ == "__main__":
    raise SystemExit(main())
