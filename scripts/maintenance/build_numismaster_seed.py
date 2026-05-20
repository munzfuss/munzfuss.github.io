#!/usr/bin/env python3
"""§BK NumisMaster Phase 5 — location-keyed seed builder.

Reads `scripts/cache/numismaster/<cache>/MC_<N>.parsed.json` files (output of
`scripts/parse_numismaster.py`) and emits one seed file per project LOCATION
under `data/seed/numismaster/<location>.yml`, with Coin-schema entries marked
`fuss: seed_unsorted`, `phase: numismaster`.

Locations and their cache composition (CACHE_WINDOW per cache + LOCATION_CACHES
roll-up):

  data/seed/numismaster/schleswig_holstein.yml
    ← cache/numismaster/schleswig_holstein/ (1514-1864, SH Danish-jurisdiction)

  data/seed/numismaster/denmark.yml
    ← cache/numismaster/denmark/ (1514-1914, project upper bound)
    ← cache/numismaster/norway/  (1608-1814, Norge under Danish rule only)
       — both fold into denmark.yml because the Denmark-Norway realm is a
         single coinage jurisdiction (Danish crown), same as how Hede 1971
         covers both under «Danmarks og Norges mønter».

Sweden-Christian-II is 0 entries (§BI negative finding) — no seed emitted.

Curation preservation: merge-aware via `scripts/lib/seed_merge.py` (§BL). Existing
`fuss`/`phase`/`fraction`/`issuing_entity`/`kind`/`note`/`*_verified` flags on
on-disk entries survive regeneration. Pass `--no-merge` for legacy wholesale
rewrite (verification / dry-run only).

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
        if "copper" in c:
            return "copper"
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

    issuing = COUNTRY_TO_ISSUING_ENTITY.get((data.get("country") or "").upper())
    if issuing is None:
        # Fallback by target-location (rare — keeps un-recognised country strings safe).
        # SH location → SH duchy; denmark location → danish_realm default (NO Norge
        # entries override via COUNTRY_TO_ISSUING_ENTITY[NORWAY] → norwegian_realm).
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
    if data.get("actual_weight_fein"):
        entry["_actual_weight_fein_g"] = data["actual_weight_fein"]
    # NumisMaster MC_ID as a stable lookup anchor (non-schema; survives merge
    # via underscore-prefix; useful for cross-checking against mc_index.json /
    # MC_<N>.parsed.json without re-parsing the id from the sources[0].url).
    entry["_numismaster_mc"] = str(mc)

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


def build_seed(no_merge: bool, dry_run: bool) -> int:
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
        no_merge=no_merge,
    )
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument(
        "--no-merge",
        action="store_true",
        help=(
            "Skip the curation-preserving merge against the existing on-disk "
            "seed and overwrite wholesale with fresh output. Destructive — only "
            "use for verification / dry-run paths."
        ),
    )
    # `--all` and `--location` retained as no-op flags for backward compat
    # with shell scripts that still pass them; the new builder walks every
    # cache regardless.
    ap.add_argument("--all", action="store_true", help="(no-op; kept for compat)")
    ap.add_argument("--location", help="(no-op; kept for compat)")
    args = ap.parse_args()
    return build_seed(args.no_merge, args.dry_run)


if __name__ == "__main__":
    sys.exit(main())
