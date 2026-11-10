"""verify_reflow: the retired Bruun anchor (catalog.bruun_part / bruun_lot_no
/ bruun_page) is no catalogue index — a baseline that still carries it and a
tree without it is not a loss (curator 2026-11-10). It replaces the
2026-10-24 «anchor moved between cited lots» excuse: the anchor is gone."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "maintenance"))

import verify_reflow as vr  # noqa: E402


class RetiredAnchor(unittest.TestCase):
    def test_retired_keys_are_not_registers(self):
        coin = {"catalog": {"bruun_part": "II", "bruun_lot_no": 13153, "bruun_page": 112,
                            "hede": "68A", "bruun_collection_id": "6435"}}
        regs = vr._catalog_registers(coin)
        for k in ("bruun_part", "bruun_lot_no", "bruun_page"):
            self.assertNotIn(k, regs)
        self.assertEqual(regs["hede"], {"68A"})
        self.assertIn("bruun_collection_id", regs)


if __name__ == "__main__":
    unittest.main()
