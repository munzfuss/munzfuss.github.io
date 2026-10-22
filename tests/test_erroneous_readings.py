"""A source's reading may be doubted or refuted — never deleted, never withheld.

Two markers, differing only in what can be shown:

    suspect     the reading does not fit, and we cannot show why  → «(*)»
    erroneous   the reading has been shown to be wrong            → «(!)»

Both are PRESENTATIONAL (curator direction 2026-09-04, «до рендера і до дельти
мають доходити і підозрілі, і помилкові»). The marked reading computes exactly
like any other and reaches the Δ; the marker rides beside the figure with its
reason. Withholding the value would change the arithmetic on our own authority
and, where it is the coin's only reading, erase the Δ entirely — deciding by
omission what the reader should have been shown deciding for themselves.

The one place a marker DOES act is merge matching, and only `erroneous` there:
a value shown to be wrong may not disprove a merge (§4's rule for unverified
values, one step stronger). A merely suspect value still counts as evidence.

Founding cases, both real:
  erroneous — the Krause Schleswig-Holstein volume's blanket 3,5 g / .986,
              printed verbatim on 43 other coins, against four weighed
              specimens of the type at 3,08-3,22 g (docs/SOURCES.md §13.15).
  suspect   — the Nationalmuseet's Nobel of Frederik I at 17,4 g against the
              14,616 g of the Møntordning af Sommeren 1514. Nineteen per cent
              over is outside specimen variance, but a heavy specimen, a
              mis-keyed digit and a mis-identified nominal all remain open.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from lib.compute import marker_reasons, normalise_field, primary_value  # noqa: E402
from lib.schema import FieldValue  # noqa: E402


def _reason(text):
    """A marker's reason is reader-facing prose, so it is an I18nText triple."""
    return {"de": text, "en": text, "uk": text}


def _fv(value, source, **kw):
    for k in ("suspect", "erroneous"):
        if isinstance(kw.get(k), str):
            kw[k] = _reason(kw[k])
    return FieldValue(value=value, source=source, **kw)


class AMarkedReadingStillComputes(unittest.TestCase):
    """The correction that matters most: marking is not withholding."""

    def test_erroneous_stays_in_the_normalised_field(self):
        got = normalise_field([_fv(3.15, "jensen"), _fv(3.5, "ngc", erroneous="volume default")])
        self.assertEqual([(3.15, "jensen"), (3.5, "ngc")], got)

    def test_suspect_stays_too(self):
        got = normalise_field([_fv(17.4, "kmk", suspect="19 % over the ordinance")])
        self.assertEqual([(17.4, "kmk")], got)

    def test_a_coin_whose_only_reading_is_marked_still_has_a_delta_input(self):
        """Dropping it would erase the Δ over our own judgement rather than
        showing the figure and saying what is known about it."""
        self.assertEqual(3.5, primary_value([_fv(3.5, "ngc", erroneous="volume default")]))

    def test_display_false_is_the_one_flag_that_does_withhold(self):
        self.assertEqual([], normalise_field([_fv(3.5, "ngc", display=False)]))


class TheMarkerReachesTheRenderer(unittest.TestCase):
    def test_each_marked_source_is_reported_with_its_kind_and_reason(self):
        marks = marker_reasons([
            _fv(3.15, "jensen"),
            _fv(3.5, "ngc", erroneous="volume default"),
            _fv(17.4, "kmk", suspect="does not fit"),
        ])
        self.assertEqual({"ngc", "kmk"}, set(marks))
        self.assertEqual("erroneous", marks["ngc"][0])
        self.assertEqual("suspect", marks["kmk"][0])
        self.assertEqual("does not fit", marks["kmk"][1].uk)

    def test_an_unmarked_reading_produces_no_marker(self):
        self.assertEqual({}, marker_reasons([_fv(3.15, "jensen")]))

    def test_erroneous_outranks_suspect_on_one_entry(self):
        """The stronger claim is the one already proven."""
        marks = marker_reasons([_fv(3.5, "ngc", suspect="odd", erroneous="shown wrong")])
        self.assertEqual("erroneous", marks["ngc"][0])

    def test_a_hidden_reading_carries_no_marker_either(self):
        self.assertEqual({}, marker_reasons([_fv(3.5, "ngc", erroneous="x", display=False)]))


