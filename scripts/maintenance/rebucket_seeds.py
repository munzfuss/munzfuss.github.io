#!/usr/bin/env python3
"""rebucket_seeds.py — move seed entries to the bucket file their
`issuing_entity` demands.

THE DRIFT THIS FIXES. Every `data/v2/seed/<source>/<entity>.yml` is supposed
to hold exactly the coins whose home file — `_home_entity(coin)` — is
`<entity>`. `write_v2_seed` guarantees that AT BUILD TIME by grouping fresh
coins with `_home_entity` and purging stale-home entries. But the invariant
silently drifts between builds in two ways:

  * a curator edits `issuing_entity` in place in a seed file (with a
    `_curation_holds`) without re-running the source builder, so the file the
    entry sits in no longer matches its home; or
  * a mint-registry / entity split (e.g. `139df3f` split `royal_slesvig` out
    of `royal_holstein`, moving Husum/Haderslev) changes what `_home_entity`
    returns, while the already-written seed files keep the old bucket.

Either way the coin's SEED bucket ≠ `_home_entity(issuing_entity)`. The
cross-source merger buckets by the seed FILE, so a full re-flow writes the
coin into the wrong `seed_unified`/`final` and `audit_v2` I1 (home-file rule)
HARD-BLOCKS the commit — even though the HEAD finals (hand-relocated once)
look correct. This script re-aligns the seed layer so a full re-flow is
I1-clean without per-coin surgery, and `--check` in the pre-commit hook stops
the drift ever reaching a re-flow again.

WHAT IT DOES NOT DO. It never re-derives `issuing_entity` — it trusts the
value already in the seed (curator-frozen or mint-derived) and only moves the
ENTRY to `<source>/<home>.yml`. That is why it is safe where re-running a
builder is not: a `_curation_holds:[issuing_entity]` override (e.g. Christian
August's Lübeck-Bishopric coins classified by nation, not mint) is preserved
verbatim, with zero risk of the builder's nation-default clobbering it.

This is the standalone, all-source generalisation of `write_v2_seed`'s own
purge+regroup logic, keyed on `_home_entity(issuing_entity)` vs the file — as
opposed to `audit_entity_misclassifications.py`, which relocates only FROM
`danish_realm` and only by mint.

Usage:
    # Report drift, exit 1 if any (pre-commit guard mode):
    .venv/bin/python scripts/maintenance/rebucket_seeds.py --check

    # Move drifted entries to their home bucket files:
    .venv/bin/python scripts/maintenance/rebucket_seeds.py --apply

Idempotent: after --apply, --check exits 0. Cascade through the merger +
absorb is the caller's responsibility (session-end sequence:
`merge_seeds_cross_source.py --apply` then `absorb_seeds_into_final_v2.py
--apply`).
"""
from __future__ import annotations

import argparse
import sys
from collections import defaultdict
from pathlib import Path

import ruamel.yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from lib.v2_seed_writer import _home_entity  # noqa: E402
from lib.v2_resolver import ruamel_to_plain  # noqa: E402

V2_SEED_ROOT = PROJECT_ROOT / "data" / "v2" / "seed"


def _yaml() -> ruamel.yaml.YAML:
    """Round-trip YAML with the project's canonical seed-file settings
    (matches `write_v2_seed`)."""
    y = ruamel.yaml.YAML(typ="rt")
    y.preserve_quotes = True
    y.width = 200
    y.indent(mapping=2, sequence=4, offset=2)
    return y


def _scan() -> list[dict]:
    """Return drift records: entries whose `_home_entity` ≠ their file stem.

    Each record: {source, from_entity, to_entity, id, coin (ruamel node)}."""
    drift: list[dict] = []
    if not V2_SEED_ROOT.exists():
        return drift
    y = _yaml()
    for src_dir in sorted(V2_SEED_ROOT.iterdir()):
        if not src_dir.is_dir():
            continue
        for path in sorted(src_dir.glob("*.yml")):
            stem = path.stem
            if stem.startswith("_"):
                continue  # _unclassified / synthetic buckets
            doc = y.load(path.read_text(encoding="utf-8")) or {}
            for c in doc.get("coins") or []:
                if not isinstance(c, dict):
                    continue
                home = _home_entity(c)
                if home and home != stem:
                    drift.append({
                        "source": src_dir.name,
                        "from_entity": stem,
                        "to_entity": home,
                        "id": c.get("id"),
                    })
    return drift


