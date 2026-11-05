"""Specimen weights printed inside images on danskmoent.dk coin pages.

Some danskmoent pages show, as an IMAGE, a table of individual specimens with
their collection and weight (Nöbbe 1938's tables of the Flensborg Blafferte
and Penninge, reproduced on the Hede / Galster pages of the coin each table
describes). A text parser never sees them. The hand transcription lives in the
harvest cache, `danskmoent/galster/gif_specimen_tables.yml`.

The binding rule (curator 2026-11-04): a table's specimens go only to the coin
whose OWN cached page embeds that image. An article that reproduces every
table is not a coin page, so an image shown only there reaches no coin.

Used by the Hede and the Galster seed builders.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

from lib.paths import GALSTER_CACHE  # noqa: E402

TABLES_FILE = GALSTER_CACHE / "gif_specimen_tables.yml"

_IMG_RE = re.compile(r"<img\b[^>]*\bsrc\s*=\s*[\"']?([^\"'\s>]+)", re.I)

_TABLES: dict[str, dict] | None = None


def _tables() -> dict[str, dict]:
    """Image basename → table row. Empty when the cache file is absent
    (a checkout without the harvest submodule)."""
    global _TABLES
    if _TABLES is None:
        _TABLES = {}
        if TABLES_FILE.exists():
            rows = (yaml.safe_load(TABLES_FILE.read_text(encoding="utf-8")) or {}).get("tables") or []
            for t in rows:
                _TABLES[Path(t["image"]).name.lower()] = t
    return _TABLES


def page_images(htm: Path) -> list[str]:
    """Basenames (lower case) of the images a cached page embeds, in order."""
    if not htm.exists():
        return []
    text = htm.read_text(encoding="latin-1", errors="replace")
    out: list[str] = []
    for src in _IMG_RE.findall(text):
        name = Path(src.split("?")[0]).name.lower()
        if name not in out:
            out.append(name)
    return out


def source_label(table: dict, specimen: dict) -> str:
    """The reading's `source`: a designation only (tooltip-text rule 10) —
    where the figure was read, the work it reproduces, and the specimen's
    collection as printed."""
    return f"danskmoent.dk ({table['work']}), {specimen['collection']}"


def readings_for_page(htm: Path, coin_keys: set[str] | None = None,
                      coins_on_page: int = 1) -> list[dict]:
    """`weight_rough_g` readings ({value, source}) for the coin built from
    `htm`. `coin_keys` are the coin's seed-level catalogue keys (e.g.
    {"hede f2h32"}, {"galster 128"}), matched against a table's optional
    `coins`. A table without `coins` on a page that yields several coins is
    skipped with a warning — it cannot say which coin it describes."""
    out: list[dict] = []
    tables = _tables()
    for name in page_images(htm):
        t = tables.get(name)
        if not t:
            continue
        bound = set(t.get("coins") or [])
        if bound:
            if not (coin_keys and bound & coin_keys):
                continue
        elif coins_on_page > 1:
            print(f"  ⚠ specimen table {name} on {htm.name}: page yields "
                  f"{coins_on_page} coins and the table names none — skipped",
                  file=sys.stderr)
            continue
        for s in t.get("specimens") or []:
            if s.get("weight_g"):
                out.append({"value": float(s["weight_g"]),
                            "source": source_label(t, s)})
    return out
