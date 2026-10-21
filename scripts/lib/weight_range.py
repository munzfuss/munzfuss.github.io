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


def range_pairs(ranges) -> list[tuple[float, str]]:
    """Expand `weight_range_g` into (value, source-label) weight readings:
    a range → lower bound + upper bound; a single figure → one reading.
    «ca.» is kept in the label."""
    out: list[tuple[float, str]] = []
    for r in ranges or []:
        get = (lambda k: r.get(k)) if isinstance(r, dict) else (lambda k: getattr(r, k, None))
        lo, hi, src = get("min"), get("max"), get("source") or ""
        ca = (" " + ui_key("weight_range.approx")) if get("approx") else ""
        if hi is not None and hi != lo:
            out.append((float(lo), f"{src} ({ui_key('weight_range.lower')}{ca})"))
            out.append((float(hi), f"{src} ({ui_key('weight_range.upper')}{ca})"))
        else:
            out.append((float(lo), f"{src} ({ui_key('weight_range.approx')})" if ca else src))
    return out
