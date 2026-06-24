"""Shared §9a intra-sub-variant thinning for over-sampled museum sources.

Museum cabinets (KMK Copenhagen, IKMK Berlin) over-sample common types —
dozens to hundreds of specimens of one sub-variant. After the §9a multi-
specimen merge their weights all collapse into one coin's ``weight_rough_g``
list; the intermediate readings between the lightest and heaviest add no
information about the standard's variance envelope. Thinning pre-merge keeps
the cross-source merger tractable and the rendered weight column to the true
min/max spread.

Rule (CLAUDE.md §9a). A sub-variant bucket of ≥5 specimens from one source is
thinned to ``min`` / position-``len//2`` middle / ``max`` (id-sorted
representatives, deterministic + idempotent).

Optional catalogued-only gate. With ``catalogued_only=True`` a bucket is only
eligible for thinning when it carries a real catalogue index (km / hede / lange
/ sieg / schou / fr / dav / galster) — for sources where an uncatalogued
descriptive grouping (nominal + ruler + year + mint + metal) is genuinely
uncertain and might group distinct coins. The default is ``False`` (thin all
≥5 buckets): for museum cabinets an uncatalogued record carries no
distinguishing signal beyond the sub-variant key + weight, so dropping the
redundant specimens loses nothing the data model can tell apart.

Two entry points:
  * ``thin_coins(coins, ...)``  — pure; thin an in-memory coin list.
  * ``thin_seed_dir(seed_dir, ...)`` — file-level; thin every ``*.yml`` under a
    ``data/v2/seed/<source>/`` directory in place. Builders call this as a
    post-write step so a single ``--write`` is self-filtering + idempotent.

Current users (both ``catalogued_only=False`` — thin all ≥5; curator direction
2026-06-24): IKMK via ``build_ikmk_seed.py`` (→ this module); KMK via its own
``thin_kmk_seed.py`` (same min/middle/max logic, predates this module). The
gate is kept as an opt-in for any future source with genuinely-uncertain
uncatalogued grouping.
"""
from __future__ import annotations

import glob
import re
import sys
from pathlib import Path

_LIB = Path(__file__).resolve().parent
sys.path.insert(0, str(_LIB.parent))
from lib.seed_merge import _make_yaml_loader  # noqa: E402

# Catalogue indices that count as a confident type identity for the gate.
CATALOG_KEYS = ("km", "hede", "lange", "sieg", "schou", "fr", "dav", "galster")


def _is_catalogued(coin: dict) -> bool:
    cat = coin.get("catalog") or {}
    return any(cat.get(k) for k in CATALOG_KEYS)


def _subvariant_key(coin: dict) -> tuple:
    """Type identity for sub-variant grouping — the catalogue/type signals the
    cross-source merger itself matches on."""
    cat = coin.get("catalog") or {}
    return (
        str(cat.get("km")), str(cat.get("hede")), str(cat.get("sieg")),
        str(cat.get("schou")), str(cat.get("lange")), coin.get("nominal"),
        coin.get("ruler"), coin.get("year_first"), str(coin.get("mint")),
        coin.get("metal"),
    )


# Catalogue keys that identify a SPECIMEN (auction lot, museum part), not a
# TYPE — these are intentionally NOT salvaged from dropped specimens (they're
# the redundant per-specimen provenance the thinning is meant to shed).
_PER_SPECIMEN_KEYS = ("bruun_lot_no", "bruun_collection_id", "bruun_part",
                      "bruun_page")


def _norm(x) -> str:
    return re.sub(r"\s+", "", str(x)).lower()


def _coin_catpairs(coin: dict):
    """Yield (key, value) TYPE catalogue refs on a coin — every km/hede/…/
    `others` sub-catalogue entry, flattening dict/list forms. Per-specimen
    locators and *_volume/*_verified companions are excluded."""
    cat = coin.get("catalog") or {}
    out = []
    for k, v in cat.items():
        if k.endswith("_volume") or k.endswith("_verified") or k in _PER_SPECIMEN_KEYS:
            continue
        if isinstance(v, dict):
            vals = [x for vv in v.values() for x in (vv if isinstance(vv, list) else [vv])]
        elif isinstance(v, list):
            vals = v
        else:
            vals = [v] if v not in (None, "") else []
        for x in vals:
            if x not in (None, ""):
                out.append((k, x))
    return out


def _append_catalog_ref(coin: dict, key: str, value) -> None:
    cat = coin.setdefault("catalog", {})
    if not isinstance(cat, dict):
        return
    cur = cat.get(key)
    if cur is None:
        cat[key] = value
    elif isinstance(cur, dict):
        return                       # cross-volume dict-form — leave untouched
    elif isinstance(cur, list):
        if all(_norm(value) != _norm(e) for e in cur):
            cur.append(value)
    elif _norm(cur) != _norm(value):
        cat[key] = [cur, value]


