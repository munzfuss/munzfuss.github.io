#!/usr/bin/env python3
"""
Audit ucoin source URLs added to schleswig.yml — find mismatches where
the linked ucoin coin doesn't actually correspond to our coin.

For each (our coin, ucoin URL) pair:
  - Look up ucoin entry by tid in _url_index.json
  - Compare denomination (normalized), year overlap, weight, fineness
  - Flag mismatches by severity

Run: .venv/bin/python scripts/oneoff/ucoin_link_audit.py
"""
from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path

import yaml


CACHE_UCOIN = Path("scripts/cache/ucoin")
SCHLESWIG = Path("data/locations/schleswig.yml")


def normalize_denom(s: str) -> set[str]:
    """Tokenize denomination for fuzzy comparison.
    «1 Søsling Lybsk» → {1, sosling, lybsk}
    «1 søsling»       → {1, sosling}
    Both share «1, sosling» → likely same coin."""
    if not s:
        return set()
    s = s.lower()
    # Replace common fraction symbols
    fr = {"½": "1-2", "⅓": "1-3", "⅔": "2-3", "¼": "1-4", "¾": "3-4",
          "⅙": "1-6", "⅛": "1-8", "⅕": "1-5"}
    for k, v in fr.items():
        s = s.replace(k, v)
    # ø, ä, ö, ü, ß
    s = s.replace("ø", "o").replace("ß", "ss")
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    # Tokenize on whitespace + slashes; drop short connectors
    tokens = re.split(r"[\s/]+", s)
    drop = {"the", "and", "von", "de", "der", "die", "das"}
    return {t for t in tokens if t and t not in drop}


def parse_ucoin_year(yr: str) -> tuple[int, int] | None:
    if not yr:
        return None
    m = re.match(r"(\d{4})(?:[–\-](\d{4}))?", yr)
    if not m:
        return None
    yf = int(m.group(1))
    yl = int(m.group(2)) if m.group(2) else yf
    return yf, yl


def main():
    with open(CACHE_UCOIN / "_url_index.json") as fp:
        ucoin = json.load(fp)
    # Build tid → ucoin entry
    by_tid = {tid: e for tid, e in ucoin.items()}

    with open(SCHLESWIG) as fp:
        d = yaml.safe_load(fp)

    issues: list[dict] = []

    for c in d["coins"]:
        sources = c.get("sources") or []
        for src in sources:
            if not isinstance(src, dict):
                continue
            if src.get("type") != "ucoin":
                continue
            url = src.get("url", "")
            # Extract tid
            m = re.search(r"tid=(\d+)", url)
            if not m:
                continue
            tid = m.group(1)
            u = by_tid.get(tid)
            if not u:
                issues.append({
                    "our_id": c["id"],
                    "severity": "ERROR",
                    "url": url,
                    "reason": f"tid={tid} not in URL index — stale link"
                })
                continue

            # Compare
            problems = []

            # Year overlap
            our_yf = c.get("year_first") or 0
            our_yl = c.get("year_last") or our_yf
            uc_yr = parse_ucoin_year(u.get("year") or "")
            if uc_yr and our_yf:
                yf, yl = uc_yr
                # Ranges overlap?
                if yl < our_yf or yf > (our_yl or our_yf):
                    # No overlap at all
                    overlap_dist = min(abs(yf - our_yl), abs(our_yf - yl))
                    problems.append({
                        "kind": "year_no_overlap",
                        "our": f"{our_yf}-{our_yl}",
                        "ucoin": u.get("year"),
                        "dist_years": overlap_dist,
                    })

            # Denomination
            our_tokens = normalize_denom(c.get("nominal", ""))
            uc_tokens = normalize_denom(u.get("denom", ""))
            if our_tokens and uc_tokens:
                shared = our_tokens & uc_tokens
                # If no shared meaningful tokens, very likely wrong
                if not shared:
                    problems.append({
                        "kind": "denom_mismatch",
                        "our": c.get("nominal"),
                        "ucoin": u.get("denom"),
                    })
                elif len(shared) == 1 and len(uc_tokens) > 2 and len(our_tokens) > 2:
                    # Only one shared token while both have many — partial mismatch
                    problems.append({
                        "kind": "denom_partial",
                        "our": c.get("nominal"),
                        "ucoin": u.get("denom"),
                        "shared": list(shared),
                    })

            # Weight (within 15%)
            our_w = c.get("weight_rough_g") or c.get("weight_g")
            uc_w = u.get("weight_g")
            if our_w and uc_w and our_w > 0:
                rel = abs(our_w - uc_w) / our_w
                if rel > 0.20:
                    problems.append({
                        "kind": "weight_mismatch",
                        "our": our_w,
                        "ucoin": uc_w,
                        "rel_pct": round(rel * 100),
                    })

            # Fineness (within 10%)
            our_f = c.get("fineness")
            uc_f = u.get("fineness")
            if our_f and uc_f and our_f > 0:
                rel = abs(our_f - uc_f) / our_f
                if rel > 0.15:
                    problems.append({
                        "kind": "fineness_mismatch",
                        "our": our_f,
                        "ucoin": uc_f,
                        "rel_pct": round(rel * 100),
                    })

            if problems:
                # Severity: any year_no_overlap or denom_mismatch with no shared tokens = ERROR
                severities = [p["kind"] for p in problems]
                if "year_no_overlap" in severities or "denom_mismatch" in severities:
                    sev = "ERROR"
                else:
                    sev = "WARN"
                issues.append({
                    "our_id": c["id"],
                    "our_nominal": c.get("nominal"),
                    "our_year": f"{our_yf}-{our_yl}",
                    "our_fuss": c.get("fuss"),
                    "ucoin_url": url,
                    "ucoin_denom": u.get("denom"),
                    "ucoin_year": u.get("year"),
                    "severity": sev,
                    "problems": problems,
                })

    # Report
    errors = [i for i in issues if i.get("severity") == "ERROR"]
    warns = [i for i in issues if i.get("severity") == "WARN"]

    print(f"=== AUDIT ===")
    print(f"  ERRORS:   {len(errors)} ucoin links wrongly attached")
    print(f"  WARNINGS: {len(warns)} mismatches in weight/fineness/partial-denom")
    print()

    if errors:
        print("=" * 100)
        print("ERRORS (wrong ucoin link)")
        print("=" * 100)
        for i in errors:
            print(f"\n  ❌ {i['our_id']}")
            print(f"     ours:   {i.get('our_nominal'):30s} {i.get('our_year')}  fuss={i.get('our_fuss')}")
            print(f"     ucoin:  {i.get('ucoin_denom'):30s} {i.get('ucoin_year')}")
            print(f"     URL:    {i.get('ucoin_url')}")
            for p in i.get("problems", []):
                print(f"     ↳ {p}")

    if warns:
        print("\n" + "=" * 100)
        print(f"WARNINGS ({len(warns)})")
        print("=" * 100)
        for i in warns:
            print(f"\n  ⚠ {i['our_id']}")
            print(f"     ours:   {i.get('our_nominal'):30s} {i.get('our_year')}")
            print(f"     ucoin:  {i.get('ucoin_denom'):30s} {i.get('ucoin_year')}")
            for p in i.get("problems", []):
                print(f"     ↳ {p}")


if __name__ == "__main__":
    main()
