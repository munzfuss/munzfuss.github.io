"""Two parser defects found in the Hede-base refusals, type Ґ (curator 2026-11-07).

- Bruun: a trading company named before the denomination («DENMARK. Danish
  East India Company. 2 Speciedaler, 1671») became the nominal.
- Hede: the Christian VII index table's «Pedersen (2017)» column was glued
  onto the nominal («1/2 Krone E3»); it is a catalogue number.

Run:
    .venv/bin/python -m unittest tests.test_parser_issuer_and_pedersen -v
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "scripts"), str(ROOT / "scripts" / "maintenance")]

import build_bruun_denmark_seed as bruun  # noqa: E402
import parse_hede as hede  # noqa: E402


class BruunIssuerPrefix(unittest.TestCase):
    def test_company_is_not_the_denomination(self):
        self.assertEqual(bruun.parse_denomination(
            "DENMARK. Danish East India Company. 2 Speciedaler, 1671. Copenhagen Mint.", ""),
            "2 Speciedaler")
        self.assertEqual(bruun.parse_denomination(
            "DENMARK. Danish West India Company. 2 Ducats, 1708. Copenhagen Mint.", ""),
            "2 Ducats")

    def test_plain_lot_unchanged(self):
        self.assertEqual(bruun.parse_denomination(
            "DENMARK. Sovereign, 1608. Elsinore Mint. Christian IV .", ""), "Sovereign")


class HedePedersenColumn(unittest.TestCase):
    def test_pedersen_number_kept_apart(self):
        r = hede._index_classify_columns(
            ["24", "15", "E3", "1/2 Krone", "Sølv", "1771", "København", "note"])
        self.assertEqual(r["nominal"], "1/2 Krone")
        self.assertEqual(r["pedersen"], "E3")

    def test_seven_column_row(self):
        r = hede._index_classify_columns(
            ["19", "150", "Sovereign", "Guld", "1608", "Helsingør", "note"])
        self.assertEqual(r["nominal"], "Sovereign")
        self.assertEqual(r["pedersen"], "")


if __name__ == "__main__":
    unittest.main()
