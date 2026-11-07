"""KMM stub rule (curator 2026-11-05): a record leaves the corpus when it is a
forgery; has no weight and no image; or has a weight but no image and no
catalogue index. Image unknown (page not cached) → kept.
"""
from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "maintenance"))

_spec = importlib.util.spec_from_file_location(
    "build_kmk_seed_for_stub_test", ROOT / "scripts" / "maintenance" / "build_kmk_seed.py")
bk = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(bk)


class StubRule(unittest.TestCase):
    def setUp(self):
        self._orig = bk._kmm_has_image
        self.image = {}
        bk._kmm_has_image = lambda rid: self.image.get(rid)

    def tearDown(self):
        bk._kmm_has_image = self._orig

    def cat(self, image, **entry):
        self.image["1"] = image
        return bk._kmm_stub_category({"id": "kmk-1", **entry})

    def test_forgery(self):
        self.assertEqual(self.cat(True, forgery_flag="falsk"), "forgery")
        self.assertEqual(self.cat(True, nominal="skilling, samtidig forfalskning"), "forgery")

    def test_no_weight_no_image_even_with_index(self):
        self.assertEqual(self.cat(False, catalog={"hede": "119B"}), "no_weight_no_image")

    def test_weight_no_image_no_index(self):
        self.assertEqual(self.cat(False, weight_rough_g=0.4), "weight_no_image_no_index")

    def test_weight_and_index_without_image_stays(self):
        self.assertIsNone(self.cat(False, weight_rough_g=0.4, catalog={"hede": "119B"}))

    def test_bruun_or_volume_tags_are_not_an_index(self):
        self.assertEqual(self.cat(False, weight_rough_g=0.4, catalog={"hede_volume": "c4h"}),
                         "weight_no_image_no_index")

    def test_index_marked_erroneous_is_not_an_index(self):
        saved = bk._ERRONEOUS_MARKS
        bk._ERRONEOUS_MARKS = {"kmk-1": {("hede", "135")}}
        try:
            self.assertEqual(self.cat(False, weight_rough_g=1.1, catalog={"hede": "135"}),
                             "weight_no_image_no_index")
            self.assertIsNone(self.cat(False, weight_rough_g=1.1,
                                       catalog={"hede": "135", "schou": "52"}))
        finally:
            bk._ERRONEOUS_MARKS = saved

    def test_marks_of_a_dropped_record_survive_in_the_scope_file(self):
        """A marked record dropped by the rule leaves the seed with its mark;
        the scope file must carry the mark, or the next run counts the
        number again and the record flips back in, unmarked."""
        import tempfile, yaml
        mark = [{"register": "hede", "value": "135", "kind": "erroneous", "reason": {"en": "x"}}]
        saved = (bk.PROJECT_ROOT, bk._ERRONEOUS_MARKS, dict(bk._MARKS_FULL), dict(bk._STUB_DROPPED))
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            (root / "data" / "v2" / "seed" / "kmk").mkdir(parents=True)
            (root / "data" / "v2" / "_scope_dropped").mkdir(parents=True)
            (root / "data" / "v2" / "_scope_dropped" / "kmk.yml").write_text(
                yaml.safe_dump({"dropped": {"kmk-1": "weight_no_image_no_index"},
                                "catalog_marks": {"kmk-1": mark}}))
            try:
                bk.PROJECT_ROOT, bk._ERRONEOUS_MARKS = root, None
                bk._STUB_DROPPED.clear()
                self.assertEqual(self.cat(False, weight_rough_g=1.1, catalog={"hede": "135"}),
                                 "weight_no_image_no_index")
                bk._STUB_DROPPED["kmk-1"] = "weight_no_image_no_index"
                bk._write_scope_dropped()
                out = yaml.safe_load((root / "data" / "v2" / "_scope_dropped" / "kmk.yml").read_text())
                self.assertEqual(out["catalog_marks"]["kmk-1"], mark)
            finally:
                bk.PROJECT_ROOT, bk._ERRONEOUS_MARKS = saved[0], saved[1]
                bk._MARKS_FULL.clear(); bk._MARKS_FULL.update(saved[2])
                bk._STUB_DROPPED.clear(); bk._STUB_DROPPED.update(saved[3])

    def test_image_stays(self):
        self.assertIsNone(self.cat(True))

    def test_unknown_image_stays(self):
        self.assertIsNone(self.cat(None))


class ImageOfAnotherObject(unittest.TestCase):
    """The page under these ids shows the neighbouring FP 1780 object; its
    photographs are not an image of the API record (curator 2026-11-06)."""

    IDS = ("167058", "167065", "167067", "167107", "167151")

    def test_neighbour_photos_do_not_count(self):
        if not (bk.KMK_CACHE / "web" / "167058.json").exists():
            self.skipTest("KMM web cache not available")
        for rid in self.IDS:
            self.assertFalse(bk._kmm_has_image(rid), rid)


if __name__ == "__main__":
    unittest.main()


class ExonumiaLedger(unittest.TestCase):
    """A KMM non-coin (banknote «Seddel», token «Andet», medal …) is kept out
    of the seed AND recorded in the scope ledger with category «exonumia», so a
    final that exists only through it leaves in absorb (curator 2026-11-07:
    KMM 463985, 50 rigsbanksdalder 1813, a «Seddel» classified under 18½)."""

    def setUp(self):
        self._saved = dict(bk._STUB_DROPPED)
        bk._STUB_DROPPED.clear()

    def tearDown(self):
        bk._STUB_DROPPED.clear()
        bk._STUB_DROPPED.update(self._saved)

    def test_banknote_is_recorded(self):
        self.assertIsNone(bk.build_entry({"id": 463985, "workDescription": "Seddel",
                                          "nominal": "50 rigsbanksdalder"}))
        self.assertEqual(bk._STUB_DROPPED.get("kmk-463985"), "exonumia")

    def test_exonumia_nominal_is_recorded(self):
        self.assertIsNone(bk.build_entry({"id": 28296, "workDescription": "Mønt",
                                          "nominal": "amulet"}))
        self.assertEqual(bk._STUB_DROPPED.get("kmk-28296"), "exonumia")
