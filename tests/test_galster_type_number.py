"""build_galster_denmark_seed._add_titled_type_number — the page's type number.

A danskmoent Galster page describes one type: the title prints «Frederik 1.,
Galster 57» and the sub-groups cite «Galster 57A» / «57B». The parser keeps the
first sub-group's refs, so the bare type number has to be added beside the
letter, or `seed_merge._drop_bare_superseded_by_letter` drops it as a stale
reading (2026-10-29: Galster 57 and 55 lost their type number on a re-seed).
Only a title that prints «Galster N» counts — `hg27` («gh27») prints 27A / 27B
and no bare 27.

Run via:
    .venv/bin/python -m unittest tests.test_galster_type_number -v
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


def _run(galster, num, title):
    cat = {"galster": galster}
    _bg._add_titled_type_number(cat, {"galster_number": num,
                                      "raw_text_excerpt": f"{title} \n\n## …"})
    return cat["galster"]


class TestTitledTypeNumber(unittest.TestCase):
    def test_title_prints_number_kept_beside_letter(self):
        self.assertEqual(_run("57B", "57", "Frederik 1., Galster 57"), ["57", "57B"])

    def test_title_without_number_adds_nothing(self):
        self.assertEqual(_run("27A", "27", "gh27"), "27A")

    def test_bare_already_present(self):
        self.assertEqual(_run(["57", "57B"], "57", "Frederik 1., Galster 57"), ["57", "57B"])

    def test_letter_on_other_base_adds_nothing(self):
        self.assertEqual(_run("125A", "120", "Frederik 1., Galster 120"), "125A")

    def test_title_number_must_match_whole(self):
        # «Galster 57B» in a title is not the bare type number 57
        self.assertEqual(_run("57B", "57", "Frederik 1., Galster 57B"), "57B")


if __name__ == "__main__":
    unittest.main()
