"""A curator nominal for a class lives in `classification_decisions` (D50).

Curator 2026-10-26: the Kobbersterling classes (Galster 7 + Numista 348708,
Galster 14 + Numista 476049) read «1 Sterling»; Numista prints «1 Sterling =
3 Pennings». The value is set by absorb from the assignment, never written into
the seed, which keeps what the source printed. Live-corpus test.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from lib.v2_index import V2Index  # noqa: E402
import yaml  # noqa: E402


class AssignmentNominal(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.idx = V2Index.load()
        cls.finals = {c["id"]: c for c in yaml.safe_load(
            (ROOT / "data/v2/final/danish_realm.yml").read_text())["coins"]}
        cls.seed = {c["id"]: c for c in yaml.safe_load(
            (ROOT / "data/v2/seed/numista/danish_realm.yml").read_text())["coins"]}

    def test_final_takes_the_curator_nominal(self):
        for sid in ("dk-numista-348708", "dk-numista-476049"):
            final = self.finals[self.idx.seed(sid).final]
            self.assertEqual(final["nominal"], "1 Sterling", sid)

    def test_seed_keeps_what_the_source_printed(self):
        for sid in ("dk-numista-348708", "dk-numista-476049"):
            self.assertEqual(self.seed[sid]["nominal"], "1 Sterling = 3 Pennings", sid)


if __name__ == "__main__":
    unittest.main()
