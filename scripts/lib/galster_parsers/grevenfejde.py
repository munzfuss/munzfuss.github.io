"""Parser for Grevens-Fejde-series Galster pages (possessive-H1 shape).

Cache files affected (8 known as of 2026-05-19):
  chr_c2g80, c2g82, c2g84, c2g85, c2g86, c2g87, c2g88, c2g91

Page structure:
  ## Christian 2.s tilhængere [under Grevens Fejde]   ← H1: thematic header
  ## <denomination> [<year>], [<mint>]                ← H2: actual coin data
  [optional further H2 like «Eksemplar fra Zincksamlingen»]
  Forside: ... (Galster N, Schou M, Sieg P)
  • Bruttovægt: ...

The standard parser mis-takes the H1 thematic header as the
denomination line, ending up with `denomination='s tilhængere…'`
(after stripping the `Christian 2.` ruler prefix). This module
instead:

  1. Extracts ruler from H1 («Christian 2.s» → `Christian II`).
  2. Reads denomination + (optional) year + (optional) mint from H2[1]
     — the second `## ` line, NOT the first.
  3. Falls back to body-text year extraction when H2[1] omits the year
     (some entries like c2g82 «2 Mark, Klipping» have year only in the
     description).
  4. Reuses standard.py's description/refs/specs/litteratur/inscription
     helpers for the body below the H2 block — those parts of the page
     follow the canonical layout, only the headline is non-standard.

Output dict shape matches standard.py with ``page_shape: "grevenfejde"``.
"""
from __future__ import annotations

import re
from pathlib import Path

from .common import HR_SENTINEL
from .standard import (
    _parse_description_and_refs,
    _parse_inscription,
    _parse_litteratur,
    _parse_specs,
)

# H1 possessive pattern: «Christian 2.s tilhængere…»
_POSSESSIVE_H1_RE = re.compile(
    r"^(Christian|Frederik|Hans|Margrethe|Erik|Olav|Olaf)\s+(\d+|I+|II|III|IV|VII?)\.s\b",
)

# Coin descriptor pattern for H2[1]: «<denom> [<year>], [<mint>]».
# Examples from the 8 known pages:
#   «1 Skilling 1525, Landskrone»
#   «2 Mark, Klipping»                  (no year — falls back to body)
#   «Halv Sølvgylden 1536, København»
#   «4 Skilling 1535, Güstrow, Mecklenburg»
#   «1 Hvid u.år (S), København»
#   «4 Skilling, København»             (no year — falls back to body)
_MINT_WORD = (
    r"(?:København|Kobenhavn|Malmø|Malmö|Malmo|Husum|Gottorp|Roskilde|"
    r"Aarhus|Ribe|Bergen|Oslo|Visby|Stockholm|Flensborg|Landskrona|"
    r"Landskrone|Helsingør|Lund|Kalundborg|Güstrow|Mecklenburg)"
)


def _extract_h2_headers(text: str) -> list[str]:
    """Return all `## …` header lines in body order, stripped."""
    out: list[str] = []
    for line in text.split("\n"):
        line = line.strip()
        if line.startswith("## "):
            content = line[3:].strip()
            if content:
                out.append(content)
    return out


def _parse_coin_descriptor(h2_line: str) -> dict:
    """Parse H2[1] into {denomination, year_label, mint_from_h2}.

    Handles optional year and mint. Year may be a single year, a comma
    list, a range, or «u.år» (undated).
    """
    out: dict = {}
    line = h2_line.strip()

    # Strip parenthesised rarity flags «(RRR)», «(S)», «(Unik)» etc.
    line_clean = re.sub(r"\s*\((?:Unik|RRR?|R+|S+|U)\)", "", line)

    # Extract year(s) — accept single year «1525», list «1535, 1536»,
    # range «1535-1540», or undated marker «u.år» / «ND».
    year_tokens = re.findall(r"(?<!\d)1[5-6]\d{2}(?:[-–]\d{4})?(?!\d)", line_clean)
    if year_tokens:
        out["year_label"] = ", ".join(year_tokens)
        for yt in year_tokens:
            line_clean = line_clean.replace(yt, "")
    elif re.search(r"u\.\s*[åA]r|\bND\b", line_clean):
        out["year_label"] = "u.år"
        line_clean = re.sub(r"u\.\s*[åA]r|\bND\b", "", line_clean)

    # Try to peel off a trailing mint name. Mint compounds like
    # «Güstrow, Mecklenburg» (mint city + region) get captured whole.
    line_clean = line_clean.strip(", .")
    mint_pattern = re.search(
        rf"[, ]+({_MINT_WORD}(?:\s*,\s*Mecklenburg)?(?:\s+eller\s+{_MINT_WORD})?)\s*$",
        line_clean,
        re.IGNORECASE,
    )
    if mint_pattern:
        out["mint_from_h2"] = mint_pattern.group(1)
        line_clean = line_clean[: mint_pattern.start()].rstrip(", .")

    # Whatever is left is the denomination. Strip a trailing «, Klipping»
    # modifier that the standard parser would call a coin-shape qualifier
    # — keep it joined to the denomination since «2 Mark Klipping» reads
    # as one denomination noun.
    line_clean = re.sub(r"\s+", " ", line_clean).strip(", .")
    if line_clean:
        out["denomination"] = line_clean
    return out


