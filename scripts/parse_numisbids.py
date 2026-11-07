#!/usr/bin/env python3
"""NumisBids lot pages — Phase 2 SYNTHESIS.

Reads `scripts/cache/numisbids/raw/<sale>_<lot>.json` (the page text of one
lot, captured in a real browser session — numisbids answers scripted fetches
with a Cloudflare challenge) and writes one typed sidecar per lot,
`scripts/cache/numisbids/<sale>_<lot>.json`, plus `_parsed_index.json`.

Broader than the project's scope on purpose: every field the lot text gives
is kept, the seed builder decides what to use.

Lot text shape (Emporium Hamburg, the first source, 2026-11-07)::

    Estimate: 70 EUR
    Price realized: 100 EUR
    …
    SCHLESWIG-HOLSTEIN-GOTTORP, Friedrich IV., 1694-1702        ← heading
    IIII Schilling 1701, 1702, Tönning. 2,76g und 2,78g. Lange 438, 438A, 2 Stk., ss und f.vz

Usage::

    python scripts/parse_numisbids.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib.paths import NUMISBIDS_CACHE  # noqa: E402

RAW = NUMISBIDS_CACHE / "raw"

_ROMAN = {"I": 1, "V": 5, "X": 10, "L": 50, "C": 100}


def roman_to_int(s: str) -> int | None:
    if not s or any(ch not in _ROMAN for ch in s):
        return None
    total = 0
    for i, ch in enumerate(s):
        v = _ROMAN[ch]
        nxt = _ROMAN[s[i + 1]] if i + 1 < len(s) else 0
        total += -v if v < nxt else v
    return total


def parse_sale(sale_text: str) -> dict:
    lines = [x.strip() for x in (sale_text or "").splitlines() if x.strip()]
    out = {"auction_house": lines[0] if lines else None,
           "auction_no": None, "auction_date": None}
    for ln in lines[1:]:
        m = re.match(r"(?:Auction|Sale)\s+(\S+)\s+(.+)$", ln)
        if m:
            out["auction_no"] = m.group(1)
            out["auction_date"] = re.sub(r"\s+", " ", m.group(2)).strip()
            break
    return out


def parse_lot(lot_text: str) -> dict:
    lines = [x.strip() for x in (lot_text or "").splitlines()]
    out: dict = {"estimate": None, "realized": None, "heading": None,
                 "description": None}
    for ln in lines:
        m = re.match(r"Estimate:\s*(.+)$", ln)
        if m:
            out["estimate"] = m.group(1).strip()
        m = re.match(r"Price realized:\s*(.+)$", ln)
        if m:
            out["realized"] = m.group(1).strip()
    try:
        i = next(k for k, ln in enumerate(lines) if ln.startswith("Share this lot"))
        body = [ln for ln in lines[i + 1:] if ln]
    except StopIteration:
        body = []
    if body:
        out["heading"] = body[0]
        out["description"] = " ".join(body[1:]) or None
    desc = out["description"] or ""
    # Denomination: leading Roman or Arabic figure + word(s) before the year.
    m = re.match(r"([IVXLC]+|\d+(?:/\d+)?)\s+([A-Za-zÄÖÜäöüß]+(?:\s[A-Za-zÄÖÜäöüß]+)?)\s+(?=\d{4}|o\.\s*J\.)", desc)
    if m:
        num = roman_to_int(m.group(1)) if m.group(1).isalpha() else m.group(1)
        out["denomination_printed"] = f"{m.group(1)} {m.group(2)}"
        out["denomination"] = f"{num} {m.group(2)}" if num is not None else None
    years = [int(y) for y in re.findall(r"\b(1[0-9]{3})\b", desc.split(".")[0])]
    out["years"] = years
    # Mint: the comma segment after the years, before the first full stop.
    first = desc.split(".")[0]
    segs = [s.strip() for s in first.split(",")]
    out["mint_printed"] = (segs[-1] if len(segs) > 1 and not re.search(r"\d", segs[-1])
                           else None)
    out["weights_g"] = [float(w.replace(",", ".")) for w in
                        re.findall(r"(\d+,\d+)\s*g\b", desc)]
    refs: dict[str, list[str]] = {}
    for cat, nums in re.findall(r"\b(Lange|Hede|KM|Schou|Sieg|Behrens|Jaeger|Dav)\.?\s+((?:[\dA-Za-z.]+(?:,\s*)?)+?)(?=,\s*\d+\s*Stk|,\s*[a-z]|\.|$)", desc):
        refs.setdefault(cat, []).extend(n.strip() for n in nums.split(",") if n.strip())
    out["refs"] = refs
    m = re.search(r"\b(\d+)\s*Stk\b", desc)
    out["pieces"] = int(m.group(1)) if m else 1
    m = re.search(r"Stk\.,\s*(.+)$", desc)
    out["grade_printed"] = m.group(1).strip() if m else None
    # Heading «TERRITORY, Ruler, reign».
    hs = [s.strip() for s in (out["heading"] or "").split(",")]
    out["territory"] = hs[0] if hs else None
    out["ruler"] = hs[1] if len(hs) > 1 else None
    out["reign"] = hs[2] if len(hs) > 2 else None
    return out


def main() -> int:
    index = {}
    for p in sorted(RAW.glob("*.json")):
        raw = json.loads(p.read_text("utf-8"))
        rec = {"id": p.stem, "url": raw["url"], "sale_id": raw["sale_id"],
               "lot_no": raw["lot_no"], "captured": raw.get("captured"),
               **parse_sale(raw.get("sale_text")), **parse_lot(raw.get("lot_text"))}
        out = NUMISBIDS_CACHE / f"{p.stem}.json"
        out.write_text(json.dumps(rec, ensure_ascii=False, indent=2) + "\n", "utf-8")
        index[p.stem] = {"heading": rec["heading"], "denomination": rec.get("denomination"),
                         "years": rec["years"]}
        print(f"  {p.stem}: {rec['heading']} | {rec.get('denomination')} {rec['years']} "
              f"{rec['mint_printed']} {rec['weights_g']} {rec['refs']}")
    (NUMISBIDS_CACHE / "_parsed_index.json").write_text(
        json.dumps(index, ensure_ascii=False, indent=2) + "\n", "utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
