"""Every reading-mark kind is known to every layer that renders or carries it.

The list of kinds lives in `seed_merge._CURATION_MARK_KEYS`; the schema, the
precedence order in compute.py, the template's `mrank` / `msign`, the
tooltip headlines in app.js and the stylesheet each repeat it. A kind added
to one place and missed in another renders without a sign or without a
headline, silently. Written when «(~)» approximate was added (curator
2026-11-06).
"""
from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from lib.seed_merge import _CURATION_MARK_KEYS  # noqa: E402
from lib.schema import FieldValue  # noqa: E402


class MarkKindsConsistentTest(unittest.TestCase):
    def test_every_layer_knows_every_kind(self):
        tpl = (ROOT / "templates" / "location.html.j2").read_text(encoding="utf-8")
        mrank = re.search(r"set mrank = \{([^}]*)\}", tpl).group(1)
        msign = re.search(r"set msign = \{([^}]*)\}", tpl).group(1)
        js = (ROOT / "assets" / "app.js").read_text(encoding="utf-8")
        css = (ROOT / "scripts" / "lib" / "style.base.css").read_text(encoding="utf-8")
        compute = (ROOT / "scripts" / "lib" / "compute.py").read_text(encoding="utf-8")
        for kind in _CURATION_MARK_KEYS:
            with self.subTest(kind=kind):
                self.assertIn(kind, FieldValue.model_fields)
                self.assertIn(f"'{kind}'", mrank)
                self.assertIn(f"'{kind}'", msign)
                alt = re.search(r"\(((?:suspect|erroneous)[a-z|]*)\)-mark", js).group(1).split("|")
                self.assertIn(kind, alt)
                for lang in ("uk", "de", "en", "da"):
                    self.assertRegex(js, rf"{lang}: \{{[^}}]*\b{kind}: \"")
                self.assertIn(f".{kind}-mark", css)
                self.assertIn(f'"{kind}"', compute)

    def test_approximate_sign(self):
        tpl = (ROOT / "templates" / "location.html.j2").read_text(encoding="utf-8")
        self.assertIn("'approximate': '(~)'", tpl)


if __name__ == "__main__":
    unittest.main()
