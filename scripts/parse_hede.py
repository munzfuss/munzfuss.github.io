"""Parse cached Hede HTML pages from danskmoent.dk into structured JSON.

Each ``scripts/cache/hede/<basename>.htm`` is parsed into a sibling
``<basename>.json`` capturing the typed fields useful for our project:

  * Identity — ruler, hede volume code, hede numbers covered, nominal,
    mint, page title.
  * Years + rarity — list of dated specimens with rarity flag
    («R» / «RR» / «RRR» / «S» / «Unik»).
  * Specs — bruttovægt, finhed, finvægt / nettovægt, and the
    «Marken fin udbragt til X speciedalere» quote (the period
    Müntzfuß standard, with parsed numeric value + unit).
  * Description — Forside / bagside / randskrift (obv / rev / edge).
  * Catalog refs cited in the description (Hede, Schou, Sieg).
  * Literatur — bibliography references.
  * Eksemplarer — specimens listed by named collection
    (Zinck-, Poulsen- etc.).
  * Multi-entry pages (e.g. f3h62.htm covers Hede 61 + 62A/B + 63 + 64)
    parse into a per-Hede `specs_by_hede` dict so each entry's spec
    block is recoverable.

Heuristics, not a strict grammar — danskmoent.dk's HTML is loose
and fields evolve across pages. The raw text is kept in the JSON
under `raw_text` as a fallback so consumers needing a field the
parser missed can recover it without re-reading HTML.

Usage::

    python scripts/parse_hede.py [--force]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from html import unescape
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib.paths import HEDE_CACHE as CACHE_DIR  # noqa: E402
from lib.mint_registry import canon_for_alias  # noqa: E402


_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"[ \t]+")
# Sentinel inserted at each <HR> position before tag-stripping so the
# section-break is preserved in the normalised text. danskmoent.dk
# pages use <HR> as the structural delimiter between cross-reference
# spec sections and the page's own primary spec block (cf. f3h68.htm).
_HR_SENTINEL = "§§HR§§"
_HR_RE = re.compile(r"<HR\b[^>]*>", re.IGNORECASE)


def _strip_html(html: str) -> str:
    """Strip HTML tags, decode entities, normalise whitespace.

    Inserts ``§§HR§§`` sentinels at every <HR> position so callers can
    detect section boundaries in the otherwise-flat text.
    """
    text = _HR_RE.sub(f"\n{_HR_SENTINEL}\n", html)
    text = _TAG_RE.sub("\n", text)
    text = unescape(text)
    text = _WS_RE.sub(" ", text)
    text = re.sub(r"\n[ \t]+", "\n", text)
    text = re.sub(r"\n{2,}", "\n", text)
    return text.strip()


# Spec line patterns. Page bodies use Danish field names with `,` as
# decimal separator: «Bruttovægt: 29,232g» / «Finhed: 0,888» /
# «Finvægt: 25,984g» (sometimes «Nettovægt:»). Some pages publish a
# per-year sub-spec («Finhed: 1560: 0,906, 1563: 0,937») — the
# leading `YYYY:` prefix would be greedy-captured as the value
# otherwise, so each spec regex tolerates one optional `YYYY:` token
# between the label and the first capture group.
#
# A small number of pages (~29 cached pages, mostly 17th-c. Frederik
# III / Christian V gold and silver) drop the colon after the label
# («Finhed 0,917», «Bruttovægt 5,990g»). The separator therefore
# matches `[:\s]+` rather than the strict `:\s*` we used before.
_YEAR_PREFIX = r"(?:\s*\d{4}\s*:\s*)?"
# Allow `:`, `;`, or whitespace as the label/value separator —
# a handful of pages use a semicolon (`Finhed; 0,875` on f4h34) or
# drop the separator entirely (`Finhed 0,917` on f3h46).
_SEP = r"[:;\s]+"
_PERIOD_VARIANT_RE = re.compile(
    # Phrases that indicate the FOLLOWING Bruttovægt is a period
    # variant of the preceding one (i.e. the same coin's standard
    # after a weight/fineness reform), NOT a sibling Hede entry.
    # Danish wording from danskmoent.dk pages:
    #   «Ved forordning af [date] nedsat til:»   (reduced by decree)
    #   «Senere nedsat til:»                     (later reduced)
    #   «Udmøntningsformler:» + DD. month YYYY:  (coinage formulae list,
    #                                              date-headed period blocks)
    r"(?:Ved\s+forordning[^:]{0,80}\s+nedsat\s+til|"
    r"Senere\s+nedsat\s+til|"
    r"Udm[øo]ntningsformler|"
    r"\d{1,2}\.\s*(?:januar|februar|marts|april|maj|juni|juli|august|"
    r"september|oktober|november|december)\s+\d{4})\s*[:.]?",
    re.IGNORECASE,
)
_BRUTTO_RE = re.compile(
    # Two label variants accepted:
    #   `Bruttovægt: 29,232g`   — standard form used on most Danish-royal pages
    #   `Vægt: 22,272g`         — shorter form used on (a) Norge sub-catalogue
    #                              pages (56/167 = ~33%) and (b) many older
    #                              Danish pages (97 in the cached corpus,
    #                              mostly Christian IV / V silver and copper)
    # The `\bV` word-boundary alternative prevents matching `Bruttovægt`
    # twice (once via Brutto, once via the V tail) — Brutto matches first
    # because Python regex evaluates alternation left-to-right; the V
    # branch only fires when «Vægt» stands alone (preceded by non-word
    # char, e.g. start-of-line `<LI>` or newline).
    #
    # Gross-vs-fine ambiguity check (2026-05-17 audit): «Vægt» is a
    # SHORTENING of «Bruttovægt», not «Finvægt». Verified by the
    # numismatic invariant `Bruttovægt × Finhed = Finvægt` across
    # **77/77 (100%)** Vægt-only pages where all three specs are
    # published: every page satisfies the invariant with ≤1% deviation
    # (rounding noise). 0 pages have both Bruttovægt AND a separate
    # Vægt (no within-page ambiguity to resolve).
    r"(?:Bruttovægt|\bVægt)" + _SEP + _YEAR_PREFIX + r"([\d,\.]+)\s*g",
    re.IGNORECASE,
)

# Known-typo overrides for danskmoent.dk pages that transcribe Hede ↔
# denomination labels incorrectly (per cross-check against Bruun PDF
# Stack's Bowers 2024-2026 auction citations + Hede 1971 book where
# accessible). The map is keyed by basename; value is a permutation
# applied to `by_hede` after standard extraction — swap the Hede tags
# but keep the spec content.
#
# Example: c5h39 page literally reads:
#   «1 Dukat\nHede 40, Schou 3, Sieg 107\nBruttovægt: 3,490g»
#   «2 Dukat\nHede 39, Schou 2, Sieg 106\nBruttovægt: 6,981g»
# But Bruun lot citations attest the canonical Hede ↔ nominal
# assignment is:
#   Hede 39 = 1 Dukat (KM-A433 per Bruun lot 13186, weight 3.49g)
#   Hede 40 = 2 Dukat (per Bruun lot 17098, weight 6.94g)
# i.e. the danskmoent page swapped the Hede labels.
#
# Each entry: basename → {bad_hede: good_hede, ...}
_KNOWN_HEDE_TYPOS: dict[str, dict[str, str]] = {
    "c5h39": {"39": "40", "40": "39"},
}
_FINHED_RE = re.compile(
    r"Finhed" + _SEP + _YEAR_PREFIX + r"([0-9][,\.][0-9]+|[01](?![.,]\d{4}))",
    re.IGNORECASE,
)
_FINVAEGT_RE = re.compile(
    r"(?:Finvægt|Nettovægt)" + _SEP + _YEAR_PREFIX + r"([\d,\.]+)\s*g",
    re.IGNORECASE,
)
# «Marken fin udbragt til 9,288 speciedalere» / «9,000 daler» /
# «10,793 dlr.» / «Marken rauh udbragt til 9,000 daler» — value + unit on one line.
# Captures basis (fin / rauh) + value + raw unit. Per-Hede line right
# after Finvægt in the spec block.
_MARKEN_FIN_RE = re.compile(
    r"Marken\s+(fin|rauh?)\s+udbragt\s+til\s+([\d,\.]+)\s+([A-Za-zæøåÆØÅ\.]+)",
    re.IGNORECASE,
)

# Unit normalisation: Danish numismatic «daler» nomenclature varies by
# century but ALL the abbreviations / spellings below map to one of
# four canonical denominator-units that match our Müntzfuß catalogue:
#
#   speciedaler   — silver-Mark standard ratio («Marken fin udbragt til
#                   9,25 speciedalere» ≡ 9¼-Speciedaler-Fuß). Hede uses
#                   «daler» as the generic word for the era's prevailing
#                   silver-Mark coin (Christian III / IV / V «daler» all
#                   mean the contemporary speciedaler-class issue).
#   rigsdaler     — Rigsdaler currency unit (RD), distinct accounting
#                   denominator (post-1625 Danish state account unit).
#   rigsbankdaler — Post-1813 Rigsbankdaler reform standard.
#   piastre       — Asiatic / overseas trade coin (rare; 1 case in cache).
_UNIT_CANONICAL: dict[str, str] = {
    "daler":           "speciedaler",
    "dalere":          "speciedaler",
    "dlr":             "speciedaler",
    "speciedaler":     "speciedaler",
    "speciedalere":    "speciedaler",
    "spdl":            "speciedaler",
    "rd":              "rigsdaler",
    "rdl":             "rigsdaler",
    "rdlr":            "rigsdaler",
    "rigsdaler":       "rigsdaler",
    "rigsdalere":      "rigsdaler",
    # Rigsdaler-Kurant — post-1726 Kurantmøntfod accounting unit
    # («rd.kr» = rigsdaler kurant, fictional silver-Mark-based reckoning
    # at 2/3 the value of a speciedaler). The Christian VI / VII era
    # «10,4 rd.kr» = canonical Kurantmøntfod ratio.
    "rd.kr":           "rigsdaler_kurant",
    "rd.kur":          "rigsdaler_kurant",
    "rdk":             "rigsdaler_kurant",
    "rigsdaler_kurant": "rigsdaler_kurant",
    "rigsbankdaler":   "rigsbankdaler",
    "rigsbankdalere":  "rigsbankdaler",
    "rbdlr":           "rigsbankdaler",
    "piastre":         "piastre",
}
_HEDE_TITLE_RE = re.compile(r"\bHede\s*([\dA-Za-z\-,\s]+?)(?:\Z|\.|\n|$)")


def _parse_decimal(s: str) -> float | None:
    """Convert Danish-decimal string to float. «29,232» → 29.232."""
    if not s:
        return None
    s = s.strip().replace(".", "").replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return None


def _ruler_volume(basename: str) -> tuple[str | None, str]:
    """From `c4h115` / `f3h62` / `nc5h42` (Norge) derive (ruler_label, volume_code).

    Norge-prefixed basenames (`n` prefix) get a Norge-tagged volume code
    (`nc5h42` → `nc5h`). This keeps the composite key for the Norge sub-
    catalogue distinct from the Danish one (Danish c5h42 vs Norge nc5h42 are
    physically different Hede entries — same Hede number under separate
    Danish-royal and Norwegian-royal volumes of the same monarch's reign).
    The ruler_label stays the monarch's name (he ruled both kingdoms in
    personal union)."""
    m = re.match(r"^(n?)(c|f)(\d+)h", basename)
    if not m:
        return None, ""
    norge_prefix, letter, num = m.groups()
    label_base = "Christian" if letter == "c" else "Frederik"
    return f"{label_base} {num}.", f"{norge_prefix}{letter}{num}h"


# Year + rarity inside parens: «1620, 1621 (R)» / «1663 (RR)» /
# «1842, 1844, 1845 (S)» / «1662 (Unik)». Captures all year-tokens
# along with the trailing rarity flag if present.
_YEAR_BLOCK_RE = re.compile(
    r"(\d{4}(?:[\s,]+\d{4})*)\s*"
    r"(?:\(\s*(R{1,3}|S|Unik)\s*\))?",
)

# Section headers that mark the END of the year-rarity zone on a Hede
# page. The year-rarity line lives between the H1 echo and the FIRST
# of these markers; anything past one of them belongs to a different
# section (specs, bibliography, specimen list, mintmaster) where
# four-digit tokens are book years, weight/fineness numerics, etc. —
# NOT coin minting years.
_SECTION_BOUNDARY_RE = re.compile(
    # Matches the labels that begin the spec block on a Hede page. The
    # year-rarity zone on the page is everything BETWEEN the H1 echo and
    # the first of these markers. Includes both `Bruttovægt` (the
    # standard label) and `Vægt` (the shorter form used on Norge sub-
    # catalogue pages + many older Danish pages — see `_BRUTTO_RE`).
    r"\b(?:Bruttov[æa]gt|V[æa]gt|Finhed|Finv[æa]gt|Marken\s+fin|"
    r"Litteratur|Eksemplar(?:er)?\s+fra|M[øo]ntmesterm[æa]rke|"
    r"M[øo]ntmester(?:\b|:)|Tilbage\s+til)",
    re.IGNORECASE,
)
# Hede convention for «century-abbreviated» dating: «(15)46» means
# 1546, «(15)63» means 1563, «(16)29» means 1629. Used heavily on
# 16th-c. Christian III / Frederik II pages where the page H1
# encodes the year as «..., (15)46, Flensborg». The plain
# `\d{4}` matcher above misses these, so we pre-expand them to
# full 4-digit form before the year-block matcher runs.
_CENTURY_ABBR_RE = re.compile(r"\(\s*(1[5-9])\s*\)\s*(\d{2})\b")


def _expand_century_abbr(text: str) -> str:
    """Rewrite Hede century-abbreviation «(15)46» → «1546» in place
    so the downstream year-block matcher catches the year."""
    return _CENTURY_ABBR_RE.sub(lambda m: f"{m.group(1)}{m.group(2)}", text)


# Hede year-range notations:
#   «1874-75» (4-digit + 2-digit short)   → «1874, 1875»
#   «1888-89» (4-digit + 2-digit short)   → «1888, 1889»
#   «1903-05» (4-digit + 2-digit short)   → «1903, 1904, 1905»
#   «1771-1786» (4-digit + 4-digit)       → «1771, 1772, …, 1786»
# Without this expansion the year-block matcher only sees the
# 4-digit endpoints («1874» but not «75» / «1771» but not «1786»),
# silently dropping every mint year between them.
_SHORT_RANGE_RE = re.compile(r"\b(\d{4})\s*-\s*(\d{2})\b(?!\d)")
_LONG_RANGE_RE = re.compile(r"\b(\d{4})\s*-\s*(\d{4})\b")
_RANGE_MAX_SPAN = 30  # implausibly long? leave the form alone


def _expand_year_ranges(text: str) -> str:
    """Expand Hede year-range notations into comma-lists so the
    year-block matcher captures every year in the range."""
    def _short(m):
        a = int(m.group(1))
        century = (a // 100) * 100
        b_short = int(m.group(2))
        b = century + b_short
        if b < a:  # «1899-01» → cross-century, wrap forward
            b += 100
        if b - a > _RANGE_MAX_SPAN:
            return m.group(0)
        return ", ".join(str(y) for y in range(a, b + 1))
    text = _SHORT_RANGE_RE.sub(_short, text)
    def _long(m):
        a, b = int(m.group(1)), int(m.group(2))
        if b < a or b - a > _RANGE_MAX_SPAN:
            return m.group(0)
        return ", ".join(str(y) for y in range(a, b + 1))
    text = _LONG_RANGE_RE.sub(_long, text)
    return text


# Year references that are NOT mint years and must be stripped before
# the year-block matcher runs. Danish numismatic prose on Hede pages
# routinely mentions legal-act dates («forordning af 21. marts 1648»,
# «slået efter møntordning 1544») and historical narratives («svenske
# hærs hærgen i Jylland 1643-44», «Trediveårskrigen 1618-48»). Without
# this filter the body-scan path treats every 4-digit year token as a
# mint year, polluting the per-coin year_label.
_NON_MINT_YEAR_PATTERNS = [
    # Legal-act references — «forordning <date> YYYY», «møntordning YYYY»,
    # «patent af YYYY», «reskript YYYY». The capture extends through the
    # year that follows so the year is removed from the scan window.
    re.compile(
        r"\b(?:m[øo]ntordning(?:en)?|m[øo]ntreform(?:en)?|m[øo]ntreskript(?:et)?|"
        r"forordning(?:en)?|patent(?:et)?|plakat(?:en)?|reskript(?:et)?|"
        r"lov(?:en)?|m[øo]ntlov(?:en)?)"
        r"(?:\s+(?:af|fra|under))?"
        r"(?:\s+\d{1,2}\.?\s*\w+)?"   # «21. marts» date head
        r"\s+(\d{4})(?:\s*-\s*\d{2,4})?",
        re.IGNORECASE,
    ),
    # Historical-narrative references — «i 1643-44», «under 1620erne».
    # Targeted to common Danish narrative prepositions to keep the rule
    # conservative; mint-year contexts almost never use these forms.
    re.compile(
        r"\b(?:hærg(?:en|ede)|krig(?:en)?|indtrængen|Syvaarskrig(?:en)?|"
        r"Trediveårskrig(?:en)?|Niårskrig(?:en)?|Skånsk(?:e)?\s+krig)\b"
        r"[^.]{0,80}?\b(\d{4})(?:\s*-\s*\d{2,4})?",
        re.IGNORECASE,
    ),
    # Bibliographic refs — «NNUM 2017», «Numismatisk Rapport 62, 1999».
    # These usually live in Litteratur sections (past the section boundary)
    # but defensive coverage helps when Litteratur is missing.
    re.compile(
        r"\b(?:NNUM|Numismatisk\s+Rapport|Hede\s+1971|Wilcke\s+\d+)\b"
        r"[^.]{0,60}?\b(\d{4})\b",
        re.IGNORECASE,
    ),
]


def _strip_non_mint_year_refs(text: str) -> str:
    """Remove legal-act / historical-narrative year references from a
    scan window so the year-block matcher doesn't pick up their years.

    The patterns target the «keyword … YYYY» shape — for each match we
    blank out the captured year(s) only (replace with a single space),
    preserving the surrounding prose so other extractors that share the
    window (refs, mintmaster) aren't disrupted."""
    def _blank_year(m: re.Match) -> str:
        # Replace just the year span with whitespace
        full = m.group(0)
        year_span = m.span(1)
        # Offset within `full` to compute the year position
        match_start = m.start()
        rel_start = year_span[0] - match_start
        rel_end = year_span[1] - match_start
        return full[:rel_start] + (" " * (rel_end - rel_start)) + full[rel_end:]
    for pat in _NON_MINT_YEAR_PATTERNS:
        text = pat.sub(_blank_year, text)
    return text


