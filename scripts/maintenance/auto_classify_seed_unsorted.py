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
    # Christian-III-Dalerfod / Flensborg-fod era (1524-1571): 1 Sølvgylden
    # = 1/3 Daler under the 8-Daler-per-marck grid (cf. fuesse.yml
    # christian_iii_dalerfod fractions «1/3»: soll_rau 9.744 g; same
    # 1/3 ratio in flensborg_fod). 1 Gylden (Flensborg Lybsk variant) is
    # also 1/3 Daler — same physical specimen, different sub-mark
    # accounting (24 ß lybsk vs 48 ß danske).
    "sølvgylden":       1.0 / 3,
    "solvgylden":       1.0 / 3,
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
        # Defensive filter: skip mint-bound Fußen whose binding doesn't
        # match this coin's mint+ruler. Prevents false positives like
        # f2h8a (Kbh Speciedaler 1560 Frederik II) being assigned to
        # christian_iii_flensborg_fod just because the Δ happens to be
        # 1.75 % — the historical attribution requires Flensburg mint +
        # Christian III ruler.
        if fid in _MINT_BOUND_FUSSES:
            if not _coin_matches_mint_binding(coin, _MINT_BOUND_FUSSES[fid]):
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


# Denomination-anchor rule table — coins whose nominal text uniquely
# identifies a Müntzfuß within the Danish-Norwegian register, with no
# possibility of cross-Fuß ambiguity. Each entry is matched in order,
# first-match wins.
#
# Adding a new rule requires verifying TWO conditions in the data:
#   (a) the denomination string only appears in this Fuß family
#       across all Danish-Norwegian seeds (`grep nominal: data/v2/final`)
#   (b) the optional year_max (if set) cleanly separates this Fuß from
#       a sibling Fuß that shares the denomination but covers a
#       different period (the Ungersk Gylden 1527-1559 → goldgulden_fod
#       vs. 1559+ → reichsdukatenfuss case).
#
# Patterns are case-insensitive substring matches on the lowercased
# `nominal` field. Order matters — narrower patterns must precede
# broader ones (Rosenobel before Nobel, etc.).
_DENOMINATION_ANCHOR_RULES: list[dict] = [
    # Rhinsk Gylden / Rhinsk Gulden — uniquely the Rhenish-Gulden
    # standard. Appears as «1 Rhinsk Gylden», «1 Rhinsk gylden»,
    # «Goldgulden (Rhinsk Gulden)» (Bruun alt spelling), «Gold Gulden
    # (Rhinsk Gylden)». Covers Phase 0 (Christian III 1536 Roskilde),
    # Phase I (Frederik II 1563-1564), Phase II (Christian IV
    # 1625-1632).
    {"patterns": ["rhinsk gylden", "rhinsk gulden"],
     "fuss": "rhinsk_gylden_fod",
     "kind": "kurant",
     "rationale": "Rhinsk-Gylden — unique to rhinsk_gylden_fod"},

    # Rosenobel — uniquely the Rose-Noble-Renaissance-adaptation.
    # Covers «1 Rosenobel» (Frederik II 1584 + Christian IV 1611-1629)
    # + «½ Rosenobel» (Christian IV 1611, period nickname Guldridder).
    # MUST precede the Nobel rule below — otherwise «Rosenobel» would
    # false-positive on the bare «Nobel» substring check.
    {"patterns": ["rosenobel"],
     "fuss": "rosenobel_fod",
     "kind": "kurant",
     "rationale": "Rosenobel — unique to rosenobel_fod"},

    # Nobel (Sovereign-tier prestige, NOT Rosenobel). Covers Hans
    # 1496-1502 + Christian II 1516-1518 + Frederik I 1532 + undated
    # Ribe Galster 68/69. The Rosenobel rule above eats «Rosenobel»
    # first, so this rule only fires on bare «Nobel» / «1 Nobel».
    {"patterns": ["nobel"],
     "fuss": "nobel_fod",
     "kind": "kurant",
     "rationale": "Nobel (Sovereign-tier) — unique to nobel_fod after Rosenobel-rule eats Rosenobel"},

    # Ungersk Gylden / Ungersk gylden — uniquely the
    # Hungarian-Venetian Dukat standard. Post 2026-05-21 merger of
    # goldgulden_fod into reichsdukatenfuss: ALL Ungersk Gylden
    # specimens (pre- and post-1559) route to reichsdukatenfuss.
    # The Fuß has Phase pre-I (1514-1558 mission-scope-clipped,
    # actual 1481-1558) for de facto Hungarian Goldgulden tradition,
    # and Phase I (1559+) for post-Augsburger codification. The
    # build's year-window phase resolver places specimens in the
    # correct phase by year_first.
    {"patterns": ["ungersk gylden", "ungersk gulden"],
     "fuss": "reichsdukatenfuss",
     "kind": "kurant",
     "rationale": "Ungersk Gylden → reichsdukatenfuss (merged 2026-05-21 — pre-I phase covers pre-1559 de facto; Phase I covers post-1559 codification; specimen-drift .972 vs .986 is period remedium per Wikipedia Sophie of Mecklenburg-Güstrow)"},

    # Sølvgylden / Silver Gulden — uniquely the Christian II
    # Lovkompleks Hauptkurant silver coin (1514-1523). Covers
    # variant spellings: «1 Sølvgylden», «Halv Sølvgylden»,
    # «1½ Sølvgylden», «¼ Sølvgylden», «Silver Gulden» (Bruun
    # English spelling), «1 Gulden» (Numista variant). year_max
    # not strictly required — post-1523 Sølvgylden is rare and
    # falls under Frederik I's reign anyway (the f1g specimens
    # belong to the SAME 14-Lod Hauptkurant tradition since
    # Frederik I's 1524 ordinance preserves the .875 fineness on
    # the silver side per Wilcke 7-2 p. 187). When `frederik_i_
    # dalerfod` lands as a separate Fuß, this rule will need a
    # year_max=1523 split similar to the Ungersk Gylden case.
    # For now (until §BY Fuß 2 lands), Sølvgylden routes to
    # 8_5_gylden_fod globally.
    {"patterns": ["sølvgylden", "solvgylden", "silver gulden"],
     "fuss": "8_5_gylden_fod",
     "kind": "kurant",
     "year_max": 1523,
     "rationale": "Sølvgylden ≤1523 — Christian II Lovkompleks Hauptkurant silver (post-1523 splits to 8_gylden_fod)"},

    # Sølvgylden / Silver Gulden continuation 1524-1533 —
    # uniquely the Frederik I Dalerfod Hauptkurant. Same physical
    # standard (14 Lod / .875) as Christian II Lovkompleks but
    # tightened to 8/M (vs 8½/M); see 8_gylden_fod
    # fuesse.yml entry. year_min=1524 + year_max=1533 (Frederik I's
    # death 10 April 1533).
    {"patterns": ["sølvgylden", "solvgylden", "silver gulden"],
     "fuss": "8_gylden_fod",
     "kind": "kurant",
     "year_min": 1524,
     "year_max": 1533,
     "rationale": "Sølvgylden 1524-1533 — Frederik I Dalerfod (post-Lovkompleks; pre-Grevens-Fejde)"},

    # 14 Penning / 14 Penny — uniquely Frederik I's Klipping
    # redemption coin under the separate act of 26 February 1524
    # (Wilcke 7-2 p. 187). The «14 %» small-change subtype was
    # introduced specifically to exchange Christian II's Klippinge
    # for new Frederik I tokens. Year range 1524-1532 (Frederik I's
    # reign as king); Numista + Bruun specimens cluster around
    # Copenhagen + Malmö 1524.
    {"patterns": ["14 penning", "14 penny"],
     "fuss": "8_gylden_fod",
     "kind": "scheide",
     "year_min": 1523,
     "year_max": 1533,
     "rationale": "14 Penning Klipping-Indfrielse-Mønt 1524 — Frederik I Dalerfod (separate act 26 Feb 1524, Wilcke 7-2 p. 187)"},
]


