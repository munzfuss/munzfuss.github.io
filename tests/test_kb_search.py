"""The kb full-text index (scripts/kb) and the Bruun printed-page conversion.

Each test pins a defect that was found in practice and that failed silently:

* The index recorded `variants.yml` as `str(hash(text))`. Python salts `hash()`
  per process, so the stored fingerprint was meaningless, and `search` never
  compared it anyway: after a rule change the search ran on the old index
  without a word (found 2026-10-19 while auditing the skills).
* «14¼» normalised to the token «141» — the vulgar fraction was glued to the
  integer (round 1 of the measurement, it moved case A14).
* «kobbermønt» did not find «kaabermønt», although the cite-source skill said
  it did: the 16th–17th-c. Danish spelling Kaaber / Kaabber had no rule.
* Bruun citations gave the PDF page (Part II lot 13163 «p. 120») instead of the
  printed page (94). The running head is read per page; on full-page feature
  lots it sits lower down (Part III PDF 82).
* Part II and Part V reuse lot numbers 14001–14226, so a page-heal keyed on the
  lot number alone would rewrite the wrong part.
"""
from __future__ import annotations

import sqlite3
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "kb"))
sys.path.insert(0, str(ROOT / "scripts" / "maintenance"))

import kb  # noqa: E402
from lib import bruun_pages  # noqa: E402
import heal_bruun_printed_pages as heal  # noqa: E402


def _meta_db(meta: dict[str, str]) -> sqlite3.Connection:
    con = sqlite3.connect(":memory:")
    con.execute("CREATE TABLE meta(key TEXT PRIMARY KEY, value TEXT)")
    con.executemany("INSERT INTO meta VALUES (?, ?)", meta.items())
    return con


class IndexStaleness(unittest.TestCase):
    def test_fingerprint_is_stable_across_processes(self):
        """The hash() bug: two interpreters must record the same fingerprint."""
        code = ("import sys; sys.path.insert(0, 'scripts/kb'); import kb, json; "
                "print(json.dumps(kb._fingerprint(), sort_keys=True))")
        runs = {subprocess.run([sys.executable, "-c", code], cwd=ROOT, capture_output=True,
                               text=True, check=True).stdout for _ in range(2)}
        self.assertEqual(len(runs), 1)

    def test_fresh_index_is_not_stale(self):
        self.assertIsNone(kb._stale_reason(_meta_db(kb._fingerprint())))

    def test_changed_rules_and_manifest_are_reported(self):
        for key, words in (("variants_sha", "variants.yml"), ("manifest_sha", "_corpus.yml"),
                           ("normalizer_version", "normaliser")):
            meta = dict(kb._fingerprint(), **{key: "something else"})
            self.assertIn(words, kb._stale_reason(_meta_db(meta)))

    def test_partial_build_is_reported(self):
        meta = dict(kb._fingerprint(), partial="schou-1795")
        self.assertIn("schou-1795", kb._stale_reason(_meta_db(meta)))


class Normalisation(unittest.TestCase):
    def same(self, a: str, b: str):
        self.assertEqual(kb.normalize(a), kb.normalize(b), f"{a!r} vs {b!r}")

    def test_vulgar_fraction_is_not_glued_to_the_integer(self):
        tokens = kb.normalize("14¼ Lod").split()
        self.assertNotIn("141", tokens)
        self.assertEqual(tokens[:2], ["14", "1/4"])

    def test_line_break_hyphenation_is_joined(self):
        self.assertEqual(kb.normalize("fir-\nkantede"), "firkantede")

    def test_old_and_modern_danish_spelling_fold(self):
        self.same("Myndt", "Mønt")
        self.same("Richsdaller", "Rigsdaler")
        self.same("Thaler", "Daler")
        self.same("Schilling", "Skilling")
        self.same("Kaabermønt", "Kobbermønt")
        self.same("Kaabber", "Kobber")

    def test_goldgulden_case_a16(self):
        """The five mismatches of Galster 1934 s. 108 (README, round 3)."""
        self.same("Goldgulden", "Goldgylden")
        self.same("Poul Guiden", "Poul Gylden")   # OCR «gulden» → «guiden»
        self.same("golt", "gold")
        self.same("kraet", "karat")
        self.same("Stück", "Styk")                # the stem; inflected forms meet by prefix search
        self.assertTrue(kb.normalize("Stucken").startswith("styk"))

    def test_unrelated_words_stay_apart(self):
        """A fold must not merge different words: «betaler» is not «daler»."""
        self.assertNotEqual(kb.normalize("betaler"), kb.normalize("be daler"))
        self.assertIn("betaler", kb.normalize("betaler"))


