#!/usr/bin/env python3
"""Fix wrong Numista URLs (pieces point to completely different coins).

Discovered via browser scraping:
  - /pieces34035.html → Chinese 5 Fen (wrong)
  - /pieces34036.html → Mauritius ¼ Rupee (wrong)
  - /pieces39943.html → Roman Semis (wrong)
  - /pieces46014.html → Central African 50 Francs (wrong)
  - /pieces112808.html → cladded-aluminum coin (wrong)

Correct replacements found:
  - km-116-chr-v-1787 → /pieces35000.html  (1 Dreiling - Christian VII 1787)
  - km-118-chr-v-1787 → /pieces33159.html  (1 Sechsling - Christian VII 1787)
  - km-162-1850      → /pieces19525.html  (1 Sechsling Prov. Gov. 1850-1851)

Not findable via Numista (drop URL):
  - km-721-chr-v-1841 (4 Rigsbankskilling 1841)
  - km-64-1-chr-v-1674 (1 Dukat Glückstadt 1674)

Run once:
    .venv/bin/python scripts/fix_wrong_numista_urls.py
"""
from __future__ import annotations
import pathlib, re
from ruamel.yaml import YAML

yaml = YAML()
yaml.preserve_quotes = True
yaml.width = 10000
yaml.indent(mapping=2, sequence=4, offset=2)

REPLACE = {
    "km-116-chr-v-1787": "https://en.numista.com/catalogue/pieces35000.html",
    "km-118-chr-v-1787": "https://en.numista.com/catalogue/pieces33159.html",
    "km-162-1850":       "https://en.numista.com/catalogue/pieces19525.html",
}

DROP = {"km-721-chr-v-1841", "km-64-1-chr-v-1674"}

# Bad-URL fragments to detect
BAD_PIECES = {"pieces34035", "pieces34036", "pieces39943", "pieces46014", "pieces112808"}

p = pathlib.Path("data/locations/schleswig.yml")
data = yaml.load(p.read_text())

replaced = 0
dropped = 0
for coin in data.get("coins", []) or []:
    cid = coin.get("id")
    new_url = REPLACE.get(cid)
    needs_drop = cid in DROP
    sources = coin.get("sources") or []
    new_sources = []
    for s in sources:
        url = s.get("url") or ""
        is_bad = any(bp in url for bp in BAD_PIECES)
        if not is_bad:
            new_sources.append(s)
            continue
        if new_url:
            s["url"] = new_url
            s["ref"] = "Numista"
            s["type"] = "numista"
            new_sources.append(s)
            replaced += 1
            print(f"  replaced {cid:40s} → {new_url.rsplit('/',1)[-1]}")
        elif needs_drop:
            dropped += 1
            print(f"  dropped  {cid:40s} (no Numista replacement)")
        # else: surprise mismatch — drop silently, user can investigate
    coin["sources"] = new_sources

with open(p, "w") as f:
    yaml.dump(data, f)

print(f"\nReplaced {replaced}  ·  Dropped {dropped}")
