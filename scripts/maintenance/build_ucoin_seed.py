#!/usr/bin/env python3
"""ucoin V2-native seed builder — emits entity-keyed
`data/v2/seed/ucoin/<entity>.yml` directly, skipping the V1→V2
regroup indirection.

Closes the V2 pipeline gap surfaced by the 2026-05-19 coverage audit:
99 V1 `dk-tid-*` curator entries (ucoin source) lived only in
`data/locations/*.yml` and never reached V2 because no ucoin builder
existed. 715 V1 location-level sources.type=ucoin attestations total;
without this builder they bypass merge_seeds_cross_source entirely.

INPUT — two sources merged per tid (cache when present, V1 fills gaps):
  1. `scripts/cache/ucoin/<tid>.json` — recent Chrome-MCP-harvested
     ucoin pages. ~329 entries as of 2026-05-19, mostly post-§BR-1
     batches (Norway / Denmark Speciedaler-era).
  2. `data/locations/*.yml` `*-tid-*` / `km-x*` entries (anything with
     `sources.type=ucoin`) — pre-cache V1 curator ucoin attestations.
     Carried over as authoritative when no cache backs them; cache
     overrides specific fields when both exist.

OUTPUT — V2 entity-keyed seed yamls (CLAUDE.md «V2 entity-keyed
pipeline» — V1 is frozen, V2 is the canonical line for NEW sources):
  data/v2/seed/ucoin/danish_realm.yml
  data/v2/seed/ucoin/danish_norway.yml
  data/v2/seed/ucoin/royal_holstein.yml
  data/v2/seed/ucoin/hanseatic_hamburg.yml
  data/v2/seed/ucoin/hanseatic_lubeck.yml

Per CLAUDE.md V2 architecture, classification by `issuing_entity` is
done by the builder itself rather than indirected through V1 seed +
`seed_v2_regroup.py`. The other 5 builders (Hede / Bruun / NumisMaster
/ Numista / Galster) still use the V1→V2 indirection for backward-
compatibility with V1 location renders; new source builders go
V2-native directly.

After running this builder, `scripts/maintenance/merge_seeds_cross_source.py
--apply` matches ucoin entries against Hede / Bruun / NumisMaster by
KM ref + year + metal, enriching unified entries.

Schema: Coin-shape with `fuss: seed_unsorted`, `phase: ucoin`,
`issuing_entity` per URL country + V1 curator placement.
Curation-preserving merge via `lib/seed_merge.py`.

Run:
    .venv/bin/python scripts/maintenance/build_ucoin_seed.py --all
    .venv/bin/python scripts/maintenance/build_ucoin_seed.py --entity danish_realm
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import ruamel.yaml
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from lib.paths import PROJECT_ROOT, UCOIN_CACHE  # noqa: E402
from lib.ruler_reigns import reign_covers_year  # noqa: E402
from lib.seed_merge import merge_seed  # noqa: E402
from lib.v2_seed_writer import _apply_pre_write_hygiene  # noqa: E402

V2_SEED_ROOT = PROJECT_ROOT / "data" / "v2" / "seed" / "ucoin"
V1_LOCATIONS = PROJECT_ROOT / "data" / "locations"


# URL country token → V2 issuing_entity. The ucoin URL slug is the
# strongest signal for the political-entity classification, mirroring
# the role NumisMaster's `country` field plays for that source. V1
# curator placement (per `_collect_v1_ucoin_entries` below) overrides
# URL country when they disagree — e.g. a Rendsburg-mint coin filed
# under «denmark» on ucoin.net but curated into SH location yaml
# stays in the SH-corresponding entity.
URL_COUNTRY_TO_ENTITY: dict[str, str] = {
    "denmark": "danish_realm",
    "norway": "danish_norway",
    "schleswig_holstein": "royal_holstein",
    "hamburg": "hanseatic_hamburg",
    "lubeck": "hanseatic_lubeck",
    # German mission entities (§CM 2026-06-01) — ucoin had harvested ~734
    # coins for these but the map omitted them → silently skipped. All three
    # Brunswick lines (incl. Wolfenbüttel) fold into the one Braunschweig-
    # Lüneburg entity. `german_empire` (§CO 2026-06-01, curator decision):
    # the unified-Empire mark/pfennig coinage (1871-1914, Reichsgoldmünzfuß)
    # gets its OWN mission entity + display location `german_empire`.
    "brunswick": "herzogtum_braunschweig_lueneburg",
    "brunswick_wolfenbuttel": "herzogtum_braunschweig_lueneburg",
    "brunswick_luneburg": "herzogtum_braunschweig_lueneburg",
    "osnabruck": "hochstift_osnabrueck",
    "bremen": "erzbisthum_bremen_verden",
    "hesse_kassel": "landgrafschaft_hessen_kassel",
    "oldenburg": "grafschaft_oldenburg",
    "lauenburg": "herzogtum_sachsen_lauenburg",
    "german_empire": "german_empire",
}

# V1 location yaml stem → default V2 entity for the V1-carry-over path.
# Used when a V1 ucoin entry's URL country and its V1 location file
# disagree (rare but happens — SH curator using denmark-URL coins for
# Rendsburg mint). V1 location placement is curator-authoritative.
V1_LOC_TO_ENTITY: dict[str, str] = {
    "denmark": "danish_realm",
    "schleswig_holstein": "royal_holstein",
    "hamburg": "hanseatic_hamburg",
    "lubeck": "hanseatic_lubeck",
}

# Per-entity year windows. ucoin coverage is broad (medieval through
# modern) but the project mission spans 1514-1914 with sub-entity
# windows reflecting their actual political existence. Per CLAUDE.md
# «Mission temporal scope». Windows must cover ALL entities that V1
# ucoin curator entries use (`gesamtstaat`, `provisional_govt`, …),
# else V1 carry-overs with those tags fall back to a default entity
# and trigger I1 home-file invariant violations downstream.
ENTITY_WINDOW: dict[str, tuple[int, int]] = {
    "danish_realm": (1514, 1914),
    "danish_norway": (1514, 1914),
    "royal_holstein": (1514, 1864),
    "provisional_govt": (1848, 1851),    # 1848 revolution SH gov't
    "hanseatic_hamburg": (1559, 1914),
    "hanseatic_lubeck": (1559, 1914),
    # German mission entities (§CM 2026-06-01). Per CLAUDE.md mission scope
    # «German lands» lower bound 1559 (Augsburger Reichsmünzordnung) / upper
    # 1914. `--all` iterates ENTITY_WINDOW.keys() + build_seed gates on
    # membership, so these MUST be here for the entities to be processed.
    "erzbisthum_bremen_verden": (1559, 1914),
    "grafschaft_oldenburg": (1559, 1914),
    "herzogtum_braunschweig_lueneburg": (1559, 1914),
    "herzogtum_sachsen_lauenburg": (1559, 1914),
    "hochstift_osnabrueck": (1559, 1914),
    "landgrafschaft_hessen_kassel": (1559, 1914),
    # German Empire (§CO 2026-06-01) — unified Reichswährung mark/pfennig
    # coinage from the Coinage Act of 4 Dec 1871 to the precious-metal-anchor
    # end 1914 (Reichsgoldmünzfuß for the gold tier).
    "german_empire": (1871, 1914),
}

# `gesamtstaat` is DEPRECATED per docs/V2_DECISIONS.md — mint-driven
# classification replaces it (Altona/Glückstadt → royal_holstein,
# Kopenhagen → danish_realm, Kongsberg → danish_norway; joint mints
# → list-form). V1 ucoin curator entries that still carry
# `issuing_entity: gesamtstaat` get remapped via mint per the helper
# below; mint-less entries fall back to V1 location classification.
_DEPRECATED_ENTITIES = frozenset({"gesamtstaat"})


def _mint_to_entity(mint) -> str | list[str] | None:
    """Map mint(s) → V2 issuing_entity per mint-driven classification.
    Single mint → scalar entity; joint → sorted list. None when missing."""
    def _classify_one(s: str) -> str | None:
        s0 = s.split(" (")[0]
        if "Altona" in s0 or "Glückstadt" in s0:
            return "royal_holstein"
        if "Kongsberg" in s0 or "Christiania" in s0:
            return "danish_norway"
        if "Kopenhagen" in s0 or "København" in s0:
            return "danish_realm"
        return None
    if isinstance(mint, list):
        ents = sorted({e for m in mint if (e := _classify_one(str(m)))})
        if not ents:
            return None
        return ents[0] if len(ents) == 1 else ents
    if isinstance(mint, str):
        return _classify_one(mint)
    return None


_MIXED_FRAC_RE = re.compile(r"^(\d+)[\-\s]1/2(?=\s)")


def _normalize_denomination(d: str | None) -> str | None:
    """«1-1/2 Skilling» / «1 1/2 Skilling» → «1½ Skilling»."""
    if not d:
        return d
    return _MIXED_FRAC_RE.sub(r"\1½", d)


def detect_metal(comp: str | None, denom: str | None) -> str:
    """Map ucoin Composition string + denomination tokens → schema metal.

    ucoin's «composition_text» typically reads:
      «Silver»             → silver
      «Silver (Billon) 0.125» → billon
      «Gold 0.917»         → gold
      «Copper»             → copper
    Falls back to denomination heuristics on missing/empty composition.
    """
    if comp:
        c = comp.lower()
        if "billon" in c:
            return "billon"
        if "gold" in c:
            return "gold"
        if "silver" in c:
            return "silver"
        if "bronze" in c:
            return "bronze"
        if "copper" in c:
            return "copper"
        if "lead" in c:
            return "lead"
    if denom:
        d = denom.lower()
        if any(t in d for t in (
            "ducat", "dukat", "goldgulden", "noble", "pistole",
            "d'or", "krone",
        )):
            return "gold"
        if "pfennig" in d or "hvid" in d:
            return "billon"
    return "silver"


def _url_country_token(url: str | None) -> str | None:
    """Extract the country token from a ucoin URL.

      https://en.ucoin.net/coin/denmark-1-skilling-1808-1809/?tid=79526
                                  ^^^^^^^
    Returns None if URL doesn't match the expected pattern."""
    if not url:
        return None
    m = re.search(r"ucoin\.net/coin/([a-z_]+)-", url)
    return m.group(1) if m else None


