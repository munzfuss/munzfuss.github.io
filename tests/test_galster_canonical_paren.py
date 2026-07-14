"""standard._parse_description_and_refs — canonical-index-paren anchoring.

danskmoent Galster pages are NOT uniformly shaped. The catalogue-index
parenthetical «(Galster N, Schou M, Sieg K …)» may sit:
  * inside the «Forside:» line (the 81 pages that always parsed);
  * on a DETACHED line after a blank line before the spec <HR> (the c3g131
    class — the legacy `Forside:` capture stopped at the blank line, losing it);
  * on a page with NO «Forside:» colon-anchor at all (c3g92, f1g128).

The fix anchors ref-extraction on the page's OWN Galster number and is
two-tier (legacy-first) so ZERO currently-correct pages change:
  Tier 1 — legacy Forside-narrow scan (unchanged behaviour; keeps the
           multi-variant summary «(Galster 66A-B)» on f1g66);
  Tier 2 — fires only when Tier 1 is empty: pick the pre-HR paren that names
           the page's Galster number and carries the most catalogue keywords,
           so prose / literature / neighbour parens («(Galster 30)»,
           «(Galster: <book> side 59)») can NOT clobber the real value.

Run via:
    .venv/bin/python -m unittest tests.test_galster_canonical_paren -v
"""
from __future__ import annotations

import sys
from pathlib import Path
import unittest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
sys.path.insert(0, str(PROJECT_ROOT / "scripts" / "lib"))

from lib.galster_parsers.standard import (  # noqa: E402
    _parse_description_and_refs,
    _find_canonical_index_paren,
    _galster_number_from_filename,
)
from lib.galster_parsers.common import HR_SENTINEL  # noqa: E402

HR = HR_SENTINEL


class TestFilenameNumber(unittest.TestCase):
    def test_every_shape(self):
        cases = {
            "chr_c3g131.htm": "131",
            "fr_f1g120.htm": "120",
            "fr_f1g66c.htm": "66c",
            "chr_c3g92.htm": "92",
            "fr_hg29.htm": "29",
            "hansg31.htm": "31",
            "gotlg146.htm": "146",
            "norge_nc2g174.htm": "174",
            "norge_nha_g149.htm": "149",
            "norge_hansg151.htm": "151",
        }
        for name, num in cases.items():
            self.assertEqual(_galster_number_from_filename(name), num, name)

    def test_no_number(self):
        self.assertIsNone(_galster_number_from_filename("norge_hansGej.htm"))


class TestCanonicalParen(unittest.TestCase):
    def test_neighbour_not_matched(self):
        # base 120: real index paren + a bare neighbour «(Galster 125)».
        region = ("blah (Galster 120A, Schou 8-9) more (Galster 120) "
                  "and (Galster 125) tail " + HR + " spec")
        self.assertEqual(
            _find_canonical_index_paren(region, "120A"),
            "Galster 120A, Schou 8-9",
        )

    def test_literature_paren_not_matched(self):
        # «(Galster: <book> side 59)» has no «Galster <num>» → ignored.
        region = ("Forside (Galster 69, Schou 1) (sølv) "
                  "(Galster: Unionstidens Udmøntninger side 59) " + HR)
        self.assertEqual(
            _find_canonical_index_paren(region, "69"),
            "Galster 69, Schou 1",
        )

    def test_letter_suffix_base_matches(self):
        region = "(Galster 92AB, Schou 48-50, Sieg 3-4) " + HR
        self.assertEqual(
            _find_canonical_index_paren(region, "92AB"),
            "Galster 92AB, Schou 48-50, Sieg 3-4",
        )

    def test_only_scans_before_first_hr(self):
        # A paren after the first HR (spec/Eksemplarer region) is out of scope.
        region = "no paren here " + HR + " (Galster 50, Schou 9)"
        self.assertIsNone(_find_canonical_index_paren(region, "50"))

    def test_none_number_returns_none(self):
        self.assertIsNone(
            _find_canonical_index_paren("(Galster 5, Schou 1) " + HR, None))


class TestTwoTierExtraction(unittest.TestCase):
    def test_c3g131_detached_paren_recovered(self):
        # No paren in the Forside line; the index paren is detached after a
        # blank line. Tier 1 empty → Tier 2 recovers it.
        text = (
            "## Christian 3., 1 Rhinsk gylden, 1536\n\n"
            "Roskilde.\nForside: portræt, bagside: våbenskjolde.\n\n"
            "(Galster 131, Schou 1-7, Sieg 23; Reinhold Junge s. XX,18)\n\n"
            + HR + "\n• Bruttovægt: 3,19g\n"
        )
        _, refs = _parse_description_and_refs(text, "131")
        self.assertEqual(refs.get("galster"), "131")
        self.assertEqual(refs.get("schou"), "1-7")
        self.assertEqual(refs.get("sieg"), "23")

    def test_no_forside_recovered(self):
        # c3g92 class — no «Forside:» anchor; paren sits in the desc before HR.
        text = (
            "## Christian 3., 2 Mark klipping, 1535 Århus\n\n"
            "Ensidet klipping; C omgivet af 3-5.\n\n"
            "(Galster 92AB, Schou 48-50, Sieg 3-4, Reinhold Junge 6ab)\n\n"
            + HR + "\n"
        )
        _, refs = _parse_description_and_refs(text, "92")
        self.assertEqual(refs.get("galster"), "92AB")
        self.assertEqual(refs.get("schou"), "48-50")

    def test_f1g66_summary_stays_tier1(self):
        # Multi-variant summary «(Galster 66A-B)» in the Forside line MUST win
        # (Tier 1); the per-variant «(Galster 66A, Schou …)» below is NOT
        # promoted (that Schou-union is the deferred accumulate case).
        text = (
            "## Frederik 1., Søsling 1524, Landskrone\n\n"
            "Forside: Oldenborgs våben, bagside: skjold (Galster 66A-B).\n"
            "prose about varianter:\n\n"
            "• A) ELECTUS (Galster 66A, Schou f. kron. 18-19)\n\n"
            "• B) ELECTUS (Galster 66B, Schou f. kron. 9-17)\n\n" + HR + "\n"
        )
        _, refs = _parse_description_and_refs(text, "66")
        self.assertEqual(refs.get("galster"), "66A-B")
        self.assertNotIn("schou", refs)

    def test_neighbour_paren_never_clobbers(self):
        # hg29 class: base 29 index paren + a bare neighbour «(Galster 30)».
        # No Forside paren → Tier 2; anchor must pick 29, never 30.
        text = (
            "## Frederik 1.\n\nForside: skjold, bagside: kors.\n\n"
            "(Galster 29, Schou 1-13) note (Galster 30)\n\n" + HR + "\n"
        )
        _, refs = _parse_description_and_refs(text, "29")
        self.assertEqual(refs.get("galster"), "29")
        self.assertEqual(refs.get("schou"), "1-13")

    def test_trailing_semicolon_newline_stripped(self):
        # c3g132: «Sieg 21;\nReinhold Junge …» — the value must strip to «21».
        text = (
            "## Christian 3.\n\nForside: portræt.\n\n"
            "(Galster 132; Schou 1-7; Sieg 21;\nReinhold Junge s. XX,19)\n\n"
            + HR + "\n"
        )
        _, refs = _parse_description_and_refs(text, "132")
        self.assertEqual(refs.get("sieg"), "21")


if __name__ == "__main__":
    unittest.main(verbosity=2)
