"""«Sch, 1» — KMM put a comma between the catalogue and its number.

The typeNumber split on «;» and «,» tore «Sch» from «1», so kmk-273643 (Hans,
Skilling, Malmø 1512) carried no Schou at all and looked like an index-less
stub. The «Sch;82» rejoin (2 records) now covers the comma too; the corpus had
two such records on 2026-10-20 (kmk-273643, kmk-273986).

Run:
    .venv/bin/python -m unittest tests.test_kmk_sch_comma -v
"""
from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "maintenance"))

_spec = importlib.util.spec_from_file_location(
    "build_kmk_seed_for_sch_comma", ROOT / "scripts" / "maintenance" / "build_kmk_seed.py")
bks = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(bks)


class SchCommaNumber(unittest.TestCase):
    def test_comma_between_sch_and_number(self):
        self.assertEqual(bks._catalog({"typeNumber": "Sch, 1"}), {"schou": "1"})

    def test_cf_after_the_number_stays_a_cf(self):
        self.assertEqual(bks._catalog({"typeNumber": "Sch, 146, cf. "}),
                         {"schou": "cf. 146"})

    def test_semicolon_form_unchanged(self):
        self.assertEqual(bks._catalog({"typeNumber": "H:99C; Sch;82"}).get("schou"), "82")


if __name__ == "__main__":
    unittest.main()
