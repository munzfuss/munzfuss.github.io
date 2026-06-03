"""End-to-end TDD test: with all four fixes in place, the cross-source
matcher must declare a CONFIDENT merge between Bruun-3831 and
Numista-420401 — both representing Hans's 1496 Nobel.

This test is the integration check that joins:

  1. Bruun parser fix (02_parse_lots.py) — pre-1500 year extraction
     correctly captures 1496 instead of 1791 (Beskrivelsen-trap).
  2. Bruun builder fix (build_bruun_denmark_seed.py) — fallback parse_year
     mirrors parser's 1300+ horizon + tighter ND-medieval gate.
  3. Cross-source merger fix (merge_seeds_cross_source.py) — `_catalog_refs`
     canonicalises friedberg → fr so Bruun's `friedberg:3` and Numista's
     `fr:3` overlap.
  4. Nominal-synonyms fix (lib/nominal_synonyms.py) — «1 Noble» and
     «Noble» normalise to the same canonical «nobel».

Before all four fixes: match_pair returned `no_match` (nominal
disagreement, no catalog overlap to override). After all four: match_pair
returns `confident` because all three primary signals (metal, nominal,
catalog) align AND at least one fallback (years) agrees.

Run via:
    .venv/bin/python -m unittest tests.test_e2e_nobel_merge -v
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

import importlib.util
_spec = importlib.util.spec_from_file_location(
    "merge_seeds_cross_source",
    str(PROJECT_ROOT / "scripts" / "maintenance" / "merge_seeds_cross_source.py"),
)
_merger = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_merger)
match_pair = _merger.match_pair


# ---------------------------------------------------------------------
# Real-world coin records — extracted from current V2 seed yamls
# 2026-05-24 (with year applied as the post-fix expected value).
# ---------------------------------------------------------------------

NUMISTA_HANS_NOBEL = {
    "id": "dk-numista-420401",
    "issuing_entity": "danish_realm",
    "nominal": "1 Noble",
    "ruler": "John I (Hans I)",
    "year_first": 1496,
    "year_last": 1502,
    "mint": None,
    "catalog": {"numista": "420401", "fr": "3"},
    "metal": "gold", "metal_verified": True,
    "weight_rough_g": 14.75,
    "kind": "kurant",
}

# Pre-fix Bruun-3831 — year=1791 (Beskrivelsen-trap)
BRUUN_HANS_NOBEL_PREFIX = {
    "id": "dk-bruun-3831",
    "issuing_entity": "danish_realm",
    "nominal": "Noble",
    "ruler": "Hans",
    "year_first": 1791, "year_last": 1791,
    "mint": "Kopenhagen", "mint_verified": True,
    "catalog": {"bruun_collection_id": "3831", "sieg": "12", "schou": "2",
                "galster": "24", "friedberg": "3"},
    "metal": "gold", "metal_verified": True,
    "weight_rough_g": [{"value": 14.67, "source": "bruun"}],
    "kind": "kurant",
}

# Post-fix Bruun-3831 — year=1496
BRUUN_HANS_NOBEL_POSTFIX = dict(BRUUN_HANS_NOBEL_PREFIX, year_first=1496, year_last=1496)


NUMISTA_HANS_GOLDGULDEN = {
    "id": "dk-numista-355730",
    "issuing_entity": "danish_realm",
    "nominal": "1 Goldgulden",
    "ruler": "John I (Hans I)",
    "year_first": 1481, "year_last": 1513,
    "catalog": {"numista": "355730", "fr": "4"},
    "metal": "gold", "metal_verified": True,
    "weight_rough_g": 3.49,
    "kind": "kurant",
}

# Hans Goldgulden Bruun-3840 — pre-fix year=1817, post-fix year=1496
BRUUN_HANS_GOLDGULDEN_POSTFIX = {
    "id": "dk-bruun-3840",
    "issuing_entity": "danish_realm",
    "nominal": "1 Goldgulden (Rhinsk Gulden)",
    "ruler": "Hans",
    "year_first": 1496, "year_last": 1497,
    "mint": "Malmö", "mint_verified": True,
    "catalog": {"bruun_collection_id": "3840", "sieg": "7", "schou": "13",
                "friedberg": "4"},
    "metal": "gold", "metal_verified": True,
    "weight_rough_g": [{"value": 3.32, "source": "bruun"}],
    "kind": "kurant",
}


class TestPreFixBaselineFails(unittest.TestCase):
    """Document the pre-fix behaviour as a baseline. These tests check
    that with the wrong year (1791), the merge still fails for the
    right reason (year mismatch) — defending against accidental merge
    if some other signal was over-permissive."""

    def test_pre_fix_bruun_with_year_1791_demotes_to_low_confidence(self):
        """With the parser bug (year=1791), all 4 primary signals still
        align (metal, nominal-after-normalisation, catalog Fr-3, ruler
        Hans/John I) but `years` fallback disagrees (1791 vs 1496-1502).

        Per match_pair confidence ladder: 4 primary True + 1 fallback
        False → `low_confidence` (the curator must inspect — not silent
        auto-merge). This is the correct safety verdict that protects
        against the parser bug silently producing wrong merges; the
        parser fix removes the year disagreement entirely so post-fix
        match goes to `confident`."""
        r = match_pair(BRUUN_HANS_NOBEL_PREFIX, NUMISTA_HANS_NOBEL,
                       entity_id="danish_realm")
        self.assertEqual(r["decision"], "low_confidence",
                         f"Pre-fix Bruun (year=1791) must demote to "
                         f"low_confidence — got {r['decision']}, "
                         f"primary={r['primary']}, fallback={r['fallback']}, "
                         f"why={r['why']}")
        # Demote-to-low-confidence is THE FALLBACK signal disagreeing.
        # If years had been matched too, the merge would auto-promote.
        self.assertIs(r["fallback"]["years"], False)


class TestPostFixHansNobelMergesConfidently(unittest.TestCase):
    """After all four fixes: Bruun-3831 (year=1496) + Numista-420401
    must merge as `confident` — same physical type, three sources."""

    def test_post_fix_merge_decision_is_confident(self):
        """The critical assertion — `confident` decision."""
        r = match_pair(BRUUN_HANS_NOBEL_POSTFIX, NUMISTA_HANS_NOBEL,
                       entity_id="danish_realm")
        self.assertEqual(
            r["decision"], "confident",
            f"Bruun-3831 (year=1496, Fr-3) + Numista-420401 (Fr-3) should "
            f"merge confidently after fixes. Got: {r['decision']}. "
            f"primary={r['primary']}, fallback={r['fallback']}, why={r['why']}"
        )

    def test_post_fix_metal_signal_true(self):
        r = match_pair(BRUUN_HANS_NOBEL_POSTFIX, NUMISTA_HANS_NOBEL,
                       entity_id="danish_realm")
        self.assertIs(r["primary"]["metal"], True)

    def test_post_fix_nominal_signal_true_after_normalisation(self):
        """«Noble» (Bruun) ≡ «1 Noble» (Numista) after the implicit-one
        strip in nominal_synonyms."""
        r = match_pair(BRUUN_HANS_NOBEL_POSTFIX, NUMISTA_HANS_NOBEL,
                       entity_id="danish_realm")
        self.assertIs(r["primary"]["nominal"], True,
                      f"Got primary['nominal']={r['primary']['nominal']!r}, "
                      f"why={r['why']}")

    def test_post_fix_catalog_signal_true_via_fr_canonical(self):
        """«friedberg:3» (Bruun) ≡ «fr:3» (Numista) after canonicalisation."""
        r = match_pair(BRUUN_HANS_NOBEL_POSTFIX, NUMISTA_HANS_NOBEL,
                       entity_id="danish_realm")
        self.assertIs(r["primary"]["catalog"], True,
                      f"Got primary['catalog']={r['primary']['catalog']!r}, "
                      f"why={r['why']}")

    def test_post_fix_year_overlap_via_fallback(self):
        """1496 ⊆ [1496, 1502] — years overlap."""
        r = match_pair(BRUUN_HANS_NOBEL_POSTFIX, NUMISTA_HANS_NOBEL,
                       entity_id="danish_realm")
        self.assertIs(r["fallback"]["years"], True,
                      f"Got fallback['years']={r['fallback']['years']!r}, "
                      f"why={r['why']}")


class TestPostFixHansGoldguldenAlsoMerges(unittest.TestCase):
    """Sister case: Hans Goldgulden — Bruun-3840 (year-fixed to 1496) +
    Numista-355730 (1481-1513). Different Friedberg ref (Fr-4 not Fr-3)
    but same merge pathway."""

    def test_hans_goldgulden_merges_confidently(self):
        r = match_pair(BRUUN_HANS_GOLDGULDEN_POSTFIX, NUMISTA_HANS_GOLDGULDEN,
                       entity_id="danish_realm")
        self.assertEqual(
            r["decision"], "confident",
            f"Hans Goldgulden merge: Bruun-3840 (Fr-4) + Numista-355730 "
            f"(Fr-4). Got {r['decision']}, primary={r['primary']}, "
            f"why={r['why']}"
        )

    def test_hans_goldgulden_nominal_collapses(self):
        """«1 Goldgulden (Rhinsk Gulden)» vs «1 Goldgulden» — both Fr-4, the
        SAME coin; the «(Rhinsk Gulden)» is a clarifying gloss, not a
        distinguishing denomination. Since 2026-06 normalise_nominal strips
        parenthetical glosses, so the two now collapse to one form (and the
        merge no longer depends on the catalog signal to rescue an advisory
        nominal mismatch). Note: the DISTINGUISHING bare forms «Ungersk Gylden»
        vs «Rhinsk Gylden» (no parens) stay distinct — see
        test_nominal_normalisation.TestContaminationStaysDistinct."""
        from lib.nominal_synonyms import normalise_nominal
        a = normalise_nominal("1 Goldgulden (Rhinsk Gulden)")
        b = normalise_nominal("1 Goldgulden")
        self.assertEqual(a, b)
        # And the end-to-end merge stays confident (catalog Fr-4 + now nominal).
        r = match_pair(BRUUN_HANS_GOLDGULDEN_POSTFIX, NUMISTA_HANS_GOLDGULDEN,
                       entity_id="danish_realm")
        self.assertEqual(r["decision"], "confident",
                         f"Hans Goldgulden merge should stay confident: got {r['decision']}")


class TestRegressionGuards(unittest.TestCase):
    """Ensure the fixes don't accidentally collapse unrelated types."""

    def test_one_noble_vs_two_nobles_still_no_match(self):
        """1 Noble ≠ 2 Nobles even with all fixes."""
        one = dict(NUMISTA_HANS_NOBEL)
        two = dict(NUMISTA_HANS_NOBEL,
                   id="dk-numista-428886",
                   nominal="2 Nobles",
                   year_first=1502, year_last=1502,
                   catalog={"numista": "428886", "fr": "2"},
                   weight_rough_g=29.5)
        r = match_pair(one, two, entity_id="danish_realm")
        self.assertEqual(r["decision"], "no_match",
                         f"1 Noble vs 2 Nobles must stay distinct. Got: "
                         f"{r['decision']}, why={r['why']}")

    def test_one_noble_vs_three_nobles_still_no_match(self):
        """1 Noble ≠ 3 Nobles."""
        one = dict(NUMISTA_HANS_NOBEL)
        three = dict(NUMISTA_HANS_NOBEL,
                     id="dk-numista-428914",
                     nominal="3 Nobles",
                     catalog={"numista": "428914", "fr": "1"},
                     weight_rough_g=44.5)
        r = match_pair(one, three, entity_id="danish_realm")
        self.assertEqual(r["decision"], "no_match")


if __name__ == "__main__":
    unittest.main(verbosity=2)
