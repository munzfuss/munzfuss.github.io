"""`trace_coin why` called a §9a-folded specimen «not a seed id» and stopped.

A specimen the kmk seed builder folded into a representative (CLAUDE.md §9a,
`lib/seed_thin`) has no seed record of its own: its id lives only in the
representative's `_thinned_from`. `why kmk-130729` therefore printed «not a
seed id — trace it first», although the specimen's weight, citation and
every curator layer are readable off the representative, and the decision
that names the folded id resolves through it (D49 stage 1). Curator
2026-10-22: «так може навчити її коректно читати випадки з thinned».
"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "maintenance"))

import trace_coin as tc  # noqa: E402


class FoldedSpecimen(unittest.TestCase):
    def test_folded_id_resolves_to_its_representative(self):
        with tempfile.TemporaryDirectory() as tmp:
            v2 = Path(tmp)
            (v2 / "seed" / "kmk").mkdir(parents=True)
            (v2 / "seed" / "kmk" / "danish_realm.yml").write_text(yaml.safe_dump({
                "coins": [{"id": "kmk-1", "_thinned_from": ["kmk-2", "kmk-3"]},
                          {"id": "kmk-9"}]}), encoding="utf-8")
            saved = tc.V2
            tc.V2 = v2
            try:
                self.assertEqual([c["id"] for _, c in tc._folded_into("kmk-2")], ["kmk-1"])
                self.assertEqual(tc._folded_into("kmk-9"), [])      # a live seed
                self.assertEqual(tc._folded_into("kmk-0"), [])      # unknown
                self.assertEqual([c["id"] for _, c in tc._seed_entries("kmk-9")], ["kmk-9"])
                self.assertEqual(tc._seed_entries("kmk-2"), [])
            finally:
                tc.V2 = saved


if __name__ == "__main__":
    unittest.main()
