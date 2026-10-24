"""The DE page writes a Danish king's ordinal with a period, the other
languages without; the data stores «Christian IV» (curator 2026-10-24). The
DE period is added only to coins of a Fuß in data/v2/_rebuild_scope.yml.

    .venv/bin/python -m unittest tests.test_ruler_render_period -v
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from lib import render  # noqa: E402

NB = " "


class RulerRender(unittest.TestCase):
    def setUp(self):
        self._saved = render._REBUILD_SCOPE
        render._REBUILD_SCOPE = frozenset({"rhinsk_gylden_fod"})

    def tearDown(self):
        render._REBUILD_SCOPE = self._saved

    def test_de_adds_period_in_scope(self):
        self.assertEqual(render.ruler_for_lang("Christian IV", "de", "rhinsk_gylden_fod"),
                         f"Christian{NB}IV.")
        self.assertEqual(render.ruler_for_lang("Christian IV.", "de", "rhinsk_gylden_fod"),
                         f"Christian{NB}IV.")

    def test_de_out_of_scope_shows_stored_form(self):
        self.assertEqual(render.ruler_for_lang("Christian IV", "de", "luebischer_muenzfuss"),
                         f"Christian{NB}IV")
        self.assertEqual(render.ruler_for_lang("Christian IV.", "de", None), f"Christian{NB}IV.")

    def test_other_languages_never_show_period(self):
        for lang in ("da", "en", "uk"):
            for raw in ("Christian IV", "Christian IV."):
                self.assertEqual(render.ruler_for_lang(raw, lang, "rhinsk_gylden_fod"),
                                 f"Christian{NB}IV", (raw, lang))

    def test_compound_forms_untouched_on_de(self):
        for raw in ("Christian I/Hans", "Christian V / Frederick III", "Frederik III von Gottorp",
                    "George II", "Hans"):
            out = render.ruler_for_lang(raw, "de", "rhinsk_gylden_fod")
            self.assertEqual(out.replace(NB, " "), raw, raw)


if __name__ == "__main__":
    unittest.main()
