"""Hede's «Lauenborg» section page (f6hl1) keys apart from the Danish Hede 1.

The page is cached as `f6hl1.htm` (fetch_hede.IRREGULAR_COIN_PAGES). Its
volume must be `f6hl`, so the aggregate index key is `f6hl1`, not `f6h1`
(which the Danish Hede 1 of Frederik VI owns), and the seed builder must read
the page's own number as «1», not «l1».
"""
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import parse_hede  # noqa: E402
import fetch_hede  # noqa: E402


class LauenborgVolume(unittest.TestCase):
    def test_volume(self):
        self.assertEqual(parse_hede._ruler_volume("f6hl1"), ("Frederik 6.", "f6hl"))

    def test_danish_pages_unchanged(self):
        self.assertEqual(parse_hede._ruler_volume("f6h1"), ("Frederik 6.", "f6h"))
        self.assertEqual(parse_hede._ruler_volume("nc5h42"), ("Christian 5.", "nc5h"))
        self.assertEqual(parse_hede._ruler_volume("f3h62ab"), ("Frederik 3.", "f3h"))

    def test_irregular_page_mapping(self):
        self.assertEqual(fetch_hede.IRREGULAR_COIN_PAGES.get("/lauenbor.htm"), "f6hl1.htm")

    def test_builder_key_regex(self):
        src = (ROOT / "scripts/maintenance/build_hede_denmark_seed.py").read_text(encoding="utf-8")
        pat = re.search(r're\.match\(r"(\^n\?\[cf\][^"]+)", composite_key\)', src).group(1)
        self.assertEqual(re.match(pat, "f6hl1").group(1), "1")
        self.assertEqual(re.match(pat, "c4h111").group(1), "111")
        self.assertEqual(re.match(pat, "f3h62ab").group(1), "62ab")


if __name__ == "__main__":
    unittest.main()
