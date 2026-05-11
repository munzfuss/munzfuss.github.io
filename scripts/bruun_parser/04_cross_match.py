"""
Stage 4 — cross-match scope-classified Bruun lots against current YAML.

Inputs:  scripts/cache/bruun/scope.json (from stage 03)
         data/locations/{denmark,schleswig_holstein,lubeck_bishopric,bremen_verden,
                          hesse_kassel,osnabrueck,oldenburg,brunswick_lueneburg}.yml
Outputs: scripts/cache/bruun/cross_match.json
         — same scope buckets, each lot tagged with `cat` (A/B/D) and `matched_ids`

Categories:
  A — match found in YAML AND our coin already has bruun_collection_id (no action)
  B — match found AND our coin lacks bruun → enrich with bruun_collection_id +
       bruun_part + bruun_lot_no + bruun_page
  D — no match → candidate to add (presented separately for user triage)

When new locations files are created they're automatically picked up by
load_our_coins() (the loader globs all locations).
"""
import json
import re
import sys
import yaml
from pathlib import Path
from collections import defaultdict, Counter

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lib.paths import BRUUN_CACHE as CACHE_DIR, PROJECT_ROOT  # noqa: E402

DATA_DIR = PROJECT_ROOT / "data" / "locations"
OUT_DIR = CACHE_DIR


def norm_ref(s):
    if s is None:
        return None
    s = str(s).strip().lower()
    s = re.sub(r"^(?:km[\-#:\s]+|hede[\-:\s]+|lange[\-:\s]+|sieg[\-:\s]+|"
               r"fr[\.\-:\s]+|schou[\-:\s]+|dav[\.\-:\s]+|bruun[\-:\s]+)", "", s)
    s = re.sub(r"^(?:cf\.?\s*|cf\s+|~)", "", s)
    return s.strip()


def first_token(ref_value):
    if ref_value is None:
        return None
    s = str(ref_value).strip()
    s = re.sub(r"^(?:cf\.?\s*|cf\s+|~)", "", s)
    return norm_ref(re.split(r"[,;]\s*", s)[0].strip())


def _collect_alt_km(others):
    """Extract KM tokens from ``catalog.others`` (e.g. «KM# 73») so the
    parity-check accepts coins that intentionally consolidate multiple
    Krause numbers under one row (the Numista-duplicate pattern, e.g.
    km-105 carrying KM# 73 as a synonym in `others`)."""
    if not others:
        return []
    out = []
    for o in others:
        m = re.search(r"\bKM[#\-]?\s*([A-Za-z]?\d+(?:\.\d+)?[A-Za-z]*)", str(o))
        if m:
            out.append(m.group(1))
    return out


def load_our_coins():
    rows = []
    # Load every location file we currently have. New ones are auto-discovered.
    location_files = sorted(p for p in DATA_DIR.glob("*.yml")
                             if not p.name.endswith("-references.yml"))
    for path in location_files:
        slug = path.stem
        loc = yaml.safe_load(path.read_text())
        for c in loc.get("coins", []):
            cat = c.get("catalog") or {}
            others = cat.get("others") or []
            rows.append({
                "loc": slug,
                "id": c.get("id"),
                "fuss": c.get("fuss"),
                "phase": c.get("phase"),
                "year_first": c.get("year_first"),
                "year_last": c.get("year_last"),
                "year_label": c.get("year_label"),
                "ruler": c.get("ruler"),
                "mint": c.get("mint"),
                "nominal": c.get("nominal"),
                "metal": c.get("metal"),
                "fineness": c.get("fineness"),
                "km_raw": cat.get("km"), "km": first_token(cat.get("km")),
                # Alternate KM tokens consolidated in `catalog.others`
                # (Numista-duplicate / synonym pattern). Parity-check
                # passes when the lot's KM matches any one of these.
                "km_alts": _collect_alt_km(others),
                "hede_raw": cat.get("hede"), "hede": first_token(cat.get("hede")),
                "lange_raw": cat.get("lange"), "lange": first_token(cat.get("lange")),
                "sieg_raw": cat.get("sieg"), "sieg": first_token(cat.get("sieg")),
                "fr_raw": cat.get("fr"), "fr": first_token(cat.get("fr")),
                "schou_raw": cat.get("schou"), "schou": first_token(cat.get("schou")),
                "dav_raw": cat.get("dav"), "dav": first_token(cat.get("dav")),
                "bruun_lot": cat.get("bruun_lot"),
                "bruun_collection_id": cat.get("bruun_collection_id"),
                # Weight readings paired with their source labels, for the
                # §9.1/§9.3 weight-sanity gate. The gate uses entries OTHER
                # than the lot under inspection — including the lot's own
                # weight in the reference set lets the contaminated reading
                # vouch for itself (median collapses to the bad value).
                "weights_pairs": _coin_weight_pairs(c.get("weight_rough_g")),
                # Plain nominal string for the denomination-name parity gate.
                "nominal": c.get("nominal"),
            })
    return rows