class OnlyMatchingActsOnAMarker(unittest.TestCase):
    def test_erroneous_is_ignored_when_comparing_two_records(self):
        from maintenance.merge_seeds_cross_source import _accepted
        entries = [{"value": 3.5, "source": "ngc", "erroneous": {"en": "default"}},
                   {"value": 3.15, "source": "jensen"}]
        self.assertEqual([{"value": 3.15, "source": "jensen"}], _accepted(entries))

    def test_but_suspect_still_counts_as_evidence(self):
        """Treating a doubt as a disproof is the confidence the two-tier marker
        exists to avoid."""
        from maintenance.merge_seeds_cross_source import _accepted
        entries = [{"value": 17.4, "source": "kmk", "suspect": {"en": "does not fit"}}]
        self.assertEqual(entries, _accepted(entries))


class TheAuditGuardsTheReason(unittest.TestCase):
    def test_a_blank_reason_is_reported(self):
        import audit_v2
        coins = [("e", {"id": "x",
                        "weight_rough_g": [{"value": 3.5, "source": "ngc", "erroneous": "  "}]})]
        errs = audit_v2.check_i11_erroneous_readings(coins)
        self.assertEqual(1, len(errs), errs)
        self.assertIn("no reason", errs[0])

    def test_a_verified_flag_over_only_erroneous_readings_is_reported(self):
        import audit_v2
        coins = [("e", {"id": "y",
                        "fineness": [{"value": 0.986, "source": "ngc",
                                      "erroneous": {"en": "default"}}],
                        "fineness_verified": True})]
        errs = audit_v2.check_i11_erroneous_readings(coins)
        self.assertEqual(1, len(errs), errs)
        self.assertIn("fineness_verified is true", errs[0])

    def test_the_live_corpus_is_clean(self):
        import audit_v2
        coins = []
        for entity in ("sonderburg_duchy", "gottorp_duchy", "danish_realm"):
            f = ROOT / f"data/v2/final/{entity}.yml"
            if f.exists():
                coins += [(entity, c) for c in yaml.safe_load(f.read_text())["coins"]]
        self.assertEqual([], audit_v2.check_i11_erroneous_readings(coins))


class TheFiveGoldguldenKeepTheCatalogueValue(unittest.TestCase):
    IDS = {"sonderburg_duchy": ["unified-ngc-1161408", "unified-ngc-1206707"],
           "gottorp_duchy": ["unified-ngc-1156100", "unified-ngc-1157533",
                             "unified-ngc-1156101"]}

    def _coins(self):
        for entity, ids in self.IDS.items():
            # D49: finals are keyed by opaque class ids; the name is `label`
            by = {c.get("label") or c.get("id"): c for c in
                  yaml.safe_load((ROOT / f"data/v2/final/{entity}.yml").read_text())["coins"]}
            for cid in ids:
                yield cid, by[cid]

    def test_the_template_value_was_not_deleted_and_is_marked(self):
        for cid, c in self._coins():
            with self.subTest(cid):
                for f, bad in (("weight_rough_g", 3.5), ("fineness", 0.986)):
                    hit = [e for e in (c.get(f) or []) if e["value"] == bad]
                    self.assertTrue(hit, f"{cid}.{f}: {bad} must stay on record")
                    for e in hit:
                        self.assertTrue(e.get("erroneous"), f"{cid}.{f}: {bad} must be marked")

    def test_the_1624_type_still_carries_the_real_weighings(self):
        c = next(x for x in yaml.safe_load(
            (ROOT / "data/v2/final/sonderburg_duchy.yml").read_text())["coins"]
            if (x.get("label") or x["id"]) == "unified-ngc-1206707")
        kept = sorted(e["value"] for e in c["weight_rough_g"] if not e.get("erroneous"))
        self.assertEqual([3.08, 3.16, 3.16, 3.19, 3.22], kept)


if __name__ == "__main__":
    unittest.main()
