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
    attach_visual_pieces,
    compute_bar_layers, compute_coin_year_runs,
    compute_hover_zones, derive_mint_overrides,
    founding_mint_start,
)
from lib.compute import compute_location
from lib.render import build_env, generate_css
from lib.schema import Location, Fuss, I18nText, Coin
from lib.v2_seed_writer import normalise_nominal_display
from lib.mint_registry import (
    CROWN_MINT_REALM as _CROWN_MINT_REALM,
    HOLSTEIN_CROWN_MINTS as _HOLSTEIN_CROWN_MINTS,
)


REPO_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = REPO_ROOT / "data"
CONFIG_DIR = REPO_ROOT / "config"
TEMPLATE_DIR = REPO_ROOT / "templates"
SITE_DIR = REPO_ROOT / "site"
DEBUG_DIR = REPO_ROOT / "output" / "debug"

V2_FINAL_DIR = DATA_DIR / "v2" / "final"
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


_HERO_REFS_RE = re.compile(
    r'(<span class="hs-lbl">[^<]*</span>\s*'
    r'<span class="hs-val">)\d+(<sub>[^<]*Referenzen[^<]*</sub></span>)',
    re.IGNORECASE,
)
_HERO_REFS_GENERIC_RE = re.compile(
    # Locate the hero «refs_unit» badge regardless of language. We
    # identify the badge by the presence of the `hs-stat` wrapper plus
    # the «hero.stat.quellen» label ABOVE the badge value — but since the
    # label is i18n'd, we anchor on the structural pattern: the LAST
    # `hs-stat` in the hero block that contains a numeric `hs-val` with a
    # `<sub>` child (the «Referenzen/References/Посилання» unit). This
    # regex matches conservatively only when the bibliography list is
    # present (caller checks for `<ol class="refs">`).
    r'(<div class="hs-stat">\s*'
    r'<span class="hs-lbl">[^<]*</span>\s*'
    r'<span class="hs-val">)(\d+)(<sub>[^<]*</sub></span>\s*</div>)',
    re.IGNORECASE,
)
_REFS_LI_VALUE_RE = re.compile(r'<li[^>]*value="(\d+)"')

_HERO_REFS_FULL_RE = re.compile(
    # Match the full `<div class="hs-stat">…</div>` wrapper that contains
    # a refs-unit `<sub>` (Referenzen / refs / посилань / Джерела). The
    # non-greedy `.*?` keeps the match scoped to a single hs-stat block.
    r'<div class="hs-stat">\s*<span class="hs-lbl">[^<]*</span>\s*'
    r'<span class="hs-val">\d+<sub>([^<]*)</sub></span>\s*</div>\s*',
    re.IGNORECASE | re.DOTALL,
)


def _strip_hero_refs_badge(html: str) -> str:
    """Remove the hero stat-badge whose `<sub>` label is a refs-unit
    synonym. Used when the page has zero bibliography entries (legacy +
    pool both empty). The template renders the badge unconditionally
    (`hero_refs=1` floor) so the post-process owns the strip-on-empty
    decision."""
    def _is_refs_unit(sub_text: str) -> bool:
        low = sub_text.lower()
        return any(
            t in low for t in
            ("referenz", "reference", "refs", "посилан", "поси­лан",
             "джерел")
        )

    def _repl(m: re.Match) -> str:
        if _is_refs_unit(m.group(1)):
            return ''
        return m.group(0)

    return _HERO_REFS_FULL_RE.sub(_repl, html)


def _patch_hero_refs_count(html: str) -> str:
    """Update the hero «Quellen N Referenzen» badge to reflect the total
    bibliography size (legacy + pool refs).

    The Jinja template emits `hero_refs = references.entries | length`
    which only sees the legacy `*-references.yml` entries. After
    `refs_pool.process_html` injects pool entries, the badge undercounts.
    Pre-existing symptom on the SH V2 page: «1 Referenzen» while the
    bibliography actually carries 50+ entries (1 legacy + 49 pool).

    Strategy: count `<li[^>]*value="N">` items inside the final
    `<ol class="refs">` block of the rendered HTML. Use that total to
    rewrite the hero badge's numeric value. Idempotent — re-running on
    already-patched HTML produces identical output.
    """
    # Locate the <ol class="refs"> block to count its <li> entries.
    ol_open = html.find('<ol class="refs">')
    ol_close = html.find('</ol>', ol_open) if ol_open >= 0 else -1
    if ol_open < 0 or ol_close < 0:
        li_count = 0
    else:
        block = html[ol_open:ol_close]
        li_count = len(_REFS_LI_VALUE_RE.findall(block))
    if li_count == 0:
        # Strip the hero «References» badge entirely — no bibliography.
        # Template sets hero_refs=1 as a floor so the badge always
        # renders; strip-on-zero keeps the no-refs case clean.
        return _strip_hero_refs_badge(html)
    # Update only the hero stat-badge whose <sub> label contains the
    # i18n'd «refs unit» word (Referenzen / References / Посилання).
    # We rewrite all hero badges to the live count — there's only ONE
    # such badge per page so the regex matches at most one location.
    new_html, n_sub = _HERO_REFS_GENERIC_RE.subn(
        lambda m: f"{m.group(1)}{li_count}{m.group(3)}", html, count=4
    )
    if n_sub == 0:
        return html
    # Multiple hero stats share the same pattern (Münzen, Müntzfüße,
    # Quellen). To avoid overwriting the wrong one, we filter: only the
    # badge whose <sub> text matches a known refs-unit synonym should be
    # updated. Walk matches manually.
    def _is_refs_unit(sub_text: str) -> bool:
        low = sub_text.lower()
        return any(
            t in low for t in
            ("referenz", "reference", "refs", "посилан", "поси­лан",
             "джерел")
        )

    def _repl(m: re.Match) -> str:
        # m.group(3) contains the `<sub>...</sub></span>...</div>` tail.
        sub_inner = re.search(r'<sub>([^<]*)</sub>', m.group(3))
        if sub_inner and _is_refs_unit(sub_inner.group(1)):
            return f"{m.group(1)}{li_count}{m.group(3)}"
        return m.group(0)

    return _HERO_REFS_GENERIC_RE.sub(_repl, html)


# =============================================================================
# V2 entity-keyed assembly (per docs/V2_PIPELINE.md §4 / §2.1)
# =============================================================================

_V2_FINAL_CACHE: dict[str, list[dict]] | None = None
_V2_SEED_CACHE: list[dict] | None = None
_V2_UNIFIED_CACHE: list[dict] | None = None
_V2_ABSORBED_SEED_IDS_CACHE: set[str] | None = None
# Global Fuß registry, parsed once — read by `_expand_outer_phase_span` for
# the founding-era `first_adoption` anchor + its `firm_<scope>` flag. Process-
# scoped like the V2 caches; a fresh `python scripts/build.py` re-parses.
_FUESSE_CACHE: dict[str, Fuss] | None = None


def _load_fuesse_cached() -> dict[str, Fuss]:
    global _FUESSE_CACHE
    if _FUESSE_CACHE is None:
        _FUESSE_CACHE = load_fuesse()
    return _FUESSE_CACHE