def _coin_weight_pairs(raw):
    """Flatten weight_rough_g to ``list[(float, source_str)]``. Sources can
    be empty when the entry is a bare scalar."""
    if isinstance(raw, list):
        out = []
        for entry in raw:
            if isinstance(entry, dict):
                v = entry.get("value")
                if isinstance(v, (int, float)) and v > 0:
                    out.append((float(v), str(entry.get("source") or "")))
        return out
    if isinstance(raw, (int, float)) and raw > 0:
        return [(float(raw), "")]
    return []


def build_index(coins, key):
    idx = defaultdict(list)
    for c in coins:
        v = c.get(key)
        if v:
            idx[v].append(c)
    return idx


def year_overlap(yf, yl, target):
    if target is None or yf is None:
        return False
    yl = yl or yf
    return (yf - 1) <= target <= (yl + 1)


_KM_PARENT_RE = re.compile(r"^([A-Za-z]?\d+)")
_HEDE_PARENT_RE = re.compile(r"^(\d+)")


def _km_parent(km_str):
    """Strip Krause sub-variant suffix to expose the parent KM number.

    «KM 744.1» / «744.2» / «744» / «744A» all collapse to «744». The parent
    number is the §9.3 compatibility axis: same parent → same Krause type
    family, differing parents → different types that must not share a
    specimen citation.
    """
    if km_str is None:
        return None
    s = norm_ref(str(km_str))
    m = _KM_PARENT_RE.match(s)
    if not m:
        return None
    # Drop optional leading letter (Pn-style coins) and trailing sub-suffix
    parent = re.sub(r"\D+$", "", m.group(1))
    return parent or None


def _hede_parent(hede_str):
    """Strip trailing letters / sub-suffix to expose the parent Hede number.

    «Hede 164B» / «164C» / «164» all collapse to «164».
    """
    if hede_str is None:
        return None
    s = norm_ref(str(hede_str))
    m = _HEDE_PARENT_RE.match(s)
    return m.group(1) if m else None


_WEIGHT_GATE = 2.0  # max ratio between lot weight and coin median; rejects
                    # cross-denomination contamination (Doppelschilling ~2 g
                    # routing to Reichsthaler ~29 g), allows normal specimen
                    # variance + adjacent-fraction sub-variants. Mirrors the
                    # IKMK matcher's gate from match_ikmk_locations.py
                    # (commit 555260c).

# Pn / off-metal / piefort markers in primary classification position.
# When a Bruun-lot meta_line opens with one of these, the lot is a §9.1
# pattern / off-metal strike that should never link to a regular
# circulation coin. The gate scans only the head of the lot's
# meta_line (post-country-prefix) so casual mentions deeper in the
# body excerpt — e.g. «starlike pattern» — don't false-positive.
_PN_HEAD_MARKERS = (
    "gold off-metal", "silver off-metal", "off-metal strike",
    "gold pattern", "silver pattern", "copper pattern",
    "pattern strike", "trial strike", "essai",
)


def _is_pn_lot(lot):
    """True if the lot's primary classification is a Pn-tier issue
    (off-metal strike / pattern / trial / essai)."""
    meta = (lot.get("meta_line") or "").strip()
    if not meta:
        return False
    # Strip leading «COUNTRY .» / «COUNTRY,» prefix, then look at the head.
    m = re.match(r"^[A-Z]+\s*[\.,]?\s*(.*)", meta)
    head = (m.group(1) if m else meta)[:160].lower()
    return any(marker in head for marker in _PN_HEAD_MARKERS)


