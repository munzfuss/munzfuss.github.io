#!/usr/bin/env python3
"""V2 invariants audit — hard-block on pre-commit per D26.

Verifies the V2 pipeline's structural invariants before allowing
a commit:

  I1. **Home-file rule** (D5 / D2): every coin in
      `data/v2/final/<entity>.yml` and `data/v2/seed_unified/<entity>.yml`
      has `issuing_entity` whose alphabetically-first element
      matches the filename. Multi-entity list-form must list all
      tags as known entities.

  I2. **Bidirectional link integrity** (D9): every `promoted_to` on
      a seed entry points to a final/unified entry that exists AND
      includes the seed id in its `composed_of`. Every `composed_of`
      entry must resolve to an existing seed/unified entry (no
      dangling refs).

  I3. **Cross-entity duplicate detection**: no coin id appears in
      ≥2 final entity files (home-file rule violation).

  I4. **Schema validation**: every V2 final / seed_unified coin
      passes `Coin` pydantic validation after stripping V2 migration
      breadcrumbs.

  I5. **Active-entity tag membership**: every `issuing_entity` (and
      every element of list-form) refers to a tag defined in
      `data/i18n/issuing_entities.yml`.

  I6. **Decision file integrity**: every `merges` / `no_merges`
      member in `data/v2/merge_decisions/<entity>.yml` resolves to
      a real seed id. Every `assignments` coin_id in
      `classification_decisions/<entity>.yml` resolves to a real
      unified id.

Exit codes:
  0 — all invariants pass (commit OK)
  1 — one or more invariants violated (commit blocked when called
      from pre-commit hook)

Usage:
  scripts/audit_v2.py                   # all invariants
  scripts/audit_v2.py --quick           # I1-I3 only (fast)
  scripts/audit_v2.py --json report.json
  scripts/audit_v2.py --no-fail         # report but exit 0 (for
                                          advisory mode during
                                          transition)
"""

from __future__ import annotations

import argparse
import json
import sys
import warnings
from collections import defaultdict
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
V2_FINAL = ROOT / "data" / "v2" / "final"
V2_SEED_UNIFIED = ROOT / "data" / "v2" / "seed_unified"
V2_SEED = ROOT / "data" / "v2" / "seed"
V2_LOCATIONS = ROOT / "data" / "v2" / "locations"
V2_MERGE_DECISIONS = ROOT / "data" / "v2" / "merge_decisions"
V2_CLASSIFICATION_DECISIONS = ROOT / "data" / "v2" / "classification_decisions"
I18N_ENTITIES = ROOT / "data" / "i18n" / "issuing_entities.yml"


def _load_yaml(p: Path) -> dict:
    if not p.exists():
        return {}
    return yaml.safe_load(p.read_text(encoding="utf-8")) or {}


def _all_v2_final_coins() -> list[tuple[str, dict]]:
    """[(entity_id, coin_dict), ...]"""
    out = []
    if not V2_FINAL.exists():
        return out
    for p in sorted(V2_FINAL.glob("*.yml")):
        d = _load_yaml(p)
        for c in d.get("coins") or []:
            out.append((p.stem, c))
    return out


def _all_v2_unified_coins() -> list[tuple[str, dict]]:
    out = []
    if not V2_SEED_UNIFIED.exists():
        return out
    for p in sorted(V2_SEED_UNIFIED.glob("*.yml")):
        d = _load_yaml(p)
        for c in d.get("coins") or []:
            out.append((p.stem, c))
    return out


def _all_v2_seed_coins() -> list[tuple[str, str, dict]]:
    """[(source, entity_id, coin_dict), ...]"""
    out = []
    if not V2_SEED.exists():
        return out
    for src_dir in sorted(V2_SEED.iterdir()):
        if not src_dir.is_dir():
            continue
        for p in sorted(src_dir.glob("*.yml")):
            d = _load_yaml(p)
            for c in d.get("coins") or []:
                out.append((src_dir.name, p.stem, c))
    return out


# ---------------------------------------------------------------------------
# Invariant checks
# ---------------------------------------------------------------------------