# Schema fields valid on the Coin model — derived once from the
# Pydantic model class. Used to strip seed-side raw extras at
# render time so source-specific builders (numista, bruun, …) can
# carry book-keeping fields like `numista_title`, `obverse`,
# `reverse`, `additional_litteratur`, `photo_credit`, etc. on
# their seed entries without breaking the strict Coin validation
# downstream.
_COIN_SCHEMA_FIELDS: frozenset[str] = frozenset(Coin.model_fields.keys())

# Valid Coin.metal values (mirrors the schema.py Coin.metal Literal). Used to
# skip out-of-scope seed entries — Numista/ucoin catalogue paper money /
# Notgeld too (metal 'paper'), which the precious-metal mission excludes and
# the schema can't represent. See the _assemble_v2_location seed-render pass.
_VALID_COIN_METALS: frozenset[str] = frozenset(
    {"silver", "gold", "billon", "copper", "lead", "bronze"})


def _load_v2_curated() -> dict[str, list[dict]]:
    """Load every `data/v2/final/<entity>.yml` once per process and return
    {entity_id: [coin_dict, ...]}. Each coin dict is the raw YAML value
    BEFORE pydantic instantiation (so dict-form phase / km can still be
    resolved per assembling location)."""
    global _V2_FINAL_CACHE
    if _V2_FINAL_CACHE is not None:
        return _V2_FINAL_CACHE
    cache: dict[str, list[dict]] = {}
    if V2_FINAL_DIR.exists():
        for path in sorted(V2_FINAL_DIR.glob("*.yml")):
            with open(path, encoding="utf-8") as f:
                doc = yaml.safe_load(f) or {}
            cache[doc.get("id", path.stem)] = doc.get("coins", []) or []
    _V2_FINAL_CACHE = cache
    return cache


def _load_v2_seed_entries() -> list[dict]:
    """Load every `data/v2/seed/<source>/<entity>.yml`, flatten into a single
    list of coin dicts. Empty until Phase 3 lands. Each coin dict carries a
    `_v2_seed_source` field (added here) so the inverse-index step can
    track provenance.

    Cached per process — the seed corpus is location-independent (the
    same 29 YAML files / 7.4 MB get walked for every page assembly), so
    re-parsing it 12 times during a full build was a major bottleneck.
    """
    global _V2_SEED_CACHE
    if _V2_SEED_CACHE is not None:
        return _V2_SEED_CACHE
    out: list[dict] = []
    if not V2_SEED_DIR.exists():
        _V2_SEED_CACHE = out
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
    _V2_SEED_CACHE = out
    return out


def _load_v2_seed_unified() -> list[dict]:
    """Load every `data/v2/seed_unified/<entity>.yml` once per process,
    flatten into a list of unified-entry dicts. Each entry has the shape
    `{id, composed_of, ...}` — used to walk the absorb chain from unified
    ids back to the V1 seed ids underlying them.

    Cached per process: the same 12 YAML files / 4.8 MB were previously
    parsed once per location during `_assemble_v2_location`, which was
    12× redundant for a full build.
    """
    global _V2_UNIFIED_CACHE
    if _V2_UNIFIED_CACHE is not None:
        return _V2_UNIFIED_CACHE
    out: list[dict] = []
    unified_dir = DATA_DIR / "v2" / "seed_unified"
    if not unified_dir.exists():
        _V2_UNIFIED_CACHE = out
        return out
    for path in sorted(unified_dir.glob("*.yml")):
        with open(path, encoding="utf-8") as f:
            doc = yaml.safe_load(f) or {}
        for uc in (doc.get("coins") or []):
            out.append(uc)
    _V2_UNIFIED_CACHE = out
    return out


def _compute_absorbed_seed_ids() -> set[str]:
    """Build the global set of V1 seed coin ids that are already
    represented in a foundation entry via the absorb chain. Walked once
    per process — the computation is purely a function of curated +
    seed-unified data, NOT of any single location's `consumes_entities`.

    Three levels (mirrors the original inline implementation in
    `_assemble_v2_location`, just hoisted out for caching):
      Level 1 — unified ids in foundation.composed_of (covers self-
        promoted D37/D39/D40 entries where unified id == seed-derived id).
      Level 2 — for each unified entry surfaced in level 1, walk its own
        `composed_of` for the underlying V1 seed ids.
      Level 3 — catalog-ref coverage. A V2 final entry may carry a
        `catalog.hede + catalog.hede_volume` ref WITHOUT explicit
        composed_of linkage (the entry was curated independently of the
        seed pipeline). The corresponding `dk-hede-<volume><number>` id
        is also marked absorbed so the seed-pass doesn't render a
        duplicate row.

    Before this hoist the function ran 12 times in a full build (once
    per location, each parsing the same V2 unified YAMLs); now it runs
    once.
    """
    global _V2_ABSORBED_SEED_IDS_CACHE
    if _V2_ABSORBED_SEED_IDS_CACHE is not None:
        return _V2_ABSORBED_SEED_IDS_CACHE

    by_entity = _load_v2_curated()
    absorbed: set[str] = set()

    # Level 1
    for ent_coins in by_entity.values():
        for c in ent_coins:
            for cid_composed in (c.get("composed_of") or []):
                absorbed.add(cid_composed)

    # Level 2
    for uc in _load_v2_seed_unified():
        uid = uc.get("id")
        if uid not in absorbed:
            continue
        for seed_id in (uc.get("composed_of") or []):
            absorbed.add(seed_id)

    # Level 3
    for ent_coins in by_entity.values():
        for c in ent_coins:
            cat = c.get("catalog") or {}
            hede_volume = cat.get("hede_volume")
            hede_num = cat.get("hede")
            if not (hede_volume and hede_num):
                continue
            hede_values = hede_num if isinstance(hede_num, list) else [hede_num]
            for hv in hede_values:
                seed_id = f"dk-hede-{hede_volume}{str(hv).lower()}"
                absorbed.add(seed_id)

    _V2_ABSORBED_SEED_IDS_CACHE = absorbed
    return absorbed


def _normalise_ie_to_list(ie) -> list[str]:
    """Return a list of entity tags from a scalar-or-list `issuing_entity`."""
    if ie is None:
        return []
    if isinstance(ie, list):
        return list(ie)
    return [ie]


# Crown-owned mint → realm where the coin actually circulated. The issuer-owns-
# mint guard (curator decision 2026-06-15): a coin's mint indicates circulation
# ONLY when the issuer owned that mint. Scoped below to `issuing_entity ==
# danish_realm` (Danish-crown realm coinage): a crown coin struck at a Holstein
# crown mint circulated in the duchies → royal_holstein; struck at Copenhagen
# too → danish_realm too. royal_holstein is politically WITHIN danish_realm, so
# a Holstein-ONLY strike is pure royal_holstein (NOT joint). Commission strikes
# of OTHER issuers at these mints (Schaumburg-Pinneberg pre-1640, Plön,
# Lübeck-bishopric, Lauenburg, the 1848 Provisional Government) keep their own
# entity — they are not danish_realm, so the scoping excludes them. See
# CLAUDE.md §7.
#
# `_CROWN_MINT_REALM` (display → realm) + `_HOLSTEIN_CROWN_MINTS` (the royal-
# Holstein gate subset) are imported from `lib.mint_registry` — the single
# source of truth for the crown-owned set (`_CROWN_OWNED`). This closes the
# 2026-07-08 gap where the hardcoded map covered only Altona + Glückstadt and
# silently dropped the other royal-Holstein crown mints (Haderslev / Flensburg
# / Rendsburg / Rethwisch / Husum / Poppenbüttel), so danish_realm crown coins
# struck there never widened onto the SH page. See mint_registry `_CROWN_OWNED`.


