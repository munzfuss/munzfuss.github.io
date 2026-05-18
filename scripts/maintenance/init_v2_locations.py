#!/usr/bin/env python3
"""V2 Phase 2 — initialise V2 location display-meta files.

For each `data/locations/<loc>.yml`:
  1. Read the V1 yaml.
  2. Drop the `coins:` block (coin data now lives in
     `data/v2/final/<entity>.yml` per Phase 1; surfaces on the page via
     Phase 5 assembly).
  3. Add `consumes_entities: [entity_id, ...]` auto-derived from the
     `source_locations` field of every `data/v2/final/<entity>.yml` —
     i.e. invert the «which V1 locations contributed coins to this entity»
     map into «which entities contribute coins to this location».
  4. Write `data/v2/locations/<loc>.yml`.

Run with --apply to commit; default is dry-run.

Per V2_PIPELINE.md §3.10, the build assembly's inverse-index pass
guarantees that multi-entity (list-form `issuing_entity`) coins surface
on every page whose `consumes_entities` intersects with the list — even
when the home-file entity isn't in consumes_entities. The auto-derived
list below captures the «coins that physically live in entity X were
sourced from location L» mapping; the inverse-index handles the rare
cross-entity case at render time.

Edge case: the synthetic `_deprecated_gesamtstaat` bucket. The single
coin in it (Tower Hill Christian VII 2-Sechsling) originally rendered
on the SH page in V1. SH's consumes_entities therefore includes
`_deprecated_gesamtstaat` so the coin remains visible during V2 review
until the curator resolves it to a real entity per V2_PIPELINE.md §3.1.
"""

from __future__ import annotations

import argparse
import sys
from collections import defaultdict
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
LOCATIONS = ROOT / "data" / "locations"
V2_FINAL = ROOT / "data" / "v2" / "final"
V2_LOCATIONS = ROOT / "data" / "v2" / "locations"


def _load_yaml(p: Path) -> dict:
    return yaml.safe_load(p.read_text(encoding="utf-8")) or {}


def _build_location_to_entities_map() -> dict[str, list[str]]:
    """Walk data/v2/final/*.yml and invert each entity's per-coin
    v1_home_location into {loc: sorted_entity_list}."""
    inv: dict[str, set[str]] = defaultdict(set)
    for entity_file in V2_FINAL.glob("*.yml"):
        d = _load_yaml(entity_file)
        eid = d.get("id")
        if eid is None:
            continue
        for coin in d.get("coins", []) or []:
            v1_loc = coin.get("v1_home_location")
            if v1_loc:
                inv[v1_loc].add(eid)
            # Also surface list-form issuing_entity members beyond the home
            # file — the inverse-index hint for any page that consumes them.
            ie = coin.get("issuing_entity")
            if isinstance(ie, list):
                # The home file is `min(ie)`; the others would surface via the
                # build assembly's inverse-index pass. For consumes_entities
                # auto-derivation we only need the home-file membership, since
                # location → home-file already covers «where did the coin live
                # in V1». The list-form expansion is a render-time concern.
                pass
    return {loc: sorted(ents) for loc, ents in inv.items()}


def _strip_coins(doc: dict) -> dict:
    """Return a shallow copy of `doc` without the `coins` key."""
    return {k: v for k, v in doc.items() if k != "coins"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", default=True,
                        help="Report only — do NOT write V2 location files (default)")
    parser.add_argument("--apply", action="store_true",
                        help="WIPE data/v2/locations/*.yml and write fresh files")
    args = parser.parse_args()

    if args.apply:
        args.dry_run = False

    loc_to_entities = _build_location_to_entities_map()

    print("=" * 70)
    print("V2 Phase 2 — init_v2_locations: consumes_entities derivation")
    print("=" * 70)

    targets = []
    preserved_overrides: list[str] = []
    for path in sorted(LOCATIONS.glob("*.yml")):
        if path.name.endswith("-references.yml"):
            continue
        loc_id = path.stem
        v1_doc = _load_yaml(path)
        v1_coins_count = len(v1_doc.get("coins") or [])
        auto_consumes = loc_to_entities.get(loc_id, [])

        # Preserve manual consumes_entities overrides from existing V2 yaml.
        # First run: file doesn't exist → use auto-derived list.
        # Subsequent runs: keep whatever the curator set (matches the
        # init_v2_locations docstring's «idempotent re-run» promise).
        existing_v2 = V2_LOCATIONS / f"{loc_id}.yml"
        consumes = auto_consumes
        if existing_v2.exists():
            try:
                existing = _load_yaml(existing_v2)
                if existing.get("consumes_entities") is not None:
                    consumes = existing["consumes_entities"]
                    if sorted(consumes) != sorted(auto_consumes):
                        preserved_overrides.append(
                            f"{loc_id}: preserved {consumes} "
                            f"(auto would be {auto_consumes})"
                        )
            except Exception:
                pass  # corrupt existing file → use auto-derived

        v2_doc = _strip_coins(v1_doc)
        # consumes_entities goes near the top, after id/km_register/name/summary,
        # before fuss_order. Use a deterministic insertion: rebuild ordered dict.
        ordered = {}
        for key in v2_doc:
            ordered[key] = v2_doc[key]
            if key == "summary":
                # Inject right after summary.
                ordered["consumes_entities"] = consumes
        # Fallback if summary wasn't present.
        if "consumes_entities" not in ordered:
            ordered["consumes_entities"] = consumes
            # Re-key into a more sensible order: id first, consumes_entities
            # near the top.
            new = {}
            for k in ("id", "km_register", "name", "summary", "consumes_entities"):
                if k in ordered:
                    new[k] = ordered[k]
            for k, v in ordered.items():
                if k not in new:
                    new[k] = v
            ordered = new

        targets.append((loc_id, ordered, v1_coins_count, consumes))
        print(f"  {loc_id:30s}  v1 coins: {v1_coins_count:>4d}  →  consumes: {consumes}")

    if preserved_overrides:
        print(f"\n--- Manual consumes_entities preserved from existing V2 yamls "
              f"({len(preserved_overrides)}) ---")
        for line in preserved_overrides:
            print(f"  {line}")

    if args.dry_run:
        print("\n--- DRY RUN — no files written. Re-run with --apply to commit. ---")
        return 0

    V2_LOCATIONS.mkdir(parents=True, exist_ok=True)
    for p in V2_LOCATIONS.glob("*.yml"):
        p.unlink()

    for loc_id, doc, _, _ in targets:
        out_path = V2_LOCATIONS / f"{loc_id}.yml"
        out_path.write_text(
            yaml.dump(doc, sort_keys=False, allow_unicode=True,
                      default_flow_style=False, width=120),
            encoding="utf-8",
        )

    print(f"\n✓ Wrote {len(targets)} location file(s) to {V2_LOCATIONS}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
