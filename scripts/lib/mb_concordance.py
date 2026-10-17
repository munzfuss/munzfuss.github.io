"""Mansfeld-Bülow (MB) number → ruler period and mint, from the Hauberg/MB
concordance that danskmoent.dk publishes (https://www.danskmoent.dk/konkord.htm,
cached and parsed by scripts/fetch_danskmoent_konkordans.py into
scripts/cache/danskmoent/konkordans/konkord.json).

Each concordance row names a ruler WITH his years («1259-1286 Erik Klipping»)
and a mint, then pairs Hauberg numbers with MB numbers or ranges («1/141-142,
2/143, …»). An MB number therefore pins the ruler and the years the source
itself gives — used by absorb's reign-window placeholder for undated KMM
pennies that carry an MB number but no ruler (curator 2026-10-17,
docs/undated_coins_denmark.md row 3).

Two guards, both refusing rather than guessing:
  * within a row the MB items run upwards; an item whose start lies below the
    previous item's end is a source misprint («2/224-427» right after «1/423»
    in Erik Menved's Nørrejylland row) and is dropped, not repaired;
  * an MB number that more than one row claims is ambiguous → None.
Rows written «Hauberg = MB» give no numbers and contribute nothing.
"""
from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path

_KONKORD = (Path(__file__).resolve().parents[1] / "cache" / "danskmoent"
            / "konkordans" / "konkord.json")
_ROW_RULER_RE = re.compile(r"^\s*(\d{3,4})\s*-\s*(\d{3,4})\s+(.+?)\s*$")
_ITEM_RE = re.compile(r"(?:\d+|-)\s*/\s*(\d+)(?:\s*-\s*(\d+))?")


@lru_cache(maxsize=1)
def _table() -> list[tuple[int, int, int, int, str, str]]:
    """[(mb_lo, mb_hi, year_from, year_to, ruler, mint)]."""
    try:
        rows = json.loads(_KONKORD.read_text(encoding="utf-8")).get("hauberg_mansfeld_bullner") or []
    except (OSError, ValueError):
        return []
    out = []
    for r in rows:
        m = _ROW_RULER_RE.match(str(r.get("ruler") or ""))
        if not m:
            continue
        y0, y1, ruler = int(m.group(1)), int(m.group(2)), m.group(3)
        prev_hi = None
        for it in _ITEM_RE.finditer(str(r.get("concordance") or "")):
            lo = int(it.group(1))
            hi = int(it.group(2) or lo)
            if hi < lo or (prev_hi is not None and lo < prev_hi):
                continue  # misprint — see module docstring
            out.append((lo, hi, y0, y1, ruler, str(r.get("mint") or "")))
            prev_hi = hi
    return out


def mb_lookup(number) -> tuple[int, int, str, str] | None:
    """(year_from, year_to, ruler, mint) for one MB number, or None when the
    number is unknown, unparseable or claimed by more than one row."""
    m = re.match(r"\s*0*(\d+)", str(number or ""))
    if not m:
        return None
    n = int(m.group(1))
    hits = {(y0, y1, ruler, mint) for lo, hi, y0, y1, ruler, mint in _table() if lo <= n <= hi}
    return next(iter(hits)) if len(hits) == 1 else None


def mb_window(values) -> tuple[int, int] | None:
    """Year window for a coin's MB value(s) (scalar, list, or «a-b» ranges):
    every number must resolve and all must agree on ONE row's years;
    otherwise None (a record citing two rulers' MB numbers stays undated)."""
    vals = values if isinstance(values, list) else [values]
    windows = set()
    for v in vals:
        s = str(v or "")
        nums = re.findall(r"\d+", s)
        if not nums:
            return None
        ends = [nums[0]]
        if len(nums) > 1 and int(nums[-1]) > int(nums[0]):
            ends.append(nums[-1])  # «541-46» is KMM's short form: use 541 only
        for n in ends:
            hit = mb_lookup(n)
            if hit is None:
                return None
            windows.add((hit[0], hit[1]))
    return next(iter(windows)) if len(windows) == 1 else None


# Nominals that only one issue period struck, as a year window for an undated
# coin that names no ruler. Erik af Pommern's copper sterlings: «Udmøntningen
# dateres af Jens Christian Moesgaard, under inddragelse af nye fund og
# overvejelser, til ca. 1420-1430/35» (J. S. Jensen, «Regionale forskelle på
# udmøntning og møntbrug i Danmark ca. 1050 - ca. 1500», Hikuin 35, 2008,
# s. 158; cached scripts/cache/danskmoent/hans_1481_1513/
# jensen_2008_hikuin35_regionale_forskelle.pdf). Curator 2026-10-17.
_NOMINAL_PERIODS = {
    "kobbersterling": (1420, 1435),
}


def nominal_window(nominal) -> tuple[int, int] | None:
    """Year window for a nominal struck in one period only, or None. KMM's
    doubt mark («1 Kobbersterling?») does not change the window; the result
    is a placeholder shown (?) either way."""
    s = re.sub(r"^\s*\d+\s+", "", str(nominal or "")).strip(" ?").lower()
    return _NOMINAL_PERIODS.get(s)