def _derive_issuing_entity(coin: dict):
    """Recompute `issuing_entity` from the union of crown mint-realms for a
    Danish-crown coin (issuing_entity == danish_realm) struck at a crown-owned
    Holstein mint. Returns the original value unchanged for every other coin —
    non-danish_realm entities (incl. already-joint lists and the SH sub-entity
    issuers), and danish_realm coins not struck at a Holstein mint (Copenhagen-
    only realm coinage stays danish_realm). See `_CROWN_MINT_REALM`."""
    ie = coin.get("issuing_entity")
    if ie != "danish_realm":            # only scalar danish_realm (crown realm coins)
        return ie
    mint = coin.get("mint")
    mset = {str(m) for m in (mint if isinstance(mint, list) else [mint]) if m}
    if not (mset & _HOLSTEIN_CROWN_MINTS):   # must be struck at a crown Holstein mint
        return ie
    realms = {_CROWN_MINT_REALM[m] for m in mset if m in _CROWN_MINT_REALM}
    if any(m not in _CROWN_MINT_REALM for m in mset):
        realms.add("danish_realm")           # conservative: unmapped mint → keep realm
    if "royal_holstein" not in realms:
        return ie
    return sorted(realms) if len(realms) > 1 else next(iter(realms))


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
    # Strip underscore-prefixed seed-generator metadata fields so the
    # assembled coin validates against the `extra='forbid'` coin schema.
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


# Per-page phase derivation (CLAUDE.md §7 «phases are location-local»; §8.2
# «first year of issue determines phase»). For fusses in this set, a coin's
# phase is COMPUTED per consumer page from `year_first` against THAT page's
# phase windows for the fuss, rather than requiring the stored scalar `phase`
# to match. This dissolves the cross-page granularity desync: the same coin
# lands in whatever window EXISTS on each page (e.g. on the Denmark page the
# 18½-Thaler has a single wide phase I[1813-1875], so every 18½ coin —
# including SH-periodised stored-II/III dual-mint coins — derives to I and
# renders; on the SH page it derives to the finer I/II/III/IV window of its
# year). The stored phase is honoured as a tiebreaker only at a shared window
# boundary (override). SCOPED rollout — start with 18½-Thaler so nothing else
# changes; widen deliberately after per-fuss review (handoff 2026-06-15).
_DERIVE_PHASE_FROM_YEAR: set[str] = {"18_5_thaler"}

# Advisory sanity tolerance (years) for the phase year-window. A coin lives in
# its STORED phase regardless of that phase's declared year window — coin
# membership is NEVER filtered by year (curator direction 2026-07-09: «потрапляння
# монети в стопу не повинно фільтруватись роком»). But when a coin's year falls
# grossly outside its phase window — beyond this many years — we log a warning so
# a data-error year, or a periodisation gap that should get its own phase, stays
# visible. The coin is kept either way. Tunable; 25y ≈ a phase-generation of slack.
_PHASE_YEAR_SANITY_TOLERANCE = 25


# Hard mission upper bound (curator direction 2026-07-09: «1914 рік це строге
# обмеження, все що після 1914 у нас не розглядається»). Outer-span expansion
# never moves an anchor past it — a coin whose year_last runs into the 1920s-30s
# (e.g. a Christian X 20-Kroner minted 1913-1931) contributes at most 1914.
_MISSION_YEAR_MAX = 1914


def _is_dated_anchor_label(label) -> bool:
    """True when a phase's outer label already names an explicit 4-digit year —
    i.e. a curated ordinance / cessation anchor such as «30. Mai 1566»,
    «15./31. Juli 1726», «2. Aug. 1914 (Goldkonvertibilität ausgesetzt)». Such a
    label is a deliberate §7a founding/closing decree anchor and is PINNED: a
    stray coin never overwrites it. A BARE year («1622») or a year-less label
    («17. Jh.») is NOT a dated anchor → it is coin-driven (auto-generated)."""
    if not label:
        return False
    s = str(label).strip()
    if re.fullmatch(r"\d{3,4}", s):   # bare year — coin-driven, not a curated anchor
        return False
    return bool(re.search(r"\d{4}", s))   # names an explicit year → curated dated anchor


