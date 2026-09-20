#!/usr/bin/env python3
"""Repair the coin `note`s that are source fragments, not prose.

THE DEFECT
----------
Twenty-one coins render a `note` that is a single stray word — «Gotland»,
«Sverige», «Bishopric», «AR», «Type II», «Ulfeldts», «, 2½ Ducat». All three
languages carry the identical string, so it was never a translation problem:
the VALUE is wrong. Each one is the residue of a seed builder splitting one
source string into a field plus a remainder, and dropping the remainder into
`note`:

  «Lübeck (Bishopric). Taler»                        → nominal + «Bishopric»
  «Halv ørtug, Vesterås (Sverige)»                   → nominal + «Sverige»
  IKMK nominal «Krone (AR)»                          → nominal + «AR»
  Numista «½ Speciedaler - Frederik III (Type II)»   → nominal + «Type II»
  NGC «Denmark 1/4 Portugaloser, 2-1/2 Ducat FR# 64.1» → nominal + «, 2½ Ducat»
  Galster page «Hans, 1 Hvid, Visby (Gotland)»       → nominal + «Gotland»

The builders have since grown guards against exactly these shapes —
`build_bruun_denmark_seed._denom_from_text` returns None for a residue that
is still a territory, and the Galster builder writes `sub_realm`, not a note.
None of that can reach the values, because `note` is a CURATED_FIELD: a
re-seed preserves whatever is already there. That is the point of the field,
and it is why these survived every regen since. So each repair carries a
`_curation_holds` entry, which freezes the repaired state — present or
absent — against the next regen.

`trace_coin.py why` reports no curator decision behind any of them.

NOT ALL OF THEM ARE REDUNDANT, AND THAT DECIDES THE TREATMENT
-------------------------------------------------------------
DROP — the fragment repeats a structured field the entry already carries, so
deleting it loses nothing: «Gotland» (the entry's own `sub_realm: gotland`
and `mint: Visby`), «Bishopric» (`mint`), «AR» (`metal: silver`), «Type II».

MOVE — «Sverige» is the ONLY record that the two «Halv ørtug, Vesterås»
pieces are Swedish issues: both carry `mint: null`. The source page names the
mint in its title — «Hans, Halv ørtug u.år, Vesterås (Sverige)» — so the fact
goes to `mint`, where it belongs, and is verified against that page (§4:
one source publishing the value directly is enough).

REWRITE — «, 2½ Ducat» is not noise but a tariff equivalence with its comma
still attached: NGC's own heading gives the ¼ Portugaløser as 2½ ducats. The
source is already cited on the entry. «Ulfeldts» is a truncated name: Hede
150 (4 skilling, København, 1644-1645, Schou 113-122 + 82-89, legend JUSTUS
(JEHOVA) JUDEX — our coin is Schou 82) records that «Mønterne, der blev slået
i denne anledning kaldes Ulfeldtmønter eller Hebræere». Both keep a note,
correctly stated and sourced, rather than losing the fact.

One nominal is repaired alongside: `unified-dk-bruun-14115` reads «Lübeck.
Taler» in the final while its own seed reads «1 Taler» — the same territory
leak, one layer further on, and the only such nominal in any final.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[2]
V2 = REPO / "data" / "v2"

_WHY_NOTE = ("2026-09-20: the note was a source fragment, not prose — a seed "
             "builder's leftover after splitting one source string into a "
             "field plus a remainder. Frozen so a re-seed cannot restore it; "
             "see repair_fragment_notes.py for the full diagnosis.")
_WHY_MINT = ("2026-09-20: recovered from the note «Sverige», which was the "
             "parenthetical of the source page's own title «Hans, Halv ørtug "
             "u.år, Vesterås (Sverige)» — the entry had mint: null, so this "
             "was the only record that the piece is a Swedish issue.")
_WHY_NOMINAL = ("2026-09-20: the final read «Lübeck. Taler» while this "
                "entry's own seed reads «1 Taler» — Bruun's territory prefix "
                "«Lübeck (Bishopric). Taler» leaked into the nominal.")

# The Hede page our Schou-82 coin belongs to, quoted for the note below.
_ULFELDT = {
    "de": "Als <i>Ulfeldtmønt</i> oder <i>Hebræermønt</i> bezeichnet — "
          "Rückseiteninschrift JUSTUS (JEHOVA) JUDEX.",
    "en": "Known as an <i>Ulfeldtmønt</i> or <i>Hebræermønt</i> — reverse "
          "legend JUSTUS (JEHOVA) JUDEX.",
    "uk": "Відома як <i>Ulfeldtmønt</i> або <i>Hebræermønt</i> — напис "
          "реверсу JUSTUS (JEHOVA) JUDEX.",
    "da": "Kaldet <i>Ulfeldtmønt</i> eller <i>Hebræermønt</i> — "
          "bagsideindskrift JUSTUS (JEHOVA) JUDEX.",
}
_ULFELDT_SOURCE = {
    "type": "literature",
    "url": "https://www.danskmoent.dk/chr/c4h150.htm",
    "ref": "Hede 150 (4 skilling, København 1644-1645, Schou 113-122 + 82-89) "
           "— danskmoent.dk c4h150.htm",
}

_DUCAT = {
    "de": "Im NGC-Katalog als ¼ Portugaløser = 2½ Dukaten geführt.",
    "en": "Listed in the NGC catalogue as ¼ Portugaløser = 2½ ducats.",
    "uk": "У каталозі NGC подано як ¼ портуґалезера = 2½ дуката.",
    "da": "Ført i NGC-kataloget som ¼ portugaløser = 2½ dukat.",
}

# fragment → what to do with the entry carrying it.
DROP = {"Gotland", "Bishopric", "AR", "Type II"}
MINT_FOR = {"Sverige": "Vesterås"}
REWRITE = {", 2½ Ducat": _DUCAT, "Ulfeldts": _ULFELDT}
FRAGMENTS = DROP | set(MINT_FOR) | set(REWRITE)

# The final-layer nominal that leaked its territory, and what the entry's own
# seed says it should be.
NOMINAL_FIX = {"unified-dk-bruun-14115": ("Lübeck. Taler", "1 Taler")}


def files() -> list[Path]:
    out = sorted(V2.glob("seed/*/*.yml"))
    out += sorted(V2.glob("seed_unified/*.yml"))
    out += sorted(V2.glob("final/*.yml"))
    return out


_ITEM_RE = re.compile(r"^  - \S")
# The id is either the item's own first key («  - id: dk-bruun-14975», the
# seeds) or a plain key further down the item (the finals, where `id:` can sit
# after `note:`). Both shapes occur, so both are read.
_ID_RE = re.compile(r"^    id: (?P<id>\S+)\s*$")
_ITEM_ID_RE = re.compile(r"^  - id: (?P<id>\S+)\s*$")


def _key_span(chunk: list[str], key: str) -> tuple[int, int] | None:
    """[start, end) of a top-level key of one coin item, children included."""
    for i, line in enumerate(chunk):
        if line.startswith(f"    {key}:") and not line.startswith(f"    {key}::"):
            j = i + 1
            while j < len(chunk) and (chunk[j].startswith("      ")
                                      or chunk[j].strip() == ""):
                j += 1
            return i, j
    return None


def _q(text: str) -> str:
    return "'" + text.replace("'", "''") + "'"


def edit_chunk(chunk: list[str], frag: str | None, eid: str) -> list[str]:
    """Apply one entry's repair to its raw lines.

    Line-based on purpose. Both round-tripping serializers this project has
    re-wrap the long `verification_note` scalars these files are full of, so a
    structural load/save rewrites ~2 900 lines to say exactly what they said
    before and buries the 66 repairs inside it. Editing the lines touches
    nothing else.
    """
    out = list(chunk)
    holds: dict[str, str] = {}

    if frag in DROP or frag in MINT_FOR:
        span = _key_span(out, "note")
        if span:
            del out[span[0]:span[1]]
        holds["note"] = _WHY_NOTE
    elif frag in REWRITE:
        span = _key_span(out, "note")
        body = [f"      {lang}: {_q(text)}"
                for lang, text in REWRITE[frag].items()]
        if span:
            out[span[0]:span[1]] = ["    note:"] + body
        holds["note"] = _WHY_NOTE

    if frag in MINT_FOR:
        span = _key_span(out, "mint")
        line = f"    mint: {MINT_FOR[frag]}"
        if span:
            out[span[0]:span[1]] = [line]
        else:
            out.insert(1, line)
        vspan = _key_span(out, "mint_verified")
        if vspan:
            out[vspan[0]:vspan[1]] = ["    mint_verified: true"]
        else:
            out.insert(out.index(line) + 1, "    mint_verified: true")
        holds["mint"] = _WHY_MINT
        holds["mint_verified"] = _WHY_MINT

    if frag == "Ulfeldts":
        # §5: the name comes from a source, so the source travels with it.
        span = _key_span(out, "sources")
        if span and not any(_ULFELDT_SOURCE["url"] in ln
                            for ln in out[span[0]:span[1]]):
            out[span[1]:span[1]] = [
                f"      - type: {_ULFELDT_SOURCE['type']}",
                f"        url: {_ULFELDT_SOURCE['url']}",
                f"        ref: {_q(_ULFELDT_SOURCE['ref'])}",
            ]

    if eid in NOMINAL_FIX:
        was, now = NOMINAL_FIX[eid]
        span = _key_span(out, "nominal")
        if span and out[span[0]].split(": ", 1)[-1].strip().strip("'\"") == was:
            out[span[0]:span[1]] = [f"    nominal: {_q(now)}"]
            holds["nominal"] = _WHY_NOMINAL

    if holds:
        span = _key_span(out, "_curation_holds")
        existing: list[str] = []
        if span:
            existing = out[span[0] + 1:span[1]]
            del out[span[0]:span[1]]
        block = ["    _curation_holds:"] + existing
        for field, why in holds.items():
            if not any(ln.strip().startswith(f"{field}:") for ln in existing):
                block.append(f"      {field}: {_q(why)}")
        while out and out[-1].strip() == "":
            out.pop()
        out += block
    return out


def process(raw: str, wanted: dict[str, str | None]) -> tuple[str, list[str]]:
    lines = raw.split("\n")
    out: list[str] = []
    chunk: list[str] = []
    eid: str | None = None
    done: list[str] = []

    def flush() -> None:
        nonlocal chunk
        if chunk and eid in wanted:
            out.extend(edit_chunk(chunk, wanted[eid], eid))
            done.append(eid)
        else:
            out.extend(chunk)
        chunk = []

    for line in lines:
        if _ITEM_RE.match(line):
            flush()
            chunk = [line]
            m = _ITEM_ID_RE.match(line)
            eid = m.group("id") if m else None
            continue
        if chunk:
            m = _ID_RE.match(line)
            if m and eid is None:
                eid = m.group("id")
            chunk.append(line)
        else:
            out.append(line)
    flush()
    return "\n".join(out), done


def targets(doc: dict) -> dict[str, str | None]:
    """{entry id: the fragment it carries, or None when only a nominal fix}."""
    key = "coins" if "coins" in doc else "entries"
    out: dict[str, str | None] = {}
    for entry in doc.get(key) or []:
        note = entry.get("note")
        frag = ((note or {}).get("de") or "").strip() if isinstance(note, dict) else ""
        if frag in FRAGMENTS:
            out[entry["id"]] = frag
        elif entry.get("id") in NOMINAL_FIX and \
                entry.get("nominal") == NOMINAL_FIX[entry["id"]][0]:
            out[entry["id"]] = None
    return out


def check(before: dict, after: dict, wanted: dict) -> None:
    """Nothing outside the named entries may change, and each must be right."""
    key = "coins" if "coins" in before else "entries"
    b = {e["id"]: e for e in before.get(key) or []}
    a = {e["id"]: e for e in after.get(key) or []}
    assert set(a) == set(b), "an entry appeared or vanished"
    for eid in b:
        if eid not in wanted:
            assert a[eid] == b[eid], f"{eid}: changed but was not a target"
            continue
        frag = wanted[eid]
        if frag in DROP or frag in MINT_FOR:
            assert "note" not in a[eid], f"{eid}: note survived"
        elif frag in REWRITE:
            assert a[eid]["note"] == REWRITE[frag], f"{eid}: wrong note"
        if frag in MINT_FOR:
            assert a[eid].get("mint") == MINT_FOR[frag], f"{eid}: mint not set"
            assert a[eid].get("mint_verified") is True, f"{eid}: flag not set"
        if eid in NOMINAL_FIX:
            assert a[eid]["nominal"] == NOMINAL_FIX[eid][1], f"{eid}: nominal"
        if frag == "Ulfeldts":
            assert any(s_.get("url") == _ULFELDT_SOURCE["url"]
                       for s_ in a[eid].get("sources") or []), \
                f"{eid}: the Hede citation was not added"
        assert a[eid].get("_curation_holds"), f"{eid}: no hold recorded"


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()

    total = 0
    for path in files():
        raw = path.read_text(encoding="utf-8")
        before = yaml.safe_load(raw) or {}
        wanted = targets(before)
        if not wanted:
            continue
        new, done = process(raw, wanted)
        assert set(done) == set(wanted), \
            f"{path.name}: edited {sorted(set(done) ^ set(wanted))} unexpectedly"
        check(before, yaml.safe_load(new) or {}, wanted)
        print(f"{path.relative_to(REPO)}")
        for eid, frag in wanted.items():
            what = ("nominal" if frag is None else
                    "drop" if frag in DROP else
                    "move → mint" if frag in MINT_FOR else "rewrite")
            print(f"    {eid}: «{frag or NOMINAL_FIX[eid][0]}» → {what}")
        total += len(wanted)
        if args.apply:
            path.write_text(new, encoding="utf-8")
    print(f"{'repaired' if args.apply else 'would repair'}: {total} entries")
    if not args.apply:
        print("(dry run — pass --apply to write)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
