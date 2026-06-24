"""§9a seed-thinning salvage — dropped specimens shed redundant weight +
per-specimen sources, but their distinguishing data (catalogue indices,
fineness, diameter) is carried onto the kept min/middle/max reps."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from lib.seed_thin import thin_coins  # noqa: E402


def _bucket(n, *, km="100", with_diameter=False):
    """n specimens of ONE sub-variant (same km/nominal/ruler/year/mint/metal),
    each carrying a distinct `others` sub-catalogue ref + its own weight."""
    out = []
    for i in range(n):
        c = {
            "id": f"x-{i:02d}",
            "catalog": {"km": km, "others": [f"Dorfmann# {i}"]},
            "nominal": "1 Taler", "ruler": "R", "year_first": 1600,
            "mint": "M", "metal": "silver",
            "weight_rough_g": 20.0 + i * 0.1,
            "sources": [{"type": "museum", "url": f"u{i}", "ref": f"ref{i}"}],
        }
        if with_diameter:
            c["diameter_mm"] = 30.0 + i
        out.append(c)
    return out


class TestSeedThinSalvage(unittest.TestCase):
    def test_thins_to_envelope(self):
        kept, stats = thin_coins(_bucket(7))
        self.assertEqual(len(kept), 3)
        self.assertEqual(stats["thinned_buckets"], 1)

    def test_salvages_all_others_refs(self):
        kept, _ = thin_coins(_bucket(7))
        refs = set()
        for c in kept:
            for x in (c.get("catalog") or {}).get("others") or []:
                refs.add(str(x).replace(" ", "").lower())
        for i in range(7):
            self.assertIn(f"dorfmann#{i}", refs, f"Dorfmann# {i} was lost")

    def test_weights_thinned_not_salvaged(self):
        kept, _ = thin_coins(_bucket(7))
        weighted = [c for c in kept if c.get("weight_rough_g") is not None]
        # only the 3 reps keep a weight; dropped weights are shed
        self.assertEqual(len(weighted), 3)

    def test_below_threshold_untouched(self):
        kept, _ = thin_coins(_bucket(4))
        self.assertEqual(len(kept), 4)

    def test_uncatalogued_gate_leaves_whole(self):
        bucket = _bucket(7)
        for c in bucket:
            c["catalog"] = {}            # no primary ref at all
        kept, stats = thin_coins(bucket, catalogued_only=True)
        self.assertEqual(len(kept), 7)   # gate skips uncatalogued buckets
        self.assertEqual(stats["thinned_buckets"], 0)

    def test_diameter_preserved_when_reps_lack_it(self):
        bucket = _bucket(7, with_diameter=True)
        # strip diameter from the 3 reps (x-00 / x-03 / x-06), keep on a dropped
        for c in bucket:
            if c["id"] in ("x-00", "x-03", "x-06"):
                c.pop("diameter_mm", None)
        kept, _ = thin_coins(bucket)
        self.assertTrue(any(c.get("diameter_mm") for c in kept),
                        "diameter lost — reps lacked it and a dropped value was not salvaged")


if __name__ == "__main__":
    unittest.main()
