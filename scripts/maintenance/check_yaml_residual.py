#!/usr/bin/env python3
"""Refuse a commit that raises a data YAML's round-trip residual.

WHAT A RESIDUAL IS
------------------
Load a data YAML with its own family's serializer and dump it straight back.
The number of lines that move is the file's residual. Zero means a structural
edit — `yaml_io.load()` / `save()` — shows ONLY what the author changed.
Anything above zero is debt: the next session that makes a structural edit to
that file pays it as spurious diff, and has to decide, under time pressure,
whether thousands of moved lines are a reformat or a data loss.

WHY A GUARD AND NOT A CLEANUP
-----------------------------
The debt is real and large — 83 of 233 data YAMLs, ~28 200 lines, accumulated
over many sessions. Paying it off is one big semantically-null commit and a
separate decision. Stopping its GROWTH is neither: a commit may leave the
backlog exactly as it found it, but it may not add to it. That single rule is
enough, because every increment has the same cause — a line written by hand
that the family's serializer would have written differently.

The mechanism is not hypothetical. `scripts/maintenance/test_yaml_io_roundtrip.py`
has pinned per-family baselines since 2026-07, but it is conditioned on the
wrong trigger: its own docs say «run it after touching yaml_io.py», while the
drift comes from touching DATA. So data/shared/fuesse.yml went 0 → 614 in a
single session (2026-09-20) with nothing to say so, and every hand-written
line in it was legal YAML.

HOW TO FIX A FAILURE
--------------------
Render the lines you are inserting through `yaml_io.canonical_lines(path,
field, value, indent)` instead of formatting them yourself — it emits what the
serializer would emit, at the real column, so folding lands in the same place.
Or make the edit with `yaml_io.edit_coin_field()`, which already does.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))
from lib.yaml_io import round_trip_residual  # noqa: E402

# Only the families whose files are hand-edited AND tracked.
TRACKED = ("data/v2/", "data/shared/", "data/i18n/", "data/locations/")
# `match_uncertainty/` is gitignored, machine-only and written by PyYAML, so it
# can never appear in a diff and measuring it is meaningless — `family_of()`
# hands it the ruamel profile, which reformats all 9.9 M lines of it.
SKIP = ("data/v2/match_uncertainty/",)


def _git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=REPO, capture_output=True,
                          text=True).stdout


def _blob(rev: str, path: str) -> str | None:
    r = subprocess.run(["git", "show", f"{rev}:{path}"], cwd=REPO,
                       capture_output=True, text=True)
    return r.stdout if r.returncode == 0 else None


def staged_paths() -> list[str]:
    out = _git("diff", "--cached", "--name-only", "--diff-filter=ACM")
    return [p for p in out.split("\n")
            if p.endswith((".yml", ".yaml")) and p.startswith(TRACKED)
            and not p.startswith(SKIP)]


def check_staged() -> int:
    paths = staged_paths()
    if not paths:
        return 0
    grew: list[tuple[str, int, int]] = []
    fresh: list[tuple[str, int]] = []
    for p in paths:
        now_raw = _blob(":0", p)
        if now_raw is None:
            continue
        now = round_trip_residual(REPO / p, raw=now_raw)
        head_raw = _blob("HEAD", p)
        if head_raw is None:
            if now:
                fresh.append((p, now))
            continue
        was = round_trip_residual(REPO / p, raw=head_raw)
        if now > was:
            grew.append((p, was, now))
    for p, n in fresh:
        print(f"  new file with residual {n}: {p}")
    if not grew:
        return 0
    print("✗ round-trip residual grew — a hand-written line is not what the "
          "serializer would emit:")
    for p, was, now in grew:
        print(f"    {p}: {was} → {now}  (+{now - was})")
    print()
    print("Render inserted lines with yaml_io.canonical_lines(), or make the "
          "edit with yaml_io.edit_coin_field().")
    return 1


def scan() -> int:
    rows = []
    for prefix in TRACKED:
        for p in sorted((REPO / prefix).rglob("*.yml")):
            rel = p.relative_to(REPO).as_posix()
            if rel.startswith(SKIP):
                continue
            try:
                rows.append((round_trip_residual(p), rel))
            except Exception as exc:                      # noqa: BLE001
                rows.append((-1, f"{rel}  ({exc.__class__.__name__})"))
    rows.sort(reverse=True)
    dirty = [r for r in rows if r[0] > 0]
    print(f"{len(rows)} files · {len(dirty)} with residual · "
          f"{sum(r[0] for r in dirty)} lines of debt")
    for n, rel in dirty[:40]:
        print(f"  {n:6}  {rel}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--staged", action="store_true",
                   help="compare each staged data YAML against HEAD")
    g.add_argument("--scan", action="store_true",
                   help="print the whole corpus's residual table")
    args = ap.parse_args()
    return check_staged() if args.staged else scan()


if __name__ == "__main__":
    sys.exit(main())
