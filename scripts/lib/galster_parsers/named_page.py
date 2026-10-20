"""Coin pages whose filename carries no Galster number.

A reign index links some numbers to a page named after the coin, not the
number: f1galst.htm «114» → husumdal.htm, «67» → ronneby.htm; c2galst.htm
«42» → 18pennin.htm. `fetch_galster.discover` records these as
`index_number_links` {path: {"numbers": [...], "volume": "f1g"}}; this parser
reads the page with the standard parser and takes the Galster number and the
ruler volume from that record.

husumdal.htm is an article, not a coin-page layout: its heading is the
coin's name («Husumdaler») and the identity sits in two sentences —
«Den senere Frederik 1. slog 1514-1522 som hertug af Gottorp mønt i Husum»
and «Særlig kendt er en sølvgylden slået i 1522, den såkaldte Husumdaler
(Galster 114, Schou 1)». For a page whose heading names no ruler, ruler,
denomination, year and mint are read from those two sentence shapes.
"""
from __future__ import annotations

import re
from pathlib import Path

from . import standard
from .standard import _extract_refs_from_paren_content

_RULER_IN_TEXT_RE = re.compile(r"\b(Christian|Frederik)\s+(\d)\.")
_STRUCK_IN_RE = re.compile(r"slog\s+[\d\-–]+\s+.*?mønt\s+i\s+([A-ZÆØÅ][\wæøå]+)",
                           re.DOTALL)
_ARTICLE_COIN_RE = re.compile(
    r"\ben\s+(?P<denom>[a-zæøå]+)\s+slået\s+i\s+(?P<year>1[45]\d\d)\b[^()]*"
    r"\((?P<refs>Galster\s+\d+[^)]*)\)")
_ROMAN = {"1": "I", "2": "II", "3": "III"}


def parse_page(html_path: Path, text: str, record: dict) -> dict:
    d = standard.parse_page(html_path, text)
    numbers = record.get("numbers") or []
    if numbers:
        d["galster_number"] = numbers[0]
        refs = d.setdefault("catalog_refs", {})
        refs.setdefault("galster", numbers[0])
    if record.get("volume"):
        d["ruler_volume"] = record["volume"]
    if not d.get("ruler"):
        m = _ARTICLE_COIN_RE.search(text)
        r = _RULER_IN_TEXT_RE.search(text)
        mint = _STRUCK_IN_RE.search(text)
        if m:
            d["denomination"] = m.group("denom").capitalize()
            d["year_label"] = m.group("year")
            d["catalog_refs"] = _extract_refs_from_paren_content(m.group("refs"))
        if r:
            d["ruler"] = f"{r.group(1)} {_ROMAN[r.group(2)]}"
        if mint:
            d["mint"] = mint.group(1)
    denom = d.get("denomination") or ""
    if re.search(r"\bu\.\s*år\b", denom, re.IGNORECASE):
        # «Christian 2., Klipping u.år, Malmø» (18pennin.htm): the heading says
        # undated; a span in the prose below («Under krigene mod Sverige i
        # årene 1518-1522 lod Christian 2. præge klippinge») is the page's
        # dating of the issue — kept as `year_hint`, written unverified.
        if d.get("year_label") and d["year_label"] != "u.år":
            d["year_hint"] = d["year_label"]
        d["year_label"] = "u.år"
        denom = re.sub(r"\s*\bu\.\s*år\b", "", denom, flags=re.IGNORECASE).strip(" ,")
    if denom.lower() == "klipping":
        # The heading names only the shape; the title line names the coin:
        # «Christian 2., Galster 42, 18 Penning».
        title = text.split("\n", 1)[0]
        tail = title.rsplit(",", 1)[-1].strip()
        if re.match(r"\d", tail):
            denom = f"{tail} klipping"
    d["denomination"] = denom
    d["page_shape"] = "named_page"
    return d
