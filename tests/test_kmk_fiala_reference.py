"""KMM writes a Fiala reference with commas inside it, and the generic
`typeNumber` split cut on those commas.

«Fiala IV, s. 194, 1144» is volume IV, page 194, number 1144. `_catalog` splits
on `[;,]`, so it only ever saw «Fiala IV»: 22 seeds carried the bare volume,
18 of them sharing `fiala: IV` across different talers — a false edge for any
§9.4 index graph. Catalogues are separated by «;», so the Fiala reference runs
to the next «;» and is lifted out before the split.

Pinned here: the reference is kept verbatim («var.» with its full stop, a
page-only form, a trailing «; Dav …» left to its own catalogue), a comparison
reference — «cf.», or its Danish form «jfr.» — yields no Fiala value at all
(CLAUDE.md anti-pattern 5), and the «4 nr. 325» notation that never had a comma
is unchanged.
"""
from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "maintenance"))

_spec = importlib.util.spec_from_file_location(
    "build_kmk_seed_for_fiala_test", ROOT / "scripts" / "maintenance" / "build_kmk_seed.py"
)
bks = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(bks)


def cat(type_number: str) -> dict:
    return bks._catalog({"id": 0, "typeNumber": type_number})


class FialaReferenceKeptWhole(unittest.TestCase):
    def test_volume_page_number(self):
        # Verbatim typeNumber of KMM 184212.
        self.assertEqual(cat("Fiala IV, s. 194, 1144"), {"fiala": "IV, s. 194, 1144"})

    def test_var_keeps_its_full_stop(self):
        # KMM 184202.
        self.assertEqual(cat("Fiala VI, 65 var."), {"fiala": "VI, 65 var."})

    def test_page_only(self):
        # KMM 184207.
        self.assertEqual(cat("Fiala IV, s. 179"), {"fiala": "IV, s. 179"})

    def test_following_catalogue_survives(self):
        # KMM 187970.
        self.assertEqual(cat("Fiala IV, s. 181, 1001; Dav 6307"),
                         {"fiala": "IV, s. 181, 1001", "dav": "6307"})

    def test_nr_notation_unchanged(self):
        # KMM 714567.
        self.assertEqual(cat("Welter 593; Fiala 4 nr. 325"),
                         {"fiala": "4 nr. 325", "welter": "593"})


class NormaliserKeepsFialaWhole(unittest.TestCase):
    """The parser was right and the cross-source normaliser undid it: Fiala sat
    in the comma-flattening numeric-index set, so «IV, s. 181, 1000» became
    ['1000', 'IV', 's. 181'] in seed_unified and «1000» in final, and the
    general «var.»-strip ate «65 var.»."""

    def test_volume_page_number_survives(self):
        from lib.catalog_codes import normalise_catalog
        for v in ("IV, s. 181, 1000", "VI, 65 var.", "4 nr. 905*-07"):
            c = {"fiala": v}
            normalise_catalog(c)
            self.assertEqual(c, {"fiala": v})


class ComparisonReferenceDropped(unittest.TestCase):
    def test_cf(self):
        # KMM 184211.
        self.assertNotIn("fiala", cat("Fiala IV, s. 194, cf. 1144"))

    def test_danish_jfr(self):
        # KMM 184201.
        self.assertNotIn("fiala", cat("Fiala VI, jfr. 164/76"))


if __name__ == "__main__":
    unittest.main()
