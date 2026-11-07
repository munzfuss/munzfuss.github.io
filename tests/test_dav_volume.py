"""Davenport volume of a value (lib.catalog_codes._dav_volume)."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

class DavVolume(unittest.TestCase):
    """A separate sub-letter belongs to the Davenport number, not the volume
    (2026-11-07: «CCT 5457 A» + bare «5457» became «CCT 5457 5457»)."""

    def test_sub_letter_is_not_volume(self):
        from lib.catalog_codes import _dav_volume, _promote_bare_dav
        self.assertEqual(_dav_volume("CCT 5457 A"), "CCT")
        self.assertEqual(_dav_volume("EC II 3679"), "EC II")
        self.assertEqual(_dav_volume("BrSL LS121"), "BrSL")
        self.assertIsNone(_dav_volume("5457"))
        self.assertEqual(_promote_bare_dav(["5457", "CCT 5457 A"]), ["CCT 5457", "CCT 5457 A"])


if __name__ == "__main__":
    unittest.main()
