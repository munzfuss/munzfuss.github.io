"""Resolve "(prior data, source not recorded)" weight entries.

Scope: ``data/locations/{denmark,schleswig_holstein}.yml``. The marker
appeared in earlier sessions when scalars were promoted to list shape
without recording which source had originally provided the value —
typically because a new Bruun-PDF specimen was being appended and the
original scalar's provenance hadn't been preserved.

For each coin with a "(prior data, source not recorded)" entry in
``weight_rough_g``, look up the value in each source's cache:

* Numista per-piece JSON
* ucoin URL-index (also handles ``dk-tid-<N>`` coin-id pattern when
  no explicit ucoin URL is on the coin)
* Bruun PDF lots (skip if the lot-no is the same as one already
  attributed in the same list — those entries are NOT the prior-data
  source by definition)

Matches use a ±0.005 g tolerance (rounding-tolerant for
2-decimal sources). When exactly one source publishes the value, the
"prior data" tag is replaced with that source's canonical short name.
When multiple agree, the tag becomes the joined list. Otherwise the
entry is left as-is and reported for manual review.

Idempotent. Re-runs are no-ops on already-resolved coins.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from ruamel.yaml import YAML

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lib.paths import (  # noqa: E402
    NUMISTA_CACHE,
    UCOIN_CACHE,
    BRUUN_CACHE,
    PROJECT_ROOT as REPO,
)

LOCATIONS = REPO / "data" / "locations"
UCOIN_INDEX = UCOIN_CACHE / "_url_index.json"
BRUUN_DIR = BRUUN_CACHE / "lots"

TARGET_FILES = ["denmark.yml", "schleswig_holstein.yml"]
WEIGHT_TOLERANCE_G = 0.005
PRIOR_MARKER = "prior data, source not recorded"


# ---------- cache loaders --------------------------------------------


def load_ucoin_index() -> dict[str, dict]:
    if not UCOIN_INDEX.exists():
        return {}
    return json.loads(UCOIN_INDEX.read_text(encoding="utf-8"))


def load_bruun_lots() -> dict[tuple[str, int], dict]:
    out: dict[tuple[str, int], dict] = {}
    if not BRUUN_DIR.exists():
        return out
    for f in sorted(BRUUN_DIR.glob("part*.json")):
        m = re.match(r"part(\d+)", f.stem)
        if not m:
            continue
        part_num = int(m.group(1))
        part_roman = {1: "I", 2: "II", 3: "III", 4: "IV"}.get(part_num, str(part_num))
        for lot in json.loads(f.read_text(encoding="utf-8")):
            lot_no = lot.get("lot_no")
            if lot_no is None:
                continue
            out[(part_roman, int(lot_no))] = lot
    return out


# ---------- per-source weight lookups --------------------------------


def numista_weight(coin: dict) -> float | None:
    cat = coin.get("catalog") or {}
    nid = cat.get("numista")
    if not nid:
        return None
    cache = NUMISTA_CACHE / f"{nid}.json"
    if not cache.exists():
        return None
    rec = json.loads(cache.read_text(encoding="utf-8"))
    w = rec.get("weight")
    if isinstance(w, (int, float)):
        return float(w)
    if isinstance(w, str):
        m = re.match(r"([\d.]+)", w)
        return float(m.group(1)) if m else None
    return None


def ucoin_weight_for_url(url: str, idx: dict) -> float | None:
    m = re.search(r"tid=(\d+)", url or "")
    if not m:
        return None
    rec = idx.get(m.group(1))
    if not rec:
        return None
    w = rec.get("weight_g")
    return float(w) if isinstance(w, (int, float)) else None


def ucoin_weight_for_id(coin_id: str, idx: dict) -> float | None:
    """Fall back to coin id when the dk-tid-<N> pattern names the tid
    directly and no ucoin URL is on the coin."""
    m = re.match(r"^[a-z]+-tid-(\d+)", coin_id or "")
    if not m:
        return None
    rec = idx.get(m.group(1))
    if not rec:
        return None
    w = rec.get("weight_g")
    return float(w) if isinstance(w, (int, float)) else None


def bruun_weight_from_ref(source_ref: str, lots: dict) -> float | None:
    m = re.search(r"Part\s+(I{1,3}V?|IV|\d+).*?lot\s+(\d+)", source_ref or "", re.IGNORECASE)
    if not m:
        return None
    part = m.group(1).upper()
    try:
        lot_no = int(m.group(2))
    except ValueError:
        return None
    lot = lots.get((str(part), lot_no))
    if not lot:
        return None
    w = lot.get("weight_g")
    return float(w) if isinstance(w, (int, float)) else None


# ---------- per-coin resolution --------------------------------------


def resolve_prior_data(coin: dict, ucoin_idx: dict, bruun_lots: dict) -> tuple[str, str | None]:
    """Returns (action, message). action ∈ {converted, no_match, n/a}."""
    w_list = coin.get("weight_rough_g")
    if not isinstance(w_list, list):
        return ("n/a", None)
    prior_idx = None
    for i, entry in enumerate(w_list):
        if isinstance(entry, dict) and PRIOR_MARKER in str(entry.get("source", "")):
            prior_idx = i
            break
    if prior_idx is None:
        return ("n/a", None)
    target = float(w_list[prior_idx]["value"])

    # Collect already-attributed sources in the SAME weight list — those
    # weights are explicitly tied to specific specimens and should NOT
    # be considered candidates for «prior data» (the prior-data entry
    # came from a *different* source than the others, by construction).
    already_attributed_invs = set()
    already_attributed_lots = set()
    for j, entry in enumerate(w_list):
        if j == prior_idx or not isinstance(entry, dict):
            continue
        src = str(entry.get("source", ""))
        m = re.search(r"Part\s+(I{1,3}V?|IV|\d+).*?lot\s+(\d+)", src, re.IGNORECASE)
        if m:
            already_attributed_lots.add((m.group(1).upper(), int(m.group(2))))
        m = re.search(r"IKMK Berlin,\s*Inv\.\s*(\d+)", src)
        if m:
            already_attributed_invs.add(m.group(1))

    matches: list[str] = []
    examined: list[tuple[str, float | None]] = []

    sources = [s for s in (coin.get("sources") or []) if isinstance(s, dict)]

    # Numista
    nw = numista_weight(coin)
    examined.append(("Numista", nw))
    if nw is not None and abs(nw - target) <= WEIGHT_TOLERANCE_G:
        matches.append("Numista")

    # ucoin — first via explicit URL on a sources[] entry; fall back to
    # coin-id pattern.
    uw: float | None = None
    for s in sources:
        if s.get("type") == "ucoin":
            cand = ucoin_weight_for_url(s.get("url") or "", ucoin_idx)
            if cand is not None:
                uw = cand
                break
    if uw is None:
        uw = ucoin_weight_for_id(coin.get("id") or "", ucoin_idx)
    examined.append(("ucoin", uw))
    if uw is not None and abs(uw - target) <= WEIGHT_TOLERANCE_G:
        matches.append("ucoin")

    # Bruun — try every Bruun source ref, skipping lots already
    # attributed in the SAME weight list (those are different
    # specimens by construction).
    for s in sources:
        if s.get("type") != "auction":
            continue
        ref = s.get("ref") or ""
        if "Bruun" not in ref:
            continue
        m = re.search(r"Part\s+(I{1,3}V?|IV|\d+).*?lot\s+(\d+)", ref, re.IGNORECASE)
        if not m:
            continue
        part_lot = (m.group(1).upper(), int(m.group(2)))
        if part_lot in already_attributed_lots:
            continue
        bw = bruun_weight_from_ref(ref, bruun_lots)
        examined.append((ref[:40], bw))
        if bw is not None and abs(bw - target) <= WEIGHT_TOLERANCE_G:
            matches.append(ref)

    if not matches:
        return ("no_match", f"target={target} examined={examined}")

    new_tag = ", ".join(matches) if len(matches) > 1 else matches[0]
    w_list[prior_idx]["source"] = new_tag
    return ("converted", f"matched: {new_tag}")


# ---------- driver ---------------------------------------------------


def process_file(path: Path, ucoin_idx: dict, bruun_lots: dict) -> dict:
    yaml = YAML(typ="rt")
    yaml.preserve_quotes = True
    yaml.width = 4096
    yaml.indent(mapping=2, sequence=4, offset=2)
    with path.open("r", encoding="utf-8") as f:
        data = yaml.load(f)
    coins = data.get("coins") if isinstance(data, dict) else None
    if not coins:
        return {"converted": 0, "no_match": 0, "examined": 0}

    summary = {"converted": 0, "no_match": 0, "examined": 0}
    converted_log: list[tuple[str, str]] = []
    no_match_log: list[tuple[str, str]] = []

    for coin in coins:
        action, msg = resolve_prior_data(coin, ucoin_idx, bruun_lots)
        if action == "n/a":
            continue
        summary["examined"] += 1
        if action == "converted":
            summary["converted"] += 1
            converted_log.append((coin.get("id", "?"), msg or ""))
        else:
            summary["no_match"] += 1
            no_match_log.append((coin.get("id", "?"), msg or ""))

    if summary["examined"]:
        with path.open("w", encoding="utf-8") as f:
            yaml.dump(data, f)
        print(f"\n{path.relative_to(REPO)}")
        print(f"  examined: {summary['examined']}  converted: {summary['converted']}  no_match: {summary['no_match']}")
        for cid, msg in converted_log[:10]:
            print(f"    ✓ {cid}: {msg}")
        if len(converted_log) > 10:
            print(f"    … and {len(converted_log) - 10} more converted")
        for cid, msg in no_match_log:
            print(f"    ? {cid}: {msg}")
    return summary


def main() -> int:
    ucoin_idx = load_ucoin_index()
    bruun_lots = load_bruun_lots()
    print(f"ucoin index: {len(ucoin_idx)} entries; "
          f"Bruun lots: {len(bruun_lots)} (parts {sorted({p for p,_ in bruun_lots})})")

    grand = {"converted": 0, "no_match": 0, "examined": 0}
    for fname in TARGET_FILES:
        path = LOCATIONS / fname
        for k, v in process_file(path, ucoin_idx, bruun_lots).items():
            grand[k] = grand.get(k, 0) + v
    print("\n=== Grand totals ===")
    for k, v in grand.items():
        print(f"  {k}: {v}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
