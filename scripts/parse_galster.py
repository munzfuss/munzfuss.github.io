"""Parse cached Galster HTML pages from danskmoent.dk into structured JSON.

Each ``scripts/cache/danskmoent/galster/<basename>.htm`` is parsed
into a sibling ``<basename>.json`` capturing:

  * Identity — ruler, Galster number, nominal, mint, year (or year-range).
  * Description — Forside / bagside / randskrift (obv / rev / edge).
  * Catalog refs cited inline: Galster N, Schou N, Schive (Norge),
    Sømod, Jensen/Skjoldager (T-/N-/F-/S-/L- prefixes).
  * Specs — Bruttovægt, Finhed, Finvægt; mintage count if cited.
  * Inscription quote + translation (when present).
  * Litteratur — bibliography references (Ernst NN&Aring;, Jensen-
    Skjoldager «Tronraneren» 2021, Galster's own articles, etc.).
  * Raw text — kept as fallback for downstream consumers.

Run::

    .venv/bin/python scripts/parse_galster.py [--force]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from html import unescape
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib.paths import GALSTER_CACHE as CACHE_DIR  # noqa: E402

# Strip HTML tags but preserve <HR> as a section-break sentinel so the
# parser can locate the «before-specs vs after-specs» boundary.
_HR_SENTINEL = "§§HR§§"
_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"[ \t]+")


def _normalise_text(html: str) -> str:
    """HTML → plain text, preserving section breaks via sentinel."""
    text = re.sub(r"<HR[^>]*>", f"\n{_HR_SENTINEL}\n", html, flags=re.IGNORECASE)
    text = re.sub(r"<BR[^>]*>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<P[^>]*>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<LI[^>]*>", "\n• ", text, flags=re.IGNORECASE)
    text = re.sub(r"<H\d[^>]*>", "\n## ", text, flags=re.IGNORECASE)
    text = re.sub(r"</H\d>", "\n", text, flags=re.IGNORECASE)
    text = _TAG_RE.sub(" ", text)
    text = unescape(text)
    text = _WS_RE.sub(" ", text)
    text = re.sub(r"\n\s*\n+", "\n\n", text)
    return text.strip()


def _parse_header_h1(text: str) -> dict:
    """The H1 line carries ruler + denomination + year + sometimes mint.

    Typical shapes (real samples from cache):
      «Frederik 1., 1 Ungersk gylden 1531»
      «Christian 2., 1 Nobel, Malmø 1516 (RRR), 1518 (RRR)»
      «Christian 3., 2 Mark 1535»
      «Frederik 1., 1 Mark 1514, Husum»
    """
    out: dict = {}
    # Pick the FIRST H1 that contains a ruler keyword — H2/H3 sections
    # ('KMMS', 'Eksemplar fra Zincksamlingen:') would otherwise win.
    h1_lines = re.findall(r"##\s*([^\n]+)", text)
    if not h1_lines:
        return out
    h1 = None
    for cand in h1_lines:
        if re.match(r"(Christian|Frederik|Hans|Margrethe|Erik|Olav|Olaf)\s+\d", cand):
            h1 = cand.strip()
            break
    if h1 is None:
        h1 = h1_lines[0].strip()
    out["h1"] = h1

    # Year sometimes lives on the line BELOW the H1 (e.g. c2g37: «1516 (RRR), 1518 (RRR). Forside: ...»)
    body_idx = text.find(h1)
    body_after = text[body_idx + len(h1):body_idx + len(h1) + 200] if body_idx >= 0 else ""

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

    # First, strip rarity-flag noise so year detection works on clean text
    rest_clean = re.sub(r"\s*\([RU][RRSU]*\)", "", rest)
    rest_clean = re.sub(r"\s+", " ", rest_clean).strip()

    # Extract year(s) — accepts «1531», «1516, 1518», «1535-1540», «u.år», «ND»
    # Try H1 first, then body_after (next 200 chars) as fallback
    year_tokens = re.findall(r"(?<!\d)1[5-6]\d{2}(?:[-–]\d{4})?(?!\d)", rest_clean)
    if not year_tokens:
        # Strip rarity flags from body_after too before search
        body_clean = re.sub(r"\s*\([RU][RRSU]*\)", "", body_after)
        year_tokens = re.findall(r"(?<!\d)1[5-6]\d{2}(?:[-–]\d{4})?(?!\d)", body_clean[:150])
    if year_tokens:
        out["year_label"] = ", ".join(year_tokens)
        # Strip years from rest for cleaner denomination
        for yt in year_tokens:
            rest_clean = rest_clean.replace(yt, "")
    elif re.search(r"u\.\s*[åA]r|ND", rest_clean):
        out["year_label"] = "u.år"
        rest_clean = re.sub(r"u\.\s*[åA]r|ND", "", rest_clean)

    # Clean up trailing commas and «Malmø,» style mint-mention
    rest_clean = re.sub(r"\s*,\s*$", "", rest_clean).strip(" ,.")

    # Try to peel off a trailing mint name from denomination — this allows
    # both denomination and mint to be retained
    mint_pattern = re.search(
        r"[, ]+(København|Kobenhavn|Malmø|Malmö|Malmo|Husum|Gottorp|Roskilde|"
        r"Aarhus|Ribe|Bergen|Oslo|Visby|Stockholm|Flensborg|Landskrona|"
        r"Helsingør|Lund)\s*$",
        rest_clean,
        re.IGNORECASE,
    )
    if mint_pattern:
        out["mint_from_h1"] = mint_pattern.group(1)
        rest_clean = rest_clean[: mint_pattern.start()].rstrip(", .")

    out["denomination"] = rest_clean.strip(", .")
    return out


def _parse_mint_line(text: str) -> str | None:
    """The line after H1 typically has the mint."""
    # Mint is on a short line after the H1, before «Forside:».
    m = re.search(
        r"(København|Kobenhavn|Malmø|Malmö|Malmo|Husum|Gottorp|Roskilde|Aarhus|"
        r"Ribe|Bergen|Oslo|Visby|Stockholm|Flensborg|Landskrona|Helsingør|Lund|"
        r"Kalundborg|Kgs\.\s*Lyngby)\s*(?:eller\s+([A-Za-zÆØÅæøå]+))?",
        text,
    )
    if m:
        primary = m.group(1)
        alt = m.group(2)
        return f"{primary} eller {alt}" if alt else primary
    return None


def _parse_description_and_refs(text: str) -> tuple[str | None, dict]:
    """Description block carries «Forside: ... bagside: ... (Galster N, Schou M, ...)».

    Returns (description_text, catalog_refs_dict).
    """
    refs: dict = {}
    desc = None
    m = re.search(r"Forside:\s*(.*?)(?:\n\n|" + _HR_SENTINEL + ")", text, re.DOTALL)
    if m:
        desc = m.group(1).strip()
        # Extract refs in parentheses
        for pm in re.finditer(r"\(([^)]+)\)", desc):
            for chunk in re.split(r",\s*", pm.group(1)):
                chunk = chunk.strip()
                # «Galster 46» / «Schou 1» / «Jensen/Skjoldager T-41/45» / «Schive XV.7-9»
                rm = re.match(
                    r"(Galster|Schou|Sieg|Hede|Sømod|Schive|Lange|Friedberg|Fr\.|Fr|"
                    r"Jensen[/ ]?Skjoldager|Delzanno|Lott|MB|NMD|MNI|Aagaard)\s*([0-9IVXLA-Z./\-]+)",
                    chunk,
                    re.IGNORECASE,
                )
                if rm:
                    key = rm.group(1).lower().replace("/", "_").replace(" ", "_").replace(".", "")
                    if key == "fr":
                        key = "friedberg"
                    if key.startswith("jensen"):
                        key = "jensen_skjoldager"
                    refs[key] = rm.group(2).strip()
    return desc, refs


_SPEC_PATTERNS = [
    (r"Bruttov[æe]gt:\s*([\d.,]+)\s*g", "bruttovaegt_g"),
    (r"Finhed:\s*([\d.,]+|\d+\s*[KkLl]od|\d+\s*K(?:arat)?(?:\s*\d+\s*[Gg]r[äa]n)?)", "finhed"),
    (r"Finv[æe]gt:\s*([\d.,]+)\s*g", "finvaegt_g"),
    (r"Diameter:\s*([\d.,]+)\s*mm", "diameter_mm"),
]


def _parse_specs(text: str) -> dict:
    """Pull the spec block (between two <HR> sentinels typically)."""
    specs: dict = {}
    for pat, key in _SPEC_PATTERNS:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            val = m.group(1).replace(",", ".").strip()
            try:
                specs[key] = float(val) if key.endswith(("_g", "_mm")) or key == "finhed" else val
            except ValueError:
                specs[key] = m.group(1).strip()
    # Mintage count: «1.234 stk.» or «1.234 styk»
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
    m = re.search(r"Litteratur:\s*\n(.*?)(?:" + _HR_SENTINEL + r"|Tilbage til|$)", text, re.DOTALL)
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


def parse_page(html_path: Path) -> dict:
    """Parse a single Galster page into structured data."""
    html = html_path.read_text(encoding="utf-8", errors="replace")
    text = _normalise_text(html)

    header = _parse_header_h1(text)
    # H1 mint takes priority over body-line mint
    mint = header.get("mint_from_h1") or _parse_mint_line(text)
    desc, refs = _parse_description_and_refs(text)
    specs = _parse_specs(text)
    litt = _parse_litteratur(text)
    inscription = _parse_inscription(text)

    out: dict = {
        "source_file": html_path.name,
        "source_url_hint": (
            "https://www.danskmoent.dk/" + html_path.name.replace("_", "/")
        ),
        "ruler": header.get("ruler"),
        "denomination": header.get("denomination"),
        "year_label": header.get("year_label"),
        "mint": mint,
        "description": desc,
        "catalog_refs": refs,
        "specs": specs,
        "inscription": inscription,
        "litteratur": litt,
        "raw_text_excerpt": text[:2000],
    }
    # Extract galster_number from filename pattern: chr_c2g37.htm → 37
    fm = re.search(r"_(c|f)\d+g(\d+\w*)\.htm$", html_path.name)
    if fm:
        out["galster_number"] = fm.group(2)
    # Norway sub-series: norge_nc2g164.htm
    fm2 = re.search(r"^norge_n(c|f)\d+g(\d+\w*)\.htm$", html_path.name)
    if fm2:
        out["galster_number"] = fm2.group(2)
        out["sub_realm"] = "norway"
    # Page-level reign tag
    if html_path.name.startswith("chr_c2"):
        out["ruler_volume"] = "c2g"
    elif html_path.name.startswith("chr_c3"):
        out["ruler_volume"] = "c3g"
    elif html_path.name.startswith("fr_f1"):
        out["ruler_volume"] = "f1g"
    elif html_path.name.startswith("norge_"):
        # norge_nc2g* → c2g sub-realm norway
        m = re.match(r"norge_n(c\d|f\d)g", html_path.name)
        if m:
            out["ruler_volume"] = m.group(1) + "g"
            out["sub_realm"] = "norway"
    return out


def parse_all(force: bool = False) -> None:
    """Parse every cached .htm and write sibling .json."""
    html_files = sorted(CACHE_DIR.glob("*.htm"))
    if not html_files:
        print(f"No HTML files in {CACHE_DIR}. Run fetch_galster.py first.", file=sys.stderr)
        sys.exit(1)
    parsed = 0
    skipped = 0
    failed = 0
    for path in html_files:
        json_path = path.with_suffix(".json")
        if json_path.exists() and not force:
            skipped += 1
            continue
        try:
            data = parse_page(path)
            json_path.write_text(json.dumps(data, indent=2, ensure_ascii=False))
            parsed += 1
        except Exception as e:
            print(f"  [{path.name}] {type(e).__name__}: {e}", file=sys.stderr)
            failed += 1
    print(f"\n  Parsed: {parsed}, skipped: {skipped}, failed: {failed}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--force", action="store_true", help="Re-parse already-parsed pages")
    args = ap.parse_args()
    parse_all(force=args.force)


if __name__ == "__main__":
    main()
