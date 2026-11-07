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



class SuspectMetalMark(unittest.TestCase):
    def test_suspect_keeps_metal_but_drops_verified(self):
        """A doubted metal stays visible but cannot outrank another source's
        attested one (curator 2026-11-07, NGC 166851 «Silver» vs Hede «Kobber»)."""
        from lib.seed_merge import apply_metal_mark
        e = {"metal": "silver", "metal_verified": True,
             "metal_mark": {"kind": "suspect", "reason": {"de": "x", "en": "x", "uk": "x", "da": "x"}}}
        apply_metal_mark(e)
        self.assertEqual(e["metal"], "silver")
        self.assertFalse(e["metal_verified"])


if __name__ == "__main__":
    unittest.main()


class VariantMetalMark(unittest.TestCase):
    def test_variant_leaves_matching_like_erroneous(self):
        """A second attested metal (brass Sechsling 1850, ucoin 187884) leaves
        the class's metal to the other members and is kept for display."""
        e = {"metal": "brass", "metal_verified": True,
             "metal_mark": {"kind": "variant", "reason": {"en": "x"}}}
        apply_metal_mark(e)
        self.assertIsNone(e["metal"])
        self.assertEqual(e["metal_mark"]["value"], "brass")

    def test_variant_reaches_metal_alts(self):
        sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "maintenance"))
        from merge_seeds_cross_source import _collect_metal_alts
        m = {"id": "sh-tid-187884", "metal": None,
             "metal_mark": {"kind": "variant", "value": "brass", "reason": {"en": "x"}}}
        alts = _collect_metal_alts([m])
        self.assertEqual([(a["value"], a["kind"]) for a in alts], [("brass", "variant")])
