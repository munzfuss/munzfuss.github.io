#!/usr/bin/env python3
"""Categorise every ucoin entry against our Schleswig coin base.

Reads from `scripts/cache/ucoin/_url_index.json` (705 entries built by
the harvest scripts) and `data/locations/schleswig.yml`. Writes a
classification snapshot to `scripts/cache/ucoin/_categorized_strict.json`
that downstream investigation tools can consume.

Categories:
  A_ALREADY                  ← strict match against our base (KM# +
                               denom + year + fineness compatibility,
                               OR direct ucoin tid found in a base coin's
                               sources block)
  B_HOLSTEIN_NEW             ← Holstein-source, KM# not in our base
  C_HOLSTEIN_KM_VARIANT      ← Holstein-source, KM# in our base but no
                               variant matches (different denom/year)
  D_DENMARK_HOLSTEIN_MINT    ← Denmark-source, Numista cache OR our base
                               attests a Holstein mint for that KM#
  E_DENMARK_AMBIGUOUS        ← KM# overlaps our base but denom/year don't
                               match — needs per-coin manual check.
                               Auto-routed entries from the heuristic;
                               manually-reviewed ones get reclassified
                               into H/J/F via MANUAL_OVERRIDES.
  F_OUT_OF_SCOPE             ← Clearly outside Holstein (year range past
                               our 1559–1866 window — Reichsmünzordnung
                               to Prussian annexation — or geographic
                               mismatch with Holstein-mint cities). Also
                               receives data-quality skips (e.g. ucoin
                               entries with bad weight values that we
                               don't want polluting the base).
  H_COPENHAGEN_CONFIRMED     ← User-reviewed Royal Danish Copenhagen
                               issues. Period field on ucoin = «Speciedaler
                               (1582-1624)» or «Rigsdaler (1625-1699)»
                               (i.e. the broader Denmark-realm coinage,
                               NOT a Glückstadt-period sub-page).
                               Manually verified, not from the heuristic.
  J_HOLSTEIN_TO_ADD          ← User-reviewed Holstein-mint candidates
                               ready to add as new coin entries (or as
                               alts to existing entries pending visual
                               verification). Period field on ucoin =
                               «Glückstadt (1617-1773)» or «Holstein-
                               Gottorp-Rendsburg (1716-1720)». An optional
                               `verification_note` flags entries that
                               look like potential duplicates of existing
                               base coins — the user clears these via
                               visual inspection before commit.
  K_WRONG_DATA_IGNORE        ← User-reviewed entries where ucoin's data
                               is demonstrably wrong (e.g. weight off by
                               2× the canonical value, fineness contradicting
                               every published source). Distinct from
                               F_OUT_OF_SCOPE because the coin itself MAY
                               be in scope, but the ucoin record is
                               poisoned — importing it would corrupt the
                               base. Recorded so future re-runs don't
                               re-surface the entry as a candidate.
  X_HANSEATIC_SKIP           ← Lübeck/Hamburg, out of Schleswig scope

Decision precedence (each step short-circuits the rest):
  1. MANUAL_OVERRIDES — user-reviewed entries with an explicit category
  2. Direct ucoin-tid bridge — base coin's sources contain this tid URL
  3. Hanseatic source filter (X_HANSEATIC_SKIP)
  4. Strict KM+denom+year+fineness match (A_ALREADY)
  5. KM-overlap fallback (B/C/D/E/F per source-region heuristics)

Promoted from `scripts/oneoff/` 2026-05-02 because it's idempotent over
the live cache and the MANUAL_OVERRIDES table belongs in version
control (otherwise re-runs from a clean state would silently lose user
review decisions).

Run:  .venv/bin/python scripts/audit_ucoin_categories.py
"""
from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path

import yaml


CACHE_UCOIN = Path("scripts/cache/ucoin")
CACHE_NUMISTA = Path("scripts/cache/numista")
SCHLESWIG = Path("data/locations/schleswig.yml")
OUT_JSON = CACHE_UCOIN / "_categorized_strict.json"

HOLSTEIN_SOURCES = {"country_schleswig_holstein", "period_2939",
                     "period_2995", "q_holstein_extras"}
HANSEATIC_SOURCES = {"country_lubeck", "country_hamburg",
                      "period_1204", "period_1205"}

EASY_HOLSTEIN_MINTS = {"glückstadt", "gluckstadt", "altona", "oldendorf"}
AMBIGUOUS_HOLSTEIN_MINTS = {"schleswig", "tönning", "toenning",
                             "reinfeld", "steinbek", "kiel",
                             "burg auf fehmarn"}
COPENHAGEN_MINTS = {"copenhagen", "kopenhagen", "royal danish mint"}


