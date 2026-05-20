"""Standard Galster coin-page parser.

Handles the canonical coin-page shape: H1 carries ruler + denomination
+ year (+ optionally mint), the body follows with «Forside:» /
«Bagside:» description prose + spec block + Litteratur.

This module is the **bulk of the existing corpus** — ~60 of the 70
pages route here. It is a verbatim move of the original parser logic
from `scripts/parse_galster.py`, with the entry point renamed
``parse_page(html_path, text)`` to match the per-shape dispatcher
contract. The shared HTML→text normalisation
(``_normalise_text`` + ``_HR_SENTINEL``) stays in `parse_galster.py`
and is passed in as the already-normalised ``text`` argument.

No behavioural change vs. the pre-refactor implementation — keeps
the 60-entry corpus stable while the new shapes (grevenfejde, etc.)
get their own dedicated modules.
"""
from __future__ import annotations

import re
from pathlib import Path

from .common import HR_SENTINEL, SPEC_PATTERNS


def _parse_header_h1(text: str) -> dict:
    """The H1 line carries ruler + denomination + year + sometimes mint.

    Returns dict with keys ``ruler``, ``denomination``, ``year_label``,
    optionally ``mint_from_h1`` and always ``h1`` (raw header text).

    Examples handled:
      «Frederik 1., 1 Ungersk gylden 1531»                  — ruler + denom on H1
      «Christian 2., 1 Nobel, Malmø 1516 (RRR), 1518 (RRR)» — ruler + denom + mint + years on H1
      «Christian 3., 2 Mark 1535»                            — ruler + denom + year
      «Frederik 1., 1 Mark 1514, Husum»                      — ruler + denom + year + mint

    When the H1 is a bare-ruler stub («Frederik 1.»), the parser
    falls through to the next non-empty body line that carries the
    denomination + mint + year.

    The optional ``mint_from_h1`` key is set when a mint name follows
    the denomination on the same H1 line. Caller may fall back to
    body-line mint parsing (``_parse_mint_line``, in dispatcher) when
    no denomination text was extracted from the H1.
    """
    out: dict = {}
    # Capture-group extraction strips the `## ` marker so the resulting
    # `h1_lines` contain raw header content. Using a string split that
    # KEEPS the `## ` prefix would break the fallback `h1_marker = f"##
    # {h1}"` lookup below — observed regression on `ernst_f1g50ern`
    # where the H1 lacks a ruler keyword so the fallback fires.
    h1_lines = re.findall(r"##\s*([^\n]+)", text)
    if not h1_lines:
        return out
    # Pick the FIRST H1 that contains a ruler keyword — H2/H3 sections
    # for «Eksemplar fra X-samlingen:» / «KMMS RP NN» also use `## `
    # after normalisation and would otherwise win.
    h1 = None
    for cand in h1_lines:
        if re.match(r"(Christian|Frederik|Hans|Margrethe|Erik|Olav|Olaf)\s+\d", cand):
            h1 = cand.strip()
            break
    if h1 is None:
        h1 = h1_lines[0].strip()
    out["h1"] = h1

    # Year sometimes lives on the line BELOW the H1 (e.g. c2g37: «1516 (RRR), 1518 (RRR). Forside: ...»)
    # Use the FULL `## h1` marker so we don't mis-locate the position
    # via a pre-H1 title that happens to contain the same ruler name
    # («Frederik 1., Galster 47 og 48 \n\n## Frederik 1.\n\n…»).
    h1_marker = f"## {h1}"
    body_idx = text.find(h1_marker)
    if body_idx >= 0:
        start = body_idx + len(h1_marker)
        body_after = text[start:start + 300]
    else:
        body_idx = text.find(h1)
        body_after = text[body_idx + len(h1):body_idx + len(h1) + 300] if body_idx >= 0 else ""

    # Pull ruler from start
    rm = re.match(r"(Christian|Frederik|Hans|Margrethe|Erik|Olav|Olaf)\s+(\d+|I+|II|III|IV|VII?)\.?", h1)
    if rm:
        ruler_name = rm.group(1)
        ruler_num = rm.group(2)
        if ruler_num.isdigit():
            ruler_num = {"1": "I", "2": "II", "3": "III", "4": "IV", "5": "V"}.get(ruler_num, ruler_num)
        out["ruler"] = f"{ruler_name} {ruler_num}".strip()
        rest = h1[rm.end():].lstrip(", .").strip()
    else:
        rest = h1

    # Bare-ruler H1 («Frederik 1.» with no denom): use the first non-
    # empty body line after the H1 as the «extended header». The first
    # «Forside:» / spec-block boundary stops the search so we don't
    # accidentally pull in description prose.
    if not rest:
        for body_line in re.split(r"\n+", body_after.strip()):
            bl = body_line.strip().rstrip(":.").strip()
            if not bl:
                continue
            if re.match(
                r"^(Forside|Bagside|Randskrift|Inskription|Litteratur|"
                r"Bruttov[æe]gt|Finhed|Finv[æe]gt|Eksempl|Diameter|"
                r"Tilbage|Afslag|" + HR_SENTINEL + ")",
                bl, re.IGNORECASE
            ):
                break
            rest = bl
            break

    rest_clean = re.sub(r"\s*\([RU][RRSU]*\)", "", rest)
    rest_clean = re.sub(r"\s+", " ", rest_clean).strip()

    year_tokens = re.findall(r"(?<!\d)1[5-6]\d{2}(?:[-–]\d{4})?(?!\d)", rest_clean)
    if not year_tokens:
        body_clean = re.sub(r"\s*\([RU][RRSU]*\)", "", body_after)
        year_tokens = re.findall(r"(?<!\d)1[5-6]\d{2}(?:[-–]\d{4})?(?!\d)", body_clean[:150])
    if year_tokens:
        out["year_label"] = ", ".join(year_tokens)
        for yt in year_tokens:
            rest_clean = rest_clean.replace(yt, "")
    elif re.search(r"u\.\s*[åA]r|ND", rest_clean):
        out["year_label"] = "u.år"
        rest_clean = re.sub(r"u\.\s*[åA]r|ND", "", rest_clean)

    rest_clean = re.sub(r"\s*,\s*$", "", rest_clean).strip(" ,.")

    _MINT_WORD = (
        r"(?:København|Kobenhavn|Malmø|Malmö|Malmo|Husum|Gottorp|Roskilde|"
        r"Aarhus|Ribe|Bergen|Oslo|Visby|Stockholm|Flensborg|Landskrona|"
        r"Landskrone|Helsingør|Lund)"
    )
    mint_pattern = re.search(
        rf"[, ]+({_MINT_WORD}(?:\s+eller\s+{_MINT_WORD})?)\s*$",
        rest_clean,
        re.IGNORECASE,
    )
    if mint_pattern:
        out["mint_from_h1"] = mint_pattern.group(1)
        rest_clean = rest_clean[: mint_pattern.start()].rstrip(", .")

    rest_clean = re.split(r"\s+-\s+", rest_clean, maxsplit=1)[0].strip(", .")

    out["denomination"] = rest_clean.strip(", .")
    return out


