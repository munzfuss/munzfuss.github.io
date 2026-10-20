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

The actual parsing logic is per-page-shape and lives in
``scripts/lib/galster_parsers/``: ``standard.py`` (typical coin pages),
``grevenfejde.py`` (possessive-H1 Grevens-Fejde series),
``reign_index.py`` + ``article.py`` (skip-only sentinels). This file
is the entry point — does HTML→text normalisation, dispatches each
page to the correct shape parser, and persists the resulting JSON.

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
from lib.galster_parsers import (  # noqa: E402
    article, classify, galst_table, grevenfejde, hans_index, issuer_table, named_page, reign_index, rigsraad, standard)
from lib.galster_parsers.common import HR_SENTINEL  # noqa: E402  (re-exported)
from lib.paths import GALSTER_CACHE as CACHE_DIR  # noqa: E402

_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"[ \t]+")

# Re-export under the legacy name so any downstream consumer that
# imported `_HR_SENTINEL` from this module keeps working.
_HR_SENTINEL = HR_SENTINEL

# Dispatch table: shape tag → parser module's `parse_page` function.
_PARSERS = {
    "standard": standard.parse_page,
    "grevenfejde": grevenfejde.parse_page,
    "reign_index": reign_index.parse_page,
    "article": article.parse_page,
    "rigsraad": rigsraad.parse_page,
    "hans_index": hans_index.parse_page,
    "galst_table": galst_table.parse_page,
    "issuer_table": issuer_table.parse_page,
}


def _normalise_text(html: str) -> str:
    """HTML → plain text, preserving section breaks via sentinel."""
    text = re.sub(r"<HR[^>]*>", f"\n{HR_SENTINEL}\n", html, flags=re.IGNORECASE)
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


_NAMED_PAGES: dict[str, dict] | None = None


def _named_pages() -> dict[str, dict]:
    """Cache filename → {"numbers", "volume"} for index-linked coin pages
    whose filename carries no Galster number (`index_number_links` in the
    discovery manifest, minus every page a filename pattern already reads)."""
    global _NAMED_PAGES
    if _NAMED_PAGES is None:
        manifest = CACHE_DIR / "_manifest.json"
        links = {}
        if manifest.exists():
            links = json.loads(manifest.read_text()).get("index_number_links") or {}
        _NAMED_PAGES = {
            path.lstrip("/").replace("/", "_", 1): rec
            for path, rec in links.items()
            if standard._galster_number_from_filename(
                path.lstrip("/").replace("/", "_", 1)) is None
        }
    return _NAMED_PAGES


def parse_page(html_path: Path) -> dict:
    """Parse a single Galster page into structured data.

    Routes through ``classify.detect_page_shape`` to pick the right
    per-shape parser module. Each module returns either a full sidecar
    dict (coin data) or a ``{"skip": True, ...}`` sentinel (non-coin
    pages — reign-index tables, articles).
    """
    html = html_path.read_text(encoding="utf-8", errors="replace")
    text = _normalise_text(html)
    record = _named_pages().get(html_path.name)
    if record is not None:
        return named_page.parse_page(html_path, text, record)
    shape = classify.detect_page_shape(html_path, text)
    parser = _PARSERS[shape]
    data = parser(html_path, text)
    if shape == "grevenfejde":
        _split_numbered_bullets(data, text, html_path.name)
    elif shape == "standard":
        _extra_subsection_numbers(data, html_path, text)
    return data


def _extra_subsection_numbers(data: dict, html_path: Path, text: str) -> None:
    """A standard page carrying a second Galster number as its own
    sub-section (fr/f1g48.htm: «1 Sølvgylden (RRR) / Galster 47, Schou 4 …»
    above «1 1/2 Sølvgylden (Unik) / Galster 48 …»; f1galst.htm links 47 and
    48 to that page). The extra number becomes a record of its own, read from
    its sub-section; without one on the page the number is skipped."""
    own = data.get("galster_number")
    extra = []
    for n in _numbers_for(html_path.name):
        if n == own or not re.search(r"^\s*Galster\s+" + re.escape(n) + r"\b",
                                    text, re.MULTILINE):
            continue
        rec = standard.parse_page(html_path, text, galster_override=n)
        rec.pop("raw_text_excerpt", None)
        extra.append(rec)
    if extra:
        data["extra_coins"] = extra


