"""Danish renders on one site, and nothing in the build complains when it is
missing.

That is the whole reason this file exists. `i18n.FALLBACK`, `I18nText.resolve`
and `refs_pool` each independently fall back to English and then German, so an
absent Danish string produces a page that renders, validates, passes every
audit and exits 0 — while quietly showing the reader another language. For the
historical prose that is the deliberate state today. For the CHROME it is not:
navigation, column headers and category labels are the part that was
translated, and a gap there would be a regression nobody would be told about.

The second class pins the two dicts that were indexed by `lang` directly. A
missing key there was worse than a fallback — `metals[metal][lang]` on an
unlisted language is Jinja Undefined, which renders as an empty cell.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from lib import i18n  # noqa: E402
from lib.render import _FIN_UNITS  # noqa: E402

UI = yaml.safe_load((ROOT / "data/i18n/ui.yml").read_text(encoding="utf-8"))
ENTITIES = yaml.safe_load(
    (ROOT / "data/i18n/issuing_entities.yml").read_text(encoding="utf-8"))

# The entities data/v2/locations/denmark.yml consumes — the only ones whose
# names a Danish reader ever sees.
DANISH_PAGE_ENTITIES = {
    "danish_realm", "danish_norway", "royal_holstein", "royal_slesvig",
    "gottorp_duchy", "sonderburg_duchy", "norburg_plon_duchy",
    "glucksburg_duchy",
}


class UiStringsAreComplete(unittest.TestCase):
    def test_every_ui_key_carries_danish(self):
        missing = sorted(k for k, v in UI.items() if not (v or {}).get("da"))
        self.assertEqual(missing, [], f"{len(missing)} UI keys without Danish")

    def test_the_three_older_languages_did_not_lose_anything(self):
        for lang in ("de", "en", "uk"):
            missing = sorted(k for k, v in UI.items() if not (v or {}).get(lang))
            with self.subTest(lang=lang):
                self.assertEqual(missing, [])

    def test_every_entity_on_the_danish_page_is_named_in_danish(self):
        for eid in sorted(DANISH_PAGE_ENTITIES):
            with self.subTest(entity=eid):
                ent = ENTITIES[eid]
                for field in ("name", "short", "description"):
                    self.assertTrue((ent.get(field) or {}).get("da"),
                                    f"{eid}.{field} has no Danish")

    def test_ui_lookup_returns_danish_rather_than_falling_back(self):
        """`ui_get` returns «[key]» for a key it cannot resolve at all, and
        the English string when Danish is absent — both of which would pass a
        naive «did it return something» check."""
        self.assertEqual(i18n.ui_get(UI, "col.fuss", "da"), "Møntfod")
        self.assertEqual(i18n.ui_get(UI, "nav.home", "da"), "Forside")


class DanishIsNotTreatedAsEnglish(unittest.TestCase):
    """The pieces that would have been WRONG rather than untranslated."""

    def test_numbers_carry_a_decimal_comma(self):
        """Danish uses a comma. The test was `lang in ("de", "uk")`, so
        Danish would have printed 28.893 g where every source prints
        28,893 g — a wrong number that reads as a correct one."""
        self.assertEqual(i18n.fmt_num(28.893, "da", decimals=3), "28,893 g")
        self.assertEqual(i18n.fmt_num(28.893, "en", decimals=3), "28.893 g")

    def test_percentages_too(self):
        self.assertIn(",", i18n.fmt_pct(-1.31, "da"))

    def test_months_are_danish_and_the_day_is_an_ordinal(self):
        self.assertEqual(i18n.fmt_date("2026-04-27", "da"), "27. april 2026")

    def test_fineness_units_are_danish(self):
        """`lod`, not the German `Lot` — the lookup used to fall back to the
        English labels for any language it did not list."""
        self.assertEqual(_FIN_UNITS["silver"][1]["da"], "lod")
        self.assertEqual(_FIN_UNITS["gold"][1]["da"], "karat")

    def test_the_fallback_chain_is_declared_rather_than_defaulted(self):
        self.assertEqual(i18n.FALLBACK["da"], ["da", "en", "de"])

    def test_an_untranslated_slot_still_falls_back_silently(self):
        """Not a defect — the documented state of the historical prose. Pinned
        so that a future change to the chain is a decision, not an accident."""
        self.assertEqual(i18n.t({"de": "D", "en": "E"}, "da"), "E")
        self.assertEqual(i18n.t({"de": "D"}, "da"), "D")


class MetalNamesCoverEveryRenderedLanguage(unittest.TestCase):
    """These lived as literal maps in location.html.j2 and were indexed by
    `lang`, so an unlisted language rendered an EMPTY metal cell rather than
    falling back."""

    METALS = ("silver", "gold", "billon", "copper", "lead", "bronze", "brass")

    def test_every_metal_is_named_in_every_language(self):
        for metal in self.METALS:
            for lang in ("de", "en", "uk", "da"):
                with self.subTest(metal=metal, lang=lang):
                    self.assertTrue((UI[f"metal.{metal}"] or {}).get(lang))

    def test_the_phase_marker_is_not_ukrainian_by_default(self):
        """It used to read `'Phase ' if lang in ('de','en') else 'Фаза '`."""
        self.assertEqual(UI["phase.label"]["da"], "Fase")


if __name__ == "__main__":
    unittest.main()
