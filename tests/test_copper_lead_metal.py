"""One type struck in copper and in lead — metal `copper_lead` (curator 2026-11-07).

Hede C5 133 (Christiansstad siege klipping) prints «Kobber; Hede 133A …» and
«Bly; Hede 133B …»; Bruun lot 14177 is «8 Skilling Lead Klippe». The record of
the type carries both metals; copper against lead alone stays a disagreement.

Run:
    .venv/bin/python -m unittest tests.test_copper_lead_metal -v
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "scripts"), str(ROOT / "scripts" / "maintenance")]

import build_bruun_denmark_seed as bruun  # noqa: E402
import build_hede_denmark_seed as hede  # noqa: E402
import merge_seeds_cross_source as m  # noqa: E402


class HedePageMetal(unittest.TestCase):
    def test_copper_and_lead_lines(self):
        raw = ("8 Skilling klipping, Christiansstad\nForside: kronet monogram.\n"
               "Kobber; Hede 133A, Schou 52, Sieg 149\nBly; Hede 133B, Schou 53, Sieg 149\n")
        self.assertEqual(hede._metal_from_text({"raw_text": raw}), "copper_lead")

    def test_copper_line_alone(self):
        raw = "2 Skilling klipping\nKobber, RRR; Hede 131, Schou 51, Sieg 146.\n"
        self.assertEqual(hede._metal_from_text({"raw_text": raw}), "copper")


class BruunLead(unittest.TestCase):
    def test_metal_word(self):
        self.assertEqual(bruun.parse_metal("8 Skilling Lead Klippe", {}), ("lead", True))

    def test_nominal_drops_metal_word(self):
        self.assertEqual(bruun._bruun_display_nominal("8 Skilling Lead Klippe"), "8 Skilling")


class MergerCompat(unittest.TestCase):
    def test_compatible(self):
        self.assertTrue(m._copper_lead_compatible("copper_lead", "lead"))
        self.assertTrue(m._copper_lead_compatible("copper", "copper_lead"))
        self.assertFalse(m._copper_lead_compatible("copper", "lead"))
        self.assertFalse(m._copper_lead_compatible("copper_lead", "silver"))

    def test_collect(self):
        members = [{"id": "a", "metal": "lead", "metal_verified": True},
                   {"id": "b", "metal": "copper", "metal_verified": False}]
        self.assertEqual(m._collect_metal(members), "copper_lead")

    def test_copper_nickel_compares_as_copper(self):
        self.assertEqual(m._normalise_metal("copper_nickel", None), "copper")


if __name__ == "__main__":
    unittest.main()
