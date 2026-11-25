#!/usr/bin/env python3
"""Helper for the add-source-work skill: bring one printed work (PDF) into
the harvest cache with a searchable text layer and a `_corpus.yml` record.

Subcommands. A PDF path is a library path (`LIBRARY_ROOT`, the same relative
path as in the cache; read from the cache as long as the library lacks it);
a text path is relative to the harvest cache.

  dupes WORDS…          corpus records whose id / title / author / url match
                        every word; cached PDFs of the same size + md5 as
                        --pdf (an already-cached copy under another name)
  fetch URL DEST        download URL to the research library at DEST (never
                        overwrites), record it in the library manifest with
                        the URL, then `inspect`
  inspect PDF           pages, text characters per page, pages without text
                        (a scan without OCR), producer
  extract PDF           pdftotext → <same name>.extract.txt (one form feed per
                        page, the `formfeed` layout); refuses to overwrite
  offsets TEXT          running-head page numbers of a formfeed extract →
                        contiguous runs of one offset (printed − pdf)
  entry …               print a `_corpus.yml` record to paste (see --help)
  verify ID [QUERY]     kb build, kb offsets ID, kb search QUERY --work ID

Run with the project venv: `.venv/bin/python .claude/skills/add-source-work/add_work.py …`.
"""
from __future__ import annotations

import argparse
import hashlib
import re
import subprocess
import sys
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "scripts"))
from lib.originals import TEXT_ROOT, MissingOriginal, iter_originals, original, rel_of  # noqa: E402
from lib.paths import LIBRARY_ROOT  # noqa: E402
CACHE = TEXT_ROOT          # text layers, _corpus.yml, _library_manifest.yml; originals go to LIBRARY_ROOT
MANIFEST = CACHE / "_corpus.yml"
LIBRARY = REPO / "scripts" / "library" / "library.py"
KB = REPO / "scripts" / "kb" / "kb.py"
UA = "Mozilla/5.0 (Macintosh)"   # danskmoent answers a bot challenge without it

sys.path.insert(0, str(REPO / "scripts" / "kb"))


def _path(p: str) -> Path:
    """A text-layer path (relative to the harvest cache)."""
    q = Path(p)
    return q if q.is_absolute() else CACHE / q


def _pdf(p: str) -> Path:
    """An original PDF: library first, then the cache (plan step 4)."""
    try:
        return original(p)
    except MissingOriginal as e:
        raise SystemExit(str(e))


def _md5(p: Path) -> str:
    h = hashlib.md5()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def cmd_dupes(a) -> int:
    import yaml
    works = (yaml.safe_load(MANIFEST.read_text(encoding="utf-8")) or {}).get("works") or []
    words = [w.casefold() for w in a.words]
    for w in works:
        hay = " ".join(str(w.get(k) or "") for k in ("id", "title", "author", "year", "source_url")).casefold()
        if words and all(x in hay for x in words):
            print(f"corpus: {w['id']}  {w.get('title')}  ({w.get('source_url')})")
    if a.pdf:
        pdf = _pdf(a.pdf)
        size, digest = pdf.stat().st_size, None
        for _rel, other in iter_originals(".pdf"):
            if other.resolve() == pdf.resolve() or other.stat().st_size != size:
                continue
            digest = digest or _md5(pdf)
            if _md5(other) == digest:
                print(f"same file already in the library: {_rel}")
    return 0


def _pdfinfo(pdf: Path) -> dict:
    out = subprocess.run(["pdfinfo", str(pdf)], capture_output=True, text=True).stdout
    return dict(ln.split(":", 1) for ln in out.splitlines() if ":" in ln)


def cmd_inspect(a) -> int:
    pdf = _pdf(a.pdf)
    info = _pdfinfo(pdf)
    pages = int(info.get("Pages", "0").strip())
    text = subprocess.run(["pdftotext", str(pdf), "-"], capture_output=True, text=True).stdout
    per = [len(re.sub(r"\s", "", t)) for t in text.split("\f")][:pages]
    empty = [i + 1 for i, n in enumerate(per) if n < 40]
    print(f"{rel_of(pdf)}: {pages} pages, "
          f"{pdf.stat().st_size / 1e6:.1f} MB, producer {info.get('Producer', '?').strip()}")
    print(f"text characters per page: median {sorted(per)[len(per) // 2] if per else 0}")
    if len(empty) == pages:
        print("NO TEXT LAYER — a scan without OCR; OCR it first (see SKILL.md), or the work "
              "indexes empty and a search miss would read as «not in the source».")
    elif empty:
        print(f"pages without text ({len(empty)}): {empty[:40]}{' …' if len(empty) > 40 else ''} "
              "— plates, blank or title pages, or unOCR'd scans: look at them")
    return 0


def cmd_fetch(a) -> int:
    dest = LIBRARY_ROOT / a.dest
    if dest.exists():
        raise SystemExit(f"exists, not overwritten: {dest}")
    dest.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(a.url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=180) as r:
        ctype = r.headers.get("Content-Type", "")
        data = r.read()
    if not data.startswith(b"%PDF"):
        raise SystemExit(f"not a PDF ({ctype}, {len(data)} bytes) — nothing written")
    dest.write_bytes(data)
    print(f"saved {a.dest} in the library ({len(data) / 1e6:.1f} MB)")
    subprocess.run([sys.executable, str(LIBRARY), "add", a.dest, "--url", a.url,
                    "--fetched", __import__("datetime").date.today().isoformat()], check=True)
    print("  → back it up: .venv/bin/python scripts/library/library.py backup " + a.dest)
    return cmd_inspect(argparse.Namespace(pdf=a.dest))


