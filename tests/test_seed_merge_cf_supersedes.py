"""A re-seed that learns a «cf.» qualifier must not keep the bare index too.

Caught 2026-10-17. KMM typeNumber «Sch. 44, cf.» was parsed as `schou: '44'`
— the coin's own Schou number — although «cf.» says Schou 44 is a SIMILAR
coin. Once the KMM parser kept the qualifier and emitted `'cf. 44'`, the
merge-aware writer UNIONED it with the stored `'44'`, so nine seeds went on
claiming the bare index alongside the corrected form. Hand-pruning them fixed
the data once; the curator asked for the rule instead, so the next parser
refinement of this kind cleans itself.

`_drop_bare_superseded_by_cf` runs after the catalogue union in `merge_one`.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from lib.seed_merge import _drop_bare_superseded_by_cf, merge_one  # noqa: E402
from ruamel.yaml.comments import CommentedMap  # noqa: E402


def _entry(schou):
    return CommentedMap({"id": "kmk-273648", "catalog": CommentedMap({"schou": schou})})


class TestCfSupersedesBare(unittest.TestCase):
    def test_fresh_cf_replaces_stored_bare(self):
        out = merge_one(_entry("44"), _entry("cf. 44"))
        self.assertEqual(out["catalog"]["schou"], "cf. 44")

    def test_rerun_is_idempotent(self):
        out = merge_one(_entry("cf. 44"), _entry("cf. 44"))
        self.assertEqual(out["catalog"]["schou"], "cf. 44")

    def test_unrelated_bare_value_kept(self):
        self.assertEqual(_drop_bare_superseded_by_cf(["45", "cf. 44"]), ["45", "cf. 44"])

    def test_two_bare_values_untouched(self):
        self.assertEqual(_drop_bare_superseded_by_cf(["44", "45"]), ["44", "45"])


if __name__ == "__main__":
    unittest.main()
