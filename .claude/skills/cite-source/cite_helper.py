#!/usr/bin/env python3
"""cite_helper — lint refs_pool entries and the prose that cites them.

Candidates, not verdicts: every flag is to be checked against the entry and
the source before anything is changed (CLAUDE.md §0b).

  cite_helper.py KEY [KEY ...]                 lint these pool keys
  cite_helper.py --fuss nobel_fod              keys + prose quotes of one Fuß
        [--location denmark]                   (fuesse.yml block + the location's
                                                fuss_periods / phases for that Fuß)
  cite_helper.py --page site-danskmoent/uk/index.html --section fuss-nobel_fod
                                               keys cited in one rendered section
                                               (incl. its lazy part t/<fuss>.html)
  cite_helper.py --usage KEY                   every prose line citing KEY
  cite_helper.py --work "Wilcke%207-2"         every key whose text contains STR
"""
from __future__ import annotations

import argparse
import html as _html
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[3]
POOL = ROOT / "data/shared/refs_pool.yml"
LANGS = ("de", "en", "uk", "da")
TR_MARK = {"de": r"\(dt\.:", "en": r"\(transl\.:", "uk": r"\(перекл\.:", "da": r"\(overs\.:"}
PAGE_RE = {"de": r"\bS\. ?[0-9ivxlcIVXLC]", "en": r"\bpp?\. ?[0-9ivxlcIVXLC]",
           "uk": r"\bс\. ?[0-9ivxlcIVXLC]", "da": r"\bs\. ?[0-9ivxlcIVXLC]"}
QUOTE_RE = re.compile(r"«<i>(.*?)</i>»", re.S)
LINK_RE = re.compile(r'<a href="([^"]+)"([^>]*)>')
REF_RE = re.compile(r"\[ref:([a-z0-9][a-z0-9-]*)\]")

# Distinctive function words per language (shared ones like «de», «en» left out).
LEX = {
    "da": "og af er det til paa på ikke blev skulde hvilket aar saa fra eller kun dog hans "
          "denne disse var har ogsaa også efter nu mønt guld",
    "en": "the of and is was to it that not with this for by as were which",
    "fr": "le la les du des au une fut que est ce sens au d l un",
    "nl": "het van een werd uit dat voor zijn geslagen munt munten worden moest wordt",
    "de": "der die das und nicht mit von zu dem aus wurde ist sich auch",
    "la": "et in est ad cum non per quod",
}
LEX = {k: set(v.split()) for k, v in LEX.items()}


def quote_lang(q: str) -> str:
    words = re.findall(r"[a-zæøåäöüéèêàç']+", q.lower().replace("’", "'"))
    words = [w.split("'")[-1] for w in words]
    score = {l: sum(w in s for w in words) for l, s in LEX.items()}
    best = max(score, key=score.get)
    ranked = sorted(score.values(), reverse=True)
    if ranked[0] == 0 or (len(ranked) > 1 and ranked[0] == ranked[1]):
        return "?"
    return best


def load_pool() -> dict:
    return yaml.safe_load(POOL.read_text())


def norm(q: str) -> list[str]:
    q = re.sub(r"<[^>]+>", "", q)
    q = re.sub(r"[…\[\]().,;:«»\"']", " ", q.lower())
    return q.split()


def overlaps(pool: dict, key: str) -> list[str]:
    """Other keys whose da/de quote shares a run of >= 7 words with KEY's."""
    def qs(k):
        e = pool.get(k) or {}
        s = e.get("da") or e.get("de") or ""
        return [norm(m) for m in QUOTE_RE.findall(s)]
    def url(k):
        m = LINK_RE.search((pool.get(k) or {}).get("da") or (pool.get(k) or {}).get("de") or "")
        return m.group(1) if m else None
    mine = qs(key)
    grams = {tuple(w[i:i + 7]) for w in mine for i in range(len(w) - 6)}
    if not grams:
        return []
    hits = []
    for k in pool:
        if k == key or not isinstance(pool[k], dict):
            continue
        # one passage = one key is about ONE work: the same wording on two
        # different pages (danskmoent repeats a description across coin pages)
        # is two passages, not an overlap.
        if url(k) and url(key) and url(k) != url(key):
            continue
        for w in qs(k):
            if any(tuple(w[i:i + 7]) in grams for i in range(len(w) - 6)):
                hits.append(k)
                break
    return hits


