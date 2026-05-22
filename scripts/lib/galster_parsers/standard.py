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
# Danish connector words that may prefix a catalogue-ref value: «hhv.» /
# «henholdsvis» (= «respectively»). Preserved verbatim in the captured
# value when the segments differ — they're semantically meaningful
# (signal that the listed values are positional per-year, not a flat
# list). When the connector pattern is DEGENERATE (all segments after
# splitting on ` og ` resolve to the same token), the «hhv. X og X»
# wrapper is collapsed to bare «X» — keeping it adds verbose noise
# without information gain. User direction 2026-05-22: «"Schou# hhv. 1
# og 1" заміни на "Schou# 1"».
_CATALOGUE_CONNECTOR_RE = re.compile(
    r"^\s*(?:hhv\.?|henholdsvis|resp\.?)\s+",
    re.IGNORECASE,
)


def _collapse_degenerate_hhv(value: str) -> str:
    """Collapse «hhv. X og X» / «X og X» to bare «X» when all segments
    are identical. Returns the original string when segments differ.

    Handles both leading-«hhv.» form (preferred Danish prose) AND the
    bare-«X og X» form (Galster occasionally drops the «hhv.» prefix).

    Examples:
      «hhv. 1 og 1»       → «1»
      «1-4 og 1-4»         → «1-4»
      «hhv. 2 og mangler» → unchanged (segments differ)
      «hhv. 4-5 og 1-9»    → unchanged (segments differ)
      «hhv. 1»              → unchanged (single segment; «hhv.» retained as marker)
    """
    if not isinstance(value, str):
        return value
    s = value.strip()
    # Strip leading «hhv.» / «henholdsvis» / «resp.» for the comparison
    stripped = _CATALOGUE_CONNECTOR_RE.sub("", s, count=1).strip()
    if " og " not in stripped:
        return value  # no list-connector → nothing to collapse
    segments = [seg.strip() for seg in stripped.split(" og ") if seg.strip()]
    if len(segments) >= 2 and len(set(segments)) == 1:
        return segments[0]
    return value


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
                # PRESERVE Danish connector prefix («hhv.» / «henholdsvis»
                # / «resp.») when segments differ — they're semantically
                # meaningful (positional-per-year list). Collapse to a
                # bare value when all segments are identical: «hhv. 1
                # og 1» → «1» (degenerate case, verbose without info
                # gain). User correction 2026-05-22.
                value_clean = value_raw.strip(" ,;.")
                if not value_clean:
                    continue
                value_clean = _collapse_degenerate_hhv(value_clean)
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


# ---------------------------------------------------------------------------
# Variant-table parsers — for pages where ONE Galster number hosts MULTIPLE
# letter-suffixed sub-variants (e.g. Galster 92 → 92A + 92B + base-92 entry
# in chr_c3g92.htm). Distinct from `_parse_subsections` (multi-Galster-number
# pages) — here all sub-variants share the same base number.
#
# Two page shapes detected so far (4 pages total across the cache):
#  - Shape A — explicit row-table with header                  «Galster | Schou | Sieg | Bruttovægt | Finhed | Finvægt | Bemærkninger»
#    Example: chr_c3g92.htm (92 + 92A + 92B), norge_nc2g172.htm
#  - Shape B — bullet+inline-spec («• …(Galster 95A, …).\nBruttovægt: …, Finhed: …, Finvægt: …»)
#    Example: chr_c3g95.htm (95A + 95B)
#
# Both shapes yield a list of {galster_suffix, schou, sieg, bruttovaegt_g,
# finhed, finvaegt_g, note} dicts, returned as `variants: [...]` in the
# parsed-JSON sidecar. The Galster seed builder consumes `variants` and
# emits one seed entry per sub-variant when populated.
#
# Cache encoding caveat: some pages were doubly-encoded somewhere in the
# fetch→parse pipeline so «Bruttovægt» / «Finvægt» came through as
# «Bruttov�gt» / «Finv�gt» (U+FFFD replacement char). The regexes
# use `Bruttov.gt` / `Finv.gt` to match either form.

# Shape A: row-table. The cache normaliser flattens HTML <td> cells to
# « cell-text \n » sequences (leading space, trailing « \n »). The header
# row + each data row appear as a 7-line block, with blank lines between
# rows. We anchor on the header («Galster\nSchou\nSieg\nBrutto…») then
# walk subsequent blank-line-separated 6- or 7-cell blocks until §§HR§§.
_VARIANT_TABLE_HEADER_RE = re.compile(
    r"\bGalster\s*\n\s*Schou\s*\n\s*Sieg\s*\n\s*Bruttov.gt\s*\n"
    r"\s*Finhed\s*\n\s*Finv.gt(?:\s*\n\s*Bem.?rkninger)?",
    re.IGNORECASE,
)

