"""TDD test for year-aware `classify_mint_to_entity`.

Function under test:
    scripts/lib/v2_entity_classify.py :: classify_mint_to_entity

Behavioural rule (user direction, 2026-05-26):

  classify_mint_to_entity(mint, year=None) → str | list[str] | None

- `year=None` → backward-compatible behaviour (use default entity).
- `year` provided → walk the mint's `year_overrides` list; the FIRST
  matching override wins. Override match rule (per locked convention):
    • `year_from` inclusive, `year_to` EXCLUSIVE.
    • Override missing one bound → that side is open
      (`year_from: None` → -∞, `year_to: None` → +∞).
- No override matches → fall back to the mint's default `entity`.

The 100 %-certain transitions added in MVP-D phase (2026-05-26):
  * **Altona**: year < 1640 → `schauenburg_pinneberg`;
                year ≥ 1640 → `royal_holstein` (default).

See `docs/research/mint_year_transitions.md` for source citations.

Run:

    .venv/bin/python -m unittest tests.test_classify_mint_year_aware -v
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from lib.v2_entity_classify import classify_mint_to_entity  # noqa: E402


class TestClassifyMintYearAwareBackwardCompat(unittest.TestCase):
    """When called without a `year` argument the function behaves
    exactly as before — year-aware logic is opt-in.
    """

    def test_kopenhagen_no_year(self):
        self.assertEqual(classify_mint_to_entity("Kopenhagen"), "danish_realm")

    def test_kopenhagen_with_year(self):
        # Kopenhagen has no year_overrides — default `danish_realm` for
        # any year.
        self.assertEqual(classify_mint_to_entity("Kopenhagen", year=1640),
                         "danish_realm")

    def test_glueckstadt_no_year(self):
        # Glückstadt: no year_overrides, default royal_holstein.
        self.assertEqual(classify_mint_to_entity("Glückstadt"), "royal_holstein")
        self.assertEqual(classify_mint_to_entity("Glückstadt", year=1640),
                         "royal_holstein")

    def test_unknown_mint_no_year(self):
        self.assertIsNone(classify_mint_to_entity("UnknownPlace"))

    def test_unknown_mint_with_year(self):
        self.assertIsNone(classify_mint_to_entity("UnknownPlace", year=1640))


class TestAltonaYearAware(unittest.TestCase):
    """Altona transitioned from Schauenburg-Pinneberg to Royal Holstein
    in 1640 after Count Otto V's childless death (verified via Wikipedia
    sources — see `docs/research/mint_year_transitions.md`).

    Convention: `year < 1640` → Schauenburg, `year ≥ 1640` → Royal
    Holstein (exclusive cutoff).
    """

    def test_pre_1640_schauenburg(self):
        """Adolf XIII / Ernst III / Otto V era Altona — Schauenburg-Pinneberg."""
        self.assertEqual(classify_mint_to_entity("Altona", year=1589),
                         "schauenburg_pinneberg")
        self.assertEqual(classify_mint_to_entity("Altona", year=1601),
                         "schauenburg_pinneberg")
        self.assertEqual(classify_mint_to_entity("Altona", year=1639),
                         "schauenburg_pinneberg")

    def test_year_1640_at_cutoff_post_period(self):
        """Exclusive cutoff: year=1640 → post-period = royal_holstein.

        (Otto V died in 1640; from that year onwards Altona is part of
        Holstein-Glückstadt under Christian IV per Wikipedia EN.)
        """
        self.assertEqual(classify_mint_to_entity("Altona", year=1640),
                         "royal_holstein")

    def test_post_1640_royal_holstein(self):
        """Christian IV / Christian V / etc. royal-mint era — Royal Holstein."""
        self.assertEqual(classify_mint_to_entity("Altona", year=1645),
                         "royal_holstein")
        self.assertEqual(classify_mint_to_entity("Altona", year=1800),
                         "royal_holstein")
        self.assertEqual(classify_mint_to_entity("Altona", year=1864),
                         "royal_holstein")

    def test_no_year_uses_default(self):
        """When year is missing, fall back to default entity (= post-
        cutoff royal_holstein per registry's `entity` field)."""
        self.assertEqual(classify_mint_to_entity("Altona"),
                         "royal_holstein")
        self.assertEqual(classify_mint_to_entity("Altona", year=None),
                         "royal_holstein")

    def test_altona_case_insensitive(self):
        """Case-insensitive normalisation per existing classifier."""
        self.assertEqual(classify_mint_to_entity("altona", year=1589),
                         "schauenburg_pinneberg")
        self.assertEqual(classify_mint_to_entity("ALTONA", year=1645),
                         "royal_holstein")


class TestClassifyMintYearAwareListInput(unittest.TestCase):
    """List-form `mint` should still work with year argument."""

    def test_single_mint_in_list_pre_1640(self):
        self.assertEqual(classify_mint_to_entity(["Altona"], year=1589),
                         "schauenburg_pinneberg")

    def test_list_mint_post_1640(self):
        self.assertEqual(classify_mint_to_entity(["Altona"], year=1645),
                         "royal_holstein")

    def test_multi_mint_year_aware(self):
        """When mint is list-form and yields different entities under
        the same year, result is sorted unique list (alphabetical).
        Example: Altona + Glückstadt at 1640 both yield royal_holstein
        → single scalar. At 1589, Altona yields Schauenburg, Glückstadt
        yields royal_holstein → list [royal_holstein, schauenburg_pinneberg]."""
        # Same-entity case
        self.assertEqual(
            classify_mint_to_entity(["Altona", "Glückstadt"], year=1645),
            "royal_holstein",
        )
        # Different-entity case
        result = classify_mint_to_entity(["Altona", "Glückstadt"], year=1589)
        self.assertEqual(
            result,
            sorted({"schauenburg_pinneberg", "royal_holstein"}),
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
