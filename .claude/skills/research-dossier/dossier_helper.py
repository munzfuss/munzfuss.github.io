#!/usr/bin/env python3
"""Mechanical signal-scan for a `docs/research/*.md` dossier.

Emits CANDIDATES, not verdicts — every hit needs a human (or agent) read of
the surrounding text before it moves a rubric score. The scan is deliberately
cheap and regex-based: it can tell you that a paragraph says «probably» with no
hedge label nearby, it cannot tell you whether the claim is actually hedged by
the sentence before it.

    python dossier_helper.py docs/research/foo.md
    python dossier_helper.py --list
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
RESEARCH = ROOT / "docs" / "research"

# C5 — speculation words. A hit is only a problem when no hedge LABEL sits near.
SPECULATION = re.compile(
    r"\b(probably|likely|presumably|apparently|suggests that|seems to|"
    r"must have been|no doubt|ймовірно|мабуть|напевно)\b", re.I)
HEDGE_LABEL = re.compile(
    r"\b(hypothesis|hypothes|unverified|not verified|open question|would be "
    r"settled|pending|гіпотеза|не перевірен|відкрите питання)\b", re.I)

# C3 — a parameter change narrated without an instrument nearby.
CHANGE = re.compile(
    r"\b(changed|drifted|rose|fell|settles? at|reduced to|raised to|became)\b", re.I)
INSTRUMENT = re.compile(
    r"\b(forordning|møntordning|moentordning|plakat|ordinance|decree|"
    r"reichsabschied|reichsmünzordnung|recess|patent|åbent brev|aabent brev)\b", re.I)

# C4 — citation shape.
URL = re.compile(r"https?://\S+")
QUOTE = re.compile(r"«[^»]{4,}»|“[^”]{4,}”")
PAGE_HINT = re.compile(r"\b(S\.|p\.|pp\.|с\.|side|Band|Kap\.|§)\s*\d", re.I)
# Sources that REPRODUCE another — must name both links.
REPRODUCTION = re.compile(
    r"\b(via|gengivelse|bearbejdede|rework|reproduc|efter|after)\b", re.I)

# C2 — parameter vocabulary, used to spot periods that carry no numbers.
PARAM = re.compile(
    r"\b(karat|carat|lod|‰|tusinddele|stk\.|stück|pieces per|per mark|"
    r"raavægt|rough weight|finvægt|fine weight|fineness|proba|проба)\b", re.I)


def blocks(text: str) -> list[tuple[str, str]]:
    """Split into (heading, body) sections on markdown headings."""
    out, head, buf = [], "(preamble)", []
    for line in text.split("\n"):
        if re.match(r"^#{1,6}\s", line):
            out.append((head, "\n".join(buf)))
            head, buf = line.strip("# ").strip(), []
        else:
            buf.append(line)
    out.append((head, "\n".join(buf)))
    return out


def scan(path: Path) -> int:
    text = path.read_text(encoding="utf-8")
    secs = blocks(text)
    print(f"DOSSIER: {path.relative_to(ROOT)}   ({len(text.splitlines())} lines, "
          f"{len(secs)} sections)\n")

    # C1
    opening = secs[0][1] + (secs[1][1] if len(secs) > 1 else "")
    scope = re.search(r"\b(scope|question|settles|excludes?|out of scope|"
                      r"boundar)\w*", opening, re.I)
    print(f"[C1] scope language in opening: {'found' if scope else 'NOT FOUND'}")

    # C2 — sections that look like a period but carry no parameter vocabulary.
    print("[C2] period-looking sections with no parameter vocabulary:")
    hits = 0
    for head, body in secs:
        if not re.search(r"1[45678]\d\d", head):
            continue
        if not PARAM.search(body):
            print(f"       · {head}")
            hits += 1
    if not hits:
        print("       (none)")

    # C3
    print("[C3] change sentences with no instrument named in the same paragraph:")
    hits = 0
    for para in re.split(r"\n\s*\n", text):
        if CHANGE.search(para) and not INSTRUMENT.search(para):
            first = para.strip().split("\n")[0][:88]
            print(f"       · {first}")
            hits += 1
            if hits >= 12:
                print("       … (truncated)")
                break
    if not hits:
        print("       (none)")

    # C4
    urls = URL.findall(text)
    quotes = QUOTE.findall(text)
    pages = PAGE_HINT.findall(text)
    repro = REPRODUCTION.findall(text)
    print(f"[C4] {len(urls)} URLs · {len(quotes)} guillemet/curly quotes · "
          f"{len(pages)} page hints · {len(repro)} reproduction markers")
    if urls and len(quotes) < len(urls) / 2:
        print("       ! fewer quotes than half the URLs — check §5a compliance")

    # C5
    print("[C5] speculation words with no hedge label in the same paragraph:")
    hits = 0
    for para in re.split(r"\n\s*\n", text):
        if SPECULATION.search(para) and not HEDGE_LABEL.search(para):
            first = para.strip().split("\n")[0][:88]
            print(f"       · {first}")
            hits += 1
            if hits >= 12:
                print("       … (truncated)")
                break
    if not hits:
        print("       (none)")
    openq = re.search(r"\b(open question|still open|unresolved|відкрит)\w*",
                      text, re.I)
    print(f"       open-questions section: {'present' if openq else 'NOT FOUND'}")

    # C6
    recomp = re.search(r"\b(recomput|re-deriv|reproduc\w+ (the|his|its) figure|"
                       r"independently|our own data|our data|перерахув)\w*",
                       text, re.I)
    print(f"[C6] recomputation language: {'found' if recomp else 'NOT FOUND'}")
    print(f"     data/v2 references: {len(re.findall(r'data/v2/', text))}")

    print("\nSignals are candidates. Verify each against the text before scoring.")
    return 0


def main() -> int:
    args = [a for a in sys.argv[1:]]
    if not args or args[0] == "--list":
        # top-level dossiers + per-instrument dossiers; `sources/` holds
        # verbatim captures, not dossiers, and is left out on purpose.
        files = sorted(RESEARCH.glob("*.md")) + sorted((RESEARCH / "instruments").glob("*.md"))
        for p in files:
            name = str(p.relative_to(RESEARCH))
            print(f"  {name:52} {len(p.read_text(encoding='utf-8').splitlines()):5} lines")
        return 0
    p = Path(args[0])
    if not p.is_absolute():
        p = ROOT / p
    if not p.exists():
        print(f"no such dossier: {p}")
        return 2
    return scan(p)


if __name__ == "__main__":
    raise SystemExit(main())