# Mint-bound Müntzfüße — fusses whose definition pins the standard to a
# specific mint+ruler combination, not just an era. Coins from other
# mints (even within the same era and entity) MUST NOT auto-classify
# into these Fußen even when the Δ-math accidentally fits — the
# physical attribution is the historical anchor.
#
# Used by TWO mechanisms:
#  (a) _classify_via_mint_anchor — positive promotion: when a coin's
#      (mint, ruler-substring, year-range) hits a registry entry,
#      assign that Fuß directly without delta-math.
#  (b) _classify_via_delta — defensive filter: skip any candidate
#      Fuß whose mint-binding doesn't match the coin's mint+ruler.
#
# Each entry's `kind_by_nominal` callback derives kind from the
# coin's nominal at classification time (e.g. Søsling lybsk → scheide;
# Daler / Sølvgylden / Rhinsk Gylden → kurant).
_MINT_BOUND_FUSSES: dict[str, dict] = {
    # Christian-III-Flensborg-fod — Flensborg mint, Christian III only,
    # 1545-1571 (1545-1554 main phase, 1554-1571 tail under Frederik II
    # — but specimens 1554+ are Frederik II issues, NOT auto-classified
    # to this Fuß without explicit curator decision; the registry pins
    # promotion to Christian III only, with year_max=1559 covering his
    # death 1559-01-01 + a 1 y boundary buffer).
    #
    # Source: Wilcke 1950 pp. 25-26 (Flensborg Bestalling 22 Jan 1547),
    # fuesse.yml christian_iii_flensborg_fod definition. Mint variants
    # tolerated: «Flensburg» (German/English) / «Flensborg» (Danish).
    # Ruler match: substring «Christian III» (covers «Christian III.»,
    # «Christian III», «Christian III. of Denmark», etc.).
    "christian_iii_flensborg_fod": {
        "allowed_mints": {"Flensburg", "Flensborg"},
        "ruler_substring": "Christian III",
        "year_min": 1545,
        "year_max": 1559,
        "allowed_entities": {"royal_holstein", "danish_realm"},
        "phase": "I",
        "kind_by_nominal": lambda n: (
            "scheide" if any(t in (n or "").lower() for t in
                              ("søsling", "sosling", "hvid", "penning", "skilling"))
            else "kurant"
        ),
        "rationale": "Christian-III-Flensborg-fod — mint=Flensburg + ruler=Christian III (Wilcke 1950 pp. 25-26)",
    },
}


