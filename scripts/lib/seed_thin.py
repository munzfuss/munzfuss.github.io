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
    cross-source merger itself matches on. EVERY type-identity register the
    merger keys on must appear here: omitting one (e.g. `galster`) lets
    specimens of DIFFERENT types share a bucket and get collapsed together,
    which both loses distinct types and — once thinning salvages refs onto the
    reps — bloats the survivor's catalogue + drives transitive over-merges."""
    cat = coin.get("catalog") or {}
    return (
        str(cat.get("km")), str(cat.get("hede")), str(cat.get("sieg")),
        str(cat.get("schou")), str(cat.get("lange")), str(cat.get("galster")),
        coin.get("nominal"), coin.get("ruler"), coin.get("year_first"),
        str(coin.get("mint")), coin.get("metal"),
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


def _weight(coin: dict):
    """One numeric weight, or None when unrecorded. Tolerates §9a list-form."""
    v = coin.get("weight_rough_g")
    if v in (None, "", []):
        return None
    if isinstance(v, list):
        vals = [e.get("value") if isinstance(e, dict) else e for e in v]
        vals = [x for x in vals if isinstance(x, (int, float)) and x > 0]
        return min(vals) if vals else None
    return v if isinstance(v, (int, float)) and v > 0 else None


def _is_curated(coin: dict) -> bool:
    """A curator wrote something onto this specimen, so it is never dropped:
    the hold pins a FIELD on THIS record."""
    return bool(coin.get("_curation_holds") or coin.get("_source_errata"))


_THINNED_FROM_KEY = "_thinned_from"


def _record_thinned_from(reps: list, dropped: list) -> None:
    """Note on the surviving representative WHICH specimens it now stands for.

    Thinning sheds a specimen because it is redundant inside its own
    sub-variant bucket — but a curator may have NAMED that specimen in a
    merge_decision, and dropping it leaves the decision pointing at an id that
    no longer exists (`kmk-348041` / `kmk-351541`, cut by the 2026-09-12
    re-seed, found inert in 2026-09-21). The decision's real referent is the
    TYPE, not the individual cabinet record, so the representative that
    absorbed the specimen can answer for it — once something writes down which
    representative that was.

    Nothing else records it. `_salvage_unique` carries the dropped specimens'
    DATA onto the keepers but not their identity, and the mapping cannot be
    recovered afterwards: re-deriving a dead id's bucket key from the harvest
    cache normalises it with today's parser while its surviving bucket-mates
    were normalised by an older one, so the keys no longer meet. This is the
    only moment the link is known.

    Written onto `reps[0]` — the same target `_salvage_unique` uses, so a
    specimen's data and its identity land on one record. A dropped specimen
    that already carried `_thinned_from` hands its list over too, so a chain
    of thinning runs stays resolvable back to the original id.
    """
    if not reps or not dropped:
        return
    target = reps[0]
    acc = set(target.get(_THINNED_FROM_KEY) or [])
    for d in dropped:
        acc |= set(d.get(_THINNED_FROM_KEY) or [])   # keep the chain
        if d.get("id"):
            acc.add(d["id"])
    acc.discard(target.get("id"))
    if acc:
        target[_THINNED_FROM_KEY] = sorted(acc)


def thin_safe(coins: list, max_weightless: int = 3) -> tuple[list, dict]:
    """Seed-layer volume control that cannot change a weight envelope.

    §9a's own thinning — «keep min / middle / max» — belongs AFTER the merge,
    on a coin's accumulated `weight_rough_g` list, and lives in
    `scripts/maintenance/thin_final_weight_lists.py`. Doing it at the seed
    layer meant grouping by a key that is not the merger's, so keeping a
    bucket's true extremes sent them to other classes than the intermediate
    readings had come from and the coin the reader sees lost its envelope:
    6 of 8 affected ikmk entries came out narrower, five collapsed to a single
    reading.

    But the seed layer still has to control VOLUME, or the merger's pairwise
    pass runs for hours: kmk unthinned is 41 490 records against 14 152, and a
    full run went from ~20 minutes to 2 entities in 20 minutes. So this keeps
    only the removals that provably cannot move any weight:

      * every DISTINCT weight survives — same-weight duplicates within one
        sub-variant bucket collapse to one. The merger dedupes readings by
        (value, source) anyway, so for records that merge together this is a
        no-op; the bucket's min and max are untouched by construction.
      * weightless records beyond `max_weightless` per bucket. They carry no
        weight at all, so no envelope — bucket-level or merged — depends on
        them. They were 23 726 of the 25 310 removals on kmk, and 98.3% of
        them carried nothing the keepers did not already have.

    Curated records are never candidates. Dropped records still hand their
    distinguishing catalogue indices, fineness and diameter to the keepers via
    `_salvage_unique`.

    Residual caveat on the duplicate rule, recorded rather than hidden: if two
    same-weight twins end up in DIFFERENT merger classes, the class that lost
    its record loses that reading. It cannot change a bucket's extremes, and
    the affected volume is small (1 584 on kmk, 1 740 on ikmk), but it is not
    an absolute guarantee — unlike the weightless rule, which is.
    """
    buckets: dict[tuple, list] = {}
    for c in coins:
        buckets.setdefault(_subvariant_key(c), []).append(c)
    kept: list = []
    dropped_total = 0
    touched_buckets = 0
    for members in buckets.values():
        curated = [c for c in members if _is_curated(c)]
        plain = [c for c in members if not _is_curated(c)]
        keep: list = list(curated)
        dropped: list = []
        seen_w: set = set()
        weightless: list = []
        for c in plain:
            w = _weight(c)
            if w is None:
                weightless.append(c)
                continue
            k = round(w, 2)
            if k in seen_w:
                dropped.append(c)
            else:
                seen_w.add(k)
                keep.append(c)
        if len(weightless) > max_weightless:
            wl_sorted = sorted(weightless, key=lambda c: str(c.get("id")))
            keep.extend(wl_sorted[:max_weightless])
            dropped.extend(wl_sorted[max_weightless:])
        else:
            keep.extend(weightless)
        if dropped:
            _salvage_unique(keep, dropped)
            _record_thinned_from(keep, dropped)
            dropped_total += len(dropped)
            touched_buckets += 1
        kept.extend(keep)
    kept.sort(key=lambda c: str(c.get("id")))
    return kept, {"before": len(coins), "after": len(kept),
                  "sub_variants": len(buckets), "thinned_buckets": touched_buckets,
                  "dropped": dropped_total,
                  # the safe rule has no catalogue gate — every bucket is
                  # eligible because no DISTINCT weight can be removed. Key
                  # kept so `thin_seed_dir`'s reporting stays uniform.
                  "skipped_uncatalogued_buckets": 0}


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
            _record_thinned_from(reps, dropped)
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
        kept, stats = thin_safe(coins)
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
