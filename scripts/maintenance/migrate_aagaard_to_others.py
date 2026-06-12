#!/usr/bin/env python3
"""One-off migration: consolidate Aagaard die-study refs into a single
`catalog.others` token per number, removing the duplicate/truncated typed
`aagaard` field.

Root cause (fixed in lib/catalog_codes._canonicalise_aagaard, which now runs
inside normalise_catalog → merger + absorb, so future pipeline output is clean):
Aagaard cites a die-combination in parens with an internal slash —
«14.1 (53-1/53.1)». Producers emitted the ref both as a typed `aagaard` field
AND as an `others` token, and the typed-field slash-split (normalise_catalog
step 1b + the renderer) severed the die-pair into «14.1 (53-1». Result on the
page: the same Aagaard index rendered twice, one copy truncated.

This applies the canonicaliser to every catalog in the V2 final layer so the
already-saved data matches what the (now-fixed) pipeline would produce. The
seed / seed_unified layers self-heal on the next merge / absorb run (both call
normalise_catalog). Final is re-dumped with the same serializer absorb uses
(yaml.dump, sort_keys=False, default_flow_style=False, width=120), so the diff
is the Aagaard consolidation only.

Usage:
    python scripts/maintenance/migrate_aagaard_to_others.py            # dry-run
    python scripts/maintenance/migrate_aagaard_to_others.py --apply
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "lib"))

from lib.catalog_codes import _canonicalise_aagaard  # noqa: E402

V2_FINAL = ROOT / "data" / "v2" / "final"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--apply", action="store_true", help="write changes (default: dry-run)")
    args = ap.parse_args()

    total_entries = 0
    for path in sorted(V2_FINAL.glob("*.yml")):
        doc = yaml.safe_load(path.read_text())
        changed = 0
        for coin in doc.get("coins", []):
            cat = coin.get("catalog")
            if isinstance(cat, dict):
                changed += _canonicalise_aagaard(cat)
        if not changed:
            continue
        total_entries += changed
        print(f"{path.name:28} {changed:4d} entr{'y' if changed == 1 else 'ies'}")
        if args.apply:
            out = yaml.dump(doc, sort_keys=False, allow_unicode=True,
                            default_flow_style=False, width=120)
            path.write_text(out)

    print(f"\n{'APPLIED' if args.apply else 'DRY-RUN'}: {total_entries} entries"
          f"{' written' if args.apply else ' would change'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
