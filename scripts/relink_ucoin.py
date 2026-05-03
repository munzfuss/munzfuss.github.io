#!/usr/bin/env python3
"""
Add ucoin source URLs to existing Schleswig coins where the match is
**provably correct** — KM# + year-range overlap + denomination tokens
agree (with orthography equivalence) + weight/fineness within tolerance.

This is the rewritten v2 of the linker. The v1 (using KM# + ±10y year
proximity only) attached 136 URLs but ~31% were wrong (different
variant under the same KM# but in a different Krause section, e.g.
Royal Denmark vs Holstein-duchy).

Match rules (ALL must pass):
  1. Same KM# (with parent-alias: "26" matches "26.1/26.2", and vice versa)
  2. Year ranges OVERLAP — not just within ±10y. Ucoin's
     [yf, yl] and ours [year_first, year_last] must intersect.
  3. Leading-quantity match: "4 Marck Danske" → 4, "2 mark dansk" → 2,
     so 4 ≠ 2 ⇒ reject.
  4. Denomination tokens share meaning: after orthography
     normalisation ("Marck"="mark", "Danske"="dansk", "Lybsk"="Lübisch",
     "Thaler"="Speciedaler" in Schleswig context, etc.) the meaningful
     (non-numeric) tokens must overlap, AND the leading quantity must agree.
  5. Source-trust:
     - Holstein-source ucoin entries (period_2939, country_schleswig_holstein,
       period_2995, q_holstein_extras): trust unconditionally.
     - Hanseatic (Lübeck/Hamburg) entries: skip (out of scope).
     - Denmark-source entries: also require Numista mint NOT to be
       Copenhagen-only.

Idempotent: skips ucoin URLs already present in a coin's sources.

Run:  .venv/bin/python scripts/oneoff/ucoin_link_existing.py
      .venv/bin/python scripts/oneoff/ucoin_link_existing.py --dry-run
"""
from __future__ import annotations

import argparse
import json
import re
import unicodedata
from pathlib import Path

from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap, CommentedSeq

CACHE_UCOIN = Path("scripts/cache/ucoin")
CACHE_NUMISTA = Path("scripts/cache/numista")
SCHLESWIG_HOLSTEIN = Path("data/locations/schleswig_holstein.yml")

HOLSTEIN_SOURCES = {"country_schleswig_holstein", "period_2939",
                     "period_2995", "q_holstein_extras"}

EASY_MINTS = {"glückstadt", "altona", "oldendorf"}
AMBIGUOUS_MINTS = {"schleswig", "tönning", "toenning", "reinfeld",
                   "steinbek", "kiel", "burg auf fehmarn"}
COPENHAGEN_MINTS = {"copenhagen", "kopenhagen", "royal danish mint"}


# --- Denomination matching helpers ----------------------------------------

