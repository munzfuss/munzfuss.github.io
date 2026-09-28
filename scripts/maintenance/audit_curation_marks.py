"""Curation marks reach final, and final is a thinning fixed point.

Two invariants of the V2 final layer that have each been broken silently:

1. MARKS REACH FINAL. A curation mark — `erroneous` «(!)», `suspect` «(*)»,
   `template` «(§)» (`seed_merge._CURATION_MARK_KEYS`) — is written on a
   reading in the SEED of the source that published it, and must travel
   seed → seed_unified → final unchanged. Until 2026-09-28 the merger copied
   only erroneous/suspect, so every absorb stripped the Nobel (§) marks from
   final; nothing noticed, because the render simply lost a marker. This check
   finds every marked seed reading and asserts that the final coin the seed
   reaches carries the same (field, value, source) reading with the same mark.
   A seed that reaches no final coin (pending classification) is not a loss and
   is only counted.

2. THINNING FIXED POINT. `thin_final_weight_lists.thin_coin` must find nothing
   to drop in a committed final. absorb runs it before writing; any other
   writer of final (relink, dedup, a hand edit) that re-introduces an
   un-thinned envelope is caught here instead of as thousands of lines of
   unexplained churn on the next re-flow.

    audit_curation_marks.py                  # both checks, whole corpus
    audit_curation_marks.py --files a.yml …  # thinning check on these finals
                                             # (marks check always corpus-wide)

Exit 1 on any violation.
"""
from __future__ import annotations

import argparse
import copy
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from lib.seed_merge import _CURATION_MARK_KEYS  # noqa: E402
from maintenance.thin_final_weight_lists import thin_coin  # noqa: E402

V2 = ROOT / "data" / "v2"
FIELDS = ("weight_rough_g", "fineness", "diameter_mm")
_Loader = getattr(yaml, "CSafeLoader", yaml.SafeLoader)


def _load(path: Path) -> dict:
    return yaml.load(path.read_text(encoding="utf-8"), Loader=_Loader) or {}


def _key(v) -> float | None:
    return round(float(v), 6) if isinstance(v, (int, float)) else None


def _marked_readings(coin: dict):
    """(field, value, source, kind) for every marked reading of one coin."""
    for f in FIELDS:
        lst = coin.get(f)
        if not isinstance(lst, list):
            continue
        for e in lst:
            if not isinstance(e, dict):
                continue
            for k in _CURATION_MARK_KEYS:
                if e.get(k):
                    yield (f, _key(e.get("value")), e.get("source"), k)


def check_marks() -> list[str]:
    # Seeds: only files that mention a mark key at all (cheap text prefilter).
    needles = tuple(f"{k}:" for k in _CURATION_MARK_KEYS)
    marked: dict[str, set] = {}
    for p in sorted((V2 / "seed").glob("*/*.yml")):
        if not any(n in p.read_text(encoding="utf-8") for n in needles):
            continue
        for c in _load(p).get("coins") or []:
            rs = set(_marked_readings(c))
            if rs and c.get("id"):
                marked[c["id"]] = rs
    if not marked:
        return []

    # seed → unified (seed_unified[].composed_of holds SEED ids)
    seed_to_unified: dict[str, str] = {}
    for p in sorted((V2 / "seed_unified").glob("*.yml")):
        for c in _load(p).get("coins") or []:
            for m in c.get("composed_of") or []:
                if m in marked:
                    seed_to_unified[m] = c["id"]

    # final[].composed_of holds UNIFIED ids, and on older entries seed ids
    # directly — resolve both (the V2Index rule, lib/v2_index.py).
    wanted_u = set(seed_to_unified.values())
    final_for: dict[str, tuple[str, set]] = {}
    for p in sorted((V2 / "final").glob("*.yml")):
        for c in _load(p).get("coins") or []:
            refs = set(c.get("composed_of") or [])
            hits = [s for s, u in seed_to_unified.items() if u in refs]
            hits += [s for s in marked if s in refs]
            if hits:
                have = set(_marked_readings(c))
                for s in hits:
                    final_for[s] = (c.get("id"), have)

    errors, unplaced = [], 0
    for sid, rs in sorted(marked.items()):
        if sid not in final_for:
            unplaced += 1
            continue
        fid, have = final_for[sid]
        for r in sorted(rs, key=str):
            if r not in have:
                f, v, src, k = r
                errors.append(f"{sid} → {fid}: {f} {v} ({src}) lost its «{k}» mark")
    print(f"marks: {sum(len(r) for r in marked.values())} marked seed reading(s) "
          f"on {len(marked)} seed(s); {unplaced} seed(s) not in final (skipped)")
    return errors


def check_thin(paths: list[Path]) -> list[str]:
    errors = []
    for p in paths:
        for c in _load(p).get("coins") or []:
            if not isinstance(c, dict):
                continue
            n = thin_coin(copy.deepcopy(c))
            if n:
                errors.append(f"{p.name}: {c.get('id')} — {n} reading(s) the "
                              f"§9a thinner would still drop")
    print(f"thin: {len(paths)} final file(s) checked")
    return errors


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--files", nargs="*", help="final yamls for the thinning check "
                    "(default: all of data/v2/final)")
    args = ap.parse_args()
    paths = ([Path(f) for f in args.files] if args.files
             else sorted((V2 / "final").glob("*.yml")))
    errors = check_marks() + check_thin(paths)
    for e in errors:
        print(f"  ✗ {e}")
    if errors:
        print("\nFix: marks belong on the SEED reading (see the reading-marker "
              "skill); an un-thinned final means absorb was bypassed — re-run "
              "absorb_seeds_into_final_v2 --apply for that entity.")
        return 1
    print("  ✓ every seed curation mark reaches final; final is thinned")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
