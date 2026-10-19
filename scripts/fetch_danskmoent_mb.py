"""Harvest + parse danskmoent.dk's Mansfeld-Bûllner coin pages (mb/mbNNN.htm).

danskmoent.dk gives every medieval coin type of Mansfeld-Bûllner's catalogue
(MB, 1241-1375) a page of its own. The head of each page lines that MB number
up with four other catalogues, e.g. ``mb/mb577.htm``::

    Mansfeld-Bûllner 577; Christoffer 2. (1319-1332); Roskilde
    Hauberg: Christoffer 2. (1319-1332); Roskilde 15
    Kaaber 151-04; København 1341
    Sømod: D 553; Magnus Smek (1332-1360); Lund
    Grinder-Hansen: 1330-1339; Roskilde

The concordance page (``fetch_danskmoent_konkordans.py``) gives only
Hauberg↔MB number ranges per mint. These pages add what it lacks: the ruler and
mint each catalogue assigns, Kaaber's and Grinder-Hansen's dating, Sømod's
number, the variant notes (A, B, C …) and the literature. The catalogues do
not always agree — Sømod gives MB 577 to Magnus Smek and Grinder-Hansen dates
it 1330-1339, after Christoffer II's death — so the parse keeps each line
VERBATIM beside the structured reading and decides nothing between them
(CLAUDE.md §0b). Harvested 2026-10-17 to have the data, independent of any
decision on how a seed or absorb should use it.

Discovery: the per-ruler / per-mint index pages named in the concordance
(``konkord.json``, ``mb/<ruler>_<mint>.htm``) link their coins through an image
map; every coin page also links its neighbours («Forrige» / «Næste»), which
picks up a page no index map links. A link that answers 404 is recorded, not
dropped: MB 319 and 320 have no page.

Phase 1 (HARVEST) output: ``scripts/cache/danskmoent/mb/<page>.htm``
Phase 2 (SYNTHESIS) output: ``scripts/cache/danskmoent/mb/mb.json``

Run::

    .venv/bin/python scripts/fetch_danskmoent_mb.py              # fetch missing + parse
    .venv/bin/python scripts/fetch_danskmoent_mb.py --parse-only
    .venv/bin/python scripts/fetch_danskmoent_mb.py --refresh    # re-fetch everything
"""
from __future__ import annotations

import argparse
import html
import json
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib.paths import KONKORDANS_CACHE, MB_CACHE as CACHE_DIR  # noqa: E402

BASE = "https://www.danskmoent.dk/mb/"
OUT = CACHE_DIR / "mb.json"
MISSING = CACHE_DIR / "_missing.json"
USER_AGENT = (
    "Mozilla/5.0 (research; muentzfuesse project; non-commercial scholarly register)"
)
DELAY_S = 1.0
_COIN_RE = re.compile(r"^mb\d+[a-z]?\.htm$", re.I)


def _get(name: str) -> str | None:
    """Raw page as text, or None on 404. danskmoent serves latin-1."""
    req = urllib.request.Request(BASE + name, headers={"User-Agent": USER_AGENT})
    try:
        raw = urllib.request.urlopen(req, timeout=30).read()
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        raise
    return raw.decode("latin-1")


def _links(text: str) -> list[str]:
    hrefs = re.findall(r'href\s*=\s*"([^"#]+)"', text, re.I)
    return [h for h in hrefs if "/" not in h and h.lower().endswith(".htm")]


def _index_pages() -> list[str]:
    konk = json.loads((KONKORDANS_CACHE / "konkord.json").read_text())
    pages = []
    for row in konk.get("hauberg_mansfeld_bullner") or []:
        p = row.get("page") or ""
        if p.startswith("mb/"):
            pages.append(p[3:])
    return sorted(set(pages))


def harvest(refresh: bool) -> None:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    missing: dict[str, str] = {}
    queue: list[tuple[str, str]] = [(p, "konkord.json") for p in _index_pages()]
    seen: set[str] = set()
    fetched = 0
    while queue:
        name, via = queue.pop(0)
        if name in seen:
            continue
        seen.add(name)
        path = CACHE_DIR / name
        if path.exists() and not refresh:
            text = path.read_text(encoding="utf-8")
        else:
            text = _get(name)
            fetched += 1
            time.sleep(DELAY_S)
            if text is None:
                missing[name] = via
                continue
            path.write_text(text, encoding="utf-8")
        for link in _links(text):
            if _COIN_RE.match(link) and link not in seen:
                queue.append((link, name))
    # Numbers inside the MB run that no page links to: ask for each, so the
    # cache says whether the page is absent (404) or just unlinked.
    nums = sorted(int(re.sub(r"\D", "", n)) for n in seen if _COIN_RE.match(n))
    for n in range(nums[0], nums[-1] + 1) if nums else []:
        name = f"mb{n:03d}.htm" if n < 100 else f"mb{n}.htm"
        if name in seen or (CACHE_DIR / name).exists():
            continue
        text = _get(name)
        fetched += 1
        time.sleep(DELAY_S)
        if text is None:
            missing[name] = "probe (no page links it)"
        else:
            (CACHE_DIR / name).write_text(text, encoding="utf-8")
            seen.add(name)
    MISSING.write_text(json.dumps(dict(sorted(missing.items())), indent=1,
                                  ensure_ascii=False) + "\n")
    print(f"fetched {fetched} page(s); {len(seen) - len(missing)} cached, "
          f"{len(missing)} link(s) answer 404")


