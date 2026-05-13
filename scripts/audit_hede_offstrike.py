#!/usr/bin/env python3
"""audit_hede_offstrike — detect c4h47-pattern (silver-spec-for-gold-strike).

Real precedent (caught 2026-05-13, commit `b0aa746`): a Hede page
primarily catalogues the silver mother coin (e.g. Hede 47 «Frederik IV
16 Skilling 1713 silver»), but the description or `eksemplarer`
section mentions a Guldafslag (gold off-strike) sub-variant — usually
with a different Schou number (e.g. Schou «1a» beside silver Schou
«1»). A curator who reads only the spec card ingests the silver
Bruttovægt/Finhed onto a `metal: gold` entry → produces a silver-
fineness gold coin. Bad data.

CLAUDE.md §9 exclusion #3 (added 2026-05-13) declares such off-strike
single-specimen entries OUT OF SCOPE — they belong to a presentation /
Probekopf register, not the circulation-coin table. Fix is therefore
DELETE the entry, not «convert metal/fineness».

This script:

  1. Walks all Hede cache pages (`scripts/cache/hede/*.json`).
  2. For each page, checks `description`, `eksemplarer`, and
     `raw_text` for off-strike markers («Guldafslag», «Sølvafslag»,
     «medaljonprægning», «cf.\\s+Hede»).
  3. Reads `specs.default.finhed` (silver spec-card publishes < 0.95
     for silver mother coins).
  4. Cross-references curated entries in `data/locations/*.yml`: for
     each flagged Hede page, lists all `coins[]` whose `catalog.hede`
     matches the page id AND `metal: gold`. These are the c4h47-trap
     candidates.
  5. Outputs the candidate list for user verdict per case.

Usage::

    .venv/bin/python scripts/audit_hede_offstrike.py
    .venv/bin/python scripts/audit_hede_offstrike.py --json
    .venv/bin/python scripts/audit_hede_offstrike.py --hede-only  # skip cross-ref

Exit codes: 0 = no candidates, 1 = at least one candidate flagged.
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
CACHE = ROOT / "scripts" / "cache" / "hede"
LOCATIONS = ROOT / "data" / "locations"

OFFSTRIKE_PATTERN = re.compile(
    r"""(?xi)
    Guldafslag        # gold off-strike of silver coin
    | Sølvafslag      # silver off-strike of gold coin
    | medaljonpr(?:æ|ae)gning  # medallion-style strike (non-capturing)
    | cf\.\s*Hede\s*\d  # «cf. Hede N» — cross-reference to mother
    """
)


def scan_hede_pages() -> list[dict]:
    """Return [{hede_id, hede_volume, marks, fineness, nominal, ...}] for flagged pages."""
    flagged = []
    for path in sorted(CACHE.glob("*.json")):
        try:
            with path.open() as f:
                d = json.load(f)
        except (json.JSONDecodeError, OSError):
            continue
        hede_id = path.stem  # e.g. "c4h47"
        # Combine text fields to search for off-strike markers
        texts = [
            d.get("description", "") or "",
            d.get("raw_text", "") or "",
        ]
        # eksemplarer is usually a list of dicts; flatten to text
        eks = d.get("eksemplarer") or []
        if isinstance(eks, list):
            for e in eks:
                if isinstance(e, dict):
                    texts.append(str(e.get("text", "") or ""))
                else:
                    texts.append(str(e))
        joined = " ".join(texts)
        marks = OFFSTRIKE_PATTERN.findall(joined)
        if not marks:
            continue
        # Silver spec-card check: finhed < 0.95
        specs = d.get("specs") or {}
        default_spec = specs.get("default") or {}
        finhed = default_spec.get("finhed")
        if finhed is None:
            continue
        try:
            finhed = float(finhed)
        except (ValueError, TypeError):
            continue
        if finhed >= 0.95:
            # Gold-mother spec card — different trap (silver off-strike). Still flag.
            pass
        flagged.append({
            "hede_id": hede_id,
            "hede_volume": d.get("ruler_volume", "") or hede_id.split("h")[0] + "h",
            "nominal": d.get("nominal", ""),
            "ruler": d.get("ruler", "") or d.get("ruler_inferred", ""),
            "finhed_spec_card": finhed,
            "off_strike_marks": list(set(m.lower() for m in marks)),
            "spec_card_metal": "silver" if finhed < 0.95 else "gold",
        })
    return flagged


def parse_hede_id(hid: str) -> tuple[str, str]:
    """Split 'c4h47' → ('c4h', '47'); 'f3h148' → ('f3h', '148'); 'c4h84a' → ('c4h', '84A')."""
    m = re.match(r"^([cf]\d+h)(\d+[a-z]?)$", hid, re.IGNORECASE)
    if not m:
        return ("", hid)
    return (m.group(1).lower(), m.group(2).upper())


def find_curated_victims(flagged_pages: list[dict]) -> list[dict]:
    """Find curated coins whose catalog.hede matches a flagged page AND metal is opposite."""
    victims = []
    flagged_by_pair = {}  # (vol, num) -> flagged-page dict
    for fp in flagged_pages:
        vol, num = parse_hede_id(fp["hede_id"])
        flagged_by_pair[(vol, num)] = fp

    for loc_path in sorted(LOCATIONS.glob("*.yml")):
        if loc_path.stem.endswith("-references"):
            continue
        try:
            with loc_path.open() as f:
                doc = yaml.safe_load(f)
        except (yaml.YAMLError, OSError):
            continue
        for coin in (doc.get("coins") or []):
            cat = coin.get("catalog") or {}
            hede_field = cat.get("hede")
            hede_volume = cat.get("hede_volume", "")
            if not hede_field or not hede_volume:
                continue
            # hede can be string '47' or list ['47','47a']
            hede_list = [hede_field] if not isinstance(hede_field, list) else hede_field
            for hv in hede_list:
                key = (hede_volume.lower(), str(hv).upper())
                if key not in flagged_by_pair:
                    continue
                fp = flagged_by_pair[key]
                coin_metal = coin.get("metal", "")
                spec_metal = fp["spec_card_metal"]
                if coin_metal == spec_metal:
                    # same metal — not a trap, just normal mother-coin entry
                    continue
                victims.append({
                    "location": loc_path.stem,
                    "coin_id": coin.get("id", "?"),
                    "coin_metal": coin_metal,
                    "coin_nominal": coin.get("nominal", ""),
                    "coin_year_label": coin.get("year_label", ""),
                    "hede_id": fp["hede_id"],
                    "hede_volume": hede_volume,
                    "hede_nominal": fp["nominal"],
                    "spec_card_metal": spec_metal,
                    "spec_card_finhed": fp["finhed_spec_card"],
                    "off_strike_marks": fp["off_strike_marks"],
                })
    return victims


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--hede-only", action="store_true",
                    help="report flagged Hede pages without curated cross-ref")
    args = ap.parse_args()

    flagged_pages = scan_hede_pages()

    if args.hede_only:
        if args.json:
            print(json.dumps({"flagged_pages": flagged_pages, "count": len(flagged_pages)},
                             indent=2, ensure_ascii=False))
        else:
            print(f"Flagged Hede pages with off-strike markers: {len(flagged_pages)}")
            for fp in flagged_pages:
                print(f"  - {fp['hede_id']}: {fp['nominal']!r} "
                      f"finhed={fp['finhed_spec_card']:.3f} "
                      f"({fp['spec_card_metal']}) "
                      f"marks={fp['off_strike_marks']}")
        return 1 if flagged_pages else 0

    victims = find_curated_victims(flagged_pages)
    if args.json:
        print(json.dumps({
            "flagged_pages": len(flagged_pages),
            "victims": victims,
            "victim_count": len(victims),
        }, indent=2, ensure_ascii=False))
    else:
        print(f"Flagged Hede pages: {len(flagged_pages)}")
        print(f"Curated c4h47-trap candidates: {len(victims)}")
        print()
        if not victims:
            print("✓ No curated entries reference a flagged Hede page at opposite metal.")
        else:
            print(f"⚠ {len(victims)} candidate(s) for review (DELETE per CLAUDE.md §9 exclusion #3):")
            for v in victims:
                print(f"  - {v['location']}::{v['coin_id']}")
                print(f"    nominal={v['coin_nominal']!r} year={v['coin_year_label']} metal={v['coin_metal']}")
                print(f"    references Hede page {v['hede_id']} "
                      f"(spec-card {v['spec_card_metal']}, finhed={v['spec_card_finhed']:.3f})")
                print(f"    off-strike marks on Hede page: {v['off_strike_marks']}")
                print()
    return 1 if victims else 0


if __name__ == "__main__":
    sys.exit(main())