def _coin_matches_mint_binding(coin: dict, binding: dict) -> bool:
    """True if the coin's mint + ruler + year + entity match the
    binding's constraints. Used by both the anchor rule (positive
    promotion) and the delta-math filter (defensive guard).
    """
    mint = coin.get("mint")
    # Mint may be scalar or list — match if any element is in allowed
    mints = mint if isinstance(mint, list) else ([mint] if mint else [])
    if not any(m in binding.get("allowed_mints", set()) for m in mints):
        return False
    ruler = str(coin.get("ruler") or "")
    if binding.get("ruler_substring") and binding["ruler_substring"] not in ruler:
        return False
    year_first = coin.get("year_first")
    ymin = binding.get("year_min")
    ymax = binding.get("year_max")
    if ymin is not None and (not isinstance(year_first, int) or year_first < ymin - 1):
        return False
    if ymax is not None and (not isinstance(year_first, int) or year_first > ymax + 1):
        return False
    return True


def _classify_via_mint_anchor(coin: dict, entity_id: str | None
                                ) -> tuple[str, str | None, str | None, dict]:
    """Mint-anchor rule: when a coin's (mint, ruler, year, entity) hits
    a `_MINT_BOUND_FUSSES` registry entry, assign that Fuß directly.

    Runs BEFORE delta-math AND before grevens_fejde_anchor: mint-binding
    is the strongest signal we have for fusses anchored to a specific
    physical mint (Flensborg, Glückstadt, Altona, Husum, …) — when it
    fires it's authoritative.

    Returns (signal, fuss_id, kind, audit). Signal is one of:
      - mint_anchor — applied (returns Fuß + Phase + kind from binding)
      - no_match — no binding fires
    """
    audit: dict = {"rule": "mint_anchor"}
    for fuss_id, binding in _MINT_BOUND_FUSSES.items():
        if binding.get("allowed_entities") and entity_id not in binding["allowed_entities"]:
            continue
        if not _coin_matches_mint_binding(coin, binding):
            continue
        kind_fn = binding.get("kind_by_nominal")
        kind = kind_fn(coin.get("nominal")) if kind_fn else coin.get("kind")
        audit.update({
            "matched_fuss": fuss_id,
            "rationale": binding.get("rationale"),
            "mint": coin.get("mint"),
            "ruler": coin.get("ruler"),
            "year_first": coin.get("year_first"),
            "entity": entity_id,
            "kind_derivation": kind,
        })
        return ("mint_anchor", fuss_id, kind, audit)
    return ("no_match", None, None, audit)


