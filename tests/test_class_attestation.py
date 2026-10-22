"""A final kept the citations of a seed that had left its class, for good.

Absorb rebuilds a final as the UNION of its stored values and its class, so
§9a curator / fold citations survive a re-flow. The union has no inverse: on
2026-10-22 the Galster 155 final (c-afd707d6) carried 163 citations of
Galster 36 — Numista 152921, danskmoent fr/hg36.htm, 161 KMM korshvid
specimens — two days after 14ef43a moved KMM 533276 out of the G36 class into
G155's. Nothing flagged it: every check asks «was anything lost?», and an
extra citation is a gain.

`lib.class_attestation` classifies a final's values by who attests them:
`moved` (a class of another final — dropped), `orphan` (only classes that reach
no final — kept, it would leave the render), `unseeded` (no class — the §9a
curator / fold case, kept). These tests pin the three causes and the two key
traps found while measuring: one url (a Bruun PDF) serving many lots, and
equal readings under a bare source label recurring across unrelated coins.
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from lib.class_attestation import AttestationIndex, prune_moved  # noqa: E402

PDF = "https://example.org/bruun_part2.pdf"


def S(url, ref):
    return {"type": "literature", "url": url, "ref": ref}


def _index(finals):
    unified = [
        {"id": "c-g155", "composed_of": ["galster-155", "kmk-533276"],
         "sources": [S("https://dm/hg155.htm", "Galster 155"),
                     S("https://kmm/533276", "KMM 533276"),
                     S(PDF, "Bruun Part II, lot 1")],
         "weight_rough_g": [{"value": 0.7, "source": "KMM 533276"}]},
        {"id": "c-g36", "composed_of": ["numista-152921"],
         "sources": [S("https://numista/152921", "Numista N#152921"),
                     S(PDF, "Bruun Part II, lot 2")],
         "weight_rough_g": [{"value": 0.8, "source": "KMM 999"},
                            {"value": 0.875, "source": "ucoin"}]},
        # a class whose head seed was excluded: reaches no final
        {"id": "c-stub", "composed_of": ["kmk-642893"],
         "sources": [S("https://kmm/642975", "KMM 642975")]},
    ]
    return AttestationIndex.build(unified, finals)


def _g155(**extra):
    fc = {"id": "c-g155", "composed_of": ["c-g155"],
          "sources": [S("https://dm/hg155.htm", "Galster 155"),
                      S("https://kmm/533276", "KMM 533276"),
                      S("https://numista/152921", "Numista N#152921"),   # moved
                      S("https://kmm/642975", "KMM 642975"),             # orphan
                      S("https://curator/page", "curator citation"),     # unseeded
                      S(PDF, "Bruun Part II, lot 1"),
                      S(PDF, "Bruun Part II, lot 2")],                   # moved
          "weight_rough_g": [{"value": 0.7, "source": "KMM 533276"},
                             {"value": 0.8, "source": "KMM 999"},        # moved
                             {"value": 0.875, "source": "ucoin"}]}       # generic
    fc.update(extra)
    return fc


G36 = {"id": "c-g36", "composed_of": ["c-g36"],
       "sources": [S("https://numista/152921", "Numista N#152921"),
                   S(PDF, "Bruun Part II, lot 2")],
       "weight_rough_g": [{"value": 0.8, "source": "KMM 999"}]}


class Causes(unittest.TestCase):
    def test_three_causes(self):
        fc = _g155()
        idx = _index([fc, G36])
        r = idx.classify(fc, "sources")
        self.assertEqual(sorted(v["ref"] for v, _ in r["moved"]),
                         ["Bruun Part II, lot 2", "Numista N#152921"])
        self.assertEqual({w for _, w in r["moved"]}, {"c-g36"})
        self.assertEqual([v["ref"] for v, _ in r["orphan"]], ["KMM 642975"])
        self.assertEqual([v["ref"] for v in r["unseeded"]], ["curator citation"])

    def test_shared_pdf_url_is_not_attestation(self):
        """Lot 2 shares the PDF url with lot 1, which the class carries — the
        url alone would call it attested and keep it for ever."""
        fc = _g155()
        r = _index([fc, G36]).classify(fc, "sources")
        self.assertIn("Bruun Part II, lot 2", [v["ref"] for v, _ in r["moved"]])

    def test_moved_needs_a_final(self):
        """If the attesting class reaches no final, dropping would remove the
        value from the render — orphan, never moved."""
        fc = _g155()
        r = _index([fc]).classify(fc, "sources")   # G36 has no final here
        self.assertEqual(r["moved"], [])
        self.assertEqual(len(r["orphan"]), 3)

    def test_moved_needs_the_home_to_carry_it(self):
        """The home final not re-absorbed yet: dropping from F would leave the
        value nowhere — not moved."""
        fc = _g155()
        r = _index([fc, {"id": "c-g36", "composed_of": ["c-g36"]}]).classify(fc, "sources")
        self.assertEqual(r["moved"], [])

    def test_generic_reading_label_never_classified(self):
        fc = _g155()
        r = _index([fc, G36]).classify(fc, "weight_rough_g")
        self.assertEqual([v for v, _ in r["moved"]],
                         [{"value": 0.8, "source": "KMM 999"}])
        flat = [v for k in r.values() for v in k]
        self.assertFalse(any("ucoin" in str(v) for v in flat))


class Twin(unittest.TestCase):
    def test_shown_final_keeps_value_whose_home_is_unsorted(self):
        """km-33-ernst-1603 (classified, on the page) and c-a4a6e739 (seed_unsorted)
        are both KM 33: one coin split in two. Dropping the NumisMaster citation
        from the shown one would take it off the page — twin, kept."""
        fc = _g155(fuss="luebischer_muenzfuss")
        home = dict(G36, fuss="seed_unsorted")
        idx = _index([fc, home])
        r = idx.classify(fc, "sources")
        self.assertEqual(r["moved"], [])
        self.assertEqual(len(r["twin"]), 2)
        self.assertEqual(prune_moved(fc, idx).get("sources"), None)
        self.assertEqual(len(fc["sources"]), 7)

    def test_shown_home_or_unshown_loser_is_moved(self):
        for f_fuss, g_fuss in (("a", "b"), ("seed_unsorted", "seed_unsorted"),
                               ("seed_unsorted", "b")):
            fc = _g155(fuss=f_fuss)
            r = _index([fc, dict(G36, fuss=g_fuss)]).classify(fc, "sources")
            self.assertEqual(len(r["moved"]), 2, (f_fuss, g_fuss))


class Prune(unittest.TestCase):
    def test_prune_drops_only_moved(self):
        fc = _g155()
        dropped = prune_moved(fc, _index([fc, G36]))
        refs = [s["ref"] for s in fc["sources"]]
        self.assertEqual(refs, ["Galster 155", "KMM 533276", "KMM 642975",
                                "curator citation", "Bruun Part II, lot 1"])
        self.assertEqual(len(dropped["sources"]), 2)
        self.assertEqual(fc["weight_rough_g"],
                         [{"value": 0.7, "source": "KMM 533276"},
                          {"value": 0.875, "source": "ucoin"}])

    def test_curation_hold_freezes_field(self):
        fc = _g155(_curation_holds={"sources": "curator keeps these"})
        prune_moved(fc, _index([fc, G36]))
        self.assertEqual(len(fc["sources"]), 7)

    def test_own_class_wins_over_other(self):
        """A citation both classes carry is attested by F's own — kept."""
        fc = {"id": "c-g36", "composed_of": ["c-g36"],
              "sources": [S("https://numista/152921", "Numista N#152921")]}
        idx = _index([fc, _g155()])
        self.assertEqual(prune_moved(fc, idx), {})  # own class attests it
        self.assertEqual(len(fc["sources"]), 1)

    def test_foundation_reaching_class_by_seed_id(self):
        """Older finals list SEED ids in composed_of — resolved to the class."""
        fc = {"id": "km-old", "composed_of": ["galster-155"],
              "sources": [S("https://numista/152921", "Numista N#152921")]}
        idx = _index([fc, G36])
        self.assertEqual(idx.final_classes["km-old"], {"c-g155"})
        self.assertEqual(len(prune_moved(fc, idx)["sources"]), 1)


if __name__ == "__main__":
    unittest.main()
