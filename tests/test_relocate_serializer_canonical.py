"""Regression: entity relocation must re-serialise seeds in the CANONICAL
format, not PyYAML's `safe_dump(width=120)`.

`audit_entity_misclassifications._relocate_misclassifications` used to write
the current- and expected-entity seed files with
`yaml.safe_dump(..., width=120)`. `lib.v2_seed_writer` writes every seed with
ruamel (width=200, indent 2/4/2, quotes preserved), so the two formats
disagree on line-wrap width and indentation — and re-serialising a file with
the wrong one re-flowed EVERY long string in it. Moving 56 coins out of
`kmk/danish_realm.yml` produced a 570 000-line diff whose real content change
(`git diff -w`) was ~1.5k lines. That is unreviewable and collides with any
parallel session.

The fix routes both writes through `_canonical_seed_yaml()` + `_dump_seed_yaml`
and reads round-trip too, so untouched entries stay byte-identical.

Run:
    .venv/bin/python -m unittest tests.test_relocate_serializer_canonical -v
"""
from __future__ import annotations

import io
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
sys.path.insert(0, str(PROJECT_ROOT / "scripts" / "maintenance"))

import audit_entity_misclassifications as A  # noqa: E402

# A seed whose scope_note + a coin note are long enough that a width=120
# dumper would wrap them onto extra lines and a width=200 dumper would not.
_LONG = (
    "Datensatz aus der Kgl. Münz- und Medaillensammlung (Nationalmuseet "
    "Kopenhagen, api.natmus.dk); die Felder sind museumsbelegt. Der Müntzfuß "
    "dieses Stücks ist noch nicht bestimmt."
)
_SEED_TEXT = (
    "status: seed\n"
    "source: KMK Copenhagen (Nationalmuseet, api.natmus.dk)\n"
    "generated_at: '2026-09-13T00:00:00Z'\n"
    "entity: gottorp_duchy\n"
    f"scope_note: {_LONG}\n"
    "coins:\n"
    "  - id: kmk-1\n"
    "    fuss: seed_unsorted\n"
    "    year_label: '1600'\n"
    "    ruler: Johan Adolph\n"
    f"    verification_note: {_LONG}\n"
    "  - id: kmk-2\n"
    "    fuss: seed_unsorted\n"
    "    year_label: '1601'\n"
    "    ruler: Johan Adolph\n"
)


class TestCanonicalSeedYaml(unittest.TestCase):
    def _dump(self, data) -> str:
        y = A._canonical_seed_yaml()
        buf = io.StringIO()
        y.dump(data, buf)
        return buf.getvalue()

    def test_roundtrip_is_byte_stable(self):
        """load → dump → load → dump is idempotent — the serializer does
        not re-flow anything on a no-op pass."""
        y = A._canonical_seed_yaml()
        first = self._dump(y.load(_SEED_TEXT))
        second = self._dump(y.load(first))
        self.assertEqual(first, second, "canonical dump is not idempotent")

    def test_long_line_not_wrapped_at_120(self):
        """width=200 (canonical), not 120 (the old safe_dump bug): the long
        scope_note stays on ONE physical line."""
        y = A._canonical_seed_yaml()
        out = self._dump(y.load(_SEED_TEXT))
        scope_lines = [ln for ln in out.splitlines() if ln.startswith("scope_note:")]
        self.assertEqual(len(scope_lines), 1)
        # The single scope_note line is longer than 120 chars — proof it did
        # not wrap at the old width.
        self.assertGreater(len(scope_lines[0]), 120)

    def test_year_label_quotes_preserved(self):
        """`year_label: '1600'` keeps its quotes on round-trip (preserve_quotes)
        — a plain re-dump would render it unquoted and churn the line."""
        out = self._dump(A._canonical_seed_yaml().load(_SEED_TEXT))
        self.assertIn("year_label: '1600'", out)

    def test_untouched_coin_survives_removal_byte_identical(self):
        """Removing one coin (the relocation's current-file path) leaves the
        OTHER coin's serialization unchanged — no whole-file re-flow."""
        y = A._canonical_seed_yaml()
        data = y.load(_SEED_TEXT)
        before = self._dump(data)
        data["coins"] = [c for c in data["coins"] if c.get("id") != "kmk-1"]
        after = self._dump(data)
        # kmk-2's block is identical in both dumps.
        self.assertIn("  - id: kmk-2\n    fuss: seed_unsorted\n"
                      "    year_label: '1601'\n    ruler: Johan Adolph\n", before)
        self.assertIn("  - id: kmk-2\n    fuss: seed_unsorted\n"
                      "    year_label: '1601'\n    ruler: Johan Adolph\n", after)
        self.assertNotIn("kmk-1", after)


if __name__ == "__main__":
    unittest.main()
