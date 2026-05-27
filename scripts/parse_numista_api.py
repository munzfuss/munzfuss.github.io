#!/usr/bin/env python3
"""Phase 2 sub-parser — Numista API v3 raw JSON → canonical sidecar.

Reads:  scripts/cache/numista/<NID>.json (Numista API v3 response saved
        verbatim by scripts/fetch_numista_api.py).
Writes: scripts/cache/numista/parsed/<NID>.json (canonical schema —
        same shape as denmark_pre_1541/n<NID>.json).

NOT a standalone CLI by default — invoked by the `parse_numista.py`
driver which detects shape per file. Can be run directly for unit
testing with `--nid <NID>` to dump a single entry.

API v3 input shape (per `fetch_numista_api.py::fetch_type` which calls
`https://api.numista.com/v3/types/{nid}?lang=en`):

  id              int
  url             "https://en.numista.com/<NID>"
  title           "½ Thaler - Frederick III"
  object_type     {id, name}
  issuer          {code, name}
  min_year        int
  max_year        int
  ruler           [{id, name, wikidata_id}]
  value           {text, numeric_value, numerator, denominator,
                   currency: {id, name, full_name}}
  demonetization  {is_demonetized: bool}
  shape           str
  composition     {text}
  obverse         {description, lettering, lettering_scripts,
                   picture, thumbnail, picture_copyright, …}
  reverse         (same shape)
  weight          float | None
  size            float | None        — diameter in mm
  mints           [{id, name}]
  references      [{catalogue: {id, code}, number}]

Output shape: see scripts/lib/numista_canonical.py module docstring.
"""
from __future__ import annotations

import argparse
import json
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
    parse_references_from_api_list,
    render_years_raw,
)


def is_api_shape(d: dict[str, Any]) -> bool:
    """Heuristic shape-detect for the driver. API v3 entries carry
    `min_year` + `object_type` (dict) and lack `_harvested_via:
    chrome_mcp_html`."""
    if not isinstance(d, dict):
        return False
    if d.get("_harvested_via") == "chrome_mcp_html":
        return False
    if "min_year" not in d:
        return False
    if not isinstance(d.get("object_type"), dict):
        return False
    return True


def _normalise_kings(api_ruler: list[dict[str, Any]] | None) -> list[dict[str, Any]]:
    """API v3 `ruler` array → canonical `kings` array.

    Canonical kings carry: id, name, reign (string), wikidata_id?.
    API supplies id, name, wikidata_id but no reign — left empty so
    downstream consumers can fill in from authoritative tables later.
    """
    if not api_ruler:
        return []
    out: list[dict[str, Any]] = []
    for r in api_ruler:
        if not isinstance(r, dict):
            continue
        entry: dict[str, Any] = {"name": r.get("name") or ""}
        if r.get("id") is not None:
            entry["id"] = r["id"]
        if r.get("wikidata_id"):
            entry["wikidata_id"] = r["wikidata_id"]
        # reign: API doesn't supply directly; leave empty for now.
        entry["reign"] = ""
        out.append(entry)
    return out


def _normalise_side(side: dict[str, Any] | None) -> dict[str, Any]:
    """API v3 `obverse`/`reverse` block → canonical 4-field shape.

    API supplies: description, lettering, lettering_scripts, picture,
    thumbnail, picture_copyright. We keep description / lettering, drop
    the picture URLs (not part of canonical schema), and reduce
    `lettering_scripts: [{name}]` → `script: <first name>`.
    Translation is not separately published by the API.
    """
    if not isinstance(side, dict):
        return {"description": None, "script": None, "lettering": None,
                "translation": None}
    scripts = side.get("lettering_scripts") or []
    script_name: str | None = None
    if isinstance(scripts, list) and scripts:
        first = scripts[0]
        if isinstance(first, dict):
            script_name = first.get("name")
    return {
        "description": side.get("description"),
        "script": script_name,
        "lettering": side.get("lettering"),
        "translation": side.get("translation"),  # usually absent
    }


def parse_api_to_canonical(d: dict[str, Any]) -> dict[str, Any] | None:
    """Convert one API v3 JSON entry → canonical sidecar dict.

    Returns None when the input is missing required fields (no id, no
    min_year — the entry is unusable downstream).
    """
    if not isinstance(d, dict):
        return None
    nid = d.get("id")
    if nid is None:
        return None
    min_year = d.get("min_year")
    if min_year is None:
        # Some API entries lack year info entirely — usually pattern /
        # undated strikes. Skip; pre-1541 builder skips them similarly.
        return None

    max_year = d.get("max_year") if d.get("max_year") is not None else min_year

    issuer_block = d.get("issuer") or {}
    issuer_name = issuer_block.get("name") if isinstance(issuer_block, dict) else None

    value = d.get("value") or {}
    value_text = value.get("text") if isinstance(value, dict) else None
    nominal = value_text or extract_nominal_from_title(d.get("title"))

    currency_str: str | None = None
    if isinstance(value, dict):
        cur = value.get("currency") or {}
        if isinstance(cur, dict):
            currency_str = cur.get("full_name") or cur.get("name")

    composition = parse_composition(
        (d.get("composition") or {}).get("text")
        if isinstance(d.get("composition"), dict) else None
    )
    if composition["metal"] is None:
        composition["metal"] = infer_metal_from_denomination(nominal)

    demonet = (d.get("demonetization") or {}).get("is_demonetized") if isinstance(d.get("demonetization"), dict) else None
    demonetized_str = ("Yes" if demonet is True else "No" if demonet is False else None)

    mint = extract_mint(d.get("mints"), None)

    out: dict[str, Any] = {
        "numista_id": int(nid),
        "url": d.get("url"),
        "title": d.get("title"),
        "issuer": issuer_name,
        "kings": _normalise_kings(d.get("ruler")),
        "type_": (d.get("object_type") or {}).get("name"),
        "year_first": int(min_year),
        "year_last": int(max_year),
        "years_raw": render_years_raw(min_year, max_year, None),
        "year_list": None,            # API doesn't expose discrete vs range
        "value": {"raw": nominal},
        "currency": currency_str,
        "composition": composition,
        "weight_g": d.get("weight"),
        "diameter_mm": d.get("size"),
        "shape": d.get("shape"),
        "technique": d.get("technique"),
        "orientation": d.get("orientation"),
        "demonetized": demonetized_str,
        "rarity_index": d.get("rarity_index"),
        "references": parse_references_from_api_list(d.get("references")),
        "obverse": _normalise_side(d.get("obverse")),
        "reverse": _normalise_side(d.get("reverse")),
        "mint": mint,
        "photo_credit": (d.get("obverse") or {}).get("picture_copyright")
                        if isinstance(d.get("obverse"), dict) else None,
        "_source_shape": "api",
        "_source_path": None,  # filled by driver
    }
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--nid", help="Parse only this NID and dump to stdout")
    ap.add_argument("--cache-dir", default="scripts/cache/numista",
                    help="Cache root (default scripts/cache/numista)")
    args = ap.parse_args()

    cache_dir = Path(args.cache_dir)
    if args.nid:
        p = cache_dir / f"{args.nid}.json"
        d = json.loads(p.read_text())
        out = parse_api_to_canonical(d)
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return 0
    # Driver mode would normally invoke this from parse_numista.py.
    print("Use --nid <NID> for direct testing; otherwise run via parse_numista.py driver.",
          file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
