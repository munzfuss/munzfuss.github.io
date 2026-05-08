"""Convert scalar ``weight_rough_g`` to list-shape with explicit source tag.

Project rule (formalised 2026-05-08): when all available sources agree
on a data point, we historically left the source unspecified —
implicitly «all sources that provide this value». That convention
breaks the moment we add a new specimen with a *different* value: we
end up appending the new specimen with its source while the old
scalar floats sourceless, looking like an unannotated «(legacy)»
entry. To prevent that, every weight that is verified and has an
unambiguous single source on the coin gets its scalar promoted to
list-shape with the source explicitly named.

Selection rule:

* ``weight_rough_g`` is a scalar (``int`` / ``float``)
* ``weight_rough_verified`` is not ``false`` (default-True counts).
  Schema default is ``True`` — only coins that explicitly set
  ``False`` are skipped.
* ``coin.sources`` has **exactly one** dict-shaped entry. Multiple
  sources mean the value's provenance is ambiguous and needs human
  review. Zero sources mean we have nothing to attribute and skip.

For matched coins, the scalar ``W`` becomes::

    weight_rough_g:
      - value: W
        source: <derived from the single sources[] entry>

The source tag is taken from ``sources[0].ref`` (which the project
already uses as the canonical short-form of each citation, e.g.
"Numista", "ucoin", "Bruun Part I, lot 1086, p. 132", "IKMK Berlin,
Inv. <id>"). If ``ref`` is missing, falls back to the source's
``type`` value uppercased.

Idempotent: re-running over already-converted coins is a no-op.
"""

from __future__ import annotations

import sys
from pathlib import Path

from ruamel.yaml import YAML

REPO = Path(__file__).resolve().parents[2]
LOCATIONS = REPO / "data" / "locations"


def derive_source_tag(source: dict) -> str:
    ref = source.get("ref")
    if ref:
        return str(ref)
    t = source.get("type")
    return str(t) if t else "?"


def fix_coin(coin: dict) -> str | None:
    """If the coin matches the criteria, mutate it in-place. Returns a
    short reason string when changed, ``None`` when skipped."""
    w = coin.get("weight_rough_g")
    if not isinstance(w, (int, float)):
        return None
    if coin.get("weight_rough_verified") is False:
        return "skipped: weight_rough_verified=false"
    sources = coin.get("sources") or []
    sources = [s for s in sources if isinstance(s, dict)]
    if len(sources) == 0:
        return "skipped: no sources to attribute"
    if len(sources) > 1:
        return f"skipped: {len(sources)} sources (ambiguous)"
    tag = derive_source_tag(sources[0])
    coin["weight_rough_g"] = [{"value": w, "source": tag}]
    return f"converted → list with source={tag!r}"


def process_file(path: Path) -> dict[str, int]:
    yaml = YAML(typ="rt")
    yaml.preserve_quotes = True
    yaml.width = 4096
    yaml.indent(mapping=2, sequence=4, offset=2)
    with path.open("r", encoding="utf-8") as f:
        data = yaml.load(f)
    coins = data.get("coins") if isinstance(data, dict) else None
    if not coins:
        return {"converted": 0, "ambiguous_skipped": 0, "no_source_skipped": 0,
                "unverified_skipped": 0, "non_scalar": 0}
    counts = {"converted": 0, "ambiguous_skipped": 0, "no_source_skipped": 0,
              "unverified_skipped": 0, "non_scalar": 0}
    converted_examples: list[tuple[str, str]] = []
    skipped_examples: list[tuple[str, str]] = []
    for coin in coins:
        result = fix_coin(coin)
        if result is None:
            counts["non_scalar"] += 1
            continue
        if result.startswith("converted"):
            counts["converted"] += 1
            if len(converted_examples) < 5:
                converted_examples.append((coin.get("id", "?"), result))
        elif "ambiguous" in result:
            counts["ambiguous_skipped"] += 1
            if len(skipped_examples) < 3:
                skipped_examples.append((coin.get("id", "?"), result))
        elif "no sources" in result:
            counts["no_source_skipped"] += 1
        elif "verified=false" in result:
            counts["unverified_skipped"] += 1
    if counts["converted"]:
        with path.open("w", encoding="utf-8") as f:
            yaml.dump(data, f)
    if counts["converted"] or counts["ambiguous_skipped"]:
        print(f"\n{path.relative_to(REPO)}")
        for k, v in counts.items():
            if v:
                print(f"  {k}: {v}")
        for cid, reason in converted_examples:
            print(f"    ✓ {cid}: {reason}")
        for cid, reason in skipped_examples:
            print(f"    – {cid}: {reason}")
    return counts


def main() -> int:
    files = sorted(p for p in LOCATIONS.glob("*.yml") if "-references" not in p.name)
    print(f"Scanning {len(files)} location files…")
    grand: dict[str, int] = {"converted": 0, "ambiguous_skipped": 0,
                             "no_source_skipped": 0, "unverified_skipped": 0,
                             "non_scalar": 0}
    for f in files:
        for k, v in process_file(f).items():
            grand[k] = grand.get(k, 0) + v
    print("\n=== Grand totals ===")
    for k, v in grand.items():
        print(f"  {k}: {v}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
