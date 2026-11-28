"""Catalogue TYPE weight ranges (`Coin.weight_range_g`).

A range («0,65–0,80 gr») or a single figure that a catalogue prints for a
type. Stored as its own structured field (so the provenance «printed for the
type» is never lost), and at build time expanded into ordinary weight
readings (curator 2026-10-21): a range counts as TWO readings, its lower and
its upper bound, each going through the normal mechanism (primary reading,
Feingewicht, Δ, specimen sub-rows); the tooltip names the source and says
which bound it is. A single figure is one ordinary reading. Merger and absorb
carry the field by union (data-accumulation principle). First source: the
danskmoent.dk Galster illustration captions (docs/SOURCES.md §13.26).
"""
from __future__ import annotations

# A localisation key embedded in a source label: «…\x1eKEY\x1e». compute.py
# runs once for all languages, so it cannot spell «lower bound»;
# render.resolve_tips swaps the key for the page language's ui.yml text.
UI_KEY_MARK = "\x1e"


def ui_key(key: str) -> str:
    return f"{UI_KEY_MARK}{key}{UI_KEY_MARK}"


def _key(r: dict) -> tuple:
    return (r.get("min"), r.get("max"), bool(r.get("approx")), r.get("source"))


def collect_weight_ranges(members: list[dict]) -> list[dict]:
    """Union of every member's `weight_range_g`, deduped, first-seen order."""
    out: list[dict] = []
    seen: set[tuple] = set()
    for m in members or []:
        for r in (m or {}).get("weight_range_g") or []:
            if not isinstance(r, dict) or _key(r) in seen:
                continue
            seen.add(_key(r))
            out.append(dict(r))
    return out


def collect_fineness_traces(members: list[dict]) -> list[dict]:
    """Union of every member's `fineness_trace` (schema.FinenessTrace —
    silver found only in traces), deduped, first-seen order. Kept beside the
    weight ranges: both are a source's statement about a type that is not a
    reading."""
    out: list[dict] = []
    seen: set[tuple] = set()
    for m in members or []:
        for t in (m or {}).get("fineness_trace") or []:
            if not isinstance(t, dict):
                continue
            k = (t.get("source"), t.get("as_printed"))
            if k in seen:
                continue
            seen.add(k)
            out.append(dict(t))
    return out


import re

# «Bruttovægt: ca. 35g» / «Vægt ca. 3 g» — the forms Hede prints.
_PRINTED_CA_RE = re.compile(
    r"^(?P<w>Bruttovægt|Vægt):?\s*ca\.?\s*(?P<v>\d+(?:[.,]\d+)?)\s*g$")
_PRINTED_TR = {
    "uk": ("перекл.", {"Bruttovægt": "вага брутто", "Vægt": "вага"}, "близько", "г"),
    "en": ("transl.", {"Bruttovægt": "gross weight", "Vægt": "weight"}, "c.", "g"),
    "de": ("dt.", {"Bruttovægt": "Rauhgewicht", "Vægt": "Gewicht"}, "ca.", "g"),
}


def approx_reason(source: str, printed: str | None = None) -> dict:
    """The reason of an `approximate` «(~)» mark on a reading a source gives
    with «ca.» (curator 2026-11-28: «(~)» replaces the «(?)» and the «ca.»
    in the label). The source in bold, its own words in italics, with a
    translation outside Danish (tooltip-text skill)."""
    m = _PRINTED_CA_RE.match((printed or "").strip())
    if not m:
        return {
            "de": f"[b]{source}[/b] gibt den Wert als ungefähr an: [i]«ca.»[/i].",
            "en": f"[b]{source}[/b] gives the value as approximate: [i]«ca.»[/i] (transl.: «circa»).",
            "uk": f"[b]{source}[/b] подає значення як приблизне: [i]«ca.»[/i] (перекл.: «близько»).",
            "da": f"[b]{source}[/b] angiver værdien som omtrentlig: [i]«ca.»[/i].",
        }
    q = printed.strip()
    out = {"da": f"[b]{source}[/b]: [i]«{q}»[/i]."}
    for lang, (lab, words, ca, unit) in _PRINTED_TR.items():
        v = m.group("v").replace(".", ",") if lang != "en" else m.group("v").replace(",", ".")
        w = words[m.group("w")]
        if lang == "de":
            w = w[0].upper() + w[1:]
        out[lang] = f"[b]{source}[/b]: [i]«{q}»[/i] ({lab}: «{w}: {ca} {v} {unit}»)."
    return out


def range_pairs(ranges) -> list[tuple[float, str]]:
    """Expand `weight_range_g` into (value, source-label) weight readings:
    a range → lower bound + upper bound; a single figure → one reading.
    A «ca.» range is marked «(~)» by `range_marks`, not in the label."""
    out: list[tuple[float, str]] = []
    for r in ranges or []:
        get = (lambda k: r.get(k)) if isinstance(r, dict) else (lambda k: getattr(r, k, None))
        lo, hi, src = get("min"), get("max"), get("source") or ""
        if hi is not None and hi != lo:
            out.append((float(lo), f"{src} ({ui_key('weight_range.lower')})"))
            out.append((float(hi), f"{src} ({ui_key('weight_range.upper')})"))
        else:
            out.append((float(lo), src))
    return out


def range_marks(ranges) -> dict[str, tuple[str, object]]:
    """`approximate` marks for the readings `range_pairs` makes of a «ca.»
    range, keyed by the same labels (compute.marker_reasons shape)."""
    from .schema import I18nText
    out: dict[str, tuple[str, object]] = {}
    for r in ranges or []:
        get = (lambda k: r.get(k)) if isinstance(r, dict) else (lambda k: getattr(r, k, None))
        if not get("approx"):
            continue
        src = get("source") or ""
        why = I18nText(**approx_reason(src))
        for _v, label in range_pairs([r]):
            out[label] = ("approximate", why)
    return out