# Denomination synonyms — words that mean the same coin type across
# Bruun's English meta-line and our YAML's mixed German/Ukrainian/English
# nominal field. Each entry is a frozenset; two denom words are compatible
# iff they belong to the same set.
_DENOM_SYNONYMS = [
    frozenset({"thaler", "taler", "speciedaler", "species", "speciesthaler",
               "reichsthaler", "reichstaler", "reichsspeciedaler", "rigsdaler",
               "rixdaler"}),
    frozenset({"ducat", "dukat"}),
    frozenset({"krone", "guldkrone"}),  # 1 Krone ≡ 4 Mark in Christian VI's reign,
                                        # but «Mark» is its OWN type in earlier rules,
                                        # so handled via per-coin alias not here
    frozenset({"skilling"}),
    frozenset({"kroneskilling"}),       # SEPARATE from skilling — Kronemont unit
    frozenset({"sechsling"}),
    frozenset({"dreiling"}),
    frozenset({"søsling", "soesling", "sösling"}),
    frozenset({"pfennig"}),
    frozenset({"groschen"}),
    frozenset({"piefort", "pieforte"}),
    frozenset({"portugaloser"}),
    frozenset({"mark"}),
    frozenset({"hvid"}),
    frozenset({"noble"}),
]


def _denom_group(word):
    """Return the synonym set containing ``word`` (lowered), or None."""
    w = word.lower().strip()
    for grp in _DENOM_SYNONYMS:
        if w in grp:
            return grp
    return None


_DENOM_TOKEN_RE = re.compile(
    r"\b(?:1[/⁄][24816]|[½¼⅛⅓⅔¾]|\d{1,2}(?:[/⁄][24816])?)?\s*"
    r"(speciedaler|species(?:thaler)?|reichs(?:speciedaler|thaler|taler)?|"
    r"thaler|taler|"
    r"rigsdaler|rixdaler|"
    r"kroneskilling|krone|guldkrone|"
    r"sechsling|dreiling|søsling|soesling|sösling|"
    r"ducat|dukat|"
    r"skilling|"
    r"piefort|pieforte|"
    r"portugaloser|"
    r"pfennig|groschen|hvid|noble|"
    r"mark)\b",
    re.IGNORECASE,
)


def _primary_denom(text):
    """Extract the first denomination noun from a string (lot meta head
    or coin nominal). Returns the lowered noun or None."""
    if not text:
        return None
    m = _DENOM_TOKEN_RE.search(text)
    if not m:
        return None
    return m.group(1).lower()


def _denom_compatible(lot, candidate):
    """Reject when lot meta's primary denomination noun and coin nominal's
    primary denomination noun belong to DIFFERENT synonym sets (e.g.
    Kroneskilling vs Skilling, Speciedaler vs Sechsling).

    Pass-through when either side fails to parse a denom token — the
    name-extraction is brittle on long meta lines, so a missed parse
    should not gate out an otherwise-valid match.
    """
    meta = (lot.get("meta_line") or "")
    # Strip country prefix to focus on the coin classification head
    m = re.match(r"^[A-Z]+\s*[\.,]?\s*(.*)", meta.strip())
    head = (m.group(1) if m else meta)[:120]
    lot_denom = _primary_denom(head)
    nom_denom = _primary_denom(candidate.get("nominal") or "")
    if not lot_denom or not nom_denom:
        return True
    g_lot = _denom_group(lot_denom)
    g_nom = _denom_group(nom_denom)
    if not g_lot or not g_nom:
        return True
    return g_lot == g_nom


