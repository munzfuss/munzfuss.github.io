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
import yaml
from pathlib import Path
from collections import defaultdict, Counter

CACHE_DIR = Path(__file__).resolve().parents[2] / "scripts" / "cache" / "bruun"
DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "locations"
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
            })
    return rows


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


def lot_compatible_with_coin(lot, candidate):
    """Apply the §9.3 KM-token parity check before linking a Bruun lot to
    a candidate coin.

    Rule:

    * When both lot and candidate carry a KM token, their parent KM
      numbers must match. (744 ↔ 744.1 ↔ 744.2 OK; 165 ↔ 166 NOT OK.)
    * When KM is absent on either side, fall back to Hede parent
      comparison. Pure Hede-only matches survive (the «hede-XXX-…»
      schema in denmark.yml uses Hede as the primary axis).
    * When neither axis has a comparable pair, return True — the
      single-letter Lange / Sieg / Dav heuristic upstream is the only
      signal we have, and demanding a parity check would reject every
      Sonderburg / Holstein-territorial coin (Lange-only catalog).
    """
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
