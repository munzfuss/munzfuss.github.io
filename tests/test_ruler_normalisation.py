"""TDD test for `_normalise_ruler` — extended with cross-language ruler
synonyms.

Function under test:
    scripts/maintenance/merge_seeds_cross_source.py :: _normalise_ruler

Different sources use English vs Danish/Norwegian forms for the same
monarch — without synonymisation, the cross-source matcher fragments
identical types:

  Numista (English):    «John I (Hans I)» / «John II» / «Eric of Pomerania»
  Bruun, Hede, Galster: «Hans» / «Erik» / «Margrethe»
  English / German:     «Margaret»

Canonical form is the Danish (matches Hede/Galster/our project YAML).

Test cases harvested from real V2 seed entries:
  - Hans of Denmark (Numista «John I (Hans I)» vs Bruun «Hans»)
    [confirmed regression case for Bruun-3831 + Numista-420401 merge]
  - Erik VII of Pomerania (Bruun «Erik of Pomerania» vs hypothetical
    Numista «Eric»)

Run via:
    .venv/bin/python -m unittest tests.test_ruler_normalisation -v
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
_normalise_ruler = _merger._normalise_ruler


class TestHansSynonyms(unittest.TestCase):
    """Hans of Denmark (1455-1513, reigned 1481-1513) — English name John I,
    Danish/Norwegian Hans / Johann."""

    def test_hans_bare(self):
        self.assertEqual(_normalise_ruler("Hans"), "hans")

    def test_john_i_canonicalises_to_hans(self):
        self.assertEqual(_normalise_ruler("John I"), "hans")

    def test_john_i_hans_i_paren_canonicalises_to_hans(self):
        """Real Numista format: «John I (Hans I)»."""
        self.assertEqual(_normalise_ruler("John I (Hans I)"), "hans")

    def test_john_ii_also_hans(self):
        """Some Swedish-side sources call Hans «John II» (Kalmar Union)."""
        self.assertEqual(_normalise_ruler("John II"), "hans")

    def test_bruun_hans_equals_numista_john_i(self):
        """The critical cross-source check — Bruun-3831 «Hans» must
        normalise identically to Numista-420401 «John I (Hans I)»."""
        self.assertEqual(
            _normalise_ruler("Hans"),
            _normalise_ruler("John I (Hans I)")
        )


class TestErikSynonyms(unittest.TestCase):
    """Erik / Eric — common cross-language spelling variant."""

    def test_erik_vii_unchanged(self):
        self.assertEqual(_normalise_ruler("Erik VII"), "erik vii")

    def test_eric_normalises_to_erik(self):
        self.assertEqual(_normalise_ruler("Eric"), "erik")

    def test_eric_vii_of_pomerania_normalises(self):
        """Numista shape: «Eric VII of Pomerania» → «erik vii» (after
        the existing «of/von» strip)."""
        self.assertEqual(
            _normalise_ruler("Eric VII of Pomerania"),
            _normalise_ruler("Erik VII")
        )


class TestMargrethelSynonyms(unittest.TestCase):
    """Margaret / Margrethe — Margrethe I (1387-1412), Margrethe II
    (modern Danish queen)."""

    def test_margrethe_unchanged(self):
        self.assertEqual(_normalise_ruler("Margrethe II"), "margrethe ii")

    def test_margaret_normalises_to_margrethe(self):
        self.assertEqual(_normalise_ruler("Margaret II"), "margrethe ii")


class TestFrederickExistingNormalisation(unittest.TestCase):
    """Pre-existing Frederick → Frederik (regression guards)."""

    def test_frederik_unchanged(self):
        self.assertEqual(_normalise_ruler("Frederik V"), "frederik v")

    def test_frederick_normalises(self):
        self.assertEqual(_normalise_ruler("Frederick V"), "frederik v")

    def test_bruun_frederik_equals_numista_frederick(self):
        """Real-world: Numista publishes «Frederick I» while Hede has
        «Frederik I»."""
        self.assertEqual(
            _normalise_ruler("Frederik I"),
            _normalise_ruler("Frederick I")
        )


class TestExistingFeaturesPreserved(unittest.TestCase):
    """Regression: pre-existing strip rules still work."""

    def test_drop_paren_reign_dates(self):
        self.assertEqual(_normalise_ruler("Christian IV. (1588-1648)"),
                         "christian iv")

    def test_drop_comma_epithet(self):
        self.assertEqual(_normalise_ruler("Christian VII, der wahnsinnige"),
                         "christian vii")

    def test_drop_issuer_bleed(self):
        self.assertEqual(_normalise_ruler("Christian VII Issuer: Danish realm"),
                         "christian vii")

    def test_drop_trailing_reign_years(self):
        self.assertEqual(_normalise_ruler("Frederik IV 1699 - 1730"),
                         "frederik iv")

    def test_drop_von_house(self):
        self.assertEqual(_normalise_ruler("Friedrich III. von Schleswig-Holstein-Gottorp"),
                         "friedrich iii")


class TestEdgeCases(unittest.TestCase):
    """Bounds."""

    def test_empty_returns_empty(self):
        self.assertEqual(_normalise_ruler(None), "")
        self.assertEqual(_normalise_ruler(""), "")

    def test_christian_no_synonym_swap(self):
        """Christian has no English variant — must not be mangled."""
        self.assertEqual(_normalise_ruler("Christian V"), "christian v")

    def test_unknown_ruler_passes_through(self):
        """Non-matched names go through lowercased."""
        self.assertEqual(_normalise_ruler("Some Unknown King"), "some unknown king")


if __name__ == "__main__":
    unittest.main(verbosity=2)
