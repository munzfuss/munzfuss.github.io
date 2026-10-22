#!/usr/bin/env python3
"""One-off: final ids become class ids (V2_DECISIONS D49, stage 3).

For every coin in data/v2/final/<entity>.yml:
  * `composed_of` members that are unified names (`unified-<head>`) become the
    class ids the registry gave those classes (`legacy_id` → `id`); seed ids
    named directly stay as they are.
  * `id` becomes the HEAD class id (D49 addendum 1) for a pipeline-promoted
    final: the class it was promoted from (its own unified name) when that
    class is still among its members; otherwise the oldest `created`, tie →
    smallest id, among its member classes. A curated FOUNDATION (`km-…`,
    `hs-…`, a bare seed id) keeps its id permanently: the pipeline never
    renamed it, and an id equal to one of its member classes would read to
    absorb as a promoted entry's self-link (addendum 3 refined 2026-10-22).
  * `legacy_id` = the id the coin carried before (only when it changed),
    `label` = the old id (the human-readable name the render keeps using),
    `origin` = `promoted` for a `unified-…` final, `foundation` otherwise.
Two finals whose head would be the same class (split-duplicates sharing a
class) are reported; the second keeps its old id, so the schema's unique-id
rule holds and nothing is silently merged.

The same `legacy_id` → `id` map is applied to the two other files keyed by
final ids: data/v2/overmerge_purge_allowlist.yml (host ids and member unified
names) and classification_decisions coin_ids that still name a final id.

Dry-run by default. After --apply: merger --apply (writes seed_unified with
class ids) and absorb --apply twice; the second absorb must be a zero diff.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import yaml  # noqa: E402

from lib import yaml_io  # noqa: E402
from lib.class_registry import Registry  # noqa: E402

V2 = ROOT / "data" / "v2"
FINAL = V2 / "final"
ALLOWLIST = V2 / "overmerge_purge_allowlist.yml"
CLS_DIR = V2 / "classification_decisions"


def legacy_map(reg: Registry) -> dict[str, str]:
    """{unified name → class id} from the registry's label / legacy_id."""
    out: dict[str, str] = {}
    for r in reg.records.values():
        for k in (r.legacy_id, r.label):
            if k:
                out.setdefault(k, r.id)
    return out


def migrate_entity(path: Path, reg: Registry, lmap: dict[str, str],
                   report: list[str]) -> tuple[dict[str, str], int]:
    """Rewrite one final file in memory. Returns ({old final id → new id}, n)."""
    ctx, doc = yaml_io.load(path)
    coins = doc.get("coins") or []
    taken: set[str] = set()
    id_map: dict[str, str] = {}
    # first pass: new composed_of + candidate head per coin
    plans = []
    for c in coins:
        if not isinstance(c, dict) or not c.get("id"):
            plans.append(None)
            continue
        old = str(c["id"])
        comp = [str(m) for m in (c.get("composed_of") or [])]
        new_comp = [lmap.get(m, m) for m in comp]
        classes = [m for m in new_comp if m in reg.records]
        own = lmap.get(old)
        if own and (own in classes or not classes):
            head = own
        elif classes and old.startswith("unified-"):
            head = min(classes, key=lambda cid: (reg.records[cid].created, cid))
        else:
            # A curated foundation (`km-…`, `hs-…`, a bare seed id) keeps its
            # id: it is curator-owned, the pipeline never renamed it, and an
            # id equal to one of its MEMBER classes would read to absorb as
            # the self-link of a promoted entry (measured 2026-10-22: the
            # member's readings fused with the foundation's own).
            head = old
        plans.append((old, new_comp, head))
    for c, plan in zip(coins, plans):
        if plan is None:
            continue
        old, new_comp, head = plan
        if head != old and head in taken:
            report.append(f"[{path.stem}] {old}: head class {head} already names "
                          f"another final — kept the old id")
            head = old
        taken.add(head)
        id_map[old] = head
        promoted = old.startswith("unified-")
        # rebuild in a stable key order: id, label, legacy_id, origin first
        rest = {k: v for k, v in c.items() if k not in ("id", "label", "legacy_id", "origin")}
        new = {"id": head, "label": old}
        if head != old:
            new["legacy_id"] = old
        new["origin"] = "promoted" if promoted else "foundation"
        new.update(rest)
        if new_comp != [str(m) for m in (c.get("composed_of") or [])]:
            new["composed_of"] = new_comp
        c.clear()
        c.update(new)
    return id_map, ctx, doc


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    reg = Registry.load_all()
    if not reg.records:
        print("no class registry — run bootstrap_class_registry.py first")
        return 2
    lmap = legacy_map(reg)
    report: list[str] = []
    stats = {"finals": 0, "id_changed": 0, "promoted": 0, "foundation": 0,
             "foundation_with_classes": 0, "no_class": 0}
    writes = []
    final_map: dict[str, str] = {}
    for path in sorted(FINAL.glob("*.yml")):
        id_map, ctx, doc = migrate_entity(path, reg, lmap, report)
        for c in doc.get("coins") or []:
            if not isinstance(c, dict) or not c.get("id"):
                continue
            stats["finals"] += 1
            stats[c["origin"]] += 1
            if c.get("legacy_id"):
                stats["id_changed"] += 1
            if c["origin"] == "foundation" and any(m in reg.records for m in (c.get("composed_of") or [])):
                stats["foundation_with_classes"] += 1
            if not any(m in reg.records for m in (c.get("composed_of") or [])):
                stats["no_class"] += 1
        final_map.update(id_map)
        writes.append((ctx, path, doc))
    # overmerge allowlist: host ids + member names
    allow_changes = 0
    if ALLOWLIST.exists():
        actx, adoc = yaml_io.load(ALLOWLIST)
        new_doc = {}
        for host, members in (adoc or {}).items():
            nh = final_map.get(str(host), str(host))
            nm = [lmap.get(str(m), str(m)) for m in (members or [])]
            allow_changes += (nh != host) + sum(a != b for a, b in zip(nm, members or []))
            new_doc[nh] = nm
        writes.append((actx, ALLOWLIST, new_doc))
    # classification decisions still keyed by a final id (a SEED key — the
    # stable form since stage 1 — is never touched, even when a final of the
    # same name changed its id)
    seed_ids: set[str] = set()
    for sf in (V2 / "seed").glob("*/*.yml"):
        for c in (yaml.safe_load(sf.read_text(encoding="utf-8")) or {}).get("coins") or []:
            if isinstance(c, dict) and c.get("id"):
                seed_ids.add(str(c["id"]))
    cls_changes = 0
    for path in sorted(CLS_DIR.glob("*.yml")):
        cctx, cdoc = yaml_io.load(path)
        changed = False
        for a in (cdoc.get("assignments") or []):
            k = str(a.get("coin_id") or "")
            if k in seed_ids or k in lmap:
                continue
            if k in final_map and final_map[k] != k:
                a["was"] = k
                a["coin_id"] = final_map[k]
                changed = True
                cls_changes += 1
        if changed:
            writes.append((cctx, path, cdoc))
    for k, v in stats.items():
        print(f"{k:24s} {v}")
    print(f"allowlist edits          {allow_changes}")
    print(f"decision keys re-keyed   {cls_changes}")
    print(f"reported                 {len(report)}")
    for ln in report:
        print(f"    {ln}")
    if not args.apply:
        print("\n--- DRY RUN — nothing written. Re-run with --apply. ---")
        return 0
    for ctx, path, doc in writes:
        yaml_io.save(ctx, path, doc)
    print(f"\n✓ wrote {len(writes)} file(s); now merger --apply, then absorb --apply twice")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