# --- Denomination matching (copied from linker for consistency) ---------

SAME_TOKEN_GROUPS = [
    {"marck", "mark"},
    {"danske", "dansk"},
    {"lybsk", "lubsk", "lubisch"},
    {"speciedaler", "speciesdaler", "speziesdaler", "thaler", "daler",
     "reichsthaler", "reichs", "species", "spec"},
    {"dukat", "ducat"},
    {"skilling", "schilling", "schillng"},
    {"sosling", "soesling"},
    {"kroner", "krone"},
]


def _normalize(s: str) -> str:
    if not s:
        return ""
    s = s.lower()
    fr = {"½": ".5", "⅓": ".333", "⅔": ".667", "¼": ".25", "¾": ".75",
          "⅙": ".167", "⅛": ".125", "⅕": ".2"}
    for k, v in fr.items():
        s = s.replace(k, v)
    s = s.replace("ø", "o").replace("ß", "ss")
    s = unicodedata.normalize("NFKD", s)
    s = "".join(c for c in s if not unicodedata.combining(c))
    return s


def normalize_denom(s: str) -> set[str]:
    s = _normalize(s)
    tokens = re.split(r"[\s/\-]+", s)
    drop = {"the", "and", "von", "de", "der", "die", "das"}
    return {t for t in tokens if t and t not in drop}


def all_quantities(s: str) -> list[float]:
    s = _normalize(s).strip()
    if s.startswith("."):
        s = "0" + s
    out: list[float] = []
    for m in re.finditer(r"(\d+(?:\.\d+)?)(?:\s*/\s*(\d+(?:\.\d+)?))?", s):
        n = float(m.group(1))
        if m.group(2):
            d = float(m.group(2))
            if d > 0:
                n = n / d
        out.append(n)
    return out


def leading_qty(s: str) -> float | None:
    qs = all_quantities(s)
    return qs[0] if qs else None


def tokens_share_meaning(a: set[str], b: set[str]) -> bool:
    def meaningful(s: set[str]) -> set[str]:
        return {t for t in s if not re.fullmatch(r"\d+([-/]\d+)?", t)}
    ma, mb = meaningful(a), meaningful(b)
    if not ma or not mb:
        return bool(a & b)
    if ma & mb:
        return True
    for g in SAME_TOKEN_GROUPS:
        if (ma & g) and (mb & g):
            return True
    return False


def denom_compatible(our_nominal: str, ucoin_denom: str) -> bool:
    if not our_nominal or not ucoin_denom:
        return False
    a = normalize_denom(our_nominal)
    b = normalize_denom(ucoin_denom)
    if not tokens_share_meaning(a, b):
        return False
    qb = leading_qty(ucoin_denom)
    qs = all_quantities(our_nominal)
    if qb is not None and qs:
        if not any(abs(qb - q) <= 0.005 for q in qs):
            return False
    return True


def parse_ucoin_year(yr: str) -> tuple[int, int] | None:
    if not yr:
        return None
    m = re.match(r"(\d{4})(?:[–\-](\d{4}))?", str(yr))
    if not m:
        return None
    yf = int(m.group(1))
    yl = int(m.group(2)) if m.group(2) else yf
    return yf, yl


def years_overlap(our_yf: int, our_yl: int, ucoin_year: str) -> bool:
    uy = parse_ucoin_year(ucoin_year)
    if not uy or not our_yf:
        return False
    yf, yl = uy
    yl_ours = our_yl or our_yf
    return not (yl < our_yf or yf > yl_ours)


def fineness_compatible(our_f, uc_f) -> bool:
    # Accept both scalar (legacy) and list-form (post-source-attribution
    # refactor) representations of `fineness`. List form: take primary
    # (first entry) for the comparison.
    if isinstance(our_f, list) and our_f:
        first = our_f[0]
        our_f = first.get("value") if isinstance(first, dict) else first
    if not our_f or not uc_f or our_f <= 0:
        return True  # missing data → don't reject on this alone
    rel = abs(our_f - uc_f) / our_f
    return rel <= 0.40


# --- Loading helpers -----------------------------------------------------

def get_kms_from_coin(c) -> set[str]:
    cat = c.get("catalog", {}) or {}
    km = cat.get("km", "")
    others = cat.get("others", []) or []
    kms: set[str] = set()
    for k_str in [km] + [str(o) for o in others if "KM" in str(o)]:
        for p in re.split(r"[,;/]", str(k_str)):
            p = p.strip().replace("KM#", "").replace("KM", "").strip()
            if p:
                kms.add(p)
    parents = {k.split(".")[0] for k in kms if "." in k}
    return kms | parents


