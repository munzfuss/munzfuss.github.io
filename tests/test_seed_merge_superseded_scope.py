"""merge_seed's «superseded» rule drops a bare id only for page catalogues.

A danskmoent Hede / Galster page id («dk-hede-c4h117») is superseded once the
parser breaks the page out into sub-letters («…c4h117a», «…c4h117b»). For any
other source a lettered id is a separate record: Bruun lot 15186 «Bruun-15139ø»
was dropped beside dk-bruun-15139c … when the parser lost the «ø»
(2026-10-19). The rule must not touch such ids.
"""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from lib.seed_merge import merge_seed  # noqa: E402


def _coin(cid, **kw):
    c = {"id": cid, "fuss": "seed_unsorted", "nominal": "1 Speciedaler",
         "catalog": {}}
    c.update(kw)
    return c


class SupersededScope(unittest.TestCase):
    def _run(self, coins):
        with tempfile.TemporaryDirectory() as d:
            out, _ = merge_seed(coins, Path(d) / "absent.yml")
        return {c["id"] for c in out}

    def test_hede_bare_page_superseded_by_subletters(self):
        ids = self._run([_coin("dk-hede-c4h117", catalog={"hede": "117"}),
                         _coin("dk-hede-c4h117a", catalog={"hede": "117A"}),
                         _coin("dk-hede-c4h117b", catalog={"hede": "117B"})])
        self.assertNotIn("dk-hede-c4h117", ids)
        self.assertIn("dk-hede-c4h117a", ids)

    def test_bruun_bare_number_kept_beside_lettered_numbers(self):
        ids = self._run([_coin("dk-bruun-15139", catalog={"bruun_collection_id": "15139"}),
                         _coin("dk-bruun-15139c", catalog={"bruun_collection_id": "15139c"}),
                         _coin("dk-bruun-15139dd", catalog={"bruun_collection_id": "15139dd"})])
        self.assertIn("dk-bruun-15139", ids)

    def test_other_sources_untouched(self):
        ids = self._run([_coin("kmk-1234"), _coin("kmk-1234a")])
        self.assertEqual(ids, {"kmk-1234", "kmk-1234a"})


if __name__ == "__main__":
    unittest.main()
