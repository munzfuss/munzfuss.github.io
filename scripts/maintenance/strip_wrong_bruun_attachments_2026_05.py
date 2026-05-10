"""Strip Bruun-lot attachments that violate §9.1 (Pn-tier off-metal
strikes) or §9.3 (cross-volume KM collisions, cross-denomination, or
cross-region misattributions).

Background. The Bruun cross-matcher's parity gate (TODO J fix, commit
d04bc99) compares parent-KM but does not check weight magnitude or
detect off-metal strike lots. Eight coin entries accumulated wrong
Bruun-lot citations through this gap, surfaced by the 2026-05-10 audit
combining within-row median checks (mine) and Bruun-mass-vs-row-
expected (parallel chat). The systemic fix landed in this same commit
(scripts/bruun_parser/04_cross_match.py: _is_pn_lot + _weight_compatible
gates); this script cleans up the data side.

Per coin, strip:
  * `catalog.bruun_collection_id`, `bruun_part`, `bruun_lot_no`,
    `bruun_page` — the primary citation pointing at the wrong lot.
  * `weight_rough_g[]` entry whose `source` mentions the lot's
    «Bruun Part X, lot N, p. P» citation.
  * `sources[]` entry whose `ref` mentions the same lot citation.

Each strip is logged so re-running on already-cleaned data is a no-op.
The Bruun lots themselves remain in `scripts/cache/bruun/lots/*.json`;
the systemic gate (`lot_compatible_with_coin`) now keeps them out of
`cross_match.json` automatically.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

from ruamel.yaml import YAML

PROJECT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT / "data" / "locations"


# (location, coin_id, lot_no_to_strip, reason)
STRIPS = [
    ("schleswig_holstein", "km-79-chr-iv-1623", 1031,
     "lot is DK KM-79 4-Speciedaler 1624 (cross-volume KM collision; SH KM-79 = 1 Sechsling)"),
    ("denmark", "dk-tid-162991", 14265,
     "lot is Schauenburg-Pinneberg KM-40 2-Taler 1606 Ernst III (cross-region + cross-ruler + cross-denomination)"),
    ("schleswig_holstein", "km-75-fr-iii-1625", 17054,
     "lot is DK KM-75 3-Speciedaler 1624 ChrIV (cross-volume KM collision; SH KM-75 = ⅛ Thaler FrIII Gottorp)"),
    ("denmark", "dk-tid-163016", 17051,
     "lot is DK KM-81 4-Kroneskilling 1620 (different denomination tier — Kronemont vs regular Skilling)"),
    ("denmark", "dk-tid-94100", 11269,
     "lot is Gold Off-Metal Strike 2 Skilling 1711 (§9.1 Pn-tier exclusion)"),
    ("denmark", "dk-tid-94113", 13210,
     "lot is Gold Off-Metal Strike 12 Skilling 1713 (§9.1 Pn-tier exclusion)"),
    ("denmark", "dk-tid-97363", 17073,
     "lot is DK KM-240 2-Speciedaler 1663 (different denomination — our row is 1-Speciedaler)"),
    ("schleswig_holstein", "km-124-chr-v-1787", 13253,
     "lot is Gold Off-Metal Strike 1/24 SH KM-124 (§9.1 Pn-tier exclusion)"),
]


def _strip_lot(coin, lot_no: int) -> tuple[int, int, int]:
    """In-place strip catalog/weight/source references to ``lot_no``.
    Returns ``(catalog_stripped, weight_stripped, sources_stripped)``."""
    cat = coin.get("catalog") or {}
    cat_n = 0
    if cat.get("bruun_lot_no") == lot_no:
        for k in ("bruun_collection_id", "bruun_part", "bruun_lot_no", "bruun_page"):
            if k in cat:
                del cat[k]
                cat_n += 1

    lot_token = f"lot {lot_no}"
    lot_token_alt = f"lot_no: {lot_no}"

    w_n = 0
    wrg = coin.get("weight_rough_g")
    if isinstance(wrg, list):
        keep = []
        for entry in wrg:
            src = ""
            if hasattr(entry, "get"):
                src = entry.get("source", "") or ""
            if lot_token in str(src) or lot_token_alt in str(src):
                w_n += 1
                continue
            keep.append(entry)
        if w_n:
            wrg.clear()
            wrg.extend(keep)

    s_n = 0
    src_list = coin.get("sources")
    if isinstance(src_list, list):
        keep = []
        for entry in src_list:
            ref = ""
            if hasattr(entry, "get"):
                ref = entry.get("ref", "") or ""
            if lot_token in str(ref) or lot_token_alt in str(ref):
                s_n += 1
                continue
            keep.append(entry)
        if s_n:
            src_list.clear()
            src_list.extend(keep)

    return cat_n, w_n, s_n


def main() -> int:
    yaml = YAML(typ="rt")
    yaml.preserve_quotes = True
    yaml.width = 4096
    yaml.indent(mapping=2, sequence=4, offset=2)

    by_loc: dict[str, list[tuple[str, int, str]]] = {}
    for loc, cid, lot, reason in STRIPS:
        by_loc.setdefault(loc, []).append((cid, lot, reason))

    grand = [0, 0, 0]
    for loc, items in by_loc.items():
        path = DATA_DIR / f"{loc}.yml"
        with path.open() as f:
            doc = yaml.load(f)
        coins = doc.get("coins") or []
        loc_changed = False
        for cid, lot, reason in items:
            coin = next((c for c in coins if c.get("id") == cid), None)
            if coin is None:
                print(f"  [skip] {loc} :: {cid} — coin not found")
                continue
            n_cat, n_w, n_s = _strip_lot(coin, lot)
            if n_cat or n_w or n_s:
                loc_changed = True
                print(f"  {loc} :: {cid} ↔ lot {lot}: catalog={n_cat}, weight={n_w}, sources={n_s}")
                print(f"     reason: {reason}")
                grand[0] += n_cat; grand[1] += n_w; grand[2] += n_s
            else:
                print(f"  [no-op] {loc} :: {cid} ↔ lot {lot} — already clean")
        if loc_changed:
            with path.open("w") as f:
                yaml.dump(doc, f)

    print()
    print(f"Total stripped: catalog-fields={grand[0]}, weight_rough_g entries={grand[1]}, "
          f"sources entries={grand[2]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
