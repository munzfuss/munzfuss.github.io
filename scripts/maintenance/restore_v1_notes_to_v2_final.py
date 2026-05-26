#!/usr/bin/env python3
"""One-time recovery: gap-fill V1 curator notes into V2 final entries.

Background
----------
V1→V2 bootstrap (`bootstrap_v2_final_from_v1.py`) migrated curated
coin entries from `data/locations/*.yml` (V1, frozen post-2026-05-18)
into `data/v2/final/*.yml` (V2 entity-keyed). `CURATED_FIELDS` of the
bootstrap declared `note` as preserved-on-migration, but a regression
in the migration path dropped the `note` field for most entries.
Sister script `restore_v1_sources_to_v2_final.py` handled the same
class of bug for `sources` lists; this script handles `note`.

Audit 2026-05-26 (after KM-29 user-reported regression):

  Per-entity coverage of `note` field in V2 final
    royal_holstein:     51 / 307   (256 missing)
    danish_realm:       …
    danish_norway:      …
    schleswig_holstein  ← V1 home, source of truth for note prose
                        323 / 323 entries with notes (V1)

For each V2 final entry whose `note` is missing AND whose source-V1
counterpart HAS a note, copy V1's note dict + record provenance via
`_curation_holds: {note: "V1 backfill 2026-05-26 from <v1-path>::<id>"}`.

V1 ↔ V2 entry matching (four strategies, applied in order):

  1. Direct id match — V2.id == V1.id.
  2. Unified-prefix match — V2.id == "unified-{V1.id}".
  3. Composed_of match — V1.id in V2.composed_of.
  4. Seed_unified bridge — V1.id appears in seed_unified composed_of
     of some unified entry whose id == V2.id (covers the post-relocation
     case where the V1 entry's composed_of representation lives in
     seed_unified rather than in final directly).

The V1 note is copied verbatim (dict-form with de/en/uk keys typical).
`_curation_holds` is added as dict-form with a one-line provenance
reason per CLAUDE.md «Manual-override preservation rule».

Idempotency: re-runs after --apply leave V2 unchanged. Only entries
LACKING a note get backfilled; once a note exists, subsequent runs
skip the entry.

Usage
-----
    .venv/bin/python scripts/maintenance/restore_v1_notes_to_v2_final.py --dry-run
    .venv/bin/python scripts/maintenance/restore_v1_notes_to_v2_final.py --apply
    .venv/bin/python scripts/maintenance/restore_v1_notes_to_v2_final.py --apply --entity royal_holstein
"""
from __future__ import annotations

import argparse
import pathlib
import sys
from collections import Counter, defaultdict

from ruamel.yaml import YAML

PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[2]
V1_DIR = PROJECT_ROOT / "data" / "locations"
V2_FINAL_DIR = PROJECT_ROOT / "data" / "v2" / "final"
V2_SEED_UNIFIED_DIR = PROJECT_ROOT / "data" / "v2" / "seed_unified"


def load_v1_notes() -> dict[str, tuple[dict, str]]:
    """Return `{v1_coin_id → (note, v1_location_file)}` across all V1
    location yamls. References files (`*-references.yml`) are skipped.
    Entries without `note` are skipped.
    """
    yaml = YAML(typ="safe")
    out: dict[str, tuple[dict, str]] = {}
    for path in sorted(V1_DIR.glob("*.yml")):
        if path.stem.endswith("-references"):
            continue
        doc = yaml.load(path) or {}
        for c in doc.get("coins") or []:
            cid = c.get("id")
            note = c.get("note")
            if cid and note:
                # First-write wins. V1 location yamls don't share IDs in
                # practice, but if a duplicate appears we honour the
                # first read (alphabetical file order).
                out.setdefault(cid, (note, path.name))
    return out


def load_seed_unified_bridge() -> dict[str, str]:
    """Return `{v1_seed_id → unified_host_id}` from seed_unified
    composed_of lists. Used for strategy 4 of V1↔V2 matching when the
    V1 id no longer appears directly in V2 final's composed_of (typical
    after a cross-source merger consolidated multiple per-source seeds
    into a single unified entry).
    """
    yaml = YAML(typ="safe")
    out: dict[str, str] = {}
    if not V2_SEED_UNIFIED_DIR.exists():
        return out
    for path in sorted(V2_SEED_UNIFIED_DIR.glob("*.yml")):
        doc = yaml.load(path) or {}
        for u in doc.get("coins") or []:
            uid = u.get("id")
            if not uid:
                continue
            for member_id in u.get("composed_of") or []:
                # Only keep the FIRST mapping per v1_seed_id (a v1 id
                # shouldn't legitimately appear in multiple unified's
                # composed_of; if it does, the merger has a bug worth
                # surfacing separately).
                out.setdefault(member_id, uid)
    return out


