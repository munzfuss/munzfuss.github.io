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

hansgals.htm (Hans, «oversigt efter Galster») is read for EVERY row, linked or
not: its Schou / Sømod columns and its remarks (Schive, Ernst, Hildebrand,
Rasmusson, Hauberg) are cross-references that the coin pages and hans.htm
often leave out — the Swedish Ørtug rows without a page carry only their
Galster number elsewhere. A linked row is flagged `index_has_page`; the seed
builder folds the catalogue of such a row into the coin's own entry and never
emits it as a coin of its own. The «Falske mønter» table (Galster 252, cast
Nobel 1508; 253, cast fantasy Sølvgylden) is skipped: no coin struck for
circulation (CLAUDE.md §9).
"""
from __future__ import annotations

import re
from html import unescape
from pathlib import Path

from .common import HR_SENTINEL  # noqa: F401  (shape-module convention)

_VOLUME = {"c2galst.htm": ("c2g", "Christian II"),
           "f1galst.htm": ("f1g", "Frederik I"),
           "hansgals.htm": ("hg", "Hans")}
# Pages whose linked rows are read too (as catalogue folds, see above).
_ALL_ROWS = {"hansgals.htm"}
_H2_RE = re.compile(r"<H2[^>]*>(.*?)</H2>", re.IGNORECASE | re.DOTALL)
# Remark cross-references, «Name N» with N a number or range. Ernst's page
# references («Ernst s. 77 fig.3») are not catalogue numbers and stay prose.
_REMARK_REF_RE = re.compile(
    r"\b(Hildebrand|Rasmusson\s+bild|Ernst)\s+(\d+(?:\s*-\s*\d+)?)\b")
# Hauberg is left out: the two rows citing it (Galster 141, 142) have their own
# pages, which already give the same Hauberg numbers.
_ROW_RE = re.compile(r"<TR[^>]*>(.*?)</TR>", re.IGNORECASE | re.DOTALL)
_CELL_RE = re.compile(r"<T[DH][^>]*>(.*?)</T[DH]>", re.IGNORECASE | re.DOTALL)


def _cell_text(cell: str) -> str:
    return re.sub(r"\s+", " ", unescape(re.sub(r"<[^>]+>", " ", cell))).strip()


def parse_coins(html: str, filename: str) -> list[dict]:
    volume, ruler = _VOLUME.get(filename, (None, None))
    all_rows = filename in _ALL_ROWS
    coins: list[dict] = []
    header: list[str] | None = None
    # Drop the forgeries table (hansgals.htm «Falske mønter») before reading.
    m_fake = re.search(r"<H2[^>]*>\s*Falske\s+m(?:ø|&oslash;)nter", html, re.IGNORECASE)
    if m_fake:
        html = html[:m_fake.start()]
    for row in _ROW_RE.findall(html):
        raw = _CELL_RE.findall(row)
        cells = [_cell_text(c) for c in raw]
        if cells and cells[0] == "Galster":
            header = cells
            continue
        if not header or not cells or not re.fullmatch(r"\d+\s*[A-Z]?", cells[0]):
            continue
        has_page = bool(re.search(r"<A\s+HREF", raw[0], re.IGNORECASE))
        if has_page and not all_rows:
            continue                                   # has its own coin page
        col = dict(zip(header, cells))
        remark = col.get("Bemærkninger") or ""
        refs = {"galster": cells[0].replace(" ", "")}
        if col.get("Schou") and col["Schou"] != "-":
            refs["schou"] = col["Schou"]
        m = re.search(r"Schive\s+([IVXL]+)\s*,\s*(\d+(?:-\d+)?)", remark)
        if m:
            refs["schive"] = f"{m.group(1)}.{m.group(2)}"
        if all_rows:
            if col.get("Sømod") and col["Sømod"] != "-":
                refs["Sømod"] = col["Sømod"]
            for name, num in _REMARK_REF_RE.findall(remark):
                key = "Rasmusson" if name.startswith("Rasmusson") else name
                # The coin pages write «Rasmusson ill. 17» for the table's
                # «Rasmusson bild 17»; one spelling per reference.
                val = f"ill. {num}" if key == "Rasmusson" else num
                # Bare «Ernst N» here is Ernst 1940 (NNÅ 1940 s. 73-93, the
                # one Ernst study of Hans' Norwegian hvids): hansg155.htm
                # prints «Ernst 1940 3-13» for the row this table gives
                # «Ernst 3-13». Same spelling as the coin pages.
                if key == "Ernst":
                    val = f"1940 {num}"
                refs[key] = re.sub(r"\s*-\s*", "-", val)
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
            **({"index_has_page": True} if has_page else {}),
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
