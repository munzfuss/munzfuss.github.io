"""Cache Schou, *Chronologisk Register over de Kongelige Forordninger og
aabne Breve …* (from 1670) from the Norwegian National Library (nb.no
digibok, public domain, «accessAllowedFrom: EVERYWHERE»).

Per volume: the IIIF manifest, then every page's ALTO OCR
(``metadata/<urn>/altos/<urn>_<page>``) saved raw as XML plus a plain-text
rendering, so the register can be grepped for coinage instruments and a
page can be quoted with its printed page label.

    scripts/cache/schou/bd<N>/_manifest.json       IIIF manifest as served
    scripts/cache/schou/bd<N>/alto/<urn>_<page>.xml raw ALTO
    scripts/cache/schou/bd<N>/pages/<page>.txt     one line per TextLine,
                                                   header line = printed label

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
import sys
import time
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib.paths import SCHOU_CACHE as CACHE_DIR  # noqa: E402

VOLUMES = {
    1: "URN:NBN:no-nb_digibok_2014050824003",
    2: "URN:NBN:no-nb_digibok_2014050824008",
    3: "URN:NBN:no-nb_digibok_2014050824016",
    4: "URN:NBN:no-nb_digibok_2014050824018",
    5: "URN:NBN:no-nb_digibok_2014050824017",
}
API = "https://api.nb.no/catalog/v1"
USER_AGENT = "Mozilla/5.0 (research; muentzfuesse project; non-commercial scholarly register)"
SLEEP_SECS = 0.25


def _get(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    return urllib.request.urlopen(req, timeout=60).read()


def _alto_to_text(xml: str) -> str:
    """One output line per ALTO TextLine; words joined by single spaces.
    HYP (hyphenation) elements are kept as the printed hyphen."""
    lines: list[str] = []
    for tl in re.finditer(r"<TextLine\b.*?</TextLine>", xml, re.S):
        words = re.findall(r'<String\b[^>]*\bCONTENT="([^"]*)"', tl.group(0))
        if words:
            lines.append(html.unescape(" ".join(words)))
    return "\n".join(lines)


def fetch_volume(bd: int, force: bool) -> None:
    urn = VOLUMES[bd]
    vol_dir = CACHE_DIR / f"bd{bd}"
    alto_dir, pages_dir = vol_dir / "alto", vol_dir / "pages"
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
    print(f"bd{bd}: done — {len(list(pages_dir.glob('*.txt')))} page texts")


def retext_volume(bd: int) -> None:
    vol_dir = CACHE_DIR / f"bd{bd}"
    manifest = json.loads((vol_dir / "_manifest.json").read_text())
    labels = {cv["@seeAlso"]["@id"].rsplit("/", 1)[-1]: cv.get("label", "")
              for cv in manifest["sequences"][0]["canvases"]}
    for xml_path in sorted((vol_dir / "alto").glob("*.xml")):
        page_id = xml_path.stem
        txt_path = vol_dir / "pages" / f"{page_id.rsplit('_', 1)[-1]}.txt"
        txt_path.write_text(f"[label {labels.get(page_id, '')}]\n"
                            + _alto_to_text(xml_path.read_text(encoding="utf-8")) + "\n",
                            encoding="utf-8")
    print(f"bd{bd}: re-rendered {len(list((vol_dir / 'pages').glob('*.txt')))} pages")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--bd", type=int, action="append", required=True)
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--retext", action="store_true",
                    help="re-render pages/*.txt from the cached ALTO, no network")
    args = ap.parse_args()
    for bd in args.bd:
        if args.retext:
            retext_volume(bd)
        else:
            fetch_volume(bd, args.force)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
