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
from lib.compute import DERIVED_SEP  # noqa: E402
from lib.render import _FIN_UNITS, resolve_tips, strip_phase_marker  # noqa: E402

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


class PhaseMarkerIsNotDoubled(unittest.TestCase):
    """The template prints «Fase I · » and the title may still open with
    «Phase I · », because the marker is localised and the title falls back.
    Six of the Danish page's 36 phase headings read «Fase I · 1514 → 1532 ·
    Phase I · …» before the strip stopped keying on the current language."""

    def test_a_marker_in_another_language_is_still_stripped(self):
        self.assertEqual(
            strip_phase_marker("Phase I · de-jure standard", "I"),
            "de-jure standard")
        self.assertEqual(strip_phase_marker("Фаза III · щось", "III"), "щось")
        self.assertEqual(strip_phase_marker("Fase I · x", "I"), "x")

    def test_a_different_phase_id_is_left_alone(self):
        """«Phase II · …» under phase I is not this phase's marker."""
        self.assertEqual(strip_phase_marker("Phase II · x", "I"),
                         "Phase II · x")

    def test_a_descriptive_title_survives_intact(self):
        """A title may legitimately open with a name and a middle dot."""
        for title in ("Christian II · 1514 reform", "de-jure standard", ""):
            with self.subTest(title=title):
                self.assertEqual(strip_phase_marker(title, "I"), title)

    def test_none_does_not_crash(self):
        self.assertEqual(strip_phase_marker(None, "I"), "")


class DerivedTooltipsAreLocalised(unittest.TestCase):
    """`compute_location` runs ONCE per location while the page renders in
    every language the site publishes, so a sentence written there is frozen
    for all of them. This one was written in Ukrainian, and ~12 900 of them
    shipped on every German and English page. It is a key plus arguments now,
    resolved per language at render time — the same thing
    `_HEDE_NORGE_TOOLTIP_*` already did."""

    def tip(self, lang, *parts):
        return resolve_tips([DERIVED_SEP.join(parts)], UI, lang)

    def test_each_language_gets_its_own_sentence(self):
        got = {l: self.tip(l, "marker.derived_split", "bruun", "hede")
               for l in ("de", "en", "uk", "da")}
        self.assertEqual(len(set(got.values())), 4, got)
        for lang, text in got.items():
            with self.subTest(lang=lang):
                self.assertIn("bruun", text)
                self.assertIn("hede", text)

    def test_no_language_gets_the_ukrainian_one(self):
        for lang in ("de", "en", "da"):
            with self.subTest(lang=lang):
                self.assertNotIn("Обчислено", self.tip(lang, "marker.derived_both", "kmk"))

    def test_a_plain_source_label_passes_through_untouched(self):
        """Most tooltip lines are source names, not keys."""
        self.assertEqual(resolve_tips(["kmk", "numista"], UI, "de"), "kmk\nnumista")

    def test_an_unknown_key_shows_the_sources_not_a_bracketed_key(self):
        """A tooltip is an aid; «[marker.nope]» in place of it is worse than
        the bare label."""
        self.assertEqual(self.tip("de", "marker.nope", "kmk"), "kmk")

    def test_a_source_label_containing_a_brace_survives(self):
        """`.format` would raise on it; the substitution is a plain replace."""
        self.assertIn("a{b}c", self.tip("en", "marker.derived_weight", "a{b}c"))

    def test_every_derived_key_exists_in_all_four_languages(self):
        for key in ("marker.derived_both", "marker.derived_split",
                    "marker.derived_weight", "marker.derived_fineness"):
            for lang in ("de", "en", "uk", "da"):
                with self.subTest(key=key, lang=lang):
                    self.assertTrue((UI[key] or {}).get(lang))


class TemplatesResolveTooltips(unittest.TestCase):
    def test_the_build_supplies_every_helper_the_template_calls(self):
        """`resolve_tips` was added to `render.py::render_location` — which
        the build does not use. build.py renders through its own context, so
        both full builds died on «'tips' is undefined» after the unit tests
        for the resolver itself had passed. Verifying a helper in isolation
        says nothing about whether the renderer hands it to the template.

        Scans the template for names called as FUNCTIONS, having removed the
        inline <script> blocks (JS keywords are not Jinja) and subtracted the
        filters, which are registered on the environment rather than passed
        in the context. What remains must be bound in build.py — the live
        render path, not render.py's unused one.
        """
        import re
        tpl = (ROOT / "templates/location.html.j2").read_text(encoding="utf-8")
        tpl = re.sub(r"<script.*?</script>", "", tpl, flags=re.S | re.I)
        build = (ROOT / "scripts/build.py").read_text(encoding="utf-8")
        render = (ROOT / "scripts/lib/render.py").read_text(encoding="utf-8")

        called = set(re.findall(r"(?<![.\w])([a-z_][a-z0-9_]*)\(", tpl))
        local = set(re.findall(r"{%-?\s*(?:set|macro)\s+([a-z_][a-z0-9_]*)", tpl))
        filters = set(re.findall(r'env\.filters\[[\'"]([a-z_0-9]+)[\'"]\]', render))
        css = {"var", "calc", "rgb", "rgba", "url", "translate", "clamp"}
        builtins = {"range", "dict", "len", "namespace", "join", "default",
                    "int", "float", "round", "list", "lower", "upper", "trim",
                    "replace", "format", "items", "get", "startswith", "split",
                    "abs", "min", "max", "sum", "attr", "sort"}
        provided = set(re.findall(r"^\s*([a-z_][a-z0-9_]*)=", build, re.M))

        missing = sorted(called - local - filters - builtins - css - provided)
        self.assertEqual(missing, [],
                         f"template calls {missing}; build.py binds none of them")
        # The scan is only meaningful if it actually sees the helpers.
        self.assertIn("tips", called)
        self.assertIn("tips", provided)

    def test_no_measurement_tooltip_joins_raw_sources(self):
        """A `sources|join` left behind would print the raw
        «marker.derived_split\x1fbruun» at the reader."""
        text = (ROOT / "templates/location.html.j2").read_text(encoding="utf-8")
        for line in text.splitlines():
            if "sources|join" in line:
                self.fail(f"unresolved tooltip join: {line.strip()[:70]}")


if __name__ == "__main__":
    unittest.main()
