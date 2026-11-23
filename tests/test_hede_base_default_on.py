"""The Hede-base rule is on unless HEDE_BASE=0 (curator 2026-11-23, D57).

It ran opt-in (HEDE_BASE=1) while the curator reviewed every group it would
join across finals; once that review reached zero, it became the default.
"""
import importlib
import os
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "maintenance"))


def _rule_with(env):
    with mock.patch.dict(os.environ, env, clear=False):
        if "HEDE_BASE" not in env:
            os.environ.pop("HEDE_BASE", None)
        import merge_seeds_cross_source as m
        m = importlib.reload(m)
        return m._HEDE_BASE_RULE


class HedeBaseDefault(unittest.TestCase):
    def tearDown(self):
        os.environ.pop("HEDE_BASE", None)
        import merge_seeds_cross_source as m
        importlib.reload(m)

    def test_on_when_unset(self):
        self.assertTrue(_rule_with({}))

    def test_on_when_one(self):
        self.assertTrue(_rule_with({"HEDE_BASE": "1"}))

    def test_off_when_zero(self):
        self.assertFalse(_rule_with({"HEDE_BASE": "0"}))


if __name__ == "__main__":
    unittest.main()
