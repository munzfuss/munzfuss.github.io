"""build_galster_denmark_seed — a caption read on another page cites that page.

A denomination overview (halvpenn.htm, lebard.htm, 3nobel.htm …) is not put
into a coin's `sources` as navigation (curator 2026-06-03). When one of its
drawing captions gives the coin's weight or diameter, it IS the source of that
value and goes into `sources` beside the coin's own page (curator 2026-11-28;
Galster 6: pommgals.htm row + halvpenn.htm caption «ca. 0,14 gr, 12 mm»).

Run via:
    .venv/bin/python -m unittest tests.test_galster_caption_page_source -v
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
import unittest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

_spec = importlib.util.spec_from_file_location(
    "build_galster_denmark_seed",
    str(PROJECT_ROOT / "scripts" / "maintenance" / "build_galster_denmark_seed.py"),
)
_bg = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_bg)

CAP = {"galster": "6", "page": "halvpenn.htm", "image": "gif/epomg6.gif",
       "metal": "Ae/Ag", "diameter_mm": 12, "weight_min": 0.14,
       "weight_max": None, "approx": True}
OWN = {"type": "literature", "url": "https://www.danskmoent.dk/pommgals.htm",
       "ref": "Galster 6 (epomg) — danskmoent.dk pommgals.htm"}


def _entry(url=OWN["url"]):
    return {"id": "dk-galster-epomg-6", "metal": "billon",
            "catalog": {"galster": "6"}, "sources": [dict(OWN, url=url)]}


class CaptionPageSourceTest(unittest.TestCase):
    def test_other_page_cited_once(self):
        e = _entry()
        _bg.apply_caption_ranges([e], {"6": [CAP]})
        _bg.apply_caption_diameters([e], {"6": [CAP]})
        urls = [s["url"] for s in e["sources"]]
        self.assertEqual(urls, [OWN["url"], "https://www.danskmoent.dk/halvpenn.htm"])

    def test_own_page_not_repeated(self):
        cap = dict(CAP, page="chr/c2g80.htm", galster="80")
        e = _entry("https://www.danskmoent.dk/chr/c2g80.htm")
        e["catalog"]["galster"] = "80"
        _bg.apply_caption_ranges([e], {"80": [cap]})
        self.assertEqual(len(e["sources"]), 1)

    def test_unused_caption_not_cited(self):
        e = _entry()
        e["weight_rough_g"] = [{"value": 0.2, "source": "x"}]
        e["diameter_mm"] = [{"value": 11.0, "source": "x"}]
        _bg.apply_caption_ranges([e], {"6": [CAP]})
        _bg.apply_caption_diameters([e], {"6": [CAP]})
        self.assertEqual(len(e["sources"]), 1)


if __name__ == "__main__":
    unittest.main()