def _narrow_to_first_year_sentence(text: str) -> str:
    """Truncate `text` at the period terminating the FIRST sentence that
    contains a 4-digit year. Hede pages place the mint-year-rarity line
    as a single sentence at the top of the body — anything after that
    first period is descriptive prose (Forside/Bagside, mintmaster
    biography, historical context) and its year tokens are not mint
    years.

    The function expands century-abbreviated «(15)46» first so the
    year-detection step sees the same shape as `_extract_years`. It
    does NOT strip non-mint refs here — that's `_extract_years`'s job
    on the narrowed window.

    Returns the unchanged text when no period follows the first year
    (very rare: H1-echo-only pages), so downstream logic still has a
    window to work with."""
    expanded = _expand_century_abbr(text)
    expanded = _expand_year_ranges(expanded)
    # Find the first 4-digit year in the expanded form
    ym = re.search(r"\b\d{4}\b", expanded)
    if not ym:
        return text
    # The "sentence end" is the first « . » that is followed by either
    # a newline OR whitespace + capital letter — i.e. genuine sentence
    # break, not the decimal-like «1.5» (unlikely in year zone) or an
    # abbreviation. We also break on a newline that doesn't itself
    # continue the year list (line followed by non-digit, non-rarity
    # token).
    sentence_end_re = re.compile(r"\.\s+(?=[A-ZÆØÅa-zæøå])|\.\s*\n|\n[A-ZÆØÅ][a-zæøåA-ZÆØÅ]+:|\Z")
    sm = sentence_end_re.search(expanded, ym.end())
    if not sm:
        return text
    return expanded[: sm.end()]


def _extract_years(text: str) -> list[dict]:
    text = _expand_century_abbr(text)
    text = _expand_year_ranges(text)
    text = _strip_non_mint_year_refs(text)
    out: list[dict] = []
    for m in _YEAR_BLOCK_RE.finditer(text):
        years = re.findall(r"\d{4}", m.group(1))
        rarity = (m.group(2) or "").strip() or None
        for y in years:
            out.append({"year": int(y), "rarity": rarity})
    # Dedup preserving first rarity per year
    seen = {}
    for e in out:
        seen.setdefault(e["year"], e)
    return list(seen.values())


# Catalog refs cited inline (Hede 115, Schou 1, Sieg 140 etc.).
# The number capture also accepts:
#   * letter suffix     — «16A», «62AB»
#   * dot sub-number    — «11.1», «11.2» (Sieg's mintmaster sub-class)
#   * comma/dash chain  — «16,17», «250-1»
_REFS_RE = re.compile(
    # `Frederik` REMOVED from this list — it's a ruler name («Frederik 2.»
    # = «Frederik II», a Danish king), not a catalogue. The previous
    # inclusion caused the parser to harvest «Frederik 2» as
    # `catalog_refs.Frederik = "2"` from every Frederik II/III/IV/V/VI/VII
    # page title, which Hede builder then mapped to `fr` (Friedberg
    # catalogue), producing fake `Fr#2` on hundreds of coins. Real
    # Friedberg refs come from Bruun PDFs (`friedberg: NN`) — the
    # danskmoent.dk Hede pages don't generally cite Friedberg.
    #
    # Same caution for `Christian` — it's the other ruling-dynasty name
    # and would create the same false-positive. Not in the regex; added
    # here only as a comment guard against future «look, the parser
    # missed Christian» additions.
    r"\b(Hede|Schou|Sieg|Galster|Bruun|Dav|Davenport|KM|Fr|Friedberg)\.?\s*"
    # Danish per-variant lists write «Schou hhv. 6, 16-29 og 16-22» —
    # «hhv.»/«henholdsvis» = «respectively». Skip that word so the number
    # capture starts at the first die-no; «og» («and») joins further groups
    # (normalised to a comma in _extract_refs). Without this the whole Schou
    # list of such a variant was dropped (81 by_letter variants affected).
    r"(?:hhv\.?\s*|henholdsvis\s*)?"
    # «:» joins year→die in «Schou 1829-37: 2, 1838: 3» / «Hede 13A: 1876» —
    # the leading year is dropped in _extract_refs (see _strip_year_tokens).
    r"([\d]+(?:\.\d+)*(?:[A-Za-z][\w\.]*)?"
    r"(?:(?:[\-/,:]|\s+og)\s*\d+(?:\.\d+)*[A-Za-z]*)*)",
    re.IGNORECASE,
)


