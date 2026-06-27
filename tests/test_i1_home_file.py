"""Regression guard for the I1 home-file audit rule (audit_v2.check_i1_home_file).

WHY THIS EXISTS — the I1 audit originally hard-coded an alphabetical-first
home-file rule (`sorted(issuing_entity)[0] == filename`). The live seed-writer
(`lib.v2_seed_writer._home_entity`) had since moved to an OVERLAP-PRIORITY rule:
a coin whose `issuing_entity` contains `royal_holstein` (the SH∩Denmark overlap
entity) homes to `royal_holstein.yml` so BOTH the schleswig_holstein and denmark
location pages pick it up via the robust file-based Pass-1 assembly — NOT
alphabetical-first (which would file an `[danish_realm, royal_holstein]` coin
under danish_realm.yml, recoverable on the SH page only via the fragile Pass-2
intersection). The audit drifted from the writer and flagged ~39 correctly-placed
coins (caught 2026-06-27, user-confirmed: royal_holstein placement is correct).

The fix imports `_home_entity` into the audit so the two can NEVER drift. These
tests pin both halves:
  - the audit accepts a [danish_realm, royal_holstein] coin in royal_holstein.yml;
  - the audit rejects the same coin in danish_realm.yml;
  - every live final + seed_unified coin passes (the data is 100% conformant).

Run via:
    .venv/bin/python -m unittest tests.test_i1_home_file -v
"""
from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
_spec = importlib.util.spec_from_file_location(
    "audit_v2", str(ROOT / "scripts" / "audit_v2.py"))
_A = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_A)


class TestOverlapPriority(unittest.TestCase):
    def test_royal_holstein_overlap_homes_to_royal_holstein(self):
        coin = {"id": "x", "issuing_entity": ["danish_realm", "royal_holstein"]}
        # Correct placement: royal_holstein.yml (overlap-priority, NOT
        # alphabetical-first danish_realm).
        self.assertEqual(_A.check_i1_home_file([("royal_holstein", coin)], set()), [])

    def test_royal_holstein_overlap_rejected_in_danish_realm(self):
        coin = {"id": "x", "issuing_entity": ["danish_realm", "royal_holstein"]}
        errs = _A.check_i1_home_file([("danish_realm", coin)], set())
        self.assertTrue(errs)
        self.assertIn("royal_holstein.yml", errs[0])

    def test_danish_norway_royal_holstein_homes_to_royal_holstein(self):
        coin = {"id": "x", "issuing_entity": ["danish_norway", "royal_holstein"]}
        self.assertEqual(_A.check_i1_home_file([("royal_holstein", coin)], set()), [])

    def test_plain_pair_falls_back_to_alphabetical_first(self):
        # No overlap entity → alphabetical-first still applies.
        coin = {"id": "x", "issuing_entity": ["bremen_verden", "oldenburg"]}
        self.assertEqual(_A.check_i1_home_file([("bremen_verden", coin)], set()), [])
        self.assertTrue(_A.check_i1_home_file([("oldenburg", coin)], set()))

    def test_scalar_issuing_entity(self):
        coin = {"id": "x", "issuing_entity": "lubeck"}
        self.assertEqual(_A.check_i1_home_file([("lubeck", coin)], set()), [])
        self.assertTrue(_A.check_i1_home_file([("hamburg", coin)], set()))

    def test_missing_and_empty_flagged(self):
        self.assertTrue(_A.check_i1_home_file(
            [("danish_realm", {"id": "x"})], set()))
        self.assertTrue(_A.check_i1_home_file(
            [("danish_realm", {"id": "x", "issuing_entity": []})], set()))


class TestLiveDataConformant(unittest.TestCase):
    def test_all_live_coins_pass_i1(self):
        coins = _A._all_v2_final_coins() + _A._all_v2_unified_coins()
        self.assertTrue(coins, "no V2 coins loaded")
        errs = _A.check_i1_home_file(coins, set())
        self.assertEqual(errs, [], f"{len(errs)} I1 violations: {errs[:5]}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
