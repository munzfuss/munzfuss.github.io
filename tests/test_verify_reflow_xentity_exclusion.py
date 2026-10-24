"""verify_reflow excuses the citation of a KMM stub excluded in ANY entity's
exclusions file, not only in the final's own entity (curator 2026-10-24:
stubs excluded in danish_realm had left 161 citations on the danish_norway
Hvid c-afd707d6). Reads the live exclusions; KMM 642896 is a specimen of
the stub kmk-642893 (danish_realm, undocumented_stub, 2026-10-16)."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "maintenance"))

import verify_reflow as vr  # noqa: E402


class CrossEntityExclusion(unittest.TestCase):
    def test_stub_excluded_elsewhere_is_excused(self):
        self.assertNotIn("642896", vr._member_excluded_kmm("danish_norway"))
        self.assertIn("642896", vr._member_excluded_kmm("danish_realm"))
        self.assertIn("642896", vr._member_excluded_kmm_any())

    def test_union_covers_each_entity(self):
        any_ = vr._member_excluded_kmm_any()
        for p in (ROOT / vr.EXCLUSIONS_REL).glob("*.yml"):
            if not p.stem.startswith("_"):
                self.assertTrue(vr._member_excluded_kmm(p.stem) <= any_, p.stem)


if __name__ == "__main__":
    unittest.main()
