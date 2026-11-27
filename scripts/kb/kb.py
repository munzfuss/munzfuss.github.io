#!/usr/bin/env python3
"""Knowledge-base search over the harvested source corpus (PILOT).

Retrieval only. `kb search` returns page-anchored passages — work, PRINTED
page where the corpus manifest establishes one, file path and line — for the
`cite-source` workflow. It never summarises, paraphrases or answers: a hit is
a pointer to text a human (or an agent under CLAUDE.md §0/§0b/§5a) must then
read in full and quote verbatim from the file.

Subcommands
-----------
  extract-htm      danskmoent + Hede .htm → plain text under scripts/cache/_derived/
  build            read scripts/cache/_corpus.yml (+ docs/research dossiers) → SQLite FTS5 index
  search QUERY     ranked passages (BM25) with a snippet; warns when the index is stale
  works            the indexed works: id, kind, languages, printed-page anchoring
  offsets WORK     running-head page-number detection → PDF→printed offset
  refkeys          compare the manifest's refs_pool_keys with refs_pool.yml
  page PDF N       one PDF page as pdftotext prints it in each mode (layout / raw /
                   plain) — check a table, a contents page or marginal notes, where
                   the plain extract may interleave columns (layout_extract.py)
  image WORK P     the ORIGINAL page as a PNG (from the research library) for a
                   printed page P of WORK — to check doubtful OCR against the
                   scan; --crop x0,y0,x1,y1 (fractions of the page) cuts a region;
                   `image --pdf REL N` renders PDF page N of a library PDF directly

Layout
------
  scripts/cache/_corpus.yml          corpus manifest (in the harvest submodule)
  scripts/cache/_derived/{danskmoent,hede}/ text extracted from the cached .htm
  docs/research/{,instruments/,sources/}*.md  the dossiers — kind «dossier», built in (DOSSIER_WORKS)
  scripts/kb/variants.yml            editable spelling-variant rules
  scripts/kb/_index/kb.sqlite        the index (gitignored, rebuildable)

Run with the project venv: `.venv/bin/python scripts/kb/kb.py …`.
"""
from __future__ import annotations

import argparse
import collections
import glob
import hashlib
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
sys.path.insert(0, str(REPO / "scripts"))
from lib.paths import HARVEST_ROOT  # noqa: E402
CACHE = HARVEST_ROOT
MANIFEST = CACHE / "_corpus.yml"
DERIVED = CACHE / "_derived"
VARIANTS = Path(__file__).resolve().parent / "variants.yml"
DB_DEFAULT = Path(__file__).resolve().parent / "_index" / "kb.sqlite"
REFS_POOL = REPO / "data" / "shared" / "refs_pool.yml"
DOCS_RESEARCH = REPO / "docs" / "research"

# Project-side works (not in the harvest cache): the research dossiers. They
# are indexed as kind «dossier» so a search can find what an earlier session
# already established about an act, a standard or a coin group — and the
# dossier's own citations lead back to the cached source. Paths of these
# passages are relative to the REPO, not to scripts/cache (see `passage_path`).
DOSSIER_WORKS = [
    {"id": "research-dossiers", "kind": "dossier", "languages": ["en"], "page_label": "§",
     "title": "Research dossiers (docs/research/*.md — one per standard, period or coin group)",
     "citation": "docs/research/<file>.md § <section>",
     "text_layers": [{"glob": "docs/research/*.md", "layout": "markdown", "base": "repo"}]},
    {"id": "instrument-dossiers", "kind": "dossier", "languages": ["en"], "page_label": "§",
     "title": "Instrument dossiers (docs/research/instruments/*.md — one per coinage act 1480–1700; the register, PLAN, FINDINGS)",
     "citation": "docs/research/instruments/<file>.md § <section>",
     "text_layers": [{"glob": "docs/research/instruments/*.md", "layout": "markdown", "base": "repo"}]},
    {"id": "research-sources", "kind": "dossier", "languages": ["en"], "page_label": "§",
     "title": "Source captures (docs/research/sources/*.md — primary-source notes with verbatim passages)",
     "citation": "docs/research/sources/<file>.md § <section>",
     "text_layers": [{"glob": "docs/research/sources/*.md", "layout": "markdown", "base": "repo"}]},
]


