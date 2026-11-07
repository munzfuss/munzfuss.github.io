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
                    "alternatives", "span", "museum"})
INFERRED = frozenset({"reign", "other_page", "feud_window", "text_year",
                      "standard", "standard_weight", "reign_holstein", "default", "compiled", "curator_window",
                      "from_name", "uncited", "type_assay", "other_source", "page_values"})
FIELDS = ("year", "ruler", "mint", "metal", "fineness", "weight", "diameter", "nominal")


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


def karat_label(fineness) -> str | None:
    """«18½ Karat» for a gold fineness that is a whole quarter-carat, else the
    decimal — the standard's own unit when it has one."""
    try:
        k = float(fineness) * 24
    except (TypeError, ValueError):
        return None
    q = round(k * 4) / 4
    if abs(k - q) > 0.005:
        return f"{float(fineness):g}"
    whole, frac = int(q), q - int(q)
    return f"{whole}{ {0: '', 0.25: '¼', 0.5: '½', 0.75: '¾'}[frac] } Karat".replace("  ", " ")


def held_standard_fineness(entry: dict, holds) -> dict | None:
    """The inferred `standard` entry for a fineness the curator froze as the
    standard's canonical value (§4 canonical anchor: held, `fineness_verified`
    false). None when the fineness is not such an anchor."""
    held = set(holds.keys() if isinstance(holds, dict) else (holds or []))
    # A held fineness that already says where it comes from (a source's assay
    # of the type, `type_assay`) is not the standard's value.
    if any(e.get("how") not in ("standard", None) and e.get("kind") == "inferred"
           for e in ((entry.get("uncertainty") or {}).get("fineness") or [])):
        return None
    fin = entry.get("fineness")
    if "fineness" not in held or entry.get("fineness_verified") is not False or fin in (None, []):
        return None
    if isinstance(fin, list):
        # A reading marked erroneous / suspect / template is a source's figure,
        # not the curator's anchor.
        vals = [r.get("value") if isinstance(r, dict) else r for r in fin
                if not (isinstance(r, dict) and (r.get("erroneous") or r.get("suspect")
                                                 or r.get("template")
                                                 or r.get("approximate")))]
        if not vals:
            return None
        first = vals[0]
    else:
        first = fin
    return make("standard", "standard", value=karat_label(first))