def _body_after_coin_descriptor(text: str) -> str:
    """Return the body text between the coin-descriptor H2[1] and the
    first ``§§HR§§`` boundary (spec / litteratur block start) or the
    next H2 header — whichever comes first. This is the «description
    paragraph» where year + mint live for H2-year-free pages.

    Constraining the search this way prevents bleeding into bibliography
    («Wilcke 1481-1588, København 1950») or sub-section headers
    («## KMMS KP 2085», «## Eksemplar fra Zincksamlingen»).
    """
    h2_positions = [m.start() for m in re.finditer(r"^## ", text, re.MULTILINE)]
    if len(h2_positions) < 2:
        return ""
    # Start: end of H2[1] line
    h2_end_line = text.find("\n", h2_positions[1])
    if h2_end_line < 0:
        return ""
    start = h2_end_line
    # End: first §§HR§§ OR next H2 header, whichever is first
    hr_pos = text.find("§§HR§§", start)
    next_h2 = h2_positions[2] if len(h2_positions) >= 3 else len(text)
    end_candidates = [pos for pos in (hr_pos, next_h2) if pos > 0]
    end = min(end_candidates) if end_candidates else len(text)
    return text[start:end]


def _parse_body_year_fallback(text: str) -> str | None:
    """When H2[1] omits the year, look in the body description for a
    year token. Used for c2g82/c2g91 («2 Mark, Klipping», «4 Skilling,
    København») where the H2 is year-free; also for c2g89/c2g90 which
    carry «U.år» (capital U — undated marker) in the body.

    Returns deduplicated comma-list of distinct year tokens, or «u.år»
    for undated, or None if nothing found.

    Search window is constrained to the description paragraph between
    H2[1] and the first ``§§HR§§`` / next H2 — keeps the search out
    of bibliography titles («Wilcke 1481-1588») that would otherwise
    contribute stray year tokens.
    """
    body = _body_after_coin_descriptor(text)
    if not body:
        return None

    body_clean = re.sub(r"\s*\((?:Unik|RRR?|R+|S+|U)\)", "", body)

    year_tokens = re.findall(r"(?<!\d)1[5-6]\d{2}(?:[-–]\d{4})?(?!\d)", body_clean)
    if year_tokens:
        seen = set()
        deduped = []
        for yt in year_tokens:
            if yt not in seen:
                deduped.append(yt)
                seen.add(yt)
        return ", ".join(deduped)
    if re.search(r"[uU]\.\s*[åA]r|\bND\b", body):
        return "u.år"
    return None


def _parse_body_mint_fallback(text: str) -> str | None:
    """When H2[1] omits the mint, pull it from the description paragraph.
    Pattern: «1534 (Unik), Klipping, Malmø eller København (Galster 82,
    ...)» — mint follows the year/qualifier list, before the catalog-
    ref parens. Same H2[1]→HR window as `_parse_body_year_fallback`.
    """
    body = _body_after_coin_descriptor(text)
    if not body:
        return None
    mint_pattern = re.search(
        rf"({_MINT_WORD}(?:\s+eller\s+{_MINT_WORD})?)(?=\s*[(.])",
        body,
        re.IGNORECASE,
    )
    if mint_pattern:
        return mint_pattern.group(1)
    return None


def parse_page(html_path: Path, text: str) -> dict:
    """Parse a Grevens-Fejde Galster coin page into structured data."""
    h2_headers = _extract_h2_headers(text)
    h1 = h2_headers[0] if h2_headers else ""

    # Ruler from possessive H1
    ruler: str | None = None
    rm = _POSSESSIVE_H1_RE.match(h1)
    if rm:
        ruler_name = rm.group(1)
        ruler_num = rm.group(2)
        if ruler_num.isdigit():
            ruler_num = {"1": "I", "2": "II", "3": "III", "4": "IV", "5": "V"}.get(
                ruler_num, ruler_num
            )
        ruler = f"{ruler_name} {ruler_num}".strip()

    # Coin descriptor from H2[1] (or H2[0] if there's only one — defensive)
    descriptor_h2 = h2_headers[1] if len(h2_headers) >= 2 else (h2_headers[0] if h2_headers else "")
    descriptor = _parse_coin_descriptor(descriptor_h2)

    denomination = descriptor.get("denomination")
    year_label = descriptor.get("year_label") or _parse_body_year_fallback(text)
    mint = descriptor.get("mint_from_h2") or _parse_body_mint_fallback(text)

    # Body parsers — these are shape-invariant
    desc, refs = _parse_description_and_refs(text)
    specs = _parse_specs(text)
    litt = _parse_litteratur(text)
    inscription = _parse_inscription(text)

    # Galster number from filename (chr_c2g80.htm → 80)
    galster_num: str | None = None
    fm = re.search(r"_(c|f)\d+g(\d+\w*)\.htm$", html_path.name)
    if fm:
        galster_num = fm.group(2)
    fm2 = re.search(r"^norge_n(c|f)\d+g(\d+\w*)\.htm$", html_path.name)
    if fm2:
        galster_num = fm2.group(2)

    out: dict = {
        "source_file": html_path.name,
        "source_url_hint": (
            "https://www.danskmoent.dk/" + html_path.name.replace("_", "/")
        ),
        "page_shape": "grevenfejde",
        "ruler": ruler,
        "denomination": denomination,
        "year_label": year_label,
        "mint": mint,
        "description": desc,
        "catalog_refs": refs,
        "specs": specs,
        "inscription": inscription,
        "litteratur": litt,
        "raw_text_excerpt": text[:2000],
    }
    if galster_num:
        out["galster_number"] = galster_num
    if html_path.name.startswith("chr_c2"):
        out["ruler_volume"] = "c2g"
    elif html_path.name.startswith("chr_c3"):
        out["ruler_volume"] = "c3g"
    elif html_path.name.startswith("fr_f1"):
        out["ruler_volume"] = "f1g"
    elif html_path.name.startswith("norge_"):
        m = re.match(r"norge_n(c\d|f\d)g", html_path.name)
        if m:
            out["ruler_volume"] = m.group(1) + "g"
            out["sub_realm"] = "norway"
    return out
