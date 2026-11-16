"""Regression guards for Bruun ref patterns that captured PROSE, not indices.

Two REF_PATTERNS entries used a bare `(\\S+?)` value capture — any non-space
run — and so harvested whatever followed the catalogue name, even when the
lot carried no index at all:

  * lot 17035 (Bruun-4090, Frederik I 4 Skilling 1532) cites the study in
    running prose — "The most recent study, by Jensen & Skjoldager, again
    leans towards 4 Skilling" — with NO Skjoldager number. The parser
    captured ",", which reached the seed as the catalogue index
    "jensen_skjoldager: ', again leans towards 4 Skilling'".
  * `Schive` matched INSIDE the mintmaster surname "Schivern Knoph" and
    captured "rn" on four lots.

A third, opposite failure: lot 11156's real ref "Skjoldager-F- 53/F-57" was
truncated to "F-" by the old lookahead, losing the index.

Run:  .venv/bin/python -m unittest tests.test_bruun_ref_prose_capture -v
"""
import importlib.util
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location(
    "bruun_parse_lots", ROOT / "scripts" / "bruun_parser" / "02_parse_lots.py"
)
pl = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(pl)


def _skjoldager(text: str):
    m = pl.REF_PATTERNS["Skjoldager"].search(text)
    return re.sub(r"\s+", "", m.group(1)) if m else None


def _schive(text: str):
    m = pl.REF_PATTERNS["Schive"].search(text)
    return pl._schive_value(m) if m else None


class SkjoldagerProse(unittest.TestCase):
    def test_prose_mention_yields_no_ref(self):
        # Verbatim from lot 17035's body_excerpt.
        self.assertIsNone(_skjoldager(
            "Scholars and collectors have argued about the denomination of "
            "this coin for centuries. The most recent study, by Jensen & "
            "Skjoldager, again leans towards 4 Skilling."
        ))

    def test_dash_placeholder_yields_no_ref(self):
        self.assertIsNone(_skjoldager("Skjoldager-–; Bruun-4090;"))

    def test_wrapped_index_captured_in_full(self):
        # lot 11156 — the PDF line-wrap leaves a space inside the index.
        self.assertEqual(
            _skjoldager("Skjoldager-F- 53/F-57; Schou-5; Bruun-3978."),
            "F-53/F-57",
        )


class SkjoldagerRealIndices(unittest.TestCase):
    """Every distinct real value in the cache still parses unchanged."""

    def test_all_attested_shapes(self):
        for raw, expected in [
            ("Skjoldager-T21/25;", "T21/25"),
            ("Skjoldager-T-22/26;", "T-22/26"),
            ("Skjoldager-T-81/T-86;", "T-81/T-86"),
            ("Skjoldager-L-01/L-34;", "L-01/L-34"),
            ("Skjoldager-S-01/S-05;", "S-01/S-05"),
            ("Skjoldager-N-05;", "N-05"),
            ("Skjoldager-51/55;", "51/55"),
            ("Skjoldager-76B/83;", "76B/83"),
        ]:
            with self.subTest(raw=raw):
                self.assertEqual(_skjoldager(raw), expected)


