"""A Hede sub-variant line whose opening parenthesis the page dropped.

danskmoent's Hede Norge 2 (Frederik V, 24 Skilling) prints «A) 1746-1763
(samtlige årstal; …; Hede Norge 2A, …)» but «B) 1763, 1764, 1765; …; Hede
Norge 2B, Schou hhv. 11, 8 og 5, Sieg Norge 3)» — no «(». The letter-group
parser looked for the anchor only inside balanced parentheses, found one
group, and kept the page whole; the bare Hede 2 record then joined KM 236
(2A) in one run and KM 241 (2B) in the next, depending on union order
(curator 2026-11-03). The fallback must stay narrow: on f3h57 a balanced
line naming «Som Hede 57A» in prose belongs to the 2 Speciedaler, and an
earlier, wider fallback overwrote 57A's years with it.

Run:  .venv/bin/python -m unittest tests.test_parse_hede_missing_open_paren -v
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


@unittest.skipUnless((CACHE / "nf5h2.htm").exists(), "harvest cache not attached")
class MissingOpenParen(unittest.TestCase):
    def test_nf5h2_splits_into_2a_and_2b(self):
        groups = ph._extract_letter_groups(_text("nf5h2"), "2")
        self.assertEqual(sorted(groups), ["A", "B"])
        self.assertEqual([y["year"] for y in groups["B"]["years"]], [1763, 1764, 1765])
        self.assertEqual(groups["B"]["catalog_refs"]["Hede"], ["2B"])

    def test_balanced_prose_mention_is_not_taken(self):
        entry = ph.parse_one(
            (CACHE / "f3h57.htm").read_text(encoding="utf-8", errors="replace"), "f3h57")
        years = entry["specs"]["by_hede"]["57A"]["years"]
        self.assertTrue(all(y["rarity"] is None for y in years))


if __name__ == "__main__":
    unittest.main()