def _normalise_year_list(text: str | None) -> list[int]:
    """Parse ucoin `years_text` into a list of ints.

    Common shapes:
      «1808»                 → [1808]
      «1808-1809»            → [1808, 1809]
      «1700 - 1712»          → [1700, …, 1712]
      «1808, 1810, 1819»     → [1808, 1810, 1819]
      «1808-1810, 1816»      → [1808, 1809, 1810, 1816]

    Year ranges expand into per-year lists (consistent with how
    `_group_consecutive_years` re-collapses below). Out-of-plausible-range
    tokens (< 1400, > 2100) are dropped.
    """
    if not text:
        return []
    out: set[int] = set()
    # Range tokens like «1808-1810» or «1700 - 1712»
    for m in re.finditer(r"(\d{4})\s*-\s*(\d{4})", str(text)):
        a, b = int(m.group(1)), int(m.group(2))
        if 1400 <= a <= 2100 and 1400 <= b <= 2100 and b - a < 100:
            for y in range(a, b + 1):
                out.add(y)
    # Bare 4-digit tokens (after range-token consumption don't pick up
    # range endpoints again; we add to a set so duplicates are harmless)
    for m in re.finditer(r"\b(\d{4})\b", str(text)):
        y = int(m.group(1))
        if 1400 <= y <= 2100:
            out.add(y)
    return sorted(out)