def _weight_compatible(lot, candidate):
    """Lot/candidate weight magnitudes must agree within ``_WEIGHT_GATE``×.

    Returns True (allow) when either side lacks a numeric weight — the
    gate only fires when both observations exist. Excludes weight
    readings whose source label mentions the LOT under inspection
    (lot number or Bruun-collection-id), so a previously-attached
    contaminated reading can't vouch for itself by collapsing the
    coin's median onto the lot's own value.
    """
    lot_w = lot.get("weight_g")
    if not isinstance(lot_w, (int, float)) or lot_w <= 0:
        return True
    pairs = candidate.get("weights_pairs") or []
    if not pairs:
        return True
    lot_no = str(lot.get("lot_no") or "")
    bruun_coll = str((lot.get("refs") or {}).get("Bruun") or "")
    # Source-label tokens that identify THIS lot's contribution to the row
    # so we can subtract it from the reference set.
    lot_tokens = []
    if lot_no:
        lot_tokens.append(f"lot {lot_no}")
        lot_tokens.append(f"lot_no: {lot_no}")
    if bruun_coll:
        lot_tokens.append(f"Bruun-coll. {bruun_coll}")
        lot_tokens.append(f"bruun_collection_id: {bruun_coll}")
    others = [v for v, src in pairs
              if not any(tok in src for tok in lot_tokens)]
    if not others:
        return True
    others.sort()
    median = others[len(others) // 2]
    if median <= 0:
        return True
    ratio = lot_w / median
    return (1.0 / _WEIGHT_GATE) <= ratio <= _WEIGHT_GATE


def lot_compatible_with_coin(lot, candidate):
    """Apply §9.1 + §9.3 compatibility checks before linking a Bruun
    lot to a candidate coin.

    Three independent gates:

    1. **§9.1 Pn-tier rejection.** If the lot's primary classification
       is an off-metal strike / pattern / trial / essai, never link —
       these belong to separate registers, not coin tables (cf.
       CLAUDE.md §9 inclusion criteria).
    2. **Weight-sanity (mass-magnitude).** When both lot and candidate
       publish a weight, the ratio must fall within
       ``[1/_WEIGHT_GATE, _WEIGHT_GATE]``. Catches cross-denomination
       contamination where a same-KM token bridges different Krause
       sub-volumes (e.g. KM-79 SH-Glückstadt 1 Sechsling ≈ 0.6 g vs
       KM-79 Denmark 4-Speciedaler ≈ 116 g).
    3. **§9.3 KM-token parity** (existing). Same-parent-KM only —
       744 ↔ 744.1 ↔ 744.2 OK; 165 ↔ 166 NOT OK. Falls back to
       parent-Hede when KM is absent. Accepts KMs listed in
       ``catalog.others`` for the Numista-duplicate consolidation
       pattern.
    """
    if _is_pn_lot(lot):
        return False
    if not _weight_compatible(lot, candidate):
        return False
    # Denom-name parity gate (`_denom_compatible`) was prototyped here
    # but produced false-positives on the «4 Mark (Krone)» / «Species-
    # Dukat» / «Courant Ducat (Rixdaler)» Bruun-double-naming patterns
    # where the lot legitimately describes the same coin under two
    # parallel names. Manual cleanup is the right tool for the
    # remaining cross-volume KM-collisions; the helper stays in place
    # for future targeted use (e.g. count-ratio + hard-incompatible-
    # pairs check) but doesn't gate routing today.

    refs = lot.get("refs", {})

    lot_km = _km_parent(refs.get("KM"))
    coin_kms = [_km_parent(candidate.get("km"))]
    coin_kms.extend(_km_parent(k) for k in (candidate.get("km_alts") or []))
    coin_kms = [k for k in coin_kms if k]
    if lot_km and coin_kms:
        return lot_km in coin_kms

    lot_hede = _hede_parent(refs.get("Hede"))
    coin_hede = _hede_parent(candidate.get("hede"))
    if lot_hede and coin_hede:
        return lot_hede == coin_hede

    return True


def match_lot(lot, indices):
    refs = lot.get("refs", {})
    year = lot.get("year")
    candidates = []
    rejected = []  # for debug — candidates that the parity gate cut
    for ref_key, idx_key in [("KM", "km"), ("Hede", "hede"), ("Lange", "lange"),
                              ("Sieg", "sieg"), ("Fr", "fr"), ("Schou", "schou"),
                              ("Dav", "dav")]:
        v = refs.get(ref_key)
        if not v:
            continue
        v_norm = norm_ref(v)
        for cand in indices[idx_key].get(v_norm, []):
            if not year_overlap(cand["year_first"], cand["year_last"], year):
                continue
            if not lot_compatible_with_coin(lot, cand):
                rejected.append((cand, f"{ref_key}={v_norm}+year (KM/Hede parity FAIL)"))
                continue
            candidates.append((cand, f"{ref_key}={v_norm}+year"))
    bruun_id = refs.get("Bruun")
    if bruun_id:
        for cand in indices["bruun_lot"].get(str(bruun_id), []):
            if not lot_compatible_with_coin(lot, cand):
                rejected.append((cand, f"Bruun-id={bruun_id} (KM/Hede parity FAIL)"))
                continue
            candidates.append((cand, f"Bruun-id={bruun_id}"))

    seen = set()
    deduped = []
    for cand, reason in candidates:
        if cand["id"] in seen:
            continue
        seen.add(cand["id"])
        deduped.append((cand, reason))

    if not deduped:
        # If parity-gate cut some candidates, surface that in the reason so
        # triage can spot them in the regenerated cross_match.json.
        if rejected:
            cut_reason = "parity-rejected: " + "; ".join(
                f"{c['id']} ({r})" for c, r in rejected[:3]
            )
            return ("D", [], cut_reason)
        return ("D", [], "no match")
    has_bruun = all(c["bruun_lot"] or c["bruun_collection_id"] for c, _ in deduped)
    return ("A" if has_bruun else "B", [c for c, _ in deduped],
            "; ".join(r for _, r in deduped[:3]))


def main():
    our_coins = load_our_coins()
    print(f"Our YAML coins: {len(our_coins)}")
    indices = {
        "km": build_index(our_coins, "km"),
        "hede": build_index(our_coins, "hede"),
        "lange": build_index(our_coins, "lange"),
        "sieg": build_index(our_coins, "sieg"),
        "fr": build_index(our_coins, "fr"),
        "schou": build_index(our_coins, "schou"),
        "dav": build_index(our_coins, "dav"),
        "bruun_lot": build_index(our_coins, "bruun_lot"),
        "bruun_collection_id": build_index(our_coins, "bruun_collection_id"),
    }

    extended = json.loads((OUT_DIR / "scope.json").read_text())

    # In-scope per bucket
    per_bucket = {b: [l for l in lots if not l["exclusions"]]
                   for b, lots in extended.items() if b != "OUT"}

    # Buckets with existing YAML — auto-detected from data/locations/*.yml
    location_files = {p.stem for p in DATA_DIR.glob("*.yml")
                       if not p.name.endswith("-references.yml")}

    summary = {}
    for bucket, lots in per_bucket.items():
        # Cross-match for buckets that have existing YAML coverage
        if bucket in location_files:
            cats = Counter()
            for lot in lots:
                cat, cands, reason = match_lot(lot, indices)
                cats[cat] += 1
                lot["cat"] = cat
                lot["matched_ids"] = [c["id"] for c in cands]
            summary[bucket] = {"total": len(lots), "A": cats["A"], "B": cats["B"], "D": cats["D"]}
        else:
            # New territories — no existing YAML yet, all are D candidates
            for lot in lots:
                lot["cat"] = "D"
            summary[bucket] = {"total": len(lots), "A": 0, "B": 0, "D": len(lots)}

    print()
    print("=== Cross-match summary (extended scope) ===")
    print(f"{'Bucket':<25} {'Total':>6} {'A':>4} {'B':>4} {'D':>4}")
    print("-" * 50)
    grand = {"total": 0, "A": 0, "B": 0, "D": 0}
    for bucket in sorted(summary.keys(), key=lambda b: -summary[b]["total"]):
        s = summary[bucket]
        print(f"{bucket:<25} {s['total']:>6} {s['A']:>4} {s['B']:>4} {s['D']:>4}")
        for k, v in s.items():
            grand[k] += v
    print("-" * 50)
    print(f"{'TOTAL':<25} {grand['total']:>6} {grand['A']:>4} {grand['B']:>4} {grand['D']:>4}")

    # Save extended cross-match
    (OUT_DIR / "cross_match.json").write_text(
        json.dumps(per_bucket, indent=2, ensure_ascii=False, default=str)
    )
    print(f"\n→ {OUT_DIR / 'cross_match.json'}")


if __name__ == "__main__":
    main()
