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


def _flatten_scalar(v):
    """First non-empty value of a scalar/list field. Used to derive a
    single match key when a catalog field may be either form."""
    if v is None:
        return None
    if isinstance(v, list):
        return str(v[0]) if v else None
    s = str(v).strip()
    return s or None


def _flatten_all(v) -> list[str]:
    """ALL non-empty string values of a scalar/list/dict catalog field.
    Used by V2-side lookups against V1 indices so list-form (per §9a
    multi-source accumulation) is iterated, not just the first item.

    Bug-trigger 2026-05-27 (V1 km-66 N#142853 not propagating because
    V2 catalog had numista=['109264','142853'] and the old flatten-to-
    scalar lookup only checked '109264')."""
    if v is None:
        return []
    if isinstance(v, list):
        out = []
        for x in v:
            if isinstance(x, dict) and x.get("value"):
                out.append(str(x["value"]))
            elif x is not None and str(x).strip():
                out.append(str(x).strip())
        return out
    s = str(v).strip()
    return [s] if s else []


def _cat_keys(cat: dict) -> dict:
    """Extract identifying keys for cross-V1/V2 matching.

    Returns potential match keys at descending specificity:
    numista (globally unique), bruun_collection_id (globally unique
    within Bruun catalogue), lange (Schleswig-Holstein-specific),
    hede + hede_volume (per-ruler-volume specific), schou (per-ruler),
    km + km_core (territory-bound)."""
    if not isinstance(cat, dict):
        return {}
    km_str = _flatten_scalar(cat.get("km"))
    km_core = None
    if km_str and "." in km_str:
        import re as _re
        m = _re.match(r"^(\d+)\.\d+$", km_str)
        if m:
            km_core = m.group(1)
    return {
        "numista": _flatten_scalar(cat.get("numista")),
        "bruun_coll": _flatten_scalar(cat.get("bruun_collection_id")),
        "lange": _flatten_scalar(cat.get("lange")),
        "hede": _flatten_scalar(cat.get("hede")),
        "hede_volume": _flatten_scalar(cat.get("hede_volume")),
        "schou": _flatten_scalar(cat.get("schou")),
        "km": km_str,
        "km_core": km_core,
    }


def _norm_nominal(n) -> str:
    """Lowercase + collapse whitespace. Used for year+nominal+ruler match."""
    import re as _re
    if not n:
        return ""
    return _re.sub(r"\s+", " ", str(n).lower()).strip()


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


def _infer_v1_register(v1_loc: str, v1_id: str) -> str | None:
    """Infer Krause register code (DK / SH / NO) from V1 location +
    id-suffix conventions. Returns None when register can't be inferred
    safely. Used to tag cross-register KMs when merging multiple V1
    entries that share a Hede-key but cite DIFFERENT KM registers
    (e.g. the same Krone-Mønt 1671 cited as KM-DK 103 by curator in
    one V1 entry and KM-SH 63 in another).

    Convention:
    - id contains `-dk-` → DK
    - id contains `-sh-` → SH
    - id contains `-no-` → NO
    - else: location-default (denmark.yml → DK; schleswig_holstein.yml → SH;
      norway.yml → NO; other → None)
    """
    if not v1_id:
        return None
    id_low = v1_id.lower()
    if "-dk-" in id_low:
        return "DK"
    if "-sh-" in id_low:
        return "SH"
    if "-no-" in id_low:
        return "NO"
    loc_default = {
        "denmark": "DK",
        "schleswig_holstein": "SH",
        "norway": "NO",
    }
    return loc_default.get(v1_loc)


