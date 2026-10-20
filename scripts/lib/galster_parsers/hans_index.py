"""Kong Hans index (danskmoent.dk/hans.htm) — the rows WITHOUT a coin page.

hans.htm lists Hans's whole coin series by denomination, one ``<LI>`` per
Galster number:

    <A HREF="hvid.htm">Hvid</A>
    <UL>
    <LI><A HREF="hansg31.htm">U.år, Malmø. Forside: …</A> (Galster 31, Schou 124-167)
    <LI>U.år (Unik), Bergen (Norge). Forside: … (Galster 152, Schou 170, …)

A row whose text is a link has its own coin page, which the standard parser
reads. A row WITHOUT a link (Galster 148, 150, 152, 154, 156, 158, 160-162,
230-232, 235, 237) exists nowhere else on the site — probed 2026-10-20 under
norge/hansg<N>, norge/nha_g<N>, fr/hg<N>, hansg<N>, all 404 — so this index
row is the only record and becomes one coin record here. Nested sub-variant
rows («A) …», under a linked row) belong to that row's page and are skipped.
"""
from __future__ import annotations

import re
from html import unescape
from pathlib import Path

from .standard import _extract_refs_from_paren_content, _parse_litteratur

_SECTION_RE = re.compile(
    r'<A\s+HREF="[^"]+"\s*>(?P<denom>[^<]+)</A>\s*<UL>(?P<body>.*?)</UL>\s*<P>',
    re.IGNORECASE | re.DOTALL,
)
_LI_RE = re.compile(r"<LI>(?P<li>.*?)(?=<LI>|</UL>|$)", re.IGNORECASE | re.DOTALL)
_REFS_RE = re.compile(r"\((?P<refs>Galster\s+\d+[^()]*(?:\([^)]*\)[^()]*)*)\)\)?\s*$")
_MINT_RE = re.compile(
    r"^(?:U\.\s*år\.?\s*(?:\([RU][RSUnik]*\))?\s*,\s*)?"
    r"(?P<mint>[A-ZÆØÅ][\wæøå]+)(?:\s*\((?P<country>Norge|Sverige|Gotland)\))?",
)


def _text(fragment: str) -> str:
    t = re.sub(r"<[^>]+>", " ", fragment)
    return re.sub(r"\s+", " ", unescape(t)).strip()


def parse_coins(html: str) -> list[dict]:
    coins: list[dict] = []
    for sec in _SECTION_RE.finditer(html):
        denom = _text(sec.group("denom"))
        # Only top-level LIs: drop nested <UL>…</UL> blocks (sub-variants).
        body = re.sub(r"<UL>.*?</UL>", "", sec.group("body"),
                      flags=re.IGNORECASE | re.DOTALL)
        for li in _LI_RE.finditer(body):
            raw = li.group("li")
            if re.match(r"\s*<A\s+HREF", raw, re.IGNORECASE):
                continue                               # has its own coin page
            text = _text(raw)
            rm = _REFS_RE.search(text)
            if not rm:
                continue
            # «mangler hos Schou og Schive» (= absent from those catalogues)
            # names two catalogues without an index; dropped before the
            # keyword-run split, which would otherwise read it as values.
            ref_text = re.sub(
                r",?\s*mangler hos (?:Schou|Schive)(?:\s+og\s+(?:Schou|Schive))?",
                "", rm.group("refs"), flags=re.IGNORECASE)
            refs = _extract_refs_from_paren_content(ref_text)
            head = text[: rm.start()].strip()
            undated = bool(re.match(r"U\.\s*år", head, re.IGNORECASE))
            years = re.findall(r"(?<!\d)1[45]\d{2}(?!\d)", head.split(".", 1)[0])
            mm = _MINT_RE.match(head)
            country = mm.group("country") if mm else None
            coins.append({
                "ruler": "Hans",
                "ruler_volume": "hg",
                "galster_number": (re.match(r"\d+[A-Z]?", refs.get("galster") or "")
                                   or [None])[0],
                "denomination": denom,
                "year_label": ", ".join(years) if years else ("u.år" if undated else None),
                "mint": mm.group("mint") if mm else None,
                "sub_realm": {"Norge": "norway", "Gotland": "gotland"}.get(country or ""),
                "description": head,
                "catalog_refs": refs,
                "specs": {},
            })
    return coins


def parse_page(html_path: Path, text: str) -> dict:
    html = html_path.read_text(encoding="utf-8", errors="replace")
    url = "https://www.danskmoent.dk/" + html_path.name.replace("_", "/", 1)
    coins = parse_coins(html)
    for c in coins:
        c.update({"source_file": html_path.name, "source_url_hint": url,
                  "page_shape": "hans_index"})
    return {
        "source_file": html_path.name,
        "source_url_hint": url,
        "page_shape": "hans_index",
        "coins": coins,
        "litteratur": _parse_litteratur(text),
        "raw_text_excerpt": text[:2000],
    }
