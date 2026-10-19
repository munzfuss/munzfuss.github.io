#!/usr/bin/env python3
"""Knowledge-base search over the harvested source corpus (PILOT).

Retrieval only. `kb search` returns page-anchored passages — work, PRINTED
page where the corpus manifest establishes one, file path and line — for the
`cite-source` workflow. It never summarises, paraphrases or answers: a hit is
a pointer to text a human (or an agent under CLAUDE.md §0/§0b/§5a) must then
read in full and quote verbatim from the file.

Subcommands
-----------
  extract-htm      danskmoent .htm → plain text under scripts/cache/_derived/
  build            read scripts/cache/_corpus.yml → SQLite FTS5 index
  search QUERY     ranked passages (BM25) with a snippet
  offsets WORK     running-head page-number detection → PDF→printed offset
  refkeys          compare the manifest's refs_pool_keys with refs_pool.yml

Layout
------
  scripts/cache/_corpus.yml          corpus manifest (in the harvest submodule)
  scripts/cache/_derived/danskmoent/ text extracted from danskmoent .htm
  scripts/kb/variants.yml            editable spelling-variant rules
  scripts/kb/_index/kb.sqlite        the index (gitignored, rebuildable)

Run with the project venv: `.venv/bin/python scripts/kb/kb.py …`.
"""
from __future__ import annotations

import argparse
import collections
import glob
import html
import os
import re
import sqlite3
import sys
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[2]
CACHE = REPO / "scripts" / "cache"
MANIFEST = CACHE / "_corpus.yml"
DERIVED = CACHE / "_derived"
VARIANTS = Path(__file__).resolve().parent / "variants.yml"
DB_DEFAULT = Path(__file__).resolve().parent / "_index" / "kb.sqlite"
REFS_POOL = REPO / "data" / "shared" / "refs_pool.yml"

NORMALIZER_VERSION = 4  # bump when normalize() changes; recorded in the db

# ---------------------------------------------------------------------------
# Normalisation
# ---------------------------------------------------------------------------

_FOLD = str.maketrans({
    "æ": "ae", "ø": "oe", "å": "aa", "ä": "ae", "ö": "oe", "ü": "ue",
    "ß": "ss", "ſ": "s", "œ": "oe", "ĳ": "ij", "ꝛ": "r",
    "­": "",  # soft hyphen
})
_HYPHEN_BREAK = re.compile(r"([^\W\d_])[-­¬]\s*\n\s*([^\W\d_])")
# «D e n a r  t i l» — 4+ single letters separated by single spaces
_LETTERSPACED = re.compile(r"(?<!\S)((?:[^\W\d_] ){3,}[^\W\d_])(?!\S)")


def _load_rules(path: Path | None = None) -> list[tuple[re.Pattern, str]]:
    # resolved at call time, so a caller that repoints VARIANTS is honoured
    data = yaml.safe_load((path or VARIANTS).read_text(encoding="utf-8")) or {}
    return [(re.compile(r["pattern"]), r["replace"]) for r in data.get("rules", [])]


_RULES: list[tuple[re.Pattern, str]] | None = None


def normalize(text: str, *, join_lines: bool = True) -> str:
    """Fold case, Nordic/German letters, OCR noise and old spellings.

    Same function for the indexed text and for the query, so every rule is
    symmetric by construction.
    """
    global _RULES
    if _RULES is None:
        _RULES = _load_rules()
    t = unicodedata.normalize("NFC", text)
    if join_lines:
        t = _HYPHEN_BREAK.sub(r"\1\2", t)
    t = _LETTERSPACED.sub(lambda m: m.group(1).replace(" ", ""), t)
    t = t.lower().translate(_FOLD)
    # vulgar fractions: «14¼» → «14 1/4», never the token «141»
    t = re.sub(r"[\u00bc-\u00be\u2150-\u215e]",
               lambda m: " " + unicodedata.normalize("NFKD", m.group(0)).replace("\u2044", "/") + " ", t)
    t = "".join(c for c in unicodedata.normalize("NFKD", t)
                if not unicodedata.combining(c))
    for rx, rep in _RULES:
        t = rx.sub(rep, t)
    return t


