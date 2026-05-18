#!/usr/bin/env python3
"""
Build the site from YAML data.

Usage:
  python scripts/build.py                        # full build
  python scripts/build.py --location schleswig_holstein   # single location
  python scripts/build.py --lang de              # single language
  python scripts/build.py --validate-only        # schema check, no render
  python scripts/build.py --debug                # dump intermediate JSON
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
from datetime import datetime
from pathlib import Path

import yaml
from jinja2 import Environment, FileSystemLoader, select_autoescape
from pydantic import ValidationError

# Make local lib importable when run as `python scripts/build.py`
sys.path.insert(0, str(Path(__file__).parent))

from lib import i18n
from lib.categorize import categorize
from lib.timeline import (
    compute_bar_layers, compute_coin_year_runs,
    compute_hover_zones, derive_holstein_mint_overrides,
)
from lib.compute import compute_location
from lib.render import build_env, generate_css
from lib.schema import Location, Fuss, I18nText


REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = REPO_ROOT / "data"
CONFIG_DIR = REPO_ROOT / "config"
TEMPLATE_DIR = REPO_ROOT / "templates"
SITE_DIR = REPO_ROOT / "site"
DEBUG_DIR = REPO_ROOT / "output" / "debug"

V2_CURATED_DIR = DATA_DIR / "v2" / "curated"
V2_SEED_DIR = DATA_DIR / "v2" / "seed"
V2_LOCATIONS_DIR = DATA_DIR / "v2" / "locations"

DEFAULT_LANGS = ["de", "en", "uk"]


def load_fuesse() -> dict[str, Fuss]:
    path = DATA_DIR / "shared" / "fuesse.yml"
    with open(path, encoding="utf-8") as f:
        raw = yaml.safe_load(f)
    
    fuesse = {}
    for fuss_id, data in raw.items():
        data["id"] = fuss_id
        fuesse[fuss_id] = Fuss(**data)
    return fuesse


def load_theme() -> dict:
    with open(CONFIG_DIR / "theme.yml", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_ui() -> dict:
    return i18n.load_ui(str(DATA_DIR / "i18n" / "ui.yml"))


def load_issuing_entities() -> dict:
    """Load political-entity definitions for the issuing_entity field."""
    path = DATA_DIR / "i18n" / "issuing_entities.yml"
    if not path.exists():
        return {}
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


_YEAR_PARSE_4DIGIT = re.compile(r"\b(1[5-9]\d{2})\b")
_YEAR_PARSE_CENTURY = re.compile(r"\b(\d{1,2})\.\s*Jh\.?")


def _landing_year_from(entry: dict) -> int:
    """Extract a chronological start year for landing-page sorting.

    Order of precedence:
      1. Explicit `year_from: int` on the entry (escape hatch).
      2. First 4-digit year in the prefix of `years_label.de`
         (the part before the `→` arrow).
      3. Century-form `NN. Jh.` in the same prefix → (NN-1) * 100.
      4. Fallback: 9999 (entry sorts last).
    """
    explicit = entry.get("year_from")
    if isinstance(explicit, int):
        return explicit
    label = ((entry.get("years_label") or {}).get("de") or "")
    prefix = re.split(r"\s*[→—\-]\s*", label, maxsplit=1)[0]
    m = _YEAR_PARSE_4DIGIT.search(prefix)
    if m:
        return int(m.group(1))
    m = _YEAR_PARSE_CENTURY.search(prefix)
    if m:
        return (int(m.group(1)) - 1) * 100
    return 9999


def load_german_fuesse() -> list[dict]:
    """Load the landing-page reference catalogue of German Müntzfüße.

    Returned as a raw list of dicts (NOT validated against Pydantic) — this
    file is purely a presentation catalogue for the landing page and is not
    cross-referenced against the per-coin `coin.fuss` field. Returns empty
    list if the file is absent.

    Sorted by chronological start year (parsed from `years_label.de`
    prefix, or taken from an optional explicit `year_from: int` field).
    Stable secondary sort by YAML position keeps insertion order among
    entries that resolve to the same year. The `order` mechanism that
    drives location-page timeline bars does NOT apply here — the
    landing intentionally surfaces a chronological view.
    """
    path = DATA_DIR / "shared" / "german_fuesse.yml"
    if not path.exists():
        return []
    with open(path, encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}
    entries = raw.get("entries", [])
    indexed = list(enumerate(entries))
    indexed.sort(key=lambda ie: (_landing_year_from(ie[1]), ie[0]))
    return [e for _, e in indexed]


def load_german_fuesse_references() -> dict | None:
    """Load the bibliography sidecar for the German Müntzfüße catalogue.

    Same convention as `data/locations/<loc>-references.yml`: a YAML
    file with `heading` (multilingual) and `entries` (each with id +
    multilingual content). Inline `<sup>` citations in the catalogue
    prose link by id; the landing template renders the section after
    the catalogue.
    """
    path = DATA_DIR / "shared" / "german_fuesse-references.yml"
    if not path.exists():
        return None
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


SEEDS_DIR = DATA_DIR / "seed"


def _hede_seed_id(hede_volume: str, hede_number: str) -> str:
    """Derive the seed coin id a Hede catalog ref would produce.

    Mirrors the id-template used by
    `scripts/maintenance/build_hede_denmark_seed.py`:
    `dk-hede-<volume><number>` (e.g. `c4h` + `115A` → `dk-hede-c4h115a`).

    Both volume and number are lowercased — Hede sub-letters are
    case-insensitive across catalogs and seed ids are generated lowercase.
    """
    return f"dk-hede-{hede_volume.lower().strip()}{hede_number.lower().strip()}"


def _weight_values(w) -> list[float]:
    """Extract numeric weights from `weight_rough_g`.

    The field tolerates two shapes per project schema:
      * scalar float                       — `weight_rough_g: 14.447`
      * list of {value, source} dicts      — `weight_rough_g: [{value: 14.4, source: ...}, ...]`
    Returns the list of all numeric values, used by the auto-suppress
    weight-mismatch guard.
    """
    if w is None:
        return []
    if isinstance(w, (int, float)):
        return [float(w)]
    if isinstance(w, list):
        out: list[float] = []
        for item in w:
            if isinstance(item, dict) and isinstance(item.get("value"), (int, float)):
                out.append(float(item["value"]))
            elif isinstance(item, (int, float)):
                out.append(float(item))
        return out
    return []


def _merge_seeds_into_raw(loc_id: str, raw: dict) -> list[tuple[str, int]]:
    """Auto-merge `data/seed/<source>/<loc_id>.yml` coin lists into the
    location's `raw['coins']` before schema validation.

    Each top-level subdirectory under `data/seed/` represents a source
    (e.g. `hede`, `bruun`); any *.yml file in that subdir whose stem
    matches the location id is treated as a seed side-car for this
    location and its `coins:` list is appended to the location's own
    coins. The seed file is the canonical intermediate — scoping
    (year cap, mint filter) happens at seed-generation time, not here;
    the build trusts what the file contains.

    Hede-seed auto-suppression
    --------------------------
    When a curated location coin already references a Hede catalog
    entry (catalog.hede + catalog.hede_volume), the corresponding
    seed coin produced by the Hede generator is REDUNDANT — its data
    has already been folded into the curated entry's sources. The
    merge filters those out automatically:

      1. Walk raw['coins'] (the curated location's own coins). For
         each coin with both `catalog.hede` and `catalog.hede_volume`,
         compute the seed-id template and add to a covered set.
      2. When merging the hede seed, skip every seed coin whose id
         appears in the covered set.

    Edge cases:
    - A curated coin may carry multiple Hede refs (rare; via list
      form in catalog.hede). Each entry contributes one suppression.
    - Year-mismatch safety: if covered-seed and would-be-suppressed
      seed have `year_first` differing by >10 years, the suppression
      is skipped and the pair is flagged (likely different sub-type
      that happens to share a catalog hede; would be an unusual
      curation, but better to surface than silently drop).
    - Bruun-seed and other future seed sources don't carry the
      `dk-hede-` id prefix and are unaffected — only the Hede seed
      is auto-suppressed against curated Hede refs.

    Returns the list of (source_subdir_name, coin_count) tuples for
    each merged file so the caller can print a one-line summary.
    `coin_count` is the NET count after suppression.

    Schema validation happens AFTER the merge (the assembled
    `raw['coins']` is what gets passed to `Location(**raw)`), so id
    collisions, missing fuss / phase references, and year-vs-phase
    range mismatches are caught there in one shot — no separate
    seed-validation pass needed.
    """
    if not SEEDS_DIR.exists():
        return []
    # Cross-location coverage: a Hede catalog entry may be curated in a
    # DIFFERENT location yaml than the one whose seed it sits in.
    # Concrete case: dk-hede-c4h178a/b (Glückstadt 1640-48 Søsling) sit
    # in `data/seed/hede/denmark.yml` (seed builder is denmark-named)
    # but the curated entry lives in `schleswig_holstein.yml` (per the
    # «move Glückstadt issues to SH yaml» convention). Without cross-
    # scan, those seed entries render as duplicates on the denmark
    # page even though they're covered elsewhere.
    #
    # Build a unified coverage set by scanning ALL location yamls' coins
    # for catalog.hede + catalog.hede_volume refs and adding the derived
    # seed-id (plus bare-basename variant) to the suppression set,
    # merged with the current location's own coverage.
    extra_curated_for_coverage: list[dict] = []
    locations_dir = DATA_DIR / "locations"
    if locations_dir.exists():
        for other_path in sorted(locations_dir.glob("*.yml")):
            if other_path.stem.endswith("-references"):
                continue
            if other_path.stem == loc_id:
                # Skip current location — its coverage comes from raw['coins'] below
                continue
            with open(other_path, encoding="utf-8") as of:
                other_doc = yaml.safe_load(of) or {}
            for oc in other_doc.get("coins") or []:
                if isinstance(oc, dict):
                    extra_curated_for_coverage.append(oc)

    # Pre-compute the suppression set + year/metal map from the curated coins.
    # We track the curated entry's metal because Hede refs frequently
    # appear as «cf. silver companion» citations on gold Portugaloser /
    # Ducat / Gold-Skilling entries — same Hede ref, different metal,
    # different coin. The metal-match check below skips suppression
    # whenever curated.metal differs from seed.metal, preventing those
    # cf-citations from incorrectly hiding the actual silver Hede-page
    # entry.
    #
    # We also derive a BARE-BASENAME variant (digits-only sub-num,
    # trailing letters stripped) and add it to the suppression set.
    # This catches the «parser bare-basename» artifact: Hede pages like
    # c5h107 describe sub-letters 107A and 107B sharing one spec block;
    # the parser emits one combined entry under the bare basename
    # `dk-hede-c5h107` (no trailing letter), while curators record the
    # actual sub-types as `hede: 107B` etc. The bare-basename seed
    # entry is therefore redundant whenever ANY sub-letter is curated.
    # Same metal + year guards apply.
    curated_coins = (raw.get("coins") or []) + extra_curated_for_coverage
    suppressed_ids: dict[str, dict] = {}  # seed_id → {year, metal, cur_id}
    for cc in curated_coins:
        if not isinstance(cc, dict):
            continue
        cat = cc.get("catalog") or {}
        if not isinstance(cat, dict):
            continue
        hv = (cat.get("hede_volume") or "").strip()
        hnum = cat.get("hede")
        if not (hv and hnum):
            continue
        # Catalog.hede is typically a scalar string but tolerate list shape
        hede_nums = hnum if isinstance(hnum, list) else [hnum]
        info = {
            "year_first": cc.get("year_first"),
            "metal": cc.get("metal"),
            "cur_id": cc.get("id"),
            "weights": _weight_values(cc.get("weight_rough_g")),
            "fineness": _weight_values(cc.get("fineness")),
        }
        for hn in hede_nums:
            if not hn:
                continue
            hn_str = str(hn).strip()
            seed_id = _hede_seed_id(hv, hn_str)
            suppressed_ids[seed_id] = info
            # Bare-basename variant: strip trailing letters from the
            # Hede sub-number (e.g. «107B» → «107»). When the sub-num
            # already has no letter suffix, no separate entry is added.
            bare_num = re.sub(r"[A-Za-z]+$", "", hn_str)
            if bare_num and bare_num != hn_str:
                bare_seed_id = _hede_seed_id(hv, bare_num)
                # Use setdefault so an explicit-letter entry's info
                # wins over a sibling sub-letter that arrives later.
                suppressed_ids.setdefault(bare_seed_id, info)

    merged: list[tuple[str, int]] = []
    for source_dir in sorted(p for p in SEEDS_DIR.iterdir() if p.is_dir()):
        seed_path = source_dir / f"{loc_id}.yml"
        if not seed_path.exists():
            continue
        with open(seed_path, encoding="utf-8") as sf:
            seed_doc = yaml.safe_load(sf) or {}
        seed_coins = seed_doc.get("coins") or []
        if not seed_coins:
            continue
        # Strip generator-internal metadata fields that the seed
        # toolchain uses but the Coin schema doesn't know about. The
        # Coin schema is `extra="forbid"`, so unknown keys must be
        # dropped before merge or validation fails. Currently only
        # `_curation_holds` (see scripts/maintenance/build_*_seed.py),
        # but any future underscore-prefixed seed-meta field follows
        # the same convention.
        for coin in seed_coins:
            if isinstance(coin, dict):
                for k in [k for k in coin if k.startswith("_")]:
                    coin.pop(k, None)

        # Auto-suppress seed coins whose Hede ref is already covered
        # by a curated entry. Safety check: only suppress when years
        # plausibly match (within 10 years) — large discrepancy means
        # the curated entry probably describes a different sub-type
        # that just happens to share a catalog hede number, and we
        # want the dup to surface for manual review rather than
        # silently merge.
        #
        # Exception: Hede pages occasionally describe yearless («u. å.»
        # / «uden år») types whose canonical year is undefined on the
        # coin itself. Seed entries inherit the parser's reign-range
        # interpretation of u.år («u. å. (1670–1699)» → year_first
        # 1670, year_last 1699), while curators attach a specific year
        # from a Bruun specimen attribution. The year discrepancy is
        # then an artefact of u.år interpretation, NOT evidence of
        # different sub-types. When the seed's year_label opens with
        # «u.» (Danish «uden»), the year-mismatch safety is bypassed
        # and suppression proceeds.
        kept: list[dict] = []
        suppressed_count = 0
        year_mismatch_count = 0
        metal_mismatch_count = 0
        weight_mismatch_count = 0
        for coin in seed_coins:
            cid = coin.get("id") if isinstance(coin, dict) else None
            if cid and cid in suppressed_ids:
                info = suppressed_ids[cid]
                cur_year = info["year_first"]
                cur_metal = info["metal"]
                cur_weights = info["weights"]
                seed_year = coin.get("year_first") if isinstance(coin, dict) else None
                seed_metal = coin.get("metal") if isinstance(coin, dict) else None
                seed_weights = _weight_values(coin.get("weight_rough_g") if isinstance(coin, dict) else None)
                seed_label = (coin.get("year_label") or "").strip().lower() if isinstance(coin, dict) else ""
                is_undated = seed_label.startswith("u.") or seed_label.startswith("u å")
                # Metal-mismatch guard: when curated and seed disagree
                # on metal, the Hede ref on the curated entry is almost
                # certainly a «cf. companion» citation (e.g. a gold
                # Portugaloser citing the silver Hede sub-type whose
                # die design it shares). Do NOT suppress the silver
                # Hede entry — it's a separate coin.
                #
                # Fineness-similarity escape hatch: when both entries
                # publish fineness within ±2% of each other, the metal
                # label disagreement is almost certainly a labelling
                # artefact (e.g. seed builder defaults `metal: silver`
                # for any non-gold non-bronze entry, while a curator
                # correctly tags `metal: billon` for fineness 0.312).
                # Same metal content = same physical coin regardless
                # of label — suppression proceeds.
                cur_fin = info["fineness"]
                seed_fin = _weight_values(coin.get("fineness") if isinstance(coin, dict) else None)
                fineness_match = False
                if cur_fin and seed_fin:
                    cur_lo, cur_hi = min(cur_fin), max(cur_fin)
                    seed_lo, seed_hi = min(seed_fin), max(seed_fin)
                    if cur_hi > 0 and seed_hi > 0:
                        # Compare midpoints with relative tolerance
                        cur_mid = (cur_lo + cur_hi) / 2
                        seed_mid = (seed_lo + seed_hi) / 2
                        if abs(cur_mid - seed_mid) / max(cur_mid, seed_mid) < 0.02:
                            fineness_match = True
                if (
                    cur_metal
                    and seed_metal
                    and cur_metal != seed_metal
                    and not fineness_match
                ):
                    metal_mismatch_count += 1
                    kept.append(coin)
                    continue
                # Weight-mismatch guard: same Hede ref + same metal but
                # weights differ by >25% indicates different denominations
                # (e.g. ½ Speciedaler 14.4g vs 24 Skilling 9.17g — both
                # claim hede sub-letter «12A» across Krause-Denmark /
                # Krause-Norway register volumes, but they're physically
                # different coins). Weight ratio min/max < 0.75 → skip.
                if cur_weights and seed_weights:
                    cur_lo, cur_hi = min(cur_weights), max(cur_weights)
                    seed_lo, seed_hi = min(seed_weights), max(seed_weights)
                    overall_min = min(cur_lo, seed_lo)
                    overall_max = max(cur_hi, seed_hi)
                    if overall_max > 0 and (overall_min / overall_max) < 0.75:
                        weight_mismatch_count += 1
                        kept.append(coin)
                        continue
                if (
                    seed_year is not None
                    and cur_year is not None
                    and abs(seed_year - cur_year) > 10
                    and not is_undated
                ):
                    year_mismatch_count += 1
                    kept.append(coin)
                    continue
                suppressed_count += 1
                continue
            kept.append(coin)
        if suppressed_count:
            print(
                f"   ⚙  {loc_id}: suppressed {suppressed_count} {source_dir.name} "
                f"seed coin(s) covered by curated Hede refs"
            )
        if metal_mismatch_count:
            print(
                f"   ℹ  {loc_id}: {metal_mismatch_count} {source_dir.name} seed "
                f"coin(s) share a curated Hede ref but differ on metal "
                f"(cf-companion citation pattern; both kept)"
            )
        if weight_mismatch_count:
            print(
                f"   ℹ  {loc_id}: {weight_mismatch_count} {source_dir.name} seed "
                f"coin(s) share a curated Hede ref but weights differ "
                f">25% (cross-register KM clash or different denomination; "
                f"both kept)"
            )
        if year_mismatch_count:
            print(
                f"   ⚠  {loc_id}: {year_mismatch_count} {source_dir.name} seed "
                f"coin(s) match a curated Hede ref but with year_first "
                f">10y apart — kept both for manual review"
            )

        raw.setdefault("coins", []).extend(kept)
        merged.append((source_dir.name, len(kept)))
    return merged


# =============================================================================
# V2 entity-keyed assembly (per docs/V2_PIPELINE.md §4 / §2.1)
# =============================================================================

_V2_CURATED_CACHE: dict[str, list[dict]] | None = None


def _load_v2_curated() -> dict[str, list[dict]]:
    """Load every `data/v2/curated/<entity>.yml` once per process and return
    {entity_id: [coin_dict, ...]}. Each coin dict is the raw YAML value
    BEFORE pydantic instantiation (so dict-form phase / km can still be
    resolved per assembling location)."""
    global _V2_CURATED_CACHE
    if _V2_CURATED_CACHE is not None:
        return _V2_CURATED_CACHE
    cache: dict[str, list[dict]] = {}
    if V2_CURATED_DIR.exists():
        for path in sorted(V2_CURATED_DIR.glob("*.yml")):
            with open(path, encoding="utf-8") as f:
                doc = yaml.safe_load(f) or {}
            cache[doc.get("id", path.stem)] = doc.get("coins", []) or []
    _V2_CURATED_CACHE = cache
    return cache


def _load_v2_seed_entries() -> list[dict]:
    """Load every `data/v2/seed/<source>/<entity>.yml`, flatten into a single
    list of coin dicts. Empty until Phase 3 lands. Each coin dict carries a
    `_v2_seed_source` field (added here) so the inverse-index step can
    track provenance."""
    out: list[dict] = []
    if not V2_SEED_DIR.exists():
        return out
    for source_dir in sorted(V2_SEED_DIR.iterdir()):
        if not source_dir.is_dir():
            continue
        for path in sorted(source_dir.glob("*.yml")):
            with open(path, encoding="utf-8") as f:
                doc = yaml.safe_load(f) or {}
            for c in doc.get("coins", []) or []:
                c = dict(c)
                c["_v2_seed_source"] = source_dir.name
                out.append(c)
    return out


def _normalise_ie_to_list(ie) -> list[str]:
    """Return a list of entity tags from a scalar-or-list `issuing_entity`."""
    if ie is None:
        return []
    if isinstance(ie, list):
        return list(ie)
    return [ie]


def _resolve_dict_fields_per_location(coin: dict, loc_id: str, km_register: str | None) -> dict:
    """Return a shallow copy of `coin` where dict-form `phase` and
    `catalog.km` are resolved to the scalar value matching `loc_id` /
    `km_register`. Migration breadcrumbs (`v1_home_location`,
    `_migration_note`, `_migration_dup_origin_id`) are stripped. The
    returned dict is ready for `Coin(**dict)` instantiation."""
    from lib.v2_resolver import (
        resolve_phase_for_location,
        resolve_km_for_location,
        strip_v2_breadcrumbs,
    )
    out = strip_v2_breadcrumbs(coin)
    # Strip underscore-prefixed seed-generator metadata fields. Coin
    # schema is `extra='forbid'`; V1's `_merge_seeds_into_raw` applies
    # the same strip at line ~347. V2 mirrors here for consistency.
    out = {k: v for k, v in out.items() if not k.startswith("_")}
    cid = out.get("id")

    phase = out.get("phase")
    if isinstance(phase, dict):
        out = {**out, "phase": resolve_phase_for_location(phase, loc_id, cid)}

    catalog = out.get("catalog")
    if isinstance(catalog, dict):
        km = catalog.get("km")
        if isinstance(km, dict):
            resolved_km = resolve_km_for_location(km, km_register or "", cid)
            out = {**out, "catalog": {**catalog, "km": resolved_km}}

    return out


def _assemble_v2_location(loc_id: str, raw: dict) -> int:
    """Populate `raw['coins']` from V2 entity-keyed curated + seed files.

    Per V2_PIPELINE.md §4.2 two-pass walk:

      Pass 1 — direct membership. Walk each entity file `<ent>.yml` for
      `ent in consumes_entities` and pick up every coin that lives there.

      Pass 2 — inverse index for multi-entity coins. Scan ALL entity
      files; surface any coin whose list-form `issuing_entity` intersects
      with `consumes_entities` AND whose id wasn't seen in Pass 1. This
      handles the case where a multi-entity coin lives in an entity file
      NOT consumed by this location, but the coin's list contains an
      entity that IS consumed.

    Seed entries with non-null `promoted_to` are dropped (the curated
    entry already represents them).

    Dict-form `phase` and `catalog.km` are resolved per the current
    location at assembly time. V2 migration breadcrumbs are stripped.

    Returns the number of coins assembled.
    """
    consumes_entities = raw.get("consumes_entities") or []
    if not consumes_entities:
        return 0
    consumes_set = set(consumes_entities)

    km_register = raw.get("km_register")
    by_entity = _load_v2_curated()
    seed_entries = _load_v2_seed_entries()

    assembled: list[dict] = []
    seen_ids: set[str] = set()

    # ---- Pass 1: direct membership ---------------------------------------
    for ent in consumes_entities:
        for coin in by_entity.get(ent, []):
            cid = coin.get("id")
            if not cid or cid in seen_ids:
                continue
            if coin.get("promoted_to"):
                continue
            assembled.append(_resolve_dict_fields_per_location(coin, loc_id, km_register))
            seen_ids.add(cid)

    # ---- Pass 2: inverse-index for multi-entity coins --------------------
    for ent, coins in by_entity.items():
        if ent in consumes_set:
            continue  # already handled in Pass 1
        for coin in coins:
            cid = coin.get("id")
            if not cid or cid in seen_ids:
                continue
            ie_list = _normalise_ie_to_list(coin.get("issuing_entity"))
            if not (set(ie_list) & consumes_set):
                continue
            if coin.get("promoted_to"):
                continue
            assembled.append(_resolve_dict_fields_per_location(coin, loc_id, km_register))
            seen_ids.add(cid)

    # ---- Seed entries (Phase 3 output; empty until then) ----------------
    for coin in seed_entries:
        cid = coin.get("id")
        if not cid or cid in seen_ids:
            continue
        ie_list = _normalise_ie_to_list(coin.get("issuing_entity"))
        if not (set(ie_list) & consumes_set):
            continue
        if coin.get("promoted_to"):
            continue
        # Strip seed-side bookkeeping field before pydantic instantiation.
        c = {k: v for k, v in coin.items() if k != "_v2_seed_source"}
        assembled.append(_resolve_dict_fields_per_location(c, loc_id, km_register))
        seen_ids.add(cid)

    # ---- Per-coin pre-filter: phase definition must exist on this page ----
    # An entity file may legitimately carry coins whose `fuss` or `phase` is
    # not defined on this consumer's location yaml — e.g. Christian-IV
    # Haderslev coins (reichsdukatenfuss Phase I 1591-1593) live in
    # royal_holstein.yml; DK page accommodates them via wide Phase-I range,
    # but the SH page's reichsdukatenfuss Phase I starts at 1600. Rather
    # than hard-fail the whole V2 build on this mismatch, we drop the coin
    # from this specific assembly with a one-line summary. The coin is NOT
    # lost — it surfaces on the OTHER consumer pages whose phase definitions
    # do accommodate it. Users iterating in Phase 8 can either widen this
    # page's phase ranges OR re-tag the coin's phase as dict-form
    # `{denmark: I, schleswig_holstein: II}` per V2_PIPELINE.md §5.
    phases_map = raw.get("phases") or {}
    kept: list[dict] = []
    dropped: list[tuple[str, str]] = []
    for c in assembled:
        fuss = c.get("fuss")
        phase = c.get("phase")  # already scalar after _resolve_dict_fields
        cid = c.get("id")
        if fuss not in phases_map:
            dropped.append((cid, f"fuss '{fuss}' not on this page"))
            continue
        ph_defs = phases_map[fuss] or []
        ph_ids = {p.get("id") if isinstance(p, dict) else getattr(p, "id", None) for p in ph_defs}
        if phase not in ph_ids:
            dropped.append((cid, f"phase '{phase}' not defined for fuss '{fuss}'"))
            continue
        # Year-range sanity: phase entry has year_from/year_to envelope.
        year_first = c.get("year_first")
        if year_first is not None:
            match = next((p for p in ph_defs
                          if (p.get("id") if isinstance(p, dict) else getattr(p, "id", None)) == phase), None)
            if match is not None:
                yf = match.get("year_from") if isinstance(match, dict) else getattr(match, "year_from", None)
                yt = match.get("year_to") if isinstance(match, dict) else getattr(match, "year_to", None)
                if yf is not None and yt is not None and (year_first < yf - 1 or year_first > yt + 1):
                    dropped.append((cid, f"year_first {year_first} outside phase {phase} [{yf}, {yt}]"))
                    continue
        kept.append(c)

    if dropped:
        print(f"   ⚠  v2/{loc_id}: dropped {len(dropped)} coin(s) — not compatible "
              f"with this page's phase definitions:")
        for cid, why in dropped[:5]:
            print(f"      • {cid}: {why}")
        if len(dropped) > 5:
            print(f"      • ... and {len(dropped) - 5} more (use phase dict-form per "
                  f"V2_PIPELINE.md §5 to render on both DK + SH)")

    raw["coins"] = kept
    # consumes_entities was a V2-only sidecar field — `Location` allows
    # extras (`model_config.extra='allow'`), so it survives the
    # instantiation as `_consumes_entities`-style metadata. No strip needed.
    return len(kept)


def load_v2_locations(filter_id: str | None = None) -> list[Location]:
    """Phase 4.2 V2 location loader. Reads `data/v2/locations/<loc>.yml`
    (display-meta only, no coins), assembles coins via
    `_assemble_v2_location()`, then validates as `Location`. Returns
    [] if `data/v2/locations/` is empty (V2 build is a no-op then)."""
    if not V2_LOCATIONS_DIR.exists():
        return []
    locations = []
    for path in sorted(V2_LOCATIONS_DIR.glob("*.yml")):
        if path.stem.endswith("-references"):
            continue
        if filter_id and path.stem != filter_id:
            continue
        with open(path, encoding="utf-8") as f:
            raw = yaml.safe_load(f) or {}
        n_assembled = _assemble_v2_location(path.stem, raw)
        if n_assembled:
            print(f"   🌱 v2/{path.stem}: assembled {n_assembled} coin(s) "
                  f"from {len(raw.get('consumes_entities') or [])} entity file(s)")
        try:
            loc = Location(**raw)
            # Attach references sidecar from V1 (V2 shares references with V1).
            v1_ref_path = DATA_DIR / "locations" / f"{path.stem}-references.yml"
            if v1_ref_path.exists():
                with open(v1_ref_path, encoding="utf-8") as rf:
                    loc._references_data = yaml.safe_load(rf)
            else:
                loc._references_data = None
            locations.append(loc)
        except ValidationError as e:
            print(f"❌ V2 schema errors in v2/{path.name}:")
            print(e)
            raise
    return locations


def load_locations(filter_id: str | None = None) -> list[Location]:
    locations = []
    for path in sorted((DATA_DIR / "locations").glob("*.yml")):
        # Skip reference sidecar files
        if path.stem.endswith("-references"):
            continue
        if filter_id and path.stem != filter_id:
            continue
        with open(path, encoding="utf-8") as f:
            raw = yaml.safe_load(f)
        seed_merges = _merge_seeds_into_raw(path.stem, raw)
        if seed_merges:
            parts = [f"{n} from {src}" for src, n in seed_merges]
            print(f"   🌱 {path.stem}: merged {sum(n for _, n in seed_merges)} "
                  f"seed coins ({', '.join(parts)})")
        try:
            loc = Location(**raw)
            # Attach references sidecar if present
            ref_path = path.parent / f"{path.stem}-references.yml"
            if ref_path.exists():
                with open(ref_path, encoding="utf-8") as rf:
                    loc._references_data = yaml.safe_load(rf)
            else:
                loc._references_data = None
            locations.append(loc)
        except ValidationError as e:
            print(f"❌ Schema errors in {path.name}"
                  f"{' (incl. seed merges)' if seed_merges else ''}:")
            print(e)
            raise
    return locations


def cross_ref_check(locations: list[Location], fuesse: dict[str, Fuss]) -> bool:
    all_ok = True
    for loc in locations:
        errors = loc.validate_cross_refs(fuesse)
        if errors:
            all_ok = False
            print(f"❌ Cross-reference errors in '{loc.id}':")
            for err in errors:
                print(f"   {err}")
    return all_ok


def dump_debug_computed(loc_id: str, computed) -> None:
    DEBUG_DIR.mkdir(parents=True, exist_ok=True)
    path = DEBUG_DIR / f"{loc_id}.computed.json"
    with open(path, "w", encoding="utf-8") as f:
        data = []
        for cc in computed:
            d = cc.raw.model_dump(exclude_none=True)
            d["_computed"] = {
                "weight_fein_g": cc.weight_fein_g,
                "soll_fein_g": cc.soll_fein_g,
                "delta_g": cc.delta_g,
                "delta_pct": cc.delta_pct,
                "within_remedium": cc.within_remedium,
                "implied_fuss": cc.implied_fuss,
            }
            if cc.alts:
                d["_computed"]["alts"] = [
                    {
                        "source": a.source,
                        "weight_rough_g": a.weight_rough_g,
                        "fineness": a.fineness,
                        "diameter_mm": a.diameter_mm,
                        "weight_fein_g": a.weight_fein_g,
                        "delta_g": a.delta_g,
                        "delta_pct": a.delta_pct,
                        "within_remedium": a.within_remedium,
                        "implied_fuss": a.implied_fuss,
                    } for a in cc.alts
                ]
            data.append(d)
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)
    print(f"   ↳ Wrote {path.relative_to(REPO_ROOT)}")


def build_location(
    loc: Location,
    fuesse: dict[str, Fuss],
    theme: dict,
    ui: dict,
    languages: list[str],
    env: Environment,
    debug: bool = False,
    repo_url: str = "",
    issuing_entities: dict | None = None,
    base_url: str = "",
    output_root: Path | None = None,
) -> None:
    """Render one location to `<output_root>/<loc.id>/<lang>/index.html`.
    `output_root` defaults to the V1 site/ directory; V2 passes
    site/v2/ to write under that subtree (per V2_PIPELINE.md §3.8).
    The template + assembly logic is shared between V1 and V2 — only
    the output path branches."""
    if output_root is None:
        output_root = SITE_DIR
    print(f"🏛️  Building {loc.id} ({len(loc.coins)} coins) → {output_root.relative_to(REPO_ROOT)}/")
    
    computed = compute_location(loc, fuesse)
    if debug:
        dump_debug_computed(loc.id, computed)
    
    tree = categorize(loc, computed, fuesse)

    # Per-location set of issuing entities that actually have coins here.
    # The filter strip in the template iterates the global registry but
    # SKIPS entries not in this set, so a chip with no coins to toggle
    # (e.g. `prussian_province` in schleswig_holstein.yml) doesn't render at all.
    # V2: `coin.issuing_entity` may be a list of strings (joint-jurisdiction
    # coins per V2_PIPELINE.md §3.10) — flatten the list into individual tags.
    active_entity_ids = set()
    for c in loc.coins:
        ie = c.issuing_entity
        if ie is None:
            continue
        if isinstance(ie, list):
            active_entity_ids.update(ie)
        else:
            active_entity_ids.add(ie)

    # Pre-compute the up-to-six period × scope layers for each timeline bar.
    # Empty when this location has no timeline (e.g. lubeck stub).
    bar_layers = {}
    coin_years = {}
    hover_zones = {}
    if loc.timeline:
        # Auto-sync `events.first_mint.holstein` / `last_mint.holstein`
        # to the actual SH coin spans so a freshly-added Bruun-era
        # Speciedaler 1859 instantly shifts the mint layer right, and a
        # curator-set patent year (e.g. 10½-Krone-Fuß first_mint=1644
        # while the first physical strike is 1645) reflects the data,
        # not the decree. Other locations are no-ops.
        mint_overrides = derive_holstein_mint_overrides(loc, fuesse)
        if mint_overrides:
            fuesse_for_bars = {**fuesse, **mint_overrides}
            diffs = []
            for fid, new_f in mint_overrides.items():
                old_lm = fuesse[fid].events.last_mint.holstein
                new_lm = new_f.events.last_mint.holstein
                old_fm = fuesse[fid].events.first_mint.holstein
                new_fm = new_f.events.first_mint.holstein
                if new_fm != old_fm or new_lm != old_lm:
                    diffs.append(
                        f"{fid}: {old_fm}–{old_lm} → {new_fm}–{new_lm}"
                    )
            if diffs:
                print(f"   📐 Mint-event auto-sync ({len(diffs)} fuesse): "
                      + "; ".join(diffs))
        else:
            fuesse_for_bars = fuesse
        bar_layers = compute_bar_layers(
            loc.timeline.bars, fuesse_for_bars,
            loc.timeline.year_from, loc.timeline.year_to,
            scope_mode=loc.timeline.scope_mode,
        )
        # Per-bar list of consecutive-year runs marking every year a coin
        # was actually minted under that stope (per data/locations/<loc>.yml
        # coin entries). Renders as 1-year-wide rectangles overlaid on the
        # layered period × scope bar.
        coin_years = compute_coin_year_runs(
            loc.timeline.bars, computed,
            loc.timeline.year_from, loc.timeline.year_to,
        )
        # Hover zones — segments where the active layer set stays constant.
        # Each zone becomes a transparent overlay div with a static
        # `data-tooltip` aggregating all active layers' texts (template
        # builds the joined text from per-layer tooltip parts).
        hover_zones = compute_hover_zones(
            bar_layers,
            loc.timeline.year_from, loc.timeline.year_to,
        )

    # Resolve references (from sidecar YAML) if present
    references_data = getattr(loc, '_references_data', None)
    
    generated_date = datetime.now().strftime("%Y-%m-%d")
    
    tmpl = env.get_template("location.html.j2")
    
    for lang in languages:
        # Pre-resolve references for this language
        refs_for_lang = None
        if references_data:
            refs_for_lang = {
                'heading': i18n.t(references_data.get('heading'), lang),
                'entries': [
                    {'id': e['id'], 'content': i18n.t(e.get('content'), lang)}
                    for e in references_data.get('entries', [])
                    if i18n.t(e.get('content'), lang)
                ]
            }
        
        html = tmpl.render(
            tree=tree,
            ui=ui,
            theme=theme,
            lang=lang,
            languages=languages,
            references=refs_for_lang,
            generated_date=generated_date,
            repo_url=repo_url,
            base_url=base_url,
            issuing_entities=issuing_entities or {},
            active_entity_ids=active_entity_ids,
            bar_layers=bar_layers,
            coin_years=coin_years,
            hover_zones=hover_zones,
            ui_get=lambda k, l=lang: i18n.ui_get(ui, k, l),
            t=lambda v, l=lang: i18n.t(v, l),
            fmt_num=lambda v, **kw: i18n.fmt_num(v, lang, **kw),
            fmt_delta=lambda g, p: i18n.fmt_delta(g, p, lang),
            fmt_date=lambda d, l=lang: i18n.fmt_date(d, l),
        )

        out_dir = output_root / loc.id / lang
        out_dir.mkdir(parents=True, exist_ok=True)
        out_file = out_dir / "index.html"
        with open(out_file, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"   → {out_file.relative_to(REPO_ROOT)}")


def build_landing(
    locations: list[Location],
    ui: dict,
    theme: dict,
    languages: list[str],
    env: Environment,
    repo_url: str = "",
    base_url: str = "",
    contact_email: str = "",
    german_fuesse: list[dict] | None = None,
    german_fuesse_references: dict | None = None,
    include_seed: bool = False,
) -> None:
    tmpl = env.get_template("landing.html.j2")
    generated_date = datetime.now().strftime("%Y-%m-%d")

    # Locations with any `seed_unsorted` coin haven't been triaged into proper
    # Müntzfuß standards. In production we hide them entirely from the landing
    # (the per-location pages still build, so existing URLs keep working). In
    # local builds (`--include-seed`, on by default when --base-url is empty)
    # they appear on the landing too, with a muted 'seed' card variant so the
    # researcher can navigate to them while iterating.
    seed_ids = {
        loc.id for loc in locations
        if any(c.fuss == "seed_unsorted" for c in loc.coins)
    }
    if include_seed:
        # Stable-sort so non-seed locations land first on the grid; seed
        # locations follow. Within each group the original location load
        # order (alphabetical via glob) is preserved.
        visible_locations = sorted(locations, key=lambda l: l.id in seed_ids)
        if seed_ids:
            print(f"🌱 Landing shows {len(seed_ids)} seed location(s) "
                  f"(local-build mode): {', '.join(sorted(seed_ids))}")
    else:
        visible_locations = [loc for loc in locations if loc.id not in seed_ids]
        if seed_ids:
            print(f"🙈 Landing hides {len(seed_ids)} location(s) with unsorted "
                  f"seed entries: {', '.join(sorted(seed_ids))}")

    # Landing is generated per-language at /<lang>/index.html;
    # root / redirects to /de/ (or user's preferred language via JS — optional)
    for lang in languages:
        # Resolve references for this language (same shape as per-
        # location pages: heading + list of {id, content}).
        gf_refs_for_lang = None
        if german_fuesse_references:
            gf_refs_for_lang = {
                'heading': i18n.t(german_fuesse_references.get('heading'), lang),
                'entries': [
                    {'id': e['id'], 'content': i18n.t(e.get('content'), lang)}
                    for e in german_fuesse_references.get('entries', [])
                    if i18n.t(e.get('content'), lang)
                ]
            }

        html = tmpl.render(
            locations=visible_locations,
            seed_ids=seed_ids,
            ui=ui,
            theme=theme,
            lang=lang,
            languages=languages,
            generated_date=generated_date,
            repo_url=repo_url,
            base_url=base_url,
            contact_email=contact_email,
            german_fuesse=german_fuesse or [],
            german_fuesse_references=gf_refs_for_lang,
            ui_get=lambda k, l=lang: i18n.ui_get(ui, k, l),
            t=lambda v, l=lang: i18n.t(v, l),
            fmt_date=lambda d, l=lang: i18n.fmt_date(d, l),
        )
        out_dir = SITE_DIR / lang
        out_dir.mkdir(parents=True, exist_ok=True)
        with open(out_dir / "index.html", "w", encoding="utf-8") as f:
            f.write(html)
        print(f"🏠 Landing: {out_dir.relative_to(REPO_ROOT)}/index.html")

    # Root index.html — language redirect.
    # Priority: 1) lang cookie set by app.js on previous visit
    #           2) browser preference (navigator.language)
    #           3) fallback to 'en'
    root_html = f"""<!DOCTYPE html><html><head>
<meta charset="UTF-8">
<title>Müntzfüße</title>
<script>
const base = {base_url!r};
const langs = ['de', 'en', 'uk'];
const m = document.cookie.match(/(?:^|;\\s*)lang=([a-z]{{2}})/);
const cookieLang = m ? m[1] : null;
const browserLang = (navigator.language || 'en').slice(0, 2).toLowerCase();
let target = 'en';
if (langs.includes(cookieLang)) target = cookieLang;
else if (langs.includes(browserLang)) target = browserLang;
window.location.replace(base + '/' + target + '/');
</script>
<noscript><meta http-equiv="refresh" content="0; url={base_url}/en/"></noscript>
</head><body><p>Loading… <a href="{base_url}/en/">English</a> · <a href="{base_url}/de/">Deutsch</a> · <a href="{base_url}/uk/">Українська</a></p></body></html>"""
    with open(SITE_DIR / "index.html", "w", encoding="utf-8") as f:
        f.write(root_html)


def generate_assets(theme: dict) -> None:
    assets_dir = SITE_DIR / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)
    css = generate_css(theme)
    with open(assets_dir / "style.css", "w", encoding="utf-8") as f:
        f.write(css)
    print(f"🎨 CSS: site/assets/style.css ({len(css):,} bytes)")

    # Copy static assets (JS, images) from /assets → site/assets
    src_assets = REPO_ROOT / "assets"
    if src_assets.is_dir():
        for src in src_assets.iterdir():
            if src.is_file():
                dst = assets_dir / src.name
                shutil.copyfile(src, dst)
                print(f"📎 Asset: site/assets/{src.name} ({dst.stat().st_size:,} bytes)")


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--location", help="Build only this location (default: all)")
    p.add_argument("--lang", help="Build only this language (default: all)")
    p.add_argument("--debug", action="store_true", help="Dump intermediate JSON")
    p.add_argument("--validate-only", action="store_true", help="Check schema + cross-refs, don't render")
    p.add_argument("--clean", action="store_true", help="Remove site/ before building")
    p.add_argument("--repo-url", default="", help="URL for source data link in footer")
    p.add_argument("--base-url", default="", help="URL prefix for assets and inter-page "
                   "links. Empty for user pages or root-served sites; '/repo-name' for "
                   "GitHub Pages project sites. Trailing slash stripped automatically.")
    p.add_argument("--include-seed", dest="include_seed", action="store_true",
                   default=None,
                   help="Include locations that still have seed_unsorted coins on the "
                        "landing page (rendered as cards with a 'seed' tag and muted "
                        "styling). Default: auto-enable when --base-url is empty "
                        "(local builds), suppress in production CI builds.")
    p.add_argument("--no-include-seed", dest="include_seed", action="store_false",
                   help="Force-hide seed locations from the landing page even on local "
                        "builds (matches production behaviour).")
    # V2 pipeline flags (per docs/V2_PIPELINE.md §4.1). Default behaviour:
    # build V1 always; build V2 additionally if data/v2/locations/ is
    # non-empty. Output goes to site/v2/<loc>/<lang>/ alongside the V1
    # site/<loc>/<lang>/.
    p.add_argument("--v1-only", dest="v1_only", action="store_true",
                   help="Suppress the V2 build path even when data/v2/locations/ "
                        "is populated.")
    p.add_argument("--v2-only", dest="v2_only", action="store_true",
                   help="Skip the V1 build path; only build site/v2/<loc>/<lang>/. "
                        "Useful for fast V2 iteration when V1 is unchanged.")
    return p.parse_args()


def main():
    args = parse_args()

    # Normalise base_url: drop trailing slash so templates can use {{ base_url }}/path
    base_url = args.base_url.rstrip("/")

    # YAML integrity guard — runs BEFORE Pydantic validation because
    # Pydantic operates on the parsed dict, after PyYAML has silently
    # collapsed duplicate keys via last-wins. A botched edit that
    # duplicates a key (two `metal:` lines under one record) survives
    # schema validation and ships broken data; this AST walk catches it.
    from lib.yaml_check import check_data_directory
    print("🛡️  YAML integrity check (duplicate keys)...")
    n_dups = check_data_directory(Path("data"))
    if n_dups:
        print(f"\n❌ Found {n_dups} duplicate-key issue(s). Fix and rerun.")
        sys.exit(1)
    print("   ✓ No duplicate keys")
    print()

    # Load shared resources
    print("📦 Loading shared resources...")
    fuesse = load_fuesse()
    print(f"   Müntzfüße: {len(fuesse)} ({', '.join(fuesse)})")

    theme = load_theme()
    ui = load_ui()
    print(f"   UI strings: {len(ui)} keys")
    issuing_entities = load_issuing_entities()
    print(f"   Issuing entities: {len(issuing_entities)} ({', '.join(issuing_entities)})")
    german_fuesse = load_german_fuesse()
    print(f"   German Müntzfüße catalogue: {len(german_fuesse)} entries")
    german_fuesse_refs = load_german_fuesse_references()
    if german_fuesse_refs:
        print(f"   German Müntzfüße references: {len(german_fuesse_refs.get('entries', []))} entries")
    
    # Load locations
    locations = load_locations(filter_id=args.location)
    print(f"   Locations: {len(locations)} ({', '.join(l.id for l in locations)})")

    # V2 — load entity-keyed locations + assemble coins per consumes_entities.
    # Mode:
    #   * default        — V1 + V2 (if data/v2/locations/ non-empty)
    #   * --v1-only      — V1 alone
    #   * --v2-only      — V2 alone
    if args.v1_only and args.v2_only:
        print("\n❌ --v1-only and --v2-only are mutually exclusive.")
        sys.exit(1)
    v2_enabled = (not args.v1_only) and V2_LOCATIONS_DIR.exists() and any(V2_LOCATIONS_DIR.glob("*.yml"))
    v2_locations: list[Location] = []
    if v2_enabled:
        print()
        print("📦 Loading V2 entity-keyed locations...")
        v2_locations = load_v2_locations(filter_id=args.location)
        print(f"   V2 locations: {len(v2_locations)} "
              f"({', '.join(l.id for l in v2_locations)})")
    print()

    # Schema + cross-ref validation
    print("🔍 Validating cross-references...")
    if not cross_ref_check(locations, fuesse):
        print("\n❌ V1 validation failed. Fix errors above and rerun.")
        sys.exit(1)
    print("   ✓ V1 cross-references OK")
    if v2_enabled and v2_locations:
        if not cross_ref_check(v2_locations, fuesse):
            print("\n❌ V2 validation failed. Fix errors above and rerun.")
            sys.exit(1)
        print("   ✓ V2 cross-references OK")
    print()

    if args.validate_only:
        print("✅ Validation-only mode. No rendering performed.")
        return
    
    # Clean site/ if requested
    if args.clean and SITE_DIR.exists():
        shutil.rmtree(SITE_DIR)
        print("🗑️  Cleaned site/")
    
    SITE_DIR.mkdir(parents=True, exist_ok=True)
    
    # Render
    languages = [args.lang] if args.lang else DEFAULT_LANGS
    env = build_env(str(TEMPLATE_DIR))

    if not args.v2_only:
        for loc in locations:
            build_location(loc, fuesse, theme, ui, languages, env,
                           debug=args.debug, repo_url=args.repo_url,
                           issuing_entities=issuing_entities, base_url=base_url)

    if v2_enabled and v2_locations:
        print()
        print(f"📦 Rendering V2 pages → {(SITE_DIR / 'v2').relative_to(REPO_ROOT)}/")
        for loc in v2_locations:
            build_location(loc, fuesse, theme, ui, languages, env,
                           debug=args.debug, repo_url=args.repo_url,
                           issuing_entities=issuing_entities, base_url=base_url,
                           output_root=SITE_DIR / "v2")

    if len(locations) > 1 or not args.location:
        # Pull contact email from local.env (or process env). Falls back to
        # empty string → footer just hides the «Contact» link.
        from lib.env import load_local_env
        load_local_env()
        contact_email = os.environ.get("CONTACT_EMAIL", "")

        # Seed-locations on landing: explicit flag wins, otherwise auto-enable
        # for local builds (no --base-url set) and disable for production CI
        # (which always sets --base-url).
        if args.include_seed is None:
            include_seed = (base_url == "")
        else:
            include_seed = args.include_seed

        build_landing(locations, ui, theme, languages, env,
                      repo_url=args.repo_url, base_url=base_url,
                      contact_email=contact_email,
                      german_fuesse=german_fuesse,
                      german_fuesse_references=german_fuesse_refs,
                      include_seed=include_seed)

    generate_assets(theme)
    
    print()
    print(f"✅ Build complete: {SITE_DIR}/")


if __name__ == "__main__":
    main()
