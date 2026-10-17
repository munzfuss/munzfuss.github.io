"""TDD test for nominal_synonyms.normalise_nominal — extended with
implicit-one quantifier handling.

Function under test:
    scripts/lib/nominal_synonyms.py :: normalise_nominal(nominal)

Different sources write the same denomination with or without an implicit
«one of» numeric quantifier:

  Numista API: «1 Noble», «1 Speciedaler», «1 Ducat»
  Bruun PDF parser: «Noble», «Speciedaler», «Ducat»
  Hede: «Speciedaler», «Dukat»
  ucoin: mixed — some «1 Speciedaler», some bare

Pre-fix normalise_nominal handled cross-language synonyms (English ↔ Danish)
but NOT the «1 X» vs «X» quantifier mismatch. So «1 Noble» and «Noble»
normalised to «1 nobel» vs «nobel» — primary["nominal"] = False in the
cross-source matcher, blocking merges that should succeed.

Fix: strip a leading bare-integer «1 » after synonym substitution. Fractions
(«½ Ducat»), other quantities («2 Nobles», «10 Ducats») and multi-digit
integers («10 Kroner») stay untouched.

Run via:
    .venv/bin/python -m unittest tests.test_nominal_normalisation -v
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from lib.nominal_synonyms import normalise_nominal


class TestImplicitOnePrefix(unittest.TestCase):
    """«1 X» strips to «X» when X is a recognised denomination.
    Real-world test cases harvested from V2 seed pairs."""

    def test_one_noble_equals_bare_noble(self):
        """Bruun-3831 («Noble») vs Numista-420401 («1 Noble») — must collapse."""
        self.assertEqual(normalise_nominal("Noble"),
                         normalise_nominal("1 Noble"))

    def test_one_speciedaler_equals_bare(self):
        self.assertEqual(normalise_nominal("Speciedaler"),
                         normalise_nominal("1 Speciedaler"))

    def test_one_specie_thaler_equals_speciedaler(self):
        """Synonym + quantifier together."""
        self.assertEqual(normalise_nominal("Speciedaler"),
                         normalise_nominal("1 Specie Thaler"))

    def test_one_ducat_equals_bare_dukat(self):
        self.assertEqual(normalise_nominal("Dukat"),
                         normalise_nominal("1 Ducat"))

    def test_one_rigsbankdaler_equals_bare(self):
        self.assertEqual(normalise_nominal("Rigsbankdaler"),
                         normalise_nominal("1 Rigsbankdaler"))

    def test_one_goldgulden_equals_bare(self):
        """Real Hans Goldgulden pair — Bruun «1 Goldgulden (Rhinsk Gulden)»
        vs Numista «1 Goldgulden»: same denomination."""
        self.assertEqual(normalise_nominal("1 Goldgulden"),
                         normalise_nominal("Goldgulden"))

    def test_one_rose_noble_equals_bare_rosenobel(self):
        """Compound synonym + quantifier."""
        self.assertEqual(normalise_nominal("1 Rose Noble"),
                         normalise_nominal("Rose Noble"))


class TestFractionsStayDistinct(unittest.TestCase):
    """«½ Ducat», «¼ Speciedaler» etc. are real partial-denomination types —
    must NOT collapse with the full denomination."""

    def test_half_ducat_distinct_from_one_ducat(self):
        self.assertNotEqual(normalise_nominal("½ Ducat"),
                            normalise_nominal("1 Ducat"))

    def test_quarter_ducat_distinct_from_ducat(self):
        self.assertNotEqual(normalise_nominal("¼ Ducat"),
                            normalise_nominal("Ducat"))

    def test_one_half_speciedaler_distinct(self):
        """ASCII «1/2» form — also distinct."""
        self.assertNotEqual(normalise_nominal("1/2 Speciedaler"),
                            normalise_nominal("Speciedaler"))
        self.assertNotEqual(normalise_nominal("1/2 Speciedaler"),
                            normalise_nominal("1 Speciedaler"))


class TestOtherQuantitiesStayDistinct(unittest.TestCase):
    """Quantities other than «1» indicate genuinely different denomination
    weights — must stay distinct."""

    def test_2_nobles_distinct_from_one_noble(self):
        """Real Bruun pair: 2 Nobles (28+ g) vs 1 Noble (14+ g)."""
        self.assertNotEqual(normalise_nominal("2 Nobles"),
                            normalise_nominal("1 Noble"))

    def test_3_nobles_distinct_from_one_noble(self):
        """Real Numista: Hans 3 Nobles (single specimen, 44+ g)."""
        self.assertNotEqual(normalise_nominal("3 Nobles"),
                            normalise_nominal("1 Noble"))

    def test_10_kroner_distinct_from_krone(self):
        self.assertNotEqual(normalise_nominal("10 Kroner"),
                            normalise_nominal("Krone"))

    def test_4_speciedaler_distinct(self):
        """Christian IV Portugaloser (10 Ducats) ≠ 1 Ducat ≠ 4 Speciedaler."""
        self.assertNotEqual(normalise_nominal("4 Speciedaler"),
                            normalise_nominal("Speciedaler"))


class TestExistingSynonymsStillWork(unittest.TestCase):
    """Regression guards — pre-existing English ↔ Danish synonyms."""

    def test_noble_to_nobel(self):
        self.assertEqual(normalise_nominal("Noble"), "nobel")

    def test_nobles_to_nobel(self):
        """Plural form stripped via «s?»."""
        self.assertEqual(normalise_nominal("Nobles"), "nobel")

    def test_thaler_to_daler(self):
        self.assertEqual(normalise_nominal("Thaler"), "daler")

    def test_specie_thaler_to_speciedaler(self):
        self.assertEqual(normalise_nominal("Specie Thaler"), "speciedaler")

    def test_rose_noble_to_rosenobel(self):
        self.assertEqual(normalise_nominal("Rose Noble"), "rosenobel")

    def test_ducat_to_dukat(self):
        self.assertEqual(normalise_nominal("Ducat"), "dukat")

    def test_schilling_to_skilling(self):
        self.assertEqual(normalise_nominal("Schilling"), "skilling")


class TestMinedFormatEquivalences(unittest.TestCase):
    """Format/spelling variants of the SAME denomination, mined from entries
    sharing a globally-unique bruun_collection_id. Each pair must collapse."""

    def test_region_prefix_stripped(self):
        # Bruun «Region. Nominal» prefix is not a coin-identity discriminator.
        self.assertEqual(normalise_nominal("Lübeck. Taler"), normalise_nominal("1 Taler"))
        self.assertEqual(normalise_nominal("Oldenburg. Taler"), normalise_nominal("1 Taler"))
        self.assertEqual(normalise_nominal("Bremen & Verden. 4 Mark"), normalise_nominal("4 Mark"))
        self.assertEqual(normalise_nominal("Danish East India Company. 2 Speciedaler"),
                         normalise_nominal("2 Speciedaler"))

    def test_unicode_fraction_equals_ascii(self):
        self.assertEqual(normalise_nominal("½ Daler"), normalise_nominal("1/2 Thaler"))
        self.assertEqual(normalise_nominal("1⁄16 Thaler"), normalise_nominal("1/16 Thaler"))

    def test_dor_apostrophe_variants(self):
        self.assertEqual(normalise_nominal("2 Frederik D'or"), normalise_nominal("2 Frederik d’Or"))
        self.assertEqual(normalise_nominal("1 Christian D'or"), normalise_nominal("1 Christian d’Or"))
        self.assertEqual(normalise_nominal("1 Frederikd'or"), normalise_nominal("1 Frederik d’Or"))

    def test_parenthetical_gloss_dropped(self):
        self.assertEqual(normalise_nominal("Speciedaler (Reichstaler)"), normalise_nominal("1 Speciedaler"))
        self.assertEqual(normalise_nominal("¼ Ducat (3 Mark)"), normalise_nominal("¼ Ducat"))

    def test_kroner_plural(self):
        self.assertEqual(normalise_nominal("2 Kroner"), normalise_nominal("2 Krone"))

    def test_guldkrone_equals_gold_krone(self):
        self.assertEqual(normalise_nominal("1 Guldkrone"), normalise_nominal("1 Gold Krone"))
        self.assertEqual(normalise_nominal("2 Guldkrone"), normalise_nominal("Gold 2 Krone"))

    def test_thaler_species_and_speciesthaler(self):
        self.assertEqual(normalise_nominal("1 Thaler Species"), normalise_nominal("1 Speciedaler"))
        self.assertEqual(normalise_nominal("1⁄24 Speciesthaler"), normalise_nominal("1/24 Speciedaler"))

    def test_reichsbank_skilling(self):
        self.assertEqual(normalise_nominal("8 Reichsbank Schilling"), normalise_nominal("8 Rigsbankskilling"))

    def test_diacritic_fold(self):
        self.assertEqual(normalise_nominal("Portugaloser (10 Ducats)"), normalise_nominal("1 Portugaløser"))


class TestContaminationStaysDistinct(unittest.TestCase):
    """CRITICAL — the improved normalisation must NOT collapse genuinely
    different coins (else it would cement a bruun-id mis-cite into the matcher).
    These pairs share a bruun_collection_id ONLY because of an adjacent-id typo,
    and must remain distinct."""

    def test_skilling_not_speciedaler(self):
        self.assertNotEqual(normalise_nominal("2 Skilling"), normalise_nominal("1 Speciedaler"))
        self.assertNotEqual(normalise_nominal("2 Kroneskilling"), normalise_nominal("1 Speciedaler"))

    def test_krone_not_half_ducat(self):
        self.assertNotEqual(normalise_nominal("1 Krone"), normalise_nominal("½ Ducat"))

    def test_two_ducat_not_krone(self):
        self.assertNotEqual(normalise_nominal("2 Ducat"), normalise_nominal("1 Krone"))

    def test_ungersk_not_rhinsk_gylden(self):
        # Distinct gold-gulden types — Bruun's generic «Gold Gulden» label
        # co-occurs with both, but Ungersk (Hungarian) ≠ Rhinsk (Rhenish).
        self.assertNotEqual(normalise_nominal("1 Ungersk Gylden"), normalise_nominal("1 Rhinsk Gylden"))

    def test_two_ducats_not_one_ducat(self):
        self.assertNotEqual(normalise_nominal("2 Ducats"), normalise_nominal("1 Ducat"))


class TestEdgeCases(unittest.TestCase):
    """Boundary conditions."""

    def test_empty_returns_empty(self):
        self.assertEqual(normalise_nominal(None), "")
        self.assertEqual(normalise_nominal(""), "")

    def test_only_whitespace_returns_empty_after_strip(self):
        self.assertEqual(normalise_nominal("   "), "")

    def test_just_number_not_affected(self):
        """Lone «1» (without trailing space + denom) is left as is.
        Probably nonsense data — let it through, classifier will drop later."""
        self.assertEqual(normalise_nominal("1"), "1")

    def test_one_followed_by_no_space_not_stripped(self):
        """«1A», «1.5», «1/2» — no whitespace after 1 → no strip."""
        self.assertEqual(normalise_nominal("1A"), "1a")
        self.assertEqual(normalise_nominal("1.5 Daler"), "1.5 daler")


if __name__ == "__main__":
    unittest.main(verbosity=2)
