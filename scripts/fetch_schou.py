"""Cache Schou, *Chronologisk Register over de Kongelige Forordninger og
aabne Breve …* (from 1670) from the Norwegian National Library (nb.no
digibok, public domain, «accessAllowedFrom: EVERYWHERE»).

Per volume: the IIIF manifest, then every page's ALTO OCR
(``metadata/<urn>/altos/<urn>_<page>``) saved raw as XML plus a plain-text
rendering, so the register can be grepped for coinage instruments and a
page can be quoted with its printed page label.

    scripts/cache/schou/bd<N>/_manifest.json       IIIF manifest as served
    <LIBRARY_ROOT>/schou/bd<N>/alto/<urn>_<page>.xml raw ALTO (an original:
                                                   outside git, recorded as
                                                   one bundle in
                                                   _library_manifest.yml)
    scripts/cache/schou/bd<N>/pages/<page>.txt     one line per TextLine,
                                                   header line = printed label
    <LIBRARY_ROOT>/schou/bd<N>/schou_bd<N>[_partK…].pdf  with --pdf

The OCR is Fraktur and noisy (lex.dk warns searches miss); keep the page
images reachable via the manifest's IIIF image service when a quote must
be checked against the print.

    .venv/bin/python scripts/fetch_schou.py --bd 1 [--bd 2 …] [--force]

Volumes (lokalhistoriewiki.no «Schous forordninger», verified 2026-10-13):
    1  Christian V  1670-1699   URN:NBN:no-nb_digibok_2014050824003
    2  Frederik IV  1699-1730   URN:NBN:no-nb_digibok_2014050824008
    3  Christian VI 1730-1746   URN:NBN:no-nb_digibok_2014050824016
    4  Frederik V   1746-1765   URN:NBN:no-nb_digibok_2014050824018
    5  Christian VII 1766-1774  URN:NBN:no-nb_digibok_2014050824017
"""
from __future__ import annotations

import argparse
import html
import json
import re
import shutil
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent / "library"))
from lib.paths import HARVEST_ROOT, LIBRARY_ROOT, SCHOU_CACHE as CACHE_DIR  # noqa: E402
import library  # noqa: E402

