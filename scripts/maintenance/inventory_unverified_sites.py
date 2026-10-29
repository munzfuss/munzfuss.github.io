#!/usr/bin/env python3
"""List every place a seed builder (or the shared seed writer) sets a
`<field>_verified` flag to False, and whether a Coin.uncertainty entry is
recorded beside it (curator 2026-10-29, docs/plans/uncertainty_markers.md).

A site counts as covered when `unc.add` / `uncertainty` appears within
`--window` lines after it. Heuristic by design: it points at the sites to
read, it does not judge them.

    .venv/bin/python scripts/maintenance/inventory_unverified_sites.py [--missing]
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FILES = sorted((ROOT / "scripts" / "maintenance").glob("build_*_seed.py")) + [
    ROOT / "scripts" / "lib" / "v2_seed_writer.py"]
SITE = re.compile(r"""["']?(\w*_verified)["']?\s*\]?\s*[:=]\s*(False|not\b|.*\bif not\b)""")
COVER = re.compile(r"\bunc\.add\b|_unc\.add\b|\buncertainty\b|\byear_unc\b")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--window", type=int, default=25)
    ap.add_argument("--missing", action="store_true", help="only uncovered sites")
    a = ap.parse_args()
    n = covered = 0
    for f in FILES:
        lines = f.read_text().splitlines()
        for i, line in enumerate(lines):
            code = line.split("#", 1)[0]
            m = SITE.search(code)
            if not m or "True" in code.split(m.group(1), 1)[1][:12]:
                continue
            n += 1
            ok = any(COVER.search(l.split("#", 1)[0])
                     for l in lines[max(0, i - 12): i + a.window])
            covered += ok
            if a.missing and ok:
                continue
            print(f"{'✓' if ok else '·'} {f.relative_to(ROOT)}:{i + 1}: {line.strip()[:100]}")
    print(f"\n{covered} of {n} sites record an uncertainty entry")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
