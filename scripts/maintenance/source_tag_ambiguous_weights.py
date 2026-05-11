"""Resolve ambiguous scalar ``weight_rough_g`` by cross-checking source caches.

Companion to ``source_tag_scalar_weights.py``. The single-source pass
left 40 coins on the floor: scalar weight + 2+ entries in
``coin.sources[]``. This script reads each source's cached data
(Numista per-piece JSON, ucoin URL-index, Bruun PDF lots) and finds
which source(s) actually publish the scalar value, then promotes the
scalar to list-shape with the matching source(s) named.

Resolution rules:

* For each source listed on the coin, look up its published weight
  in the corresponding cache.
* The scalar matches a source if the absolute difference is
  ≤ 0.005 g (rounding-tolerant; sources publish to 2-decimal
  precision). The tolerance is symmetric — ``ours == 28.59`` matches
  ``cache == 28.587`` and vice versa.
* If exactly **one** source matches → tag with that source's
  canonical short-name ("Numista", "ucoin",
  "Bruun Part X, lot N, p. M").
* If **multiple** sources match → tag is the joined list
  («"Numista, ucoin"») — preserves the historical «all sources agree»
  semantics while making the source explicit.
* If **no** source matches → leave the coin untouched and report it
  for manual review (the value may have come from a source we don't
  cache, or there's a transcription drift).

Idempotent. Re-runs are no-ops on already-converted coins.
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

WEIGHT_TOLERANCE_G = 0.005


# ---------- cache loaders --------------------------------------------


def load_ucoin_index() -> dict[str, dict]:
    if not UCOIN_INDEX.exists():
        return {}
    return json.loads(UCOIN_INDEX.read_text(encoding="utf-8"))


def load_bruun_lots() -> dict[tuple[str, int], dict]:
    """Return {(part_no, lot_no) -> lot dict}."""
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


def ucoin_weight(coin: dict, source_url: str, ucoin_idx: dict) -> float | None:
    m = re.search(r"tid=(\d+)", source_url or "")
    if not m:
        return None
    rec = ucoin_idx.get(m.group(1))
    if not rec:
        return None
    w = rec.get("weight_g")
    return float(w) if isinstance(w, (int, float)) else None


def bruun_weight(coin: dict, source_ref: str, bruun_lots: dict) -> float | None:
    cat = coin.get("catalog") or {}
    # First preference: explicit catalog.bruun_part / bruun_lot_no
    part = cat.get("bruun_part")
    lot_no = cat.get("bruun_lot_no")
    # Or parse "Bruun Part II, lot 14224, p. 301" from source ref
    if not (part and lot_no):
        m = re.search(r"Part\s+(I{1,3}V?|IV|\d+).*?lot\s+(\d+)", source_ref or "", re.IGNORECASE)
        if m:
            part = m.group(1).upper()
            try:
                lot_no = int(m.group(2))
            except ValueError:
                lot_no = None
    if not (part and lot_no):
        return None
    lot = bruun_lots.get((str(part), int(lot_no)))
    if not lot:
        return None
    w = lot.get("weight_g")
    return float(w) if isinstance(w, (int, float)) else None


# ---------- per-coin resolution --------------------------------------


def derive_source_tag(s: dict) -> str:
    return str(s.get("ref") or s.get("type") or "?")


def resolve_coin(coin: dict, ucoin_idx: dict, bruun_lots: dict) -> tuple[str, str | None]:
    """Return (action, message). action ∈ {converted, skipped, no_match}."""
    w = coin.get("weight_rough_g")
    if not isinstance(w, (int, float)):
        return ("non_scalar", None)
    if coin.get("weight_rough_verified") is False:
        return ("skipped", "weight_rough_verified=false")
    sources = [s for s in (coin.get("sources") or []) if isinstance(s, dict)]
    if len(sources) < 2:
        return ("skipped", "<2 sources — handled by single-source pass")

    matches: list[tuple[dict, float]] = []
    examined: list[tuple[str, float | None]] = []
    for src in sources:
        stype = src.get("type", "")
        url = src.get("url", "") or ""
        ref = src.get("ref", "") or ""
        cached_w: float | None = None
        if stype == "numista":
            cached_w = numista_weight(coin)
        elif stype == "ucoin":
            cached_w = ucoin_weight(coin, url, ucoin_idx)
        elif stype == "auction" and "Bruun" in ref:
            cached_w = bruun_weight(coin, ref, bruun_lots)
        # museum / web / others not auto-resolvable here
        examined.append((derive_source_tag(src), cached_w))
        if cached_w is not None and abs(cached_w - float(w)) <= WEIGHT_TOLERANCE_G:
            matches.append((src, cached_w))

    if not matches:
        return ("no_match", f"scalar={w} examined={examined}")

    # Promote to list shape
    tags = [derive_source_tag(s) for s, _ in matches]
    combined_tag = ", ".join(tags) if len(tags) > 1 else tags[0]
    coin["weight_rough_g"] = [{"value": float(w), "source": combined_tag}]
    return ("converted", f"matched: {combined_tag}")


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
        action, msg = resolve_coin(coin, ucoin_idx, bruun_lots)
        if action == "converted":
            summary["converted"] += 1
            summary["examined"] += 1
            converted_log.append((coin.get("id", "?"), msg or ""))
        elif action == "no_match":
            summary["no_match"] += 1
            summary["examined"] += 1
            no_match_log.append((coin.get("id", "?"), msg or ""))

    if summary["examined"]:
        with path.open("w", encoding="utf-8") as f:
            yaml.dump(data, f)
        print(f"\n{path.relative_to(REPO)}")
        print(f"  examined: {summary['examined']}  converted: {summary['converted']}  no_match: {summary['no_match']}")
        for cid, msg in converted_log:
            print(f"    ✓ {cid}: {msg}")
        for cid, msg in no_match_log:
            print(f"    ? {cid}: {msg}")
    return summary


def main() -> int:
    ucoin_idx = load_ucoin_index()
    bruun_lots = load_bruun_lots()
    print(f"ucoin index: {len(ucoin_idx)} entries; "
          f"Bruun lots: {len(bruun_lots)} (parts {sorted({p for p,_ in bruun_lots})})")

    files = sorted(p for p in LOCATIONS.glob("*.yml") if "-references" not in p.name)
    grand = {"converted": 0, "no_match": 0, "examined": 0}
    for f in files:
        for k, v in process_file(f, ucoin_idx, bruun_lots).items():
            grand[k] = grand.get(k, 0) + v
    print("\n=== Grand totals ===")
    for k, v in grand.items():
        print(f"  {k}: {v}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