def _parse_mint_line(text: str) -> str | None:
    """The line after H1 typically has the mint."""
    m = re.search(
        r"(København|Kobenhavn|Malmø|Malmö|Malmo|Husum|Gottorp|Roskilde|Aarhus|"
        r"Ribe|Bergen|Oslo|Visby|Stockholm|Flensborg|Landskrona|Landskrone|"
        r"Helsingør|Lund|Kalundborg|Kgs\.\s*Lyngby)\s*(?:eller\s+([A-Za-zÆØÅæøå]+))?",
        text,
    )
    if m:
        primary = m.group(1)
        alt = m.group(2)
        return f"{primary} eller {alt}" if alt else primary
    return None


_CATALOGUE_KEYWORDS = (
    "Galster", "Schou", "Sieg", "Hede", "Sømod", "Schive", "Lange",
    "Friedberg", "Fr.", "Fr",
    "Jensen/Skjoldager", "Jensen Skjoldager", "Jensen og Skjoldager",
    "Delzanno", "Lott", "MB", "NMD", "MNI", "Aagaard",
)
_CATALOGUE_KEYWORD_RE = re.compile(
    r"\b(" + "|".join(re.escape(k) for k in _CATALOGUE_KEYWORDS) + r")\b",
    re.IGNORECASE,
)
# Danish connector words that bleed into the catalogue-ref value when
# the source uses «hhv.» / «henholdsvis» (= «respectively»). The actual
# value follows AFTER the connector. Strip from the captured value
# prefix.
_CATALOGUE_CONNECTOR_RE = re.compile(
    r"^\s*(?:hhv\.?|henholdsvis|resp\.?)\s+",
    re.IGNORECASE,
)