def check_i1_home_file(coins: list[tuple[str, dict]], known_entities: set[str]
                       ) -> list[str]:
    """I1 — home-file rule. Every coin in <entity>.yml has issuing_entity
    whose alphabetically-first element = filename stem."""
    errors: list[str] = []
    for entity_id, c in coins:
        if entity_id.startswith("_"):
            continue  # synthetic buckets (_unclassified, _deprecated_*) skip
        ie = c.get("issuing_entity")
        if ie is None:
            errors.append(
                f"I1: coin {c.get('id')!r} in {entity_id}.yml has no issuing_entity"
            )
            continue
        if isinstance(ie, list):
            if not ie:
                errors.append(
                    f"I1: coin {c.get('id')!r} in {entity_id}.yml has empty "
                    f"issuing_entity list"
                )
                continue
            first = sorted(ie)[0]
            if first != entity_id:
                errors.append(
                    f"I1: coin {c.get('id')!r} in {entity_id}.yml has list-form "
                    f"issuing_entity {ie} — alphabetical-first is {first!r}, "
                    f"home file should be {first}.yml"
                )
        else:
            if ie != entity_id:
                errors.append(
                    f"I1: coin {c.get('id')!r} in {entity_id}.yml has scalar "
                    f"issuing_entity {ie!r} — home file should be {ie}.yml"
                )
    return errors


def check_i2_bidirectional(final_coins: list[tuple[str, dict]],
                            unified_coins: list[tuple[str, dict]],
                            seed_coins: list[tuple[str, str, dict]]
                            ) -> list[str]:
    """I2 — bidirectional link integrity. composed_of refs resolve;
    promoted_to refs resolve + reciprocate. Final entries must have a
    non-empty composed_of (V1-bootstrap orphan prevention)."""
    errors: list[str] = []
    final_by_id = {c["id"]: c for _, c in final_coins if c.get("id")}
    unified_by_id = {c["id"]: c for _, c in unified_coins if c.get("id")}
    seed_by_id = {c["id"]: c for _, _, c in seed_coins if c.get("id")}

    # I2a — orphan-baseline check. Every final entry SHOULD reference at
    # least one seed/unified id. Empty composed_of typically indicates a
    # V1-bootstrap stub whose seed-cluster migrated or was consumed —
    # such entries render with no sources/weight on display tables.
    #
    # The 2026-05-25 cleanup (`cleanup_orphan_finals.py`) reclaimed 140
    # safe-delete cases; the residual 282 are legitimately preserved:
    #   - ≈152 are T3 entries with V1-curated sources (no other source
    #     attests them)
    #   - ≈89 are low-confidence twin candidates (curator review queue)
    #   - ≈41 are classification-conflict pairs (curator decision queue)
    #
    # I2a is therefore a soft check — it reports the current count but
    # only HARD-BLOCKS if the count exceeds a baseline. Baseline grows
    # only by explicit bump after a curator review pass.
    I2A_BASELINE = 250
    orphan_count = 0
    for _, fc in final_coins:
        composed = fc.get("composed_of")
        if composed == [] or composed is None:
            orphan_count += 1
    if orphan_count > I2A_BASELINE:
        errors.append(
            f"I2a: final-orphan count regressed: {orphan_count} > baseline "
            f"{I2A_BASELINE}. Either run `cleanup_orphan_finals.py --apply` "
            f"to reclaim new orphans, or bump I2A_BASELINE in audit_v2.py "
            f"after a curator review."
        )

    # composed_of must resolve to seed or unified id
    for _, fc in final_coins:
        fid = fc.get("id")
        for cid in fc.get("composed_of") or []:
            if cid not in unified_by_id and cid not in seed_by_id and cid not in final_by_id:
                errors.append(
                    f"I2: final {fid!r} composed_of references unknown id {cid!r}"
                )
    for _, uc in unified_coins:
        uid = uc.get("id")
        for cid in uc.get("composed_of") or []:
            if cid not in seed_by_id and cid not in unified_by_id:
                errors.append(
                    f"I2: unified {uid!r} composed_of references unknown id {cid!r}"
                )

    # promoted_to must point at a real final/unified id AND that host must
    # mention the seed in its composed_of (reciprocal)
    for _, _, sc in seed_coins:
        sid = sc.get("id")
        pt = sc.get("promoted_to")
        if pt is None:
            continue
        host = unified_by_id.get(pt) or final_by_id.get(pt)
        if host is None:
            errors.append(
                f"I2: seed {sid!r} promoted_to {pt!r} — host not found in "
                f"unified or final"
            )
            continue
        host_composed = host.get("composed_of") or []
        if sid not in host_composed:
            errors.append(
                f"I2: seed {sid!r} promoted_to {pt!r}, but host's composed_of "
                f"does NOT include {sid!r} (one-sided link)"
            )

    return errors


