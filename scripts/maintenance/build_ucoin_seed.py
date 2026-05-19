#!/usr/bin/env python3
"""ucoin V1 seed builder — emits location-keyed `data/seed/ucoin/<location>.yml`.

Closes the V2 pipeline gap surfaced by the 2026-05-19 coverage audit:
99 V1 `dk-tid-*` curator entries (ucoin source) lived only in
`data/locations/denmark.yml` and never reached V2 because no
ucoin-→-V1-seed builder existed (NumisMaster / Hede / Bruun / Galster /
Numista all had builders; ucoin did not). 715 V1 location-level
sources.type=ucoin attestations total; without this builder they bypass
seed_v2_regroup + merge_seeds_cross_source entirely.

INPUT — two sources merged per tid (cache when present, V1 fills gaps):
  1. `scripts/cache/ucoin/<tid>.json` — recent Chrome-MCP-harvested
     ucoin pages. ~329 entries as of 2026-05-19, mostly post-§BR-1
     batches (Norway / Denmark Speciedaler-era).
  2. `data/locations/*.yml` `*-tid-*` entries — pre-cache V1 curator
     ucoin attestations. Carried over as authoritative when no cache
     backs them; cache overrides specific fields when both exist.

OUTPUT — one V1 seed yaml per project location:
  data/seed/ucoin/denmark.yml             (URL=denmark + URL=norway → Danish realm)
  data/seed/ucoin/schleswig_holstein.yml  (URL=schleswig_holstein)
  data/seed/ucoin/hamburg.yml             (URL=hamburg)
  data/seed/ucoin/lubeck.yml              (URL=lubeck)

After running this builder, `scripts/maintenance/seed_v2_regroup.py --apply`
picks up the new `data/seed/ucoin/*` and produces
`data/v2/seed/ucoin/<entity>.yml`. The cross-source merger then
matches ucoin entries against Hede / Bruun / NumisMaster by KM ref +
year + metal etc., so ucoin attestations enrich unified entries.

Schema follows the NumisMaster builder's pattern: Coin-shape with
`fuss: seed_unsorted`, `phase: ucoin`. issuing_entity inferred from
URL country token. Curation-preserving merge via `lib/seed_merge.py`.

Run:
    .venv/bin/python scripts/maintenance/build_ucoin_seed.py --all
    .venv/bin/python scripts/maintenance/build_ucoin_seed.py --location denmark
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
from lib.seed_merge import merge_seed  # noqa: E402

SEED_ROOT = PROJECT_ROOT / "data" / "seed" / "ucoin"
V1_LOCATIONS = PROJECT_ROOT / "data" / "locations"


# URL country token → V1 location file (where the entries land in the
# location-keyed V1 seed). Mirrors NumisMaster's LOCATION_CACHES roll-up
# pattern: denmark.yml absorbs both DK + NO (Danish-Norway realm is one
# coinage jurisdiction).
URL_COUNTRY_TO_LOCATION: dict[str, str] = {
    "denmark": "denmark",
    "norway": "denmark",           # Norge under Danish rule folds in
    "schleswig_holstein": "schleswig_holstein",
    "hamburg": "hamburg",
    "lubeck": "lubeck",
}

# URL country token → V2 issuing_entity. Norge gets danish_norway;
# Schleswig-Holstein gets royal_holstein as default (the most-common
# Danish-king-as-Holstein-duke coinage); curators promote to a specific
# Holstein cadet line (gottorp_duchy / sonderburg_duchy / etc.) on
# per-entry basis if the source supports it.
URL_COUNTRY_TO_ENTITY: dict[str, str] = {
    "denmark": "danish_realm",
    "norway": "danish_norway",
    "schleswig_holstein": "royal_holstein",
    "hamburg": "hanseatic_hamburg",
    "lubeck": "hanseatic_lubeck",
}

# Per-location year windows. ucoin coverage is broad (medieval through
# modern) but the project mission spans 1514-1914 with Schleswig-Holstein
# duchy ending 1864. Per CLAUDE.md «Mission temporal scope».
LOCATION_WINDOW: dict[str, tuple[int, int]] = {
    "denmark": (1514, 1914),
    "schleswig_holstein": (1514, 1864),
    "hamburg": (1559, 1914),
    "lubeck": (1559, 1914),
}


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
        if "copper" in c:
            return "copper"
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
            r"\b(KM|Hede|Sieg|Lange|Fr|Schou|Dav)#?\s*([\w.\-/]+)",
            str(raw),
            re.IGNORECASE,
        ):
            prefix = m.group(1).lower()
            val = m.group(2).rstrip(".,;")
            if prefix == "km":
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


def _build_entry_from_cache(cache: dict, location: str) -> dict | None:
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
    year_from, year_to = LOCATION_WINDOW.get(location, (1500, 1920))
    if (yl or yf) < year_from or yf > year_to:
        return None

    tid = cache.get("tid")
    if tid is None:
        return None
    # ID prefix mirrors V1 convention: dk-tid-*, hb-tid-*, lu-tid-*, sh-tid-*
    prefix = {
        "denmark": "dk",
        "schleswig_holstein": "sh",
        "hamburg": "hb",
        "lubeck": "lu",
    }.get(location, "tid")
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

    # ucoin URL country may differ from `location` (NO folds into denmark.yml)
    url_country = _url_country_token(cache.get("url")) or "denmark"
    issuing = URL_COUNTRY_TO_ENTITY.get(url_country, "danish_realm")

    metal_attested = bool(cache.get("composition_text"))

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
        "ruler": cache.get("ruler_text"),
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


def _build_entry_from_v1(v1_coin: dict, location: str) -> dict | None:
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
    year_from, year_to = LOCATION_WINDOW.get(location, (1500, 1920))
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
        "mint": v1_coin.get("mint"),
        "catalog": cat,
        "metal": v1_coin.get("metal") or "silver",
        "fineness": v1_coin.get("fineness"),
        "weight_rough_g": v1_coin.get("weight_rough_g"),
        "issuing_entity": v1_coin.get("issuing_entity") or "danish_realm",
        "verified": False,
        "metal_verified": v1_coin.get("metal_verified", False),
        "fineness_verified": v1_coin.get("fineness_verified", False),
        "weight_rough_verified": v1_coin.get("weight_rough_verified", False),
        "mint_verified": v1_coin.get("mint_verified", False),
        "sources": v1_coin.get("sources") or [],
        "verification_note": {
            "de": "ucoin-Seed (V1-Carryover): pre-cache V1-Curator-Eintrag, kein Cache-Backing.",
            "en": "ucoin seed (V1 carry-over): pre-cache V1 curator entry, no cache backing.",
            "uk": "ucoin-seed (V1-carryover): pre-cache V1-curator entry без кеш-підтримки.",
        },
    }
    return entry


def _collect_v1_tid_entries() -> dict[str, tuple[str, dict]]:
    """Walk V1 location yamls; return {tid_key: (location, coin_dict)}.

    Maps every V1 curator entry with a ucoin source attestation to its
    (location, coin) pair. `tid_key` is the numeric tid extracted from
    the FIRST ucoin source URL; entries lacking a parseable tid use
    their `id` as the key (so the entry still flows through the seed
    builder even when the URL has no tid query string).

    Both naming conventions are accepted:
      - `*-tid-{N}` ids from the bulk-import phase (dk-tid-, hb-tid-,
        lu-tid-)
      - `km-x{N}-*` curator-named ids where the curator used a non-
        standard Krause-DK volume number instead of a standard KM ref
        (these still have a ucoin URL in `sources`)
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
        location = path.stem
        for c in (doc.get("coins") or []):
            if not isinstance(c, dict):
                continue
            cid = c.get("id") or ""
            srcs = c.get("sources") or []
            ucoin_src = next(
                (s for s in srcs
                 if isinstance(s, dict) and s.get("type") == "ucoin"),
                None,
            )
            if ucoin_src is None:
                continue
            # Try to extract tid from URL (?tid=NNNN) — preferred key for
            # cache↔V1 matching. Fall back to id when URL has no tid.
            url = ucoin_src.get("url") or ""
            m_url = re.search(r"\?tid=(\d+)", url)
            if m_url:
                key = m_url.group(1)
            else:
                key = cid  # fallback: dedupe by V1 id
            out[key] = (location, c)
    return out