def get_ucoin_km(uc_entry: dict) -> str | None:
    """Pull the catalog reference from a ucoin entry, but ONLY return it
    when it's a real Krause-Mishler (KM#) number. ucoin's TSV column is
    overloaded — many entries carry «UC# 100» which is *ucoin's own*
    catalog code, not Krause-Mishler. Treating «UC#» as KM was the bug
    that made km-162-1850 (real KM# 162) surface as a phantom
    «B_HOLSTEIN_NEW» candidate just because «UC# 100» didn't match
    anything. Return None for any non-KM prefix so downstream matching
    falls back to denomination + year + weight only."""
    raw = (uc_entry.get("km") or "").strip()
    if not raw:
        return None
    # Anything starting with «UC» (ucoin internal), «N#» (Numista internal),
    # or other non-KM prefixes → not a KM number.
    if re.match(r"^(UC|N|UCOIN)\b", raw, re.IGNORECASE):
        return None
    return raw


def load_numista_mints():
    out: dict[str, list[str]] = {}
    for f in sorted(CACHE_NUMISTA.glob("*.json")):
        if "_issues" in f.name:
            continue
        try:
            with open(f) as fp:
                d = json.load(fp)
        except Exception:
            continue
        refs = d.get("references") or []
        kms = [r.get("number") for r in refs if r.get("catalogue", {}).get("code") == "KM"]
        mints = [m.get("name", "") for m in (d.get("mints") or [])]
        for km in kms:
            if km:
                out.setdefault(km, []).extend(mints)
    return out


def is_copenhagen_only(mint_names: list[str]) -> bool:
    if not mint_names:
        return False
    txt = " ".join(mint_names).lower()
    has_cph = any(m in txt for m in COPENHAGEN_MINTS)
    has_holstein = (any(m in txt for m in EASY_HOLSTEIN_MINTS) or
                    any(m in txt for m in AMBIGUOUS_HOLSTEIN_MINTS))
    return has_cph and not has_holstein


def has_holstein_mint(mint_names: list[str]) -> bool:
    if not mint_names:
        return False
    txt = " ".join(mint_names).lower()
    return (any(m in txt for m in EASY_HOLSTEIN_MINTS) or
            any(m in txt for m in AMBIGUOUS_HOLSTEIN_MINTS))


def base_coin_mint_holstein(base_candidates: list[dict]) -> bool | None:
    """Look at our own base entries with this KM# — if any has a Holstein
    mint, return True (this KM# is known to us as Holstein-relevant).
    Returns None if no info."""
    if not base_candidates:
        return None
    for c in base_candidates:
        m = (c.get("mint") or "").lower()
        if any(h in m for h in EASY_HOLSTEIN_MINTS):
            return True
        if any(h in m for h in AMBIGUOUS_HOLSTEIN_MINTS):
            return True
    return False


# --- Main ----------------------------------------------------------------

