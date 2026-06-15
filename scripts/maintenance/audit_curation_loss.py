#!/usr/bin/env python3
"""Curation-loss field-diff audit — the pre-apply gate (CLAUDE.md §4 / handoff
«curation-loss field-diff audit»).

The absorb step (`absorb_seeds_into_final_v2.process_entity`) RE-DERIVES the
non-immutable fields of every final entry from its composed_of members. A
hand-curated value on a final that is NOT frozen via `_curation_holds` is
therefore silently overwritten on the next `absorb --apply`. The classic case:
`unified-dk-bruun-3839` year_label «1497» → «1481-1513» (a member's loose
reign-window pollutes the curated discrete year).

This tool is PURELY ANALYTICAL — it calls `process_entity` (which only computes,
never writes) and diffs the would-be-written final against the current final on
the loss-risk fields, skipping any field protected by `_curation_holds`. Output
is the EXACT set of fields the next apply would change, classified:

  LOSS-WIDEN   year span widened (discrete/tight → looser reign-window span)
  CATALOG-DROP a cross-source catalog ref present now, gone after
  MEASURE-DROP a weight/fineness/diameter reading present now, gone after
  MINT         scalar mint replaced (Royal Danish→Kopenhagen tagged INTENDED)
  METAL        scalar metal replaced (verified-wins — usually intended)
  YEAR-ADD     discrete year(s) ADDED within the same span (enrichment, no loss)

Field classification (from reading absorb `_enrich_final_entry`):
  IMMUTABLE (never touched): fuss phase kind fraction nominal ruler mintmaster
                             issuing_entity
  GAP-FILL  (foundation wins): note verification_note inscription_* weight_label
  UNION     (additive):        sources composed_of
  RE-DERIVED (loss risk):      year_* mint metal catalog(xsrc) fineness
                               weight_rough_g diameter_mm   ← audited here

Usage:
  audit_curation_loss.py                  # all entities with seed_unified
  audit_curation_loss.py --entity X       # one entity
  audit_curation_loss.py --losses-only    # hide YEAR-ADD / INTENDED rows
"""
from __future__ import annotations
import argparse
import sys
import warnings
from pathlib import Path

import yaml

warnings.filterwarnings("ignore")
_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
sys.path.insert(0, str(_HERE.parent))
import absorb_seeds_into_final_v2 as A  # noqa: E402

FINAL_DIR = _HERE.parent.parent / "data" / "v2" / "final"

XSRC_CAT = {"hede", "sieg", "schou", "galster", "galster_volume",
            "jensen_skjoldager", "schive", "skaare", "friedberg",
            "davenport", "lange", "fr", "dav", "nmd"}


def _holds(e: dict) -> set:
    h = e.get("_curation_holds")
    return set(h.keys() if isinstance(h, dict) else (h or []))


def _catset(e: dict, k: str) -> set:
    v = (e.get("catalog") or {}).get(k)
    if v is None:
        return set()
    return {str(x).strip() for x in (v if isinstance(v, list) else [v])}


def _measureset(e: dict, f: str) -> set:
    v = e.get(f)
    if v is None:
        return set()
    out = set()
    for x in (v if isinstance(v, list) else [v]):
        val = x.get("value") if isinstance(x, dict) else x
        if val is None:
            continue
        try:
            out.add(round(float(val), 3))
        except (TypeError, ValueError):
            out.add(val)
    return out


def _year_ints(e: dict) -> set:
    yr = e.get("year_ranges")
    if yr:
        out = set()
        for r in yr:
            try:
                out.update(range(int(r[0]), int(r[1]) + 1))
            except (TypeError, ValueError, IndexError):
                pass
        return out
    yf, yl = e.get("year_first"), e.get("year_last")
    if yf is not None and yl is not None:
        try:
            return set(range(int(yf), int(yl) + 1))
        except (TypeError, ValueError):
            return set()
    return set()


