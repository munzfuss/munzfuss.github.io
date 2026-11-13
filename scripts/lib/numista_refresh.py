"""Stitch a fresh Numista API v3 response onto an existing parsed sidecar.

A refresh never overwrites the harvested raw file. The fresh response is
saved verbatim under ``scripts/cache/numista/refresh/<date>/<NID>.json``
and laid over ``parsed/<NID>.json`` field by field, with every
difference recorded, so that a value Numista removed or corrected is
visible instead of being absorbed by a blind union.

Policy, per canonical field:

* the fresh value is non-empty and differs  -> fresh wins   (``changed``)
* the fresh value is empty, the old is not   -> old kept     (``kept_old``)
* the fresh number is the old one rounded    -> fresh wins   (``rounded``)
* ... or the old one cut off (6.98 -> 6.9)   -> fresh wins   (``truncated``)
  — Numista replaced many weights with one-decimal figures in 2026
  (28.893 -> 28.9 on N#90574); the seed follows what the source
  publishes now (curator 2026-11-12), the older figure stays in the log
* two lists differ only in order             -> no change
  — e.g. ``year_list``, which the API never returns and which was
  backfilled from ``getIssues``
* ``references`` are compared register by register: ``added`` /
  ``changed`` / ``absent_in_response``, and the result is the UNION of
  old and fresh. The API omits some catalogues that the type page shows
  (Schive, Brekke, AAJT — N#121754, 100212, 110303) and on some types the
  whole block (N#71918, 476668), so absence from a response proves
  nothing; an old value the response lacks stays and is logged, and a
  genuine correction by Numista (N#148219: KM 606 -> 605) is left for
  review instead of being guessed.

The old sidecar's shape decides how much is applied. An API-shaped old
sidecar is like-for-like, so every field is laid over. A sidecar parsed
from a Chrome scrape or the pre-1541 HTML path formats several fields
differently (mint strings, lettering, title), so a field diff there
mostly measures the parser, not Numista: only ``references`` are applied
and the other diffs are logged as ``not_applied``.

Used by ``scripts/maintenance/refresh_numista_types.py`` (the fetch) and
``scripts/parse_numista.py`` (so a re-parse re-applies the newest
refresh instead of undoing it).
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from lib.paths import NUMISTA_CACHE

REFRESH_DIR = NUMISTA_CACHE / "refresh"

# Bookkeeping keys that are not data and are never compared.
_META = {"_source_shape", "_source_path", "_refresh"}


def _empty(v: Any) -> bool:
    return v is None or v == "" or v == [] or v == {}


def _as_set(v: Any) -> frozenset[str]:
    if _empty(v):
        return frozenset()
    if isinstance(v, (list, tuple)):
        return frozenset(str(x) for x in v)
    return frozenset(p.strip() for p in str(v).split("|") if p.strip())


def _decimals(x: float) -> int:
    t = repr(float(x))
    return 0 if t.endswith(".0") else len(t.split(".")[1])


def _is_rounding_of(old: Any, new: Any) -> bool:
    """True when ``new`` is ``old`` rounded to fewer decimals (28.893 -> 28.9,
    41.15 -> 41). Only labels the change in the log; the fresh value is
    taken either way."""
    if isinstance(old, bool) or isinstance(new, bool):
        return False
    if not isinstance(old, (int, float)) or not isinstance(new, (int, float)):
        return False
    d = _decimals(new)
    return d < _decimals(old) and round(float(old), d) == float(new)


def _is_truncation_of(old: Any, new: Any) -> bool:
    """True when ``new`` is ``old`` cut to fewer decimals without rounding
    (6.98 -> 6.9, 0.768 -> 0.7): Numista's 2026 one-decimal weights are
    often truncated. Labels the change; the fresh value is taken (curator
    2026-11-13, «Брати нові»)."""
    if isinstance(old, bool) or isinstance(new, bool):
        return False
    if not isinstance(old, (int, float)) or not isinstance(new, (int, float)):
        return False
    d = _decimals(new)
    if d >= _decimals(old):
        return False
    f = 10 ** d
    return int(float(old) * f + 1e-9) / f == float(new)


def _same(a: Any, b: Any) -> bool:
    """Equal, or equal lists in a different order."""
    if a == b:
        return True
    if isinstance(a, list) and isinstance(b, list):
        try:
            return sorted(map(str, a)) == sorted(map(str, b))
        except TypeError:
            return False
    return False


_ALIAS = {"friedberg": "fr", "davenport": "dav", "galster uu": "galster"}


def _norm_value(reg: str, v: str) -> str:
    """One comparable form of a catalogue value: decimal comma as dot, a
    trailing «(Denmark)»-style volume note dropped, a Davenport volume
    prefix dropped («EC I 8220» = «8220»)."""
    v = re.sub(r"\s*\([^)]*\)\s*$", "", v.strip())
    if any(c.isdigit() for c in v):
        v = re.sub(r"(?<=\d),(?=\d)", ".", v)
    if reg == "dav":
        v = v.split()[-1] if v.split() else v
    return v


def _norm_refs(refs: dict | None) -> dict[str, dict[str, str]]:
    """References in one comparable form — register -> {normalised value:
    value as given} — so that a parser difference is not reported as a
    Numista edit: register synonyms folded (friedberg = fr, davenport =
    dav), an ``others`` label «AAJT# 6» read as register ``aajt``, values
    normalised by ``_norm_value``."""
    out: dict[str, dict[str, str]] = {}

    def add(reg: str, vals) -> None:
        reg = _ALIAS.get(reg.lower(), reg.lower())
        for v in vals:
            out.setdefault(reg, {}).setdefault(_norm_value(reg, v), v)

    for reg, val in (refs or {}).items():
        if reg == "others":
            for label in (val if isinstance(val, list) else [val]):
                code, _, num = str(label).partition("#")
                if num.strip():
                    add(code.strip(), [num.strip()])
                else:
                    add("others", [str(label)])
        else:
            add(reg, sorted(_as_set(val)))
    return {k: v for k, v in out.items() if v}


def diff_references(old: dict | None, new: dict | None) -> dict[str, dict]:
    """Register-level diff of two canonical ``references`` dicts, compared
    in the normalised form of ``_norm_refs`` and reported with the values
    as each side gives them; «406.1|406.2» and ["406.2","406.1"] are equal."""
    a_all, b_all = _norm_refs(old), _norm_refs(new)
    out: dict[str, dict] = {}
    for reg in sorted(set(a_all) | set(b_all)):
        a, b = a_all.get(reg, {}), b_all.get(reg, {})
        if set(a) == set(b):
            continue
        if not a:
            out[reg] = {"status": "added", "new": sorted(b.values())}
        elif not b:
            out[reg] = {"status": "absent_in_response", "old": sorted(a.values())}
        else:
            out[reg] = {"status": "changed", "old": sorted(a.values()),
                        "new": sorted(b.values()),
                        "absent_in_response": sorted(a[k] for k in set(a) - set(b)),
                        "gained": sorted(b[k] for k in set(b) - set(a))}
    return out


# Values an API response lacks are normally kept (absence proves nothing,
# see ``union_references``). These are the exceptions: values checked on the
# live type page and found gone there too, i.e. a correction by Numista, so
# the old value is dropped from THIS record only. Keyed by N#; each entry
# names who checked what, when.
CONFIRMED_ABSENT: dict[str, dict[str, list[str]]] = {
    # «½ Speciedaler - Christian VII (Rethwisch; without value on obverse)»:
    # harvested 2026-05 with KM 606; the type page now gives KM# 605, SIEG#
    # 32, Hede# 9B and says «Mintage shared with KM# 606» — 606 is the
    # «with value» type (Hede 9A). Checked 2026-11-12, removal approved by
    # Serhii the same day.
    "148219": {"km": ["606"]},
}


def drop_confirmed_absent(nid: str | int, refs: dict) -> tuple[dict, dict]:
    """Remove the CONFIRMED_ABSENT values of one record from its references.
    Returns (references, {register: [dropped values]})."""
    rule = CONFIRMED_ABSENT.get(str(nid))
    if not rule:
        return refs, {}
    out, dropped = {}, {}
    for reg, vals in refs.items():
        gone = {_norm_value(_ALIAS.get(reg.lower(), reg.lower()), g)
                for g in rule.get(reg, [])}
        keep = [v for v in (vals if isinstance(vals, list) else [vals])
                if _norm_value(_ALIAS.get(reg.lower(), reg.lower()), str(v)) not in gone]
        lost = [v for v in (vals if isinstance(vals, list) else [vals]) if v not in keep]
        if lost:
            dropped[reg] = lost
        if keep:
            out[reg] = (keep if reg == "others" or (isinstance(vals, list) and len(keep) > 1)
                        else keep[0])
    return out, dropped


def union_references(old: dict | None, new: dict | None) -> dict:
    """Fresh references first, then every old value the fresh response
    lacks. The API leaves out some catalogues the type page shows (Schive,
    Brekke, AAJT seen 2026-11-12) and sometimes the whole block, so a value
    missing from the response is not evidence that Numista removed it."""
    out: dict = {}
    seen: dict[str, set[str]] = {}

    def norm(reg: str, v: str) -> tuple[str, str]:
        r = _ALIAS.get(reg.lower(), reg.lower())
        return r, _norm_value(r, v)

    def put(reg: str, vals) -> None:
        for v in (vals if isinstance(vals, list) else [vals]):
            if _empty(v):
                continue
            if reg == "others":
                code, _, num = str(v).partition("#")
                key = norm(code.strip(), num.strip()) if num.strip() else ("others", str(v))
            else:
                key = norm(reg, str(v))
            if key[1] in seen.setdefault(key[0], set()):
                continue
            seen[key[0]].add(key[1])
            cur = out.get(reg)
            if reg == "others":
                out[reg] = (cur or []) + [v]
            else:
                out[reg] = v if cur is None else (cur + [v] if isinstance(cur, list) else [cur, v])

    for refs in (new or {}, old or {}):
        for reg, vals in refs.items():
            put(reg, vals)
    return out


def overlay(old: dict[str, Any], new: dict[str, Any], *,
            date: str, raw_path: str) -> tuple[dict[str, Any], dict[str, Any]]:
    """Return (result sidecar, changes). ``old`` and ``new`` are canonical
    sidecars; ``new`` comes from ``parse_api_to_canonical``."""
    like_for_like = old.get("_source_shape") == "api"
    result = dict(old)
    changes: dict[str, Any] = {}

    ref_diff = diff_references(old.get("references"), new.get("references"))
    if ref_diff:
        changes["references"] = ref_diff
        result["references"] = union_references(old.get("references"),
                                                new.get("references"))
    nid = new.get("numista_id") or old.get("numista_id")
    refs, dropped = drop_confirmed_absent(nid, result.get("references") or {})
    if dropped:
        result["references"] = refs
        changes["confirmed_absent"] = dropped

    for key in sorted((set(old) | set(new)) - _META - {"references"}):
        a, b = old.get(key), new.get(key)
        if _same(a, b):
            continue
        if _empty(b):
            changes[key] = {"status": "kept_old", "old": a}
            continue
        if not like_for_like:
            changes[key] = {"status": "not_applied", "old": a, "new": b}
            continue
        status = ("added" if _empty(a)
                  else "rounded" if _is_rounding_of(a, b)
                  else "truncated" if _is_truncation_of(a, b) else "changed")
        changes[key] = {"status": status, "old": a, "new": b}
        result[key] = b

    result["_refresh"] = {"date": date, "raw": raw_path,
                          "applied": "all" if like_for_like else "references"}
    return result, changes


def latest_refresh(nid: int | str) -> Path | None:
    """Newest saved fresh response for one NID, or None."""
    if not REFRESH_DIR.exists():
        return None
    hits = sorted(REFRESH_DIR.glob(f"*/{nid}.json"))
    return hits[-1] if hits else None
