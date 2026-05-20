#!/usr/bin/env python3
"""§8a auto-classifier — resolve `fuss: seed_unsorted` foundation
entries into real Müntzfuß + Phase.

Two-signal pipeline:

  1. **Hede yield (primary)** — when the coin carries
     `hede_muentzfuss_yield: {value, unit, basis}`, look up the
     (value, unit) pair in the auto-built grid_stops index from
     `data/shared/fuesse.yml`. Exact match (with ε=0.01 tolerance)
     yields a direct fuss assignment. No fineness/weight math
     needed — Hede 1971 is the canonical source per §0.

  2. **Fineness/weight-Δ math (fallback)** — when no yield is
     available, apply the CLAUDE.md §8a procedure:
       a. Filter fusses by metal.
       b. Compute soll_fein for each fraction under each fuss.
       c. Compute Δ = (coin.fein - soll_fein) / soll_fein.
       d. Pick the fuss with the smallest |Δ| within ±2% envelope.
       e. If |Δ| > 20% under the best match → kind=scheide under
          the parent fuss (Scheidemünze residual).
       f. Otherwise mark «no_fit» and leave as seed_unsorted.

Phase resolution (post-fuss-pick) walks the entity's display
location yamls, finds the phase whose year_from <= coin.year_first
<= year_to under the picked fuss. If multiple locations consume
the entity AND their phase definitions disagree on which phase
covers this year, sets `phase` to dict-form per V2_PIPELINE.md §5.

Modes:
  --dry-run    Print proposals + summary, don't modify data (default).
  --apply      Mutate V2 final entries in place: replaces
               (fuss=seed_unsorted, phase=<source-tag>) with the
               resolved (fuss, phase).

Per-coin output:
  fuss        — resolved Müntzfuß id (was seed_unsorted)
  phase       — resolved phase id (was source-tag like «hede»)
  kind        — kurant / scheide / gedenk (preserved from coin or
                downgraded to scheide via §8a step (e))
  *_reason    — audit trail: signal used (hede_yield / delta_math),
                value, Δ if computed
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import yaml

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
V2_FINAL = PROJECT_ROOT / "data" / "v2" / "final"
V2_LOCATIONS = PROJECT_ROOT / "data" / "v2" / "locations"
FUESSE_YAML = PROJECT_ROOT / "data" / "shared" / "fuesse.yml"

YIELD_TOLERANCE = 0.01   # ±0.01 on grid_stops match (rounds 9.250 to 9.25 etc.)
DELTA_TOLERANCE = 0.02   # ±2% Soll-fein envelope per §8a step 3
SCHEIDE_THRESHOLD = 0.20  # > 20% under → kind=scheide per §8a step 6

# Hede yield UNIT → metal class. Maps each canonical unit to the metal
# we expect that fuss family to use, so the lookup table can be
# pre-filtered before the (value, unit) match.
_UNIT_METAL: dict[str, str] = {
    "speciedaler":      "silver",
    "rigsdaler":        "silver",
    "rigsdaler_kurant": "silver",
    "rigsbankdaler":    "silver",
    "piastre":          "silver",
}

# Manual yield → fuss overrides for ambiguous units. Multiple silver
# yield-units can map to the same fuss (18.5 speciedaler AND 18.5
# rigsbankdaler are both 18½-Fuß), and the same numeric value can
# attach to different fusses across unit families.
_YIELD_TO_FUSS_OVERRIDE: dict[tuple[float, str], str] = {
    # Post-1813 Rigsbankdaler reform — same numerical ratio as Speciedaler-Fuß
    (18.5, "rigsbankdaler"): "18_5_thaler",
}


def _load_fuesse() -> dict[str, dict]:
    """Load fuesse.yml, drop the seed_unsorted sentinel."""
    raw = yaml.safe_load(FUESSE_YAML.read_text())
    return {fid: fdef for fid, fdef in raw.items() if fid != "seed_unsorted"}


def _build_yield_index(fuesse: dict[str, dict]) -> dict[tuple[float, str], str]:
    """Auto-build `(grid_stops, unit) → fuss_id` index from the fuesse
    catalogue. Each Müntzfuß's `grid_stops` IS its Hede yield value.
    Unit is inferred per metal: silver → speciedaler (default); the
    Kurantmøntfod family (kronemont*) maps to rigsdaler_kurant; gold
    fusses get «dukat» / «pistole» / «krone» depending on the named
    standard.
    """
    index: dict[tuple[float, str], str] = {}
    for fid, fdef in fuesse.items():
        gs = fdef.get("grid_stops")
        metal = fdef.get("metal")
        if gs is None:
            continue
        # Unit inference per fuss-family name
        if metal == "silver":
            if fid.startswith("kronemont"):
                unit = "rigsdaler_kurant"
            else:
                unit = "speciedaler"
        elif metal == "gold":
            # Gold standards rarely show up with Hede yield in our data
            # (gold pages quote brutto/fein in grams, not «Marken fin
            # udbragt til N dukater»). Skip for now — fineness/weight
            # math handles gold via fallback.
            continue
        else:
            continue
        index[(round(float(gs), 5), unit)] = fid
    # Apply manual overrides
    index.update(_YIELD_TO_FUSS_OVERRIDE)
    return index


def _lookup_yield(value: float, unit: str,
                  index: dict[tuple[float, str], str]) -> str | None:
    """Find fuss_id matching (value ± tolerance, unit)."""
    for (idx_v, idx_u), fid in index.items():
        if idx_u != unit:
            continue
        if abs(idx_v - value) <= YIELD_TOLERANCE:
            return fid
    return None


def _normalise_fineness(fineness: Any) -> float | None:
    """Reduce list-form fineness to a single representative value."""
    if isinstance(fineness, (int, float)):
        return float(fineness)
    if isinstance(fineness, list):
        vals: list[float] = []
        for entry in fineness:
            if isinstance(entry, dict) and isinstance(entry.get("value"), (int, float)):
                vals.append(float(entry["value"]))
        if vals:
            # Use median as representative (robust to outliers like c5h110's .671)
            vals.sort()
            return vals[len(vals) // 2]
    return None


def _normalise_weight(weight_rough_g: Any) -> float | None:
    """Median weight reading across multi-source list."""
    if isinstance(weight_rough_g, (int, float)):
        return float(weight_rough_g)
    if isinstance(weight_rough_g, list):
        vals: list[float] = []
        for entry in weight_rough_g:
            if isinstance(entry, dict) and isinstance(entry.get("value"), (int, float)):
                vals.append(float(entry["value"]))
        if vals:
            vals.sort()
            return vals[len(vals) // 2]
    return None


def _parse_fraction(fraction: str | None) -> float | None:
    """Parse «1/12» / «3» / «1.5» / «1/8» into float ratio."""
    if fraction is None or fraction == "":
        return None
    s = str(fraction).strip()
    if "/" in s:
        try:
            num, den = s.split("/", 1)
            return float(num) / float(den)
        except (ValueError, ZeroDivisionError):
            return None
    try:
        return float(s)
    except ValueError:
        return None


# Speciedaler-fraction inference from nominal text — used when a
# coin's structured `fraction` field is missing (D37/D39/D40-promoted
# NumisMaster entries are the common case: NumisMaster catalogues
# don't tag fraction explicitly).
#
# Denomination → fraction (relative to 1 Speciedaler = 1 unit):
#   Speciedaler / Rigsdaler / Krone = 1
#   Mark   = 1/6                 (1 Spd = 6 Mark Lybsk)
#   Skilling = 1/96              (1 Spd = 96 Skilling)
#   Søsling = 1/192              (Søsling = ½ Skilling = 1/192 Spd)
#   Hvid    = 1/288              (Hvid = 1/3 Skilling = 1/288 Spd; pre-1814)
#   Dreiling = 1/288             (Dreiling = ⅓ Skilling)
#   Sechsling = 1/144            (Sechsling = ½ Schilling Lübsk family)
#   Skilling Rigsmønt = 1/96     (post-1813 reform, Speciedaler still 96)
#   Rigsbankskilling = 1/96 (post-1813 Rigsbankdaler-system 96 RbS = 1 RbDl)
#   Øre = 1/100 Krone (post-1873 — handled separately under kronefod)
#   Ducat / Dukat = 1 (gold-standard unit)
#
# Multipliers parsed first («4 Skilling» → 4 × 1/96 = 1/24). Fractional
# multipliers handled («1/2 Skilling» → 0.5 × 1/96 = 1/192).
_DENOMINATION_UNITS: dict[str, float] = {
    # Silver — speciedaler-fraction-equivalent
    "speciedaler":      1.0,
    "rigsdaler":        1.0,
    "rigsbankdaler":    1.0,
    "krone":            1.0,
    "kroner":           1.0,
    "kronen":           1.0,
    "mark":             1.0 / 6,
    "skilling":         1.0 / 96,
    "skillinge":        1.0 / 96,
    "rigsbankskilling": 1.0 / 96,
    "skillingrigsmønt": 1.0 / 96,
    "sechsling":        1.0 / 144,
    "søsling":          1.0 / 192,
    "sosling":          1.0 / 192,
    "hvid":             1.0 / 288,
    "dreiling":         1.0 / 288,
    "penning":          1.0 / 1152,
    "penninge":         1.0 / 1152,
    # Gold — used for reichsdukatenfuss / pistolenfuss / etc.
    "ducat":            1.0,
    "dukat":            1.0,
    "dukaten":          1.0,
    "ducaten":          1.0,
    "pistole":          1.0,
    "pistolen":         1.0,
    "gulden":           1.0,
    "goldgulden":       1.0,
    # Post-1873 Krone-system (handled in fallback for kronefod)
    "øre":              0.01,
    "ore":              0.01,
}


def _infer_speciedaler_fraction_from_nominal(nominal: str | None) -> float | None:
    """Parse «4 Skilling», «1 Speciedaler», «1/2 Krone», «8 Skilling
    Rigsmont», etc. into a Speciedaler-equivalent ratio. Returns None
    when the nominal doesn't match a known denomination word.

    Resolves common Danish-Norwegian coin nomenclature only. Foreign-
    denomination coins (Lion Daler, Asiatic Piastre, etc.) return None
    and stay as `seed_unsorted` for manual classification.
    """
    if not nominal or not isinstance(nominal, str):
        return None
    s = nominal.lower().strip()
    # Strip parenthesised qualifiers like «(2 Skilling = 1/48 Speciedaler)»
    s = re.sub(r"\([^)]*\)", "", s).strip()
    # Strip trailing qualifiers («Skilling Rigsmønt», «Skilling Dansk»,
    # «Skilling Lybsk» — qualifier doesn't change the fraction).
    m = re.match(
        r"^\s*(\d+(?:[\./]\d+)?(?:[½¼¾⅓⅔⅙⅛])?|[½¼¾⅓⅔⅙⅛])\s+([a-zåæøö]+)",
        s,
    )
    if not m:
        # Bare denomination word (no leading multiplier) — assume 1
        for word, unit in _DENOMINATION_UNITS.items():
            if s.startswith(word):
                return unit
        return None
    mult_str = m.group(1)
    denom_word = m.group(2)
    # Parse multiplier
    fraction_glyphs = {"½": 0.5, "¼": 0.25, "¾": 0.75, "⅓": 1/3, "⅔": 2/3,
                       "⅙": 1/6, "⅛": 0.125}
    if mult_str in fraction_glyphs:
        mult = fraction_glyphs[mult_str]
    elif any(g in mult_str for g in fraction_glyphs):
        # E.g. «1½» — integer plus fraction
        mult = 0.0
        for ch in mult_str:
            if ch in fraction_glyphs:
                mult += fraction_glyphs[ch]
            elif ch.isdigit():
                mult = mult * 10 + int(ch)
    elif "/" in mult_str:
        try:
            num, den = mult_str.split("/", 1)
            mult = float(num) / float(den)
        except (ValueError, ZeroDivisionError):
            return None
    else:
        try:
            mult = float(mult_str)
        except ValueError:
            return None
    unit = _DENOMINATION_UNITS.get(denom_word)
    if unit is None:
        return None
    return mult * unit


def _build_location_phase_index() -> dict[str, dict[str, list[tuple[str, int, int]]]]:
    """Walk V2 location yamls; build:
        {entity_id → {fuss_id → [(phase_id, year_from, year_to), ...]}}

    For each entity, the consuming location's phase definitions are
    aggregated. When multiple locations consume the same entity,
    their phase year-ranges combine (first-match wins per coin's year).
    """
    out: dict[str, dict[str, list]] = defaultdict(lambda: defaultdict(list))
    for loc_path in sorted(V2_LOCATIONS.glob("*.yml")):
        loc_doc = yaml.safe_load(loc_path.read_text()) or {}
        consumes = loc_doc.get("consumes_entities") or []
        phases = loc_doc.get("phases") or {}
        for fuss_id, phase_list in phases.items():
            if fuss_id == "seed_unsorted":
                continue
            for ph in (phase_list or []):
                if not isinstance(ph, dict):
                    continue
                pid = ph.get("id")
                yf = ph.get("year_from")
                yt = ph.get("year_to")
                if pid is None or yf is None or yt is None:
                    continue
                for ent in consumes:
                    out[ent][fuss_id].append((pid, int(yf), int(yt)))
    return out


def _resolve_phase(entity_id: str, fuss_id: str, year_first: int | None,
                   phase_index: dict) -> str | None:
    """Find the phase whose year-range covers the coin's year_first.

    Tries the entity's phase definitions for `fuss_id`. Picks the
    phase whose range covers year_first; if multiple match, picks
    the narrowest range (more specific phase).
    """
    if year_first is None:
        return None
    candidates: list[tuple[int, str]] = []  # (range_width, phase_id)
    for pid, yf, yt in (phase_index.get(entity_id) or {}).get(fuss_id, []):
        if yf - 1 <= year_first <= yt + 1:  # ±1y tolerance for boundary years
            width = yt - yf
            candidates.append((width, pid))
    if not candidates:
        return None
    candidates.sort()  # narrowest first
    return candidates[0][1]


def _classify_via_yield(coin: dict, yield_index: dict) -> tuple[str, str | None, dict]:
    """Apply Hede-yield direct lookup. Returns (signal, fuss_id, audit)."""
    yld = coin.get("hede_muentzfuss_yield")
    if not yld:
        return ("no_yield", None, {})
    value = yld.get("value")
    unit = yld.get("unit")
    if not isinstance(value, (int, float)) or not unit:
        return ("yield_malformed", None, {})
    fuss_id = _lookup_yield(float(value), unit, yield_index)
    audit = {"hede_yield_value": float(value), "hede_yield_unit": unit}
    if fuss_id is None:
        return ("yield_unmapped", None, audit)
    audit["matched_fuss"] = fuss_id
    return ("hede_yield", fuss_id, audit)


def _fuesse_with_phase_for_year(entity_id: str, year_first: int | None,
                                  phase_index: dict) -> set[str] | None:
    """Return the set of fuss_ids for which the entity's display
    locations declare at least one phase covering `year_first`. None
    when year_first is unknown (no year filter applied).

    Used to constrain delta-math candidate fuss search to era-
    plausible options (CLAUDE.md §8a step 2 «denomination-name
    mismatch» becomes «year-era mismatch» here: a 1670 coin can't
    fall under a fuss whose phases only run 1618-1660, regardless of
    how cleanly the math fits).
    """
    if year_first is None:
        return None
    ent_phases = phase_index.get(entity_id) or {}
    if not ent_phases:
        return None
    fuesse_ok: set[str] = set()
    for fid, phase_list in ent_phases.items():
        for _pid, yf, yt in phase_list:
            if yf - 1 <= year_first <= yt + 1:
                fuesse_ok.add(fid)
                break
    return fuesse_ok


def _classify_via_delta(coin: dict, fuesse: dict[str, dict],
                         entity_id: str | None = None,
                         phase_index: dict | None = None) -> tuple[str, str | None, dict]:
    """Apply fineness/weight-Δ fallback math per CLAUDE.md §8a.

    Returns (signal, fuss_id, audit) where signal is one of:
      - delta_confident: |Δ| < 1% AND unique candidate
      - delta_low_conf: |Δ| 1-2% (within tolerance, weaker signal)
      - delta_scheide: |Δ| > 20% under → kind=scheide
      - delta_no_fit: nothing within ±2%
      - no_data: missing fineness or weight
    """
    metal = coin.get("metal")
    fineness = _normalise_fineness(coin.get("fineness"))
    weight = _normalise_weight(coin.get("weight_rough_g"))
    fraction = _parse_fraction(coin.get("fraction"))
    fraction_source = "field"

    # When the structured fraction field is missing (typical for D37/
    # D39/D40-promoted NumisMaster entries), infer from nominal text.
    if fraction is None:
        fraction = _infer_speciedaler_fraction_from_nominal(coin.get("nominal"))
        if fraction is not None:
            fraction_source = "inferred_from_nominal"

    audit: dict[str, Any] = {
        "metal": metal,
        "fineness": fineness,
        "weight_g": weight,
        "fraction": fraction,
        "fraction_source": fraction_source,
        "nominal": coin.get("nominal"),
    }

    if not metal or fineness is None or weight is None or fraction is None:
        return ("no_data", None, audit)

    coin_fein = fineness * weight
    audit["coin_fein_g"] = round(coin_fein, 5)

    # Era filter: when phase-index + year_first available, restrict
    # candidate fusses to those whose phases cover this coin's year
    # in the entity's display locations. Stops «1670 Skilling →
    # kronemont_chr_iv» (Chr IV-era fuss) misclassifications.
    year_first = coin.get("year_first")
    era_filter: set[str] | None = None
    if entity_id and phase_index is not None and year_first is not None:
        era_filter = _fuesse_with_phase_for_year(entity_id, year_first, phase_index)
        if era_filter is not None:
            audit["era_filter_fuesse"] = sorted(era_filter)

    # Compute Δ vs each fuss's soll_fein for this fraction
    candidates: list[tuple[float, str, float]] = []  # (abs_delta, fuss_id, delta_g)
    for fid, fdef in fuesse.items():
        if fdef.get("metal") != metal:
            continue
        if era_filter is not None and fid not in era_filter:
            continue
        grid_stops = fdef.get("grid_stops")
        grid_unit_g = fdef.get("grid_unit_g")
        fine_std = fdef.get("fineness_standard")
        if grid_stops is None or grid_unit_g is None or fine_std is None:
            continue
        # soll_fein per 1-unit coin = grid_unit_g × fineness_standard / grid_stops
        soll_fein_one = (grid_unit_g * fine_std) / grid_stops
        soll_fein = soll_fein_one * fraction
        if soll_fein <= 0:
            continue
        delta_g = coin_fein - soll_fein
        delta_pct = delta_g / soll_fein
        candidates.append((abs(delta_pct), fid, delta_pct))

    if not candidates:
        return ("no_data", None, audit)

    candidates.sort()
    best_abs, best_fid, best_delta = candidates[0]

    audit["best_fuss"] = best_fid
    audit["best_delta_pct"] = round(best_delta * 100, 2)
    if len(candidates) >= 2:
        audit["runner_up_fuss"] = candidates[1][1]
        audit["runner_up_delta_pct"] = round(candidates[1][2] * 100, 2)

    # Scheidemünze residual: best |Δ| > 20% under
    if best_delta < -SCHEIDE_THRESHOLD:
        audit["scheide_residual"] = True
        return ("delta_scheide", best_fid, audit)

    if best_abs <= 0.01:
        return ("delta_confident", best_fid, audit)
    if best_abs <= DELTA_TOLERANCE:
        return ("delta_low_conf", best_fid, audit)
    return ("delta_no_fit", None, audit)


def _classify_via_era_anchor(coin: dict, entity_id: str | None
                              ) -> tuple[str, str | None, str | None, dict]:
    """Era-anchor rule: post-1813 Danish-realm Skilling / Rigsbank-*
    coins unambiguously belong to 18_5_thaler (Rigsbankdaler reform).

    The fineness/weight-Δ math fails on these when fineness is missing
    (typical for copper Scheide entries from NumisMaster) AND when the
    Hede-yield path doesn't fire (no Hede-attested «Marken … udbragt
    til N» yield). Year + denomination + entity, however, uniquely
    determine the fuss — Frederik VI's Forordning af 5. Januar 1813
    established 18½-Thaler-Fuß as the sole Danish-realm standard for
    Rigsbankdaler / Rigsbankskilling. By extension Tn-token KMs
    (Krause's classification for crown-issued small-change in this
    era) also fall under this Fuß as Scheidemünze.

    Returns (signal, fuss_id, kind, audit). Signal is one of:
      - era_anchor — applied (returns 18_5_thaler + kind by metal)
      - no_match — rule does not fire (year/entity/nominal don't fit)
    """
    audit: dict = {"rule": "era_anchor"}
    year_first = coin.get("year_first")
    if not isinstance(year_first, int) or year_first < 1813:
        return ("no_match", None, None, audit)
    if entity_id not in {"danish_realm", "royal_holstein", "danish_norway"}:
        return ("no_match", None, None, audit)
    nominal = str(coin.get("nominal") or "").lower()
    # Denomination patterns for 18½-Thaler-Fuß post-1813:
    #   Rigsbankdaler / Rigsbankskilling (the canonical units)
    #   bare «Skilling» (Krause Tn-tokens carry plain «Skilling»;
    #                    1813+ «Skilling» is by definition
    #                    Rigsbankskilling per the Forordning)
    #   Skilling Rigsmønt (the post-1854 currency-tag variant)
    if not any(tok in nominal for tok in (
            "rigsbank", "rigsbanktegn", "rigsbankdaler",
            "skilling rigsmønt", "skilling")):
        return ("no_match", None, None, audit)
    metal = coin.get("metal")
    if metal == "silver":
        kind = "kurant"
    elif metal in ("copper", "billon", "bronze"):
        kind = "scheide"
    else:
        # Unknown metal — apply anyway as kurant by default; curator
        # can override via classification_decisions.
        kind = "kurant"
    audit.update({
        "year_first": year_first,
        "entity": entity_id,
        "metal": metal,
        "nominal": coin.get("nominal"),
    })
    return ("era_anchor", "18_5_thaler", kind, audit)


def classify_coin(coin: dict, fuesse: dict, yield_index: dict,
                  entity_id: str | None = None,
                  phase_index: dict | None = None) -> dict:
    """Run both signal paths; return decision dict."""
    decision: dict[str, Any] = {
        "coin_id": coin.get("id"),
        "nominal": coin.get("nominal"),
        "year_first": coin.get("year_first"),
        "ruler": coin.get("ruler"),
        "current_fuss": coin.get("fuss"),
        "current_phase": coin.get("phase"),
        "current_kind": coin.get("kind"),
    }

    # Primary: Hede yield
    yld_signal, yld_fuss, yld_audit = _classify_via_yield(coin, yield_index)
    if yld_fuss:
        decision["proposed_fuss"] = yld_fuss
        decision["signal"] = yld_signal  # hede_yield
        decision["audit"] = yld_audit
        return decision

    # Era-anchor: post-1813 Danish-realm Skilling / Rigsbank → 18_5_thaler
    era_signal, era_fuss, era_kind, era_audit = _classify_via_era_anchor(
        coin, entity_id)
    if era_fuss:
        decision["proposed_fuss"] = era_fuss
        if era_kind:
            decision["proposed_kind"] = era_kind
        decision["signal"] = era_signal
        decision["audit"] = era_audit
        return decision

    # Fallback: fineness/weight-Δ
    delta_signal, delta_fuss, delta_audit = _classify_via_delta(
        coin, fuesse, entity_id=entity_id, phase_index=phase_index)
    if delta_fuss:
        decision["signal"] = delta_signal
        decision["audit"] = delta_audit
        if delta_signal == "delta_scheide":
            decision["proposed_fuss"] = delta_fuss
            decision["proposed_kind"] = "scheide"
        else:
            decision["proposed_fuss"] = delta_fuss
    else:
        # No fit
        decision["signal"] = delta_signal if delta_signal != "no_data" else yld_signal
        decision["audit"] = delta_audit if delta_audit else yld_audit

    return decision


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--apply", action="store_true",
                    help="Mutate V2 final entries (default: dry-run)")
    ap.add_argument("--entity",
                    help="Process only this entity (e.g. danish_realm)")
    ap.add_argument("--limit", type=int, default=0,
                    help="Process only first N coins per entity (debug)")
    ap.add_argument("--show", choices=("all", "applied", "skipped"),
                    default="applied",
                    help="Which classifications to print")
    args = ap.parse_args()

    fuesse = _load_fuesse()
    yield_index = _build_yield_index(fuesse)
    phase_index = _build_location_phase_index()

    print(f"Loaded {len(fuesse)} Müntzfüße from fuesse.yml")
    print(f"Yield index: {len(yield_index)} (value, unit) → fuss entries")
    print(f"Phase index: {len(phase_index)} entities with location-mapped phases")
    print()
    if yield_index:
        sample = sorted(yield_index.items())[:10]
        print("Yield index sample:")
        for (v, u), fid in sample:
            print(f"  ({v}, {u}) → {fid}")
        print()

    by_entity: dict[str, list[dict]] = {}
    total = 0
    classified = 0
    by_signal: Counter = Counter()
    by_outcome: Counter = Counter()

    paths = [V2_FINAL / f"{args.entity}.yml"] if args.entity else sorted(V2_FINAL.glob("*.yml"))
    for path in paths:
        if not path.exists():
            print(f"  [skip] {path} not found")
            continue
        ent_id = path.stem
        doc = yaml.safe_load(path.read_text()) or {}
        coins = doc.get("coins") or []
        entity_decisions: list[dict] = []
        seed_unsorted_count = 0
        for coin in coins:
            if coin.get("fuss") != "seed_unsorted":
                continue
            seed_unsorted_count += 1
            if args.limit and seed_unsorted_count > args.limit:
                break
            decision = classify_coin(coin, fuesse, yield_index,
                                     entity_id=ent_id, phase_index=phase_index)
            decision["entity_id"] = ent_id
            # Phase resolution
            if decision.get("proposed_fuss"):
                year_first = decision.get("year_first")
                phase_id = _resolve_phase(ent_id, decision["proposed_fuss"],
                                          year_first, phase_index)
                if phase_id:
                    decision["proposed_phase"] = phase_id
                else:
                    decision["proposed_phase_status"] = "no_matching_phase_in_consumer_locations"
            entity_decisions.append(decision)
            total += 1
            by_signal[decision.get("signal", "unknown")] += 1
            if decision.get("proposed_fuss") and decision.get("proposed_phase"):
                by_outcome["READY"] += 1
                classified += 1
            elif decision.get("proposed_fuss"):
                by_outcome["FUSS_OK_PHASE_GAP"] += 1
            else:
                by_outcome["SKIPPED"] += 1
        by_entity[ent_id] = entity_decisions

    print(f"\n=== Summary ===")
    print(f"  seed_unsorted entries walked: {total}")
    print(f"  fully-classified (fuss + phase): {classified}")
    print()
    print("  Outcomes:")
    for k, n in by_outcome.most_common():
        print(f"    {k:30s} {n}")
    print()
    print("  Signal distribution:")
    for sig, n in by_signal.most_common():
        print(f"    {sig:30s} {n}")
    print()

    # Per-entity tally
    print("  Per-entity outcomes:")
    for ent, decisions in by_entity.items():
        if not decisions:
            continue
        ready = sum(1 for d in decisions if d.get("proposed_fuss") and d.get("proposed_phase"))
        partial = sum(1 for d in decisions if d.get("proposed_fuss") and not d.get("proposed_phase"))
        skipped = sum(1 for d in decisions if not d.get("proposed_fuss"))
        print(f"    {ent:35s} ready={ready:4d}  fuss-only={partial:4d}  skipped={skipped:4d}")

    # Show samples
    print()
    if args.show in ("all", "applied"):
        print("  Sample READY classifications (first 15):")
        n_shown = 0
        for ent, decisions in by_entity.items():
            for d in decisions:
                if d.get("proposed_fuss") and d.get("proposed_phase"):
                    print(f"    {ent}/{d['coin_id']}: nominal={d.get('nominal')!r} "
                          f"yr={d.get('year_first')}  "
                          f"→ fuss={d['proposed_fuss']} phase={d['proposed_phase']}  "
                          f"signal={d.get('signal')}")
                    n_shown += 1
                    if n_shown >= 15:
                        break
            if n_shown >= 15:
                break

    if args.show in ("all", "skipped"):
        print()
        print("  Sample SKIPPED entries (first 10) — need manual review:")
        n_shown = 0
        for ent, decisions in by_entity.items():
            for d in decisions:
                if not d.get("proposed_fuss"):
                    print(f"    {ent}/{d['coin_id']}: nominal={d.get('nominal')!r} "
                          f"yr={d.get('year_first')}  "
                          f"signal={d.get('signal')}  audit={d.get('audit')}")
                    n_shown += 1
                    if n_shown >= 10:
                        break
            if n_shown >= 10:
                break

    if args.apply:
        # Apply classifications: mutate V2 final entries
        write_count = 0
        for ent, decisions in by_entity.items():
            if not decisions:
                continue
            path = V2_FINAL / f"{ent}.yml"
            doc = yaml.safe_load(path.read_text()) or {}
            coins = doc.get("coins") or []
            applied_ids = {d["coin_id"]: d for d in decisions
                           if d.get("proposed_fuss") and d.get("proposed_phase")}
            mutated = 0
            for coin in coins:
                cid = coin.get("id")
                if cid not in applied_ids:
                    continue
                d = applied_ids[cid]
                coin["fuss"] = d["proposed_fuss"]
                coin["phase"] = d["proposed_phase"]
                if d.get("proposed_kind"):
                    coin["kind"] = d["proposed_kind"]
                mutated += 1
            if mutated:
                doc["coins"] = coins
                # Pretty-write keeping the existing flow style
                ruamel_yaml_str = yaml.dump(
                    doc, allow_unicode=True, sort_keys=False, width=120,
                    default_flow_style=False,
                )
                path.write_text(ruamel_yaml_str)
                print(f"  wrote {ent}: {mutated} coins reclassified")
                write_count += mutated
        print(f"\n✓ Applied {write_count} classifications across {len(by_entity)} entit(y/ies)")
    else:
        print("\n  [dry-run — no files written. Re-run with --apply to commit.]")

    return 0


if __name__ == "__main__":
    sys.exit(main())