def _group_consecutive_years(years: list[int]) -> list[tuple[int, int]]:
    """[1808, 1809, 1810, 1819] → [(1808, 1810), (1819, 1819)]."""
    if not years:
        return []
    sorted_ys = sorted(set(years))
    out: list[tuple[int, int]] = []
    cur_start = cur_end = sorted_ys[0]
    for y in sorted_ys[1:]:
        if y == cur_end + 1:
            cur_end = y
            continue
        out.append((cur_start, cur_end))
        cur_start = cur_end = y
    out.append((cur_start, cur_end))
    return out


def _format_year_label(ranges: list[tuple[int, int]]) -> str:
    parts: list[str] = []
    for a, b in ranges:
        parts.append(str(a) if a == b else f"{a}–{b}")
    return ", ".join(parts)


def _parse_km_ref(refs_text: str | None, refs_list: list | None) -> dict:
    """Parse ucoin `references_text` / `references_list` into catalog dict.

    ucoin's standard form is «KM# 526». Sub-variants like «KM# 526.1»
    are preserved verbatim. Multi-ref entries («KM# 526, Hede 52»)
    aren't common in our cache but are tolerated.

    Returns a dict with keys among {km, hede, sieg, lange, fr, schou,
    dav}. Unknown prefixes are dropped (curator can backfill from the
    `_references_text` audit field on the seed entry)."""
    catalog: dict = {}
    sources: list = []
    if refs_list and isinstance(refs_list, list):
        sources.extend(refs_list)
    if refs_text and refs_text not in sources:
        sources.append(refs_text)
    for raw in sources:
        if not raw:
            continue
        for m in re.finditer(
            r"\b(KM|Hede|Sieg|Lange|Fr|Schou|Dav|UC)#?\s*([\w.\-/]+)",
            str(raw),
            re.IGNORECASE,
        ):
            prefix = m.group(1).lower()
            val = m.group(2).rstrip(".,;")
            if prefix == "uc":
                # ucoin's OWN catalogue number (the type has no Krause #) — keep
                # it as an `others` locator, NEVER in `km`: «UC#» is not a Krause
                # number. (Curator-approved 2026-06-25; the cross-source merger
                # supplies the real KM/Hede from other sources.)
                catalog.setdefault("others", []).append(f"ucoin# {val}")
            elif prefix == "km":
                catalog.setdefault("km", val)
            elif prefix == "hede":
                catalog.setdefault("hede", val)
            elif prefix == "sieg":
                catalog.setdefault("sieg", val)
            elif prefix == "lange":
                catalog.setdefault("lange", val)
            elif prefix == "fr":
                catalog.setdefault("fr", val)
            elif prefix == "schou":
                catalog.setdefault("schou", val)
            elif prefix == "dav":
                catalog.setdefault("dav", val)
    return catalog


