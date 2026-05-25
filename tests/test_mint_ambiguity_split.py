"""TDD test for mint ambiguity-marker splitting in seed-writer hygiene.

Function under test (indirectly):
    scripts/lib/v2_seed_writer.py :: _apply_pre_write_hygiene

When a seed source documents uncertainty between candidate mints via
language markers («København eller Malmö», «Copenhagen or Malmö»,
«Hamburg/Altona», «Berlin oder Frankfurt»), the seed builder should:
  1. Split the mint string into list-form
  2. Canonicalise each token (Copenhagen → Kopenhagen etc.)
  3. Set mint_verified=False so the (?) marker renders

Real case: dk-galster-f1g-45 (Frederik I Nobel 1532) — Galster
documents «København eller Malmö» (cataloguer uncertain between two
mints). Pre-fix: scalar string stored verbatim, rendered as raw text.
Post-fix: list-form ['Kopenhagen', 'Malmö'] + mint_verified=False →
(?) marker renders in table.

Run via:
    .venv/bin/python -m unittest tests.test_mint_ambiguity_split -v
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

import importlib.util
_spec = importlib.util.spec_from_file_location(
    "v2_seed_writer",
    str(PROJECT_ROOT / "scripts" / "lib" / "v2_seed_writer.py"),
)
_w = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_w)
_apply_pre_write_hygiene = _w._apply_pre_write_hygiene


def coin(**fields):
    base = {
        "id": "test",
        "nominal": "Test denom",
        "issuing_entity": "danish_realm",
        "metal": "gold",
    }
    base.update(fields)
    return base


class TestDanishEllerMarker(unittest.TestCase):
    """Real Galster pattern: «X eller Y»."""

    def test_kobenhavn_eller_malmo_splits(self):
        """The actual dk-galster-f1g-45 case."""
        c = coin(mint="København eller Malmø", mint_verified=True)
        result, _ = _apply_pre_write_hygiene([c])
        self.assertIsInstance(result[0]["mint"], list)
        self.assertIn("Kopenhagen", result[0]["mint"])
        self.assertIn("Malmö", result[0]["mint"])
        self.assertFalse(result[0]["mint_verified"],
                         "Ambiguous source mint must set mint_verified=False")

    def test_glykstad_eller_altona(self):
        """SH mint case."""
        c = coin(mint="Glückstadt eller Altona")
        result, _ = _apply_pre_write_hygiene([c])
        self.assertIsInstance(result[0]["mint"], list)
        self.assertEqual(set(result[0]["mint"]), {"Glückstadt", "Altona"})
        self.assertFalse(result[0]["mint_verified"])


class TestEnglishOrMarker(unittest.TestCase):
    """Bruun PDF + English sources use «or»."""

    def test_copenhagen_or_malmo(self):
        c = coin(mint="Copenhagen or Malmø")
        result, _ = _apply_pre_write_hygiene([c])
        self.assertEqual(set(result[0]["mint"]), {"Kopenhagen", "Malmö"})
        self.assertFalse(result[0]["mint_verified"])

    def test_copenhagen_mint_or_malmo(self):
        """Bruun-form with «Mint» suffix."""
        c = coin(mint="Copenhagen Mint or Malmø")
        result, _ = _apply_pre_write_hygiene([c])
        # Canonical form drops «Mint» suffix
        self.assertEqual(set(result[0]["mint"]),
                         {"Kopenhagen", "Malmö"})
        self.assertFalse(result[0]["mint_verified"])


class TestGermanOderMarker(unittest.TestCase):
    """German «oder»."""

    def test_glykstad_oder_altona(self):
        """German Holstein-mint split case."""
        c = coin(mint="Glückstadt oder Altona")
        result, _ = _apply_pre_write_hygiene([c])
        self.assertEqual(set(result[0]["mint"]), {"Glückstadt", "Altona"})
        self.assertFalse(result[0]["mint_verified"])


class TestSlashSeparator(unittest.TestCase):
    """«X/Y» slash form."""

    def test_kobenhavn_slash_malmo(self):
        c = coin(mint="København/Malmø")
        result, _ = _apply_pre_write_hygiene([c])
        self.assertEqual(set(result[0]["mint"]), {"Kopenhagen", "Malmö"})
        self.assertFalse(result[0]["mint_verified"])

    def test_glykstad_slash_altona(self):
        c = coin(mint="Glückstadt / Altona")
        result, _ = _apply_pre_write_hygiene([c])
        self.assertEqual(set(result[0]["mint"]), {"Glückstadt", "Altona"})
        self.assertFalse(result[0]["mint_verified"])


class TestPreservesVerifiedMints(unittest.TestCase):
    """Single-mint strings shouldn't be touched."""

    def test_single_kobenhavn_stays_verified(self):
        c = coin(mint="København", mint_verified=True)
        result, _ = _apply_pre_write_hygiene([c])
        # Canonical: Kopenhagen
        self.assertEqual(result[0]["mint"], "Kopenhagen")
        self.assertTrue(result[0]["mint_verified"])

    def test_single_copenhagen_stays_verified(self):
        c = coin(mint="Copenhagen", mint_verified=True)
        result, _ = _apply_pre_write_hygiene([c])
        self.assertEqual(result[0]["mint"], "Kopenhagen")
        self.assertTrue(result[0]["mint_verified"])


class TestJointMintsListUntouched(unittest.TestCase):
    """Already-list-form mints (genuine joint coinage, not ambiguity)
    should pass through canonical without ambiguity flag."""

    def test_already_list_form(self):
        c = coin(mint=["Altona", "Kopenhagen"], mint_verified=True)
        result, _ = _apply_pre_write_hygiene([c])
        self.assertEqual(set(result[0]["mint"]), {"Altona", "Kopenhagen"})
        # NOT flagged as ambiguous — list-form is intentional joint-mint signal
        self.assertTrue(result[0]["mint_verified"])


class TestNonAmbiguousWordsNotTriggering(unittest.TestCase):
    """Words that contain «or» as substring must not falsely split."""

    def test_gottorp_not_split(self):
        """«Gottorp» contains «or» but as substring of the mint name —
        word-boundary regex protects this."""
        c = coin(mint="Gottorp", mint_verified=True)
        result, _ = _apply_pre_write_hygiene([c])
        self.assertEqual(result[0]["mint"], "Gottorp")
        self.assertTrue(result[0]["mint_verified"])

    def test_borkum_not_split(self):
        """Hypothetical mint name containing «or» as substring."""
        c = coin(mint="Norburg", mint_verified=True)
        result, _ = _apply_pre_write_hygiene([c])
        # Norburg passes through as-is (not in canonical aliases, so kept)
        self.assertEqual(result[0]["mint"], "Norburg")
        self.assertTrue(result[0]["mint_verified"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
