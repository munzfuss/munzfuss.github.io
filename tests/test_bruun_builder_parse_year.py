"""TDD test for Bruun-builder year-extraction fallback.

Function under test:
    scripts/maintenance/build_bruun_denmark_seed.py :: parse_year(lot)

The builder's parse_year is a defensive helper: it trusts the upstream
parser's `lot.year` first, but falls back to a regex scan on meta_line /
body_excerpt when the parser left lot.year=None. The fallback regex must
mirror the upstream parser's year horizon (1300+) so a fresh build against
a stale cache (or one that wasn't re-parsed since the parser fix) still
classifies pre-1500 in-scope coins correctly.

The earlier `r"\b(15[0-4][0-9])\b"` floor at 1500-1549 silently lost the
year on every pre-1500 lot — symptom of the same bug as the parser
(fixed independently in `02_parse_lots.py`).

Run via:
    .venv/bin/python -m unittest tests.test_bruun_builder_parse_year -v
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

import importlib.util
_spec = importlib.util.spec_from_file_location(
    "build_bruun_denmark_seed",
    str(PROJECT_ROOT / "scripts" / "maintenance" / "build_bruun_denmark_seed.py"),
)
_builder = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_builder)
parse_year = _builder.parse_year


def lot(year=None, meta_line=None, body_excerpt=None):
    """Build a minimal lot dict."""
    out = {}
    if year is not None:
        out["year"] = year
    if meta_line is not None:
        out["meta_line"] = meta_line
    if body_excerpt is not None:
        out["body_excerpt"] = body_excerpt
    return out


class TestLotYearTrustedWhenPresent(unittest.TestCase):
    """When upstream parser set lot.year, builder trusts it."""

    def test_standard_post1500_year_trusted(self):
        self.assertEqual(parse_year(lot(year=1672)), 1672)

    def test_pre1500_year_trusted(self):
        """After parser fix, lot.year may be 1496 (Hans Nobel). Builder
        must trust it, not over-write."""
        self.assertEqual(parse_year(lot(year=1496)), 1496)

    def test_string_year_coerced(self):
        """lot.year may come through as a string from JSON (rare but valid)."""
        self.assertEqual(parse_year(lot(year="1672")), 1672)


class TestFallbackRegexCoversPre1500(unittest.TestCase):
    """When lot.year is None, fallback regex on meta_line / body_excerpt.
    Must cover the full Scandinavian horizon (1300+)."""

    def test_hans_nobel_1496_from_meta(self):
        """Lot 1001 scenario: lot.year=None (legacy cache before parser fix).
        Builder falls back to meta_line → finds 1496."""
        l = lot(meta_line="DENMARK. Noble, 1496. Malmö or Copenhagen Mint. Hans.",
                body_excerpt="Galster-24; Sieg-12; Schou-2; Bruun-3831.")
        self.assertEqual(parse_year(l), 1496)

    def test_hans_goldgulden_1496_from_meta(self):
        """Lot 1002 scenario: ND (ca. 1496-1497). Pre-fix builder would
        return None (regex 15[0-4][0-9] doesn't match 1496)."""
        l = lot(meta_line="DENMARK. Goldgulden (Rhinsk Gulden), ND (ca. 1496-1497). Malmö or Copenhagen Mint. Hans.",
                body_excerpt="Galster-26; Sieg-7;")
        self.assertEqual(parse_year(l), 1496)

    def test_christopher_iii_1440(self):
        """Christopher III ND (1440-42). 1440 ≥ 1300, in fallback range."""
        l = lot(meta_line="DENMARK. Skilling, ND (1440-42). Lund Mint. Christopher III of Bavaria.",
                body_excerpt="Galster-18; Sieg-4;")
        self.assertEqual(parse_year(l), 1440)


class TestFallbackRegexPost1500(unittest.TestCase):
    """Standard post-1500 fallback cases — must continue to work."""

    def test_speciedaler_1672_from_meta(self):
        l = lot(meta_line="DENMARK. Speciedaler, 1672. Copenhagen Mint. Christian V.",
                body_excerpt="KM-393; Dav-3635;")
        self.assertEqual(parse_year(l), 1672)

    def test_year_in_body_when_meta_yearless(self):
        l = lot(meta_line="DENMARK. Speciedaler. Christian VII.",
                body_excerpt="Struck in 1772 at Copenhagen Mint.")
        self.assertEqual(parse_year(l), 1772)

    def test_meta_priority_over_body(self):
        """Meta has year 1496; body has 1791. Meta wins."""
        l = lot(meta_line="DENMARK. Noble, 1496. Malmö.",
                body_excerpt="Beskrivelsen 1791-pl. 1, 2;")
        self.assertEqual(parse_year(l), 1496)


class TestMedievalNDRangeRejected(unittest.TestCase):
    """ND-medieval guard: lots starting with ND (10xx/11xx/12xx) are
    rejected outright (true medieval, definitely OOS for V2)."""

    def test_nd_1100_rejected(self):
        l = lot(year=1145, meta_line="DENMARK. Penning, ND (1100). Lund.")
        self.assertIsNone(parse_year(l))

    def test_nd_1234_rejected(self):
        l = lot(meta_line="DENMARK. Mystery Penning, ND (1234). Roskilde.",
                body_excerpt="rare medieval.")
        self.assertIsNone(parse_year(l))

    def test_nd_1396_not_rejected(self):
        """ND (1396) is 13xx — does NOT match the 10xx/11xx/12xx gate."""
        l = lot(meta_line="SWEDEN. 6 Penny, ND (1396-1439). Åbo Mint. Erik.",
                body_excerpt="Galster-201;")
        self.assertEqual(parse_year(l), 1396)


class TestEmptyInputs(unittest.TestCase):
    """No year anywhere → None (not crash)."""

    def test_empty_lot(self):
        self.assertIsNone(parse_year({}))

    def test_meta_and_body_present_but_no_year(self):
        l = lot(meta_line="DENMARK. Speciedaler. Christian VII.",
                body_excerpt="KM-543. Description without years.")
        self.assertIsNone(parse_year(l))


if __name__ == "__main__":
    unittest.main(verbosity=2)
