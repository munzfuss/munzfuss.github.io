#!/usr/bin/env python3
"""Tietjen + Co. auction catalogues — Phase 2 SYNTHESIS.

Reads each cached catalogue PDF under `scripts/cache/auctions/tietjen/`
(`tietjen_<year>_auktion_<n>.pdf`), lays every page out with
`pdftotext -layout` (the lot lines are two-column: description left, grade
and estimate right) and writes one typed list of lots per catalogue,
`scripts/cache/auctions/tietjen/auktion_<n>_lots.json`.

Every lot is kept (broader than the project's scope on purpose); the seed
builder decides which lots to use. Per lot: number, «*» (illustrated on the
plates), the section heading it stands under («LÜBECK»,
«SCHLESWIG-HOLSTEIN», …), the description joined across lines, grade,
rarity («R»), estimate, weights («27,18 g»), catalogue numbers (Behr., Dav.,
J., Gaed., Lange, Hede, KM, Kunzel, Friedb.), years, mint mark («Mz. JJJ»),
the denomination (the words before the first year) and the PDF page.

Usage::

    python scripts/parse_tietjen.py
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib.paths import HARVEST_ROOT  # noqa: E402

CACHE = HARVEST_ROOT / "auctions" / "tietjen"

LOT_RE = re.compile(r"^(\d{1,4})(\*?)\s{2,}(\S.*)$")
TAIL_RE = re.compile(r"\s{2,}(?:(R{1,3})\s+)?([a-zA-Z][\w\- ]{0,14}?)?\s+([\d.]+[.,][-–])\s*$")
HEADING_RE = re.compile(r"^[A-ZÄÖÜ][A-ZÄÖÜ .,\-•&/()]{3,}$")
REF_RE = re.compile(
    r"\b(Behr|Dav|J|Gaed|Lange|Hede|KM|Kunzel|Friedb|Gaett)\.?\s+([0-9][\w./]*|–)")
WEIGHT_RE = re.compile(r"(\d+,\d+)\s*g\b")
YEAR_RE = re.compile(r"\b(1[0-9]{3})\b")
MZ_RE = re.compile(r"\bMz\.\s+([A-ZÄÖÜ]{1,4})\b")


def pages_layout(pdf: Path) -> list[str]:
    out = subprocess.run(["pdftotext", "-layout", str(pdf), "-"],
                         capture_output=True, text=True, check=True).stdout
    return out.split("\f")


def parse_catalogue(pdf: Path) -> list[dict]:
    lots: list[dict] = []
    section = None
    cur: dict | None = None

    def close():
        nonlocal cur
        if cur is None:
            return
        lines = cur.pop("_lines")
        last = lines[-1]
        m = TAIL_RE.search(last)
        if m:
            cur["rarity"] = m.group(1)
            cur["grade"] = (m.group(2) or "").strip() or None
            cur["estimate"] = m.group(3)
            lines[-1] = last[:m.start()]
        text = " ".join(x.strip() for x in lines if x.strip())
        text = re.sub(r"(\w)- (\w)", r"\1\2", text)
        cur["text"] = text
        cur["weights_g"] = [float(w.replace(",", ".")) for w in WEIGHT_RE.findall(text)]
        refs: dict[str, list[str]] = {}
        for cat, num in REF_RE.findall(text):
            refs.setdefault(cat, []).append(num.rstrip("."))
        cur["refs"] = refs
        first = text.split(".")[0]
        cur["years"] = [int(y) for y in YEAR_RE.findall(first)]
        m = re.match(r"(.+?)\s+(?=1[0-9]{3}\b|o\.\s*J\.)", text)
        cur["denomination"] = m.group(1).strip() if m else None
        m = MZ_RE.search(text)
        cur["mint_mark"] = m.group(1) if m else None
        lots.append(cur)
        cur = None

    for pno, page in enumerate(pages_layout(pdf), start=1):
        for raw in page.splitlines():
            line = raw.rstrip()
            if not line.strip():
                continue
            m = LOT_RE.match(line)
            if m:
                close()
                cur = {"lot": int(m.group(1)), "illustrated": bool(m.group(2)),
                       "section": section, "pdf_page": pno, "_lines": [m.group(3)]}
                continue
            s = line.strip()
            lead = len(line) - len(line.lstrip(" "))
            if ((lead == 0 or lead >= 8) and HEADING_RE.match(s)
                    and not re.search(r"\d", s) and not s.endswith(".")):
                close()
                section = s
                continue
            if cur is not None and line.startswith(" "):
                cur["_lines"].append(s)
    close()
    return lots


def main() -> int:
    for pdf in sorted(CACHE.glob("tietjen_*_auktion_*.pdf")):
        n = re.search(r"auktion_(\d+)", pdf.stem).group(1)
        lots = parse_catalogue(pdf)
        out = CACHE / f"auktion_{n}_lots.json"
        out.write_text(json.dumps({"catalogue": pdf.name, "auction": n, "lots": lots},
                                  ensure_ascii=False, indent=1) + "\n", "utf-8")
        print(f"  {pdf.name}: {len(lots)} lots → {out.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
