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
            self.assertIn("    mint:\n      - Goslar\n      - Zellerfeld\n", p.read_text())
            self.assertEqual(yaml.safe_load(p.read_text())["coins"][0]["mint"], ["Goslar", "Zellerfeld"])

    def test_scalar_to_list_uses_the_family_offset(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "data" / "v2" / "seed" / "kmk"
            p.mkdir(parents=True)
            f = p / "x.yml"
            f.write_text(DOC)
            edit_coin_field(f, "b", "mint", ["Goslar", "Zellerfeld"])
            self.assertIn("    mint:\n      - Goslar\n      - Zellerfeld\n", f.read_text())

    def test_remove_nested_mapping(self):
        a, _ = self._edit("catalog", None)
        self.assertNotIn("catalog", a)
        self.assertEqual(a["ruler"], "X")


if __name__ == "__main__":
    unittest.main()


FINAL_DOC = """coins:
  - fuss: a
    mintmaster: Goslar; X
    id: one
    mint: Zellerfeld
  - fuss: b
    mintmaster: Goslar; Y
    id: two
    mint: Zellerfeld
  - fuss: c
    id: three
    mint: Altona
"""


class IdNotFirstKey(unittest.TestCase):
    """In data/v2/final/*.yml `id` is not the item's first key, so the block
    must start at the item's «- » marker, not at the `id:` line."""

    def _edit(self, cid, field, value):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "x.yml"
            p.write_text(FINAL_DOC)
            edit_coin_field(p, cid, field, value)
            return {c["id"]: c for c in yaml.safe_load(p.read_text())["coins"]}

    def test_field_before_id_hits_its_own_coin(self):
        c = self._edit("one", "mintmaster", "X")
        self.assertEqual(c["one"]["mintmaster"], "X")
        self.assertEqual(c["two"]["mintmaster"], "Goslar; Y")

    def test_absent_field_never_reaches_the_next_coin(self):
        with self.assertRaises(KeyError):
            self._edit("three", "mintmaster", None)
        c = self._edit("two", "mintmaster", None)
        self.assertNotIn("mintmaster", c["two"])
        self.assertEqual(c["one"]["mintmaster"], "Goslar; X")


class EditGuard(unittest.TestCase):
    """`_assert_edit_landed` refuses an edit whose result is not the coin and
    field state that was asked for — before anything is written."""

    def test_guard_refuses_wrong_coin(self):
        from lib import yaml_io
        lines = FINAL_DOC.split("\n")
        with self.assertRaises(RuntimeError):
            yaml_io._assert_edit_landed(lines, "one", "mintmaster", "Z", Path("x.yml"))

    def test_guard_accepts_alias_in_block(self):
        from lib import yaml_io
        lines = (FINAL_DOC.replace("    mint: Zellerfeld\n  - fuss: b",
                                   "    mint: Zellerfeld\n    verification_note: *id001\n  - fuss: b")).split("\n")
        yaml_io._assert_edit_landed(lines, "one", "mint", "Zellerfeld", Path("x.yml"))
