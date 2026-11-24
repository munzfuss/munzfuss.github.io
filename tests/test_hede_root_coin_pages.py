"""Root-level coin pages linked from a Hede-number cell.

danskmoent.dk documents some coins on a root page named after the
denomination — Hede 6 Frederik VI 1/6 Rigsdaler 1808 on «/6delrdlr.htm»,
Hede 65 Christian IV Løvedaler on «/loeve.htm» — linked from the Hede cell
of the reign table. Before 2026-11-18 the harvest never fetched them and the
seed cited the overview with «Tiefenseite fehlt». Their layout is not the
cNhM deep-page layout (the deep-page parser read the reign span 1588-1648 as
years), so they are cached under `hede/root/`, the overview row stays the
data, and the stub cites the page (`coin_page`).

Run:  .venv/bin/python -m unittest tests.test_hede_root_coin_pages -v
"""
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from lib.paths import HARVEST_ROOT  # noqa: E402

import fetch_hede as fh  # noqa: E402
import parse_hede as ph  # noqa: E402

CACHE = HARVEST_ROOT / "hede"


def _html(name: str) -> str:
    return (CACHE / name).read_text(encoding="utf-8", errors="replace")


@unittest.skipUnless((CACHE / "f6hede.htm").exists(), "harvest cache (scripts/cache submodule) not attached")
class RootCoinPages(unittest.TestCase):
    def test_scanner_sees_hede_cell_links(self):
        found = set()
        for p in sorted(CACHE.glob("*hede*.htm")):
            found |= fh._scan_irregular_coin_links(_html(p.name))
        for link in list(fh.ROOT_COIN_PAGES) + list(fh.IRREGULAR_COIN_PAGES):
            self.assertIn(link, found, link)

    def test_root_pages_cached_outside_parser_glob(self):
        for link in fh.ROOT_COIN_PAGES:
            name = Path(link).name
            self.assertTrue((CACHE / fh.ROOT_PAGES_SUBDIR / name).exists(), name)
            self.assertFalse((CACHE / name).exists(), name)

    def test_stub_carries_coin_page(self):
        stubs = {s["id"]: s for s in ph._extract_index_stubs(_html("f6hede.htm"), "f6hede")}
        self.assertEqual(stubs["f6h6"]["coin_page"], "/6delrdlr.htm")
        self.assertEqual(stubs["f6h6"]["_source_type"], "index_stub")
        stubs = {s["id"]: s for s in ph._extract_index_stubs(_html("c4hede.htm"), "c4hede")}
        self.assertEqual(stubs["c4h65"]["coin_page"], "/loeve.htm")

    def test_every_root_page_names_its_hede_number(self):
        # The mapping key → stub id must match the Hede number the page prints.
        for link, stub_id in fh.ROOT_COIN_PAGES.items():
            text = _html(f"{fh.ROOT_PAGES_SUBDIR}/{Path(link).name}")
            num = re.match(r"n?[cf]\d+h(\d+)", stub_id).group(1)
            self.assertRegex(text, rf"Hede (?:Norge )?{num}[A-Z]*\b", link)


if __name__ == "__main__":
    unittest.main()
