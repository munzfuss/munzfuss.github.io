"""compute._collapse_letter_runs — sub-letter runs shown as a letter range.

«4a, 4b, 4c, 4d» renders «4a-d» (curator 2026-10-30), with the same ≥3
threshold as number runs. A marked number keeps its own token, so the
template can still hang its «(?)» / «(*)» / «(!)» on it.

Run via:
    .venv/bin/python -m unittest tests.test_catalog_letter_runs -v
"""
from __future__ import annotations

import sys
from pathlib import Path
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from lib.compute import _collapse_letter_runs  # noqa: E402


class LetterRunsTest(unittest.TestCase):
    def test_run_of_four(self):
        self.assertEqual(_collapse_letter_runs(["3b", "4a", "4b", "4c", "4d"]), ["3b", "4a-d"])

    def test_two_letters_stay(self):
        self.assertEqual(_collapse_letter_runs(["210A", "210B"]), ["210A", "210B"])

    def test_gap_breaks_run(self):
        self.assertEqual(_collapse_letter_runs(["5a", "5b", "5c", "5e"]), ["5e", "5a-c"])

    def test_cases_not_mixed(self):
        self.assertEqual(_collapse_letter_runs(["37A", "37b", "37C"]), ["37A", "37b", "37C"])

    def test_marked_value_kept_apart(self):
        self.assertEqual(_collapse_letter_runs(["9A", "9B", "9C", "9D"], {"9B"}),
                         ["9A", "9B", "9C", "9D"])


if __name__ == "__main__":
    unittest.main()