def _strip_year_tokens(num: str, catalogue: str) -> str:
    """Drop year / year-range tokens from a captured number list. Danish pages
    write «Schou 1829-37: 2» (year-range : die) and «Schou 1731,1» (Schou
    year,running-no) — the LEADING year is not a catalogue number. A 4-digit
    1500-1950 leading value can only be a year for Schou/Hede/Sieg/KM/Fr/Galster
    (their numbering never reaches the 1500s). Dav is EXEMPT — Davenport numbers
    legitimately sit in the 1200-1700s (Dav 1288, 1725)."""
    if catalogue == "Dav":
        return num
    kept = []
    for t in num.split(","):
        head = t.split("-")[0]
        if head.isdigit() and 1500 <= int(head) <= 1950:
            continue
        kept.append(t)
    return ",".join(kept)


def _extract_refs(text: str) -> dict[str, list[str]]:
    refs: dict[str, list[str]] = {}
    for m in _REFS_RE.finditer(text):
        catalogue = m.group(1).capitalize()
        # Normalise aliases to canonical form
        if catalogue == "Davenport":
            catalogue = "Dav"
        elif catalogue == "Friedberg":
            catalogue = "Fr"
        num = re.sub(r"\bog\b", ",", m.group(2))   # «6, 16-29 og 16-22» → «6,16-29,16-22»
        num = num.replace(":", ",")                 # «1829-37: 2» → «1829-37,2»
        num = re.sub(r"\s+", "", num)
        num = _strip_year_tokens(num, catalogue)    # drop leading year(-range) tokens
        if not num:
            continue
        bucket = refs.setdefault(catalogue, [])
        if num not in bucket:
            bucket.append(num)
    return refs


def _slice_after(text: str, marker: str) -> str | None:
    """Return text after `marker` (case-insensitive) or None."""
    m = re.search(re.escape(marker), text, re.IGNORECASE)
    if not m:
        return None
    return text[m.end():].strip()


def _slice_between(text: str, start_marker: str, end_marker: str) -> str | None:
    """Return text between two markers."""
    s = re.search(re.escape(start_marker), text, re.IGNORECASE)
    if not s:
        return None
    rest = text[s.end():]
    e = re.search(re.escape(end_marker), rest, re.IGNORECASE)
    if e:
        return rest[: e.start()].strip()
    return rest.strip()


def _extract_eksemplarer(text: str) -> dict[str, list[str]]:
    """Pull «Eksemplar(er) fra <Collection>:» blocks.

    Collections seen: Zincksamlingen, Poulsensamlingen,
    Schousamlingen, Bruunsamlingen.
    """
    out: dict[str, list[str]] = {}
    # Find all «Eksemplar(er) fra <name>:» headers and extract the
    # list under each up to the next blank line / next header /
    # «Litteratur:» / end.
    pattern = re.compile(
        r"Eksemplar(?:er)?\s+fra\s+(\w+(?:samlingen|amlingen|samling)?):"
        r"(.*?)(?=Eksemplar(?:er)?\s+fra|Litteratur:|Tilbage til|$)",
        re.IGNORECASE | re.DOTALL,
    )
    for m in pattern.finditer(text):
        name = m.group(1).strip()
        block = m.group(2).strip()
        # Lines that look like specimen entries (contain a year or «Schou»)
        items = []
        for line in block.split("\n"):
            line = line.strip()
            if not line:
                continue
            # Skip Hede sub-headers («Hede 115A:») — they're part of
            # the inner structure but the parsed list doesn't preserve
            # the grouping today. The «Schou N» / year tokens stay.
            if re.match(r"Hede\s+\d", line, re.IGNORECASE):
                continue
            items.append(line)
        if items:
            out[name] = items
    return out


def _extract_litteratur(text: str) -> list[str]:
    body = _slice_after(text, "Litteratur:")
    if not body:
        return []
    # Cut at next section header
    body = re.split(
        r"\n(?:Tilbage til|Eksemplar)",
        body,
        maxsplit=1,
        flags=re.IGNORECASE,
    )[0]
    items = []
    for line in body.split("\n"):
        line = line.strip()
        if not line:
            continue
        items.append(line)
    return items


