"""Guards for the 2026-11-03 re-flow speed-ups — each one rests on an
assumption that a later change elsewhere could quietly break.

* Absorb's ConfidentBlocker (lib/confident_blocking.py) skips every final that
  shares no ruler / catalogue / others token with the coin. That is sound only
  while `match_pair` has no `confident` verdict without `ruler` or `catalog`
  True. A new rule that confirms on nominal + metal + year alone would make
  absorb stop finding those finals — the classes would land in seed_unsorted
  and nothing would fail. The first test runs match_pair over every pair of a
  varied synthetic set and checks that each confident pair is a candidate.
* The per-record memo in the merger is live only while a PASS-1 / PASS-2 row is
  evaluated. Outside, a changed record must be read afresh — the reign gate
  (step 2a) runs between the passes.
* lib/yaml_cache must hand back exactly the document a libyaml parse gives, a
  fresh object every time.
"""
from __future__ import annotations

import itertools
import os
import pickle
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "maintenance"))

import yaml  # noqa: E402

import maintenance.merge_seeds_cross_source as mg  # noqa: E402
from lib import confident_blocking as cb  # noqa: E402
from lib import yaml_cache  # noqa: E402


def _coins():
    """Records that agree and disagree on every signal match_pair reads."""
    rulers = [None, "Christian IV", "Frederik III"]
    nominals = [None, "1 Skilling", "2 Skilling", "1 Daler", "1 Speciedaler"]
    catalogs = [
        {}, {"hede": "39", "hede_volume": "c4h"}, {"hede": "39A", "hede_volume": "c4h"},
        {"hede": "39a", "hede_volume": "c4h"}, {"hede": "41", "hede_volume": "c4h"},
        {"km": "70"}, {"km": "70.1"}, {"km": "70.2"}, {"lange": "404A, 405"},
        {"lange": "405"}, {"schou": "29-32"}, {"schou": "32"}, {"sieg": "12"},
        {"others": ["Jesse# 34-41"]}, {"others": ["Jesse# 35"]},
        {"numista": "301095"},
    ]
    metals = [None, "silver", "billon"]
    years = [None, (1624, 1624), (1625, 1630)]
    weights = [None, 1.1, 1.12, 2.4]
    out = []
    for i, (r, n, c) in enumerate(itertools.product(rulers, nominals, catalogs)):
        coin = {"id": f"t-{i}", "ruler": r, "nominal": n, "catalog": dict(c),
                "metal": metals[i % 3]}
        y = years[i % 3]
        if y:
            coin["year_first"], coin["year_last"] = y
            coin["year_ranges"] = [list(y)]
        w = weights[i % 4]
        if w:
            coin["weight_rough_g"] = w
        out.append(coin)
    return out


class ConfidentBlockingIsASuperset(unittest.TestCase):
    def _check(self, reign_index):
        coins = _coins()
        blocker = cb.ConfidentBlocker(coins, "danish_realm", reign_index)
        missed, confident = [], 0
        for a in coins:
            kept = set(blocker.indices(a))
            for j, b in enumerate(coins):
                if a is b:
                    continue
                if mg.match_pair(a, b, "danish_realm",
                                 reign_index=reign_index)["decision"] != "confident":
                    continue
                confident += 1
                if j not in kept:
                    missed.append((a["id"], b["id"]))
        # the set must exercise the matcher, or the check proves nothing
        self.assertGreater(confident, 50)
        self.assertEqual(missed, [], "confident pairs the blocker would skip")

    def test_without_reign_index(self):
        """The self-foundation fold calls match_pair without a reign index."""
        self._check(None)

    def test_with_reign_index(self):
        """The absorb candidate loop infers missing rulers from the years."""
        coins = [c for c in _coins() if c.get("ruler") and c.get("year_first")]
        self._check(mg._build_reign_index(coins, "danish_realm"))


class PerRecordMemoWindow(unittest.TestCase):
    def test_changed_record_is_read_afresh_outside_a_row(self):
        coin = {"id": "x", "weight_rough_g": 1.0}
        mg._per_record_memo_reset()
        self.assertEqual(mg._weight_repr(coin), 1.0)
        coin["weight_rough_g"] = 2.0
        self.assertEqual(mg._weight_repr(coin), 2.0)

    def test_memo_is_live_inside_a_row_and_emptied_by_reset(self):
        coin = {"id": "x", "weight_rough_g": 1.0}
        mg._per_record_memo_reset()

        def row():
            first = mg._weight_repr(coin)
            coin["weight_rough_g"] = 3.0          # never happens in a real row
            return first, mg._weight_repr(coin)

        self.assertEqual(mg._with_record_memo(row)(), (1.0, 1.0))
        self.assertFalse(mg._PER_RECORD_MEMO_ON)
        mg._per_record_memo_reset()
        self.assertEqual(mg._weight_repr(coin), 3.0)

    def test_row_evaluators_still_pickle_by_name(self):
        """The fork pool sends the evaluator by name; the wrapper keeps it."""
        self.assertIs(pickle.loads(pickle.dumps(mg._pass1_eval_i)), mg._pass1_eval_i)
        self.assertIs(pickle.loads(pickle.dumps(mg._pass2_eval_row)), mg._pass2_eval_row)


class YamlCacheGivesTheParse(unittest.TestCase):
    TEXT = ("coins:\n  - id: a\n    weight_rough_g: [{value: 1.5, source: x}]\n"
            "    year_ranges: [[1624, 1625]]\n    note: &n {de: «Witten»}\n"
            "  - id: b\n    note: *n\n    flag: yes\n    date: 2026-11-03\n")

    def setUp(self):
        self._dir = tempfile.TemporaryDirectory()
        self._saved = yaml_cache._DIR
        yaml_cache._DIR = Path(self._dir.name)

    def tearDown(self):
        yaml_cache._DIR = self._saved
        self._dir.cleanup()

    def test_cold_and_warm_equal_libyaml(self):
        want = yaml.load(self.TEXT, Loader=yaml.CSafeLoader)
        cold = yaml_cache.load(self.TEXT)
        warm = yaml_cache.load(self.TEXT)
        self.assertEqual(cold, want)
        self.assertEqual(warm, want)
        self.assertEqual(pickle.dumps(warm), pickle.dumps(want))
        # an alias stays one shared object, as in the parse
        self.assertIs(warm["coins"][0]["note"], warm["coins"][1]["note"])

    def test_every_call_is_a_fresh_object(self):
        first = yaml_cache.load(self.TEXT)
        first["coins"].clear()
        self.assertEqual(len(yaml_cache.load(self.TEXT)["coins"]), 2)

    def test_switch_off(self):
        os.environ["MUNZFUSS_YAML_CACHE"] = "0"
        try:
            yaml_cache.load(self.TEXT)
            self.assertEqual(list(Path(self._dir.name).glob("*.pickle")), [])
        finally:
            del os.environ["MUNZFUSS_YAML_CACHE"]


if __name__ == "__main__":
    unittest.main()
