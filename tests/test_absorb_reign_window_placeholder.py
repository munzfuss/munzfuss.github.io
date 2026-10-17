"""A coin no source dates, but whose ruler is known, keeps its place on the page.

Curator direction 2026-10-17. The page assembly drops a coin with no year
(«no year information»); KMM 150279 (1 Hvid, Hans, Malmø, Schou 146) was about
to vanish that way once its only dated companion, KMM 273987, left the class
because its index is «Sch. 146, cf.». The rule: give such a coin its ruler's
reign window, marked «(?)» — the existing reign-span override then sets
`year_verified: false` and `year_is_reign_span`, so it never drives phase
expansion. The window is a final-layer placeholder: the next attested year
replaces it, and a curator year hold leaves the coin alone.

Also pins the bare «Hans» lookup: KMM writes the king without a numeral, and
`normalise_ruler_name` used to return None for it, so even the old reign-window
fallback could not fire for Hans.
"""
from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "maintenance"))
_spec = importlib.util.spec_from_file_location(
    "absorb_seeds_into_final_v2",
    ROOT / "scripts" / "maintenance" / "absorb_seeds_into_final_v2.py")
AB = importlib.util.module_from_spec(_spec)
sys.modules["absorb_seeds_into_final_v2"] = AB
_spec.loader.exec_module(AB)
from lib.ruler_reigns import reign_window, reign_window_placeholder  # noqa: E402


def enrich(ruler="Hans", member_years=None, holds=None, entity="danish_realm"):
    coin = {"id": "unified-kmk-150279", "ruler": ruler, "nominal": "1 Hvid",
            "composed_of": ["unified-kmk-150279"]}
    if holds:
        coin["_curation_holds"] = holds
    coin["issuing_entity"] = entity
    member = {"id": "unified-kmk-150279", "ruler": ruler, "nominal": "1 Hvid",
              "issuing_entity": entity}
    if member_years:
        member.update({"year_first": member_years[0], "year_last": member_years[1],
                       "year_ranges": [list(member_years)]})
    out, _ = AB._enrich_final_entry(coin, [coin, member], "danish_realm")
    return out


class TestReignPlaceholder(unittest.TestCase):
    def test_bare_hans_resolves(self):
        self.assertEqual(reign_window("Hans"), (1481, 1513))
        self.assertEqual(reign_window("Hans?"), (1481, 1513))

    def test_undated_coin_gets_reign_window_unverified(self):
        out = enrich()
        self.assertEqual((out.get("year_first"), out.get("year_last")), (1481, 1513))
        self.assertIs(out.get("year_verified"), False)
        self.assertIs(out.get("year_is_reign_span"), True)

    def test_attested_year_is_kept(self):
        out = enrich(member_years=(1490, 1490))
        self.assertEqual((out.get("year_first"), out.get("year_last")), (1490, 1490))
        self.assertNotEqual(out.get("year_is_reign_span"), True)

    def test_unknown_ruler_stays_undated(self):
        self.assertIsNone(enrich(ruler="?").get("year_first"))

    def test_curator_year_hold_wins(self):
        self.assertIsNone(enrich(holds={"year_first": "kept undated"}).get("year_first"))