def all_works(man: dict) -> list[dict]:
    """The manifest's works plus the project-side dossier works."""
    return list(man["works"]) + DOSSIER_WORKS


def passage_path(path: str) -> str:
    """Where a passage's `path` lives on disk: relative to the repo root when
    the cache sits inside it, absolute when `lib.paths` resolved it elsewhere
    (a git worktree reads the main checkout's cache)."""
    if path.startswith("docs/"):
        return path
    p = CACHE / path
    try:
        return str(p.relative_to(REPO))
    except ValueError:
        return str(p)


_MD_HEADING = re.compile(r"^(#{1,4})\s+(.*)$")


def _md_sections(lines: list[str]):
    """Split a Markdown file into (heading, first_line_no, lines) blocks; the
    text before the first heading is the «(head)» block."""
    heading, first, buf = "(head)", 1, []
    for i, ln in enumerate(lines, start=1):
        m = _MD_HEADING.match(ln)
        if m:
            if any(x.strip() for x in buf):
                yield heading, first, buf
            heading, first, buf = m.group(2).strip(), i, [ln]
        else:
            buf.append(ln)
    if any(x.strip() for x in buf):
        yield heading, first, buf

NORMALIZER_VERSION = 5  # bump when normalize() changes; recorded in the db

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
    n = changed = 0
    srcs = sorted((CACHE / "danskmoent").rglob("*.htm")) + sorted((CACHE / "hede").glob("*.htm"))
    for p in srcs:
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


