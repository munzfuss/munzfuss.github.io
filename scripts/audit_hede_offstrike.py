#!/usr/bin/env python3
"""audit_hede_offstrike — detect c4h47-pattern (silver-spec-for-gold-strike).

Real precedent (caught 2026-05-13, commit `b0aa746`): a Hede page
primarily catalogues a SILVER mother coin (e.g. Hede 47 «Frederik IV
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

This script is **bidirectional** — it flags both directions of the
metal-mismatch trap:

  - silver mother coin (spec card .500-.937) + Guldafslag → curated
    `metal: gold` referencing the page = TRAP (c4h47 prototype)
  - gold mother coin (spec card ≥.95) + Sølvafslag → curated
    `metal: silver` referencing the page = symmetric TRAP

Logic:

  1. Walk all Hede cache pages (`scripts/cache/hede/*.json`).
  2. For each page, scan `description`, `eksemplarer`, and `raw_text`
     for off-strike markers («Guldafslag», «Sølvafslag»,
     «medaljonprægning», «cf.\\s+Hede»).
  3. Extract spec-card fineness from BOTH `specs.default.finhed` AND
     `specs.by_hede.<num>.finhed` (Hede pages with a shared spec card
     across several catalogue numbers store specs per-sub-number; the
     2026-05-13 implementation only checked `specs.default`, missing
     ~18 such pages including f3h62 + f3h68 referenced by §AM
     candidates).
  4. If no finhed is published anywhere, fall back to nominal-text
     metal inference (gold tokens: Dukat / Pistole / Guldjeton /
     Goldgulden / Portugaløser / Rosenobel / Sovereign / Krone-Guld;
     silver tokens: Speciedaler / Rigsdaler / Mark / Skilling /
     Daler / Krone-silver). Pages with ambiguous nominals are
     flagged with `spec_card_metal: "unknown"` and skipped in
     cross-ref.
  5. Cross-reference curated entries in `data/locations/*.yml`: for
     each flagged Hede page, list all `coins[]` whose
     `(catalog.hede_volume, catalog.hede)` matches any of the page's
     legitimate-reference numbers (filename num + by_hede sub-numbers)
     AND whose `metal` differs from the spec-card metal. These are
     the c4h47-trap candidates.

Usage::

    .venv/bin/python scripts/audit_hede_offstrike.py
    .venv/bin/python scripts/audit_hede_offstrike.py --json
    .venv/bin/python scripts/audit_hede_offstrike.py --hede-only   # skip curated cross-ref
    .venv/bin/python scripts/audit_hede_offstrike.py --self-test   # synthetic bidirectional sanity check

Exit codes: 0 = no candidates / self-test passes, 1 = candidate(s)
flagged / self-test fails.
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

# Threshold for spec_card metal classification.
# Empirically: silver fineness 0.156-0.937 in our cache; gold .917-.986.
# .95 cleanly separates them; .917 (Guldkrone) is gold but the only
# gold below .95 — for those we rely on nominal-text fallback or
# explicit cataloguing. Within `specs.<spec>.finhed`-using pages the
# silver/.95-gold split holds.
METAL_FINHED_THRESHOLD = 0.95

# Nominal-text tokens for metal inference fallback (pages without finhed).
# Order matters: more-specific compounds before generic roots.
GOLD_NOMINAL_TOKENS = (
    "dukat",          # incl. «Dukat», «Ducat», «Halvdukat»
    "pistole",        # Pistole, Friedrichsdor-Pistolen-tier
    "goldgulden",
    "portugaløser", "portugaloser",
    "guldjeton",      # Guldjeton (gold token, Frederik IV)
    "guldkrone",      # Guldkrone (gold-tariff Krone)
    "ungersk gylden", # «ungarsk gylden» — Hungarian-style gold gulden
    "rosenobel",      # English Rose Noble (gold)
    "sovereign",
)
SILVER_NOMINAL_TOKENS = (
    "speciedaler", "speciemark",
    "rigsdaler", "rigsbankdaler",
    "rigsort",
    "mark dansk", "skilling lybsk", "skilling dansk",
    "kurantdaler", "kurantmark", "kurantskilling",
    "halvdaler",
    "krone",   # bare «Krone» when not Guldkrone — assume silver (Corona Danica etc.)
    "daler",   # bare daler — silver Speciedaler ≃ default
    "mark",    # bare Mark (DK silver, when not Guld-prefixed)
    "skilling",  # silver scheidemünze
    "sechsling", "dreiling",
)


def infer_metal_from_nominal(nominal: str | None) -> str | None:
    """Best-effort metal inference from coin nominal text.

    Returns "gold", "silver", or None (ambiguous). Used only when
    the cache page publishes NO finhed at all (rare; ~5 pages).
    """
    if not nominal:
        return None
    n = nominal.lower()
    # Gold-first: «Guld-» compounds beat the bare «-krone» / «-daler» silver match.
    for tok in GOLD_NOMINAL_TOKENS:
        if tok in n:
            return "gold"
    for tok in SILVER_NOMINAL_TOKENS:
        if tok in n:
            return "silver"
    return None


def _collect_finhed_pairs(specs: dict) -> list[tuple[str, float]]:
    """Walk `specs.default` and `specs.by_hede.*` for numeric finhed values.

    Returns list of (sub_hede_num, finhed) pairs. `sub_hede_num` is
    "__default__" for the page-level spec card or the upper-cased
    by_hede key (e.g. "62AB", "68A").
    """
    pairs: list[tuple[str, float]] = []
    if not isinstance(specs, dict):
        return pairs
    default = specs.get("default") or {}
    if isinstance(default, dict):
        fh = default.get("finhed")
        try:
            if fh is not None:
                pairs.append(("__default__", float(fh)))
        except (TypeError, ValueError):
            pass
    by_hede = specs.get("by_hede") or {}
    if isinstance(by_hede, dict):
        for sub_num, sub in by_hede.items():
            if not isinstance(sub, dict):
                continue
            fh = sub.get("finhed")
            try:
                if fh is not None:
                    pairs.append((str(sub_num).upper(), float(fh)))
            except (TypeError, ValueError):
                continue
    return pairs


def parse_hede_id(hid: str) -> tuple[str, str]:
    """Split 'c4h47' → ('c4h', '47'); 'f3h148' → ('f3h', '148'); 'c4h84a' → ('c4h', '84A');
    'f3hej' → ('f3h', 'EJ') (parser-quirk pages with non-numeric Hede id)."""
    m = re.match(r"^([cf]\d+h)(.+)$", hid, re.IGNORECASE)
    if not m:
        return ("", hid)
    return (m.group(1).lower(), m.group(2).upper())


def _build_flagged_record(
    hede_id: str,
    nominal: str,
    ruler: str,
    marks: list[str],
    spec_pairs: list[tuple[str, float]],
) -> dict | None:
    """Construct a flagged-page record. Returns None if metal cannot be inferred."""
    vol, filename_num = parse_hede_id(hede_id)
    # Matchable numbers: filename number + every by_hede sub-key
    matchable: list[str] = []
    if filename_num:
        matchable.append(filename_num)
    sub_finhed: list[float] = []
    for sub_num, fh in spec_pairs:
        sub_finhed.append(fh)
        if sub_num != "__default__":
            matchable.append(sub_num)
    matchable_unique = sorted(set(matchable))

    if spec_pairs:
        # Use min finhed: silver mother coins flagged at lowest fineness;
        # gold mother coins all at ~.979-.986 → threshold split unaffected.
        finhed = min(sub_finhed)
        spec_card_metal = "silver" if finhed < METAL_FINHED_THRESHOLD else "gold"
        inference = "specs"
    else:
        finhed = None
        spec_card_metal = infer_metal_from_nominal(nominal) or "unknown"
        inference = "nominal-text" if spec_card_metal != "unknown" else "ambiguous"

    return {
        "hede_id": hede_id,
        "hede_volume": vol,
        "matchable_numbers": matchable_unique,
        "nominal": nominal,
        "ruler": ruler,
        "finhed_spec_card": finhed,
        "off_strike_marks": sorted(set(m.lower() for m in marks)),
        "spec_card_metal": spec_card_metal,
        "inference": inference,
    }


def scan_hede_pages() -> list[dict]:
    """Walk Hede cache, return list of flagged-page records (one per cache file)."""
    flagged: list[dict] = []
    for path in sorted(CACHE.glob("*.json")):
        try:
            with path.open() as f:
                d = json.load(f)
        except (json.JSONDecodeError, OSError):
            continue
        hede_id = path.stem
        # Combine text fields to search for off-strike markers
        texts = [
            d.get("description", "") or "",
            d.get("raw_text", "") or "",
        ]
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
        specs = d.get("specs") or {}
        spec_pairs = _collect_finhed_pairs(specs)
        nominal = d.get("nominal", "") or ""
        ruler = d.get("ruler", "") or d.get("ruler_inferred", "") or ""
        record = _build_flagged_record(hede_id, nominal, ruler, marks, spec_pairs)
        if record is None:
            continue
        flagged.append(record)
    return flagged


def find_curated_victims(flagged_pages: list[dict]) -> list[dict]:
    """Curated coins matching a flagged page at opposite metal."""
    victims: list[dict] = []
    flagged_by_pair: dict[tuple[str, str], dict] = {}
    for fp in flagged_pages:
        if fp["spec_card_metal"] == "unknown":
            # Cannot reliably cross-ref pages with ambiguous metal
            continue
        vol = fp["hede_volume"]
        for num in fp["matchable_numbers"]:
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
            hede_volume = (cat.get("hede_volume") or "").lower()
            if not hede_field or not hede_volume:
                continue
            hede_list = [hede_field] if not isinstance(hede_field, list) else hede_field
            for hv in hede_list:
                key = (hede_volume, str(hv).upper())
                if key not in flagged_by_pair:
                    continue
                fp = flagged_by_pair[key]
                coin_metal = coin.get("metal", "")
                spec_metal = fp["spec_card_metal"]
                if coin_metal == spec_metal:
                    continue  # same metal — normal mother-coin entry, not a trap
                victims.append({
                    "location": loc_path.stem,
                    "coin_id": coin.get("id", "?"),
                    "coin_metal": coin_metal,
                    "coin_nominal": coin.get("nominal", ""),
                    "coin_year_label": coin.get("year_label", ""),
                    "hede_id": fp["hede_id"],
                    "hede_ref": f"{hede_volume}{hv}",
                    "hede_volume": hede_volume,
                    "hede_nominal": fp["nominal"],
                    "spec_card_metal": spec_metal,
                    "spec_card_finhed": fp["finhed_spec_card"],
                    "spec_card_inference": fp["inference"],
                    "off_strike_marks": fp["off_strike_marks"],
                })
    return victims


# --- self-test ----------------------------------------------------------

def _self_test() -> int:
    """Synthesise both bidirectional traps and verify the audit flags them.

    Returns 0 if both directions correctly flagged; 1 otherwise.
    """
    # Direction A: silver spec card + Guldafslag, curated gold coin
    silver_page = _build_flagged_record(
        hede_id="c4h47",  # real prototype
        nominal="16 Skilling",
        ruler="Frederik 4.",
        marks=["Guldafslag"],
        spec_pairs=[("__default__", 0.667)],
    )
    # Direction B: gold spec card + Sølvafslag, curated silver coin
    gold_page = _build_flagged_record(
        hede_id="f3h36",  # real, currently flagged
        nominal="10 Dukat",
        ruler="Frederik 3.",
        marks=["Sølvafslag"],
        spec_pairs=[("__default__", 0.979)],
    )
    # Direction C: nominal-text fallback (no finhed) — silver Speciedaler
    nominal_only = _build_flagged_record(
        hede_id="f3h62",  # real, currently uses by_hede only
        nominal="1, 2, 3 og 4 Speciedaler",
        ruler="Frederik 3.",
        marks=["Guldafslag"],
        spec_pairs=[],  # simulate no finhed → nominal fallback
    )

    pages = [silver_page, gold_page, nominal_only]
    ok = True
    if silver_page["spec_card_metal"] != "silver":
        print(f"FAIL: silver-spec-card direction — got {silver_page['spec_card_metal']!r}")
        ok = False
    if gold_page["spec_card_metal"] != "gold":
        print(f"FAIL: gold-spec-card direction — got {gold_page['spec_card_metal']!r}")
        ok = False
    if nominal_only["spec_card_metal"] != "silver":
        print(f"FAIL: nominal-text fallback (Speciedaler→silver) — got {nominal_only['spec_card_metal']!r}")
        ok = False
    if nominal_only["inference"] != "nominal-text":
        print(f"FAIL: nominal-text inference flag — got {nominal_only['inference']!r}")
        ok = False

    # Synthesised curated coin matching each (in-memory, no YAML mutation):
    # silver-page victim = gold coin claiming c4h47
    synth_victims = [
        {"coin_metal": "gold", "page": silver_page, "label": "gold→silver-page (Guldafslag)"},
        {"coin_metal": "silver", "page": gold_page, "label": "silver→gold-page (Sølvafslag)"},
        {"coin_metal": "gold", "page": nominal_only, "label": "gold→nominal-silver-page (Guldafslag)"},
    ]
    for sv in synth_victims:
        page = sv["page"]
        flagged_by_pair = {(page["hede_volume"], n): page for n in page["matchable_numbers"]}
        key = (page["hede_volume"], page["matchable_numbers"][0])
        if key not in flagged_by_pair:
            print(f"FAIL: lookup key missing for {sv['label']}")
            ok = False
            continue
        if sv["coin_metal"] == page["spec_card_metal"]:
            print(f"FAIL: would not trip — coin metal matches spec for {sv['label']}")
            ok = False
            continue
        # OK — opposite-metal detected
        print(f"PASS: {sv['label']} → would flag (page {page['hede_id']}, "
              f"spec_metal={page['spec_card_metal']}, coin_metal={sv['coin_metal']})")
    return 0 if ok else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--hede-only", action="store_true",
                    help="report flagged Hede pages without curated cross-ref")
    ap.add_argument("--self-test", action="store_true",
                    help="run synthetic bidirectional sanity check (no I/O on data/)")
    args = ap.parse_args()

    if args.self_test:
        return _self_test()

    flagged_pages = scan_hede_pages()

    if args.hede_only:
        if args.json:
            print(json.dumps(
                {"flagged_pages": flagged_pages, "count": len(flagged_pages)},
                indent=2, ensure_ascii=False,
            ))
        else:
            print(f"Flagged Hede pages with off-strike markers: {len(flagged_pages)}")
            # Group by spec_card_metal for readability
            by_metal: dict[str, list[dict]] = {}
            for fp in flagged_pages:
                by_metal.setdefault(fp["spec_card_metal"], []).append(fp)
            for metal in ("silver", "gold", "unknown"):
                if metal not in by_metal:
                    continue
                print(f"\n  --- spec_card {metal} ({len(by_metal[metal])}) ---")
                for fp in by_metal[metal]:
                    finhed_str = (f"{fp['finhed_spec_card']:.3f}"
                                  if fp["finhed_spec_card"] is not None else "n/a")
                    print(f"  - {fp['hede_id']}: {fp['nominal']!r} "
                          f"finhed={finhed_str} "
                          f"({fp['inference']}) "
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
        # Summary
        silver_pages = sum(1 for fp in flagged_pages if fp["spec_card_metal"] == "silver")
        gold_pages = sum(1 for fp in flagged_pages if fp["spec_card_metal"] == "gold")
        unknown_pages = sum(1 for fp in flagged_pages if fp["spec_card_metal"] == "unknown")
        print(f"Flagged Hede pages: {len(flagged_pages)} "
              f"(silver-mother {silver_pages}, gold-mother {gold_pages}, "
              f"ambiguous {unknown_pages})")
        print(f"Curated c4h47-trap candidates: {len(victims)}")
        print()
        if not victims:
            print("✓ No curated entries reference a flagged Hede page at opposite metal.")
        else:
            print(f"⚠ {len(victims)} candidate(s) for review (DELETE per CLAUDE.md §9 exclusion #3):")
            for v in victims:
                print(f"  - {v['location']}::{v['coin_id']}")
                print(f"    nominal={v['coin_nominal']!r} year={v['coin_year_label']} "
                      f"metal={v['coin_metal']}")
                fh = v["spec_card_finhed"]
                fh_str = f"{fh:.3f}" if fh is not None else "n/a"
                print(f"    references Hede {v['hede_ref']} (page {v['hede_id']}, "
                      f"spec-card {v['spec_card_metal']}, finhed={fh_str}, "
                      f"inference={v['spec_card_inference']})")
                print(f"    off-strike marks on Hede page: {v['off_strike_marks']}")
                print()
    return 1 if victims else 0


if __name__ == "__main__":
    sys.exit(main())
