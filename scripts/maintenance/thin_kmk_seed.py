#!/usr/bin/env python3
"""thin_kmk_seed.py — §9a intra-sub-variant thinning for the KMK (Royal Coin
Cabinet Copenhagen) seed, applied PRE-merge.

The KMK harvest is the full cabinet (~42k specimens), with massive per-type
clusters (one Hede-17 Christian-IV 2-Skilling-1648 sub-variant has 302
specimens). ~14% of KMK object records carry a recorded weight
(`measurements: [{dimension: Vægt, unit: Gram, data: …}]`); the other ~86%
have an empty `measurements` list in the museum's own record (the source
never digitised a weight for that specimen — the builder is faithfully
extracting nothing, not dropping data). KMK measurements only ever carry
`Vægt` — never diameter or fineness.

Per CLAUDE.md §9a («sort by weight, keep [0, len//2, -1], drop the rest»):
for each sub-variant bucket (keyed by catalogue type identity) with ≥5 KMK
specimens, preserve the weight-variance envelope —
  * if any members carry a weight: sort THOSE by weight ascending and keep
    positions [0, len//2, -1] (min / middle / max). The weightless members
    of the same sub-variant add no measurement signal (same type, redundant
    inventory citations) and are dropped.
  * if NO member carries a weight: there is no envelope to preserve — keep
    [0, len//2, -1] of the id-sorted list (deterministic representatives).
Buckets < 5 are kept whole (protects genuinely-distinct single specimens,
mules, off-metal strikes — which KMK would have given a distinct catalogue
identity, breaking them out of the bucket anyway).

Thinning PRE-merge means the cross-source merger consolidates 3-per-type, not
302-per-type — tractable + the rendered weight column keeps the true min/max
spread rather than three arbitrary middling readings.

Idempotent: re-running on an already-thinned seed keeps every bucket ≤3, so
the envelope of a ≤3 list returns the same entries.

Run:
    .venv/bin/python scripts/maintenance/thin_kmk_seed.py [--dry-run]
"""
from __future__ import annotations

import argparse
import glob
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from lib.seed_merge import _make_yaml_loader  # noqa: E402
from lib.seed_thin import _salvage_unique  # noqa: E402

KMK_SEED_DIR = ROOT / "data" / "v2" / "seed" / "kmk"
KMK_CACHE_DIR = ROOT / "scripts" / "cache" / "kmk"


_WEIGHTLESS_KEEP = 3


def _is_curated(coin: dict) -> bool:
    """True when a curator has written something onto this specimen.

    Thinning must never discard such an entry: the hold pins a FIELD on THIS
    record, and dropping the record drops the decision with it. Two held
    norburg entries (kmk-81785 / -81790, `mint` + `issuing_entity`) were lost
    exactly this way; at HEAD they had survived only by where their ids fell
    in the sort, which is luck, not protection.
    """
    return bool(coin.get("_curation_holds") or coin.get("_source_errata"))


def _subvariant_key(coin: dict) -> tuple:
    """Type identity for sub-variant grouping — the catalogue/type signals the
    cross-source merger itself matches on. Specimens sharing this key are the
    same type; KMK over-sampled them."""
    cat = coin.get("catalog") or {}
    return (
        str(cat.get("km")), str(cat.get("hede")), str(cat.get("sieg")),
        str(cat.get("schou")), str(cat.get("lange")), str(cat.get("galster")),
        coin.get("nominal"), coin.get("ruler"), coin.get("year_first"),
        str(coin.get("mint")), coin.get("metal"),
    )


def _weight(coin: dict):
    """Single numeric weight for sort, or None when the specimen has no
    recorded weight. KMK seed weights are scalar floats (one specimen = one
    record); tolerate the §9a list-form just in case."""
    w = coin.get("weight_rough_g")
    if w in (None, [], ""):
        return None
    if isinstance(w, list):
        vals = [e.get("value") if isinstance(e, dict) else e for e in w]
        vals = [v for v in vals if isinstance(v, (int, float))]
        return min(vals) if vals else None
    return w if isinstance(w, (int, float)) else None


_PHOTO_MEMO: dict[str, bool] = {}


def _has_photo(coin: dict) -> bool:
    """True when this KMM record carries a still-photo asset.

    Same probe `absorb_seeds_into_final_v2._kmm_specimen_has_image` uses, and
    verified against the natmus page state the same way: a record with a still
    asset shows photo(s), one without shows «Genstanden er endnu ikke
    affotograferet» (2026-06-08 spot-check, KMM 290904 vs 123284). Memoised;
    maintenance-side only — the build never reads cache.
    """
    nid = str(coin.get("id") or "").split("-")[-1]
    if nid in _PHOTO_MEMO:
        return _PHOTO_MEMO[nid]
    has = False
    try:
        d = json.loads((KMK_CACHE_DIR / f"{nid}.json").read_text())
        rel = d.get("related") or {}
        assets = rel.get("assets") or [] if isinstance(rel, dict) else []
        has = any(isinstance(a, dict) and a.get("type") == "still" for a in assets)
    except (FileNotFoundError, ValueError, OSError):
        has = False
    _PHOTO_MEMO[nid] = has
    return has


