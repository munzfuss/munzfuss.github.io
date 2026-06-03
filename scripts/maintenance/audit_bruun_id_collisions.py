#!/usr/bin/env python3
"""§CS audit — cross-final bruun_collection_id collision triage.

THE PROBLEM. A V2 `final` foundation entry can carry a `bruun_collection_id`
in its OWN catalog (V1-bootstrap) that is NOT attested by any of its
`composed_of` members. Two very different things produce that shape:

  (A) MIS-CITE  — the id points at a DIFFERENT coin (a hand-typed V1 typo;
                  e.g. km-562 «1 Speciedaler» carrying bruun 7628, which the
                  cache says is the «2 Ducat» of 1748). The fix is to DROP the
                  stale id (the correct one already flows from the cache-backed
                  seed via composed_of, or is added separately).
  (B) SPLIT-CLUSTER — the id points at the SAME coin, which simply did not
                  merge into this foundation and stands as its own orphan
                  `unified-dk-bruun-<X>` entry (a coverage gap). The fix is to
                  MERGE the two entries — NOT to drop the id (dropping would
                  lose a correct citation, violating CLAUDE.md §9a).

A blanket "drop unattested bruun-id" guard cannot tell (A) from (B) and would
damage (B). This audit classifies each collision using the CACHE as the
authority for "what coin is bruun-X really?" — the discriminator is
**year_first + metal** (robust; nominal comparison is too noisy — Krone≡4 Mark,
Bruun «Region. Nominal» prefixes, d'or quote variants). Same year + same metal
⇒ same coin ⇒ SPLIT-CLUSTER (merge); otherwise ⇒ MIS-CITE (drop candidate).

Output: a triage report, and (with --write) a match_uncertainty YAML so the
candidates are surfaced, never silently lost (CLAUDE.md data-accumulation
principle). This audit NEVER edits coin data — it only classifies + surfaces.

Run:  .venv/bin/python scripts/maintenance/audit_bruun_id_collisions.py [--write] [--json]
"""
from __future__ import annotations

import argparse
import glob
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))
from lib.seed_merge import _make_yaml_loader  # noqa: E402
from lib.nominal_synonyms import normalise_nominal  # noqa: E402

_Y = _make_yaml_loader()

FINAL_GLOB = str(REPO / "data/v2/final/*.yml")
UNIFIED_GLOB = str(REPO / "data/v2/seed_unified/*.yml")
BRUUN_SEED_GLOB = str(REPO / "data/v2/seed/bruun/*.yml")
MATCH_UNCERTAINTY_DIR = REPO / "data/v2/match_uncertainty"


def _bruun_ids(coin) -> list[str]:
    bid = (coin.get("catalog") or {}).get("bruun_collection_id")
    if bid is None:
        return []
    return [str(v) for v in (bid if isinstance(bid, list) else [bid])]


def _load_all(glob_pat):
    for ff in glob.glob(glob_pat):
        doc = _Y.load(open(ff).read()) or {}
        for c in doc.get("coins") or []:
            yield ff.split("/")[-1], c


def build_indices():
    # seed_unified id -> set(bruun ids it carries)  (= what merge proved together)
    uni = {}
    for _, c in _load_all(UNIFIED_GLOB):
        ids = _bruun_ids(c)
        if ids:
            uni[c.get("id")] = set(ids)
    # cache identity: bruun-id -> (nominal, year_first, metal, ruler) from the seed
    cache = {}
    for _, c in _load_all(BRUUN_SEED_GLOB):
        bcat = c.get("catalog") or {}
        for x in _bruun_ids(c):
            cache[x] = {
                "nominal": c.get("nominal"),
                "year_first": c.get("year_first"),
                "metal": c.get("metal"),
                "ruler": c.get("ruler"),
                "km": bcat.get("km"),
                "hede": bcat.get("hede"),
            }
    return uni, cache


def find_collisions(uni):
    """Return (owners, suspects):
    owners[X]   = set of final-ids where X is composed-attested (legit owner)
    suspects[X] = list of (final_id, entity, coin) where X is own-catalog-only
    """
    owners = defaultdict(set)
    suspects = defaultdict(list)
    for ent, c in _load_all(FINAL_GLOB):
        ids = _bruun_ids(c)
        if not ids:
            continue
        attested = set()
        for m in (c.get("composed_of") or []):
            attested |= uni.get(m, set())
        for x in ids:
            if x in attested:
                owners[x].add(c.get("id"))
            else:
                suspects[x].append((c.get("id"), ent, c))
    return owners, suspects


