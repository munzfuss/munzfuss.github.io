"""An «erroneous» metal mark (schema Coin.metal_mark, curator 2026-11-07)
takes the printed metal out of play and keeps it for the «(!)» display."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from lib.seed_merge import apply_metal_mark  # noqa: E402


class MetalMark(unittest.TestCase):
    def test_erroneous_moves_value_out(self):
        e = {"metal": "copper", "metal_verified": True,
             "metal_mark": {"kind": "erroneous", "reason": {"en": "x"}}}
        apply_metal_mark(e)
        self.assertIsNone(e["metal"])
        self.assertFalse(e["metal_verified"])
        self.assertEqual(e["metal_mark"]["value"], "copper")
        apply_metal_mark(e)  # idempotent
        self.assertEqual(e["metal_mark"]["value"], "copper")

    def test_suspect_changes_nothing(self):
        e = {"metal": "copper", "metal_mark": {"kind": "suspect", "reason": {"en": "x"}}}
        apply_metal_mark(e)
        self.assertEqual(e["metal"], "copper")


if __name__ == "__main__":
    unittest.main()
