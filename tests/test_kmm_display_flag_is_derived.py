"""`display: false` on a KMM citation is DERIVED by absorb, never curated.

Every full re-flow on a clean HEAD (2026-10-15, twice) dropped one
`display: false` from `erzbisthum_bremen_verden.yml` — the SOLE source of
`unified-kmk-741043` — and sessions reverted it by hand as if it were a
curation loss. It was not: commit 5560422 (KMM ref rewrite) wrote the flag
onto the coin's only citation, but absorb's
`_suppress_weightless_museum_overcollection` recomputes the flag from scratch
on every run (pop on the kept specimens, set on the surplus), and a coin with
one KMM citation always keeps it visible. HEAD was simply not a fixed point of
absorb. The guard: a hand-set flag on a citation absorb keeps is removed, and
the computation is idempotent, so a committed final that matches absorb's
output stays byte-identical on the next re-flow.
"""
from __future__ import annotations

import copy
import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "maintenance"))

import absorb_seeds_into_final_v2 as absorb  # noqa: E402


def _src(nid: int, hidden: bool = False) -> dict:
    s = {"type": "museum",
         "url": f"https://samlinger.natmus.dk/KMM/object/{nid}",
         "ref": f"KMM {nid}"}
    if hidden:
        s["display"] = False
    return s


class KmmDisplayFlagIsDerived(unittest.TestCase):
    def _run(self, coin, weights=None, images=()):
        weights = weights or {}
        with mock.patch.object(absorb, "_kmm_specimen_weight",
                               lambda nid: weights.get(str(nid))), \
             mock.patch.object(absorb, "_kmm_specimen_has_image",
                               lambda nid: str(nid) in images):
            return absorb._suppress_weightless_museum_overcollection(coin)

    def test_sole_citation_flag_is_cleared(self):
        # the unified-kmk-741043 shape: one weight-giving KMM citation
        coin = {"sources": [_src(741043, hidden=True)]}
        self._run(coin, weights={"741043": 0.54})
        self.assertNotIn("display", coin["sources"][0])

    def test_sole_weightless_citation_flag_is_cleared(self):
        coin = {"sources": [_src(741043, hidden=True)]}
        self._run(coin)
        self.assertNotIn("display", coin["sources"][0])

    def test_surplus_flags_are_a_fixed_point(self):
        coin = {"sources": [_src(n) for n in (5, 3, 4, 1, 2)]}
        self._run(coin)
        once = copy.deepcopy(coin)
        self.assertEqual(
            [s.get("display") for s in once["sources"]],
            [False, False, False, None, False])  # keep lowest id (1)
        self._run(coin)
        self.assertEqual(coin, once)


if __name__ == "__main__":
    unittest.main()