def _build_entry_from_cache(cache: dict, entity: str) -> dict | None:
    """Synthesise one seed entry from a cache JSON record.

    Returns None when the entry is out-of-scope (year window) or lacks
    minimum data (no year_first)."""
    yf = cache.get("min_year")
    yl = cache.get("max_year")
    if yf is None:
        # Fallback: derive from years_text
        ys = _normalise_year_list(cache.get("years_text"))
        if not ys:
            return None
        yf, yl = ys[0], ys[-1]
    year_from, year_to = ENTITY_WINDOW.get(entity, (1500, 1920))
    if (yl or yf) < year_from or yf > year_to:
        return None

    tid = cache.get("tid")
    if tid is None:
        return None
    # ID prefix mirrors V1 convention: dk-tid-* / sh-tid-* / hb-tid-* /
    # lu-tid-* — keyed on the V1-style territorial code so V1 location
    # renders that still read ucoin source attestations recognise the id.
    prefix = {
        "danish_realm": "dk",
        "danish_norway": "dk",  # Norge under Danish rule shares dk- prefix
        "royal_holstein": "sh",
        "hanseatic_hamburg": "hb",
        "hanseatic_lubeck": "lu",
    }.get(entity, "tid")
    cid = f"{prefix}-tid-{tid}"

    composition = cache.get("composition_text") or ""
    metal = detect_metal(composition, cache.get("denomination"))

    raw_fineness = cache.get("fineness")
    if raw_fineness is not None and (raw_fineness < 0 or raw_fineness > 1):
        raw_fineness = None

    catalog = _parse_km_ref(cache.get("references_text"), cache.get("references_list"))

    # year_label + year_ranges from explicit-year list if available
    ys = _normalise_year_list(cache.get("years_text"))
    if ys:
        grouped = _group_consecutive_years(ys)
        year_label = _format_year_label(grouped)
        year_ranges = [[a, b] for a, b in grouped]
        yf = grouped[0][0]
        yl = grouped[-1][1]
    else:
        year_label = str(yf) if yf == yl else f"{yf}-{yl}"
        year_ranges = [[yf, yl if yl is not None else yf]]

    # issuing_entity is THE entity slot the entry lands in. Since we
    # already pre-filtered cache entries by target entity in `build_seed`,
    # the entry's `issuing_entity` matches the file it's being written to.
    issuing = entity

    metal_attested = bool(cache.get("composition_text"))

    # Reign-window check on the cache's ruler attribution. ucoin's
    # source-data is user-edited and can attribute a coin to a king
    # whose reign doesn't cover the coin's minting year (real case
    # 2026-05-22: tid=79557 «4 Skilling 1807» tagged ruler
    # «Frederick VI» — but Christian VII reigned until 13 March 1808
    # so the 1807 coin is Christian VII's). When the cache's ruler
    # falls OUTSIDE the canonical reign window for the coin's year,
    # we keep the cache value in `ruler` (preserving the source
    # attestation) but flip `ruler_verified: False` so the cross-
    # source merger's verified-wins-over-unverified rule (§4) lets
    # NumisMaster / Bruun / Hede attestations override. The merger
    # also stops treating ruler-disagreement as a primary-signal
    # «no_match» when one side is unverified per CLAUDE.md §4.
    raw_ruler = cache.get("ruler_text")
    in_reign = reign_covers_year(raw_ruler, yf)
    # in_reign: True → reign covers year; False → year outside reign
    # (ruler attribution suspect); None → unrecognised ruler name or
    # year missing (can't decide, leave verified=True per default).
    ruler_verified = not (in_reign is False)

    entry: dict = {
        "id": cid,
        "fuss": "seed_unsorted",
        "phase": "ucoin",
        "kind": "kurant",
        "nominal": _normalize_denomination(cache.get("denomination")),
        "year_label": year_label,
        "year_first": yf,
        "year_last": yl if yl is not None else yf,
        "year_ranges": year_ranges,
        "ruler": raw_ruler,
        "ruler_verified": ruler_verified,
        "mint": cache.get("mint_text"),
        "catalog": catalog,
        "metal": metal,
        "fineness": raw_fineness,
        "weight_rough_g": cache.get("weight_g"),
        "issuing_entity": issuing,
        "verified": False,
        "metal_verified": metal_attested,
        "fineness_verified": raw_fineness is not None,
        "weight_rough_verified": cache.get("weight_g") is not None,
        "mint_verified": bool(cache.get("mint_text")),
        "sources": [
            {
                "type": "ucoin",
                "url": cache.get("url"),
                "ref": "ucoin",
            }
        ],
        "verification_note": {
            "de": (
                "ucoin-Seed: user-edited Münzkatalog (ucoin.net). "
                "Per-Münze-Verifikation gegen Primärquellen (Hede / "
                "Sieg / Lange / NumisMaster / Bruun) vor §BF-Promotion."
            ),
            "en": (
                "ucoin seed: user-edited coin catalogue (ucoin.net). "
                "Per-coin verification against primary sources (Hede / "
                "Sieg / Lange / NumisMaster / Bruun) before §BF promotion."
            ),
            "uk": (
                "ucoin-seed: користувацький каталог монет (ucoin.net). "
                "Покоінна верифікація проти первинних джерел (Hede / "
                "Sieg / Lange / NumisMaster / Bruun) перед §BF-промоцією."
            ),
        },
    }
    # Cache audit fields, underscore-prefixed so build.py's schema validator
    # strips them at render time but they survive seed merge for inspection.
    if cache.get("diameter_mm") is not None:
        entry["diameter_mm"] = cache["diameter_mm"]
        entry["diameter_mm_verified"] = True
    if cache.get("currency"):
        entry["_currency"] = cache["currency"]
    if cache.get("period"):
        entry["_period"] = cache["period"]
    if cache.get("references_text"):
        entry["_references_text"] = cache["references_text"]
    entry["_ucoin_tid"] = str(tid)

    return entry


