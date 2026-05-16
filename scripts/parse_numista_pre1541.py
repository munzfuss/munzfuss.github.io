"""Parse cached Numista HTML pages (1514-1541 Denmark sub-window) into
structured JSON sidecars.

Input: scripts/cache/numista/denmark_pre_1541/n<N#>.html (fetched by
scripts/fetch_numista_pre1541.py).
Output: sibling n<N#>.json.

Extracts:
  * Numista N# + URL + title
  * Issuer, ruler(s), type, years, value, currency
  * Composition (metal + fineness), weight (brutto), diameter, shape,
    technique, orientation, demonetization
  * Cross-references (SIEG, Schou, Fr, Galster, Hede, MB, Lange, Dav,
    N#) with raw tokens
  * Obverse + Reverse: description, script, lettering, translation
  * Photo credit (copyright line)
  * Mint (when in title or description)
  * Comments
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from html import unescape
from pathlib import Path

CACHE_DIR = Path(__file__).resolve().parent / "cache" / "numista" / "denmark_pre_1541"

_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")


def strip_tags(html: str) -> str:
    """HTML → plain text (basic)."""
    txt = _TAG_RE.sub(" ", html)
    txt = unescape(txt)
    txt = txt.replace("\xa0", " ")
    txt = _WS_RE.sub(" ", txt)
    return txt.strip()


def extract_feature(html: str, label: str) -> str | None:
    """Pull <th>label</th><td>value</td> from Features table."""
    pattern = (
        r"<th>\s*" + re.escape(label) + r"\s*</th>\s*<td>(.*?)</td>"
    )
    m = re.search(pattern, html, re.DOTALL)
    if not m:
        return None
    val = strip_tags(m.group(1)).strip()
    return val if val else None


def parse_kings(html: str) -> list[dict]:
    """King field can have multiple entries (e.g. «Christian II / Christian III»)."""
    m = re.search(r"<th>\s*King\s*</th>\s*<td>(.*?)</td>", html, re.DOTALL)
    if not m:
        return []
    block = m.group(1)
    kings: list[dict] = []
    for km in re.finditer(
        r'<a\s+href="/catalogue/ruler\.php\?id=(\d+)"[^>]*>\s*([^<]+?)\s*<span[^>]*>\(<em>([^<]+?)</em>\)\s*</span>',
        block,
        re.DOTALL,
    ):
        # Collapse whitespace runs (Numista pads king names with many spaces)
        name = re.sub(r"\s+", " ", km.group(2)).strip()
        # Strip parenthesised native form e.g. "Frederick I (Frederik I)" → "Frederick I"
        name = re.sub(r"\s*\([^)]+\)\s*$", "", name)
        kings.append({
            "id": int(km.group(1)),
            "name": name,
            "reign": km.group(3).strip(),
        })
    return kings


def parse_composition(html: str) -> dict:
    """Parse «Billon (.250 silver)» / «Gold (.986)» / «Silver (.875)» / «Gold»."""
    raw = extract_feature(html, "Composition")
    if not raw:
        return {}
    out: dict = {"raw": raw}
    # Detect metal
    if "gold" in raw.lower():
        out["metal"] = "gold"
    elif "billon" in raw.lower():
        out["metal"] = "billon"
    elif "silver" in raw.lower():
        out["metal"] = "silver"
    elif "copper" in raw.lower():
        out["metal"] = "copper"
    else:
        out["metal"] = "unknown"
    # Fineness in parens: (.986) or (.250 silver)
    fm = re.search(r"\(\.(\d+)", raw)
    if fm:
        out["fineness"] = float("0." + fm.group(1))
    return out


def parse_weight(html: str) -> float | None:
    raw = extract_feature(html, "Weight")
    if not raw:
        return None
    m = re.search(r"([\d.]+)", raw.replace(",", "."))
    return float(m.group(1)) if m else None


def parse_diameter(html: str) -> float | None:
    raw = extract_feature(html, "Diameter")
    if not raw:
        return None
    m = re.search(r"([\d.]+)", raw.replace(",", "."))
    return float(m.group(1)) if m else None


def parse_references(html: str) -> dict:
    """References can be «SIEG# C2-1, MB# 45, Fr# 11, Galster UU# 46».
    Each `<a>NAME</a>#&#8239;VALUE` pair."""
    m = re.search(r"<th>\s*References\s*</th>\s*<td>(.*?)</td>", html, re.DOTALL)
    if not m:
        return {}
    block = m.group(1)
    refs: dict = {}
    # Pattern: <a ...>SIEG</a>#&#8239;VALUE  OR  <a ...>Galster UU</a>#&#8239;VALUE
    for am in re.finditer(
        r'<a[^>]+class="fiche_catalogue"[^>]*>([^<]+)</a>#(?:&nbsp;|&#8239;|\s)*([^<,]+?)(?=,|<|$)',
        block,
    ):
        name = am.group(1).strip()
        value = am.group(2).strip().rstrip(",;.")
        key = name.lower().replace(" ", "_").replace("/", "_")
        # Normalise specific known catalogues
        if key in ("sieg",):
            refs["sieg"] = value
        elif key == "mb":
            refs["mb"] = value
        elif key in ("fr", "friedberg"):
            refs["friedberg"] = value
        elif key in ("galster", "galster_uu"):
            refs["galster"] = value
        elif key == "hede":
            refs["hede"] = value
        elif key == "schou":
            refs["schou"] = value
        elif key == "lange":
            refs["lange"] = value
        elif key in ("dav", "dav_ec_i"):
            refs["davenport"] = value
        elif key == "schive":
            refs["schive"] = value
        elif key in ("kmd", "km"):
            refs["km"] = value
        else:
            refs[key] = value
    return refs


def parse_obv_rev(html: str, side: str) -> dict:
    """Pull Obverse / Reverse block: description, script, lettering, translation."""
    out: dict = {}
    # Find the h3 block + its content until the next h3
    pat = rf"<h3>\s*{side}\s*</h3>(.*?)(?:<h3>|<h2>|<div\s+id=\"fiche_comments\"|<h4>\s*Mint)"
    m = re.search(pat, html, re.DOTALL | re.IGNORECASE)
    if not m:
        return out
    block = m.group(1)
    # First <p> is the description
    pm = re.search(r"<p>(.*?)</p>", block, re.DOTALL)
    if pm:
        desc = strip_tags(pm.group(1)).strip()
        if desc and not desc.startswith("Lettering"):
            out["description"] = desc
    # Script: usually on its own line
    sm = re.search(r"Script[:\s]+([A-Za-z()\s]+?)(?:Lettering|Translation|$)", strip_tags(block))
    if sm:
        out["script"] = sm.group(1).strip()
    # Lettering — multiple Lettering blocks (regular + uncial); take first
    lm = re.search(r"<strong>\s*Lettering\s*[:]?\s*</strong>\s*(?:<br\s*/?>)?\s*([^<]+)", block)
    if not lm:
        # alt pattern
        lm = re.search(r"Lettering[:\s]+([^\n\r<]+?)(?:Translation|Script|$)", strip_tags(block))
    if lm:
        out["lettering"] = lm.group(1).strip()
    # Translation
    tm = re.search(r"<strong>\s*Translation\s*[:]?\s*</strong>\s*(?:<br\s*/?>)?\s*([^<]+)", block)
    if not tm:
        tm = re.search(r"Translation[:\s]+([^\n\r<]+?)(?:Lettering|Script|$)", strip_tags(block))
    if tm:
        out["translation"] = tm.group(1).strip()
    return out


def parse_mint(html: str, title: str | None) -> str | None:
    """Pull mint either from <h4>Mint</h4> block or from title (mint).
    Title pattern: «<denom> - <ruler> (<mint>; details)»."""
    # H4 Mint block
    m = re.search(r"<h4>\s*Mint\s*</h4>\s*<p>(.*?)</p>", html, re.DOTALL)
    if m:
        val = strip_tags(m.group(1)).strip()
        # «Malmö, Scania, Sweden» — take first comma-separated part
        return val.split(",")[0].strip()
    # Try title parens
    if title:
        tm = re.search(r"\(([A-Za-zÆØÅæøåö]+)(?:[;,)])", title)
        if tm and tm.group(1) not in ("first", "second", "type", "first type", "second type", "ND"):
            return tm.group(1)
    return None


def parse_title(html: str) -> str | None:
    """Pull page title (denomination + ruler + variant)."""
    m = re.search(r"<title>\s*([^<]+?)\s*</title>", html)
    if not m:
        return None
    t = unescape(m.group(1))
    # Strip « - Denmark – Numista» suffix (incl. unescaped –)
    t = re.sub(r"\s*[-–]\s*(?:Denmark|Norway)\s*[-–]\s*Numista\s*$", "", t)
    return t.strip()


def parse_photo_credit(html: str) -> str | None:
    """Photo credit can be in alt text or comment near image."""
    # Pattern: ©&nbsp;Source (License)
    m = re.search(r"©\s*([^<\n(]+?)\s*\(([^)]+)\)", strip_tags(html))
    if m:
        return f"{m.group(1).strip()} ({m.group(2).strip()})"
    return None


def parse_year_range(html: str) -> tuple[int | None, int | None]:
    """Pull year range from Years field."""
    raw = extract_feature(html, "Years") or extract_feature(html, "Year")
    if not raw:
        return None, None
    years = [int(m) for m in re.findall(r"\b(1[5-6]\d{2})\b", raw)]
    if not years:
        return None, None
    return min(years), max(years)


def parse_value(html: str) -> dict | None:
    """Value field: «2 Penning (1⁄288)»."""
    raw = extract_feature(html, "Value")
    if not raw:
        return None
    out = {"raw": raw}
    fm = re.search(r"\((\d+)\s*[⁄/]\s*(\d+)\)", raw)
    if fm:
        out["numerator"] = int(fm.group(1))
        out["denominator"] = int(fm.group(2))
    return out


def parse_page(html_path: Path) -> dict:
    html = html_path.read_text(encoding="utf-8")
    nid = int(re.search(r"n(\d+)\.html", html_path.name).group(1))

    title = parse_title(html)
    kings = parse_kings(html)
    year_first, year_last = parse_year_range(html)
    composition = parse_composition(html)

    out: dict = {
        "source_file": html_path.name,
        "numista_id": nid,
        "url": f"https://en.numista.com/{nid}",
        "title": title,
        "issuer": extract_feature(html, "Issuer"),
        "kings": kings,
        "type_": extract_feature(html, "Type"),
        "year_first": year_first,
        "year_last": year_last,
        "years_raw": extract_feature(html, "Years"),
        "value": parse_value(html),
        "currency": extract_feature(html, "Currency"),
        "composition": composition,
        "weight_g": parse_weight(html),
        "diameter_mm": parse_diameter(html),
        "shape": extract_feature(html, "Shape"),
        "technique": extract_feature(html, "Technique"),
        "orientation": extract_feature(html, "Orientation"),
        "demonetized": extract_feature(html, "Demonetized"),
        "rarity_index": None,
        "references": parse_references(html),
        "obverse": parse_obv_rev(html, "Obverse"),
        "reverse": parse_obv_rev(html, "Reverse"),
        "mint": parse_mint(html, title),
        "photo_credit": parse_photo_credit(html),
    }
    # Rarity index
    rm = re.search(r"Numista Rarity index:\s*(\d+)", strip_tags(html))
    if rm:
        out["rarity_index"] = int(rm.group(1))
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()
    html_files = sorted(CACHE_DIR.glob("n*.html"))
    if not html_files:
        print(f"No HTML files in {CACHE_DIR}. Run fetch_numista_pre1541.py first.", file=sys.stderr)
        return 1
    parsed = skipped = failed = 0
    for path in html_files:
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
