#!/usr/bin/env python3
"""build_numista_pre1541_seed.py — §AZ Tier 3 seed builder.

Reads parsed Numista pre-1541 JSON sidecars from
scripts/cache/numista/denmark_pre_1541/n<N#>.json and emits
data/seed/numista/denmark_pre_1541.yml — a third parallel seed
source alongside Bruun (Tier 1) and Galster (Tier 2).

Numista's distinctive contribution per §BJ survey:
  - Per-specimen brutto + diameter often more precise than Galster
  - Cross-reference validation (SIEG/Galster/Schou/Fr/MB)
  - Photo credit traces to specimen-holding institution
    (Münzkabinett Berlin, Nationalmuseet i København)
  - Obverse + Reverse lettering with Latin → English translation
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CACHE_DIR = PROJECT_ROOT / "scripts" / "cache" / "numista" / "denmark_pre_1541"

sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
from lib.v2_seed_writer import write_v2_seed  # noqa: E402

YEAR_FROM = 1514
YEAR_TO = 1541


def normalise_ruler(kings: list[dict]) -> str | None:
    """Pick the most-specific ruler. If multiple, prefer the one that
    falls in the 1514-1541 window."""
    if not kings:
        return None
    in_window = []
    for k in kings:
        rg = k.get("reign", "")
        ym = re.search(r"(\d{4})", rg)
        if ym and 1513 <= int(ym.group(1)) <= 1559:
            in_window.append(k["name"])
    if in_window:
        return " / ".join(in_window)
    return kings[0]["name"]


def detect_metal(comp: dict, value_text: str | None) -> str:
    m = comp.get("metal")
    if m and m != "unknown":
        return m
    if value_text:
        v = value_text.lower()
        if "ducat" in v or "gulden" in v or "noble" in v or "krone" in v:
            return "gold"
        if "skilling" in v or "hvid" in v or "penning" in v:
            return "billon"
    return "silver"


def detect_issuing_entity(data: dict):
    """Returns V2 issuing_entity (scalar or list-form). Uses centralised
    mint→entity classifier with sub-realm fallback for entries lacking
    explicit mint info. Norway → `danish_norway` (V2-canonical),
    NOT legacy `norwegian_realm`."""
    mint = data.get("mint") or data.get("mint_text")
    if mint:
        from lib.v2_entity_classify import classify_mint_to_entity
        result = classify_mint_to_entity(mint)
        if result:
            return result
    issuer = (data.get("issuer") or "").lower()
    if "norway" in issuer:
        return "danish_norway"
    return "danish_realm"


def build_entry(data: dict) -> dict | None:
    nid = data.get("numista_id")
    if not nid:
        return None
    yf = data.get("year_first")
    yl = data.get("year_last")
    if yf is None:
        return None
    # Filter — entries fully outside scope rejected; overlapping kept
    # (the upstream fetcher's N# list is already scoped, so this is
    # belt-and-braces).
    if yl is not None and yl < YEAR_FROM:
        return None
    if yf > YEAR_TO:
        return None

    composition = data.get("composition") or {}
    value = data.get("value") or {}
    references = data.get("references") or {}
    obverse = data.get("obverse") or {}
    reverse = data.get("reverse") or {}

    cid = f"dk-numista-{nid}"

    metal = detect_metal(composition, value.get("raw"))
    fineness = composition.get("fineness")

    # Filter to schema-allowed catalog keys (per scripts/lib/schema.py
    # CatalogRefs model). Numista's per-coin `references` block can
    # carry non-schema entries (`brekke`, `thesen`, `aajt`, etc.) that
    # Pydantic's strict-extra=forbid rejects on Location load.
    _ALLOWED = {
        "km", "lange", "hede", "sieg", "schou", "fr", "dav", "mb",
        "bruun_collection_id", "bruun_part", "bruun_lot_no", "bruun_page",
        "bruun_lot", "numista", "hede_volume", "galster", "friedberg",
    }
    catalog: dict = {
        "numista": str(nid),
    }
    for k, v in references.items():
        if k in _ALLOWED:
            catalog[k] = v

    sources_list: list[dict] = [
        {
            "type": "literature",
            "url": data.get("url"),
            "ref": f"Numista N#{nid} — {data.get('title') or '?'}",
        }
    ]

    # Nominal preference: structured `value.raw` field first; fall back
    # to the title's denomination prefix («1 Joachimstaler - Christian
    # III ...» → «1 Joachimstaler») when `value` is null. Some Numista
    # entries (esp. pre-1541 / unusual types) leave the structured value
    # blank but the title carries the denomination explicitly.
    nominal = value.get("raw")
    if not nominal and data.get("title"):
        title = data["title"]
        # Split on " - " (Numista's canonical separator between
        # denomination prefix and ruler/era info).
        if " - " in title:
            nominal = title.split(" - ", 1)[0].strip()
    entry: dict = {
        "id": cid,
        "fuss": "seed_unsorted",
        "phase": "numista",
        "kind": "kurant",
        "nominal": nominal,
        "year_label": data.get("years_raw"),
        "year_first": yf,
        "year_last": yl if yl is not None else yf,
        "year_ranges": [[yf, yl if yl is not None else yf]],
        "ruler": normalise_ruler(data.get("kings") or []),
        "mint": data.get("mint"),
        "catalog": catalog,
        "metal": metal,
        "fineness": fineness,
        "weight_rough_g": data.get("weight_g"),
        "diameter_mm": data.get("diameter_mm"),
        "issuing_entity": detect_issuing_entity(data),
        "verified": False,
        # `metal_verified` true when Numista's composition_text actually
        # named a metal — Numista publishes composition explicitly on
        # every coin page; absence of `composition.metal` means the
        # builder fell through to denomination-based inference.
        "metal_verified": bool(composition.get("metal")),
        "fineness_verified": fineness is not None,
        "weight_rough_verified": data.get("weight_g") is not None,
        "diameter_mm_verified": data.get("diameter_mm") is not None,
        "mint_verified": data.get("mint") is not None,
        "sources": sources_list,
        "verification_note": {
            "de": (
                "Numista-Seed: spezifikische Müntzfuß- und Phase-Zuordnung "
                "sowie Per-Münze-Verifikation stehen noch aus; Daten direkt "
                "aus der HTML-Katalogseite (en.numista.com) übernommen. "
                "Numista ist Benutzer-editiert; Cross-references (SIEG, "
                "Galster, Schou, Fr) müssen gegen Primärquellen geprüft "
                "werden bevor in kuratierte Einträge promotet."
            ),
            "en": (
                "Numista seed: Müntzfuß and phase assignment plus per-coin "
                "verification are still outstanding; data taken directly "
                "from the HTML catalog page (en.numista.com). Numista is "
                "user-edited; cross-references (SIEG, Galster, Schou, Fr) "
                "must be checked against primary sources before promotion "
                "into curated entries."
            ),
            "uk": (
                "Numista-seed: призначення Müntzfuß і фази та покоінна "
                "верифікація ще очікуються; дані взято безпосередньо з "
                "HTML-каталог-сторінки (en.numista.com). Numista редагується "
                "користувачами; cross-references (SIEG, Galster, Schou, Fr) "
                "треба перевірити проти первинних джерел перед промоцією у "
                "кур'єйтед-записи."
            ),
        },
    }

    # Photo credit + lettering enrichment
    if data.get("photo_credit"):
        entry["photo_credit"] = data["photo_credit"]
    if obverse:
        entry["obverse"] = obverse
    if reverse:
        entry["reverse"] = reverse
    if data.get("title"):
        entry["numista_title"] = data["title"]
    if data.get("rarity_index"):
        entry["numista_rarity_index"] = data["rarity_index"]
    if data.get("shape"):
        entry["shape"] = data["shape"]
    if data.get("technique"):
        entry["technique"] = data["technique"]

    return entry


def collect_entries() -> list[dict]:
    entries: list[dict] = []
    for json_path in sorted(CACHE_DIR.glob("n*.json")):
        try:
            data = json.loads(json_path.read_text())
        except json.JSONDecodeError as e:
            print(f"  [{json_path.name}] parse error: {e}", file=sys.stderr)
            continue
        entry = build_entry(data)
        if entry:
            entries.append(entry)
    return entries


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
    args = ap.parse_args()
    print(f"Collecting Numista pre-1541 entries from {CACHE_DIR}...")
    entries = collect_entries()
    entries.sort(key=lambda e: (e.get("year_first", 9999), e.get("id", "")))

    from collections import Counter
    by_ruler = Counter(e.get("ruler") or "?" for e in entries)
    by_mint = Counter(e.get("mint") or "?" for e in entries)
    by_metal = Counter(e.get("metal") for e in entries)
    by_realm = Counter(e.get("issuing_entity") for e in entries)
    print(f"\nTotal entries: {len(entries)}")
    print(f"By ruler: {dict(by_ruler.most_common())}")
    print(f"By mint:  {dict(by_mint.most_common(15))}")
    print(f"By metal: {dict(by_metal.most_common())}")
    print(f"By realm: {dict(by_realm.most_common())}")

    write_v2_seed(
        entries,
        source_name="numista",
        source_label="Numista en.numista.com per-coin HTML catalog (1514-1541 Denmark sub-window)",
        scope_note=(
            "§AZ Tier 3 — Numista HTML-scrape enrichment. Parallel source "
            "to v2/seed/bruun/ (Tier 1) + v2/seed/galster/ (Tier 2). "
            "Distinctive contribution: per-specimen diameter, photo credit "
            "to specimen-holding institution (Münzkabinett Berlin / "
            "Nationalmuseet i København), obverse + reverse lettering with "
            "Latin → English translations, and Numista rarity-index as a "
            "popular-availability indicator. Numista is user-edited — "
            "cross-references (SIEG, Galster, Schou, Fr, MB) require "
            "primary-source verification before §BF promotion."
        ),
        dry_run=args.dry_run,
        no_merge=args.no_merge,
        extra_top_level={
            "scope_year_from": YEAR_FROM,
            "scope_year_to": YEAR_TO,
        },
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
