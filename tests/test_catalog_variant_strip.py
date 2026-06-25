"""normalise_catalog drops a trailing «var.» / «variant» qualifier from a
catalogue index.

Curator decision 2026-06-25: «var.» merely flags a variant OF the index — the
index itself is sufficient («Lange 16b var.» → «16b», «358 C IV var.» → «358 C IV»).
Distinct from cf./unlisted, which DROP the whole value (a «cf.» points at a
DIFFERENT coin); a «var.» IS this coin's own index with a redundant qualifier, so
the index is kept and only the qualifier stripped.

Run via:
    .venv/bin/python -m unittest tests.test_catalog_variant_strip -v
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from lib.catalog_codes import normalise_catalog, _strip_variant_qualifier  # noqa: E402


class TestStripHelper(unittest.TestCase):
    def test_strips_trailing_var(self):
        self.assertEqual(_strip_variant_qualifier("16b var."), "16b")
        self.assertEqual(_strip_variant_qualifier("271 var."), "271")
        self.assertEqual(_strip_variant_qualifier("358 C IV var."), "358 C IV")
        self.assertEqual(_strip_variant_qualifier("399 A var."), "399 A")

    def test_strips_full_word_variant(self):
        self.assertEqual(_strip_variant_qualifier("12 variant"), "12")

    def test_keeps_clean_index(self):
        self.assertEqual(_strip_variant_qualifier("16b"), "16b")
        self.assertEqual(_strip_variant_qualifier("XIV.32-33"), "XIV.32-33")


class TestNormaliseCatalogStripsVar(unittest.TestCase):
    def test_lange_var_stripped(self):
        cat = {"lange": "16b var."}
        normalise_catalog(cat)
        self.assertEqual(cat["lange"], "16b")

    def test_lange_letter_sub_var_stripped(self):
        cat = {"lange": "358 C IV var."}
        normalise_catalog(cat)
        self.assertEqual(cat["lange"], "358 C IV")

    def test_clean_index_untouched(self):
        cat = {"lange": "16b", "schive": "XIV.32-33"}
        normalise_catalog(cat)
        self.assertEqual(cat["lange"], "16b")
        self.assertEqual(cat["schive"], "XIV.32-33")


if __name__ == "__main__":
    unittest.main(verbosity=2)
