"""audit_i18n.normalize_catref canonicalises a catalogue ref to a separator-free
token so the SAME reference written with a space or a hyphen compares equal across
languages — «Hede 25» / «Hede-25» / «Hede25» all → «HEDE25». Before the hyphen was
stripped too, R3 flagged 20 spurious cross-language mismatches (HEDE25 ≠ HEDE-25)
where one language printed «Hede-25» and another «Hede 25».

Run via:
    .venv/bin/python -m unittest tests.test_i18n_catref -v
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from audit_i18n import normalize_catref  # noqa: E402


class TestNormalizeCatref(unittest.TestCase):
    def test_space_and_hyphen_collapse_equal(self):
        self.assertEqual(normalize_catref("Hede 25"), normalize_catref("Hede-25"))
        self.assertEqual(normalize_catref("Hede 25"), normalize_catref("Hede25"))
        self.assertEqual(normalize_catref("Hede 25"), "HEDE25")

    def test_km_dk_hash_and_separators(self):
        self.assertEqual(normalize_catref("KM-DK# 25"), normalize_catref("KM DK 25"))
        self.assertEqual(normalize_catref("KM#46"), "KM46")

    def test_subletter_preserved(self):
        self.assertEqual(normalize_catref("Hede 77C"), "HEDE77C")
        self.assertEqual(normalize_catref("Hede-77C"), "HEDE77C")

    def test_distinct_numbers_stay_distinct(self):
        # The fix must NOT collapse different refs — only formatting variants of ONE.
        self.assertNotEqual(normalize_catref("Hede 25"), normalize_catref("Hede 28"))
        self.assertNotEqual(normalize_catref("Hede 77"), normalize_catref("Hede 77C"))
        self.assertNotEqual(normalize_catref("KM 25"), normalize_catref("KM-DK 25"))


if __name__ == "__main__":
    unittest.main()
