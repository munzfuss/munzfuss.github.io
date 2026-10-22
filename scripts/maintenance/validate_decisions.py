#!/usr/bin/env python3
"""Integrity gate for the curator decision files (§CN / merge_decisions).

WHY THIS EXISTS — a hand-edit to data/v2/merge_decisions/<entity>.yml (or
_cross_entity.yml) can silently corrupt the file: a clobbered `- members:`
block leaves a duplicate `reason:` key, and PyYAML's default loader keeps only
the LAST value — so a force-merge decision silently vanishes and the merger
applies a WRONG grouping with no warning (caught 2026-06-26: the KM-567→Hede-10
force-merge was dropped this way, re-scattering the coin).

This validator (a) strict-loads every decisions file with a duplicate-key-
raising loader, and (b) checks every merges/no_merges entry carries
`members` = a list of >= 2 non-empty ids (>= 1 in `_cross_entity.yml` merges: a RELOCATE), and every year_demote entry carries
`member_id`/`members`. Both checks share `merge_seeds_cross_source`'s
implementation so the merger and this gate never drift.
`--check-classification` (D49 stage 1) does the same for
data/v2/classification_decisions/<entity>.yml: every `coin_id` must resolve to a
seed of the entity (bare-Hede and `_thinned_from` expansion included) or to a
current class / final id, and no two assignments may reach one class with
different fuss / phase / kind.

Run standalone (used by .githooks/pre-commit):
    .venv/bin/python scripts/maintenance/validate_decisions.py        # all files
    .venv/bin/python scripts/maintenance/validate_decisions.py --quiet
Exit 0 = all clean; exit 1 = at least one file failed (details on stderr).
"""
from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
_spec = importlib.util.spec_from_file_location(
    "merge_seeds_cross_source",
    str(ROOT / "scripts" / "maintenance" / "merge_seeds_cross_source.py"))
_M = importlib.util.module_from_spec(_spec)
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "maintenance"))
_spec.loader.exec_module(_M)

DECISIONS_DIR = ROOT / "data" / "v2" / "merge_decisions"
CLASSIFY_DIR = ROOT / "data" / "v2" / "classification_decisions"
SEED_DIR = ROOT / "data" / "v2" / "seed"


def _decision_files() -> list[Path]:
    files: list[Path] = []
    if DECISIONS_DIR.exists():
        files += sorted(DECISIONS_DIR.glob("*.yml"))  # per-entity + _cross_entity
    return files


def _seed_ids(entity: str) -> set[str]:
    import yaml
    out: set[str] = set()
    for f in sorted(SEED_DIR.glob(f"*/{entity}.yml")):
        d = yaml.safe_load(f.read_text()) or {}
        for c in (d.get("coins") if isinstance(d, dict) else d) or []:
            if c.get("id"):
                out.add(c["id"])
    return out


def _thinned_index() -> dict[str, list[str]]:
    """{thinned-away id: [representative ids]} across EVERY seed bucket.

    Global, not per-entity, because §9a thinning and V2 entity routing are
    independent: a member may name a specimen whose representative now sits in
    another bucket. `_expand_member_against` still intersects the result with
    the entity's own id set, so a cross-bucket representative cannot silently
    satisfy a member that does not belong to that entity."""
    import yaml
    coins = []
    for f in sorted(SEED_DIR.glob("*/*.yml")):
        d = yaml.safe_load(f.read_text()) or {}
        coins.extend((d.get("coins") if isinstance(d, dict) else d) or [])
    return _M.build_thinned_index(coins)


def _cross_entity_pulls() -> dict[str, set[str]]:
    """{target_entity: {member seed ids pulled INTO it}} from _cross_entity.yml.

    The merger processes an entity over its own seed buckets PLUS everything a
    cross-entity decision pulls into it (`_load_cross_entity_decisions`). A
    per-entity `no_merges` may therefore legitimately name a seed whose home
    bucket is a different entity — it is in this entity's processing set for the
    duration of the run, so the block is live.

    Without this, a routing change that re-homes a seed makes a working
    safeguard look like an orphan. Real case 2026-07-29: the per-letter mint fix
    moved `dk-hede-c7h13b` to danish_realm, and the four §CW pairs that keep the
    Albertsdaler out of the domestic Hede 13 cluster were reported as
    non-resolving — while a merge run proved the split still held, because the
    Hede 13 cross-entity group pulls every letter into royal_holstein.
    """
    import yaml
    path = DECISIONS_DIR / "_cross_entity.yml"
    if not path.exists():
        return {}
    doc = yaml.safe_load(path.read_text()) or {}
    out: dict[str, set[str]] = {}
    for blk in (doc.get("merges") or []):
        target = blk.get("target_entity")
        if not target:
            continue
        out.setdefault(target, set()).update(blk.get("members") or [])
    return out