def _chunk_lines(lines: list[str], size: int, start_line: int = 1, max_chars: int | None = None):
    """Yield (first_line_no, last_line_no, text) windows of ~size non-empty lines.

    max_chars caps a window by length as well: typed HTML transcriptions hold
    one paragraph per line, so 25 lines can be 20 000 characters, and BM25's
    length normalisation then buries the passage (README, round 5)."""
    buf, first, count, chars = [], None, 0, 0
    for i, ln in enumerate(lines, start=start_line):
        if first is None:
            first = i
        buf.append(ln)
        chars += len(ln)
        if ln.strip():
            count += 1
        full = count >= size or (max_chars is not None and chars >= max_chars)
        if full and not ln.strip():
            yield first, i, "\n".join(buf)
            buf, first, count, chars = [], None, 0, 0
        elif count >= size * 2 or (max_chars is not None and chars >= 2 * max_chars):
            yield first, i, "\n".join(buf)
            buf, first, count, chars = [], None, 0, 0
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
        base = REPO if unit.get("base") == "repo" else CACHE
        files = sorted(glob.glob(str(base / unit["glob"])))
        if not files:
            print(f"warning: {wid}: no files for {unit['glob']}", file=sys.stderr)
        for f in files:
            fp = Path(f)
            rel = str(fp.relative_to(base))
            text = _read_text(fp)
            lines = text.split("\n")
            if layout == "markdown":
                # one passage per heading section, long sections windowed; the
                # locator names the file and the section so a hit reads as
                # «1640_bestalling_timpff_glueckstadt § 4.3 ⚠ Source-internal …»
                for heading, first, sec_lines in _md_sections(lines):
                    for a, b, body in _chunk_lines(sec_lines, unit.get("chunk_lines", 40),
                                                  start_line=first, max_chars=unit.get("chunk_chars", 4000)):
                        loc = f"{fp.stem} {page_label} {heading[:70]}"
                        yield Passage(wid, None, rel, None, None, loc, a, b, lang, body)
            elif layout == "file-per-page":
                # nb.no volumes: covers / inserts precede file 0001 in the PDF,
                # so PDF page = file number + pdf_page_shift (0 when absent).
                pdf = int(re.sub(r"\D", "", fp.stem) or 0) + int(unit.get("pdf_page_shift", 0))
                printed = None
                pp = unit.get("printed_page", {})
                if pp.get("method") == "offset":
                    printed = _printed_from_offset(pdf, pp)
                elif pp.get("method") == "label":
                    m = re.match(pp.get("regex", r"\[label (\S+)\]"), lines[0] if lines else "")
                    printed = m.group(1) if m else None
                # A volume bound from parts with separate paginations: a file
                # inside a section takes that section's volume name, and its
                # printed page is the file number + the section's `offset`;
                # without `offset` the unit's own method stays; `unpaged: true`
                # (half-titles, blanks between the parts) reports no printed page.
                pvol = vol
                if fp.stem.isdigit():
                    for sec in unit.get("sections", []):
                        if sec["from"] <= int(fp.stem) <= sec["to"]:
                            pvol = sec.get("volume", vol)
                            if sec.get("unpaged"):
                                printed = None
                            elif "offset" in sec:
                                n = int(fp.stem) + int(sec["offset"])
                                printed = str(n) if sec.get("first", 1) <= n <= sec.get("last", n) else None
                            break
                yield Passage(wid, pvol, rel, pdf, printed, _locator(printed, pdf, page_label),
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
                    elif pp.get("method") == "label":
                        # a running head printed in the page's first lines («Page 94 Stack's …»)
                        rx_l = re.compile(pp["regex"])
                        head = [ln for ln in cl[1:] if ln.strip()][: pp.get("lines", 3)]
                        printed = next((m.group(1) for m in map(rx_l.search, head) if m), None)
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
                for a, b, body in _chunk_lines(lines, unit.get("chunk_lines", 30),
                                              max_chars=unit.get("chunk_chars")):
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
CREATE TABLE work(id TEXT PRIMARY KEY, title TEXT, citation TEXT, ocr TEXT, kind TEXT);
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
    for w in all_works(man):
        if args.work and w["id"] not in args.work:
            continue
        con.execute("INSERT INTO work VALUES (?,?,?,?,?)",
                    (w["id"], w.get("title"), w.get("citation"), w.get("ocr"), w.get("kind")))
        for p in iter_passages(w):
            cur = con.execute(
                "INSERT INTO passage(work,volume,path,pdf_page,printed,locator,line_start,line_end,lang,text)"
                " VALUES (?,?,?,?,?,?,?,?,?,?)",
                (p.work, p.volume, p.path, p.pdf_page, p.printed, p.locator,
                 p.line_start, p.line_end, p.lang, p.text))
            con.execute("INSERT INTO fts(rowid, body) VALUES (?,?)", (cur.lastrowid, normalize(p.text)))
            total[p.work] += 1
    for k, v in _fingerprint().items():
        con.execute("INSERT INTO meta VALUES (?, ?)", (k, v))
    if getattr(args, "work", None):
        con.execute("INSERT INTO meta VALUES ('partial', ?)", (",".join(args.work),))
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
           fts_raw: bool = False, split: bool = True, per_work: int = 0,
           kind: list[str] | None = None):
    """Ranked passages for `q`.

    per_work caps how many passages of one work enter the list (0 = no cap),
    so one book that discusses the topic on every page does not push every
    other work out of the top; ignored when the search is restricted to a
    single work.
    """
    terms = query_terms(q)
    # single digits are mostly the halves of split fractions («14¼» → 14 1 4)
    # and section numbers: as free terms they only add noise
    terms = [t for t in terms if not (t.isdigit() and len(t) == 1)] or terms
    if not terms:
        return [], terms
    cap = per_work if per_work and not (work and len(work) == 1) else 0
    where, params = [], []
    if work:
        where.append("p.work IN (%s)" % ",".join("?" * len(work)))
        params += work
    if kind:
        where.append("p.work IN (SELECT id FROM work WHERE kind IN (%s))" % ",".join("?" * len(kind)))
        params += kind
    if lang:
        where.append("p.lang LIKE ?")
        params.append(f"%{lang}%")
    extra = (" AND " + " AND ".join(where)) if where else ""
    sql = ("SELECT p.id, p.work, p.volume, p.path, p.pdf_page, p.printed, p.locator,"
           " p.line_start, p.text, bm25(fts) AS score"
           " FROM fts JOIN passage p ON p.id = fts.rowid"
           f" WHERE fts MATCH ?{extra} ORDER BY score LIMIT ?")
    seen, rows, per = set(), [], {}
    pool = max(limit, 1) * 50 if cap else limit
    # --fts: the query keeps FTS5 syntax (quotes, NEAR, OR); its words are
    # normalised like the index, then the operators restored to upper case
    raw = re.sub(r"\b(near|and|or|not)\b", lambda m: m.group(1).upper(),
                 normalize(q, join_lines=False))
    exprs = [raw] if fts_raw else [_fts_expr(terms, "AND", prefix, con, split), _fts_expr(terms, "OR", prefix, con, split)]
    for expr in exprs:
        for r in con.execute(sql, [expr, *params, pool]):
            if r[0] in seen:
                continue
            seen.add(r[0])
            if cap and per.get(r[1], 0) >= cap:
                continue
            per[r[1]] = per.get(r[1], 0) + 1
            rows.append(r)
            if len(rows) >= limit:
                break
        if len(rows) >= limit or len(terms) == 1:
            break
    return rows, terms


