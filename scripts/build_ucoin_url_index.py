#!/usr/bin/env python3
"""
Build a URL index per ucoin tid using slug-generation rules observed
from the listing harvest.

Output:  scripts/cache/ucoin/_url_index.json
         { "<tid>": {"url": "https://en.ucoin.net/coin/<slug>/?tid=<tid>",
                     "source": "<source>", "km": "<km>", "denom": "...",
                     "year": "...", "weight_g": ..., "fineness": ...} }

Slug rules observed (from sample slugs captured in q=holstein search):
  - lowercase, spaces → '-'
  - ½ → '1-2'   ⅓ → '1-3'   ⅔ → '2-3'   ¼ → '1-4'   ¾ → '3-4'
  - ⅙ → '1-6'   ⅛ → '1-8'   ⅕ → '1-5'   ⅖ → '2-5'   ⅗ → '3-5'
  - 2½ → '2-1-2',  1/N → '1-N'  (slash → '-')
  - ø → 'o',  ä → 'a',  ö → 'o',  ü → 'u',  ß → 'ss',  ł → 'l'
  - apostrophes / non-ASCII removed; multiple '-' collapsed

Country prefix per source:
  period_*, q_holstein_extras → 'denmark' (most), 'schleswig_holstein' (UC#100)
  country_schleswig_holstein  → 'schleswig_holstein'
  country_lubeck              → 'lubeck'
  country_hamburg             → 'hamburg'
"""
from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path

CACHE = Path("scripts/cache/ucoin")
OUT = CACHE / "_url_index.json"

VULGAR_FRACTIONS = {
    "½": "1-2", "⅓": "1-3", "⅔": "2-3",
    "¼": "1-4", "¾": "3-4",
    "⅕": "1-5", "⅖": "2-5", "⅗": "3-5", "⅘": "4-5",
    "⅙": "1-6", "⅚": "5-6",
    "⅛": "1-8", "⅜": "3-8", "⅝": "5-8", "⅞": "7-8",
}

PER_SOURCE_COUNTRY = {
    "country_schleswig_holstein": "schleswig_holstein",
    "country_lubeck": "lubeck",
    "country_hamburg": "hamburg",
    # All Denmark periods
    "period_374": "denmark",
    "period_646": "denmark",
    "period_647": "denmark",
    "period_846": "denmark",
    "period_1115": "denmark",
    "period_1147": "denmark",
    "period_2939": "denmark",
    "period_2940": "denmark",
    "period_2995": "denmark",
    "period_1204": "lubeck",
    "period_1205": "lubeck",
}

# UC#100 was found via q_holstein search, slug starts with schleswig_holstein
SPECIAL_SLUG = {
    "187884": "schleswig_holstein-1-sechsling-1850",  # UC# 100
}


def slugify_denom(s: str) -> str:
    """Replicate ucoin's slug algorithm for denomination + year."""
    if not s:
        return ""
    out = s
    # First: replace vulgar fractions
    for v, repl in VULGAR_FRACTIONS.items():
        # If preceded by a digit (e.g. "2½"), insert "-" between them
        out = re.sub(rf"(\d){re.escape(v)}", rf"\1-{repl}", out)
        out = out.replace(v, repl)
    # Decompose accents (ø, ü, ä, ö, ß handling first)
    out = out.replace("ø", "o").replace("Ø", "o")
    out = out.replace("ß", "ss")
    out = unicodedata.normalize("NFKD", out)
    out = "".join(c for c in out if not unicodedata.combining(c))
    # Slashes → '-'
    out = out.replace("/", "-")
    # Lowercase, replace non-alphanum with '-'
    out = out.lower()
    out = re.sub(r"[^\w\d]+", "-", out)
    # Collapse multiple '-'
    out = re.sub(r"-+", "-", out).strip("-")
    return out


def build_slug(country: str, denom: str, year: str) -> str:
    denom_slug = slugify_denom(denom)
    year_slug = year.replace("–", "-").replace("/", "-").replace(" ", "")
    parts = [country, denom_slug, year_slug]
    return "-".join(p for p in parts if p)


def main():
    index: dict[str, dict] = {}
    for f in sorted(CACHE.glob("*.tsv")):
        source = f.stem
        country = PER_SOURCE_COUNTRY.get(source, "denmark")
        for line in f.read_text().splitlines():
            line = line.rstrip("\r")
            if not line or line.startswith("#"):
                continue
            parts = line.split("\t")
            while len(parts) < 7:
                parts.append("")
            km, tid, denom, year, w, d, fine = parts[:7]
            tid = tid.strip()
            if not tid or not tid.isdigit():
                continue
            if tid in SPECIAL_SLUG:
                slug = SPECIAL_SLUG[tid]
            else:
                slug = build_slug(country, denom.strip(), year.strip())
            url = f"https://en.ucoin.net/coin/{slug}/?tid={tid}"
            entry = {
                "url": url,
                "source": source,
                "km": km.strip(),
                "denom": denom.strip(),
                "year": year.strip(),
                "weight_g": float(w) if w.strip() else None,
                "diameter_mm": float(d) if d.strip() else None,
                "fineness": float(fine) if fine.strip() else None,
            }
            # Don't overwrite a more-Holstein-relevant source with a less one
            existing = index.get(tid)
            if existing and existing["source"] in (
                "country_schleswig_holstein", "period_2939", "period_2995"
            ):
                continue
            index[tid] = entry

    with OUT.open("w") as fp:
        json.dump(index, fp, ensure_ascii=False, indent=2, sort_keys=True)
    print(f"Wrote {len(index)} entries to {OUT}")
    print(f"Sample slugs:")
    for tid in list(index.keys())[:8]:
        e = index[tid]
        print(f"  {tid}: {e['url']}")


if __name__ == "__main__":
    main()