# ---------------------------------------------------------------------------
# HTML → text (danskmoent)
# ---------------------------------------------------------------------------

_BLOCK_TAGS = re.compile(
    r"(?i)<\s*(br|/p|p|/div|div|/li|li|/tr|tr|/h[1-6]|h[1-6]|/table|table|/ul|/ol|/blockquote|hr)\b[^>]*>")


def html_to_text(raw: str) -> str:
    s = re.sub(r"(?is)<!--.*?-->", " ", raw)
    s = re.sub(r"(?is)<(script|style|head)\b.*?</\1\s*>", " ", s)
    s = re.sub(r"(?i)</t[dh]\s*>", " \t ", s)
    s = _BLOCK_TAGS.sub("\n", s)
    s = re.sub(r"(?s)<[^>]+>", " ", s)
    s = html.unescape(s).replace("\xa0", " ").replace("\r", "")
    lines = [re.sub(r"[ \t]+", " ", ln).strip() for ln in s.split("\n")]
    out, blank = [], 0
    for ln in lines:
        if ln:
            out.append(ln)
            blank = 0
        elif blank == 0 and out:
            out.append("")
            blank = 1
    return "\n".join(out).strip() + "\n"


def _read_text(path: Path) -> str:
    b = path.read_bytes()
    try:
        return b.decode("utf-8")
    except UnicodeDecodeError:
        return b.decode("cp1252", errors="replace")


def cmd_extract_htm(args) -> int:
    src_root = CACHE / "danskmoent"
    n = changed = 0
    for p in sorted(src_root.rglob("*.htm")):
        rel = p.relative_to(CACHE)
        out = DERIVED / rel.with_suffix(".txt")
        text = html_to_text(_read_text(p))
        header = f"# derived from scripts/cache/{rel} by scripts/kb/kb.py extract-htm\n\n"
        new = header + text
        n += 1
        if not out.exists() or out.read_text(encoding="utf-8") != new:
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(new, encoding="utf-8")
            changed += 1
    print(f"extract-htm: {n} .htm files, {changed} text files written under {DERIVED.relative_to(REPO)}")
    return 0


# ---------------------------------------------------------------------------
# Manifest → passages
# ---------------------------------------------------------------------------

@dataclass
class Passage:
    work: str
    volume: str | None
    path: str                 # relative to scripts/cache
    pdf_page: int | None
    printed: str | None       # printed page / range as a string, None = not established
    locator: str              # human label: «S. 139», «pdf 12», «Side 58-82», «lines 1-40»
    line_start: int           # 1-based, in the file at `path`
    line_end: int
    lang: str
    text: str


def load_manifest(path: Path = MANIFEST) -> dict:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _offset_for(pdf: int, segments: list[dict]) -> int | None:
    for s in segments:
        if s.get("from", 1) <= pdf <= s.get("to", 10**9):
            return s["offset"]
    return None


def _printed_from_offset(pdf: int, spec: dict) -> str | None:
    off = _offset_for(pdf, spec.get("segments", []))
    if off is None:
        return None
    p = pdf + off
    return str(p) if p >= 1 else None


def _chunk_lines(lines: list[str], size: int, start_line: int = 1):
    """Yield (first_line_no, last_line_no, text) windows of ~size non-empty lines."""
    buf, first, count = [], None, 0
    for i, ln in enumerate(lines, start=start_line):
        if first is None:
            first = i
        buf.append(ln)
        if ln.strip():
            count += 1
        if count >= size and not ln.strip():
            yield first, i, "\n".join(buf)
            buf, first, count = [], None, 0
        elif count >= size * 2:
            yield first, i, "\n".join(buf)
            buf, first, count = [], None, 0
    if buf and any(x.strip() for x in buf):
        yield first, start_line + len(lines) - 1, "\n".join(buf)


