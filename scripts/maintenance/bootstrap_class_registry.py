#!/usr/bin/env python3
"""One-off: create data/v2/class_registry/<entity>.yml from seed_unified (D49, stage 2).

One record per seed_unified class across every entity: `id` = opaque
`c-<8 hex>` (sha1 of the sorted specimen set — reproducible), `label` and
`legacy_id` = the class's current `unified-<head>` id, `members` = its seeds
plus every specimen a representative absorbed by §9a thinning
(`_thinned_from`), `created` = today, `status: active`. After this the merger
recognises its own partition as these records on every run
(`lib/class_registry.Registry.inherit`), so a merger run right after the
bootstrap must leave the registry byte-identical — that is the stage-2
acceptance test.

Reports, never hides: a specimen held by two records (two classes name the
same seed — possible across entities through a cross-entity pull), and the
counts. Dry-run by default.

    .venv/bin/python scripts/maintenance/bootstrap_class_registry.py          # report
    .venv/bin/python scripts/maintenance/bootstrap_class_registry.py --apply
"""
from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import yaml  # noqa: E402

from lib.class_registry import (REGISTRY_DIR, Record, Registry, make_id,  # noqa: E402
                                rep_to_dead_index, specimens_of)

V2 = ROOT / "data" / "v2"


def _coins(path: Path) -> list[dict]:
    d = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return [c for c in ((d.get("coins") if isinstance(d, dict) else d) or [])
            if isinstance(c, dict) and c.get("id")]


def build(today: str | None = None) -> tuple[Registry, dict[str, list[str]]]:
    today = today or date.today().isoformat()
    seeds: list[dict] = []
    for f in sorted((V2 / "seed").glob("*/*.yml")):
        seeds.extend(_coins(f))
    rep_dead = rep_to_dead_index(seeds)
    reg = Registry()
    taken: set[str] = set()
    for f in sorted((V2 / "seed_unified").glob("*.yml")):
        for c in _coins(f):
            spec = specimens_of([str(m) for m in (c.get("composed_of") or [])], rep_dead)
            rid = make_id(spec, taken)
            taken.add(rid)
            reg.records[rid] = Record(id=rid, entity=f.stem, members=sorted(spec),
                                      created=today, label=c["id"], legacy_id=c["id"])
    dup = {s: h for s, h in reg.holders().items() if len(h) > 1}
    return reg, dup


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    if REGISTRY_DIR.exists() and any(REGISTRY_DIR.glob("*.yml")) and args.apply:
        print(f"{REGISTRY_DIR} already has shards — the bootstrap is one-off; "
              "remove them deliberately first if you really mean to redo it.")
        return 2
    reg, dup = build()
    ents = sorted({r.entity for r in reg.records.values()})
    print(f"records: {len(reg.records)} across {len(ents)} entities; "
          f"specimens: {sum(len(r.members) for r in reg.records.values())}; "
          f"ids with a collision suffix: {sum('-' in r.id[2:] for r in reg.records.values())}")
    if dup:
        print(f"⚠ {len(dup)} specimen(s) held by two records (reported, kept):")
        for s, h in sorted(dup.items())[:20]:
            print(f"    {s}: {', '.join(reg.records[x].label or x for x in h)}")
        if len(dup) > 20:
            print(f"    … (+{len(dup) - 20})")
    if not args.apply:
        print("\n--- DRY RUN — nothing written. Re-run with --apply. ---")
        return 0
    written = reg.save(REGISTRY_DIR, entities=ents)
    print(f"✓ wrote {len(written)} shard(s) to {REGISTRY_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
