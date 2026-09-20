#!/usr/bin/env python3
"""Give the Hede-derived coin `note`s their Danish text back.

WHY THIS IS NOT A TRANSLATION
-----------------------------
These notes were written FROM danskmoent.dk's Hede pages, which are Danish.
The German and English we render are the translation; the Danish is the
original, and it is already on disk in `scripts/cache/hede/<page>.json`
under `description`. So this restores a source text rather than producing a
new one — no network, no model, no §0 exposure: every character comes from
the cited source.

WHAT IS AND IS NOT TOUCHED
--------------------------
Only coins where ALL of the following hold, because anything looser stops
being a restoration:

  * the coin renders on the Danish page (the four entities `denmark.yml`
    consumes, inside their year caps) and its `note` has no `da`;
  * a Hede page for its catalogue number is in the cache WITH a description;
  * that coin has NO Numista obverse/reverse description. This is the load-
    bearing exclusion. Where Numista also describes the type, our note is
    the NUMISTA description — richer, and about both faces — so substituting
    Hede's «Forside: portræt, bagside: våbenskjold» would silently DOWNGRADE
    the Danish reader's text while the other three languages keep the full
    one. Those coins stay English until someone translates them;
  * the German note opens «Vorderseite» and the Hede lead opens «Forside»,
    and the two are within 30 % of each other in length. A note that opens
    with a nominal is curator prose about one specimen, not a rendering of
    the Hede page, and the Hede text is not a substitute for it;
  * the `note:` line carries no YAML anchor. The emitter shares one mapping
    across coins with identical notes, and a per-coin Danish text must never
    reach a coin it was not read for.

Everything rejected is counted and printed. That number is the remaining
work, not an error.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[2]
FINAL = REPO / "data" / "v2" / "final"
HEDE = REPO / "scripts" / "cache" / "hede"
NUMISTA = REPO / "scripts" / "cache" / "numista"
FOLD_WIDTH = 200

# entity -> inclusive year cap, per `denmark.yml::consumes_entities`.
DENMARK_ENTITIES = {
    "danish_realm": None,
    "danish_norway": 1814,
    "royal_holstein": 1864,
    "gottorp_duchy": 1543,
}

# Lines below which the Hede page stops being prose: the measurement block
# and the mintmark/variant apparatus the HTML flattened into the same field.
_METRIC = re.compile(
    r"^(Vægt|Bruttovægt|Finhed|Finvægt|Marken fin|Randskrift|Møntmestermærke"
    r"|Sieg skelner|Illustrationen|Stemplerne)\b")
_CAT_PAREN = re.compile(r"\((?:Hede|Schou|Sieg|KM|Galster|Fr)[^)]*\)")
# Where the prose ends and the flattened variant table begins.
_TABLE = re.compile(
    r"(?:\b[A-E]\)|\bHede\b|\bSchou\b|\bSieg\b|\bÅr:|U\.år|\((?:R{1,3}|Unik)\))")
_TABLE_LEFTOVER = re.compile(
    r"(?:\b[A-E]\)|\bHede\b|\bSchou\b|\bSieg\b|\(R{1,3}\)|\(Unik\))")
# Words that begin a sentence whose full stop went missing with the inline
# mintmark image that used to precede them.
_SENTENCE = ("Møntmester", "Møntmærke", "Udmøntet", "Kaldet", "Slået", "Ved ",
             "Indskriften", "Mønten", "Del ")


# «Mønten» opens a sentence often enough to sit in the list above, but it is
# also an ordinary noun mid-sentence — «…kun virkede på Mønten i Altona til
# 1816» is one clause, and splitting it leaves the dangling «…virkede på.».
# So the split is refused when the preceding word is a preposition.
_PREP = {"på", "i", "ved", "af", "fra", "til", "om", "hos", "for", "med",
         "under", "over", "efter", "mod", "og"}
_SENTENCE_RE = re.compile(
    r"(?P<prev>[\wæøåÆØÅ]+) (?P<next>(?:%s))" % "|".join(_SENTENCE))


def _split_sentence(m: "re.Match") -> str:
    if m.group("prev").lower() in _PREP:
        return m.group(0)
    return f"{m.group('prev')}. {m.group('next')}"


# Where the page's prose gives way to its apparatus. `description` is cut at
# the first of these; `raw_text` keeps going.
_RAW_STOP = re.compile(
    r"\n(?=(?:Bruttovægt|Vægt|Finhed|Finvægt|Marken fin|Eksemplar|Litteratur"
    r"|Tilbage|Prøve))")


def source_text(page: dict) -> str:
    """The page's prose, repaired where `description` truncates it.

    The parser's `description` drops whatever followed the last inline element
    it recognised, which on 85 of the 729 cached pages cuts a sentence in half
    — «Udmøntet af Hans de Willers (Johan fra Vilna) i 2.259» loses its
    «eksemplarer.» and reads as a dangling number. `raw_text` holds the whole
    page, so the tail is taken from there, up to the measurement block.
    """
    desc = (page.get("description") or "").strip()
    raw = page.get("raw_text") or ""
    if not desc:
        return ""
    at = raw.find(desc)
    if at < 0:
        return desc
    tail = _RAW_STOP.split(raw[at + len(desc):])[0]
    return (desc + tail).strip()


def hede_lead(desc: str) -> str:
    """The prose part of a Hede page description, as one paragraph."""
    kept: list[str] = []
    for line in desc.replace("\r", "").split("\n"):
        if _METRIC.match(line.strip()):
            break
        kept.append(line)
    t = re.sub(r"\s*\n\s*", " ", "\n".join(kept))
    t = _CAT_PAREN.sub("", t)
    m = _TABLE.search(t)
    if m:
        t = t[:m.start()]
    t = re.sub(r"\s{2,}", " ", t).strip()
    t = re.sub(r"\s+([.,;:])", r"\1", t)
    # Repair what the dropped inline images left behind.
    t = re.sub(r",\s*,", ",", t)
    t = re.sub(r":\s*\.", ".", t)
    t = re.sub(r"\.{2,}", ".", t)
    t = re.sub(r":\s*,", ",", t)
    t = _SENTENCE_RE.sub(_split_sentence, t)
    t = re.sub(r"(?:^|(?<=\. ))Møntmestermærke[.:]\s*", "", t)
    t = re.sub(r"\s{2,}", " ", t).strip(" ,;:")
    if t and not t.endswith((".", "»", "!", "?")):
        t += "."
    return t


# danskmoent.dk talking about ITSELF — «click for the newspaper piece», «see
# the bibliography», «the coin is shown top right on this page». True of that
# site, meaningless on ours, and §0z role-3 furniture either way. The auction
# clause goes with them: what a find fetched at auction is out of scope
# project-wide, not a fact about the coinage.
_FURNITURE = re.compile(
    r"(?:Klik\b|denne side|litteraturliste|Tilbage til|avisomtale"
    r"|solgtes på auktion|indbragte)", re.I)


def drop_site_furniture(text: str) -> str:
    # The bibliography pointer also appears parenthetically inside a sentence
    # that is otherwise a fact worth keeping, so remove it BEFORE deciding
    # which whole sentences to drop.
    text = re.sub(r"\s*\((?:se|jf\.?)\s+litteraturlisten\)", "", text, flags=re.I)
    kept = [s for s in re.split(r"(?<=[.!?])\s+", text) if not _FURNITURE.search(s)]
    return re.sub(r"\s{2,}", " ", " ".join(kept)).strip()


def is_restoration(de: str, da: str) -> bool:
    """True when `da` is plausibly the text `de` was translated from."""
    if not de.startswith("Vorderseite") or not da.startswith("Forside"):
        return False
    if len(da) < 25 or _TABLE_LEFTOVER.search(da):
        return False
    # The lower bound is the real guard: Danish materially SHORTER than the
    # German means our note says things the Hede page does not, so the page is
    # not what it was written from. Longer is normal and fine — the page often
    # closes with a specimen sentence our German dropped, and that sentence is
    # the source's own prose, not an invention.
    return 0.70 <= len(da) / len(de) <= 3.50


def _numista_page(nid) -> dict | list | None:
    """One cached Numista type, or None. Some cached files hold a LIST."""
    page = NUMISTA / f"{nid}.json"
    if not page.is_file():
        return None
    return json.loads(page.read_text(encoding="utf-8"))


def cached_page_text(volume: str, number) -> str:
    """The Hede page for one catalogue number, falling back to its base page.

    danskmoent.dk publishes ONE page per base Hede number, and that page
    carries the sub-variants (A, B, C …) as rows on it — there is no
    `c4h102A.htm`. Our catalog fields cite the sub-variant, so asking for the
    page under its own name misses on 193 of the coins that DO have their
    Danish description on disk, under the base number. Trying the base second
    keeps an exact page winning whenever one exists (`c4h108ab`, `c5h112a`).
    """
    for name in (f"{volume}{number}",
                 re.sub(r"[A-Za-z]+$", "", f"{volume}{number}")):
        page = HEDE / f"{name}.json"
        if page.is_file():
            text = source_text(json.loads(page.read_text(encoding="utf-8")))
            if text:
                return text
    return ""


def _as_list(v) -> list:
    if v is None:
        return []
    return v if isinstance(v, list) else [v]


def danish_by_coin(entity: str, cap: int | None,
                   overwrite: bool = False) -> tuple[dict[str, str], int]:
    """{coin id: Danish note} for one entity, plus the count left behind."""
    doc = yaml.safe_load((FINAL / f"{entity}.yml").read_text(encoding="utf-8"))
    found: dict[str, str] = {}
    left = 0
    for coin in (doc.get("coins") or []):
        yf = coin.get("year_first")
        if cap is not None and (yf is None or yf > cap):
            continue
        note = coin.get("note")
        if not isinstance(note, dict):
            continue
        has_da = "da" in note
        if has_da and not (overwrite and note["da"].startswith("Forside")):
            continue
        if not has_da:
            left += 1
        cat = coin.get("catalog") or {}
        volume = cat.get("hede_volume")
        desc = ""
        for number in _as_list(cat.get("hede")):
            if not volume:
                continue
            text = cached_page_text(volume, number)
            if text:
                desc = text
        if not desc:
            continue
        de = (note.get("de") or "").strip()
        da = drop_site_furniture(hede_lead(desc))
        # The Numista gate below is a PROXY for «our note came from Numista,
        # not from Hede». `is_restoration` answers that same question from the
        # texts themselves — when the German opens «Vorderseite», the Danish
        # opens «Forside» and they are within the length band, our note IS the
        # Hede page rendered into German, whatever else Numista happens to
        # publish about the type. Direct evidence beats the proxy, so it is
        # tested first; 7 coins are only reachable this way.
        if is_restoration(de, da):
            found[coin["id"]] = da
            if not has_da:
                left -= 1
            continue
        # Numista describes this type → our note is Numista's, not Hede's.
        if any(
            isinstance(_numista_page(n), dict)
            and ((_numista_page(n).get("obverse") or {}).get("description"))
            for n in _as_list(cat.get("numista"))
        ):
            continue
    return found, left


# A coin item starts at «  - <key>:» and its keys are plain at that depth, so
# `id:` can sit after `note:` in the mapping — the id is read per CHUNK, not
# as a line that happens to precede the note.
_ITEM_RE = re.compile(r"^  - \S")
_ID_LINE_RE = re.compile(r"^    id: (?P<id>\S+)\s*$")
# An anchored note is shared with other coins — never give it a per-coin text.
_NOTE_RE = re.compile(r"^(?P<indent>\s*)note:\s*$")
_LANG_RE = re.compile(r"^(?P<indent>\s*)(?P<lang>de|en|uk|da): (?P<rest>.*)$")


def unfold(first: str, cont: list[str]) -> str:
    return yaml.safe_load(
        "v: " + first + "".join("\n  " + c.strip() for c in cont))["v"]


def fold(indent: str, key: str, text: str) -> list[str]:
    if ": " in text or " #" in text or text[:1] in "-?:,[]{}#&*!|>'\"%@`":
        text = "'" + text.replace("'", "''") + "'"
    cont = indent + "  "
    lines, cur = [], f"{indent}{key}: "
    for word in text.split(" "):
        if cur.strip() and len(cur) + len(word) + 1 > FOLD_WIDTH:
            lines.append(cur.rstrip() + " ")
            cur = cont
        cur += word + " "
    lines.append(cur.rstrip())
    return lines


def process(raw: str, danish: dict[str, str],
            overwrite: bool = False) -> tuple[str, int]:
    lines = raw.split("\n")
    # Pre-read each coin chunk's id, so a `note:` knows which coin it is on
    # regardless of where `id:` sits in the mapping.
    id_of_line: list[str | None] = [None] * len(lines)
    start, current = None, None
    for n, line in enumerate(lines):
        if _ITEM_RE.match(line):
            start, current = n, None
        m_id = _ID_LINE_RE.match(line)
        if m_id and start is not None:
            current = m_id.group("id")
            for k in range(start, len(lines)):
                if k > start and _ITEM_RE.match(lines[k]):
                    break
                id_of_line[k] = current
    out: list[str] = []
    added = 0
    i = 0
    while i < len(lines):
        line = lines[i]
        coin_id = id_of_line[i]
        m = _NOTE_RE.match(line)
        if not m or coin_id not in danish:
            out.append(line)
            i += 1
            continue
        note_indent = m.group("indent")
        out.append(line)
        i += 1
        block: list[str] = []
        langs: dict[str, str] = {}
        key, first, cont = None, "", []

        def close() -> None:
            if key:
                langs[key] = unfold(first, cont)

        while i < len(lines):
            line = lines[i]
            if not line.strip():
                break
            lm = _LANG_RE.match(line)
            if lm and lm.group("indent") == note_indent + "  ":
                close()
                key, first, cont = lm.group("lang"), lm.group("rest"), []
                block.append(line)
                i += 1
                continue
            if key and line.startswith(note_indent + "    "):
                cont.append(line)
                block.append(line)
                i += 1
                continue
            break
        close()
        out.extend(block)
        if langs.get("de", "").strip() == "":
            continue
        if "da" in langs:
            if not overwrite or not langs["da"].startswith("Forside"):
                continue
            if langs["da"] == danish[coin_id]:
                continue
            # Drop the stale `da` this script wrote on an earlier run.
            keep, skipping = [], False
            for bline in block:
                lm = _LANG_RE.match(bline)
                if lm and lm.group("indent") == note_indent + "  ":
                    skipping = lm.group("lang") == "da"
                if not skipping:
                    keep.append(bline)
            del out[len(out) - len(block):]
            out.extend(keep)
        out.extend(fold(note_indent + "  ", "da", danish[coin_id]))
        added += 1
    return "\n".join(out), added


def _strip_da(doc) -> None:
    for coin in (doc.get("coins") or []):
        note = coin.get("note")
        if isinstance(note, dict):
            note.pop("da", None)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--overwrite", action="store_true",
                    help="replace a Danish note this script wrote earlier "
                         "when the text it now reads differs")
    ap.add_argument("--apply", action="store_true",
                    help="write changes (default: dry run)")
    args = ap.parse_args()

    total_added = total_left = 0
    for entity, cap in DENMARK_ENTITIES.items():
        path = FINAL / f"{entity}.yml"
        danish, left = danish_by_coin(entity, cap, args.overwrite)
        raw = path.read_text(encoding="utf-8")
        new, added = process(raw, danish, args.overwrite)
        total_added += added
        total_left += left
        print(f"  {added:5}  +da   {left:4} left   {path.name}")
        if not added:
            continue
        before, after = yaml.safe_load(raw), yaml.safe_load(new)
        _strip_da(before)
        _strip_da(after)
        assert before == after, f"{path.name}: the edit changed more than `da`"
        parsed = yaml.safe_load(new)
        for coin in (parsed.get("coins") or []):
            if coin["id"] in danish:
                got = (coin.get("note") or {}).get("da")
                assert got == danish[coin["id"]], f"{coin['id']}: wrong text"
        if args.apply:
            path.write_text(new, encoding="utf-8")
    print(f"{'restored' if args.apply else 'would restore'}: {total_added} "
          f"Danish notes from the Hede cache; {total_left} notes still "
          f"English (Numista-described, curator prose, or no cached page)")
    if not args.apply:
        print("(dry run — pass --apply to write)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