def _locator(printed: str | None, pdf: int | None, label: str) -> str:
    if printed:
        return f"{label} {printed}"
    if pdf is not None:
        return f"pdf {pdf} (printed page not established)"
    return "unpaginated"


def iter_passages(work: dict):
    wid, lang = work["id"], "+".join(work.get("languages", []))
    page_label = work.get("page_label", "p.")
    for unit in work["text_layers"]:
        layout = unit["layout"]
        vol = unit.get("volume")
        files = sorted(glob.glob(str(CACHE / unit["glob"])))
        if not files:
            print(f"warning: {wid}: no files for {unit['glob']}", file=sys.stderr)
        for f in files:
            fp = Path(f)
            rel = str(fp.relative_to(CACHE))
            text = _read_text(fp)
            lines = text.split("\n")
            if layout == "file-per-page":
                pdf = int(re.sub(r"\D", "", fp.stem) or 0)
                printed = None
                pp = unit.get("printed_page", {})
                if pp.get("method") == "offset":
                    printed = _printed_from_offset(pdf, pp)
                elif pp.get("method") == "label":
                    m = re.match(pp.get("regex", r"\[label (\S+)\]"), lines[0] if lines else "")
                    printed = m.group(1) if m else None
                yield Passage(wid, vol, rel, pdf, printed, _locator(printed, pdf, page_label),
                              1, len(lines), lang, text)
            elif layout in ("markers", "formfeed"):
                pages = []  # (pdf, printed_from_marker, first_line, chunk_lines)
                if layout == "formfeed":
                    ln_no = 1
                    for idx, chunk in enumerate(text.split("\f"), start=1):
                        cl = chunk.split("\n")
                        pages.append((idx, None, ln_no, cl))
                        ln_no += len(cl) - 1
                else:
                    rx = re.compile(unit["marker"])
                    cur = None
                    for i, ln in enumerate(lines, start=1):
                        m = rx.match(ln)
                        if m:
                            if cur:
                                pages.append(cur)
                            gd = m.groupdict()
                            cur = (int(gd["pdf"]) if gd.get("pdf") else None,
                                   gd.get("printed"), i, [ln])
                        elif cur:
                            cur[3].append(ln)
                    if cur:
                        pages.append(cur)
                pp = unit.get("printed_page", {"method": "none"})
                for pdf, mprinted, first, cl in pages:
                    printed = None
                    if pp.get("method") == "marker":
                        printed = mprinted if mprinted and not mprinted.startswith("-") else None
                    elif pp.get("method") == "offset" and pdf is not None:
                        printed = _printed_from_offset(pdf, pp)
                    body = "\n".join(cl)
                    if not body.strip():
                        continue
                    yield Passage(wid, vol, rel, pdf, printed, _locator(printed, pdf, page_label),
                                  first, first + len(cl) - 1, lang, body)
            elif layout in ("whole", "section"):
                sec = None
                if layout == "section":
                    # the manifest's map wins; the in-text «(Side N-M)» line is a fallback
                    sec = (unit.get("sections") or {}).get(fp.stem)
                    if sec is None:
                        rx = re.compile(unit.get("section_regex", r"\((?:S|s)ide ([0-9][0-9\-–]*)\)"))
                        for ln in lines[:40]:
                            m = rx.search(ln)
                            if m:
                                sec = m.group(1)
                                break
                    sec = str(sec) if sec is not None else None
                for a, b, body in _chunk_lines(lines, unit.get("chunk_lines", 30)):
                    if sec:
                        loc = f"{page_label} {sec} (section range)"
                    else:
                        loc = f"lines {a}-{b}"
                    yield Passage(wid, vol, rel, None, sec, loc, a, b, lang, body)
            else:
                raise SystemExit(f"{wid}: unknown layout {layout!r}")


# ---------------------------------------------------------------------------
# Build
# ---------------------------------------------------------------------------

