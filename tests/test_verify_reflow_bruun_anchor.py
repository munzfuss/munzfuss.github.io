"""verify_reflow: a Bruun anchor (catalog.bruun_part / bruun_lot_no /
bruun_page) that points at another specimen is not a loss when both lots
are still cited in the coin's sources (curator 2026-10-24, Hede 29: the
rebuild took the anchor from Part II lot 13103 instead of Part I lot 1037)."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "maintenance"))

import verify_reflow as vr  # noqa: E402

SOURCES = [{"ref": "Bruun Part I, lot 1037, p. 51"}, {"ref": "Bruun Part II, lot 13103, p. 54"}]


def coin(part, lot, page, sources=SOURCES):
    return {"catalog": {"bruun_part": part, "bruun_lot_no": lot, "bruun_page": page},
            "sources": sources}


class AnchorTest(unittest.TestCase):
    def test_moved_between_cited_lots(self):
        self.assertIsNotNone(vr._bruun_anchor_moved(coin("I", 1037, 75), coin("II", 13103, 80)))

    def test_old_lot_no_longer_cited_is_not_excused(self):
        cur = coin("II", 13103, 80, sources=[{"ref": "Bruun Part II, lot 13103, p. 54"}])
        self.assertIsNone(vr._bruun_anchor_moved(coin("I", 1037, 75), cur))

    def test_anchor_dropped_is_not_excused(self):
        self.assertIsNone(vr._bruun_anchor_moved(coin("I", 1037, 75), coin(None, None, None)))

    def test_unchanged_anchor(self):
        self.assertIsNone(vr._bruun_anchor_moved(coin("I", 1037, 75), coin("I", 1037, 75)))


if __name__ == "__main__":
    unittest.main()