def build_seed(location: str, no_merge: bool, dry_run: bool,
               v1_tid_global: dict | None = None) -> int:
    if location not in URL_COUNTRY_TO_LOCATION.values():
        print(f"ERROR: unknown location '{location}'", file=sys.stderr)
        return 2
    out_path = SEED_ROOT / f"{location}.yml"

    # V1 LOCATION ASSIGNMENT IS CURATOR DECISION — overrides URL-country.
    # A V1 SH-curator-yaml entry whose ucoin URL says denmark stays in SH
    # (Rendsburg mint coins are SH-duchy regardless of how ucoin.net files
    # them). Conversely, if a tid exists in V1 SH AND has cache data, the
    # cache record lands in SH too — NOT denmark — to avoid splitting one
    # physical coin across two location seed files.
    #
    # The global V1 tid index is built once across all locations and
    # threaded through; this lets us know «tid X is curated to location
    # Y» when deciding where the cache-only record should land.
    if v1_tid_global is None:
        v1_tid_global = _collect_v1_tid_entries()

    relevant_url_countries = {k for k, v in URL_COUNTRY_TO_LOCATION.items() if v == location}

    cache_by_tid: dict[str, dict] = {}
    for json_path in sorted(UCOIN_CACHE.glob("*.json")):
        try:
            data = json.loads(json_path.read_text())
        except json.JSONDecodeError:
            continue
        tid = str(data.get("tid") or json_path.stem)
        # If V1 places this tid in a SPECIFIC location, honour that
        # placement and skip when it doesn't match THIS location.
        if tid in v1_tid_global:
            v1_loc, _ = v1_tid_global[tid]
            if v1_loc != location:
                continue
        else:
            # Cache-only entry — fall back to URL-country mapping.
            url_country = _url_country_token(data.get("url"))
            if url_country not in relevant_url_countries:
                continue
        cache_by_tid[tid] = data

    # V1 entries for THIS location
    v1_for_location = {tid: coin for tid, (loc, coin) in v1_tid_global.items() if loc == location}

    # Union of tids: cache + V1
    all_tids = set(cache_by_tid) | set(v1_for_location)

    entries: list[dict] = []
    counts = {"from_cache": 0, "from_v1": 0, "skipped_oob": 0}
    for tid in sorted(all_tids, key=lambda t: int(t) if t.isdigit() else 0):
        cache = cache_by_tid.get(tid)
        v1 = v1_for_location.get(tid)
        entry = None
        if cache:
            entry = _build_entry_from_cache(cache, location)
            if entry and v1:
                # When V1 has a CUSTOM id (e.g. `km-x012-fr-iv-1718`),
                # preserve it instead of the synthesised `dk-tid-{tid}`.
                # The V1 id is the curator's anchor for promotion in
                # `data/locations/`; switching it silently would break
                # any cross-references that point at the V1 id.
                v1_id = v1.get("id") or ""
                if v1_id and not v1_id.startswith(("dk-tid-", "hb-tid-",
                                                   "lu-tid-", "sh-tid-")):
                    entry["id"] = v1_id
                # Merge V1's curator-set fields onto cache entry. We do NOT
                # adopt V1's fuss/phase here (cross-source merger handles
                # foundation re-derivation); we DO adopt richer catalog,
                # multi-spec weight_rough_g, and verified flags.
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
            entry = _build_entry_from_v1(v1, location)
            if entry:
                counts["from_v1"] += 1
        if entry is None:
            counts["skipped_oob"] += 1
            continue
        entries.append(entry)

    entries.sort(key=lambda e: (e.get("year_first", 9999), e.get("id", "")))
    print(
        f"  [{location}] cache={len(cache_by_tid)} v1={len(v1_for_location)} "
        f"→ {len(entries)} entries (from_cache={counts['from_cache']}, "
        f"from_v1={counts['from_v1']}, skipped_oob={counts['skipped_oob']})"
    )
    if dry_run:
        return 0
    out_path.parent.mkdir(parents=True, exist_ok=True)

    if not no_merge:
        entries, stats = merge_seed(entries, out_path)
        print(
            f"  [{location}] merge: merged_existing={stats['merged_existing']}, "
            f"added_new={stats['added_new']}, orphan_curated={stats['orphan_curated']}"
        )

    yaml_out = ruamel.yaml.YAML()
    yaml_out.preserve_quotes = True
    yaml_out.width = 200
    yaml_out.indent(mapping=2, sequence=4, offset=2)

    scope_note = (
        f"ucoin seed for location `{location}`. User-edited coin catalogue "
        f"(ucoin.net), tier-equivalent to Numista per CLAUDE.md §5.6. "
        f"Pulls from `scripts/cache/ucoin/<tid>.json` recent harvests plus "
        f"V1 location-yaml carry-overs (pre-cache curator imports). Per-coin "
        "verification against primary sources (Hede / Sieg / Lange / Wilcke / "
        "NumisMaster / Bruun) before §BF promotion."
    )
    out = {
        "status": "seed",
        "source": "ucoin (ucoin.net per-coin pages, harvested via Chrome MCP)",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "location": location,
        "scope_note": scope_note,
        "coins": entries,
    }
    with out_path.open("w") as f:
        yaml_out.dump(out, f)
    print(f"  [{location}] wrote {out_path.relative_to(PROJECT_ROOT)} ({len(entries)} entries)")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    locations = sorted(set(URL_COUNTRY_TO_LOCATION.values()))
    g.add_argument("--location", choices=tuple(locations),
                   help="Build seed for one location")
    g.add_argument("--all", action="store_true",
                   help="Build seeds for every location")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--no-merge", action="store_true",
                    help="Skip curation-preserving merge (wholesale overwrite).")
    args = ap.parse_args()

    locs = locations if args.all else [args.location]
    # Build the V1 tid index ONCE — used by every location to know which
    # tids the curator has already placed in a specific location seed.
    v1_tid_global = _collect_v1_tid_entries()
    rc = 0
    for loc in locs:
        rc = build_seed(loc, args.no_merge, args.dry_run, v1_tid_global) or rc
    return rc


if __name__ == "__main__":
    sys.exit(main())