_YEAR_TOL = 2


def _catvals(x):
    if x is None:
        return set()
    return {str(v).strip() for v in (x if isinstance(x, list) else [x]) if v is not None}


def _base_code(code):
    """Catalog base number: «401.2»→«401», «90C»→«90», «112A»→«112»."""
    m = re.match(r"\s*(\d+)", str(code))
    return m.group(1) if m else str(code).strip()


def _catalog_signal(coin, cache_rec):
    """How strongly the foundation's km/hede corroborate the cache bruun-id's.
    Returns ('exact'|'family'|'none', reason). Catalog is the project's
    strongest coin-identity signal — it OVERRIDES a metal-label discrepancy
    (a Bruun-seed metal mis-parse, or a gold proof sharing the same Hede)."""
    fcat = coin.get("catalog") or {}
    fkm, fhede = _catvals(fcat.get("km")), _catvals(fcat.get("hede"))
    xkm, xhede = _catvals(cache_rec.get("km")), _catvals(cache_rec.get("hede"))
    exact = (fkm & xkm) | (fhede & xhede)
    if exact:
        return "exact", "km/hede " + ",".join(sorted(exact))
    km_fam = {_base_code(v) for v in fkm} & {_base_code(v) for v in xkm}
    hede_fam = {_base_code(v) for v in fhede} & {_base_code(v) for v in xhede}
    fam = km_fam | hede_fam
    if fam:
        return "family", "base " + ",".join(sorted(fam))
    return "none", ""


def _metal_class(m):
    """Coarse metal class: silver+billon are compatible (billon = low-grade
    silver alloy, often a labelling judgement on the same coin); gold and base
    (copper/bronze) are hard-distinct."""
    if not m:
        return None
    m = str(m).lower()
    if "gold" in m:
        return "gold"
    if "silver" in m or "billon" in m:
        return "silver"
    if "copper" in m or "bronze" in m:
        return "base"
    return m


def _classify_pair(coin, cache_rec) -> tuple[str, str]:
    """Verdict from normalised nominal + metal-class + year-range overlap.
    Nominal is now reliable (see lib/nominal_synonyms preprocessing), so it is
    a primary signal again; year is checked as RANGE overlap (multi-year Hede
    types legitimately carry specimens across several years).
      'miscite' — metal-class hard-differs OR cache year falls well outside the
                  foundation's [year_first..year_last] => a DIFFERENT coin.
      'merge'   — nominal + metal + year-overlap all agree => same coin/type
                  (un-merged split-cluster).
      'review'  — metal+year compatible but nominal differs => ambiguous
                  (denom typo, OR an un-encoded accounting equivalence like
                  12 Skilling≡⅛ Speciedaler / Krone≡4 Mark) — needs human eyes.
    """
    # Catalog corroboration is the strongest signal — it OVERRIDES metal/year.
    sig, sigr = _catalog_signal(coin, cache_rec)
    if sig == "exact":
        return "merge", f"catalog {sigr} match ⇒ same coin (metal-label/specimen diff)"
    nom_b = normalise_nominal(coin.get("nominal"))
    nom_x = normalise_nominal(cache_rec.get("nominal"))
    nom_ok = bool(nom_b) and nom_b == nom_x
    mb, mx = _metal_class(coin.get("metal")), _metal_class(cache_rec.get("metal"))
    metal_hard = mb is not None and mx is not None and mb != mx
    yf, yl, yx = coin.get("year_first"), coin.get("year_last"), cache_rec.get("year_first")
    year_known = yf is not None and yx is not None
    year_overlap = None
    if year_known:
        lo = int(yf) - _YEAR_TOL
        hi = int(yl if yl is not None else yf) + _YEAR_TOL
        year_overlap = lo <= int(yx) <= hi
    if sig == "family":
        # same catalog family (sub-variant) — never an outright drop; if it also
        # matches nominal+metal+year it's a clean split-cluster, else review.
        if nom_ok and not metal_hard and year_overlap is not False:
            return "merge", f"catalog family {sigr} + nominal/metal/year agree"
        return "review", f"catalog family {sigr} but metal/nominal/year differ (sub-variant?)"
    # No catalog corroboration — fall back to metal/year/nominal discriminator.
    if metal_hard:
        return "miscite", f"no catalog match; metal {coin.get('metal')}≠{cache_rec.get('metal')} (nom '{nom_b}' vs '{nom_x}')"
    if year_known and not year_overlap:
        return "miscite", f"no catalog match; year {yx} outside [{yf}..{yl}]±{_YEAR_TOL} (nom '{nom_b}' vs '{nom_x}')"
    if nom_ok:
        return "merge", f"no catalog but nominal '{nom_b}' + metal {mb} + year {yx}∈[{yf}..{yl}] agree"
    return "review", f"no catalog; nominal '{nom_b}'≠'{nom_x}' but metal/year compatible (accounting-equiv? typo?)"