def check_member_resolution(entity_filter: set[str] | None = None) -> list[tuple]:
    """Every merges/no_merges member must resolve to current SEED id(s). A
    member resolves if it IS a seed id OR if it is a bare Hede code that the
    merger's `_expand_member_against` expands to sub-letter seeds («dk-hede-
    c4h112» → c4h112a/c4h112b — the intended curator shorthand: the decision is
    made at the «whole Hede 112» level and the merger applies it to every
    sub-variant, grouping them so a no_merge never blocks within one coin).

    Using the merger's OWN resolver (`_M._expand_member_against`) keeps this gate
    and the merger from ever drifting. The resolver is also handed the
    `_thinned_from` index, so a member naming a specimen §9a thinning has since
    dropped resolves to the representative that absorbed it rather than reading
    as an orphan. A member that still resolves to nothing is
    a real orphan: typically a folded final/V1 id (`km-305-2-fr-iii-1669`) whose
    seed is already another member (redundant → drop), or a typo (re-point). NEVER
    re-point a bare Hede code to a flat sub-variant list — that would make a
    no_merge block the legitimate within-coin pair. Returns [(entity, key, member)].
    """
    import yaml
    orphans: list[tuple] = []
    seeds_cache: dict[str, set[str]] = {}
    pulls = _cross_entity_pulls()
    thinned = _thinned_index()
    for path in sorted(DECISIONS_DIR.glob("*.yml")):
        ent = path.stem
        if ent.startswith("_"):
            continue  # _cross_entity members span entities — out of scope here
        if entity_filter and ent not in entity_filter:
            continue
        if ent not in seeds_cache:
            # The entity's processing set = its own seeds + everything a
            # cross-entity decision pulls into it (mirrors the merger).
            seeds_cache[ent] = _seed_ids(ent) | pulls.get(ent, set())
        sids = seeds_cache[ent]
        doc = yaml.safe_load(path.read_text()) or {}
        for key in ("merges", "no_merges"):
            for blk in (doc.get(key) or []):
                for m in (blk.get("members") or []):
                    if not _M._expand_member_against(m, sids, thinned):
                        orphans.append((ent, key, m))
    return orphans


def _layer_ids(entity: str, layer: str) -> tuple[set[str], dict[str, str]]:
    """(ids, {composed_of member → id}) of data/v2/<layer>/<entity>.yml."""
    import yaml
    path = ROOT / "data" / "v2" / layer / f"{entity}.yml"
    ids: set[str] = set()
    member_of: dict[str, str] = {}
    if not path.exists():
        return ids, member_of
    d = yaml.safe_load(path.read_text()) or {}
    for c in (d.get("coins") if isinstance(d, dict) else d) or []:
        if not isinstance(c, dict) or not c.get("id"):
            continue
        ids.add(c["id"])
        for m in c.get("composed_of") or []:
            member_of.setdefault(str(m), c["id"])
    return ids, member_of


def _cls_value(a: dict) -> tuple[str, str, str]:
    """Hashable (fuss, phase, kind) of an assignment — a value may be a dict
    (per-language phase label), so compare the canonical text."""
    import json as _j
    return tuple(_j.dumps(a.get(k), sort_keys=True, default=str, ensure_ascii=False)
                 for k in ("fuss", "phase", "kind"))


