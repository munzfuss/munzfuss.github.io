"""Unit tests for `timeline.founding_mint_start` — the founding-era reign-span
mint/phase START rule (curator direction 2026-07-10).

Rule recap (see the helper docstring + CLAUDE.md handoff 2026-07-10):
  A standard whose earliest coin is a reign-window placeholder year
  (`year_is_reign_span`) earlier than any DATED coin must not silently start at
  the nearest dated coin. Two sub-rules keyed on `first_adoption.firm_<scope>`:
    * firm=True  → HARD-clip the start to the founding year, no fade.
    * firm=False → start from the reign coin's own year WITH the uncertainty fade.
  When no reign coin is earlier than the earliest dated coin, the dated start is
  returned unchanged (approx=False) — the rule is a no-op.
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts" / "lib"))

from lib.timeline import founding_mint_start  # noqa: E402


class FoundingMintStart(unittest.TestCase):
    # ---- the four real founding-era fusses (denmark anywhere scope) ----
    def test_reichsdukatenfuss_rule2_fade(self):
        # de-facto anywhere founding (firm=False) → fade from the reign coin 1513,
        # NOT the nearest dated coin 1531.
        self.assertEqual(
            founding_mint_start(1513, 1531, 1481, False), (1513, True))

    def test_8_5_gylden_fod_rule1_hard(self):
        # Møntordning Sommeren 1514 (firm) → hard-clip to 1514, cutting the reign
        # coin's 1513 spill; the dated coin 1516 is superseded by the decree.
        self.assertEqual(
            founding_mint_start(1513, 1516, 1514, True), (1514, False))

    def test_9_thaler_rule1_hard_noop(self):
        # Reichsabschied 1566 (firm); reign coin 1559 clips to 1566 = the dated
        # start, so the visible start is unchanged.
        self.assertEqual(
            founding_mint_start(1559, 1566, 1566, True), (1566, False))

    def test_9_25_thaler_no_regression(self):
        # The regression guard: 9¼-Thaler's 1622 is firm (a curator-certain
        # de-facto start, NOT a Møntordning). Keying on `firm` (not literally
        # "has a decree") keeps the accepted 1622 — the reign coin 1588 clips up.
        self.assertEqual(
            founding_mint_start(1588, 1622, 1622, True), (1622, False))

    # ---- no-op cases (the common path) ----
    def test_no_reign_coin(self):
        self.assertEqual(founding_mint_start(None, 1600, 1590, True), (1600, False))
        self.assertEqual(founding_mint_start(None, 1600, 1590, False), (1600, False))

    def test_reign_coin_not_earliest(self):
        # a dated coin is at/before the reign coin → dated start, no rule.
        self.assertEqual(founding_mint_start(1620, 1600, 1590, True), (1600, False))
        self.assertEqual(founding_mint_start(1600, 1600, 1590, False), (1600, False))

    # ---- edge cases ----
    def test_rule2_no_adoption_still_fades_from_reign(self):
        # firm=False but adoption unknown → still Rule 2 (fade from reign coin).
        self.assertEqual(founding_mint_start(1513, 1531, None, False), (1513, True))

    def test_rule1_no_adoption_falls_through_to_reign(self):
        # firm=True but adoption is None → can't hard-clip to a founding year, so
        # fall through to the reign coin WITH fade (honest: no firm anchor to use).
        self.assertEqual(founding_mint_start(1513, 1531, None, True), (1513, True))

    def test_only_reign_coins_no_dated(self):
        # a fuss with ONLY reign placeholders (dated_min None):
        # firm → clip to adoption; not firm → the reign coin with fade.
        self.assertEqual(founding_mint_start(1513, None, 1500, True), (1513, False))
        self.assertEqual(founding_mint_start(1513, None, 1520, True), (1520, False))
        self.assertEqual(founding_mint_start(1513, None, 1500, False), (1513, True))

    def test_adoption_after_reign_but_before_dated_rule1(self):
        # reign 1580, adoption 1600 (firm), dated 1610 → clip = max(1580,1600)=1600,
        # min(1610,1600)=1600, hard.
        self.assertEqual(founding_mint_start(1580, 1610, 1600, True), (1600, False))


if __name__ == "__main__":
    unittest.main()
