"""Regression: `year_label` / `year_first` are REQUIRED for classified coins but
OPTIONAL for `fuss == seed_unsorted`.

Undated KMM museum specimens (no year, no KM) are legitimately yearless and
never render; before 2026-06-29 they failed `Coin` schema validation (audit_v2
I4, 43 of 51 findings) on the two required year fields. The `Coin` model now
exempts `seed_unsorted` via `_check_year_required` while keeping the contract
strict for every coin that actually renders.

Run:
    .venv/bin/python -m unittest tests.test_year_optional_seed_unsorted -v
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from lib.schema import Coin  # noqa: E402

_BASE = dict(id="t", phase="A", kind="kurant", nominal="2 Dukat")


class TestYearOptionalForSeedUnsorted(unittest.TestCase):
    def test_seed_unsorted_without_year_is_valid(self):
        # An unclassified museum record with neither year nor catalogue number.
        c = Coin(fuss="seed_unsorted", **_BASE)
        self.assertIsNone(c.year_label)
        self.assertIsNone(c.year_first)

    def test_classified_without_year_label_is_rejected(self):
        with self.assertRaises(Exception):
            Coin(fuss="9_thaler", year_first=1611, **_BASE)

    def test_classified_without_year_first_is_rejected(self):
        with self.assertRaises(Exception):
            Coin(fuss="9_thaler", year_label="1611", **_BASE)

    def test_classified_with_year_is_valid(self):
        c = Coin(fuss="9_thaler", year_label="1611", year_first=1611, **_BASE)
        self.assertEqual(c.year_first, 1611)

    def test_seed_unsorted_with_year_still_allowed(self):
        # Exempt does not mean forbidden — a seed_unsorted coin MAY carry a year.
        c = Coin(fuss="seed_unsorted", year_label="1611", year_first=1611, **_BASE)
        self.assertEqual(c.year_label, "1611")


if __name__ == "__main__":
    unittest.main(verbosity=2)
