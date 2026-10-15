"""§2 used to be «mandatory, DE-only», and the linter enforced it literally.

That framing declared three states violations that were in fact correct:
a verbatim quote carrying the source's spelling (§5a requires it), a URL
or lemma title that breaks when re-spelled, and the proper name of a
treaty or ordinance — which the i18n policy lists in modern orthography
while the §2 table demanded the period form. The audit therefore
reported hundreds of §2 ERRORS against text nobody should change, and
the noise made the one class that mattered (§0z project-meta leaking
into reader prose) impossible to see.

CLAUDE.md §2 was rewritten 2026-09-02 as three tiers: tier 1 is the
source's form, untouchable, and carries the instrument's own LANGUAGE
too; tier 2 is standard names, identical in every language; tier 3 is
our own connective German prose, a recommendation at warning severity.
These tests pin the tiers so a future rule addition cannot quietly
re-break them — the Danish protection in particular used to hold only
by three hand-tuned lookaheads inside unrelated regexes.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import audit_prose as ap  # noqa: E402


def hits(text: str, lang: str = "de") -> list[ap.Hit]:
    return list(ap.lint_text(text, lang, "note", "t.yml", text, None))


def sections(text: str, lang: str = "de") -> set[str]:
    return {h.rule for h in hits(text, lang)}


class Tier1SourceForm(unittest.TestCase):
    def test_verbatim_quote_keeps_its_spelling(self):
        # §5a requires the source's exact words; re-spelling falsifies.
        self.assertNotIn("§2", sections(
            'Wikisource: «Die beiden Staaten vereinbarten, als Münzfuß '
            'den 9-Taler-Fuß der Augsburger Reichsmünzordnung».'))

    def test_url_and_lemma_are_not_respelled(self):
        self.assertNotIn("§2", sections(
            "Wikipedia DE «Zinnaer Münzfuß» — de.wikipedia.org/wiki/Zinnaer Münzfuß."))

    def test_named_instrument_keeps_its_name(self):
        for s in ("Vereinsthaler nach Wiener Münzvertrag 24. Januar 1857.",
                  "Reichsmünzordnung 1559 gilt reichsweit.",
                  "Münzgesetz vom 4. Dezember 1871 führt die Goldmark ein."):
            with self.subTest(s=s):
                self.assertNotIn("§2", sections(s))

    def test_our_own_prose_is_still_flagged_but_only_as_warning(self):
        got = hits("Der Fuß folgt einem eigenen Münzfuß mit reduziertem Gehalt.")
        self.assertTrue(any(h.rule == "§2" for h in got))
        self.assertTrue(all(h.severity == "warning" for h in got if h.rule == "§2"),
                        "tier 3 is a recommendation — never an error")


class Tier1Language(unittest.TestCase):
    """A named instrument carries its own language, not the field's."""

    def test_danish_forms_are_never_flagged(self):
        for s in ("Speciedaler 1671 nach Kurantmøntfod.",
                  "Forordning af 9. Juli 1757 om Kurantdukater.",
                  "Møntordningen af 20. september 1541 gilt für beide Reiche.",
                  "Myndt-Ordning af 22. marts 1671 legt den Krone-Fuß fest.",
                  "Møntloven af 23. maj 1873 führt die Krone ein.",
                  "Plakat 2. december 1782 erlaubt die freie Goldabgabe."):
            with self.subTest(s=s):
                self.assertEqual(set(), sections(s))

    def test_standard_names_are_clean_in_en_and_uk(self):
        # Tier 2: the standard's name is one string project-wide, so the
        # period form inside English or Ukrainian prose is correct.
        for lang, s in (("en", "The Reichsdukatenfuß governed trade gold."),
                        ("uk", "Reichsdukatenfuß діяв для торговельного золота.")):
            with self.subTest(lang=lang):
                self.assertEqual(set(), sections(s, lang))


class Tier1DoesNotExcuseProjectMeta(unittest.TestCase):
    """Tier 1 is about spelling, never about role-3 leakage (§0z)."""

    def test_claude_md_inside_quotes_is_still_an_error(self):
        got = hits("Per Projekt-Konvention «CLAUDE.md §4» gesetzt.")
        self.assertTrue(any(h.rule == "§0z" and h.severity == "error" for h in got))

    def test_todo_section_ids_are_caught(self):
        # «§BF» is a docs/TODO.md backlog entry — and a CLOSED one, so the
        # note tells the reader to wait for a step that already happened.
        for s in ("Verifikation gegen Primärquellen vor §BF-Promotion.",
                  "NumisMaster-Seed (§BK Phase 5): Krause-Mishler-basiert.",
                  "hängt am §AZ Paper-Source-Import."):
            with self.subTest(s=s):
                self.assertIn("§0z", sections(s), f"section id not caught: {s}")

    def test_legal_paragraph_marks_are_not_section_ids(self):
        # A period ordinance quoted verbatim can carry «§ 12»; digit-form
        # marks are deliberately outside the rule (see its comment).
        self.assertNotIn("§0z", sections(
            "Die Ordnung bestimmt in § 12 die Ausbringung je Marck."))

    def test_project_file_and_schema_field_leak(self):
        for s in ("Wert aus fuesse.yml: fineness_display übernommen.",
                  "Flagge bleibt fineness_verified: false.",
                  "Siehe docs/research/moentordning_1541.md.",
                  "noch unklassifiziert (seed_unsorted) biß zur Zuordnung."):
            with self.subTest(s=s):
                self.assertIn("§0z", sections(s), f"leak not caught: {s}")


class AttributedHedges(unittest.TestCase):
    def test_attributed_hedge_is_excused(self):
        self.assertNotIn("§2a", sections(
            "1 Ducat 1716 · Philipp Ernst — laut Bruun extrem selten."))

    def test_our_own_hedge_is_not_excused_by_a_nearby_catalogue_ref(self):
        # The Hede number identifies the coin; it does not attribute the
        # guess about the mintmaster.
        got = hits("8 Skilling 1669 (Hede-121B) · Münzmeister vermutlich Gotfred Krüger.")
        self.assertTrue(any(h.rule == "§0b" for h in got),
                        "a catalogue reference must not silence our own hedge")

    def test_distant_attribution_does_not_reach(self):
        got = hits(
            "zwei Varianten des Münzmeisters nach Hede 26 vereint unter KM-73 "
            "(Numista 420365 gruppiert beide): 26A trekløver, Schou 4, "
            "Sieg 133.1 — vermutlich verschiedene Ausgaben.")
        self.assertTrue(any(h.rule == "§0b" for h in got))



class FirstPersonInsideQuotes(unittest.TestCase):
    """A quotation's own «we / our» is the source speaking (curator 2026-10-15)."""

    @staticmethod
    def _rules(text, lang):
        return [h.rule for h in ap.lint_text(text, lang, "f", "x", text, None)]

    def test_quoted_translation_is_excused(self):
        t = "розміщує двір «binnen unser Stadt Flensburgk» («у нашому місті Flensborg»)."
        self.assertNotIn("§0z", self._rules(t, "uk"))

    def test_unquoted_project_voice_still_fires(self):
        self.assertIn("§0z", self._rules("Це відображено у нашому артефакті.", "uk"))
        self.assertIn("§0a", self._rules("we treat this coin as gold.", "en"))
        self.assertIn("§0a", self._rules("Hier wir behandeln die Müntze.", "de"))

    def test_german_low_quotes_are_quotes_too(self):
        self.assertNotIn("§0a", self._rules("es heißt: „wir behandeln die Müntze“.", "de"))


if __name__ == "__main__":
    unittest.main()
