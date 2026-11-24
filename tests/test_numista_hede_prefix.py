"""Numista Hede references printed with the ruler volume and a dot before the
sub-letter («C4 80.C», N#307035) reduce to the bare number every other source
gives («80C»); a prefix naming another king is left as printed."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "maintenance"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from build_numista_seed import _filter_catalog, _normalise_hede_value  # noqa: E402
from lib.seed_merge import merge_one  # noqa: E402


class HedePrefixTest(unittest.TestCase):
    def test_ruler_prefix_and_dot(self):
        self.assertEqual(_normalise_hede_value("C4 80.C", "Christian IV"), "80C")

    def test_other_king_left_as_printed(self):
        self.assertEqual(_normalise_hede_value("C4 80.C", "Frederik III"), "C4 80.C")

    def test_dot_without_prefix(self):
        self.assertEqual(_normalise_hede_value("80.c"), "80C")

    def test_plain_values_untouched(self):
        for v in ("5", "39A", "39A-39G", "71A-71C"):
            self.assertEqual(_normalise_hede_value(v, "Christian IV"), v)

    def test_list(self):
        self.assertEqual(_normalise_hede_value(["C4 80.C", "80C"], "Christian IV"), ["80C"])

    def test_through_filter_catalog(self):
        self.assertEqual(_filter_catalog({"km": "A40.2", "hede": "C4 80.C"}, "Christian IV"),
                         {"km": "A40.2", "hede": "80C"})


class SeedMergeDropsStalePrefixedTest(unittest.TestCase):
    """A re-seed must replace the stale «C4 80.C» by «80C», not union them."""

    def _merge(self, existing_hede, fresh_hede):
        existing = {"id": "x", "catalog": {"hede": existing_hede}}
        fresh = {"id": "x", "catalog": {"hede": fresh_hede}}
        return merge_one(existing, fresh)["catalog"]["hede"]

    def test_stale_prefixed_dropped(self):
        self.assertEqual(self._merge("C4 80.C", "80C"), "80C")

    def test_other_values_still_accumulate(self):
        self.assertCountEqual(self._merge("C4 80.C", "81C"), ["C4 80.C", "81C"])


if __name__ == "__main__":
    unittest.main()
