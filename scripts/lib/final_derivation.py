"""What a final would be if it were built from its members alone.

Absorb enriches a final with `members = [final] + classes`
(`absorb_seeds_into_final_v2.process_entity`): the final is its own first
member, so whatever it once held is re-unioned on every run and a seed that
leaves a class leaves its values behind. This module runs the SAME enrichment
twice — once as absorb does, once with the final replaced by a skeleton that
carries only what the curator decides (identity, fuss / phase / kind,
`_curation_holds` and the held values) — and compares the two field by field.

    A = enrich(final, [final] + classes)      what absorb writes today
    B = enrich(skel,  [skel]  + classes)      what the members + decisions give

    O = A − B    exists only because the final carried it   (candidates)
    G = B − A    a member value the self-union suppresses   (must be empty)

Plan: docs/plans/rebuild_final_from_members.md, stage 1. Read-only.
"""
from __future__ import annotations

import copy
import json

# Keys of a final that are curator decisions or identity, not member data.
SKELETON_KEYS = frozenset({
    "id", "label", "origin", "composed_of", "legacy_id", "class_id",
    "fuss", "phase", "kind", "_curation_holds",
})

# Readings: one item per (value, source) attestation.
READING_FIELDS = frozenset({"weight_rough_g", "fineness", "diameter_mm"})


def holds_of(fc: dict) -> set[str]:
    h = fc.get("_curation_holds")
    return set(h.keys() if isinstance(h, dict) else (h or []))


def skeleton(fc: dict) -> dict:
    """The final as the curator decided it: identity, classification, holds
    and each held field's value (with its `_verified` companion)."""
    sk = {k: copy.deepcopy(v) for k, v in fc.items() if k in SKELETON_KEYS}
    for f in holds_of(fc):
        for k in (f, f"{f}_verified"):
            if k in fc:
                sk[k] = copy.deepcopy(fc[k])
    return sk


def _j(v) -> str:
    return json.dumps(v, sort_keys=True, ensure_ascii=False, default=str)


def items(field: str, v) -> set:
    """A field's value as a set of comparable items.

    Lists compare per element (sources by (url, ref), readings by
    (value, source)); catalogue per (register, value); year_ranges per year;
    anything else is one item (its canonical JSON)."""
    if v is None or v == [] or v == {} or v == "":
        return set()
    if field == "sources" and isinstance(v, list):
        return {(str(s.get("url") or ""), str(s.get("ref") or ""))
                if isinstance(s, dict) else ("", _j(s)) for s in v}
    if field in READING_FIELDS:
        vs = v if isinstance(v, list) else [v]
        out = set()
        for x in vs:
            if isinstance(x, dict):
                try:
                    val = round(float(x.get("value")), 5)
                except (TypeError, ValueError):
                    val = _j(x.get("value"))
                out.add((val, str(x.get("source") or "")))
            else:
                out.add((_j(x), ""))
        return out
    if field == "catalog" and isinstance(v, dict):
        out = set()
        for reg, rv in v.items():
            if isinstance(rv, dict):
                for vol, x in rv.items():
                    for y in (x if isinstance(x, list) else [x]):
                        out.add((reg, f"{vol}:{y}"))
            else:
                for y in (rv if isinstance(rv, list) else [rv]):
                    out.add((reg, _j(y) if isinstance(y, dict) else str(y)))
        return out
    if field == "year_ranges" and isinstance(v, list):
        out = set()
        for r in v:
            if isinstance(r, (list, tuple)) and len(r) == 2:
                a, b = r
                if isinstance(a, int) and isinstance(b, int) and 0 <= b - a < 1000:
                    out.update(range(a, b + 1))
                    continue
            out.add(_j(r))
        return out
    if isinstance(v, list):
        return {_j(x) for x in v}
    return {_j(v)}


def diff(a: dict, b: dict) -> dict[str, tuple[set, set]]:
    """{field: (O, G)} for every field where A and B differ."""
    out = {}
    for f in set(a) | set(b):
        ia, ib = items(f, a.get(f)), items(f, b.get(f))
        if ia != ib:
            out[f] = (ia - ib, ib - ia)
    return out


def _pair_key(field: str, item):
    """What two items must share to be one value under two labels: the url of
    a source, the value of a reading."""
    if field == "sources" or field in READING_FIELDS:
        return item[0]
    return None


def classify(field: str, o: set, g: set) -> dict[str, list]:
    """Sort one field's (O, G) into

        own       only the final supplies it
        relabel   (old, new): same url / same reading value, the final keeps
                  an older label of what a member now carries under a new one
        hidden    a member value the self-run does not show
        diverged  (final's, members') for a single-valued field
    """
    out = {"own": [], "relabel": [], "hidden": [], "diverged": []}
    if field not in ("catalog", "year_ranges") and len(o) <= 1 and len(g) <= 1 \
            and o and g and _pair_key(field, next(iter(o))) is None:
        out["diverged"].append((next(iter(o)), next(iter(g))))
        return out
    by_key: dict = {}
    for x in g:
        k = _pair_key(field, x)
        if k is not None and k != "":
            by_key.setdefault(k, []).append(x)
    used = set()
    for x in sorted(o, key=str):
        k = _pair_key(field, x)
        cand = [y for y in by_key.get(k, []) if y not in used] if k not in (None, "") else []
        if cand:
            used.add(cand[0])
            out["relabel"].append((x, cand[0]))
        else:
            out["own"].append(x)
    out["hidden"] = sorted((y for y in g if y not in used), key=str)
    return out


def _post(ab, e: dict) -> dict:
    """The per-entry passes absorb runs after enrichment and before writing
    (fraction inference, catalogue fold, KMM over-collection, §9a thinning),
    in absorb's order — applied to both sides alike."""
    if "fraction" not in holds_of(e):
        cand = ab.infer_fraction(e, ab._get_fuss_fractions_cache())
        if cand and not e.get("fraction"):
            e["fraction"] = cand
    if isinstance(e.get("catalog"), dict) and "catalog" not in holds_of(e):
        ab._fold_catalog_indices(e["catalog"])
    ab._suppress_weightless_museum_overcollection(e)
    if ab.THIN_ENABLED:
        ab._thin_weights(e)
    return e


def derive_pair(ab, fc: dict, classes: list[dict], entity_id: str):
    """(A, B) for one final. `ab` is the absorb module (its `_LIVE_UNIFIED`
    must already hold the entity's classes, as `process_entity` sets it)."""
    a, _ = ab._enrich_final_entry(copy.deepcopy(fc),
                                  [copy.deepcopy(fc)] + copy.deepcopy(classes),
                                  entity_id)
    sk = skeleton(fc)
    b, _ = ab._enrich_final_entry(copy.deepcopy(sk),
                                  [copy.deepcopy(sk)] + copy.deepcopy(classes),
                                  entity_id)
    return _post(ab, a), _post(ab, b)