def _extract_specs(text: str, basename: str = "") -> dict:
    """Parse the spec block. When multiple spec blocks appear (multi-
    entry pages like f3h62 covering Hede 61, 62AB, 63, 64), return
    `by_hede` dict keyed by the Hede sub-tag preceding each block.

    Edge-case 1: pages like f3h68.htm cross-reference sister-types
    (Hede 61, 62AB, 63) AND repeat the page's own primary spec at
    the bottom WITHOUT a preceding Hede tag. The unmarked block is
    attributed to the page's primary Hede number derived from the
    basename (e.g. `f3h68` → primary number `68`), so the index
    correctly resolves the canonical `f3h68` lookup to its own
    spec rather than the cross-reference.

    Edge-case 2 (multi-coin TABLE layout — c4h46, c4h58, c5h39, etc.):
    pages of the «1 og 2 X»-style document multiple denominations
    in a top-of-page description list, then repeat each label with
    its spec block inside a TABLE below. Crude «last Hede tag in
    400-char lookback» picks the WRONG sibling's tag because the
    table-cell spec block has no Hede tag of its own, and the wider
    lookback sees both siblings' tags. Fix: pre-extract a
    «denomination-label → Hede» map from the description-list lines
    (which have the «<label> - Hede X» format), then for each
    table-cell spec block match its immediately preceding denomination
    label against the map.
    """
    bruttos = list(_BRUTTO_RE.finditer(text))
    if not bruttos:
        return {}

    if len(bruttos) == 1:
        return {"default": _spec_from_around(text, bruttos[0].start())}

    # Derive the page's primary Hede number from basename so unmarked
    # spec blocks fall back to it.
    primary = ""
    bm = re.match(r"^n?[cf]\d+h([\dA-Za-z]+)$", basename)
    if bm:
        primary = bm.group(1)

    # Pre-pass: build a «denomination-label → Hede» map from the
    # descriptive section of the page (before the first HR sentinel,
    # or before the first spec block, whichever comes first). Multiple
    # patterns are supported because danskmoent's descriptive lists
    # are heterogeneous:
    #
    #   A. dash-form (c4h46):
    #        «1 Speciedaler 1597\n- Hede 46, Schou 2, Sieg 112»
    #
    #   B. parenthetical-form (c4h58):
    #        «3 Speciedaler\n1624 (R), 1627 (Unik), 1628 (Unik).\n
    #         (Hede 57, Schou hhv. 3-4, 4 og 9, Sieg 125)»
    #
    #   C. inline-form (c5h42):
    #        «2 Dukat 1694, 1696. (Hede 42, Schou hhv. 3-4 og 3, Sieg 69)»
    #
    # Strategy: scan the descriptive section line by line. Track the
    # most recent line that looks like a denomination label (e.g.
    # «1 Dukat», «3 Speciedaler»). When a Hede ref is encountered,
    # associate it with the current denomination. Inline-form is also
    # supported: a line containing both a leading denomination AND a
    # Hede ref is treated as a single (label, Hede) pair.
    label_to_hede: dict[str, str] = {}
    # Reverse mapping for emitting the per-Hede nominal in by_hede output.
    # Distinct from label_to_hede so we can pick the FIRST-seen label (the
    # canonical one from description list) rather than parens-stripped /
    # prefix-only variants.
    hede_to_nominal: dict[str, str] = {}
    # Descriptive section: until first HR sentinel OR first Bruttovægt
    descriptive_end = bruttos[0].start()
    if _HR_SENTINEL in text:
        hr_pos = text.find(_HR_SENTINEL)
        if 0 < hr_pos < descriptive_end:
            descriptive_end = hr_pos
    descriptive = text[:descriptive_end]
    # Denomination label regex: line starts with «N <Denomination>»
    # (N = integer or fraction; Denomination = capitalised word).
    # Optionally trailed by a single 4-digit year (e.g. «1 Speciedaler
    # 1603»). The year is INCLUDED in the captured label when present
    # so table-cell labels that repeat the year can match the
    # descriptive-list labels exactly.
    DENOM_LABEL_RE = re.compile(
        r"^\s*(\d+(?:/\d+)?(?:\s*[½¼¾⅓⅔⅙⅛])?|[½¼¾⅓⅔⅙⅛])"
        r"\s+([A-Za-zæøåöäüßẞ][\w]*(?:\s+[A-Za-zæøåöäüßẞ][\w]*)*?)"
        r"(\s+\d{4}(?:[,–\-]\d{4})?)?"  # optional trailing year(s)
        r"(?=\s*$|\s*[,.;:]|\s*\(|\s*\-\s*Hede)",
        re.MULTILINE,
    )
    HEDE_REF_RE = re.compile(
        r"\bHede\s+(\d+[A-Za-z]*(?:[\-/,]\s*\d+[A-Za-z]*)*)",
    )

    def _normalise_label(s: str) -> str:
        return re.sub(r"\s+", " ", s.lower()).strip()

    current_denom: str | None = None
    for line in descriptive.split("\n"):
        line_s = line.strip()
        if not line_s:
            continue
        # Try denomination label at start of line
        m = DENOM_LABEL_RE.match(line_s)
        if m:
            denom_label = (m.group(1) + " " + m.group(2) + (m.group(3) or "")).strip()
            current_denom = _normalise_label(denom_label)
        # Find Hede ref anywhere in this line
        hm = HEDE_REF_RE.search(line_s)
        if hm and current_denom:
            hede_key = hm.group(1).replace(" ", "")
            label_to_hede.setdefault(current_denom, hede_key)
            hede_to_nominal.setdefault(hede_key, current_denom)

    # Also support legacy «label\n- Hede X» pattern explicitly to handle
    # cases where the label is on a previous line and the Hede ref line
    # starts with «-» (avoiding the DENOM_LABEL_RE/inline-only path).
    for desc_m in re.finditer(
        r"(?<=\n)([^\n]+?)\s*\n\s*-\s*Hede\s+(\d+[A-Za-z]*(?:[\-/,]\s*\d+[A-Za-z]*)*)",
        descriptive,
    ):
        norm = _normalise_label(desc_m.group(1))
        hede_key = desc_m.group(2).replace(" ", "")
        label_to_hede.setdefault(norm, hede_key)
        hede_to_nominal.setdefault(hede_key, norm)

    # Store a parens-stripped «base prefix» for each mapping to help
    # match table-cell labels with slightly different parenthetical
    # year qualifiers (e.g. «2 Speciedaler 1597 (R), 1600 (RR)» in
    # description vs «2 Speciedaler 1597, 1600» in table).
    for orig in list(label_to_hede.keys()):
        base = re.sub(r"\s*\([^)]+\)", "", orig).strip()
        if base != orig:
            label_to_hede.setdefault(base, label_to_hede[orig])

    def _label_to_hede(label_text: str) -> str | None:
        """Best-effort match of a table-cell label against the
        description-list mapping. Tries exact match, then base-prefix
        match, then leading-N-words match."""
        norm = re.sub(r"\s+", " ", label_text.lower()).strip()
        if norm in label_to_hede:
            return label_to_hede[norm]
        # Try base (parens stripped)
        base = re.sub(r"\s*\([^)]+\)", "", norm).strip()
        if base in label_to_hede:
            return label_to_hede[base]
        # Try sub-prefix match (label_to_hede key starts with the
        # table-cell label or vice versa). Useful when years differ
        # slightly between description list and table cell, or when
        # the description list omits the year present in the table.
        # Match by leading-token shared prefix; require the prefix to
        # uniquely identify one Hede in the map.
        for k, v in label_to_hede.items():
            k_tokens = k.split()
            n_tokens = norm.split()
            common = 0
            for a, b in zip(k_tokens, n_tokens):
                if a == b: common += 1
                else: break
            # ≥2 tokens match (multiplier + denomination, e.g. «1 speciedaler»)
            # is enough as long as the prefix uniquely picks ONE Hede number.
            if common >= 2:
                prefix = " ".join(n_tokens[:common])
                matches = {vv for kk, vv in label_to_hede.items()
                           if " ".join(kk.split()[:common]) == prefix}
                if len(matches) == 1:
                    return v
        return None

    # Direct «Hede [Norge] N» header line detector — matches pages like
    # nf3h39 / nc5h13 where each spec block is immediately preceded by
    # a Hede header (bare on its own line OR appended after the
    # denomination label with a comma). Without this the label_window
    # scan finds the Hede header as the immediate parent, doesn't map
    # it against the denomination → Hede dict (it isn't a denomination
    # label), and falls back to the 400-char heuristic which picks the
    # WRONG (later or earlier) Hede tag on multi-coin pages.
    # Two forms:
    #   A. «Hede [Norge] N» as the entire line (nf3h39 layout)
    #   B. «<denom>, Hede [Norge] N» single-line form (nc5h13 layout)
    DIRECT_HEDE_HEADER_RE = re.compile(
        r"^\s*Hede(?:\s+Norge)?\s+(\d+[A-Za-z]*(?:[\-/,]\s*\d+[A-Za-z]*)*)\s*$",
        re.IGNORECASE,
    )
    INLINE_HEDE_HEADER_RE = re.compile(
        r"\bHede(?:\s+Norge)?\s+(\d+[A-Za-z]*(?:[\-/,]\s*\d+[A-Za-z]*)*)\s*$",
        re.IGNORECASE,
    )

    by_hede: dict[str, dict] = {}
    for m in bruttos:
        pos = m.start()
        spec = _spec_from_around(text, pos)
        tag = None

        # Edge-case 2: look back ~150 chars for an immediate denomination
        # label (the line right before the Bruttovægt). Match against the
        # pre-built description-list map.
        label_window_start = max(0, pos - 150)
        label_window = text[label_window_start: pos]
        # Look at the last non-empty line before the Bruttovægt
        lines = [l.strip() for l in label_window.split("\n") if l.strip()]
        for candidate in reversed(lines):
            # Skip lines that look like spec fields, parenthetical comments,
            # or HR sentinels
            if (candidate.startswith("Bruttovægt") or candidate.startswith("Finhed")
                or candidate.startswith("Finvægt") or candidate.startswith("Marken")
                or candidate.startswith(_HR_SENTINEL) or candidate.startswith("-")):
                continue
            # Pre-check: is this a bare «Hede [Norge] N» header line?
            # If yes, extract the Hede number directly — the page is
            # using the multi-Hede header-per-block layout.
            direct_hede = DIRECT_HEDE_HEADER_RE.match(candidate)
            if direct_hede:
                tag = direct_hede.group(1).replace(" ", "")
                break
            # Pre-check: is this a «<denom>, Hede [Norge] N» single-line
            # form? Look for the Hede header at the END of the line
            # — common on nc5h13-style pages.
            inline_hede = INLINE_HEDE_HEADER_RE.search(candidate)
            if inline_hede:
                tag = inline_hede.group(1).replace(" ", "")
                break
            matched = _label_to_hede(candidate)
            if matched:
                tag = matched
                break
            # If candidate isn't in label map, try only the FIRST
            # candidate (immediate parent line) — don't keep climbing
            break

        # Edge-case 1 fallback: original «look-back for Hede tag» heuristic.
        # Apply only if denomination-label lookup didn't resolve.
        if not tag:
            window_start = max(0, pos - 400)
            window = text[window_start: pos]
            last_hr = window.rfind(_HR_SENTINEL)
            if last_hr >= 0:
                window = window[last_hr + len(_HR_SENTINEL):]
            tag_m = re.findall(
                r"\bHede\s+(\d+[A-Za-z]*(?:[\-/,]\s*\d+[A-Za-z]*)*)", window)
            tag = tag_m[-1] if tag_m else None

        # Extract per-Hede catalog refs from the immediate label window —
        # multi-coin pages (f4h25 covering Hede 23/24/25, etc.) have a
        # «<denom><BR>Hede N, Schou X, Sieg Y» label line right before
        # each Bruttovægt spec block. Without this, the seed builder
        # falls back to page-level aggregated `catalog_refs` and applies
        # them indiscriminately to every sub-Hede entry — observed bug
        # on 68 multi-Hede pages.
        per_hede_refs = _extract_per_hede_refs(label_window, tag) if tag else None

        if tag:
            key = tag.replace(" ", "")
            # Attach the descriptive-list nominal to the spec when known.
            # Lets downstream consumers (seed builder) use the per-Hede
            # nominal directly instead of guessing via weight-sorted
            # multi-nominal splits.
            if key in hede_to_nominal:
                spec = {**spec, "nominal": hede_to_nominal[key]}
            if per_hede_refs:
                spec = {**spec, "catalog_refs": per_hede_refs}
            by_hede[key] = spec
        elif primary and primary not in by_hede:
            if primary in hede_to_nominal:
                spec = {**spec, "nominal": hede_to_nominal[primary]}
            by_hede[primary] = spec
        else:
            # No Hede attribution AND primary already covered. Most
            # often this is a period-variant continuation of the
            # preceding spec block — e.g. «Ved forordning af 5. april
            # 1618 nedsat til: Bruttovægt: 2,206g» on c4h100. The
            # original implementation stored these under «unknown_N»
            # keys, which polluted downstream consumers with phantom
            # Hede entries. Detect period-variant trigger phrases
            # between the previous Bruttovægt and this one; if found,
            # skip this spec (consumer keeps the first one). Otherwise
            # fall back to «unknown_N» so the data isn't silently lost.
            window_start = max(0, pos - 400)
            preamble = text[window_start: pos]
            if _PERIOD_VARIANT_RE.search(preamble):
                continue
            by_hede.setdefault(f"unknown_{pos}", spec)
    # Apply known-typo Hede label permutation for documented danskmoent
    # transcription errors (see _KNOWN_HEDE_TYPOS docstring above).
    typo_map = _KNOWN_HEDE_TYPOS.get(basename)
    if typo_map:
        corrected: dict[str, dict] = {}
        for old_key, spec in by_hede.items():
            new_key = typo_map.get(old_key, old_key)
            # When swapping, also re-attach the correct nominal label from
            # hede_to_nominal for the NEW key (the page's nominal label
            # belonged to the WRONG Hede; after correction the same
            # nominal still applies but to the corrected Hede number).
            if new_key != old_key:
                # Swap nominal too: spec's old «nominal» field reflected
                # the page label which was on the WRONG Hede; the
                # corrected coin should carry the correct nominal that
                # the canonical Bruun citation attests for new_key.
                # We re-source the nominal from hede_to_nominal[new_key]
                # via the OTHER pre-existing entry's nominal (since both
                # entries got swapped, the nominals also swap).
                pass  # nominal stays attached to spec; after full swap
                      # of by_hede dict, each spec is now associated
                      # with the corrected Hede number — and its
                      # original nominal label (from page) was correct
                      # FOR THAT SPEC (= same physical coin), so the
                      # mapping is now coherent.
            corrected[new_key] = spec
        by_hede = corrected

    # Page-shape override for the f3h68 hybrid pattern. This is the
    # only page in the cache where the descriptive section enumerates
    # 4 page-own sub-types (Hede 68A, 68B, 69, 70 — 1/2/3 Speciedaler
    # 1665-1667) while the spec TABLE re-uses cross-reference labels
    # (Hede 61 = 1 Spd, 62AB = 2 Spd, 63 = 63 — sibling types from
    # the canonical f3h62 page at the SAME 9¼-Speciedaler standard).
    # The bottom block (after second <HR>) duplicates the 1-Speciedaler
    # spec without a label, so basename fallback captures it as «68» —
    # a Hede number that doesn't exist as a coin type.
    #
    # Standard extraction therefore produces by_hede = {61, 62AB, 63,
    # 68} — all four keys are bogus relative to what the page actually
    # documents. The override discards them and rebuilds by_hede with
    # the 4 page-own sub-types, mapping each to the spec for its
    # denomination (Hede 68A and 68B both share the 1-Speciedaler
    # spec; 69 takes the 2-Spd spec; 70 takes the 3-Spd spec).
    if basename == "f3h68" and set(by_hede.keys()) >= {"61", "62AB", "63"}:
        spec_1spd = by_hede.get("61") or by_hede.get("68")
        spec_2spd = by_hede.get("62AB")
        spec_3spd = by_hede.get("63")
        if spec_1spd and spec_2spd and spec_3spd:
            def _with_nominal(spec: dict, nom: str) -> dict:
                out = {k: v for k, v in spec.items() if k != "nominal"}
                out["nominal"] = nom
                return out
            by_hede = {
                "68A": _with_nominal(spec_1spd, "1 speciedaler"),
                "68B": _with_nominal(spec_1spd, "1 speciedaler"),
                "69":  _with_nominal(spec_2spd, "2 speciedaler"),
                "70":  _with_nominal(spec_3spd, "3 speciedaler"),
            }

    # Period-variant consolidation may leave by_hede with exactly one
    # entry (e.g. c4h107 has 2 Bruttovægt blocks for pre-/post-reform
    # but only Hede 107 — second skipped). Downstream consumers (seed
    # builder) treat single-entry by_hede as a multi-Hede page and try
    # to split the page nominal across N entries, failing on single
    # denominations like «1/2 Krone». Emit as `default` instead so the
    # data shape matches the page's reality (one coin, one spec).
    if len(by_hede) == 1:
        only_spec = next(iter(by_hede.values()))
        return {"default": only_spec}
    return {"by_hede": by_hede}


