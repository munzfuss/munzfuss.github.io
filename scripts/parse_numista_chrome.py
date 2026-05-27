#!/usr/bin/env python3
"""Phase 2 sub-parser — Numista chrome_mcp_html scrape → canonical sidecar.

Two chrome variants both bear `_harvested_via: chrome_mcp_html`:

  chrome_v1  — older HARVEST_ROUTINE iteration (BO.1 / BO.5 era):
    Keys: issuer_text, ruler_text, value_text, years_text, min_year,
          max_year, composition_text, fineness, weight_g, diameter_mm,
          mint_text, references_list, obverse_text, reverse_text

  chrome_v2  — newer HARVEST_ROUTINE iteration (BO.6 / BO.7 era):
    Keys: country, ruler, denomination, year_first, year_last,
          year_list, metal, fineness, weight_g, diameter_mm,
          mintmaster, references_list (+ optional composition_text,
          currency, mint_text, mint_name, emperor)

Both variants funnel into the same canonical sidecar schema as
`parse_numista_api.py`. The driver hands raw cache files to whichever
sub-parser the shape-detector picks.

NOT a standalone CLI by default — invoked from `parse_numista.py`.
Can be run with `--nid <NID>` for unit testing.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from lib.numista_canonical import (  # noqa: E402
    extract_mint,
    extract_nominal_from_title,
    infer_metal_from_denomination,
    parse_composition,
    parse_references_from_strings,
    render_years_raw,
)


def is_chrome_shape(d: dict[str, Any]) -> bool:
    """Shape-detect for the driver. Chrome scrapes carry
    `_harvested_via: chrome_mcp_html` (the canonical marker stamped by
    the /tmp/save_numista.py routine)."""
    if not isinstance(d, dict):
        return False
    return d.get("_harvested_via") == "chrome_mcp_html"


def _chrome_variant(d: dict[str, Any]) -> str:
    """Return 'v1' or 'v2' based on which header set the cache uses.
    v1 carries issuer_text; v2 uses country. (Both can occasionally
    have BOTH due to overlapping harvest rounds — pick v2 when ambiguous
    because it carries the richer year_list field.)"""
    if "country" in d:
        return "v2"
    return "v1"


def _normalise_ruler(ruler_field: Any) -> list[dict[str, Any]]:
    """Chrome stores ruler as a free-text string ("Christian IV (1588-1648)"
    or "Frederick III (Frederik III)"). Parse out name + reign range when
    parens contain digits. Returns list-of-dict matching canonical kings
    shape; empty list when input is empty."""
    if not ruler_field:
        return []
    if isinstance(ruler_field, list):
        # v2 sometimes emits list-of-string when there are co-rulers
        out: list[dict[str, Any]] = []
        for r in ruler_field:
            out.extend(_normalise_ruler(r))
        return out
    if not isinstance(ruler_field, str):
        return []
    s = ruler_field.strip()
    if not s:
        return []
    # Pattern: "Name (Native form)" OR "Name (1234-1567)" OR plain "Name"
    m = re.match(r"^(.+?)\s*\(([^)]+)\)\s*$", s)
    if m:
        name = m.group(1).strip()
        paren = m.group(2).strip()
        # Is paren a reign range or a name variant?
        if re.match(r"^\d{3,4}\s*[-–]\s*\d{3,4}$", paren):
            return [{"name": name, "reign": paren}]
        # Likely native-name variant — drop, keep main name
        return [{"name": name, "reign": ""}]
    return [{"name": s, "reign": ""}]


def _year_extract(d: dict[str, Any], variant: str) -> tuple[int | None, int | None, list[int] | None, str | None]:
    """Pull (year_first, year_last, year_list, years_raw) per variant."""
    year_list = d.get("year_list")
    if isinstance(year_list, list):
        year_list = [int(y) for y in year_list if y is not None]
    else:
        year_list = None
    if variant == "v2":
        yf = d.get("year_first")
        yl = d.get("year_last")
        years_raw = d.get("year_text") or d.get("years_text")
    else:
        yf = d.get("min_year")
        yl = d.get("max_year")
        years_raw = d.get("years_text")
    yf = int(yf) if yf is not None else None
    yl = int(yl) if yl is not None else (yf if yf is not None else None)
    if not years_raw:
        years_raw = render_years_raw(yf, yl, year_list)
    return yf, yl, year_list, years_raw


def _extract_value(d: dict[str, Any], variant: str) -> dict[str, str | None]:
    """Pull canonical {raw: <denom>} from the variant-specific keys."""
    if variant == "v2":
        raw = d.get("denomination") or d.get("value_text")
    else:
        raw = d.get("value_text")
    if not raw:
        raw = extract_nominal_from_title(d.get("title"))
    if raw and isinstance(raw, str):
        raw = re.sub(r"\s+", " ", raw).strip()
        # Strip trailing Daler-fraction parenthesis (CLAUDE.md §1 — also
        # already done by extract_nominal_from_title but value_text may
        # carry «2 Skilling (1⁄48)» literally).
        raw = re.sub(
            r"\s+\(([⅓⅔¼½¾⅕⅖⅗⅘⅙⅚⅛⅜⅝⅞]|\d+\s*[⁄/]\s*\d+)\)\s*$",
            "",
            raw,
        ).strip()
    return {"raw": raw or None}


def _extract_composition(d: dict[str, Any]) -> dict[str, Any]:
    """Canonical {raw, metal, fineness}. Chrome scrapes pre-extract
    `fineness` (numeric) and sometimes `metal` directly; combine with
    `composition_text` to fill `raw` for traceability."""
    comp_text = d.get("composition_text") or d.get("composition") or None
    if isinstance(comp_text, dict):
        comp_text = comp_text.get("text") or comp_text.get("raw")
    parsed = parse_composition(comp_text)
    # Prefer chrome's directly-extracted fields when present and
    # parser disagrees / didn't find anything.
    chrome_metal = d.get("metal")
    if chrome_metal and parsed["metal"] is None:
        parsed["metal"] = chrome_metal
    chrome_fineness = d.get("fineness")
    if chrome_fineness is not None and parsed["fineness"] is None:
        try:
            parsed["fineness"] = float(chrome_fineness)
        except (TypeError, ValueError):
            pass
    return parsed


def _extract_mint(d: dict[str, Any], variant: str) -> str | list[str] | None:
    """Chrome mint can live in `mint_text`, `mint_name`, or `mint`."""
    # `mint_text` is the canonical chrome field; `mint_name` / `mint`
    # appear in older variants.
    candidate = d.get("mint_text") or d.get("mint_name") or d.get("mint")
    return extract_mint(None, candidate)


def _normalise_side(text_field: Any) -> dict[str, Any]:
    """Chrome `obverse_text` / `reverse_text` are free-form strings (or
    None) — wrap into canonical 4-field shape with description set;
    script/lettering/translation null."""
    return {
        "description": text_field if isinstance(text_field, str) and text_field.strip() else None,
        "script": None,
        "lettering": None,
        "translation": None,
    }


def parse_chrome_to_canonical(d: dict[str, Any]) -> dict[str, Any] | None:
    """Convert one chrome-scrape JSON entry → canonical sidecar dict."""
    if not isinstance(d, dict):
        return None
    nid = d.get("id")
    if nid is None:
        return None
    variant = _chrome_variant(d)

    yf, yl, year_list, years_raw = _year_extract(d, variant)
    if yf is None:
        return None

    # Issuer string — variant-specific key, fall back to either.
    issuer_str = (d.get("issuer_text") if variant == "v1"
                  else d.get("country"))
    if not issuer_str:
        # Sometimes a v2 entry has issuer_text too (overlap during harvest
        # rotation). Try the other key as a backstop.
        issuer_str = d.get("issuer_text") if variant == "v2" else d.get("country")

    nominal_block = _extract_value(d, variant)
    composition = _extract_composition(d)
    if composition["metal"] is None:
        composition["metal"] = infer_metal_from_denomination(nominal_block["raw"])

    return {
        "numista_id": int(nid),
        "url": d.get("url"),
        "title": d.get("title"),
        "issuer": issuer_str,
        "kings": _normalise_ruler(d.get("ruler") or d.get("ruler_text")),
        "type_": d.get("type") or d.get("type_text"),
        "year_first": yf,
        "year_last": yl,
        "years_raw": years_raw,
        "year_list": year_list,
        "value": nominal_block,
        "currency": d.get("currency") or d.get("currency_text"),
        "composition": composition,
        "weight_g": d.get("weight_g"),
        "diameter_mm": d.get("diameter_mm"),
        "shape": d.get("shape"),
        "technique": d.get("technique"),
        "orientation": d.get("orientation"),
        "demonetized": d.get("demonetized"),
        "rarity_index": d.get("rarity_index"),
        "references": parse_references_from_strings(d.get("references_list")
                                                    or [d.get("references_text")]
                                                       if d.get("references_text") else None),
        "obverse": _normalise_side(d.get("obverse_text")),
        "reverse": _normalise_side(d.get("reverse_text")),
        "mint": _extract_mint(d, variant),
        "photo_credit": None,
        # Mintmaster is chrome-specific extras not modelled in
        # canonical (yet). Stash for downstream builder visibility.
        "_mintmaster": d.get("mintmaster"),
        "_source_shape": f"chrome_{variant}",
        "_source_path": None,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--nid")
    ap.add_argument("--cache-dir", default="scripts/cache/numista")
    args = ap.parse_args()
    cache_dir = Path(args.cache_dir)
    if args.nid:
        p = cache_dir / f"{args.nid}.json"
        d = json.loads(p.read_text())
        out = parse_chrome_to_canonical(d)
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return 0
    print("Use --nid <NID> for direct testing.", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