class TestWhoseWindow(unittest.TestCase):
    """2026-10-17, second pass: the first version took the KING's window for
    any name the loose normaliser resolved — a Gottorp duke got 1648-1670, an
    open alternative got its first ruler's reign only."""

    def test_gottorp_duke_reads_the_ducal_table(self):
        self.assertEqual(reign_window_placeholder("Frederik 3 af Slesvig-Holsten-Gottorp", "royal_holstein"), (1616, 1659))

    def test_alternative_spans_both_reigns(self):
        self.assertEqual(reign_window_placeholder("Christian I/Hans ?", "danish_realm"), (1448, 1513))
        self.assertEqual(reign_window_placeholder("Frederik 7 eller Christian 9", "danish_realm"), (1848, 1906))
        self.assertEqual(reign_window_placeholder("Christian 3/4", "danish_realm"), (1534, 1648))

    def test_qualified_unknown_name_stays_undated(self):
        self.assertIsNone(reign_window_placeholder("frederik 3 som ærkebiskop", "danish_realm"))
        self.assertIsNone(reign_window_placeholder("August Frederik von Holsten-Gottorp", "royal_holstein"))

    def test_alternative_placeholder_is_marked_unverified(self):
        out = enrich(ruler="Christian I/Hans ?")
        self.assertEqual((out.get("year_first"), out.get("year_last")), (1448, 1513))
        self.assertIs(out.get("year_verified"), False)
        self.assertIs(out.get("year_is_reign_span"), True)

    def test_issuer_decides_whose_window(self):
        # Curator 2026-10-17: a same-named ruler of another issuer is another man.
        self.assertEqual(reign_window_placeholder("Frederik 3", "gottorp_duchy"), (1616, 1659))
        self.assertIsNone(reign_window_placeholder("Hans", "sweden"))
        self.assertIsNone(reign_window_placeholder("Frederik 3", "erzbisthum_bremen_verden"))
        self.assertEqual(reign_window_placeholder("Christian IV.", ["danish_realm", "royal_holstein"]), (1588, 1648))
        self.assertIsNone(enrich(entity="sweden").get("year_first"))

    def test_sonderburg_hans_der_juengere(self):
        # NDB 10 (1974) S. 534 f.: his third from the Flensburg treaty of
        # 27.1.1564, † 9.10.1622. KMM / NGC write him several ways.
        for r in ("Hans den Yngre", "Hans  den Yngre", "Johann",
                  "Hans den Yngre af Slesvig-Holsten-Sønderborg 1564-1622"):
            self.assertEqual(reign_window_placeholder(r, "sonderburg_duchy"), (1564, 1622), r)
        self.assertIsNone(reign_window_placeholder("Johann", "royal_holstein"))

    def test_medieval_rulers_and_kmm_misspellings(self):
        # Undated-coins plan row 2 (curator 2026-10-17): KMM's own spellings.
        cases = {"Christoffer2": (1320, 1332), "Ckristopher II": (1320, 1332),
                 "Chyristoffer 1": (1252, 1259), "Ereik Menved": (1286, 1319),
                 "Hardeknuyd": (1035, 1042), "Magnud den Gode": (1042, 1047),
                 "Vardemar I": (1157, 1182), "Margrethe": (1376, 1412),
                 "Kongeløs tid": (1332, 1340), "Jakob Erlandsen": (1249, 1274),
                 "Kristian 1": (1448, 1481), "Chrtistian 4": (1588, 1648)}
        for r, w in cases.items():
            self.assertEqual(reign_window_placeholder(r, "danish_realm"), w, r)
        self.assertEqual(reign_window_placeholder("Håkon 5 Magnusson", "danish_norway"), (1299, 1319))
        # Not resolved on purpose: a modern queen, a vague dynasty, an
        # ambiguous first name.
        for r in ("Margrethe 2", "Valdemarerne?", "Johan"):
            self.assertIsNone(reign_window_placeholder(r, "danish_realm"), r)

    def test_schauenburg_ernst_iii(self):
        # NumisMaster MC_96084 ruler link «Ernst III 1601 - 1622».
        self.assertEqual(reign_window_placeholder("Ernst III", "schauenburg_pinneberg"), (1601, 1622))
        self.assertEqual(reign_window_placeholder("Ernst 3 af Schaumburg-Pinneberg", "royal_holstein"), (1601, 1622))
        self.assertIsNone(reign_window_placeholder("Ernst III", "danish_realm"))

    def test_rigsraadet(self):
        self.assertEqual(reign_window_placeholder("Rigsrådet", "danish_realm"), (1481, 1483))


if __name__ == "__main__":
    unittest.main()
