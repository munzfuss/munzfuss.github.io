#!/usr/bin/env python3
"""Extract Numista piece-id from each coin's source URL and store as catalog.numista.

Phase 1 of the enrichment plan: no network needed, just URL parsing.
Phase 2 (separate script) fetches each Numista page and parses additional
catalog references (Lange#, Hede#, Sieg#, MB#, Weinm#, etc.).
"""
from __future__ import annotations
import re, pathlib
from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap

YML = pathlib.Path("data/locations/schleswig_holstein.yml")

# Numista URLs come in several formats:
#   https://en.numista.com/catalogue/pieces<NUMERIC_ID>.html
#   https://en.numista.com/catalogue/pieces<NUMERIC_ID>.html?<query>
#   https://en.numista.com/<NUMERIC_ID>                     (short form)
PIECE_RE_LONG = re.compile(r"numista\.com/catalogue/pieces?(\d+)\.html", re.IGNORECASE)
PIECE_RE_SHORT = re.compile(r"numista\.com/(\d+)(?:/|$|\?)", re.IGNORECASE)


def extract_numista_id(url: str | None) -> str | None:
    if not url: return None
    m = PIECE_RE_LONG.search(url) or PIECE_RE_SHORT.search(url)
    return m.group(1) if m else None


def main():
    yaml = YAML()
    yaml.preserve_quotes = True
    yaml.width = 10000
    yaml.indent(mapping=2, sequence=4, offset=2)

    data = yaml.load(YML.read_text())
    coins = data.get("coins") or []

    set_count = 0
    skipped_already = 0
    no_url = 0

    for coin in coins:
        cat = coin.get("catalog")
        if cat is None:
            cat = CommentedMap()
            coin["catalog"] = cat

        # Skip if already set
        if cat.get("numista"):
            skipped_already += 1
            continue

        # Find Numista source URL
        sources = coin.get("sources") or []
        nid = None
        for s in sources:
            url = s.get("url") or ""
            cand = extract_numista_id(url)
            if cand:
                nid = cand
                break

        if not nid:
            no_url += 1
            continue

        cat["numista"] = nid
        set_count += 1

    YML.write_text("")
    with open(YML, "w") as f:
        yaml.dump(data, f)

    print(f"Total coins:         {len(coins)}")
    print(f"  Already had .numista: {skipped_already}")
    print(f"  Newly set:            {set_count}")
    print(f"  No Numista URL found: {no_url}")


if __name__ == "__main__":
    main()
