"""A page sometimes disagrees with a shared Müntzfuß card about one line.

The Danish site says «coinage standard» where the German pages keep
«Müntzfuß», and the sentence sits inside a `grundwerte` row. Overriding
`rows` was the only lever, and it replaces the whole list — restating a
six-row card in three languages to change one word meant duplicating ~27 KB
of prose into denmark.yml and leaving two copies to drift apart.

`rows_patch` edits one shared row in place. It is keyed by the row's GERMAN
key text because that is the authoring language, is mandatory on every
`I18nText`, and is distinct across all 107 rows in `fuesse.yml` — unlike a
list index, which silently points at the wrong row the moment someone
inserts one above it.

Two things here are load-bearing rather than obvious:

  * `rows` KEEPS its full-replacement meaning. Two pages rely on it with
    lists of a different LENGTH than the shared one (denmark supplies 7 rows
    against 3 shared for reichsdukatenfuss; schleswig_holstein 4 against 6
    for rhinsk_gylden_fod). Had the patch been implemented by redefining
    `rows` to merge positionally, the Schleswig-Holstein card would have
    silently grown the two shared rows its override exists to drop.

  * A patch that matches nothing RAISES. The failure it guards against is a
    shared row being reworded later: the patch would then quietly stop
    applying and the page would go back to showing the very wording the
    patch was written to change — with no error anywhere.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from lib.categorize import _merge_grundwerte  # noqa: E402
from lib.schema import Grundwerte  # noqa: E402


def _row(de, en, uk, vde="V-de", ven="V-en", vuk="V-uk"):
    return {"key": {"de": de, "en": en, "uk": uk},
            "value": {"de": vde, "en": ven, "uk": vuk}}


BASE = Grundwerte(
    heading={"de": "H-de", "en": "H-en", "uk": "H-uk"},
    rows=[
        _row("Müntzfuß-Formel", "Münzfuß formula", "Формула стопи"),
        _row("Feingehalt", "Fineness", "Проба"),
        _row("Verhältnis zu anderen Müntzfüßen", "Relation to others",
             "Відношення до інших", "de-text", "Standalone Münzfuß family",
             "Самостійна родина Müntzfuß"),
    ],
)


class RowsPatch(unittest.TestCase):
    def patch(self, patch):
        return _merge_grundwerte(BASE, Grundwerte(rows_patch=patch))

    def test_patches_only_the_named_row_and_only_the_named_languages(self):
        g = self.patch({"Verhältnis zu anderen Müntzfüßen":
                        {"value": {"en": "Standalone coinage-standard family"}}})
        self.assertEqual(len(g.rows), 3)
        self.assertEqual(g.rows[2].value.en, "Standalone coinage-standard family")
        # uk and de on the same row are inherited, not blanked
        self.assertEqual(g.rows[2].value.uk, "Самостійна родина Müntzfuß")
        self.assertEqual(g.rows[2].value.de, "de-text")
        # and the other rows are untouched
        self.assertEqual(g.rows[0].key.en, "Münzfuß formula")

    def test_patches_the_key_as_well_as_the_value(self):
        g = self.patch({"Müntzfuß-Formel": {"key": {"en": "Coinage-standard formula"}}})
        self.assertEqual(g.rows[0].key.en, "Coinage-standard formula")
        self.assertEqual(g.rows[0].key.uk, "Формула стопи")

    def test_everything_outside_rows_survives(self):
        g = self.patch({"Feingehalt": {"value": {"uk": "Проба (уточнено)"}}})
        self.assertEqual(g.heading.de, "H-de")

    def test_an_unmatched_key_raises_rather_than_doing_nothing(self):
        """The row was reworded and the patch now hits nothing — the page
        would otherwise go back to the shared text without a word of warning."""
        with self.assertRaises(ValueError) as cm:
            self.patch({"Formel die es nicht gibt": {"value": {"en": "x"}}})
        self.assertIn("matched 0 rows", str(cm.exception))

    def test_an_ambiguous_key_raises(self):
        base = Grundwerte(rows=[_row("Dublette", "a", "a"), _row("Dublette", "b", "b")])
        with self.assertRaises(ValueError):
            _merge_grundwerte(base, Grundwerte(
                rows_patch={"Dublette": {"value": {"en": "x"}}}))

    def test_rows_patch_does_not_leak_into_the_rendered_card(self):
        g = self.patch({"Feingehalt": {"value": {"en": "x"}}})
        self.assertIsNone(g.rows_patch)


class RowsStillReplacesWholesale(unittest.TestCase):
    """The behaviour two shipped pages depend on."""

    def test_a_shorter_override_list_does_not_inherit_the_shared_tail(self):
        """schleswig_holstein/rhinsk_gylden_fod overrides 6 shared rows with 4.
        A positional merge would hand it back the two it dropped."""
        g = _merge_grundwerte(BASE, Grundwerte(rows=[_row("Nur eine", "only one", "лише один")]))
        self.assertEqual(len(g.rows), 1)
        self.assertEqual(g.rows[0].key.en, "only one")

    def test_a_longer_override_list_is_taken_as_given(self):
        """denmark/reichsdukatenfuss supplies 7 rows against 3 shared."""
        rows = [_row(f"K{i}", f"k{i}", f"к{i}") for i in range(7)]
        g = _merge_grundwerte(BASE, Grundwerte(rows=rows))
        self.assertEqual(len(g.rows), 7)

    def test_rows_and_rows_patch_compose_in_that_order(self):
        g = _merge_grundwerte(BASE, Grundwerte(
            rows=[_row("Neu", "new", "новий")],
            rows_patch={"Neu": {"value": {"en": "patched"}}}))
        self.assertEqual(len(g.rows), 1)
        self.assertEqual(g.rows[0].value.en, "patched")


class ShippedPatches(unittest.TestCase):
    """The four rows denmark.yml actually patches today."""

    def test_every_shipped_patch_key_resolves(self):
        import yaml
        with open(ROOT / "data/shared/fuesse.yml", encoding="utf-8") as fh:
            fuesse = yaml.safe_load(fh)
        with open(ROOT / "data/v2/locations/denmark.yml", encoding="utf-8") as fh:
            loc = yaml.safe_load(fh)
        found = 0
        for fuss, fp in (loc.get("fuss_periods") or {}).items():
            patch = ((fp or {}).get("grundwerte") or {}).get("rows_patch") or {}
            for de_key in patch:
                found += 1
                shared = (fuesse[fuss].get("grundwerte") or {}).get("rows") or []
                keys = [(r.get("key") or {}).get("de") for r in shared]
                self.assertIn(de_key, keys,
                              f"{fuss}: patch key {de_key!r} is not in the shared card")
        self.assertGreater(found, 0, "no shipped patches found — did they move?")


if __name__ == "__main__":
    unittest.main()
