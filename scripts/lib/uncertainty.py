"""Coin.uncertainty — how and by whom a field's value is uncertain.

One entry per source and field: `kind` hedged (the source prints the value
and marks it uncertain itself) or inferred (the source gives none and the
pipeline supplies one), `how` (the qualifier or the basis), `as_printed` (the
source's text, verbatim), `value`. Seed builders call `add` at the point
where they set `<field>_verified: False`; the merger unions with `union`.
Plan and rules: docs/plans/uncertainty_markers.md (curator 2026-10-29).
"""
from __future__ import annotations

HEDGED = frozenset({"circa", "attributed", "query", "decade", "century",
                    "illegible", "after", "window", "doubt", "possibly",
                    "alternatives"})
INFERRED = frozenset({"reign", "other_page", "feud_window", "text_year",
                      "standard", "default", "compiled", "curator_window",
                      "from_name", "uncited"})
FIELDS = ("year", "ruler", "mint", "metal", "fineness", "weight", "diameter")


def make(how: str, source: str, *, as_printed: str | None = None,
         value=None) -> dict:
    """One entry; `kind` follows from `how`."""
    if how in HEDGED:
        kind = "hedged"
    elif how in INFERRED:
        kind = "inferred"
    else:
        raise ValueError(f"unknown uncertainty basis {how!r}")
    e = {"kind": kind, "how": how, "source": source}
    if as_printed:
        e["as_printed"] = str(as_printed).strip()
    if value is not None:
        e["value"] = str(value)
    return e


def add(entry: dict, field: str, how: str, source: str, *,
        as_printed: str | None = None, value=None) -> dict:
    """Append one entry to `entry["uncertainty"][field]`; returns the entry."""
    if field not in FIELDS:
        raise ValueError(f"unknown uncertainty field {field!r}")
    item = make(how, source, as_printed=as_printed, value=value)
    lst = entry.setdefault("uncertainty", {}).setdefault(field, [])
    if item not in lst:
        lst.append(item)
    return entry


def year_value(first, last) -> str | None:
    if first is None:
        return None
    return str(first) if last in (None, first) else f"{first}-{last}"


def _key(e: dict) -> tuple:
    return (e.get("seed"), e.get("source"), e.get("kind"), e.get("how"),
            e.get("as_printed"), e.get("value"))


def union(members: list[dict]) -> dict | None:
    """Every member's entries, field by field, each stamped with its seed id
    (the member's own id when the entry has none); nothing collapsed."""
    out: dict[str, list[dict]] = {}
    seen: set[tuple] = set()
    for m in members:
        for field, lst in (m.get("uncertainty") or {}).items():
            for e in lst or []:
                if not isinstance(e, dict):
                    continue
                e = dict(e)
                e.setdefault("seed", m.get("id"))
                k = (field,) + _key(e)
                if k in seen:
                    continue
                seen.add(k)
                out.setdefault(field, []).append(e)
    return {f: out[f] for f in FIELDS if f in out} or None