def _extract_per_hede_refs(label_window: str, hede_tag: str) -> dict:
    """Extract catalog refs (Schou / Sieg / Fr) for ONE Hede number
    from its immediate label line.

    Multi-coin pages (e.g. f4h25.htm covering Hede 23+24+25) have a
    label line of the shape «<denom> Hede N, Schou X, Sieg Y, Fr Z»
    right before each Bruttovægt spec block. The flat
    `parsed["catalog_refs"]` AGGREGATES refs across every sub-Hede
    on the page — applying them indiscriminately to all sub-entries
    is the seed-builder bug observed on 68 multi-Hede pages (2026-05-19
    f4h25 audit). This helper extracts refs for ONE Hede tag from its
    own label line, scoped to the segment starting at «Hede N» and
    ending at the next «Hede M» reference (or end of window).

    Returns a dict in the same shape as `parsed["catalog_refs"]`:
    `{"Schou": [...], "Sieg": [...], "Fr": [...]}`, or empty dict
    when no per-Hede refs are visible in the window.
    """
    if not label_window or not hede_tag:
        return {}
    # Find «Hede {tag}» anchor in the window — tolerate whitespace
    # variations + match the SPECIFIC tag (not a sibling).
    pattern = rf"\bHede\s+{re.escape(hede_tag)}\b"
    m = re.search(pattern, label_window)
    if not m:
        return {}
    # Segment: from this Hede anchor to the next Hede anchor (or end).
    seg_start = m.end()
    next_hede = re.search(r"\bHede\s+\d", label_window[seg_start:])
    if next_hede:
        segment = label_window[seg_start: seg_start + next_hede.start()]
    else:
        segment = label_window[seg_start:]
    # Bound to label end — stop at Bruttovægt / Finhed / spec-block
    # markers so the segment doesn't bleed into the spec block proper.
    for stop_marker in ("Bruttov", "Finhed", "Finv", _HR_SENTINEL):
        idx = segment.find(stop_marker)
        if idx >= 0:
            segment = segment[:idx]

    refs: dict = {}
    # Schou — possibly multiple comma-separated values («Schou 13-15»
    # or «Schou 2-3» or «Schou 1 og 6»).
    schou_matches = re.findall(
        r"\bSchou\s+([\d]+[A-Za-z]?(?:[\-/]\d+[A-Za-z]?)*(?:\s+og\s+\d+[A-Za-z]?)*)",
        segment,
    )
    if schou_matches:
        # Flatten «1 og 6» → ['1', '6']? Keep as single string for now
        # (consistent with parser's flat catalog_refs shape).
        refs["Schou"] = [s.strip() for s in schou_matches]
    # Sieg — single ref typically «Sieg 30» or «Sieg 31.1»
    sieg_match = re.search(
        r"\bSieg\s+(\d+(?:\.\d+)?[A-Za-z]?)", segment
    )
    if sieg_match:
        refs["Sieg"] = [sieg_match.group(1).strip()]
    # Fr (Friedberg) — gold-coin catalog, occasionally per-Hede on the
    # ducat / krone pages.
    fr_match = re.search(r"\bFr\.?\s+(\d+[A-Za-z]?)", segment)
    if fr_match:
        refs["Fr"] = [fr_match.group(1).strip()]
    return refs


def _spec_from_around(text: str, brutto_pos: int) -> dict:
    """Extract a single spec block starting at the given Bruttovægt
    position. Looks ahead up to ~400 chars OR until the next HR
    sentinel — whichever comes first — to avoid bleeding fields from
    a downstream cross-reference block into this one."""
    window = text[brutto_pos: brutto_pos + 400]
    next_hr = window.find(_HR_SENTINEL)
    if next_hr >= 0:
        window = window[:next_hr]
    spec: dict = {}
    if (m := _BRUTTO_RE.search(window)):
        v = _parse_decimal(m.group(1))
        if v is not None:
            spec["bruttovægt_g"] = v
    if (m := _FINHED_RE.search(window)):
        v = _parse_decimal(m.group(1))
        if v is not None:
            spec["finhed"] = v
    if (m := _FINVAEGT_RE.search(window)):
        v = _parse_decimal(m.group(1))
        if v is not None:
            spec["finvægt_g"] = v
    if (m := _MARKEN_FIN_RE.search(window)):
        # groups: 1 = basis (fin/rauh), 2 = decimal value, 3 = unit-raw
        basis_raw = m.group(1).lower()
        v = _parse_decimal(m.group(2))
        unit_raw = m.group(3).strip().rstrip(".").lower()
        if v is not None:
            basis = "rauh" if basis_raw.startswith("rau") else "fin"
            unit_canonical = _UNIT_CANONICAL.get(unit_raw, unit_raw)
            spec["marken_fin_udbragt_til"] = {
                "value": v,
                "unit": unit_canonical,
                "unit_raw": unit_raw,
                "basis": basis,
            }
    return spec


# Header patterns. Page format conventions seen:
#   <H1>Christian 5.<BR>1 Speciedaler 1683, Glückstadt</H1>
#   <H1>Christian 4. - oversigt efter Hede</H1>  (overview, skipped)
#   <H1>Christian 4., 4 Skilling, København</H1>
# We extract `ruler / nominal / mint / years` from the H1 content.
_H1_RE = re.compile(r"<H1[^>]*>(.*?)</H1>", re.IGNORECASE | re.DOTALL)
_TITLE_TAG_RE = re.compile(r"<TITLE>(.*?)</TITLE>", re.IGNORECASE | re.DOTALL)

# A segment is denomination-shaped when it starts with a digit/fraction
# («1 speciedaler», «½ Krone», «32 Skilling») OR opens with a bare denomination
# noun («Blaffert u. år», «Dukat», «Breddaler»). Used to tell a lone «Ruler,
# NOMINAL» H1 line (mint on the variant lines) from «Ruler, …, Mint».
_DENOM_SHAPE_RE = re.compile(
    r"^\s*(?:[\d½⅓¼⅔¾⅛⅜⅝⅞]"
    r"|(?:blaffert|dukat|ducat|breddaler|piaster|s[øö]sling|hvid|penning|mark|"
    r"skilling|krone|kroner|daler|speciedaler|rigsdaler|rigsbankdaler|gylden|"
    r"guldkrone|guldm[øö]nt|solidi|sechsling|dreiling|witten|øre|"
    r"frederik d'?or|christian d'?or)\b)",
    re.IGNORECASE,
)


def _is_denomination(s: str) -> bool:
    """True when the segment looks like a coin denomination, not a mint."""
    return bool(_DENOM_SHAPE_RE.match(s or ""))


# Mint recovery for «Ruler, NOMINAL» pages (the H1 carries no mint — it lives on
# the per-variant A)/B)/C) lines). Verbatim (NOT registry-display): the seed
# builder's _normalize_mints keys on the Danish source spelling «København».
_MINT_CAND_RE = re.compile(r"[A-ZÆØÅ][A-Za-zæøåäöü]+")


def _first_mint_in(segment: str) -> str | None:
    """First recognised mint name (verbatim) in a text segment, else None."""
    for cand in _MINT_CAND_RE.findall(segment or ""):
        if canon_for_alias(cand) is not None:
            return cand
    return None


def _mints_from_variant_lines(text: str) -> list[str]:
    """All distinct mints (verbatim, deduped by canonical, first-seen order)
    across the A)/B)/C) variant lines — for a single-coin page struck at
    several mints (e.g. c7h35: A) København, B) Altona → one coin, both)."""
    found: list[str] = []
    seen: set[str] = set()
    for m in re.finditer(r"(?m)^\s*[A-ZÆØÅ]\)\s*(.*)$", text):
        for cand in _MINT_CAND_RE.findall(m.group(1)):
            canon = canon_for_alias(cand)
            if canon and canon not in seen:
                seen.add(canon)
                found.append(cand)
    return found


def _mint_per_letter_block(text: str) -> dict[str, str]:
    """{letter: verbatim mint} from each letter-group block that names a mint.
    Reuses the same block matcher as _extract_letter_groups so a letter's mint
    aligns with its years/refs (78A København, 78B Helsingør)."""
    out: dict[str, str] = {}
    for m in _LETTER_GROUP_BLOCK_RE.finditer(text):
        mint = _first_mint_in(m.group(2))
        if mint:
            out[m.group(1)] = mint
    return out


def _parse_header(html: str) -> dict:
    out: dict = {}
    title_m = _TITLE_TAG_RE.search(html)
    if title_m:
        out["page_title"] = _strip_html(title_m.group(1)).strip()
    h1_m = _H1_RE.search(html)
    if not h1_m:
        return out
    h1 = _strip_html(h1_m.group(1))
    # Expand Hede century-abbreviation «(15)46» → «1546» AND year-range
    # notations «1874-75» / «1771-1786» before the year-block matcher
    # and the nominal-vs-year/mint splitter run. The H1's yr_match
    # regex (line ~416 below) only accepts 4-digit on both sides of a
    # dash, so without the expansion «1874-75» is captured as just
    # «1874» — silently dropping every short-form 2-digit suffix.
    h1 = _expand_century_abbr(h1)
    h1 = _expand_year_ranges(h1)
    out["h1"] = h1
    # H1 typically has 2 lines: «Ruler.\nNominal Year, Mint»
    parts = [p.strip() for p in h1.split("\n") if p.strip()]
    if not parts:
        return out
    # Ruler line: ends with '.', e.g. «Christian 5.»
    ruler_line = parts[0].rstrip(",").rstrip(".")
    # Sometimes «Ruler., Nominal, Mint» on one line
    if "," in parts[0]:
        segs = [s.strip() for s in parts[0].split(",")]
        out["ruler"] = segs[0].rstrip(".") + "."
        if len(segs) > 1:
            # Look for year tokens in remaining segs
            rest_text = ", ".join(segs[1:])
            yr_match = re.search(r"\d{4}(?:[\-,\s]+\d{4})*", rest_text)
            if yr_match:
                out["years"] = _extract_years(yr_match.group(0))
                rest_text_no_yr = (
                    rest_text[: yr_match.start()] + rest_text[yr_match.end():]
                )
            else:
                rest_text_no_yr = rest_text
            # Last comma-separated piece is usually the mint; the
            # remaining pieces form the (possibly multi-denomination)
            # nominal. E.g. «1, 2, 3 og 4 speciedaler, København» splits
            # into ['1','2','3 og 4 speciedaler','København'] → nominal
            # «1, 2, 3 og 4 speciedaler», mint «København».
            rs = [s.strip() for s in rest_text_no_yr.split(",") if s.strip()]
            if rs:
                # «Ruler, NOMINAL» layout: a LONE denomination-shaped segment
                # after the ruler-comma is the NOMINAL, not the mint — the mint
                # lives on the per-variant A)/B)/C) lines, not on the H1 ruler
                # line. Without this guard the parser field-swaps the nominal
                # into the mint slot (c4h53 «1 speciedaler», c4h78 «4 Skilling»,
                # f7h4 «1 Speciedaler» …). Restricted to len==1 + denomination
                # shape so multi-segment / real-mint / mojibake-mint / parenthetical
                # -mint / out-of-registry-mint lines keep their current parse.
                if len(rs) == 1 and _is_denomination(rs[0]):
                    out["nominal"] = rs[0]
                else:
                    out["mint"] = rs[-1]
                    if len(rs) > 1:
                        out["nominal"] = ", ".join(rs[:-1])
    else:
        out["ruler"] = ruler_line + "."
    if len(parts) >= 2 and "nominal" not in out:
        # Second line: «1 Speciedaler 1683, Glückstadt» or
        # «1 Speciedaler u. år (1670), København» (undated; year in
        # parentheses). For the «u. år (YYYY)» pattern, fold the
        # parenthesised year into the years field AND drop the whole
        # «u. år (YYYY)» fragment from the nominal so the nominal
        # comes out clean.
        line = parts[1]
        # (Former U+FFFD→å band-aid removed 2026-07-11: it wrongly guessed
        # EVERY mojibake was å — the corruption also hit æ/ø — and it only
        # covered the nominal line, never description/raw_text. Root-fixed at
        # source: fetch_hede now decodes ISO-8859-1 strictly instead of
        # utf-8+replace, so the cache no longer bakes U+FFFD. Re-harvest the
        # 272 affected pages after this change.)
        undated = re.search(r"\bu\.?\s*å?r\.?\s*\(\s*(\d{4})\s*\)", line, re.IGNORECASE)
        if undated:
            out.setdefault("years", _extract_years(undated.group(1)))
            line = (line[: undated.start()] + line[undated.end():]).strip()
            line = re.sub(r"\s+,", ",", line).strip(" ,")
        yr_match = re.search(r"\d{4}(?:[\-,\s]+\d{4})*", line)
        if yr_match:
            out["years"] = _extract_years(yr_match.group(0))
            before = line[: yr_match.start()].strip().rstrip(",")
            after = line[yr_match.end():].strip().lstrip(",")
            # Standard Danish H1 layout: «<nominal> <year>, <mint>». In that
            # case `before` is the bare nominal and `after` is the mint.
            #
            # Norge H1 layout (e.g. nf3h66): «<nominal>, <mint> <year>» — the
            # mint precedes the year and `after` is empty. When `after` is
            # empty AND `before` carries a comma, split `before` on its LAST
            # comma: trailing segment = mint, preceding segments = nominal.
            # The «preceding segments» join preserves multi-denom labels like
            # «1, 2, 3 og 4 Speciedaler» without truncating to «1».
            if not after and "," in before:
                segs = [s.strip() for s in before.split(",") if s.strip()]
                if len(segs) >= 2:
                    out["nominal"] = ", ".join(segs[:-1])
                    out["mint"] = segs[-1]
                else:
                    out["nominal"] = before
            else:
                out["nominal"] = before
                if after:
                    out["mint"] = after.strip(",").strip()
        else:
            # No year match — try splitting on the trailing comma to
            # separate «Nominal, Mint» (typical after the «u. år
            # (YYYY)» fragment was stripped above). For multi-
            # denomination headings like «1, 2, 3 og 4 Speciedaler,
            # København», the LAST comma-segment is the mint and all
            # the preceding ones are part of the denomination list
            # — join them back so the nominal isn't truncated to
            # «1».
            if "," in line:
                segs = [s.strip() for s in line.split(",") if s.strip()]
                if len(segs) >= 2:
                    out["nominal"] = ", ".join(segs[:-1])
                    out["mint"] = segs[-1]
                else:
                    out["nominal"] = line.strip(" ,")
            else:
                out["nominal"] = line
    return out


