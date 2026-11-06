"""Hede pages that give one spec block for several coins «hhv.» (respectively).

c4h61 describes 1, 2 and 3 Speciedaler 1624 on one page and lists the weights
in label order («Bruttovægt hhv.: 29,232g, 58,464g, 87,696g»). The overview
c4hede.htm links Hede 60AB, 61AB and 62 all to this page. Before the fix the
page gave one seed with the title nominal «1, 2 og 3 speciedaler» and every
Schou / Sieg number of the three coins, no weight, and Hede 60 and 62 fell
back to overview stubs marked «Tiefenseite fehlt».
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import parse_hede as p  # noqa: E402

TEXT = """Christian 4., Hede 61
Christian 4., 1, 2 og 3 speciedaler 1624, København
Forside: brystbillede, bagside: provinsvåben
1 Speciedaler
A) (RRR) Skjoldene indadbuede (Hede 60A, Schou 16, Sieg 120)
B) (Unik) Skjoldene ligesidede (Hede 60B, Schou 17, Sieg 120)
2 Speciedaler
A) (RR) Skjoldene indadbuede (Hede 61A, Schou 8, Sieg 121)
B) (RRR) Skjoldene ligesidede (Hede 61B, Schou 9, Sieg 121)
3 Speciedaler
A) (RRR) Skjoldene indadbuede (Hede 62, Schou 5, Sieg 122)

Bruttovægt hhv.: 29,232g, 58,464g, 87,696g
Finhed: 0,881
Finvægt hhv.: 25,781g, 51,562g, 77,342g
Marken fin udbragt til 9,071 speciedalere
"""


class HhvSpecs(unittest.TestCase):
    def test_one_spec_per_coin(self):
        by = p._extract_specs(TEXT, "c4h61")["by_hede"]
        self.assertEqual(sorted(by), ["60AB", "61", "62"])
        self.assertEqual(by["61"]["nominal"], "2 speciedaler")
        self.assertEqual(by["61"]["bruttovægt_g"], 58.464)
        self.assertEqual(by["61"]["finvægt_g"], 51.562)
        self.assertEqual(by["61"]["finhed"], 0.881)
        self.assertEqual(by["61"]["catalog_refs"], {"Schou": ["8", "9"], "Sieg": ["121"]})
        self.assertEqual(by["60AB"]["catalog_refs"], {"Schou": ["16", "17"], "Sieg": ["120"]})
        self.assertEqual(by["62"]["bruttovægt_g"], 87.696)

    def test_count_mismatch_falls_back(self):
        text = TEXT.replace("29,232g, 58,464g, 87,696g", "29,232g, 58,464g")
        self.assertIsNone(p._extract_hhv_specs(text, "c4h61"))


if __name__ == "__main__":
    unittest.main()