def _fingerprint() -> dict[str, str]:
    """What the index was built from: normaliser version, variant rules, manifest."""
    sha = lambda p: hashlib.sha1(p.read_bytes()).hexdigest()  # noqa: E731
    return {"normalizer_version": str(NORMALIZER_VERSION),
            "variants_sha": sha(VARIANTS), "manifest_sha": sha(MANIFEST),
            "dossiers_sha": _dossiers_fingerprint()}


def _dossiers_fingerprint() -> str:
    """A hash over every dossier file's path, size and mtime: an edited or
    added dossier makes the index stale (a rebuild is ~10 s)."""
    h = hashlib.sha1()
    for w in DOSSIER_WORKS:
        for unit in w["text_layers"]:
            for f in sorted(glob.glob(str(REPO / unit["glob"]))):
                st = os.stat(f)
                h.update(f"{Path(f).relative_to(REPO)}|{st.st_size}|{st.st_mtime_ns}\n".encode())
    return h.hexdigest()


def _stale_reason(con) -> str | None:
    """Why the index no longer matches the code / rules / manifest, or None."""
    have = dict(con.execute("SELECT key, value FROM meta").fetchall())
    for k, v in _fingerprint().items():
        if have.get(k) != v:
            return {"normalizer_version": "kb.py's normaliser changed",
                    "variants_sha": "variants.yml changed",
                    "manifest_sha": "_corpus.yml changed",
                    "dossiers_sha": "a docs/research dossier changed"}[k]
    if have.get("partial"):
        return f"built with --work {have['partial']} only"
    return None


def external_works(man: dict) -> list[dict]:
    """Works we could NOT obtain but whose host offers a full-text search:
    `_corpus.yml` top-level `external:` (id, title, citation, access,
    search_url with {id} and {q}, volumes: {label: host id})."""
    return list(man.get("external") or [])


def _print_external(ext: dict, query: str) -> None:
    from urllib.parse import quote
    print(f"\n{ext['id']} — NOT in the corpus: {ext.get('title', '')}")
    print(f"  access: {ext.get('access', '')}")
    for label, hid in (ext.get("volumes") or {}).items():
        print(f"  {label:10s} {ext['search_url'].format(id=hid, q=quote(query))}")
    if ext.get("note"):
        print(f"  note: {ext['note']}")