def _parse_description_and_refs(text: str) -> tuple[str | None, dict]:
    """Description block carries «Forside: ... bagside: ... (Galster N, Schou M, ...)».

    Returns (description_text, catalog_refs_dict).

    Multi-ref parsing strategy: locate each catalogue keyword in the
    paren content and capture everything between this keyword and the
    NEXT keyword (or end of paren). This preserves comma-separated
    sub-values within one catalogue ref (e.g. «Schive XVI.2-7,11-13»
    stays whole) AND strips Danish connectors like «hhv.» («Schou
    hhv. 12-15, 1, 1, 4 og 27-29» → schou = «12-15, 1, 1, 4 og 27-29»).
    """
    refs: dict = {}
    desc = None
    m = re.search(r"Forside:\s*(.*?)(?:\n\n|" + HR_SENTINEL + ")", text, re.DOTALL)
    if m:
        desc = m.group(1).strip()
        for pm in re.finditer(r"\(([^)]+)\)", desc):
            content = pm.group(1)
            keyword_matches = list(_CATALOGUE_KEYWORD_RE.finditer(content))
            for i, km in enumerate(keyword_matches):
                kw_start = km.start()
                value_start = km.end()
                # Value runs until the next keyword or end of paren content
                value_end = (
                    keyword_matches[i + 1].start()
                    if i + 1 < len(keyword_matches)
                    else len(content)
                )
                value_raw = content[value_start:value_end]
                # Strip Danish connector prefix («hhv. » etc.) and
                # trailing commas / whitespace
                value_clean = _CATALOGUE_CONNECTOR_RE.sub("", value_raw).strip(" ,;.")
                if not value_clean:
                    continue
                # Normalise keyword → ref-field name
                kw = km.group(1).lower()
                kw_clean = kw.replace("/", "_").replace(" ", "_").replace(".", "")
                if kw_clean == "fr":
                    kw_clean = "friedberg"
                elif kw_clean.startswith("jensen"):
                    kw_clean = "jensen_skjoldager"
                refs[kw_clean] = value_clean
    return desc, refs


def _parse_specs(text: str) -> dict:
    """Pull the spec block (between two <HR> sentinels typically)."""
    specs: dict = {}
    for pat, key in SPEC_PATTERNS:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            val = m.group(1).replace(",", ".").strip()
            try:
                specs[key] = float(val) if key.endswith(("_g", "_mm")) or key == "finhed" else val
            except ValueError:
                specs[key] = m.group(1).strip()
    mm = re.search(r"([\d.]{3,})\s*(?:stk|styk|St\.|Stk\.)\b", text)
    if mm:
        try:
            specs["mintage"] = int(mm.group(1).replace(".", ""))
        except ValueError:
            pass
    return specs


def _parse_litteratur(text: str) -> list[str]:
    """Extract bibliographic citations from the Litteratur block."""
    out: list[str] = []
    m = re.search(r"Litteratur:\s*\n(.*?)(?:" + HR_SENTINEL + r"|Tilbage til|$)", text, re.DOTALL)
    if not m:
        return out
    block = m.group(1)
    for line in re.split(r"\n[•\-]\s*", block):
        line = line.strip().strip("•- ")
        if len(line) > 10 and not line.startswith("Tilbage"):
            out.append(line)
    return out


def _parse_inscription(text: str) -> str | None:
    """Many pages quote the legend inscription + translation."""
    m = re.search(r'"([^"]+)":\s*\n*"([^"]+)"', text)
    if m:
        return f"{m.group(1)} / {m.group(2)}"
    return None


