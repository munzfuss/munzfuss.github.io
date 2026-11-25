"""Seed thinning (lib.seed_thin.thin_safe) — two rules from 2026-11-25.

1. An inferred metal (`metal_verified: false`) is not type identity: it does
   not split a sub-variant bucket (as in the merger, CLAUDE.md §4).
2. Curated weightless records fill the weightless quota: a curator hold on
   records of a bucket must not put `max_weightless` more weightless
   specimens back beside them.

Real case: six KMM 1 Skilling Hans records got billon by analogy on
2026-11-08 (holds); the next KMM re-seed turned their find-mates into three
new classes (kmk-427536 / 427538 / 427539).

Run:  .venv/bin/python -m unittest tests.test_thin_curated_quota -v
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from lib.seed_thin import _subvariant_key, thin_safe  # noqa: E402


def _rec(i, **kw):
    c = {"id": f"kmk-{i}", "nominal": "1 Skilling", "ruler": "Hans",
         "sources": [{"type": "museum", "url": f"https://samlinger.natmus.dk/KMM/object/{i}"}]}
    c.update(kw)
    return c


class CuratedQuota(unittest.TestCase):
    def test_inferred_metal_does_not_split_bucket(self):
        held = _rec(1, metal="billon", metal_verified=False)
        bare = _rec(2)
        self.assertEqual(_subvariant_key(held), _subvariant_key(bare))
        attested = _rec(3, metal="silver")
        self.assertNotEqual(_subvariant_key(attested), _subvariant_key(bare))

    def test_curated_weightless_fill_the_quota(self):
        hold = {"metal": "analogy (curator)"}
        curated = [_rec(i, metal="billon", metal_verified=False, _curation_holds=hold)
                   for i in range(100, 106)]
        plain = [_rec(i) for i in range(200, 231)]
        kept, st = thin_safe(curated + plain)
        ids = {c["id"] for c in kept}
        self.assertEqual(ids, {c["id"] for c in curated})
        self.assertEqual(set(st["assignments"].values()), {"kmk-100"})

    def test_quota_shared_when_curated_are_few(self):
        curated = [_rec(100, _curation_holds={"metal": "x"})]
        plain = [_rec(i) for i in range(200, 210)]
        kept, _ = thin_safe(curated + plain)
        ids = sorted(c["id"] for c in kept)
        self.assertEqual(ids, ["kmk-100", "kmk-200", "kmk-201"])


if __name__ == "__main__":
    unittest.main()