def _build_entry_from_v1(v1_coin: dict, entity: str) -> dict | None:
    """Carry over a V1 location-yaml *-tid-* entry as a seed-shaped entry.

    Used when no cache record exists for the tid (older V1 imports). The
    V1 entry is already Coin-shape; we drop curator-set fuss/phase to
    avoid downgrading curated entries and let the V2 absorb step merge
    the V1 form back in via composed_of.
    """
    cid = v1_coin.get("id") or ""
    if not cid:
        return None
    yf = v1_coin.get("year_first")
    yl = v1_coin.get("year_last")
    if yf is None:
        return None
    year_from, year_to = ENTITY_WINDOW.get(entity, (1500, 1920))
    if (yl or yf) < year_from or yf > year_to:
        return None

    # Build a seed entry that mirrors V1 fields but tags fuss=seed_unsorted
    # (the cross-source merger picks up the V1 entry's catalog and merges
    # it with cache-derived entries that share KM#).
    cat = dict(v1_coin.get("catalog") or {})
    # Strip non-schema catalog keys that V1 may carry
    cat = {k: v for k, v in cat.items()
           if k in {"km", "lange", "hede", "sieg", "schou", "fr", "dav", "mb",
                    "bruun_collection_id", "bruun_part", "bruun_lot_no",
                    "bruun_page", "bruun_lot", "numista", "hede_volume", "others"}}

    entry: dict = {
        "id": cid,
        "fuss": "seed_unsorted",
        "phase": "ucoin",
        "kind": v1_coin.get("kind") or "kurant",
        "nominal": v1_coin.get("nominal"),
        "year_label": v1_coin.get("year_label") or str(yf),
        "year_first": yf,
        "year_last": yl if yl is not None else yf,
        "year_ranges": v1_coin.get("year_ranges") or [[yf, yl if yl is not None else yf]],
        "ruler": v1_coin.get("ruler"),
        # V1-carryover ruler is always unverified per §4 (pre-cache
        # curator-set, no citation). Even if the V1 ruler happens to
        # align with the reign window, the carry-over branch's
        # «no cache backing» self-description applies to ruler too.
        "ruler_verified": False,
        "mint": v1_coin.get("mint"),
        "catalog": cat,
        "metal": v1_coin.get("metal") or "silver",
        "fineness": v1_coin.get("fineness"),
        "weight_rough_g": v1_coin.get("weight_rough_g"),
        # Always use the entity resolved by `_collect_v1_ucoin_entries`
        # — it has already applied the deprecated-entity → mint-driven
        # remap. Taking `v1_coin.issuing_entity` directly would leak
        # the deprecated `gesamtstaat` tag back into V2 seed.
        "issuing_entity": entity,
        "verified": False,
        # V1-carryover entries inherit curator-set values WITHOUT a
        # cited source — that's the literal meaning of «pre-cache, no
        # cache backing». Per CLAUDE.md §4, the `*_verified: True`
        # flag is reserved for values «directly attested by an
        # acceptable source» (coin inscription / Hede / Numista / etc.);
        # a manual curator flag without citation is NOT a source. So
        # pre-cache carry-overs get all verified flags = False
        # regardless of what V1 had — let the cross-source merger
        # pick up the cache-backed (post-§AZ) Numista / NumisMaster /
        # Bruun / Hede attestation as the verifying source.
        #
        # Verified flags on cache-backed ucoin seeds (the OTHER branch
        # of this builder, _build_entry_from_cache) come from cache
        # content directly — that path stays unchanged.
        "metal_verified": False,
        "fineness_verified": False,
        "weight_rough_verified": False,
        "mint_verified": False,
        "sources": v1_coin.get("sources") or [],
        "verification_note": {
            "de": "ucoin-Seed (V1-Carryover): pre-cache V1-Curator-Eintrag, kein Cache-Backing.",
            "en": "ucoin seed (V1 carry-over): pre-cache V1 curator entry, no cache backing.",
            "uk": "ucoin-seed (V1-carryover): pre-cache V1-curator entry без кеш-підтримки.",
        },
    }
    return entry