def lint(pool: dict, key: str) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    e = pool.get(key)
    if not isinstance(e, dict):
        return [("high", "key not in refs_pool")]
    for l in LANGS:
        if not (e.get(l) or "").strip():
            out.append(("high", f"{l}: missing language"))
    texts = {l: e.get(l) or "" for l in LANGS}
    base = texts["da"] or texts["de"]
    quotes = QUOTE_RE.findall(base)
    if not quotes:
        out.append(("high", "no verbatim «<i>…</i>» quote"))
    # same quotes in every language
    qsets = {l: QUOTE_RE.findall(t) for l, t in texts.items() if t}
    if len({tuple(v) for v in qsets.values()}) > 1:
        out.append(("medium", "quotes differ between languages: "
                    + ", ".join(f"{l}={len(v)}" for l, v in qsets.items())))
    # translations
    for q in quotes:
        ql = quote_lang(q)
        short = re.sub(r"<[^>]+>", "", q)[:50]
        if ql == "?":
            out.append(("low", f"quote language not detected — check translations by hand: «{short}…»"))
            continue
        for l in LANGS:
            t = texts[l]
            if not t:
                continue
            idx = t.find(q)
            after = t[idx + len(q):] if idx >= 0 else ""
            has = re.search(TR_MARK[l], after) is not None
            if l == ql and has:
                out.append(("low", f"{l}: quote is already {ql}, translation not needed: «{short}…»"))
            if l != ql and not has:
                out.append(("high", f"{l}: {ql} quote without translation ({TR_MARK[l].replace(chr(92), '')[1:]} …): «{short}…»"))
        n = len(norm(q))
        if n > 32:
            out.append(("low", f"quote ~{n} words (guideline ~25): «{short}…»"))
    # labels
    for l, t in texts.items():
        if re.search(r"(Verbatim|Ordret|Wörtlich|Дослівно|Цитата)\s*:\s*«", t):
            out.append(("low", f"{l}: label before the quote"))
    # title identical across languages
    titles = {l: (re.search(r"<i>(.*?)</i>", t) or [None, None])[1] for l, t in texts.items() if t}
    if len(set(titles.values())) > 1:
        out.append(("low", "first <i>title</i> differs between languages (titles stay original): "
                    + " | ".join(f"{l}={v}" for l, v in titles.items())))
    # links
    for l, t in texts.items():
        links = LINK_RE.findall(t)
        for href, attrs in links:
            if 'target="_blank"' not in attrs:
                out.append(("low", f"{l}: link without target=_blank: {href}"))
        live = [h for h, _ in links if "web.archive.org" not in h]
        if live and "web.archive.org" not in t:
            out.append(("medium", f"{l}: no archive copy for {live[0]}"))
    # page hint
    # Page hint is required for a paginated work we read (a PDF / scan). A web
    # reproduction of a print work is cited as what was read: the quote is the
    # locator (curator 2026-10-12), so an .htm reproduction is not flagged.
    links = [h for h, _ in LINK_RE.findall(base) if "web.archive.org" not in h]
    paginated = any(h.lower().split("#")[0].endswith(".pdf") for h in links) or \
        (not links and re.search(r"Årsskrift|Aarsskrift|Jaarboek|Bd\.|bd\.|vol\.", base))
    if paginated:
        for l, t in texts.items():
            if t and not re.search(PAGE_RE[l], t) and not re.search(r"Lot \d", t):
                out.append(("high", f"{l}: paginated work without page hint"))
    for k in overlaps(pool, key):
        out.append(("high", f"quote overlaps the passage of {k} (one passage = one key)"))
    return out


def prose_strings(node, lang=None, path=""):
    if isinstance(node, dict):
        for k, v in node.items():
            yield from prose_strings(v, k if k in LANGS else lang, f"{path}.{k}")
    elif isinstance(node, list):
        for i, v in enumerate(node):
            yield from prose_strings(v, lang, f"{path}[{i}]")
    elif isinstance(node, str) and lang:
        yield lang, path, node


def prose_quote_issues(lang: str, s: str) -> list[str]:
    out = []
    for m in QUOTE_RE.finditer(s):
        q = m.group(1)
        ql = quote_lang(q)
        tail = s[m.end():m.end() + 6]
        has = tail.lstrip().startswith("(«") or tail.lstrip().startswith("(„")
        if ql not in ("?", lang) and not has:
            out.append(f"{ql} quote without («translation»): «{re.sub(r'<[^>]+>', '', q)[:50]}…»")
        if ql == "?" and not has and lang != "da":
            out.append(f"quote of undetected language, no translation: «{re.sub(r'<[^>]+>', '', q)[:50]}…»")
    return out


