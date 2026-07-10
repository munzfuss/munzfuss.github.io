"""§BK NumisMaster Phase 5 — parse cached MC_<N>.html → MC_<N>.parsed.json.

General-purpose parser (renamed from `parse_numismaster_pre1541.py`). Takes any
sub-scope directory under `scripts/cache/numismaster/<sub_scope>/`, walks every
`MC_*.html`, writes a sibling `MC_<N>.parsed.json` with the structured field
extraction. Idempotent — re-run skips already-parsed files unless `--force`.

Sub-scope directories:
  schleswig_holstein/   — §BJ SH cluster (~561 MCs, all in mission scope)
  denmark/              — §BJ Denmark (~987 MCs ≤ 1914)
  norway/               — §BJ Norway (~344 MCs ≤ 1814 Danish-rule era)

Output schema per `MC_<N>.parsed.json`:
  - source_file, numismaster_id, url, sub_scope
  - country, catalog_number, political_period, coinage_entity
  - denomination, date_raw, year_first, year_last
  - ruler, mint, composition (metal), mass_g, fineness, actual_weight_fein
  - obverse / reverse {description, legend}
  - general_note (verbatim) + catalog_refs (parsed cross-refs)
  - parsed_at — UTC ISO-8601 wall-clock

Cross-refs extracted from «General note» (verbatim) and the page body:
  - schou (Sch#)         — Schou 1926 Danish-Norwegian catalogue
  - lange (L#)           — Lange 1908/1912 Schleswig-Holstein catalogue
  - friedberg (Fr#)      — Friedberg gold-coin standard
  - km (KM#)             — Krause-Mishler (per-country numbering caveat per CLAUDE.md §9)
  - mb (MB#)             — Madai-Bach (pre-Krause SH duchy numbering)
  - sieg                 — Sieg-Møntkatalog
  - hede                 — Hede 1957 / 1971
  - bruun                — L. E. Bruun Collection catalogue
  - schou_norway         — Schive 1865 / Schou-Norway

Run:
    .venv/bin/python scripts/parse_numismaster.py --sub-scope schleswig_holstein
    .venv/bin/python scripts/parse_numismaster.py --sub-scope schleswig_holstein --force
    .venv/bin/python scripts/parse_numismaster.py --all
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from html import unescape
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib.paths import NUMISMASTER_CACHE  # noqa: E402

# Sub-scope directories that this parser knows about.
KNOWN_SUB_SCOPES = (
    "schleswig_holstein",
    "denmark",
    "norway",
)

_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")


def strip_tags(html: str) -> str:
    html = re.sub(r"<script[^>]*>.*?</script>", " ", html, flags=re.DOTALL)
    html = re.sub(r"<style[^>]*>.*?</style>", " ", html, flags=re.DOTALL)
    txt = _TAG_RE.sub(" ", html)
    txt = unescape(txt)
    txt = txt.replace("\xa0", " ")
    txt = _WS_RE.sub(" ", txt)
    return txt.strip()


def pull(text: str, key: str, until: str) -> str | None:
    """Pull '<key>: ... <until>' value with whitespace tolerance."""
    pat = re.escape(key) + r":\s*(.+?)\s*(?=" + re.escape(until) + r")"
    m = re.search(pat, text)
    return m.group(1).strip() if m else None


def _normalise_year_string(s: str) -> str:
    """Normalise NumisMaster date strings before year-token extraction:

      * «(1)617» / «(1)619»  → «1617» / «1619»  (century-abbreviation form
        seen on Frederik I / Christian III pre-1559 Schleswig-Holstein
        pages where the actual coin's engraving says «(15)63» or «(1)617»).
      * «(15)Z5» / «(15)Z6»  → «1525» / «1526»  (century-abbreviation form
        WITH Z→2 substitution in the YY tail — same Z glyph as «15Z3»
        but the price-table column header uses the parenthesised form
        when the century digits are abbreviated on the coin engraving).
      * «16Z8» / «1Z28»      → «1628» / «1228»  (Z is a literal engraving
        glyph used on some 17th-c. Schleswig-Holstein-Gottorp coins as a
        variant for the digit 2 — confirmed on MC_167311's reverse legend
        «Value '1Z8' in cartouche»; the Date field then shows the year
        with the same Z glyph, e.g. «16Z8»).
      * «1Z8» / «1Z2»        → same Z→2 rule applies to short tokens that
        could be coin-value labels but not years; leave non-year strings
        alone via the date-string scope of this function (caller decides
        when to apply).
      * «ND(ca1523)» / «ca. 1523» / «circa 1523» → injects spaces around
        the 4-digit year token so the downstream `\\b(1[5-9]\\d{2})\\b`
        extractor catches it (the «a» in «ca» is a \\w-char and would
        otherwise eat the leading word-boundary). The «ND(…)» / «ca»
        prefix conveys a numismatic uncertainty («No Date, circa year»)
        that we lose at this stage — coins surfaced via this path should
        still carry `year_verified: false` if curators want to flag the
        attribution-only year. Today we leave verification to the curator
        and just ensure the year token isn't silently dropped.
    """
    if not s:
        return s
    # Expand «(1)YY» / «(15)YY» / «(16)YY» — capture century group + 2-digit
    # tail, with optional Z→2 substitution inside the tail («(15)Z5» → «1525»).
    def _expand_parenthesised_century(m):
        century = m.group(1) if len(m.group(1)) == 2 else "1"
        tail = m.group(2).replace("Z", "2").replace("z", "2")
        return century + tail
    s = re.sub(
        r"\(\s*(1[5-9]?)\s*\)\s*([\dZz]{2})",
        _expand_parenthesised_century,
        s,
    )
    # Some pages use the bare form «(1)617» = «1617» (single «1» + 3 digits).
    s = re.sub(r"\(\s*1\s*\)\s*(\d{3})", r"1\1", s)
    # «ND(ca1523)» / «(ca1523)» / «c.1523» / «ca. 1523» / «circa 1523» →
    # inject spaces around the year so the downstream \b extractor matches.
    # Restricted to plausible mint-year range 1[5-9]\d{2} to avoid collateral.
    s = re.sub(
        r"\b(?:ca|circa|c)\.?\s*(1[5-9]\d{2})\b",
        r" \1 ",
        s,
        flags=re.IGNORECASE,
    )
    # Replace Z→2 only INSIDE 4-digit year tokens of shape `1[56789]Z[0-9]` /
    # `1[56789][0-9]Z` / `1Z[0-9]{2}` (anchor on the «1» + century to avoid
    # corrupting unrelated text). Conservative: must be exactly 4 chars with
    # at least one Z and one or more digits, starting with `1`.
    def _z_to_two(m):
        tok = m.group(0)
        return tok.replace("Z", "2").replace("z", "2")
    s = re.sub(r"\b1[5-9Zz]\d?[ZzD0-9]\d\b|\b1[5-9Zz][0-9Zz][0-9Zz]\b", _z_to_two, s)
    return s


def _complete_abbrev_year(start: int, abbrev: str) -> int:
    """Complete an abbreviated range-END ('22' in «ND(1618-22)») to a full year,
    anchored to the START's century — 1618-22 → 1622, 1566-68 → 1568.

    RAISES ValueError when the completed end lands BEFORE the start. That happens
    at a century boundary («1698-02» naively → 1602) or on a malformed range. We
    deliberately do NOT auto-roll «1698-02» to 1702: a silent guess could be wrong,
    so the re-flow HALTS on it and a human decides (curator direction 2026-07-09).
    """
    a = abbrev.strip()
    if len(a) >= 4:
        end = int(a)
    elif len(a) in (1, 2) and a.isdigit():
        end = (start // 100) * 100 + int(a)
    else:
        raise ValueError(f"unexpected abbreviated year-end {abbrev!r} (start {start})")
    if end < start:
        raise ValueError(
            f"abbreviated range {start}-{abbrev} completes to {end} < start {start} "
            f"— century-boundary (e.g. 1698-02 → 1702) OR malformed; verify by hand, "
            f"do NOT auto-roll")
    return end


# «ND(1618-22)» abbreviated-range and «ND(1622)» / «ND(ca1622)» single-year markers.
_ND_RANGE_RE = re.compile(r"\bND\(\s*(\d{4})\s*-\s*(\d{1,4})\s*\)")
_ND_SINGLE_RE = re.compile(r"\bND\(\s*(?:ca\.?\s*|circa\s*|c\.?\s*)?(\d{4})\s*\)", re.I)


def extract_nd_range(text: str | None) -> tuple[int, int] | None:
    """Read the «ND(YYYY-YY)» / «ND(YYYY)» display marker → (year_first, year_last),
    or None when no ND marker is present.

    NumisMaster's STRUCTURED «Date» field unreliably collapses these markers
    («ND(1618-22)» → «1618 - 1618», or worse «1604 - 1604»), so the ND(…) marker
    is authoritative for an undated coin. Scoped to the header region ABOVE the
    «Value information» price table so a «Related coins» sidebar ND marker of an
    UNRELATED coin can't bleed in. Propagates _complete_abbrev_year's ValueError
    on a malformed abbreviated end.
    """
    if not text:
        return None
    # The ND(…) marker sits in the «Value information» price-table Date column
    # (NOT the header). Scope to that table — from «Value information» to the
    # «Related coins» sidebar — the SAME bounds parse_dates_table uses, so a
    # related-coin's ND marker in the sidebar can't bleed in.
    m_vi = re.search(r"\bValue information\b", text)
    start_pos = m_vi.end() if m_vi else 0
    m_end = re.search(
        r"\b(?:Related coins|Notes|Subscription|Back to|Permalink|"
        r"Tilbage til|Copyright|Connect with us|About Us)\b", text[start_pos:])
    scope = text[start_pos:start_pos + m_end.start()] if m_end else text[start_pos:]
    m = _ND_RANGE_RE.search(scope)
    if m:
        start = int(m.group(1))
        return start, _complete_abbrev_year(start, m.group(2))
    m = _ND_SINGLE_RE.search(scope)
    if m:
        y = int(m.group(1))
        return y, y
    return None


def parse_year_range(date_str: str | None) -> tuple[int | None, int | None]:
    if not date_str:
        return None, None
    nums = re.findall(r"\b(\d{4})\b", _normalise_year_string(date_str))
    if not nums:
        return None, None
    years = [int(n) for n in nums]
    return min(years), max(years)


def parse_dates_table(text: str, date_raw: str | None = None) -> list[int]:
    """Extract the per-year list from the «Value information in US Dollars» Date
    table. NumisMaster publishes individual mint years in this table (e.g.
    «Date 1632 / 1636 / 1642» for a coin whose Date range is 1632-1642),
    which is finer-grained than the Date range field. Returns sorted unique
    list of 4-digit years.

    The Value-information section is bounded by:
      - START: «Value information» marker
      - END: «Related coins» (NumisMaster lists OTHER coins of the same
        country / ruler in a sidebar that contains LOTS of years — must
        NOT bleed into our per-coin date list)

    A defensive year-window filter is applied using the Date-range field
    (parsed-page date_raw) when present: any year that falls outside
    [year_first-1, year_last+1] is dropped. This handles the rare case
    where the section boundary marker is missing on a malformed page.

    Pages occasionally use «(1)617» (century-abbreviation), so we run the
    same normaliser as parse_year_range before extracting tokens.
    """
    # Locate the section start
    m = re.search(r"\bValue information\b", text)
    if not m:
        return []
    # Capture everything between the marker and the «Related coins» sidebar.
    # Starting AT the marker (not past it) so the first year token — which
    # appears in the first row of the price table, immediately after the
    # column-header line «Date Mintage VG8 F12 …» — is included.
    tail = text[m.end():]
    end = re.search(
        r"\b(?:Related coins|Notes|Subscription|Back to|Permalink|"
        r"Tilbage til|Copyright|Connect with us|About Us)\b", tail,
    )
    if end:
        tail = tail[:end.start()]
    tail = _normalise_year_string(tail)
    # Year tokens — keep only plausible mint-year range (1500-1925)
    ys = {int(y) for y in re.findall(r"\b(1[5-9]\d{2})\b", tail) if 1500 <= int(y) <= 1925}

    # Defensive window filter: when the Date-range field is parseable, drop
    # any extracted year > 1 yr outside [year_first, year_last] — that's
    # almost certainly bleed-through from a Related-coins block that the
    # boundary regex above didn't catch (e.g. malformed page lacking the
    # standard end-marker).
    if date_raw and ys:
        yf, yl = parse_year_range(date_raw)
        if yf is not None and yl is not None:
            lo, hi = yf - 1, yl + 1
            ys = {y for y in ys if lo <= y <= hi}
    return sorted(ys)


def _clean_ruler(raw: str | None) -> str | None:
    """Strip trailing reign-year range («Friedrich 1729 - 1766» → «Friedrich»,
    «Christian III 0 -» → «Christian III»). Returns None for placeholder
    «(no Ruler Name) 0»."""
    if not raw:
        return None
    s = raw.strip()
    # Trailing « <NUM> - <NUM>» or « <NUM> -» reign annotation
    s = re.sub(r"\s+\d{1,4}\s*-\s*\d{0,4}\s*$", "", s)
    s = s.strip()
    if not s or s.startswith("(no Ruler Name)"):
        return None
    return s


def _clean_mint(raw: str | None) -> str | None:
    """Trim «N/A» (with optional trailing «Event: …» bleed-through) → None.
    For real mint values: drop bleed-in past «Event:», then strip the
    trailing « Mint» suffix («Husum Mint» → «Husum») since the place name
    is what we care about — the word «Mint» is a NumisMaster UI suffix,
    not part of the historical mint name."""
    if not raw:
        return None
    s = raw.strip()
    # «N/A Event: Death of …» — page lacked a real Mint value
    if s.upper().startswith("N/A"):
        return None
    # Trim post-«Event:» bleed-in (anchor-pull captured next field)
    m = re.split(r"\s+Event:\s+", s, maxsplit=1)
    s = m[0].strip()
    if not s or s.upper() == "N/A":
        return None
    # Strip trailing « Mint» suffix: «Husum Mint» → «Husum», «Copenhagen
    # Mint» → «Copenhagen», etc. Only the literal trailing word; an
    # embedded « Mint » in a multi-word mint name is left alone (none
    # observed, but defensive).
    s = re.sub(r"\s+Mint\s*$", "", s, flags=re.IGNORECASE).strip()
    return s or None


def parse_references(text: str) -> dict:
    """Extract cross-references from «General note» / page body. Catalogues
    covered: Schou (Sch#), Lange (L#), Friedberg (Fr#), Krause-Mishler (KM#),
    Madai-Bach (MB#), Sieg, Hede, Bruun, Schive (Norway), Davenport (Dav#).

    Each ref captures the FULL token sequence — range («358CI-358CIII») or
    comma-list («339, 339C») — as a single string. Downstream consumers can
    parse / explode the range / list as needed; we keep the source's
    transcription so the curator sees the same shape on the seed.
    """
    refs: dict = {}
    # Token-list helper: «<NUM>[<letter-suffix>]» possibly chained via
    # comma/dash with another «<NUM>[<letter-suffix>]». Greedy.
    _LIST_OR_RANGE = r"(\d+[A-Za-z]*(?:\s*[,\-/]\s*\d+[A-Za-z]*)*)"

    # Schou — «Sch#1357», «Sch. 1357», «Sch#1, 2»
    m = re.search(r"\bSch[#.]?\s*" + _LIST_OR_RANGE, text)
    if m:
        refs["schou"] = re.sub(r"\s+", "", m.group(1)).replace(",", ", ")
    # Lange — «L#23», «L#23, 23AB», «L#358CI-358CIII»
    m = re.search(r"\bL[#.]?\s*" + _LIST_OR_RANGE, text)
    if m:
        refs["lange"] = re.sub(r"\s+", "", m.group(1)).replace(",", ", ").replace("-", "-")
    # Friedberg — «Fr#16», «Fr. 16», «Fr#16, 17»
    m = re.search(r"\bFr\.?\s*#?\s*" + _LIST_OR_RANGE, text)
    if m:
        refs["friedberg"] = re.sub(r"\s+", "", m.group(1)).replace(",", ", ")
    # Krause-Mishler — «KM 75», «KM#75». KM rarely uses commas in NumisMaster
    # (single sub-num usually); kept on single-token regex to avoid catching
    # adjacent unrelated numbers.
    m = re.search(r"\bKM\s*#?\s*([\w\.]+)", text)
    if m and m.group(1) not in ("Mishler",):
        refs["km"] = m.group(1).rstrip(".,;")
    # Madai-Bach — «MB#33», «MB#A43» (pre-Krause SH duchy numbering)
    m = re.search(r"\bMB\s*#?\s*([A-Za-z]?\d+[A-Za-z]*)", text)
    if m:
        refs["mb"] = m.group(1)
    # Sieg — «Sieg 39», «Sieg#39», «Sieg#39, 40»
    m = re.search(r"\bSieg\s*#?\s*" + _LIST_OR_RANGE, text)
    if m:
        refs["sieg"] = re.sub(r"\s+", "", m.group(1)).replace(",", ", ").rstrip(".")
    # Hede — «Hede 39A», «Hede#39A», «Hede#39A, 39B»
    m = re.search(r"\bHede\s*#?\s*" + _LIST_OR_RANGE, text)
    if m:
        refs["hede"] = re.sub(r"\s+", "", m.group(1)).replace(",", ", ")
    # Bruun — «Bruun 8149»
    m = re.search(r"\bBruun\s*#?\s*(\d+[A-Za-z]?)", text)
    if m:
        refs["bruun"] = m.group(1)
    # Schive — Norwegian-specific «Schive XV.7-9» (preserve roman+arabic span)
    m = re.search(r"\bSchive\s+([IVXLCDM]+\.[\d\-,A-Za-z ]+?)(?:[;.]|\s*$)", text)
    if m:
        refs["schive"] = m.group(1).strip()
    # Davenport — «Dav#8235», «Dav. #8235», «Dav 8235»
    m = re.search(r"\bDav\.?\s*#?\s*(\d+[A-Za-z]?)", text)
    if m:
        refs["dav"] = m.group(1)
    return refs


def parse_obv_rev(text: str, side: str) -> dict:
    """Pull Obverse / Reverse: description + legend."""
    out: dict = {}
    m = re.search(
        rf"\b{side}\b\s+(.+?)(?=\b{side}\s*\(BW\)|\bObverse\s*\(BW\)|\bReverse\s*\(BW\)|\bCharacteristics|\bObverse|\bReverse|Details|$)",
        text,
        re.DOTALL,
    )
    if m:
        desc = m.group(1).strip()
        if 5 < len(desc) < 600:
            out["description"] = desc
    if side.lower() == "obverse":
        leg = re.search(r"Obv\.?\s*legend:\s*([^\n]+?)\s*(?:Rev|General|$)", text)
    else:
        leg = re.search(r"Rev\.?\s*legend:\s*([^\n]+?)\s*(?:Obv|General|$)", text)
    if leg:
        out["legend"] = leg.group(1).strip(" .")
    return out


def parse_page(html_path: Path, sub_scope: str) -> dict:
    html = html_path.read_text(encoding="utf-8")
    text = strip_tags(html)
    m = re.search(r"MC_(\d+)\.html", html_path.name)
    if not m:
        raise ValueError(f"Cannot extract MC_ID from {html_path.name}")
    mc = int(m.group(1))

    # Anchor extraction. NumisMaster page format is consistent across sub-scopes:
    # Country: X Catalog #: Y Political period: Z Coinage entity: W Denomination: D
    # Date: A - B Ruler: R Mint: M Characteristics ... Composition ... Mass ... Fineness
    # Actual weight ... Melt value ... Details ... General note ... Value information
    country = pull(text, "Country", "Catalog #") or pull(text, "Country", "Political period")
    catalog_no = pull(text, "Catalog #", "Political period")
    political = pull(text, "Political period", "Coinage entity")
    coinage = pull(text, "Coinage entity", "Denomination")
    denom = pull(text, "Denomination", "Date")
    date_raw = pull(text, "Date", "Ruler")
    ruler_raw = pull(text, "Ruler", "Mint")
    mint_raw = pull(text, "Mint", "Characteristics")

    composition = pull(text, "Composition", "Mass") or pull(text, "Composition", "Actual weight")
    mass_str = pull(text, "Mass", "Fineness") or pull(text, "Mass", "Actual weight")
    fineness_str = pull(text, "Fineness", "Actual weight")
    actual_weight_str = pull(text, "Actual weight", "Melt value")

    mass_g = None
    if mass_str:
        m_ = re.search(r"([\d.]+)\s*g", mass_str)
        if m_:
            try:
                mass_g = float(m_.group(1))
            except ValueError:
                pass
    fineness = None
    if fineness_str:
        m_ = re.search(r"(\.\d+|\d+\.\d+)", fineness_str)
        if m_:
            try:
                fineness = float(m_.group(1))
            except ValueError:
                pass
    actual_weight_fein = None
    if actual_weight_str:
        m_ = re.search(r"([\d.]+)", actual_weight_str)
        if m_:
            try:
                actual_weight_fein = float(m_.group(1))
            except ValueError:
                pass

    yf, yl = parse_year_range(date_raw)
    # An «ND(YYYY-YY)» display marker is AUTHORITATIVE over the structured «Date»
    # field, which NumisMaster unreliably collapses (ND(1618-22) → «1618 - 1618»,
    # or «1604 - 1604»). When present, it also flags the coin as UNDATED so the
    # seed builder can set year_verified: false (§4). Curator direction 2026-07-09.
    nd = extract_nd_range(text)
    undated = nd is not None
    if nd is not None:
        yf, yl = nd
    ruler = _clean_ruler(ruler_raw)
    mint = _clean_mint(mint_raw)

    # General note + refs. References live in either «General note: Ref. …» or as
    # standalone in the page body. Run parse_references against BOTH the general
    # note AND the catalog_number prefix (so an MB# or Dav# that lives only in
    # the Catalog # field is captured even when no General note is present).
    general_note = (
        pull(text, "General note", "Value information")
        or pull(text, "Details General note", "Value information")
    )
    ref_corpus_parts = [s for s in (general_note, catalog_no) if s]
    refs = parse_references("\n".join(ref_corpus_parts)) if ref_corpus_parts else {}

    # «Value information» Date table — per-year list (finer than the date range).
    # For an UNDATED («ND») coin the price-table dates are the SAME collapsed
    # attribution as the structured Date field (not real struck years), so we drop
    # them — the ND(…) marker's range (yf, yl) is the whole truth.
    dates_explicit = [] if undated else parse_dates_table(text, date_raw=date_raw)

    return {
        "source_file": html_path.name,
        "numismaster_id": mc,
        "url": f"https://numismaster.com/MC_{mc}",
        "sub_scope": sub_scope,
        "country": country,
        "catalog_number": catalog_no,
        "political_period": political,
        "coinage_entity": coinage,
        "denomination": denom,
        "date_raw": date_raw,
        "year_first": yf,
        "year_last": yl,
        "undated": undated,
        "dates_explicit": dates_explicit,
        "ruler": ruler,
        "mint": mint,
        "composition": composition,
        "mass_g": mass_g,
        "fineness": fineness,
        "actual_weight_fein": actual_weight_fein,
        "obverse": parse_obv_rev(text, "Obverse"),
        "reverse": parse_obv_rev(text, "Reverse"),
        "general_note": general_note,
        "catalog_refs": refs,
        "parsed_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }


def parse_sub_scope(sub_scope: str, force: bool) -> tuple[int, int, int]:
    """Walk one sub-scope cache dir; parse every MC_<N>.html → MC_<N>.parsed.json.
    Returns (parsed, skipped, failed)."""
    cache_dir = NUMISMASTER_CACHE / sub_scope
    if not cache_dir.exists():
        print(f"  [{sub_scope}] cache dir not found — skipping", file=sys.stderr)
        return 0, 0, 0
    files = sorted(cache_dir.glob("MC_*.html"))
    if not files:
        print(f"  [{sub_scope}] no MC_*.html files — skipping")
        return 0, 0, 0
    parsed = skipped = failed = 0
    for path in files:
        json_path = path.with_name(path.stem + ".parsed.json")
        if json_path.exists() and not force:
            skipped += 1
            continue
        try:
            data = parse_page(path, sub_scope)
            json_path.write_text(json.dumps(data, indent=2, ensure_ascii=False))
            parsed += 1
        except Exception as e:
            print(f"  [{sub_scope}/{path.name}] {type(e).__name__}: {e}", file=sys.stderr)
            failed += 1
    print(f"  [{sub_scope}] parsed: {parsed}, skipped: {skipped}, failed: {failed}")
    return parsed, skipped, failed


def main() -> int:
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--sub-scope", choices=KNOWN_SUB_SCOPES,
                   help="Parse one specific sub-scope directory")
    g.add_argument("--all", action="store_true",
                   help="Parse every known sub-scope directory")
    ap.add_argument("--force", action="store_true",
                    help="Re-parse files even if MC_<N>.parsed.json already exists")
    args = ap.parse_args()

    scopes = list(KNOWN_SUB_SCOPES) if args.all else [args.sub_scope]
    totals = [0, 0, 0]
    for scope in scopes:
        p, s, f = parse_sub_scope(scope, args.force)
        totals[0] += p
        totals[1] += s
        totals[2] += f
    print(f"\nTotal: parsed={totals[0]}, skipped={totals[1]}, failed={totals[2]}")
    return 0 if totals[2] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
