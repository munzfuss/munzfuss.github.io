"""Stale `_thinned_from` links are pruned once the run re-decides the specimen.

Function under test:
    scripts/lib/seed_thin.py :: prune_stale_thinned

`_thinned_from` and `sources` survive a re-seed, and thinning only adds links,
so a specimen moved to another representative (or kept as its own record)
stayed linked — and cited — on the old one (2026-10-19: 2 025 kmk specimens on
two representatives; KMM 354144 cited on two finals).

Run:

    .venv/bin/python -m unittest tests.test_prune_stale_thinned -v
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import tempfile  # noqa: E402

import yaml  # noqa: E402

from lib.seed_thin import prune_stale_thinned, thin_safe, thin_seed_dir  # noqa: E402


def _src(n):
    return {"type": "museum", "url": f"https://samlinger.natmus.dk/KMM/object/{n}",
            "ref": f"KMM {n}"}


def _sid(e):
    u = e.get("url", "")
    return "kmk-" + u.rsplit("/", 1)[-1] if "/KMM/object/" in u else None


class PruneStaleThinnedTest(unittest.TestCase):
    def test_moved_to_other_representative(self):
        old = {"id": "kmk-1", "_thinned_from": ["kmk-3", "kmk-9"],
               "sources": [_src(1), _src(3), _src(9)]}
        new = {"id": "kmk-2", "_thinned_from": ["kmk-3"], "sources": [_src(2), _src(3)]}
        st = prune_stale_thinned([old, new], {"kmk-1", "kmk-2", "kmk-3"},
                                 {"kmk-3": "kmk-2"}, _sid)
        # kmk-3 now belongs to kmk-2; kmk-9 was not seen this run → kept
        self.assertEqual(old["_thinned_from"], ["kmk-9"])
        self.assertEqual(old["sources"], [_src(1), _src(9)])
        self.assertEqual(new["_thinned_from"], ["kmk-3"])
        self.assertEqual(new["sources"], [_src(2), _src(3)])
        self.assertEqual(st, {"links_pruned": 1, "citations_pruned": 1})

    def test_live_record_unlinked(self):
        # KMM 354144: its own seed, still linked from kmk-122261
        k = {"id": "kmk-122261", "_thinned_from": ["kmk-354144"],
             "sources": [_src(122261), _src(354144)]}
        prune_stale_thinned([k], {"kmk-122261", "kmk-354144"}, {}, _sid)
        self.assertNotIn("_thinned_from", k)
        self.assertEqual(k["sources"], [_src(122261)])

    def test_current_assignment_untouched(self):
        k = {"id": "kmk-2", "_thinned_from": ["kmk-3"], "sources": [_src(2), _src(3)]}
        st = prune_stale_thinned([k], {"kmk-2", "kmk-3"}, {"kmk-3": "kmk-2"}, _sid)
        self.assertEqual(k["_thinned_from"], ["kmk-3"])
        self.assertEqual(st["links_pruned"], 0)


class ProtectedThinningTest(unittest.TestCase):
    """Curator-excluded seeds are never thinned away (2026-10-19: 11 KMM
    exclusions vanished into representatives) but stay the representative
    their duplicates are thinned into."""

    def test_protected_never_dropped(self):
        coins = [{"id": f"kmk-{i}", "nominal": "Hvid", "ruler": "Hans"} for i in range(1, 8)]
        prot = frozenset({"kmk-3", "kmk-5", "kmk-6", "kmk-7"})
        kept, st = thin_safe(coins, protected=prot)
        ids = {c["id"] for c in kept}
        self.assertTrue(prot <= ids)
        self.assertEqual(set(st["assignments"].values()), {"kmk-3"})

    def test_protected_stays_representative(self):
        coins = [{"id": f"kmk-{i}", "nominal": "(?)", "ruler": "X"} for i in (1, 2, 3, 4, 9)]
        kept, st = thin_safe(coins, protected=frozenset({"kmk-9"}))
        self.assertIn("kmk-9", {c["id"] for c in kept})
        self.assertTrue(all(v == "kmk-9" for v in st["assignments"].values()))


class ThinSeedDirLiveLinkTest(unittest.TestCase):
    """A link to a live record of the same file is pruned with no curator
    decision behind it (2026-10-29: IKMK 18288000/07/09/10 were records and
    links of 18236465 at once; the class registry re-cut four Bremen classes
    on every merger run)."""

    def test_link_to_live_record_pruned(self):
        def isrc(n):
            return {"type": "museum", "url": f"https://ikmk.smb.museum/object?id={n}"}

        def iid(e):
            u = e.get("url", "")
            return "ikmk-" + u.rsplit("=", 1)[-1] if "object?id=" in u else None

        doc = {"coins": [
            {"id": "ikmk-1", "nominal": "A", "weight_rough_g": 1.5,
             "_thinned_from": ["ikmk-2", "ikmk-9"],
             "sources": [isrc(1), isrc(2), isrc(9)]},
            {"id": "ikmk-2", "nominal": "A", "weight_rough_g": 1.7,
             "sources": [isrc(2)]},
        ]}
        with tempfile.TemporaryDirectory() as td:
            f = Path(td) / "e.yml"
            f.write_text(yaml.safe_dump(doc))
            thin_seed_dir(Path(td), source_id_of=iid)
            out = {c["id"]: c for c in yaml.safe_load(f.read_text())["coins"]}
        # ikmk-2 is its own record → unlinked; ikmk-9 unseen → kept
        self.assertEqual(out["ikmk-1"]["_thinned_from"], ["ikmk-9"])
        self.assertEqual(out["ikmk-1"]["sources"], [isrc(1), isrc(9)])
        self.assertEqual(out["ikmk-2"]["sources"], [isrc(2)])


if __name__ == "__main__":
    unittest.main()