# Shape B: bullet+inline-spec. Two-line block:
#   «• <prose> (Galster {N}{suffix}, Schou {…}, Sieg {…}, …).»
#   «Bruttovægt: <N>g, Finhed: <F>, Finvægt: <N>g.»
_VARIANT_BULLET_RE = re.compile(
    r"•\s+(?P<prose>[^\n]*?)\(\s*Galster\s+(?P<base>\d+)(?P<suffix>[A-Z]?)"
    r"(?:,\s*Schou\s*(?P<schou>[^,\n)]+))?"
    r"(?:,\s*Sieg\s*(?P<sieg>[^,\n)]+))?"
    r"[^\n)]*\)\s*\.?\s*\n+"
    r"\s*Bruttov.gt:\s*(?P<brutto>\d+[,.]\d+)\s*g\s*,"
    r"\s*Finhed:\s*(?P<finhed>\d+[,.]\d+(?:[,.]\d+)?)\s*,"
    r"\s*Finv.gt:\s*(?P<finv>\d+[,.]\d+)\s*g",
    re.MULTILINE,
)


def _to_float(s: str | None) -> float | None:
    if s is None:
        return None
    s = s.replace(",", ".").strip()
    # Some pages write «0,312,5» (a typo for «0,3125»). Collapse the
    # extra separator before parsing.
    if s.count(".") > 1:
        head, *rest = s.split(".")
        s = head + "." + "".join(rest)
    try:
        return float(s)
    except ValueError:
        return None


def _parse_variant_table_shape_a(text: str, base_galster: str | None) -> list[dict]:
    """Shape A — explicit row-table. Returns one dict per data row.

    The base-galster (page's Galster number from filename, e.g. «92» for
    chr_c3g92) is used to construct the per-row full identifier when the
    row's Galster cell carries only a letter suffix («A» / «B») or is
    blank (for the «Kendes ikke mere» orphan row).
    """
    m = _VARIANT_TABLE_HEADER_RE.search(text)
    if not m:
        return []
    body_start = m.end()
    # Body runs until next §§HR§§ sentinel or end-of-text.
    end_marker = text.find(HR_SENTINEL, body_start)
    body = text[body_start:end_marker] if end_marker != -1 else text[body_start:]
    # Split body into row-blocks (separated by blank lines).
    raw_blocks = [b.strip() for b in re.split(r"\n\s*\n", body) if b.strip()]
    variants: list[dict] = []
    for block in raw_blocks:
        cells = [c.strip() for c in block.split("\n")]
        # A valid data row has 6 or 7 cells. Cells beyond 7 indicate
        # spurious wrap-around text (e.g. the next section header bleed-
        # ing in) — accept only 6/7-cell rows.
        if len(cells) < 6 or len(cells) > 7:
            continue
        galster_cell, schou_cell, sieg_cell, brutto_cell, finhed_cell, finv_cell = cells[:6]
        note_cell = cells[6] if len(cells) == 7 else ""
        # Reject obvious header re-occurrences.
        if galster_cell.lower() == "galster":
            continue
        # Build the full galster identifier.
        suffix = galster_cell.strip()
        if suffix == "-":
            galster_full = base_galster or ""
        elif suffix.isalpha() and base_galster:
            galster_full = f"{base_galster}{suffix}"
        else:
            galster_full = suffix or (base_galster or "")
        var = {
            "galster": galster_full or None,
            "schou": None if schou_cell == "-" else (schou_cell or None),
            "sieg": None if sieg_cell == "-" else (sieg_cell or None),
            "bruttovaegt_g": _to_float(brutto_cell.rstrip("g")) if brutto_cell != "-" else None,
            "finhed": _to_float(finhed_cell) if finhed_cell != "-" else None,
            "finvaegt_g": _to_float(finv_cell.rstrip("g")) if finv_cell != "-" else None,
            "note": note_cell or None,
        }
        # Drop entries that carry no measurement signal at all.
        if not any([var["bruttovaegt_g"], var["finhed"], var["finvaegt_g"]]):
            continue
        variants.append(var)
    return variants


def _parse_variant_bullets_shape_b(text: str) -> list[dict]:
    """Shape B — bullet+inline-spec. Returns one dict per matched bullet."""
    variants: list[dict] = []
    for m in _VARIANT_BULLET_RE.finditer(text):
        base = m.group("base")
        suffix = m.group("suffix") or ""
        galster_full = f"{base}{suffix}"
        variants.append({
            "galster": galster_full,
            "schou": (m.group("schou") or "").strip() or None,
            "sieg": (m.group("sieg") or "").strip() or None,
            "bruttovaegt_g": _to_float(m.group("brutto")),
            "finhed": _to_float(m.group("finhed")),
            "finvaegt_g": _to_float(m.group("finv")),
            "note": None,
        })
    return variants


def _parse_variants(text: str, base_galster: str | None) -> list[dict]:
    """Try both shapes; return whichever matches (or empty list)."""
    a = _parse_variant_table_shape_a(text, base_galster)
    if a:
        return a
    b = _parse_variant_bullets_shape_b(text)
    return b


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

    # Sub-variant tables (Shape A row-table / Shape B inline bullets) —
    # one Galster number with letter-suffixed sub-variants 92A/92B/95A/95B
    # etc. When detected, emit a `variants: [...]` list; the seed builder
    # yields one entry per variant downstream.
    variants = _parse_variants(text, galster_num)

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
        "variants": variants,
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