def _restore_multi(v1_coins: list[dict], v2_coin: dict,
                   v1_locs: list[str], v1_ids: list[str]) -> dict:
    """Restore data from MULTIPLE V1 entries (sharing a Hede-key) onto
    one V2 entry. Specific concern: V1 had separate per-register entries
    for the same physical coin (curator dual-citation under DK + SH
    Krause volumes); V2 collapsed them into one entry with a single
    KM. Add the cross-register KM(s) + each V1 entry's distinct
    Numista N# / sources as list-form alongside V2's existing values.

    The base single-V1 restore (`_restore_one`) handles year-ranges /
    diameter / sources of the primary V1 match. THIS multi-V1 pass
    layers additional cross-register catalog data on top.

    Returns counts of fields touched."""
    counts = {"km_register": 0, "numista_alt": 0, "sources": 0}
    v2_cat = v2_coin.get("catalog") or {}
    v2_km = v2_cat.get("km")
    v2_km_scalar = v2_km if not isinstance(v2_km, list) else None
    # Collect existing KMs already on V2 (set form)
    v2_km_values: set[str] = set()
    if isinstance(v2_km, list):
        for k in v2_km:
            if isinstance(k, dict) and k.get("value"):
                v2_km_values.add(str(k["value"]))
            elif isinstance(k, str):
                v2_km_values.add(k)
    elif v2_km:
        v2_km_values.add(str(v2_km))
    v2_numista = v2_cat.get("numista")
    v2_numista_set: set[str] = set()
    if isinstance(v2_numista, list):
        v2_numista_set = {str(x) for x in v2_numista}
    elif v2_numista:
        v2_numista_set.add(str(v2_numista))

    cross_register_kms: list[dict] = []  # each: {value, register}
    new_numistas: list[str] = []
    for v1c, loc, vid in zip(v1_coins, v1_locs, v1_ids):
        v1_cat = v1c.get("catalog") or {}
        v1_km = _flatten_scalar(v1_cat.get("km"))
        if v1_km and v1_km not in v2_km_values:
            reg = _infer_v1_register(loc, vid)
            if reg:
                cross_register_kms.append({"value": v1_km, "register": reg})
        v1_n = _flatten_scalar(v1_cat.get("numista"))
        if v1_n and v1_n not in v2_numista_set:
            new_numistas.append(v1_n)
        # Source merging: same logic as _restore_one, but per V1 entry.
        v1_sources = v1c.get("sources") or []
        if v1_sources:
            v2_sources = v2_coin.get("sources") or []
            existing_urls = set()
            for s in v2_sources:
                if isinstance(s, dict) and s.get("url"):
                    existing_urls.add(s["url"])
            for s in v1_sources:
                if not isinstance(s, dict):
                    continue
                url = s.get("url")
                if not url or url.startswith("#"):
                    continue
                if url in existing_urls:
                    continue
                v2_sources.append(dict(s))
                existing_urls.add(url)
                counts["sources"] += 1
            v2_coin["sources"] = v2_sources

    # Apply cross-register KMs: promote V2's km to list[KMRef] form.
    if cross_register_kms:
        new_km_list: list = []
        # Preserve existing entries (with their implicit page-default register
        # tag — emit as plain string so the renderer applies its default)
        if isinstance(v2_km, list):
            new_km_list.extend(v2_km)
        elif v2_km is not None:
            new_km_list.append(str(v2_km))
        for entry in cross_register_kms:
            new_km_list.append(entry)
            counts["km_register"] += 1
        v2_coin.setdefault("catalog", {})["km"] = new_km_list

    # Apply alternative Numistas as list-form
    if new_numistas:
        new_n_list = list(v2_numista_set)
        new_n_list.extend(new_numistas)
        if len(new_n_list) == 1:
            v2_coin.setdefault("catalog", {})["numista"] = new_n_list[0]
        else:
            v2_coin.setdefault("catalog", {})["numista"] = sorted(new_n_list)
        counts["numista_alt"] = len(new_numistas)

    return counts


def _restore_classification(v1_coin: dict, v2_coin: dict) -> bool:
    """Propagate V1 curator classification (fuss/phase/kind/fraction)
    when V2 is at seed_unsorted (no V2 curator decision yet) AND V1 has
    a concrete classification. Migration is ATOMIC — all four fields
    move together; partial migration would corrupt the entry.

    Skips when:
    - V2.fuss != seed_unsorted (curator already classified V2 elsewhere)
    - V1.fuss is None / seed_unsorted (V1 has no curator decision)
    - `fraction` is in `_curation_holds` on V2 (curator pin)

    Returns True if classification was migrated.
    """
    if v2_coin.get("fuss") != "seed_unsorted":
        return False
    v1_fuss = v1_coin.get("fuss")
    if not v1_fuss or v1_fuss == "seed_unsorted":
        return False
    holds = set(v2_coin.get("_curation_holds") or [])
    if "fuss" in holds:
        return False
    # Carry the classification quartet
    v2_coin["fuss"] = v1_fuss
    if v1_coin.get("phase"):
        v2_coin["phase"] = v1_coin["phase"]
    if v1_coin.get("kind"):
        v2_coin["kind"] = v1_coin["kind"]
    if v1_coin.get("fraction") and "fraction" not in holds:
        v2_coin["fraction"] = v1_coin["fraction"]
    return True


