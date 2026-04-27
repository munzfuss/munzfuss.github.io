#!/usr/bin/env python3
"""One-off migration: move data-quality notes from fuss_refs.secondary into coin.note.

The "Стопа" column was meant to show only nominal & actual computed standards,
but for several coins it was being used to document fineness estimates and
weight uncertainties — content that belongs in the «Примітка» column.

Affected coins:
  - 7 Tönning Scheide (km-155, 158, 164, x009, 185, 183, 212): full secondary moves
    to note (data-quality only).
  - km-82 (8 Skilling Danske): secondary contains both the actual implied standard
    and historical context. Drop secondary entirely — auto-implied «↳ Факт ≈ X»
    will replace the math part; historical sentence moves to note.

Run once:
    .venv/bin/python scripts/relocate_data_notes.py
"""
from __future__ import annotations
import pathlib
from ruamel.yaml import YAML
from ruamel.yaml.scalarstring import LiteralScalarString

yaml = YAML()
yaml.preserve_quotes = True
yaml.width = 10000
yaml.indent(mapping=2, sequence=4, offset=2)

# Coin id → "full" (move whole secondary to note) or "split" (special handling for km-82)
COINS_FULL_MOVE = {
    "km-155-fr-iv-1695",
    "km-158-fr-iv-1696",
    "km-164-fr-iv-1698",
    "km-x009-fr-iv-1701",
    "km-185-karl-fr-1703",
    "km-183-karl-fr-1703",
    "km-212-karl-fr-1711",
}

# For km-82, append only the historical-context sentence (after "·" separator).
# Already-translated phrasing per language:
KM82_TRAILS = {
    "de": "Vorläufer des späteren Kurantmøntfod 1726 nach dem Standard «<i>lighter than Species, heavier than Scheidemünze</i>»",
    "en": "Forerunner of the later Kurantmøntfod of 1726, fitting the standard «<i>lighter than Species, heavier than petty coin</i>».",
    "uk": "Попередник пізнішого Kurantmøntfod 1726 за стандартом «<i>lighter than Species, heavier than розмінна монета</i>».",
}


def _block(s: str) -> str:
    """Wrap multiline strings with literal-scalar to keep YAML readable."""
    return LiteralScalarString(s) if "\n" in s or len(s) > 120 else s


def append_to_note(coin: dict, additions: dict[str, str]):
    note = coin.get("note") or {}
    if not isinstance(note, dict):
        return
    for lang in ("de", "en", "uk"):
        add = (additions.get(lang) or "").strip()
        if not add:
            continue
        cur = (note.get(lang) or "").rstrip()
        if not cur:
            note[lang] = add
        else:
            sep = " · " if not cur.endswith(("·", ";", ".")) else " "
            note[lang] = cur + sep + add
    coin["note"] = note


p = pathlib.Path("data/locations/schleswig.yml")
data = yaml.load(p.read_text())

processed = 0
for coin in data.get("coins", []) or []:
    cid = coin.get("id")
    refs = coin.get("fuss_refs") or []
    if not refs:
        continue

    if cid in COINS_FULL_MOVE:
        # Find secondary, take its label as additions
        sec = next((r for r in refs if r.get("rank") == "secondary"), None)
        if not sec:
            continue
        lbl = sec.get("label") or {}
        additions = {lang: (lbl.get(lang) or "") for lang in ("de", "en", "uk")}
        append_to_note(coin, additions)
        # Remove secondary
        coin["fuss_refs"] = [r for r in refs if r.get("rank") != "secondary"]
        processed += 1
        print(f"  moved-secondary→note  {cid}")

    elif cid == "km-82-1,-chr-v-1694":
        # Drop secondary entirely; append historical context to note
        coin["fuss_refs"] = [r for r in refs if r.get("rank") != "secondary"]
        append_to_note(coin, KM82_TRAILS)
        processed += 1
        print(f"  km-82: dropped secondary, appended historical context to note")

with open(p, "w") as f:
    yaml.dump(data, f)

print(f"\n{processed} coins migrated.")
