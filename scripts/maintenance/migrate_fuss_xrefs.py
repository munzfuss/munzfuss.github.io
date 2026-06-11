#!/usr/bin/env python3
"""Migrate hand-written fuss cross-refs to `[fuss:KEY]` id-markers.

One-shot migration for the fuss cross-reference system
(docs/fuss_cross_refs_design.md, TODO §CT). Converts, across all prose
surfaces:

  1. KEY-form refs   `<code>9_25_thaler</code>`  → `[fuss:9_25_thaler]`
     (KEY ∈ top-level keys of data/shared/fuesse.yml — the snake_case
     id is unambiguous, only ever appears as a cross-ref).

  2. Display-name forms already introduced on 2026-06-11 for the two
     cards that were de-snake_cased by hand:
        `<code>Rosenobel-fod</code>` → `[fuss:rosenobel_fod]`
        `<code>Nobelfod</code>`      → `[fuss:nobel_fod]`

Idempotent: re-running finds nothing to do. Reports per-file counts.

Usage:
    .venv/bin/python scripts/maintenance/migrate_fuss_xrefs.py [--apply]

Without --apply it's a dry-run (prints what WOULD change). With --apply
it rewrites the files in place.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[2]
FUESSE_YML = REPO / "data" / "shared" / "fuesse.yml"

# Display-name → key for the two cards converted by hand on 2026-06-11.
# (These spans no longer hold the key, so they need an explicit map.)
DISPLAY_NAME_TO_KEY = {
    "Rosenobel-fod": "rosenobel_fod",
    "Nobelfod": "nobel_fod",
}


def fuss_keys() -> list[str]:
    """Top-level fuss ids from fuesse.yml."""
    data = yaml.safe_load(FUESSE_YML.read_text(encoding="utf-8"))
    return list(data.keys())


def target_files() -> list[Path]:
    files = [FUESSE_YML]
    files += sorted((REPO / "data" / "v2" / "locations").glob("*.yml"))
    files += sorted((REPO / "data" / "locations").glob("*.yml"))
    return files


def build_substitutions(keys: list[str]) -> list[tuple[re.Pattern, str, str]]:
    """List of (compiled_pattern, replacement, label)."""
    subs: list[tuple[re.Pattern, str, str]] = []
    # KEY-form — longest keys first so a key that is a prefix of another
    # can't partial-match (exact `<code>…</code>` boundaries make this
    # safe anyway, but order defensively).
    for key in sorted(keys, key=len, reverse=True):
        pat = re.compile(r"<code>" + re.escape(key) + r"</code>")
        subs.append((pat, f"[fuss:{key}]", f"key:{key}"))
    # Display-name form (the two hand-converted cards).
    for name, key in DISPLAY_NAME_TO_KEY.items():
        pat = re.compile(r"<code>" + re.escape(name) + r"</code>")
        subs.append((pat, f"[fuss:{key}]", f"name:{name}→{key}"))
    return subs


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true",
                    help="rewrite files in place (default: dry-run)")
    args = ap.parse_args()

    keys = fuss_keys()
    subs = build_substitutions(keys)

    grand_total = 0
    for path in target_files():
        text = path.read_text(encoding="utf-8")
        new = text
        per_label: dict[str, int] = {}
        for pat, repl, label in subs:
            new, n = pat.subn(repl, new)
            if n:
                per_label[label] = per_label.get(label, 0) + n
        total = sum(per_label.values())
        if total:
            grand_total += total
            rel = path.relative_to(REPO)
            print(f"{rel}: {total} ref(s)")
            for label, n in sorted(per_label.items(), key=lambda kv: -kv[1]):
                print(f"    {n:>3}  {label}")
            if args.apply:
                path.write_text(new, encoding="utf-8")

    mode = "APPLIED" if args.apply else "DRY-RUN (use --apply to write)"
    print(f"\n{mode} — {grand_total} cross-ref(s) "
          f"across {len(target_files())} files scanned")
    return 0


if __name__ == "__main__":
    sys.exit(main())