def check_classification_resolution(entity_filter: set[str] | None = None
                                    ) -> tuple[list[tuple], list[tuple]]:
    """Every classification_decisions `coin_id` must resolve (D49 stage 1), and
    two assignments reaching one class may not disagree.

    A `coin_id` resolves when it is a SEED id of the entity's processing set
    (with the merger's bare-Hede and `_thinned_from` expansion — the same
    `_expand_member_against` the member check uses), or, for backward
    compatibility, a current seed_unified / final id of that entity or a
    member a final's `composed_of` names. Anything else is an orphan absorb
    reports as ASSIGN-MISS and never applies.

    A conflict is two assignments whose keys reach the SAME class (seed_unified
    id, via composed_of) with different (fuss, phase, kind): absorb refuses to
    write on it. Agreeing duplicates are fine. Returns (orphans, conflicts) as
    [(entity, coin_id)] and [(entity, class, [coin_ids], [values])]."""
    import yaml
    orphans: list[tuple] = []
    conflicts: list[tuple] = []
    pulls = _cross_entity_pulls()
    thinned = _thinned_index()
    for path in sorted(CLASSIFY_DIR.glob("*.yml")):
        ent = path.stem
        if ent.startswith("_") or (entity_filter and ent not in entity_filter):
            continue
        sids = _seed_ids(ent) | pulls.get(ent, set())
        uids, seed_class = _layer_ids(ent, "seed_unified")
        fids, final_member = _layer_ids(ent, "final")
        known = uids | fids | set(final_member)
        doc = yaml.safe_load(path.read_text()) or {}
        by_class: dict[str, list[dict]] = {}
        for a in (doc.get("assignments") or []):
            if not isinstance(a, dict) or not a.get("coin_id") or a.get("superseded_by"):
                continue   # superseded entries are records, not live decisions
            cid = str(a["coin_id"])
            seeds = _M._expand_member_against(cid, sids, thinned)
            if not seeds and cid not in known:
                orphans.append((ent, cid))
                continue
            classes = {seed_class[s] for s in seeds if s in seed_class} or {cid}
            for cls in classes:
                by_class.setdefault(cls, []).append(a)
        for cls, lst in by_class.items():
            vals = {_cls_value(a) for a in lst}
            if len(vals) > 1:
                conflicts.append((ent, cls, sorted(str(a["coin_id"]) for a in lst),
                                  sorted(map(str, vals))))
    return orphans, conflicts


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--quiet", action="store_true")
    ap.add_argument("--check-members", action="store_true",
                    help="also verify every merges/no_merges member resolves to "
                         "a current seed id (orphan detector; exit 1 if any)")
    ap.add_argument("--check-classification", action="store_true",
                    help="also verify every classification_decisions coin_id "
                         "resolves and no two assignments on one class disagree "
                         "(exit 1 if any)")
    ap.add_argument("--entity", help="restrict the resolution checks to this entity")
    args = ap.parse_args()
    ef = {args.entity} if args.entity else None
    rc = 0

    if args.check_members:
        orphans = check_member_resolution(ef)
        if orphans:
            print(f"⚠ {len(orphans)} non-resolving merge-decision member(s) "
                  "(orphans):", file=sys.stderr)
            for ent, key, m in orphans:
                tag = "BLOCK-INACTIVE" if key == "no_merges" else "skipped"
                print(f"    [{ent}] {key}: {m}   ({tag})", file=sys.stderr)
            print("  Each must resolve to a SEED id. Re-point or drop via the "
                  "v2-merge-coins skill;\n  a non-resolving no_merges member is a "
                  "silent over-merge gap.", file=sys.stderr)
            rc = 1
        elif not args.quiet:
            print("✓ all merge-decision members resolve to seed ids.")

    if args.check_classification:
        orphans, conflicts = check_classification_resolution(ef)
        if orphans:
            print(f"⚠ {len(orphans)} non-resolving classification coin_id(s) "
                  "(absorb reports them as ASSIGN-MISS and never applies them):",
                  file=sys.stderr)
            for ent, cid in orphans:
                print(f"    [{ent}] {cid}", file=sys.stderr)
            print("  Re-key to a SEED id of the coin (scripts/maintenance/"
                  "migrate_classification_keys.py), move the entry to the coin's "
                  "entity, or drop it.", file=sys.stderr)
            rc = 1
        if conflicts:
            print(f"⚠ {len(conflicts)} classification conflict(s) — assignments "
                  "reaching one class with different values:", file=sys.stderr)
            for ent, cls, cids, vals in conflicts:
                print(f"    [{ent}] {cls}: {', '.join(cids)} → {vals}", file=sys.stderr)
            rc = 1
        if not orphans and not conflicts and not args.quiet:
            print("✓ all classification coin_ids resolve, no conflicts.")

    if args.check_members or args.check_classification:
        return rc

    files = _decision_files()
    failed = 0
    for path in files:
        try:
            _M.load_decisions_yaml(path)  # strict-load + structural validate
        except _M.DecisionsIntegrityError as e:
            failed += 1
            print(f"✗ {path.relative_to(ROOT)}\n  {e}", file=sys.stderr)
        except Exception as e:  # noqa: BLE001 — surface any parse failure too
            failed += 1
            print(f"✗ {path.relative_to(ROOT)}: {type(e).__name__}: {e}",
                  file=sys.stderr)
    if failed:
        print(f"\n{failed}/{len(files)} decision file(s) FAILED integrity check.",
              file=sys.stderr)
        return 1
    if not args.quiet:
        print(f"✓ {len(files)} decision file(s) pass integrity check.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
