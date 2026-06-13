#!/usr/bin/env python3
"""Apply lib.catalog_codes.normalise_catalog to every catalog in the V2 final
layer, bringing already-saved data in line with the (idempotent) normaliser the
cross-source merger and absorb step both run.

Triggered when normalise_catalog gains a new hygiene rule. Current pass covers:
  - Aagaard die-study refs consolidated into one `others` token per number.
  - Numeric index fields (schou, sieg, hede, lange, galster, …) flattened from
    comma/slash-joined multi-source strings, deduped, plain-int-in-plain-range
    subsumed («9, 10, 8-13» → «8-13»), and numerically sorted.
  - A `*_hede1971` old-edition number that leaked into its modern base list
    («sieg: [147, 141]» + «sieg_hede1971: 147») stripped from the list.

The seed / seed_unified layers self-heal on the next merge / absorb run. Final
is re-dumped with absorb's serializer (yaml.dump, sort_keys=False,
default_flow_style=False, width=120), so the diff is the normalisation only.

Usage:
    python scripts/maintenance/migrate_normalise_catalog.py            # dry-run
    python scripts/maintenance/migrate_normalise_catalog.py --apply
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "lib"))

from lib.catalog_codes import normalise_catalog  # noqa: E402

V2_FINAL = ROOT / "data" / "v2" / "final"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--apply", action="store_true", help="write changes (default: dry-run)")
    args = ap.parse_args()

    total = 0
    for path in sorted(V2_FINAL.glob("*.yml")):
        doc = yaml.safe_load(path.read_text())
        changed = 0
        for coin in doc.get("coins", []):
            cat = coin.get("catalog")
            if isinstance(cat, dict) and normalise_catalog(cat):
                changed += 1
        if not changed:
            continue
        total += changed
        print(f"{path.name:28} {changed:4d} entr{'y' if changed == 1 else 'ies'}")
        if args.apply:
            out = yaml.dump(doc, sort_keys=False, allow_unicode=True,
                            default_flow_style=False, width=120)
            path.write_text(out)

    print(f"\n{'APPLIED' if args.apply else 'DRY-RUN'}: {total} entries"
          f"{' written' if args.apply else ' would change'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
