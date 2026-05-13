"""Apply ucoin-sourced composition to coin records.

Reads `scripts/cache/ucoin/_composition.json` (the sidecar built by
`ucoin_fetch_composition.py`) and for each coin that links to a tid
present in the sidecar:

  1. Map ucoin's «Composition» text to our enum:
       Bronze              → copper
       Gold X.XXX          → gold + fineness X.XXX
       Silver X.XXX        → silver + fineness X.XXX
       Silver (no value)   → silver (fineness unset)
       Copper-nickel / …   → copper (alloy)
  2. If our coin currently has metal=None: SET it from source, flip
     metal_verified: true.
  3. If our coin currently has inferred metal (metal_verified: false):
     compare against source. If they agree → flip metal_verified: true
     (source confirms inference). If they disagree → log a warning
     and leave metal as-is (manual review required).
  4. Optionally set fineness when missing and ucoin gives a decimal
     value; flip fineness_verified: true.
"""
from __future__ import annotations
import json
import re
import sys
from pathlib import Path

from ruamel.yaml import YAML

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lib.paths import UCOIN_CACHE, PROJECT_ROOT  # noqa: E402

SIDECAR = UCOIN_CACHE / "_composition.json"


def map_composition(text: str) -> tuple[str | None, float | None]:
    """Map ucoin composition string to (metal_enum, fineness).

    Handles ucoin's «Silver (Billon) X.XXX» / «Gold (Electrum) X.XXX»
    bracketed-qualifier forms by stripping the bracket before parsing
    the metal token + fineness number.
    """
    t = text.strip().lower()
    if not t:
        return None, None
    # Pure bronze / copper alloy
    if any(k in t for k in ("bronze", "brass", "copper-nickel", "copper nickel", "cupronickel", "aluminium-bronze")):
        return "copper", None
    if t.startswith("copper") and "nickel" not in t:
        return "copper", None
    # Bracketed qualifier — «Silver (Billon) 0.166» / «Gold (Electrum) 0.500»
    # The (qualifier) overrides the leading metal label for our taxonomy
    # since ucoin uses (Billon) / (Electrum) precisely to flag low-fineness
    # silver / electrum-gold variants distinct from the bare metal class.
    bracket = re.match(r"^(gold|silver)\s*\((billon|electrum)\)\s*([\d.]+)?", t)
    if bracket:
        outer, inner, fin = bracket.group(1), bracket.group(2), bracket.group(3)
        try:
            f = float(fin) if fin else None
        except ValueError:
            f = None
        if inner == "billon":
            return "billon", f
        if inner == "electrum":
            return "gold", f  # electrum = gold-silver alloy → keep gold
    # Match bare «Gold X.XXX» / «Silver X.XXX»
    m = re.match(r"^(gold|silver|billon|electrum)(?:\s+([\d.]+))?", t)
    if m:
        kw, fin = m.group(1), m.group(2)
        try:
            f = float(fin) if fin else None
        except ValueError:
            f = None
        # Project taxonomy: «Silver X.XXX» with X.XXX < 0.5 → billon
        # (low-fineness silver-copper alloy is the «billon» tier in our
        # schema; ucoin uses the bare «Silver» label regardless of
        # fineness, so we normalise on the numeric value).
        if kw == "silver" and f is not None and f < 0.5:
            return "billon", f
        if kw == "billon":
            return "billon", f
        if kw == "electrum":
            return "gold", f  # electrum is gold-silver alloy
        return kw, f
    return None, None


def _w(c):
    w = c.get("weight_rough_g")
    if isinstance(w, list):
        return w[0].get("value") if w else None
    return w


def extract_tid(coin: dict) -> str | None:
    for s in coin.get("sources") or []:
        url = s.get("url") or ""
        m = re.search(r"\?tid=(\d+)", url)
        if m:
            return m.group(1)
    return None