VOLUMES = {
    1: "URN:NBN:no-nb_digibok_2014050824003",
    2: "URN:NBN:no-nb_digibok_2014050824008",
    3: "URN:NBN:no-nb_digibok_2014050824016",
    4: "URN:NBN:no-nb_digibok_2014050824018",
    5: "URN:NBN:no-nb_digibok_2014050824017",
    # 6-25: lokalhistoriewiki.no list, checked against the nb.no catalogue API
    # 2026-11-25 (14, 15 and 25 from the list only). 19 is in two volumes:
    # 19 = parts 1-3 (1823-1825), 1904 = part 4 (1826).
    6: "URN:NBN:no-nb_digibok_2014050824014",   # 1775-1777
    7: "URN:NBN:no-nb_digibok_2009101603026",   # 1778-1780
    8: "URN:NBN:no-nb_digibok_2014050824015",   # 1781-1784
    9: "URN:NBN:no-nb_digibok_2014050824013",   # 1785-1788
    10: "URN:NBN:no-nb_digibok_2014050824019",  # 1789-1792
    11: "URN:NBN:no-nb_digibok_2014050824012",  # 1793-1796
    12: "URN:NBN:no-nb_digibok_2014050824004",  # 1797-1799
    13: "URN:NBN:no-nb_digibok_2010020503014",  # 1800-1803
    14: "URN:NBN:no-nb_digibok_2014050824011",  # 1804-1808
    15: "URN:NBN:no-nb_digibok_2014050824006",  # 1808-1811
    16: "URN:NBN:no-nb_digibok_2014050824007",  # 1812-1813
    17: "URN:NBN:no-nb_digibok_2014050824005",  # 1814-1817
    18: "URN:NBN:no-nb_digibok_2014050824009",  # 1818-1822
    19: "URN:NBN:no-nb_digibok_2014050926010",  # 1823-1825 (19:1-3)
    1904: "URN:NBN:no-nb_digibok_2014050926009",  # 1826 (19:4)
    20: "URN:NBN:no-nb_digibok_2008040802005",  # 1829-1833
    21: "URN:NBN:no-nb_digibok_2021011448521",  # 1834-1837
    22: "URN:NBN:no-nb_digibok_2008091503008",  # 1838-1839
    23: "URN:NBN:no-nb_digibok_2008091003012",  # 1839-1843
    24: "URN:NBN:no-nb_digibok_2012041238001",  # 1844-1847
    25: "URN:NBN:no-nb_digibok_2009091403004",  # 1848-1849
    # Registers and supplements (nb.no catalogue API, 2026-11-25; the last from
    # the lokalhistoriewiki list only). Directory = the key itself.
    "reg1795": "URN:NBN:no-nb_digibok_2015061048075",       # Alphabetisk Register 1795
    "reg1812": "URN:NBN:no-nb_digibok_2009100803005",       # Alphabetisk Register 1812
    "reg1823": "URN:NBN:no-nb_digibok_2022103128001",       # Alphabetisk Register 1823
    "reg1823_1849": "URN:NBN:no-nb_digibok_2022103128002",  # Alphabetisk Register 1823-1849 (1851)
    "anhang1793_1822": "URN:NBN:no-nb_digibok_2014050824001",  # Anhang 1793-1822
    "anhang_1udg_1_10": "URN:NBN:no-nb_digibok_2014050824010",  # Anhang to the 1st ed., 1-10
}
# Other nb.no collections fetched the same way (--collection). Catalogue API
# checked 2026-11-24: every title, period and «accessAllowedFrom: EVERYWHERE».
# Fogtman, Kongelige Rescripter, Resolutioner og Collegialbreve 1660-1813.
FOGTMAN = {
    "d1": "URN:NBN:no-nb_digibok_2015060948112",      # 1660-1670
    "d2": "URN:NBN:no-nb_digibok_2009101603008",      # 1670-1699
    "d3": "URN:NBN:no-nb_digibok_2015060948105",      # 1699-1730
    "d4_1": "URN:NBN:no-nb_digibok_2020050448519",    # 1730-1739
    "d4_2": "URN:NBN:no-nb_digibok_2015060948130",    # 1740-1746
    "d5_1": "URN:NBN:no-nb_digibok_2010020403009",    # 1746-1754
    "d5_2": "URN:NBN:no-nb_digibok_2010011503005",    # 1754-1765
    "d6_01": "URN:NBN:no-nb_digibok_2010020203025",   # 1766-1776
    "d6_02": "URN:NBN:no-nb_digibok_2010020203011",   # 1777-1784
    "d6_03": "URN:NBN:no-nb_digibok_2010020403005",   # 1785-1786
    "d6_04": "URN:NBN:no-nb_digibok_2010020403004",   # 1787-1788
    "d6_05": "URN:NBN:no-nb_digibok_2009101603029",   # 1789-1790
    "d6_06": "URN:NBN:no-nb_digibok_2015060948131",   # 1791-1792
    "d6_07": "URN:NBN:no-nb_digibok_2010020503012",   # 1793-1794
    "d6_08": "URN:NBN:no-nb_digibok_2010020403001",   # 1795-1796
    "d6_09": "URN:NBN:no-nb_digibok_2010020203033",   # 1797-1798
    "d6_10": "URN:NBN:no-nb_digibok_2010020203024",   # 1799-1800
    "d6_11": "URN:NBN:no-nb_digibok_2010011803006",   # 1801-1802
    "d6_12": "URN:NBN:no-nb_digibok_2009101603019",   # 1803-1804
    "d6_13": "URN:NBN:no-nb_digibok_2013070108089",   # 1805-1806
    "d7_1": "URN:NBN:no-nb_digibok_2015070848045",    # 1808 (from 13 March)
    "d7_2": "URN:NBN:no-nb_digibok_2023012348012",    # D. 7, B. 2
    "d7_3": "URN:NBN:no-nb_digibok_2023012348011",    # 1811-1812
    "d7_4": "URN:NBN:no-nb_digibok_2023012348010",    # 1813
}
# Norske Rigs-Registranter, tildeels i Uddrag, B. 1-12 (1523-1660).
NRR = {
    "b01": "URN:NBN:no-nb_digibok_2017061207087",  # 1523-1571
    "b02": "URN:NBN:no-nb_digibok_2018062548003",  # 1572-1588
    "b03": "URN:NBN:no-nb_digibok_2019121948004",  # 1588-1602
    "b04": "URN:NBN:no-nb_digibok_2019121948008",  # 1603-1618
    "b05": "URN:NBN:no-nb_digibok_2013060508001",  # 1619-1627
    "b06": "URN:NBN:no-nb_digibok_2019121948006",  # 1628-1634
    "b07": "URN:NBN:no-nb_digibok_2015120808053",  # 1635-1640
    "b08": "URN:NBN:no-nb_digibok_2019121948005",  # 1641-1648
    "b09": "URN:NBN:no-nb_digibok_2015110407053",  # 1648-1649
    "b10": "URN:NBN:no-nb_digibok_2011051604046",  # 1650-1653
    "b11": "URN:NBN:no-nb_digibok_2019121948007",  # 1653-1656
    "b12": "URN:NBN:no-nb_digibok_2008121603025",  # 1657-1660
}
# Norges gamle Love, Anden Række (1388-1604). Catalogue API checked 2026-11-25:
# these three are «accessAllowedFrom: EVERYWHERE»; B. 3:1 (1483-1513,
# 2014110708117) and B. 4:1 (1513-1536, 2012110208030) are NORWAY only.
NGL = {
    "r2_b1_1": "URN:NBN:no-nb_digibok_2010110806011",    # 1388-1447, 1a I
    "r2_b1_2_3": "URN:NBN:no-nb_digibok_2017091507090",  # 1388-1447, 1a II-III
    "r2_b2": "URN:NBN:no-nb_digibok_2018101748001",      # 1448-1482
}
# Wessel Berg, Kongelige Rescripter, Resolutioner og Collegial-Breve for Norge
# i Tidsrummet 1660-1813 (Christiania 1841-1847). Catalogue API checked
# 2026-11-27: every title and «accessAllowedFrom: EVERYWHERE», public domain.
WESSEL_BERG = {
    "b1": "URN:NBN:no-nb_digibok_2008111103067",   # 1660-1746
    "b2": "URN:NBN:no-nb_digibok_2008100703002",   # 1746-1780
    "b3": "URN:NBN:no-nb_digibok_2008091603025",   # 1781-1796
    "b4": "URN:NBN:no-nb_digibok_2010022412001",   # 1797-1813
    "register": "URN:NBN:no-nb_digibok_2010021712005",  # Register (1847)
}
COLLECTIONS = {  # name -> (volumes, cache directory, PDF file prefix)
    "schou": (VOLUMES, CACHE_DIR, "schou"),
    "fogtman": (FOGTMAN, CACHE_DIR.parent / "fogtman", "fogtman"),
    "nrr": (NRR, CACHE_DIR.parent / "norske_rigsregistranter", "nrr"),
    "ngl": (NGL, CACHE_DIR.parent / "norges_gamle_love", "ngl"),
    "wessel_berg": (WESSEL_BERG, CACHE_DIR.parent / "wessel_berg", "wessel_berg"),
}
PDF_PREFIX = "schou"
API = "https://api.nb.no/catalog/v1"
USER_AGENT = "Mozilla/5.0 (research; non-commercial scholarly register)"
SLEEP_SECS = 0.25


