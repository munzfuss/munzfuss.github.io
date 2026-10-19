#!/usr/bin/env python3
"""Audit refs_pool page hints against the kb index (read-only report).

For every work in scripts/cache/_corpus.yml whose passages carry an
established PRINTED page, take each refs_pool key the work's refs_match
finds, read the key's verbatim quote (the first «<i>…</i>» of the da field,
which carries the original wording) and its claimed page(s) («s. N» /
«s. N–M» outside the quote), then score every passage of the work by the
share of the quote's words it contains.

Verdicts
  ok        a claimed page carries the quote as well as the best page does
  MISMATCH  the quote sits clearly better on another page (or volume)
  weak      no passage carries ≥ 60 % of the quote's words — OCR damage,
            a quote from a table, or a quote that is not in this work;
            no verdict on the page
  no-page   the key gives no page (allowed for unpaginated reproductions)

A MISMATCH is a candidate, not a finding: open the page image before any
fix (CLAUDE.md §0b), and every fix goes through the cite-source skill.
"""
from __future__ import annotations

import argparse
import re
import sqlite3
import sys
from collections import defaultdict
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
import kb  # noqa: E402

_QUOTE = re.compile(r"«<i>(.*?)</i>»", re.S)
_PAGE = re.compile(r"\b[sS]\.\s*(\d+)(?:\s*[–-]\s*(\d+))?")
_ROMAN = {"I": 1, "II": 2, "III": 3, "IV": 4, "V": 5, "VI": 6, "VII": 7}


def quote_and_pages(entry: dict) -> tuple[str | None, set[int]]:
    s = entry.get("da") or entry.get("de") or ""
    qs = _QUOTE.findall(s)
    quote = qs[0] if qs else None
    outside = _QUOTE.sub(" ", s)
    pages: set[int] = set()
    for a, b in _PAGE.findall(outside):
        a = int(a)
        b = int(b) if b else a
        if b < a:  # «s. 261–62»
            b = int(str(a)[: len(str(a)) - len(str(b))] + str(b))
        if 0 <= b - a <= 20:
            pages.update(range(a, b + 1))
    return quote, pages


def claimed_volume(key: str, entry: dict, work: dict) -> str | None:
    """Volume the key cites, for multi-volume works (Secher: key secher-ccd-N-…)."""
    m = re.match(r"secher-ccd-(\d+)-", key)
    if m and work["id"] == "secher-ccd":
        return m.group(1)
    m = re.search(r"-p(\d)-", key)
    if m and work["id"] == "bruun-sb-2024-2026":
        return {v: k for k, v in _ROMAN.items()}[int(m.group(1))]
    return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=str(kb.DB_DEFAULT))
    ap.add_argument("--work", action="append")
    ap.add_argument("--all", action="store_true", help="print ok rows too")
    args = ap.parse_args()
    con = sqlite3.connect(args.db)
    pool = yaml.safe_load(kb.REFS_POOL.read_text(encoding="utf-8"))
    counts: dict[str, int] = defaultdict(int)
    print("| verdict | key | claimed | best page (share) | claimed share | volume |")
    print("|---|---|---|---|---|---|")
    for w in kb.load_manifest()["works"]:
        if args.work and w["id"] not in args.work:
            continue
        rows = con.execute("SELECT volume, printed, text FROM passage WHERE work=? AND printed IS NOT NULL",
                           (w["id"],)).fetchall()
        if not rows:
            continue
        rows = [(v, pr, set(kb._TOKEN.findall(kb.normalize(t)))) for v, pr, t in rows]
        for key in kb.refs_keys_for(w, pool):
            quote, pages = quote_and_pages(pool[key])
            if not quote:
                counts["no-quote"] += 1
                continue
            qtok = sorted({t for t in kb.query_terms(quote) if len(t) >= 4 and not t.isdigit()})
            if len(qtok) < 3:
                counts["short"] += 1
                continue
            vol = claimed_volume(key, pool[key], w)
            share: dict[tuple, float] = defaultdict(float)
            for volume, printed, toks in rows:
                sh = sum(1 for t in qtok if t in toks) / len(qtok)
                k = (volume or "", printed)
                share[k] = max(share[k], sh)
            (bvol, bpage), best = max(share.items(), key=lambda kv: kv[1])

            def pnums(p):
                m = re.match(r"(\d+)(?:\s*[–-]\s*(\d+))?", p or "")
                if not m:
                    return set()
                a = int(m.group(1))
                return set(range(a, int(m.group(2) or a) + 1))

            if not pages:
                verdict = "no-page"
                cshare = None
            else:
                cand = [sh for (v, p), sh in share.items()
                        if pnums(p) & pages and (vol is None or v == vol)]
                cshare = max(cand, default=0.0)
                if best < 0.6:
                    verdict = "weak"
                elif cshare >= best - 0.1:
                    verdict = "ok"
                else:
                    verdict = "MISMATCH"
            counts[verdict] += 1
            if verdict == "ok" and not args.all:
                continue
            claimed = (f"{min(pages)}–{max(pages)}" if len(pages) > 1 else str(min(pages))) if pages else "—"
            cs = f"{cshare:.2f}" if cshare is not None else "—"
            print(f"| {verdict} | `{key}` | {claimed} | {bpage} ({best:.2f}) | {cs} | "
                  f"{(vol or '') + (' → ' + bvol if vol and bvol != vol else (bvol and ' ' + bvol) or '')} |")
    print()
    print("counts: " + ", ".join(f"{k} {v}" for k, v in sorted(counts.items())))
    return 0


if __name__ == "__main__":
    sys.exit(main())
