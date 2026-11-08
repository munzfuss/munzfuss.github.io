"""verify_reflow.orphaned: a seed that was in a final, is still in a
seed_unified class, and is in no final now is a loss — unless the curator
excluded it or a member of its class (2026-11-07: Hede 6 folded into the
seedless foundation km-733-chr-v-1842, whose exclusion dropped the coin)."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "maintenance"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from verify_reflow import orphaned  # noqa: E402

WAS = {"dk-hede-c8h6": ("danish_realm", "c-58969558", "18_5_thaler"),
       "dk-tid-70755": ("danish_realm", "c-58969558", "18_5_thaler")}
UNI = {"c-58969558": ["dk-hede-c8h6", "dk-tid-70755"]}


class SeedOrphans(unittest.TestCase):
    def test_foundation_exclusion_trap_is_a_loss(self):
        out = orphaned(WAS, {}, UNI, {"km-733-chr-v-1842"})
        self.assertEqual(len(out), 1)
        self.assertIn("SEED ORPHANED", out[0])

    def test_still_in_a_final_is_fine(self):
        now = {k: ("royal_holstein", "c-58969558", "18_5_thaler") for k in WAS}
        self.assertEqual(orphaned(WAS, now, UNI, set()), [])

    def test_curator_excluded_member_excuses_the_class(self):
        self.assertEqual(orphaned(WAS, {}, UNI, {"dk-tid-70755"}), [])

    def test_seed_that_left_the_corpus_is_not_ours(self):
        self.assertEqual(orphaned(WAS, {}, {}, set()), [])


if __name__ == "__main__":
    unittest.main()
