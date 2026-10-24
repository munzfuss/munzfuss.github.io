"""Bruun's Swedish catalogues keep the code Bruun printed in `others`
(«Delzanno# 2», not the builder's internal «delzanno# 2»), and stored tokens
in the internal form are rewritten by normalise_catalog (curator 2026-10-24).

    .venv/bin/python -m unittest tests.test_catalog_printed_label -v
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from lib.catalog_codes import catalog_from_ref_dict, normalise_catalog  # noqa: E402

MAP = {"Delzanno": "delzanno", "Llt": "lott", "MB": "mb_swedish", "Galster": "galster"}


class PrintedLabel(unittest.TestCase):
    def test_builder_writes_printed_code(self):
        out = catalog_from_ref_dict({"Delzanno": "2", "Llt": "18", "Galster": "148"}, MAP,
                                    printed_label=True)
        self.assertEqual(out["galster"], "148")
        self.assertEqual(out["others"], ["Delzanno# 2", "Llt# 18"])

    def test_code_that_would_fold_keeps_internal_name(self):
        out = catalog_from_ref_dict({"MB": "3"}, MAP, printed_label=True)
        self.assertEqual(out, {"others": ["mb_swedish# 3"]})

    def test_default_unchanged_for_other_builders(self):
        self.assertEqual(catalog_from_ref_dict({"Delzanno": "2"}, MAP), {"others": ["delzanno# 2"]})

    def test_stored_internal_names_normalised_and_deduplicated(self):
        cat = {"others": ["delzanno# 2", "Delzanno# 2", "lott# 18", "sm# 5", "malmer# 1",
                          "mb_swedish# 3", "Sømod# 120"]}
        normalise_catalog(cat)
        self.assertEqual(cat["others"], ["Delzanno# 2", "Llt# 18", "SM# 5", "Malmer# 1",
                                         "mb_swedish# 3", "Sømod# 120"])


if __name__ == "__main__":
    unittest.main()
