#!/usr/bin/env python3
"""cleanup_orphan_finals.py — remove stale V1-bootstrap final entries
whose seed-cluster moved or never materialised, and whose data is
already preserved in a twin entry.

Background
----------
V2 final tier (`data/v2/final/<entity>.yml`) contains coin entries
assembled by the absorb pipeline. Each entry SHOULD carry a non-empty
`composed_of: [<seed_unified_id>, ...]` pointing to its seed-cluster.

V1 → V2 bootstrap (2026-05-18) created stub entries in V2 final from
V1 location yamls with only catalog refs + ruler/year + fuss/phase
classification. As the absorb pipeline iterated and the entity
classifier refined entity assignment, many stub entries were left
behind when their underlying seed-cluster:
  a) migrated to a different entity (e.g. ucoin tid moved from
     danish_realm to royal_holstein because the mint is Glückstadt);
  b) was consumed into a new unified-cluster with a different id;
  c) never had a matching seed (manual V1 curation only).

The audit (2026-05-25) found 422 such orphans (composed_of: [] / None)
out of 3043 final entries — 14%. Triage:

  T1 same-entity twin    77  Duplicate WITHIN the same entity
  T2 cross-entity twin   190 Twin lives in a different entity
  T3 no twin found       155 Genuinely V1-only data (most have sources)

This script handles the safe-deletion subset:
  - T1+T2 high+medium confidence WHERE orphan.fuss == twin.fuss AND
    orphan.phase == twin.phase (no classification info loss);
  - Empty T3 entries (no sources/weight/fineness/note — pure stubs).

Skips:
  - T1+T2 low confidence (shared_refs = 1 only, risk of mis-merge);
  - T3 with any data (legitimate V1-only entries — preserved);
  - T1+T2 where orphan and twin have different fuss/phase (classification
    conflict — needs curator decision).

Decisions are logged to `data/v2/orphan_cleanup_log.yml` for audit.

Usage
-----
    .venv/bin/python scripts/maintenance/cleanup_orphan_finals.py --dry-run
    .venv/bin/python scripts/maintenance/cleanup_orphan_finals.py --apply

Idempotent — re-runs after --apply produce no further changes.
"""
from __future__ import annotations

import argparse
import pathlib
import sys
from collections import defaultdict
from datetime import datetime, timezone

from ruamel.yaml import YAML

PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[2]
FINAL_DIR = PROJECT_ROOT / "data" / "v2" / "final"
LOG_PATH = PROJECT_ROOT / "data" / "v2" / "orphan_cleanup_log.yml"

# Catalog-key canonical synonyms (mirrors merge_seeds_cross_source.py
# _catalog_refs logic).
KEY_SYNONYMS = {"friedberg": "fr", "davenport": "dav"}
CATALOG_FIELDS = (
    "km", "hede", "sieg", "schou", "lange", "fr", "dav", "numista",
    "bruun_collection_id", "jensen_skjoldager", "schive", "mb",
    "skaare", "galster", "friedberg", "davenport", "nmd", "skjoldager",
)


def coin_refs(coin: dict) -> dict[str, set[str]]:
    """Return {canonical_catalog_key: set(values)} for a coin's catalog
    dict. Mirrors merger's _catalog_refs but emits set-of-values for
    easier intersection."""
    cat = coin.get("catalog") or {}
    out: dict[str, set[str]] = defaultdict(set)
    for k in CATALOG_FIELDS:
        v = cat.get(k)
        if v is None:
            continue
        canonical = KEY_SYNONYMS.get(k, k)
        if isinstance(v, list):
            for x in v:
                out[canonical].add(str(x).strip())
        else:
            out[canonical].add(str(v).strip())
    return dict(out)


def shared_ref_count(a_refs: dict, b_refs: dict) -> int:
    """Count catalog keys where a and b share AT LEAST ONE value."""
    shared = 0
    for k in a_refs:
        if k in b_refs and (a_refs[k] & b_refs[k]):
            shared += 1
    return shared


