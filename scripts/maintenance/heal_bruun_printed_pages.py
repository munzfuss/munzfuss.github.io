#!/usr/bin/env python3
"""One-time heal: Bruun page citations PDF page → printed catalogue page.

Curator decision 2026-10-19: Bruun (Stack's Bowers, L. E. Bruun Collection
Parts I–V) is cited by lot and PRINTED page. The seed builder and
normalise_bruun_sources.py now emit printed pages (lib.bruun_pages); this
script rewrites the citations already in the data — the canonical source
refs «Bruun Part II, lot 13163, p. 120» and the free-form mentions in notes
and decision reasons («Bruun Part V (lot 14085, p. 51)», «Bruun V lot 14211
p. 94», «Los …, S. …», «лот …, с. …»).

A page is rewritten only when it is a PDF page of THAT lot: the lot number
(plus a «Part N» / «Bruun N» given just before it, when present) selects the
candidate lots in the parser cache, and the page must lie in one candidate's
page_span. Part II and Part V share lot numbers (e.g. 14206), so the span test
is what disambiguates. Anything else is left untouched and listed.

Text-level edit (digits only), so a file's YAML layout is not reflowed.
`catalog.bruun_page` is NOT touched: it stays the PDF page, a machine locator
into scripts/cache/bruun/pages (never rendered).

    .venv/bin/python scripts/maintenance/heal_bruun_printed_pages.py [--apply]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
from lib.bruun_pages import PART_OF_ROMAN, printed_page  # noqa: E402

GLOBS = ["data/v2/**/*.yml", "data/shared/*.yml", "data/i18n/*.yml",
         "data/locations/*.yml", "scripts/maintenance/build_bruun_denmark_seed.py"]

# The removals ledger records the OLD refs on purpose (verify_reflow matches them).
SKIP = {"data/v2/_recorded_removals.yml"}

_MENTION = re.compile(
    r"(?P<lotw>\b(?:lot|Lot|Los|лот))\s+(?P<lot>\d{3,5})(?:/\d{3,5})?"
    r"(?P<mid>[^\d\n]{0,30}?(?:\n[ \t]*)?[^\d\n]{0,12}?)"
    r"(?P<pm>p\.|S\.|с\.|s\.)(?P<sp>[ \t]?|\n[ \t]*)(?P<page>\d{1,3})\b")
_PART = re.compile(r"(?:Part|Bruun)\s+(IV|V|III|II|I)\b")


def _lots() -> dict[int, list[tuple[int, list[int]]]]:
    out: dict[int, list[tuple[int, list[int]]]] = defaultdict(list)
    for part in range(1, 6):
        data = json.loads((ROOT / f"scripts/cache/bruun/lots/part{part}.json").read_text(encoding="utf-8"))
        for lot in data if isinstance(data, list) else data["lots"]:
            if isinstance(lot.get("lot_no"), int):
                span = lot.get("page_span") or ([lot["page"]] if lot.get("page") else [])
                out[lot["lot_no"]].append((part, [int(p) for p in span]))
    return out


def heal_text(text: str, lots, report: list, path: str) -> tuple[str, int]:
    n = 0

    def rep(m: re.Match) -> str:
        nonlocal n
        lot, page = int(m.group("lot")), int(m.group("page"))
        cands = lots.get(lot, [])
        before = text[max(0, m.start() - 40):m.start()]
        pm = [_PART.findall(before)[-1]] if _PART.findall(before) else []
        if pm:
            cands = [c for c in cands if c[0] == PART_OF_ROMAN[pm[0]]]
        hits = [c for c in cands if page in c[1]]
        if len(hits) != 1:
            if cands and not any(str(page) == printed_page(c[0], c[1][0]) for c in cands):
                report.append(f"{path}: unresolved «{m.group(0)!s}» candidates {cands}")
            return m.group(0)
        part = hits[0][0]
        pr = printed_page(part, page)
        if not pr:
            report.append(f"{path}: no running head on Part {part} PDF {page} «{m.group(0)}»")
            return m.group(0)
        n += 1
        return m.group(0)[: m.start("page") - m.start()] + pr
    return _MENTION.sub(rep, text), n


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    lots = _lots()
    report: list[str] = []
    per_file: Counter = Counter()
    for g in GLOBS:
        for f in sorted(ROOT.glob(g)):
            rel = str(f.relative_to(ROOT))
            if rel in SKIP:
                continue
            text = f.read_text(encoding="utf-8")
            new, n = heal_text(text, lots, report, rel)
            if n:
                per_file[rel] = n
                if args.apply:
                    f.write_text(new, encoding="utf-8")
    for rel, n in sorted(per_file.items()):
        print(f"{n:6d}  {rel}")
    print(f"total {sum(per_file.values())} page numbers in {len(per_file)} files"
          f"{'' if args.apply else ' (dry run)'}")
    for r in report:
        print("REPORT", r)
    return 0


if __name__ == "__main__":
    sys.exit(main())
