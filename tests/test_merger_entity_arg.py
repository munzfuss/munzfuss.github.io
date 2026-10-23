"""An --entity nobody has a seed for must fail, not succeed over zero coins.

`--entity danish_realm,danish_norway` used to look like it ought to work and did not:
the flag takes ONE entity, so the comma-joined string matches no seed file. The
run then completed normally, wrote the unified yamls, and reported

    Per-source seeds total:  0
    Unified entries total:   0
    ✓ Wrote unified yamls to …/data/v2/seed_unified/

which reads as «nothing to merge», not as «you asked for an entity that doesn't
exist». The re-flow it was supposed to perform silently didn't happen, and the
next step in the chain — absorb, then the reflow gate — would have measured
against a tree nobody had re-merged (CLAUDE.md §9b: the baseline was not what
the caller assumed).
"""
from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MERGER = ROOT / "scripts" / "maintenance" / "merge_seeds_cross_source.py"


def run(*args) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(MERGER), *args],
                          capture_output=True, text=True, cwd=ROOT)


class TestUnknownEntityIsRejected(unittest.TestCase):
    def test_a_typo_exits_nonzero(self):
        r = run("--entity", "danish_ralm")
        self.assertEqual(r.returncode, 2)
        self.assertIn("Unknown entity", r.stdout)

    def test_the_error_lists_what_is_available(self):
        r = run("--entity", "danish_ralm")
        self.assertIn("danish_realm", r.stdout)

    def test_a_comma_list_rejects_its_unknown_member(self):
        # Since 2026-10-23 `--entity a,b` runs several entities in one
        # process; an unknown name inside the list still fails, by name.
        r = run("--entity", "danish_realm,danish_ralm")
        self.assertEqual(r.returncode, 2)
        self.assertIn("danish_ralm", r.stdout)

    def test_nothing_is_written_on_rejection(self):
        # The rejection happens before any output path is touched.
        before = {p: p.stat().st_mtime
                  for p in (ROOT / "data" / "v2" / "seed_unified").glob("*.yml")}
        run("--entity", "danish_ralm", "--apply")
        after = {p: p.stat().st_mtime
                 for p in (ROOT / "data" / "v2" / "seed_unified").glob("*.yml")}
        self.assertEqual(before, after)


class TestAKnownEntityStillRuns(unittest.TestCase):
    def test_a_real_entity_passes_the_guard(self):
        # Dry-run on the smallest entity: the guard must not stand in the way.
        r = run("--entity", "rantzau_county")
        self.assertEqual(r.returncode, 0, r.stdout[-2000:])
        self.assertNotIn("Unknown entity", r.stdout)


if __name__ == "__main__":
    unittest.main()
