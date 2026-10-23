#!/usr/bin/env python3
"""One-shot: give every seed back the ruler spelling its source printed.

Stage N (9b603b5, 2026-10-23) wrote the canonical display form of Danish
kings («Christian IV.») into the seeds. The curator moved that normalisation
to the merger (2026-10-23): a seed keeps what the source printed, the merger
writes the display form into seed_unified, knowing the coin's entity exactly
(the writer normalised before entity routing, so four Bruun Christian II lots
got «Christian II.» while their entity stayed bare).

For each seed entry, the ruler is restored from the revision before stage N
ONLY when the current value is exactly the canonical form of that old value
(i.e. stage N's own edit, untouched since). The `ruler_verified: false` that
stage N added for a trailing «?» is removed when the entry had no such key
before. Everything else is left alone and reported.

    .venv/bin/python scripts/maintenance/restore_seed_ruler_source_form.py            # report
    .venv/bin/python scripts/maintenance/restore_seed_ruler_source_form.py --apply

Line-based edits (CLAUDE.md «Programmatic edits»): the ruler line is
re-rendered with `yaml_io.canonical_lines`, a removed flag line is deleted;
the rest of each file stays byte-for-byte.
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import yaml  # noqa: E402

from lib import yaml_io  # noqa: E402
from lib.ruler_reigns import canonical_ruler_display  # noqa: E402

_L = getattr(yaml, "CSafeLoader", yaml.SafeLoader)
SEED = ROOT / "data" / "v2" / "seed"
BEFORE = "9b603b5^"


def _old_entries(rel: str) -> dict[str, dict]:
    r = subprocess.run(["git", "show", f"{BEFORE}:{rel}"], cwd=ROOT,
                       capture_output=True, text=True)
    if r.returncode != 0:
        return {}
    return {c["id"]: c for c in (yaml.load(r.stdout, Loader=_L) or {}).get("coins") or []
            if isinstance(c, dict) and c.get("id")}


def _is_stage_n_edit(old: str, cur: str) -> bool:
    new, _ = canonical_ruler_display(old, "danish_realm")
    return new != old and new == cur


def _apply_file(path: Path, pending: list[tuple[str, str | None, bool]]) -> None:
    lines = path.read_text(encoding="utf-8").split("\n")
    positions = []
    for cid, ruler, drop_flag in pending:
        b = yaml_io._coin_block_bounds(lines, cid)
        if b is None:
            raise KeyError(f"{cid} not in {path}")
        positions.append((b[0], b[1], cid, ruler, drop_flag))
    for start, end, cid, ruler, drop_flag in sorted(positions, reverse=True):
        ruler_i = flag_i = None
        for i in range(start, end):
            s = lines[i]
            if ruler_i is None and re.match(r"^\s*(?:-\s+)?ruler:(\s|$)", s):
                ruler_i = i
            elif flag_i is None and re.match(r"^\s*(?:-\s+)?ruler_verified:(\s|$)", s):
                flag_i = i
        if ruler_i is None:
            raise KeyError(f"{cid}: no ruler line in {path}")
        if drop_flag and flag_i is not None:
            if lines[flag_i].lstrip().startswith("- "):
                raise ValueError(f"{cid}: ruler_verified opens the entry, not removed")
            del lines[flag_i]
            if flag_i < ruler_i:
                ruler_i -= 1
        if ruler is not None:
            key_col = len(lines[ruler_i]) - len(lines[ruler_i].lstrip())
            dash = lines[ruler_i].lstrip().startswith("- ")
            if dash:
                key_col += 2
            rl = yaml_io.canonical_lines(path, "ruler", ruler, indent=key_col)
            if dash:
                rl[0] = lines[ruler_i][:key_col - 2] + "- " + rl[0].lstrip()
            lines[ruler_i:ruler_i + 1] = rl
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    table: Counter = Counter()
    skipped: Counter = Counter()
    flags = 0
    for p in sorted(SEED.glob("*/*.yml")):
        rel = str(p.relative_to(ROOT))
        old = _old_entries(rel)
        if not old:
            continue
        pending = []
        for c in (yaml.load(p.read_text(), Loader=_L) or {}).get("coins") or []:
            if not isinstance(c, dict) or c.get("id") not in old:
                continue
            o = old[c["id"]]
            o_r, c_r = o.get("ruler"), c.get("ruler")
            if not isinstance(o_r, str) or o_r == c_r:
                continue
            if not _is_stage_n_edit(o_r, c_r):
                skipped[(o_r, c_r)] += 1
                continue
            drop = ("ruler_verified" not in o and c.get("ruler_verified") is False
                    and canonical_ruler_display(o_r, "danish_realm")[1])
            table[(c_r, o_r)] += 1
            flags += bool(drop)
            pending.append((c["id"], o_r, bool(drop)))
        if a.apply and pending:
            _apply_file(p, pending)
    print(f"{'seeds':>6}  current -> source form")
    for (cur, src), n in sorted(table.items(), key=lambda t: -t[1])[:40]:
        print(f"{n:6}  {cur!r} -> {src!r}")
    print(f"\nrestored: {sum(table.values())} rulers, {flags} ruler_verified flags removed, "
          f"{len(table)} distinct pairs")
    if skipped:
        print("\nNOT restored (current value is not stage N's canonical form of the old one):")
        for (o, c), n in skipped.most_common():
            print(f"{n:6}  old {o!r}  now {c!r}")
    print("applied" if a.apply else "report only (--apply to write)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
