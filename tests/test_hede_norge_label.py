"""The rendered catalogue column must tell the reader WHICH Hede series a
number belongs to.

Hede numbers the Danish and the Norwegian volumes as two independent series —
«Hede 39» is a 2 Dukat in gold, «Hede Norge 39» a 1 Speciedaler in silver —
and danskmoent.dk disambiguates them in print exactly that way. The Denmark
page renders the Danish, Norwegian and royal-Holstein entities side by side, so
without the qualifier a Norwegian index reads as a Danish one.

Two tiers, because the evidence differs:
  * ATTESTED — the record carries `hede_volume` (`nc5h`, `nf3h`).
  * INFERRED — the number is cited by KMK / Numista / Bruun, none of which
    publishes the volume, so the series is read off the issuing entity and the
    tooltip says so rather than asserting a source that does not exist.

The critical negative case is a DANISH Hede number on a NORWEGIAN coin: Bruun
lot 17085 prints a Christiania 2 Ducat as «Hede-39 (Denmark)», and our own
`dk-hede-f5h36a/b/c` (Kongsberg, Danish volume `f5h`) sit in the danish_norway
entity. An attested volume must always win over the entity guess.

Added 2026-07-25.

Run:
    .venv/bin/python -m unittest tests.test_hede_norge_label -v
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from lib.compute import _compute_catalog_groups  # noqa: E402
from lib.schema import Coin  # noqa: E402


# A plain Hede number carries only the catalogue-name tooltip (curator
# 2026-10-27, CATALOG_TOOLTIP) — never a Hede Norge marker.
_PLAIN_HEDE_TIP = "marker.cat_hede"


def _coin(hede, volume=None, entity=None):
    return Coin.model_validate({
        "id": "t", "nominal": "1 Speciedaler", "metal": "silver",
        "fuss": "f", "phase": "A", "kind": "kurant",
        "year_label": "1665", "year_first": 1665, "year_last": 1665,
        "issuing_entity": entity,
        "catalog": {"hede": hede, "hede_volume": volume},
    })


def _group(coin):
    """(prefix, values, tooltip) for the Hede group, or None."""
    for prefix, vals, tip in _compute_catalog_groups(coin):
        if prefix.startswith("Hede"):
            return prefix, vals, tip
    return None


class TestAttestedSeries(unittest.TestCase):
    def test_norwegian_volume_is_qualified(self):
        prefix, vals, tip = _group(_coin("39", "nf3h", "danish_norway"))
        self.assertEqual(prefix, "Hede Norge")
        self.assertEqual(vals, ["39"])
        self.assertEqual(tip, "marker.hede_norge_attested")

    def test_danish_volume_stays_plain(self):
        prefix, _, tip = _group(_coin("39", "f3h", "danish_realm"))
        self.assertEqual(prefix, "Hede")
        self.assertEqual(tip, _PLAIN_HEDE_TIP)

    def test_attested_danish_volume_beats_the_norwegian_entity(self):
        """dk-hede-f5h36a: Kongsberg mint, Danish volume, Norwegian entity.
        The published volume must win — this is the case Bruun flags in print
        as «Hede-39 (Denmark)» on a NORWAY lot."""
        prefix, _, _ = _group(_coin("36A", "f5h", "danish_norway"))
        self.assertEqual(prefix, "Hede")


class TestInferredSeries(unittest.TestCase):
    def test_volumeless_norwegian_coin_is_qualified_and_marked(self):
        """A Bruun / KMK / Numista citation carries no volume; the series is
        inferred, and the tooltip must say so."""
        prefix, vals, tip = _group(_coin("60", None, "danish_norway"))
        self.assertEqual(prefix, "Hede Norge")
        self.assertEqual(vals, ["60"])
        self.assertEqual(tip, "marker.hede_norge_inferred")

    def test_volumeless_danish_coin_stays_plain(self):
        prefix, _, tip = _group(_coin("60", None, "danish_realm"))
        self.assertEqual(prefix, "Hede")
        self.assertEqual(tip, _PLAIN_HEDE_TIP)

    def test_joint_entity_including_norway_is_qualified(self):
        prefix, _, _ = _group(
            _coin("60", None, ["danish_realm", "danish_norway"]))
        self.assertEqual(prefix, "Hede Norge")

    def test_no_entity_stays_plain(self):
        prefix, _, tip = _group(_coin("60", None, None))
        self.assertEqual(prefix, "Hede")
        self.assertEqual(tip, _PLAIN_HEDE_TIP)


class TestTooltipKeysAreTranslated(unittest.TestCase):
    def test_both_keys_exist_in_all_three_languages(self):
        import yaml
        ui = yaml.safe_load(
            (PROJECT_ROOT / "data/i18n/ui.yml").read_text(encoding="utf-8"))
        for key in ("marker.hede_norge_attested", "marker.hede_norge_inferred"):
            self.assertIn(key, ui)
            for lang in ("de", "en", "uk"):
                self.assertTrue(ui[key].get(lang), f"{key} missing {lang}")


if __name__ == "__main__":
    unittest.main()
