"""Norway after 1814 is its own entity, `norway` (curator 2026-10-19).

Function under test:
    scripts/lib/mint_registry.py :: norway_split_entity
    (+ the Kongsberg year override and the year-aware «Norge» nation rule)

Rule: a Norwegian coin struck from 1815 on belongs to the Kingdom of Norway;
up to 1814 to Norway under the Danish crown. No Norwegian coin is dated 1814
or 1815 (the first is the 1816 Skilling), so a range opening in 1814 and
running on is a later piece. A coin naming a Danish king stays in
`danish_norway` whatever its date.

Run:

    .venv/bin/python -m unittest tests.test_norway_split -v
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from lib.mint_registry import (  # noqa: E402
    classify_nation_to_entity, norway_split_entity,
)
from lib.v2_entity_classify import classify_mint_to_entity  # noqa: E402


class NorwaySplitTest(unittest.TestCase):
    def test_post_1814_goes_to_norway(self):
        self.assertEqual(norway_split_entity("danish_norway", 1816, 1816, "Carl XIII"), "norway")
        self.assertEqual(norway_split_entity("danish_norway", 1907, 1907, None), "norway")

    def test_up_to_1814_stays(self):
        self.assertEqual(norway_split_entity("danish_norway", 1813, 1813, "Frederik 6"), "danish_norway")
        self.assertEqual(norway_split_entity("danish_norway", 1814, 1814, None), "danish_norway")

    def test_range_opening_in_1814_is_later_piece(self):
        # KMM 471237, 2 Krone «1814-1914» jubilee coin
        self.assertEqual(norway_split_entity("danish_norway", 1814, 1914, None), "norway")
        # a range opening before 1814 is not touched
        self.assertEqual(norway_split_entity("danish_norway", 1806, 1830, "Magnus VII"), "danish_norway")

    def test_danish_king_stays(self):
        # KMM 148142 «1 Rigsbankdaler, Frederik 6, 1834, Kongsberg»
        self.assertEqual(norway_split_entity("danish_norway", 1834, 1834, "Frederik 6"), "danish_norway")
        self.assertEqual(norway_split_entity("norway", 1834, 1834, "Frederick VI"), "danish_norway")

    def test_other_entities_untouched(self):
        self.assertEqual(norway_split_entity("danish_realm", 1900, 1900, None), "danish_realm")
        self.assertEqual(norway_split_entity("danish_norway", None, None, None), "danish_norway")

    def test_kongsberg_override(self):
        self.assertEqual(classify_mint_to_entity("Kongsberg", year=1814), "danish_norway")
        self.assertEqual(classify_mint_to_entity("Kongsberg", year=1815), "norway")
        self.assertEqual(classify_mint_to_entity("Kongsberg"), "danish_norway")

    def test_nation_rule(self):
        self.assertEqual(classify_nation_to_entity("Norge", 1814), "danish_norway")
        self.assertEqual(classify_nation_to_entity("Norge", 1815), "norway")
        self.assertEqual(classify_nation_to_entity("Danmark-Norge", 1820), "danish_realm")


if __name__ == "__main__":
    unittest.main()
