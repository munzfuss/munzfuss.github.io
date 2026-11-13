"""The stitch rules of a Numista refresh (scripts/lib/numista_refresh.py).

The case behind them: N#90574 was harvested with KM + Dav only; Numista
later added Hede 11B, 11C and SIEG 31, rounded the weight 28.893 -> 28.9
and listed the mints in another order. The refresh must take the new
references and Numista's current weight, keep the backfilled year_list, and log
anything Numista removed.
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from lib.numista_refresh import diff_references, overlay  # noqa: E402


def _old(**kw):
    base = {"_source_shape": "api", "references": {"km": "632", "dav": "EC III 1308"},
            "weight_g": 28.893, "diameter_mm": 41.15, "year_list": [1776, 1780],
            "mint": ["Royal Danish Mint", "Altona"], "title": "1 Speciedaler"}
    base.update(kw)
    return base


def _new(**kw):
    base = {"_source_shape": "api",
            "references": {"km": "632", "dav": "EC III 1308", "sieg": "31", "hede": ["11B", "11C"]},
            "weight_g": 28.9, "diameter_mm": 41, "year_list": None,
            "mint": ["Altona", "Royal Danish Mint"], "title": "1 Speciedaler (Short inscription)"}
    base.update(kw)
    return base


class StitchTest(unittest.TestCase):
    def run_overlay(self, old, new):
        return overlay(old, new, date="2026-11-12", raw_path="numista/refresh/x.json")

    def test_new_references_are_taken(self):
        res, ch = self.run_overlay(_old(), _new())
        self.assertEqual(res["references"]["hede"], ["11B", "11C"])
        self.assertEqual(ch["references"]["hede"], {"status": "added", "new": ["11B", "11C"]})

    def test_rounded_number_takes_numista_current_and_is_labelled(self):
        res, ch = self.run_overlay(_old(), _new())
        self.assertEqual(res["weight_g"], 28.9)
        self.assertEqual(res["diameter_mm"], 41)
        self.assertEqual(ch["weight_g"], {"status": "rounded", "old": 28.893, "new": 28.9})

    def test_truncated_number_takes_numista_current_and_is_labelled(self):
        res, ch = self.run_overlay(_old(weight_g=6.98), _new(weight_g=6.9))
        self.assertEqual(res["weight_g"], 6.9)
        self.assertEqual(ch["weight_g"]["status"], "truncated")

    def test_a_real_weight_change_wins(self):
        res, ch = self.run_overlay(_old(), _new(weight_g=27.5))
        self.assertEqual(res["weight_g"], 27.5)
        self.assertEqual(ch["weight_g"]["status"], "changed")

    def test_field_absent_from_api_is_kept(self):
        res, ch = self.run_overlay(_old(), _new())
        self.assertEqual(res["year_list"], [1776, 1780])
        self.assertEqual(ch["year_list"]["status"], "kept_old")

    def test_list_order_is_no_change(self):
        _, ch = self.run_overlay(_old(), _new())
        self.assertNotIn("mint", ch)

    def test_reference_missing_from_response_is_kept_and_logged(self):
        res, ch = self.run_overlay(_old(), _new(references={"km": "632"}))
        self.assertEqual(res["references"]["dav"], "EC III 1308")
        self.assertEqual(ch["references"]["dav"],
                         {"status": "absent_in_response", "old": ["EC III 1308"]})

    def test_no_reference_block_keeps_all(self):
        res, _ = self.run_overlay(_old(), _new(references={}))
        self.assertEqual(res["references"], {"km": "632", "dav": "EC III 1308"})

    def test_changed_value_keeps_both(self):
        res, ch = self.run_overlay(_old(references={"km": "606"}), _new(references={"km": "605"}))
        self.assertEqual(res["references"]["km"], ["605", "606"])
        self.assertEqual(ch["references"]["km"]["absent_in_response"], ["606"])

    def test_chrome_sidecar_takes_only_references(self):
        res, ch = self.run_overlay(_old(_source_shape="chrome_v2"), _new())
        self.assertEqual(res["title"], "1 Speciedaler")
        self.assertEqual(ch["title"]["status"], "not_applied")
        self.assertEqual(res["references"]["sieg"], "31")
        self.assertEqual(res["_refresh"]["applied"], "references")

    def test_reference_values_compare_as_sets(self):
        self.assertEqual(diff_references({"km": "406.1|406.2"}, {"km": ["406.2", "406.1"]}), {})


class ConfirmedAbsentTest(unittest.TestCase):
    def test_checked_value_is_dropped_from_that_record_only(self):
        old = {"_source_shape": "api", "numista_id": 148219, "references": {"km": "606"}}
        new = {"_source_shape": "api", "numista_id": 148219,
               "references": {"km": "605", "hede": "9B"}}
        res, ch = overlay(old, new, date="d", raw_path="x")
        self.assertEqual(res["references"]["km"], "605")
        self.assertEqual(ch["confirmed_absent"], {"km": ["606"]})
        other = dict(old, numista_id=1); other_new = dict(new, numista_id=1)
        res2, _ = overlay(other, other_new, date="d", raw_path="x")
        self.assertEqual(res2["references"]["km"], ["605", "606"])


class ParserDifferenceIsNoEditTest(unittest.TestCase):
    """The pre-1541 HTML parser and the API parser name some registers
    differently; that must not read as Numista removing a reference."""

    def test_register_synonyms_and_others_labels(self):
        old = {"galster": "168", "friedberg": "12", "aajt": "6", "sieg": "F2-15.2"}
        new = {"others": ["Galster UU# 168", "AAJT# 6"], "fr": "12", "sieg": "F2-15,2"}
        self.assertEqual(diff_references(old, new), {})

    def test_volume_notes_are_one_value(self):
        self.assertEqual(diff_references({"dav": "8220", "km": ["260", "645 (Denmark)"]},
                                         {"dav": "EC I 8220", "km": ["260", "645"]}), {})

    def test_a_missing_register_still_shows(self):
        d = diff_references({"schive": ["XVI:11"], "skaare": "311"}, {"skaare": "311"})
        self.assertEqual(d, {"schive": {"status": "absent_in_response", "old": ["XVI:11"]}})


if __name__ == "__main__":
    unittest.main()
