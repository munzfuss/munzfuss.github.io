"""catalog_from_ref_dict drops dash/placeholder «no number» markers.

Sources print «–» / «-» / «,» in a catalogue column to mean «this coin has no
number in that catalogue» (Bruun lot «Schive: –», Hede «Sieg: -»). Those are NOT
references — they must never land in a typed catalog field as a phantom index.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from lib.catalog_codes import catalog_from_ref_dict  # noqa: E402

_MAP = {"Schive": "schive", "Skjoldager": "jensen_skjoldager",
        "Sieg": "sieg", "Galster": "galster"}


class TestDashSkip(unittest.TestCase):
    def test_dash_markers_dropped_real_refs_kept(self):
        out = catalog_from_ref_dict(
            {"Schive": "–", "Skjoldager": "–", "Sieg": "26", "Galster": "60"},
            key_field_map=_MAP)
        self.assertEqual(out, {"sieg": "26", "galster": "60"})
        self.assertNotIn("schive", out)
        self.assertNotIn("jensen_skjoldager", out)

    def test_all_dash_variants_dropped(self):
        for dash in ("-", "–", "—", "−", "--"):
            out = catalog_from_ref_dict({"Sieg": dash}, key_field_map=_MAP)
            self.assertEqual(out, {}, f"{dash!r} not dropped")

    def test_bare_comma_dropped(self):
        # Bruun lot «Skjoldager: ,» — the trailing-comma strip leaves empty
        out = catalog_from_ref_dict({"Skjoldager": ","}, key_field_map=_MAP)
        self.assertEqual(out, {})

    def test_real_index_with_letter_kept(self):
        out = catalog_from_ref_dict({"Sieg": "80.1", "Schou": "11"},
                                    key_field_map={**_MAP, "Schou": "schou"})
        self.assertEqual(out, {"sieg": "80.1", "schou": "11"})


if __name__ == "__main__":
    unittest.main()
