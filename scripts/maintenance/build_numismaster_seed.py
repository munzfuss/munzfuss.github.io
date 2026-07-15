#!/usr/bin/env python3
"""§BK NumisMaster — V2-native entity-keyed seed builder.

Reads `scripts/cache/numismaster/<cache>/MC_<N>.parsed.json` files (output of
`scripts/parse_numismaster.py`), classifies each coin by issuing political
entity, and writes one seed file per entity under
`data/v2/seed/numismaster/<entity>.yml` (via `lib.v2_seed_writer.write_v2_seed`),
with Coin-schema entries marked `fuss: seed_unsorted`, `phase: numismaster`.

Cache windows (CACHE_WINDOW per cache; all caches roll up, then the mint→entity
classifier routes each coin to its political-entity file):

  cache/numismaster/schleswig_holstein/ (1514-1864, SH Danish-jurisdiction)
  cache/numismaster/denmark/            (1514-1914, project upper bound)
  cache/numismaster/norway/             (1608-1814, Norge under Danish rule —
       Denmark-Norway is a single coinage jurisdiction, same as how Hede 1971
       covers both under «Danmarks og Norges mønter»).

Sweden-Christian-II is 0 entries (§BI negative finding) — no seed emitted.

Curation preservation: merge-aware via `scripts/lib/seed_merge.py` (§BL). Existing
`fuss`/`phase`/`fraction`/`issuing_entity`/`kind`/`note`/`*_verified` flags on
on-disk entries survive regeneration.

Run:
    .venv/bin/python scripts/maintenance/build_numismaster_seed.py --location schleswig_holstein
    .venv/bin/python scripts/maintenance/build_numismaster_seed.py --location denmark
    .venv/bin/python scripts/maintenance/build_numismaster_seed.py --all
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import ruamel.yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from lib.paths import NUMISMASTER_CACHE, PROJECT_ROOT  # noqa: E402
from lib.v2_seed_writer import write_v2_seed  # noqa: E402
from lib.entity_routing import route_entity_with_rules  # noqa: E402
from lib.note_extract import source_note  # noqa: E402

# Per-CACHE-DIR year window applied to entries from that cache:
#   schleswig_holstein  1514-1864 (Danish-jurisdiction SH end)
#   denmark             1514-1914 (project upper bound)
#   norway              1608-1814 (Danish-rule era only; NumisMaster floor 1608)
CACHE_WINDOW: dict[str, tuple[int, int]] = {
    "schleswig_holstein": (1514, 1864),
    "denmark": (1514, 1914),
    "norway": (1608, 1814),
}

# Per-LOCATION cache-dir composition — multiple sub-scopes can fold into one
# location (the Denmark-Norway realm covers both DK and NO Danish-rule entries).
LOCATION_CACHES: dict[str, list[str]] = {
    "schleswig_holstein": ["schleswig_holstein"],
    "denmark": ["denmark", "norway"],  # DK + Norge-under-Danish-rule both → denmark.yml
}

# NumisMaster `coinage_entity` values that mark the entry as out-of-scope for the
# project's circulation-coin register. Per CLAUDE.md §9.1 (patterns / trial
# strikes — «not struck for circulation») and §9.2 (exonumia — tokens, jetons,
# credit-markers belong to separate registers). Membership is checked against
# the `coinage_entity` value with its trailing « CGNNNNNN» id stripped.
EXCLUDED_COINAGE_ENTITIES: frozenset[str] = frozenset({
    "Patterns",                 # §9.1 pattern strikes (Pn-prefix KMs)
    "Trial Strikes",            # §9.1 trial / probe strikes (TS-prefix KMs)
    "Gutschriftsmarke Coinage", # §9.2 exonumia — credit-marker tokens (no denomination)
    # NOTE: «Token Coinage» (Tn-prefix KMs) is NOT excluded — Krause's
    # Tn range covers crown-issued small-change emergency / Scheide
    # coinage in our scope (Christian VI, Frederik VI). When such a Tn
    # piece carries a denomination + period weight/composition, it
    # belongs in the table as a Scheidemünze. Per-case classification
    # (Müntzfuß + phase) is curator's decision. See v2_seed_writer.py
    # `_OUT_OF_SCOPE_KM_PREFIXES` for the parallel rationale.
})


# Mixed-fraction denomination normaliser: «1-1/2 Pfennig» / «1 1/2 Specie Daler»
# → «1½ Pfennig» / «1½ Specie Daler». NumisMaster stores mixed fractions in the
# ASCII «N-1/2» or «N 1/2» form; the rendered output uses the typographic ½
# ligature consistent with the rest of the corpus («1½ Thaler», «2½ Schilling»).
# Bare halves («1/2 Skilling») are left alone — they are correctly read as
# half-X, not 1½, and existing numismatic literature renders them either way.
_MIXED_FRAC_RE = re.compile(r"^(\d+)[\-\s]1/2(?=\s)")


def _normalize_denomination(d: str | None) -> str | None:
    """Apply mixed-fraction normalisation («N-1/2 X» / «N 1/2 X» → «N½ X»)."""
    if not d:
        return d
    return _MIXED_FRAC_RE.sub(r"\1½", d)


def _coinage_entity_excluded(raw: str | None) -> bool:
    """True if the parsed `coinage_entity` falls in EXCLUDED_COINAGE_ENTITIES.
    Strips the trailing « CGNNNNNN» id NumisMaster appends to the human name."""
    if not raw:
        return False
    name = raw.rsplit(" CG", 1)[0] if " CG" in raw else raw
    return name in EXCLUDED_COINAGE_ENTITIES


# Map NumisMaster `country` strings → canonical V2 `issuing_entity` tag.
# Replaced the legacy `schleswig_holstein_duchy` catch-all with per-line
# canonical entities (D38, 2026-05-19) — NumisMaster's `country` field
# is THE authoritative signal for which Holstein cadet line struck the
# coin. Each value maps directly to its V2 entity per
# `data/i18n/issuing_entities.yml`.
#
# Holstein cadet lines (independent ducal coinage):
#   GOTTORP        → gottorp_duchy
#   SONDERBURG     → sonderburg_duchy
#   PLOEN, NORBURG → norburg_plon_duchy
#   GLUCKSBURG     → glucksburg_duchy
#   SCHAUMBURG-PINNEBERG → schauenburg_pinneberg
#
# Danish-king-as-Holstein-duke:
#   GLUCKSTADT     → royal_holstein  (Danish king's Holstein mint)
#   SCHLESWIG-HOLSTEIN (generic) → royal_holstein  (royal Holstein
#                                  coinage absent specific cadet-line
#                                  attribution)
#   HOLSTEIN-GOTTORP-RENDSBORG → gottorp_duchy  (Rendsborg was a
#                                Gottorp mint pre-1721)
COUNTRY_TO_ISSUING_ENTITY: dict[str, str] = {
    # Danish realm + personal-union extensions
    "DENMARK": "danish_realm",
    "NORWAY": "danish_norway",
    "NORW AY": "danish_norway",  # observed parser variant
    "SWEDEN": "danish_realm",     # only Christian-II 1514-1523 in mission scope (= Danish-rule)
    # Danish-king-as-Holstein-duke (royal Holstein coinage)
    "GLUCKSTADT": "royal_holstein",
    "GLÜCKSTADT": "royal_holstein",  # parser sometimes preserves umlaut
    "SCHLESWIG-HOLSTEIN": "royal_holstein",
    # Independent Holstein cadet lines
    "SCHLESWIG-HOLSTEIN-GOTTORP": "gottorp_duchy",
    "HOLSTEIN-GOTTORP-RENDSBORG": "gottorp_duchy",
    "SCHLESWIG-HOLSTEIN-SONDERBURG": "sonderburg_duchy",
    "SCHLESWIG-HOLSTEIN-PLOEN": "norburg_plon_duchy",
    "SCHLESWIG-HOLSTEIN-NORBURG": "norburg_plon_duchy",
    "SCHLESWIG-HOLSTEIN-GLUCKSBURG": "glucksburg_duchy",
    "SCHAUMBURG-PINNEBERG": "schauenburg_pinneberg",
}


def detect_metal(comp: str | None, denom: str | None) -> str:
    if comp:
        c = comp.lower()
        if "gold" in c:
            return "gold"
        if "billon" in c:
            return "billon"
        if "silver" in c:
            return "silver"
        if "bronze" in c:
            return "bronze"
        if "copper" in c:
            return "copper"
        if "lead" in c or "blei" in c:
            return "lead"
    if denom:
        d = denom.lower()
        if any(t in d for t in (
            "ducat", "dukat", "goldgulden", "noble", "pistole",
            "d'or", "frederik d'or", "christian d'or", "krone",
            "portugaloser", "rosenobel",
        )):
            return "gold"
        if "pfennig" in d or "hvid" in d:
            return "billon"
    return "silver"


def _coin_id(location: str, mc: int) -> str:
    """Stable coin id used as the merge anchor. Format: `<location>-numismaster-<mc>`
    where <location> is the target seed file (schleswig_holstein / denmark).
    The legacy `denmark_pre_1541` seed uses `dk-numismaster-<mc>` — kept distinct
    so the new general seed doesn't clash."""
    return f"{location}-numismaster-{mc}"