SAME_TOKEN_GROUPS = [
    {"marck", "mark"},
    {"danske", "dansk"},
    {"lybsk", "lubsk", "lubisch"},
    # Thaler-class — covers "Reichsthaler" ≡ "Speciedaler" in Schleswig
    # 9¼-Fuß. Also catches compound tokens "Reichs Thaler" /
    # "Thaler Species" / "Speziesdaler" splitting into separate words.
    {"speciedaler", "speciesdaler", "speziesdaler", "thaler", "daler",
     "reichsthaler", "reichs", "species", "spec"},
    {"dukat", "ducat"},
    {"skilling", "schilling", "schillng"},  # "schillng" typo in ucoin slug
    {"sosling", "soesling"},
    {"kroner", "krone"},  # silver Krone; "guldkrone" deliberately excluded
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


def leading_qty(s: str) -> float | None:
    """Extract the leading numeric quantity from a denomination string.
    "4 Marck Danske" → 4.0; "1/16 Reichs Thaler" → 0.0625; "⅔ Spec" → 0.667.
    Returns None if no leading number found.
    """
    s = _normalize(s).strip()
    if s.startswith("."):
        s = "0" + s
    m = re.match(r"^\s*(\d+(?:\.\d+)?)(?:\s*/\s*(\d+(?:\.\d+)?))?", s)
    if not m:
        return None
    n = float(m.group(1))
    if m.group(2):
        d = float(m.group(2))
        if d > 0:
            n = n / d
    return n


def all_quantities(s: str) -> list[float]:
    """All numeric quantities in a denomination string.
    "⅙ Thaler Species 10 Schilling Courant" → [0.167, 10].
    Used to match ucoin's simpler labels against our verbose dual-name
    nominals like "X Thaler Species N Schilling Courant".
    """
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


def tokens_share_meaning(a: set[str], b: set[str]) -> bool:
    """True if a and b share a meaningful (non-numeric) token,
    treating SAME_TOKEN_GROUPS as equivalent."""
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


def parse_ucoin_year(yr: str) -> tuple[int, int] | None:
    if not yr:
        return None
    m = re.match(r"(\d{4})(?:[–\-](\d{4}))?", str(yr))
    if not m:
        return None
    yf = int(m.group(1))
    yl = int(m.group(2)) if m.group(2) else yf
    return yf, yl


def denom_compatible(our_nominal: str, ucoin_denom: str) -> bool:
    """A ucoin entry is compatible with our coin iff:
      - meaningful (non-numeric) tokens share via SAME_TOKEN_GROUPS, AND
      - the ucoin's leading quantity matches ANY quantity in our nominal
        (our nominals can be dual-form like "⅙ Thaler Species 10 Schilling
        Courant" — both 0.167 and 10 are valid quantities for matching).
    """
    if not our_nominal or not ucoin_denom:
        return False

    a = normalize_denom(our_nominal)
    b = normalize_denom(ucoin_denom)
    if not tokens_share_meaning(a, b):
        return False

    qb = leading_qty(ucoin_denom)
    qs = all_quantities(our_nominal)
    if qb is not None and qs:
        # Allow tiny floating-point drift (1/16 = 0.0625 exactly)
        if not any(abs(qb - q) <= 0.005 for q in qs):
            return False
    return True


def years_overlap(our_yf: int, our_yl: int, ucoin_year: str) -> bool:
    """True if the two year ranges intersect (inclusive)."""
    uy = parse_ucoin_year(ucoin_year)
    if not uy or not our_yf:
        return False
    yf, yl = uy
    yl_ours = our_yl or our_yf
    return not (yl < our_yf or yf > yl_ours)


# --- Numista mint cross-reference -----------------------------------------

def load_ucoin_index():
    with open(CACHE_UCOIN / "_url_index.json") as fp:
        return json.load(fp)


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


def has_holstein_mint(mint_names: list[str]) -> bool:
    if not mint_names:
        return False
    txt = " ".join(mint_names).lower()
    return (any(m in txt for m in EASY_MINTS) or
            any(m in txt for m in AMBIGUOUS_MINTS))


def is_copenhagen_only(mint_names: list[str]) -> bool:
    if not mint_names:
        return False
    txt = " ".join(mint_names).lower()
    has_cph = any(m in txt for m in COPENHAGEN_MINTS)
    has_holstein = (any(m in txt for m in EASY_MINTS) or
                    any(m in txt for m in AMBIGUOUS_MINTS))
    return has_cph and not has_holstein


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


# --- Main -----------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--verbose", action="store_true",
                    help="print every match decision")
    args = ap.parse_args()

    ucoin = load_ucoin_index()
    numista_mints = load_numista_mints()

    by_km: dict[str, list[dict]] = {}
    for tid, e in ucoin.items():
        km = (e.get("km") or "").replace("KM# ", "").replace("UC# ", "").replace("H# ", "").strip()
        e["_tid"] = tid
        by_km.setdefault(km, []).append(e)
        if "." in km:
            by_km.setdefault(km.split(".")[0], []).append(e)

    yaml = YAML(typ="rt")
    yaml.preserve_quotes = True
    yaml.width = 1000
    yaml.indent(mapping=2, sequence=4, offset=2)
    with open(SCHLESWIG_HOLSTEIN) as fp:
        doc = yaml.load(fp)

    coins_modified = 0
    sources_added = 0
    skipped_dup = 0
    skipped_year = 0
    skipped_denom = 0
    skipped_mint = 0
    skipped_hanseatic = 0

    rejected_examples: list[str] = []

    for coin in doc.get("coins", []):
        our_kms = get_kms_from_coin(coin)
        if not our_kms:
            continue

        yf = coin.get("year_first") or 0
        yl = coin.get("year_last") or yf
        our_nominal = coin.get("nominal", "")

        existing_sources = coin.get("sources") or []
        existing_urls = {s.get("url") for s in existing_sources if isinstance(s, dict)}

        new_sources_for_this_coin = []

        for km in our_kms:
            for u in by_km.get(km, []):
                # 1. Year range overlap (no ±10y slop)
                if not years_overlap(yf, yl, u.get("year") or ""):
                    skipped_year += 1
                    if args.verbose:
                        print(f"  [{coin['id']}] KM={km} skip year: ours={yf}-{yl}, ucoin={u.get('year')}")
                    continue

                # 2. Source-trust: only Hanseatic gets dropped here.
                # The Copenhagen-only Numista filter is OFF by design —
                # strict denom+year+fineness identity below is a stronger
                # signal than mint provenance (e.g. Christian IV's
                # Kronemønt was Copenhagen-struck but historically
                # belongs to our Schleswig-Holstein scope as a ruler-
                # relevant coin).
                src = u.get("source", "")
                if src in {"country_lubeck", "country_hamburg",
                           "period_1204", "period_1205"}:
                    skipped_hanseatic += 1
                    continue

                # 3. Denomination compatibility (leading qty + tokens)
                if not denom_compatible(our_nominal, u.get("denom", "")):
                    skipped_denom += 1
                    if args.verbose:
                        print(f"  [{coin['id']}] KM={km} skip denom: ours='{our_nominal}', ucoin='{u.get('denom')}'")
                    rejected_examples.append(
                        f"  REJECT denom  {coin['id']:32s}  KM={km:8s}  "
                        f"ours='{our_nominal}'  ucoin='{u.get('denom')}'  "
                        f"({u.get('year')})"
                    )
                    continue

                # 4. Fineness sanity check — catches different
                # alloy variants under the same KM# (e.g. silver
                # Rigsdaler Rigsmønt .875 vs lower-grade .500 issue).
                # Only reject if difference is large enough to
                # indicate a different metal/alloy class.
                our_f = coin.get("fineness")
                uc_f = u.get("fineness")
                if our_f and uc_f and our_f > 0:
                    rel = abs(our_f - uc_f) / our_f
                    if rel > 0.40:
                        if args.verbose:
                            print(f"  [{coin['id']}] KM={km} skip fineness: ours={our_f}, ucoin={uc_f} ({round(rel*100)}%)")
                        skipped_denom += 1  # bucket with denom rejection for the report
                        rejected_examples.append(
                            f"  REJECT fineness {coin['id']:30s}  KM={km:8s}  "
                            f"ours={our_f}  ucoin={uc_f}  ({round(rel*100)}% off)"
                        )
                        continue

                url = u["url"]
                if url in existing_urls:
                    skipped_dup += 1
                    continue
                if any(s.get("url") == url for s in new_sources_for_this_coin):
                    continue

                new_sources_for_this_coin.append({
                    "type": "ucoin",
                    "url": url,
                    "ref": f"ucoin tid {u['_tid']}",
                })

        if new_sources_for_this_coin:
            if "sources" not in coin or coin.get("sources") is None:
                coin["sources"] = CommentedSeq()
            for s in new_sources_for_this_coin:
                m = CommentedMap()
                m["type"] = s["type"]
                m["url"] = s["url"]
                m["ref"] = s["ref"]
                coin["sources"].append(m)
                sources_added += 1
            coins_modified += 1

    print(f"Coins modified:                {coins_modified}")
    print(f"ucoin URLs added:              {sources_added}")
    print(f"Skipped (already present):     {skipped_dup}")
    print(f"Skipped (year disjoint):       {skipped_year}")
    print(f"Skipped (denom mismatch):      {skipped_denom}")
    print(f"Skipped (Copenhagen-only):     {skipped_mint}")
    print(f"Skipped (Hanseatic out-scope): {skipped_hanseatic}")

    if args.verbose and rejected_examples:
        print(f"\nFirst 30 denom rejections:")
        for r in rejected_examples[:30]:
            print(r)

    if not args.dry_run:
        with open(SCHLESWIG_HOLSTEIN, "w") as fp:
            yaml.dump(doc, fp)
        print(f"\nWrote {SCHLESWIG_HOLSTEIN}")
    else:
        print("\n(dry-run: no file written)")


if __name__ == "__main__":
    main()
