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
from lib.galster_parsers import article, classify, grevenfejde, reign_index, standard  # noqa: E402
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


def parse_page(html_path: Path) -> dict:
    """Parse a single Galster page into structured data.

    Routes through ``classify.detect_page_shape`` to pick the right
    per-shape parser module. Each module returns either a full sidecar
    dict (coin data) or a ``{"skip": True, ...}`` sentinel (non-coin
    pages — reign-index tables, articles).
    """
    html = html_path.read_text(encoding="utf-8", errors="replace")
    text = _normalise_text(html)
    shape = classify.detect_page_shape(html_path, text)
    parser = _PARSERS[shape]
    return parser(html_path, text)


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
