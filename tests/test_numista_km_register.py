"""Numista «<km> (<Country>)» Krause-volume tag → register-keyed km dict
(`build_numista_seed._apply_km_country_register`), and the merger's
cross-register single-KM preservation (`_merge_km_field`).

Guards two things that bit during the 2026-06-25 country→register work:
  * the «no» (Norway) register is a YAML BOOLEAN — the code is «nor», and a
    `{nor: '260'}` dict must round-trip through YAML as the string key, not False;
  * a single-register km dict whose register != the entity's own volume must NOT
    collapse to bare (that drops the cross-volume tag and re-opens §9.4).
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "maintenance"))
import build_numista_seed as bns  # noqa: E402
from merge_seeds_cross_source import _ENTITY_TO_KM_REGISTER, _merge_km_field  # noqa: E402


class TestCountryRegisterParse(unittest.TestCase):
    def _km(self, km, entity):
        cat = {"km": km}
        bns._apply_km_country_register(cat, entity)
        return cat.get("km")

    def test_single_country_tag(self):
        self.assertEqual(self._km("479 (Denmark)", "danish_norway"), {"dk": "479"})

    def test_cross_volume_bare_plus_tagged(self):
        # bare «260» → Norway (entity register «nor»); «645 (Denmark)» → dk
        self.assertEqual(self._km(["260", "645 (Denmark)"], "danish_norway"),
                         {"nor": "260", "dk": "645"})

    def test_unknown_parenthetical_left_raw(self):
        # «OM» is not a country → no restructuring
        self.assertEqual(self._km("505 (OM)", "danish_realm"), "505 (OM)")

    def test_no_tag_unchanged(self):
        self.assertEqual(self._km("526", "danish_realm"), "526")

    def test_no_entity_register_aborts(self):
        # bare value with no resolvable entity register → leave km untouched
        self.assertEqual(self._km(["260", "645 (Denmark)"], "_unclassified"),
                         ["260", "645 (Denmark)"])


class TestIssuerCountryVolume(unittest.TestCase):
    """A single bare KM on a page Numista files under «Norway» / «Denmark» is in
    that country's Krause volume when the coin routes to the other kingdom."""

    def _km(self, km, entity, issuer):
        cat = {"km": km}
        bns._apply_km_country_register(cat, entity, issuer)
        return cat.get("km")

    def test_norway_section_on_danish_realm(self):
        # N#100478, Christian VI Reisedaler 1732-1733: Norway KM 230
        # (Denmark KM 230 is the 3 Speciedaler 1661).
        self.assertEqual(self._km("230", "danish_realm", "Norway"), {"nor": "230"})

    def test_denmark_section_on_danish_norway(self):
        # N#83064, Danish Asiatic Company Piastre 1777: Denmark KM 639.
        self.assertEqual(self._km("639", "danish_norway", "Denmark"), {"dk": "639"})

    def test_same_volume_untouched(self):
        self.assertEqual(self._km("230", "danish_norway", "Norway"), "230")
        self.assertEqual(self._km("640", "danish_realm", "Denmark"), "640")

    def test_bare_list_untouched(self):
        # N#119248 under «Norway»: «260» is Norway, «645» Denmark — the section
        # does not name the volume of each member of a bare list.
        self.assertEqual(self._km(["260", "645"], "danish_realm", "Norway"),
                         ["260", "645"])

    def test_sh_entity_not_decided(self):
        self.assertEqual(self._km("640", "royal_holstein", "Denmark"), "640")

    def test_sections_with_own_numbering_unchanged(self):
        self.assertEqual(self._km("26", "royal_holstein", "Glückstadt, City of"),
                         {"glu": "26"})


class TestNorwayRegisterIsNotYamlBoolean(unittest.TestCase):
    def test_nor_code(self):
        self.assertEqual(_ENTITY_TO_KM_REGISTER["danish_norway"], "nor")
        self.assertNotIn(_ENTITY_TO_KM_REGISTER["danish_norway"],
                         {"no", "yes", "true", "false", "on", "off", "n", "y"})

    def test_nor_survives_yaml_roundtrip(self):
        dumped = yaml.dump({"km": {"nor": "260", "dk": "645"}},
                           sort_keys=False, allow_unicode=True, default_flow_style=False)
        back = yaml.safe_load(dumped)["km"]
        self.assertEqual(back, {"nor": "260", "dk": "645"})  # not {False: ...}


class TestMergerCrossRegisterSingleKm(unittest.TestCase):
    def test_single_register_matching_entity_collapses(self):
        # dk on a danish_realm coin → bare (unchanged behaviour)
        km, _ = _merge_km_field([{"id": "x", "catalog": {"km": {"dk": "75"}}}], "danish_realm")
        self.assertEqual(km, "75")

    def test_single_register_cross_volume_kept(self):
        # dk on a danish_norway coin → keep the dict (don't drop the register)
        km, _ = _merge_km_field([{"id": "x", "catalog": {"km": {"dk": "479"}}}], "danish_norway")
        self.assertEqual(km, {"dk": "479"})


if __name__ == "__main__":
    unittest.main()
