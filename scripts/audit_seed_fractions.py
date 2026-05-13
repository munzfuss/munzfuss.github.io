#!/usr/bin/env python3
"""audit_seed_fractions — cross-check seed `fraction` field against nominal text.

Real precedent: dk-hede-f3h48 had `fraction: '1'` on a «1/6 Speciedaler»
nominal — auto-render math multiplied Soll-fein × 1 producing a target
26 g for a coin that should target 4.33 g (Δ silently wrong by 5x).
Caught manually 2026-05-13 (commit `93b2f6e`).

Similarly: dk-hede-f2h30 had `fraction: '1/96'` on «1 Skilling Lybsk»
that was actually 1/32 Speciedaler in pre-Kipper era (commit `2e3e1a9`).

This script walks `data/seed/hede/denmark.yml`, parses each entry's
`nominal` field, and flags two patterns:

  (a) **fraction:None on a parseable nominal** — entry has a clear
      «1/N <denom>» or «N <denom>» nominal but no fraction set.
  (b) **fraction-vs-nominal mismatch** — nominal says «1/6 Speciedaler»
      but fraction is set to «1» / «1/4» / etc. — clear discrepancy.

Sub-currency denominations (Skilling Lybsk, Sechsling, Schilling
Banco) are NOT scanned for nominal-fraction match because their
fraction is era-dependent (1 Sk Lybsk = 1/32 Sp pre-Kipper but 1/48
Sp post-Kipper). These need per-case era-aware research. The script
DOES still flag them when fraction is None.

Usage::

    .venv/bin/python scripts/audit_seed_fractions.py
    .venv/bin/python scripts/audit_seed_fractions.py --json

Exit codes: 0 = clean, 1 = at least one flag.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("PyYAML required.", file=sys.stderr)
    sys.exit(2)

ROOT = Path(__file__).resolve().parent.parent
SEED = ROOT / "data" / "seed" / "hede" / "denmark.yml"

# Sub-currency denominations whose fraction is era-dependent
SUB_CURRENCY = re.compile(
    r"""(?xi)
    Skilling\s+Lybsk
    | Sechsling
    | Schilling\s+Banco
    | Skilling\s+Danske
    | Mark\s+Banco
    | Pfennig
    | Heller
    """
)

# Sub-unit denominations whose fraction is expressed as a ratio-of-parent
# (not the literal N from the nominal). E.g. «1 Mark Danske» = 1/4 Speciedaler
# in 9_thaler; «1 Krone-mønt» = 1/4 Speciedaler. These need per-Fuß-aware
# checks, not the naive «N <denom>» → fraction N rule. Skip from validation.
SUB_UNIT_DENOM = re.compile(
    r"""(?xi)
    \bMark\b(?!\s+Reichswährung)  # Danish Mark, NOT Mark Reichswährung
    | \bKrone\b
    | \bRigsbankskilling\b
    | \bSkilling\b
    | \bPortugaløser?\b   # Portuguese gold coin = 10 Dukaten by Danish convention
    """
)

# Unicode fraction symbols
SYM_MAP = {
    "½": "1/2", "¼": "1/4", "¾": "3/4",
    "⅓": "1/3", "⅔": "2/3",
    "⅙": "1/6", "⅕": "1/5", "⅛": "1/8",
    "1/24": "1/24",  # explicit  pass-through
}


def parse_expected_fraction(nominal: str) -> str | None:
    """Extract the expected fraction from a nominal text.

    Returns None when the nominal can't be parsed with high confidence
    (e.g. sub-currency denominations where fraction is era-dependent).
    """
    if not nominal:
        return None
    if SUB_CURRENCY.search(nominal):
        return None  # era-dependent, don't guess
    if SUB_UNIT_DENOM.search(nominal):
        return None  # sub-unit (Mark/Krone/Skilling), fraction is ratio-of-parent
    # Strip leading whitespace, look at first token
    s = nominal.strip()
    # «1/4 Speciedaler», «1/12 Speciedaler», «1/2 Mark»
    m = re.match(r"^(\d+)/(\d+)\s", s)
    if m:
        return f"{m.group(1)}/{m.group(2)}"
    # «½ Mark» / «¼ Speciedaler» etc.
    for sym, frac in SYM_MAP.items():
        if s.startswith(sym):
            return frac
    # «2 Speciedaler» / «1 Speciedaler» / «3 Krone»
    m = re.match(r"^(\d+)\s+(?:Speciedaler|Speciesdaler|Ducat|Dukat|Krone|Reichsthaler|Daler|Mark|Reichsbankskilling|Reichsbankdaler|Rigsbankdaler|Portugal|Portugaløser|Ungersk\s+gylden|Goldgulden)\b",
                 s, re.IGNORECASE)
    if m:
        n = int(m.group(1))
        return str(n) if n != 1 else "1"
    return None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    with SEED.open() as f:
        doc = yaml.safe_load(f) or {}
    coins = doc.get("coins") or []

    none_with_parseable: list[dict] = []
    mismatch: list[dict] = []
    skipped_sub_currency: list[dict] = []

    for c in coins:
        if not isinstance(c, dict):
            continue
        cid = c.get("id", "?")
        nominal = c.get("nominal", "") or ""
        fuss = c.get("fuss") or ""
        actual = c.get("fraction")
        if actual is not None:
            actual = str(actual)
        expected = parse_expected_fraction(nominal)
        # Skip seed_unsorted entries from the fraction:None check — they
        # aren't actively rendered with Δ-from-Soll, so fraction is
        # naturally pending until the entry gets placed. Mismatch check
        # still applies (a wrong fraction value would propagate when
        # the entry gets promoted).
        is_placed = fuss not in ("", "seed_unsorted")
        if expected is None:
            if SUB_CURRENCY.search(nominal) and actual is None and is_placed:
                skipped_sub_currency.append({
                    "id": cid, "nominal": nominal, "fraction": actual,
                    "fuss": fuss,
                    "note": "sub-currency, era-dependent — needs per-case research",
                })
            continue
        if actual is None and is_placed:
            none_with_parseable.append({
                "id": cid, "nominal": nominal, "expected": expected,
                "fuss": fuss,
            })
        elif actual is not None and actual != expected:
            mismatch.append({
                "id": cid, "nominal": nominal,
                "actual": actual, "expected": expected,
                "fuss": fuss,
            })

    if args.json:
        print(json.dumps({
            "fraction_none_with_parseable_nominal": none_with_parseable,
            "fraction_vs_nominal_mismatch": mismatch,
            "skipped_sub_currency_none": skipped_sub_currency,
            "counts": {
                "none_parseable": len(none_with_parseable),
                "mismatch": len(mismatch),
                "sub_currency_none": len(skipped_sub_currency),
            },
        }, indent=2, ensure_ascii=False))
    else:
        print(f"Seed entries scanned: {len(coins)}")
        print()
        if none_with_parseable:
            print(f"⚠ {len(none_with_parseable)} entries: fraction: None on a parseable nominal:")
            for f in none_with_parseable:
                print(f"  - {f['id']}: nominal={f['nominal']!r} → expected fraction {f['expected']!r}")
            print()
        if mismatch:
            print(f"⚠ {len(mismatch)} entries: fraction-vs-nominal mismatch:")
            for f in mismatch:
                print(f"  - {f['id']}: nominal={f['nominal']!r} fraction={f['actual']!r} ≠ expected {f['expected']!r}")
            print()
        if skipped_sub_currency:
            print(f"ℹ {len(skipped_sub_currency)} sub-currency entries with fraction: None (era-dependent, per-case research needed):")
            for f in skipped_sub_currency[:10]:
                print(f"  - {f['id']}: nominal={f['nominal']!r}")
            if len(skipped_sub_currency) > 10:
                print(f"    … and {len(skipped_sub_currency) - 10} more.")
            print()
        if not none_with_parseable and not mismatch and not skipped_sub_currency:
            print("✓ All seed entries have consistent fraction/nominal pairing.")

    return 1 if (none_with_parseable or mismatch) else 0


if __name__ == "__main__":
    sys.exit(main())