class BruunPrintedPage(unittest.TestCase):
    def test_known_lot(self):
        """Part II lot 13163: PDF 120 is printed page 94."""
        self.assertEqual(bruun_pages.printed_page(2, 120), "94")

    def test_running_head_lower_on_feature_pages(self):
        self.assertEqual(bruun_pages.printed_page(3, 82), "64")
        self.assertEqual(bruun_pages.printed_page(3, 114), "96")

    def test_offset_is_constant_within_each_part(self):
        for part, off in bruun_pages.OFFSET.items():
            heads = bruun_pages.printed_pages(part)
            arabic = {p: int(v) for p, v in heads.items() if v.isdigit()}
            self.assertGreater(len(arabic), 100, f"part {part}: too few running heads read")
            self.assertEqual({p - v for p, v in arabic.items()}, {off}, f"part {part}")

    def test_heal_rewrites_only_the_lot_whose_span_holds_the_page(self):
        lots = heal._lots()
        self.assertGreaterEqual(len({p for p, _ in lots[14206]}), 2, "lot 14206 in Parts II and V")
        report: list[str] = []
        text, n = heal.heal_text("Bruun Part V (lot 14206, p. 93)", lots, report, "t")
        self.assertEqual((text, n), ("Bruun Part V (lot 14206, p. 77)", 1))
        # already printed → untouched, and not reported as unresolved
        text, n = heal.heal_text("Bruun Part V (lot 14206, p. 77)", lots, report, "t")
        self.assertEqual((text, n, report), ("Bruun Part V (lot 14206, p. 77)", 0, []))

    def test_heal_is_idempotent_on_the_data(self):
        """After the 2026-10-19 heal no Bruun page in data/v2 is a PDF page."""
        lots = heal._lots()
        for f in sorted((ROOT / "data" / "v2").glob("**/*.yml")):
            rel = str(f.relative_to(ROOT))
            if rel in heal.SKIP:
                continue
            _, n = heal.heal_text(f.read_text(encoding="utf-8"), lots, [], rel)
            self.assertEqual(n, 0, rel)


class LiveIndex(unittest.TestCase):
    """Shape of real searches; skipped when no current index is built."""

    @classmethod
    def setUpClass(cls):
        if not kb.DB_DEFAULT.exists():
            raise unittest.SkipTest("no kb index — run scripts/kb/kb.py build")
        cls.con = sqlite3.connect(kb.DB_DEFAULT)
        if kb._stale_reason(cls.con):
            raise unittest.SkipTest("kb index is stale — run scripts/kb/kb.py build")

    def test_modern_spelling_finds_the_old_one(self):
        rows, _ = kb.search(self.con, "kobbermønt", work=["secher-ccd"], limit=30)
        self.assertTrue(any("kaab" in r[8].lower() for r in rows))

    def test_act_is_found_among_the_sources(self):
        rows, _ = kb.search(self.con, "kroner 1618 lødig mark", kind=["source"], limit=5)
        self.assertTrue(any(r[1] == "secher-ccd" and r[5] for r in rows),
                        "an act text with a printed page among the first five")


if __name__ == "__main__":
    unittest.main()
