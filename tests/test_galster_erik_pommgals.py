"""Erik af Pommern in the Galster seed (2026-10-26).

- pommgals.htm («oversigt efter Galster») is the only record of Galster 6, 8
  and 12: their numbers link the halvpenn.htm / lebard.htm overviews, not a
  coin page. Each becomes a coin, dated and minted from its erikpomm.htm line.
- Galster 11 (philsosl.htm, «Dronning Philippas søsling») reads Søsling, Erik
  VII, u.år (1424).
- Coins of Erik VII after 1439 go to `erik_gotland`, which the Denmark page
  does not consume (curator: «монети еріка коли він вже не був королем не
  повинні бути на сторінці данії») — Galster 138, «ERIC GOTOR REX», c. 1448.
Live cache test for the parser part: reads scripts/cache.
"""
from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from lib.galster_parsers import galst_table  # noqa: E402
from lib.mint_registry import erik_gotland_entity  # noqa: E402
from lib.paths import GALSTER_CACHE  # noqa: E402


class ErikAfterDeposition(unittest.TestCase):
    def test_after_1439_moves(self):
        self.assertEqual(erik_gotland_entity("danish_realm", "Erik VII", 1448), "erik_gotland")

    def test_reign_and_undated_stay(self):
        self.assertEqual(erik_gotland_entity("danish_realm", "Erik VII", 1439), "danish_realm")
        self.assertEqual(erik_gotland_entity("danish_realm", "Erik VII", None), "danish_realm")

    def test_other_rulers_and_entities_stay(self):
        self.assertEqual(erik_gotland_entity("danish_realm", "Erik XIV", 1562), "danish_realm")
        self.assertEqual(erik_gotland_entity("sweden", "Erik VII", 1448), "sweden")


class PommgalsRows(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        html = (GALSTER_CACHE / "pommgals.htm").read_text(encoding="utf-8", errors="replace")
        cls.rows = {c["galster_number"]: c for c in galst_table.parse_coins(html, "pommgals.htm")}

    def test_overview_linked_numbers_are_rows(self):
        self.assertTrue({"6", "8", "12"} <= set(self.rows))
        self.assertNotIn("11", self.rows)          # philsosl.htm is its page
        self.assertNotIn("2", self.rows)           # epomg2.htm

    def test_dating_and_mint_from_reign_page(self):
        r = self.rows["6"]
        self.assertEqual((r["year_label"], r["mint"], r.get("year_approx")),
                         ("1400-1420", "Næstved", True))
        self.assertEqual((self.rows["12"]["year_label"], self.rows["12"]["mint"]), ("1424", "Lund"))

    def test_only_the_danish_table(self):
        self.assertFalse(any(int(n) > 100 for n in self.rows))


class PhilippaSosling(unittest.TestCase):
    def test_parse(self):
        d = json.loads((GALSTER_CACHE / "philsosl.json").read_text(encoding="utf-8"))
        self.assertEqual((d["ruler"], d["denomination"], d["year_label"], d["year_hint"],
                          d["galster_number"]),
                         ("Erik VII", "Søsling", "u.år", "1424", "11"))


if __name__ == "__main__":
    unittest.main()