def check_i3_cross_entity_dup(final_coins: list[tuple[str, dict]]
                               ) -> list[str]:
    """I3 — no coin id in ≥2 final entity files."""
    errors: list[str] = []
    seen: dict[str, str] = {}  # id → first-entity-seen
    for entity_id, c in final_coins:
        cid = c.get("id")
        if not cid:
            continue
        if cid in seen:
            errors.append(
                f"I3: coin id {cid!r} appears in BOTH {seen[cid]}.yml AND "
                f"{entity_id}.yml — home-file rule violation"
            )
        else:
            seen[cid] = entity_id
    return errors


def check_i4_schema(final_coins: list[tuple[str, dict]],
                     unified_coins: list[tuple[str, dict]]
                     ) -> list[str]:
    """I4 — pydantic Coin validation after stripping V2 breadcrumbs."""
    warnings.filterwarnings("ignore")
    sys.path.insert(0, str(ROOT / "scripts"))
    try:
        from lib.schema import Coin
        from lib.v2_resolver import strip_v2_breadcrumbs
    except ImportError as e:
        return [f"I4: cannot import Coin schema: {e}"]

    errors: list[str] = []
    n_checked = 0
    for entity_id, c in final_coins + unified_coins:
        cid = c.get("id", "?")
        c_clean = strip_v2_breadcrumbs(c)
        # Strip private fields
        c_clean = {k: v for k, v in c_clean.items() if not k.startswith("_")}
        try:
            Coin(**c_clean)
            n_checked += 1
        except Exception as e:
            errors.append(
                f"I4: schema validation failed for {entity_id}/{cid}: "
                f"{type(e).__name__}: {str(e)[:160]}"
            )
            if len(errors) >= 50:
                errors.append(f"I4: ... (truncated, {len(final_coins) + len(unified_coins) - n_checked} more)")
                break
    return errors


def check_i5_entity_tags(coins: list[tuple[str, dict]],
                          known_entities: set[str]
                          ) -> list[str]:
    """I5 — every issuing_entity tag exists in data/i18n/issuing_entities.yml."""
    errors: list[str] = []
    for entity_id, c in coins:
        ie = c.get("issuing_entity")
        if ie is None:
            continue
        tags = ie if isinstance(ie, list) else [ie]
        for tag in tags:
            if tag.startswith("_"):
                continue  # synthetic (e.g. _deprecated_gesamtstaat) tolerated
            if tag not in known_entities:
                errors.append(
                    f"I5: coin {c.get('id')!r} in {entity_id}.yml has "
                    f"issuing_entity {tag!r} not in i18n/issuing_entities.yml"
                )
    return errors


