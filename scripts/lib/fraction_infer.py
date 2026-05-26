"""Infer ``coin.fraction`` from ``coin.nominal`` + ``coin.fuss``.

Background — why this exists
============================

The build pipeline computes Soll-Feingewicht + Δ from
``fuss.fractions[coin.fraction]``. When ``fraction`` is missing on a
coin that already has fuss + phase + weight + fineness, the «Soll»
and «Δ» columns render blank even though everything needed is on the
entry. The user pointed this out 2026-05-27: «ці дані мають
прораховуватись як тільки коін отримує своє місце в стопі».

Source of truth — RULES
=======================

Per-fuss tables mapping a denom-head token (lowercase, stripped of
suffixes) to either a fixed fraction string or a count→fraction
callable. Rules were lifted from `data/locations/denmark.yml`
hand-curated entries (extracted originally for the V1 Hede/ucoin seed
backfill, see `scripts/maintenance/infer_dk_seed_fractions.py`); this
module is the single source of truth — `infer_dk_seed_fractions.py`
now re-exports from here.

Extension policy
================

Add a new fuss → list-of-rules entry whenever a new Müntzfuß lands in
`data/shared/fuesse.yml::fractions`. Each rule is ``(token, fn)``
where ``token`` is matched against the denom head (lowercase, before
parens/commas, suffix-stripped) and ``fn(count) → fraction_str``
returns the fraction. The returned string must exist as a key in
that fuss's ``fractions`` block in fuesse.yml — `infer_fraction()`
double-checks this before emitting.

Idempotency
===========

`infer_fraction()` returns ``None`` when no rule matches or the
candidate isn't a defined fuss fraction. Callers should skip the
entry rather than guess. Conservative-by-construction: it's safer to
leave Soll blank than to emit a wrong target.
"""
from __future__ import annotations

import re
from pathlib import Path


def _identity(n: int) -> str:
    return str(n)


def _fixed(frac: str):
    def _f(n: int) -> str:
        return frac
    return _f


