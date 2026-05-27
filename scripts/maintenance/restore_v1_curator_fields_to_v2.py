"""Restore V1-curator-set fields to V2 final entries that lost them.

Background
==========

When a V1-bootstrap foundation entry gets purged by absorb's
stale-foundation pass (Shape A/B), curator-set fields are migrated to
the new unified host via `curator_migrations`. Before 2026-05-27 the
migration covered only `_FOUNDATION_IMMUTABLE_FIELDS + {note}`; year
metadata (year_ranges/year_label/year_first/year_last), explicit
diameter_mm, and curator-handpicked sources were silently dropped.

This causes visible regressions on the rendered page:

  KM-650 Christian VII Species-Dukat (Altona):
    V1 entry → year_label «1791-1792, 1794, 1802» + 4 web sources
               (Numista, NGC, Smithsonian, danskmoent.dk Hede)
    V2 final → year_label «1791-1802» (merger-derived wide span)
               + only auction sources (Bruun I/II/IV + ucoin)

The absorb fix (extended `_MIGRATION_PRESERVED_FIELDS`) only helps
going forward when a fresh bulk-promote happens. For existing V2 final
entries where the V1 foundation was purged in an earlier run, no
retro-migration ever occurs — those entries stay with the cache-derived
data only.

What this script does
=====================

Walks V1 location yamls. For each V1 entry, finds the V2 final entry
it would have been migrated to (by catalog overlap — numista N#, or
bruun_collection_id, or KM + ruler + year_first), and back-fills:

  1. `year_ranges` — if V2 missing OR V2 is a single wide-span range
     and V1 has discrete sub-ranges, REPLACE with V1's discrete shape.
     `year_label` derived from year_ranges via the project's
     standard formatter.
  2. `diameter_mm` — if V2 missing and V1 has a scalar attestation, add
     as a list-form `{value, source: 'v1_curator'}`.
  3. `sources[]` — for each V1 source URL not in V2 sources, ADD it
     (dedupe by URL).

Conservative: never overwrites V2 fields where V2 already has
broader/equivalent content. Idempotent.

Run:
    .venv/bin/python scripts/maintenance/restore_v1_curator_fields_to_v2.py [--dry-run]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml as _yaml
from ruamel.yaml import YAML

PROJECT = Path(__file__).resolve().parents[2]
V1_LOCATIONS = PROJECT / "data" / "locations"
V2_FINAL = PROJECT / "data" / "v2" / "final"


def _v1_yaml_iter():
    """Yield (loc_id, list-of-coin-dicts) for every V1 location yaml."""
    for path in sorted(V1_LOCATIONS.glob("*.yml")):
        if path.stem.endswith("-references"):
            continue
        with path.open() as f:
            doc = _yaml.safe_load(f)
        if not isinstance(doc, dict):
            continue
        coins = doc.get("coins") or []
        yield path.stem, coins


def _v2_yaml_pair_iter(yaml_loader):
    """Yield (path, doc) for every V2 final yaml (loaded preserving formatting)."""
    for path in sorted(V2_FINAL.glob("*.yml")):
        with path.open() as f:
            doc = yaml_loader.load(f)
        if isinstance(doc, dict):
            yield path, doc


def _cat_keys(cat: dict) -> dict:
    """Extract identifying keys for cross-V1/V2 matching.

    Returns a dict with five potential match keys: numista (globally
    unique), bruun_collection_id (globally unique within Bruun catalogue),
    lange (Schleswig-Holstein-specific catalogue), km (territory-bound,
    needs ruler+year disambiguation upstream), and km_no_subvariant
    (km stripped of dot-suffix — covers «70» ↔ «70.1» bare-vs-dot match
    cases per the merger's CATALOG_KEY_SYNONYMS tolerance)."""
    if not isinstance(cat, dict):
        return {}
    km_raw = cat.get("km")
    if isinstance(km_raw, list):
        km_str = str(km_raw[0]) if km_raw else None
    else:
        km_str = str(km_raw) if km_raw is not None else None
    km_core = None
    if km_str and "." in km_str:
        import re as _re
        m = _re.match(r"^(\d+)\.\d+$", km_str)
        if m:
            km_core = m.group(1)
    return {
        "numista": str(cat.get("numista") or "") or None,
        "bruun_coll": str(cat.get("bruun_collection_id") or "") or None,
        "lange": str(cat.get("lange") or "") or None,
        "km": km_str,
        "km_core": km_core,
    }


def _norm_ruler(s) -> str:
    """Lowercase + strip trailing punctuation + drop «von <house>» tails.
    Matches `merge_seeds_cross_source._normalise_ruler` shape."""
    import re as _re
    if not s:
        return ""
    s = str(s).split("(")[0].split(",")[0]
    s = _re.split(r"\s+(?:von|af|of|zu)\s+", s, maxsplit=1)[0]
    s = _re.sub(r"[\s.]+$", "", s)
    return _re.sub(r"\s+", " ", s).lower()


def _ranges_to_label(year_ranges: list) -> str:
    """Compact label for a list of [lo, hi] ranges. Same convention as
    the merger's `_format_year_label`: `1791-1792, 1794, 1802`."""
    parts = []
    for r in year_ranges or []:
        if not isinstance(r, (list, tuple)) or len(r) != 2:
            continue
        lo, hi = int(r[0]), int(r[1])
        if hi == lo:
            parts.append(str(lo))
        else:
            parts.append(f"{lo}-{hi}")
    return ", ".join(parts)


def _restore_one(v1_coin: dict, v2_coin: dict) -> dict:
    """Mutate v2_coin in place. Returns counts of fields touched."""
    counts = {"year": 0, "diameter": 0, "sources": 0}

    # Year metadata: V1's discrete year_ranges → V2 if V2 has a single
    # wide-span range OR no year_ranges at all.
    v1_yr = v1_coin.get("year_ranges")
    if isinstance(v1_yr, list) and len(v1_yr) > 1:
        v2_yr = v2_coin.get("year_ranges")
        v2_is_wide = (
            not isinstance(v2_yr, list)
            or len(v2_yr) <= 1
            or (
                len(v2_yr) == 1
                and isinstance(v2_yr[0], (list, tuple))
                and v2_yr[0][1] - v2_yr[0][0] > 2
            )
        )
        if v2_is_wide:
            v2_coin["year_ranges"] = v1_yr
            # Derive label + year_first/last from the new ranges.
            v2_coin["year_label"] = _ranges_to_label(v1_yr)
            lows = [r[0] for r in v1_yr if isinstance(r, (list, tuple))]
            highs = [r[1] for r in v1_yr if isinstance(r, (list, tuple))]
            if lows and highs:
                v2_coin["year_first"] = min(lows)
                v2_coin["year_last"] = max(highs)
            counts["year"] = 1

    # Diameter: V1 scalar → V2 list-form if V2 lacks any attestation.
    v1_d = v1_coin.get("diameter_mm")
    if isinstance(v1_d, (int, float)) and v1_d > 0:
        v2_d = v2_coin.get("diameter_mm")
        if v2_d in (None, [], ""):
            v2_coin["diameter_mm"] = [{"value": float(v1_d), "source": "v1_curator"}]
            counts["diameter"] = 1

    # Sources: add V1 URLs not in V2.
    v1_sources = v1_coin.get("sources") or []
    if v1_sources:
        v2_sources = v2_coin.get("sources") or []
        existing_urls = set()
        for s in v2_sources:
            if isinstance(s, dict) and s.get("url"):
                existing_urls.add(s["url"])
        added = 0
        for s in v1_sources:
            if not isinstance(s, dict):
                continue
            url = s.get("url")
            if not url:
                continue
            if url in existing_urls:
                continue
            # Skip anchor URLs (#refN — V1-local) and obvious dupes.
            if url.startswith("#"):
                continue
            v2_sources.append(dict(s))
            existing_urls.add(url)
            added += 1
        if added:
            v2_coin["sources"] = v2_sources
            counts["sources"] = added
    return counts


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true",
                    help="Report what would change without writing files")
    args = ap.parse_args()

    # Build V1 entry index keyed on identifying catalog refs.
    v1_index_by_numista: dict[str, dict] = {}
    v1_index_by_bruun_coll: dict[str, dict] = {}
    v1_index_by_lange: dict[str, dict] = {}
    # km + normalised ruler + year_first — territory-scoped fallback.
    v1_index_by_km_ruler_year: dict[tuple, dict] = {}
    # km-core (sub-variant stripped) + ruler + year — bare-vs-dot tolerance.
    v1_index_by_km_core_ruler_year: dict[tuple, dict] = {}
    for loc_id, coins in _v1_yaml_iter():
        for c in coins:
            if not isinstance(c, dict):
                continue
            cat = _cat_keys(c.get("catalog") or {})
            if cat.get("numista"):
                v1_index_by_numista.setdefault(cat["numista"], c)
            if cat.get("bruun_coll"):
                v1_index_by_bruun_coll.setdefault(cat["bruun_coll"], c)
            if cat.get("lange"):
                v1_index_by_lange.setdefault(cat["lange"], c)
            km = cat.get("km")
            km_core = cat.get("km_core")
            ruler = _norm_ruler(c.get("ruler"))
            year_first = c.get("year_first")
            if km and ruler and year_first:
                v1_index_by_km_ruler_year.setdefault(
                    (km, ruler, year_first), c
                )
            if km_core and ruler and year_first:
                v1_index_by_km_core_ruler_year.setdefault(
                    (km_core, ruler, year_first), c
                )

    yloader = YAML()
    yloader.preserve_quotes = True
    yloader.width = 4096
    yloader.indent(mapping=2, sequence=4, offset=2)

    grand = {"files": 0, "files_changed": 0,
             "year": 0, "diameter": 0, "sources": 0}
    for path, doc in _v2_yaml_pair_iter(yloader):
        grand["files"] += 1
        coins = doc.get("coins") or []
        per_file = {"year": 0, "diameter": 0, "sources": 0}
        for v2c in coins:
            if not isinstance(v2c, dict):
                continue
            cat = _cat_keys(v2c.get("catalog") or {})
            v1c = None
            # Priority order: most-specific globally-unique keys first.
            if cat.get("numista") and cat["numista"] in v1_index_by_numista:
                v1c = v1_index_by_numista[cat["numista"]]
            elif cat.get("bruun_coll") and cat["bruun_coll"] in v1_index_by_bruun_coll:
                v1c = v1_index_by_bruun_coll[cat["bruun_coll"]]
            elif cat.get("lange") and cat["lange"] in v1_index_by_lange:
                v1c = v1_index_by_lange[cat["lange"]]
            if v1c is None:
                # km + ruler + year_first fallback — territory-bound,
                # disambiguated by the ruler+year pair. Try the V2's KM
                # verbatim, then the bare-form parent (V2 «70.1» → V1
                # «70» bare).
                ruler = _norm_ruler(v2c.get("ruler"))
                year_first = v2c.get("year_first")
                if ruler and year_first:
                    km = cat.get("km")
                    if km:
                        key = (km, ruler, year_first)
                        if key in v1_index_by_km_ruler_year:
                            v1c = v1_index_by_km_ruler_year[key]
                        elif (cat.get("km_core")
                              and (cat["km_core"], ruler, year_first) in v1_index_by_km_ruler_year):
                            v1c = v1_index_by_km_ruler_year[
                                (cat["km_core"], ruler, year_first)
                            ]
            if v1c is None:
                continue
            r = _restore_one(v1c, v2c)
            for k, v in r.items():
                per_file[k] += v
        total = sum(per_file.values())
        if total:
            grand["files_changed"] += 1
            for k, v in per_file.items():
                grand[k] += v
            rel = path.relative_to(PROJECT)
            print(f"  {rel}: year={per_file['year']} "
                  f"diameter={per_file['diameter']} "
                  f"sources={per_file['sources']}")
            if not args.dry_run:
                with path.open("w") as f:
                    yloader.dump(doc, f)
    print()
    print(f"Files scanned:           {grand['files']}")
    print(f"Files changed:           {grand['files_changed']}")
    print(f"Year-fields restored:    {grand['year']}")
    print(f"Diameters restored:      {grand['diameter']}")
    print(f"Sources added:           {grand['sources']}")
    if args.dry_run:
        print("(dry-run — no files written)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
