"""Unit tests for the fuss cross-reference resolver.

Function under test:
    scripts/lib/fuss_refs.py :: process_html

The resolver turns `[fuss:KEY]` prose markers into the effective display
name (passed in via `name_map`, already per-page + per-language
resolved), linked to the `#fuss-KEY` card anchor when that card is
rendered on the page, plain `<code>` otherwise, and a visible
placeholder for an unknown key (§0 — never silently drop).

Design + decisions: docs/fuss_cross_refs_design.md.

Run via:
    .venv/bin/python -m unittest tests.test_fuss_refs -v
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from lib import fuss_refs  # noqa: E402


NAME_MAP = {
    "rosenobel_fod": "Rosenobel-fod",
    "nobel_fod": "Nobelfod",
    "reichsdukatenfuss": "Rigsdukatfod",   # Denmark override flavour
}


class TestFussRefs(unittest.TestCase):

    def test_same_page_marker_becomes_link(self):
        html = '<section id="fuss-rosenobel_fod">x</section> [fuss:rosenobel_fod]'
        out = fuss_refs.process_html(html, "de", NAME_MAP)
        self.assertIn(
            '<a class="fuss-xref" href="#fuss-rosenobel_fod">'
            '<code>Rosenobel-fod</code></a>',
            out,
        )

    def test_off_page_marker_is_plain_code_no_link(self):
        # No `id="fuss-nobel_fod"` anchor on this page → plain <code>.
        html = 'card without that anchor. [fuss:nobel_fod] here.'
        out = fuss_refs.process_html(html, "de", NAME_MAP)
        self.assertIn("<code>Nobelfod</code>", out)
        self.assertNotIn('href="#fuss-nobel_fod"', out)

    def test_unknown_key_renders_visible_placeholder(self):
        html = "[fuss:does_not_exist]"
        out = fuss_refs.process_html(html, "de", NAME_MAP)
        self.assertIn("UNKNOWN FUSS", out)
        self.assertIn("does_not_exist", out)
        # The literal marker must NOT survive into the output.
        self.assertNotIn("[fuss:does_not_exist]", out)

    def test_per_page_name_comes_from_name_map(self):
        # Same marker, two different name_maps → two different names.
        html = '<section id="fuss-reichsdukatenfuss">x</section> [fuss:reichsdukatenfuss]'
        dk = fuss_refs.process_html(html, "de", {"reichsdukatenfuss": "Rigsdukatfod"})
        de = fuss_refs.process_html(html, "de", {"reichsdukatenfuss": "Reichsdukatenfuß"})
        self.assertIn("<code>Rigsdukatfod</code>", dk)
        self.assertIn("<code>Reichsdukatenfuß</code>", de)

    def test_marker_adjacent_to_punctuation(self):
        html = ('<section id="fuss-nobel_fod">x</section> '
                'der [fuss:nobel_fod]-Linie und [fuss:nobel_fod].')
        out = fuss_refs.process_html(html, "de", NAME_MAP)
        # Both resolve; the trailing `-Linie` / `.` stay intact, the
        # marker boundary does not swallow them.
        self.assertIn("</a>-Linie", out)
        self.assertIn("</a>.", out)
        self.assertNotIn("[fuss:nobel_fod]", out)

    def test_multiple_distinct_markers_one_pass(self):
        html = ('<section id="fuss-nobel_fod">x</section>'
                '<section id="fuss-rosenobel_fod">y</section>'
                ' [fuss:nobel_fod] [fuss:rosenobel_fod]')
        out = fuss_refs.process_html(html, "de", NAME_MAP)
        self.assertIn("<code>Nobelfod</code>", out)
        self.assertIn("<code>Rosenobel-fod</code>", out)

    def test_no_markers_is_noop(self):
        html = "<p>plain prose, no markers</p>"
        self.assertEqual(fuss_refs.process_html(html, "de", NAME_MAP), html)


if __name__ == "__main__":
    unittest.main()