def _classify_via_grevens_fejde_anchor(coin: dict, entity_id: str | None
                                         ) -> tuple[str, str | None, str | None, dict]:
    """Era-anchor rule: Christian III silver/billon coinage 1534-1540
    belongs to `christian_iii_dalerfod` Phase 0 (de-facto-Etablierung).

    Why this routing.
    -----------------
    Per refactor 2026-05-21 (research findings danskmoent.dk c3hede.htm
    continuous catalogue, Wilcke 1950 7-3 p. 242 «die 1537 Karbung
    etabliert das 14½-Lod-Daler-Standard», Reynold Junge mintmaster
    continuity 1534-1540): the formerly-separate
    `christian_iii_grevens_fejde_fod` Fuß was merged INTO
    `christian_iii_dalerfod` as Phase 0 (1534-1540, de-facto-
    Etablierung). The 1537 Joachimsdaler is metrically identical to
    the 1541 Møntordning Daler (14½ Lod, 8/M, 26.494 g fein) — Wilcke
    himself explicitly notes this metric continuity. The 1541
    Møntordning codifies de jure what Junge had already established
    de facto by 1537.

    Function name retained as `_classify_via_grevens_fejde_anchor`
    for historical continuity; the trigger and the kind-derivation
    logic are unchanged — only the routing target changed from
    grevens_fejde_fod to dalerfod (with Phase 0 picked up by the
    build's year-window phase resolver: 1534-1540 → Phase 0,
    1541-1543 → Phase A1, 1544-1555 → Phase A2).

    Returns (signal, fuss_id, kind, audit). Signal is one of:
      - grevens_fejde_anchor — applied (routes to dalerfod Phase 0)
      - no_match — rule does not fire
    """
    audit: dict = {"rule": "grevens_fejde_anchor"}
    year_first = coin.get("year_first")
    if not isinstance(year_first, int) or not (1534 <= year_first <= 1540):
        return ("no_match", None, None, audit)
    if entity_id != "danish_realm":
        return ("no_match", None, None, audit)
    ruler = str(coin.get("ruler") or "")
    if "Christian III" not in ruler:
        return ("no_match", None, None, audit)
    metal = coin.get("metal")
    if metal not in ("silver", "billon"):
        return ("no_match", None, None, audit)
    # Kind derivation: Klippe + sub-Skilling + Hvid = Scheide;
    # Joachimsdaler + 2 Mark + 1 Mark + 8 Skilling = Kurant
    nominal = str(coin.get("nominal") or "").lower()
    if any(tok in nominal for tok in ("joachimstaler", "joachimsdaler",
                                       "1 gulden", "½ gulden", "halv gulden")):
        kind = "kurant"
    elif any(tok in nominal for tok in ("hvid", "penning", "klippe")):
        kind = "scheide"
    elif "skilling" in nominal:
        # 8 Skilling kurant; 1-4 Skilling typically scheide
        # Per Wilcke 7-3 p. 242 the 4 ß variants are debased Scheide
        if nominal.startswith("8 skilling") or nominal.startswith("1 mark") \
           or nominal.startswith("2 mark"):
            kind = "kurant"
        else:
            kind = "scheide"
    else:
        kind = coin.get("kind") or "kurant"
    audit.update({
        "year_first": year_first,
        "entity": entity_id,
        "ruler": ruler,
        "metal": metal,
        "nominal": coin.get("nominal"),
        "kind_derivation": kind,
        "target_fuss_phase": "christian_iii_dalerfod / Phase 0 (de-facto-Etablierung)",
    })
    return ("grevens_fejde_anchor", "christian_iii_dalerfod", kind, audit)