def _looks_like_overview(html: str) -> bool:
    """Overview pages have «oversigt efter Hede» in H1 and a big TABLE
    listing many entries — skip them in per-page parsing (we still
    keep their raw HTML cached for human reference)."""
    return bool(re.search(r"oversigt\s+efter\s+Hede", html, re.IGNORECASE))


# Hede letter-grouped sub-variant pattern: a single page lists 2+
# mintmaster/year sub-variants sharing the SAME specs but having
# DIFFERENT year lists, Hede sub-letter suffixes and Sieg sub-numbers.
# Example (c9h16, 10 Øre Christian IX):
#
#   A) 1874-75, 1882, 1884, 1886, 1888-89, 1891; CS (Hede 16A, Sieg 11.1)
#   B) 1894, 1897, 1899, 1903-05; VBP (Hede 16B, Sieg 11.2)
#
# Distinct from the «multi-Hede page» case (specs.by_hede), where each
# sub-Hede has its OWN spec block. Here the spec block is shared and
# the only per-variant data is years + mintmaster + catalog sub-refs.
_LETTER_GROUP_BLOCK_RE = re.compile(
    r"^[ \t]*([A-Z])\)\s+"            # «A)» / «B)» at line start
    r"([\s\S]+?)"                     # body — years + mm + refs (lazy)
    r"(?=^[ \t]*[A-Z]\)|"             # ends at next letter-group …
    # Same section-boundary set as `_SECTION_BOUNDARY_RE`. Without the
    # comprehensive list, pages whose specs use the bare `Vægt:` form
    # (instead of `Bruttovægt:`) let the letter-block body engulf the
    # spec values + any trailing prose. The last parenthesised group
    # in such an over-long body usually fails the «Hede {ref}{letter}»
    # anchor check (e.g. it's an «(Aagaard, NNUM 2017 side 74)»
    # bibliography paren), and the whole letter-group is dropped —
    # f2h9 c4h25-style pages then have NO per-letter years extracted.
    r"^[ \t]*Bruttov[æa]gt|"          # spec — full form
    r"^[ \t]*V[æa]gt|"                # spec — bare form (many pre-1700)
    r"^[ \t]*Finhed|"
    r"^[ \t]*Finv[æa]gt|"
    r"^[ \t]*Marken\s+fin|"           # «Marken fin udbragt til …»
    r"^[ \t]*Litteratur|"             # bibliography
    r"^[ \t]*Eksemplar|"              # specimen list (Bondes / Zincksamlingen)
    r"^[ \t]*M[øo]ntmesterm[æa]rke|"
    r"^[ \t]*M[øo]ntmester(?:\b|:)|"
    r"^[ \t]*Bem[æa]rk|"              # explanatory annotation paragraphs
    r"^[ \t]*Tilbage|"                # «Tilbage til Dansk Mønts forside»
    r"\Z)",                           # … or end-of-text
    re.MULTILINE,
)
# Within a letter-group body the catalog refs sit in a parenthesis at
# the tail: «(Hede 16A, Sieg 11.1)». The mintmaster is the free token
# between the year-list and that parenthesis (often on its own line as
# in «...1891; \n CS \n (Hede 16A, Sieg 11.1)»).
_LETTER_GROUP_REFS_RE = re.compile(r"\(([^()]+)\)\s*$")


def _extract_letter_groups(text: str, page_hede: str) -> dict | None:
    """Detect Hede letter-grouped sub-variants on a page whose specs
    block is shared. Returns a dict keyed by letter («A», «B», …) with
    per-letter years + catalog_refs + mintmaster, OR None if no
    letter-group pattern is present on the page.

    `page_hede` is the page's primary Hede number (e.g. «16» from
    `c9h16`); a letter-group is only accepted if its catalog tail
    contains «Hede {page_hede}{LETTER}» — without that anchor the
    «A)» / «B)» pattern is just numbered prose and should be ignored.
    """
    blocks = list(_LETTER_GROUP_BLOCK_RE.finditer(text))
    if len(blocks) < 2:
        return None
    out: dict[str, dict] = {}
    for m in blocks:
        letter = m.group(1)
        body = m.group(2).strip()
        # Catalog refs live in the tail parenthesis. Match the LAST
        # parenthesised group so any inline parens earlier in the
        # mintmaster description don't confuse the matcher.
        refs_m = None
        for inner in re.finditer(r"\(([^()]+)\)", body):
            refs_m = inner
        if not refs_m:
            continue
        refs_text = refs_m.group(1)
        # Require the letter-anchored Hede ref («Hede 16A» when letter
        # is «A» and page_hede is «16»). Without it, this is not a
        # letter-group entry.
        if not re.search(
            rf"\bHede\s*{re.escape(page_hede)}{letter}\b",
            refs_text,
            re.IGNORECASE,
        ):
            continue
        refs = _extract_refs(refs_text)
        # Years: scan the body up to the tail parenthesis
        years_text = body[: refs_m.start()]
        years = _extract_years(years_text)
        # Mintmaster: tail of years_text, last non-empty alphabetic
        # token. The page tends to write «...; CS» or «...VBP» — a
        # short uppercase initials block separated from the year list
        # by «;» or newline.
        mm_match = None
        for mm_m in re.finditer(r"\b([A-ZÆØÅ]{1,5})\b", years_text):
            mm_match = mm_m
        mintmaster = mm_match.group(1) if mm_match else None
        plausible_years = [y for y in years if 1450 <= y["year"] <= 1950]
        # A year-less variant line is still a real sub-variant — many pages
        # distinguish sub-types by DESIGN («A) ring om kronen» vs «B) uden
        # ring», c4h117) with years only in the Zincksamlingen list. The
        # «Hede {page_hede}{letter}» anchor (checked above) is the reliable
        # signal; do NOT drop the letter just because its line carries no year.
        out[letter] = {
            "years": plausible_years,
            "catalog_refs": refs,
            "mintmaster": mintmaster,
        }
    return out if len(out) >= 2 else None


def parse_one(html: str, basename: str) -> dict:
    text = _strip_html(html)
    ruler_label, volume = _ruler_volume(basename)
    out: dict = {
        "id": basename,
        "ruler_volume": volume,
        "ruler_inferred": ruler_label,
    }
    # Header (ruler / nominal / mint / years)
    header = _parse_header(html)
    out.update({k: v for k, v in header.items() if k != "h1"})
    if "ruler" not in out and ruler_label:
        out["ruler"] = ruler_label

    # Fallback year extraction. The header path only inspects the
    # <H1>; many pages publish the year-rarity list in a paragraph
    # immediately under the H1 (e.g. «1541 (R), 1544 (S), 1546 (RR)
    # …»). When the header parse came back without years, scan the
    # body text after the title/H1 echo for the same year-block
    # pattern — but stop AT the first specs / bibliography / specimen-
    # list section header. Those sections legitimately carry year-
    # shaped tokens that are NOT coin years:
    #   * «Bruttovægt: 28,893g» / «Finhed: 0,875» — spec numerics
    #   * «Wilcke, Julius: Kurantmønten 1726-1788, København 1927»
    #     — book title + publication year in Litteratur
    #   * «1768, Schou 2 / 1769, Schou 7» — specimen catalogue rows
    #     (these years are usually a subset of the year-rarity line
    #     above, but if a year appears ONLY here without a rarity, we
    #     prefer not to elevate it without explicit signal)
    # Stopping at the section boundary preserves the year-rarity line
    # that lives between the H1 echo and the first spec marker.
    if not out.get("years"):
        # Skip the first line if it just echoes the H1 (ruler + nominal)
        body_start = text
        first_newline = text.find("\n")
        if 0 < first_newline < 200:
            body_start = text[first_newline:]
        section_m = _SECTION_BOUNDARY_RE.search(body_start)
        if section_m:
            scan_window = body_start[:section_m.start()]
        else:
            # No section marker found — fall back to the original
            # 600-char cap to keep behaviour sane on pages with
            # missing/non-standard structure.
            scan_window = body_start[:600]
        # Restrict year extraction to the FIRST sentence containing a
        # year-block. Hede pages put the year-rarity line as a single
        # sentence right after the H1 echo («1808, 1809, 1810 (Unik),
        # 1819 (Unik).»). The prose that follows can include years
        # that are NOT mint years — biographical notes (e.g. «Michael
        # Flor virkede ... til 1816»), historical context («I 1643-44
        # hærgede den svenske hær»), legal-act dates («Ved forordning
        # 1648»), bibliographic refs, etc. The `_strip_non_mint_year_refs`
        # pre-filter handles the common cases; this scope tightening
        # adds a structural belt-and-braces by capping extraction at
        # the first year-sentence's terminating period.
        scan_window = _narrow_to_first_year_sentence(scan_window)
        year_candidates = _extract_years(scan_window)
        # Reject the candidate list if it crosses into noise — a
        # plausible year-block is contiguous and short. We accept up
        # to 30 entries, restricted to 1450..(current_year-100) to
        # filter parser noise.
        plausible = [y for y in year_candidates if 1450 <= y["year"] <= 1950]
        if plausible:
            out["years"] = plausible

    # Spec block(s)
    specs = _extract_specs(text, basename)
    if specs:
        out["specs"] = specs

    # Letter-grouped sub-variants («A) ... (Hede XA, Sieg X.1) /
    # B) ... (Hede XB, Sieg X.2)»). Extract for BOTH shapes:
    #   * `specs.default` (single shared spec) — emits as `by_letter`
    #     and the builder generates one coin per letter with shared
    #     spec + per-letter years.
    #   * `specs.by_hede` (per-sub-letter specs already present) —
    #     emits per-letter years into the corresponding `by_hede`
    #     entry so the builder gets per-Hede years instead of the
    #     page-aggregate (which may include legal-act years like
    #     «møntordning 1544» that are NOT mint years for the sub-letter).
    if specs:
        # Page's primary Hede number from filename: «c9h16» → «16»
        bm = re.match(r"^n?[cf]\d+h([\d]+)", basename)
        if bm:
            letter_groups = _extract_letter_groups(text, bm.group(1))
            if letter_groups:
                if "default" in specs:
                    out["by_letter"] = letter_groups
                elif "by_hede" in specs:
                    # Attach per-letter years to matching by_hede sub-spec.
                    # Match by Hede sub-letter — «A» → key like «9A», «9a».
                    page_hede = bm.group(1)
                    for letter, lv in letter_groups.items():
                        sub_key = f"{page_hede}{letter}"
                        # by_hede keys may be upper / lower case
                        for k in list(specs["by_hede"].keys()):
                            if k.lower() == sub_key.lower():
                                specs["by_hede"][k]["years"] = lv["years"]
                                break

    # «Ruler, NOMINAL» mint recovery (Part 2). The H1 carried a nominal but no
    # mint — the mint lives on the per-variant A)/B)/C) lines. Recover it so the
    # seed builder doesn't drop the coin as mint-less. Runs AFTER by_letter +
    # specs are populated; gated on «no top-level mint» so it never touches
    # pages that already parse a mint.
    if out.get("nominal") and not out.get("mint"):
        by_letter = out.get("by_letter")
        if by_letter:
            # Per-letter (sub-variant) mint — 78A København, 78B Helsingør are
            # DIFFERENT mints, so each by_letter entry gets its own. Verbatim;
            # the builder normalises + uses it (fallback to top-level if absent).
            for letter, mint in _mint_per_letter_block(text).items():
                if letter in by_letter:
                    by_letter[letter]["mint"] = mint
        elif "by_hede" not in (out.get("specs") or {}):
            # Single-coin page (one spec, no sub-grouping): one coin struck at
            # all the variant-line mints → aggregate as a Danish-conjunction
            # string, which _normalize_mints splits into a multi-mint list.
            recovered = _mints_from_variant_lines(text)
            if recovered:
                out["mint"] = " og ".join(recovered)
        # by_hede field-swap pages (c4h53) are left for a per-spec-group mint
        # follow-up — each by_hede group can span different mints.

    # Catalog refs
    refs = _extract_refs(text)
    if refs:
        out["catalog_refs"] = refs

    # Literatur
    lit = _extract_litteratur(text)
    if lit:
        out["litteratur"] = lit

    # Eksemplarer (specimen lists)
    eks = _extract_eksemplarer(text)
    if eks:
        out["eksemplarer"] = eks

    # Description heuristic — lines mentioning Forside / bagside /
    # randskrift, before the first Bruttovægt block.
    desc_match = re.search(
        r"(Forside\s*:.*?)(?=Bruttovægt|Eksemplar|Litteratur|$)",
        text,
        re.DOTALL | re.IGNORECASE,
    )
    if desc_match:
        desc = desc_match.group(1).strip()
        # Strip the HR sentinel — useful internally for spec-block
        # boundary detection but noise in human-readable prose.
        desc = desc.replace(_HR_SENTINEL, "").strip()
        # Trim long Mintmaster sub-variant tables (keep first 800 chars)
        out["description"] = desc[:800]

    # Hede number(s) covered — derive from filename + cross-check
    # against page title's «Hede ...» phrase.
    hm_filename = re.search(r"^n?[cf]\d+h([\d\-,A-Za-z\s]+?)(?:\.|note|$)", basename)
    if hm_filename:
        out["hede_numbers_filename"] = re.findall(r"\d+[A-Za-z]*", hm_filename.group(1))
    title_str = out.get("page_title", "")
    if "Hede" in title_str:
        out["hede_numbers_title"] = re.findall(
            r"\bHede\s*(\d+[A-Za-z]*(?:[\-,]\s*\d+[A-Za-z]*)*)",
            title_str,
        )

    # Strip the HR sentinel from raw_text too — internal marker only.
    out["raw_text"] = text.replace(_HR_SENTINEL, "").strip()
    return out


