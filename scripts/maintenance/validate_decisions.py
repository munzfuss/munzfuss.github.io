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
`members` = a list of >= 2 non-empty ids, and every year_demote entry carries
`member_id`/`members`. Both checks share `merge_seeds_cross_source`'s
implementation so the merger and this gate never drift.

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


def check_member_resolution(entity_filter: set[str] | None = None) -> list[tuple]:
    """Every merges/no_merges member MUST be a current SEED id. A non-resolving
    member is an orphan: a `merges` orphan is usually a redundant final/foundation
    id (its seed is already a member), but a `no_merges` orphan is an INACTIVE
    block — a silent over-merge gap. Returns [(entity, key, member), …].

    The fix is never to delete blindly: `resolve` the member to its seed id
    (`.claude/skills/v2-merge-coins/merge_helper.py resolve <entity> <id>`),
    re-point or drop, then re-merge + re-absorb. See the v2-merge-coins skill.
    """
    import yaml
    orphans: list[tuple] = []
    seeds_cache: dict[str, set[str]] = {}
    for path in sorted(DECISIONS_DIR.glob("*.yml")):
        ent = path.stem
        if ent.startswith("_"):
            continue  # _cross_entity members span entities — out of scope here
        if entity_filter and ent not in entity_filter:
            continue
        if ent not in seeds_cache:
            seeds_cache[ent] = _seed_ids(ent)
        sids = seeds_cache[ent]
        doc = yaml.safe_load(path.read_text()) or {}
        for key in ("merges", "no_merges"):
            for blk in (doc.get(key) or []):
                for m in (blk.get("members") or []):
                    if m not in sids:
                        orphans.append((ent, key, m))
    return orphans


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--quiet", action="store_true")
    ap.add_argument("--check-members", action="store_true",
                    help="also verify every merges/no_merges member resolves to "
                         "a current seed id (orphan detector; exit 1 if any)")
    ap.add_argument("--entity", help="restrict --check-members to this entity")
    args = ap.parse_args()

    if args.check_members:
        ef = {args.entity} if args.entity else None
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
            return 1
        if not args.quiet:
            print("✓ all merge-decision members resolve to seed ids.")
        return 0

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
