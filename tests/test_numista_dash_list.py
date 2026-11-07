"""Numista multi-number references joined by spaced dashes become a list;
a single spaced dash is a range and stays as printed."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "maintenance"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from build_numista_seed import _filter_catalog  # noqa: E402


class DashListTest(unittest.TestCase):
    def test_list_of_four(self):
        self.assertEqual(_filter_catalog({"lange": "69 - 70a - 71a - 73a"})["lange"],
                         ["69", "70a", "71a", "73a"])

    def test_single_dash_is_range(self):
        self.assertEqual(_filter_catalog({"lange": "21 - 22"})["lange"], "21 - 22")

    def test_unspaced_range_untouched(self):
        self.assertEqual(_filter_catalog({"lange": ["48-51", "51A"]})["lange"], ["48-51", "51A"])

    def test_list_member_split(self):
        self.assertEqual(_filter_catalog({"lange": ["1 - 2 - 3", "4"]})["lange"], ["1", "2", "3", "4"])


if __name__ == "__main__":
    unittest.main()
