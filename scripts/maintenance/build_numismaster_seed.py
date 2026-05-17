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
import sys
from datetime import datetime, timezone
from pathlib import Path

import ruamel.yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from lib.paths import NUMISMASTER_CACHE, PROJECT_ROOT  # noqa: E402
from lib.seed_merge import merge_seed  # noqa: E402

SEED_ROOT = PROJECT_ROOT / "data" / "seed" / "numismaster"

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

# Map NumisMaster `country` strings → project `issuing_entity` tag. The 9 SH
# cadet-line countries map to schleswig_holstein_duchy (consistent with how
# the existing curated seed treats Holstein-Gottorp-Rendsborg).
COUNTRY_TO_ISSUING_ENTITY: dict[str, str] = {
    "DENMARK": "danish_realm",
    "NORWAY": "norwegian_realm",
    "NORW AY": "norwegian_realm",  # observed parser variant
    "SWEDEN": "danish_realm",       # only Christian-II 1514-1523 in mission scope (= Danish-rule)
    "SCHLESWIG-HOLSTEIN": "schleswig_holstein_duchy",
    "SCHLESWIG-HOLSTEIN-GLUCKSBURG": "schleswig_holstein_duchy",
    "SCHLESWIG-HOLSTEIN-GOTTORP": "schleswig_holstein_duchy",
    "SCHLESWIG-HOLSTEIN-NORBURG": "schleswig_holstein_duchy",
    "SCHLESWIG-HOLSTEIN-PLOEN": "schleswig_holstein_duchy",
    "SCHLESWIG-HOLSTEIN-SONDERBURG": "schleswig_holstein_duchy",
    "SCHAUMBURG-PINNEBERG": "schleswig_holstein_duchy",
    "HOLSTEIN-GOTTORP-RENDSBORG": "schleswig_holstein_duchy",
    "GLUCKSTADT": "schleswig_holstein_duchy",
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


def build_entry(data: dict, location: str, year_from: int, year_to: int) -> dict | None:
    yf = data.get("year_first")
    yl = data.get("year_last")
    if yf is None:
        return None
    if (yl or yf) < year_from or yf > year_to:
        return None

    mc = data.get("numismaster_id")
    if mc is None:
        return None
    cid = _coin_id(location, mc)

    composition = data.get("composition") or ""
    metal = detect_metal(composition, data.get("denomination"))

    # Catalog refs — schema-clean subset only. Coin.catalog (CatalogRefs)
    # accepts: km, lange, hede, sieg, schou, fr, dav, bruun_collection_id,
    # bruun_part, bruun_lot_no, bruun_page, bruun_lot, numista. NumisMaster's
    # extra-vocabulary refs (mb / schive / numismaster_mc / generic bruun-
    # number) are dropped here — the canonical raw record lives in
    # `MC_<N>.parsed.json`, so curators who want them open the cache. The
    # parser's `friedberg` key maps to schema `fr`.
    _ALLOWED_CATALOG_KEYS = {
        "km", "lange", "hede", "sieg", "schou", "fr", "dav",
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
            if prefix == "km":
                catalog["km"] = value
            elif prefix == "fr":
                catalog["fr"] = value
            # MB# / other prefixes are not in schema; carried only on the parsed JSON
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

    entry: dict = {
        "id": cid,
        "fuss": "seed_unsorted",
        "phase": "numismaster",
        "kind": "kurant",
        "nominal": data.get("denomination"),
        "year_label": data.get("date_raw"),
        "year_first": yf,
        "year_last": yl if yl is not None else yf,
        "year_ranges": [[yf, yl if yl is not None else yf]],
        "ruler": data.get("ruler"),
        "mint": data.get("mint"),
        "catalog": catalog,
        "metal": metal,
        "fineness": raw_fineness,
        "weight_rough_g": data.get("mass_g"),
        "issuing_entity": issuing,
        "verified": False,
        "fineness_verified": raw_fineness is not None,
        "weight_rough_verified": data.get("mass_g") is not None,
        "mint_verified": bool(data.get("mint")),
        "sources": [
            {
                "type": "literature",
                "url": data.get("url"),
                "ref": (
                    f"NumisMaster MC_{mc} — "
                    f"{data.get('country', '?')} {data.get('catalog_number', '')} "
                    f"{data.get('denomination', '')} {data.get('date_raw', '')}".strip()
                ),
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


def build_seed(location: str, no_merge: bool, dry_run: bool) -> int:
    if location not in LOCATION_CACHES:
        print(f"ERROR: unknown location '{location}'. Valid: {list(LOCATION_CACHES)}", file=sys.stderr)
        return 2
    out_path = SEED_ROOT / f"{location}.yml"
    caches = LOCATION_CACHES[location]

    all_entries: list[dict] = []
    total_scanned = 0
    cache_summary: list[str] = []
    for cache_name in caches:
        entries, scanned = collect_from_cache(cache_name, location)
        all_entries.extend(entries)
        total_scanned += scanned
        yf, yt = CACHE_WINDOW[cache_name]
        cache_summary.append(f"{cache_name}({yf}-{yt}):{len(entries)}/{scanned}")

    all_entries.sort(key=lambda e: (e.get("year_first", 9999), e.get("id", "")))
    print(f"  [{location}] from caches → {', '.join(cache_summary)} = {len(all_entries)} total entries")
    if dry_run:
        return 0
    out_path.parent.mkdir(parents=True, exist_ok=True)

    if not no_merge:
        all_entries, stats = merge_seed(all_entries, out_path)
        print(
            f"  [{location}] merge: merged_existing={stats['merged_existing']}, "
            f"added_new={stats['added_new']}, orphan_curated={stats['orphan_curated']}"
        )

    yaml = ruamel.yaml.YAML()
    yaml.preserve_quotes = True
    yaml.width = 200
    yaml.indent(mapping=2, sequence=4, offset=2)

    scope_note = (
        f"§BK NumisMaster seed for location `{location}`. Krause-Mishler-based "
        f"commercial catalogue (Librios). Caches consumed: {', '.join(caches)}. "
        f"Per-cache year windows: " + ", ".join(
            f"{c}={CACHE_WINDOW[c][0]}-{CACHE_WINDOW[c][1]}" for c in caches
        ) + ". Per-coin verification against primary sources (Hede / Sieg / "
        "Lange / Wilcke / Schive) before §BF promotion. Krause numbering is "
        "per-country — see CLAUDE.md §9 caveat on cross-volume KM# collisions."
    )

    out = {
        "status": "seed",
        "source": "NumisMaster (numismaster.com per-coin HTML MC_NNNNN pages)",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "location": location,
        "caches": list(caches),
        "scope_note": scope_note,
        "coins": all_entries,
    }
    with out_path.open("w") as f:
        yaml.dump(out, f)
    print(f"  [{location}] wrote {out_path.relative_to(PROJECT_ROOT)} ({len(all_entries)} entries)")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--location", choices=tuple(LOCATION_CACHES.keys()),
                   help="Build seed for one location")
    g.add_argument("--all", action="store_true",
                   help="Build seeds for every location")
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
    args = ap.parse_args()

    locations = list(LOCATION_CACHES.keys()) if args.all else [args.location]
    rc = 0
    for loc in locations:
        rc = build_seed(loc, args.no_merge, args.dry_run) or rc
    return rc


if __name__ == "__main__":
    sys.exit(main())