def cmd_search(args) -> int:
    man = load_manifest()
    exts = external_works(man)
    ext_ids = {e["id"] for e in exts}
    asked_ext = [e for e in exts if e["id"] in (args.work or [])]
    if asked_ext:
        # an external work has no local text: hand back the host's own search
        print("external work(s): the query is NOT run locally — open the URL(s) in a browser "
              "(the host may refuse automated access)")
        for e in asked_ext:
            _print_external(e, args.query)
        args.work = [w for w in args.work if w not in ext_ids]
        if not args.work:
            return 0
    db = Path(args.db)
    if not db.exists():
        print(f"no index at {db}; run `kb.py build` first", file=sys.stderr)
        return 2
    con = sqlite3.connect(db)
    why = _stale_reason(con)
    if why:
        print(f"WARNING: index is stale ({why}) — run `kb.py build`; results may miss or misplace passages",
              file=sys.stderr)
    rows, terms = search(con, args.query, work=args.work, lang=args.lang, limit=args.limit,
                         prefix=not args.exact, fts_raw=args.fts,
                         split=not args.no_split, per_work=args.per_work,
                         kind=args.kind)
    print(f"query terms (normalised): {' '.join(terms)}")
    if exts and not args.work:
        print("not searched (online-only, see `kb.py works --kind external`): "
              + ", ".join(e["id"] for e in exts), file=sys.stderr)
    if not rows:
        print("no hits")
        return 1
    for rank, (pid, w, vol, path, pdf, printed, loc, l0, text, score) in enumerate(rows, 1):
        off, snip = _best_snippet(text, terms)
        volp = (f" Bd {vol}" if str(vol).isdigit() else f" {vol}") if vol else ""
        print(f"\n{rank:2d}. {w}{volp} · {loc} · bm25 {score:.2f}")
        print(f"    {passage_path(path)}:{l0 + off}")
        print(f"    «{snip}»")
    return 0


def cmd_works(args) -> int:
    """The indexed works: id (for --work), kind (for --kind), languages, page anchoring."""
    man = load_manifest()
    kinds = args.kind or []
    print(f"{'id':36s} {'kind':10s} {'lang':8s} printed page  title")
    for w in all_works(man):
        if kinds and w.get("kind") not in kinds:
            continue
        methods = {(u.get("printed_page") or {}).get("method", "none") for u in w["text_layers"]}
        anchored = "yes" if methods - {"none"} else ("range" if any(u.get("layout") == "section" for u in w["text_layers"]) else ("section" if w.get("kind") == "dossier" else "no"))
        print(f"{w['id']:36s} {w.get('kind', ''):10s} {'+'.join(w.get('languages', [])):8s} {anchored:12s}  {w.get('title', '')[:70]}")
    for e in external_works(man):
        if kinds and "external" not in kinds:
            continue
        print(f"{e['id']:36s} {'external':10s} {'+'.join(e.get('languages', [])):8s} {'online only':12s}  {e.get('title', '')[:70]}")
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

def cmd_page(args) -> int:
    """Print one page of a cached PDF in the chosen pdftotext mode(s). The
    corpus extracts are plain mode, which guesses a reading order and can
    interleave columns on a contents page, a table or beside marginal notes;
    `layout` keeps the columns as printed, `raw` follows the PDF's own text
    order. Read the page here before taking a figure from a table or an
    author from a contents page."""
    import subprocess
    from lib.originals import MissingOriginal, original
    pdf = Path(args.pdf)
    if not (pdf.is_absolute() and pdf.exists()):
        try:
            pdf = original(args.pdf)
        except MissingOriginal as e:
            raise SystemExit(str(e))
    modes = ["layout", "raw", "plain"] if args.mode == "all" else [args.mode]
    for m in modes:
        cmd = ["pdftotext", "-f", str(args.n), "-l", str(args.n)]
        if m != "plain":
            cmd.append(f"-{m}")
        out = subprocess.run(cmd + [str(pdf), "-"], capture_output=True, text=True).stdout
        if len(modes) > 1:
            print(f"===== {m} =====")
        print(out.rstrip("\f\n"))
    return 0