def _group_consecutive_years(years: list[int]) -> list[tuple[int, int]]:
    """Collapse a sorted year list into consecutive-run [first, last] ranges.

    Example
    -------
    [1514, 1520, 1522, 1523, 1524, 1533]
      → [(1514, 1514), (1520, 1520), (1522, 1524), (1533, 1533)]

    The result drives both the rendered `year_label` (e.g. «1514, 1520, 1522–1524,
    1533») and the structured `year_ranges` field (timeline visualisation). Per
    CLAUDE.md §3a the canonical year_label form uses en-dash between range
    endpoints; this helper enforces that shape upstream of the YAML write so
    consumers don't have to re-parse.
    """
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
    """Format a list of consecutive-year ranges as the canonical year_label string
    («1514, 1520, 1522–1524, 1533»), per CLAUDE.md §3a. Single-year ranges render
    as bare years; multi-year ranges use en-dash."""
    parts: list[str] = []
    for a, b in ranges:
        parts.append(str(a) if a == b else f"{a}–{b}")
    return ", ".join(parts)


def build_entry(data: dict, location: str, year_from: int, year_to: int) -> dict | None:
    yf = data.get("year_first")
    yl = data.get("year_last")
    if yf is None:
        return None
    if (yl or yf) < year_from or yf > year_to:
        return None

    # CLAUDE.md §9 exclusions — patterns, trial strikes, tokens, exonumia
    # never enter the circulation-coin register. NumisMaster's own
    # `coinage_entity` taxonomy carries the signal directly.
    if _coinage_entity_excluded(data.get("coinage_entity")):
        return None

    mc = data.get("numismaster_id")
    if mc is None:
        return None
    cid = _coin_id(location, mc)

    composition = data.get("composition") or ""
    metal = detect_metal(composition, data.get("denomination"))

    # Catalog refs — schema-clean subset only. Coin.catalog (CatalogRefs)
    # accepts: km, lange, hede, sieg, schou, fr, dav, mb, bruun_collection_id,
    # bruun_part, bruun_lot_no, bruun_page, bruun_lot, numista. NumisMaster's
    # extra-vocabulary refs (schive / numismaster_mc / generic bruun-number)
    # are dropped here — the canonical raw record lives in
    # `MC_<N>.parsed.json`, so curators who want them open the cache. The
    # parser's `friedberg` key maps to schema `fr`.
    _ALLOWED_CATALOG_KEYS = {
        "km", "lange", "hede", "sieg", "schou", "fr", "dav", "mb",
        "bruun_collection_id", "bruun_part", "bruun_lot_no", "bruun_page",
        "bruun_lot", "numista",
    }
    catalog: dict = {}
    if data.get("catalog_number"):
        cat = data["catalog_number"]
        parts = cat.split("#", 1)
        if len(parts) == 2:
            prefix = parts[0].strip().lower()
            value = parts[1].strip()
            if prefix in _ALLOWED_CATALOG_KEYS:
                catalog[prefix] = value
            elif prefix == "fr":
                catalog["fr"] = value
    for k, v in (data.get("catalog_refs") or {}).items():
        key = "fr" if k == "friedberg" else k
        if key in _ALLOWED_CATALOG_KEYS:
            catalog.setdefault(key, v)

    # Issuer classification — three-tier with country-vs-mint priority
    # determined by country specificity:
    #
    # Tier 1 (SPECIFIC subnational country): country wins.
    #   E.g. country=HOLSTEIN-GOTTORP-RENDSBORG → gottorp_duchy. Krause
    #   has explicitly tagged this as a sub-state coinage (Christian
    #   August's brief HGR period 1716-1720). Mint=Rendsburg alone
    #   would route to royal_holstein default — wrong for this catalog
    #   attribution.
    #
    # Tier 2 (UMBRELLA country): mint-classifier with year wins, country
    # used as fallback when mint is None or unclassifiable.
    #   E.g. country=DENMARK + mint=Altona post-1640 → royal_holstein
    #   (Altona Royal-Danish mint location, NOT Copenhagen-area
    #   danish_realm). Country=SCHAUMBURG-PINNEBERG + mint=Rinteln →
    #   schauenburg_pinneberg (Holstein side) or grafschaft_schaumburg (NS mints).
    #   Country=SCHAUMBURG-PINNEBERG + mint=Altona pre-1640 →
    #   schauenburg_pinneberg via year-aware override.
    #
    # Tier 3 (unknown country): fall back to target-location default.
    #
    # Umbrella set captures Krause groupings that lump together coinage
    # from multiple political entities (Denmark = realm + royal-Holstein
    # + royal-Schleswig portions; Schaumburg-Pinneberg = full Schauenburg
    # including ancestral non-SH region; etc.).
    _UMBRELLA_COUNTRIES = {
        "DENMARK", "NORWAY", "NORW AY", "DENMARK-NORWAY",
        "SCHLESWIG-HOLSTEIN", "SCHAUMBURG-PINNEBERG", "SWEDEN",
    }

    issuing: str | None = None
    country_upper = (data.get("country") or "").upper()
    country_tag = COUNTRY_TO_ISSUING_ENTITY.get(country_upper)

    if country_upper in _UMBRELLA_COUNTRIES:
        # Umbrella → mint-classifier first, country-tag as fallback.
        from lib.v2_entity_classify import classify_mint_to_entity  # noqa: PLC0415
        raw_mint = data.get("mint")
        if raw_mint:
            mint_tag = classify_mint_to_entity(raw_mint, year=yf)
            if mint_tag:
                issuing = mint_tag
        if issuing is None:
            issuing = country_tag
    else:
        # Specific subnational country → country wins.
        issuing = country_tag

    if issuing is None:
        # Last-resort fallback by target-location (rare — keeps un-recognised
        # country strings safe). SH location → SH duchy; denmark location
        # → danish_realm default.
        issuing = {
            "schleswig_holstein": "schleswig_holstein_duchy",
            "denmark": "danish_realm",
        }.get(location, "danish_realm")

    # Fineness sanity-check — Coin.fineness schema enforces [0, 1] (decimal
    # fraction). NumisMaster occasionally concatenates Composition + Fineness
    # into one «Composition» field («Silver Fineness: 40.7»), so the parser
    # mis-reads the gross mass as fineness on those records. Drop out-of-range
    # fineness values to keep the seed schema-clean; curators can backfill from
    # the parsed.json or primary sources later.
    raw_fineness = data.get("fineness")
    if raw_fineness is not None and (raw_fineness < 0 or raw_fineness > 1):
        raw_fineness = None

    # Build year_label + year_ranges. Preference order:
    #   1. `dates_explicit` from the «Value information» table — per-year
    #      precision (e.g. 1632, 1636, 1642 for an entry whose Date range
    #      is 1632-1642). When available, render as comma-list and emit
    #      per-year `year_ranges` so the rendering layer can show the
    #      discrete-year shape rather than the bracketing range.
    #   2. Otherwise fall back to date_raw. Collapse single-year ranges:
    #      «1628 - 1628» → «1628» (else the rendered «1628 - 1628» reads
    #      as a 1-year range, which is incorrect for what is actually a
    #      single dated coin).
    # Undated («ND(YYYY-YY)») coins: the parser has already put the ND-marker range
    # into yf/yl and cleared dates_explicit; here we flag the year as attribution-
    # only (year_verified: false, §4) below.
    undated = bool(data.get("undated"))
    dates_explicit = data.get("dates_explicit") or []
    if dates_explicit:
        # dates_explicit is the per-coin attested year list from the
        # NumisMaster «Value information» price table. It is the
        # SOURCE OF TRUTH for year_first / year_last / year_ranges when
        # present — the broader `date_raw` range («1632 - 1642») is an
        # editorial summary that may bracket years where no specimens are
        # actually documented in the table. We anchor on the table values.
        #
        # Consecutive attested years collapse into a single range entry
        # (e.g. 1522, 1523, 1524 → 1522–1524) per CLAUDE.md §3a canonical
        # year_label form. Both `year_label` and `year_ranges` reflect the
        # grouped shape so the timeline visualisation also draws one bar
        # per run instead of N bars per individual year.
        grouped = _group_consecutive_years(dates_explicit)
        year_label = _format_year_label(grouped)
        year_ranges = [[a, b] for a, b in grouped]
        yf = grouped[0][0]
        yl = grouped[-1][1]
    else:
        # Single-year collapse: «1628 - 1628» → «1628»
        if yf is not None and yl is not None and yf == yl:
            year_label = str(yf)
        elif undated and yf is not None and yl is not None:
            # UNDATED coin: yf/yl come from the «ND(YYYY-YY)» marker (parser), NOT
            # from date_raw — date_raw is the stale collapsed structured field
            # («1618 - 1618»), so build the label from the ND range instead.
            year_label = _format_year_label([[yf, yl]])
        else:
            year_label = data.get("date_raw")
        year_ranges = [[yf, yl if yl is not None else yf]]

    # metal_verified: when NumisMaster's «Composition» field is explicitly
    # populated (most pages), the metal classification is source-attested;
    # flip the flag to true so the (?) marker doesn't render. Pages whose
    # composition is None (or where our detect_metal heuristic guessed
    # from denomination tokens) keep metal_verified absent / false.
    metal_attested = bool(data.get("composition"))

    entry: dict = {
        "id": cid,
        "fuss": "seed_unsorted",
        "phase": "numismaster",
        "kind": "kurant",
        "nominal": _normalize_denomination(data.get("denomination")),
        "year_label": year_label,
        "year_first": yf,
        "year_last": yl if yl is not None else yf,
        "year_ranges": year_ranges,
        "ruler": data.get("ruler"),
        "mint": data.get("mint"),
        "catalog": catalog,
        "metal": metal,
        "fineness": raw_fineness,
        "weight_rough_g": data.get("mass_g"),
        "issuing_entity": issuing,
        "verified": False,
        "metal_verified": metal_attested,
        "fineness_verified": raw_fineness is not None,
        "weight_rough_verified": data.get("mass_g") is not None,
        "mint_verified": bool(data.get("mint")),
        "sources": [
            {
                "type": "literature",
                "url": data.get("url"),
                "ref": "NumisMaster",
            }
        ],
        "verification_note": {
            "de": (
                "NumisMaster-Seed (§BK Phase 5): Krause-Mishler-basiertes "
                "kommerzielles Katalog (Librios). Per-Münze-Verifikation "
                "gegen Primärquellen (Hede / Sieg / Lange / Wilcke / "
                "Schive) vor §BF-Promotion."
            ),
            "en": (
                "NumisMaster seed (§BK Phase 5): Krause-Mishler-based "
                "commercial catalogue (Librios). Per-coin verification "
                "against primary sources (Hede / Sieg / Lange / Wilcke / "
                "Schive) before §BF promotion."
            ),
            "uk": (
                "NumisMaster-seed (§BK Phase 5): Krause-Mishler-базований "
                "комерційний каталог (Librios). Покоінна верифікація "
                "проти первинних джерел (Hede / Sieg / Lange / Wilcke / "
                "Schive) перед §BF-промоцією."
            ),
        },
    }
    # UNDATED coin: the year is the «ND(…)» attribution range, not a struck date —
    # flag year_verified: false so the renderer shows «(?)» AND the coin is excluded
    # from phase/timeline outer-span expansion (build._expand_outer_phase_span,
    # timeline.derive_mint_overrides). Curator direction 2026-07-09 (Serhii).
    if undated:
        entry["year_verified"] = False
    # Enrichment fields not in Coin schema — prefix with `_` so build.py's
    # seed-merger strips them at validation time (line 343 in build.py). The
    # canonical raw record lives in MC_<N>.parsed.json; these `_`-keys keep
    # the enrichment visible on the seed YAML for human review without
    # tripping the strict Coin schema downstream.
    if data.get("political_period"):
        entry["_political_period"] = data["political_period"]
    if data.get("coinage_entity"):
        entry["_coinage_entity"] = data["coinage_entity"]
    if data.get("obverse"):
        entry["_obverse"] = data["obverse"]
    if data.get("reverse"):
        entry["_reverse"] = data["reverse"]
    if data.get("general_note"):
        entry["_general_note"] = data["general_note"]
    # _source_note candidate (Phase-1, commit 80a1b62): the cleaned + language-
    # tagged descriptive field, for the later note-selector. NumisMaster's
    # richest description is `general_note`; source language en. Non-schema
    # (underscore) → stripped before the strict Coin schema at final/render, so
    # nothing reaches the page yet. Wiring it here (the deferred follow-up) makes
    # a re-seed reproduce it durably instead of dropping the one-off population.
    _sn = source_note(data.get("general_note"), "en")
    if _sn:
        entry["_source_note"] = _sn
    if data.get("actual_weight_fein"):
        entry["_actual_weight_fein_g"] = data["actual_weight_fein"]
    # NumisMaster MC_ID as a stable lookup anchor (non-schema; survives merge
    # via underscore-prefix; useful for cross-checking against mc_index.json /
    # MC_<N>.parsed.json without re-parsing the id from the sources[0].url).
    entry["_numismaster_mc"] = str(mc)

    # Layer the tradition-driven entity-routing rules
    # (data/v2/entity_routing_rules.yml) on top of the mint/country default
    # computed above — same two-step path as build_numista_seed. Safe-mode:
    # the rule actively re-routes only when the coin's mint is None /
    # unverified, else just records a hint. This is what splits the Schauenburg
    # coinage — Niedersächsisch denominations (Mariengroschen / Fürstengroschen
    # / Arendschilling) on mint-less pieces re-route to grafschaft_schaumburg,
    # while the Holstein-Pinneberg default (schauenburg_pinneberg) and the
    # mint-authoritative Niedersachsen mints (Oldendorf/Stadthagen/… via
    # mint_registry) are honoured. The NumisMaster `country` string doubles as
    # the issuer lineage signal for the rule's issuer_any match.
    routing_input = dict(entry)
    routing_input["_numista_issuer"] = data.get("country")
    routed_ent, _hint = route_entity_with_rules(
        routing_input, default_entity=entry["issuing_entity"]
    )
    entry["issuing_entity"] = routed_ent
    if _hint is not None:
        entry["_entity_routing_hint"] = _hint

    return entry


