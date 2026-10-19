#!/usr/bin/env python3
"""Go/no-go measurement: plain `grep -ri` vs `kb search` on eval_set.yml.

For every case: locate the GOLD passage in the index (the passage of the
target work / page that carries the refs_pool quote), then ask

  grep  — does `grep -rIin -F <keyword>` over the cache (as a researcher runs
          it today, .htm and .txt alike) hit a line inside the gold passage?
          How many matching lines does the researcher have to read?
  kb    — at which rank does `kb search <query>` return the gold passage?

Prints a Markdown table. Read-only; needs `kb.py build` first.
"""
from __future__ import annotations

import argparse
import os
import re
import sqlite3
import subprocess
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
import kb  # noqa: E402

EVAL = Path(__file__).resolve().parent / "eval_set.yml"
GREP_ROOTS = ["secher", "schou", "wilcke", "danskmoent", "munro", "bobzin", "coingallery"]


def quote_of(pool: dict, key: str) -> str:
    entry = pool[key]
    s = entry.get("da") or entry.get("de") or entry.get("en") or ""
    m = re.findall(r"«<i>(.*?)</i>»", s)
    if not m:
        raise SystemExit(f"{key}: no «<i>…</i>» quote in refs_pool")
    return m[0]


def gold_passages(con, case: dict, quote: str) -> list[tuple]:
    rows = con.execute("SELECT id, path, line_start, line_end, printed, text FROM passage WHERE work=?",
                       (case["work"],)).fetchall()
    if "printed" in case:
        rows = [r for r in rows if r[4] in case["printed"]]
    if "path" in case:
        rows = [r for r in rows if case["path"] in r[1]]
    qtok = [t for t in kb.query_terms(quote) if len(t) >= 4 and not t.isdigit()]
    scored = []
    for r in rows:
        toks = set(kb._TOKEN.findall(kb.normalize(r[5])))
        share = sum(1 for t in qtok if t in toks) / max(1, len(qtok))
        scored.append((share, r))
    best = max((s for s, _ in scored), default=0)
    gold = [r for s, r in scored if s >= max(0.5, best - 0.15)]
    probe = re.sub(r"\s+", " ", kb.normalize(str(case["probe"]), join_lines=False))
    gold = [r for r in gold if probe in re.sub(r"\s+", " ", kb.normalize(r[5]))]
    if not gold:
        raise SystemExit(f"{case['key']}: gold passage not found (best quote-token share {best:.2f})")
    return gold


def grep_hits(keyword: str) -> list[tuple[str, int]]:
    env = dict(os.environ, LC_ALL="en_US.UTF-8")
    roots = [str(kb.CACHE / r) for r in GREP_ROOTS]
    out = subprocess.run(["grep", "-rIin", "-F", "--", keyword, *roots],
                         capture_output=True, text=True, env=env, errors="replace").stdout
    hits = []
    for ln in out.splitlines():
        m = re.match(r"(.+?):(\d+):", ln)
        if m:
            hits.append((str(Path(m.group(1)).relative_to(kb.CACHE)), int(m.group(2))))
    return hits


def grep_found(hits, gold) -> bool:
    for _, path, a, b, _, _ in gold:
        if path.startswith("_derived/"):
            raw = path[len("_derived/"):].rsplit(".", 1)[0] + ".htm"
            if any(h[0] == raw for h in hits):
                return True
        elif any(h[0] == path and a <= h[1] <= b for h in hits):
            return True
    return False


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--db", default=str(kb.DB_DEFAULT))
    ap.add_argument("--depth", type=int, default=50, help="kb ranks looked at")
    args = ap.parse_args()
    con = sqlite3.connect(args.db)
    pool = yaml.safe_load(kb.REFS_POOL.read_text(encoding="utf-8"))
    cases = yaml.safe_load(EVAL.read_text(encoding="utf-8"))["cases"]
    print("| # | refs_pool key | query | grep | grep: gold hit | grep: lines / files | kb rank | kb rank (in work) |")
    print("|---|---|---|---|---|---|---|---|")
    stats = {"grep": 0, "kb1": 0, "kb5": 0, "kb10": 0, "kbw1": 0, "kbw10": 0, "kbany": 0,
             "miss_kb10": 0, "miss_kbw10": 0, "hit_kb10": 0}
    for i, c in enumerate(cases, 1):
        gold = gold_passages(con, c, quote_of(pool, c["key"]))
        gids = {r[0] for r in gold}
        hits = grep_hits(c["grep"])
        g = grep_found(hits, gold)
        nfiles = len({h[0] for h in hits})
        rows, _ = kb.search(con, c["query"], limit=args.depth)
        rank = next((n for n, r in enumerate(rows, 1) if r[0] in gids), None)
        rows_w, _ = kb.search(con, c["query"], work=[c["work"]], limit=args.depth)
        rank_w = next((n for n, r in enumerate(rows_w, 1) if r[0] in gids), None)
        stats["grep"] += g
        stats["kb1"] += rank == 1
        stats["kb5"] += bool(rank and rank <= 5)
        stats["kb10"] += bool(rank and rank <= 10)
        stats["kbw1"] += rank_w == 1
        stats["kbw10"] += bool(rank_w and rank_w <= 10)
        stats["kbany"] += bool(rank)
        if g:
            stats["hit_kb10"] += bool(rank and rank <= 10)
        else:
            stats["miss_kb10"] += bool(rank and rank <= 10)
            stats["miss_kbw10"] += bool(rank_w and rank_w <= 10)
        print(f"| {i} | `{c['key']}` | {c['query']} | `{c['grep']}` | {'✅' if g else '❌'} | "
              f"{len(hits)} / {nfiles} | {rank or f'>{args.depth}'} | {rank_w or f'>{args.depth}'} |")
    n = len(cases)
    print(f"\ngrep finds the gold passage in {stats['grep']}/{n} cases.")
    print(f"kb (whole corpus): rank 1 in {stats['kb1']}/{n}, top 5 in {stats['kb5']}/{n}, "
          f"top 10 in {stats['kb10']}/{n}, top {args.depth} in {stats['kbany']}/{n}; "
          f"restricted to the work: rank 1 in {stats['kbw1']}/{n}, top 10 in {stats['kbw10']}/{n}.")
    gm = n - stats["grep"]
    print(f"Of the {gm} cases grep misses, kb has the passage in the top 10 in {stats['miss_kb10']} "
          f"(whole corpus) / {stats['miss_kbw10']} (within the work). Of the {stats['grep']} grep "
          f"finds, kb has it in the top 10 in {stats['hit_kb10']}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
