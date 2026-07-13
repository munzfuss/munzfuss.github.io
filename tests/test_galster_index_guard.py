"""Galster catalogue-index guard — the non-numbered «Gej» placeholder stays out.

`galster_parsers/standard.py` sets galster_number = «Gej» for `norge/hansGej.htm`
(a special non-numbered Hans Bergen Goldgulden) so the coin_id stays stable
(`dk-galster-hg-gej`). But «Gej» is NOT a real Galster catalogue number — it's the
page-filename fragment. `_is_real_galster_index` gates it out of the coin's
`catalog.galster` field AND the human-facing source-ref label (a real Galster
number carries a digit: «27», «27A»). The «Gej» token survives only in the id.

Run: .venv/bin/python -m unittest tests.test_galster_index_guard -v
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
sys.path.insert(0, str(PROJECT_ROOT / "scripts" / "maintenance"))

from build_galster_denmark_seed import _is_real_galster_index  # noqa: E402


class GalsterIndexGuard(unittest.TestCase):
    def test_numeric_is_real(self) -> None:
        self.assertTrue(_is_real_galster_index("27"))
        self.assertTrue(_is_real_galster_index("27A"))
        self.assertTrue(_is_real_galster_index("131"))

    def test_gej_placeholder_not_real(self) -> None:
        self.assertFalse(_is_real_galster_index("Gej"))

    def test_none_or_empty_not_real(self) -> None:
        self.assertFalse(_is_real_galster_index(None))
        self.assertFalse(_is_real_galster_index(""))


if __name__ == "__main__":
    unittest.main()
