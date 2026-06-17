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
    compute_hover_zones, derive_holstein_mint_overrides,
)
from lib.compute import compute_location
from lib.render import build_env, generate_css
from lib.schema import Location, Fuss, I18nText, Coin
from lib.v2_seed_writer import normalise_nominal_display


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
    # Direct id-match suppression set — covers V1-curator entries that
    # share the SAME id with a seed coin (e.g. dk-tid-XXX exists in V1
    # location yaml AND the new ucoin seed builder carries it over with
    # the same id). The Hede-catalog-ref suppression below is a
    # superset that catches cross-id shape; this trivial id-match pass
    # handles the dk-tid-* / km-x* / hb-tid-* / lu-tid-* cases where
    # seed and curated agree on the literal id.
    curated_ids = {
        cc.get("id") for cc in curated_coins
        if isinstance(cc, dict) and cc.get("id")
    }
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
            # Trivial duplicate: seed coin shares an id with an already-
            # present curated coin. The curated entry is the canonical
            # one (it carries the curator's fuss/phase assignment + may
            # have multi-source enrichment); drop the seed copy.
            if cid and cid in curated_ids:
                suppressed_count += 1
                continue
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

_V2_FINAL_CACHE: dict[str, list[dict]] | None = None
_V2_SEED_CACHE: list[dict] | None = None
_V2_UNIFIED_CACHE: list[dict] | None = None
_V2_ABSORBED_SEED_IDS_CACHE: set[str] | None = None

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
# danish_realm` (Danish-crown realm coinage), and the crown owned Altona +
# Glückstadt (royal Holstein mints, from 1617/1640), Kopenhagen (Denmark
# proper) and Kongsberg (Norway). So a crown coin struck at a Holstein mint
# circulated in the duchies → royal_holstein; struck at Copenhagen too →
# danish_realm too. royal_holstein is politically WITHIN danish_realm, so a
# Holstein-ONLY strike is pure royal_holstein (NOT joint). Commission strikes
# of OTHER issuers at Altona (Schaumburg-Pinneberg pre-1640, Plön, the 1848
# Provisional Government) keep their own entity — they are not danish_realm, so
# the scoping excludes them. See CLAUDE.md §7.
_CROWN_MINT_REALM: dict[str, str] = {
    "Altona": "royal_holstein", "Glückstadt": "royal_holstein", "Gluckstadt": "royal_holstein",
    "Kopenhagen": "danish_realm", "Royal Danish": "danish_realm", "Copenhagen": "danish_realm",
    "Kongsberg": "danish_norway",
}
_HOLSTEIN_CROWN_MINTS = {"Altona", "Glückstadt", "Gluckstadt"}


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


