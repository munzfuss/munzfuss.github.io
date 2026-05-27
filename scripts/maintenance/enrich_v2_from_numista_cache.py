"""Enrich V2 entries with Numista-cache measurements where missing.

Background
==========

Every coin entry in V2 final + V2 seed/* yamls that carries
`catalog.numista: <N#>` has a corresponding cached Numista page at
`scripts/cache/numista/<N#>.json`. Many of those caches publish
measurements — `weight`, `composition.text` (fineness), `size`
(diameter) — that did NOT get pulled into the entry's
`weight_rough_g` / `fineness` / `diameter_mm` lists.

Two ingestion paths exist:

  (a) `build_numista_pre1541_seed.py` for the pre-1541 medieval coinage
      tier. Reads cache, emits seeds with full Numista data.
  (b) V1-curated entries (`data/locations/<loc>.yml`) carry
      `catalog.numista` + a `sources[].type: numista` URL by curator
      handwriting. The V1 → V2 bootstrap migrates these into
      `data/v2/final/<entity>.yml` foundations BUT never opens the
      Numista cache to pull weight/fineness/diameter.

Curator-flagged 2026-05-27 on KM-27 Friedrich Karl Plön 1760 1 Ducat
(N#222051): «нумiста є серед джерел, вона дає своє значення ваги, але
воно десь загубилось». Cache has `weight: 3.46`; rendered row shows
3.48 (Bruun) + 3.5 (NumisMaster) — no 3.46 (Numista).

What this script does
=====================

Scans V2 final + V2 seed yamls. For each coin with `catalog.numista`
set (single N# or list), loads the corresponding cache JSON and:

  1. Parses weight → adds to `weight_rough_g` (list-form) as a new
     `FieldValue(value, source='numista')` if no existing entry has
     `source: numista`.
  2. Parses `composition.text` for «.XXX» pattern → adds to `fineness`
     as `FieldValue(value, source='numista')` if missing.
  3. Parses `size` → adds to `diameter_mm` as `FieldValue` if missing.

Idempotent — re-runs are no-ops once Numista values are present.

CLAUDE.md §9a data-accumulation: never overwrites another source's
value, just appends a Numista entry alongside.

CLAUDE.md §4 verified-wins: when ALL sources on this field are
unverified or the existing entry has no `*_verified: true` flag, the
Numista addition flips `*_verified: true` (cache JSON is the
authoritative Numista record).

Run:
    .venv/bin/python scripts/maintenance/enrich_v2_from_numista_cache.py [--dry-run]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from ruamel.yaml import YAML

PROJECT = Path(__file__).resolve().parents[2]
CACHE_DIR = PROJECT / "scripts" / "cache" / "numista"

TARGET_GLOBS = [
    "data/v2/final/*.yml",
    "data/v2/seed/numista/*.yml",
    "data/v2/seed/ucoin/*.yml",
    "data/v2/seed/bruun/*.yml",
    "data/v2/seed/hede/*.yml",
    "data/v2/seed/galster/*.yml",
    "data/v2/seed/numismaster/*.yml",
    "data/v2/seed_unified/*.yml",
]

_FINENESS_RE = re.compile(r"\.(\d{3})")


def _load_numista_cache(nid: str) -> dict | None:
    p = CACHE_DIR / f"{nid}.json"
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return None


def _parse_fineness(composition_text: str | None) -> float | None:
    """«Gold (.986)» → 0.986. «Silver» → None (no fineness given)."""
    if not composition_text:
        return None
    m = _FINENESS_RE.search(composition_text)
    if not m:
        return None
    try:
        return int(m.group(1)) / 1000.0
    except ValueError:
        return None


def _has_source(field_val, source: str) -> bool:
    """True if `field_val` (scalar or list) already has an entry with
    the given source. Scalar form has no embedded source so always returns
    False (caller may want to promote scalar → list and add)."""
    if field_val is None:
        return False
    if isinstance(field_val, list):
        for entry in field_val:
            if isinstance(entry, dict) and entry.get("source") == source:
                return True
    # scalar — no embedded source
    return False


def _promote_to_list(field_val) -> list:
    """Convert a scalar measurement to list-form, OR pass through a list.
    Scalar values are wrapped without a `source` label (caller is in
    a position to know whether to add one)."""
    if field_val is None:
        return []
    if isinstance(field_val, list):
        return list(field_val)
    # Scalar — wrap as a sourceless entry (legacy form, kept for backward
    # compatibility when the original source isn't known)
    return [{"value": field_val}]


def _enrich_coin(coin: dict) -> dict:
    """Mutate `coin` in place. Returns counts of fields touched."""
    counts = {"weight": 0, "fineness": 0, "diameter": 0}
    cat = coin.get("catalog") or {}
    nid_raw = cat.get("numista")
    if nid_raw is None:
        return counts
    # numista field may be scalar or list — iterate
    nids = nid_raw if isinstance(nid_raw, list) else [nid_raw]
    for nid in nids:
        if not nid:
            continue
        cache = _load_numista_cache(str(nid))
        if cache is None:
            continue

        # Weight
        w = cache.get("weight")
        if w is not None and not _has_source(coin.get("weight_rough_g"), "numista"):
            try:
                w_val = float(w)
            except (TypeError, ValueError):
                w_val = None
            if w_val is not None:
                lst = _promote_to_list(coin.get("weight_rough_g"))
                lst.append({"value": w_val, "source": "numista"})
                coin["weight_rough_g"] = lst
                counts["weight"] += 1
                # Verified-flag promotion per §4: if cache attests
                # weight, mark verified — Numista cache is source-of-truth.
                coin["weight_rough_verified"] = True

        # Fineness
        comp = cache.get("composition")
        comp_text = comp.get("text") if isinstance(comp, dict) else None
        fn_val = _parse_fineness(comp_text)
        if fn_val is not None and not _has_source(coin.get("fineness"), "numista"):
            lst = _promote_to_list(coin.get("fineness"))
            lst.append({"value": fn_val, "source": "numista"})
            coin["fineness"] = lst
            counts["fineness"] += 1
            coin["fineness_verified"] = True

        # Diameter (cache key is `size` in mm, may be float)
        size = cache.get("size")
        if size is not None and not _has_source(coin.get("diameter_mm"), "numista"):
            try:
                size_val = float(size)
            except (TypeError, ValueError):
                size_val = None
            if size_val is not None:
                lst = _promote_to_list(coin.get("diameter_mm"))
                lst.append({"value": size_val, "source": "numista"})
                coin["diameter_mm"] = lst
                counts["diameter"] += 1
                coin["diameter_mm_verified"] = True
    return counts


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true",
                    help="Report what would change without writing files")
    args = ap.parse_args()

    y = YAML()
    y.preserve_quotes = True
    y.width = 4096
    y.indent(mapping=2, sequence=4, offset=2)

    grand = {"files": 0, "files_changed": 0,
             "weight": 0, "fineness": 0, "diameter": 0}
    for pattern in TARGET_GLOBS:
        for path in sorted(PROJECT.glob(pattern)):
            grand["files"] += 1
            with path.open() as f:
                doc = y.load(f)
            if not isinstance(doc, dict):
                continue
            coins = doc.get("coins")
            if not isinstance(coins, list):
                continue
            file_counts = {"weight": 0, "fineness": 0, "diameter": 0}
            for coin in coins:
                if not isinstance(coin, dict):
                    continue
                c = _enrich_coin(coin)
                for k, v in c.items():
                    file_counts[k] += v
            total_file = sum(file_counts.values())
            if total_file:
                grand["files_changed"] += 1
                for k, v in file_counts.items():
                    grand[k] += v
                rel = path.relative_to(PROJECT)
                print(f"  {rel}: weight={file_counts['weight']} "
                      f"fineness={file_counts['fineness']} "
                      f"diameter={file_counts['diameter']}")
                if not args.dry_run:
                    with path.open("w") as f:
                        y.dump(doc, f)
    print()
    print(f"Files scanned:    {grand['files']}")
    print(f"Files changed:    {grand['files_changed']}")
    print(f"Weights added:    {grand['weight']}")
    print(f"Fineness added:   {grand['fineness']}")
    print(f"Diameters added:  {grand['diameter']}")
    if args.dry_run:
        print("(dry-run — no files written)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
