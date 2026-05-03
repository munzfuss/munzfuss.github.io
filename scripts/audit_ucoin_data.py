#!/usr/bin/env python3
"""
For every base coin that has a ucoin source URL, compare the ucoin data
(weight_g, fineness, diameter_mm, denom, year) with what we have stored.

Aggregate:
  - PERFECT_MATCH:  every comparable field agrees
  - PARTIAL_MATCH:  one or more fields differ; lists which
  - NEW_DATA:       ucoin provides field(s) we don't have

Fields with tolerances:
  weight_g    — 5 % tolerance (catalogue specs vs typical specimen)
  fineness    — 3 % tolerance (rounding in old sources)
  diameter_mm — 1 mm tolerance

Note: a coin with two ucoin URLs is reported separately for each URL.

Run:  .venv/bin/python scripts/oneoff/ucoin_data_audit.py
"""
from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from pathlib import Path

import yaml


CACHE_UCOIN = Path("scripts/cache/ucoin")
SCHLESWIG_HOLSTEIN = Path("data/locations/schleswig_holstein.yml")
OUT_JSON = CACHE_UCOIN / "_data_audit.json"


def parse_ucoin_year(yr: str) -> tuple[int, int] | None:
    if not yr:
        return None
    m = re.match(r"(\d{4})(?:[–\-](\d{4}))?", str(yr))
    if not m:
        return None
    yf = int(m.group(1))
    yl = int(m.group(2)) if m.group(2) else yf
    return yf, yl


def cmp_weight(our_w: float | None, uc_w: float | None) -> str | None:
    if our_w is None and uc_w is None:
        return None  # nothing to compare
    if our_w is None:
        return f"new_data: weight={uc_w}"
    if uc_w is None:
        return None  # ucoin doesn't say — fine
    if our_w == 0:
        return None
    rel = abs(our_w - uc_w) / our_w
    if rel <= 0.05:
        return None  # match
    return f"weight: ours={our_w}, ucoin={uc_w} ({round(rel*100)}% off)"


def cmp_fineness(our_f, uc_f) -> str | None:
    if our_f is None and uc_f is None:
        return None
    if our_f is None:
        return f"new_data: fineness={uc_f}"
    if uc_f is None:
        return None
    if our_f == 0:
        return None
    rel = abs(our_f - uc_f) / our_f
    if rel <= 0.03:
        return None
    return f"fineness: ours={our_f}, ucoin={uc_f} ({round(rel*100)}% off)"


def cmp_diameter(our_d, uc_d) -> str | None:
    if our_d is None and uc_d is None:
        return None
    if our_d is None:
        return f"new_data: diameter_mm={uc_d}"
    if uc_d is None:
        return None
    if abs(our_d - uc_d) <= 1.0:
        return None
    return f"diameter_mm: ours={our_d}, ucoin={uc_d}"


def cmp_year(our_yf, our_yl, uc_year) -> str | None:
    if not uc_year:
        return None
    uy = parse_ucoin_year(uc_year)
    if not uy:
        return None
    yf, yl = uy
    yl_ours = our_yl or our_yf or 0
    yf_ours = our_yf or 0
    # Mismatch if ranges differ significantly
    if yf == yf_ours and yl == yl_ours:
        return None  # exact match
    # Overlap is fine — only flag if ranges are quite different
    if yf < yf_ours - 2 or yl > yl_ours + 2:
        return f"year_range: ours=[{yf_ours},{yl_ours}], ucoin=[{yf},{yl}]"
    return None  # close enough


def _field_pairs(field_value):
    """Normalise a measurement field to [(value, source), ...].
    Handles bare scalar (single (value, None) entry) and list-form
    ([{value, source}, ...] entries)."""
    if field_value is None:
        return []
    if isinstance(field_value, (int, float)):
        return [(float(field_value), None)]
    if isinstance(field_value, list):
        out = []
        for entry in field_value:
            if isinstance(entry, dict):
                out.append((entry.get("value"), entry.get("source")))
        return out
    return []