def find_v1_match(v2_entry: dict, v1_notes: dict[str, tuple[dict, str]],
                   bridge: dict[str, str]) -> tuple[dict, str, str] | None:
    """Apply the four matching strategies in order. Return (note,
    v1_location_file, match_strategy) when a match is found, None otherwise.
    """
    v2_id = v2_entry.get("id") or ""
    if not v2_id:
        return None

    # Strategy 1: direct id match
    if v2_id in v1_notes:
        note, v1_file = v1_notes[v2_id]
        return (note, v1_file, "direct")

    # Strategy 2: unified-prefix match
    if v2_id.startswith("unified-"):
        candidate = v2_id[len("unified-"):]
        if candidate in v1_notes:
            note, v1_file = v1_notes[candidate]
            return (note, v1_file, "unified-prefix")

    # Strategy 3: composed_of match — walk V2's composed_of, see if any
    # member id has a V1 note. Self-references stripped first.
    composed = v2_entry.get("composed_of") or []
    for member_id in composed:
        if member_id == v2_id:
            continue
        if member_id in v1_notes:
            note, v1_file = v1_notes[member_id]
            return (note, v1_file, "composed-of")
        # Some composed_of members are unified-X form; check stripped
        if isinstance(member_id, str) and member_id.startswith("unified-"):
            stripped = member_id[len("unified-"):]
            if stripped in v1_notes:
                note, v1_file = v1_notes[stripped]
                return (note, v1_file, "composed-of-unified")

    # Strategy 4: seed_unified bridge — find any V1 id that maps to
    # this V2 entry's id via seed_unified composed_of.
    for v1_id, unified_host in bridge.items():
        # Match when bridge target is exactly v2_id, or v2_id stripped of
        # the unified- prefix matches the bridge target.
        if unified_host == v2_id and v1_id in v1_notes:
            note, v1_file = v1_notes[v1_id]
            return (note, v1_file, "seed-unified-bridge")

    return None


def restore_for_file(v2_path: pathlib.Path,
                      v1_notes: dict[str, tuple[dict, str]],
                      bridge: dict[str, str]) -> tuple[int, dict, "YAML"]:
    """Process one V2 final file. Returns (entries_touched, doc, yaml_obj).
    `doc` is None when no entries were touched (caller can skip write).
    """
    yaml = YAML()
    yaml.preserve_quotes = True
    yaml.width = 100000
    yaml.indent(mapping=2, sequence=4, offset=2)

    with open(v2_path) as f:
        doc = yaml.load(f)
    coins = doc.get("coins") or []

    entries_touched = 0
    per_strategy: Counter[str] = Counter()
    for c in coins:
        if c.get("note"):
            continue  # already has a note — skip
        match = find_v1_match(c, v1_notes, bridge)
        if not match:
            continue
        note, v1_file, strategy = match
        c["note"] = note
        # Provenance marker per CLAUDE.md «Manual-override preservation rule».
        # Use dict form (preferred for new edits) so the reason travels with
        # the data through every regen.
        holds = c.get("_curation_holds") or {}
        if not isinstance(holds, dict):
            # Legacy list-form — promote to dict, preserve existing entries
            holds = {k: None for k in holds}
        holds["note"] = (
            f"V1 backfill 2026-05-26 from {v1_file}::{c.get('id')} "
            f"(matched via {strategy}; V1→V2 bootstrap had dropped "
            f"the note field — see restore_v1_notes_to_v2_final.py)."
        )
        c["_curation_holds"] = holds
        entries_touched += 1
        per_strategy[strategy] += 1
    if entries_touched:
        # Print strategy breakdown so the curator can sanity-check
        # which matching paths fired.
        return entries_touched, doc, yaml, per_strategy
    return 0, None, yaml, per_strategy


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                  formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--apply", action="store_true",
                    help="Write changes back to V2 final yamls (default: dry-run)")
    ap.add_argument("--dry-run", action="store_true",
                    help="Report what WOULD change without writing")
    ap.add_argument("--entity", default=None,
                    help="Restrict to a single V2 entity file (e.g. royal_holstein)")
    args = ap.parse_args()

    if not args.apply and not args.dry_run:
        args.dry_run = True
    if args.apply and args.dry_run:
        print("ERROR: --apply and --dry-run are mutually exclusive", file=sys.stderr)
        return 2

    print("Loading V1 entries with notes...")
    v1_notes = load_v1_notes()
    print(f"  {len(v1_notes)} V1 entries have notes")
    print("Loading seed_unified bridge...")
    bridge = load_seed_unified_bridge()
    print(f"  {len(bridge)} seed_unified composed_of links")
    print()

    totals = Counter()
    grand_strategy: Counter[str] = Counter()
    paths = (
        [V2_FINAL_DIR / f"{args.entity}.yml"] if args.entity
        else sorted(V2_FINAL_DIR.glob("*.yml"))
    )

    for v2_path in paths:
        if not v2_path.exists():
            print(f"  ⚠️  {v2_path.name}: not found", file=sys.stderr)
            continue
        entries_touched, doc, yaml_obj, per_strategy = restore_for_file(
            v2_path, v1_notes, bridge)
        if entries_touched:
            strat_summary = ", ".join(
                f"{s}={n}" for s, n in per_strategy.most_common())
            print(f"  {v2_path.name:36s}  notes_backfilled:{entries_touched:4d}  "
                  f"[{strat_summary}]")
            totals["entries"] += entries_touched
            grand_strategy.update(per_strategy)
            if args.apply:
                with open(v2_path, "w") as f:
                    yaml_obj.dump(doc, f)

    print()
    print(f"Total entries backfilled: {totals['entries']}")
    if grand_strategy:
        print("Per match-strategy breakdown:")
        for s, n in grand_strategy.most_common():
            print(f"  {s:24s}  {n}")
    print()
    if args.dry_run:
        print("--- DRY RUN — no files written. Re-run with --apply to commit. ---")
    else:
        print(f"✓ Wrote backfilled V2 final yamls to {V2_FINAL_DIR}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
