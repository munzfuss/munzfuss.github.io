"""Reclassify Denmark seed entries — assign each coin currently sitting
under ``fuss: seed_unsorted`` to its real Müntzfuß + phase based on
metal, nominal, year, and (when available) the parsed Hede
``marken_fin_udbragt_til`` value.

Processes both seed sources in place:

  * ``data/seed/hede/denmark.yml``     — Hede-derived entries (phase=hede)
  * ``data/locations/denmark.yml``     — ucoin bulk block (phase=A)

For each coin, the classifier walks a list of deterministic rules
ordered from most-specific to most-general. The first matching rule
sets ``fuss`` and ``phase``; coins that no rule matches keep
``fuss: seed_unsorted`` with the original phase.

Rules anchor to documented signals:

  * **Hede MFU** is the strongest signal — the «Marken fin udbragt til
    X (unit)» line on a danskmoent.dk page IS the period Müntzfuß
    statement. Mapped directly to our Fuß catalogue.
  * **Nominal-token + year window** is the secondary signal — used for
    coins without MFU (ucoin seeds, gold coins where Hede states the
    standard via «<denom>fod» rather than MFU).
  * **Fineness range** is a tertiary disambiguator for ambiguous
    nominals (e.g. Skilling can be Scheide of multiple parent Fusses).

Anything that doesn't match a rule stays in seed_unsorted (the catch-
all bucket) and is reported under «unclassified» at the end.

The script does NOT flip ``*_verified`` flags. Verification stays
``false`` post-classification because the Fuß-bucket placement is
inferred from the source's published numbers — not a per-coin sanity
check against fineness × weight × specimen variance. That second
step is the «promotion» work covered in
``data/seed/hede/README.md``.

Run:
    python scripts/maintenance/classify_dk_seeds.py [--dry-run]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from ruamel.yaml import YAML

PROJECT = Path(__file__).resolve().parents[2]
LOC_FILE = PROJECT / "data" / "locations" / "denmark.yml"
SEED_FILE = PROJECT / "data" / "seed" / "hede" / "denmark.yml"
HEDE_CACHE = PROJECT / "scripts" / "cache" / "hede"


# ---------------------------------------------------------------------------
# MFU lookup table — populated lazily from the parsed Hede cache
# ---------------------------------------------------------------------------

_MFU_CACHE: dict[str, tuple[float, str]] | None = None


def _mfu_lookup() -> dict[str, tuple[float, str]]:
    """Composite Hede key («c5h120», «f3h62ab») → (value, unit) from
    the parsed cache. Cached after first call."""
    global _MFU_CACHE
    if _MFU_CACHE is not None:
        return _MFU_CACHE
    out: dict[str, tuple[float, str]] = {}
    for p in sorted(HEDE_CACHE.glob("*.json")):
        if p.name.startswith("_"):
            continue
        d = json.loads(p.read_text(encoding="utf-8"))
        vol = d.get("ruler_volume") or ""
        specs = d.get("specs") or {}
        if "default" in specs:
            mfu = specs["default"].get("marken_fin_udbragt_til")
            if mfu and vol:
                # Use page's primary hede number (from filename)
                bm = re.match(r"^[cf]\d+h(.+)$", d["id"])
                if bm:
                    out[f"{vol}{bm.group(1).lower()}"] = (mfu["value"], mfu["unit"])
        elif "by_hede" in specs:
            for sub, spec in specs["by_hede"].items():
                mfu = spec.get("marken_fin_udbragt_til")
                if mfu and vol:
                    out[f"{vol}{sub.lower()}"] = (mfu["value"], mfu["unit"])
    _MFU_CACHE = out
    return out


def _get_mfu(coin: dict) -> tuple[float, str] | None:
    cat = coin.get("catalog") or {}
    vol = cat.get("hede_volume")
    hede = cat.get("hede")
    if not vol or not hede:
        return None
    key = f"{vol}{str(hede).lower()}"
    mfu = _mfu_lookup().get(key)
    if mfu is None:
        return None
    v, unit = mfu
    # Drop implausible parser artefacts (year-prefixed sub-values that
    # leaked through; real MFU values are 8.5 ≤ x ≤ 50).
    if v < 7.0 or v > 60.0:
        return None
    return v, unit


# ---------------------------------------------------------------------------
# Classification rules
# ---------------------------------------------------------------------------

def _nominal_has(coin: dict, *tokens: str) -> bool:
    n = (coin.get("nominal") or "").lower()
    return any(t.lower() in n for t in tokens)


def _phase_by_year(year: int, fuss_phases: list[tuple[int, int, str]]) -> str | None:
    """Pick the phase whose [year_from, year_to] envelopes the year.
    Falls back to nearest-by-year if the year overshoots."""
    for yf, yt, pid in fuss_phases:
        if yf <= year <= yt:
            return pid
    # Slight overshoots — phase boundaries usually leak ±1
    for yf, yt, pid in fuss_phases:
        if yf - 1 <= year <= yt + 1:
            return pid
    return None


# Phase year-ranges per fuss, mirroring data/locations/denmark.yml.
# Update here when adding/changing phases in denmark.yml.
PHASES: dict[str, list[tuple[int, int, str]]] = {
    "reichsdukatenfuss":  [(1546, 1588, "pre-A"), (1591, 1726, "A"),
                           (1726, 1771, "B"), (1771, 1813, "C"),
                           (1813, 1871, "D")],
    "courantdukatenfuss": [(1714, 1796, "A")],
    "pistolenfuss":       [(1771, 1870, "A")],
    "9_thaler":           [(1566, 1625, "A"), (1648, 1683, "B")],
    "9_25_thaler":        [(1622, 1726, "A"), (1726, 1788, "B"),
                           (1788, 1813, "C"), (1813, 1854, "D")],
    "kronemont_chr_iv":   [(1618, 1624, "A"), (1651, 1652, "B"),
                           (1665, 1675, "C")],
    "kronemont":          [(1644, 1669, "A"), (1670, 1699, "B")],
    "kronemont_fine":     [(1693, 1771, "A")],
    "guldkrone":          [(1618, 1628, "pre-A"), (1657, 1666, "A"),
                           (1668, 1668, "B")],
    "11_333_thaler":      [(1726, 1813, "A")],
    "18_5_thaler":        [(1813, 1875, "A")],
    "30_thaler":          [(1873, 1947, "A")],
    "reichsgoldmuenzfuss":[(1873, 1914, "A")],
    "kronefod":           [(1873, 1914, "A")],
}


def _classify_silver_by_mfu(mfu: tuple[float, str], year: int) -> tuple[str, str | None] | None:
    """Use the Hede `marken_fin_udbragt_til` value + unit to pick a
    silver Müntzfuß. Returns (fuss_id, phase_id) or None."""
    v, unit = mfu
    u = unit.lower()
    # Speciedaler-denominated standards: 9 / 9.071 / 9.143 / 9.25 / 9.288…
    if "speciedaler" in u:
        if 8.9 <= v <= 9.15:
            return ("9_thaler", _phase_by_year(year, PHASES["9_thaler"]))
        if 9.16 <= v <= 9.35:
            # 9.288 = 9¼; 9.143 = atypical Christian IV reformpost-1622
            return ("9_25_thaler", _phase_by_year(year, PHASES["9_25_thaler"]))
        if 9.35 < v <= 9.6:
            # Atypical Speciedaler standards (Tranquebar Piaster etc.)
            return None
    # Rigsdaler / RD-denominated — covers 11⅓ Helstaten Courant
    if u in {"rigsdaler", "rd"} or "rigsdaler" in u:
        if 11.0 <= v <= 11.5:
            ph = _phase_by_year(year, PHASES["11_333_thaler"])
            if ph:
                return ("11_333_thaler", ph)
            # Coins minted before 1726 with MFU 11.333 are early
            # Helstaten-Courant prototypes — leave for explicit review.
            return None
    # Rigsbankdaler — 18½-Fuß
    if "rigsbank" in u:
        if 18.0 <= v <= 19.0:
            return ("18_5_thaler", _phase_by_year(year, PHASES["18_5_thaler"]))
    # Daler-denominated kronemont family — covers Christian V Krone
    # («10,4 daler / rd») AND Christian IV Krone («10,6–10,95 daler»).
    if u in {"daler", "dlr", "rd"}:
        if 10.35 <= v <= 10.45:
            return ("kronemont", _phase_by_year(year, PHASES["kronemont"]))
        # Christian IV Krone era: ≈ 10.6 – 10.95 daler (1618-1645)
        if 10.5 <= v <= 11.0 and 1618 <= year <= 1675:
            return ("kronemont_chr_iv", _phase_by_year(year, PHASES["kronemont_chr_iv"]))
    return None


def _classify_gold(coin: dict) -> tuple[str, str | None] | None:
    """Gold standards keyed off nominal + year — Hede's MFU line is
    rarely populated for gold pages, so we rely on the denomination
    name plus regnal year window."""
    year = coin["year_first"]
    nom_l = (coin.get("nominal") or "").lower()
    # Post-1873 Krone-fod gold (10/20 Kroner)
    if "krone" in nom_l and year >= 1873 and year <= 1914:
        return ("kronefod", "A")
    # Christian IV Esrum + Frederik III Guldkrone (1618-1670) — must
    # match BEFORE the generic «Guldkrone» check. Frederik II's «1
    # Guldkrone» 1563-1564 is NOT a Krone-fod piece (3.3 g @ .934,
    # closer to Goldgulden / Reichsdukat-pattern); those route to
    # reichsdukatenfuss/pre-A via the catch-all gold rule further down.
    if "guldkrone" in nom_l or (("krone" in nom_l or "guldcrone" in nom_l)
                                  and 1618 <= year <= 1670):
        if 1618 <= year <= 1670:
            ph = _phase_by_year(year, PHASES["guldkrone"])
            if ph:
                return ("guldkrone", ph)
    # Pistole / Friedrich d'or / Christiansdor — pistolenfuss
    if any(t in nom_l for t in ("pistole", "d'or", "frederiksdor",
                                 "frederik d", "christiansdor", "christian d",
                                 "friederich d", "frederich d'")):
        return ("pistolenfuss", "A")
    # Kurantdukat / Speciedukat — courantdukatenfuss
    if "kurantdukat" in nom_l or "speciedukat" in nom_l:
        return ("courantdukatenfuss", "A")
    # Plain Dukat / Ducat / Gylden / Gulden — Reichsdukatenfuss default.
    # «Ungersk Gylden» (Hungarian-pattern ducat) and «Rhinsk Gylden» both
    # fit Reichsdukatenfuss (same 67-Dukaten standard, .986 fineness).
    # «Portugaløser» (10-Dukat presentation piece, Hede's «Portuguese-
    # pattern» gold), «Rosenobel» (English rose-noble pattern struck
    # in Danish gold), «Guldmønt» (Hede's bare «gold coin» label when
    # the type predates a settled denomination) — all gold pieces
    # at Reichsdukat-family fineness.
    # Final catch-all for Renaissance gold tokens. «guldkrone» is
    # included here as a fall-through — Frederik II's 1563-1564
    # «Guldkrone» (3.34 g, .934) is a Goldgulden-pattern piece that
    # mathematically fits Reichsdukatenfuß-family rather than the
    # later Krone-fod tariff coin (the Guldkrone earlier-block has
    # already caught the 1618-1670 cases that DO belong to the
    # Krone-fod fuss).
    if any(t in nom_l for t in ("dukat", "ducat", "gylden", "gulden",
                                  "portugaløser", "portugaloser",
                                  "rosenobel", "guldmønt", "guldmoent",
                                  "guldkrone", "guldcrone")):
        ph = _phase_by_year(year, PHASES["reichsdukatenfuss"])
        if ph:
            return ("reichsdukatenfuss", ph)
        return None
    return None


def _classify_silver_by_year_and_nominal(coin: dict) -> tuple[str, str | None] | None:
    """Fallback for silver coins without a usable MFU value — assign
    by nominal + year window. Lower confidence than MFU-based path."""
    year = coin["year_first"]
    nom_l = (coin.get("nominal") or "").lower()
    # Christian IV silver Krone (Corona Danica family) — three discrete
    # mint windows: 1618-1624 (A), 1651-1652 (B), 1665-1675 (C).
    if "krone" in nom_l and any(yf <= year <= yt
                                  for yf, yt, _ in PHASES["kronemont_chr_iv"]):
        return ("kronemont_chr_iv", _phase_by_year(year, PHASES["kronemont_chr_iv"]))
    # Speciedaler — 9-Fuß pre-1622, 9¼-Fuß after
    if "speciedaler" in nom_l:
        if year < 1622:
            return ("9_thaler", "A")
        if year < 1854:
            return ("9_25_thaler", _phase_by_year(year, PHASES["9_25_thaler"]))
    # Krone / 2 Krone / 2 Mark / 4 Mark — Christian V kronemont (1670-1699)
    if any(t in nom_l for t in ("krone", "mark")) and 1670 <= year <= 1699:
        return ("kronemont", "B")
    # Krone / Mark — kronemont_fine (1693-1771, Frederik IV → Christian VI)
    if any(t in nom_l for t in ("krone", "mark")) and 1693 <= year <= 1771:
        return ("kronemont_fine", "A")
    # Frederik III silver Krone / Mark 1644-1669 → kronemont/A
    if any(t in nom_l for t in ("krone", "mark")) and 1644 <= year <= 1669:
        return ("kronemont", "A")
    # Silver Mark / 2 Mark / 4 Mark — pre-Krone era (Christian IV /
    # Frederik II) → 9_thaler/A. Pre-Reichsmünzordnung issues
    # (year < 1566) are outside Denmark page scope; the seed builder
    # filters them at ingest, so no routing rule is needed here.
    if "mark" in nom_l and 1566 <= year <= 1625:
        return ("9_thaler", "A")
    # Christian IV silver Mark 1622-1670 (Kipper-era debasement
    # «Hebræermønt» 1644-1646 at .593 fineness, etc.) — bucket into
    # 9_25_thaler/A.
    if "mark" in nom_l and 1622 <= year <= 1670:
        return ("9_25_thaler", "A")
    # «12 Mark» 1747-1763 (Frederik V) — 12 Mark Danske ≡ 1 Reichsdaler
    # Specie, 9¼-Fuß. Caught by `mark` token + year ≥ 1726.
    if "mark" in nom_l and 1726 <= year <= 1813:
        return ("9_25_thaler", _phase_by_year(year, PHASES["9_25_thaler"]))
    # Tranquebar / Asian-trade Piaster — silver Speciedaler-class
    # trade dollar. Routes by year to nearest Specie standard.
    if "piaster" in nom_l or "piastre" in nom_l:
        if 1622 <= year < 1726:
            return ("9_25_thaler", "A")
        if 1726 <= year <= 1813:
            return ("9_25_thaler", _phase_by_year(year, PHASES["9_25_thaler"]))
    # Silver Daler multi-units (3/4/6/8 Daler) under Christian IV —
    # 9-Fuß Speciedaler multiples (10 Daler Sterndaler etc.).
    if "daler" in nom_l and 1566 <= year <= 1625:
        return ("9_thaler", "A")
    if "daler" in nom_l and 1622 <= year <= 1670:
        return ("9_25_thaler", "A")
    # Rigsdaler Courant 1726-1813 — 11⅓-Fuß («Rixdaler» is older spelling).
    # Pre-1726 Rixdaler (Frederik IV 1700-1725) is Speciedaler-tier
    # (9¼-Fuß), so route those to 9_25_thaler/A.
    if any(t in nom_l for t in ("rigsdaler", "rixdaler", "skilling courant")):
        if 1726 <= year <= 1813:
            return ("11_333_thaler", "A")
        if 1622 <= year < 1726:
            return ("9_25_thaler", "A")
    # Rigsbankdaler / Rigsbankskilling 1813-1874 — 18½-Fuß. Includes
    # late «1 Rigsdaler» (1854) and «2 Rigsdaler» (1864) under the
    # post-1854 Rigsmønt rebranding (same standard, new accounting).
    if any(t in nom_l for t in ("rigsbank", "rigsdaler", "rixdaler")) \
            and 1813 <= year <= 1874:
        return ("18_5_thaler", "A")
    # Post-1873 Scandinavian Krone-Mønt silver / billon / copper
    # auxiliary issue (1/2 Kroner Kurant + 10/25 øre Scheide + 1/2/5
    # øre bronze). The gold 10/20 Kroner are caught by the dedicated
    # gold rule in `_classify_gold` and routed to `kronefod`; the
    # silver / billon / copper auxiliaries land in `kronefod_silver`
    # under the same Mønlov 1873 framework.
    if 1873 <= year <= 1914 and any(t in nom_l for t in (
            "øre", "ore", "öre", "krone")):
        return ("kronefod", "A")
    return None


def _classify_scheidemuenze(coin: dict) -> tuple[str, str | None] | None:
    """Scheidemünze (small change — Skilling / Hvid / Søsling /
    Penning) bind to the parent kurant Müntzfuß active in their year
    of mintage. Returns (parent_fuss, phase) — kind=scheide gets set
    by the caller separately."""
    year = coin["year_first"]
    nom_l = (coin.get("nominal") or "").lower()
    scheide_token = any(t in nom_l for t in (
        "skilling", "hvid", "søsling", "soesling", "penning",
        "rigsbankskilling", "denning", "sechsling", "dreiling",
    ))
    if not scheide_token:
        return None
    # 18½-Fuß era — Rigsbankskilling 1813-1874
    if "rigsbankskilling" in nom_l and year >= 1813:
        return ("18_5_thaler", "A")
    # By year window of the parent Kurant standard (phases per
    # data/locations/denmark.yml). Skilling/Hvid/Søsling/Penning
    # circulate as Scheide-tier sub-units of whichever silver Kurant
    # holds period dominance:
    #   1566-1625  Reichsmünz Speciedaler                 9_thaler/A
    #   1625-1726  Speciedaler (9¼-Fuß; parallel Krone)   9_25_thaler/A
    #   1726-1813  Helstaten Courant (Forordning 1726)    11_333_thaler/A
    #   1813-1874  Rigsbankdaler (Statsbankerot reform)   18_5_thaler/A
    #   1874-1914  Krone-fod (Mønlov 1873)                kronefod/A
    # Pre-1566 issues fall outside Denmark page scope and are
    # filtered at seed ingest, not here.
    if 1566 <= year < 1622:
        return ("9_thaler", "A")
    if 1622 <= year < 1726:
        return ("9_25_thaler", "A")
    if 1726 <= year < 1813:
        return ("11_333_thaler", "A")
    if 1813 <= year < 1874:
        return ("18_5_thaler", "A")
    if 1874 <= year <= 1914:
        return ("kronefod", "A")
    return None


def classify(coin: dict) -> tuple[str | None, str | None, str]:
    """Return (fuss_id, phase_id, reason). When fuss_id is None the
    coin stays in seed_unsorted."""
    metal = coin.get("metal")
    year = coin.get("year_first")
    if not year or year < 1500:
        return None, None, "no year / pre-1500"

    # 1. Gold path (nominal + year — Hede rarely publishes gold MFU)
    if metal == "gold":
        result = _classify_gold(coin)
        if result and result[1]:
            return result[0], result[1], "gold-by-nominal+year"

    # 2. Silver / billon / unspecified path. Many ucoin entries lack a
    #    `metal` field — we fall through to the nominal-based rules
    #    instead of requiring metal=silver|billon.
    if metal in ("silver", "billon") or metal is None:
        # 2a. MFU-driven (highest confidence)
        mfu = _get_mfu(coin)
        if mfu:
            r = _classify_silver_by_mfu(mfu, year)
            if r and r[1]:
                return r[0], r[1], f"silver-MFU={mfu[0]:.3f} {mfu[1]}"
        # 2b. Scheidemünze fallback (Skilling/Hvid family)
        r = _classify_scheidemuenze(coin)
        if r and r[1]:
            return r[0], r[1], "scheide-by-year"
        # 2c. Silver kurant by nominal + year
        r = _classify_silver_by_year_and_nominal(coin)
        if r and r[1]:
            return r[0], r[1], "silver-by-nominal+year"

    return None, None, "no rule matched"


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------

def _make_yaml() -> YAML:
    y = YAML()
    y.preserve_quotes = True
    y.width = 4096
    y.indent(mapping=2, sequence=4, offset=2)
    return y


def _is_seed_entry(coin: dict) -> bool:
    return coin.get("fuss") == "seed_unsorted"


def _apply(file_path: Path, dry_run: bool, label: str) -> tuple[int, int, dict]:
    y = _make_yaml()
    with file_path.open() as f:
        doc = y.load(f)
    coins = doc.get("coins") or []
    classified = 0
    unchanged = 0
    by_target: dict[tuple[str, str | None], int] = {}
    leftover_reasons: dict[str, int] = {}
    for coin in coins:
        if not _is_seed_entry(coin):
            unchanged += 1
            continue
        fuss, phase, reason = classify(coin)
        if fuss and phase:
            coin["fuss"] = fuss
            coin["phase"] = phase
            # Update kind for Scheidemünze when a small-change nominal lands
            # on a parent Kurant fuss.
            nom_l = (coin.get("nominal") or "").lower()
            if any(t in nom_l for t in ("skilling", "hvid", "søsling",
                                          "penning", "rigsbankskilling")):
                if coin.get("kind") not in ("scheide", "tarif"):
                    coin["kind"] = "scheide"
            classified += 1
            by_target[(fuss, phase)] = by_target.get((fuss, phase), 0) + 1
        else:
            leftover_reasons[reason] = leftover_reasons.get(reason, 0) + 1
    if not dry_run:
        with file_path.open("w") as f:
            y.dump(doc, f)
    print(f"\n=== {label} ({file_path.relative_to(PROJECT)}) ===")
    print(f"  total coins:      {len(coins)}")
    print(f"  not seed entries: {unchanged}")
    print(f"  classified:       {classified}")
    print(f"  left in seed:     {len(coins) - unchanged - classified}")
    print(f"  by target fuss/phase:")
    for (fuss, phase), n in sorted(by_target.items(), key=lambda kv: -kv[1]):
        print(f"    {n:4d}  {fuss}/{phase}")
    if leftover_reasons:
        print(f"  leftover reasons:")
        for r, n in sorted(leftover_reasons.items(), key=lambda kv: -kv[1]):
            print(f"    {n:4d}  {r}")
    return classified, len(coins) - unchanged - classified, by_target


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true",
                    help="Report what would change without writing files")
    args = ap.parse_args()

    total_classified = 0
    total_left = 0
    for path, label in ((SEED_FILE, "Hede seed"), (LOC_FILE, "denmark.yml")):
        c, l, _ = _apply(path, args.dry_run, label)
        total_classified += c
        total_left += l
    print()
    print(f"TOTAL classified: {total_classified}")
    print(f"TOTAL left in seed_unsorted: {total_left}")
    if args.dry_run:
        print("(dry-run — no files written)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