def main():
    with open(CACHE_UCOIN / "_url_index.json") as fp:
        ucoin = json.load(fp)
    with open(SCHLESWIG) as fp:
        doc = yaml.safe_load(fp)

    base_by_km: dict[str, list[dict]] = {}
    # Reverse lookup tid → coin for entries already present in our base
    # via their `sources[].url` block. Lets the categorizer recognise
    # ucoin entries we've manually folded in even when there's no KM#
    # bridging them (e.g. ucoin-only candidates added under km-x*** ids
    # with the ucoin tid as the only catalog reference).
    base_by_ucoin_tid: dict[str, dict] = {}
    for c in doc.get("coins", []):
        for km in get_kms_from_coin(c):
            base_by_km.setdefault(km, []).append(c)
            if "." in km:
                base_by_km.setdefault(km.split(".")[0], []).append(c)
        for s in (c.get("sources") or []):
            url = s.get("url") or ""
            m = re.search(r"[?&]tid=(\d+)", url)
            if m:
                base_by_ucoin_tid.setdefault(m.group(1), c)

    numista_mints = load_numista_mints()

    results: dict[str, list[dict]] = {
        "A_ALREADY": [],
        "B_HOLSTEIN_NEW": [],
        "C_HOLSTEIN_KM_VARIANT": [],
        "D_DENMARK_HOLSTEIN_MINT": [],
        "E_DENMARK_AMBIGUOUS": [],
        "F_OUT_OF_SCOPE": [],
        "H_COPENHAGEN_CONFIRMED": [],
        "J_HOLSTEIN_TO_ADD": [],
        "K_WRONG_DATA_IGNORE": [],
        "X_HANSEATIC_SKIP": [],
    }

    # Manual overrides — entries reviewed by the user where the heuristic
    # categorisation is wrong. Each entry includes the rationale so future
    # re-runs preserve the decision and the audit trail.
    #
    # 2026-05-03 revision: after fetching ucoin Period field for all 22
    # auto-categorised E entries, the picture changed substantially —
    # ucoin's Period IS the most reliable mint indicator. Entries with
    # Period «Glückstadt (1617-1773)» or «Holstein-Gottorp-Rendsburg
    # (1716-1720)» are HOLSTEIN-MINT candidates worth adding; entries
    # with Period «Speciedaler (1582-1624)» or «Rigsdaler (1625-1699)»
    # are Royal Danish Copenhagen out-of-scope.
    #
    # Routing:
    #   - 12 Royal Danish Copenhagen → H_COPENHAGEN_CONFIRMED
    #   - 7 confirmed Holstein candidates → J_HOLSTEIN_TO_ADD
    #   - 2 ambiguous (possible duplicate of existing) → J with verification flag
    #   - 1 unreliable data → F_OUT_OF_SCOPE with reason
    MANUAL_OVERRIDES = {
        # ----- Group A: Glückstadt-mint per ucoin (Period «Glückstadt 1617-1773») -----
        # All 6 added to schleswig.yml (2026-05-03) — auto-routed to A_ALREADY
        # via the direct ucoin-tid bridge in the new coin entries' sources.
        "163582": ("A_ALREADY",              "Added as km-x004-chr-v-1694 (1 Sk Danske, fills gap in 1693-1697 series; KM-DK# 81 Royal Danish cross-ref)"),
        "163585": ("A_ALREADY",              "Folded into existing km-358-h123-chr-v-1681 (KM-DK# 71 cross-ref); user verified same coin as Hede 123 under Royal Danish register"),
        "163588": ("A_ALREADY",              "Added as km-x005-chr-iv-1620 (2 Sk Lybsk Glückstadt, earliest documented Christian IV Glückstadt Sk-Lybsk; KM-DK# 8)"),
        "163638": ("A_ALREADY",              "Added as km-x007-chr-iv-1620 (4 Sk Lybsk Glückstadt, sibling to km-x005; KM-DK# 9)"),
        "163670": ("A_ALREADY",              "Added as km-72-chr-v-1682 — separate Krause type from km-70.1 (1682-only, .979, Hede 117); km-70-1 simultaneously cleaned to be only Coin B"),
        "163671": ("K_WRONG_DATA_IGNORE",    "ucoin '1 krone' 3g .917 — same coin as our km-40-2 Guldkrone (5.996g .917) per Numista N#306974 but with corrupted ucoin weight (3g = exactly half of correct value); data unreliable, do not import"),
        # ----- Group D-MED-WD-PRE1617 (14 weight-divergent pre-1617 — Glückstadt impossible): -----
        "163398": ("H_COPENHAGEN_CONFIRMED", "Christian IV 1 Gulden 1591-1593 UC# 12 silver .972 — pre-1617 → Copenhagen"),
        "173642": ("H_COPENHAGEN_CONFIRMED", "Christian IV 1 Speciedaler 1596 UC# 13 silver .937 — pre-1617 → Copenhagen"),
        "163068": ("H_COPENHAGEN_CONFIRMED", "Christian IV 1 Speciedaler 1597 UC# 8 silver .937 — pre-1617 → Copenhagen"),
        "162972": ("H_COPENHAGEN_CONFIRMED", "Christian IV 1 Penning 1602 KM# 5 copper — pre-1617 → Copenhagen"),
        "162975": ("H_COPENHAGEN_CONFIRMED", "Christian IV 1 Penning 1602 KM# 6 copper (sub-variant) — pre-1617 → Copenhagen"),
        "162978": ("H_COPENHAGEN_CONFIRMED", "Christian IV 1 Hvid 1602 KM# 9 billon .1 — pre-1617 → Copenhagen"),
        "163043": ("H_COPENHAGEN_CONFIRMED", "Christian IV 1 Mark 1602-1604 KM# 12 silver .593 — pre-1617 → Copenhagen"),
        "163008": ("H_COPENHAGEN_CONFIRMED", "Christian IV 2 Skilling 1603-1613 KM# 16.1 silver .298 — pre-1617 → Copenhagen"),
        "163077": ("H_COPENHAGEN_CONFIRMED", "Christian IV 10 Ducat 1604 UC# 11 GOLD .979 — pre-1617 → Copenhagen"),
        "162991": ("H_COPENHAGEN_CONFIRMED", "Christian IV 1 Søsling 1607 KM# 40 silver .125 — pre-1617 → Copenhagen"),
        "162992": ("H_COPENHAGEN_CONFIRMED", "Christian IV 1 Søsling 1611 KM# 47 silver .125 — pre-1617 → Copenhagen"),
        "162986": ("H_COPENHAGEN_CONFIRMED", "Christian IV 1 Hvid 1613-1614 KM# 54 billon .1 — pre-1617 → Copenhagen"),
        "163017": ("H_COPENHAGEN_CONFIRMED", "Christian IV 4 Skilling 1616-1619 KM# 55.1 silver .437 — majority pre-1617 → Copenhagen"),
        "163019": ("H_COPENHAGEN_CONFIRMED", "Christian IV 4 Skilling 1616-1619 KM# 55.2 silver .437 (sub-variant) — majority pre-1617 → Copenhagen"),
        # ----- Group D-MED-WD-POST1617 (9 added as NEW Holstein candidates): -----
        "162985": ("A_ALREADY",              "Added as km-x028-chr-iv-1618 (1 Hvid 1618 billon .1, KM-DK# 63)"),
        "163005": ("A_ALREADY",              "Added as km-x029-chr-iv-1619 (2 Skilling 1619-1621 silver .86, KM-DK# 69)"),
        "163035": ("A_ALREADY",              "Added as km-x030-chr-iv-1619 (8 Skilling 1619 silver .86, KM-DK# 71)"),
        "163040": ("A_ALREADY",              "Added as km-x031-chr-iv-1618-eighth (⅛ Krone 1618 silver .86, KM-DK# 56; new fraction 1/8 added to kronemont_chr_iv)"),
        "170135": ("A_ALREADY",              "Added as km-x032-chr-iv-1646-half-spec (½ Speciedaler 1646 silver .88, KM-DK# 135)"),
        "97094":  ("A_ALREADY",              "Added as km-x033-chr-iv-1644-sixteen (16 Skilling 1644-1646 silver .593 Hebræermünt-era, KM-DK# 136)"),
        "97361":  ("A_ALREADY",              "Added as km-x034-fr-iii-1655 (Frederik III 1 Speciedaler 1655-1656 silver .875, KM-DK# 204)"),
        "97374":  ("A_ALREADY",              "Added as km-x035-chr-iv-1647 (Christian IV 2 Speciedaler 1647 silver .888, KM-DK# 146)"),
        "97404":  ("A_ALREADY",              "Added as km-x036-chr-iv-1637 (Christian IV 1 Dukat 1637 GOLD .98, gap-filler in our Christian IV ducat series, KM-DK# 124)"),
        # ----- Group D-MED-WITH-BASE (6 reviewed 2026-05-03 — base-overlap candidates): -----
        "163009": ("A_ALREADY",              "Added as km-x024-chr-iv-1618 (Christian IV 2 Skilling 1618 .298 — user verified visually different from km-5 Sonderburg)"),
        "163023": ("A_ALREADY",              "Folded into existing km-70-chr-iv-1619 as alt — user verified visually identical (same KM# 70 Royal Danish); ucoin diverges in fineness (.437 vs Numista .859), recorded as alt with note"),
        "163047": ("A_ALREADY",              "Added as km-x025-chr-iv-1612 (Christian IV 1 Mark 1612-1618 .593 — kept separate from km-A4 per user instruction; very similar parameters but ucoin has no image to confirm identity)"),
        "163065": ("H_COPENHAGEN_CONFIRMED", "Christian IV 1 Speciedaler 1590 UC# 6 .937 29.23g — user verified visually different from km-278276 Schauenburg; pre-1617 strict rule routes to Copenhagen"),
        "163411": ("A_ALREADY",              "Added as km-x026-chr-iv-1611 (Christian IV 1 Rosenoble 1611-1629 GOLD .833 — separate trade-gold standard, distinct from silver km-A4 per metal filter)"),
        "96430":  ("A_ALREADY",              "Added as km-x027-fr-iii-1651 (Frederik III 1 Søsling 1651 COPPER — distinct from silver km-93 per metal filter)"),
        # ----- Group D-MED-1617+ (8 reviewed 2026-05-03 — added as new Holstein-mint candidates): -----
        "163036": ("A_ALREADY",              "Added as km-x016-chr-iv-1622 (Christian IV 6 Skilling 1622, fineness inferred from .888 standard)"),
        "163037": ("A_ALREADY",              "Added as km-x017-chr-iv-1622 (Christian IV 12 Skilling 1622-1623 .888)"),
        "163038": ("A_ALREADY",              "Added as km-x018-chr-iv-1624 (Christian IV 12 Skilling 1624-1625 .860, post-Kipper reduction)"),
        "97085":  ("A_ALREADY",              "Added as km-x019-chr-iv-1627 (Christian IV 6 Skilling 1627-1629 .781, KM-DK# 109)"),
        "97086":  ("A_ALREADY",              "Added as km-x020-chr-iv-1628 (Christian IV 6 Skilling 1628-1629 .781, KM-DK# 110, sub-variant of km-x019)"),
        "97375":  ("A_ALREADY",              "Added as km-x021-fr-iii-1649 (Frederik III 2 Speciedaler 1649-1650 .888, early-reign issue)"),
        "97324":  ("A_ALREADY",              "Added as km-x022-fr-iii-1651 (Frederik III 2 Kroner 1651 .860 — Pumphosekrone predecessor; filed under kronemont_fine fuss)"),
        "97396":  ("A_ALREADY",              "Added as km-x023-fr-iii-1652 (Frederik III ½ Dukat 1652 GOLD .980, sister to km-x015 1/16 Dukat 1648)"),
        # ----- Group D-MED-PRE-1617: 10 pre-1617 entries, definitively Copenhagen -----
        # (Glückstadt mint was founded in 1617 — anything before that year cannot
        #  be Glückstadt-mint regardless of which Period ucoin files them under)
        "162984": ("H_COPENHAGEN_CONFIRMED", "Frederik II 1 Hvid 1582-1583, billon — pre-Glückstadt → Copenhagen"),
        "163001": ("H_COPENHAGEN_CONFIRMED", "Frederik II 1 Skilling 1582-1583 .187 — pre-Glückstadt → Copenhagen"),
        "163011": ("H_COPENHAGEN_CONFIRMED", "Frederik II 2 Skilling 1582-1585 .312 — pre-Glückstadt → Copenhagen"),
        "163030": ("H_COPENHAGEN_CONFIRMED", "Frederik II 8 Skilling 1582-1585 .610 — pre-Glückstadt → Copenhagen"),
        "163075": ("H_COPENHAGEN_CONFIRMED", "Christian IV 10 Ducat 1588 GOLD (accession piece, UC# 10) — pre-Glückstadt → Copenhagen"),
        "163012": ("H_COPENHAGEN_CONFIRMED", "Christian IV 2 Skilling 1594-1596 .312 — pre-Glückstadt → Copenhagen"),
        "163067": ("H_COPENHAGEN_CONFIRMED", "Christian IV 4 Mark 1596 .937 (high-fineness rarity) — pre-Glückstadt → Copenhagen"),
        "163071": ("H_COPENHAGEN_CONFIRMED", "Christian IV 2 Speciedaler 1597-1600 .888 — pre-Glückstadt → Copenhagen"),
        "163409": ("H_COPENHAGEN_CONFIRMED", "Christian IV 4 Daler 1604 GOLD .833 — pre-Glückstadt → Copenhagen"),
        "163074": ("H_COPENHAGEN_CONFIRMED", "Christian IV 2 Speciedaler 1607 .888 — pre-Glückstadt → Copenhagen"),
        # ----- Group D-HIGH (4 reviewed 2026-05-03 from D_DENMARK_HOLSTEIN_MINT pre-screen): -----
        "97365":  ("A_ALREADY",              "Added as km-x013-fr-iii-1664 (Frederik III Glückstadt 1 Speciedaler 1664-only at .875 — separate type from km-51 1664-1666 .888 per user verification of fineness mismatch)"),
        "99114":  ("A_ALREADY",              "Added as km-x014-chr-iv-1624 (Christian IV Glückstadt 2 Speciedaler 1624-1634 at .875 — visually distinct from km-16 1623 per user verification)"),
        "97236":  ("A_ALREADY",              "Folded into existing km-x001-fr-iii-1659 as third ucoin source URL (KM-DK# 194 cross-ref); user verified visually identical with year-only differences"),
        "97384":  ("A_ALREADY",              "Added as km-x015-chr-iv-1648 (Christian IV 1/16 Dukat 1648 GOLD — different metal from km-93 silver, user-confirmed separate coin; mint Glückstadt-vs-Copenhagen unverified)"),
        # ----- Group B: Holstein-Gottorp-Rendsburg (Period «Holstein-Gottorp-Rendsburg 1716-1720») -----
        # All 4 added to schleswig.yml as Frederik IV interim issues during the
        # Danish occupation of Gottorp lands (1713-1721).
        "169251": ("A_ALREADY",              "Added as km-x008-fr-iv-1719 (1 Sk Rendsburg-Gottorp interim; KM-DK# 5)"),
        "169252": ("A_ALREADY",              "Added as km-x010-fr-iv-1716 (12 Sk Rendsburg-Gottorp interim; KM-DK# 6)"),
        "169253": ("A_ALREADY",              "Added as km-x011-fr-iv-1719-half (½ Dukat Rendsburg-Gottorp interim; KM-DK# 7)"),
        "169254": ("A_ALREADY",              "Added as km-x012-fr-iv-1718 (1 Dukat Rendsburg-Gottorp interim; KM-DK# 8)"),
        # ----- Group C: Royal Danish Copenhagen (Period «Speciedaler 1582-1624» / «Rigsdaler 1625-1699») -----
        "101246": ("H_COPENHAGEN_CONFIRMED", "Christian IV 2 Dukat 1644-1648 (KM# 140); Hebræermønt-style legend «IUDEX IUSTUS יהוה» but Period=Rigsdaler ≠ Glückstadt → Copenhagen mint"),
        "162976": ("H_COPENHAGEN_CONFIRMED", "Christian IV 2 Penning 1602 copper (KM# 7); Period «Speciedaler 1582-1624» = Copenhagen"),
        "162977": ("H_COPENHAGEN_CONFIRMED", "Christian IV 1 Hvid 1602 billon (KM# 8); Copenhagen"),
        "163042": ("H_COPENHAGEN_CONFIRMED", "Christian IV 24 Skilling 1624 (KM# 93); Copenhagen"),
        "163045": ("H_COPENHAGEN_CONFIRMED", "Christian IV 1 Mark 1606-1607 (KM# 33); Copenhagen"),
        "163070": ("H_COPENHAGEN_CONFIRMED", "Christian IV 1 Speciedaler 1608-1621 (KM# 44); Copenhagen"),
        "96444":  ("H_COPENHAGEN_CONFIRMED", "Christian IV 1 Skilling 1629 (KM# 113.1); Copenhagen"),
        "96445":  ("H_COPENHAGEN_CONFIRMED", "Christian IV 1 Skilling 1629 (KM# 113.2); Copenhagen sub-variant"),
        "96446":  ("H_COPENHAGEN_CONFIRMED", "Christian IV 1 Skilling 1644-1648 (KM# 131); Copenhagen"),
        "96458":  ("H_COPENHAGEN_CONFIRMED", "Christian IV 2 Skilling 1630-1632 (KM# 120); Copenhagen"),
        "96461":  ("H_COPENHAGEN_CONFIRMED", "Frederick III 2 Skilling 1648-1651 (KM# 158); Copenhagen"),
        "99093":  ("H_COPENHAGEN_CONFIRMED", "Frederick III 2 Mark 1658-1661 (KM# 218); Copenhagen"),
    }

    for tid, e in ucoin.items():
        # Manual override takes precedence over heuristic logic.
        if tid in MANUAL_OVERRIDES:
            cat_name, reason = MANUAL_OVERRIDES[tid]
            results[cat_name].append({
                "tid": tid, "km": (e.get("km") or "").strip(),
                "denom": e.get("denom"), "year": e.get("year"),
                "fineness": e.get("fineness"), "weight_g": e.get("weight_g"),
                "url": e.get("url"), "source": e.get("source", ""),
                "manual_override_reason": reason,
            })
            continue
        # Direct tid bridge: if a base coin's sources include this exact
        # ucoin URL, it's already incorporated — no need to run the
        # heuristic match logic.
        direct_match = base_by_ucoin_tid.get(tid)
        if direct_match is not None:
            results["A_ALREADY"].append({
                "tid": tid, "km": (e.get("km") or "").strip(),
                "denom": e.get("denom"), "year": e.get("year"),
                "fineness": e.get("fineness"), "weight_g": e.get("weight_g"),
                "url": e.get("url"), "source": e.get("source", ""),
                "matched_ids": [direct_match["id"]],
                "match_method": "ucoin_tid_in_sources",
            })
            continue

        # Detect whether the catalog reference is a real Krause-Mishler
        # number or one of ucoin's internal codes (UC#, H#, etc.). The
        # legacy line stripped «UC# » as if it were «KM# », which made
        # entries like «UC# 100» hijack KM# 100 lookups in our base —
        # producing phantom B_HOLSTEIN_NEW entries for coins we already
        # carry under their real KM# (e.g. km-162-1850 surfaced as
        # «new» because nothing in our base matches «UC# 100»).
        raw_km_field = (e.get("km") or "").strip()
        is_real_km = bool(raw_km_field) and not re.match(
            r"^(UC|N|H|UCOIN)#?\s", raw_km_field, re.IGNORECASE
        )
        km_raw = (raw_km_field
                  .replace("KM# ", "").replace("KM#", "")
                  .replace("UC# ", "").replace("UC#", "")
                  .replace("H# ", "").strip()) if is_real_km else ""
        source = e.get("source", "")

        if source in HANSEATIC_SOURCES:
            results["X_HANSEATIC_SKIP"].append({"tid": tid, **e})
            continue

        # Strict A_ALREADY check — only keyed on KM# when we actually have one.
        candidates: list = []
        if is_real_km and km_raw:
            candidates = list(base_by_km.get(km_raw, []))
            if "." in km_raw:
                candidates += base_by_km.get(km_raw.split(".")[0], [])
        else:
            # No usable KM#: fall back to denom + year matching across
            # the entire base (cheaper than indexing — base is small).
            for kms_key, group in base_by_km.items():
                for c in group:
                    if c not in candidates:
                        candidates.append(c)
        # dedup by id
        seen, dedup = set(), []
        for c in candidates:
            if c["id"] in seen: continue
            seen.add(c["id"])
            dedup.append(c)
        candidates = dedup

        match_ids = []
        for c in candidates:
            yf = c.get("year_first") or 0
            yl = c.get("year_last") or yf
            if (years_overlap(yf, yl, e.get("year") or "")
                    and denom_compatible(c.get("nominal", ""), e.get("denom", ""))
                    and fineness_compatible(c.get("fineness"), e.get("fineness"))):
                match_ids.append(c["id"])

        record = {"tid": tid, "km": km_raw, "denom": e.get("denom"),
                  "year": e.get("year"), "fineness": e.get("fineness"),
                  "weight_g": e.get("weight_g"), "url": e.get("url"),
                  "source": source}

        if match_ids:
            record["matched_ids"] = match_ids
            results["A_ALREADY"].append(record)
            continue

        # Not matched. Holstein-source?
        if source in HOLSTEIN_SOURCES:
            if candidates:
                # KM# exists in base but no variant matches → KM_VARIANT
                record["base_km_present_ids"] = [c["id"] for c in candidates]
                results["C_HOLSTEIN_KM_VARIANT"].append(record)
            else:
                results["B_HOLSTEIN_NEW"].append(record)
            continue

        # Denmark-source. Use Numista cache + base-coin mint hints.
        n_mints = (numista_mints.get(km_raw, [])
                   or numista_mints.get(km_raw.split(".")[0], []))
        record["numista_mints"] = sorted(set(n_mints)) if n_mints else []
        base_holstein = base_coin_mint_holstein(candidates)

        # Heuristic priority:
        if has_holstein_mint(n_mints) or base_holstein is True:
            record["why"] = "numista_or_base_attests_holstein_mint"
            results["D_DENMARK_HOLSTEIN_MINT"].append(record)
        elif is_copenhagen_only(n_mints):
            record["why"] = "numista_says_copenhagen_only"
            results["F_OUT_OF_SCOPE"].append(record)
        elif candidates:
            # KM# in our base but mint info missing — needs check
            record["why"] = "km_in_base_but_no_variant_match_no_mint_info"
            record["base_km_present_ids"] = [c["id"] for c in candidates]
            results["E_DENMARK_AMBIGUOUS"].append(record)
        else:
            # No KM# overlap, Denmark source, no Holstein mint info → likely Copenhagen
            record["why"] = "no_km_overlap_denmark_source"
            results["F_OUT_OF_SCOPE"].append(record)

    # --- Report -----------------------------------------------------------

    print(f"=== STRICT CATEGORIZATION ({len(ucoin)} ucoin entries) ===\n")
    for cat in ["A_ALREADY", "B_HOLSTEIN_NEW", "C_HOLSTEIN_KM_VARIANT",
                "D_DENMARK_HOLSTEIN_MINT", "E_DENMARK_AMBIGUOUS",
                "F_OUT_OF_SCOPE", "H_COPENHAGEN_CONFIRMED",
                "J_HOLSTEIN_TO_ADD", "K_WRONG_DATA_IGNORE",
                "X_HANSEATIC_SKIP"]:
        rs = results[cat]
        print(f"  {cat:30s}  {len(rs):4d}")

    # Diff against the v1 linker outcome
    print()
    n_a_strict = len(results["A_ALREADY"])
    print(f"v1 linker actually attached to: 124 coins (~33% wrong)")
    print(f"v2 linker (strict):              89 coins")
    print(f"v3 strict-categorize A_ALREADY:  {n_a_strict} ucoin entries")

    # Save
    with open(OUT_JSON, "w") as fp:
        json.dump(results, fp, indent=2, ensure_ascii=False)
    print(f"\nWrote {OUT_JSON}")


if __name__ == "__main__":
    main()
