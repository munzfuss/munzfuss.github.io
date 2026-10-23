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


class CatalogKmHold(unittest.TestCase):
    """`_curation_holds: {catalog.km}` keeps the stored KM shape (volume
    tags); the other registers still follow the members (km-105, 2026-10-23)."""

    def test_held_km_overrides_rebuilt_km_only(self):
        fc = {"id": "f", "catalog": {"km": {"dk": "73", "sh": "105"}, "hede": "120"},
              "_curation_holds": {"catalog.km": "volume tags"}}
        out = {"id": "f", "catalog": {"km": ["73", "105"], "hede": "120", "sieg": "140"}}
        ab._apply_catalog_km_hold(out, fc)
        self.assertEqual(out["catalog"], {"km": {"dk": "73", "sh": "105"}, "hede": "120", "sieg": "140"})

    def test_no_hold_no_change(self):
        fc = {"id": "f", "catalog": {"km": {"dk": "73"}}}
        out = {"id": "f", "catalog": {"km": ["73", "105"]}}
        ab._apply_catalog_km_hold(out, fc)
        self.assertEqual(out["catalog"]["km"], ["73", "105"])


class EmptyDuplicateRelease(unittest.TestCase):
    """`kind: empty_duplicate` drops a memberless final only while every
    recorded host is a final (2026-10-23)."""

    def setUp(self):
        self._saved = (ab._EMPTY_DUPLICATES, ab._ALL_FINAL_IDS)
        ab._EMPTY_DUPLICATES = {"km-1": ["host-a", "host-b"]}
        ab._ALL_FINAL_IDS = {"host-a"}

    def tearDown(self):
        ab._EMPTY_DUPLICATES, ab._ALL_FINAL_IDS = self._saved

    def test_released_when_all_hosts_exist(self):
        self.assertTrue(ab._is_released_empty_duplicate(
            {"id": "km-1", "composed_of": []}, set(), {"host-b"}))

    def test_kept_when_a_host_is_missing(self):
        self.assertFalse(ab._is_released_empty_duplicate(
            {"id": "km-1", "composed_of": []}, set(), set()))

    def test_kept_when_a_member_is_live(self):
        self.assertFalse(ab._is_released_empty_duplicate(
            {"id": "km-1", "composed_of": ["c-x"]}, {"c-x"}, {"host-b"}))

    def test_unrecorded_final_untouched(self):
        self.assertFalse(ab._is_released_empty_duplicate(
            {"id": "km-2", "composed_of": []}, set(), {"host-a", "host-b"}))


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


class Flags(unittest.TestCase):
    """The «(?)» flags are not all member data: a V1 foundation's are the
    curator's claims, and `year_is_reign_span` is absorb's own bookkeeping."""

    def test_foundation_keeps_its_unverified_claim(self):
        fc = _promoted(id="km-1", origin="foundation", composed_of=["c-cls"],
                       fineness_verified=False, verified=False)
        sk = ab._skeleton(fc)
        self.assertIs(sk["fineness_verified"], False)
        self.assertIs(sk["verified"], False)
        self.assertIn("fineness_verified", ab._skeleton(_promoted(fineness_verified=False)))  # an explicit false travels everywhere

    def test_reign_span_flag_travels_on_a_promoted_final(self):
        sk = ab._skeleton(_promoted(year_is_reign_span=True))
        self.assertIs(sk["year_is_reign_span"], True)


class FoundationOwnRecord(unittest.TestCase):
    """What the enrichment reads from the foundation itself — its prose, its
    years, a curator fraction — is the foundation's own record, not member
    data; a V1 foundation keeps it. Source data (citations, catalogue
    numbers, readings) it does not keep: the harvests supply that."""

    def test_prose_years_and_fraction_stay_on_a_foundation(self):
        fc = _promoted(id="km-1", origin="foundation", composed_of=[],
                       inscription_obv="CHRISTIANVS", year_first=1624, year_last=1634,
                       year_ranges=[[1624, 1634]], year_label="1624-1634",
                       verification_note={"en": "V1 curator"}, fraction="1/2")
        sk = ab._skeleton(fc)
        for k in ("inscription_obv", "year_first", "year_last", "year_ranges", "year_label",
                  "verification_note", "fraction"):
            self.assertEqual(sk[k], fc[k], k)
        for k in ("sources", "metal", "mint"):
            self.assertNotIn(k, sk, k)

    def test_promoted_keeps_fraction_only(self):
        sk = ab._skeleton(_promoted(fraction="1/2", inscription_obv="X", year_first=1624,
                                    verification_note={"en": "boilerplate"}))
        self.assertEqual(sk["fraction"], "1/2")
        for k in ("inscription_obv", "year_first", "verification_note"):
            self.assertNotIn(k, sk, k)


class ExplicitUnverified(unittest.TestCase):
    """A stored `*_verified: false` is a claim of non-attestation; the
    rebuild must not turn it into the schema default (true)."""

    def test_false_flags_travel_on_a_promoted_final(self):
        sk = ab._skeleton(_promoted(year_verified=False, mint_verified=True, metal_verified=False))
        self.assertIs(sk["year_verified"], False)
        self.assertIs(sk["metal_verified"], False)
        self.assertNotIn("mint_verified", sk)