SCHEMA = """
CREATE TABLE meta(key TEXT PRIMARY KEY, value TEXT);
CREATE TABLE passage(
  id INTEGER PRIMARY KEY,
  work TEXT, volume TEXT, path TEXT, pdf_page INTEGER, printed TEXT,
  locator TEXT, line_start INTEGER, line_end INTEGER, lang TEXT, text TEXT);
CREATE VIRTUAL TABLE fts USING fts5(body, content='', tokenize='unicode61');
CREATE VIRTUAL TABLE vocab USING fts5vocab(fts, row);
CREATE TABLE work(id TEXT PRIMARY KEY, title TEXT, citation TEXT, ocr TEXT);
"""


def cmd_build(args) -> int:
    man = load_manifest()
    db = Path(args.db)
    db.parent.mkdir(parents=True, exist_ok=True)
    tmp = db.with_suffix(".tmp")
    if tmp.exists():
        tmp.unlink()
    con = sqlite3.connect(tmp)
    con.executescript(SCHEMA)
    total = collections.Counter()
    for w in man["works"]:
        if args.work and w["id"] not in args.work:
            continue
        con.execute("INSERT INTO work VALUES (?,?,?,?)",
                    (w["id"], w.get("title"), w.get("citation"), w.get("ocr")))
        for p in iter_passages(w):
            cur = con.execute(
                "INSERT INTO passage(work,volume,path,pdf_page,printed,locator,line_start,line_end,lang,text)"
                " VALUES (?,?,?,?,?,?,?,?,?,?)",
                (p.work, p.volume, p.path, p.pdf_page, p.printed, p.locator,
                 p.line_start, p.line_end, p.lang, p.text))
            con.execute("INSERT INTO fts(rowid, body) VALUES (?,?)", (cur.lastrowid, normalize(p.text)))
            total[p.work] += 1
    con.execute("INSERT INTO meta VALUES ('normalizer_version', ?)", (str(NORMALIZER_VERSION),))
    con.execute("INSERT INTO meta VALUES ('variants_sha', ?)",
                (str(hash(VARIANTS.read_text(encoding='utf-8'))),))
    con.commit()
    con.close()
    os.replace(tmp, db)
    for k, v in total.items():
        print(f"  {k:40s} {v:6d} passages")
    print(f"build: {sum(total.values())} passages → {db}")
    return 0


# ---------------------------------------------------------------------------
# Search
# ---------------------------------------------------------------------------

_TOKEN = re.compile(r"[^\W_]+", re.UNICODE)


def query_terms(q: str) -> list[str]:
    return _TOKEN.findall(normalize(q, join_lines=False))


def _doc_count(con, term: str) -> int:
    r = con.execute("SELECT doc FROM vocab WHERE term = ?", (term,)).fetchone()
    return r[0] if r else 0


def _prefix_count(con, term: str) -> int:
    r = con.execute("SELECT sum(doc) FROM vocab WHERE term >= ? AND term < ?",
                    (term, term + "\uffff")).fetchone()
    return r[0] or 0


def compound_splits(con, term: str, *, min_part: int = 3, min_doc: int = 3,
                    keep: int = 3) -> list[tuple[str, str]]:
    """Two-part splits of a query word whose parts both occur in the index.

    «smaamoent» (query «småmønt») → («smaa», «moent»), which as a phrase
    matches «Smaa-Myndt» / «Smaa Mynt» in the text. The left part must be a
    whole indexed word, the right part may be a prefix of one (inflection).
    Ranked by the rarer part's document count; at most `keep` are returned.
    """
    if len(term) < 2 * min_part + 1 or term.isdigit():
        return []
    out = []
    for i in range(min_part, len(term) - min_part + 1):
        left, right = term[:i], term[i:]
        dl = _doc_count(con, left)
        if dl < min_doc:
            continue
        dr = _prefix_count(con, right)
        if dr < min_doc:
            continue
        out.append((min(dl, dr), left, right))
    out.sort(reverse=True)
    return [(a, b) for _, a, b in out[:keep]]