def _expand_outer_phase_span(loc_id: str, raw: dict) -> None:
    """Coin-driven outer-span expansion (Change 2, curator direction 2026-07-09).

    «монети визначають роки фаз, а не фази обрізають стопу по роках» — a fuss's
    displayed span is anchored by two OUTER points: its earliest phase's start
    (year_from / from_label) and its latest phase's end (year_to / to_label).
    Those two anchors shift OUTWARD to cover a coin of the fuss whose year falls
    beyond them; interior phase boundaries are never touched. The moved anchor's
    label is auto-generated from the coin year (labels follow the ints).

    Three guards keep the shift honest (all curator direction 2026-07-09):

      • REIGN-SPAN EXCLUDED — a coin whose year IS a ruler's reign window
        (`year_is_reign_span: true`, e.g. «1588-1648» Christian IV) never moves an
        anchor: the exact mint year is unknown, so it's not a boundary signal.
        But an imprecise-but-NARROW estimate (`year_verified: false` WITHOUT the
        reign-span flag — e.g. a Hans Rhinsk-Gylden «1496-1497 (?)») DOES move the
        anchor: it's a genuine narrow mint-date estimate, so the fuss span reaches
        it (curator direction 2026-07-10 — corrects the earlier verified-only guard
        that wrongly excluded such estimates). A data-error year (not reign-span)
        must therefore be FIXED at the source (errata / year correction), not left
        as `year_verified: false` — the log below surfaces it.
      • 1914 CAP — a coin's year_last contributes at most _MISSION_YEAR_MAX; the
        realm's precious-metal era ends 1914 and nothing after it is in scope.
      • DATED-ANCHOR PIN — a phase whose outer label already names an explicit
        year (an ordinance / cessation date, `_is_dated_anchor_label`) is left
        untouched, int and label both, since the curator anchored it to a decree.
        Only bare-year («1622») and year-less («17. Jh.») anchors are coin-driven.

    Every shift is LOGGED with the coin that drove it (curator direction
    2026-07-09: «механізм повинен реагувати» на них) so a suspect driver — a
    ruler-span still lacking `year_verified: false`, say — is visible and can be
    corrected; once corrected it stops moving the anchor.

    seed_unsorted is skipped — its «phases» are synthetic source-name buckets,
    not real periods. Mutates `raw['phases']` in place; `raw` is a fresh
    per-location parse (never a shared cache) and this runs once, after
    `raw['coins']` is finalised and before `Location(**raw)`.
    """
    phases_map = raw.get("phases") or {}
    coins = raw.get("coins") or []
    # Scope for the founding-era START rule (mirrors timeline._mint_sync_scope):
    # anywhere on a denmark_only page, holstein on SH, else no data-driven axis.
    _tl = raw.get("timeline") or {}
    if _tl.get("scope_mode") == "denmark_only":
        _scope = "anywhere"
    elif loc_id == "schleswig_holstein":
        _scope = "holstein"
    else:
        _scope = None
    _fuesse = _load_fuesse_cached() if _scope is not None else {}
    # (year, driver_id) so a shift can name the coin that caused it. reign_min
    # holds the earliest reign-window placeholder per fuss — it feeds only the
    # founding-era START (via timeline.founding_mint_start), never the END.
    fuss_min: dict[str, tuple[int, str]] = {}
    fuss_max: dict[str, tuple[int, str]] = {}
    reign_min: dict[str, tuple[int, str]] = {}
    for c in coins:
        fuss = c.get("fuss")
        if not fuss or fuss == "seed_unsorted":
            continue
        cid = c.get("id") or "?"
        yf = c.get("year_first")
        yl = c.get("year_last") or yf
        if c.get("year_is_reign_span") is True:
            # reign placeholder: feeds the founding-era START rule only.
            if yf is not None and (fuss not in reign_min or yf < reign_min[fuss][0]):
                reign_min[fuss] = (yf, cid)
            continue
        if yf is not None and (fuss not in fuss_min or yf < fuss_min[fuss][0]):
            fuss_min[fuss] = (yf, cid)
        if yl is not None:
            yl = min(yl, _MISSION_YEAR_MAX)   # 1914 hard cap
            if fuss not in fuss_max or yl > fuss_max[fuss][0]:
                fuss_max[fuss] = (yl, cid)

    shifts: list[str] = []
    for fuss, ph_defs in phases_map.items():
        if fuss == "seed_unsorted" or not ph_defs:
            continue
        with_from = [p for p in ph_defs if p.get("year_from") is not None]
        with_to = [p for p in ph_defs if p.get("year_to") is not None]
        if with_from and (fuss in fuss_min or fuss in reign_min):
            # Founding-era START — resolve dated + reign coins via the SAME rule
            # the timeline mint stripe uses (timeline.founding_mint_start). The
            # phase table has no fade, so the returned approx flag is ignored;
            # only the start YEAR is applied. A fuss with no reign placeholder
            # earlier than its dated coin resolves to the dated start (no-op).
            dated_min = fuss_min[fuss][0] if fuss in fuss_min else None
            rmin = reign_min[fuss][0] if fuss in reign_min else None
            adoption_year, firm = None, True
            _f = _fuesse.get(fuss) if _scope is not None else None
            _fa = getattr(_f.events, "first_adoption", None) if (_f and _f.events) else None
            if _fa is not None:
                adoption_year = getattr(_fa, _scope, None)
                firm = getattr(_fa, f"firm_{_scope}", True)
            new_from, _approx = founding_mint_start(rmin, dated_min, adoption_year, firm)
            if new_from is not None:
                earliest = min(with_from, key=lambda p: p["year_from"])
                if (new_from < earliest["year_from"]
                        and not _is_dated_anchor_label(earliest.get("from_label"))):
                    # name what actually set new_from: the reign placeholder
                    # (Rule 2), a dated coin, or the firm founding year (Rule 1).
                    if rmin is not None and new_from == rmin:
                        drv = reign_min[fuss][1]
                    elif dated_min is not None and new_from == dated_min:
                        drv = fuss_min[fuss][1]
                    else:
                        drv = f"founding {new_from}"
                    shifts.append(f"{fuss}/{earliest.get('id')} start {earliest['year_from']} → {new_from} (driver {drv})")
                    earliest["year_from"] = new_from
                    earliest["from_label"] = str(new_from)
        if with_to and fuss in fuss_max:
            latest = max(with_to, key=lambda p: p["year_to"])
            new_to, drv = fuss_max[fuss]
            if new_to > latest["year_to"] and not _is_dated_anchor_label(latest.get("to_label")):
                shifts.append(f"{fuss}/{latest.get('id')} end {latest['year_to']} → {new_to} (driver {drv})")
                latest["year_to"] = new_to
                latest["to_label"] = str(new_to)

    if shifts:
        print(f"   ⇄  v2/{loc_id}: {len(shifts)} outer-span shift(s) from coins "
              f"(verify each driver's year before trusting the new anchor):")
        for s in shifts:
            print(f"      • {s}")


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
    # `consumes_entities` accepts a bare entity-id string OR a dict
    # `{entity: <id>, year_from?: Y, year_to?: Y}` — the dict form caps the
    # entity's coins to its «under-this-jurisdiction» window on THIS page
    # (per-location, not global). E.g. the Denmark page consumes Norway only
    # ≤1814 (Treaty of Kiel) and the Danish-controlled SH duchies only ≤1864
    # (2nd Schleswig War), while those same entities render their full span on
    # their own pages. The cap is enforced in the per-coin pre-filter below;
    # Pass 1/2/seed-render iterate the entity ids unchanged.
    _raw_consumes = raw.get("consumes_entities") or []
    if not _raw_consumes:
        return 0
    consumes_window: dict[str, tuple] = {}
    for _e in _raw_consumes:
        if isinstance(_e, dict):
            consumes_window[_e["entity"]] = (_e.get("year_from"), _e.get("year_to"))
        else:
            consumes_window[_e] = (None, None)
    consumes_entities = list(consumes_window.keys())
    consumes_set = set(consumes_entities)

    km_register = raw.get("km_register")
    by_entity = _load_v2_curated()
    seed_entries = _load_v2_seed_entries()

    assembled: list[dict] = []
    seen_ids: set[str] = set()

    # «Already-absorbed» V1 seed coin ids — every coin represented in a
    # foundation entry via the three-level absorb chain (Level 1 direct
    # composed_of, Level 2 unified.composed_of, Level 3 catalog-hede
    # ref coverage). The set is location-INDEPENDENT (purely a function
    # of curated + seed-unified data), so it's computed once per process
    # in `_compute_absorbed_seed_ids` and reused across every location's
    # assembly. Pre-hoist this ran 12× per full build; now it runs once.
    # See the function docstring for the per-level rationale, including
    # the rendered-duplicate bug reports that motivated each level.
    absorbed_seed_ids = _compute_absorbed_seed_ids()

    # ---- Pass 1: direct membership ---------------------------------------
    for ent in consumes_entities:
        for coin in by_entity.get(ent, []):
            cid = coin.get("id")
            if not cid or cid in seen_ids:
                continue
            if coin.get("promoted_to"):
                continue
            # Foreign-issuer guard: a coin filed in this entity's file whose OWN
            # issuing_entity does not intersect the page's consumed entities does
            # NOT belong on this page — e.g. a Romanian 20-Lei struck on contract
            # (Auftragsprägung) in Hamburg (issuing_entity: romania) sits in
            # hanseatic_hamburg.yml by mint but is issued by Romania, which no
            # German page consumes. This applies the same issuing-entity
            # intersection rule Pass 2 + the seed pass already enforce (lines
            # below), using the RAW issuing_entity — NOT the mint-realm-derived
            # one: the derivation only WIDENS danish_realm crown coins onto the
            # SH page (Pass 2) and must never NARROW a file-resident coin off its
            # own entity's page. A coin with no issuing_entity is kept (can't
            # decide → keep). Zero-regression by construction: every coin living
            # in file `ent` has `ent` in its raw issuing_entity, and `ent` is in
            # consumes_set, so the intersection is non-empty for all but genuinely
            # foreign contract-mintings.
            raw_ie = set(_normalise_ie_to_list(coin.get("issuing_entity")))
            if raw_ie and not (raw_ie & consumes_set):
                continue
            rc = _resolve_dict_fields_per_location(coin, loc_id, km_register)
            rc["issuing_entity"] = _derive_issuing_entity(rc)
            assembled.append(rc)
            seen_ids.add(cid)

    # ---- Pass 2: inverse-index for multi-entity coins --------------------
    for ent, coins in by_entity.items():
        if ent in consumes_set:
            continue  # already handled in Pass 1
        for coin in coins:
            cid = coin.get("id")
            if not cid or cid in seen_ids:
                continue
            # Use the mint-realm-derived issuing_entity so a crown coin struck
            # at a Holstein mint (but filed under danish_realm) is picked up by
            # the SH page here. See _derive_issuing_entity.
            ie_list = _normalise_ie_to_list(_derive_issuing_entity(coin))
            if not (set(ie_list) & consumes_set):
                continue
            if coin.get("promoted_to"):
                continue
            rc = _resolve_dict_fields_per_location(coin, loc_id, km_register)
            rc["issuing_entity"] = _derive_issuing_entity(rc)
            assembled.append(rc)
            seen_ids.add(cid)

    # ---- Seed entries (Phase 3 output) ---------------------------------
    # Skip any seed entry already represented in a foundation entry's
    # composed_of (it's the same coin via the unified→foundation
    # absorb chain; rendering both produces a visible duplicate row).
    for coin in seed_entries:
        cid = coin.get("id")
        if not cid or cid in seen_ids:
            continue
        if cid in absorbed_seed_ids:
            continue
        ie_list = _normalise_ie_to_list(coin.get("issuing_entity"))
        if not (set(ie_list) & consumes_set):
            continue
        if coin.get("promoted_to"):
            continue
        # Strip seed-side bookkeeping AND source-specific raw fields
        # before pydantic instantiation. Source builders may carry
        # extras like `numista_title`, `obverse`, `reverse`,
        # `additional_litteratur`, `photo_credit`, `shape`,
        # `technique`, `numista_rarity_index`, `_v2_seed_source`,
        # `_currency`, `_period`, `_references_text`, `_ucoin_tid` etc.
        # — useful for audit + provenance in seed YAMLs but rejected
        # by Coin's strict schema. Filter to schema-known keys only;
        # the alternative (per-source allowlists) drifts as builders
        # evolve. The strip is location-independent so seen by every
        # consumer page identically.
        c = {k: v for k, v in coin.items() if k in _COIN_SCHEMA_FIELDS}
        # Required-field normalisation for seed entries with sparse
        # source data:
        #   * `nominal: None`  → drop the entry (without nominal we
        #     can't render anything useful; the seed builder should
        #     fix the underlying data but the render shouldn't crash)
        #   * `year_label: None` + `year_first` available → derive
        #     a plain year-string. Per §3a year_label is a plain
        #     decimal year/range, so `str(year_first)` (or
        #     `f"{year_first}–{year_last}"` for ranges) is correct.
        if c.get("nominal") is None:
            continue
        # Reader-facing nominal guarantee (idempotent): Danish-realm
        # spelling (Noble→Nobel / Rose Noble→Rosenobel) + implicit «1 »
        # count. Belt-and-suspenders over the seed-write normalisation
        # so every rendered row is correct regardless of source path
        # (incl. curated entries hand-added to a final/location yaml).
        c["nominal"] = normalise_nominal_display(c["nominal"])
        if c.get("year_label") is None:
            yf = c.get("year_first")
            yl = c.get("year_last")
            if yf is not None:
                if yl is not None and yl != yf:
                    c["year_label"] = f"{yf}–{yl}"
                else:
                    c["year_label"] = str(yf)
            else:
                # No year info at all — skip rather than fabricate.
                continue
        assembled.append(_resolve_dict_fields_per_location(c, loc_id, km_register))
        seen_ids.add(cid)

    # ---- Per-coin pre-filter: phase definition must EXIST on this page ----
    # An entity file may legitimately carry coins whose `fuss` or `phase`-id is
    # not *defined* on this consumer's location yaml (a phase this page's
    # periodisation doesn't declare). Rather than hard-fail the whole V2 build
    # on that mismatch, we drop the coin from this specific assembly with a
    # one-line summary. The coin is NOT lost — it surfaces on the OTHER
    # consumer pages whose phase definitions do accommodate it.
    #
    # A coin is NEVER dropped by *year* (curator direction 2026-07-09:
    # «потрапляння монети в стопу не повинно фільтруватись роком»). A coin whose
    # year falls outside its phase's declared window still renders in that
    # phase — e.g. the Christian-IV Haderslev reichsdukatenfuss coins (1591-1593)
    # render on BOTH the DK page and the SH page even though the SH
    # reichsdukatenfuss Phase I window opens at 1600. The only per-coin drops
    # here are structural: an out-of-scope metal, the per-entity consume-window
    # (a page-scope jurisdiction cap, not a fuss/phase gate), a fuss absent from
    # this page, or a phase-id this page does not define. Gross year/phase
    # mismatches are surfaced as an advisory warning (see year_warn), never a drop.
    phases_map = raw.get("phases") or {}
    kept: list[dict] = []
    dropped: list[tuple[str, str]] = []
    year_warn: list[tuple[str, str]] = []
    for c in assembled:
        fuss = c.get("fuss")
        phase = c.get("phase")  # already scalar after _resolve_dict_fields
        cid = c.get("id")
        # Out-of-scope guard (choke point for ALL passes — curated, seed_unified
        # via _load_v2_curated, and seed-render): skip entries with a `metal`
        # the schema can't model (Numista/ucoin harvest paper money / Notgeld,
        # metal 'paper'), which the precious-metal mission excludes. `None`
        # allowed (sparse seed). Prevents the whole location failing validation.
        _m = c.get("metal")
        if _m is not None and _m not in _VALID_COIN_METALS:
            dropped.append((cid, f"out-of-scope metal '{_m}'"))
            continue
        # Per-entity consume-window cap (see consumes_window above): keep the
        # coin only if its year falls within the «under this jurisdiction»
        # window of AT LEAST ONE of its consumed entities. A coin matched via
        # an uncapped entity (window (None, None)) always passes. This is what
        # lets the Denmark page show Norway only ≤1814 + Danish-controlled SH
        # only ≤1864, while those entities render their full span elsewhere.
        _yf_coin = c.get("year_first")
        if _yf_coin is not None:
            _matched = [consumes_window[e]
                        for e in _normalise_ie_to_list(c.get("issuing_entity"))
                        if e in consumes_window]
            if _matched and not any(
                (lo is None or _yf_coin >= lo) and (hi is None or _yf_coin <= hi)
                for lo, hi in _matched
            ):
                dropped.append((cid, f"year {_yf_coin} outside consume-window"))
                continue
        if fuss not in phases_map:
            dropped.append((cid, f"fuss '{fuss}' not on this page"))
            continue
        ph_defs = phases_map[fuss] or []
        ph_ids = {p.get("id") if isinstance(p, dict) else getattr(p, "id", None) for p in ph_defs}
        # Per-page phase derivation (scoped, _DERIVE_PHASE_FROM_YEAR): compute
        # the phase from year_first against THIS page's windows for the fuss;
        # the stored phase wins only as a boundary tiebreaker (override). This
        # re-buckets a coin into whatever window exists on this page (no drop,
        # no manual re-tag) and is what synchronises the cross-page granularity
        # desync. Falls through to the standard checks when no window matches.
        if fuss in _DERIVE_PHASE_FROM_YEAR and _yf_coin is not None and ph_defs:
            cands: list = []
            for p in ph_defs:
                pid = p.get("id") if isinstance(p, dict) else getattr(p, "id", None)
                lo = p.get("year_from") if isinstance(p, dict) else getattr(p, "year_from", None)
                hi = p.get("year_to") if isinstance(p, dict) else getattr(p, "year_to", None)
                if lo is not None and hi is not None and lo <= _yf_coin <= hi:
                    cands.append(pid)
            if cands:
                derived = phase if phase in cands else cands[0]
                if derived != phase:
                    c = {**c, "phase": derived}
                kept.append(c)
                continue
        if phase not in ph_ids:
            dropped.append((cid, f"phase '{phase}' not defined for fuss '{fuss}'"))
            continue
        # Year-range sanity (ADVISORY ONLY — a coin is NEVER filtered by year).
        # The coin lives in its stored phase regardless of the phase's declared
        # year window; the window is a display/data hint, not a membership gate
        # (curator direction 2026-07-09). When year_first falls grossly outside
        # the window — beyond _PHASE_YEAR_SANITY_TOLERANCE — log a warning so a
        # data-error year (or a periodisation gap that should get its own phase)
        # stays visible, but keep the coin either way.
        year_first = c.get("year_first")
        if year_first is not None:
            match = next((p for p in ph_defs
                          if (p.get("id") if isinstance(p, dict) else getattr(p, "id", None)) == phase), None)
            if match is not None:
                yf = match.get("year_from") if isinstance(match, dict) else getattr(match, "year_from", None)
                yt = match.get("year_to") if isinstance(match, dict) else getattr(match, "year_to", None)
                if yf is not None and yt is not None:
                    dev = (yf - year_first) if year_first < yf else (year_first - yt if year_first > yt else 0)
                    if dev > _PHASE_YEAR_SANITY_TOLERANCE:
                        year_warn.append((cid, f"year_first {year_first} is {dev}y outside phase {phase} [{yf}, {yt}]"))
        kept.append(c)

    if dropped:
        print(f"   ⚠  v2/{loc_id}: dropped {len(dropped)} coin(s) — not compatible "
              f"with this page's phase definitions:")
        for cid, why in dropped[:5]:
            print(f"      • {cid}: {why}")
        if len(dropped) > 5:
            print(f"      • ... and {len(dropped) - 5} more (use phase dict-form per "
                  f"V2_PIPELINE.md §5 to render on both DK + SH)")

    if year_warn:
        print(f"   ℹ  v2/{loc_id}: {len(year_warn)} coin(s) kept but dated >"
              f"{_PHASE_YEAR_SANITY_TOLERANCE}y outside their phase window "
              f"(check for a data-error year or a missing phase):")
        for cid, why in year_warn[:5]:
            print(f"      • {cid}: {why}")
        if len(year_warn) > 5:
            print(f"      • ... and {len(year_warn) - 5} more")

    raw["coins"] = kept
    # Change 2 — shift the two OUTER year-anchors of each fuss outward to cover
    # coins that fall beyond them (interior boundaries untouched). Runs after
    # the kept set is final so the extents reflect exactly what renders here.
    _expand_outer_phase_span(loc_id, raw)
    # consumes_entities was a V2-only sidecar field — `Location` allows
    # extras (`model_config.extra='allow'`), so it survives the
    # instantiation as `_consumes_entities`-style metadata. No strip needed.
    return len(kept)


