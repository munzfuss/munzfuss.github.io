"""build_galster_denmark_seed._add_subgroup_letters — lettered variants.

Checked against the cached danskmoent pages (curator 2026-10-30): bajg19's
sub-groups cite no number but the page writes «Galster 19A:» → 19A, 19B;
f1g55's group B cites «Galster 55B» → 55B; f1g57's groups A-C cite Galster
57B, 57B, 57A → 57A and 57B, never «57C»; nc2g174's groups cite the bare
«Galster 174» → nothing added. Skipped when the harvest cache is absent.

Run via:
    .venv/bin/python -m unittest tests.test_galster_subgroup_letters -v
"""
from __future__ import annotations

import importlib.util
import json
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


def _run(page: str, start):
    p = _bg.GALSTER_CACHE / f"{page}.json"
    if not p.is_file():
        raise unittest.SkipTest("harvest cache not present")
    data = json.loads(p.read_text())
    cat = {"galster": start}
    _bg._add_subgroup_letters(cat, data)
    return cat["galster"]


class SubgroupLettersTest(unittest.TestCase):
    def test_uncited_groups_with_lettered_caption(self):
        self.assertEqual(_run("bajg19", "19"), ["19", "19A", "19B"])

    def test_groups_citing_their_letters(self):
        self.assertEqual(_run("fr_f1g55", ["55", "55A"]), ["55", "55A", "55B"])

    def test_group_letter_never_used_when_groups_cite_galster(self):
        self.assertEqual(_run("fr_f1g57", ["57", "57B"]), ["57", "57B", "57A"])

    def test_groups_citing_bare_number_add_nothing(self):
        self.assertEqual(_run("norge_nc2g174", "174"), "174")


if __name__ == "__main__":
    unittest.main()
