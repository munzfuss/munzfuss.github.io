"""Thin out intra-sub-variant IKMK / Bruun specimens that contribute no
distinguishing signal beyond min / middle / max.

RETIRED (2026-06-24): operated on the V1 data/locations/<loc>.yml coin
yamls (removed once V2 reached parity), applying 4 hardcoded SH IKMK
drops from the 2026-05-09 audit — no longer runnable. The V2 §9a thinning
for the museum sources lives in thin_kmk_seed.py (now integrated into
build_kmk_seed.py); an equivalent ikmk-seed thinning is an open
follow-up (see docs/handoff.md).

Background. Several coin entries accumulated 5+ specimens from a single
resource (most often IKMK Berlin) within a single Stempelvariante
sub-group. After §9a multi-specimen merge, all of those weights live in
``weight_rough_g`` and all of their citations live in ``sources[]``. The
intermediate values between the lightest and heaviest specimens carry
no additional information about the standard's variance envelope — they
are noise from over-sampling one museum's holdings — and they crowd the
rendered weight column with redundant alt-source badges.

Operational rule (formalised 2026-05-09): when one coin entry has ≥5
weight_rough_g entries from a *single resource* AND those entries
sub-group by published catalog index (e.g. Lange 339C vs cf Lange 339B
vs Lange 339B) into one bucket of ≥5 specimens AND the bucket has
uniform/absent fineness — keep only ``min``, the position-``len//2``
middle of the weight-sorted list, and ``max``; drop the others along
with their matching ``sources[]`` URLs.

This script encodes the manual decision for the four sub-groups
identified in the 2026-05-09 audit:

* schleswig_holstein :: km-46-fr-iii-1617    cf Lange 339B (11 → 3)
* schleswig_holstein :: km-46-fr-iii-1617    Lange 339C    ( 8 → 3)
* schleswig_holstein :: km-5-hans-jr-sonderb-1618 Lange 536b ( 6 → 3)
* schleswig_holstein :: km-9-hans-jr-sonderb-1619 Lange 533A ( 7 → 3)

Total: 20 specimens removed. Mule and cf-Lange-534 specimens on km-9
are in their own (smaller) sub-groups and stay untouched.

The script is idempotent — re-running after the cleanup is a no-op
because each target inv-number is filtered out only if still present.

Usage::

    python scripts/maintenance/thin_intra_subvariant_specimens.py
"""

from __future__ import annotations

import sys
from pathlib import Path

from ruamel.yaml import YAML

PROJECT = Path(__file__).resolve().parents[2]


# Per-(coin, sub-group) decisions: list of inv-numbers to DROP. Inv-numbers to
# KEEP are simply those not in this list. Sourced from the 2026-05-09 audit.
DROPS: dict[tuple[str, str], list[str]] = {
    # ('<location>', '<coin id>'): ['inv-no', ...]
    ("schleswig_holstein", "km-46-fr-iii-1617"): [
        # cf Lange 339B (drop 8 of 11; keep 1.69 / 2.01 / 2.40)
        "18284942",  # 1.82
        "18284945",  # 1.90
        "18285049",  # 1.91
        "18285053",  # 2.00
        "18285052",  # 2.03
        "18285059",  # 2.08
        "18284940",  # 2.10
        "18285056",  # 2.10
        # Lange 339C (drop 5 of 8; keep 1.57 / 1.90 / 2.02)
        "18285096",  # 1.79
        "18285098",  # 1.85
        "18285061",  # 1.89
        "18285107",  # 1.92
        "18285112",  # 1.94
    ],
    ("schleswig_holstein", "km-5-hans-jr-sonderb-1618"): [
        # Lange 536b (drop 3 of 6; keep 1.63 / 2.03 / 2.34)
        "18284708",  # 1.78
        "18284706",  # 1.96
        "18284702",  # 2.14
    ],
    ("schleswig_holstein", "km-9-hans-jr-sonderb-1619"): [
        # Lange 533A (drop 4 of 7; keep 1.71 / 1.83 / 2.21)
        "18284695",  # 1.73
        "18284402",  # 1.82
        "18284694",  # 2.04
        "18284696",  # 2.06
    ],
}


def _matches_inv(text: str, inv: str) -> bool:
    """True if the given source/ref/url string mentions the inv number.

    Inv numbers appear in three places per coin entry:

    * ``weight_rough_g[i].source`` ⇒ ``IKMK Berlin, Inv. <inv>[...]``
    * ``sources[i].ref``           ⇒ ``IKMK Berlin, Inv. <inv>[...]``
    * ``sources[i].url``           ⇒ ``https://ikmk.smb.museum/object?id=<inv>``
    """
    if not text:
        return False
    return inv in str(text)


def _filter_coin(coin, drops: list[str]) -> tuple[int, int]:
    """In-place filter weight_rough_g and sources by inv-numbers."""
    wrg = coin.get("weight_rough_g")
    src = coin.get("sources")
    n_w = n_s = 0

    if isinstance(wrg, list):
        keep = []
        for entry in wrg:
            label = entry.get("source", "") if hasattr(entry, "get") else ""
            if any(_matches_inv(label, inv) for inv in drops):
                n_w += 1
                continue
            keep.append(entry)
        if n_w:
            # Reassign in place to preserve YAML round-trip metadata where
            # possible. ruamel CommentedSeq supports clear()+extend.
            wrg.clear()
            wrg.extend(keep)

    if isinstance(src, list):
        keep = []
        for entry in src:
            ref = entry.get("ref", "") if hasattr(entry, "get") else ""
            url = entry.get("url", "") if hasattr(entry, "get") else ""
            if any(_matches_inv(ref, inv) or _matches_inv(url, inv) for inv in drops):
                n_s += 1
                continue
            keep.append(entry)
        if n_s:
            src.clear()
            src.extend(keep)

    return n_w, n_s


def main() -> int:
    yaml = YAML(typ="rt")
    yaml.preserve_quotes = True
    yaml.width = 4096
    yaml.indent(mapping=2, sequence=4, offset=2)

    by_loc: dict[str, list[tuple[str, list[str]]]] = {}
    for (loc, cid), invs in DROPS.items():
        by_loc.setdefault(loc, []).append((cid, invs))

    grand_w = grand_s = 0
    for loc, items in by_loc.items():
        path = PROJECT / "data" / "locations" / f"{loc}.yml"
        with path.open() as f:
            doc = yaml.load(f)
        coins = doc.get("coins") or []
        loc_w = loc_s = 0
        for cid, invs in items:
            coin = next((c for c in coins if c.get("id") == cid), None)
            if coin is None:
                print(f"  [skip] {loc} :: {cid} — coin not found")
                continue
            n_w, n_s = _filter_coin(coin, invs)
            loc_w += n_w
            loc_s += n_s
            print(f"  {loc} :: {cid} — dropped weight_rough_g={n_w}, sources={n_s}")
        if loc_w or loc_s:
            with path.open("w") as f:
                yaml.dump(doc, f)
        grand_w += loc_w
        grand_s += loc_s

    print()
    print(f"Total: weight_rough_g entries dropped = {grand_w}, sources entries dropped = {grand_s}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
