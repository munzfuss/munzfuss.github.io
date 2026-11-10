"""Every script reaches the harvest cache through `lib.paths`, never through a
spelled-out `scripts/cache` path.

`lib.paths.HARVEST_ROOT` honours MUNZFUSS_HARVEST_DIR and `local.env`, and in a
git worktree (whose `scripts/cache` submodule directory is empty) resolves to
the main checkout's cache. A path built as `ROOT / "scripts" / "cache"` or
`"scripts/cache/…"` bypasses all of that and reads the empty directory — the
failure this test exists to stop (curator 2026-11-10).

The check looks at code only: comment lines are skipped, and the pattern needs
a quote right before `scripts`, so prose in docstrings («`scripts/cache/x`»)
does not trip it.
"""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATTERN = re.compile(r"""["']scripts["']\s*/\s*["']cache["']|[f]?["']scripts/cache\b""")
ALLOWED = {
    ROOT / "scripts" / "lib" / "paths.py",
    Path(__file__).resolve(),
}


def offenders() -> list[str]:
    out = []
    files = list((ROOT / "scripts").rglob("*.py")) + list((ROOT / "tests").glob("*.py"))
    for f in files:
        if f.resolve() in ALLOWED or "cache" in f.relative_to(ROOT).parts[1:2]:
            continue
        for n, line in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
            if line.lstrip().startswith("#"):
                continue
            if PATTERN.search(line):
                out.append(f"{f.relative_to(ROOT)}:{n}: {line.strip()}")
    return out


class CachePathsViaLib(unittest.TestCase):
    def test_no_spelled_out_cache_paths(self):
        found = offenders()
        self.assertEqual(found, [], "use lib.paths.HARVEST_ROOT (or a per-source "
                         "constant) instead of a spelled-out scripts/cache path:\n"
                         + "\n".join(found))


if __name__ == "__main__":
    unittest.main()
