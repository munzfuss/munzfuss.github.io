"""Printed catalogue pages of the Stack's Bowers Bruun catalogues (Parts I–V).

Citation convention (curator 2026-10-19): a Bruun lot is cited by lot number
and the PRINTED page of the catalogue — «Bruun Part II, lot 13163, p. 94» —
the page a reader finds in any copy, paper or PDF. The text cache
`scripts/cache/bruun/pages/partN.txt` is split at `========== PAGE N ==========`,
where N is the PDF page; the printed number is the running head in the page's
first lines («Page 94 Stack's Bowers Galleries», «Bid Online at
www.StacksBowers.com P age 95» — letter-spaced by pypdf). The offset is constant
within a part (I −24, II −26, III −18, IV −16, V −16), but the head is read per
page and the offset is only a cross-check.

`catalog.bruun_page` and the parser's `page` / `page_span` stay PDF pages: they
are machine locators into the cache, never rendered.
"""
from __future__ import annotations

import re
from functools import lru_cache
from pathlib import Path

PAGES_DIR = Path(__file__).resolve().parents[1] / "cache" / "bruun" / "pages"
ROMAN = {1: "I", 2: "II", 3: "III", 4: "IV", 5: "V"}
PART_OF_ROMAN = {v: k for k, v in ROMAN.items()}
OFFSET = {1: 24, 2: 26, 3: 18, 4: 16, 5: 16}

_MARK = re.compile(r"^========== PAGE (\d+) ==========$")
_HEAD = re.compile(r"P\s?a\s?g\s?e\s+(\d+|[ivxlc]+)\b")
# the same running head anywhere on the page (feature pages print it lower down)
_HEAD_STRICT = re.compile(r"^\s*(?:P\s?a\s?g\s?e\s+(\d+|[ivxlc]+) Stack.s Bowers Galleries"
                          r"|Bid Online at www\.StacksBowers\.com P\s?a\s?g\s?e\s+(\d+|[ivxlc]+))\s*$")


@lru_cache(maxsize=None)
def printed_pages(part: int) -> dict[int, str]:
    """{PDF page: printed page as printed (arabic or roman)} for one part."""
    out: dict[int, str] = {}
    cur, body = None, []
    lines = (PAGES_DIR / f"part{part}.txt").read_text(encoding="utf-8").split("\n")
    for ln in lines + ["========== PAGE 0 =========="]:
        m = _MARK.match(ln)
        if m:
            if cur is not None:
                found = None
                for h in [x for x in body if x.strip()][:3]:
                    hm = _HEAD.search(h)
                    if hm:
                        found = hm.group(1)
                        break
                if found is None:
                    for h in body:
                        hm = _HEAD_STRICT.match(h)
                        if hm:
                            found = hm.group(1) or hm.group(2)
                            break
                if found is not None:
                    out[cur] = found
            cur, body = int(m.group(1)), []
        elif cur is not None:
            body.append(ln)
    return out


def printed_page(part: int, pdf_page: int | None) -> str | None:
    """Printed page for a PDF page; None when the page carries no running head
    (plates, blank pages) — the caller then cites no page, never a computed one."""
    if pdf_page is None:
        return None
    return printed_pages(part).get(int(pdf_page))