RULES: dict[str, list[tuple[str, callable]]] = {
    # ------- 9¼-Thaler-Fuß (Speciedaler-base, post-1622) -------
    "9_25_thaler": [
        ("speciedaler", _identity),
        ("specie", _identity),                  # «Specie Daler» two-word form
        ("kronerigsdaler", _fixed("1")),
        ("piaster", _fixed("1")),
        ("krone", _identity),
        ("kroner", _identity),
        ("rigsdaler", _identity),
        ("rixdaler", _identity),
        ("mark", lambda n: {1: "1/3", 2: "2/3", 4: "1", 6: "1",
                              8: "2", 12: "3", 16: "4"}.get(n, None)),
        ("marck", lambda n: {1: "1/3", 2: "2/3", 4: "1", 6: "1",
                               8: "2", 12: "3", 16: "4"}.get(n, None)),
        ("skilling", lambda n: {1: "1/96", 2: "1/48", 4: "1/24",
                                  6: "1/16", 8: "1/12", 12: "1/8",
                                  16: "1/6", 24: "1/4", 32: "1/3"}.get(n, None)),
        ("hvid", _fixed("1/192")),
        ("søsling", _fixed("1/96")),
        ("soesling", _fixed("1/96")),
        ("penning", _fixed("1/192")),
    ],
    # ------- 9-Thaler-Fuß (early Speciedaler, 1566-1625) -------
    "9_thaler": [
        ("speciedaler", _identity),
        ("specie", _identity),
        ("mark", lambda n: {1: "1/3", 4: "1", 6: "1",
                              8: "2", 12: "3"}.get(n, None)),
        ("marck", lambda n: {1: "1/3", 4: "1", 6: "1",
                               8: "2", 12: "3"}.get(n, None)),
        ("skilling", lambda n: {1: "1/96", 2: "1/48", 4: "1/24",
                                  8: "1/12"}.get(n, None)),
        ("hvid", _fixed("1/192")),
        ("søsling", _fixed("1/96")),
        ("penning", _fixed("1/192")),
        ("daler", _identity),
    ],
    # ------- 11⅓-Thaler-Fuß (Helstaten Courant, 1726-1813) -------
    "11_333_thaler": [
        ("rigsdaler", _identity),
        ("rixdaler", _identity),
        ("krone", _identity),
        ("kroner", _identity),
        ("speciedaler", _identity),
        ("specie", _identity),
        ("skilling", lambda n: {1: "1/96", 2: "1/48", 4: "1/24",
                                  8: "1/12", 12: "1/8", 24: "1/4",
                                  32: "1/3"}.get(n, None)),
        ("sechsling", lambda n: {2: "1/48"}.get(n, None)),  # 2 Sechsling = 4 Skilling
        ("søsling", _fixed("1/96")),
        ("hvid", _fixed("1/192")),
        ("penning", _fixed("1/192")),
    ],
    # ------- 18½-Thaler-Fuß (Rigsbankdaler, 1813-1874) -------
    "18_5_thaler": [
        ("rigsbankdaler", _identity),
        ("rigsdaler", _identity),
        ("krone", _identity),
        ("kroner", _identity),
        ("rigsbankskilling", lambda n: {1: "1/96", 2: "1/96",
                                          3: "1/24", 4: "1/24",
                                          6: "1/12", 12: "1/12",
                                          16: "1/6", 32: "1/3"}.get(n, None)),
        ("skilling", lambda n: {1: "1/96", 2: "1/96", 3: "1/24",
                                  4: "1/24", 6: "1/12", 8: "1/12",
                                  12: "1/12", 16: "1/6",
                                  32: "1/3"}.get(n, None)),
        ("schilling", lambda n: {1: "1/96", 2: "1/96", 4: "1/24",
                                   6: "1/12", 8: "1/12",
                                   12: "1/12", 16: "1/6",
                                   32: "1/3"}.get(n, None)),
        ("øre", lambda n: {10: "1/192"}.get(n, None)),  # 1854-74 Rigsmønt øre
    ],
    # ------- 10½-Krone-Fuß (Christian V Krone + Frederik III) -------
    # No «Ducat» rule here intentionally: gold Ducats under kronemont
    # are out-of-standard (typically Vægterdukat reichsdukatenfuss
    # mis-classified). Curator must decide per case.
    "kronemont": [
        ("krone", _identity),
        ("kroner", _identity),
        ("mark", lambda n: {1: "1/4", 2: "1/2", 4: "1", 6: "1"}.get(n, None)),
        ("marck", lambda n: {1: "1/4", 2: "1/2", 4: "1", 6: "1"}.get(n, None)),
    ],
    # ------- Christian IV Krone / Corona Danica -------
    "kronemont_chr_iv": [
        ("krone", _identity),
        ("kroneskilling", lambda n: {1: "1/96", 2: "1/48",
                                       4: "1/24", 8: "1/12"}.get(n, None)),
        ("skilling", lambda n: {1: "1/96", 2: "1/48",
                                  4: "1/24", 8: "1/12",
                                  12: "1/8"}.get(n, None)),
    ],
    # ------- 13⅓-Krone-Fuß (Specieskrone, 1693-1771) -------
    "kronemont_fine": [
        ("krone", _identity),
        ("kroner", _identity),
        ("mark", lambda n: {1: "1/4", 2: "1/2", 4: "1"}.get(n, None)),
        ("marck", lambda n: {1: "1/4", 2: "1/2", 4: "1"}.get(n, None)),
    ],
    # ------- 8-Daler-Fuß (Joachimsdaler / Daler-base, pre-1566 → 1620s) -------
    # fractions: 1, 1/3, 1/6, 1/12, 1/48.
    # 1 Daler / Joachimsdaler / Taler = "1"
    # 2 Mark = "1/3" ; 1 Mark = "1/6" ; 4 Skilling = "1/12" ; 1 Skilling = "1/48"
    "8_daler_fod": [
        ("joachimsdaler", _identity),
        ("joachimstaler", _identity),
        ("daler", _identity),
        ("taler", _identity),
        ("thaler", _identity),
        ("mark", lambda n: {1: "1/6", 2: "1/3"}.get(n, None)),
        ("marck", lambda n: {1: "1/6", 2: "1/3"}.get(n, None)),
        ("skilling", lambda n: {1: "1/48", 4: "1/12"}.get(n, None)),
    ],
    # ------- 8-Daler-Lybsk-Fuß (Lübeck Banco / Sølvgylden-base) -------
    # fractions: 1, 1/2, 1/24, 1/48, 1/384.
    # 1 Sølvgylden = "1" ; ½ Sølvgylden = "1/2"
    # 1 Rhinsk Gylden ≈ Sølvgylden (note: post-1490 Rhinsk Gylden silver-based)
    # 1 Søsling Lybsk = "1/48" (28 Sösl. Lübsch = 1 Mark Lübsch ≈ … verify)
    # Sub-units conservatively mapped; ambiguous tokens skipped.
    "8_daler_lybsk_fod": [
        ("sølvgylden", _identity),
        ("solvgylden", _identity),
        ("rhinsk", _identity),                  # «N Rhinsk Gylden» → N
        ("gylden", _identity),                  # bare «Gylden» under this fuss
        ("søsling", lambda n: {1: "1/48"}.get(n, None)),
        ("soesling", lambda n: {1: "1/48"}.get(n, None)),
    ],
    # ------- 8.5-Gylden-Fuß (Schauenburg) -------
    # fractions: 1, 1/2, 1/4, 1/32, 1/96
    "8_5_gylden_fod": [
        ("sølvgylden", _identity),
        ("solvgylden", _identity),
        ("gylden", _identity),
    ],
    # ------- F2-Guldkrone-Fuß (Frederik II Guldkrone, gold) -------
    "f2_guldkrone_fod": [
        ("guldkrone", _identity),
        ("guldcrone", _identity),
        ("krone", _identity),
    ],
    # ------- Rosenobel-Fuß (gold) -------
    "rosenobel_fod": [
        ("rosenobel", _identity),
        ("nobel", _identity),
        ("noble", _identity),
    ],
    # ------- Nobel-Fuß (gold, English-style) -------
    "nobel_fod": [
        ("nobel", _identity),
        ("noble", _identity),
    ],
    # ------- Reichsdukatenfuß (gold, .986) -------
    "reichsdukatenfuss": [
        ("ducat", _identity),
        ("dukat", _identity),
        ("ducats", _identity),
        ("portugaloser", lambda n: str(n * 10) if n else "10"),
        ("portugaløser", lambda n: str(n * 10) if n else "10"),
        ("rosenobel", _fixed("5/2")),
        ("gylden", _identity),
        ("gulden", _identity),
        ("goldgulden", _identity),
        ("guldmønt", _identity),
        ("ungersk", _identity),                 # «Ungersk Gylden» — head token «ungersk», treat as 1 Ducat
    ],
    # ------- Pistolenfuß (gold, .906) -------
    "pistolenfuss": [
        ("pistole", _identity),
        ("d'or", _identity),
        ("d’or", _identity),                    # curly apostrophe variant
        ("frederik", _identity),
        ("christian", _identity),
        ("christians", _identity),              # «Christians D'or»
        ("frederiksdor", _identity),
        ("christiansdor", _identity),
    ],
    # ------- Courantdukatenfuß (gold, .875) -------
    # fractions: 1, 1/2, 2.
    "courantdukatenfuss": [
        ("kurantdukat", _identity),
        ("kurant", _identity),
        ("courantdukat", _identity),
        ("courant", _identity),
        ("speciedukat", _identity),
        ("ducat", _identity),
        ("dukat", _identity),
        ("mark", lambda n: {12: "1"}.get(n, None)),  # 12 Mark Courant = 1 Courantdukat
        ("marck", lambda n: {12: "1"}.get(n, None)),
    ],
    # ------- Guldkrone (gold, .917) -------
    "guldkrone": [
        ("guldkrone", _identity),
        ("guldcrone", _identity),
        ("mark", lambda n: {18: "1"}.get(n, None)),  # 18 Mark = 1 Guldkrone
        ("marck", lambda n: {18: "1"}.get(n, None)),
    ],
    # ------- Reichsgoldmünzfuß (German 1871, gold) -------
    "reichsgoldmuenzfuss": [
        ("krone", _identity),
        ("kroner", _identity),
        ("mark", _identity),
    ],
    # ------- Krone-fod (Skandinavisk Møntunion, 1873-1914) -------
    "kronefod": [
        ("krone", _identity),
        ("kroner", _identity),
        ("øre", lambda n: {1: "1/100", 2: "1/50", 5: "1/20",
                              10: "1/10", 25: "1/4", 50: "1/2"}.get(n, None)),
        ("ore", lambda n: {1: "1/100", 2: "1/50", 5: "1/20",
                              10: "1/10", 25: "1/4", 50: "1/2"}.get(n, None)),
        ("öre", lambda n: {1: "1/100", 2: "1/50", 5: "1/20",
                              10: "1/10", 25: "1/4", 50: "1/2"}.get(n, None)),
    ],
}


