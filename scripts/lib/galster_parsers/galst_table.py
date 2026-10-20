"""Reign-index tables (c2galst.htm, f1galst.htm) — the rows WITHOUT a link.

The table lists every Galster number of the reign, one row each:

    Galster | Schou | Sømod | Prægested | Nominal | Materiale | År | Bemærkninger
    37      | 1, 1  | 18    | Malmø     | 1 Nobel | Guld      | 1516, 1518 |
    163     | 17    | 135   | Ukendt sted | Skilling | Sølv  | u.år | Schive XV, 6, side 138

A row whose number is a link has its own coin page. A row WITHOUT one
(c2galst: Galster 163 — found 2026-10-20) is the only record of that coin on
the site, so it becomes one coin record here, read column by column. «Ukendt
sted» (unknown place) leaves the mint empty; a «Schive» remark (Schive's
Norwegian catalogue) marks the Norwegian series.
"""
from __future__ import annotations

import re
from html import unescape
from pathlib import Path

from .common import HR_SENTINEL  # noqa: F401  (shape-module convention)

_VOLUME = {"c2galst.htm": ("c2g", "Christian II"),
           "f1galst.htm": ("f1g", "Frederik I")}
_ROW_RE = re.compile(r"<TR[^>]*>(.*?)</TR>", re.IGNORECASE | re.DOTALL)
_CELL_RE = re.compile(r"<T[DH][^>]*>(.*?)</T[DH]>", re.IGNORECASE | re.DOTALL)


def _cell_text(cell: str) -> str:
    return re.sub(r"\s+", " ", unescape(re.sub(r"<[^>]+>", " ", cell))).strip()


def parse_coins(html: str, filename: str) -> list[dict]:
    volume, ruler = _VOLUME.get(filename, (None, None))
    coins: list[dict] = []
    header: list[str] | None = None
    for row in _ROW_RE.findall(html):
        raw = _CELL_RE.findall(row)
        cells = [_cell_text(c) for c in raw]
        if cells and cells[0] == "Galster":
            header = cells
            continue
        if not header or not cells or not re.fullmatch(r"\d+\s*[A-Z]?", cells[0]):
            continue
        if re.search(r"<A\s+HREF", raw[0], re.IGNORECASE):
            continue                                   # has its own coin page
        col = dict(zip(header, cells))
        remark = col.get("Bemærkninger") or ""
        refs = {"galster": cells[0].replace(" ", "")}
        if col.get("Schou") and col["Schou"] != "-":
            refs["schou"] = col["Schou"]
        m = re.search(r"Schive\s+([IVXL]+)\s*,\s*(\d+(?:-\d+)?)", remark)
        if m:
            refs["schive"] = f"{m.group(1)}.{m.group(2)}"
        place = col.get("Prægested") or ""
        year = col.get("År") or ""
        coins.append({
            "ruler": ruler,
            "ruler_volume": volume,
            "galster_number": refs["galster"],
            "denomination": col.get("Nominal"),
            "year_label": "u.år" if re.match(r"u\.\s*år", year, re.I) else year or None,
            "mint": None if place.lower().startswith("ukendt") else place or None,
            "sub_realm": "norway" if "Schive" in remark else None,
            "description": remark,
            "catalog_refs": refs,
            "specs": {},
        })
    return coins


def parse_page(html_path: Path, text: str) -> dict:
    html = html_path.read_text(encoding="utf-8", errors="replace")
    url = "https://www.danskmoent.dk/" + html_path.name.replace("_", "/", 1)
    coins = parse_coins(html, html_path.name)
    for c in coins:
        c.update({"source_file": html_path.name, "source_url_hint": url,
                  "page_shape": "galst_table"})
    return {
        "source_file": html_path.name,
        "source_url_hint": url,
        "page_shape": "galst_table",
        "coins": coins,
        "raw_text_excerpt": text[:2000],
    }
