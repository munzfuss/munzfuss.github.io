#!/usr/bin/env python3
"""build_bruun_denmark_seed.py — generate `data/seed/bruun/denmark_pre_1541.yml`
from parsed Bruun-corpus lots.

Scope: §AZ Tier 1 (per `docs/research/denmark_pre_1541_source_survey.md`).
Hede 1957 monograph does NOT catalogue pre-Christian-III rulers; Bruun
PDFs are the primary specimen-attestation source for the 1514-1541
sub-window the §BI anchor rescope opened. This script transforms the
already-parsed Bruun lot JSON (`scripts/cache/bruun/lots/part{1-4}.json`)
into project-shaped seed entries that §BF can promote into curated
`data/locations/denmark.yml` coin entries.

This does NOT touch Hede-derived seed (`data/seed/hede/denmark.yml`) —
Bruun-seed is a parallel source. Both are consumed by §BF.

Scope filter: 1514 ≤ year ≤ 1541 AND region ∈ {DENMARK, NORW AY,
DENMARK-NORWAY}. Excludes:
  - Pre-1514 (Hans + Erik VII outside §BI anchor)
  - 1541+ Christian III post-Møntordning (already covered by hede-seed)
  - Sweden under Christian II (Kalmar Union political, but treated as
    out-of-realm for our seed; mints Stockholm 1535 under Christian III
    pre-king phase ARE kept since Christian III claimed Sweden)

Output schema mirrors `data/seed/hede/denmark.yml` for parser compatibility:
  - id: `dk-bruun-<bruun-coll-id>` (or `dk-bruun-pt<N>-<lot-no>` if no coll-id)
  - catalog: dict of all attested cross-refs from lot.refs
  - sources: Bruun-lot citation block + Stack's Bowers auction reference
  - bruun_collection_id / bruun_part / bruun_lot_no for fast lookup
  - verified: false on all per §AF/§4 (specimens are auction-grade, not
    project-verified)
  - fineness_verified / weight_rough_verified per attestation status

Run:
    .venv/bin/python scripts/maintenance/build_bruun_denmark_seed.py
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import ruamel.yaml

# Boilerplate ----------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CACHE_DIR = PROJECT_ROOT / "scripts" / "cache" / "bruun" / "lots"
OUT_PATH = PROJECT_ROOT / "data" / "seed" / "bruun" / "denmark_pre_1541.yml"

# Region filter — Bruun parser produced "NORW AY" with internal space
REALM_REGIONS = {"DENMARK", "NORW AY", "NORWAY", "DENMARK-NORWAY"}

# Year window (per §BI anchor)
YEAR_FROM = 1514
YEAR_TO = 1541

# Map Bruun ref-key to project catalog field
REF_FIELDS = {
    "Bruun": "bruun_collection_id",
    "Sieg": "sieg",
    "Schou": "schou",
    "Galster": "galster",
    "Fr": "friedberg",
    "Lange": "lange",
    "Dav": "davenport",
    "KM": "km",
    "Hede": "hede",
    "Schive": "schive",
    "NMD": "nmd",
    "Llt": "lott",
    "Delzanno": "delzanno",
    "SM": "sm",
    "Hagander": "hagander",
    "Appelgren": "appelgren",
    "MB": "mb_swedish",  # confirmed Swedish-specific per §BJ survey
    "Hauberg": "hauberg",
    "Malmer": "malmer",
}


def parse_year(lot: dict) -> int | None:
    """Try lot.year first, then regex on meta_line / body_excerpt.
    Reject medieval ND-ranges (10xx/11xx/12xx) BEFORE checking lot.year —
    the upstream Bruun parser sometimes sets lot.year to a stray 15xx
    catalog-ref token (Sieg-1535, etc.) on medieval-Penny lots."""
    meta = lot.get("meta_line") or ""
    body = lot.get("body_excerpt") or ""
    # Reject medieval ND-ranges outright — regardless of any 15xx token
    if re.search(r"ND\s*\([01]?[01]\d\d", meta) or re.search(r"ND\s*\([01]?2\d\d", meta):
        return None
    if re.search(r"ND\s*\([01]?[01]\d\d", body[:200]) or re.search(r"ND\s*\([01]?2\d\d", body[:200]):
        return None
    y = lot.get("year")
    if y is not None:
        try:
            return int(str(y)[:4])
        except (ValueError, TypeError):
            pass
    for src in (meta, body):
        if not src:
            continue
        # First 4-digit 15xx year in the text
        m = re.search(r"\b(15[0-4][0-9])\b", src)
        if m:
            return int(m.group(1))
    return None


def parse_ruler_from_meta(meta_line: str | None, body: str | None, ruler_hint: str | None) -> str | None:
    """Bruun parser sometimes mis-attributes a mintmaster name as `ruler`
    (e.g. "Hans Seyer" → ruler="Hans"). The meta_line carries the actual
    ruler after the period name + mint. Pattern: `<Country>. <Type>, <year>. <Mint> Mint. <RULER>. NGC ...`

    Meta and body may have line-break splits ("Christian \nII"). We
    normalise whitespace before matching."""
    text = " ".join((meta_line or "", body or ""))
    text = re.sub(r"\s+", " ", text)
    # Check "Hans Mule" — a real ruler-equivalent (archbishop) for Oslo 1523-24
    if re.search(r"\bHans\s+Mule\b", text):
        return "Hans Mule"
    # Christian III / II / I — III must be checked first to win match (III contains II)
    for r in ["Christian III", "Christian II", "Frederik I", "Frederick I"]:
        if re.search(rf"\b{re.escape(r)}\b", text):
            return r
    return ruler_hint


def parse_mint(lot: dict) -> str | None:
    """Extract mint from meta_line: pattern `<Mint> Mint.` typically."""
    meta = lot.get("meta_line") or ""
    # Direct ".Malmö Mint." or "Copenhagen Mint." patterns
    m = re.search(
        r"\b(Copenhagen|København|Malmö|Malmø|Malmo|Husum|Gottorp|Roskilde|"
        r"Aarhus|Ribe|Bergen|Oslo|Visby|Stockholm|Flensborg|Landskrona|"
        r"Helsingør|Helsingor|Lund)\s+Mint\b",
        meta,
    )
    if m:
        return m.group(1)
    # Without "Mint" suffix
    m = re.search(
        r"\b(Copenhagen|København|Malmö|Husum|Gottorp|Roskilde|Aarhus|Ribe|"
        r"Bergen|Oslo|Visby|Stockholm|Flensborg|Landskrona|Helsingør|Lund)\b",
        meta,
    )
    if m:
        return m.group(1)
    return lot.get("mint")


def parse_denomination(meta: str | None, body: str | None) -> str | None:
    """Extract a denomination string from meta_line."""
    if not meta:
        return None
    # Pattern: `<COUNTRY>. <denomination>, <year>.`
    m = re.match(r"^[^.]+\.\s+([^,]+),\s*(?:ND\s*)?[\(\d]", meta)
    if m:
        d = m.group(1).strip()
        # Filter junk
        if d.startswith("Gotland.") or d.startswith("Schleswig"):
            # secondary realm marker; strip it
            m2 = re.match(r"^[^.]+\.\s+([^,]+)", d)
            if m2:
                d = m2.group(1).strip()
        return d
    return None


def parse_metal(denom: str | None, refs: dict) -> str:
    """Best-effort metal classification from denomination."""
    if not denom:
        return "silver"  # safest default
    d = denom.lower()
    if any(t in d for t in ["nobel", "goldgulden", "rhinsk gylden", "ungersk gylden", "ducat", "dukat", "crown", "krone", "guldreal"]) and "silver" not in d:
        return "gold"
    if "fr" in refs:  # Friedberg only appears on gold lots per §BJ key
        return "gold"
    if "klipping" in d or "klippe" in d:
        return "silver"  # billon Klippe usually classed as silver
    if "hvid" in d or "penning" in d or "blaffert" in d:
        return "billon"
    if "skilling" in d or "søsling" in d or "sosling" in d:
        return "billon"  # most pre-1541 skillinge are debased
    if "joachimstaler" in d or "joachimsdaler" in d or "silver gulden" in d or "sølvgylden" in d or "solvgylden" in d:
        return "silver"
    if "mark" in d:
        return "silver"
    return "silver"


def parse_mintmaster(body: str | None) -> str | None:
    """Pull `Mintmaster: <Name>` from body_excerpt."""
    if not body:
        return None
    m = re.search(r"Mintmaster:\s*([A-ZÆØÅa-zæøå .,()\-]+?)(?:\.|$|\sAn |\sExcept)", body)
    if m:
        return m.group(1).strip(" .,")
    return None


def parse_rarity(rarity: str | None) -> str | None:
    if not rarity:
        return None
    r = rarity.strip().upper()
    if "EXTREMELY" in r:
        return "RRR"
    if "VERY RARE" in r or "VRARE" in r:
        return "RR"
    if "RARE" in r:
        return "R"
    return None


def lot_id(part: int, lot: dict) -> str:
    refs = lot.get("refs") or {}
    bruun_id = refs.get("Bruun")
    if bruun_id:
        return f"dk-bruun-{bruun_id}"
    return f"dk-bruun-pt{part}-{lot.get('lot_no')}"


# Build coin entry ----------------------------------------------------


def build_coin_entry(part: int, lot: dict) -> dict | None:
    year = parse_year(lot)
    if year is None or not (YEAR_FROM <= year <= YEAR_TO):
        return None
    region = (lot.get("region") or "").strip()
    if region not in REALM_REGIONS:
        return None

    meta = lot.get("meta_line") or ""
    body = lot.get("body_excerpt") or ""
    refs = lot.get("refs") or {}
    ruler = parse_ruler_from_meta(meta, body, lot.get("ruler"))
    mint = parse_mint(lot)
    denom = parse_denomination(meta, body)
    metal = parse_metal(denom, refs)
    mintmaster = parse_mintmaster(body)

    catalog: dict[str, Any] = {}
    for k, field in REF_FIELDS.items():
        if k in refs:
            catalog[field] = refs[k]
    # Special: Jensen-Skjoldager key in Bruun refs (cited as "Jensen & Skjoldager-...")
    if "Jensen & Skjoldager" in body:
        m = re.search(r"Jensen\s*&?\s*Skjoldager-?\s*([A-Z0-9/\-,. ]+?)(?:[;.]|\sschou|\sweight)", body, re.IGNORECASE)
        if m:
            catalog["jensen_skjoldager"] = m.group(1).strip().rstrip(",;")

    # Norwegian region marker
    is_norway = "NORW" in region

    cid = lot_id(part, lot)
    entry: dict[str, Any] = {
        "id": cid,
        "fuss": "seed_unsorted",
        "phase": "bruun",
        "kind": "kurant",
        "nominal": denom,
        "year_label": str(year),
        "year_first": year,
        "year_last": year,
        "year_ranges": [[year, year]],
        "ruler": ruler,
        "mint": mint,
        "catalog": catalog,
        "metal": metal,
        "fineness": None,  # not in Bruun lot data; comes from spec tables (Wilcke)
        "weight_rough_g": lot.get("weight_g"),
        "issuing_entity": "norwegian_realm" if is_norway else "danish_realm",
        "verified": False,
        "fineness_verified": False,
        "weight_rough_verified": bool(lot.get("weight_g")),
        "mint_verified": bool(mint),
        "sources": [
            {
                "type": "literature",
                "ref": (
                    f"Bruun-{refs.get('Bruun', '?')} · Stack's Bowers Bruun "
                    f"Collection Part {{romnum}}, lot {lot.get('lot_no')}"
                ).format(romnum=("I", "II", "III", "IV")[part - 1]),
            }
        ],
        "verification_note": {
            "de": (
                "Bruun-Seed: spezifikische Münzfuß- und Phase-Zuordnung sowie "
                "Per-Münze-Verifikation stehen noch aus; Daten direkt aus dem "
                "Bruun-Auktionskatalog (Stack's Bowers L. E. Bruun Collection 2024-2026) "
                "übernommen. Brutto-Gewicht ist ein per-Specimen-Wert; Feingehalt "
                "fehlt in Bruun-Daten und folgt aus dem Wilcke 1950-Ordonnance-"
                "Spezifikations-Tabel (s. docs/research/moentordning_1541.md)."
            ),
            "en": (
                "Bruun seed: Müntzfuß and phase assignment plus per-coin "
                "verification are still outstanding; data taken directly from "
                "the Bruun auction catalogue (Stack's Bowers L. E. Bruun "
                "Collection 2024-2026). Brutto weight is a per-specimen value; "
                "fineness is not in Bruun data and follows from the Wilcke 1950 "
                "ordinance specification table (see docs/research/moentordning_1541.md)."
            ),
            "uk": (
                "Bruun-seed: призначення Müntzfuß і фази та покоінна верифікація "
                "ще очікуються; дані взято безпосередньо з аукціонного каталогу "
                "Bruun (Stack's Bowers L. E. Bruun Collection 2024-2026). "
                "Brutto-вага це per-specimen значення; проба відсутня в Bruun-"
                "даних і випливає з таблиці специфікацій ордонансів Wilcke 1950 "
                "(див. docs/research/moentordning_1541.md)."
            ),
        },
    }

    # Carry mintmaster as a note field (project schema doesn't have dedicated)
    if mintmaster:
        entry["mintmaster"] = mintmaster

    # Rarity flag
    rarity = parse_rarity(lot.get("rarity"))
    if rarity:
        entry["rarity"] = rarity

    # NGC grade as a per-specimen quality flag
    if lot.get("grade"):
        entry["ngc_grade"] = lot.get("grade")

    # Bruun-citation fast-lookup anchor
    bruun_id = refs.get("Bruun")
    if bruun_id:
        entry["bruun_collection_id"] = bruun_id
        entry["bruun_part"] = part
        entry["bruun_lot_no"] = lot.get("lot_no")
        if lot.get("page"):
            entry["bruun_page"] = lot["page"]

    return entry


# Main pipeline -------------------------------------------------------


def collect_entries() -> list[dict]:
    entries: list[dict] = []
    for part in (1, 2, 3, 4):
        path = CACHE_DIR / f"part{part}.json"
        if not path.exists():
            print(f"  warning: {path} missing — skipping", file=sys.stderr)
            continue
        data = json.loads(path.read_text())
        added = 0
        for lot in data:
            entry = build_coin_entry(part, lot)
            if entry:
                entries.append(entry)
                added += 1
        print(f"  part{part}: {added} entries added (from {len(data)} total lots)")
    return entries


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--dry-run", action="store_true", help="Print summary; do not write file")
    args = ap.parse_args()

    print(f"Collecting Bruun pre-1541 realm entries ({YEAR_FROM}-{YEAR_TO})...")
    entries = collect_entries()
    print(f"\nTotal entries: {len(entries)}\n")

    # Sort by year, then by Bruun-id
    entries.sort(key=lambda e: (e.get("year_first", 9999), e.get("bruun_collection_id", "")))

    # Summary
    from collections import Counter
    by_ruler = Counter(e.get("ruler") or "?" for e in entries)
    by_mint = Counter(e.get("mint") or "?" for e in entries)
    by_metal = Counter(e.get("metal") or "?" for e in entries)
    print(f"By ruler: {dict(by_ruler.most_common())}")
    print(f"By mint: {dict(by_mint.most_common())}")
    print(f"By metal: {dict(by_metal.most_common())}")

    if args.dry_run:
        return 0

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    yaml = ruamel.yaml.YAML()
    yaml.preserve_quotes = True
    yaml.width = 200
    yaml.indent(mapping=2, sequence=4, offset=2)

    out = {
        "status": "seed",
        "source": "Stack's Bowers L. E. Bruun Collection (parts I-IV, 2024-2026)",
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "scope_year_from": YEAR_FROM,
        "scope_year_to": YEAR_TO,
        "scope_note": (
            "§AZ Tier 1 — Bruun corpus pre-1541 realm lots, covers the gap "
            "Hede 1957 doesn't catalogue (Christian II + Frederik I + "
            "Christian III pre-1541 Møntordning). NOT a substitute for the "
            "Hede seed at data/seed/hede/denmark.yml; parallel source."
        ),
        "coins": entries,
    }
    with OUT_PATH.open("w") as f:
        yaml.dump(out, f)
    print(f"\nWrote {OUT_PATH.relative_to(PROJECT_ROOT)} ({len(entries)} entries)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
