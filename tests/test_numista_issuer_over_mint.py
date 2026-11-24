"""A state that had its coin struck at another state's mint is the issuer
(`build_numista_seed._resolve_default_entity`, `_ISSUER_OVER_MINT`, 2026-11-24)."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "maintenance"))
import build_numista_seed as bns  # noqa: E402


def _ent(issuer, mint, year):
    return bns._resolve_default_entity({"issuer": issuer, "mint": mint, "year_first": year})


class TestIssuerOverMint(unittest.TestCase):
    def test_plon_at_rethwisch_and_hamburg(self):
        iss = "Schleswig-Holstein-Norburg-Plön, Duchy of"
        self.assertEqual(_ent(iss, "Rethwisch", 1761), "norburg_plon_duchy")   # N#41864
        self.assertEqual(_ent(iss, "Hamburg Mint", 1760), "norburg_plon_duchy")  # N#222051

    def test_gottorp_at_hamburg(self):
        self.assertEqual(_ent("Schleswig-Holstein-Gottorp, Duchy of", "Hamburg Mint", 1673),
                         "gottorp_duchy")  # N#313829

    def test_bremen_at_hamburg(self):
        self.assertEqual(_ent("City of Bremen", "Hamburg Mint (Hamburgische Münze)", 1904),
                         "hanseatic_bremen")  # N#20410

    def test_crown_issuer_still_follows_mint(self):
        # one sovereign, several territories: the mint decides, as before
        self.assertEqual(_ent("Denmark", "Altona, Schleswig-Holstein", 1796), "royal_holstein")
        self.assertEqual(_ent("Denmark", "Copenhagen", 1796), "danish_realm")


if __name__ == "__main__":
    unittest.main()
