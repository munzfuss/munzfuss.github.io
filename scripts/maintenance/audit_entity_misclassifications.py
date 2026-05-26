#!/usr/bin/env python3
"""audit_entity_misclassifications.py — find + relocate entity-misclassified seeds.

Scans every `data/v2/seed/<source>/<entity>.yml` and reports any coin
whose `mint` field maps unambiguously to ONE entity via the unified
`mint_registry`, but whose `issuing_entity` field says a different
entity. Acts on the per-source seed layer — Phase 3.2 (cross-source
merger) and Phase 4 (absorb) operate per-entity and so silently lose
data when source seeds disagree on which entity owns a given coin.

Surfaced 2026-05-26 by user audit: a Bruun Christian IV 1 Dukat 1640
Glückstadt landed in `danish_realm` (default fallback) while the ucoin
+ NumisMaster entries for the same coin landed in `royal_holstein`
(direct mint match). Merger couldn't merge them — different entity
files — so Bruun's weight reading + lot citation never reached the
unified entry. Project-wide audit on 4812 seed entries found 87 cases
of this exact shape (87 SH-mint Bruun/ucoin/NumisMaster entries
misclassified to `danish_realm` instead of `royal_holstein`) plus
smaller pockets in 4 other (current,expected) shapes.

Usage:

    # Report only (default, no writes):
    .venv/bin/python scripts/maintenance/audit_entity_misclassifications.py

    # Apply: rewrite per-source seeds, removing mismatched entries
    # from the wrong entity file and re-merging into the expected one.
    .venv/bin/python scripts/maintenance/audit_entity_misclassifications.py --apply

    # Restrict to one source:
    .venv/bin/python scripts/maintenance/audit_entity_misclassifications.py --source bruun

The script is idempotent — re-running after --apply produces zero
mismatches. Cascade through merger + absorb is the caller's
responsibility (typical session-end sequence:
`merge_seeds_cross_source.py --apply` then
`absorb_seeds_into_final_v2.py --apply`).

Skipped cases (NOT reported as mismatches):
  * Mint = None / empty (classifier returns None — no expected value).
  * Mint maps to a list of entities AND current `issuing_entity` is
    one of them (joint mint with legitimate multi-entity tag).
  * The mint registry has the entity = None (out-of-scope foreign
    mint).
"""
from __future__ import annotations

import argparse
import sys
from collections import Counter, defaultdict
from pathlib import Path

import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from lib.seed_merge import merge_seed  # noqa: E402
from lib.v2_entity_classify import classify_mint_to_entity  # noqa: E402
from lib.v2_resolver import ruamel_to_plain  # noqa: E402

V2_SEED_ROOT = PROJECT_ROOT / "data" / "v2" / "seed"

# Entities the script will RELOCATE FROM with --apply. Everything else
# is reported but left in place — those cases reflect legitimate
# year-aware issuer-based classification by the source builder that the
# mint-only classifier doesn't model:
#
#  * `schauenburg_pinneberg` Altona/Oldendorf/Rinteln 1589-1640 — Adolf
#    XIII / Otto V Schauenburg issuer pre-Hesse-takeover. Mint-default
#    points to royal_holstein (post-1640 Altona) or
#    holstein_schauenburg_county (post-1640 territorial reorg), but
#    NumisMaster + Bruun correctly tag by issuer.
#  * `fuerstbisthum_luebeck` Lübeck-Bishopric coinage struck at
#    Glückstadt (royal mint hosted bishopric production occasionally).
#  * `herzogtum_sachsen_lauenburg` Lauenburg-territorial 1815-1864 coinage
#    struck at Altona (Royal-Holstein mint under Danish king).
#  * `gottorp_duchy` 1716-1720 Holstein-Gottorp-Rendsburg coinage —
#    Christian August's Gottorp claim during Great Northern War, struck
#    at Rendsburg.
#
# `danish_realm` is the catch-all default (alias-lookup miss → fall to
# default) so every entry that lands there with a non-Danish-realm
# mint is by definition a misclassification, NOT a deliberate issuer
# override. Hence only it is in the relocate set.
_RELOCATE_FROM_ENTITIES = frozenset({"danish_realm"})


