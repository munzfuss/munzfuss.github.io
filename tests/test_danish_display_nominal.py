"""Danish display names of denominations on the Denmark page's entities
(`lib.nominal_synonyms.danish_display_nominal`).

- «Witten» → «Hvid», «Kobbersterling» → «Sterling» (curator 2026-10-26).
- «Lebard» → «Hulpenning»: the lebard is the hollow penny named for its
  leopard, Lindahl 1955 s. 82 «Hulpenning (lebard)» (curator 2026-11-02).
- Entities off the Denmark page keep the source's word.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from lib.nominal_synonyms import danish_display_nominal  # noqa: E402


class DanishDisplayNominal(unittest.TestCase):
    def test_denmark_page_entity(self):
        self.assertEqual(danish_display_nominal("1 Witten", "danish_realm"), "1 Hvid")
        self.assertEqual(danish_display_nominal("1 Kobbersterling", "danish_realm"), "1 Sterling")
        self.assertEqual(danish_display_nominal("1 Lebard", "danish_realm"), "1 Hulpenning")

    def test_other_entity_keeps_the_source_word(self):
        self.assertEqual(danish_display_nominal("1 Lebard", "hanseatic_lubeck"), "1 Lebard")
        self.assertEqual(danish_display_nominal("1 Witten", "hanseatic_lubeck"), "1 Witten")


if __name__ == "__main__":
    unittest.main()
