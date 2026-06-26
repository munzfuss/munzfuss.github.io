"""Integrity gate for curator decision files (§CN / merge_decisions).

Guards the corruption caught 2026-06-26: a hand-edit clobbered a `- members:`
block, leaving a merges entry with a DUPLICATE `reason:` key. PyYAML's default
loader silently keeps the last value, so the real force-merge decision vanished
and the merger applied a wrong grouping with no warning.

These tests pin both halves of the fix in `merge_seeds_cross_source`:
  - `_StrictDecisionsLoader` raises `DecisionsIntegrityError` on duplicate keys;
  - `validate_decisions_doc` flags any merges/no_merges entry missing `members`.

Run via:
    .venv/bin/python -m unittest tests.test_decisions_integrity -v
"""
from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "maintenance"))
_spec = importlib.util.spec_from_file_location(
    "merge_seeds_cross_source",
    str(ROOT / "scripts" / "maintenance" / "merge_seeds_cross_source.py"))
_M = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_M)


class TestDuplicateKey(unittest.TestCase):
    def _load(self, text):
        with tempfile.NamedTemporaryFile("w", suffix=".yml", delete=False) as f:
            f.write(text)
            p = f.name
        return _M.load_decisions_yaml(p)

    def test_duplicate_reason_key_raises(self):
        # exactly the 2026-06-26 corruption: one entry, two `reason:` keys
        bad = (
            "merges:\n"
            "  - members: [a, b]\n"
            "    reason: |\n"
            "      first\n"
            "    reason: |\n"
            "      second (clobbered neighbour)\n"
        )
        with self.assertRaises(_M.DecisionsIntegrityError):
            self._load(bad)

    def test_clean_file_loads(self):
        ok = (
            "merges:\n"
            "  - members: [a, b]\n"
            "    reason: ok\n"
            "no_merges:\n"
            "  - members: [c, d]\n"
        )
        doc = self._load(ok)
        self.assertEqual(len(doc["merges"]), 1)


class TestStructuralValidation(unittest.TestCase):
    def test_missing_members_flagged(self):
        doc = {"merges": [{"reason": "no members here"}]}
        errs = _M.validate_decisions_doc(doc, "x.yml")
        self.assertTrue(any("members" in e for e in errs))

    def test_single_member_flagged(self):
        doc = {"merges": [{"members": ["only-one"], "reason": "r"}]}
        errs = _M.validate_decisions_doc(doc, "x.yml")
        self.assertTrue(any("members" in e for e in errs))

    def test_non_string_member_flagged(self):
        doc = {"no_merges": [{"members": ["a", 123]}]}
        errs = _M.validate_decisions_doc(doc, "x.yml")
        self.assertTrue(errs)

    def test_year_demote_needs_member(self):
        doc = {"year_demote": [{"reason": "no member id"}]}
        errs = _M.validate_decisions_doc(doc, "x.yml")
        self.assertTrue(any("year_demote" in e for e in errs))

    def test_valid_doc_no_errors(self):
        doc = {"merges": [{"members": ["a", "b"], "reason": "r"}],
               "no_merges": [{"members": ["c", "d"]}],
               "year_demote": [{"member_id": "e", "reason": "r"}]}
        self.assertEqual(_M.validate_decisions_doc(doc, "x.yml"), [])


class TestLiveFiles(unittest.TestCase):
    def test_all_committed_decision_files_pass(self):
        d = ROOT / "data" / "v2" / "merge_decisions"
        files = sorted(d.glob("*.yml")) if d.exists() else []
        self.assertTrue(files, "no decision files found")
        for p in files:
            with self.subTest(file=p.name):
                _M.load_decisions_yaml(p)  # must not raise


if __name__ == "__main__":
    unittest.main(verbosity=2)
