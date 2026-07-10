"""Tests for the NumisMaster «ND(YYYY-YY)» abbreviated-range parser fix.

Functions under test (scripts/parse_numismaster.py):
    _complete_abbrev_year(start, abbrev) — complete an abbreviated range END
    extract_nd_range(text)               — read the «ND(YYYY-YY)» display marker

The bug (surfaced via the 120994 / 9¼-Thaler audit, 2026-07-09): NumisMaster's
structured «Date» field UNRELIABLY collapses the «ND(1618-22)» display marker to
«1618 - 1618» (or worse, «1604 - 1604»), and parse_year_range's `\\b\\d{4}\\b`
extractor drops the 2-digit abbreviated end «22». The fix reads the ND(…) marker
directly and completes the abbreviated end to the start's century, RAISING on a
century-boundary/malformed end (1698-02 → 1602 < start) rather than auto-guessing.

Run via:
    .venv/bin/python -m unittest tests.test_numismaster_nd_range -v
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

import parse_numismaster as p  # noqa: E402


def _page(date_marker: str, *, sidebar: str = "") -> str:
    """Minimal NumisMaster-shaped page: the ND marker lives in the «Value
    information» price-table Date column, before the «Related coins» sidebar."""
    return (
        "Country ... Denomination ... Date 1618 - 1618 Ruler John ... "
        "Value information in US Dollars "
        f'Date Mintage <a class="link">{date_marker}</a> '
        f"Related coins {sidebar}"
    )


class CompleteAbbrevYear(unittest.TestCase):
    def test_two_digit_same_century(self):
        self.assertEqual(p._complete_abbrev_year(1618, "22"), 1622)
        self.assertEqual(p._complete_abbrev_year(1566, "68"), 1568)
        self.assertEqual(p._complete_abbrev_year(1616, "59"), 1659)
        self.assertEqual(p._complete_abbrev_year(1624, "30"), 1630)

    def test_end_equal_to_start_last_two(self):
        # 1620-20 → 1620 (a single-year expressed as an abbreviated «range»)
        self.assertEqual(p._complete_abbrev_year(1620, "20"), 1620)

    def test_full_four_digit_end_passthrough(self):
        self.assertEqual(p._complete_abbrev_year(1618, "1622"), 1622)

    def test_century_boundary_raises(self):
        # 1698-02 would naively complete to 1602 < 1698 — MUST raise, not auto-roll
        with self.assertRaises(ValueError):
            p._complete_abbrev_year(1698, "02")

    def test_end_before_start_same_century_raises(self):
        # 1650-30 → 1630 < 1650 — malformed, must raise
        with self.assertRaises(ValueError):
            p._complete_abbrev_year(1650, "30")

    def test_garbage_end_raises(self):
        with self.assertRaises(ValueError):
            p._complete_abbrev_year(1618, "2x")


class ExtractNdRange(unittest.TestCase):
    def test_abbreviated_range(self):
        self.assertEqual(p.extract_nd_range(_page("ND(1618-22)")), (1618, 1622))
        self.assertEqual(p.extract_nd_range(_page("ND(1566-68)")), (1566, 1568))
        self.assertEqual(p.extract_nd_range(_page("ND(1624-30)")), (1624, 1630))

    def test_full_range(self):
        self.assertEqual(p.extract_nd_range(_page("ND(1616-1659)")), (1616, 1659))

    def test_single_year_nd(self):
        self.assertEqual(p.extract_nd_range(_page("ND(1523)")), (1523, 1523))

    def test_single_year_nd_circa(self):
        self.assertEqual(p.extract_nd_range(_page("ND(ca1622)")), (1622, 1622))

    def test_no_nd_marker_returns_none(self):
        self.assertIsNone(p.extract_nd_range(_page("1618 - 1622")))
        self.assertIsNone(p.extract_nd_range("plain text no marker"))
        self.assertIsNone(p.extract_nd_range(None))

    def test_sidebar_nd_does_not_bleed_in(self):
        # An ND marker AFTER «Related coins» (a related-coin in the sidebar) must
        # NOT be picked up — only the coin's own price-table marker counts.
        page = _page("ND(1618-22)", sidebar='<a class="link">ND(1700-05)</a>')
        self.assertEqual(p.extract_nd_range(page), (1618, 1622))
        # And when the coin itself has no marker, the sidebar one is ignored.
        page2 = ("... Value information Date Mintage "
                 'Related coins <a class="link">ND(1700-05)</a>')
        self.assertIsNone(p.extract_nd_range(page2))

    def test_century_boundary_propagates_raise(self):
        with self.assertRaises(ValueError):
            p.extract_nd_range(_page("ND(1698-02)"))


if __name__ == "__main__":
    unittest.main()