def load_v2_locations(filter_id: str | list[str] | None = None) -> list[Location]:
    """Phase 4.2 V2 location loader. Reads `data/v2/locations/<loc>.yml`
    (display-meta only, no coins), assembles coins via
    `_assemble_v2_location()`, then validates as `Location`. Returns
    [] if `data/v2/locations/` is empty (V2 build is a no-op then).

    `filter_id` accepts a single string (legacy) or a list of ids
    (multi-location filter via `--location a,b,c` split). `None` loads
    everything.
    """
    if not V2_LOCATIONS_DIR.exists():
        return []
    if filter_id is None:
        filter_set: set[str] | None = None
    elif isinstance(filter_id, str):
        filter_set = {filter_id}
    else:
        filter_set = set(filter_id)
    locations = []
    for path in sorted(V2_LOCATIONS_DIR.glob("*.yml")):
        if path.stem.endswith("-references"):
            continue
        if filter_set is not None and path.stem not in filter_set:
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

    Post-2026-05-20 routing (D44):
    - V2 pages → `site/<loc>/<lang>/index.html` (default; output_root=SITE_DIR)
    - V1 pages → `site/v1/<loc>/<lang>/index.html` (subtree; explicit
      output_root=SITE_DIR/v1)

    V2 became the default URL after the cross-source pipeline matured;
    V1 remains accessible via the /v1/ prefix so existing links keep
    working. The template + assembly logic is shared between V1 and V2
    — only the output path branches."""
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
        # Auto-sync each Fuß's `events.first_mint.<scope>` /
        # `last_mint.<scope>` to the actual coin spans on this page, where
        # <scope> is the scope the page's own coins represent: `holstein`
        # on the SH page, `anywhere` on the denmark_only-scope page. So a
        # freshly-added Bruun-era Speciedaler 1859 instantly shifts the
        # mint layer right, a curator-set patent year (e.g. 10½-Krone-Fuß
        # first_mint=1644 while the first physical strike is 1645) reflects
        # the data not the decree, and a coin moving between fusses re-fits
        # both fusses' mint stripes + tooltips. Ephemeral per-render — the
        # YAML is never written. Other locations are no-ops.
        mint_overrides = derive_mint_overrides(loc, fuesse)
        if mint_overrides:
            fuesse_for_bars = {**fuesse, **mint_overrides}
            diffs = []
            for fid, new_f in mint_overrides.items():
                old_ev, new_ev = fuesse[fid].events, new_f.events
                # Report whichever scope actually changed (anywhere or
                # holstein) — generic over the page's sync scope.
                for scope in ("anywhere", "holstein"):
                    old_fm = getattr(old_ev.first_mint, scope)
                    new_fm = getattr(new_ev.first_mint, scope)
                    old_lm = getattr(old_ev.last_mint, scope)
                    new_lm = getattr(new_ev.last_mint, scope)
                    if new_fm != old_fm or new_lm != old_lm:
                        diffs.append(
                            f"{fid} [{scope}]: {old_fm}–{old_lm} → {new_fm}–{new_lm}"
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
        # Visual segmentation: split each fade-bearing layer into solid +
        # faded pieces aligned with hover-zone breakpoints, so the
        # fade-end CSS mask only acts on the solo tail (not the active
        # overlap zone). Mutates bar_layers in place — adds `visual_pieces`
        # to affected layers.
        attach_visual_pieces(bar_layers, hover_zones)

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
                    for e in (references_data.get('entries') or [])
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

        # Inline-refs post-processing pass (introduced 2026-05-25, see
        # scripts/lib/refs_pool.py). Scans rendered HTML for `<sup>[ref:KEY]</sup>`
        # markers, resolves against the shared pool, renumbers in
        # appearance order, injects entries into the biblio section.
        from lib import refs_pool as _refs_pool_mod
        _pool = _refs_pool_mod.load_refs_pool(DATA_DIR / "shared" / "refs_pool.yml")
        html = _refs_pool_mod.process_html(html, lang, _pool)

        # Fuss cross-reference pass (introduced 2026-06-11, see
        # scripts/lib/fuss_refs.py + docs/fuss_cross_refs_design.md).
        # Resolves `[fuss:KEY]` prose markers to the effective display
        # name for this page+lang — honouring per-location
        # `fuss_periods[KEY].name` overrides (global «Reichsdukatenfuß»
        # ↔ Denmark «Rigsdukatfod») — and links to the `#fuss-KEY` card
        # anchor when that card is rendered on this page.
        from lib import fuss_refs as _fuss_refs_mod
        _fp_overrides = loc.fuss_periods or {}
        _fuss_name_map = {}
        for _fk, _fobj in fuesse.items():
            _ov = _fp_overrides.get(_fk)
            _nm = _ov.name if (_ov is not None and _ov.name) else _fobj.name
            _fuss_name_map[_fk] = i18n.t(_nm, lang)
        html = _fuss_refs_mod.process_html(html, lang, _fuss_name_map)

        # Hero «References» count fix (2026-05-27): the template's
        # `hero_refs = references.entries | length` only counts the
        # legacy `*-references.yml` entries — it doesn't see the
        # ~50-150 pool refs that `process_html` injects post-render.
        # Patch the rendered HTML to reflect the TOTAL bibliography
        # size by counting `<li[^>]*value="N">` items inside the
        # final `<ol class="refs">` block and updating the matching
        # hero badge value.
        html = _patch_hero_refs_count(html)

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
    output_root: Path | None = None,
    fuesse: dict | None = None,
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

    # Hide locations with NO coins at all. `loc.coins` is the assembled set —
    # seed_unsorted coins count the same as sorted ones, so a location with
    # only seed entries still shows; only a truly-empty (0-coin) tab is hidden
    # (e.g. a consumes_entities page whose every coin dropped on the phase
    # filter). User direction 2026-06-17.
    empty_ids = [loc.id for loc in visible_locations if not loc.coins]
    if empty_ids:
        visible_locations = [loc for loc in visible_locations if loc.coins]
        print(f"🙈 Landing hides {len(empty_ids)} empty (0-coin) location(s): "
              f"{', '.join(sorted(empty_ids))}")

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
                    for e in (german_fuesse_references.get('entries') or [])
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

        # Inline-refs post-processing pass — same mechanism as
        # per-location pages (see _refs_pool_mod docstring).
        from lib import refs_pool as _refs_pool_mod
        _pool = _refs_pool_mod.load_refs_pool(DATA_DIR / "shared" / "refs_pool.yml")
        html = _refs_pool_mod.process_html(html, lang, _pool)

        # Fuss cross-reference pass (see scripts/lib/fuss_refs.py). The
        # landing has no per-location override context — resolve markers
        # against the GLOBAL fuss names only. `#fuss-KEY` anchors are not
        # present on the landing, so refs render as plain <code>name</code>.
        from lib import fuss_refs as _fuss_refs_mod
        _fuss_name_map = (
            {_fk: i18n.t(_fobj.name, lang) for _fk, _fobj in fuesse.items()}
            if fuesse else {}
        )
        html = _fuss_refs_mod.process_html(html, lang, _fuss_name_map)

        root = output_root if output_root is not None else SITE_DIR
        out_dir = root / lang
        out_dir.mkdir(parents=True, exist_ok=True)
        with open(out_dir / "index.html", "w", encoding="utf-8") as f:
            f.write(html)
        print(f"🏠 Landing: {out_dir.relative_to(REPO_ROOT)}/index.html")

    # Root index.html — language redirect.
    # Priority: 1) lang cookie set by app.js on previous visit
    #           2) browser preference (navigator.language)
    #           3) fallback to 'en'
    # The redirect-base prefix is `(base_url + output_root-suffix)`:
    # for the V2 default landing root=SITE_DIR → empty suffix; for the
    # V1 landing root=SITE_DIR/v1 → suffix «/v1». Tooltip on each click
    # in app.js still works because output is per-tree.
    root = output_root if output_root is not None else SITE_DIR
    rel_root_suffix = ""
    if output_root is not None and output_root != SITE_DIR:
        rel_root_suffix = "/" + output_root.relative_to(SITE_DIR).as_posix()
    redirect_base = base_url + rel_root_suffix
    root_html = f"""<!DOCTYPE html><html><head>
