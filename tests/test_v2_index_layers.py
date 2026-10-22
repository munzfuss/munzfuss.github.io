"""The three V2 id layers do not link the way their field names suggest, and a
hand-rolled traversal that gets it wrong returns an EMPTY answer rather than an
error — which is why five such probes shipped confident nonsense in one session
(2026-08-25): «0 of 14 077 kmk seeds reach final», «0 of 166 coins relocated,
166 dead». The true answers were «14 022» and «165 of 166».

    seed_unified[].composed_of  →  SEED ids
    final[].composed_of         →  UNIFIED ids, and sometimes seed ids directly

`lib.v2_index` is the single correct traversal. These tests pin the two things
that make it safe to reach for: it resolves BOTH shapes of `composed_of`, and a
lookup on the wrong layer RAISES instead of missing quietly.
"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "maintenance"))

from lib.v2_index import LayerError, V2Index  # noqa: E402


def _write(tmp: Path, rel: str, coins: list) -> None:
    p = tmp / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(yaml.safe_dump({"coins": coins}, allow_unicode=True))


class SyntheticLayers(unittest.TestCase):
    """Both link shapes, and the guard, on a corpus small enough to read."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def test_final_holding_unified_ids_is_resolved(self):
        """The normal shape: final → unified → seed, two hops."""
        _write(self.tmp, "seed/hede/x.yml", [{"id": "dk-hede-a1"}])
        _write(self.tmp, "seed_unified/x.yml",
               [{"id": "unified-dk-hede-a1", "composed_of": ["dk-hede-a1"]}])
        _write(self.tmp, "final/x.yml",
               [{"id": "unified-dk-hede-a1", "fuss": "kronefod",
                 "composed_of": ["unified-dk-hede-a1"]}])
        pl = V2Index.load(self.tmp).seed("dk-hede-a1")
        self.assertEqual(pl.unified, "unified-dk-hede-a1")
        self.assertEqual(pl.final_entity, "x")
        self.assertEqual(pl.fuss, "kronefod")

    def test_final_holding_a_seed_id_directly_is_resolved(self):
        """The older shape, still in the data: final → seed, one hop.

        A traversal assuming only the two-hop form silently drops these.
        """
        _write(self.tmp, "seed/hede/x.yml", [{"id": "dk-hede-b1"}])
        _write(self.tmp, "seed_unified/x.yml", [])
        _write(self.tmp, "final/x.yml",
               [{"id": "km-legacy", "composed_of": ["dk-hede-b1"]}])
        self.assertEqual(V2Index.load(self.tmp).seed("dk-hede-b1").final,
                         "km-legacy")

    def test_seed_lookup_of_a_unified_id_raises(self):
        """THE regression this module exists for — it must not come back empty."""
        _write(self.tmp, "seed/hede/x.yml", [{"id": "dk-hede-c1"}])
        _write(self.tmp, "seed_unified/x.yml",
               [{"id": "unified-dk-hede-c1", "composed_of": ["dk-hede-c1"]}])
        _write(self.tmp, "final/x.yml", [])
        with self.assertRaises(LayerError) as cm:
            V2Index.load(self.tmp).seed("unified-dk-hede-c1")
        self.assertIn("not a seed id", str(cm.exception))

    def test_unified_lookup_of_a_seed_id_raises_too(self):
        _write(self.tmp, "seed/hede/x.yml", [{"id": "dk-hede-d1"}])
        _write(self.tmp, "seed_unified/x.yml",
               [{"id": "unified-dk-hede-d1", "composed_of": ["dk-hede-d1"]}])
        _write(self.tmp, "final/x.yml", [])
        with self.assertRaises(LayerError):
            V2Index.load(self.tmp).by_unified("dk-hede-d1")

    def test_resolve_accepts_any_layer(self):
        """The entry point for a caller that does not know what it holds."""
        _write(self.tmp, "seed/hede/x.yml", [{"id": "dk-hede-e1"}])
        _write(self.tmp, "seed_unified/x.yml",
               [{"id": "unified-dk-hede-e1", "composed_of": ["dk-hede-e1"]}])
        _write(self.tmp, "final/x.yml",
               [{"id": "unified-dk-hede-e1",
                 "composed_of": ["unified-dk-hede-e1"]}])
        index = V2Index.load(self.tmp)
        self.assertEqual(index.resolve("dk-hede-e1")[0], "seed")
        self.assertIn(index.resolve("unified-dk-hede-e1")[0],
                      {"unified", "final"})
        with self.assertRaises(KeyError):
            index.resolve("dk-hede-nope")


class LiveCorpus(unittest.TestCase):
    """The half of the regression that only the real data can show."""

    @classmethod
    def setUpClass(cls):
        cls.idx = V2Index.load()

    def test_kmk_seeds_do_reach_final(self):
        """A probe keyed on the wrong layer answered «0 of 14 077».

        Any substantial share proves the traversal connects; the exact figure
        moves with the data, so this asserts the shape, not the number.
        """
        kmk = list(self.idx.seeds(source="kmk"))
        self.assertGreater(len(kmk), 1000, "kmk seeds missing from the index")
        self.assertGreater(sum(1 for p in kmk if p.in_final), len(kmk) // 2)

    def test_trace_coin_wrapper_keeps_its_dict_shape(self):
        """trace_coin.build_index delegates here; its subcommands read dicts."""
        import trace_coin

        built = trace_coin.build_index()
        self.assertEqual(len(built), len(self.idx))
        self.assertEqual(
            set(next(iter(built.values()))),
            {"source", "seed_entity", "unified", "label", "final", "final_entity",
             "fuss", "phase", "sources"})


if __name__ == "__main__":
    unittest.main()
