"""ucoin `mint_text` → (mint, mint_verified).

«Mintage» / «Mark» are table headers the harvest read off the page; they are not
mints. «Clausthal-Zellerfeld» is a real string but an imprecise attribution —
the 1924 merger of two mints that worked side by side — so it is kept verbatim
and marked unverified, letting a museum record naming the actual mint win a
merge instead of standing beside it as a second mint.
"""
from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "maintenance"))

_spec = importlib.util.spec_from_file_location(
    "build_ucoin_seed_for_test", ROOT / "scripts" / "maintenance" / "build_ucoin_seed.py")
bus = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(bus)


class UcoinMintText(unittest.TestCase):
    def test_page_headers_are_not_mints(self):
        for raw in ("Mintage", "Mark", "Mark\tMintage"):
            self.assertEqual(bus._ucoin_mint({"mint_text": raw}), (None, False))

    def test_imprecise_town_kept_unverified(self):
        self.assertEqual(bus._ucoin_mint({"mint_text": "Clausthal-Zellerfeld"}),
                         ("Clausthal-Zellerfeld", False))
        self.assertEqual(bus._ucoin_mint({"mint_text": "Clausthal-Zellerfeld (Germany)"}),
                         ("Clausthal-Zellerfeld (Germany)", False))

    def test_ordinary_mint_verified(self):
        self.assertEqual(bus._ucoin_mint({"mint_text": "Eversburg"}), ("Eversburg", True))
        self.assertEqual(bus._ucoin_mint({"mint_text": "Zellerfeld"}), ("Zellerfeld", True))

    def test_absent(self):
        self.assertEqual(bus._ucoin_mint({}), (None, False))


if __name__ == "__main__":
    unittest.main()
