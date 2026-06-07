#!/usr/bin/env python3
"""Audit Hede parser → seed data-loss: which danskmoent.dk Hede cache pages
are NOT represented in `data/v2/seed/hede/*.yml`, and WHY.

WHY THIS EXISTS. parse_hede.py turns `scripts/cache/hede/<id>.htm` pages into
`<id>.json` sidecars; build_hede_denmark_seed.py filters those into the seed.
Some pages drop out — sub-variant lines the parser missed, field-swaps where the
nominal landed in the mint slot, pages with no single spec block, out-of-scope
or exonumia. This audit re-derives the CURRENT loss categories so the count is
never stale (the hand-written «76/53/22/16» breakdown in handoff drifted as
parser fixes shipped — c4h163/c4h164 were «absent» in that note but are seeded
now). Run it before any sub-variant-loss work to know the real, current state.

CATEGORIES (per page absent from seed):
  - sub_letter_loss  page IS seeded but HTML sub-letters (163A/B/C) the parser
                     didn't capture in catalog_refs.Hede → partial loss.
  - field_swap       nominal=None + mint looks like a denomination («1 speciedaler»)
                     — the parser's «Ruler, NOMINAL» line (comma right after the
                     ruler, no mint) put the nominal into the mint slot. The seed
                     builder then skips it (skipped_no_mint). Parser bug.
  - oos_post_1914    year_first > 1914 — correctly absent (project upper bound).
  - exonumia         jeton / medaille / Rigsbanktegn — correctly absent (§9.2).
  - in_scope_absent  has a plausible nominal+mint but still not seeded — usually
                     no single spec block, multi-coin page, or undated. Needs
                     per-case review.

Usage:
  .venv/bin/python scripts/maintenance/audit_hede_seed_loss.py          # report
  .venv/bin/python scripts/maintenance/audit_hede_seed_loss.py --json   # machine
  .venv/bin/python scripts/maintenance/audit_hede_seed_loss.py --category field_swap
"""
import argparse
import glob
import json
import os
import re
import sys

import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
L = getattr(yaml, "CSafeLoader", yaml.SafeLoader)

CACHE = os.path.join(ROOT, "scripts", "cache", "hede")
SEED_GLOB = os.path.join(ROOT, "data", "v2", "seed", "hede", "*.yml")

_CID_RE = re.compile(r"/([cf]\d+h\d+[a-z]*)\.json$")
_DENOM = re.compile(
    r"(speciedaler|rigsdaler|rigsbankdaler|skilling|mark|krone|kroner|øre|"
    r"daler|dukat|piaster|hvid|søsling|penning|frederik d|christian d|"
    r"guldmønt|solidi|blaffert|breddaler)",
    re.I,
)
_EXONUMIA = re.compile(r"jeton|medaille|medalje|rigsbanktegn|tegn for", re.I)
YEAR_TO = 1914  # project scope upper bound


def _seed_ids() -> set[str]:
    ids: set[str] = set()
    for f in glob.glob(SEED_GLOB):
        d = yaml.load(open(f), L)
        coins = d.get("coins", d) if isinstance(d, dict) else d
        for c in coins or []:
            m = re.search(r"([cf]\d+h\d+[a-z]*)$", c.get("id", ""))
            if m:
                ids.add(m.group(1))
    return ids


def _year_first(d: dict):
    ys = [x.get("year") for x in (d.get("years") or []) if isinstance(x, dict) and x.get("year")]
    return min(ys) if ys else None


def audit() -> dict:
    seed = _seed_ids()
    pages = []
    for f in sorted(glob.glob(os.path.join(CACHE, "*.json"))):
        m = _CID_RE.search(f)
        if not m:
            continue
        htm = f.replace(".json", ".htm")
        if not os.path.exists(htm):
            continue
        pages.append((f, m.group(1), htm))

    out = {"sub_letter_loss": [], "field_swap": [], "oos_post_1914": [],
           "exonumia": [], "in_scope_absent": [], "ok": 0, "total": len(pages)}

    for f, cid, htm in pages:
        d = json.load(open(f))
        raw = re.sub(r"<[^>]+>", " ", open(htm, encoding="utf-8", errors="replace").read())
        base = re.search(r"h(\d+)", cid).group(1)
        in_seed = any(s == cid or s.startswith(cid) for s in seed)
        nom = d.get("nominal")
        mint = d.get("mint")
        yf = _year_first(d)

        if in_seed:
            # partial-loss check: HTML sub-letters not in captured Hede refs
            subs = sorted(set(re.findall(rf"\b{base}([A-Za-z]):", raw)))
            captured = {str(x) for x in (d.get("catalog_refs", {}).get("Hede") or [])}
            cap_letters = {re.search(r"[A-Za-z]$", x).group(0).upper()
                           for x in captured if re.search(r"[A-Za-z]$", x)}
            missing = [s for s in subs if s.upper() not in cap_letters]
            if missing:
                out["sub_letter_loss"].append(
                    {"id": cid, "html_subletters": subs,
                     "captured": sorted(cap_letters), "missing": missing})
            else:
                out["ok"] += 1
            continue

        # absent from seed — categorise
        if yf and yf > YEAR_TO:
            out["oos_post_1914"].append({"id": cid, "year_first": yf})
        elif _EXONUMIA.search((str(nom) or "") + " " + d.get("raw_text", "")):
            out["exonumia"].append({"id": cid, "nominal": nom})
        elif (not nom or nom == "None") and mint and _DENOM.search(str(mint)):
            out["field_swap"].append({"id": cid, "mint_holds_nominal": mint, "year_first": yf})
        else:
            out["in_scope_absent"].append(
                {"id": cid, "nominal": nom, "mint": mint, "year_first": yf})
    return out


def main():
    ap = argparse.ArgumentParser(description="Audit Hede parser→seed data-loss.")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    ap.add_argument("--category", help="print only this category's ids")
    args = ap.parse_args()

    res = audit()
    if args.json:
        json.dump(res, sys.stdout, ensure_ascii=False, indent=1)
        print()
        return
    if args.category:
        for row in res.get(args.category, []):
            print(json.dumps(row, ensure_ascii=False))
        return

    print(f"Hede cache pages (with htm): {res['total']}")
    print(f"  OK (seeded, no detected loss):   {res['ok']}")
    print(f"  sub_letter_loss (partial):       {len(res['sub_letter_loss'])}")
    print(f"  field_swap (parser nominal→mint):{len(res['field_swap'])}")
    print(f"  in_scope_absent (needs review):  {len(res['in_scope_absent'])}")
    print(f"  oos_post_1914 (correct):         {len(res['oos_post_1914'])}")
    print(f"  exonumia (correct):              {len(res['exonumia'])}")
    for cat in ("sub_letter_loss", "field_swap"):
        if res[cat]:
            print(f"\n--- {cat} ---")
            for row in res[cat]:
                print("   " + json.dumps(row, ensure_ascii=False))


if __name__ == "__main__":
    main()
