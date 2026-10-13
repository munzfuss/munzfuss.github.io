"""`compute_coin_year_runs` — markers are clamped to the fuss's effective
mint span when `mint_spans` is given.

Function under test:
    scripts/lib/timeline.py :: compute_coin_year_runs

The case (2026-10-13, Denmark axis opened at 1490): `unified-dk-galster-c2g-44`
(8½-Gylden-Fod) is a reign-window placeholder «1513-1523» (`year_verified:
false`). `derive_mint_overrides` + the founding rule pin that fuss's mint
layer to 1514, but the marker code only filtered by the axis, so a lone 1513
marker appeared one year before the mint stripe. With the post-sync spans
passed in, the first run starts at 1514; without them the old behaviour
(1513) is kept so other callers are unaffected.

Run via:
    .venv/bin/python -m unittest tests.test_coin_year_runs_mint_span -v
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path
from types import SimpleNamespace as NS

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from lib.timeline import compute_coin_year_runs  # noqa: E402


def _coin(fid: str, first: int, last: int) -> NS:
    raw = NS(id=f"{fid}-{first}", fuss=fid, year_first=first, year_last=last,
             year_ranges=[[first, last]], issuing_entity="danish_realm")
    return NS(raw=raw)


def _bar(fid: str) -> NS:
    return NS(id=fid)


class TestMintSpanClamp(unittest.TestCase):
    def test_marker_clamped_to_mint_span(self):
        runs = compute_coin_year_runs(
            [_bar("g85")], [_coin("g85", 1513, 1523)], 1490, 1914,
            mint_spans={"g85": (1514, 1523)},
        )["g85"]
        self.assertEqual(runs[0]["first"], 1514)
        self.assertEqual(runs[-1]["last"], 1523)

    def test_without_spans_old_behaviour(self):
        runs = compute_coin_year_runs(
            [_bar("g85")], [_coin("g85", 1513, 1523)], 1490, 1914,
        )["g85"]
        self.assertEqual(runs[0]["first"], 1513)

    def test_fuss_absent_from_spans_keeps_axis_filter(self):
        runs = compute_coin_year_runs(
            [_bar("g85")], [_coin("g85", 1513, 1523)], 1490, 1914,
            mint_spans={"other": (1600, 1700)},
        )["g85"]
        self.assertEqual(runs[0]["first"], 1513)


if __name__ == "__main__":
    unittest.main()