# ---------------------------------------------------------------------------

_PART_RE = re.compile(r"_pdf(\d+)-(\d+)\.pdf$", re.I)


def _pdf_for_text(text_rel: str, pdf_page: int) -> tuple[str, int] | None:
    """The library PDF (relative path) and its page number for PDF page
    ``pdf_page`` of the work whose text layer is ``text_rel``. Three text
    layouts: ``x.extract.txt`` beside ``x.pdf``; ``pages/<name>.txt`` (one file
    per PDF, form feeds) with ``<name>.pdf`` one level up; ``pages/NNNN.txt``
    (one file per page) whose volume directory — or a ``_pdf/<voldir>.pdf``
    sibling (Secher) — holds the PDF, possibly split into ``_partK_pdfAAA-BBB``
    pieces, in which case the page is shifted into the piece."""
    from lib.originals import iter_originals
    t = Path(text_rel)
    pdfs = [rel for rel, _ in iter_originals(".pdf")]
    cands: list[str] = []
    if t.name.endswith(".extract.txt"):
        cands = [t.with_name(t.name[: -len(".extract.txt")] + ".pdf").as_posix()]
    elif t.parent.name == "pages" and not t.stem.isdigit():
        cands = [(t.parent.parent / (t.stem + ".pdf")).as_posix()]
    elif t.parent.name == "pages":
        vol = t.parent.parent
        cands = [r for r in pdfs if Path(r).parent == vol]
        if not cands:
            cands = [r for r in pdfs if Path(r).stem == vol.name
                     and Path(r).parts[0] == vol.parts[0]]
    # a work stored in pieces under GitHub's old 100 MB limit:
    # <stem>.pdf → <stem>_part<K>_pdf<AAA>-<BBB>.pdf beside it
    for base in list(cands):
        b = Path(base)
        cands += [r for r in pdfs if Path(r).parent == b.parent
                  and Path(r).name.startswith(b.stem + "_part") and _PART_RE.search(r)]
    cands = [c for c in dict.fromkeys(cands) if c in pdfs]
    if not cands:
        return None
    if len(cands) == 1 and not _PART_RE.search(cands[0]):
        return cands[0], pdf_page
    for c in sorted(cands):
        m = _PART_RE.search(c)
        if m and int(m.group(1)) <= pdf_page <= int(m.group(2)):
            return c, pdf_page - int(m.group(1)) + 1
    return None


