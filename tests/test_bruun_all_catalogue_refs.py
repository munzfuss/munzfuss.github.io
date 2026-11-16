"""Bruun lot parser: every catalogue reference a lot prints is captured.

Shapes the parser skipped or cut before 2026-11-17 (inventory over the full
text of all five parts): letter-prefixed numbers (Dav-A3641, Aagaard-TKG6,
FP-SH8.1), lettered type groups (Becker-M 9/166, Malmer-KG 7), decimal-comma
sub-numbers (Sieg-102,3), a catalogue cited twice (refs_more), and an
unclosed paren that swallowed the lot's own Bruun number (lot 14131).
"""
import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location(
    "bruun_parse_lots", ROOT / "scripts" / "bruun_parser" / "02_parse_lots.py")
P = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(P)


def refs(text: str) -> dict:
    masked = P._mask_parens(text)
    out = {}
    for k, pat in P.REF_PATTERNS.items():
        m = pat.search(text if k in P._UNMASKED_KEYS else masked)
        if m:
            out[k] = P._ref_value(k, m)
    return out


def more(text: str) -> dict:
    return P._more_refs(text, P._mask_parens(text), refs(text))


class LetterPrefixes(unittest.TestCase):
    def test_davenport_letter_prefix(self):
        # Part V lot 14161 (2 Krone 1691, Hede 91).
        r = refs("NGC AU-55. Dav-A3641; KM-410; Hede-91; Sieg-47; Schou-12; Aagaard-54; Bruun-7065.")
        self.assertEqual(r["Dav"], "A3641")
        self.assertEqual(r["KM"], "410")

    def test_davenport_large_size_stays_apart(self):
        r = refs("NGC MS-62. KM-147; Dav- LS529; Hede-63D; Bruun-5846.")
        self.assertNotIn("Dav", r)
        self.assertEqual(r["Dav-LS"], "529")
        self.assertEqual(refs("DAV-LS581; KM-85; Bruun-11766.")["Dav-LS"], "581")

    def test_aagaard_codes(self):
        self.assertEqual(refs("Schou-1; Aagaard-TKG6; Bruun-5700.")["Aagaard"], "TKG6")
        self.assertEqual(refs("Schou-52; Aagaard-8S-1; Bruun-7277.")["Aagaard"], "8S-1")
        self.assertEqual(refs("Lange-82; Aagaard-Vsp-1; Bruun-7274.")["Aagaard"], "Vsp-1")
        self.assertEqual(refs("Aagaard-74.1 (49-2/49-5); Bruun-1.")["Aagaard"], "74.1 (49-2/49-5)")

    def test_aagaard_prose_die_is_not_the_index(self):
        # Lot 1217: «Aagaard-A1» in the chain, «(Aagaard 60-1)» in the prose.
        r = refs("NMD-52; Schou-12; Aagaard-A1; Bruun-10082. A different die (Aagaard 60-1) is known.")
        self.assertEqual(r["Aagaard"], "A1")

    def test_fp_letter_series(self):
        self.assertEqual(refs("Schou-1; FP-E6; Bruun-7746.")["FP"], "E6")
        self.assertEqual(refs("Schou-1; FP-SH8.1; Bruun-1.")["FP"], "SH8.1")


class OtherShapes(unittest.TestCase):
    def test_decimal_comma(self):
        self.assertEqual(refs("Hede-53C; Sieg- 102,3; Schou-9; Bruun-5072.")["Sieg"], "102.3")
        self.assertEqual(refs("NGC VF-25. KM-99,2; SM-62; Bruun-11774.")["KM"], "99.2")

    def test_list_comma_is_not_decimal(self):
        self.assertEqual(refs("Dav-1301A; KM-575, 238; Bruun-7640.")["KM"], "575")

    def test_lange_spaced_letter(self):
        self.assertEqual(refs("Aagaard-1.1; Lange-60 B; Bruun-5941.")["Lange"], "60B")

    def test_lange_cf_glued_stays_out(self):
        self.assertNotIn("Lange", refs("KM-130; Lange-Cf 944a; Weinmaster-153; Bruun-14906."))

    def test_becker_and_malmer_groups(self):
        self.assertEqual(refs("Hauberg-10; C. J. Becker-M 9/166; Bruun-1.")["Becker"], "M 9/166")
        self.assertEqual(refs("Hauberg-1; Malmer-KG 7 (CE III:A2); Bruun-1181.")["Malmer"], "KG7")
        self.assertEqual(refs("Malmer-14.A78-b; Bruun-1395;")["Malmer"], "14.A78-b")

    def test_new_catalogues(self):
        r = refs("KM-122; Kalvelage/Trippler-320; Ramus-34-35; Schütz-1606; "
                 "Gaedechens-1633; Weinmaster-153; Stevnsborg-LS1-012; Bruun-1.")
        self.assertEqual(r["Trippler/Kalvelage"], "320")
        self.assertEqual(r["Ramus"], "34-35")
        self.assertEqual(r["Schütz"], "1606")
        self.assertEqual(r["Gaedechens"], "1633")
        self.assertEqual(r["Weinmeister"], "153")
        self.assertEqual(r["LS"], "1-012")

    def test_f_code_never_reads_a_grade(self):
        self.assertNotIn("F", refs("Christian IV . NGC F-12. KM-36; Hede-95B; Bruun-1."))
        self.assertEqual(refs("NGC MS-68. F-295; KM-791.2; Bruun-83.")["F"], "295")

    def test_cf_stays_out(self):
        self.assertNotIn("KM", refs("NGC MS-60. Fr-243; cf. KM-476; Hede- 10; Bruun-7306."))


class UnclosedParen(unittest.TestCase):
    def test_lot_14131(self):
        text = ("NGC AU Details—Cleaned. Dav-3570A; KM- 192.2; Hede-91B; Aagaard-18 "
                "(53-29/53-4; Bruun-6102. Weight: 21.53 gms. Ex: Joh. G. Guildal "
                "Collection (Private Sale - 1918).")
        r = refs(text)
        self.assertEqual(r["Bruun"], "6102")
        self.assertEqual(r["Aagaard"], "18")


class RefsMore(unittest.TestCase):
    def test_two_krause_volumes(self):
        t = "NGC AU Details—Cleaned. Dav-1295; KM- 539 (Denmark); KM-230 (Norway); NMD-2; Bruun-7577."
        self.assertEqual(more(t), {"KM": ["230 (Norway)"]})

    def test_continuation_with_qualifier(self):
        t = "NGC MS-62. Hede-38; Sieg-23.2 (Denmark), 14.2 (Norway); Schou-8; Bruun-7334."
        self.assertEqual(more(t), {"Sieg": ["14.2 (Norway)"]})

    def test_bare_comma_continuation_not_attributed(self):
        t = "NGC EF-45. Dav-LS530, 3537; KM-115; Bruun-5851."
        self.assertEqual(more(t), {})

    def test_number_after_own_bruun_is_description(self):
        t = "NGC MS-64 Red. KM-673; Hede-11; Bruun-8014. Struck on a Skilling 1771, KM-616."
        self.assertEqual(more(t), {})


if __name__ == "__main__":
    unittest.main()
