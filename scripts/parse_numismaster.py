"""§BK NumisMaster Phase 5 — parse cached MC_<N>.html → MC_<N>.parsed.json.

General-purpose parser (renamed from `parse_numismaster_pre1541.py`). Takes any
sub-scope directory under `scripts/cache/numismaster/<sub_scope>/`, walks every
`MC_*.html`, writes a sibling `MC_<N>.parsed.json` with the structured field
extraction. Idempotent — re-run skips already-parsed files unless `--force`.

Sub-scope directories:
  schleswig_holstein/   — §BJ SH cluster (~561 MCs, all in mission scope)
  denmark/              — §BJ Denmark (~987 MCs ≤ 1914)
  norway/               — §BJ Norway (~344 MCs ≤ 1814 Danish-rule era)
  denmark_pre_1541/     — §AZ legacy (3 MCs); kept for backwards compat

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
    "denmark_pre_1541",   # §AZ legacy
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


def parse_year_range(date_str: str | None) -> tuple[int | None, int | None]:
    if not date_str:
        return None, None
    nums = re.findall(r"\b(\d{4})\b", date_str)
    if not nums:
        return None, None
    years = [int(n) for n in nums]
    return min(years), max(years)


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
    For real mint values, drop any bleed-in past «Event:» if present."""
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
    return s


def parse_references(text: str) -> dict:
    """Extract cross-references from «General note» / page body. Catalogues
    covered: Schou (Sch#), Lange (L#), Friedberg (Fr#), Krause-Mishler (KM#),
    Madai-Bach (MB#), Sieg, Hede, Bruun, Schive (Norway).
    """
    refs: dict = {}
    # Schou — «Sch#1357» / «Sch. 1357»
    m = re.search(r"\bSch[#.]?\s*(\d+[A-Za-z]?)", text)
    if m:
        refs["schou"] = m.group(1)
    # Lange — «L#23», «L#23, 23AB»
    m = re.search(r"\bL[#.]?\s*(\d+[A-Za-z, ]*\d?[A-Za-z]?)", text)
    if m:
        refs["lange"] = m.group(1).strip(", ")
    # Friedberg — «Fr#16», «Fr. 16»
    m = re.search(r"\bFr\.?\s*#?\s*(\d+[a-zA-Z]?)", text)
    if m:
        refs["friedberg"] = m.group(1)
    # Krause-Mishler — «KM 75», «KM#75»
    m = re.search(r"\bKM\s*#?\s*([\w\.]+)", text)
    if m and m.group(1) not in ("Mishler",):
        refs["km"] = m.group(1).rstrip(".,;")
    # Madai-Bach — «MB#33» (pre-Krause SH duchy numbering)
    m = re.search(r"\bMB\s*#?\s*(\d+[A-Za-z]?)", text)
    if m:
        refs["mb"] = m.group(1)
    # Sieg — «Sieg 39» / «Sieg#39»
    m = re.search(r"\bSieg\s*#?\s*(\d+[A-Za-z.]?)", text)
    if m:
        refs["sieg"] = m.group(1).rstrip(".")
    # Hede — «Hede 39A» / «Hede#39A»
    m = re.search(r"\bHede\s*#?\s*(\d+[A-Za-z]?)", text)
    if m:
        refs["hede"] = m.group(1)
    # Bruun — «Bruun 8149» (rare in NumisMaster, common in auction notes)
    m = re.search(r"\bBruun\s*#?\s*(\d+[A-Za-z]?)", text)
    if m:
        refs["bruun"] = m.group(1)
    # Schive — Norwegian-specific «Schive XV.7-9» (preserve roman+arabic span)
    m = re.search(r"\bSchive\s+([IVXLCDM]+\.[\d\-,A-Za-z ]+?)(?:[;.]|\s*$)", text)
    if m:
        refs["schive"] = m.group(1).strip()
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
    ruler = _clean_ruler(ruler_raw)
    mint = _clean_mint(mint_raw)

    # General note + refs. References live in either «General note: Ref. …» or as
    # standalone in the page body.
    general_note = (
        pull(text, "General note", "Value information")
        or pull(text, "Details General note", "Value information")
    )
    refs = parse_references(general_note or text)

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