def fuss_blocks(fuss: str, location: str | None):
    f = yaml.safe_load((ROOT / "data/shared/fuesse.yml").read_text())
    f = f.get("fuesse", f)
    yield f"fuesse.yml::{fuss}", f.get(fuss) or {}
    if location:
        loc = yaml.safe_load((ROOT / f"data/v2/locations/{location}.yml").read_text())
        yield f"{location}.yml::fuss_periods.{fuss}", (loc.get("fuss_periods") or {}).get(fuss) or {}
        phases = loc.get("phases") or {}
        if isinstance(phases, dict):            # V2 locations: {fuss: [phase, …]}
            for i, ph in enumerate(phases.get(fuss) or []):
                yield f"{location}.yml::phases.{fuss}[{i}]", ph
        else:
            for i, ph in enumerate(phases):
                if isinstance(ph, dict) and ph.get("fuss") == fuss:
                    yield f"{location}.yml::phases[{i}]", ph
        for b in ((loc.get("timeline") or {}).get("bars") or []):
            if isinstance(b, dict) and fuss in (b.get("id"), b.get("fuss")):
                yield f"{location}.yml::timeline.bars[{b.get('id')}]", b


def page_keys(page: Path, section: str) -> list[str]:
    h = page.read_text()
    ids = [(m.start(), m.group(1)) for m in re.finditer(r'<section[^>]*id="([^"]+)"', h)]
    start = next(p for p, i in ids if i == section)
    nxt = [p for p, i in ids if p > start]
    chunk = h[start:nxt[0] if nxt else len(h)]
    if section.startswith("fuss-"):
        lazy = page.parent / "t" / f"{section[5:]}.html"
        if lazy.exists():
            chunk += lazy.read_text()
    order: dict[str, int] = {}
    for k, n in re.findall(r'href="#ref-pool-([a-z0-9-]+)"[^>]*>\[(\d+)\]', chunk):
        order.setdefault(k, int(n))
    return sorted(order, key=order.get)


def usage(key: str) -> None:
    for f in sorted((ROOT / "data").rglob("*.yml")):
        if f.name == "refs_pool.yml":
            continue
        for i, line in enumerate(f.read_text().split("\n"), 1):
            for m in re.finditer(re.escape(f"[ref:{key}]"), line):
                lang = line.strip().split(":", 1)[0]
                ctx = re.sub(r"<[^>]+>", "", _html.unescape(line[max(0, m.start() - 400):m.start()]))
                print(f"{f.relative_to(ROOT)}:{i} [{lang}] …{ctx[-160:]}")


def report(pool, keys):
    total = 0
    for n, k in enumerate(keys, 1):
        issues = lint(pool, k)
        total += len(issues)
        if issues:
            print(f"{n:>3}  {k}")
            for prio, msg in sorted(issues, key=lambda x: ("high", "medium", "low").index(x[0])):
                print(f"       [{prio}] {msg}")
    print(f"--- {len(keys)} keys, {total} candidate issue(s)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("keys", nargs="*")
    ap.add_argument("--fuss")
    ap.add_argument("--location")
    ap.add_argument("--page")
    ap.add_argument("--section")
    ap.add_argument("--usage")
    ap.add_argument("--work")
    a = ap.parse_args()
    pool = load_pool()
    if a.usage:
        usage(a.usage)
        return
    if a.work:
        for k, e in pool.items():
            if isinstance(e, dict) and any(a.work in (e.get(l) or "") for l in LANGS):
                q = QUOTE_RE.findall(e.get("da") or e.get("de") or "")
                print(k, "::", re.sub(r"<[^>]+>", "", q[0])[:90] if q else "(no quote)")
        return
    if a.page:
        keys = page_keys(ROOT / a.page, a.section)
        print(f"SECTION {a.section} — {len(keys)} keys (in display order)")
        report(pool, keys)
        return
    if a.fuss:
        keys: list[str] = []
        for label, block in fuss_blocks(a.fuss, a.location):
            for lang, path, s in prose_strings(block):
                for k in REF_RE.findall(s):
                    if k not in keys:
                        keys.append(k)
                for msg in prose_quote_issues(lang, s):
                    print(f"PROSE {label}{path} [{lang}]: {msg}")
        missing = [k for k in keys if k not in pool]
        for k in missing:
            print(f"UNRESOLVED [ref:{k}]")
        report(pool, [k for k in keys if k in pool])
        return
    if not a.keys:
        ap.print_help()
        sys.exit(1)
    report(pool, a.keys)


if __name__ == "__main__":
    main()
