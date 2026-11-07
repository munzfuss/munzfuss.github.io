"""«Sieg 2016» names the catalogue's edition year, not a Sieg number
(danskmoent f7h19 / f7h20: «Vægt: Hede (og Sieg 2016) angiver 4,872g»)."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import parse_hede as P  # noqa: E402


class SiegEditionYear(unittest.TestCase):
    def test_edition_year_dropped(self):
        txt = "(Hede 19, Schou hhv 2 og 5, Sieg 22)\nVægt: Hede (og Sieg 2016) angiver 4,872g"
        self.assertEqual(P._extract_refs(txt).get("Sieg"), ["22"])

    def test_dav_keeps_high_numbers(self):
        self.assertEqual(P._strip_year_tokens("2016", "Dav"), "2016")

    def test_schou_bound_unchanged(self):
        self.assertEqual(P._strip_year_tokens("2016", "Schou"), "2016")


if __name__ == "__main__":
    unittest.main()
