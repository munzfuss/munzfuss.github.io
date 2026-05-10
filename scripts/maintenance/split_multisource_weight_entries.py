"""Split `\\n`-joined source labels in measurement-list entries into one
entry per source.

Background. Several weight_rough_g / fineness / diameter_mm entries
historically used a single FieldValue with the ``source`` string
joining two or more independent citations via a literal ``\\n``::

    weight_rough_g:
      - {value: 28.893, source: "Hede 39A\\nNumista"}

This is a stringly-typed encoding of structured provenance. Every
audit / dedup script that reads sources has to re-parse the string
with ``re.split(r"[,;\\n]", ...)`` to recover the constituent
sources — the parser-of-display-string anti-pattern.

The cleanest fix is **Option C from TODO I**: split each multi-source
entry into N entries that share the same numeric value, one per
source line. The existing display pipeline already groups list-form
entries by rounded value (see ``compute.make_display_groups``), so
two entries with the same value collapse into ONE rendered span with
both sources accumulated into the tooltip — visually identical to
the previous shape, structurally clean.

Example transformation::

    # before
    weight_rough_g:
      - {value: 28.893, source: "Hede 39A\\nNumista"}

    # after
    weight_rough_g:
      - {value: 28.893, source: "Hede 39A"}
      - {value: 28.893, source: "Numista"}

The script handles ``weight_rough_g``, ``fineness``, ``diameter_mm``
uniformly. Idempotent — re-running on already-split data is a no-op
because no remaining ``\\n`` is found.

Usage::

    python scripts/maintenance/split_multisource_weight_entries.py [--dry-run]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap

PROJECT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT / "data" / "locations"
SHARED_DIR = PROJECT / "data" / "shared"

LIST_FIELDS = ("weight_rough_g", "fineness", "diameter_mm")


def _split_entries(field_value):
    """Return (new_list, n_splits) where each multi-source FieldValue is
    expanded into one entry per source line. Non-list inputs pass
    through unchanged.
    """
    if not isinstance(field_value, list):
        return field_value, 0
    out = []
    n_splits = 0
    for entry in field_value:
        if not isinstance(entry, (dict, CommentedMap)):
            out.append(entry)
            continue
        src = entry.get("source", "")
        if not isinstance(src, str) or "\n" not in src:
            out.append(entry)
            continue
        parts = [p.strip() for p in src.split("\n") if p.strip()]
        if len(parts) <= 1:
            # Single-line after strip — collapse the empty bits and continue.
            entry["source"] = parts[0] if parts else ""
            out.append(entry)
            continue
        # Emit one copy per source line, preserving every other key.
        for i, p in enumerate(parts):
            if i == 0:
                # Mutate original entry in place so any preserved
                # ruamel comments / formatting carry on the first copy.
                entry["source"] = p
                out.append(entry)
            else:
                clone = CommentedMap()
                for k, v in entry.items():
                    clone[k] = v
                clone["source"] = p
                out.append(clone)
            n_splits += 1
        n_splits -= 1  # one of the N entries is the original; we count N-1 NEW splits
    return out, n_splits


def _process_doc(doc):
    coins = doc.get("coins") or []
    n_total_splits = 0
    n_coins_touched = 0
    for coin in coins:
        if not isinstance(coin, (dict, CommentedMap)):
            continue
        coin_touched = False
        for field in LIST_FIELDS:
            cur = coin.get(field)
            if not isinstance(cur, list):
                continue
            new, n = _split_entries(cur)
            if n:
                # Reassign in-place to preserve YAML metadata where possible.
                cur.clear()
                cur.extend(new)
                n_total_splits += n
                coin_touched = True
        if coin_touched:
            n_coins_touched += 1
    return n_total_splits, n_coins_touched


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    yaml = YAML(typ="rt")
    yaml.preserve_quotes = True
    yaml.width = 4096
    yaml.indent(mapping=2, sequence=4, offset=2)

    paths = sorted(list(DATA_DIR.glob("*.yml")) + list(SHARED_DIR.glob("*.yml")))
    grand = 0
    coins_total = 0
    for path in paths:
        if path.name.endswith("-references.yml"):
            continue
        with path.open() as f:
            doc = yaml.load(f)
        if doc is None:
            continue
        n_splits, n_coins = _process_doc(doc)
        if n_splits:
            print(f"  {path.relative_to(PROJECT)}: {n_splits} new entries across {n_coins} coins")
            if not args.dry_run:
                with path.open("w") as f:
                    yaml.dump(doc, f)
        grand += n_splits
        coins_total += n_coins

    print()
    print(f"Total: {grand} new entries across {coins_total} coins"
          f"{' (dry-run; no files written)' if args.dry_run else ''}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
