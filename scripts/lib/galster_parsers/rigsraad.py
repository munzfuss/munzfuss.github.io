"""Rigsrådet page parser (danskmoent.dk/rigsraad.htm).

The Rigsrådet (Council of the Realm) coinage of the three interregna sits on
ONE page, grouped under «Rigsrådet <years>» headers, one bullet per coin:

    Rigsrådet 1448
    • Hvid U.år, Malmø. Henførtes tidligere til 1448, … se nedenfor.
    • Skilling U.år, Malmø. Forside: …, bagside: … (Galster 21)
    Rigsrådet 1481-83
    • Hvid U.år, Malmø. Forside: lebard, bagside: kors på skjold (Galster 22)
    Rigsrådet 1533
    • Toskilling, Malmø (S); Forside …, bagside: … (Galster 81, Schou 1-2, Sieg 1)

A bullet without a «(Galster N…)» paren is a cross-reference, not a coin (the
1448 Hvid bullet points to Galster 22 under 1481-83). Each coin bullet becomes
one record in ``coins``; the seed builder emits one entry per record. The
header years are the page's dating of the group: for a bullet marked «U.år»
they are an attribution, so the record carries ``year_label: "u.år"`` plus
``year_hint`` (the header span), which the builder writes with
``year_verified: false``.
"""
from __future__ import annotations

import re
from pathlib import Path

from .standard import _extract_refs_from_paren_content, _parse_litteratur

_GROUP_RE = re.compile(r"^\s*Rigsrådet\s+(1[4-6]\d\d)(?:\s*[-–]\s*(\d{2,4}))?\s*$")
_COIN_BULLET_RE = re.compile(
    r"^\s*•\s*(?P<head>(?:[^.;]|\.(?=\s*år))+?)\s*(?:\([RSU]+\))?\s*[.;](?!\s*år)\s*(?P<desc>.*?)"
    r"\(\s*(?P<refs>Galster\s+\d+[^)]*)\)\s*$"
)
_HEAD_RE = re.compile(
    r"^(?P<denom>.+?)(?P<undated>\s+U\.\s*år)?\s*,\s*(?P<mint>[A-ZÆØÅ][\wæøå]+)\s*"
    r"(?:\([RSU]+\))?$"
)


def _expand_year(first: str, last: str | None) -> tuple[int, int]:
    y1 = int(first)
    if not last:
        return y1, y1
    if len(last) == 2:
        return y1, int(first[:2] + last)
    return y1, int(last)


def parse_page(html_path: Path, text: str) -> dict:
    coins: list[dict] = []
    group: tuple[int, int] | None = None
    for line in text.split("\n"):
        g = _GROUP_RE.match(line)
        if g:
            group = _expand_year(g.group(1), g.group(2))
            continue
        m = _COIN_BULLET_RE.match(line)
        if not m or group is None:
            continue
        h = _HEAD_RE.match(m.group("head").strip())
        if not h:
            continue
        refs = _extract_refs_from_paren_content(m.group("refs"))
        span = (f"{group[0]}" if group[0] == group[1]
                else f"{group[0]}-{group[1]}")
        undated = bool(h.group("undated"))
        coin = {
            "ruler": "Rigsrådet",
            "denomination": h.group("denom").strip(),
            "year_label": "u.år" if undated else span,
            "mint": h.group("mint"),
            "description": m.group("desc").strip().rstrip(" ,;"),
            "catalog_refs": refs,
            "galster_number": refs.get("galster"),
            "specs": {},
        }
        if undated:
            coin["year_hint"] = span
        coins.append(coin)

    url = "https://www.danskmoent.dk/" + html_path.name.replace("_", "/", 1)
    for c in coins:
        c.update({
            "source_file": html_path.name,
            "source_url_hint": url,
            "page_shape": "rigsraad",
        })
    return {
        "source_file": html_path.name,
        "source_url_hint": url,
        "page_shape": "rigsraad",
        "coins": coins,
        "litteratur": _parse_litteratur(text),
        "raw_text_excerpt": text[:2000],
    }
