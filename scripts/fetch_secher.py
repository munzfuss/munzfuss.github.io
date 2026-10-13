"""Cache Secher (ed.), *Corpus constitutionum Daniæ. Forordninger, Recesser
og andre kongelige Breve, Danmarks Lovgivning vedkommende 1558-1660*,
6 Bd. (København 1887-1918) — the printed texts of the Danish acts for
1558-1660, i.e. the ACT itself for the register's «text seen» column.

Source: Det Kongelige Bibliotek's digitisation. Two mirrors: Selskabet
for Udgivelse af Kilder til dansk Historie (kildeskriftselskabet.dk,
«kan downloades gratis», ~50 kB/s on 2026-10-13) and Wikimedia Commons
(the same scans re-uploaded for da.wikisource, ~2 MB/s; the «_gl.pdf»
files there are the KB originals byte-for-byte in size, the plain ones a
smaller re-encoding). Commons is the default. 150-400 MB each, so the
PDFs are NOT committed; only the text layer is:

    scripts/cache/secher/_pdf/bd<N>.pdf          gitignored download
    scripts/cache/secher/bd<N>/pages/<NNNN>.txt  pdftotext -layout, one
                                                 file per PDF page
    scripts/cache/secher/bd<N>/_index.json       page count, source URL,
                                                 fetch date, sha256

Volumes (kildeskriftselskabet.dk, verified 2026-10-13):
    1  1558-1575  (1887-88)   2  1576-1595  (1889-90)
    3  1596-1621  (1891-94)   4  1622-1638  (1897)
    5  1639-1650  (1903)      6  1651-1660  (1918)

archive.org also holds Google scans of Bd 2 (corpusconstitut01sechgoog),
Bd 4 (…00sechgoog) and one Hæfte of Bd 3 (…02sechgoog) with their own
OCR; ``--archive-org`` saves those ``_djvu.txt`` files beside the KB text
as a second reading for a doubtful passage.

    .venv/bin/python scripts/fetch_secher.py --bd 1 [--bd 2 …] [--archive-org] [--kb]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import urllib.request
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib.paths import SECHER_CACHE as CACHE_DIR  # noqa: E402

KB_URL = "https://kildeskriftselskabet.dk/images/Pdf-filer/1887_Secher_1300166350{code}.pdf"
VOLUMES = {1: "66", 2: "74", 3: "82", 4: "90", 5: "104", 6: "112"}
_C = ("https://upload.wikimedia.org/wikipedia/commons/{h}/Corpus_constitutionum_Dani%C3%A6_"
      "Forordninger%2C_Recesser_og_andre_kongelige_Breve%2C_Danmarks_Lovgivning_vedkommende_"
      "1558-1660_-_bind_{bd}_%28%C3%A5r_{yrs}%29.pdf")
COMMONS_URL = {bd: _C.format(h=h, bd=bd, yrs=yrs) for bd, h, yrs in [
    (1, "2/22", "1558-1575"), (2, "f/ff", "1576-1595"), (3, "a/af", "1596-1621"),
    (4, "6/6b", "1622-1638"), (5, "6/6d", "1639-1650"), (6, "d/d9", "1651-1660")]}
YEARS = {1: "1558-1575", 2: "1576-1595", 3: "1596-1621",
         4: "1622-1638", 5: "1639-1650", 6: "1651-1660"}
ARCHIVE_ORG = {2: "corpusconstitut01sechgoog", 3: "corpusconstitut02sechgoog",
               4: "corpusconstitut00sechgoog"}
USER_AGENT = "Mozilla/5.0 (research; muentzfuesse project; non-commercial scholarly register)"


def _download(url: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=120) as resp, dest.open("wb") as fh:
        while chunk := resp.read(1 << 20):
            fh.write(chunk)


def _split_pages(pdf: Path, pages_dir: Path) -> int:
    """pdftotext -layout on the whole file, then split on form feeds."""
    txt = subprocess.run(["pdftotext", "-layout", str(pdf), "-"],
                         check=True, capture_output=True).stdout.decode("utf-8")
    pages = txt.split("\f")
    if pages and not pages[-1].strip():
        pages.pop()
    pages_dir.mkdir(parents=True, exist_ok=True)
    for i, body in enumerate(pages, start=1):
        (pages_dir / f"{i:04d}.txt").write_text(body, encoding="utf-8")
    return len(pages)


def fetch_volume(bd: int, archive_org: bool, kb: bool = False) -> None:
    pdf = CACHE_DIR / "_pdf" / f"bd{bd}.pdf"
    url = KB_URL.format(code=VOLUMES[bd]) if kb else COMMONS_URL[bd]
    if not pdf.exists():
        print(f"bd{bd}: downloading {url}")
        _download(url, pdf)
    gi = CACHE_DIR / "_pdf" / ".gitignore"
    if not gi.exists():
        gi.write_text("*.pdf\n")
    vol_dir = CACHE_DIR / f"bd{bd}"
    n = _split_pages(pdf, vol_dir / "pages")
    index = {
        "volume": bd, "years": YEARS[bd], "source_url": url,
        "fetched": date.today().isoformat(), "pdf_bytes": pdf.stat().st_size,
        "pdf_sha256": hashlib.sha256(pdf.read_bytes()).hexdigest(), "pages": n,
    }
    if archive_org and bd in ARCHIVE_ORG:
        ident = ARCHIVE_ORG[bd]
        alt = vol_dir / f"{ident}_djvu.txt"
        if not alt.exists():
            _download(f"https://archive.org/download/{ident}/{ident}_djvu.txt", alt)
        index["archive_org_djvu"] = alt.name
    (vol_dir / "_index.json").write_text(json.dumps(index, indent=1) + "\n")
    print(f"bd{bd}: {n} pages of text")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--bd", type=int, action="append", required=True)
    ap.add_argument("--archive-org", action="store_true")
    ap.add_argument("--kb", action="store_true", help="kildeskriftselskabet.dk mirror instead of Commons")
    args = ap.parse_args()
    for bd in args.bd:
        fetch_volume(bd, args.archive_org, args.kb)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
