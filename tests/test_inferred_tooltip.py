"""The «[ ]» tooltip of a value the pipeline supplies says that the sources
give none and where the shown value comes from — never the value itself,
which stands in the cell (curator 2026-11-03). A dating compiled from works
keeps its own form."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from lib import i18n, render  # noqa: E402
from lib.compute import DERIVED_SEP  # noqa: E402

UI = i18n.load_ui(str(ROOT / "data" / "i18n" / "ui.yml"))


def coin(field, *entries, **kw):
    return {"id": "x", "fuss": "rhinsk_gylden_fod", "ruler": "Christian II.",
            "uncertainty": {field: list(entries)}, **kw}


class Basis(unittest.TestCase):
    def test_standard_fineness_names_the_fuss_not_the_value(self):
        c = coin("fineness", {"kind": "inferred", "how": "standard",
                              "source": "standard", "value": "18½ Karat"})
        tip = render.uncertainty_mark(c, "fineness", UI, "uk")["tip"]
        self.assertEqual(tip, "Джерела проби не подають. "
                              "Її виведено з параметрів стопи [b]Guldgyldenfod[/b].")

    def test_standard_weight_keeps_the_fraction(self):
        c = coin("weight", {"kind": "inferred", "how": "standard_weight",
                            "source": "standard", "value": "1/71⅓ Cöllnische Marck"})
        tip = render.uncertainty_mark(c, "weight", UI, "en")["tip"]
        self.assertIn("[b]Guldgyldenfod[/b]: 1/71⅓ Cöllnische Marck.", tip)

    def test_reign_with_source_mark_translated(self):
        c = coin("year", {"kind": "inferred", "how": "reign", "source": "galster",
                          "as_printed": "u.år", "value": "1513-1523"},
                 year_label="1513-1523")
        uk = render.uncertainty_mark(c, "year", UI, "uk")["tip"].split("\n")
        self.assertEqual(uk[0], "Джерела року не подають. Наведено роки правління Christian II.")
        self.assertEqual(uk[1], "[b]Galster (danskmoent.dk)[/b]: [i]«u.år»[/i] («без року»)")
        da = render.uncertainty_mark(c, "year", UI, "da")["tip"]
        self.assertTrue(da.endswith("[i]«u.år»[/i]"))   # Danish mark, Danish page

    def test_metal_entry_survives_rendering_in_another_language(self):
        c = coin("metal", {"kind": "inferred", "how": "from_name", "source": "galster",
                           "as_printed": "Hvid", "value": "billon"}, metal="billon")
        self.assertIsNotNone(render.uncertainty_mark(c, "metal", UI, "uk"))
        self.assertIsNotNone(render.uncertainty_mark(c, "metal", UI, "de"))

    def test_compiled_dating_keeps_its_form(self):
        c = coin("year", {"kind": "inferred", "how": "compiled", "source": "Märcher 2018",
                          "as_printed": "ca. 1400", "value": "1403-1413"},
                 {"kind": "inferred", "how": "reign", "source": "galster",
                  "as_printed": "u.år", "value": "1403-1413"},
                 year_label="1403-1413")
        tip = render.uncertainty_mark(c, "year", UI, "uk")["tip"]
        self.assertTrue(tip.startswith("зведено з датувань джерел: 1403-1413"))
        self.assertIn("роки правління: 1403-1413", tip)


class FussLabel(unittest.TestCase):
    def test_value_and_derived_tooltips_name_the_basis(self):
        self.assertEqual(render.resolve_tips(["Guldgyldenfod"], UI, "uk"),
                         "Значення виведено з параметрів стопи [b]Guldgyldenfod[/b].")
        d = render.resolve_tips([DERIVED_SEP.join(
            ["marker.derived_weight", "Guldgyldenfod"])], UI, "en")
        self.assertIn("the parameters of the standard [b]Guldgyldenfod[/b]", d)
        self.assertEqual(render.resolve_tips(["Bruun Part III, lot 11304"], UI, "uk"),
                         "Bruun Part III, lot 11304")


if __name__ == "__main__":
    unittest.main()