def _build_index(parsed_files: list[Path]) -> dict:
    """Aggregate index: map composite Hede key («c4h28») → parsed file
    + condensed summary of the most useful fields. Lets downstream
    tooling (matcher, audit) look up by Hede key without re-loading
    every per-page JSON.

    When two parsed files claim the same composite key (e.g. a page
    whose own primary Hede is 68 and another page that cross-
    references Hede 68's sub-variant), the entry whose basename
    matches the key wins — the «canonical» file for that Hede gets
    priority over cross-references.
    """
    index: dict[str, dict] = {}
    for f in parsed_files:
        d = json.loads(f.read_text(encoding="utf-8"))
        vol = d.get("ruler_volume", "")
        # Page's own primary Hede number from basename — used both
        # for canonical-file scoring below and as a fallback when the
        # parsed JSON doesn't surface a number through the usual paths.
        own_m = re.match(r"^n?[cf]\d+h(\w+)$", d["id"])
        own_num = own_m.group(1).lower() if own_m else None
        # Take the union of filename- and title-derived numbers
        nums = set(d.get("hede_numbers_filename") or [])
        nums.update(d.get("hede_numbers_title") or [])
        # If specs has by_hede, those are also Hede sub-keys
        if isinstance(d.get("specs"), dict) and "by_hede" in d["specs"]:
            nums.update(d["specs"]["by_hede"].keys())
        # by_letter pages contribute one Hede sub-key per letter
        # variant («c9h16» with letters A,B → 16A, 16B). The bare
        # numeric «16» key is dropped from the index for these pages
        # so downstream lookups land on the per-letter entry that
        # carries the actual year list + sub-Sieg ref.
        if d.get("by_letter"):
            letter_nums = set()
            page_hede = own_num or ""
            for letter in d["by_letter"].keys():
                letter_nums.add(f"{page_hede}{letter}".lower())
            # Drop the bare numeric key only if every letter-variant
            # claims a Hede sub-letter that's actually present in the
            # page's Hede catalog refs (defensive against partial
            # detections).
            if letter_nums and page_hede in nums:
                nums.discard(page_hede)
            nums.update(letter_nums)
        if not nums and own_num:
            nums.add(own_num)
        for n in nums:
            key = f"{vol}{n.lower()}"
            entry = {
                "file": d["id"],
                "ruler": d.get("ruler"),
                "nominal": d.get("nominal"),
                "mint": d.get("mint"),
                "years": d.get("years") or [],
            }
            specs = d.get("specs") or {}
            if "by_hede" in specs:
                for sk, sv in specs["by_hede"].items():
                    if sk.lower() == n.lower():
                        entry["specs"] = sv
                        break
                else:
                    entry["specs"] = next(iter(specs["by_hede"].values()), None)
            elif "default" in specs:
                entry["specs"] = specs["default"]
            entry["catalog_refs"] = d.get("catalog_refs")
            # by_letter override: when this key targets a per-letter
            # sub-variant (e.g. «c9h16a»), prefer that variant's own
            # years + catalog refs over the page-level aggregate.
            by_letter = d.get("by_letter") or {}
            if by_letter:
                page_hede = (own_num or "").lower()
                for letter, lv in by_letter.items():
                    if n.lower() == f"{page_hede}{letter.lower()}":
                        entry["years"] = lv.get("years") or []
                        if lv.get("catalog_refs"):
                            entry["catalog_refs"] = lv["catalog_refs"]
                        if lv.get("mintmaster"):
                            entry["mintmaster"] = lv["mintmaster"]
                        break
            # Canonicality: a file whose basename's primary number
            # matches the key always wins over cross-references that
            # only mention this key.
            is_canonical = (own_num == n.lower())
            existing = index.get(key)
            if existing is None:
                index[key] = entry
            elif is_canonical and not _is_canonical(existing, key, vol):
                index[key] = entry
    return index


def _is_canonical(entry: dict, key: str, volume: str) -> bool:
    """An index entry is canonical when its `file` basename's primary
    number matches the lookup key (after the volume prefix is
    stripped)."""
    file_id = entry.get("file") or ""
    if not file_id.startswith(volume):
        return False
    file_num = file_id[len(volume):].lower()
    key_num = key[len(volume):].lower()
    return file_num == key_num


# Index-stub extraction — for Hede entries listed in `*hede.htm`
# overview tables WITHOUT a `<A HREF>` link to a deep page. These are
# real catalogue entries that danskmoent.dk simply hasn't published a
# detail page for (often «Kendes ikke mere» / «Prøvemøntning» / very
# rare specimens). The index row itself attests: nominal, metal, year,
# mint, Sieg-ref and a brief comment — enough to emit a seed-stub
# `<vol>h<N>.json` that flows through the normal seed-builder
# pipeline. Weight + fineness stay None (require the deep page or
# paper-source for actual measurements).
#
# Output JSON shape mirrors the normal deep-page parse but carries an
# explicit `_source_type: "index_stub"` marker so downstream code
# (seed builder, audits) can distinguish stub from real data.

_INDEX_TR_RE = re.compile(r"<TR[^>]*>(.*?)</TR>", re.I | re.S)
_INDEX_TD_RE = re.compile(r"<TD[^>]*>(.*?)</TD>", re.I | re.S)
# Match <A HREF="…cNhN.htm"> in the FIRST cell — captures the
# target's own Hede-N for cross-reference detection.
_INDEX_FIRST_CELL_LINK_RE = re.compile(
    r"<A\s+HREF=[\"'][^\"']*\b[cfn]\d+h(\d+[a-z]?)\.htm[\"']", re.I,
)
_INDEX_HEDE_NUMBER_RE = re.compile(
    r"^\s*(?:Hede\s+)?(\d+[A-Z]{0,3}(?:-\d+[A-Z]{0,3})?)\s*$", re.I,
)
_INDEX_HTML_ENTITIES = {
    "&oslash;": "ø", "&Oslash;": "Ø",
    "&aelig;":  "æ", "&AElig;":  "Æ",
    "&aring;":  "å", "&Aring;":  "Å",
    "&uuml;":   "ü", "&Uuml;":   "Ü",
    "&ouml;":   "ö", "&Ouml;":   "Ö",
    "&auml;":   "ä", "&Auml;":   "Ä",
    "&szlig;":  "ß",
    "&amp;":    "&",
    "&nbsp;":   " ",
    "&quot;":   '"',
    "&#39;":    "'",
}
_INDEX_METAL_TOKENS = {
    "sølv":            "silver",
    "guld":            "gold",
    "kobber":          "copper",
    "bronze":          "bronze",
    "aluminiumbronze": "bronze",  # Krone-fod 1/2 Krone tier
    "tin":             "tin",
    "messing":         "brass",
    "kobbernikkel":    "copper_nickel",
    "billon":          "billon",
}


def _index_decode_entities(s: str) -> str:
    out = s
    for ent, ch in _INDEX_HTML_ENTITIES.items():
        out = out.replace(ent, ch)
    return out


def _index_clean_cell(html_cell: str) -> str:
    """Strip tags, normalise whitespace, decode common HTML entities."""
    bare = re.sub(r"<[^>]+>", " ", html_cell)
    bare = re.sub(r"\s+", " ", bare).strip()
    return _index_decode_entities(bare)


