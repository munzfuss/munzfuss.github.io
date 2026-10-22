"""The merger records seeds that left a class which kept its id.

2026-10-19: splitting Hede 87 / 91 / 95 kept the class id
unified-dk-hede-f3h87ab while the KM 192 records moved to Hede 91. Absorb only
decontaminated finals for class ids that VANISHED, so the Hede 87 final kept
KM 192.x. The merger now writes `match_uncertainty/<entity>.departed.json`
({class id: [seeds that left]}); absorb removes what
those seeds alone contributed.
"""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "maintenance"))
import merge_seeds_cross_source as M  # noqa: E402


class TestDepartedSidecar(unittest.TestCase):
    def test_departed_written(self):
        with tempfile.TemporaryDirectory() as tmp:
            su, mu = Path(tmp, "su"), Path(tmp, "mu")
            su.mkdir()
            (su / "x.yml").write_text(yaml.safe_dump({"coins": [
                {"id": "unified-a", "composed_of": ["a", "b", "c"]}]}), encoding="utf-8")
            old_su, old_mu = M.V2_SEED_UNIFIED, M.V2_MATCH_UNCERTAINTY
            M.V2_SEED_UNIFIED, M.V2_MATCH_UNCERTAINTY = su, mu
            try:
                M._write_departed("x", [{"id": "unified-a", "composed_of": ["a"]},
                                            {"id": "unified-b", "composed_of": ["b", "c"]}])
            finally:
                M.V2_SEED_UNIFIED, M.V2_MATCH_UNCERTAINTY = old_su, old_mu
            dep = json.loads((mu / "x.departed.json").read_text(encoding="utf-8"))
            self.assertFalse((mu / "x.prev_classes.json").exists())
        self.assertEqual(dep, {"unified-a": ["b", "c"]})


if __name__ == "__main__":
    unittest.main()
