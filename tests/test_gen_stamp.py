"""Unit tests for the content-stable `generated_at` resolver (2026-07-15).

`resolve_generated_at` reuses the existing file's timestamp when the
regenerated payload (compared with the timestamp field stripped from both
sides) is unchanged, so a no-op merger/absorb re-run leaves the committed
`seed_unified` / `classification_decisions` file byte-identical instead of a
daily one-line churn. When content differs — or there is no prior file /
timestamp — it returns today's date.

Run via:
    .venv/bin/python -m unittest tests.test_gen_stamp -v
"""
import sys
import unittest
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from lib.gen_stamp import resolve_generated_at  # noqa: E402

OLD = "2020-01-01"
TODAY = date.today().isoformat()


class ResolveGeneratedAt(unittest.TestCase):
    def test_no_existing_doc_returns_today(self):
        self.assertEqual(
            resolve_generated_at({"generated_at": TODAY, "coins": []}, None),
            TODAY)

    def test_empty_existing_doc_returns_today(self):
        self.assertEqual(
            resolve_generated_at({"generated_at": TODAY, "coins": []}, {}),
            TODAY)

    def test_existing_without_ts_returns_today(self):
        # existing carries content but no generated_at → cannot reuse
        self.assertEqual(
            resolve_generated_at({"generated_at": TODAY, "coins": [1]},
                                 {"coins": [1]}),
            TODAY)

    def test_content_equal_reuses_old_ts(self):
        # identical payload apart from the timestamp → keep the prior date
        new = {"id": "e", "generated_at": TODAY, "coins": [{"id": "a"}]}
        old = {"id": "e", "generated_at": OLD, "coins": [{"id": "a"}]}
        self.assertEqual(resolve_generated_at(new, old), OLD)

    def test_placeholder_ts_irrelevant_to_compare(self):
        # a None placeholder in new_payload is stripped before compare
        new = {"id": "e", "generated_at": None, "coins": [{"id": "a"}]}
        old = {"id": "e", "generated_at": OLD, "coins": [{"id": "a"}]}
        self.assertEqual(resolve_generated_at(new, old), OLD)

    def test_content_differ_bumps_to_today(self):
        new = {"id": "e", "generated_at": TODAY, "coins": [{"id": "a"}]}
        old = {"id": "e", "generated_at": OLD, "coins": [{"id": "b"}]}
        self.assertEqual(resolve_generated_at(new, old), TODAY)

    def test_added_key_bumps_to_today(self):
        # extra content key present in new but not old → real change
        new = {"id": "e", "generated_at": TODAY, "coins": [], "extra": 1}
        old = {"id": "e", "generated_at": OLD, "coins": []}
        self.assertEqual(resolve_generated_at(new, old), TODAY)

    def test_conditional_key_present_in_both_reuses(self):
        # the decisions file's optional bulk_promote_pending, unchanged
        new = {"entity_id": "e", "generated_at": TODAY,
               "bulk_promote_pending": "no_basic_peer_only",
               "assignments": [], "pending": [], "multi_match_warnings": []}
        old = dict(new)
        old["generated_at"] = OLD
        self.assertEqual(resolve_generated_at(new, old), OLD)

    def test_custom_ts_field(self):
        new = {"stamp": TODAY, "coins": [1]}
        old = {"stamp": OLD, "coins": [1]}
        self.assertEqual(resolve_generated_at(new, old, ts_field="stamp"), OLD)

    def test_key_order_irrelevant(self):
        # dict equality is order-independent — reordered keys still reuse
        new = {"coins": [{"id": "a"}], "id": "e", "generated_at": TODAY}
        old = {"id": "e", "generated_at": OLD, "coins": [{"id": "a"}]}
        self.assertEqual(resolve_generated_at(new, old), OLD)


if __name__ == "__main__":
    unittest.main()