_NOMINAL_RE = re.compile(
    r"^\s*"
    r"(?P<frac_num>1/\d+|\d+/\d+|⅛|¼|⅓|½|⅔|¾|⅙|⅚|⅕|⅖|⅗|⅘|⅐|⅑|⅒)?\s*"
    r"(?P<count>\d+(?:[,\.]\d+)?)?\s*"
    r"(?P<rest>.+?)\s*$",
)

_FRACTION_UNICODE = {
    "½": "1/2", "¼": "1/4", "¾": "3/4",
    "⅓": "1/3", "⅔": "2/3", "⅛": "1/8",
    "⅙": "1/6", "⅚": "5/6",
    "⅕": "1/5", "⅖": "2/5", "⅗": "3/5", "⅘": "4/5",
    "⅐": "1/7", "⅑": "1/9", "⅒": "1/10",
}


def _parse_nominal_head(nom: str) -> tuple[str | None, int | None, str]:
    """Return (leading_fraction_string, count_int, rest_token).

    Examples:
      «1 Speciedaler»                 → (None, 1, "Speciedaler")
      «½ Speciedaler»                 → ("1/2", None, "Speciedaler")
      «1/4 Krone»                     → ("1/4", None, "Krone")
      «10 Kroner»                     → (None, 10, "Kroner")
      «16 Rigsbankskilling»           → (None, 16, "Rigsbankskilling")
    """
    m = _NOMINAL_RE.match(nom)
    if not m:
        return None, None, nom.strip()
    frac = m.group("frac_num")
    if frac and frac in _FRACTION_UNICODE:
        frac = _FRACTION_UNICODE[frac]
    cnt = m.group("count")
    cnt_int = int(cnt) if cnt and cnt.isdigit() else None
    rest = (m.group("rest") or "").strip()
    return frac, cnt_int, rest


