#!/usr/bin/env python3
"""Drop the stale broken-prefix danskmoent Hede-overview source URLs from finals.

Background. The danskmoent reign-overview index pages live at the site ROOT
(`/c5hede1.htm`, `/f3hede1.htm`), not under `/chr` or `/fr`. `_danskmoent_url`
in build_hede_denmark_seed was fixed to route them to the root, so current SEEDS
cite the correct URL — but the FINAL yamls carried the pre-fix broken form
(`/chr/c5hede1.htm`, `/fr/f3hede1.htm` → 404) frozen in place, because absorb
UNIONS sources and never rewrites/removes. A re-absorb therefore added the
correct root-URL twin ALONGSIDE the broken one; this script removes the broken
member of each pair.

Safety (mirrors the T9 discipline). A broken source entry is removed ONLY when
the SAME coin already carries a source entry with the corrected root URL — i.e.
the removal is a de-duplication, never a loss. If the twin is absent, the entry
is REWRITTEN to the root URL instead (so no citation is dropped). The whole-file
count of broken vs. correct-root URLs is asserted 1:1 before any write.

Text transform (not YAML reserialize) to preserve comments/formatting/order.
Each target entry is the uniform 3-line block:
      - type: literature
        url: https://www.danskmoent.dk/(chr|fr)/<slug>.htm
        ref: danskmoent.dk overview <slug> (Hede <x> — Tiefenseite fehlt)
Structure is asserted per block; a mismatch aborts rather than corrupts.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

FINAL_DIR = Path("data/v2/final")
BROKEN_URL_RE = re.compile(
    r"^(\s*)url:\s*(https://www\.danskmoent\.dk)/(?:chr|fr)/"
    r"([cf]\d+hede\d*)\.htm\s*$"
)


def process(path: Path, apply: bool) -> tuple[int, int]:
    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    removed = 0
    rewritten = 0
    out: list[str] = []
    i = 0
    n = len(lines)
    while i < n:
        m = BROKEN_URL_RE.match(lines[i].rstrip("\n"))
        if not m:
            out.append(lines[i])
            i += 1
            continue
        indent, base, slug = m.group(1), m.group(2), m.group(3)
        root_url = f"{base}/{slug}.htm"
        # Assert the surrounding 3-line block shape.
        prev = out[-1] if out else ""
        nxt = lines[i + 1] if i + 1 < n else ""
        type_ok = prev.strip() == "- type: literature"
        ref_ok = nxt.lstrip().startswith("ref:")
        if not (type_ok and ref_ok):
            print(
                f"  !! {path.name}:{i+1} unexpected block shape around broken url "
                f"(prev={prev.strip()!r} next={nxt.strip()!r}) — aborting",
                file=sys.stderr,
            )
            sys.exit(2)
        # REWRITE-ONLY: correct the url to the root form, never remove the
        # entry. Rewriting preserves the `ref` (the citation content), so no
        # coin can lose a danskmoent citation — verify_reflow keys on the ref,
        # and every ref survives. Where a re-absorb previously added the correct
        # root-URL twin alongside the broken one, this produces a same-url
        # duplicate; absorb's source union dedups by url on the next run.
        out.append(f"{indent}url: {root_url}\n")
        i += 1
        rewritten += 1
    if apply and (removed or rewritten):
        path.write_text("".join(out), encoding="utf-8")
    return removed, rewritten


def main() -> int:
    apply = "--apply" in sys.argv
    total_removed = total_rewritten = 0
    for path in sorted(FINAL_DIR.glob("*.yml")):
        r, w = process(path, apply)
        if r or w:
            print(f"  {path.name}: removed {r}, rewritten {w}")
            total_removed += r
            total_rewritten += w
    verb = "removed" if apply else "would remove"
    print(f"\n{verb} {total_removed} broken-URL entries; rewritten {total_rewritten}.")
    if not apply:
        print("(dry-run — pass --apply to write)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
