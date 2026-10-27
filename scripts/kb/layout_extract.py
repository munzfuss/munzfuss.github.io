#!/usr/bin/env python3
"""Second text layer of every cached PDF: `pdftotext -layout`.

The corpus extracts (`*.extract.txt`, `pages/NNNN.txt`) are plain pdftotext,
which guesses a reading order. On a page laid out in columns that are not a
running text — a contents page, a table, marginal notes — the guess can
interleave the columns: the Denar til daler (2018) contents page put chapter
4's author under chapter 6's heading (2026-10-27). `-layout` keeps the
columns side by side as printed, so what stands next to what can be read off.

This layer is for checking, not for search: `kb.py build` does not index it
(the corpus manifest does not name it), so a hit never appears twice. Read a
page with `kb.py page <pdf> <n> --mode layout`, or open the file here.

Output: scripts/cache/_derived/layout/<path of the pdf under scripts/cache>.layout.txt,
pages separated by form feeds (\\f), page N = the N-th chunk. A file is
rewritten only when the PDF is newer.

    .venv/bin/python scripts/kb/layout_extract.py            # every PDF
    .venv/bin/python scripts/kb/layout_extract.py bruun      # paths containing «bruun»
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
CACHE = REPO / "scripts" / "cache"
OUT = CACHE / "_derived" / "layout"


def layout_path(pdf: Path) -> Path:
    return OUT / (str(pdf.relative_to(CACHE)) + ".layout.txt")


def main(argv: list[str]) -> int:
    needle = argv[0] if argv else ""
    pdfs = sorted(p for p in CACHE.rglob("*.pdf")
                  if needle in str(p) and OUT not in p.parents)
    done = skipped = failed = 0
    for pdf in pdfs:
        out = layout_path(pdf)
        if out.exists() and out.stat().st_mtime >= pdf.stat().st_mtime:
            skipped += 1
            continue
        out.parent.mkdir(parents=True, exist_ok=True)
        r = subprocess.run(["pdftotext", "-layout", str(pdf), str(out)],
                           capture_output=True, text=True)
        if r.returncode:
            print(f"  ✗ {pdf.relative_to(CACHE)}: {r.stderr.strip()[:200]}", file=sys.stderr)
            failed += 1
            continue
        done += 1
    print(f"layout: {done} written, {skipped} up to date, {failed} failed → {OUT.relative_to(REPO)}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