def _term_group(con, t: str, prefix: bool, split: bool) -> str:
    alts = [f'"{t}"*' if prefix and len(t) >= 3 and not t.isdigit() else f'"{t}"']
    if split and con is not None:
        for left, right in compound_splits(con, t):
            alts.append(f'"{left} {right}"*' if prefix else f'"{left} {right}"')
    return alts[0] if len(alts) == 1 else "(" + " OR ".join(alts) + ")"


def _fts_expr(terms: list[str], op: str, prefix: bool, con=None, split: bool = True) -> str:
    return f" {op} ".join(_term_group(con, t, prefix, split) for t in terms)


def _best_snippet(text: str, terms: list[str], width: int = 1) -> tuple[int, str]:
    lines = text.split("\n")
    norm = [normalize(ln, join_lines=False) for ln in lines]
    best, best_i = -1, 0
    for i in range(len(lines)):
        window = " ".join(norm[max(0, i - width): i + width + 1])
        toks = set(_TOKEN.findall(window))
        score = sum(1 for t in terms if any(tok.startswith(t) for tok in toks))
        if score > best:
            best, best_i = score, i
    a, b = max(0, best_i - width), min(len(lines), best_i + width + 1)
    snip = " ".join(re.sub(r"\s+", " ", ln).strip() for ln in lines[a:b]).strip()
    return best_i, snip[:400]


def search(con: sqlite3.Connection, q: str, *, work: list[str] | None = None,
           lang: str | None = None, limit: int = 10, prefix: bool = True,
           fts_raw: bool = False, split: bool = True):
    terms = query_terms(q)
    if not terms:
        return [], terms
    where, params = [], []
    if work:
        where.append("p.work IN (%s)" % ",".join("?" * len(work)))
        params += work
    if lang:
        where.append("p.lang LIKE ?")
        params.append(f"%{lang}%")
    extra = (" AND " + " AND ".join(where)) if where else ""
    sql = ("SELECT p.id, p.work, p.volume, p.path, p.pdf_page, p.printed, p.locator,"
           " p.line_start, p.text, bm25(fts) AS score"
           " FROM fts JOIN passage p ON p.id = fts.rowid"
           f" WHERE fts MATCH ?{extra} ORDER BY score LIMIT ?")
    seen, rows = set(), []
    # --fts: the query keeps FTS5 syntax (quotes, NEAR, OR); its words are
    # normalised like the index, then the operators restored to upper case
    raw = re.sub(r"\b(near|and|or|not)\b", lambda m: m.group(1).upper(),
                 normalize(q, join_lines=False))
    exprs = [raw] if fts_raw else [_fts_expr(terms, "AND", prefix, con, split), _fts_expr(terms, "OR", prefix, con, split)]
    for expr in exprs:
        for r in con.execute(sql, [expr, *params, limit]):
            if r[0] in seen:
                continue
            seen.add(r[0])
            rows.append(r)
            if len(rows) >= limit:
                break
        if len(rows) >= limit or len(terms) == 1:
            break
    return rows, terms


def cmd_search(args) -> int:
    db = Path(args.db)
    if not db.exists():
        print(f"no index at {db}; run `kb.py build` first", file=sys.stderr)
        return 2
    con = sqlite3.connect(db)
    rows, terms = search(con, args.query, work=args.work, lang=args.lang, limit=args.limit,
                         prefix=not args.exact, fts_raw=args.fts,
                         split=not args.no_split)
    print(f"query terms (normalised): {' '.join(terms)}")
    if not rows:
        print("no hits")
        return 1
    for rank, (pid, w, vol, path, pdf, printed, loc, l0, text, score) in enumerate(rows, 1):
        off, snip = _best_snippet(text, terms)
        volp = (f" Bd {vol}" if str(vol).isdigit() else f" {vol}") if vol else ""
        print(f"\n{rank:2d}. {w}{volp} · {loc} · bm25 {score:.2f}")
        print(f"    scripts/cache/{path}:{l0 + off}")
        print(f"    «{snip}»")
    return 0


# ---------------------------------------------------------------------------
# Offsets — running-head page-number detection
# ---------------------------------------------------------------------------