<meta charset="UTF-8">
<title>Müntzfüße</title>
<script>
const base = {redirect_base!r};
const langs = ['de', 'en', 'uk'];
const m = document.cookie.match(/(?:^|;\\s*)lang=([a-z]{{2}})/);
const cookieLang = m ? m[1] : null;
const browserLang = (navigator.language || 'en').slice(0, 2).toLowerCase();
let target = 'en';
if (langs.includes(cookieLang)) target = cookieLang;
else if (langs.includes(browserLang)) target = browserLang;
window.location.replace(base + '/' + target + '/');
</script>
<noscript><meta http-equiv="refresh" content="0; url={redirect_base}/en/"></noscript>
</head><body><p>Loading… <a href="{redirect_base}/en/">English</a> · <a href="{redirect_base}/de/">Deutsch</a> · <a href="{redirect_base}/uk/">Українська</a></p></body></html>"""
    with open(root / "index.html", "w", encoding="utf-8") as f:
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


def copy_static_root() -> None:
    """Copy verbatim root-level static files from /static → site/ root.

    For files that must be served at the site root URL itself, not under
    /assets/ — Google/Bing site-verification tokens, robots.txt, a
    custom-domain CNAME, .well-known/, etc. GitHub Pages deploys the build
    output `site/` (NOT the repo root), so a file dropped in the repo root
    is never served; placing it in /static gets it copied to site/<name>
    and thus served at https://<host>/<name>.
    """
    src_static = REPO_ROOT / "static"
    if not src_static.is_dir():
        return
    for src in src_static.iterdir():
        if src.is_file():
            dst = SITE_DIR / src.name
            shutil.copyfile(src, dst)
            print(f"📄 Static-root: site/{src.name} ({dst.stat().st_size:,} bytes)")


def _render_location_worker(loc_id: str, output_root_str: str, debug: bool,
                            repo_url: str, base_url: str,
                            location_filter: list[str] | None,
                            lang: str | None) -> None:
    """ProcessPoolExecutor worker — renders one location in a clean
    subprocess.

    Reloads the shared resources (fuesse / theme / ui / issuing_entities)
    + the V1 or V2 Location for `loc_id` from disk inside the worker.
    The alternative — pickling everything across the IPC boundary —
    crashes on Pydantic `model_config` proxies and bloats per-task IPC.
    Re-parsing the YAMLs costs ~0.3 s of fixed overhead per worker
    process, easily amortised across the ~5-15 s a single SH/DK render
    takes; for the small Hessen / Lauenburg pages a single worker
    handles them all in the queue, so the overhead is paid once.

    `output_root_str == ""` means the V2 default tree (SITE_DIR);
    a non-empty path string targets `SITE_DIR / "v1"` (or any other
    override path). The caller passes a string because `pathlib.Path`
    pickles cleanly but mixing `None`-sentinel + Path is uglier here.
    """
    from pathlib import Path as _Path
    fuesse = load_fuesse()
    theme = load_theme()
    ui = load_ui()
    issuing_entities = load_issuing_entities()

    # Locate the location in data/v2/locations/<id>.yml.
    loc_list = load_v2_locations(filter_id=[loc_id])
    if not loc_list:
        raise RuntimeError(f"worker: location {loc_id!r} not found "
                           f"(output_root={output_root_str!r})")
    loc = loc_list[0]

    env = build_env(str(TEMPLATE_DIR))
    languages = [lang] if lang else DEFAULT_LANGS
    output_root = _Path(output_root_str) if output_root_str else None
    build_location(loc, fuesse, theme, ui, languages, env,
                   debug=debug, repo_url=repo_url,
                   issuing_entities=issuing_entities, base_url=base_url,
                   output_root=output_root)


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--location", help="Build only these location(s). Accepts one id "
                   "(e.g. `--location schleswig_holstein`) or a comma-separated list "
                   "(e.g. `--location denmark,schleswig_holstein,lubeck`). Default: all.")
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
    # Parallelism: ProcessPoolExecutor across locations. After the
    # A+B+C cache hoists the per-location render is fast (~0.05 s),
    # so worker startup + IPC overhead actually slows the full build
    # if turned on by default. Kept as opt-in for the case where
    # individual renders grow expensive again (e.g. SH+DK with
    # multi-thousand-coin pages).
    p.add_argument("--jobs", "-j", type=int, default=None,
                   help="Number of parallel location renderers. Default: "
                        "1 (serial). Pass an int > 1 to opt into a worker "
                        "pool; only helpful when per-location render time "
                        "is large.")
    p.add_argument("--serial", action="store_true",
                   help="Force serial location rendering (equivalent to --jobs 1; "
                        "the current default).")
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
    
    # Resolve --location filter: accept comma-separated list for multi-
    # location builds (e.g. `--location denmark,schleswig_holstein`). A
    # single id (legacy behaviour) still works — the split + filter is a
    # no-op when there's just one id.
    location_filter: list[str] | None = None
    if args.location:
        location_filter = [s.strip() for s in args.location.split(",") if s.strip()]

    # V2 is the only build path (V1 was removed 2026-06-24 once the V2
    # pipeline reached parity; data/v2/locations/ + data/v2/final/ are the
    # source of truth). build_v2 is False only when data/v2/locations/ is
    # empty — then the build is a no-op.
    build_v2 = V2_LOCATIONS_DIR.exists() and any(V2_LOCATIONS_DIR.glob("*.yml"))

    v2_locations: list[Location] = []
    if build_v2:
        print("📦 Loading V2 entity-keyed locations...")
        v2_locations = load_v2_locations(filter_id=location_filter)
        print(f"   V2 locations: {len(v2_locations)} "
              f"({', '.join(l.id for l in v2_locations)})")
    print()

    # Schema + cross-ref validation
    print("🔍 Validating cross-references...")
    if build_v2 and v2_locations:
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

    # Parallel renderer: ProcessPoolExecutor across locations. Each call
    # to `build_location` is CPU-bound and reads only its own Location
    # + the shared (read-only) fuesse / theme / ui / issuing_entities
    # state — safe to fork across workers. Disabled by --serial (or
    # --jobs 1) for deterministic profiling / debug.
    serial = args.serial or args.jobs is None or args.jobs <= 1
    n_workers = 1 if serial else int(args.jobs)

    def render_all(loc_list, output_root):
        """Render the given Location list, sequentially or via a worker
        pool. Workers re-load shared resources inside the subprocess —
        much cheaper than pickling Pydantic + Jinja state through the
        executor IPC layer.
        """
        if serial or n_workers <= 1 or len(loc_list) <= 1:
            for loc in loc_list:
                build_location(loc, fuesse, theme, ui, languages, env,
                               debug=args.debug, repo_url=args.repo_url,
                               issuing_entities=issuing_entities,
                               base_url=base_url, output_root=output_root)
            return
        from concurrent.futures import ProcessPoolExecutor, as_completed
        out_arg = str(output_root) if output_root is not None else ""
        with ProcessPoolExecutor(max_workers=n_workers) as ex:
            futures = {
                ex.submit(_render_location_worker, loc.id,
                          out_arg, args.debug, args.repo_url, base_url,
                          location_filter, args.lang): loc.id
                for loc in loc_list
            }
            for fut in as_completed(futures):
                loc_id = futures[fut]
                # Re-raise worker exceptions verbatim (with traceback).
                fut.result()

    # V2 pages land at `site/<loc>/<lang>/index.html`.
    if build_v2 and v2_locations:
        print(f"📦 Rendering V2 pages → {SITE_DIR.relative_to(REPO_ROOT)}/  "
              f"({n_workers} worker{'s' if n_workers > 1 else ''})")
        render_all(v2_locations, None)

    # The landing lists EVERY location, so it must NEVER be re-rendered from a
    # partial `--location` subset — doing so dropped the un-built locations from
    # the landing grid (the classic partial-build footgun: `--location a,b`
    # rebuilt a landing showing only a + b). Rebuild it ONLY on a full build; any
    # `--location` run leaves the existing complete landing untouched. CI always
    # does a full build, so production is unaffected. (Previously the guard was
    # `len>1 or not --location`, which let MULTI-location partial builds clobber
    # the landing with just that subset.)
    if v2_locations and not location_filter:
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

        # Landing → V2 location list (V2 is root after D44).
        build_landing(v2_locations, ui, theme, languages, env,
                      repo_url=args.repo_url, base_url=base_url,
                      contact_email=contact_email,
                      german_fuesse=german_fuesse,
                      german_fuesse_references=german_fuesse_refs,
                      include_seed=include_seed, fuesse=fuesse)
    elif v2_locations and location_filter:
        print(f"   ⏭  Landing NOT rebuilt (partial --location build of "
              f"{', '.join(location_filter)}) — the existing complete "
              f"site/<lang>/index.html is preserved so no location vanishes "
              f"from the grid. Run a full `python scripts/build.py` to refresh "
              f"the landing.")

    generate_assets(theme)
    copy_static_root()

    print()
    print(f"✅ Build complete: {SITE_DIR}/")


if __name__ == "__main__":
    main()