def cmd_extract(a) -> int:
    pdf = _pdf(a.pdf)
    out = (CACHE / rel_of(pdf)).with_suffix(".extract.txt")
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists():
        raise SystemExit(f"exists, not overwritten: {out}")
    subprocess.run(["pdftotext", str(pdf), str(out)], check=True)
    ff = out.read_text(encoding="utf-8", errors="replace").count("\f")
    pages = int(_pdfinfo(pdf).get("Pages", "0").strip())
    print(f"wrote {out.relative_to(CACHE)}: {ff} form feeds for {pages} pages"
          + ("" if ff == pages else "  ← MISMATCH: page numbers from this file would be off"))
    return 0


def cmd_offsets(a) -> int:
    from kb import _head_numbers
    pages = _path(a.text).read_text(encoding="utf-8", errors="replace").split("\f")
    per_page = []
    for i, body in enumerate(pages, start=1):
        ds = {n - i for n in _head_numbers(body) if -50 <= n - i <= 2000}
        per_page.append((i, ds))
    # contiguous runs where one offset is seen on every page that shows a number;
    # a new run starts with the offset most pages of the work agree on
    seen = {}
    for _, ds in per_page:
        for d in ds:
            seen[d] = seen.get(d, 0) + 1
    runs, cur = [], None
    for i, ds in per_page:
        if not ds:
            continue
        if cur and cur[0] in ds:
            cur[2], cur[3] = i, cur[3] + 1
        else:
            if cur:
                runs.append(cur)
            cur = [max(ds, key=lambda d: (seen[d], -abs(d))), i, i, 1]
    if cur:
        runs.append(cur)
    for d, f, t, n in runs:
        if n >= a.min:
            print(f"offset {d:+d}: pdf {f}–{t} ({n} pages with a matching head number)")
    print("Read the first, last and every boundary page before recording a segment; "
          "plates and unnumbered pages break runs on purpose.")
    return 0


def cmd_entry(a) -> int:
    seg = ", ".join(f"{{from: {f}, to: {t}, offset: {o}}}" for f, t, o in
                    (s.split(":") for s in a.segment)) if a.segment else ""
    pp = (f"{{method: offset, segments: [{seg}]}}" if seg else "{method: none}")
    print(f"""- id: {a.id}
  title: '{a.title}'
  author: '{a.author}'
  year: '{a.year}'
  citation: '{a.citation or f"{a.author.split()[-1]} {a.year}, s. <printed>"}'
  languages: [{", ".join(a.lang)}]
  kind: {a.kind}
  source_url: '{a.url}'
  page_count: {a.pages}
  text_layers:
  - {{glob: '{a.file}', layout: formfeed,
     printed_page: {pp}, basis: '{a.basis}'}}
  ocr: '{a.ocr}'
  refs_match: '{a.refs_match}'
  refs_pool_keys: []
""")
    return 0


def cmd_verify(a) -> int:
    py = sys.executable
    subprocess.run([py, str(KB), "build"], check=True, stdout=subprocess.DEVNULL)
    subprocess.run([py, str(KB), "offsets", a.id], check=True)
    keys = subprocess.run([py, str(KB), "refkeys", "--print"], capture_output=True, text=True).stdout
    print(next((ln for ln in keys.splitlines() if ln.startswith(a.id + ":")), f"{a.id}: not in manifest"))
    if a.query:
        subprocess.run([py, str(KB), "search", a.query, "--work", a.id], check=True)
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("dupes"); s.add_argument("words", nargs="*"); s.add_argument("--pdf"); s.set_defaults(fn=cmd_dupes)
    s = sub.add_parser("fetch"); s.add_argument("url"); s.add_argument("dest"); s.set_defaults(fn=cmd_fetch)
    s = sub.add_parser("inspect"); s.add_argument("pdf"); s.set_defaults(fn=cmd_inspect)
    s = sub.add_parser("extract"); s.add_argument("pdf"); s.set_defaults(fn=cmd_extract)
    s = sub.add_parser("offsets"); s.add_argument("text"); s.add_argument("--min", type=int, default=3); s.set_defaults(fn=cmd_offsets)
    s = sub.add_parser("entry")
    for k in ("id", "title", "author", "year", "url", "file", "basis", "ocr", "refs_match"):
        s.add_argument(f"--{k.replace('_', '-')}", dest=k, required=True)
    s.add_argument("--pages", type=int, required=True)
    s.add_argument("--lang", action="append", default=[])
    s.add_argument("--kind", default="literature", choices=["source", "register", "literature", "web", "extract"])
    s.add_argument("--citation")
    s.add_argument("--segment", action="append", help="FROM:TO:OFFSET, repeatable")
    s.set_defaults(fn=cmd_entry)
    s = sub.add_parser("verify"); s.add_argument("id"); s.add_argument("query", nargs="?"); s.set_defaults(fn=cmd_verify)
    a = ap.parse_args(argv)
    return a.fn(a)


if __name__ == "__main__":
    raise SystemExit(main())