def _collect_v1_ucoin_entries() -> dict[str, tuple[str, dict]]:
    """Walk V1 location yamls; return {tid_key: (v2_entity, coin_dict)}.

    Maps every V1 curator entry with a ucoin source attestation to its
    target V2 entity + the V1 coin dict. The V2 entity is derived from
    the V1 location file (curator placement is authoritative) plus the
    V1 entry's own `issuing_entity` field when present.

    `tid_key` is the numeric tid extracted from the FIRST ucoin source
    URL; entries lacking a parseable tid use their `id` as the key.

    Both V1 id conventions are accepted:
      - `*-tid-{N}` ids from the bulk-import phase
      - `km-x{N}-*` / curator-named ids where the curator used a non-
        standard Krause-DK ref but the entry has a ucoin source URL
    """
    out: dict[str, tuple[str, dict]] = {}
    for path in sorted(V1_LOCATIONS.glob("*.yml")):
        if "references" in path.name:
            continue
        try:
            doc = yaml.safe_load(open(path))
        except Exception:
            continue
        if not isinstance(doc, dict):
            continue
        v1_loc = path.stem
        for c in (doc.get("coins") or []):
            if not isinstance(c, dict):
                continue
            srcs = c.get("sources") or []
            ucoin_src = next(
                (s for s in srcs
                 if isinstance(s, dict) and s.get("type") == "ucoin"),
                None,
            )
            if ucoin_src is None:
                continue
            # Entity classification (priority order):
            #   1. If V1 issuing_entity is DEPRECATED (gesamtstaat etc.),
            #      remap via mint-driven rule per V2_DECISIONS.md.
            #   2. If V1 has explicit issuing_entity (live tag), honour it.
            #   3. Otherwise fall back to V1 location stem → V2 entity.
            v1_ie = c.get("issuing_entity")
            if isinstance(v1_ie, list) and v1_ie:
                v1_ie = v1_ie[0]
            entity = None
            if isinstance(v1_ie, str) and v1_ie in _DEPRECATED_ENTITIES:
                # Mint-driven remap. Falls through to V1_LOC_TO_ENTITY
                # when mint info is absent/unknown.
                remapped = _mint_to_entity(c.get("mint"))
                if isinstance(remapped, str) and remapped in ENTITY_WINDOW:
                    entity = remapped
                elif isinstance(remapped, list):
                    # Joint-mint: pick alphabetically-first as home file.
                    entity = remapped[0]
            if entity is None and isinstance(v1_ie, str) and v1_ie in ENTITY_WINDOW:
                entity = v1_ie
            if entity is None:
                entity = V1_LOC_TO_ENTITY.get(v1_loc, "danish_realm")
            cid = c.get("id") or ""
            url = ucoin_src.get("url") or ""
            m_url = re.search(r"\?tid=(\d+)", url)
            key = m_url.group(1) if m_url else cid
            out[key] = (entity, c)
    return out


