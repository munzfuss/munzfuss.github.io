"""A lettered Hede sub-variant takes the number the page prints for it
(«Hede 8A»), not danskmoent's file name + letter («8bA», c8h8b.htm)."""
from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
_spec = importlib.util.spec_from_file_location(
    "hede_seed_for_letter_test", ROOT / "scripts" / "maintenance" / "build_hede_denmark_seed.py")
HB = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(HB)


class PrintedLetter(unittest.TestCase):
    def test_single_printed_number(self):
        self.assertEqual(HB._printed_letter_hede({"catalog_refs": {"Hede": ["8A"]}}), "8A")

    def test_none_when_absent_or_ambiguous(self):
        self.assertIsNone(HB._printed_letter_hede({"catalog_refs": {}}))
        self.assertIsNone(HB._printed_letter_hede({"catalog_refs": {"Hede": ["8A", "8B"]}}))
        self.assertIsNone(HB._printed_letter_hede({"catalog_refs": {"Hede": ["134a (tillæg)"]}}))


if __name__ == "__main__":
    unittest.main()
