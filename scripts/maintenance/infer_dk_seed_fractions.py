"""Set ``coin.fraction`` on every Denmark seed coin whose nominal
maps cleanly to a fraction that the coin's `fuss` already defines.

Without ``fraction`` the build pipeline can't look up the Soll value
in ``fuesse[fuss].fractions[fraction]`` → both «Soll-Fein» and
«Δ» (Delta) columns render blank. The Hede / ucoin seeds carry
``weight_rough_g`` + ``fineness`` + ``fuss`` + ``phase`` directly
from source; supplying ``fraction`` unblocks the rest of the
compute pipeline.

Rules are conservative — we lift them from the actual canonical
entries in `denmark.yml` (which were curated by hand). Only
exact-token matches at the per-fuss level are honoured, and the
target fraction must exist in `data/shared/fuesse.yml` for that
fuss. Anything ambiguous stays blank rather than risk a wrong Soll.

Idempotent: re-running after new seed imports re-applies cleanly.

Run:
    python scripts/maintenance/infer_dk_seed_fractions.py [--dry-run]
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import yaml as _yaml
from ruamel.yaml import YAML

PROJECT = Path(__file__).resolve().parents[2]
TARGETS = [
    PROJECT / "data" / "locations" / "denmark.yml",
    PROJECT / "data" / "seed" / "hede" / "denmark.yml",
]
FUESSE_PATH = PROJECT / "data" / "shared" / "fuesse.yml"


# Per-fuss (denom_token, count-multiplier-or-None) → fraction. The
# value can be:
#   - a string: the fixed fraction (e.g. «1/96» for any «N Skilling»
#     in the 11_333_thaler fuss; or «1/3» for «1 Mark» in 9_25)
#   - a callable: count → fraction_string (e.g. lambda n: str(n) for
#     «N Speciedaler» — count becomes the fraction directly)
#
# Tokens are lowercased and stripped before lookup. The matcher
# tolerates trailing tokens (e.g. «Danske», «Klippe», «Piefort»,
# «(Krone)») by matching only the head denom-token; if more
# specificity is needed, add an explicit longer-token rule first.
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
        ("kronerigsdaler", _fixed("1")),       # 6 Mark = 1 Speciedaler
        ("piaster", _fixed("1")),               # Tranquebar 1 Piaster
        ("krone", _fixed("1")),                 # «Krone» as 4-Mark unit
        ("kroner", _fixed("1")),
        ("mark", lambda n: {1: "1/3", 2: "2/3", 4: "1", 6: "1",
                              8: "2", 12: "3", 16: "4"}.get(n, None)),
        ("skilling", lambda n: {1: "1/96", 2: "1/48", 4: "1/24",
                                  6: "1/16", 8: "1/12", 12: "1/8",
                                  16: "1/6", 24: "1/4", 32: "1/3"}.get(n, None)),
        ("hvid", _fixed("1/192")),              # 4 Hvid = 1 Skilling
        ("søsling", _fixed("1/96")),            # 2 Hvid = 1 Søsling
        ("soesling", _fixed("1/96")),
        ("penning", _fixed("1/192")),
    ],
    # ------- 9-Thaler-Fuß (early Speciedaler, 1566-1625) -------
    # Note: 9_thaler.fractions has no '2/3' — «2 Mark» in this fuss
    # falls through to no_rule (intentional; multi-Mark units in the
    # 1566-1625 window are sparsely documented).
    "9_thaler": [
        ("speciedaler", _identity),
        ("mark", lambda n: {1: "1/3", 4: "1", 6: "1",
                              8: "2", 12: "3"}.get(n, None)),
        ("skilling", lambda n: {1: "1/96", 2: "1/48", 4: "1/24",
                                  8: "1/12"}.get(n, None)),
        ("hvid", _fixed("1/192")),
        ("søsling", _fixed("1/96")),
        ("penning", _fixed("1/192")),
        ("daler", _identity),                   # 3-/4-Daler multiples (6/8 not in fractions list)
    ],
    # ------- 11⅓-Thaler-Fuß (Helstaten Courant, 1726-1813) -------
    "11_333_thaler": [
        ("rigsdaler", _identity),
        ("rixdaler", _identity),
        ("skilling", lambda n: {1: "1/96", 2: "1/48", 4: "1/24",
                                  8: "1/12", 12: "1/8", 24: "1/4"}.get(n, None)),
        ("søsling", _fixed("1/96")),
        ("hvid", _fixed("1/192")),
        ("penning", _fixed("1/192")),
    ],
    # ------- 18½-Thaler-Fuß (Rigsbankdaler, 1813-1874) -------
    "18_5_thaler": [
        ("rigsbankdaler", _identity),
        ("rigsdaler", _identity),
        ("rigsbankskilling", lambda n: {1: "1/96", 2: "1/96",
                                          3: "1/24", 4: "1/24",
                                          6: "1/12", 12: "1/12",
                                          16: "1/6"}.get(n, None)),
        ("skilling", lambda n: {1: "1/96", 2: "1/96", 4: "1/24",
                                  6: "1/12", 8: "1/12",
                                  12: "1/12", 16: "1/6"}.get(n, None)),
    ],
    # ------- 10½-Krone-Fuß (Christian V Krone + Frederik III) -------
    "kronemont": [
        ("krone", _identity),
        ("kroner", _identity),
        ("mark", lambda n: {1: "1/4", 2: "1/2", 4: "1", 6: "1"}.get(n, None)),
    ],
    # ------- Christian IV Krone / Corona Danica -------
    # Christian IV's plain «N Skilling» 1618-1619 issues (Hede
    # c4h110..c4h112 etc.) are minted at the same MFU 10,8 daler
    # standard as the Krone — they're scheide sub-units of the
    # kronemont_chr_iv Fuß, so 1 Skilling = 1/96, 2 = 1/48 etc.
    "kronemont_chr_iv": [
        ("krone", _identity),
        ("kroneskilling", lambda n: {1: "1/96", 2: "1/48",
                                       4: "1/24", 8: "1/12"}.get(n, None)),
        ("skilling", lambda n: {1: "1/96", 2: "1/48",
                                  4: "1/24", 8: "1/12"}.get(n, None)),
    ],
    # ------- 13⅓-Krone-Fuß (Specieskrone, 1693-1771) -------
    "kronemont_fine": [
        ("krone", _identity),
        ("kroner", _identity),
        ("mark", lambda n: {1: "1/4", 2: "1/2", 4: "1"}.get(n, None)),
    ],
    # ------- Reichsdukatenfuß (gold, .986) -------
    "reichsdukatenfuss": [
        ("ducat", _identity),
        ("dukat", _identity),
        ("ducats", _identity),
        ("portugaloser", lambda n: str(n * 10) if n else "10"),
        ("portugaløser", lambda n: str(n * 10) if n else "10"),
        ("rosenobel", _fixed("5/2")),
        ("gylden", _identity),                  # Ungersk / Rhinsk Gylden ≈ Ducat
        ("gulden", _identity),
        ("goldgulden", _identity),
        ("guldmønt", _identity),
    ],
    # ------- Pistolenfuß (gold, .906) -------
    "pistolenfuss": [
        ("pistole", _identity),
        ("d'or", _identity),
        ("frederik", _identity),                # «N Frederik d'Or» — strip the d'Or matching
        ("christian", _identity),               # «N Christian d'Or»
        ("frederiksdor", _identity),
        ("christiansdor", _identity),
    ],
    # ------- Courantdukatenfuß (gold, .875) -------
    "courantdukatenfuss": [
        ("kurantdukat", _identity),
        ("speciedukat", _identity),
    ],
    # ------- Guldkrone (gold, .917) -------
    "guldkrone": [
        ("guldkrone", _identity),
        ("guldcrone", _identity),
    ],
    # ------- Reichsgoldmünzfuß (German 1871, gold) — kept for future
    # Holstein-on-Reichsmark pages; Denmark's 1873-1914 gold is on
    # kronefod, not this Fuß.
    "reichsgoldmuenzfuss": [
        ("krone", _identity),
        ("kroner", _identity),
    ],
    # ------- Krone-fod (Skandinavisk Møntunion, 1873-1914 gold) -------
    "kronefod": [
        ("krone", _identity),                   # 5 Kroner / 10 Kroner / 20 Kroner
        ("kroner", _identity),
    ],
    # ------- Krone-fod silver / copper auxiliaries -------
    # 1, 2 Kroner = Kurant silver («1»/«2» fractions, .800).
    # 25 øre = 1/4, 10 øre = 1/10, 5 / 2 / 1 øre = 1/20 / 1/50 / 1/100
    # — see fuesse.yml::kronefod_silver.fractions for the per-
    # denomination Soll-Fein values.
    "kronefod_silver": [
        ("krone", _identity),
        ("kroner", _identity),
        # Øre denominations: «N øre» → fraction = «1/(100/N)»
        # 25 → 1/4, 10 → 1/10, 5 → 1/20, 2 → 1/50, 1 → 1/100
        ("øre",  lambda n: {1: "1/100", 2: "1/50", 5: "1/20",
                              10: "1/10", 25: "1/4", 50: "1/2"}.get(n, None)),
        ("ore",  lambda n: {1: "1/100", 2: "1/50", 5: "1/20",
                              10: "1/10", 25: "1/4", 50: "1/2"}.get(n, None)),
        ("öre",  lambda n: {1: "1/100", 2: "1/50", 5: "1/20",
                              10: "1/10", 25: "1/4", 50: "1/2"}.get(n, None)),
    ],
}


_NOMINAL_RE = re.compile(
    r"^\s*"
    r"(?P<frac_num>1/\d+|⅛|¼|⅓|½|⅔|¾)?\s*"     # leading fraction («½ Speciedaler»)
    r"(?P<count>\d+(?:[,\.]\d+)?)?\s*"          # count number («2 Speciedaler»)
    r"(?P<rest>.+?)\s*$",
)

_FRACTION_UNICODE = {
    "½": "1/2", "¼": "1/4", "¾": "3/4",
    "⅓": "1/3", "⅔": "2/3", "⅛": "1/8",
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


def infer_fraction(coin: dict, fuss_fractions: dict[str, dict]) -> str | None:
    fuss = coin.get("fuss")
    if not fuss or fuss == "seed_unsorted":
        return None
    rules = RULES.get(fuss)
    if not rules:
        return None
    nom = coin.get("nominal") or ""
    leading_frac, count, rest = _parse_nominal_head(nom)
    head = _denom_head_token(rest)
    if not head:
        return None

    available = fuss_fractions.get(fuss, set())

    # Path 1 — leading unicode/text fraction («½ Speciedaler»). The
    # leading-fraction wins over count unless count specifies a
    # multi-unit denomination.
    if leading_frac:
        candidate = leading_frac
        if candidate in available:
            # Sanity-check the head matches a defined denom for this fuss
            for token, _ in rules:
                if head.startswith(token):
                    return candidate
            # leading frac without recognised head — still emit
            return candidate

    # Path 2 — count + denom token («N Speciedaler» etc.).
    for token, fn in rules:
        if head.startswith(token):
            n = count if count is not None else 1
            cand = fn(n)
            if cand and cand in available:
                return cand
            return None

    return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true",
                    help="Report what would change without writing files")
    args = ap.parse_args()

    # Load defined fractions per fuss
    with FUESSE_PATH.open() as f:
        fuesse_raw = _yaml.safe_load(f)
    fuss_fractions: dict[str, set] = {
        fid: set((d.get("fractions") or {}).keys())
        for fid, d in fuesse_raw.items()
    }

    y = YAML()
    y.preserve_quotes = True
    y.width = 4096
    y.indent(mapping=2, sequence=4, offset=2)

    grand = {"set": 0, "already_set": 0, "no_rule": 0, "no_fuss": 0}

    for path in TARGETS:
        if not path.exists():
            continue
        with path.open() as f:
            doc = y.load(f)
        coins = doc.get("coins") or []
        per_file = {"set": 0, "already_set": 0, "no_rule": 0, "no_fuss": 0}
        no_rule_samples = []
        for coin in coins:
            if coin.get("fraction"):
                per_file["already_set"] += 1
                continue
            if coin.get("fuss") == "seed_unsorted" or not coin.get("fuss"):
                per_file["no_fuss"] += 1
                continue
            frac = infer_fraction(coin, fuss_fractions)
            if frac:
                coin["fraction"] = frac
                per_file["set"] += 1
            else:
                per_file["no_rule"] += 1
                if len(no_rule_samples) < 6:
                    no_rule_samples.append(
                        (coin.get("id"), coin.get("nominal"), coin.get("fuss"))
                    )

        if not args.dry_run and per_file["set"]:
            with path.open("w") as f:
                y.dump(doc, f)

        print(f"=== {path.relative_to(PROJECT)} ({len(coins)} coins) ===")
        for k, n in per_file.items():
            print(f"  {k:18s} {n:5d}")
            grand[k] += n
        if no_rule_samples:
            print("  no-rule samples:")
            for cid, nom, f in no_rule_samples:
                print(f"    {cid:25s} nom={nom!r:25s} fuss={f}")
        print()

    print("Grand total:")
    for k, n in grand.items():
        print(f"  {k:18s} {n:5d}")
    if args.dry_run:
        print("(dry-run — no files written)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