def cmd_image(args) -> int:
    """Render one ORIGINAL page (research library PDF) to PNG and print its path."""
    import subprocess
    import tempfile
    from lib.originals import MissingOriginal, original
    if args.pdf:
        rel, page = args.pdf, int(args.page)
    else:
        con = sqlite3.connect(args.db)
        q = "SELECT DISTINCT volume, path, pdf_page FROM passage WHERE work = ? AND printed = ?"
        prm: list = [args.work, str(args.page)]
        if args.volume:
            q += " AND volume = ?"
            prm.append(args.volume)
        rows = [r for r in con.execute(q, prm).fetchall() if r[2] is not None]
        if not rows:
            raise SystemExit(f"no indexed page «{args.page}» of {args.work}"
                             + (f" vol. {args.volume}" if args.volume else "")
                             + " (printed page not established there? use --pdf REL N)")
        if len({(r[0], r[1], r[2]) for r in rows}) > 1:
            listing = "\n".join(f"  vol. {r[0]} · {r[1]} · pdf p. {r[2]}" for r in rows)
            raise SystemExit(f"page «{args.page}» of {args.work} is ambiguous — pass --volume:\n{listing}")
        _vol, text_rel, pdf_page = rows[0]
        hit = _pdf_for_text(text_rel, int(pdf_page))
        if not hit:
            raise SystemExit(f"no library PDF found for {text_rel} (pdf p. {pdf_page}); "
                             "render it with --pdf REL N")
        rel, page = hit
    try:
        pdf = original(rel)
    except MissingOriginal as e:
        raise SystemExit(str(e))
    out_dir = Path(args.out or tempfile.gettempdir())
    out_dir.mkdir(parents=True, exist_ok=True)
    stem = out_dir / f"kb_{Path(rel).stem}_p{page}"
    subprocess.run(["pdftoppm", "-f", str(page), "-l", str(page), "-r", str(args.dpi),
                    "-png", "-singlefile", str(pdf), str(stem)], check=True)
    png = stem.with_suffix(".png")
    if args.crop:
        from PIL import Image
        x0, y0, x1, y1 = (float(v) for v in args.crop.split(","))
        im = Image.open(png)
        w, h = im.size
        png = stem.with_name(stem.name + "_crop.png")
        im.crop((int(x0 * w), int(y0 * h), int(x1 * w), int(y1 * h))).save(png)
    print(f"{rel} · pdf p. {page}")
    print(png)
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="kb", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--db", default=str(DB_DEFAULT))
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("extract-htm")
    s.set_defaults(fn=cmd_extract_htm)
    s = sub.add_parser("build")
    s.add_argument("--work", action="append",
                   help="build an index of ONLY these works (replaces the whole index; search then warns)")
    s.set_defaults(fn=cmd_build)
    s = sub.add_parser("search")
    s.add_argument("query")
    s.add_argument("--work", action="append", help="restrict to work id (repeatable)")
    s.add_argument("--lang", help="restrict to a language code (da, de, la, en, sv, no)")
    s.add_argument("--kind", action="append",
                   help="restrict to a kind of work: source, register, literature, catalogue, web, extract, dossier "
                        "(repeatable; `kb.py works` lists each work's kind)")
    s.add_argument("--limit", type=int, default=10)
    s.add_argument("--exact", action="store_true", help="no prefix matching")
    s.add_argument("--no-split", action="store_true", help="no compound splitting of query words")
    s.add_argument("--per-work", type=int, default=0,
                   help="at most N passages of one work in the list (0 = no cap; ignored with one --work)")
    s.add_argument("--fts", action="store_true", help="pass QUERY to FTS5 as-is (NEAR, quotes)")
    s.set_defaults(fn=cmd_search)
    s = sub.add_parser("works")
    s.add_argument("--kind", action="append", help="only works of this kind")
    s.set_defaults(fn=cmd_works)
    s = sub.add_parser("offsets")
    s.add_argument("work")
    s.set_defaults(fn=cmd_offsets)
    s = sub.add_parser("refkeys")
    s.add_argument("--print", action="store_true", help="print the keys each work's refs_match finds")
    s.set_defaults(fn=cmd_refkeys)
    s = sub.add_parser("page")
    s.add_argument("pdf", help="library path of the PDF (absolute, or relative to the library; the old scripts/cache/ spelling works)")
    s.add_argument("n", type=int, help="PDF page number (1-based)")
    s.add_argument("--mode", choices=["layout", "raw", "plain", "all"], default="layout")
    s.set_defaults(fn=cmd_page)
    s = sub.add_parser("image", help="render an original page from the research library")
    s.add_argument("work", nargs="?", help="work id (kb.py works); omit with --pdf")
    s.add_argument("page", help="printed page (as kb search reports it); with --pdf the PDF page")
    s.add_argument("--volume", help="volume, when the work has several")
    s.add_argument("--pdf", help="library PDF path: render its PDF page directly")
    s.add_argument("--crop", help="x0,y0,x1,y1 as fractions of the page, e.g. 0,0.5,1,1")
    s.add_argument("--dpi", type=int, default=150)
    s.add_argument("--out", help="output directory (default: the system temp dir)")
    s.set_defaults(fn=cmd_image)
    args = ap.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