def audit_entity(entity_id: str) -> dict:
    cur_doc = yaml.safe_load((FINAL_DIR / f"{entity_id}.yml").read_text("utf-8")) or {}
    cur = {c["id"]: c for c in (cur_doc.get("coins") or []) if c.get("id")}
    res = A.process_entity(entity_id)
    comp = {c["id"]: c for c in res["enriched_final_entries"] if c.get("id")}

    rows = {"LOSS-WIDEN": [], "CATALOG-DROP": [], "MEASURE-DROP": [],
            "MINT": [], "METAL": [], "YEAR-ADD": []}
    both = [i for i in cur if i in comp]
    for i in both:
        a, b = cur[i], comp[i]
        H = _holds(a)

        # YEAR — distinguish widening (loss) from in-span addition (enrichment)
        if not ({"year_ranges", "year_first", "year_label"} & H):
            af, al = a.get("year_first"), a.get("year_last")
            bf, bl = b.get("year_first"), b.get("year_last")
            if af is not None and bf is not None and (af, al) != (bf, bl):
                try:
                    widened = int(bf) < int(af) or int(bl) > int(al)
                except (TypeError, ValueError):
                    widened = True
                tag = "LOSS-WIDEN" if widened else "YEAR-ADD"
                rows[tag].append((i, a.get("year_label"), b.get("year_label")))
            elif (af, al) == (bf, bl) and a.get("year_label") != b.get("year_label"):
                rows["YEAR-ADD"].append((i, a.get("year_label"), b.get("year_label")))

        # CATALOG cross-source DROPS
        for k in XSRC_CAT:
            dropped = _catset(a, k) - _catset(b, k)
            if dropped:
                rows["CATALOG-DROP"].append((i, k, sorted(dropped), sorted(_catset(b, k))))

        # MEASUREMENT DROPS (non-held)
        for f in ("fineness", "weight_rough_g", "diameter_mm"):
            if f in H:
                continue
            d = _measureset(a, f) - _measureset(b, f)
            if d:
                rows["MEASURE-DROP"].append((i, f, sorted(map(str, d))))

        # MINT change — scalar OR list-form. The Royal-Danish→Kopenhagen
        # registry fold is the dominant case and is INTENDED (Numista's
        # mint id 260 «Royal Danish Mint» = Den Kongelige Mønt, Copenhagen,
        # verified against the live source 2026-06-15); flag anything else.
        ROYAL = {"Royal Danish", "Royal Danish Mint"}
        am, bm = a.get("mint"), b.get("mint")
        aset = set(am if isinstance(am, list) else ([am] if am else []))
        bset = set(bm if isinstance(bm, list) else ([bm] if bm else []))
        if aset != bset:
            removed = aset - bset
            added = bset - aset
            # INTENDED iff the only removal is a Royal-Danish alias AND it
            # folds into an already-present-or-added Kopenhagen (no other
            # mint gained/lost).
            intended = (removed <= ROYAL and not (added - {"Kopenhagen"})
                        and ("Kopenhagen" in bset))
            rows["MINT"].append((i, am, bm, "INTENDED" if intended else "REVIEW"))

        # METAL scalar replace
        if a.get("metal") and b.get("metal") and a.get("metal") != b.get("metal"):
            rows["METAL"].append((i, a.get("metal"), b.get("metal")))

    return {
        "entity": entity_id,
        "current": len(cur),
        "computed": len(comp),
        "in_both": len(both),
        "dropped_entries": sorted(set(cur) - set(comp)),
        "new_entries": sorted(set(comp) - set(cur)),
        "rows": rows,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--entity")
    ap.add_argument("--losses-only", action="store_true",
                    help="hide YEAR-ADD and INTENDED-mint rows")
    ap.add_argument("--show", type=int, default=12, help="rows per category to print")
    args = ap.parse_args()

    entities = ([args.entity] if args.entity
                else A._entities_with_seed_unified())

    grand = {k: 0 for k in ("LOSS-WIDEN", "CATALOG-DROP", "MEASURE-DROP",
                            "MINT", "METAL", "YEAR-ADD")}
    grand_intended_mint = 0
    for ent in entities:
        r = audit_entity(ent)
        rows = r["rows"]
        intended_mint = sum(1 for x in rows["MINT"] if x[-1] == "INTENDED")
        review_mint = len(rows["MINT"]) - intended_mint
        loss_total = (len(rows["LOSS-WIDEN"]) + len(rows["CATALOG-DROP"])
                      + len(rows["MEASURE-DROP"]) + review_mint + len(rows["METAL"]))
        for k in grand:
            grand[k] += len(rows[k])
        grand_intended_mint += intended_mint

        if loss_total == 0 and not any(rows.values()):
            continue
        print(f"\n{'='*78}\n{ent}: current={r['current']} computed={r['computed']} "
              f"in_both={r['in_both']} dropped={len(r['dropped_entries'])} "
              f"new={len(r['new_entries'])}")
        print(f"  REAL-LOSS={loss_total}  (widen={len(rows['LOSS-WIDEN'])} "
              f"cat-drop={len(rows['CATALOG-DROP'])} measure-drop={len(rows['MEASURE-DROP'])} "
              f"mint-review={review_mint} metal={len(rows['METAL'])})  "
              f"| benign: year-add={len(rows['YEAR-ADD'])} mint-intended={intended_mint}")
        for cat, items in rows.items():
            if not items:
                continue
            if args.losses_only and cat == "YEAR-ADD":
                continue
            shown = items
            if args.losses_only and cat == "MINT":
                shown = [x for x in items if x[-1] != "INTENDED"]
                if not shown:
                    continue
            print(f"  --- {cat}: {len(shown)} ---")
            for row in shown[:args.show]:
                print("     ", row)

    print(f"\n{'#'*78}\nGRAND TOTALS across {len(entities)} entit(y/ies):")
    print(f"  REAL LOSS: widen={grand['LOSS-WIDEN']} cat-drop={grand['CATALOG-DROP']} "
          f"measure-drop={grand['MEASURE-DROP']} metal={grand['METAL']}")
    print(f"  MINT: total={grand['MINT']} (intended Royal-Danish={grand_intended_mint}, "
          f"review={grand['MINT']-grand_intended_mint})")
    print(f"  BENIGN: year-add={grand['YEAR-ADD']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