def alt_covers_field(coin, tid, field, ucoin_value, tolerance_pct):
    """Return True if any non-primary entry in `coin[field]` (list-form)
    is (a) sourced from this ucoin tid (or generic "ucoin" label) AND
    (b) records a value matching ucoin's reading. Suppresses conflict
    flags when the divergence is already structurally documented."""
    if not ucoin_value:
        return False
    pairs = _field_pairs(coin.get(field))
    # Skip the first (primary) entry; check the rest
    for val, src in pairs[1:]:
        if val is None or src is None:
            continue
        sl = src.lower()
        if not (f"tid {tid}" in sl or sl == "ucoin"):
            continue
        if val == 0:
            continue
        rel = abs(val - ucoin_value) / val
        if rel <= tolerance_pct:
            return True
    return False


def main():
    with open(CACHE_UCOIN / "_url_index.json") as fp:
        ucoin = json.load(fp)
    with open(SCHLESWIG_HOLSTEIN) as fp:
        doc = yaml.safe_load(fp)

    rows = []  # one row per (coin, ucoin_url) pair

    for coin in doc.get("coins", []):
        sources = coin.get("sources") or []
        for src in sources:
            if not isinstance(src, dict): continue
            if src.get("type") != "ucoin": continue
            url = src.get("url", "")
            m = re.search(r"tid=(\d+)", url)
            if not m: continue
            tid = m.group(1)
            u = ucoin.get(tid)
            if not u: continue

            # Pick PRIMARY value from list-form fields; fall back to scalar.
            def _primary(v):
                if v is None: return None
                if isinstance(v, (int, float)): return float(v)
                if isinstance(v, list) and v:
                    first = v[0]
                    return first.get("value") if isinstance(first, dict) else None
                return None
            our_w = _primary(coin.get("weight_g")) or _primary(coin.get("weight_rough_g"))
            our_f = _primary(coin.get("fineness"))
            our_d = _primary(coin.get("diameter_mm"))
            our_yf = coin.get("year_first") or 0
            our_yl = coin.get("year_last") or our_yf

            diffs = []
            new_fields = []
            covered = []  # diffs suppressed because measurement_alts records the alt value
            for cmp_fn, args, label, alt_field, tol in [
                (cmp_weight,    (our_w, u.get("weight_g")),       "weight",      "weight_rough_g", 0.05),
                (cmp_fineness,  (our_f, u.get("fineness")),       "fineness",    "fineness",       0.03),
                (cmp_diameter,  (our_d, u.get("diameter_mm")),    "diameter_mm", "diameter_mm",    0.05),
                (cmp_year,      (our_yf, our_yl, u.get("year")),  "year_range",  None,             None),
            ]:
                res = cmp_fn(*args)
                if not res:
                    continue
                if res.startswith("new_data:"):
                    new_fields.append(res.replace("new_data: ", ""))
                    continue
                # Real diff. Check if measurement_alts already covers it.
                if alt_field is not None:
                    uc_v = (u.get("weight_g") if alt_field == "weight_rough_g"
                            else u.get(alt_field))
                    if alt_covers_field(coin, tid, alt_field, uc_v, tol):
                        covered.append(res)
                        continue
                diffs.append(res)

            row = {
                "coin_id": coin["id"],
                "tid": tid,
                "our_nominal": coin.get("nominal"),
                "our_year": f"{our_yf}-{our_yl}",
                "ucoin_denom": u.get("denom"),
                "ucoin_year": u.get("year"),
                "diffs": diffs,
                "new_fields": new_fields,
                "covered_by_alts": covered,
            }
            if not diffs and not new_fields and not covered:
                row["status"] = "PERFECT_MATCH"
            elif covered and not diffs and not new_fields:
                row["status"] = "ALT_RECORDED"  # «враховано альтернативні дані»
            elif new_fields and not diffs and not covered:
                row["status"] = "NEW_DATA_ONLY"
            elif covered and not diffs:
                # has new fields too — primarily ALT_RECORDED with extra
                row["status"] = "ALT_RECORDED"
            elif diffs and not new_fields:
                row["status"] = "PARTIAL_MISMATCH"
            else:
                row["status"] = "MIXED"
            rows.append(row)

    # Aggregate
    status_counts = Counter(r["status"] for r in rows)
    diff_kinds = Counter()
    new_kinds = Counter()
    for r in rows:
        for d in r["diffs"]:
            diff_kinds[d.split(":")[0]] += 1
        for n in r["new_fields"]:
            new_kinds[n.split("=")[0]] += 1

    # Field-by-field breakdown — for each field, where do we stand?
    # match | differ | new (ucoin has, we lacked) | none (neither has)
    field_stats: dict[str, Counter] = {
        "weight": Counter(), "fineness": Counter(),
        "diameter_mm": Counter(), "year_range": Counter(),
    }
    for coin in doc.get("coins", []):
        sources = coin.get("sources") or []
        for src in sources:
            if not isinstance(src, dict): continue
            if src.get("type") != "ucoin": continue
            url = src.get("url", "")
            m = re.search(r"tid=(\d+)", url)
            if not m: continue
            tid = m.group(1)
            u = ucoin.get(tid)
            if not u: continue

            our = {
                "weight":      _primary(coin.get("weight_g")) or _primary(coin.get("weight_rough_g")),
                "fineness":    _primary(coin.get("fineness")),
                "diameter_mm": _primary(coin.get("diameter_mm")),
            }
            uc = {
                "weight":      u.get("weight_g"),
                "fineness":    u.get("fineness"),
                "diameter_mm": u.get("diameter_mm"),
            }

            for f in ["weight", "fineness", "diameter_mm"]:
                ov, uv = our[f], uc[f]
                if ov is None and uv is None:
                    field_stats[f]["both_missing"] += 1
                elif ov is not None and uv is None:
                    field_stats[f]["ucoin_missing"] += 1
                elif ov is None and uv is not None:
                    field_stats[f]["new_data"] += 1
                else:
                    if f == "diameter_mm":
                        ok = abs(ov - uv) <= 1.0
                    elif f == "weight":
                        ok = (ov == 0) or (abs(ov - uv) / ov <= 0.05)
                    else:  # fineness
                        ok = (ov == 0) or (abs(ov - uv) / ov <= 0.03)
                    field_stats[f]["match" if ok else "differ"] += 1

    print(f"=== ucoin DATA AUDIT — {len(rows)} (coin, ucoin_url) pairs ===\n")

    print("By status:")
    for s in ["PERFECT_MATCH", "ALT_RECORDED", "NEW_DATA_ONLY",
              "PARTIAL_MISMATCH", "MIXED"]:
        print(f"  {s:20s}  {status_counts.get(s, 0):3d}")
    print()

    print("Mismatch kinds (when our value differs from ucoin):")
    for k, n in diff_kinds.most_common():
        print(f"  {n:3d}  {k}")
    print()

    print("New-data kinds (we lack the value, ucoin provides):")
    for k, n in new_kinds.most_common():
        print(f"  {n:3d}  {k}")
    print()

    print("=== Field-by-field breakdown (per (coin, ucoin_url) pair) ===")
    print(f"  {'field':<13s}  {'match':>6s}  {'differ':>6s}  {'new':>6s}  {'uc_missing':>10s}  {'both_missing':>12s}")
    for f in ["weight", "fineness", "diameter_mm"]:
        s = field_stats[f]
        print(f"  {f:<13s}  {s['match']:>6d}  {s['differ']:>6d}  {s['new_data']:>6d}  {s['ucoin_missing']:>10d}  {s['both_missing']:>12d}")
    print()

    # Sample mismatches
    print("=== Sample mismatches (first 20) ===")
    bad = [r for r in rows if r["status"] in ("PARTIAL_MISMATCH", "MIXED")]
    for r in bad[:20]:
        print(f"\n  {r['coin_id']}  ({r['our_nominal']})")
        for d in r["diffs"]:
            print(f"     ↳ {d}")
        for n in r["new_fields"]:
            print(f"     + new_data: {n}")

    # Sample new-data only
    print("\n=== Sample NEW_DATA_ONLY (first 15) ===")
    for r in [r for r in rows if r["status"] == "NEW_DATA_ONLY"][:15]:
        print(f"  {r['coin_id']}  ({r['our_nominal']})")
        for n in r["new_fields"]:
            print(f"     + {n}")

    with open(OUT_JSON, "w") as fp:
        json.dump(rows, fp, indent=2, ensure_ascii=False)
    print(f"\nWrote {OUT_JSON}")


if __name__ == "__main__":
    main()
