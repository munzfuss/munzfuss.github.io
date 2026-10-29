"""Coin.uncertainty — how and by whom a value is uncertain (curator 2026-10-29,
docs/plans/uncertainty_markers.md): entries built per source, unioned across
members without losing any, and the source's own text kept verbatim."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "maintenance"))

from lib import uncertainty as U  # noqa: E402
from lib.schema import Coin  # noqa: E402


class Entries(unittest.TestCase):
    def test_kind_follows_basis(self):
        self.assertEqual(U.make("circa", "bruun")["kind"], "hedged")
        self.assertEqual(U.make("reign", "hede")["kind"], "inferred")
        with self.assertRaises(ValueError):
            U.make("guess", "x")

    def test_union_keeps_every_source_and_range(self):
        a = U.add({"id": "dk-bruun-1"}, "year", "circa", "bruun",
                  as_printed="ND (ca. 1496-97)", value="1496-1497")
        b = U.add({"id": "ngc-2"}, "year", "attributed", "ngc",
                  as_printed="(1495-98)", value="1495-1498")
        c = U.add({"id": "dk-hede-c1"}, "year", "reign", "hede", value="1481-1513")
        u = U.union([a, b, c, a])
        self.assertEqual([(e["seed"], e["value"]) for e in u["year"]],
                         [("dk-bruun-1", "1496-1497"), ("ngc-2", "1495-1498"),
                          ("dk-hede-c1", "1481-1513")])

    def test_schema_accepts_entries(self):
        e = U.add({}, "mint", "alternatives", "hede",
                  as_printed="København eller Malmø", value="København, Malmø")
        Coin.model_validate({"id": "x", "fuss": "seed_unsorted", "phase": "A",
                             "kind": "kurant", "nominal": "1 Skilling",
                             "metal": "silver", **e})


class GalsterPrinted(unittest.TestCase):
    def test_dating_phrase_is_verbatim(self):
        import build_galster_denmark_seed as G
        d = {"raw_text_excerpt": "## Søren Norby, Skilling, Visby\n\nU.år (1523?). Forside"}
        self.assertEqual(G._printed_dating(d), ("query", "U.år (1523?)"))
        d = {"raw_text_excerpt": "## Hvid, Ribe, ca. 1380\n"}
        self.assertEqual(G._printed_dating(d), ("circa", "ca. 1380"))
        d = {"raw_text_excerpt": "Søsling u. år (1440-1442), Lund"}
        self.assertEqual(G._printed_dating(d), ("attributed", "u. år (1440-1442)"))


class BruunPrinted(unittest.TestCase):
    def test_nd_text(self):
        import build_bruun_denmark_seed as B
        self.assertEqual(B.nd_printed({"meta_line": "DENMARK. Goldgulden, ND (ca. 1496-97). Hans."}),
                         ("circa", "ND (ca. 1496-97)"))
        self.assertEqual(B.nd_printed({"meta_line": "Klippe, ND (1607-11). Christian IV."}),
                         ("attributed", "ND (1607-11)"))


if __name__ == "__main__":
    unittest.main()