def _scan_one_source(src_dir: Path) -> list[dict]:
    """For each yaml in `data/v2/seed/<src>/`, find coins whose
    `issuing_entity` disagrees with the mint-driven classifier.

    Returns a list of dicts:
      {
        "source": "<src>",
        "current_entity": str,  # entity-file the coin currently lives in
        "expected_entity": str, # entity the mint maps to
        "coin": dict,           # the full coin dict (for relocation)
        "filepath": Path,       # source file
      }
    """
    out: list[dict] = []
    for yml_path in sorted(src_dir.glob("*.yml")):
        # Skip the auto-generated unclassified bucket — its entries
        # are by definition not classified, so they don't apply.
        if yml_path.stem == "_unclassified":
            continue
        current_entity = yml_path.stem
        try:
            data = yaml.safe_load(yml_path.read_text(encoding="utf-8")) or {}
        except (OSError, yaml.YAMLError):
            continue
        coins = data.get("coins") or []
        for c in coins:
            if not isinstance(c, dict):
                continue
            mint = c.get("mint")
            if mint in (None, "", []):
                continue
            # Year-aware classification per MVP-D (2026-05-26): use the
            # coin's `year_first` as the canonical era anchor when
            # available (any year_overrides in the mint registry are
            # evaluated against it). Falls back to year-blind default
            # when `year_first` is missing.
            year = c.get("year_first")
            if not isinstance(year, int):
                year = None
            expected = classify_mint_to_entity(mint, year=year)
            if expected is None:
                continue
            # Joint-mint allow: if mint maps to a list of entities AND
            # current is in that list, treat as agreement.
            ie = c.get("issuing_entity")
            if isinstance(expected, list):
                if current_entity in expected:
                    continue
                # Otherwise: take the alphabetically-first as expected.
                expected_scalar = sorted(expected)[0]
            else:
                expected_scalar = expected
            # Multi-entity coin (list-form issuing_entity) — if expected
            # is in the list, no mismatch.
            if isinstance(ie, list) and expected_scalar in [str(e) for e in ie]:
                continue
            if current_entity != expected_scalar:
                out.append({
                    "source": src_dir.name,
                    "current_entity": current_entity,
                    "expected_entity": expected_scalar,
                    "coin": c,
                    "filepath": yml_path,
                })
    return out