def confidence_tier(shared: int, year_match: bool, ruler_match: bool) -> str:
    """Same scoring rule the diagnostic phase used."""
    if year_match and ruler_match and shared >= 2:
        return "high"
    if shared >= 1 and (year_match or ruler_match):
        return "medium"
    return "low"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0],
                                  formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--apply", action="store_true",
                    help="Write changes back to final yamls (default: dry-run)")
    ap.add_argument("--dry-run", action="store_true",
                    help="Report what WOULD change without writing")
    ap.add_argument("--include-low", action="store_true",
                    help="ALSO process low-confidence pairs (shared_refs=1, "
                         "no year/ruler agreement). Default: skip.")
    args = ap.parse_args()

    if not args.apply and not args.dry_run:
        args.dry_run = True
    if args.apply and args.dry_run:
        print("ERROR: --apply and --dry-run are mutually exclusive", file=sys.stderr)
        return 2

    yaml = YAML()
    yaml.preserve_quotes = True
    yaml.width = 100000
    yaml.indent(mapping=2, sequence=4, offset=2)

    # Load all final entries
    print(f"Loading {FINAL_DIR}...")
    all_finals: dict[str, list[dict]] = {}
    docs: dict[str, dict] = {}  # entity → full doc for write-back
    for p in sorted(FINAL_DIR.glob("*.yml")):
        with open(p) as f:
            doc = yaml.load(f)
        docs[p.stem] = doc
        all_finals[p.stem] = doc.get("coins") or []

    # Build reverse index: (catalog_key, value) → [(entity, coin)]
    ref_index = defaultdict(list)
    for entity, coins in all_finals.items():
        for c in coins:
            refs = coin_refs(c)
            for k, vs in refs.items():
                for v in vs:
                    ref_index[(k, v)].append((entity, c))

    # Identify orphans + their twins
    actions = []  # list of dicts: action, orph_entity, orph_id, twin_*, reason
    for entity, coins in all_finals.items():
        for c in coins:
            comp = c.get("composed_of")
            if comp and comp != []:
                continue
            # This is an orphan
            o_refs = coin_refs(c)
            o_year = c.get("year_first")
            o_ruler = (c.get("ruler") or "").lower().strip()
            o_fuss = c.get("fuss")
            o_phase = c.get("phase")

            # Find best twin
            twin_scores: dict[tuple[str, str], int] = {}
            for k, vs in o_refs.items():
                for v in vs:
                    for (twin_ent, twin_c) in ref_index.get((k, v), []):
                        if twin_c is c:
                            continue
                        twin_comp = twin_c.get("composed_of") or []
                        if not twin_comp:
                            continue  # twin also orphan
                        key = (twin_ent, twin_c.get("id"))
                        if key not in twin_scores:
                            t_refs = coin_refs(twin_c)
                            twin_scores[key] = shared_ref_count(o_refs, t_refs)

            # Determine action
            if not twin_scores:
                # T3 no-twin: check whether truly empty
                if not any([c.get("weight_rough_g"), c.get("fineness"),
                            c.get("sources"), c.get("diameter_mm"), c.get("note")]):
                    actions.append({
                        "action": "DELETE",
                        "reason": "T3_empty_stub",
                        "orph_entity": entity,
                        "orph_id": c.get("id"),
                        "twin_entity": None,
                        "twin_id": None,
                        "confidence": None,
                        "shared_refs": 0,
                        "nominal": c.get("nominal"),
                        "year_first": o_year,
                        "fuss": o_fuss, "phase": o_phase,
                    })
                else:
                    actions.append({
                        "action": "SKIP_PRESERVE_V1_DATA",
                        "reason": "T3_has_sources_or_notes",
                        "orph_entity": entity,
                        "orph_id": c.get("id"),
                        "twin_entity": None,
                        "twin_id": None,
                        "confidence": None,
                        "shared_refs": 0,
                        "nominal": c.get("nominal"),
                        "year_first": o_year,
                        "fuss": o_fuss, "phase": o_phase,
                    })
                continue

            # Best twin
            best = max(twin_scores.items(), key=lambda x: x[1])
            twin_ent, twin_id = best[0]
            shared = best[1]
            twin_c = next(tc for e, tc in [(twin_ent, tc) for tc in all_finals[twin_ent]
                                            if tc.get("id") == twin_id])
            t_year = twin_c.get("year_first")
            t_ruler = (twin_c.get("ruler") or "").lower().strip()
            t_fuss = twin_c.get("fuss")
            t_phase = twin_c.get("phase")

            year_match = (t_year == o_year) or (t_year and o_year and abs(t_year - o_year) <= 2)
            ruler_match = (o_ruler == t_ruler) or not o_ruler or not t_ruler
            conf = confidence_tier(shared, year_match, ruler_match)
            tier = "T1" if twin_ent == entity else "T2"

            # Safety gate — four cases:
            # (1) exact match → safe DELETE (orphan info redundant)
            # (2) orphan seed_unsorted, twin concrete → safe DELETE (twin
            #     classification is the better signal anyway)
            # (3) orphan concrete, twin seed_unsorted → PROPAGATE orphan's
            #     fuss/phase to twin, then DELETE orphan
            # (4) both concrete but differ → SKIP_CLASSIFICATION_CONFLICT
            classification_match = (o_fuss == t_fuss) and (o_phase == t_phase)
            orph_unclassified = (o_fuss == "seed_unsorted")
            twin_unclassified = (t_fuss == "seed_unsorted")
            propagate_classification = False

            if conf == "low" and not args.include_low:
                action = "SKIP_LOW_CONFIDENCE"
                reason = f"{tier}_shared={shared}_year={year_match}_ruler={ruler_match}"
            elif classification_match:
                action = "DELETE"
                reason = f"{tier}_{conf}_redundant"
            elif orph_unclassified and not twin_unclassified:
                # Twin has better classification — safe to delete orphan
                action = "DELETE"
                reason = f"{tier}_{conf}_orphan_unclassified"
            elif not orph_unclassified and twin_unclassified:
                # Orphan has better classification — propagate to twin then delete
                action = "PROPAGATE_AND_DELETE"
                reason = f"{tier}_{conf}_promote_orphan_classification"
                propagate_classification = True
            else:
                # Both concrete but classifications differ — curator decision
                action = "SKIP_CLASSIFICATION_CONFLICT"
                reason = (f"{tier}_{conf}_fuss_{o_fuss}_vs_{t_fuss}_phase_{o_phase}_vs_{t_phase}")

            actions.append({
                "action": action,
                "reason": reason,
                "orph_entity": entity,
                "orph_id": c.get("id"),
                "twin_entity": twin_ent,
                "twin_id": twin_id,
                "confidence": conf,
                "shared_refs": shared,
                "nominal": c.get("nominal"),
                "year_first": o_year,
                "fuss": o_fuss, "phase": o_phase,
                "twin_fuss": t_fuss, "twin_phase": t_phase,
                "propagate_classification": propagate_classification,
            })

    # Report + apply
    from collections import Counter
    action_count = Counter(a["action"] for a in actions)
    reason_count = Counter(a["reason"] for a in actions)
    print(f"\n=== Audit summary ===")
    for k, v in action_count.most_common():
        print(f"  {k:35} {v}")
    print(f"\n=== Top reasons ===")
    for k, v in reason_count.most_common(15):
        print(f"  {k:60} {v}")

    # Apply propagate-and-delete first (writes twin's fuss/phase BEFORE
    # orphan is dropped, so the orphan's classification info survives).
    propagates = [a for a in actions if a["action"] == "PROPAGATE_AND_DELETE"]
    if args.apply and propagates:
        print(f"\n=== Applying {len(propagates)} classification propagations ===")
        # Build index: (entity, twin_id) → list of pending (twin_c, new_fuss, new_phase)
        for a in propagates:
            twin_ent = a["twin_entity"]
            twin_id = a["twin_id"]
            new_fuss = a["fuss"]
            new_phase = a["phase"]
            for c in docs[twin_ent].get("coins") or []:
                if c.get("id") == twin_id:
                    c["fuss"] = new_fuss
                    c["phase"] = new_phase
                    break
        # Write back affected entities
        touched = {a["twin_entity"] for a in propagates}
        for entity in touched:
            path = FINAL_DIR / f"{entity}.yml"
            with open(path, "w") as f:
                yaml.dump(docs[entity], f)
            print(f"  propagated classifications into {entity}.yml")

    # Apply deletes (both straight DELETE and PROPAGATE_AND_DELETE drop the orphan)
    deletes = [a for a in actions
               if a["action"] in ("DELETE", "PROPAGATE_AND_DELETE")]
    if args.apply and deletes:
        print(f"\n=== Applying {len(deletes)} deletes ===")
        by_entity = defaultdict(list)
        for d in deletes:
            by_entity[d["orph_entity"]].append(d["orph_id"])
        for entity, drop_ids in by_entity.items():
            drop_set = set(drop_ids)
            doc = docs[entity]
            coins = doc.get("coins") or []
            kept = [c for c in coins if c.get("id") not in drop_set]
            doc["coins"] = kept
            path = FINAL_DIR / f"{entity}.yml"
            with open(path, "w") as f:
                yaml.dump(doc, f)
            print(f"  {entity:35} {len(coins)} → {len(kept)}  (−{len(coins)-len(kept)})")

    # Write log
    if args.apply or args.dry_run:
        log = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "mode": "apply" if args.apply else "dry-run",
            "summary": dict(action_count),
            "actions": actions,
        }
        if args.apply:
            with open(LOG_PATH, "w") as f:
                yaml.dump(log, f)
            print(f"\n→ log written to {LOG_PATH}")
        else:
            print(f"\n--- DRY RUN — no files written. Re-run with --apply to commit. ---")

    return 0


if __name__ == "__main__":
    sys.exit(main())
