#!/usr/bin/env python3
"""Apply Numista enrichment: replace catalog-list URLs with piece-level URLs,
enrich catalog{} blocks with Fr#, Lange# refs pulled from Numista metadata.

Run once:
    .venv/bin/python scripts/apply_numista_enrichment.py
"""
from __future__ import annotations
import json, pathlib, re
from ruamel.yaml import YAML

yaml = YAML()
yaml.preserve_quotes = True
yaml.width = 10000
yaml.indent(mapping=2, sequence=4, offset=2)

SCRATCH = pathlib.Path("scripts/numista_scratch.json")
YML = pathlib.Path("data/locations/schleswig.yml")

scratch = json.loads(SCRATCH.read_text())
pieces = scratch["pieces"]
mapping = scratch["_mapping_missing_coins"]
not_on_numista = set(mapping.get("_not_on_numista", []))

data = yaml.load(YML.read_text())

# Parse refs: "KM# 147" → ("km", "147"); "Fr# 3082" → ("fr", "3082")
REF_FIELD_MAP = {
    "KM#": "km",
    "Fr#": "fr",
    "Friedberg#": "fr",
    "Lange#": "lange",
    "Hede#": "hede",
    "Sieg#": "sieg",
    "Schou#": "schou",
    "Bruun#": "bruun_lot",
    "Dav#": "dav",
    "Aagaard#": "aagaard",
    "Galster#": "galster",
}


def parse_ref(ref: str):
    parts = ref.split(" ", 1)
    if len(parts) != 2:
        return None
    prefix = parts[0] + ("#" if not parts[0].endswith("#") else "")
    field = REF_FIELD_MAP.get(prefix)
    if not field:
        return None
    return field, parts[1]


def ensure_source(coin, piece_id: str, extra_refs: list[str]):
    """Replace the catalog-list URL with the piece URL. Also ensures a Numista source exists."""
    piece_url = f"https://en.numista.com/catalogue/pieces{piece_id}.html"
    sources = coin.get("sources") or []
    replaced = False
    for s in sources:
        url = s.get("url") or ""
        if "schleswig_holstein_gottorp_duchy" in url:
            s["url"] = piece_url
            s["type"] = "numista"
            s["ref"] = "Numista"
            replaced = True
    if not replaced:
        # No catalog-list URL; just make sure there's a Numista source if missing
        if not any(("numista.com" in (s.get("url") or "")) for s in sources):
            sources.append({"type": "numista", "url": piece_url, "ref": "Numista"})
    coin["sources"] = sources


def drop_catalog_list(coin):
    sources = coin.get("sources") or []
    sources = [s for s in sources if "schleswig_holstein_gottorp_duchy" not in (s.get("url") or "")]
    coin["sources"] = sources


def enrich_catalog(coin, refs: list[str]):
    """Merge Fr#, Lange#, Hede# etc. into coin.catalog if not already present."""
    cat = coin.get("catalog") or {}
    for r in refs:
        parsed = parse_ref(r)
        if not parsed:
            continue
        field, val = parsed
        if field == "km":
            continue  # Already known from our data; don't overwrite
        if not cat.get(field):
            cat[field] = val
    coin["catalog"] = cat


def collect_piece_id_from_sources(coin) -> str | None:
    for s in coin.get("sources") or []:
        url = s.get("url") or ""
        m = re.search(r"numista\.com/(?:catalogue/pieces)?(\d+)(?:\.html)?", url)
        if m and "schleswig_holstein_gottorp_duchy" not in url:
            return m.group(1)
    return None


# ─── Step 1: fix 19 catalog-list-URL coins ───────────────────────────────────
fixed = 0
dropped = 0
for coin in data.get("coins", []) or []:
    cid = coin.get("id")
    if cid in mapping and cid not in {"_not_on_numista"}:
        pid = mapping[cid]
        if pid:
            ensure_source(coin, pid, pieces.get(pid, {}).get("refs", []))
            enrich_catalog(coin, pieces.get(pid, {}).get("refs", []))
            fixed += 1
            print(f"  fixed  {cid:40s} → /pieces{pid}.html")
    elif cid in not_on_numista:
        drop_catalog_list(coin)
        dropped += 1
        print(f"  dropped catalog-list  {cid:40s} (not on Numista)")

# ─── Step 2: enrich all other coins that already have piece URLs ──────────────
enriched = 0
for coin in data.get("coins", []) or []:
    pid = collect_piece_id_from_sources(coin)
    if not pid or pid not in pieces:
        continue
    p = pieces[pid]
    refs = p.get("refs") or []
    before = dict(coin.get("catalog") or {})
    enrich_catalog(coin, refs)
    after = dict(coin.get("catalog") or {})
    new_keys = set(after) - set(before)
    if new_keys:
        enriched += 1
        print(f"  enriched {coin.get('id'):40s} +{sorted(new_keys)}")

# ─── Save ─────────────────────────────────────────────────────────────────────
with open(YML, "w") as f:
    yaml.dump(data, f)

print()
print(f"Fixed {fixed} catalog-list URLs → piece URLs")
print(f"Dropped {dropped} catalog-list URLs (piece not on Numista)")
print(f"Enriched {enriched} coins with extra catalog refs (Fr#/Lange#/…)")