def classify(owners, suspects, cache):
    merges, miscites, reviews, unknown = [], [], [], []
    for x, sus in sorted(suspects.items()):
        real_owners = owners.get(x, set())
        for fid, ent, coin in sus:
            others = real_owners - {fid}
            if not others:
                continue  # not owned elsewhere -> not a cross-final collision
            rec = cache.get(x)
            row = {
                "bruun_id": x, "final_id": fid, "entity": ent,
                "nominal": coin.get("nominal"), "year_first": coin.get("year_first"),
                "metal": coin.get("metal"), "owned_by": sorted(others),
                "cache": rec,
            }
            if rec is None:
                row["verdict"] = "unknown (bruun-id not in cache)"
                unknown.append(row)
                continue
            verdict, reason = _classify_pair(coin, rec)
            row["reason"] = reason
            if verdict == "miscite":
                row["verdict"] = "MIS-CITE (drop candidate)"
                miscites.append(row)
            elif verdict == "merge":
                row["verdict"] = "MERGE (same coin / split-cluster)"
                merges.append(row)
            else:
                row["verdict"] = "REVIEW (year+metal match, nominal differs)"
                reviews.append(row)
    return merges, miscites, reviews, unknown


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--write", action="store_true",
                    help="write triage to data/v2/match_uncertainty/bruun_id_collisions.yml")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    uni, cache = build_indices()
    owners, suspects = find_collisions(uni)
    merges, miscites, reviews, unknown = classify(owners, suspects, cache)

    if args.json:
        print(json.dumps({"miscite": miscites, "merge": merges, "review": reviews,
                          "unknown": unknown},
                         ensure_ascii=False, indent=2, default=str))
        return 0

    def show(title, rows):
        print(f"\n=== {title} ({len(rows)}) ===")
        for r in rows:
            cr = r.get("cache") or {}
            print(f"  [{r['entity']}] {r['final_id']:<34} bruun {r['bruun_id']}")
            print(f"      this: {r['nominal']!r} {r['year_first']} {r['metal']}  |  "
                  f"cache bruun-{r['bruun_id']}: {cr.get('nominal')!r} {cr.get('year_first')} {cr.get('metal')}")
            print(f"      owned-by: {r['owned_by']}  -> {r['verdict']}"
                  + (f"  [{r.get('reason')}]" if r.get("reason") else ""))

    show("MIS-CITE — year OR metal differ ⇒ different coin (safe drop candidate)", miscites)
    show("REVIEW — year+metal match but nominal differs (denom typo? synonym gap?)", reviews)
    show("MERGE — same coin, un-merged split-cluster (do NOT drop; merge)", merges)
    if unknown:
        show("UNKNOWN — bruun-id absent from cache (manual check)", unknown)

    print(f"\nSUMMARY: {len(miscites)} mis-cite (drop), {len(reviews)} review, "
          f"{len(merges)} merge (split-cluster), {len(unknown)} unknown")

    if args.write:
        MATCH_UNCERTAINTY_DIR.mkdir(parents=True, exist_ok=True)
        out = MATCH_UNCERTAINTY_DIR / "bruun_id_collisions.yml"
        payload = {
            "audit": "cross-final bruun_collection_id collisions (§CS)",
            "discriminator": "year_first(±1) + metal + normalised nominal vs cache bruun-id identity",
            "mis_cites_drop": miscites,
            "reviews": reviews,
            "merges_splitcluster": merges,
            "unknown": unknown,
        }
        import yaml as _py
        out.write_text(_py.dump(payload, sort_keys=False, allow_unicode=True,
                                default_flow_style=False, width=120))
        print(f"\nwrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