def _clean(fragment: str) -> str:
    txt = re.sub(r"<[^>]*>", " ", fragment)
    txt = html.unescape(txt).replace("\xa0", " ")
    return re.sub(r"\s+", " ", txt).strip()


_REIGN = r"\((\d{4})\s*-\s*(\d{4})\)"
_MB_RE = re.compile(r"^Mansfeld-B.llner\s+(\d+[a-z]?)\s*[;,]?\s*(.*)$", re.I)
_HBG_RE = re.compile(r"^Hauberg\s*:\s*(.*?)\s*(?:" + _REIGN + r")?\s*[;-]\s*(.+?)\s+(\d+[a-z]?|-)$", re.I)
_KAABER_RE = re.compile(r"^Kaaber\s*:?\s*(\S+)\s*;\s*(.+?)\s+(\d{4})(?:/(\d{2}))?$", re.I)
_SOMOD_RE = re.compile(r"^S.mod\s*:?\s*((?:D|JS)\s*\d+[a-z]?)\s*;\s*(.*?)\s*(?:" + _REIGN + r")?\s*[;-]\s*([^.]+?)\.?(?:\s+(.*))?$", re.I)
# Grinder-Hansen dates by decade, printed «1330-1339», «1241-50» or with the
# mint first («Roskilde; 1241-1250»). An abbreviated end year takes the
# century of the start (1241-50 → 1250); `raw` keeps the printed form.
_GH_SPAN = r"(\d{4})\s*-\s*(\d{2,4})"
_GH_RE = re.compile(r"^Grinder-Hansen\s*:\s*" + _GH_SPAN + r"\s*[;-]\s*(.+)$", re.I)
_GH_REV_RE = re.compile(r"^Grinder-Hansen\s*:\s*([^;\d]+?)\s*;\s*" + _GH_SPAN + r"\s*$", re.I)
# «ikke!» (not in that catalogue), «udgår» (dropped), «-» (none).
_ABSENT_RE = re.compile(r"^[^:]+:\s*(ikke!?|udg[aå]r|-)\s*$", re.I)
_LABELS = (("mansfeld", "mansfeld_bullner"), ("hauberg", "hauberg"),
           ("kaaber", "kaaber"), ("sømod", "somod"), ("grinder", "grinder_hansen"))
_RULER_MINT_RE = re.compile(r"^(.*?)\s*(?:" + _REIGN + r")?\s*[;-]\s*(.+)$")


def _span(a: str, b: str) -> list[int]:
    lo = int(a)
    hi = int(b) if len(b) == 4 else int(a[: 4 - len(b)] + b)
    return [lo, hi]


def _ruler_mint(rest: str) -> dict:
    m = _RULER_MINT_RE.match(rest)
    if not m:
        return {}
    out = {"ruler": m.group(1).strip(" ;-") or None, "mint": m.group(4).strip()}
    if m.group(2):
        out["reign"] = [int(m.group(2)), int(m.group(3))]
    return out