# Sub-section pattern for multi-Galster pages. E.g. `fr_f1g48.htm`
# documents BOTH Galster 47 (1 Sølvgylden, 28.5g) AND Galster 48 (1½
# Sølvgylden, 45.58g) as two sub-sections under one shared H1. The body
# carries:
#   « 1 Sølvgylden (RRR)\nGalster 47, Schou 4, ...\n• Bruttovægt: ca. 28,5g\n\n
#     1 1/2 Sølvgylden (Unik)\nGalster 48, Schou 2, ...\n• Bruttovægt: 45,58g»
# We pick the sub-section whose Galster-number matches the page's
# filename-derived number (parsed downstream).
_SUBSECTION_RE = re.compile(
    r"^\s*([\d/½¼¾⅓⅔⅙⅛\s]+\s*[A-Za-zÆØÅæøåü][^\n(]+?)\s*(?:\([^)]+\))?\s*\n"
    r"Galster\s+(\d+\w*)",
    re.MULTILINE,
)


def _parse_subsections(text: str, galster_num: str | None) -> dict:
    """When the page hosts multiple Galster-number sub-sections, pick
    the one whose number matches the cache filename (`galster_num`).
    Returns {denomination, bruttovaegt_g, finhed, finvaegt_g} extracted
    from that sub-section, or empty dict when no sub-sections detected.
    """
    if not galster_num:
        return {}
    matches = list(_SUBSECTION_RE.finditer(text))
    if len(matches) < 2:
        return {}
    target = None
    for i, m in enumerate(matches):
        if m.group(2).strip().lower() == galster_num.strip().lower():
            start = m.start()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            hr_pos = text.find(HR_SENTINEL, start, end)
            if hr_pos != -1:
                end = hr_pos
            target = (m.group(1).strip(", ."), text[start:end])
            break
    if not target:
        return {}
    denom, body = target
    out: dict = {"denomination": denom}
    for pat, key in SPEC_PATTERNS:
        m = re.search(pat, body, re.IGNORECASE)
        if m:
            val = m.group(1).replace(",", ".").strip()
            try:
                out[key] = float(val) if key.endswith(("_g", "_mm")) else val
            except ValueError:
                out[key] = m.group(1).strip()
    return out


def parse_page(html_path: Path, text: str) -> dict:
    """Parse a standard Galster coin page into structured data."""
    header = _parse_header_h1(text)
    mint = header.get("mint_from_h1") or _parse_mint_line(text)
    desc, refs = _parse_description_and_refs(text)
    specs = _parse_specs(text)
    litt = _parse_litteratur(text)
    inscription = _parse_inscription(text)

    galster_num: str | None = None
    fm = re.search(r"_(c|f)\d+g(\d+\w*)\.htm$", html_path.name)
    if fm:
        galster_num = fm.group(2)
    fm2 = re.search(r"^norge_n(c|f)\d+g(\d+\w*)\.htm$", html_path.name)
    if fm2:
        galster_num = fm2.group(2)

    sub = _parse_subsections(text, galster_num)
    denomination = sub.get("denomination") or header.get("denomination")
    if sub:
        for spec_key in ("bruttovaegt_g", "finhed", "finvaegt_g", "diameter_mm"):
            if spec_key in sub:
                specs[spec_key] = sub[spec_key]

    out: dict = {
        "source_file": html_path.name,
        "source_url_hint": (
            "https://www.danskmoent.dk/" + html_path.name.replace("_", "/")
        ),
        "page_shape": "standard",
        "ruler": header.get("ruler"),
        "denomination": denomination,
        "year_label": header.get("year_label"),
        "mint": mint,
        "description": desc,
        "catalog_refs": refs,
        "specs": specs,
        "inscription": inscription,
        "litteratur": litt,
        "raw_text_excerpt": text[:2000],
    }
    fm = re.search(r"_(c|f)\d+g(\d+\w*)\.htm$", html_path.name)
    if fm:
        out["galster_number"] = fm.group(2)
    fm2 = re.search(r"^norge_n(c|f)\d+g(\d+\w*)\.htm$", html_path.name)
    if fm2:
        out["galster_number"] = fm2.group(2)
        out["sub_realm"] = "norway"
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