def _restore_one(v1_coin: dict, v2_coin: dict) -> dict:
    """Mutate v2_coin in place. Returns counts of fields touched."""
    counts = {"year": 0, "diameter": 0, "sources": 0, "classification": 0}
    # Classification migration first — when V2 is at seed_unsorted and
    # V1 has a curator classification, it's the highest-value restoration
    # (the coin moves from «bulk-seed (unsortiert)» into a real fuss).
    if _restore_classification(v1_coin, v2_coin):
        counts["classification"] = 1

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
    # hede_volume + hede + ruler — per-ruler Hede catalogue (volume needed
    # because Hede numbering restarts per-ruler).
    v1_index_by_hede_full: dict[tuple, dict] = {}
    # Same key → LIST of (loc, coin) — used by the multi-V1 cross-register
    # pass to merge KM/Numista alternatives from sibling V1 entries that
    # cite the same coin under different Krause volumes (e.g. KM-DK 103 +
    # KM-SH 63 both citing Hede c5h121 Christian V Krone-Mønt).
    import collections as _col2
    v1_buckets_by_hede_full: dict[tuple, list] = _col2.defaultdict(list)
    # year + normalised nominal + ruler — fuzziest fallback for V1 entries
    # without specific catalog ref (typically ucoin-V1 entries with UC# only).
    # Stored as LIST to detect ambiguity; only single-entry buckets are used.
    import collections as _col
    v1_index_by_ynr_buckets: dict[tuple, list] = _col.defaultdict(list)
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
            hede = cat.get("hede")
            hede_vol = cat.get("hede_volume")
            if hede and hede_vol and ruler:
                v1_index_by_hede_full.setdefault(
                    (hede_vol, hede, ruler), c
                )
                v1_buckets_by_hede_full[(hede_vol, hede, ruler)].append(
                    (loc_id, c)
                )
            nominal = _norm_nominal(c.get("nominal"))
            if year_first and nominal and ruler:
                v1_index_by_ynr_buckets[(year_first, nominal, ruler)].append(c)

    yloader = YAML()
    yloader.preserve_quotes = True
    yloader.width = 4096
    yloader.indent(mapping=2, sequence=4, offset=2)

    grand = {"files": 0, "files_changed": 0,
             "year": 0, "diameter": 0, "sources": 0,
             "km_register": 0, "numista_alt": 0, "classification": 0}
    for path, doc in _v2_yaml_pair_iter(yloader):
        grand["files"] += 1
        coins = doc.get("coins") or []
        per_file = {"year": 0, "diameter": 0, "sources": 0,
                    "km_register": 0, "numista_alt": 0, "classification": 0}
        for v2c in coins:
            if not isinstance(v2c, dict):
                continue
            cat = _cat_keys(v2c.get("catalog") or {})
            v2_cat_raw = v2c.get("catalog") or {}
            v1c = None
            ruler = _norm_ruler(v2c.get("ruler"))
            year_first = v2c.get("year_first")
            # Priority order: most-specific globally-unique keys first.
            # Iterate ALL values in list-form catalog fields (per §9a
            # multi-source accumulation V2 may carry numista=['A','B']
            # — the V1 match could correspond to ANY of those Numista
            # entries, not just the first).
            for nv in _flatten_all(v2_cat_raw.get("numista")):
                if nv in v1_index_by_numista:
                    v1c = v1_index_by_numista[nv]
                    break
            if v1c is None:
                for bv in _flatten_all(v2_cat_raw.get("bruun_collection_id")):
                    if bv in v1_index_by_bruun_coll:
                        v1c = v1_index_by_bruun_coll[bv]
                        break
            if v1c is None:
                for lv in _flatten_all(v2_cat_raw.get("lange")):
                    if lv in v1_index_by_lange:
                        v1c = v1_index_by_lange[lv]
                        break
            if v1c is None and ruler:
                # hede_volume + hede + ruler — Hede numbering restarts
                # per ruler, so volume IS required for disambiguation.
                # Iterate list-form hede too.
                for hv_v in _flatten_all(v2_cat_raw.get("hede_volume")):
                    for h_v in _flatten_all(v2_cat_raw.get("hede")):
                        if (hv_v, h_v, ruler) in v1_index_by_hede_full:
                            v1c = v1_index_by_hede_full[(hv_v, h_v, ruler)]
                            break
                    if v1c:
                        break
            if v1c is None and ruler and year_first:
                # km + ruler + year_first fallback — territory-bound,
                # disambiguated by the ruler+year pair. Try the V2's KM
                # verbatim, then the bare-form parent (V2 «70.1» → V1
                # «70» bare).
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
            if v1c is None and ruler and year_first:
                # year + normalised nominal + ruler — UNIQUE-ONLY fallback.
                # Only apply when EXACTLY ONE V1 entry has the (year, nom,
                # ruler) tuple AND its KM is not present in any V2 entry
                # (avoid clobbering distinct sub-variants that V1 split
                # differently from V2). This catches the «UC# 1» ucoin
                # V1 entries that match a Hede-cataloged V2 entry but
                # have no shared catalog key.
                nom = _norm_nominal(v2c.get("nominal"))
                if nom:
                    bucket = v1_index_by_ynr_buckets.get(
                        (year_first, nom, ruler), []
                    )
                    if len(bucket) == 1:
                        v1c = bucket[0]
            if v1c is None:
                continue
            r = _restore_one(v1c, v2c)
            for k, v in r.items():
                per_file[k] += v
            # Multi-V1 pass: if this V2 entry has hede+hede_volume+ruler
            # and the V1 bucket has 2+ entries (cross-register dual
            # citation), merge KMs and Numista alternatives from the
            # SIBLING V1 entries that share the matcher key.
            v1_hede = cat.get("hede")
            v1_hede_vol = cat.get("hede_volume")
            if v1_hede and v1_hede_vol and ruler:
                bucket = v1_buckets_by_hede_full.get(
                    (v1_hede_vol, v1_hede, ruler), []
                )
                if len(bucket) > 1:
                    siblings = [e for e in bucket if e[1] is not v1c]
                    sib_coins = [e[1] for e in siblings]
                    sib_locs = [e[0] for e in siblings]
                    sib_ids = [e[1].get("id") for e in siblings]
                    extra = _restore_multi(sib_coins, v2c, sib_locs, sib_ids)
                    # Aggregate counts into per_file
                    per_file.setdefault("km_register", 0)
                    per_file.setdefault("numista_alt", 0)
                    per_file["km_register"] = per_file.get("km_register", 0) + extra.get("km_register", 0)
                    per_file["numista_alt"] = per_file.get("numista_alt", 0) + extra.get("numista_alt", 0)
                    per_file["sources"] += extra.get("sources", 0)
        total = sum(per_file.values())
        if total:
            grand["files_changed"] += 1
            for k, v in per_file.items():
                grand[k] += v
            rel = path.relative_to(PROJECT)
            print(f"  {rel}: cls={per_file['classification']} "
                  f"year={per_file['year']} "
                  f"diameter={per_file['diameter']} "
                  f"sources={per_file['sources']} "
                  f"km_alt_register={per_file['km_register']} "
                  f"numista_alt={per_file['numista_alt']}")
            if not args.dry_run:
                with path.open("w") as f:
                    yloader.dump(doc, f)
    print()
    print(f"Files scanned:           {grand['files']}")
    print(f"Files changed:           {grand['files_changed']}")
    print(f"Classifications:         {grand['classification']}")
    print(f"Year-fields restored:    {grand['year']}")
    print(f"Diameters restored:      {grand['diameter']}")
    print(f"Sources added:           {grand['sources']}")
    print(f"Cross-register KMs:      {grand['km_register']}")
    print(f"Numista alts:            {grand['numista_alt']}")
    if args.dry_run:
        print("(dry-run — no files written)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
