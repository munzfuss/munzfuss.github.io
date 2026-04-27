#!/usr/bin/env python3
"""
One-shot migration: pull full c-note HTML from the original artifact and patch
every coin in data/locations/schleswig.yml whose catalog.km matches.

Drops the `# TODO: expand note from original HTML if needed` marker once
the note.de is replaced.

Usage:
  python scripts/migrate_notes.py \
      --html ~/Downloads/holstein_muentzwesen_47.html \
      --yaml data/locations/schleswig.yml
"""
from __future__ import annotations

import argparse
import html
import json
import re
import sys
from pathlib import Path

from ruamel.yaml import YAML
from ruamel.yaml.scalarstring import LiteralScalarString, PreservedScalarString


KM_CELL_RE = re.compile(
    r'<td class="c-km">(.*?)</td>', re.DOTALL
)
NOTE_CELL_RE = re.compile(
    r'<td class="c-note">(.*?)</td>', re.DOTALL
)
STOPE_CELL_RE = re.compile(r'<td class="c-stope">(.*?)</td>', re.DOTALL)
NOM_CELL_RE = re.compile(r'<td class="c-nom">(.*?)</td>', re.DOTALL)
YEAR_CELL_RE = re.compile(r'<td class="c-year">(.*?)</td>', re.DOTALL)
ROW_RE = re.compile(r"<tr[^>]*>(.*?)</tr>", re.DOTALL)
KM_NUM_RE = re.compile(r"KM[#\s\-]*\s*([A-Za-z0-9./\-]+)", re.IGNORECASE)
YEAR_NUM_RE = re.compile(r"\b(1[5-9]\d{2})\b")
SF_LINE_RE = re.compile(
    r'<span class="sf-line (primary|secondary|tertiary)">(.*?)</span>', re.DOTALL
)


def strip_tags(s: str) -> str:
    return re.sub(r"<[^>]+>", "", s)


def extract_km_numbers(cell_html: str) -> list[str]:
    """From a <td class='c-km'> cell, extract KM numbers (may appear as 'KM-42.1', 'KM# 42.1', 'KM# 82.1, 82.2')."""
    text = strip_tags(cell_html)
    text = html.unescape(text)
    matches = KM_NUM_RE.findall(text)
    nums = []
    for m in matches:
        # Split further on comma / slash combos that may appear
        for part in re.split(r"[,\s]+", m):
            part = part.strip().strip(".")
            if part:
                nums.append(part)
    return nums


def normalize_nom(s: str) -> str:
    """Reduce the nominal cell to a canonical form for fallback lookup."""
    # Replace block-level tags with space before stripping
    s = re.sub(r"<\s*br\s*/?\s*>", " ", s, flags=re.IGNORECASE)
    s = html.unescape(strip_tags(s))
    # Collapse all whitespace and drop anything non-alphanumeric
    s = re.sub(r"\s+", "", s)
    s = re.sub(r"[^\w]", "", s, flags=re.UNICODE)
    return s.lower()


def extract_sf_lines(stope_cell_html: str) -> list[dict]:
    """Pull <span class='sf-line primary|secondary|tertiary'>…</span> out of a c-stope cell."""
    refs = []
    for m in SF_LINE_RE.finditer(stope_cell_html):
        rank, inner = m.group(1), m.group(2)
        inner = inner.replace("\n", " ")
        inner = re.sub(r"\s+", " ", inner).strip()
        refs.append({"rank": rank, "label": {"de": inner}})
    return refs


