"""Catalogue TYPE weight ranges (`Coin.weight_range_g`).

A range («0,65–0,80 gr») or a single «ca.» figure that a catalogue prints
for a type — not a weighed specimen. It never enters `weight_rough_g`, the
primary reading, Feingewicht, Δ or the implied Fuß. Merger and absorb carry
it by union (data-accumulation principle); the renderer shows it as its own
line in the weight column. First source: the danskmoent.dk Galster
illustration captions (docs/SOURCES.md §13, curator 2026-10-21).
"""
from __future__ import annotations


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

