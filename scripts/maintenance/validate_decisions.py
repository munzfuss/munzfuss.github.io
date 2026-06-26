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


def _decision_files() -> list[Path]:
    files: list[Path] = []
    if DECISIONS_DIR.exists():
        files += sorted(DECISIONS_DIR.glob("*.yml"))  # per-entity + _cross_entity
    return files


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

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