def _denom_head_token(rest: str) -> str:
    """Strip suffixes («Danske», «Klippe», «(Krone)», «Rigsbanktegn»,
    «Lybsk» etc.) and return the leading lowercase denom token."""
    rest = re.split(r"[,\(]", rest, maxsplit=1)[0].strip()
    parts = rest.split()
    if not parts:
        return ""
    head = parts[0].lower().strip(".:,;")
    return head


def load_fuss_fractions(fuesse_path: str | Path | None = None) -> dict[str, set]:
    """Load the `{fuss_id → set(fraction_keys)}` table from fuesse.yml.

    `fuesse_path` defaults to <project>/data/shared/fuesse.yml. The
    set-of-keys form is what `infer_fraction()` checks against to
    avoid emitting a fraction the fuss doesn't actually define.
    """
    import yaml as _yaml
    if fuesse_path is None:
        # Walk up from this file to find data/shared/fuesse.yml.
        here = Path(__file__).resolve()
        for parent in here.parents:
            candidate = parent / "data" / "shared" / "fuesse.yml"
            if candidate.exists():
                fuesse_path = candidate
                break
    if fuesse_path is None:
        raise FileNotFoundError("Could not locate data/shared/fuesse.yml")
    with Path(fuesse_path).open() as f:
        raw = _yaml.safe_load(f)
    return {
        fid: set((d.get("fractions") or {}).keys())
        for fid, d in raw.items()
    }


