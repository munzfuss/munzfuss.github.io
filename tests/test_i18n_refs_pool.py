"""`data/shared/refs_pool.yml` is a reader-facing surface and must be audited.

It was not, for four months. The pool holds 181 bibliography entries that the
build injects straight into every page citing them, per language — and
`refs_pool.py` falls back silently (`entry.get(lang) or entry.get("en") or
entry.get("de")`), so a missing language shows up as another language's text
rather than as an error. `audit_i18n.py` discovers its files from a hardcoded
list of `data/shared/` names that did not include this one, so every
completeness figure the audit printed was short by the whole pool. Turning it
on immediately surfaced sixteen German-only entries.

Two things are pinned here: that the file is in the scan at all, and that it
is walked by the walker written for ITS shape. It is a flat {key: {lang: text}}
map, unlike `fuesse.yml` (nested slots) and the `-references` sidecars
(`entries[].content`), and the `data/shared/` branch previously sent anything
not named `*-references` to the fuß walker — which would have found nothing
here and reported a clean file.

Run via:
    .venv/bin/python -m unittest tests.test_i18n_refs_pool -v
"""
from __future__ import annotations

import argparse
import sys
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from audit_i18n import collect_files, walk_refs_pool_triples  # noqa: E402

POOL = ROOT / "data" / "shared" / "refs_pool.yml"


class TestRefsPoolIsAudited(unittest.TestCase):
    def test_the_pool_is_in_a_full_scan(self):
        files = collect_files(argparse.Namespace(location=None))
        self.assertIn(POOL, files,
                      "refs_pool.yml must be scanned — the build renders it")

    def test_a_location_scan_leaves_the_shared_pool_out(self):
        # The pool is shared across pages; charging one location for every
        # other location's citations would make --location unusable.
        files = collect_files(argparse.Namespace(location="denmark"))
        self.assertNotIn(POOL, files)

    def test_the_walker_reads_the_pool_shape(self):
        doc = yaml.safe_load(POOL.read_text(encoding="utf-8"))
        found = dict(walk_refs_pool_triples(doc))
        self.assertGreater(len(found), 100, "the pool has ~181 entries")
        # The field name is the stable key, which is what the citation
        # marker carries — that is what makes a hit actionable.
        key = next(iter(doc))
        self.assertIn(key, found)
        self.assertEqual(found[key], doc[key])

    def test_the_walker_skips_a_non_mapping_entry(self):
        self.assertEqual(dict(walk_refs_pool_triples({"k": "not a mapping"})), {})
        self.assertEqual(dict(walk_refs_pool_triples({})), {})
        self.assertEqual(dict(walk_refs_pool_triples(None)), {})


if __name__ == "__main__":
    unittest.main()
