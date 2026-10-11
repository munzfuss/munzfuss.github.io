"""Unit tests for the fineness → period-unit (Karat / Lot) display helper."""
import os
import re
import sys
import unittest

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(_HERE))  # scripts/

from lib.render import fin_unit  # noqa: E402


def _plain(value, metal, lang="de"):
    """Rendered text without its `fin-unit` span (fa3dfd1), nbsp entities
    normalised to spaces, trimmed."""
    return re.sub(r"<[^>]+>", "", str(fin_unit(value, metal, lang))).replace("\xa0", " ").replace("&nbsp;", " ").strip()


class TestFinUnit(unittest.TestCase):
    def test_gold_whole(self):
        self.assertEqual(_plain(0.875, "gold"), "(21 Karat)")

    def test_silver_whole(self):
        self.assertEqual(_plain(0.875, "silver"), "(14 Lot)")

    def test_gold_fraction(self):
        # .986 × 24 = 23.664 → nearest ⅔ (.667)
        self.assertEqual(_plain(0.986, "gold"), "(23⅔ Karat)")

    def test_silver_fraction(self):
        # .900 × 16 = 14.4 → nearest ⅜ (.375) over ½ (.5)
        self.assertEqual(_plain(0.900, "silver"), "(14⅜ Lot)")

    def test_billon_uses_lot(self):
        self.assertEqual(_plain(0.500, "billon"), "(8 Lot)")

    def test_carry_to_whole(self):
        # .9999 × 24 = 23.9976 → carries to 24
        self.assertEqual(_plain(0.9999, "gold"), "(24 Karat)")

    def test_copper_empty(self):
        self.assertEqual(_plain(0.500, "copper"), "")

    def test_none_empty(self):
        self.assertEqual(_plain(None, "gold"), "")

    def test_uk_labels(self):
        self.assertEqual(_plain(0.986, "gold", "uk"), "(23⅔ карат)")
        self.assertEqual(_plain(0.875, "silver", "uk"), "(14 лот)")

    def test_en_keeps_period_form(self):
        self.assertEqual(_plain(0.875, "silver", "en"), "(14 Lot)")

    def test_block_span_own_line(self):
        # wrapped in a .fin-unit span (CSS makes it a left-aligned block on its
        # own line); one nbsp glues number+unit
        out = str(fin_unit(0.875, "silver", "de"))
        self.assertTrue(out.startswith('<span class="fin-unit">('))
        self.assertTrue(out.endswith("</span>"))
        self.assertEqual(out.count("&nbsp;"), 1)


if __name__ == "__main__":
    unittest.main()