def _get(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    for attempt in range(1, 4):      # nb.no drops a connection now and then
        try:
            return urllib.request.urlopen(req, timeout=60).read()
        except Exception:  # noqa: BLE001
            if attempt == 3:
                raise
            time.sleep(10 * attempt)


def _alto_to_text(xml: str) -> str:
    """One output line per ALTO TextLine; words joined by single spaces.
    HYP (hyphenation) elements are kept as the printed hyphen."""
    lines: list[str] = []
    for tl in re.finditer(r"<TextLine\b.*?</TextLine>", xml, re.S):
        words = re.findall(r'<String\b[^>]*\bCONTENT="([^"]*)"', tl.group(0))
        if words:
            lines.append(html.unescape(" ".join(words)))
    return "\n".join(lines)


def _key(bd: str):
    return int(bd) if str(bd).isdigit() else bd


def _dir(bd) -> Path:
    """Text side of a volume (manifest, pages) — the harvest cache."""
    return CACHE_DIR / (f"bd{bd}" if isinstance(bd, int) else bd)


def _rel(bd) -> str:
    return _dir(bd).relative_to(HARVEST_ROOT).as_posix()


def _lib_dir(bd) -> Path:
    """Originals of a volume (ALTO, PDF) — the research library."""
    return LIBRARY_ROOT / _rel(bd)


def _alto_dir(bd) -> Path:
    """Where the ALTO is read from: the library, or the cache while a volume
    has not been moved yet (plan step 7 removes the cache copies)."""
    lib = _lib_dir(bd) / "alto"
    old = _dir(bd) / "alto"
    return old if (old.is_dir() and not lib.is_dir()) else lib


def fetch_volume(bd, force: bool) -> None:
    urn = VOLUMES[bd]
    vol_dir = _dir(bd)
    alto_dir, pages_dir = _alto_dir(bd), vol_dir / "pages"
    alto_dir.mkdir(parents=True, exist_ok=True)
    pages_dir.mkdir(parents=True, exist_ok=True)
    man_path = vol_dir / "_manifest.json"
    if man_path.exists() and not force:
        manifest = json.loads(man_path.read_text())
    else:
        manifest = json.loads(_get(f"{API}/iiif/{urn}/manifest"))
        man_path.write_text(json.dumps(manifest, indent=1, ensure_ascii=False) + "\n")
    canvases = manifest["sequences"][0]["canvases"]
    print(f"bd{bd}: {len(canvases)} canvases")
    for cv in canvases:
        alto_url = cv["@seeAlso"]["@id"]
        page_id = alto_url.rsplit("/", 1)[-1]          # <urn>_0039
        page_no = page_id.rsplit("_", 1)[-1]           # 0039 / C1 / I1 …
        xml_path = alto_dir / f"{page_id}.xml"
        txt_path = pages_dir / f"{page_no}.txt"
        if xml_path.exists() and txt_path.exists() and not force:
            continue
        try:
            xml = _get(alto_url).decode("utf-8")
        except Exception as exc:  # noqa: BLE001 — log and continue
            print(f"  {page_id}: {type(exc).__name__}: {exc}", file=sys.stderr)
            continue
        xml_path.write_text(xml, encoding="utf-8")
        txt_path.write_text(f"[label {cv.get('label', '')}]\n" + _alto_to_text(xml) + "\n",
                            encoding="utf-8")
        time.sleep(SLEEP_SECS)
    if alto_dir.is_relative_to(LIBRARY_ROOT):
        library.register(f"{_rel(bd)}/alto", bundle=True)
    print(f"bd{bd}: done — {len(list(pages_dir.glob('*.txt')))} page texts")


def fetch_pdf(bd, force: bool, tmp_dir: Path, keep_original: bool = False,
              as_served: bool = False) -> None:
    """The library's own PDF (page images only, colour, c. 0.5 MB a page)
    reduced to grey at half the linear resolution — legible down to the
    fractions and footnotes (tested 2026-11-25 on Bd 2 s. 420, 519). The
    split into < 100 MB parts was for GitHub's file limit while PDFs were
    committed; it is kept so new volumes match the stored ones. Written to
    the research library and recorded in the manifest (work_url = the nb.no
    item; the reduced file is not re-downloadable byte for byte)."""
    urn = VOLUMES[bd]
    vol_dir = _lib_dir(bd)
    vol_dir.mkdir(parents=True, exist_ok=True)
    out = vol_dir / f"{PDF_PREFIX}_{vol_dir.name}.pdf"
    stored = [d for d in (vol_dir, _dir(bd))
              if (d / out.name).exists() or list(d.glob(f"{PDF_PREFIX}_{vol_dir.name}_part*.pdf"))]
    if stored and not force:
        print(f"{vol_dir.name}: PDF already stored")
        return
    tmp_dir.mkdir(parents=True, exist_ok=True)
    src = tmp_dir / f"{vol_dir.name}_original.pdf"
    if not src.exists():
        # Download to a .part name and rename only when the whole body arrived:
        # a read timeout must never leave a truncated file under the final name.
        req = urllib.request.Request(f"https://www.nb.no/services/downloader?urn={urn}",
                                     headers={"User-Agent": USER_AGENT})
        dl = src.with_suffix(".download")
        for attempt in range(1, 5):
            try:
                with urllib.request.urlopen(req, timeout=900) as r, open(dl, "wb") as f:
                    shutil.copyfileobj(r, f)
                    want = r.headers.get("Content-Length")
                if want and int(want) != dl.stat().st_size:
                    raise OSError(f"short body: {dl.stat().st_size} of {want} bytes")
                dl.rename(src)
                break
            except Exception as exc:  # noqa: BLE001 — retry, then give the volume up
                print(f"{vol_dir.name}: download attempt {attempt}: {type(exc).__name__}: {exc}",
                      file=sys.stderr)
                dl.unlink(missing_ok=True)
                time.sleep(60 * attempt)
        else:
            print(f"{vol_dir.name}: PDF NOT fetched", file=sys.stderr)
            return
    if src.read_bytes()[:5] != b"%PDF-":
        print(f"{vol_dir.name}: downloader did not return a PDF", file=sys.stderr)
        src.unlink()
        return
    if as_served:
        # Stored byte for byte as the host serves it (curator 2026-11-26): the
        # sha256 in the manifest is then reproducible from the download URL.
        shutil.move(str(src), str(out))
        library.register(out.relative_to(LIBRARY_ROOT).as_posix(),
                         url=f"https://www.nb.no/services/downloader?urn={urn}",
                         fetched=time.strftime("%Y-%m-%d"))
        print(f"{vol_dir.name}: {out.stat().st_size / 1e6:.0f} MB stored as served")
        return
    part = out.with_suffix(".part.pdf")
    subprocess.run(
        ["gs", "-q", "-dNOPAUSE", "-dBATCH", "-sDEVICE=pdfwrite",
         "-sColorConversionStrategy=Gray", "-dProcessColorModel=/DeviceGray",
         "-dDownsampleColorImages=true", "-dDownsampleGrayImages=true",
         "-dColorImageResolution=200", "-dGrayImageResolution=200",
         "-dColorImageDownsampleType=/Bicubic", "-dGrayImageDownsampleType=/Bicubic",
         "-dColorImageDownsampleThreshold=1.0", "-dGrayImageDownsampleThreshold=1.0",
         f"-sOutputFile={part}", str(src)], check=True)
    part.rename(out)
    print(f"{vol_dir.name}: {src.stat().st_size / 1e6:.0f} MB -> {out.stat().st_size / 1e6:.0f} MB")
    if out.stat().st_size > 95e6:          # GitHub refuses files over 100 MB
        n = int(subprocess.run(["qpdf", "--show-npages", str(out)], check=True,
                               capture_output=True, text=True).stdout)
        parts = -(-out.stat().st_size // int(90e6))
        step = -(-n // parts)
        for i in range(parts):
            a, b = i * step + 1, min(n, (i + 1) * step)
            piece = vol_dir / f"{PDF_PREFIX}_{vol_dir.name}_part{i + 1}_pdf{a:03d}-{b:03d}.pdf"
            subprocess.run(["qpdf", str(out), "--pages", ".", f"{a}-{b}", "--", str(piece)], check=True)
        out.unlink()
        print(f"{vol_dir.name}: split into {parts} parts of <= {step} pages")
    for f in sorted(vol_dir.glob(f"{PDF_PREFIX}_{vol_dir.name}*.pdf")):
        library.register(f.relative_to(LIBRARY_ROOT).as_posix(),
                         fetched=time.strftime("%Y-%m-%d"))
    if not keep_original:
        src.unlink()


def retext_volume(bd) -> None:
    vol_dir = _dir(bd)
    manifest = json.loads((vol_dir / "_manifest.json").read_text())
    labels = {cv["@seeAlso"]["@id"].rsplit("/", 1)[-1]: cv.get("label", "")
              for cv in manifest["sequences"][0]["canvases"]}
    for xml_path in sorted(_alto_dir(bd).glob("*.xml")):
        page_id = xml_path.stem
        txt_path = vol_dir / "pages" / f"{page_id.rsplit('_', 1)[-1]}.txt"
        txt_path.write_text(f"[label {labels.get(page_id, '')}]\n"
                            + _alto_to_text(xml_path.read_text(encoding="utf-8")) + "\n",
                            encoding="utf-8")
    print(f"bd{bd}: re-rendered {len(list((vol_dir / 'pages').glob('*.txt')))} pages")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--collection", choices=sorted(COLLECTIONS), default="schou")
    ap.add_argument("--bd", type=_key, action="append",
                    help="volume key; omit for every volume of the collection")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--retext", action="store_true",
                    help="re-render pages/*.txt from the cached ALTO, no network")
    ap.add_argument("--pdf", action="store_true",
                    help="fetch the library's PDF and store a reduced grey copy (page images)")
    ap.add_argument("--as-served", action="store_true",
                    help="with --pdf: store the library's PDF unchanged (no reduction, no split)")
    ap.add_argument("--tmp", type=Path, default=Path("/tmp/schou_pdf"),
                    help="where the full-size PDF is kept while it is reduced")
    args = ap.parse_args()
    global VOLUMES, CACHE_DIR, PDF_PREFIX
    VOLUMES, CACHE_DIR, PDF_PREFIX = COLLECTIONS[args.collection]
    for bd in args.bd or list(VOLUMES):
        if args.pdf:
            fetch_pdf(bd, args.force, args.tmp, as_served=args.as_served)
        elif args.retext:
            retext_volume(bd)
        else:
            fetch_volume(bd, args.force)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