def collect_from_cache(cache_name: str, location: str) -> tuple[list[dict], int]:
    """Walk one cache dir's parsed.json files → build entries for `location`.
    Applies CACHE_WINDOW[cache_name] year-range filter. Returns (entries, scanned)."""
    year_from, year_to = CACHE_WINDOW[cache_name]
    cache_dir = NUMISMASTER_CACHE / cache_name
    entries: list[dict] = []
    scanned = 0
    for json_path in sorted(cache_dir.glob("MC_*.parsed.json")):
        scanned += 1
        try:
            data = json.loads(json_path.read_text())
        except json.JSONDecodeError as e:
            print(f"  [{json_path.name}] parse error: {e}", file=sys.stderr)
            continue
        entry = build_entry(data, location, year_from, year_to)
        if entry:
            entries.append(entry)
    return entries, scanned


def build_seed(dry_run: bool) -> int:
    """V2-native: walk every cache once, classify each coin by issuing_entity
    (set per-coin via COUNTRY_TO_ISSUING_ENTITY map at build_entry time),
    delegate to shared `write_v2_seed` for grouping + per-entity output."""
    all_entries: list[dict] = []
    cache_summary: list[str] = []
    for cache_name in CACHE_WINDOW.keys():
        # collect_from_cache wants a `location` arg used only for fallback
        # entity assignment (rare); pass a sensible default based on cache
        # name so unrecognised `country` strings still route reasonably.
        fallback_location = {
            "schleswig_holstein": "schleswig_holstein",
        }.get(cache_name, "denmark")
        entries, scanned = collect_from_cache(cache_name, fallback_location)
        all_entries.extend(entries)
        yf, yt = CACHE_WINDOW[cache_name]
        cache_summary.append(f"{cache_name}({yf}-{yt}):{len(entries)}/{scanned}")

    print(f"  from caches → {', '.join(cache_summary)} = {len(all_entries)} total entries")
    scope_note = (
        "§BK NumisMaster seed — Krause-Mishler-based commercial catalogue "
        f"(Librios). Caches consumed: {', '.join(CACHE_WINDOW.keys())}. "
        "Per-cache year windows: " + ", ".join(
            f"{c}={CACHE_WINDOW[c][0]}-{CACHE_WINDOW[c][1]}" for c in CACHE_WINDOW
        ) + ". Per-coin verification against primary sources (Hede / Sieg / "
        "Lange / Wilcke / Schive) before §BF promotion. Krause numbering is "
        "per-country — see CLAUDE.md §9 caveat on cross-volume KM# collisions."
    )
    write_v2_seed(
        all_entries,
        source_name="numismaster",
        source_label="NumisMaster (numismaster.com per-coin HTML MC_NNNNN pages)",
        scope_note=scope_note,
        dry_run=dry_run,
    )
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    # `--all` and `--location` retained as no-op flags for backward compat
    # with shell scripts that still pass them; the new builder walks every
    # cache regardless.
    ap.add_argument("--all", action="store_true", help="(no-op; kept for compat)")
    ap.add_argument("--location", help="(no-op; kept for compat)")
    args = ap.parse_args()
    return build_seed(args.dry_run)


if __name__ == "__main__":
    sys.exit(main())
