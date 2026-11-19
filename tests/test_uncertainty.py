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


class HeldFieldKeepsItsEntry(unittest.TestCase):
    def test_entry_explaining_a_frozen_field_survives_regen(self):
        from lib.seed_merge import merge_one
        from ruamel.yaml.comments import CommentedMap
        existing = CommentedMap({
            "id": "dk-bruun-3839", "fineness": 0.739583,
            "_curation_holds": ["fineness", "fineness_verified"],
            "uncertainty": {"fineness": [U.make("standard", "standard", value="17¾ Karat")],
                            "year": [U.make("circa", "bruun", value="1497")]}})
        fresh = {"id": "dk-bruun-3839", "fineness": None,
                 "uncertainty": {"year": [U.make("circa", "bruun", value="1496-1497")]}}
        out = merge_one(existing, fresh)
        self.assertEqual(out["uncertainty"]["fineness"][0]["how"], "standard")
        self.assertEqual(out["uncertainty"]["year"][0]["value"], "1496-1497")


class GalsterPrinted(unittest.TestCase):
    def test_dating_phrase_is_verbatim(self):
        import build_galster_denmark_seed as G
        d = {"raw_text_excerpt": "## Søren Norby, Skilling, Visby\n\nU.år (1523?). Forside"}
        self.assertEqual(G._printed_dating(d), ("query", "U.år (1523?)"))
        d = {"raw_text_excerpt": "## Hvid, Ribe, ca. 1380\n"}
        self.assertEqual(G._printed_dating(d), ("circa", "ca. 1380"))
        d = {"raw_text_excerpt": "Søsling u. år (1440-1442), Lund"}
        self.assertEqual(G._printed_dating(d), ("attributed", "u. år (1440-1442)"))
        d = {"raw_text_excerpt": "Søsling(?) (klipping), u. år (1531-32)?\n"}
        self.assertEqual(G._printed_dating(d), ("query", "u. år (1531-32)?"))


class BruunPrinted(unittest.TestCase):
    def test_nd_text(self):
        import build_bruun_denmark_seed as B
        self.assertEqual(B.nd_printed({"meta_line": "DENMARK. Goldgulden, ND (ca. 1496-97). Hans."}),
                         ("circa", "ND (ca. 1496-97)"))
        self.assertEqual(B.nd_printed({"meta_line": "Klippe, ND (1607-11). Christian IV."}),
                         ("attributed", "ND (1607-11)"))


class PlainDating(unittest.TestCase):
    """«(?)» only when the source itself hedges the year (curator 2026-11-19);
    a plain dating of an undated coin is a known year."""

    def test_plain_and_hedged(self):
        for s in ("ND (1670)", "U.år (1611)", "ND (1481-1512)", "(1616-59)",
                  "u. år (1440-1442)", "ND(1618-22)", "U.år (1661) (RRR)"):
            self.assertTrue(U.plain_dating(s), s)
        for s in ("ND (ca. 1496-97)", "ND (c. 1400)", "ND (1669-70?)", "(ca1565)",
                  "ND(ca1640)", "U.år (1609 (Hede) eller 1611 (Harck))",
                  "1373/77—96", "u. år (1531-32)?", "efter reces 1424", None, ""):
            self.assertFalse(U.plain_dating(s), s)

    def test_roman_date_is_a_dated_coin(self):
        self.assertTrue(U.roman_dated("MDCCLX (1760) G"))
        self.assertFalse(U.roman_dated("(1616-59)"))
        import parse_ngc
        out = parse_ngc.parse_years({"dates": [{"year_mint": "MDCCII (1702)"}]})
        self.assertNotIn("year_attributed", out)
        self.assertTrue(parse_ngc.parse_years(
            {"dates": [{"year_mint": "(1618-22)"}]}).get("year_attributed"))


if __name__ == "__main__":
    unittest.main()
