#!/usr/bin/env python3
"""One-off: dedupe coin.sources entries that point to the same URL.

After cleanup_sources.py promoted `#refN` sources to direct URLs, some coins
ended up with two entries linking to the same page — the original one plus
the promoted one. In the rendered «Джерело» cell this shows up as a doubled
link.

Rule: group sources by URL; within a group keep the entry whose `ref` label
carries more information (longer label, or contains a parenthetical like
«(Bruun-Slg.)»). Ties fall back to the first occurrence. Preserves the
original order of URL groups.

Run once:
    python scripts/dedupe_sources.py
"""
from __future__ import annotations
import pathlib
from ruamel.yaml import YAML

yaml = YAML()
yaml.preserve_quotes = True
yaml.width = 10000
yaml.indent(mapping=2, sequence=4, offset=2)


def score_ref(ref: str) -> int:
    """Higher = more specific label, preferred on collision."""
    if not ref:
        return 0
    s = 0
    if "(" in ref:
        s += 10  # «SB (Bruun-Slg.)» beats «Stacks Bowers»
    s += len(ref)
    return s


def dedupe_sources(sources):
    # Preserve first-seen order of URLs; within each group pick best-scored entry.
    order = []
    buckets: dict[str, list] = {}
    no_url = []
    for s in sources:
        url = s.get("url") or ""
        if not url:
            no_url.append(s)
            continue
        if url not in buckets:
            buckets[url] = []
            order.append(url)
        buckets[url].append(s)

    out = []
    for url in order:
        group = buckets[url]
        best = max(group, key=lambda s: score_ref(s.get("ref") or ""))
        out.append(best)
    out.extend(no_url)
    return out


def main():
    p = pathlib.Path("data/locations/schleswig_holstein.yml")
    data = yaml.load(p.read_text())

    changed = 0
    dropped = 0
    for coin in data.get("coins", []) or []:
        srcs = coin.get("sources") or []
        if not srcs:
            continue
        deduped = dedupe_sources(srcs)
        if len(deduped) != len(srcs):
            dropped += len(srcs) - len(deduped)
            changed += 1
            print(f"  {coin.get('id'):40s} {len(srcs)} → {len(deduped)}")
            coin["sources"] = deduped

    with open(p, "w") as f:
        yaml.dump(data, f)
    print(f"\n{changed} coins touched · {dropped} duplicate source entries removed")


if __name__ == "__main__":
    main()
