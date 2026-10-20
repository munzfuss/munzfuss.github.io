"""Issuer pages with a coin table (danskmoent.dk/nordby.htm, «Søren Norby»).

The page lists the issuer's coins in one table — Prægested | Galster |
Hauberg | Nominal | Materiale | År — each Galster number linking to its coin
page. Its «År» cell can date a coin its own page leaves undated:
«U. år (1523)» for Galster 145 (gotlg145.htm gives no year). Parsed into
`year_hints` {coin page filename: "1523"}, which the seed builder applies to
an undated coin as an unverified year, citing this page (curator 2026-10-20).
"""
from __future__ import annotations

import re
from html import unescape
from pathlib import Path

_ROW_RE = re.compile(r"<TR[^>]*>(.*?)</TR>", re.IGNORECASE | re.DOTALL)
_CELL_RE = re.compile(r"<TD[^>]*>(.*?)(?=<TD|</TR>|$)", re.IGNORECASE | re.DOTALL)
_HREF_RE = re.compile(r'HREF="([^"]+\.htm)"', re.IGNORECASE)


def _text(cell: str) -> str:
    return re.sub(r"\s+", " ", unescape(re.sub(r"<[^>]+>", " ", cell))).strip()


def parse_year_hints(html: str) -> dict[str, str]:
    hints: dict[str, str] = {}
    for row in _ROW_RE.findall(html):
        cells = _CELL_RE.findall(row)
        if len(cells) < 6:
            continue
        link = _HREF_RE.search(cells[1])
        year = _text(cells[5])
        m = re.fullmatch(r"U\.\s*år\s*\((1[45]\d\d)\)", year, re.IGNORECASE)
        if link and m:
            hints[link.group(1).replace("/", "_", 1)] = m.group(1)
    return hints


def parse_page(html_path: Path, text: str) -> dict:
    html = html_path.read_text(encoding="utf-8", errors="replace")
    return {
        "source_file": html_path.name,
        "source_url_hint": "https://www.danskmoent.dk/" + html_path.name.replace("_", "/", 1),
        "page_shape": "issuer_table",
        "skip": True,
        "skip_reason": "issuer page: dates for coin pages (year_hints), not a coin",
        "year_hints": parse_year_hints(html),
        "raw_text_excerpt": text[:2000],
    }