def _classify_via_denomination_anchor(coin: dict, entity_id: str | None
                                        ) -> tuple[str, str | None, str | None, dict]:
    """Denomination-anchor rule: when a coin's nominal text uniquely
    identifies a Müntzfuß within the Danish-Norwegian register, assign
    it directly without delta-math.

    Why an anchor rule is needed.
    -----------------------------
    The §BV cycle added six new Müntzfüße with characteristic
    denominations (Rhinsk Gylden, Rosenobel, Nobel, Ungersk Gylden,
    plus the existing pattern-matchable ones). Several of these
    specimens carry NO fineness in the seed data (Bruun parser doesn't
    extract fineness; Galster pages sometimes only carry brutto) — so
    the fineness/weight-Δ fallback CANNOT classify them, even though
    the denomination alone uniquely determines the Fuß.

    The rule table `_DENOMINATION_ANCHOR_RULES` carries the patterns
    + targeted Fuß + optional year constraint. First-match wins; order
    in the table matters (narrower patterns precede broader ones —
    Rosenobel before Nobel).

    Entity scope:
      * `danish_realm` — all four §BV rules apply
      * `danish_norway` — Norway shares Danish-realm currency for the
        relevant periods (pre-1814 Kalmar-Union era), so the same
        rules apply when the denomination appears there too. Future
        rules with period-specific Norwegian-mint scope would need a
        per-rule entity gate.
      * Other entities — rules currently don't fire (the §BV Fuesse
        are Danish-Norwegian-exclusive); generalise if needed when
        German lands need parallel denomination-anchor rules.

    Returns (signal, fuss_id, kind, audit). Signal is one of:
      - denomination_anchor — applied (returns Fuß + kind from rule)
      - no_match — no denomination rule fires
    """
    audit: dict = {"rule": "denomination_anchor"}
    if entity_id not in {"danish_realm", "danish_norway"}:
        return ("no_match", None, None, audit)
    nominal = str(coin.get("nominal") or "").lower()
    if not nominal:
        return ("no_match", None, None, audit)
    year_first = coin.get("year_first")
    for rule in _DENOMINATION_ANCHOR_RULES:
        if not any(p in nominal for p in rule["patterns"]):
            continue
        # Year constraint check
        year_max = rule.get("year_max")
        if year_max is not None:
            if not isinstance(year_first, int) or year_first > year_max:
                # Pattern matched but year is past the cutoff — fall
                # through to the next rule (or to delta-math).
                continue
        year_min = rule.get("year_min")
        if year_min is not None:
            if not isinstance(year_first, int) or year_first < year_min:
                continue
        audit.update({
            "matched_pattern": next(p for p in rule["patterns"] if p in nominal),
            "rationale": rule["rationale"],
            "nominal": coin.get("nominal"),
            "year_first": year_first,
            "entity": entity_id,
        })
        return ("denomination_anchor", rule["fuss"], rule.get("kind"), audit)
    return ("no_match", None, None, audit)


