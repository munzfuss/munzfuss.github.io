#!/usr/bin/env python3
"""Cross-check every Numista-referenced coin in schleswig_holstein.yml against the
cached Numista API JSON in scripts/cache/numista/<nid>.json.

Reports for each coin:
  - missing fields in YAML that Numista provides (mint, fineness, diameter, weight)
  - contradictions where YAML and Numista disagree

Run: .venv/bin/python scripts/oneoff/numista_audit.py
"""
from __future__ import annotations
import json
import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from lib.paths import NUMISTA_CACHE as CACHE, PROJECT_ROOT  # noqa: E402
from ruamel.yaml import YAML  # noqa: E402

SY = PROJECT_ROOT / "data" / "locations" / "schleswig_holstein.yml"

# Tolerances for "contradiction" — small differences are reasonable specimen variation
WEIGHT_TOL_REL = 0.05   # 5 %
DIAM_TOL_ABS = 1.0       # 1 mm


def numista_fineness(comp: dict) -> float | None:
    """Extract numeric fineness from Numista composition.text like 'Silver (.917)'."""
    if not comp:
        return None
    text = comp.get("text", "")
    m = re.search(r"\((\.\d{3,4})\)", text)
    if m:
        return float(m.group(1))
    return None


def numista_metal(comp: dict) -> str | None:
    if not comp:
        return None
    text = comp.get("text", "").lower()
    for needle, label in [
        ("silver", "silver"),
        ("gold", "gold"),
        ("billon", "billon"),
        ("copper", "copper"),
        ("bronze", "copper"),
        ("brass", "copper"),
    ]:
        if needle in text:
            return label
    return None


def numista_diameter(size: dict | None) -> float | None:
    if not size:
        return None
    if isinstance(size, dict):
        return size.get("value")
    return None


def main() -> int:
    yaml = YAML()
    yaml.preserve_quotes = True
    doc = yaml.load(SY)

    rows = []
    for coin in doc.get("coins", []):
        cat = coin.get("catalog", {}) or {}
        nid = cat.get("numista")
        if not nid:
            continue
        nid = str(nid)
        cache_path = CACHE / f"{nid}.json"
        if not cache_path.exists():
            rows.append({"id": coin["id"], "nid": nid, "issue": "MISSING_CACHE"})
            continue
        try:
            api = json.loads(cache_path.read_text())
        except Exception as e:
            rows.append({"id": coin["id"], "nid": nid, "issue": f"CACHE_PARSE_ERROR: {e}"})
            continue

        issues = []

        # mint — equivalences: Kopenhagen ≡ Copenhagen ≡ "Royal Danish Mint"
        mints = api.get("mints") or []
        api_mint_names = [m.get("name", "").split(",")[0].strip() for m in mints if m.get("name")]
        api_mint_short = api_mint_names[0] if api_mint_names else None
        yaml_mint = coin.get("mint")

        def _mint_eq(a: str, b: str) -> bool:
            if not a or not b:
                return False
            COPENHAGEN_ALIASES = {"kopenhagen", "copenhagen", "royal danish mint", "kongelige mønt"}
            la, lb = a.lower(), b.lower()
            if any(alias in la for alias in COPENHAGEN_ALIASES) and any(alias in lb for alias in COPENHAGEN_ALIASES):
                return True
            return la in lb or lb in la

        if api_mint_short and not yaml_mint:
            issues.append(f"missing mint (Numista: '{api_mint_short}')")
        elif yaml_mint and api_mint_short and not _mint_eq(api_mint_short, str(yaml_mint)):
            issues.append(f"mint contradicts: yaml='{yaml_mint}' vs Numista='{api_mint_short}'")

        # weight
        api_w = api.get("weight")
        yaml_w = coin.get("weight_rough_g")
        if api_w and not yaml_w:
            issues.append(f"missing weight (Numista: {api_w} g)")
        elif api_w and yaml_w:
            if abs(float(yaml_w) - float(api_w)) / max(float(yaml_w), float(api_w)) > WEIGHT_TOL_REL:
                issues.append(f"weight differs >5%: yaml={yaml_w} g, Numista={api_w} g")

        # fineness
        api_fineness = numista_fineness(api.get("composition") or {})
        yaml_fineness = coin.get("fineness")
        if api_fineness and yaml_fineness is None:
            issues.append(f"missing fineness (Numista: {api_fineness})")
        elif api_fineness and yaml_fineness is not None:
            if abs(float(yaml_fineness) - float(api_fineness)) > 0.005:
                issues.append(f"fineness differs: yaml={yaml_fineness}, Numista={api_fineness}")

        # diameter
        api_diam = numista_diameter(api.get("size") or {})
        yaml_diam = coin.get("diameter_mm")
        if api_diam and not yaml_diam:
            issues.append(f"missing diameter (Numista: {api_diam} mm)")
        elif api_diam and yaml_diam:
            if abs(float(yaml_diam) - float(api_diam)) > DIAM_TOL_ABS:
                issues.append(f"diameter differs: yaml={yaml_diam} mm, Numista={api_diam} mm")

        # metal
        api_metal = numista_metal(api.get("composition") or {})
        yaml_metal = coin.get("metal")
        if api_metal and not yaml_metal:
            issues.append(f"missing metal (Numista: {api_metal})")
        elif api_metal and yaml_metal and api_metal != yaml_metal:
            issues.append(f"metal differs: yaml={yaml_metal}, Numista={api_metal}")

        if issues:
            rows.append({"id": coin["id"], "nid": nid, "issue": "; ".join(issues), "mint": api_mint_short})

    # Summary
    by_kind = {}
    for r in rows:
        for kw in ("missing mint", "missing weight", "missing fineness", "missing diameter", "missing metal", "differs", "contradicts", "MISSING_CACHE"):
            if kw in str(r.get("issue", "")):
                by_kind.setdefault(kw, 0)
                by_kind[kw] += 1
    print(f"Total coins audited: {sum(1 for c in doc['coins'] if (c.get('catalog') or {}).get('numista'))}")
    print(f"Coins with issues:   {len(rows)}")
    print()
    print("By issue type:")
    for k, v in sorted(by_kind.items(), key=lambda x: -x[1]):
        print(f"  {v:4d}  {k}")
    print()
    print("Detail:")
    for r in rows:
        print(f"  {r['id']:50}  N#{r['nid']:8}  {r.get('issue')}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
