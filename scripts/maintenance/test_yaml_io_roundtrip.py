#!/usr/bin/env python3
"""Tripwire for lib/yaml_io.py — proves the family-aware serializer config still
round-trips each data-file family near-zero, and that edit_coin_field is
byte-surgical.

WHY: the project's data YAMLs are written by two serializers with family-
specific settings (PyYAML width=120 for v2/final+seed_unified; ruamel with
distinct width/offset for v2/seed vs locations vs shared). Round-tripping a
file through the WRONG config reformats the ENTIRE file (a multi-thousand-line
spurious diff from a one-field edit — observed repeatedly). This test pins the
known per-family round-trip baseline so any config regression is caught loudly
(thousands of changed lines) instead of silently shipping a reformat.

Run:  .venv/bin/python scripts/maintenance/test_yaml_io_roundtrip.py
Exit 0 = all families within baseline + edit_coin_field surgical; 1 = regression.
"""
from __future__ import annotations

import difflib
import io
import os
import shutil
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts"))
from lib import yaml_io  # noqa: E402


def _changed(a: str, b: str) -> int:
    return sum(
        1 for l in difflib.unified_diff(a.split("\n"), b.split("\n"), lineterm="")
        if l[:1] in "+-" and l[:3] not in ("+++", "---")
    )


# (relative path, expected family, residual ceiling). Ceilings sit a little
# above the empirically-observed baseline so harmless future data edits don't
# trip them, but a wrong-serializer regression (hundreds+) does.
ROUNDTRIP_CASES = [
    ("data/v2/final/rantzau_county.yml",        "pyyaml120",     5),
    ("data/v2/seed_unified/danish_realm.yml",   "pyyaml120",     5),
    ("data/v2/seed/bruun/danish_realm.yml",     "ruamel_seed",   40),
    ("data/locations/denmark.yml",              "ruamel_loc",    20),
    ("data/locations/schleswig_holstein.yml",   "ruamel_loc",    20),
    ("data/shared/fuesse.yml",                  "ruamel_shared", 80),
]


def test_family_detection() -> list[str]:
    fails = []
    for rel, expect_fam, _ in ROUNDTRIP_CASES:
        got = yaml_io.family_of(rel)
        if got != expect_fam:
            fails.append(f"family_of({rel}) = {got!r}, expected {expect_fam!r}")
    return fails


def test_roundtrip() -> list[str]:
    fails = []
    for rel, expect_fam, ceiling in ROUNDTRIP_CASES:
        p = REPO / rel
        if not p.exists():
            print(f"  SKIP (missing): {rel}")
            continue
        orig = p.read_text()
        ctx, doc = yaml_io.load(p)
        tf = tempfile.mktemp(suffix=".yml")
        yaml_io.save(ctx, tf, doc)
        new = Path(tf).read_text()
        os.unlink(tf)
        n = _changed(orig, new)
        status = "OK  " if n <= ceiling else "FAIL"
        print(f"  {status} {expect_fam:<14} {rel:<40} residual={n} (ceil {ceiling})")
        if n > ceiling:
            fails.append(f"round-trip {rel}: residual {n} > ceiling {ceiling} "
                         f"(serializer/config regression?)")
    return fails


def test_edit_coin_field() -> list[str]:
    """edit_coin_field must change ONLY the target field's line(s); the rest of
    the file stays byte-identical, and a set→restore cycle returns the original."""
    fails = []
    src = REPO / "data/v2/seed/bruun/danish_realm.yml"
    tmp = Path(tempfile.mktemp(suffix=".yml"))
    shutil.copy(src, tmp)
    try:
        original = tmp.read_text()
        # 1) scalar set
        changed = yaml_io.edit_coin_field(tmp, "dk-bruun-5536", "hede", "ZZTEST",
                                          expect_contains="5")
        after = tmp.read_text()
        d = _changed(original, after)
        if not changed or d != 2:
            fails.append(f"edit_coin_field scalar set: changed={changed}, diff lines={d} (want 2)")
        # 2) restore -> byte-identical to original
        yaml_io.edit_coin_field(tmp, "dk-bruun-5536", "hede", "5")
        if tmp.read_text() != original:
            fails.append("edit_coin_field set→restore is not byte-identical")
        # 3) must_exist=False on a missing field is a no-op
        noop = yaml_io.edit_coin_field(tmp, "dk-bruun-5536", "no_such_field", "x",
                                       must_exist=False)
        if noop is not False:
            fails.append("edit_coin_field missing field with must_exist=False should return False")
        # 4) wrong-coin id raises
        try:
            yaml_io.edit_coin_field(tmp, "dk-bruun-NONEXISTENT", "hede", "x")
            fails.append("edit_coin_field on unknown coin id should raise")
        except KeyError:
            pass
        print(f"  {'OK  ' if not fails else 'FAIL'} edit_coin_field surgical (scalar set/restore/no-op/raise)")
    finally:
        if tmp.exists():
            os.unlink(tmp)
    return fails


def main() -> int:
    print("== family detection ==")
    fails = test_family_detection()
    for f in fails:
        print(f"  FAIL {f}")
    print("== round-trip residuals (family-aware) ==")
    fails += test_roundtrip()
    print("== edit_coin_field surgical ==")
    fails += test_edit_coin_field()
    print()
    if fails:
        print(f"FAILED ({len(fails)}):")
        for f in fails:
            print(f"  - {f}")
        return 1
    print("PASS — all families round-trip within baseline; edit_coin_field surgical.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