class BuilderSideExtraction(unittest.TestCase):
    """The seed builder re-scans the lot body with its OWN Jensen-Skjoldager
    pattern. Both extractors must reject prose — otherwise the weaker one
    re-introduces the artefact on the next regen, which is how the bogus
    index survived a parser fix + full re-parse."""

    PAT = re.compile(
        r"Jensen\s*&?\s*Skjoldager[-:]?\s*"
        r"((?:[A-Z]{1,2}-?\s*)?\d+[A-Za-z]*(?:\s*/\s*(?:[A-Z]{1,2}-?\s*)?\d+[A-Za-z]*)*)"
    )

    def _cap(self, text):
        m = self.PAT.search(text)
        return re.sub(r"\s+", "", m.group(1)) if m else None

    def test_builder_pattern_matches_parser_pattern(self):
        src = (ROOT / "scripts" / "maintenance"
               / "build_bruun_denmark_seed.py").read_text()
        self.assertIn(
            r"((?:[A-Z]{1,2}-?\s*)?\d+[A-Za-z]*(?:\s*/\s*(?:[A-Z]{1,2}-?\s*)?\d+[A-Za-z]*)*)",
            src,
            "builder-side Jensen-Skjoldager capture drifted from the parser's",
        )

    def test_two_letter_series(self):
        # Part V lots 15179 / 15180 print «Jensen & Skjoldager-SH 25» / «-SH11».
        self.assertEqual(self._cap("Jensen & Skjoldager-SH 25; Schou-24"), "SH25")

    def test_prose_rejected(self):
        self.assertIsNone(self._cap(
            "The most recent study, by Jensen & Skjoldager, again leans "
            "towards 4 Skilling."
        ))

    def test_real_indices_kept(self):
        self.assertEqual(self._cap("Jensen & Skjoldager-T21/25;"), "T21/25")
        self.assertEqual(self._cap("Jensen & Skjoldager-F- 53/F-57;"), "F-53/F-57")


class SchiveSurname(unittest.TestCase):
    def test_mintmaster_surname_is_not_a_ref(self):
        # lot 13235 — «Schivern Knoph» is the mintmaster, not the catalogue.
        self.assertIsNone(_schive("Mintmaster: Schivern Knoph. Engraver: Johan"))

    def test_real_plate_ref_still_parses(self):
        self.assertEqual(_schive("Schive-X:14; Bruun-8853;"), "X:14")


class SchiveNonReferences(unittest.TestCase):
    """Shapes that are NOT this coin's own Schive index (CLAUDE.md §5
    anti-pattern): a «cf.» points at a similar OTHER coin, «Unlisted» is
    the negative claim that the coin is absent from the catalogue."""

    def test_cf_form_rejected(self):
        self.assertIsNone(_schive("Schive-cf. II:24; NM-3; NMH-14b;"))

    def test_cf_after_plate_rejected(self):
        # lot 12015 — «Schive-IX: cf. 1-2» previously captured the bare «IX:».
        self.assertIsNone(_schive("Schive-IX: cf. 1-2; NM-26 (1976);"))

    def test_unlisted_rejected(self):
        self.assertIsNone(_schive("Schive-Unlisted; NM-8; NMH-49;"))

    def test_dash_placeholder_rejected(self):
        self.assertIsNone(_schive("Schive-–; Bruun-3831;"))


class SchiveCanonicalForm(unittest.TestCase):
    """The catalogue spells the plate/number separator three ways for the
    same kind of reference; the parser emits one canonical «PLATE:NUMS»."""

    def test_pl_prefixed_citation_recovered(self):
        # lot 1001 — was captured as the literal «pl.», losing the index.
        self.assertEqual(_schive("Schive-pl. XIV , 38; Bruun-3831."), "XIV:38")

    def test_hyphen_separator_folded(self):
        # lot 12005 — «III-21» is the same reference as the 38 siblings'
        # «III:21» form.
        self.assertEqual(_schive("Schive-III-21; NM-11;"), "III:21")

    def test_range_keeps_its_own_hyphen(self):
        self.assertEqual(_schive("Schive-XVIII:10-12; Schou-1;"), "XVIII:10-12")
        self.assertEqual(_schive("Schive-XVII:24-27; Schou-5;"), "XVII:24-27")

    def test_wrapped_space_after_dash(self):
        # «Schive- XIV:26» — the PDF line-wrap leaves a space.
        self.assertEqual(_schive("Schive- XIV:26; Schou-215;"), "XIV:26")

    def test_t_plate(self):
        self.assertEqual(_schive("Schive-T:7; NM-7; NMH-56;"), "T:7")


if __name__ == "__main__":
    unittest.main()