def _classify_via_kronefod_anchor(coin: dict, entity_id: str | None
                                   ) -> tuple[str, str | None, str | None, dict]:
    """Era-anchor rule: post-1873 Danish-realm / Norwegian-realm coins with
    Krone- or Øre-family denominations belong unambiguously to `kronefod`
    (Skandinaviska Myntunionen, Lov nr. 66 af 23. maj 1873).

    Why an anchor rule is needed here.
    --------------------------------
    The fineness/weight-Δ math fails on the small-Øre tier when:
      * fineness is missing (typical for bronze 5/2/1 Øre — NumisMaster
        rarely tags «Bronze» as fineness)
      * the Δ against the Hauptkurant Soll-fein lands in the «dead zone»
        between full-Kurant (±2%) and large-Scheide (>20%) because the
        Øre tier is *deliberately* under-weight per the Lov nr. 66
        subsidiary-tier schedule (.600 / .400 Ag, then Bronze).
    Year + denomination + entity, however, uniquely determine the fuss:
    post-1873 Danish-realm Krone/Øre denominations are by definition
    `kronefod` until the Goldkonvertibilität end on 2 August 1914 — and
    our project upper bound is 1914 so every Krone/Øre coin in scope
    is `kronefod`.

    Kind derivation:
      * Commemorative / Gedenk Krone → kind=gedenk
      * Øre family (25 / 10 / 5 / 2 / 1 Øre) → kind=scheide
        (per fuesse.yml `kronefod.grundwerte` — these tiers are
        «absichtlich unterwertig» / deliberately under-weight)
      * Krone family (1 / 2 / 5 / 10 / 20 Kroner) → kind=kurant
        (silver 1/2 Krone are full-Kurant companions, gold 5/10/20
        Kroner are Hauptkurant — both circulate as kurant)

    Entity scope:
      * `danish_realm` — DK adopted 1873-05-23
      * `danish_norway` — Norway adopted 1875 via SMU extension
    Not applied to `royal_holstein` / `prussian_schleswig_holstein`:
    Schleswig-Holstein became Prussian 1864/1867 and post-1871 used
    `reichsgoldmuenzfuss` (Goldmark), not the Krone-fod.

    Returns (signal, fuss_id, kind, audit).
    """
    audit: dict = {"rule": "era_kronefod"}
    year_first = coin.get("year_first")
    if not isinstance(year_first, int) or year_first < 1873:
        return ("no_match", None, None, audit)
    if entity_id not in {"danish_realm", "danish_norway"}:
        return ("no_match", None, None, audit)
    nominal = str(coin.get("nominal") or "").lower()
    if not nominal:
        return ("no_match", None, None, audit)
    # Match Krone/Kroner (kurant) — exclude "Rigsdaler"-prefixed legacy
    # nominals («Rigsdaler kurant», «Skilling kurant») which would
    # falsely match on substring «krone». Anchor on the word boundary
    # via direct token check.
    krone_match = (
        ("krone" in nominal or "kroner" in nominal)
        and "rigs" not in nominal
        and "courant" not in nominal
        and "kurant" not in nominal
    )
    # Match Øre family — all spellings used in source data:
    #   «Øre» (Danish canonical capitalised) / «øre» (lowercase variant)
    #   «Öre» (Swedish-influenced spelling occasionally on parsed pages)
    #   bare «Ore» (transliteration in some sources)
    # Case-insensitive: NumisMaster + Numista mix capitalisation, and the
    # uppercase «Ø» (U+00D8) vs lowercase «ø» (U+00F8) are distinct chars
    # that ignored-case correctly folds together.
    ore_match = bool(
        re.search(r"\børe\b|\böre\b|\bore\b",
                  coin.get("nominal") or "",
                  flags=re.IGNORECASE)
    )
    if not (krone_match or ore_match):
        return ("no_match", None, None, audit)
    # Kind derivation
    if "commemorat" in nominal or "gedenk" in nominal:
        kind = "gedenk"
    elif ore_match:
        kind = "scheide"
    else:
        kind = "kurant"
    audit.update({
        "year_first": year_first,
        "entity": entity_id,
        "nominal": coin.get("nominal"),
        "match": "krone" if krone_match else "øre",
    })
    return ("era_kronefod", "kronefod", kind, audit)


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

    # Mint-anchor: Müntzfüße pinned to a specific mint+ruler combination
    # (Flensborg-fod = Flensburg + Christian III). Runs FIRST among the
    # anchor rules because mint-binding is the strongest historical
    # signal — if the coin's mint + ruler match, the Fuß is settled.
    ma_signal, ma_fuss, ma_kind, ma_audit = _classify_via_mint_anchor(
        coin, entity_id)
    if ma_fuss:
        decision["proposed_fuss"] = ma_fuss
        if ma_kind:
            decision["proposed_kind"] = ma_kind
        decision["signal"] = ma_signal
        decision["audit"] = ma_audit
        return decision

    # Era-anchor: Grevens-Fejde 1534-1540 Christian III silver/billon
    # cascade. Runs BEFORE denomination_anchor because denominations
    # (2 Mark, 4 Skilling, Joachimsdaler) overlap with other Fuß
    # families but the year+ruler+entity combination uniquely
    # identifies this period (Wilcke 7-3 p. 242).
    gf_signal, gf_fuss, gf_kind, gf_audit = _classify_via_grevens_fejde_anchor(
        coin, entity_id)
    if gf_fuss:
        decision["proposed_fuss"] = gf_fuss
        if gf_kind:
            decision["proposed_kind"] = gf_kind
        decision["signal"] = gf_signal
        decision["audit"] = gf_audit
        return decision

    # Denomination-anchor: §BV unique-denomination patterns
    # (Rhinsk Gylden, Rosenobel, Nobel, Ungersk Gylden ≤1559).
    # Runs BEFORE delta-math because these denominations uniquely
    # determine the Fuß even when fineness/weight data is missing
    # — and several seed entries (Bruun, partial Galster pages)
    # carry no fineness so delta-math can't classify them.
    dn_signal, dn_fuss, dn_kind, dn_audit = _classify_via_denomination_anchor(
        coin, entity_id)
    if dn_fuss:
        decision["proposed_fuss"] = dn_fuss
        if dn_kind:
            decision["proposed_kind"] = dn_kind
        decision["signal"] = dn_signal
        decision["audit"] = dn_audit
        return decision

    # Era-anchor: post-1873 Danish-realm / Norwegian Krone-Øre → kronefod.
    # Runs BEFORE 18½-Thaler anchor because the year-bounds differ (1873+
    # for Krone-fod, 1813-1873 for 18½-Thaler) and a Krone post-1873 coin
    # would otherwise hit the 18½-Thaler era-anchor on the «skilling» word
    # check if its nominal accidentally carried that token.
    kf_signal, kf_fuss, kf_kind, kf_audit = _classify_via_kronefod_anchor(
        coin, entity_id)
    if kf_fuss:
        decision["proposed_fuss"] = kf_fuss
        if kf_kind:
            decision["proposed_kind"] = kf_kind
        decision["signal"] = kf_signal
        decision["audit"] = kf_audit
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
        # Apply classifications: mutate V2 final entries via SURGICAL
        # line-level edits. We do NOT round-trip the whole YAML
        # through any parser — that re-serialises every long string,
        # reflows multi-line scalars, and produces a multi-thousand-
        # line cosmetic diff that buries the actual fuss/phase/kind
        # mutations in noise.
        #
        # Instead, walk the file line-by-line: find each coin block
        # by its `id: <coin_id>` line (anchor), then back-walk to the
        # block's `- fuss: seed_unsorted` line and the `phase:` /
        # `kind:` lines that follow within the same indentation
        # level. Replace the three values in place. Resulting diff
        # contains exactly the changed lines per coin (typically
        # 3 lines × N coins = ~30 lines for a batch of 10 coins).
        write_count = 0
        for ent, decisions in by_entity.items():
            if not decisions:
                continue
            path = V2_FINAL / f"{ent}.yml"
            applied_ids = {d["coin_id"]: d for d in decisions
                           if d.get("proposed_fuss") and d.get("proposed_phase")}
            if not applied_ids:
                continue
            lines = path.read_text().splitlines(keepends=True)
            # Build coin-block index: for each coin, find the line
            # number of its `id:` line (the anchor — id appears once
            # per coin block, unique value), then back-walk to the
            # nearest `- fuss:` line above (block start).
            id_to_block_start: dict[str, int] = {}
            for i, line in enumerate(lines):
                m = re.match(r"^\s+id:\s+(\S+)\s*$", line)
                if m and m.group(1) in applied_ids:
                    # Back-walk to the `- fuss:` line
                    for j in range(i, -1, -1):
                        if re.match(r"^-\s+fuss:\s+\S", lines[j]):
                            id_to_block_start[m.group(1)] = j
                            break
            mutated = 0
            for cid, d in applied_ids.items():
                if cid not in id_to_block_start:
                    print(f"  [warn] {ent}/{cid}: id-line not found, skipping")
                    continue
                start = id_to_block_start[cid]
                # Forward-walk from the block start; replace the
                # `- fuss:` line + any `  phase:` / `  kind:` lines
                # we encounter before the next block (`- fuss:`).
                end = len(lines)
                for j in range(start + 1, len(lines)):
                    if re.match(r"^-\s+fuss:\s+\S", lines[j]):
                        end = j
                        break
                for j in range(start, end):
                    if j == start:
                        # The `- fuss:` block-start line
                        lines[j] = re.sub(
                            r"(^-\s+fuss:\s+)\S+(\s*$)",
                            rf"\g<1>{d['proposed_fuss']}\g<2>",
                            lines[j],
                        )
                    elif re.match(r"^\s+phase:\s+\S", lines[j]):
                        lines[j] = re.sub(
                            r"(^\s+phase:\s+)\S+(\s*$)",
                            rf"\g<1>{d['proposed_phase']}\g<2>",
                            lines[j],
                        )
                    elif d.get("proposed_kind") and re.match(r"^\s+kind:\s+\S", lines[j]):
                        lines[j] = re.sub(
                            r"(^\s+kind:\s+)\S+(\s*$)",
                            rf"\g<1>{d['proposed_kind']}\g<2>",
                            lines[j],
                        )
                mutated += 1
            if mutated:
                path.write_text("".join(lines))
                print(f"  wrote {ent}: {mutated} coins reclassified")
                write_count += mutated
        print(f"\n✓ Applied {write_count} classifications across {len(by_entity)} entit(y/ies)")
    else:
        print("\n  [dry-run — no files written. Re-run with --apply to commit.]")

    return 0


if __name__ == "__main__":
    sys.exit(main())
