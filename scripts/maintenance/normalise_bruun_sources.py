"""Rewrite all Bruun catalog citations to a single canonical form.

Background
==========

Two Bruun source formats existed in V2 data:

  OLD: `{type: literature, ref: "Bruun-<coll_id> · Stack's Bowers Bruun
         Collection Part <N>, lot <lot_no>"}`  — no URL, no page,
         redundant collection-id baked into the ref text. Emitted by an
         older revision of `build_bruun_denmark_seed.py`.

  NEW: `{type: auction, url: <part-PDF-URL>,
         ref: "Bruun Part <N>, lot <lot_no>, p. <page>"}` — concise,
         per-part PDF URL, lot + page locator. Emitted by the current
         builder (`_build_bruun_source` in `build_bruun_denmark_seed.py`),
         and matches the format curators have been hand-writing in
         `data/locations/<loc>.yml::sources`.

Side-effect: entries that were merged from BOTH a curator-hand source
(new format) AND a Bruun seed merge (old format) ended up with TWO
Bruun source entries for the same physical lot — visually a duplicate
ref line on the rendered page. Curator flagged 2026-05-27.

What this script does
=====================

Scans V2 final + V2 seed_unified + V2 per-source seed yamls. For each
source entry whose ref-text matches the OLD-format regex:

  1. Parses out part (roman numeral) + lot_no + collection_id.
  2. Looks up the canonical PDF URL from the matching `_BRUUN_PART_PDF_URL`.
  3. Looks up the page number on the SAME coin entry (from
     `catalog.bruun_page` when set, otherwise from the matching Bruun
     parser cache `scripts/cache/bruun/lots/part<N>.json`).
  4. Rewrites the source as:
       `{type: auction, url: <PDF URL>, ref: "Bruun Part <N>, lot
        <lot_no>, p. <page>"}`
  5. Drops it if a same-shape entry already exists on the same coin
     (dedupe pass).

Idempotent — re-running on already-normalised data is a no-op.

Run:
    python scripts/maintenance/normalise_bruun_sources.py [--dry-run]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from ruamel.yaml import YAML

PROJECT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT / "scripts"))
from maintenance.build_bruun_denmark_seed import (  # noqa: E402
    _BRUUN_PART_PDF_URL, _BRUUN_PART_ROMAN,
)


# Targets to scan (all V2 layers + ALSO V1 entity / location files when
# present — V1 SH yaml has the same OLD-format problem on a few entries).
TARGET_GLOBS = [
    "data/v2/final/*.yml",
    "data/v2/seed_unified/*.yml",
    "data/v2/seed/bruun/*.yml",
]


# OLD-format ref-text:
# «Bruun-7837 · Stack's Bowers Bruun Collection Part III, lot 11292»
# Also tolerate slight variants (curly apostrophe, en-dash) seen in the
# wild.
_OLD_BRUUN_REF_RE = re.compile(
    r"^Bruun-(\d+)\s*[·•]\s*"          # «Bruun-7837 ·»
    r"Stack[''’]s Bowers Bruun Collection\s+"
    r"Part\s+([IVX]+),?\s+lot\s+(\d+)"  # «Part III, lot 11292»
    r"\s*$"
)

# Page-number lookup caches from the parser output. Two indexes
# keyed on different identifiers, since legacy refs reference by
# collection-id («Bruun-7837») while canonical-form refs reference by
# (part, lot_no). Both lookups go to the SAME source-of-truth — the
# parser's page extraction in `scripts/cache/bruun/lots/part*.json`.
_PAGE_BY_COLL: dict[str, int] | None = None
_PAGE_BY_PART_LOT: dict[tuple[int, int], int] | None = None


def _load_page_caches() -> tuple[dict[str, int], dict[tuple[int, int], int]]:
    global _PAGE_BY_COLL, _PAGE_BY_PART_LOT
    if _PAGE_BY_COLL is not None and _PAGE_BY_PART_LOT is not None:
        return _PAGE_BY_COLL, _PAGE_BY_PART_LOT
    by_coll: dict[str, int] = {}
    by_part_lot: dict[tuple[int, int], int] = {}
    for part_n in (1, 2, 3, 4):
        p = PROJECT / "scripts" / "cache" / "bruun" / "lots" / f"part{part_n}.json"
        if not p.exists():
            continue
        for lot in json.loads(p.read_text(encoding="utf-8")):
            page_span = lot.get("page_span") or []
            page = page_span[0] if page_span else lot.get("page")
            if not page:
                continue
            coll = str((lot.get("refs") or {}).get("Bruun", "")).strip()
            if coll:
                by_coll[coll] = int(page)
            lot_no = lot.get("lot_no")
            if isinstance(lot_no, int):
                by_part_lot[(part_n, lot_no)] = int(page)
    _PAGE_BY_COLL = by_coll
    _PAGE_BY_PART_LOT = by_part_lot
    return by_coll, by_part_lot


def _load_page_cache() -> dict[str, int]:
    """Backward-compat alias for the coll-id cache."""
    return _load_page_caches()[0]


def _roman_to_part(roman: str) -> int | None:
    try:
        return _BRUUN_PART_ROMAN.index(roman) + 1
    except ValueError:
        return None


def _canonical_source(part: int, lot_no: int, page: int | None) -> dict:
    """Build the canonical source entry for given part + lot + page."""
    romnum = _BRUUN_PART_ROMAN[part - 1]
    page_str = f", p. {page}" if page else ""
    return {
        "type": "auction",
        "url": _BRUUN_PART_PDF_URL[part],
        "ref": f"Bruun Part {romnum}, lot {lot_no}{page_str}",
    }


_CANONICAL_BRUUN_REF_RE = re.compile(
    r"^Bruun Part ([IVX]+), lot (\d+)(?:, p\. (\d+))?$"
)


def _normalise_coin_sources(
    coin: dict,
    page_by_coll: dict[str, int],
    page_by_part_lot: dict[tuple[int, int], int],
) -> tuple[int, int]:
    """Rewrite OLD-format Bruun sources on a coin; correct wrong pages on
    canonical-form entries; dedupe duplicates.

    Returns (n_rewritten, n_deduped) — counts of source-entry rewrites
    (OLD-format → canonical, or canonical-with-wrong-page →
    canonical-with-cache-page) and post-rewrite dedupe drops.
    """
    sources = coin.get("sources")
    if not isinstance(sources, list) or not sources:
        return 0, 0
    n_rewrite = 0
    new_sources: list[dict] = []
    for s in sources:
        if not isinstance(s, dict):
            new_sources.append(s)
            continue
        ref = str(s.get("ref") or "")
        ref_str = ref.strip()

        # Pass 1: rewrite LEGACY format «Bruun-7837 · Stack's Bowers ...»
        m = _OLD_BRUUN_REF_RE.match(ref_str)
        if m:
            coll_id, roman, lot_no_str = m.group(1), m.group(2), m.group(3)
            part = _roman_to_part(roman)
            if part is None:
                new_sources.append(s)
                continue
            try:
                lot_no = int(lot_no_str)
            except ValueError:
                new_sources.append(s)
                continue
            # Per-collection-id page lookup. Falls back to (part, lot_no)
            # if coll_id is unknown (rare — happens when the coll_id in
            # legacy text is malformed).
            page = page_by_coll.get(coll_id) or page_by_part_lot.get((part, lot_no))
            new_sources.append(_canonical_source(part, lot_no, page))
            n_rewrite += 1
            continue

        # Pass 2: correct canonical-form entries with a stale/wrong page.
        # Looks up the authoritative page from the parser cache by
        # (part_roman → part, lot_no). When the entry's page differs
        # from the cache page, rewrite. When the entry has no page but
        # the cache does, fill it in. When the cache has nothing,
        # leave the entry untouched.
        m = _CANONICAL_BRUUN_REF_RE.match(ref_str)
        if m:
            roman, lot_no_str, page_str = m.group(1), m.group(2), m.group(3)
            part = _roman_to_part(roman)
            try:
                lot_no = int(lot_no_str)
            except ValueError:
                part = None
            if part is None:
                new_sources.append(s)
                continue
            cache_page = page_by_part_lot.get((part, lot_no))
            entry_page = int(page_str) if page_str else None
            if cache_page is None:
                # No authoritative page — keep entry as-is.
                new_sources.append(s)
                continue
            if entry_page == cache_page:
                new_sources.append(s)
                continue
            # Rewrite to canonical with cache page.
            new_sources.append(_canonical_source(part, lot_no, cache_page))
            n_rewrite += 1
            continue

        # Non-Bruun source — keep as-is.
        new_sources.append(s)

    # Dedupe pass. After all rewrites are done above, every Bruun ref
    # is in canonical form with the cache-correct page. Dedupe is
    # therefore safe to do by exact (part_roman, lot_no) — the page
    # will match on collision.
    by_lot: dict[tuple[str, str], dict] = {}
    n_dedupe = 0
    out: list[dict] = []
    seen_sigs: set[tuple] = set()
    for s in new_sources:
        if isinstance(s, dict):
            ref = s.get("ref") or ""
            m = _CANONICAL_BRUUN_REF_RE.match(ref.strip()) if isinstance(ref, str) else None
            if m:
                key = (m.group(1), m.group(2))
                if key in by_lot:
                    n_dedupe += 1
                    continue
                by_lot[key] = s
            # Strict (url, ref, type) dedupe — guards against literal
            # duplicates in non-Bruun sources too.
            sig = (s.get("url") or "", s.get("ref") or "", s.get("type") or "")
            if sig in seen_sigs:
                n_dedupe += 1
                continue
            seen_sigs.add(sig)
        out.append(s)

    if n_rewrite or n_dedupe:
        coin["sources"] = out
    return n_rewrite, n_dedupe


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true",
                    help="Report what would change without writing files")
    args = ap.parse_args()

    page_by_coll, page_by_part_lot = _load_page_caches()
    if not page_by_coll:
        print("WARNING: no Bruun parser cache loaded — page lookups disabled.",
              file=sys.stderr)

    y = YAML()
    y.preserve_quotes = True
    y.width = 4096
    y.indent(mapping=2, sequence=4, offset=2)

    grand = {"files": 0, "files_changed": 0,
             "rewrites": 0, "dedupes": 0}
    for pattern in TARGET_GLOBS:
        for path in sorted(PROJECT.glob(pattern)):
            grand["files"] += 1
            with path.open() as f:
                doc = y.load(f)
            if not isinstance(doc, dict):
                continue
            coins = doc.get("coins")
            if not isinstance(coins, list):
                continue
            n_rewrite_file = 0
            n_dedupe_file = 0
            for coin in coins:
                if not isinstance(coin, dict):
                    continue
                r, d = _normalise_coin_sources(coin, page_by_coll, page_by_part_lot)
                n_rewrite_file += r
                n_dedupe_file += d
            if n_rewrite_file or n_dedupe_file:
                grand["files_changed"] += 1
                grand["rewrites"] += n_rewrite_file
                grand["dedupes"] += n_dedupe_file
                rel = path.relative_to(PROJECT)
                print(f"  {rel}: rewrites={n_rewrite_file} dedupes={n_dedupe_file}")
                if not args.dry_run:
                    with path.open("w") as f:
                        y.dump(doc, f)
    print()
    print(f"Files scanned:      {grand['files']}")
    print(f"Files changed:      {grand['files_changed']}")
    print(f"Ref-rewrites total: {grand['rewrites']}")
    print(f"Dedupes total:      {grand['dedupes']}")
    if args.dry_run:
        print("(dry-run — no files written)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