class YearHoldFamily(unittest.TestCase):
    """A hold on one year field carries the whole year family: a stored
    single year has no `year_ranges` key, so a hold on `year_ranges` alone
    carried nothing and the year-hold path read None (c4h144a, 2026-10-23)."""

    def test_hold_on_year_ranges_carries_first_last_label(self):
        fc = _promoted(year_first=1629, year_last=1629, year_label="1629",
                       _curation_holds={"year_ranges": "1629 only"})
        sk = ab._skeleton(fc)
        self.assertEqual((sk["year_first"], sk["year_last"], sk["year_label"]), (1629, 1629, "1629"))

    def test_no_year_hold_carries_no_years_on_a_promoted_final(self):
        sk = ab._skeleton(_promoted(year_first=1629, year_label="1629"))
        self.assertNotIn("year_first", sk)


class HeadClassByLabel(unittest.TestCase):
    """The head class is the one the final's `label` names, then the class
    with the final's id, then the highest-authority class — never the id
    that sorts first."""

    def test_label_outranks_id_and_authority(self):
        uni = {"c-aa": dict(CLS, id="c-aa", label="unified-ikmk-1"),
               "c-zz": dict(CLS, id="c-zz", label="unified-dk-hede-nf3h8b"),
               "c-mm": dict(CLS, id="c-mm", label="unified-dk-bruun-9")}
        fc = _promoted(id="c-aa", label="unified-dk-hede-nf3h8b", composed_of=["c-aa", "c-mm", "c-zz"])
        self.assertEqual(ab._head_class_order(fc, fc["composed_of"], uni), ["c-zz", "c-mm", "c-aa"])

    def test_without_a_label_match_authority_decides_before_self(self):
        uni = {"c-aa": dict(CLS, id="c-aa", label="unified-ikmk-1"),
               "c-mm": dict(CLS, id="c-mm", label="unified-dk-bruun-9"),
               "c-hh": dict(CLS, id="c-hh", label="unified-dk-hede-x")}
        fc = _promoted(id="c-mm", label="unified-dk-hede-nf3h9", composed_of=["c-aa", "c-mm", "c-hh"])
        self.assertEqual(ab._head_class_order(fc, fc["composed_of"], uni), ["c-hh", "c-mm", "c-aa"])

    def test_sub_letter_class_matches_a_bare_hede_label(self):
        uni = {"c-aa": dict(CLS, id="c-aa", label="unified-ikmk-1"),
               "c-hh": dict(CLS, id="c-hh", label="unified-dk-hede-nf3h8b")}
        fc = _promoted(id="c-aa", label="unified-dk-hede-nf3h8", composed_of=["c-aa", "c-hh"])
        self.assertEqual(ab._head_class_order(fc, fc["composed_of"], uni), ["c-hh", "c-aa"])


class PlaceholderNeverWins(unittest.TestCase):
    """A head class whose record has no nominal carries the literal «(?)»;
    another class's real value must win the scalar."""

    def test_gapfill_skips_the_placeholder(self):
        head = dict(CLS, id="c-h", label="unified-kmk-1", nominal="(?)")
        other = dict(CLS, id="c-o", label="unified-kmk-2", composed_of=["s2"], nominal="1 Lejrskilling")
        fc = _promoted(id="c-h", label="unified-kmk-1", composed_of=["c-h", "c-o"], nominal="(?)")
        ab._LIVE_UNIFIED.clear()
        ab._LIVE_UNIFIED.update({"c-h": head, "c-o": other})
        ab.SELF_UNION_ENABLED = False
        try:
            base = ab._own(fc)
            with contextlib.redirect_stdout(io.StringIO()):
                out, _ = ab._enrich_final_entry(base, [base, head, other], "danish_realm")
            ab._normalise_final_entry(out, {"c-h": head, "c-o": other})
        finally:
            ab.SELF_UNION_ENABLED = True
        self.assertEqual(out["nominal"], "1 Lejrskilling")
        self.assertIsNone(ab._first_real([{"nominal": "(?)"}, {"nominal": ""}], "nominal"))


class PlaceholderStaysWhenAlone(unittest.TestCase):
    """When no class has a real nominal the placeholder itself stays — the
    schema requires the field (run 4: two _unclassified finals lost it)."""

    def test_placeholder_kept_without_a_real_value(self):
        head = dict(CLS, id="c-h", label="unified-kmk-1", nominal="(?)")
        fc = _promoted(id="c-h", label="unified-kmk-1", composed_of=["c-h"], nominal="(?)")
        ab._LIVE_UNIFIED.clear()
        ab._LIVE_UNIFIED.update({"c-h": head})
        ab.SELF_UNION_ENABLED = False
        try:
            base = ab._own(fc)
            with contextlib.redirect_stdout(io.StringIO()):
                out, _ = ab._enrich_final_entry(base, [base, head], "danish_realm")
        finally:
            ab.SELF_UNION_ENABLED = True
        self.assertEqual(out["nominal"], "(?)")
