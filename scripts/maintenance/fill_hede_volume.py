"""Auto-fill ``catalog.hede_volume`` from each coin's ``ruler`` field.

Hede 1971 (`Danmarks og Norges mønter 1541-1814`, plus the 19th-c.
extension) publishes a separate catalogue volume per Danish king;
danskmoent.dk hosts entries under URLs keyed by ruler-prefix + Hede
number (e.g. `chr/c5h120.htm`, `fr/f3h62.htm`). The bare Hede number
(«120», «28A», «107a») is therefore ambiguous across rulers — every
volume restarts numbering at 1.

To let the IKMK matcher (and any future cross-source tooling)
disambiguate, every coin that carries a `catalog.hede` field also
needs `catalog.hede_volume` set to the ruler-volume code per
danskmoent.dk URL convention (c1h..c10h, f1h..f9h).

This script walks every location YAML, derives the volume from the
coin's `ruler` field, and writes the new field. Idempotent: skips
coins whose `hede_volume` is already set.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

from ruamel.yaml import YAML

PROJECT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT / "data" / "locations"

# Longest-prefix-first ordering avoids «Christian I» eating
# «Christian IV». Each entry maps a ruler-substring to the Hede
# volume code per danskmoent.dk URL convention.
RULER_TO_VOLUME: list[tuple[str, str]] = [
    ("Christian X", "c10h"),
    ("Christian IX", "c9h"),
    ("Christian VIII", "c8h"),
    ("Christian VII", "c7h"),
    ("Christian VI", "c6h"),
    ("Christian V", "c5h"),
    ("Christian IV", "c4h"),
    ("Christian III", "c3h"),
    ("Christian II", "c2h"),
    ("Christian I", "c1h"),
    # Frederik / Friedrich (German + Ukrainian forms)
    ("Frederik IX", "f9h"),
    ("Frederik VIII", "f8h"),
    ("Frederik VII", "f7h"),
    ("Frederik VI", "f6h"),
    ("Frederik V", "f5h"),
    ("Frederik IV", "f4h"),
    ("Frederik III", "f3h"),
    ("Frederik II", "f2h"),
    ("Frederik I", "f1h"),
    ("Friedrich IX", "f9h"),
    ("Friedrich VIII", "f8h"),
    ("Friedrich VII", "f7h"),
    ("Friedrich VI", "f6h"),
    ("Friedrich V", "f5h"),
    ("Friedrich IV", "f4h"),
    ("Friedrich III", "f3h"),
    ("Friedrich II", "f2h"),
    ("Friedrich I", "f1h"),
    ("Фредерік IX", "f9h"),
    ("Фредерік VIII", "f8h"),
    ("Фредерік VII", "f7h"),
    ("Фредерік VI", "f6h"),
    ("Фредерік V", "f5h"),
    ("Фредерік IV", "f4h"),
    ("Фредерік III", "f3h"),
    ("Фредерік II", "f2h"),
    ("Фредерік I", "f1h"),
    ("Кристіан X", "c10h"),
    ("Кристіан IX", "c9h"),
    ("Кристіан VIII", "c8h"),
    ("Кристіан VII", "c7h"),
    ("Кристіан VI", "c6h"),
    ("Кристіан V", "c5h"),
    ("Кристіан IV", "c4h"),
    ("Кристіан III", "c3h"),
    ("Кристіан II", "c2h"),
    ("Кристіан I", "c1h"),
]


def _ruler_to_volume(ruler_text: str) -> str | None:
    if not ruler_text:
        return None
    for needle, code in RULER_TO_VOLUME:
        if needle in ruler_text:
            return code
    return None


def main() -> int:
    yaml = YAML(typ="rt")
    yaml.preserve_quotes = True
    yaml.width = 4096
    yaml.indent(mapping=2, sequence=4, offset=2)

    grand_filled = 0
    grand_skipped_no_ruler = 0
    grand_skipped_no_match = []

    for path in sorted(DATA_DIR.glob("*.yml")):
        if path.name.endswith("-references.yml"):
            continue
        with path.open() as f:
            doc = yaml.load(f)
        coins = doc.get("coins") or []
        loc_filled = 0
        loc_changed = False
        for coin in coins:
            cat = coin.get("catalog")
            if not cat:
                continue
            hede = cat.get("hede")
            if not hede:
                continue
            if cat.get("hede_volume"):
                continue
            ruler = (coin.get("ruler") or "").strip()
            if not ruler:
                grand_skipped_no_ruler += 1
                continue
            volume = _ruler_to_volume(ruler)
            if not volume:
                grand_skipped_no_match.append((path.stem, coin.get("id"), ruler))
                continue
            cat["hede_volume"] = volume
            loc_filled += 1
            loc_changed = True
        if loc_changed:
            with path.open("w") as f:
                yaml.dump(doc, f)
            print(f"  {path.stem}: filled hede_volume for {loc_filled} coins")
            grand_filled += loc_filled

    print()
    print(f"Total filled: {grand_filled}")
    print(f"Skipped (no ruler): {grand_skipped_no_ruler}")
    print(f"Skipped (no ruler match): {len(grand_skipped_no_match)}")
    for loc, cid, ruler in grand_skipped_no_match[:10]:
        print(f"  {loc}/{cid}: ruler='{ruler[:60]}'")
    return 0


if __name__ == "__main__":
    sys.exit(main())