def _relocate_misclassifications(
    misclassifications: list[dict],
    apply: bool = False,
) -> None:
    """For each misclassified entry: remove from current-entity yaml,
    inject into expected-entity yaml via `merge_seed`.

    Both writes go through `merge_seed` (the merge-aware writer) to
    preserve any curator-edited fields that survive across regen.
    """
    # Group by (source, current_entity, expected_entity) to batch the
    # per-file rewrites — touching each entity file at most once per
    # (current, expected) pair keeps disk I/O low and the diff readable.
    grouped: dict[tuple[str, str, str], list[dict]] = defaultdict(list)
    for m in misclassifications:
        grouped[(m["source"], m["current_entity"], m["expected_entity"])].append(m["coin"])

    actions_taken = 0
    for (src, cur, exp), coins in sorted(grouped.items()):
        # Only relocate from entities in the allow-list. Other current
        # entities reflect issuer-aware classification we should NOT
        # override blindly — see `_RELOCATE_FROM_ENTITIES` comment.
        is_relocatable = cur in _RELOCATE_FROM_ENTITIES
        marker = "→" if is_relocatable else "⊘"
        suffix = "" if is_relocatable else "  [skipped — issuer-aware]"
        print(f"  {src:12s}  {cur:34s} {marker} {exp:34s}  "
              f"{len(coins)} coin(s){suffix}")
        if not apply or not is_relocatable:
            continue
        # Read both yamls
        cur_path = V2_SEED_ROOT / src / f"{cur}.yml"
        exp_path = V2_SEED_ROOT / src / f"{exp}.yml"
        cur_data = yaml.safe_load(cur_path.read_text(encoding="utf-8")) or {}
        exp_data = (
            yaml.safe_load(exp_path.read_text(encoding="utf-8")) or {}
            if exp_path.exists() else {}
        )
        # Remove the misclassified coins from current
        coin_ids = {c.get("id") for c in coins if c.get("id")}
        cur_coins_before = len(cur_data.get("coins") or [])
        cur_data["coins"] = [
            c for c in (cur_data.get("coins") or [])
            if c.get("id") not in coin_ids
        ]
        cur_coins_after = len(cur_data["coins"])
        # Update issuing_entity on each relocated coin to match the
        # destination file (when it was scalar = old wrong tag, set to
        # new correct tag; when list-form, swap the wrong tag for new).
        relocated_coins: list[dict] = []
        for c in coins:
            new_c = dict(c)
            old_ie = new_c.get("issuing_entity")
            if isinstance(old_ie, str):
                new_c["issuing_entity"] = exp
            elif isinstance(old_ie, list):
                new_list = sorted({(exp if e == cur else str(e)) for e in old_ie})
                new_c["issuing_entity"] = new_list if len(new_list) > 1 else new_list[0]
            else:
                new_c["issuing_entity"] = exp
            relocated_coins.append(new_c)
        # Inject into expected via merge_seed so curator overrides survive.
        # merge_seed reads the existing yaml at out_path and merges fresh
        # coins against it. Returns (merged_list, stats).
        # NB: merge_seed returns ruamel.yaml CommentedMap objects (so it
        # can preserve comments + ordering on round-trip with ruamel
        # dumper). PyYAML's safe_dump can't serialize CommentedMap, so
        # we flatten to plain dicts before assembling the output payload.
        merged, _stats = merge_seed(relocated_coins, exp_path)
        exp_data["coins"] = ruamel_to_plain(merged)
        # Also flatten the rest of exp_data — it was loaded via PyYAML
        # safe_load (plain dicts), so this is a no-op for those keys
        # but keeps the call shape uniform.
        exp_data = ruamel_to_plain(exp_data)
        # Preserve top-level keys if missing in destination
        if not exp_data.get("entity_id"):
            exp_data["entity_id"] = exp
        # Write both
        cur_path.write_text(
            yaml.safe_dump(cur_data, sort_keys=False, allow_unicode=True,
                           default_flow_style=False, width=120),
            encoding="utf-8",
        )
        exp_path.write_text(
            yaml.safe_dump(exp_data, sort_keys=False, allow_unicode=True,
                           default_flow_style=False, width=120),
            encoding="utf-8",
        )
        print(f"    moved {len(coin_ids)} ids: {src}/{cur}.yml "
              f"({cur_coins_before}→{cur_coins_after}) → {src}/{exp}.yml")
        actions_taken += len(coin_ids)
    if apply:
        print(f"\n✓ Relocated {actions_taken} coin(s) across {len(grouped)} "
              f"(source, src_entity, dst_entity) batch(es).")
        print(f"  Cascade: run `merge_seeds_cross_source.py --apply` "
              f"then `absorb_seeds_into_final_v2.py --apply`.")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--apply", action="store_true",
                    help="Rewrite per-source seeds (default: report only).")
    ap.add_argument("--source", default=None,
                    help="Restrict to one source subdir (bruun / ucoin / numista / "
                         "numismaster / hede / galster).")
    args = ap.parse_args()

    if not V2_SEED_ROOT.exists():
        print(f"V2 seed root not found: {V2_SEED_ROOT}", file=sys.stderr)
        return 1

    src_dirs = (
        [V2_SEED_ROOT / args.source] if args.source
        else sorted(d for d in V2_SEED_ROOT.iterdir() if d.is_dir())
    )

    all_mismatches: list[dict] = []
    per_source: Counter[str] = Counter()
    per_shape: Counter[tuple[str, str]] = Counter()
    for src_dir in src_dirs:
        if not src_dir.is_dir():
            continue
        mismatches = _scan_one_source(src_dir)
        all_mismatches.extend(mismatches)
        per_source[src_dir.name] = len(mismatches)
        for m in mismatches:
            per_shape[(m["current_entity"], m["expected_entity"])] += 1

    print(f"Scanned {len(src_dirs)} source dir(s); "
          f"found {len(all_mismatches)} mismatched coin(s).\n")

    print("Per-source mismatch counts:")
    for src, n in per_source.most_common():
        print(f"  {src:12s}  {n}")
    print()

    print("Top mismatch shapes (current_entity → expected_entity):")
    for (cur, exp), n in per_shape.most_common(20):
        print(f"  {cur:34s} → {exp:34s}  {n}")
    print()

    if not all_mismatches:
        print("✓ No misclassifications found.")
        return 0

    print(f"{'Relocation plan (--apply to commit):' if not args.apply else 'Applying relocations:'}")
    _relocate_misclassifications(all_mismatches, apply=args.apply)

    if not args.apply:
        print("\n--- DRY RUN — no files written. Re-run with --apply to commit. ---")

    return 0


if __name__ == "__main__":
    sys.exit(main())
