#!/usr/bin/env python3
"""Phase-2 enrichment: merge Numista catalog references into each coin's catalog.

Reads scripts/numista_refs.json (output of Chrome batch fetch) — keyed by
Numista piece-id, value = list of ref strings like "KM# 12", "Lange# 539".

Continuation handling:
    Numista renders multi-variant references as
        "KM# 616.1, 616.2, etc., C# 47, Hede# 37"
    which we parse as ["KM# 616.1", "616.2", "etc.", "C# 47", "Hede# 37"].
    Items without "#" are merged into a single named field as a comma-list:
        cat.km = "616.1, 616.2"
    (the literal "etc." is dropped — it isn't a real catalog index)

Routing:
    KM            → catalog.km
    Lange         → catalog.lange
    Hede          → catalog.hede
    SIEG / Sieg   → catalog.sieg
    Schou         → catalog.schou
    Fr            → catalog.fr
    Bruun (lot)   → catalog.bruun_lot   (rare in Numista; usually our own)
    Dav variants  → first non-empty → catalog.dav; rest → catalog.others
    All other prefixes → catalog.others (deduplicated)

If a named field is already populated, the new value is appended to others
ONLY when the value differs from the existing one.
"""
from __future__ import annotations
import json, pathlib
from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap, CommentedSeq

REFS_JSON = pathlib.Path("scripts/numista_refs.json")
YML = pathlib.Path("data/locations/schleswig_holstein.yml")

# Map Numista prefix → catalog field name in our schema
PREFIX_FIELD = {
    "KM": "km",
    "Lange": "lange",
    "Hede": "hede",
    "SIEG": "sieg",
    "Sieg": "sieg",
    "Schou": "schou",
    "Fr": "fr",
    "Bruun": "bruun_lot",
}

DAV_PREFIXES = {"Dav", "Dav EC II", "Dav EC III", "Dav EC IV", "Dav ECT",
                "Dav Lg", "Dav SG", "Dav GT I", "Dav CCT"}

SKIP_VALUES = {"etc.", "etc", "..."}


def split_prefix(item: str) -> tuple[str | None, str]:
    """'KM# 12' → ('KM', '12'); 'Dav EC II# 3679' → ('Dav EC II', '3679');
    '616.2' → (None, '616.2')."""
    if "#" not in item:
        return None, item.strip()
    p, rest = item.split("#", 1)
    return p.strip(), rest.strip()


def expand_continuations(items: list[str]) -> list[tuple[str, str]]:
    """[('KM# 616.1'), ('616.2'), ('etc.'), ('C# 47')] →
    [('KM','616.1'), ('KM','616.2'), ('C','47')] (etc. dropped, prefix inherited)."""
    out = []
    last_prefix = None
    for it in items:
        if it in SKIP_VALUES:
            continue
        p, v = split_prefix(it)
        if v in SKIP_VALUES:
            continue
        if p is None:
            if last_prefix is None:
                continue  # orphan continuation, skip
            out.append((last_prefix, v))
        else:
            last_prefix = p
            out.append((p, v))
    return out


def merge_refs_into_catalog(cat: CommentedMap, refs: list[tuple[str, str]]):
    """In-place: distribute refs into named fields & catalog.others."""
    others = list(cat.get("others") or [])
    others_set = set(others)

    # ---- IDEMPOTENT CLEANUP: undo damage from a previous buggy run ----
    # The .dav field was meant to hold a bare value (e.g. "1311", "EC IV 72")
    # because the Jinja template prepends "Dav " when rendering. An earlier
    # version of this script wrote "Dav EC II# 3674" into .dav, producing
    # "Dav Dav EC II# 3674" in the rendered HTML. Detect that pattern and
    # move it to others.
    existing_dav = cat.get("dav")
    if isinstance(existing_dav, str) and ("#" in existing_dav or
                                          existing_dav.startswith("Dav ")):
        # Split " · "-joined entries back into individual refs and rehome
        for piece in existing_dav.split(" · "):
            piece = piece.strip()
            if not piece: continue
            if piece not in others_set:
                others.append(piece)
                others_set.add(piece)
        cat.pop("dav", None)

    # Group same-field refs first so multiple values get joined as comma-list
    by_field: dict[str, list[str]] = {}
    leftover: list[str] = []  # for prefixes that don't map to named fields

    for prefix, value in refs:
        if prefix in PREFIX_FIELD:
            by_field.setdefault(PREFIX_FIELD[prefix], []).append(value)
        elif prefix in DAV_PREFIXES:
            # Route ALL Dav variants (Dav EC II, Dav GT I, etc.) to others,
            # since the .dav schema field stores only one bare value and the
            # template prepends "Dav " — no clean way to represent variants there.
            leftover.append(f"{prefix}# {value}")
        else:
            leftover.append(f"{prefix}# {value}")

    # Apply named fields
    for field, values in by_field.items():
        # Dedup while preserving order
        seen = set()
        uniq = []
        for v in values:
            if v not in seen:
                seen.add(v)
                uniq.append(v)
        merged = ", ".join(uniq)

        existing = cat.get(field)
        if not existing:
            cat[field] = merged
        elif str(existing).strip() == merged.strip():
            pass  # identical, nothing to do
        else:
            # Existing value differs — keep existing in field, append new to others
            field_label = {"km": "KM", "sieg": "Sieg", "fr": "Fr",
                           "lange": "Lange", "hede": "Hede", "schou": "Schou",
                           "bruun_lot": "Bruun"}.get(field, field.title())
            for v in uniq:
                fmt = f"{field_label}# {v}"
                if fmt not in others_set:
                    others.append(fmt)
                    others_set.add(fmt)

    # Merge leftover (non-mapped) refs into others
    for ref in leftover:
        if ref not in others_set:
            others.append(ref)
            others_set.add(ref)

    if others:
        cat["others"] = others


def main():
    refs_data: dict[str, list[str]] = json.loads(REFS_JSON.read_text())

    yaml = YAML()
    yaml.preserve_quotes = True
    yaml.width = 10000
    yaml.indent(mapping=2, sequence=4, offset=2)

    data = yaml.load(YML.read_text())
    coins = data.get("coins") or []

    enriched = 0
    no_nid = 0
    no_data = 0
    nothing_added = 0

    for coin in coins:
        cat = coin.get("catalog") or CommentedMap()
        nid = cat.get("numista")
        if not nid:
            no_nid += 1
            continue
        items = refs_data.get(str(nid))
        if items is None:
            no_data += 1
            continue
        if not items:
            nothing_added += 1
            continue
        # Snapshot before
        before_others = list(cat.get("others") or [])
        before_keys = {k: cat.get(k) for k in ("km","lange","hede","sieg","schou","fr","dav","bruun_lot")}
        refs = expand_continuations(items)
        merge_refs_into_catalog(cat, refs)
        coin["catalog"] = cat
        # Did anything change?
        after_others = list(cat.get("others") or [])
        after_keys = {k: cat.get(k) for k in ("km","lange","hede","sieg","schou","fr","dav","bruun_lot")}
        if before_others != after_others or before_keys != after_keys:
            enriched += 1
        else:
            nothing_added += 1

    with open(YML, "w") as f:
        yaml.dump(data, f)

    print(f"Coins:                  {len(coins)}")
    print(f"  Enriched:             {enriched}")
    print(f"  Nothing new to add:   {nothing_added}")
    print(f"  No catalog.numista:   {no_nid}")
    print(f"  No data fetched:      {no_data}")


if __name__ == "__main__":
    main()