def _index_parse_years(year_cell: str) -> list[dict]:
    """Parse the index «year» cell into the deep-page years[] shape.

    Handles forms seen in indices:
      "1607, 1608"       → [{year:1607}, {year:1608}]
      "1545"             → [{year:1545}]
      "(15)45"           → [{year:1545}]            (c3 century-abbrev)
      "1924-1926"        → [{year:1924},…,{year:1926}]
      "1781-96"          → [{year:1781},…,{year:1796}]
      "U.år" / "u.år"    → []  (undated)
      "1939, 1940"       → [{year:1939},{year:1940}]
    """
    if not year_cell:
        return []
    s = year_cell.strip()
    if re.match(r"^[Uu]\.?\s*[åa]r", s):
        return []
    # Century-abbrev form «(15)45» → 1545
    s = _expand_century_abbr(s)
    # Short-range form «1781-96» → «1781-1796»
    s = _expand_year_ranges(s)
    out: list[dict] = []
    for tok in re.findall(r"\b\d{4}(?:\s*-\s*\d{4})?\b", s):
        if "-" in tok:
            a, b = [int(x.strip()) for x in tok.split("-", 1)]
            for y in range(a, b + 1):
                out.append({"year": y, "rarity": None})
        else:
            out.append({"year": int(tok), "rarity": None})
    return out


def _index_classify_columns(cells: list[str]) -> dict | None:
    """Detect the column layout per row and extract structured fields.

    Two layouts seen across volumes:
      7-col: [Hede, Sieg, Nominal, Metal, Year, Mint, Comment]
        (c3, c4, f2, f4, f5, f6, c8, c10, f9)
      8-col: [Hede, Sieg, ProofTag, Nominal, Metal, Year, Mint, Comment]
        (c7 — Prøvemøntning rows with P1/T34/E3 sub-classification tag)

    Detection: cell[3] is a metal token → 7-col; cell[4] is a metal
    token → 8-col. Otherwise fall back to 7-col with empty metal.
    Returns dict with: hede, sieg, nominal, metal, years[], mint, note.
    """
    if len(cells) < 4:
        return None
    hede = cells[0].strip()
    if hede.lower().startswith("hede "):
        hede = hede[5:].strip()
    sieg = cells[1] if len(cells) > 1 else ""

    cell3 = cells[3].lower().strip() if len(cells) > 3 else ""
    cell4 = cells[4].lower().strip() if len(cells) > 4 else ""

    if cell3 in _INDEX_METAL_TOKENS:
        # 7-col layout
        nominal = cells[2]
        metal = _INDEX_METAL_TOKENS[cell3]
        years_cell = cells[4] if len(cells) > 4 else ""
        mint = cells[5] if len(cells) > 5 else ""
        note = " · ".join(c for c in cells[6:] if c) if len(cells) > 6 else ""
    elif cell4 in _INDEX_METAL_TOKENS:
        # 8-col layout with proof-tag at cell[2]
        # Merge proof-tag into nominal: «1/3 Speciedaler P1»
        nominal = f"{cells[3]} {cells[2]}".strip() if cells[2] else cells[3]
        metal = _INDEX_METAL_TOKENS[cell4]
        years_cell = cells[5] if len(cells) > 5 else ""
        mint = cells[6] if len(cells) > 6 else ""
        note = " · ".join(c for c in cells[7:] if c) if len(cells) > 7 else ""
    else:
        # Layout unclear — bail. Caller will skip the row.
        return None

    return {
        "hede": hede,
        "sieg": sieg,
        "nominal": nominal.strip(),
        "metal": metal,
        "years": _index_parse_years(years_cell),
        "mint": mint.strip().rstrip(",.;"),
        "note": note.strip(),
    }


def _extract_index_stubs(html: str, basename: str) -> list[dict]:
    """Walk an overview page (`<vol>hede.htm`) and return one parsed-
    JSON-compatible stub per row whose Hede-cell has NO `<A HREF>` link.

    Returned dicts mirror the deep-page parse_one() output:
      id, ruler_volume, ruler_inferred, page_title, ruler,
      years[], nominal, mint, specs.default{...None...},
      catalog_refs{Hede, Sieg}, _source_type: "index_stub",
      metal_from_index: <metal-token>, index_note: <comment>.

    Skips rows that link to deep pages (real entries) or that have
    malformed structure (e.g. table header row, footer row).
    """
    ruler_label, volume_code = _ruler_volume(basename + "h0")
    # `_ruler_volume` expects an `…h<NUM>` suffix to parse the volume.
    # Indices like `c4hede` won't fit; rebuild manually.
    m = re.match(r"^(n?)(c|f)(\d+)hede$", basename)
    if not m:
        return []
    norge_prefix, letter, num = m.groups()
    ruler_label = (
        f"{'Christian' if letter == 'c' else 'Frederik'} {num}."
    )
    volume_code = f"{norge_prefix}{letter}{num}h"

    stubs: list[dict] = []
    for row_match in _INDEX_TR_RE.finditer(html):
        body = row_match.group(1)
        tds = _INDEX_TD_RE.findall(body)
        if len(tds) < 4:
            continue
        first_td = tds[0]
        first_clean = _index_clean_cell(first_td)
        if not _INDEX_HEDE_NUMBER_RE.match(first_clean):
            continue
        # Skip the table header row («<B>Hede</B>» / «Hede» plain)
        if first_clean.strip().lower() in ("hede", ""):
            continue
        # If the FIRST cell links to the row's OWN canonical deep page
        # (e.g. Hede 16 → c4h16.htm), the deep page exists — skip stub
        # generation. Soft-links to thematic articles (halvglkr.htm,
        # loeve.htm) or cross-refs to OTHER Hede pages (Hede 47 →
        # c4h46.htm) don't establish an own deep page, so those rows
        # DO become stubs.
        own_hede = _INDEX_HEDE_NUMBER_RE.match(first_clean).group(1).lower()
        # Strip trailing letter-suffix («2ab», «17ab», «99abcd») to the
        # bare numeric form for canonical-link comparison — the deep
        # page convention is `<vol>h<N>.htm` (parent number), with
        # sub-letter variants handled inside via the by_letter
        # mechanism. «Hede 2AB» row whose first cell links to f5h2.htm
        # is a real deep page covering 2A + 2B.
        own_bare = re.sub(r"[a-z]+$", "", own_hede)
        first_link = _INDEX_FIRST_CELL_LINK_RE.search(first_td)
        if first_link:
            link_bare = re.sub(r"[a-z]+$", "", first_link.group(1).lower())
            if link_bare == own_bare:
                continue  # canonical deep page exists
        cells = [_index_clean_cell(td) for td in tds]
        parsed_row = _index_classify_columns(cells)
        if parsed_row is None:
            continue
        hede_no = parsed_row["hede"]
        # Construct file-id matching deep-page convention. Sub-letter
        # forms like «17AB» / «13AB» / «22AB» become a single stub on
        # the parent number for now; the seed builder's by_letter
        # mechanism doesn't fire because we have no per-letter year
        # split. Future enrichment via paper-source can expand these.
        stub_id = f"{volume_code}{hede_no.lower()}"
        catalog_refs: dict[str, list[str]] = {"Hede": [hede_no]}
        if parsed_row["sieg"]:
            catalog_refs["Sieg"] = [parsed_row["sieg"]]
        stub = {
            "id": stub_id,
            "ruler_volume": volume_code,
            "ruler_inferred": ruler_label,
            "page_title": f"{ruler_label}, Hede {hede_no} (index stub)",
            "ruler": ruler_label,
            "years": parsed_row["years"],
            "nominal": parsed_row["nominal"],
            "mint": parsed_row["mint"],
            "specs": {
                "default": {
                    "bruttovægt_g": None,
                    "finhed": None,
                    "finvægt_g": None,
                    "marken_fin_udbragt_til": None,
                },
            },
            "catalog_refs": catalog_refs,
            "litteratur": [],
            "_source_type": "index_stub",
            "_source_index": f"{basename}.htm",
            "metal_from_index": parsed_row["metal"],
            "index_note": parsed_row["note"],
        }
        stubs.append(stub)
    return stubs


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true",
                    help="Reparse pages even if .json sibling exists")
    args = ap.parse_args()

    parsed = 0
    skipped = 0
    overviews = 0
    failed = 0
    parsed_files: list[Path] = []
    for f in sorted(CACHE_DIR.glob("*.htm")):
        basename = f.stem
        json_path = f.with_suffix(".json")
        if json_path.exists() and not args.force:
            skipped += 1
            parsed_files.append(json_path)
            continue
        html = f.read_text(encoding="utf-8", errors="replace")
        if _looks_like_overview(html):
            overviews += 1
            continue
        try:
            entry = parse_one(html, basename)
        except Exception as exc:
            failed += 1
            print(f"  [{basename}] parse error: {exc}", file=sys.stderr)
            continue
        json_path.write_text(
            json.dumps(entry, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        parsed += 1
        parsed_files.append(json_path)

    # Second pass: index-only stubs. For each overview page
    # (`*hede.htm`), extract rows whose Hede cell has no deep-page link
    # and emit a synthetic sidecar at `<vol>h<N>.json` marked
    # `_source_type: "index_stub"`. Skips any stub whose target sidecar
    # already exists (a real deep-page parse takes precedence) AND any
    # stub whose Hede composite-key is already covered by another deep
    # page's `specs.by_hede` (e.g. Hede 34 is documented inside
    # c4h33.htm via by_hede — no stub needed).
    #
    # First-pass aggregate built from deep-page parses only — drives
    # the «is this Hede already covered?» check below.
    deep_index = _build_index(parsed_files)
    stub_written = 0
    stub_skipped_existing = 0
    stub_skipped_covered = 0
    for f in sorted(CACHE_DIR.glob("*hede.htm")):
        basename = f.stem  # e.g. c3hede
        if not re.match(r"^n?[cf]\d+hede$", basename):
            continue
        html = f.read_text(encoding="utf-8", errors="replace")
        stubs = _extract_index_stubs(html, basename)
        for stub in stubs:
            # Skip if a deep-page parse (real or by_hede / by_letter
            # sub-entry on another page) already covers this composite
            # key. Composite shape: <ruler_volume><hede>.
            composite_key = f"{stub['ruler_volume']}{stub['catalog_refs']['Hede'][0].lower()}"
            if composite_key in deep_index:
                stub_skipped_covered += 1
                continue
            # Also try the bare-number form (strip trailing letters) —
            # «60ab» row may be covered by a deep page that lists «60a»
            # + «60b» separately via by_letter.
            bare_hede = re.sub(r"[a-z]+$", "", stub["catalog_refs"]["Hede"][0].lower())
            if bare_hede != stub["catalog_refs"]["Hede"][0].lower():
                bare_key = f"{stub['ruler_volume']}{bare_hede}"
                if bare_key in deep_index:
                    stub_skipped_covered += 1
                    continue
            stub_path = CACHE_DIR / f"{stub['id']}.json"
            if stub_path.exists() and not args.force:
                stub_skipped_existing += 1
                continue
            stub_path.write_text(
                json.dumps(stub, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            stub_written += 1
            parsed_files.append(stub_path)

    # Aggregate index. `sort_keys=True` keeps the on-disk output
    # deterministic across runs — without it, dict insertion order
    # (which varies with filesystem listing / re-parse subsets) would
    # rewrite most of the file on every run even when the actual
    # entries are unchanged. Stable order makes regenerated indices
    # produce minimal diffs in the submodule.
    index = _build_index(parsed_files)
    (CACHE_DIR / "_parsed_index.json").write_text(
        json.dumps(index, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    print(f"Parsed: {parsed}")
    print(f"Skipped (already parsed): {skipped}")
    print(f"Overviews skipped (in-page parsing not implemented): {overviews}")
    print(f"Failed: {failed}")
    print(f"Index stubs written: {stub_written}")
    print(f"Index stubs skipped (existing sidecar): {stub_skipped_existing}")
    print(f"Index stubs skipped (covered by by_hede / by_letter): {stub_skipped_covered}")
    print(f"Aggregate index: {len(index)} composite Hede keys")
    return 0


if __name__ == "__main__":
    sys.exit(main())