def build_seed(entity: str, no_merge: bool, dry_run: bool,
               v1_tid_global: dict | None = None) -> int:
    if entity not in ENTITY_WINDOW:
        print(f"ERROR: unknown entity '{entity}'", file=sys.stderr)
        return 2
    out_path = V2_SEED_ROOT / f"{entity}.yml"

    # V1 curator placement OVERRIDES URL-country derivation. A V1 SH-
    # curator-yaml entry whose ucoin URL says denmark stays in the SH-
    # corresponding entity (royal_holstein). When V1 has no explicit
    # placement for a tid, fall back to URL-country mapping.
    if v1_tid_global is None:
        v1_tid_global = _collect_v1_ucoin_entries()

    cache_by_tid: dict[str, dict] = {}
    for json_path in sorted(UCOIN_CACHE.glob("*.json")):
        # Skip housekeeping sidecars (e.g. `_failed_open_ids.json` is a
        # list of failed-fetch records, not a per-tid coin dict).
        if json_path.name.startswith("_"):
            continue
        try:
            data = json.loads(json_path.read_text())
        except json.JSONDecodeError:
            continue
        if not isinstance(data, dict):
            continue
        tid = str(data.get("tid") or json_path.stem)
        # Determine target entity: V1 curator placement first, then URL.
        if tid in v1_tid_global:
            v1_entity, _ = v1_tid_global[tid]
            target_entity = v1_entity
        else:
            url_country = _url_country_token(data.get("url"))
            target_entity = URL_COUNTRY_TO_ENTITY.get(url_country)
        if target_entity != entity:
            continue
        cache_by_tid[tid] = data

    # V1 carry-overs for THIS entity
    v1_for_entity = {
        tid: coin for tid, (ent, coin) in v1_tid_global.items() if ent == entity
    }

    all_tids = set(cache_by_tid) | set(v1_for_entity)

    entries: list[dict] = []
    counts = {"from_cache": 0, "from_v1": 0, "skipped_oob": 0}
    for tid in sorted(all_tids, key=lambda t: int(t) if t.isdigit() else 0):
        cache = cache_by_tid.get(tid)
        v1 = v1_for_entity.get(tid)
        entry = None
        if cache:
            entry = _build_entry_from_cache(cache, entity)
            if entry and v1:
                # Preserve V1's custom id (e.g. `km-x012-fr-iv-1718`)
                # over the synthesised `dk-tid-{tid}` — the V1 id is
                # the curator's anchor in `data/locations/`.
                v1_id = v1.get("id") or ""
                if v1_id and not v1_id.startswith(("dk-tid-", "hb-tid-",
                                                   "lu-tid-", "sh-tid-")):
                    entry["id"] = v1_id
                # Merge V1's curator catalog refs onto cache entry.
                v1_cat = v1.get("catalog") or {}
                for k, v in v1_cat.items():
                    if k in {"km", "lange", "hede", "sieg", "schou", "fr",
                             "dav", "mb", "bruun_collection_id", "bruun_part",
                             "bruun_lot_no", "bruun_page", "bruun_lot",
                             "numista", "hede_volume"}:
                        entry["catalog"].setdefault(k, v)
            if entry:
                counts["from_cache"] += 1
        elif v1:
            entry = _build_entry_from_v1(v1, entity)
            if entry:
                counts["from_v1"] += 1
        if entry is None:
            counts["skipped_oob"] += 1
            continue
        entries.append(entry)

    entries.sort(key=lambda e: (e.get("year_first", 9999), e.get("id", "")))
    print(
        f"  [{entity}] cache={len(cache_by_tid)} v1={len(v1_for_entity)} "
        f"→ {len(entries)} entries (from_cache={counts['from_cache']}, "
        f"from_v1={counts['from_v1']}, skipped_oob={counts['skipped_oob']})"
    )
    if dry_run:
        return 0
    out_path.parent.mkdir(parents=True, exist_ok=True)

    if not no_merge:
        entries, stats = merge_seed(entries, out_path)
        print(
            f"  [{entity}] merge: merged_existing={stats['merged_existing']}, "
            f"added_new={stats['added_new']}, orphan_curated={stats['orphan_curated']}"
        )

    # Pre-write hygiene — out-of-scope filter + nominal/mint/catalog
    # normalisation. Applied AFTER merge_seed so orphan-curated entries
    # also benefit retroactively when hygiene rules tighten.
    entries, hygiene_stats = _apply_pre_write_hygiene(entries)
    if any(hygiene_stats.values()):
        print(
            f"  [{entity}] hygiene: "
            f"out_of_scope_filtered={hygiene_stats['out_of_scope_filtered']}, "
            f"out_of_scope_km_filtered={hygiene_stats.get('out_of_scope_km_filtered', 0)}, "
            f"nominal_normalised={hygiene_stats['nominal_normalised']}, "
            f"mint_normalised={hygiene_stats['mint_normalised']}, "
            f"catalog_split={hygiene_stats['catalog_split']}"
        )

    yaml_out = ruamel.yaml.YAML()
    yaml_out.preserve_quotes = True
    yaml_out.width = 200
    yaml_out.indent(mapping=2, sequence=4, offset=2)

    scope_note = (
        f"ucoin V2 seed for entity `{entity}`. User-edited coin catalogue "
        f"(ucoin.net), tier-equivalent to Numista per CLAUDE.md §5.6. "
        f"Pulls from `scripts/cache/ucoin/<tid>.json` recent harvests plus "
        f"V1 location-yaml carry-overs (pre-cache curator imports). "
        "Entity classification: V1 curator placement first; URL-country "
        "fallback for cache-only entries. Per-coin verification against "
        "primary sources (Hede / Sieg / Lange / Wilcke / NumisMaster / "
        "Bruun) before §BF promotion."
    )
    out = {
        "status": "seed",
        "source": "ucoin (ucoin.net per-coin pages, harvested via Chrome MCP)",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "entity": entity,
        "scope_note": scope_note,
        "coins": entries,
    }
    with out_path.open("w") as f:
        yaml_out.dump(out, f)
    print(f"  [{entity}] wrote {out_path.relative_to(PROJECT_ROOT)} ({len(entries)} entries)")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    entities = sorted(ENTITY_WINDOW.keys())
    g.add_argument("--entity", choices=tuple(entities),
                   help="Build seed for one V2 entity")
    g.add_argument("--all", action="store_true",
                   help="Build seeds for every V2 entity")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--no-merge", action="store_true",
                    help="Skip curation-preserving merge (wholesale overwrite).")
    args = ap.parse_args()

    ents = entities if args.all else [args.entity]
    v1_tid_global = _collect_v1_ucoin_entries()
    rc = 0
    for ent in ents:
        rc = build_seed(ent, args.no_merge, args.dry_run, v1_tid_global) or rc
    return rc


if __name__ == "__main__":
    sys.exit(main())
