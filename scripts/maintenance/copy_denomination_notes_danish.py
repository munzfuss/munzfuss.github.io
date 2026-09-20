#!/usr/bin/env python3
"""Give the denomination-only coin `note`s their Danish leaf.

WHY THIS IS A COPY AND NOT A TRANSLATION
----------------------------------------
A few dozen coins carry a `note` that is nothing but the denomination —
«1/16 Taler», «⅓ Speciedaler», «Rytterpenning», «Firehvid». CLAUDE.md's i18n
policy puts those one tier above ordinary prose: a coin denomination in a
formal slot is ONE string in every language, kept in its period Danish /
German / Latin form. So the Danish leaf is the German leaf, byte for byte —
translating «Speciedaler» to anything would break the rule, not satisfy it.

WHAT IS EXCLUDED, AND WHY EACH EXCLUSION EXISTS
-----------------------------------------------
  * anything with a verb, a catalogue reference, a mint-master, a year or a
    «·» apparatus separator. «Ducat 1685 (Hede-12A) · Bruun-Specimen.» is a
    sentence about one specimen, not a denomination, and it needs real
    Danish;
  * the known source fragments — «Gotland», «Sverige», «Bishopric», «AR»,
    «Type II», «Ulfeldts», «, 2½ Ducat». These are not notes at all: they are
    stale parser output (a sub-realm label, a territory, the metal
    abbreviation, a denomination-equivalence tail) frozen into the seed
    because `note` is a soft-curated field, so a later builder fix cannot
    reach them. Copying one into a fourth language would spread the defect,
    not translate it. They are listed, not written.

Everything skipped is reported. Nothing here needs the network.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[2]
FINAL = REPO / "data" / "v2" / "final"
LOCATION = REPO / "data" / "v2" / "locations" / "denmark.yml"

# Stale parser output, not prose. Diagnosed 2026-09-20; the builders that
# produced them now guard against it, but the values survive in the seeds.
FRAGMENTS = {"Gotland", "Sverige", "Bishopric", "AR", "Type II", "Ulfeldts",
             ", 2½ Ducat"}

# A denomination and nothing else: an optional numeric or fraction part, then
# the coin's name. No sentence punctuation, no «·» apparatus, no digits after
# the first word (a year), no parentheses.
_DENOM = re.compile(
    r"^[\d½⅓¼⅙⅛⅔¾\s/.-]*"          # 1 · ½ · 1/16 · 2½ · 4-
    r"[A-Za-zÆØÅæøå][A-Za-zÄÖÜäöüßÆØÅæøå\- ]*$"
)


def is_denomination(text: str) -> bool:
    t = text.strip()
    if not t or len(t) >= 60 or t in FRAGMENTS:
        return False
    if any(ch in t for ch in "·().,;:0123456789".replace("0123456789", "")):
        return False
    if re.search(r"\d", t.split(" ", 1)[-1]) and " " in t:
        return False          # a trailing year — «Skilling 1771»
    return bool(_DENOM.match(t))


def entities() -> list[tuple[str, int | None]]:
    loc = yaml.safe_load(LOCATION.read_text(encoding="utf-8"))
    out = []
    for e in loc.get("consumes_entities") or []:
        out.append((e, None) if isinstance(e, str)
                   else (e["entity"], e.get("year_to")))
    return out


_ITEM_RE = re.compile(r"^  - \S")
_ID_RE = re.compile(r"^    id: (?P<id>\S+)\s*$")
_NOTE_RE = re.compile(r"^(?P<indent>\s*)note:\s*$")
_LANG_RE = re.compile(r"^(?P<indent>\s*)(?P<lang>de|en|uk|da): (?P<rest>.*)$")


def wanted(entity: str, cap: int | None) -> tuple[dict[str, str], list[str]]:
    """{coin id: Danish note} plus the fragment ids left alone."""
    doc = yaml.safe_load((FINAL / f"{entity}.yml").read_text(encoding="utf-8"))
    found: dict[str, str] = {}
    frags: list[str] = []
    for coin in doc.get("coins") or []:
        yf = coin.get("year_first")
        if cap is not None and (yf is None or yf > cap):
            continue
        note = coin.get("note")
        if not isinstance(note, dict) or note.get("da"):
            continue
        de = (note.get("de") or "").strip()
        if de in FRAGMENTS:
            frags.append(coin["id"])
        elif is_denomination(de):
            found[coin["id"]] = de
    return found, frags


def process(raw: str, danish: dict[str, str]) -> tuple[str, int]:
    """Insert `da:` after the `uk:` line of each named coin's note.

    Line-based for the same reason the Hede restorer is: re-emitting the file
    through a YAML dumper would reflow all 600 entries we are not touching.
    An ANCHORED note is shared with other coins and is never given a per-coin
    text.
    """
    lines = raw.split("\n")
    out: list[str] = []
    coin_id: str | None = None
    chunk: list[str] = []
    written = 0

    def flush() -> None:
        nonlocal written
        if coin_id in danish:
            for i, line in enumerate(chunk):
                m = _NOTE_RE.match(line)
                if not m:
                    continue
                indent = m.group("indent")
                j = i + 1
                last = None
                while j < len(chunk):
                    lm = _LANG_RE.match(chunk[j])
                    if not lm or len(lm.group("indent")) <= len(indent):
                        break
                    last = j
                    j += 1
                if last is not None:
                    pad = _LANG_RE.match(chunk[last]).group("indent")
                    text = danish[coin_id].replace("'", "''")
                    chunk.insert(last + 1, f"{pad}da: '{text}'")
                    written += 1
                break
        out.extend(chunk)

    for line in lines:
        if _ITEM_RE.match(line):
            flush()
            chunk = [line]
            coin_id = None
            continue
        if chunk:
            m = _ID_RE.match(line)
            if m and coin_id is None:
                coin_id = m.group("id")
            chunk.append(line)
        else:
            out.append(line)
    flush()
    return "\n".join(out), written


def strip_da(doc: dict) -> dict:
    for coin in doc.get("coins") or []:
        note = coin.get("note")
        if isinstance(note, dict):
            note.pop("da", None)
    return doc


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    total = 0
    frags: list[str] = []
    for entity, cap in entities():
        path = FINAL / f"{entity}.yml"
        danish, ent_frags = wanted(entity, cap)
        frags += ent_frags
        if not danish:
            continue
        raw = path.read_text(encoding="utf-8")
        new, written = process(raw, danish)
        before = yaml.safe_load(raw)
        after = yaml.safe_load(new)
        assert strip_da(after) == strip_da(before), f"{entity}: edit changed more than da"
        after = yaml.safe_load(new)
        for cid, text in danish.items():
            got = next((c["note"].get("da") for c in after["coins"]
                        if c.get("id") == cid), None)
            assert got == text, f"{entity}/{cid}: wrote {got!r}, wanted {text!r}"
        print(f"  {written:4}  +da   {path.name}")
        total += written
        if args.apply:
            path.write_text(new, encoding="utf-8")
    print(f"{'copied' if args.apply else 'would copy'}: {total} denomination "
          f"notes; {len(frags)} source fragments left for a separate fix")
    if frags:
        print("  fragments: " + ", ".join(sorted(frags)))
    if not args.apply:
        print("(dry run — pass --apply to write)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
