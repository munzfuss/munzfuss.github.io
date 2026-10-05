"""`yaml_io.edit_coin_field` replacing or removing a BLOCK field.

It matched a list field's items only at the key's own indent. The V2 seed
families write sequences offset by two («mint:» then «  - CPS»), so replacing
or removing such a field left the items behind as orphans — invalid YAML that
the next loader refused (2026-10-05, a ucoin seed's `mint: [CPS, IWS]` → None).
"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from lib.yaml_io import edit_coin_field  # noqa: E402

DOC = """coins:
  - id: a
    mint:
      - CPS
      - IWS
    mint_verified: true
    catalog:
      fiala: IV
    ruler: X
  - id: b
    mint: Altona
"""


class BlockField(unittest.TestCase):
    def _edit(self, field, value):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "x.yml"
            p.write_text(DOC)
            edit_coin_field(p, "a", field, value)
            return yaml.safe_load(p.read_text())["coins"]

    def test_remove_offset_list(self):
        a, b = self._edit("mint", None)
        self.assertNotIn("mint", a)
        self.assertTrue(a["mint_verified"])
        self.assertEqual(b["mint"], "Altona")

    def test_replace_offset_list_with_scalar(self):
        a, _ = self._edit("mint", "Zellerfeld")
        self.assertEqual(a["mint"], "Zellerfeld")

    def test_replace_offset_list_keeps_offset(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "x.yml"
            p.write_text(DOC)
            edit_coin_field(p, "a", "mint", ["Goslar", "Zellerfeld"])
            self.assertIn("    mint:\n      - 'Goslar'\n      - 'Zellerfeld'\n", p.read_text())
            self.assertEqual(yaml.safe_load(p.read_text())["coins"][0]["mint"], ["Goslar", "Zellerfeld"])

    def test_remove_nested_mapping(self):
        a, _ = self._edit("catalog", None)
        self.assertNotIn("catalog", a)
        self.assertEqual(a["ruler"], "X")


if __name__ == "__main__":
    unittest.main()
