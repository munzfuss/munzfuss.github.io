"""Galster numbers in the catalogue column (curator 2026-10-26).

The display form is danskmoent.dk's: a capital sub-letter straight after the
number, a sub-letter range «23A-D» («Galster 23A-D», «124A-C», «66A-B»).
Eriksson 2017's «23 a-d» / «23a» and KMM's «G. 23a» show in that form; a token
a letter range covers (the bare number, each letter inside) is not shown.
Display only — the data keeps every value.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from lib.compute import _galster_display_tokens as show  # noqa: E402


class GalsterDisplay(unittest.TestCase):
    def test_range_covers_number_and_letters(self):
        self.assertEqual(show(["23", "23A", "23A-D", "23B", "23C", "23D"]), "23A-D")

    def test_lower_case_sources_read_as_capitals(self):
        self.assertEqual(show(["23a", "23c"]), ["23A", "23C"])
        self.assertEqual(show("23 a-d"), "23A-D")

    def test_letter_outside_the_range_stays(self):
        self.assertEqual(show(["66A-B", "66C"]), ["66A-B", "66C"])

    def test_plain_numbers_untouched(self):
        self.assertEqual(show("1"), "1")
        self.assertEqual(show(["34-41"]), "34-41")


if __name__ == "__main__":
    unittest.main()
