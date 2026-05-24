"""TDD test for Bruun parser year extraction.

Function under test:
    scripts/bruun_parser/02_parse_lots.py :: extract_year(meta_line, body_match)

Two bugs this function guards against (both surfaced via Bruun-3831 audit,
2026-05-24):

  Bug 1 — pre-1500 YEAR_RE floor. The old pattern `r"\b(1[5-9]\d{2}|20\d{2})\b"`
          starts at 1500. Hans Nobel 1496, Hans Goldgulden 1481-1497, Erik VII
          Witten 1400 — all silently ignored. Parser fell through to whatever
          1500+ year appeared next (catalog reference, edition year).

  Bug 2 — catalog-year theft. With the old logic, `year` was the FIRST 4-digit
          year-shape in body_match[:600]. Body text typically carries refs like
          «Beskrivelsen 1791-pl.», «Bruun-1898», Hede-edition years. When the
          coin year (in meta_line) failed Bug 1, parser captured a ref-year.
          Fix: prioritise meta_line over body — the cataloguer's explicit
          dating in meta_line ALWAYS wins when present.

Test set is real-world: every pre-1500 lot in the live Bruun cache plus
all 8 lots that triggered «Beskrivelsen YYYY» risk, plus 8 post-1500
regression guards (correctly-parsed lots that must keep their year after
the fix). Total ~25 real cases + 8 synthetic edges.

Run via:
    .venv/bin/python -m unittest tests.test_bruun_year_extraction -v
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

# Import the function under test from the digit-prefixed module path
import importlib.util
_spec = importlib.util.spec_from_file_location(
    "bruun_parse_lots",
    str(PROJECT_ROOT / "scripts" / "bruun_parser" / "02_parse_lots.py"),
)
_parser = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_parser)
extract_year = _parser.extract_year


class TestPre1500MetaLineYear(unittest.TestCase):
    """Real lots from Bruun cache where meta_line carries a pre-1500 year.
    Old parser returned None or a catalog-year; new parser returns the
    actual coin year from meta_line."""

    def test_lot_1001_hans_nobel_1496(self):
        """part1 lot 1001 — the original audit case. Buggy year was 1791
        (taken from «Beskrivelsen 1791-pl.» in body)."""
        meta = "DENMARK. Noble, 1496. Malmö or Copenhagen Mint. Hans. NGC AU-55.  Fr-3; Galster-24; Sieg-12;"
        body = ("DENMARK. Noble, 1496. Malmö or Copenhagen Mint. Hans. NGC AU-55.  Fr-3; "
                "Galster-24; Sieg-12; Schou-2; Beskrivelsen 1791-pl. 1, 2; Schive-pl. XIV , 38; "
                "Bruun-3831. Weight: 14.67 gms. UNIQUE in private hands with only 2 in museums.")
        self.assertEqual(extract_year(meta, body), 1496)

    def test_lot_1002_hans_goldgulden_1496_1497(self):
        """part1 lot 1002 — Hans Goldgulden / Rhinsk Gulden ND (1496-1497).
        Buggy year was 1817 (some catalog ref)."""
        meta = "DENMARK. Goldgulden (Rhinsk Gulden), ND (ca. 1496-1497). Malmö or Copenhagen Mint. Hans."
        body = meta + " Galster-26; Sieg-7; Schou-13; Bruun-3840. Weight: 3.32 gms. Beskrivelsen 1817-pl. 1, 5."
        self.assertEqual(extract_year(meta, body), 1496)

    def test_lot_11146_erik_witten_1400(self):
        """part3 lot 11146 — Erik VII Witten ND (c. 1400). Buggy year 1898."""
        meta = "DENMARK. Witten, ND (c. 1400). Næstved Mint. Erik VII of Pomerania. NGC EF Details—Environmental Dam-"
        body = meta + " age. Galster-7; Sieg-2; Bruun-1898."
        self.assertEqual(extract_year(meta, body), 1400)

    def test_lot_11148_christopher_iii_1440(self):
        """part3 lot 11148 — Christopher III Skilling ND (1440-42). Buggy year 1874."""
        meta = "DENMARK. Skilling, ND (1440-42). Lund Mint. Christopher III of Bavaria. NGC EF-45. Galster-18; Sieg-4; FL-11;"
        body = meta + " Bruun-1874."
        self.assertEqual(extract_year(meta, body), 1440)

    def test_lot_11151_hans_goldgulden_1496(self):
        """part3 lot 11151 — Hans Goldgulden ND (1496-1497). Buggy year 1922."""
        meta = "DENMARK. Goldgulden (Rhinsk Gulden), ND (1496-1497). Malmö or Copenhagen Mint. Hans. NGC EF-45."
        body = meta + " Galster-26; Sieg-7; Schou-13; Bruun-1922."
        self.assertEqual(extract_year(meta, body), 1496)

    def test_lot_12029_hans_sosling_1481_1512(self):
        """part3 lot 12029 — Hans Søsling ND (1481-1512). Buggy year 1512
        (parser grabbed upper bound that happens to be 1500+)."""
        meta = "NORW AY . 1/2 Skilling (Søsling), ND (1481-1512). Bergen Mint. Hans. NGC EF-45. Galster-149;"
        body = meta + " Sieg-15; NMD-3;"
        # First year in meta wins (year_first semantics — phase classification
        # needs the lower bound per §8.2).
        self.assertEqual(extract_year(meta, body), 1481)

    def test_lot_12030_hans_hvid_1483_1505(self):
        """part3 lot 12030 — Hans Hvid ND (1483-1505). Buggy year 1505
        (upper bound of range)."""
        meta = "NORW AY . Hvid, ND (1483-1505). Nidaros (Trondheim)"
        body = meta + " Mint. Hans."
        self.assertEqual(extract_year(meta, body), 1483)

    def test_lot_14125_erik_pommerania_1396(self):
        """part2 lot 14125 — Erik of Pommerania Sweden 6 Penny ND (1396-1439).
        Buggy year was None (no 1500+ year in either meta or body)."""
        meta = "SWEDEN. 6 Penny / Abo, ND (1396-1439). Åbo Mint. Erik of Pommerania. NGC EF-45. Galster-201;"
        body = meta + " Delzanno-315;"
        self.assertEqual(extract_year(meta, body), 1396)

    def test_lot_14127_kristian_i_1457(self):
        """part2 lot 14127 — Kristian I Sweden Örtug ND (1457-1461). Buggy None."""
        meta = "SWEDEN. Örtug, ND (1457-1461). Stockholm Mint. Kristian I. NGC VF-35. Galster-214;"
        body = meta + " Delzanno-365; Llt-1; Bru-"
        self.assertEqual(extract_year(meta, body), 1457)


class TestBeskrivelsenTrap(unittest.TestCase):
    """Catalog-year-theft cases — body contains «Beskrivelsen YYYY» (the
    Beskrivelse over Danske Mønter 1791 catalogue edition). Old parser
    happily grabbed 1791 when the real coin year was earlier."""

    def test_beskrivelsen_1791_yields_to_meta_1496(self):
        """Lot 1001 distilled: meta has 1496, body has 1791. Meta wins."""
        meta = "DENMARK. Noble, 1496. Malmö or Copenhagen Mint. Hans."
        body = "Galster-24; Sieg-12; Schou-2; Beskrivelsen 1791-pl. 1, 2; Bruun-3831."
        self.assertEqual(extract_year(meta, body), 1496)

    def test_beskrivelsen_1791_yields_to_meta_1604_portugaloser(self):
        """Lot 1050 distilled: meta has 1604, body has Beskrivelsen 1791.
        Meta already wins (this was correctly parsed before fix), but
        regression-guard that meta_line priority preserves it."""
        meta = "DENMARK. Portugaloser (10 Ducats), ND (1604-1607). Copenhagen Mint. Christian IV . NGC AU-58."
        body = meta + " Fr-32; Hede-11A; Beskrivelsen 1791-pl. 1, 1."
        self.assertEqual(extract_year(meta, body), 1604)

    def test_beskrivelsen_1817_yields_to_meta_1496(self):
        """Hypothetical paired with lot 1002 — catalog edition 1817 (Ramus &
        Devegge), body-only year, must yield to meta year."""
        meta = "DENMARK. Goldgulden (Rhinsk Gulden), ND (ca. 1496-1497). Malmö or Copenhagen Mint. Hans."
        body = meta + " Beskrivelsen 1817-pl. 1, 5."
        self.assertEqual(extract_year(meta, body), 1496)


class TestPost1500Regression(unittest.TestCase):
    """Real lots that were CORRECTLY parsed before the fix. They must keep
    their year after the refactor (no regression)."""

    def test_speciedaler_1672(self):
        """Standard dated form, post-1500 — unchanged."""
        meta = "DENMARK. Speciedaler, 1672. Copenhagen Mint. Christian V . NGC MS-61."
        body = meta + " KM-393; Dav-3635; Hede-72; Sieg-31. Weight: 27.42 gms."
        self.assertEqual(extract_year(meta, body), 1672)

    def test_speciedaler_mdciii_1603(self):
        """MDCIII (1603) — Roman + Arabic dual form."""
        meta = "DENMARK. Speciedaler, MDCIII (1603). Copenhagen Mint. Christian IV ."
        body = meta + " KM-19; Dav-3512; Hede-51; Sieg-100. Weight: 27.44 gms."
        self.assertEqual(extract_year(meta, body), 1603)

    def test_rigsbankskilling_1813(self):
        """Post-1813 reform, standard year extraction."""
        meta = "DENMARK. 32 Rigsbankskilling, 1813. Altona Mint. Frederik VI. NGC AU-58."
        body = meta + " KM-695; Hede-19; Sieg-3."
        self.assertEqual(extract_year(meta, body), 1813)

    def test_krone_1875(self):
        """Late-period Skandinaviske Krone."""
        meta = "DENMARK. Krone, 1875. Copenhagen Mint. Christian IX. NGC MS-65."
        body = meta + " KM-797.1; Sieg-5."
        self.assertEqual(extract_year(meta, body), 1875)

    def test_kurantdukat_1735(self):
        """Convention-era gold dukat."""
        meta = "DENMARK. Kurantdukat, 1735. Copenhagen Mint. Christian VI. NGC AU-58."
        body = meta + " KM-516.1; Fr-251; Hede-1."
        self.assertEqual(extract_year(meta, body), 1735)


class TestEdgeCases(unittest.TestCase):
    """Synthetic edge cases for robustness."""

    def test_empty_inputs(self):
        self.assertIsNone(extract_year(None, None))
        self.assertIsNone(extract_year("", ""))

    def test_meta_only_yearless(self):
        """Meta line has no year — fall back to body."""
        meta = "DENMARK. Speciedaler. Christian VII. NGC AU-58."
        body = "KM-543.1; Dav-1311. Weight: 28.89 gms. Struck in 1772 from the new dies."
        self.assertEqual(extract_year(meta, body), 1772)

    def test_no_year_anywhere(self):
        """Neither meta nor body has a valid year — return None (not crash)."""
        meta = "DENMARK. Speciedaler. Christian VII."
        body = "KM-543. Lot description without any year markers. Weight: 28.89 gms."
        self.assertIsNone(extract_year(meta, body))

    def test_year_just_above_upper_bound(self):
        """Year 1981 must NOT be accepted (modern catalog edition trap)."""
        meta = "DENMARK. Speciedaler, 1672. Copenhagen. Christian V."
        body = "Sieg 1981 edition: 31; Weight: 27.42."
        # 1672 in meta wins, 1981 in body would be invalid anyway
        self.assertEqual(extract_year(meta, body), 1672)

    def test_year_below_lower_bound(self):
        """Year 1099 must NOT be accepted — outside parser horizon."""
        meta = "DENMARK. Some Coin, 1099. Pre-medieval."
        body = ""
        self.assertIsNone(extract_year(meta, body))

    def test_year_just_at_lower_bound(self):
        """Year 1100 IS accepted — early Scandinavian medieval."""
        meta = "DENMARK. Penning, 1100. Lund."
        body = ""
        self.assertEqual(extract_year(meta, body), 1100)

    def test_erik_vii_1396_pre_1400(self):
        """Erik VII of Pomerania ND (1396-1439) — first year 1396 is
        pre-1400 but in scope of the parser. Builder downstream filter
        decides whether the coin enters V2 seed."""
        meta = "SWEDEN. 6 Penny / Abo, ND (1396-1439). Åbo Mint. Erik of Pommerania."
        body = ""
        self.assertEqual(extract_year(meta, body), 1396)

    def test_multiple_years_in_meta_first_wins(self):
        """When meta has multiple years (e.g. range «1604-1607»), the first
        year wins for year_first semantics."""
        meta = "DENMARK. Portugaloser, ND (1604-1607). Copenhagen. Christian IV."
        body = ""
        self.assertEqual(extract_year(meta, body), 1604)

    def test_modern_catalog_year_in_body_ignored_when_meta_has_real_year(self):
        """Hed-2007 edition reference in body must not steal year."""
        meta = "DENMARK. Speciedaler, 1672. Copenhagen Mint. Christian V."
        body = meta + " Hede catalogue 2007 edition: 72; Sieg 31."
        self.assertEqual(extract_year(meta, body), 1672)

    def test_catalog_dashed_ref_in_body_fallback_ignored(self):
        """Body fallback (no year in meta) must skip catalog refs like
        «Dav-1311», «Bruun-1898», «KM-543» — they look like years but
        the alpha-dash prefix marks them as catalog identifiers."""
        meta = "DENMARK. Speciedaler. Christian VII. NGC AU-58."  # yearless
        body = "KM-543.1; Dav-1311. Weight: 28.89 gms. Struck in 1772 from new dies."
        # Should skip Dav-1311 (alpha-dash) and find «1772» which is plain prose
        self.assertEqual(extract_year(meta, body), 1772)

    def test_bruun_3831_dash_ref_skipped_in_body(self):
        """Body has «Bruun-3831» — must be skipped. Year comes from meta."""
        meta = "DENMARK. Noble, 1496. Malmö or Copenhagen Mint. Hans."
        body = "Galster-24; Sieg-12; Schou-2; Bruun-3831. Weight: 14.67 gms."
        self.assertEqual(extract_year(meta, body), 1496)


if __name__ == "__main__":
    unittest.main(verbosity=2)