def _measure_values(coin: dict, field: str) -> set:
    v = coin.get(field)
    if v is None:
        return set()
    seq = v if isinstance(v, list) else [v]
    out = set()
    for e in seq:
        val = e.get("value") if isinstance(e, dict) else e
        if isinstance(val, (int, float)):
            out.add(round(float(val), 4))
    return out


def _salvage_unique(reps: list, dropped: list) -> None:
    """Carry the dropped specimens' DISTINGUISHING data onto the kept reps so
    the §9a thinning sheds only redundant readings, never unique information:

      * every distinct catalogue index — incl. the `others` sub-catalogue
        (dorfmann# / schrötter# / olding# / aagaard#) that is NOT in the
        bucket key — is unioned onto reps[0];
      * fineness / diameter_mm are preserved at the type level: the kept reps
        already carry the type's reading(s); only when the reps lack the field
        entirely is a dropped specimen's value salvaged (so the type never
        loses a measurement it only had on a thinned specimen).

    The dropped specimens' weight readings and per-specimen source URLs are
    deliberately NOT carried — that redundancy is exactly what thinning sheds.
    """
    target = reps[0]
    have_cat = {(k, _norm(x)) for r in reps for (k, x) in _coin_catpairs(r)}
    for d in dropped:
        for (k, x) in _coin_catpairs(d):
            if (k, _norm(x)) not in have_cat:
                have_cat.add((k, _norm(x)))
                _append_catalog_ref(target, k, x)
    for field in ("fineness", "diameter_mm"):
        if any(_measure_values(r, field) for r in reps):
            continue                 # reps already represent this measurement
        for d in dropped:
            if _measure_values(d, field):
                target[field] = d[field]   # type's only reading — preserve it
                break


def thin_coins(coins: list, min_bucket: int = 5,
               catalogued_only: bool = True) -> tuple[list, dict]:
    """Return (kept_coins, stats). Thin each ≥``min_bucket`` sub-variant bucket
    to min/middle/max (id-sorted). With ``catalogued_only`` (default), only
    buckets carrying a real catalogue index are eligible; uncatalogued buckets
    are left whole. Stable + idempotent (re-running keeps every bucket ≤3)."""
    buckets: dict[tuple, list] = {}
    for c in coins:
        buckets.setdefault(_subvariant_key(c), []).append(c)
    kept: list = []
    thinned_buckets = 0
    skipped_uncatalogued = 0
    for members in buckets.values():
        eligible = len(members) >= min_bucket
        if eligible and catalogued_only and not any(_is_catalogued(m) for m in members):
            eligible = False
            if len(members) >= min_bucket:
                skipped_uncatalogued += 1
        if eligible:
            ms = sorted(members, key=lambda c: str(c.get("id")))
            idx = sorted({0, len(ms) // 2, len(ms) - 1})
            reps = [ms[i] for i in idx]
            dropped = [ms[i] for i in range(len(ms)) if i not in idx]
            _salvage_unique(reps, dropped)
            kept.extend(reps)
            thinned_buckets += 1
        else:
            kept.extend(members)
    kept.sort(key=lambda c: str(c.get("id")))
    return kept, {
        "before": len(coins), "after": len(kept),
        "sub_variants": len(buckets), "thinned_buckets": thinned_buckets,
        "skipped_uncatalogued_buckets": skipped_uncatalogued,
    }


def thin_seed_dir(seed_dir: Path, min_bucket: int = 5,
                  catalogued_only: bool = True, dry_run: bool = False) -> int:
    """Thin every ``*.yml`` under ``seed_dir`` in place. Returns 0."""
    yaml = _make_yaml_loader()
    total_before = total_after = 0
    for f in sorted(glob.glob(str(Path(seed_dir) / "*.yml"))):
        doc = yaml.load(Path(f).read_text())
        coins = doc.get("coins") or []
        if not coins:
            continue
        kept, stats = thin_coins(coins, min_bucket=min_bucket,
                                 catalogued_only=catalogued_only)
        total_before += stats["before"]
        total_after += stats["after"]
        print(f"  {Path(f).name}: {stats['before']} → {stats['after']}  "
              f"({stats['thinned_buckets']} buckets thinned, "
              f"{stats['skipped_uncatalogued_buckets']} uncatalogued ≥{min_bucket} "
              f"left whole, {stats['sub_variants']} sub-variants)")
        if not dry_run and stats["after"] != stats["before"]:
            doc["coins"] = kept
            with open(f, "w") as fh:
                yaml.dump(doc, fh)
    print(f"\nTOTAL: {total_before} → {total_after} "
          f"({total_before - total_after} specimens dropped)")
    return 0
