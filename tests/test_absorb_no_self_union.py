"""`absorb --no-self-union`: a final is rebuilt from its members and its own
skeleton, never from its stored copy.

Enrichment ran on `[final] + classes`, so a final was its own first member and
whatever it once held was re-unioned forever: 947 citations on 394 finals that
another final's class attested (2026-10-22), 4 261 promoted finals with a
`ruler` their class had since corrected. With the switch (docs/plans/
rebuild_final_from_members.md, stage A) the final contributes only what no
member can — identity, fuss / phase / kind, `_curation_holds` and the held
values, curator prose (`note`), bookkeeping — and a V1 foundation keeps its
descriptive scalars. These tests pin that policy field by field, and that the
switch OFF is today's behaviour exactly.
"""
from __future__ import annotations

import contextlib
import io
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "maintenance"))

with contextlib.redirect_stdout(io.StringIO()):
    from maintenance import absorb_seeds_into_final_v2 as ab  # noqa: E402

N = "https://en.numista.com/121758"


def _src(url, ref):
    return {"url": url, "ref": ref, "type": "catalog"}


CLS = {"id": "c-cls", "label": "unified-s1", "composed_of": ["s1"],
       "nominal": "1 Skilling", "ruler": "Frederik III.", "metal": "silver",
       "mint": "Bergen", "mint_verified": True,
       "sources": [_src(N, "Numista")],
       "verification_note": {"en": "KMM record"}}


def _promoted(**extra):
    fc = {"id": "c-cls", "label": "unified-s1", "origin": "promoted",
          "composed_of": ["c-cls"], "fuss": "f", "phase": "A", "kind": "kurant",
          "nominal": "1 Skilling", "ruler": "Frederik 3", "metal": "silver",
          "mint": "Bergen", "mint_verified": True,
          "sources": [_src(N, "Numista"), _src("https://x/hg36.htm", "Galster 36")],
          "note": {"en": "Obverse: portrait."},
          "verification_note": {"en": "Hede seed boilerplate"}}
    fc.update(extra)
    return fc


def _enrich(fc, cls=CLS):
    ab._LIVE_UNIFIED.clear()
    ab._LIVE_UNIFIED.update({cls["id"]: cls})
    base = ab._own(fc)
    with contextlib.redirect_stdout(io.StringIO()):
        out, _ = ab._enrich_final_entry(base, [base, cls], "danish_norway")
    return out


class SwitchOff(unittest.TestCase):
    def test_own_is_the_stored_final(self):
        ab.SELF_UNION_ENABLED = True
        fc = _promoted()
        self.assertIs(ab._own(fc), fc)
        out = _enrich(fc)
        self.assertIn(("https://x/hg36.htm", "Galster 36"),
                      {(s["url"], s["ref"]) for s in out["sources"]})
        self.assertEqual(out["ruler"], "Frederik 3")


class SwitchOn(unittest.TestCase):
    def setUp(self):
        ab.SELF_UNION_ENABLED = False

    def tearDown(self):
        ab.SELF_UNION_ENABLED = True

    def test_a_citation_no_member_gives_is_gone(self):
        out = _enrich(_promoted())
        self.assertEqual({(s["url"], s["ref"]) for s in out["sources"]}, {(N, "Numista")})

    def test_promoted_scalars_follow_the_class(self):
        out = _enrich(_promoted())
        self.assertEqual(out["ruler"], "Frederik III.")
        self.assertEqual(out["verification_note"], {"en": "KMM record"})

    def test_foundation_scalars_stay(self):
        fc = _promoted(id="km-1", origin="foundation", composed_of=["c-cls"])
        out = _enrich(fc)
        self.assertEqual(out["ruler"], "Frederik 3")

    def test_classification_note_and_holds_stay(self):
        fc = _promoted(mint="Kongsberg", mint_verified=True,
                       _curation_holds={"mint": "curator: Kongsberg"})
        out = _enrich(fc)
        self.assertEqual((out["fuss"], out["phase"], out["kind"]), ("f", "A", "kurant"))
        self.assertEqual(out["note"], {"en": "Obverse: portrait."})
        self.assertIn("Kongsberg", out["mint"] if isinstance(out["mint"], list) else [out["mint"]])
        self.assertEqual(out["_curation_holds"], {"mint": "curator: Kongsberg"})

    def test_skeleton_keeps_bookkeeping_only(self):
        sk = ab._skeleton(_promoted(_weights_thinned=["x"], v1_home_location="denmark"))
        self.assertEqual(set(sk) - {"__order__"}, {"id", "label", "origin", "composed_of", "fuss", "phase",
                                   "kind", "note", "_weights_thinned", "v1_home_location"})


if __name__ == "__main__":
    unittest.main()


class KeyOrder(unittest.TestCase):
    def test_rebuilt_entry_keeps_the_stored_key_order(self):
        ab.SELF_UNION_ENABLED = False
        try:
            fc = _promoted()
            out = _enrich(fc)
        finally:
            ab.SELF_UNION_ENABLED = True
        shared = [k for k in fc if k in out]
        self.assertEqual([k for k in out if k in fc], shared)
        self.assertNotIn("__order__", out)


class HeadClassFirst(unittest.TestCase):
    def test_a_scalar_comes_from_the_head_class(self):
        """A promoted final of two classes: `nominal` is the HEAD class's (the
        one whose id the final carries), not the class whose id sorts first."""
        head = dict(CLS, id="c-zz", label="unified-s1", nominal="1 Krone")
        other = dict(CLS, id="c-aa", label="unified-s2", composed_of=["s2"], nominal="1 Mark")
        fc = _promoted(id="c-zz", composed_of=["c-aa", "c-zz"], nominal="1 Krone")
        ab._LIVE_UNIFIED.clear()
        ab._LIVE_UNIFIED.update({"c-zz": head, "c-aa": other})
        ab.SELF_UNION_ENABLED = False
        try:
            base = ab._own(fc)
            order = sorted(fc["composed_of"], key=lambda m: (m != fc["id"], m))
            with contextlib.redirect_stdout(io.StringIO()):
                out, _ = ab._enrich_final_entry(base, [base] + [ab._LIVE_UNIFIED[m] for m in order], "danish_norway")
        finally:
            ab.SELF_UNION_ENABLED = True
        self.assertEqual(order, ["c-zz", "c-aa"])
        self.assertEqual(out["nominal"], "1 Krone")
