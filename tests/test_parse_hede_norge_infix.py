"""Unit tests for the Norwegian «Hede Norge N» regional infix in parse_hede.

danskmoent.dk writes the Danish volumes as «Hede 16A» but the Norwegian
ones as «Hede Norge 16A». Several regexes anchored on a bare `Hede\\s*`
and therefore dropped the Hede number across the whole Norwegian corpus
(104 of 167 Norwegian pages parsed with an EMPTY `catalog_refs.Hede`;
0 of 60 pages carrying >=2 «A)»/«B)» letter blocks produced `by_letter`).

Covered here:
  * `_extract_refs` — the infix (defect 1) + the «hhv. X og Y»
    enumeration split (defect 4).
  * `_extract_letter_groups` on nc5h16 — the infix at the letter anchor
    (defect 2) plus anchor-containing-parenthesis selection (defect 3:
    block «B)» swallows the following «3 Dukat» section, so its LAST
    parenthesis is the wrong one, «(RRR)»).
  * A Danish letter-group page that already worked — regression guard.

Run:  .venv/bin/python -m unittest tests.test_parse_hede_norge_infix -v
"""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import parse_hede as ph  # noqa: E402

CACHE = ROOT / "scripts" / "cache" / "hede"


def _text(basename: str) -> str:
    return ph._strip_html(
        (CACHE / f"{basename}.htm").read_text(encoding="utf-8", errors="replace")
    )


class ExtractRefsInfix(unittest.TestCase):
    def test_danish_form_unchanged(self):
        self.assertEqual(
            ph._extract_refs("Hede 16A, Sieg 11.1"),
            {"Hede": ["16A"], "Sieg": ["11.1"]},
        )

    def test_norwegian_infix_with_enumeration(self):
        # Hede number was LOST entirely before the fix; «hhv. 8 og 3»
        # collapsed into the single bogus token «8,3».
        self.assertEqual(
            ph._extract_refs("Hede Norge 16A, Schou hhv. 8 og 3"),
            {"Hede": ["16A"], "Schou": ["8", "3"]},
        )

    def test_norwegian_infix_plain(self):
        self.assertEqual(
            ph._extract_refs("Hede Norge 11, Schou 5"),
            {"Hede": ["11"], "Schou": ["5"]},
        )

    def test_comma_run_stays_joined(self):
        # A literal comma inside one reference run is the source's own
        # within-run notation and stays joined — only «og» splits.
        self.assertEqual(
            ph._extract_refs("Schou 136-165,59-61"),
            {"Schou": ["136-165,59-61"]},
        )


# scripts/cache is a private submodule; CI checks out without it.
_NO_CACHE = "hede cache submodule not present"


@unittest.skipUnless((CACHE / "nc5h16.htm").exists(), _NO_CACHE)
class LetterGroupsNorwegian(unittest.TestCase):
    def test_nc5h16_a_and_b(self):
        groups = ph._extract_letter_groups(_text("nc5h16"), "16")
        self.assertIsNotNone(groups, "nc5h16 produced no letter groups")
        self.assertEqual(sorted(groups), ["A", "B"])
        self.assertEqual(groups["A"]["catalog_refs"]["Hede"], ["16A"])
        self.assertEqual(groups["A"]["catalog_refs"]["Schou"], ["8", "3"])
        self.assertEqual([y["year"] for y in groups["A"]["years"]], [1673, 1678])
        # 16B is «u.år» (undated) in Hede — an empty year list is correct.
        self.assertEqual(groups["B"]["catalog_refs"]["Hede"], ["16B"])
        self.assertEqual(groups["B"]["catalog_refs"]["Schou"], ["11"])
        self.assertEqual(groups["B"]["years"], [])


@unittest.skipUnless((CACHE / "c4h100.htm").exists(), _NO_CACHE)
class LetterGroupsDanishRegression(unittest.TestCase):
    def test_c4h100_unchanged(self):
        groups = ph._extract_letter_groups(_text("c4h100"), "100")
        self.assertIsNotNone(groups)
        self.assertEqual(sorted(groups), ["A", "B"])
        self.assertEqual(groups["A"]["catalog_refs"]["Hede"], ["100A"])
        self.assertEqual(groups["A"]["catalog_refs"]["Sieg"], ["49.1"])
        # Source: «Schou hhv. 21-31, 32-33, 96-100 og 126-129». The «og»
        # split is the defect-4 correction and applies to Danish pages
        # too; the comma-separated head stays joined (see
        # ExtractRefsInfix.test_comma_run_stays_joined).
        self.assertEqual(
            groups["A"]["catalog_refs"]["Schou"], ["21-31,32-33,96-100", "126-129"]
        )
        self.assertEqual(groups["B"]["catalog_refs"]["Hede"], ["100B"])
        self.assertEqual(groups["B"]["catalog_refs"]["Sieg"], ["49.2"])
        self.assertEqual(
            [y["year"] for y in groups["A"]["years"]], [1616, 1617, 1618, 1619]
        )


if __name__ == "__main__":
    unittest.main()