def _numbers_for(filename: str) -> list[str]:
    manifest = CACHE_DIR / "_manifest.json"
    if not manifest.exists():
        return []
    links = json.loads(manifest.read_text()).get("index_number_links") or {}
    rec = links.get("/" + filename.replace("_", "/", 1)) or {}
    return rec.get("numbers") or []


def _split_numbered_bullets(data: dict, text: str, filename: str) -> None:
    """A Grevens-Fejde page carrying TWO Galster numbers, one bullet each:
    chr/c2g82.htm «• 1534 (Unik), Klipping, … (Galster 82, … Sieg 3)» and
    «• 1535 (RRR), Klipping, … (Galster 83, … Sieg 4; …)» — c2galst.htm
    links both 82 and 83 to that page. Each number takes the years and the
    Sieg number of its own bullet; the page's own number stays in `data`, the
    others go to `coins` (one record each). Without this the page gave Galster
    82 the years of both bullets and Galster 83 no record at all."""
    numbers = _numbers_for(filename)
    if len(numbers) < 2:
        return
    per: dict[str, dict] = {}
    for n in numbers:
        m = re.search(
            r"^\s*•\s*(?P<years>[^,(\n]*?)\s*(?:\([^)]*\))?\s*,[^\n]*?"
            r"\(Galster\s+" + re.escape(n) + r"\b(?P<rest>[^)]*)\)",
            text, re.MULTILINE)
        if not m:
            return                                  # shape not as expected
        years = re.findall(r"(?<!\d)1[45]\d{2}(?!\d)", m.group("years"))
        sieg = re.search(r"\bSieg\s+(\d+[A-Za-z]?)", m.group("rest"))
        refs = {"galster": n}
        if sieg:
            refs["sieg"] = sieg.group(1)
        per[n] = {"year_label": ", ".join(years) or None, "catalog_refs": refs}
    own = data.get("galster_number")
    extra = []
    for n, rec in per.items():
        if n == own:
            data.update(rec)
        else:
            c = {k: v for k, v in data.items() if k not in ("coins", "raw_text_excerpt")}
            c.update(rec)
            c["galster_number"] = n
            extra.append(c)
    data["extra_coins"] = extra


def parse_all(force: bool = False) -> None:
    """Parse every cached .htm and write sibling .json."""
    html_files = sorted(CACHE_DIR.glob("*.htm"))
    if not html_files:
        print(f"No HTML files in {CACHE_DIR}. Run fetch_galster.py first.", file=sys.stderr)
        sys.exit(1)
    parsed = 0
    skipped_cache = 0
    skipped_shape = 0
    failed = 0
    shape_counts: dict[str, int] = {}
    for path in html_files:
        json_path = path.with_suffix(".json")
        if json_path.exists() and not force:
            skipped_cache += 1
            continue
        try:
            data = parse_page(path)
            shape_counts[data.get("page_shape", "?")] = shape_counts.get(
                data.get("page_shape", "?"), 0) + 1
            if data.get("skip"):
                skipped_shape += 1
            json_path.write_text(json.dumps(data, indent=2, ensure_ascii=False))
            parsed += 1
        except Exception as e:
            print(f"  [{path.name}] {type(e).__name__}: {e}", file=sys.stderr)
            failed += 1
    print(f"\n  Parsed: {parsed}  (per-shape: {shape_counts})")
    print(f"  Cache-skip (sidecar exists): {skipped_cache}")
    print(f"  Shape-skip (article / reign_index): {skipped_shape}")
    print(f"  Failed: {failed}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--force", action="store_true", help="Re-parse already-parsed pages")
    args = ap.parse_args()
    parse_all(force=args.force)


if __name__ == "__main__":
    main()