def _line(text: str) -> dict:
    """One head line → {catalogue, raw, …}. `raw` is always kept verbatim."""
    d: dict = {"raw": text}
    low = text.lower()
    label = next((k for p, k in _LABELS if low.startswith(p)), None)
    if label:
        d["catalogue"] = label
    else:
        m = re.match(r"^([^:]+):", text)
        d["catalogue"] = "other"
        if m:
            d["label"] = m.group(1).strip()
    if _ABSENT_RE.match(text):
        d["absent"] = True
    elif m := _MB_RE.match(text):
        d.update(number=m.group(1), **_ruler_mint(m.group(2)))
    elif label == "hauberg" and (m := _HBG_RE.match(text)):
        d.update(ruler=m.group(1).strip() or None, mint=m.group(4).strip(),
                 number=None if m.group(5) == "-" else m.group(5))
        if m.group(2):
            d["reign"] = [int(m.group(2)), int(m.group(3))]
    elif label == "kaaber" and (m := _KAABER_RE.match(text)):
        d.update(number=m.group(1), place=m.group(2).strip(), year=int(m.group(3)))
        if m.group(4):
            d["year_to"] = int(m.group(3)[:2] + m.group(4))
    elif label == "somod" and (m := _SOMOD_RE.match(text)):
        d.update(number=re.sub(r"\s+", " ", m.group(1)), ruler=m.group(2).strip() or None,
                 mint=m.group(5).strip())
        if m.group(3):
            d["reign"] = [int(m.group(3)), int(m.group(4))]
        if m.group(6):
            d["remark"] = m.group(6).strip()
    elif label == "grinder_hansen" and (m := _GH_RE.match(text)):
        d.update(dating=_span(m.group(1), m.group(2)), mint=m.group(3).strip())
    elif label == "grinder_hansen" and (m := _GH_REV_RE.match(text)):
        d.update(dating=_span(m.group(2), m.group(3)), mint=m.group(1).strip())
    return d


def parse_page(name: str, text: str) -> dict:
    title = re.search(r"<TITLE>(.*?)</TITLE>", text, re.S | re.I)
    # The head list is the first <UL> naming Mansfeld-Bûllner. It usually
    # follows the <H1> directly, but some pages put a subtitle («(uden
    # måner)») or table markup between them (mb285, mb548).
    head_ul = next((m for m in re.finditer(r"<UL>(.*?)</UL>", text, re.S | re.I)
                    if re.search(r"Mansfeld-B", m.group(1), re.I)), None)
    lines = []
    if head_ul:
        lines = [_clean(li) for li in re.split(r"<LI>", head_ul.group(1), flags=re.I)]
        lines = [x for x in lines if x]
    rec = {"page": name, "url": BASE + name,
           "title": _clean(title.group(1)) if title else None,
           "lines": [_line(x) for x in lines]}
    sub = re.search(r"</H1>\s*(?:<p>)?\s*\(([^)<]*)\)", text, re.S | re.I)
    if sub:
        rec["subtitle"] = _clean(sub.group(1))
    body = text[head_ul.end():] if head_ul else text
    lit = re.search(r"<B>\s*Litteratur:?\s*</B>\s*<UL>(.*?)</UL>", body, re.S | re.I)
    if lit:
        rec["literature"] = [x for x in (_clean(li) for li in re.split(r"<LI>", lit.group(1), flags=re.I)) if x]
        body = body[:lit.start()]
    notes = _clean(re.split(r"<A HREF=\"\.\./index", body, flags=re.I)[0])
    notes = re.sub(r"Tilbage til .*$", "", notes).strip()
    if notes:
        rec["notes"] = notes
    rec["images"] = re.findall(r'<img[^>]+src="([^"]+\.(?:jpg|gif))"', text, re.I)
    rec["images"] = [i for i in rec["images"] if not re.search(r"(^|/)[12]\.gif$|forkert\.gif", i)]
    for label in ("Forrige", "Næste"):
        m = re.search(r'<a href="([^"]+)"><img[^>]*alt="' + label, text, re.I)
        if m:
            rec["prev" if label == "Forrige" else "next"] = m.group(1)
    back = re.findall(r'<A HREF="([^".]+_[^"]+\.htm)">Tilbage til ([^<]+)</A>', text, re.I)
    if back:
        rec["index_page"], rec["index_label"] = back[-1][0], _clean(back[-1][1])
    return rec


def parse() -> None:
    recs = []
    for path in sorted(CACHE_DIR.glob("*.htm"), key=lambda p: (len(p.stem), p.stem)):
        if not _COIN_RE.match(path.name):
            continue
        recs.append(parse_page(path.name, path.read_text(encoding="utf-8")))
    by_cat: dict[str, int] = {}
    unparsed = 0
    for r in recs:
        for ln in r["lines"]:
            c = ln.get("catalogue")
            if c:
                by_cat[c] = by_cat.get(c, 0) + 1
            if c != "other" and len(ln) <= 2:
                unparsed += 1
    missing = json.loads(MISSING.read_text()) if MISSING.exists() else {}
    OUT.write_text(json.dumps({
        "source": BASE,
        "harvested": "2026-10-17",
        "pages": len(recs),
        "missing_pages": missing,
        "coins": recs,
    }, indent=1, ensure_ascii=False) + "\n")
    print(f"parsed {len(recs)} coin page(s) → {OUT.name}; lines by catalogue {by_cat}; "
          f"{unparsed} line(s) kept raw only")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--parse-only", action="store_true")
    ap.add_argument("--refresh", action="store_true")
    a = ap.parse_args()
    if not a.parse_only:
        harvest(a.refresh)
    parse()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