def _clone_header(src_dir: Path, target_entity: str) -> dict:
    """Build a top-level header for a NEW `<src>/<target_entity>.yml` by
    cloning a sibling seed file's header (every top-level key except
    `coins`), overriding only `entity`. Never hardcodes header text."""
    y = _yaml()
    sibling = None
    for p in sorted(src_dir.glob("*.yml")):
        if not p.stem.startswith("_"):
            sibling = p
            break
    if sibling is None:
        raise SystemExit(f"  ✗ no sibling seed file in {src_dir} to clone header from")
    doc = y.load(sibling.read_text(encoding="utf-8")) or {}
    header = {k: v for k, v in doc.items() if k != "coins"}
    header = ruamel_to_plain(header)
    header["entity"] = target_entity
    return header


def _apply(drift: list[dict]) -> None:
    y = _yaml()
    # Group moves per source, and per (from_file → to_entity).
    by_source: dict[str, list[dict]] = defaultdict(list)
    for d in drift:
        by_source[d["source"]].append(d)

    for source, moves in sorted(by_source.items()):
        src_dir = V2_SEED_ROOT / source
        move_ids = {m["id"] for m in moves}
        to_by_id = {m["id"]: m["to_entity"] for m in moves}

        # 1. Pull the moved entries out of their source files, resolving
        #    aliases to plain values so they carry no dangling `*anchor`
        #    reference into the target file (the anchor stays defined in the
        #    source). Collect them grouped by destination entity.
        pulled: dict[str, list[dict]] = defaultdict(list)
        from_files = {m["from_entity"] for m in moves}
        for fe in sorted(from_files):
            fpath = src_dir / f"{fe}.yml"
            doc = y.load(fpath.read_text(encoding="utf-8")) or {}
            coins = doc.get("coins") or []
            kept = []
            for c in coins:
                cid = isinstance(c, dict) and c.get("id")
                if cid and cid in move_ids and to_by_id[cid] != fe:
                    pulled[to_by_id[cid]].append(ruamel_to_plain(c))
                else:
                    kept.append(c)
            doc["coins"] = kept
            with fpath.open("w", encoding="utf-8") as f:
                y.dump(doc, f)

        # 2. Append the pulled entries to their destination bucket files,
        #    creating a file (header cloned from a sibling) when absent.
        for te, entries in sorted(pulled.items()):
            tpath = src_dir / f"{te}.yml"
            if tpath.exists():
                doc = y.load(tpath.read_text(encoding="utf-8")) or {}
                if doc.get("coins") is None:
                    doc["coins"] = []
            else:
                doc = _clone_header(src_dir, te)
                doc["coins"] = []
            doc["coins"].extend(entries)
            with tpath.open("w", encoding="utf-8") as f:
                y.dump(doc, f)

        print(f"  [{source}] moved {len(moves)} entr{'y' if len(moves)==1 else 'ies'}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true",
                    help="Report drift and exit 1 if any (guard mode).")
    ap.add_argument("--apply", action="store_true",
                    help="Move drifted entries to their home bucket files.")
    args = ap.parse_args()

    drift = _scan()

    if not drift:
        print("✓ no seed-bucket drift — every seed entry sits in its "
              "_home_entity(issuing_entity) file.")
        return 0

    # Report (always).
    per = defaultdict(list)
    for d in drift:
        per[(d["from_entity"], d["to_entity"])].append(f"{d['source']}:{d['id']}")
    print(f"seed-bucket drift: {len(drift)} entr"
          f"{'y' if len(drift)==1 else 'ies'}")
    for (fe, te), ids in sorted(per.items()):
        print(f"  {fe} ⇒ {te}: {len(ids)}   {ids}")

    if args.apply:
        print("\napplying —")
        _apply(drift)
        # Re-scan to assert idempotency.
        if _scan():
            print("  ✗ drift remains after --apply (unexpected)")
            return 1
        print("✓ all drifted entries relocated; re-scan clean.")
        return 0

    if args.check:
        print("\n✗ seed-bucket drift present (guard). Run "
              "`rebucket_seeds.py --apply` before the next re-flow.")
        return 1

    print("\n(dry run — pass --apply to move, --check for guard exit code.)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