def _fraction_str_to_pair(s: str) -> tuple[int, int] | None:
    """Parse «1/2», «3/2», «1» → (num, denom). Returns None if unparseable."""
    s = s.strip()
    if "/" in s:
        a, _, b = s.partition("/")
        if a.isdigit() and b.isdigit() and int(b) != 0:
            return int(a), int(b)
        return None
    if s.isdigit():
        return int(s), 1
    return None


def _format_fraction(num: int, denom: int) -> str:
    """Reduce + format «num/denom» → canonical fraction string. (2,4) → «1/2», (4,1) → «4»."""
    from math import gcd
    if denom == 0:
        return ""
    g = gcd(num, denom)
    num //= g
    denom //= g
    if denom == 1:
        return str(num)
    return f"{num}/{denom}"


def infer_fraction(coin: dict,
                   fuss_fractions: dict[str, set] | None = None) -> str | None:
    """Return the inferred ``fraction`` string for this coin, or None.

    Returns None when:
    - coin has no fuss set or fuss=='seed_unsorted'
    - the coin's fuss has no RULES entry
    - the nominal can't be parsed
    - the candidate isn't a defined fraction in fuss.fractions

    `fuss_fractions` is the result of `load_fuss_fractions()`; passed
    as a parameter so callers can cache it across many invocations.
    Loads lazily if omitted.

    Sub-unit + leading-fraction handling
    ====================================

    «½ Speciedaler» under 9_25_thaler → fraction "1/2" (head is base unit
    whose count-1 maps to fraction "1"; leading_frac IS the fraction).

    «½ Skilling» under 9_25_thaler → fraction "1/192" (head is sub-unit;
    1 Skilling = 1/96; ½ × 1/96 = 1/192). Computed by multiplying the
    leading fraction by the sub-unit's count=1 fraction. If the result
    isn't a defined `fuss.fractions` key, returns None rather than risk
    a wrong Soll.
    """
    fuss = coin.get("fuss")
    if not fuss or fuss == "seed_unsorted":
        return None
    rules = RULES.get(fuss)
    if not rules:
        return None
    if fuss_fractions is None:
        fuss_fractions = load_fuss_fractions()
    nom = coin.get("nominal") or ""
    leading_frac, count, rest = _parse_nominal_head(nom)
    head = _denom_head_token(rest)
    if not head:
        return None

    available = fuss_fractions.get(fuss, set())

    # Path 1 — leading unicode/text fraction («½ Speciedaler», «½ Skilling»).
    # Sub-unit-aware: only emit leading_frac as the FINAL fraction when
    # head IS a base unit (token's fn(1) == "1"); for sub-units multiply
    # leading_frac × sub-unit fraction.
    if leading_frac:
        head_matched = False
        for token, fn in rules:
            if not head.startswith(token):
                continue
            head_matched = True
            sub_unit_fraction = fn(1)
            if sub_unit_fraction is None:
                # fn(1) returned None — the rule doesn't have a «1 X»
                # mapping. Skip (curator decides).
                return None
            if sub_unit_fraction == "1":
                # Head IS the base unit → leading_frac IS the fraction.
                if leading_frac in available:
                    return leading_frac
                return None
            # Head is a sub-unit. Compute leading_frac × sub_unit_fraction.
            lf_pair = _fraction_str_to_pair(leading_frac)
            su_pair = _fraction_str_to_pair(sub_unit_fraction)
            if not (lf_pair and su_pair):
                return None
            num = lf_pair[0] * su_pair[0]
            denom = lf_pair[1] * su_pair[1]
            candidate = _format_fraction(num, denom)
            if candidate and candidate in available:
                return candidate
            return None
        if head_matched:
            return None
        # No token matched. Don't emit a fraction we can't justify
        # against a known head denomination.
        return None

    # Path 2 — count + denom token («N Speciedaler» etc.).
    for token, fn in rules:
        if head.startswith(token):
            n = count if count is not None else 1
            cand = fn(n)
            if cand and cand in available:
                return cand
            return None

    return None