def build_maps(
    html_text: str,
) -> tuple[dict[str, dict], dict[tuple[str, int], dict]]:
    """
    Walk all <tr> rows in coin tables. For each row, capture c-km, c-note,
    c-stope. Index a dict {note_html, fuss_refs} by every KM number found,
    and by (normalized_nominal, first_year) for fallback.
    """
    by_km: dict[str, dict] = {}
    by_nom_year: dict[tuple[str, int], dict] = {}
    for row_match in ROW_RE.finditer(html_text):
        row_html = row_match.group(1)
        km_cell = KM_CELL_RE.search(row_html)
        note_cell = NOTE_CELL_RE.search(row_html)
        stope_cell = STOPE_CELL_RE.search(row_html)
        nom_cell = NOM_CELL_RE.search(row_html)
        year_cell = YEAR_CELL_RE.search(row_html)
        if not note_cell:
            continue

        note_html = note_cell.group(1).strip()
        note_html = note_html.replace("\n", " ")
        note_html = re.sub(r"\s+", " ", note_html).strip()

        fuss_refs = extract_sf_lines(stope_cell.group(1)) if stope_cell else []

        payload = {"note": note_html, "fuss_refs": fuss_refs}

        if km_cell:
            for k in extract_km_numbers(km_cell.group(1)):
                by_km.setdefault(k, payload)

        if nom_cell and year_cell:
            nom = normalize_nom(nom_cell.group(1))
            years = YEAR_NUM_RE.findall(strip_tags(year_cell.group(1)))
            if years:
                first_year = int(years[0])
                key = (nom, first_year)
                by_nom_year.setdefault(key, payload)
    return by_km, by_nom_year


def normalize_km(s: str) -> list[str]:
    """Split 'KM#' value like '42.1' or '82.1, 82.2' into a list of individual numbers."""
    if not s:
        return []
    return [p.strip() for p in re.split(r"[,\s]+", str(s)) if p.strip()]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--html", required=True)
    ap.add_argument("--yaml", required=True)
    ap.add_argument("--dump-map", default=None, help="Write the KM→note map to a JSON for inspection")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    html_text = Path(args.html).expanduser().read_text(encoding="utf-8")
    km_map, nom_year_map = build_maps(html_text)
    print(f"Extracted notes for {len(km_map)} KM numbers + {len(nom_year_map)} (nominal,year) keys")

    if args.dump_map:
        Path(args.dump_map).write_text(
            json.dumps({
                "by_km": km_map,
                "by_nom_year": {f"{k[0]}|{k[1]}": v for k, v in nom_year_map.items()},
            }, ensure_ascii=False, indent=2),
            encoding="utf-8",
            newline="\n",
        )
        print(f"Wrote map → {args.dump_map}")

    yaml = YAML()
    yaml.preserve_quotes = True
    yaml.width = 10000
    yaml.indent(mapping=2, sequence=4, offset=2)
    with open(args.yaml, encoding="utf-8") as f:
        data = yaml.load(f)

    patched = 0
    unmatched: list[str] = []
    for coin in data.get("coins", []) or []:
        cat = coin.get("catalog") or {}
        km_value = cat.get("km")
        kms = normalize_km(km_value)
        payload = None
        for k in kms:
            if k in km_map:
                payload = km_map[k]
                break

        if payload is None:
            # Fallback: (normalized nominal, year_first)
            nom_key = normalize_nom(str(coin.get("nominal", "")))
            year_first = coin.get("year_first")
            if year_first is not None:
                payload = nom_year_map.get((nom_key, int(year_first)))

        if payload is None:
            unmatched.append(f"{coin.get('id')} (KM# {km_value}, nominal={coin.get('nominal')!r}, year={coin.get('year_first')})")
            continue

        note_html = payload["note"]
        note = coin.get("note")
        if note is None:
            coin["note"] = {"de": LiteralScalarString(note_html)}
        else:
            note["de"] = LiteralScalarString(note_html)

        refs = payload.get("fuss_refs") or []
        if refs:
            coin["fuss_refs"] = [
                {"rank": r["rank"], "label": {"de": LiteralScalarString(r["label"]["de"])}}
                for r in refs
            ]
        patched += 1

    if not args.dry_run:
        with open(args.yaml, "w", encoding="utf-8") as f:
            yaml.dump(data, f)

    print(f"Patched {patched} / {len(data.get('coins', []))} coins")
    if unmatched:
        print(f"Unmatched ({len(unmatched)}):")
        for u in unmatched:
            print(f"  {u}")


if __name__ == "__main__":
    main()
