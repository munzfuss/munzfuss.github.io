#!/usr/bin/env python3
"""One-shot: write every Danish king's name in the seeds in its canonical
display form — what `v2_seed_writer._canonicalise_ruler` does on a re-seed,
applied to the seeds on disk without re-running ten builders.

    .venv/bin/python scripts/maintenance/canonicalise_seed_rulers.py            # report
    .venv/bin/python scripts/maintenance/canonicalise_seed_rulers.py --apply

Edits go through `lib.yaml_io.edit_coin_field` (line-based, the rest of the
file byte-for-byte untouched; CLAUDE.md «Programmatic edits»). Prints the
(raw → canonical) table with counts — the §9b «old vs new over the distinct
values of every seed» measurement — and refuses nothing: holds are honoured
inside the writer's helper. Plan: docs/plans/rebuild_final_from_members.md,
stage N.
"""
from __future__ import annotations

import argparse
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import yaml  # noqa: E402

from lib import yaml_io  # noqa: E402
from lib.v2_seed_writer import _canonicalise_ruler  # noqa: E402

_L = getattr(yaml, "CSafeLoader", yaml.SafeLoader)
SEED = ROOT / "data" / "v2" / "seed"


def _apply_file(path: Path, pending: list[tuple]) -> None:
    """All of one file's edits in a single read / write. Each edit is what
    `yaml_io.edit_coin_field` does — the coin's block by `_coin_block_bounds`,
    the field's line replaced by the line the family's serializer would emit
    (`canonical_lines`), so the round-trip residual does not rise (Check 9) —
    only without re-reading a 10 MB file ten thousand times. A missing
    `ruler_verified` is inserted right below the `ruler:` line."""
    lines = path.read_text(encoding="utf-8").split("\n")
    # Edit from the bottom up so earlier block offsets stay valid.
    positions = []
    for cid, new_ruler, new_flag, flag_exists in pending:
        b = yaml_io._coin_block_bounds(lines, cid)
        if b is None:
            raise KeyError(f"{cid} not in {path}")
        positions.append((b[0], b[1], cid, new_ruler, new_flag, flag_exists))
    for start, end, cid, new_ruler, new_flag, flag_exists in sorted(positions, reverse=True):
        ruler_i = flag_i = None
        for i in range(start, end):
            s = lines[i]
            if ruler_i is None and re.match(r"^\s*(?:-\s+)?ruler:(\s|$)", s):
                ruler_i = i
            elif flag_i is None and re.match(r"^\s*(?:-\s+)?ruler_verified:(\s|$)", s):
                flag_i = i
        if ruler_i is None:
            raise KeyError(f"{cid}: no ruler line in {path}")
        key_col = len(lines[ruler_i]) - len(lines[ruler_i].lstrip())
        if lines[ruler_i].lstrip().startswith("- "):
            key_col += 2
        if new_flag is not None:
            fl = yaml_io.canonical_lines(path, "ruler_verified", new_flag, indent=key_col)
            if flag_i is not None:
                lines[flag_i:flag_i + 1] = fl
            else:
                lines[ruler_i + 1:ruler_i + 1] = fl
        if new_ruler is not None:
            rl = yaml_io.canonical_lines(path, "ruler", new_ruler, indent=key_col)
            if lines[ruler_i].lstrip().startswith("- "):
                rl[0] = lines[ruler_i][:key_col - 2] + "- " + rl[0].lstrip()
            lines[ruler_i:ruler_i + 1] = rl
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    table: Counter = Counter()
    per_file: Counter = Counter()
    edits = 0
    pending: list[tuple] = []
    for p in sorted(SEED.glob("*/*.yml")):
        coins = (yaml.load(p.read_text(), Loader=_L) or {}).get("coins") or []
        for c in coins:
            if not isinstance(c, dict) or not c.get("id"):
                continue
            before = (c.get("ruler"), c.get("ruler_verified"))
            if not _canonicalise_ruler(c):
                continue
            after = (c.get("ruler"), c.get("ruler_verified"))
            table[(before[0], after[0], after[1] if after[1] != before[1] else None)] += 1
            per_file[f"{p.parent.name}/{p.stem}"] += 1
            if a.apply:
                pending.append((c["id"], after[0] if after[0] != before[0] else None,
                                after[1] if after[1] != before[1] else None,
                                before[1] is not None))
                edits += 1
        if a.apply and pending:
            _apply_file(p, pending)
            pending = []
    print(f"{'seeds':>6}  raw -> canonical")
    for (raw, new, flag), n in sorted(table.items(), key=lambda t: -t[1]):
        print(f"{n:6}  {raw!r} -> {new!r}{'  ruler_verified: ' + str(flag) if flag is not None else ''}")
    print(f"\ntotal seeds changed: {sum(table.values())}  distinct forms: {len(table)}")
    for f, n in per_file.most_common():
        print(f"  {n:6}  {f}")
    if a.apply:
        print(f"\napplied: {edits} entries edited")
    return 0


if __name__ == "__main__":
    sys.exit(main())