def load_locations(filter_id: str | list[str] | None = None,
                   skip_seed_merge: bool = False) -> list[Location]:
    """Load V1 locations from `data/locations/*.yml`.

    `filter_id` — single id or list of ids; None = load all.

    `skip_seed_merge` — when True, bypass `_merge_seeds_into_raw`.
    Useful when V1 won't be rendered this run (the default-V2 fast
    path), since the seed merge is the dominant cost of V1 load
    (~28 s on a full build). The returned Location objects are
    still schema-valid; their `coins` list just doesn't include
    seed-only entries (which are only relevant to the V1 render).
    """
    # `filter_id` may be a single string (legacy single-location filter)
    # or a list of ids (multi-location flag — `--location a,b,c` splits
    # into a list before reaching us). Normalise to a set for O(1) lookup;
    # `None` means «no filter, load everything».
    filter_set: set[str] | None
    if filter_id is None:
        filter_set = None
    elif isinstance(filter_id, str):
        filter_set = {filter_id}
    else:
        filter_set = set(filter_id)

    locations = []
    for path in sorted((DATA_DIR / "locations").glob("*.yml")):
        # Skip reference sidecar files
        if path.stem.endswith("-references"):
            continue
        if filter_set is not None and path.stem not in filter_set:
            continue
        with open(path, encoding="utf-8") as f:
            raw = yaml.safe_load(f)
        if skip_seed_merge:
            seed_merges = []
        else:
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

    # Locate the location: V1 path is data/locations/<id>.yml; V2 path is
    # data/v2/locations/<id>.yml. Pick by output-root: V2 default tree
    # uses V2 yamls, /v1/ tree uses V1 yamls.
    is_v1 = output_root_str.endswith("/v1") or output_root_str.endswith("\\v1")
    if is_v1:
        loc_list = load_locations(filter_id=[loc_id])
    else:
        loc_list = load_v2_locations(filter_id=[loc_id])
    if not loc_list:
        raise RuntimeError(f"worker: location {loc_id!r} not found "
                           f"(v1={is_v1}, output_root={output_root_str!r})")
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
    # V2 pipeline flags (per docs/V2_PIPELINE.md §4.1). Default behaviour
    # post-2026-05-21 (D-fast-build): V2 ONLY by default, since V1 is frozen
    # per CLAUDE.md «V1 is FROZEN after the 2026-05-18 bootstrap». Re-render
    # V1 only when explicitly requested (CI deploy / template change / V1
    # YAML edit). Cuts a typical local build from ~65 s to ~30 s.
    p.add_argument("--v1-only", dest="v1_only", action="store_true",
                   help="Suppress the V2 build path even when data/v2/locations/ "
                        "is populated. V1 lands at site/v1/<loc>/<lang>/.")
    p.add_argument("--include-v1", dest="include_v1", action="store_true",
                   help="Build V1 pages alongside V2 (site/v1/<loc>/<lang>/). "
                        "Required for production CI deploys (the /v1/ tree is "
                        "still live-served). Local iteration usually doesn't "
                        "need this — V1 is frozen.")
    # `--v2-only` retained as an alias of the new default; kept for
    # back-compatibility with existing shell scripts and CI tooling
    # that might still pass it. Has no effect when --include-v1 is off
    # (the default).
    p.add_argument("--v2-only", dest="v2_only", action="store_true",
                   help="(Alias of the new default — V2 only. Kept for "
                        "back-compat; redundant unless overriding --include-v1.)")
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

    # Mode selection (V1 vs V2):
    #   * default        — V2 ONLY (V1 is frozen per CLAUDE.md)
    #   * --include-v1   — V1 + V2 (CI deploys / template-wide refactors)
    #   * --v1-only      — V1 alone (rare: when validating V1 in isolation)
    #   * --v2-only      — alias of default (kept for back-compat)
    if args.v1_only and (args.v2_only or args.include_v1):
        print("\n❌ --v1-only conflicts with --v2-only / --include-v1.")
        sys.exit(1)
    # Effective flags:
    build_v1 = args.v1_only or args.include_v1
    build_v2 = (not args.v1_only) and V2_LOCATIONS_DIR.exists() and any(V2_LOCATIONS_DIR.glob("*.yml"))

    # V1 location load — the `_merge_seeds_into_raw` step alone walks
    # ~28 MB of seed YAML and dominates load time (~28 s out of the
    # original 191 s build). Skip the seed-merge step entirely when V1
    # won't be rendered AND V2 carries its own coin assembly. In that
    # case Location is still validated (Pydantic schema check) but its
    # `coins` list is empty of seed-only entries — which is fine
    # because we won't render those V1 pages this run.
    v1_load_needs_seed_merge = build_v1
    locations = load_locations(filter_id=location_filter,
                               skip_seed_merge=not v1_load_needs_seed_merge)
    print(f"   Locations: {len(locations)} ({', '.join(l.id for l in locations)})")

    v2_locations: list[Location] = []
    if build_v2:
        print()
        print("📦 Loading V2 entity-keyed locations...")
        v2_locations = load_v2_locations(filter_id=location_filter)
        print(f"   V2 locations: {len(v2_locations)} "
              f"({', '.join(l.id for l in v2_locations)})")
    print()

    # Schema + cross-ref validation
    print("🔍 Validating cross-references...")
    # V1 cross-ref check runs on the location list even when we won't
    # render V1 — it's also the schema-integrity check for the underlying
    # YAML, which V2 references via `consumes_entities`-driven coin
    # assembly. Cheap relative to V2 work after the seed-merge caching.
    if not cross_ref_check(locations, fuesse):
        print("\n❌ V1 validation failed. Fix errors above and rerun.")
        sys.exit(1)
    print("   ✓ V1 cross-references OK")
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

    # URL routing post-2026-05-20 (D44): V2 is the DEFAULT — V2 pages
    # land at `site/<loc>/<lang>/index.html`. V1 pages, when explicitly
    # included via --include-v1 (or --v1-only), land at
    # `site/v1/<loc>/<lang>/index.html` so the /v1/ tree stays reachable
    # for existing references.
    if build_v1:
        print(f"📦 Rendering V1 pages → {(SITE_DIR / 'v1').relative_to(REPO_ROOT)}/  "
              f"({n_workers} worker{'s' if n_workers > 1 else ''})")
        render_all(locations, SITE_DIR / "v1")

    if build_v2 and v2_locations:
        if build_v1:
            print()
        print(f"📦 Rendering V2 pages (default) → {SITE_DIR.relative_to(REPO_ROOT)}/  "
              f"({n_workers} worker{'s' if n_workers > 1 else ''})")
        render_all(v2_locations, None)

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

        # Default landing → V2 location list (V2 is root after D44).
        # Falls back to V1 location list when V2 is disabled / empty.
        default_landing_locs = (
            v2_locations if (build_v2 and v2_locations) else locations
        )
        build_landing(default_landing_locs, ui, theme, languages, env,
                      repo_url=args.repo_url, base_url=base_url,
                      contact_email=contact_email,
                      german_fuesse=german_fuesse,
                      german_fuesse_references=german_fuesse_refs,
                      include_seed=include_seed, fuesse=fuesse)

        # V1 landing at site/v1/<lang>/index.html so V1 location pages'
        # home-link («../../index.html») has a target. Emitted only when
        # V1 was actually rendered in this run.
        if build_v1:
            build_landing(locations, ui, theme, languages, env,
                          repo_url=args.repo_url, base_url=base_url,
                          contact_email=contact_email,
                          german_fuesse=german_fuesse,
                          german_fuesse_references=german_fuesse_refs,
                          include_seed=include_seed, fuesse=fuesse,
                          output_root=SITE_DIR / "v1")

    generate_assets(theme)
    
    print()
    print(f"✅ Build complete: {SITE_DIR}/")


if __name__ == "__main__":
    main()