def _keep_weightless(members: list, covered_years: set) -> list:
    """Pick which weightless specimens of an over-sampled bucket to keep.

    A weightless KMM stub is mostly pure redundancy — measured over the whole
    kmk corpus, 23 198 of 23 601 (98.3%) carried nothing the kept
    representatives did not already have, not one carried a different mint, and
    the 310 with an unseen catalogue index are salvaged onto the reps anyway.
    Keeping them all inflated the kmk seed from 14k to 37.7k entries and
    ballooned the source lists §9a exists to trim.

    Two things in that population are NOT redundant, so selection is by signal
    rather than by list position:

      * a photograph — 6.6% of the dropped stubs had one, and on 7.3% of
        sampled buckets the discarded members held every photo the type had;
      * a year no kept member covers — 93 records corpus-wide.

    Everything else is interchangeable, so the fill is by lowest id, which is
    also STABLE: the previous rule cut the bucket at [0, mid, -1] of an
    id-sort, so every re-seed reshuffled the survivors and `verify_reflow`
    reported the former representatives as vanished coins.
    """
    ranked = sorted(
        members,
        key=lambda c: (not _has_photo(c), str(c.get("id"))),
    )
    keep = ranked[:_WEIGHTLESS_KEEP]
    kept_years = {c.get("year_label") for c in keep} | covered_years
    for c in ranked[_WEIGHTLESS_KEEP:]:
        y = c.get("year_label")
        if y and y not in kept_years:
            keep.append(c)          # a year nobody else covers
            kept_years.add(y)
    return keep


def thin(dry_run: bool) -> int:
    yaml = _make_yaml_loader()
    total_before = total_after = 0
    for f in sorted(glob.glob(str(KMK_SEED_DIR / "*.yml"))):
        doc = yaml.load(Path(f).read_text())
        coins = doc.get("coins") or []
        if not coins:
            continue
        buckets: dict[tuple, list] = {}
        for c in coins:
            buckets.setdefault(_subvariant_key(c), []).append(c)
        kept: list = []
        thinned_buckets = 0
        for key, members in buckets.items():
            # §9a thins ONE redundancy: intermediate WEIGHT readings between a
            # bucket's min and max. So the threshold counts weight-BEARING
            # members, and a weightless specimen is never a candidate.
            #
            # Until 2026-09-12 the bucket was sorted by `id` and cut to
            # [0, mid, -1] with weight playing no part, so 86% of what thinning
            # dropped (23 615 of 27 476) were records with no weight at all:
            # each one a distinct KMM object, and shedding it removed a museum
            # citation without removing one gram of redundant weight. Which
            # weightless stub survived was decided by its id's sort position,
            # so every re-seed reshuffled the survivors and `verify_reflow`
            # read the previous representatives as 20 vanished coins.
            curated = [c for c in members if _is_curated(c)]
            plain = [c for c in members if not _is_curated(c)]
            weighted = [c for c in plain if _weight(c) is not None]
            weightless = [c for c in plain if _weight(c) is None]
            reps: list = []
            dropped: list = []
            if len(weighted) >= 5:
                by_weight = sorted(weighted, key=_weight)
                idx = sorted({0, len(by_weight) // 2, len(by_weight) - 1})
                reps = [by_weight[i] for i in idx]
                dropped = [by_weight[i] for i in range(len(by_weight))
                           if i not in idx]
            else:
                reps = list(weighted)
            if len(weightless) > _WEIGHTLESS_KEEP:
                wl_keep = _keep_weightless(
                    weightless,
                    {c.get("year_label") for c in reps + curated})
                dropped += [c for c in weightless if c not in wl_keep]
            else:
                wl_keep = list(weightless)
            if dropped:
                # §9a salvage: carry the dropped specimens' distinguishing
                # catalogue indices (+ fineness/diameter the reps lack) onto the
                # kept reps; shed only the redundant weight + per-specimen sources.
                _salvage_unique(reps + wl_keep + curated, dropped)
                thinned_buckets += 1
            kept.extend(curated)
            kept.extend(reps)
            kept.extend(wl_keep)
        # preserve original entry order (by id) for a stable diff
        kept.sort(key=lambda c: str(c.get("id")))
        total_before += len(coins)
        total_after += len(kept)
        name = Path(f).name
        print(f"  {name}: {len(coins)} → {len(kept)}  "
              f"({thinned_buckets} buckets thinned, {len(buckets)} sub-variants)")
        if not dry_run:
            doc["coins"] = kept
            with open(f, "w") as fh:
                yaml.dump(doc, fh)
    print(f"\nTOTAL: {total_before} → {total_after} "
          f"({total_before - total_after} specimens dropped)")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry-run", action="store_true",
                    help="report the reduction without writing")
    args = ap.parse_args()
    return thin(dry_run=args.dry_run)


if __name__ == "__main__":
    raise SystemExit(main())
