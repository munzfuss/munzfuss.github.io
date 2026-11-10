#!/usr/bin/env python3
"""Record the readings a SOURCE-SANITY gate refused, so the re-flow gate can tell
them apart from data falling on the floor.

WHY THIS EXISTS
---------------
A source sometimes prints a number that cannot be what it claims. NGC's own
specification table gives «Fineness: 35.5000» on the Norwegian gold off-strikes
struck from Speciedaler dies, 58.0 on two different nominals and 40.7 on four —
a 12-Ducat, a 3-Ducat and two 2-Ducats alike. Shared across nominals of
different size, so not a per-piece weight either; what the field holds there
cannot be established from the page, and `parse_ngc.sift_fineness` therefore
REFUSES it rather than reinterpreting it (guessing would be §0b invention).

That refusal makes a measurement list shrink in the finals, and a shrinking list
is exactly what `verify_reflow` is built to block. Without a record the only way
through is `--no-verify`, and a gate routinely bypassed protects nothing — the
same reasoning that produced `data/v2/exclusions/` for coins and
`_retracted_refs.yml` for catalogue registers. This is the third member of that
family, for measurement readings.

It is a SEPARATE file from `_retracted_refs.yml` for a mechanical reason:
`heal_hede_retracted_refs.py` rewrites that one wholesale, so a second author
sharing it would be silently wiped on the next heal run.

WHAT AN ENTRY EXCUSES
---------------------
Exactly one value, of exactly one field, on the coins carrying exactly one seed.
Nothing else: another value in the same shrink, another field on the same coin,
a citation dropped, a coin gone — all still block. An entry can never become a
blanket amnesty.

The ledger is DERIVED, never hand-written: every entry is reconstructed from the
parser cache, where the refused number is preserved as `fineness_unusable_raw`
beside a `flags.fineness_unusable` marker. Re-run this after any parser-gate
change and the ledger follows.

Usage::

    python scripts/maintenance/record_source_sanity_retractions.py            # dry-run
    python scripts/maintenance/record_source_sanity_retractions.py --apply
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from lib.paths import HARVEST_ROOT  # noqa: E402

from lib import yaml_io  # noqa: E402

LEDGER = ROOT / "data" / "v2" / "_source_sanity_retractions.yml"
NGC_CACHE = HARVEST_ROOT / "ngc"

_HEADER = """# Readings a SOURCE-SANITY gate refused at parse, and the finals therefore lost.
#
# Written by scripts/maintenance/record_source_sanity_retractions.py; read by
# scripts/maintenance/verify_reflow.py.
#
# WHY IT EXISTS. A source can print a number that cannot be what it claims — NGC
# gives «Fineness: 35.5000» on the Norwegian gold off-strikes struck from
# Speciedaler dies. parse_ngc.sift_fineness refuses such a value instead of
# guessing what it meant (§0b), which makes a measurement list shrink in the
# finals, which is precisely what verify_reflow blocks. This file is the record
# that tells a deliberate refusal apart from real loss — the same shape as
# data/v2/exclusions/ for coins and _retracted_refs.yml for catalogue registers.
#
# Separate from _retracted_refs.yml on purpose: heal_hede_retracted_refs.py
# rewrites that file wholesale and would wipe these entries.
#
# An entry excuses ONE value of ONE field on the coins carrying ONE seed. It
# excuses nothing else — another value in the same shrink, another field, a
# citation, a coin — all still block.
#
# DERIVED, never hand-written: rebuilt from the parser cache, where the refused
# number is preserved as `fineness_unusable_raw`. Re-run the script after any
# parser-gate change.
"""


def collect_ngc_fineness() -> list[dict]:
    """One entry per NGC record whose fineness the parse gate refused."""
    out = []
    for path in sorted(NGC_CACHE.glob("*/cuid_*.parsed.json")):
        try:
            rec = json.loads(path.read_text())
        except (OSError, json.JSONDecodeError):
            continue
        raw = rec.get("fineness_unusable_raw")
        if raw is None:
            continue
        if not (rec.get("flags") or {}).get("fineness_unusable"):
            # the flag and the raw value are written together; a record carrying
            # one without the other is a cache inconsistency, not a retraction
            continue
        out.append({
            "seed": f"ngc-{rec['cuid']}",
            "field": "fineness",
            "dropped": [{"source": "ngc", "value": raw}],
            "reason": (f"NGC prints «Fineness: {raw}» for {rec.get('heading') or 'this type'}, "
                       "which cannot be a fineness; refused by parse_ngc.sift_fineness and "
                       "preserved in the cache as fineness_unusable_raw."),
        })
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--apply", action="store_true", help="write the ledger")
    args = ap.parse_args()

    entries = collect_ngc_fineness()
    entries.sort(key=lambda e: e["seed"])

    print(f"===== record_source_sanity_retractions "
          f"({'APPLY' if args.apply else 'dry-run'}) =====")
    print(f"  refused readings found in the NGC cache: {len(entries)}")
    for e in entries:
        print(f"    {e['seed']:16s} {e['field']:9s} {e['dropped']}")

    if not args.apply:
        print("\n--- DRY RUN — ledger not written. Re-run with --apply. ---")
        return 0

    payload = {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "retractions": entries,
    }
    LEDGER.write_text(_HEADER + yaml_io.dump_v2_canonical(payload))
    print(f"\n✓ wrote {LEDGER.relative_to(ROOT)} ({len(entries)} entries)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