def check_i6_decision_refs(unified_coins: list[tuple[str, dict]],
                            seed_coins: list[tuple[str, str, dict]]
                            ) -> list[str]:
    """I6 — merge_decisions members + classification_decisions coin_ids
    resolve to real seed / unified entries."""
    errors: list[str] = []
    seed_ids = {c["id"] for _, _, c in seed_coins if c.get("id")}
    unified_ids = {c["id"] for _, c in unified_coins if c.get("id")}

    if V2_MERGE_DECISIONS.exists():
        for p in V2_MERGE_DECISIONS.glob("*.yml"):
            d = _load_yaml(p)
            for entry in (d.get("merges") or []) + (d.get("no_merges") or []):
                for mid in entry.get("members") or []:
                    if mid not in seed_ids and mid not in unified_ids:
                        errors.append(
                            f"I6: merge_decisions/{p.stem}.yml references "
                            f"unknown id {mid!r}"
                        )

    if V2_CLASSIFICATION_DECISIONS.exists():
        for p in V2_CLASSIFICATION_DECISIONS.glob("*.yml"):
            d = _load_yaml(p)
            for entry in d.get("assignments") or []:
                cid = entry.get("coin_id")
                if cid and cid not in unified_ids and cid not in seed_ids:
                    errors.append(
                        f"I6: classification_decisions/{p.stem}.yml::assignments "
                        f"references unknown coin_id {cid!r}"
                    )
    return errors


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--quick", action="store_true",
                        help="Skip slow checks (I4 schema, I6 decision refs)")
    parser.add_argument("--no-fail", action="store_true",
                        help="Report only — exit 0 even on violations "
                             "(advisory mode during transition)")
    parser.add_argument("--json", type=Path, default=None)
    args = parser.parse_args()

    print("V2 invariants audit (per D26 — hard-block on pre-commit)\n")

    if not V2_FINAL.exists():
        print("data/v2/final/ not found — V2 pipeline not initialised. Pass.")
        return 0

    final_coins = _all_v2_final_coins()
    unified_coins = _all_v2_unified_coins()
    seed_coins = _all_v2_seed_coins()
    known_entities = set(_load_yaml(I18N_ENTITIES).keys())

    print(f"Inputs:")
    print(f"  V2 final coins:    {len(final_coins)}")
    print(f"  V2 unified coins:  {len(unified_coins)}")
    print(f"  V2 seed coins:     {len(seed_coins)}")
    print(f"  Known entity tags: {len(known_entities)}")
    print()

    results: dict[str, list[str]] = {}

    print("Running I1 (home-file rule)...")
    results["I1"] = check_i1_home_file(final_coins + unified_coins, known_entities)
    print(f"  {len(results['I1'])} violation(s)")

    print("Running I2 (bidirectional link integrity)...")
    results["I2"] = check_i2_bidirectional(final_coins, unified_coins, seed_coins)
    print(f"  {len(results['I2'])} violation(s)")

    print("Running I3 (cross-entity duplicate detection)...")
    results["I3"] = check_i3_cross_entity_dup(final_coins)
    print(f"  {len(results['I3'])} violation(s)")

    if not args.quick:
        print("Running I4 (schema validation)...")
        results["I4"] = check_i4_schema(final_coins, unified_coins)
        print(f"  {len(results['I4'])} violation(s)")
    else:
        results["I4"] = []
        print("Skipping I4 (--quick mode)")

    print("Running I5 (issuing_entity tag membership)...")
    results["I5"] = check_i5_entity_tags(final_coins + unified_coins, known_entities)
    print(f"  {len(results['I5'])} violation(s)")

    if not args.quick:
        print("Running I6 (decision file refs)...")
        results["I6"] = check_i6_decision_refs(unified_coins, seed_coins)
        print(f"  {len(results['I6'])} violation(s)")
    else:
        results["I6"] = []
        print("Skipping I6 (--quick mode)")

    total = sum(len(v) for v in results.values())
    print()
    print(f"=== Total violations: {total} ===")

    if args.json:
        args.json.write_text(json.dumps(results, ensure_ascii=False, indent=2))
        print(f"\nJSON report → {args.json}")

    if total == 0:
        print("✓ All V2 invariants pass.")
        return 0

    # Show details
    for invariant, errors in results.items():
        if not errors:
            continue
        print(f"\n--- {invariant} ({len(errors)} violation(s)) ---")
        for e in errors[:10]:
            print(f"  {e}")
        if len(errors) > 10:
            print(f"  ... and {len(errors) - 10} more")

    if args.no_fail:
        print("\n(--no-fail mode — exiting 0 despite violations)")
        return 0
    print("\n✗ V2 invariants violated — commit blocked.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
