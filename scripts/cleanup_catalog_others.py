#!/usr/bin/env python3
"""One-shot cleanup of catalog.others pollution.

Three problem patterns found by audit:

1. Duplicates: "KM# X" appears in others while cat.km already = X.
   Action: drop the duplicate.

2. Narrative annotations leaked into the catalog field
   (e.g., "Glückstadt (nicht Kopenhagen!)", "≠ Hede 67A").
   Action: move to a 3-language note appendix; remove from others.

3. Bare source-name references like "Aagaard 2022" (no identifier).
   Action: move to coin.sources as a literature ref.

Patterns 2 and 3 are coin-specific; we hardcode them here rather than
guessing heuristically.

Run once:
    .venv/bin/python scripts/cleanup_catalog_others.py
"""
from __future__ import annotations
import re, pathlib
from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap, CommentedSeq

YML = pathlib.Path("data/locations/schleswig.yml")

# Coin-specific narrative items that need to migrate from catalog.others to note.
# Format: { coin_id: [list of strings to remove from others, with appendix text per lang] }
NARRATIVE_MIGRATION: dict[str, dict] = {
    "km-63-chr-v-1672": {
        "remove": [
            "Glückstadt (nicht Kopenhagen!)",
            "≠ Hede 67A",
            "im Aagaard 2022 Corpus dokumentiert",
        ],
        "note_append": {
            "de": "Glückstadter Prägung (nicht Kopenhagen) — abzugrenzen von Hede 67A; im Aagaard-2022-Corpus belegt.",
            "en": "Glückstadt issue (not Copenhagen) — to be distinguished from Hede 67A; documented in the Aagaard 2022 corpus.",
            "uk": "Карбування Glückstadt (не Копенгаген) — відрізняти від Hede 67A; задокументовано в корпусі Aagaard 2022.",
        },
    },
}

# Bare source-name refs to migrate to sources[].
SOURCE_MIGRATION: dict[str, list[dict]] = {
    "km-77-1-chr-v-1686": [
        {"remove": "Aagaard 2022",
         "source": {"type": "literature", "ref": "Aagaard 2022 Corpus"}},
    ],
    "km-80-chr-v-1694": [
        {"remove": "Aagaard 2022",
         "source": {"type": "literature", "ref": "Aagaard 2022 Corpus"}},
    ],
}


def remove_from_others(cat: CommentedMap, items: list[str]) -> int:
    others = cat.get("others") or []
    new_list = [o for o in others if o not in items]
    removed = len(others) - len(new_list)
    if removed:
        if new_list:
            cat["others"] = new_list
        else:
            cat.pop("others", None)
    return removed


def append_to_note(coin: CommentedMap, appendix: dict[str, str]):
    note = coin.get("note") or CommentedMap()
    for lang, text in appendix.items():
        existing = note.get(lang)
        if existing:
            # Append after a separator
            if text not in existing:
                note[lang] = f"{existing.rstrip('. ')} · {text}"
        else:
            note[lang] = text
    coin["note"] = note


def add_source(coin: CommentedMap, src: dict):
    sources = coin.get("sources")
    if sources is None:
        sources = CommentedSeq()
        coin["sources"] = sources
    # Avoid duplicate
    for s in sources:
        if s.get("ref") == src.get("ref") and s.get("type") == src.get("type"):
            return
    cm = CommentedMap()
    for k, v in src.items():
        cm[k] = v
    sources.append(cm)


def dedupe_named_field_in_others(cat: CommentedMap):
    """Remove from cat.others any string of form `<Label># <val>` where the
    named cat.<field> equals val. Examples: cat.km='146' kills 'KM# 146'."""
    field_label = {
        "km": "KM", "lange": "Lange", "hede": "Hede", "sieg": "Sieg",
        "schou": "Schou", "fr": "Fr", "bruun_lot": "Bruun",
    }
    others = cat.get("others") or []
    if not others:
        return 0
    to_remove = set()
    for field, label in field_label.items():
        val = cat.get(field)
        if not val:
            continue
        # Compare both with `# ` and without space
        candidates = {f"{label}# {val}", f"{label} #{val}", f"{label} # {val}", f"{label}#{val}"}
        for o in others:
            if o.strip() in candidates:
                to_remove.add(o)
    if to_remove:
        new_list = [o for o in others if o not in to_remove]
        if new_list:
            cat["others"] = new_list
        else:
            cat.pop("others", None)
    return len(to_remove)


def main():
    yaml = YAML()
    yaml.preserve_quotes = True
    yaml.width = 10000
    yaml.indent(mapping=2, sequence=4, offset=2)

    data = yaml.load(YML.read_text())
    coins = data.get("coins") or []

    dups_removed = 0
    narratives_moved = 0
    sources_moved = 0

    for coin in coins:
        cid = coin.get("id")
        cat = coin.get("catalog")
        if not isinstance(cat, dict):
            continue

        # 1. Dedup duplicates
        n = dedupe_named_field_in_others(cat)
        dups_removed += n
        if n:
            print(f"  dedup {cid}: removed {n} dup ref(s) from .others")

        # 2. Narrative migration (coin-specific)
        if cid in NARRATIVE_MIGRATION:
            spec = NARRATIVE_MIGRATION[cid]
            removed = remove_from_others(cat, spec["remove"])
            if removed:
                append_to_note(coin, spec["note_append"])
                narratives_moved += removed
                print(f"  narrative {cid}: moved {removed} item(s) to note")

        # 3. Source migration (coin-specific)
        if cid in SOURCE_MIGRATION:
            for spec in SOURCE_MIGRATION[cid]:
                removed = remove_from_others(cat, [spec["remove"]])
                if removed:
                    add_source(coin, spec["source"])
                    sources_moved += removed
                    print(f"  source {cid}: moved 1 ref to sources[]")

    with open(YML, "w") as f:
        yaml.dump(data, f)

    print()
    print(f"Total duplicates removed:   {dups_removed}")
    print(f"Narrative items migrated:   {narratives_moved}")
    print(f"Source refs migrated:       {sources_moved}")


if __name__ == "__main__":
    main()
