"""Regression tests for the «form-#2» km str-repr corruption.

Two surfaces:

* PRODUCER — `merge_seeds_cross_source.py :: _merge_km_field`. When a member's
  `catalog.km` is a register-dict whose value is a LIST (e.g.
  `{sh: ['651', '651.1']}`), the old code did `str(val)` on the whole list →
  emitted the str-repr «['651', '651.1']». Fixed to iterate the list.

* HEAL — `lib/catalog_codes.py :: normalise_catalog`. The hygiene net called on
  every absorb/merge/seed-write now explodes any str-repr element back into its
  members, in BOTH the top-level list shape (`["['651','651.1']", '651']`) and
  the register-dict shape (`{sh: ["['696.1','696']", …]}`).

Run via:
    .venv/bin/python -m unittest tests.test_km_str_repr_form2 -v
"""
from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from lib.catalog_codes import (  # noqa: E402
    normalise_catalog,
    _is_str_repr_list,
    _flatten_str_repr_list,
)

_spec = importlib.util.spec_from_file_location(
    "merge_seeds_cross_source",
    str(PROJECT_ROOT / "scripts" / "maintenance" / "merge_seeds_cross_source.py"),
)
_merger = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_merger)
_merge_km_field = _merger._merge_km_field


def _all_km_values(km) -> list:
    """Flatten a km (scalar / list / register-dict) to every leaf value."""
    out: list = []
    if isinstance(km, dict):
        for v in km.values():
            out += v if isinstance(v, list) else [v]
    elif isinstance(km, list):
        out = list(km)
    elif km is not None:
        out = [km]
    return out


def _has_str_repr(km) -> bool:
    return any(_is_str_repr_list(v) for v in _all_km_values(km))


class TestMergeKmFieldProducer(unittest.TestCase):
    """_merge_km_field must never str() a list-valued register."""

    def test_register_dict_with_list_value_no_str_repr(self):
        # member km is a register-dict whose sh value is a LIST
        members = [{"id": "dk-hede-x", "catalog": {"km": {"sh": ["651", "651.1"]}}}]
        km, _conflicts = _merge_km_field(members, "royal_holstein")
        self.assertFalse(_has_str_repr(km), f"str-repr leaked: {km!r}")
        self.assertEqual(set(map(str, _all_km_values(km))), {"651", "651.1"})

    def test_register_dict_list_plus_bare_member(self):
        # the live c7h13a shape: a register-dict-list foundation + a bare member
        members = [
            {"id": "dk-hede-c7h13a", "catalog": {"km": {"sh": ["651", "651.1"]}}},
            {"id": "dk-numista-132002", "catalog": {"km": "651"}},
        ]
        km, _ = _merge_km_field(members, "royal_holstein")
        self.assertFalse(_has_str_repr(km), f"str-repr leaked: {km!r}")
        self.assertEqual(set(map(str, _all_km_values(km))), {"651", "651.1"})

    def test_two_register_dict_preserved(self):
        members = [{"id": "m", "catalog": {"km": {"sh": ["155", "155.1"], "dk": "722"}}}]
        km, _ = _merge_km_field(members, "royal_holstein")
        self.assertFalse(_has_str_repr(km), f"str-repr leaked: {km!r}")
        self.assertIsInstance(km, dict)
        self.assertEqual(set(map(str, km.get("sh"))), {"155", "155.1"})
        self.assertEqual(str(km.get("dk")), "722")


class TestNormaliseCatalogHeal(unittest.TestCase):
    """normalise_catalog explodes form-#2 str-repr elements in both shapes."""

    def test_top_level_list_str_repr(self):
        cat = {"km": ["['651', '651.1']", "651"]}
        normalise_catalog(cat)
        self.assertEqual(cat["km"], ["651", "651.1"])

    def test_c7h13a_real_corruption(self):
        cat = {"km": ["['651', '651.1', '640', '640.2']", "651"]}
        normalise_catalog(cat)
        self.assertEqual(cat["km"], ["651", "651.1", "640", "640.2"])

    def test_register_dict_internal_str_repr(self):
        # km-696 shape: str-repr element inside the sh register's list
        cat = {"km": {"sh": ["['696.1', '696']", "696.1", "696"], "dk": "706.1"}}
        normalise_catalog(cat)
        self.assertEqual(cat["km"], {"sh": ["696.1", "696"], "dk": "706.1"})

    def test_scalar_str_repr(self):
        cat = {"km": "['651', '651.1']"}
        normalise_catalog(cat)
        self.assertEqual(cat["km"], ["651", "651.1"])

    def test_clean_km_untouched(self):
        for clean in (
            {"km": "651"},
            {"km": ["651", "651.1"]},
            {"km": {"sh": ["651", "651.1"], "dk": "706.1"}},
        ):
            before = dict(clean)["km"]
            # deep-ish copy of the value for comparison
            import copy
            expect = copy.deepcopy(before)
            normalise_catalog(clean)
            self.assertEqual(clean["km"], expect, f"clean km mutated: {clean['km']!r}")


class TestFlattenHelper(unittest.TestCase):
    def test_is_str_repr_list_guards(self):
        self.assertTrue(_is_str_repr_list("['651', '651.1']"))
        self.assertFalse(_is_str_repr_list("651"))
        self.assertFalse(_is_str_repr_list("404.1"))
        self.assertFalse(_is_str_repr_list(651))
        self.assertFalse(_is_str_repr_list("[not valid python"))

    def test_flatten_explodes_and_passes_through(self):
        self.assertEqual(
            _flatten_str_repr_list(["['a', 'b']", "c"]), ["a", "b", "c"]
        )
        self.assertEqual(_flatten_str_repr_list(["a", "b"]), ["a", "b"])


if __name__ == "__main__":
    unittest.main()
