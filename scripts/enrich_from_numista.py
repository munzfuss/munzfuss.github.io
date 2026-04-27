#!/usr/bin/env python3
"""Enrich coin.catalog with extra refs (Fr#, Lange#, Hede#, Sieg#, Schou#, Dav#, Galster#, Aagaard#)
pulled from Numista piece pages (metadata in scripts/numista_scratch.json).

For each coin with a piece-level Numista URL:
  1. Look up the piece by its ID in scratch.
  2. If scraped Numista KM# matches our YAML KM# → enrich catalog with non-KM refs.
  3. If mismatch → skip (log warning).
  4. If no KM# on Numista but piece is in our mapping → still enrich (trust mapping).

Also reports orphan/wrong Numista URLs (Numista piece is a completely different coin).

Run once:
    .venv/bin/python scripts/enrich_from_numista.py
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

REF_FIELD_MAP = {
    "KM#": "km",
    "Fr#": "fr", "Friedberg#": "fr",
    "Lange#": "lange",
    "Hede#": "hede",
    "Sieg#": "sieg",
    "Schou#": "schou",
    "Bruun#": "bruun_lot",
    "Dav#": "dav",
    "Aagaard#": "aagaard",
    "Galster#": "galster",
}


def parse_ref(r: str):
    parts = r.split(" ", 1)
    if len(parts) != 2: return None
    prefix = parts[0]
    if not prefix.endswith("#"): prefix += "#"
    field = REF_FIELD_MAP.get(prefix)
    if not field: return None
    return field, parts[1].strip()


def piece_id_of_coin(coin) -> str | None:
    for s in coin.get("sources") or []:
        url = s.get("url") or ""
        m = re.search(r"numista\.com/(?:catalogue/pieces)?(\d+)(?:\.html)?", url)
        if m: return m.group(1)
    return None


def normalize_km(km: str) -> str:
    """Normalize KM# for comparison: '82.1, 82.2' → '82' (prefix match); '124 / 150' → '124'."""
    if not km: return ""
    # Take first token
    first = re.split(r"[, /]+", str(km).strip())[0]
    return first


data = yaml.load(YML.read_text())

enriched = 0
mismatches = []
no_data = []
for coin in data.get("coins", []) or []:
    pid = piece_id_of_coin(coin)
    if not pid:
        continue
    p = pieces.get(pid)
    if not p:
        no_data.append((coin.get("id"), pid))
        continue
    numista_km = p.get("km", "") or ""
    our_km = normalize_km((coin.get("catalog") or {}).get("km", ""))
    if "MISMATCH" in numista_km or numista_km == "":
        # Skip — either not a piece-data-bearing page or wrong coin
        if "MISMATCH" in numista_km:
            mismatches.append((coin.get("id"), pid, p.get("v", "")))
        continue
    # Compare KM#. Accept prefix matches (Numista's "82" ↔ our "82.1"; "615" ↔ "615.1").
    n_km = normalize_km(numista_km)
    def same_or_prefix(a: str, b: str) -> bool:
        a = a.replace("A", "").replace("B", "")  # suffix letters
        b = b.replace("A", "").replace("B", "")
        if not a or not b: return True
        return a == b or a.startswith(b+".") or b.startswith(a+".")
    if our_km and n_km and not same_or_prefix(our_km, n_km):
        mismatches.append((coin.get("id"), pid, f"our KM# {our_km} vs Numista KM# {numista_km}"))
        continue
    # OK — enrich
    cat = coin.get("catalog") or {}
    added = []
    for r in p.get("refs", []) or []:
        parsed = parse_ref(r)
        if not parsed: continue
        field, val = parsed
        if field == "km": continue
        if not cat.get(field):
            cat[field] = val
            added.append(f"{field}={val}")
    if added:
        coin["catalog"] = cat
        enriched += 1
        print(f"  enriched {coin.get('id'):40s} + {', '.join(added)}")

with open(YML, "w") as f:
    yaml.dump(data, f)

print()
print(f"Enriched {enriched} coins with extra catalog refs.")
if mismatches:
    print(f"\n⚠ {len(mismatches)} Numista URL mismatches (wrong piece linked in YAML):")
    for cid, pid, note in mismatches:
        print(f"    {cid:40s} /pieces{pid}.html  — {note}")
if no_data:
    print(f"\n  (no Numista metadata scraped for {len(no_data)} coins; run browser scraper on: {[pid for _,pid in no_data]})")
