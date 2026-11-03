"""Every issuing entity a location page consumes has its six colour rules
(badge, filter chip, timeline marker; dark and light) — curator 2026-11-03."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from lib.entity_palette import missing_palette  # noqa: E402


class Palette(unittest.TestCase):
    def test_every_consumed_entity_is_coloured(self):
        self.assertEqual(missing_palette(), {})

    def test_a_new_entity_without_colours_is_reported(self):
        css = ".ent-badge.ent-x { color: red; }\n"
        gaps = missing_palette(css, {"x"})
        self.assertEqual(len(gaps["x"]), 5)
        self.assertNotIn("badge", gaps["x"])


if __name__ == "__main__":
    unittest.main()
