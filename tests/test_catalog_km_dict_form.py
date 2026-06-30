"""Regression: `catalog.km` dict-form accepts per-register LIST values.

Cross-Krause-volume coins namespace their KM by register (`{sh: …, dk: …}` —
KM-SH# on the Schleswig-Holstein page, KM-DK# on the Denmark page). A coin may
carry SEVERAL KM numbers within one volume, so each register's value is a single
KM OR a list of KMs. Before 2026-06-29 the schema typed the dict value as plain
`str`, so the list-valued form (the actual shape of c5h125a / f3h153a / km-696-1)
failed `Coin` validation (audit_v2 I4) even though it rendered correctly.

Run:
    .venv/bin/python -m unittest tests.test_catalog_km_dict_form -v
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from lib.schema import Coin  # noqa: E402

_BASE = dict(id="t", phase="A", kind="kurant", nominal="4 Mark",
             fuss="9_thaler", year_label="1659", year_first=1659)


def _km(km):
    return Coin(catalog={"km": km}, **_BASE).catalog.km


class TestCatalogKmDictForm(unittest.TestCase):
    def test_dict_of_list(self):
        # f3h153a real shape — both registers list-valued.
        km = {"sh": ["95", "A43", "B43"], "dk": ["A43", "B43"]}
        self.assertEqual(_km(km), km)

    def test_dict_mixed_str_and_list(self):
        # km-696-1 real shape — one register list, one register scalar.
        km = {"sh": ["696.1", "696"], "dk": "706.1"}
        self.assertEqual(_km(km), km)

    def test_dict_of_str_still_allowed(self):
        km = {"sh": "95", "dk": "A43"}
        self.assertEqual(_km(km), km)

    def test_plain_list_and_scalar_still_allowed(self):
        self.assertEqual(_km(["77", "77.1"]), ["77", "77.1"])
        self.assertEqual(_km("73"), "73")


if __name__ == "__main__":
    unittest.main(verbosity=2)
