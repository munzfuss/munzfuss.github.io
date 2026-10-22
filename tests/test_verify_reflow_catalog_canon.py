"""verify_reflow compares `catalog.others` through catalog_codes'
canonicalisation, so a spelling change there is not a lost index
(2026-10-22: «Ernst# 1940 3-13» → «Ernst 1940# 3-13»)."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "maintenance"))

import verify_reflow as vr  # noqa: E402


class OthersCanonTest(unittest.TestCase):
    def test_old_and_new_ernst_spelling_compare_equal(self):
        old = vr._catalog_registers({"catalog": {"others": ["Ernst# 1940 3-13", "B# 68"]}})
        new = vr._catalog_registers({"catalog": {"others": ["Ernst 1940# 3-13", "B# 68"]}})
        self.assertEqual(old, new)

    def test_real_drop_still_visible(self):
        old = vr._catalog_registers({"catalog": {"others": ["Ernst# 1940 22-23", "B# 68"]}})
        new = vr._catalog_registers({"catalog": {"others": ["B# 68"]}})
        self.assertEqual(old["others"] - new["others"], {"ERNST 1940# 22-23"})


if __name__ == "__main__":
    unittest.main()