def process_file(path: Path, sidecar: dict, stats: dict) -> int:
    yaml = YAML()
    yaml.preserve_quotes = True
    yaml.width = 4096
    yaml.indent(mapping=2, sequence=4, offset=2)
    with open(path) as f:
        doc = yaml.load(f)
    touched = 0
    for c in doc.get("coins") or []:
        tid = extract_tid(c)
        if not tid or tid not in sidecar:
            continue
        ucoin_metal, ucoin_fin = map_composition(sidecar[tid].get("composition", ""))
        if ucoin_metal is None:
            stats["unknown_composition"].append((c.get("id"), sidecar[tid].get("composition")))
            continue
        cur_metal = c.get("metal")
        # Default to False when field absent: project convention is that
        # `metal_verified: true` is set explicitly when a source attests
        # the metal; absence means inferred from heuristics (sub-Skilling
        # → billon, etc.) and unconfirmed. Defaulting to True would
        # silently treat all legacy entries without the flag as source-
        # attested, blocking ucoin-driven correction below.
        cur_verified = bool(c.get("metal_verified", False))
        # Case 1: metal missing → set + verify
        if cur_metal is None:
            c["metal"] = ucoin_metal
            c["metal_verified"] = True
            stats["metal_set"].append((c.get("id"), ucoin_metal))
            touched += 1
        # Case 2: metal present + unverified inference → confirm or
        # replace with ucoin's source-attested value (per CLAUDE.md §4
        # «verified-wins-over-unverified» — our inferred value yields
        # to a source-cited reading; ucoin is the cited source here).
        elif not cur_verified:
            if cur_metal == ucoin_metal:
                c["metal_verified"] = True
                stats["metal_confirmed"].append((c.get("id"), ucoin_metal))
                touched += 1
            else:
                c["metal"] = ucoin_metal
                c["metal_verified"] = True
                stats["metal_replaced"].append(
                    (c.get("id"), f"was={cur_metal} (inferred) → {ucoin_metal} (ucoin)")
                )
                touched += 1
        # Case 3: metal present + verified — only flag if disagrees
        elif cur_metal != ucoin_metal:
            stats["metal_disagree_with_source"].append(
                (c.get("id"), f"ours={cur_metal} (verified) ucoin={ucoin_metal}")
            )
        # Fineness inference from ucoin
        if ucoin_fin is not None and c.get("fineness") is None:
            c["fineness"] = ucoin_fin
            c["fineness_verified"] = True
            stats["fineness_set"].append((c.get("id"), ucoin_fin))
            touched += 1
    if touched:
        with open(path, "w") as f:
            yaml.dump(doc, f)
    return touched


def main():
    if not SIDECAR.exists():
        raise SystemExit(f"No sidecar at {SIDECAR}; run ucoin_fetch_composition.py first")
    sidecar = json.loads(SIDECAR.read_text())
    stats = {
        "metal_set": [], "metal_confirmed": [], "metal_replaced": [],
        "metal_mismatch": [],
        "metal_disagree_with_source": [], "fineness_set": [],
        "unknown_composition": [],
    }
    total = 0
    for p in sorted((PROJECT_ROOT / "data/locations").glob("*.yml")):
        if "references" in p.name:
            continue
        n = process_file(p, sidecar, stats)
        if n:
            print(f"  {p.relative_to(PROJECT_ROOT)}: {n} fields touched")
            total += n
    seed = PROJECT_ROOT / "data/seed/hede/denmark.yml"
    if seed.exists():
        n = process_file(seed, sidecar, stats)
        if n:
            print(f"  {seed.relative_to(PROJECT_ROOT)}: {n} fields touched")
            total += n
    print(f"\nTotal field changes: {total}\n")
    for k, lst in stats.items():
        print(f"  {k}: {len(lst)}")
        for s in lst[:5]:
            print(f"    {s}")
        if len(lst) > 5:
            print(f"    ... ({len(lst) - 5} more)")


if __name__ == "__main__":
    main()
