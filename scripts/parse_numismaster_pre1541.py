"""§AZ Tier 4 — parse NumisMaster MC_NNNNN pages into structured JSON.

Per-coin URL pattern: https://numismaster.com/MC_<N> renders full
catalog data for pre-1541 Schleswig-Holstein-as-duchy entries (the
Holstein-Gottorp-Rendsborg id=-10012282 search-result page surfaces
3 MB_-numbered entries in the 1514-1541 window per Chrome MCP browse
2026-05-16; full sub-territory walk left for future enrichment).

Each `scripts/cache/numismaster/denmark_pre_1541/MC_<N>.html` →
sibling `MC_<N>.json` with:
  - country, catalog_number, political_period, coinage_entity
  - denomination, year_first, year_last, ruler, mint
  - composition (metal), mass_g, fineness, actual_weight_fein
  - obverse / reverse descriptions + legend transcriptions
  - cross-references parsed from «General note» / «Ref.»

Run:
    .venv/bin/python scripts/parse_numismaster_pre1541.py [--force]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from html import unescape
from pathlib import Path

CACHE_DIR = Path(__file__).resolve().parent / "cache" / "numismaster" / "denmark_pre_1541"

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


def parse_year_range(date_str: str | None) -> tuple[int | None, int | None]:
    if not date_str:
        return None, None
    nums = re.findall(r"\b(\d{4})\b", date_str)
    if not nums:
        return None, None
    years = [int(n) for n in nums]
    return min(years), max(years)


def parse_references(text: str) -> dict:
    """References live in «General note: Ref. Sch#1357; L#23, 23AB.» / «Fr. #16.» style strings.

    Catalog catalogues encountered:
      - Sch# (Schou) — 1357 etc.
      - L# (Lange) — 23, 23AB
      - Fr. # (Friedberg) — 16
      - cf KM# (Krause-Mishler) — appears occasionally on patterns
    """
    refs: dict = {}
    # Schou
    m = re.search(r"Sch[#.]?\s*(\d+[A-Za-z]?)", text)
    if m:
        refs["schou"] = m.group(1)
    # Lange
    m = re.search(r"\bL[#.]?\s*(\d+[A-Za-z, ]*\d?[A-Za-z]?)", text)
    if m:
        refs["lange"] = m.group(1).strip(", ")
    # Friedberg
    m = re.search(r"Fr\.?\s*#?\s*(\d+[a-zA-Z]?)", text)
    if m:
        refs["friedberg"] = m.group(1)
    # Krause-Mishler
    m = re.search(r"\bKM\s*#?\s*(\w+)", text)
    if m and m.group(1) not in ("Mishler",):
        refs["km"] = m.group(1)
    return refs


def parse_obv_rev(text: str, side: str) -> dict:
    """Pull Obverse / Reverse: description + Obv/Rev legend."""
    out: dict = {}
    # Description after «Obverse» / «Reverse» until «Obverse (BW)» / etc.
    m = re.search(
        rf"\b{side}\b\s+(.+?)(?=\b{side}\s*\(BW\)|\bObverse\s*\(BW\)|\bReverse\s*\(BW\)|\bCharacteristics|\bObverse|\bReverse|Details|$)",
        text,
        re.DOTALL,
    )
    if m:
        desc = m.group(1).strip()
        if 5 < len(desc) < 600:
            out["description"] = desc
    # Legend
    if side.lower() == "obverse":
        leg = re.search(r"Obv\.?\s*legend:\s*([^\n]+?)\s*(?:Rev|General|$)", text)
    else:
        leg = re.search(r"Rev\.?\s*legend:\s*([^\n]+?)\s*(?:Obv|General|$)", text)
    if leg:
        out["legend"] = leg.group(1).strip(" .")
    return out


def parse_page(html_path: Path) -> dict:
    html = html_path.read_text(encoding="utf-8")
    text = strip_tags(html)
    mc = int(re.search(r"MC_(\d+)\.html", html_path.name).group(1))

    # Anchor extraction: Country: X Catalog #: Y Political period: Z Coinage entity: W Denomination: D Date: A - B Ruler: R Mint: M
    country = pull(text, "Country", "Catalog #") or pull(text, "Country", "Political period")
    catalog_no = pull(text, "Catalog #", "Political period")
    political = pull(text, "Political period", "Coinage entity")
    coinage = pull(text, "Coinage entity", "Denomination")
    denom = pull(text, "Denomination", "Date")
    date_raw = pull(text, "Date", "Ruler")
    ruler = pull(text, "Ruler", "Mint")
    mint = pull(text, "Mint", "Characteristics")

    composition = pull(text, "Composition", "Mass") or pull(text, "Composition", "Actual weight")
    mass_str = pull(text, "Mass", "Fineness") or pull(text, "Mass", "Actual weight")
    fineness_str = pull(text, "Fineness", "Actual weight")
    actual_weight_str = pull(text, "Actual weight", "Melt value")

    mass_g = None
    if mass_str:
        m = re.search(r"([\d.]+)\s*g", mass_str)
        if m:
            mass_g = float(m.group(1))
    fineness = None
    if fineness_str:
        m = re.search(r"(\.\d+|\d+\.\d+)", fineness_str)
        if m:
            fineness = float(m.group(1))
    actual_weight_fein = None
    if actual_weight_str:
        m = re.search(r"([\d.]+)", actual_weight_str)
        if m:
            try:
                actual_weight_fein = float(m.group(1))
            except ValueError:
                pass

    yf, yl = parse_year_range(date_raw)

    # Clean ruler: «Christian III 0 -» → «Christian III»; «Friedrich I 0 -» → «Friedrich I»
    if ruler:
        ruler = re.sub(r"\s*\d+\s*-\s*$", "", ruler).strip()
        if ruler == "(no Ruler Name) 0":
            ruler = None

    # Mint: «N/A» → None
    if mint and mint.upper() == "N/A":
        mint = None

    # General note + refs
    general_note = pull(text, "General note", "Value information") or pull(text, "Details General note", "Value information")
    refs = parse_references(general_note or text)

    return {
        "source_file": html_path.name,
        "numismaster_id": mc,
        "url": f"https://numismaster.com/MC_{mc}",
        "country": country,
        "catalog_number": catalog_no,
        "political_period": political,
        "coinage_entity": coinage,
        "denomination": denom,
        "date_raw": date_raw,
        "year_first": yf,
        "year_last": yl,
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
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()
    files = sorted(CACHE_DIR.glob("MC_*.html"))
    if not files:
        print(f"No MC_*.html in {CACHE_DIR}", file=sys.stderr)
        return 1
    parsed = skipped = failed = 0
    for path in files:
        json_path = path.with_suffix(".json")
        if json_path.exists() and not args.force:
            skipped += 1
            continue
        try:
            data = parse_page(path)
            json_path.write_text(json.dumps(data, indent=2, ensure_ascii=False))
            parsed += 1
        except Exception as e:
            print(f"  [{path.name}] {type(e).__name__}: {e}", file=sys.stderr)
            failed += 1
    print(f"Parsed: {parsed}, skipped: {skipped}, failed: {failed}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
