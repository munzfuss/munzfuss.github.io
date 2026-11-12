"""Galster hollow pennies take their nominal from danskmoent's denomination
pages (curator 2026-11-02).

«Hulpenning» names the form, not the value. A type listed only on «1 Penning»
(1penning.htm) becomes «1 Penning»; Galster 79 is listed on both «1 Penning»
and «Blaffert» (blaflybs.htm), so it stays «1 Hulpenning» with both lines as
alternatives. Live cache test: reads scripts/cache.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "maintenance"))

import build_galster_denmark_seed as b  # noqa: E402


def _nominal(source_file, vol, n, nominal="Hulpenning"):
    return b._hollow_penny_nominal(
        {"source_file": source_file, "ruler_volume": vol, "galster_number": n}, nominal)


@unittest.skipUnless((b.GALSTER_CACHE / "1penning.htm").exists(), "harvest cache (scripts/cache submodule) not attached")
class HollowPennyNominal(unittest.TestCase):
    def test_listed_as_penning(self):
        self.assertEqual(_nominal("fr_f1g129.htm", "f1g", "129"), ("1 Penning", None))
        self.assertEqual(_nominal("epomg5.htm", "epomg", "5"), ("1 Penning", None))
        # unlinked line, matched by «Galster 156» under Hans
        self.assertEqual(_nominal("hansgals.htm", "hg", "156"), ("1 Penning", None))

    def test_listed_as_penning_and_blaffert(self):
        nominal, alts = _nominal("fr_f1g79.htm", "f1g", "79", "Hulpenning; Blaffert")
        self.assertEqual(nominal, "1 Hulpenning")
        self.assertEqual({a[0] for a in alts}, {"1 Penning", "1 Blaffert"})

    def test_other_nominals_untouched(self):
        self.assertEqual(_nominal("fr_f1g128.htm", "f1g", "128", "Blaffert"), ("Blaffert", None))


if __name__ == "__main__":
    unittest.main()
