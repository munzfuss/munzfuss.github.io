#!/usr/bin/env python3
"""Classify each coin in schleswig.yml by issuing political entity.

Heuristic rules (applied in order):
  1. Provisional Government 1850-1851 → 'provisional_govt'
  2. Gottorp ducal rulers (Adolf, John Adolphus, Frederick III v. Gottorp,
     Christian Albert, Frederick IV (Gottorp), Karl Friedrich, Karl Peter Ulrich)
     → 'gottorp_duchy' (until 1773)
  3. Pre-1773, Danish king + Holstein-related mint (Glückstadt/Altona/Poppenbüttel)
     → 'royal_holstein'
  4. Pre-1773, Danish king + Copenhagen / pure Danish mint
     → 'danish_realm'
  5. Post-1773 (after Gottorp buy-out) → 'gesamtstaat'
  6. Anything within Reichsgoldmünze era 1871+ → 'prussian_province'
  (Default fallback: gesamtstaat)

Run once:
    .venv/bin/python scripts/classify_issuing_entity.py
"""
from __future__ import annotations
import pathlib, re
from ruamel.yaml import YAML

yaml = YAML()
yaml.preserve_quotes = True
yaml.width = 10000
yaml.indent(mapping=2, sequence=4, offset=2)

GOTTORP_RULER_KEYS = (
    "von Gottorp",        # all our Gottorp dukes are normalized as 'X von Gottorp'
    "Christian Albrecht", # alternative German spelling
    "Karl Friedrich",     # alternative
    "Karl Peter Ulrich",  # alternative
    "Friedrich IV.",      # depending on normalization
    "John Adolphus",
    "Johann Adolf",
)

ROYAL_HOLSTEIN_MINTS = ("Glückstadt", "Altona", "Poppenbüttel")
DANISH_MINTS         = ("Kopenhagen", "København", "Copenhagen", "Christiansborg")


def is_gottorp_ruler(ruler: str) -> bool:
    if not ruler: return False
    return any(k in ruler for k in GOTTORP_RULER_KEYS)


def is_holstein_mint(mint: str) -> bool:
    if not mint: return False
    return any(m in mint for m in ROYAL_HOLSTEIN_MINTS)


def is_danish_mint(mint: str) -> bool:
    if not mint: return False
    return any(m in mint for m in DANISH_MINTS)


def classify(coin: dict) -> str:
    ruler = coin.get("ruler") or ""
    mint = coin.get("mint") or ""
    year = coin.get("year_first") or coin.get("year_last") or 1700
    fuss = coin.get("fuss") or ""

    # 1. Provisional Government 1850-1851
    if ruler.startswith("Prov.") or "Provisorisch" in ruler or "rovisional" in ruler:
        return "provisional_govt"
    if 1848 <= year <= 1851 and not ruler:
        return "provisional_govt"

    # 6. Reichsgoldmünze era → Prussian
    if fuss == "30_thaler" and year >= 1867:
        return "prussian_province"
    if year >= 1871:
        return "prussian_province"

    # 2. Gottorp dukes pre-1773
    if is_gottorp_ruler(ruler) and year < 1773:
        return "gottorp_duchy"

    # 5. Post-1773 — Gesamtstaat
    if year >= 1773:
        return "gesamtstaat"

    # 3. Pre-1773 Danish king at Holstein mint
    if is_holstein_mint(mint):
        return "royal_holstein"

    # 4. Pre-1773 Danish king at Copenhagen / Danish mint
    if is_danish_mint(mint):
        return "danish_realm"

    # Heuristic fallback: pre-1773 with no mint info but Danish king (Frederik III, Christian V, etc.)
    if any(k in ruler for k in ("Frederik III", "Christian V", "Christian IV", "Christian Albert")) \
       and not is_gottorp_ruler(ruler):
        return "royal_holstein"

    return "gesamtstaat"


def main():
    p = pathlib.Path("data/locations/schleswig.yml")
    data = yaml.load(p.read_text())

    classified_counts: dict[str, int] = {}
    for coin in data.get("coins", []) or []:
        if coin.get("issuing_entity"):
            continue  # don't overwrite existing
        ent = classify(coin)
        coin["issuing_entity"] = ent
        classified_counts[ent] = classified_counts.get(ent, 0) + 1

    with open(p, "w") as f:
        yaml.dump(data, f)

    print("Classification distribution:")
    for ent, n in sorted(classified_counts.items(), key=lambda x: -x[1]):
        print(f"  {ent:22s} {n}")
    print(f"\nTotal classified: {sum(classified_counts.values())}")


if __name__ == "__main__":
    main()