def _head_numbers(body: str) -> list[int]:
    lines = [ln for ln in body.split("\n") if ln.strip()]
    cand = lines[:3] + lines[-3:]
    nums = []
    for ln in cand:
        if re.match(r"^\s*(##|===)", ln):
            continue
        for m in re.findall(r"(?<![\d,.])(\d{1,4})(?![\d,.])", ln):
            nums.append(int(m))
    return nums


def cmd_offsets(args) -> int:
    man = load_manifest()
    works = [w for w in man["works"] if w["id"] == args.work]
    if not works:
        print(f"unknown work {args.work}", file=sys.stderr)
        return 2
    per_file: dict[str, collections.Counter] = collections.defaultdict(collections.Counter)
    seq: dict[str, list] = collections.defaultdict(list)
    pages: dict[str, int] = collections.Counter()
    for p in iter_passages(works[0]):
        if p.pdf_page is None:
            continue
        key = p.volume or p.path
        pages[key] += 1
        for n in _head_numbers(p.text):
            d = n - p.pdf_page
            if -50 <= d <= 2000:
                per_file[key][d] += 1
                seq[key].append((p.pdf_page, d))
    for key, c in per_file.items():
        top = c.most_common(3)
        print(f"{key}: {pages[key]} pages; offset printed−pdf candidates {top}")
        if top:
            d0 = top[0][0]
            hits = sorted(pdf for pdf, d in seq[key] if d == d0)
            print(f"   dominant {d0:+d}: pdf {hits[0]}–{hits[-1]}, {len(hits)} pages agree")
    return 0


# ---------------------------------------------------------------------------
# refs_pool keys
# ---------------------------------------------------------------------------

def refs_keys_for(work: dict, pool: dict) -> list[str]:
    rx = work.get("refs_match")
    if not rx:
        return []
    r = re.compile(rx, re.I)
    out = []
    for k, v in pool.items():
        if not isinstance(v, dict):
            continue
        s = " ".join(str(x) for x in v.values() if isinstance(x, str))
        if r.search(s):
            out.append(k)
    return sorted(out)


def cmd_refkeys(args) -> int:
    man = load_manifest()
    pool = yaml.safe_load(REFS_POOL.read_text(encoding="utf-8"))
    drift = 0
    for w in man["works"]:
        want = refs_keys_for(w, pool)
        have = sorted(w.get("refs_pool_keys") or [])
        if args.print:
            print(f"{w['id']}: {want}")
            continue
        if want != have:
            drift += 1
            add, rm = sorted(set(want) - set(have)), sorted(set(have) - set(want))
            print(f"{w['id']}: +{add} -{rm}")
    if not args.print:
        print("refkeys: manifest in step with refs_pool.yml" if not drift
              else f"refkeys: {drift} works out of step")
    return 1 if drift else 0


# ---------------------------------------------------------------------------

def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="kb", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--db", default=str(DB_DEFAULT))
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("extract-htm")
    s.set_defaults(fn=cmd_extract_htm)
    s = sub.add_parser("build")
    s.add_argument("--work", action="append", help="build only these work ids")
    s.set_defaults(fn=cmd_build)
    s = sub.add_parser("search")
    s.add_argument("query")
    s.add_argument("--work", action="append", help="restrict to work id (repeatable)")
    s.add_argument("--lang", help="restrict to a language code (da, de, la, en, sv, no)")
    s.add_argument("--limit", type=int, default=10)
    s.add_argument("--exact", action="store_true", help="no prefix matching")
    s.add_argument("--no-split", action="store_true", help="no compound splitting of query words")
    s.add_argument("--fts", action="store_true", help="pass QUERY to FTS5 as-is (NEAR, quotes)")
    s.set_defaults(fn=cmd_search)
    s = sub.add_parser("offsets")
    s.add_argument("work")
    s.set_defaults(fn=cmd_offsets)
    s = sub.add_parser("refkeys")
    s.add_argument("--print", action="store_true", help="print the keys each work's refs_match finds")
    s.set_defaults(fn=cmd_refkeys)
    args = ap.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
