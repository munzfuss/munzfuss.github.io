"""A curator `_curation_holds` on a `*_verified` flag must survive the on-disk
seed-normalisation pass, not just the merge.

Caught 2026-09-10 while fixing the reflow-home-drift (commit fd231b5). The seed
entry kmk-81473 (Christian III «1 Rhinsk gylden» 1536, KMM GP 888.51) held
`mint_verified: false` since 2026-08-20 so the corrected Roskilde reading — not
Galster's / KMM's Gottorp misattribution — wins the merged mint (§4 verified
accumulator would otherwise union both into the render). A pipeline re-seed at
9808d38 silently flipped that held flag back to `true` (git-proven: 67e7a90
False → 9808d38 True, hold present on both sides).

Why the hold looked honoured yet failed: `merge_seed`/`merge_one` DO honour
holds. But `write_v2_seed`'s on-disk «orphan-curated normalisation» pass runs
BEFORE `merge_seed`, iterating every existing entry and auto-promoting
`mint_verified`/`metal_verified` false→true from a scalar-mint-plus-source-URL
(sources-imply-mint) or fineness (fineness-implies-metal). That pass did not
consult `_curation_holds`, so it mutated the on-disk entry to `true` and wrote
it back; the subsequent merge then faithfully preserved the already-corrupted
value under the very hold meant to stop it.

Fix (option A, targeted): both auto-promotion rules now skip a field named in
the entry's `_curation_holds`. This test drives the real normalisation pass by
calling `write_v2_seed(coins=[], …)` against a throwaway seed dir — fresh=[]
sends the single existing entry straight through the on-disk purge/normalise
path — and asserts the held flag is untouched.
"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

import ruamel.yaml
import yaml as _yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from lib import v2_seed_writer as W  # noqa: E402


def _write_seed(src_dir: Path, coin: dict) -> Path:
    y = ruamel.yaml.YAML(typ="rt")
    doc = {
        "status": "seed", "source": "holdtest", "entity": "gottorp_duchy",
        "scope_note": "test fixture", "coins": [coin],
    }
    path = src_dir / "gottorp_duchy.yml"
    with path.open("w") as f:
        y.dump(doc, f)
    return path


def _load(path: Path, cid: str) -> dict:
    coins = _yaml.safe_load(path.read_text())["coins"]
    return next(c for c in coins if c["id"] == cid)


class TestNormalisePassRespectsHolds(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(prefix="seedholdtest_")
        self._root = Path(self._tmp.name)
        self._src = self._root / "holdtest"
        self._src.mkdir(parents=True)
        # Redirect the writer's seed root at the throwaway tree.
        self._orig_root = W.V2_SEED_ROOT
        W.V2_SEED_ROOT = self._root

    def tearDown(self):
        W.V2_SEED_ROOT = self._orig_root
        self._tmp.cleanup()

    def _run_pass(self):
        # fresh=[] → nothing new is built; the existing entry runs through the
        # on-disk purge/normalise loop (and survives as orphan_curated).
        W.write_v2_seed(coins=[], source_name="holdtest", scope_note="test")

    def test_held_mint_verified_not_flipped(self):
        # The kmk-81473 shape: scalar mint + a source URL + held false flag —
        # exactly the sources-imply-mint trigger.
        path = _write_seed(self._src, {
            "id": "test-held-mint", "nominal": "1 Gylden", "metal": "gold",
            "issuing_entity": "gottorp_duchy",
            "year_first": 1536, "year_last": 1536,
            "mint": "Gottorp", "mint_verified": False,
            "sources": [{"type": "museum", "url": "https://example.org/x"}],
            "_curation_holds": {"mint_verified": "frozen: Roskilde wins merged mint"},
        })
        self._run_pass()
        self.assertIs(_load(path, "test-held-mint")["mint_verified"], False)

    def test_held_metal_verified_not_flipped(self):
        # The fineness-implies-metal trigger: metal set + fineness_verified true
        # + held metal_verified false.
        path = _write_seed(self._src, {
            "id": "test-held-metal", "nominal": "1 Speciedaler", "metal": "silver",
            "issuing_entity": "gottorp_duchy",
            "year_first": 1600, "year_last": 1600,
            "fineness": 0.875, "fineness_verified": True,
            "metal_verified": False,
            "_curation_holds": {"metal_verified": "frozen for test"},
        })
        self._run_pass()
        self.assertIs(_load(path, "test-held-metal")["metal_verified"], False)

    def test_list_form_hold_also_honoured(self):
        # Legacy list-form holds must work too (merge reads set() over keys).
        path = _write_seed(self._src, {
            "id": "test-held-listform", "nominal": "1 Gylden", "metal": "gold",
            "issuing_entity": "gottorp_duchy",
            "year_first": 1536, "year_last": 1536,
            "mint": "Gottorp", "mint_verified": False,
            "sources": [{"type": "museum", "url": "https://example.org/x"}],
            "_curation_holds": ["mint_verified"],
        })
        self._run_pass()
        self.assertIs(_load(path, "test-held-listform")["mint_verified"], False)

    def test_unheld_mint_verified_still_auto_promotes(self):
        # Control: without a hold, the sources-imply-mint rule MUST still fire —
        # the fix narrows the rule to held fields only, it does not disable it.
        path = _write_seed(self._src, {
            "id": "test-unheld", "nominal": "1 Gylden", "metal": "gold",
            "issuing_entity": "gottorp_duchy",
            "year_first": 1536, "year_last": 1536,
            "mint": "Gottorp", "mint_verified": False,
            "sources": [{"type": "museum", "url": "https://example.org/x"}],
        })
        self._run_pass()
        self.assertIs(_load(path, "test-unheld")["mint_verified"], True)


if __name__ == "__main__":
    unittest.main()
