"""What a final holds that its members no longer give.

Absorb enriches a final with `[final] + classes`, so a value the final once
held is re-unioned forever, even after the seed that brought it has left the
class. `lib.final_derivation` re-runs the same enrichment from a skeleton
(identity, fuss / phase / kind, holds) and sorts the difference: `own` (only
the final supplies it), `relabel` (same url, the final keeps an older ref
text), `diverged` (a single-valued field the final froze), `hidden` (a member
value the self-union does not show). Plan: docs/plans/
rebuild_final_from_members.md, stage 1.

These tests pin the skeleton (holds survive, data does not) and the sorting.
The last one runs absorb's real enrichment on a synthetic final.
"""
from __future__ import annotations

import contextlib
import io
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from lib import final_derivation as fd  # noqa: E402

N = "https://en.numista.com/121758"


def _src(url, ref):
    return {"url": url, "ref": ref, "type": "catalog"}


class Skeleton(unittest.TestCase):
    def test_keeps_decisions_and_held_values_only(self):
        fc = {"id": "c-1", "label": "unified-x", "origin": "promoted",
              "composed_of": ["c-1"], "fuss": "f", "phase": "A", "kind": "kurant",
              "ruler": "Frederik III.", "mint": "Bergen", "mint_verified": True,
              "sources": [_src(N, "a")],
              "_curation_holds": {"mint": "curator, Bergen"}}
        sk = fd.skeleton(fc)
        self.assertEqual(sk["mint"], "Bergen")
        self.assertTrue(sk["mint_verified"])
        self.assertEqual(sk["fuss"], "f")
        self.assertNotIn("ruler", sk)
        self.assertNotIn("sources", sk)


class Classify(unittest.TestCase):
    def test_same_url_new_ref_is_a_relabel(self):
        o = fd.items("sources", [_src(N, "Numista N#121758 (Bergen)")])
        g = fd.items("sources", [_src(N, "Numista N#121758 (Bergen) - Norway")])
        cl = fd.classify("sources", o, g)
        self.assertEqual(len(cl["relabel"]), 1)
        self.assertEqual(cl["own"], [])
        self.assertEqual(cl["hidden"], [])

    def test_a_source_no_member_gives_is_own(self):
        o = fd.items("sources", [_src("https://x/hg36.htm", "Galster 36")])
        cl = fd.classify("sources", o, set())
        self.assertEqual(len(cl["own"]), 1)

    def test_single_valued_field_diverges(self):
        o, g = fd.items("ruler", "Frederik III."), fd.items("ruler", "Frederik 3")
        cl = fd.classify("ruler", o, g)
        self.assertEqual(len(cl["diverged"]), 1)

    def test_catalogue_value_per_register(self):
        a = fd.items("catalog", {"km": ["13", "13.1"], "hede": "11"})
        b = fd.items("catalog", {"km": "13", "hede": "11"})
        self.assertEqual(a - b, {("km", "13.1")})

    def test_year_ranges_compare_by_year(self):
        self.assertEqual(fd.items("year_ranges", [[1650, 1652]]),
                         fd.items("year_ranges", [[1650, 1650], [1651, 1652]]))


class RealEnrichment(unittest.TestCase):
    def test_a_citation_left_on_the_final_is_own(self):
        with contextlib.redirect_stdout(io.StringIO()):
            from maintenance import absorb_seeds_into_final_v2 as ab
        cls = {"id": "c-cls", "label": "unified-s1", "composed_of": ["s1"],
               "nominal": "1 Skilling", "metal": "silver",
               "sources": [_src(N, "Numista")]}
        fc = {"id": "c-cls", "label": "unified-s1", "origin": "promoted",
              "composed_of": ["c-cls"], "fuss": "f", "phase": "A",
              "kind": "kurant", "nominal": "1 Skilling", "metal": "silver",
              "sources": [_src(N, "Numista"),
                          _src("https://x/hg36.htm", "Galster 36")]}
        ab._LIVE_UNIFIED.clear()
        ab._LIVE_UNIFIED.update({"c-cls": cls})
        with contextlib.redirect_stdout(io.StringIO()):
            a, b = fd.derive_pair(ab, fc, [cls], "danish_norway")
        o, g = fd.diff(a, b)["sources"]
        self.assertEqual(o, {("https://x/hg36.htm", "Galster 36")})
        self.assertEqual(g, set())


if __name__ == "__main__":
    unittest.main()
