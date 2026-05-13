#!/usr/bin/env python3
"""audit_refs_page_hints — enforce CLAUDE.md §5a «Mandatory page hints».

Walks every `data/locations/*-references.yml` + `data/shared/*-references.yml`
file. For each `entries[].content.de` (and en/uk) field whose ref body
points at a long-form work (≥ 10 pages by heuristic — see LONGFORM_PATTERN
below) AND the scope-note carries NO literal page reference, emit a
flag.

Per CLAUDE.md §5a (clarified 2026-05-13):

- Long-form refs WITH URL → page hint required in scope note.
- Long-form refs WITHOUT URL (paper-only) → page hint required, same
  rule, no exemption. Paper-only refs without a digital secondary
  carrying a page citation are bad citations by construction.

The script flags both cases identically. Resolution per case: find the
page (via secondary source or digital scan) and add it, OR drop the
ref entirely if no page can be sourced.

Usage::

    .venv/bin/python scripts/audit_refs_page_hints.py
    .venv/bin/python scripts/audit_refs_page_hints.py --json

Exit codes: 0 = clean (no missing page hints), 1 = at least one flag.
"""
from __future__ import annotations

import argparse
import glob
import json
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("PyYAML required. Install via .venv/bin/pip install pyyaml", file=sys.stderr)
    sys.exit(2)

ROOT = Path(__file__).resolve().parent.parent

# A ref points at a long-form work when its content carries one of these
# signals. Match against the de/en text body.
LONGFORM_PATTERN = re.compile(
    r"""(?xi)
    archive\.org           # archive.org book scan
    | wikisource\.org      # Wikisource per-page transcription
    | elexikon\.ch         # Meyers eLexikon (multi-volume work)
    | \.pdf                # any direct PDF link
    | \bdanskmoent\.dk/artikler/   # NNUM long-form articles
    | \bzeno\.org          # zeno.org (multi-volume encyclopaedias)
    | \bdeutsche-biographie # ADB / NDB (multi-volume biographical dict)
    | Verlag\b             # any book published with named publisher (paper-only signal)
    | \bMonographie?\b
    | \bBerlin \d{4}\b     # «Berlin 1905» style paper citation
    | \bLeipzig \d{4}\b
    | \bHamburg \d{4}\b
    | \bKopenhagen \d{4}\b
    | \bMünchen \d{4}\b
    """
)

# Page-hint signals (presence of any = ref is properly cited).
PAGE_HINT_PATTERN = re.compile(
    r"""(?xi)
    \bS\.\s*\d                 # «S. 14» / «S. 113-114»
    | \bp{1,2}\.\s*\d          # «p. 113» / «pp. 113-114»
    | \bBand\s*\d              # «Band 11»
    | \bBd\.\s*\d              # «Bd. 11»
    | \bKap\.\s*\d             # «Kap. 4»
    | \bChapter\s*\d           # «Chapter 4»
    | \bRozd[іi]l\s*\d         # «Розділ 4»
    | \b§\s*\d                 # «§ 5»
    | \bстор\.\s*\d            # «стор. 14»
    | \bс\.\s*\d               # «с. 14»
    """
)

# Wiki-only refs (no print original) exception: section anchor instead of
# page hint. Pure Wikipedia article without «MKL 1888, Band N» style cross-
# reference is OK without page hint.
WIKI_ONLY_PATTERN = re.compile(
    r"""(?xi)
    ^(?!.*\b(?:S|p|pp|Band|Bd|Kap|§)\.?\s*\d)
    .*wikipedia\.org
    """,
    re.DOTALL,
)


def is_longform(text: str) -> bool:
    return bool(LONGFORM_PATTERN.search(text))


def has_page_hint(text: str) -> bool:
    return bool(PAGE_HINT_PATTERN.search(text))


def is_wiki_only(text: str) -> bool:
    """Pure Wikipedia article without print original — exempt per §5a."""
    return bool(WIKI_ONLY_PATTERN.match(text))


def scan_file(path: Path) -> list[dict]:
    """Return list of flag dicts for refs in this file missing page hints."""
    with path.open() as f:
        doc = yaml.safe_load(f) or {}
    items = doc.get("entries") or doc.get("references") or doc.get("items") or []
    flags = []
    for ref in items:
        if not isinstance(ref, dict):
            continue
        rid = ref.get("id", "?")
        content = ref.get("content") or {}
        if not isinstance(content, dict):
            continue
        # Combine de+en+uk to catch the page hint in any language.
        joined = " ".join(
            (content.get(k) or "") for k in ("de", "en", "uk")
        )
        if not joined.strip():
            continue
        if not is_longform(joined):
            continue
        if has_page_hint(joined):
            continue
        if is_wiki_only(joined):
            continue
        # Pull a short snippet for the report
        de = content.get("de") or content.get("en") or content.get("uk") or ""
        snippet = re.sub(r"\s+", " ", de).strip()[:140]
        flags.append({
            "file": path.name,
            "ref_id": rid,
            "snippet": snippet,
        })
    return flags


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--json", action="store_true", help="JSON output")
    args = ap.parse_args()

    paths = sorted(
        list((ROOT / "data" / "locations").glob("*-references.yml"))
        + list((ROOT / "data" / "shared").glob("*-references.yml"))
    )
    all_flags: list[dict] = []
    for p in paths:
        all_flags.extend(scan_file(p))

    if args.json:
        print(json.dumps({"flags": all_flags, "count": len(all_flags)},
                         indent=2, ensure_ascii=False))
    else:
        if not all_flags:
            print("✓ All long-form refs carry a page hint.")
        else:
            print(f"⚠ {len(all_flags)} ref(s) missing page hint:")
            for f in all_flags:
                print(f"  - {f['file']}::{f['ref_id']}")
                print(f"    {f['snippet']}")
    return 1 if all_flags else 0


if __name__ == "__main__":
    sys.exit(main())
