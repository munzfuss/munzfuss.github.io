#!/usr/bin/env python3
"""Phase 2 (SYNTHESIS) — per-coin tables of the «Metallanalyser av mynt» appendices.

Source: Numismatiska forskningsgruppen, Stockholm University, series
«Metallanalyser av mynt». Each issue has an APPENDIX that lists every assayed
coin on one line (number, ruler / mint / denomination / date / catalogue
number, weight, lod, Ag, Cu, Zn, Sn, Sb, Au, Pb) plus photos. Phase-1 cache
(PDF + `pdftotext -layout` extract with a provenance header) lives in
`scripts/cache/danskmoent/hans_1481_1513/`; see docs/research/eriksson_2017_assays.md §7–§8.

This parser reads the extract text and writes one JSON sidecar per issue
(`<stem>.parsed.json` beside the extract): one record per coin, the printed
values kept as printed (decimal comma → float, nothing rounded or corrected —
the slips found in the article tables are NOT the appendix's, §7 of the note).
Only Ag is calibrated (editorial, s. 17–18); the other metals are kept raw.

The parse is checked against the row count each appendix ends on; a mismatch
aborts with exit 1 rather than writing a partial sidecar.

Usage::

    python scripts/parse_su_metallanalyser.py [--issue 2017_1]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lib.paths import HARVEST_ROOT  # noqa: E402

CACHE = HARVEST_ROOT / "danskmoent" / "hans_1481_1513"

# issue → (extract stem, expected number of coin rows, author, title)
ISSUES = {
    "2016_1": ("heljeback_2016_metallanalyser_1400_1448_appendix", 145,
               "Heljeback", "Haltanalyser av danska mynt ca 1400-1448"),
    "2017_1": ("eriksson_2017_metallanalyser_appendix", 118,
               "Eriksson", "Haltanalyser av danska mynt 1448-1523"),
    "2017_3": ("lindblad_2017_metallanalyser_gotland_appendix", 181,
               "Lindblad", "Haltanalyser av gotländska mynt ca 1150-1554"),
}

_NUM = r"\d+,\d+"
# number · middle (who / where / what / when / catalogue) · weight [flag] ·
# lod · Ag · Cu · tail (minor metals, positions not reliable: empty cells
# collapse in the text layer).
_ROW = re.compile(
    rf"^\s*(?P<nr>\d+)\s+(?P<mid>.+?)\s+(?P<w>{_NUM})\s*(?P<flag>f|ks)?"
    rf"(?:\s+(?P<lod>\d+)\s+(?P<ag>{_NUM})\s+(?P<cu>{_NUM}|\d+,\d)(?P<tail>.*))?\s*$"
)
_MID_2017_1 = re.compile(
    r"^(?P<ruler>KI|RR|H|KII)\s+(?P<mint>\S+)\s+(?P<denom>.+?)\s+"
    r"(?P<year>u\.å\.(?:\s*\([^)]*\))?|\d{4})\s+(?P<cat>\S+)$"
)
_MID_2016_1 = re.compile(
    r"^(?P<ruler>EaP|EAP|KaB|RR)\s+(?P<mint>\S+)\s+(?P<denom>.+?)\s+"
    r"(?P<cat>\d+(?:\s*/\s*\d+)*)(?:\s+(?P<var>.+))?$"
)
_DATE_2017_3 = (r"(?:\d{4}(?:/\d{2})?[‐-]\d{4}(?:/\d{2})?|[Cc]a\s+\d{4}|\d{4}[‐-]tal|\(\d{4}\)|u\.å\.|\d{4})")
_MID_2017_3 = re.compile(
    rf"^(?P<mint>\S+)\s+(?P<denom>.+?)\s+(?P<year>{_DATE_2017_3})(?:\s+(?P<cat>.+))?$"
)


def _f(s: str | None) -> float | None:
    return float(s.replace(",", ".")) if s else None


def parse_issue(issue: str) -> list[dict]:
    stem, expected, _, _ = ISSUES[issue]
    text = (CACHE / f"{stem}.extract.txt").read_text(encoding="utf-8")
    mid_re = {"2017_1": _MID_2017_1, "2016_1": _MID_2016_1,
              "2017_3": _MID_2017_3}[issue]
    rows: list[dict] = []
    for line in text.splitlines():
        if "JPG" in line:
            continue
        m = _ROW.match(line)
        if not m:
            continue
        mid = re.sub(r"\s{2,}", " ", m["mid"].strip())
        mm = mid_re.match(mid)
        if not mm:
            continue
        rec = {"issue": issue, "nr": int(m["nr"]), **{
            k: (v.strip() if isinstance(v, str) else v)
            for k, v in mm.groupdict().items()}}
        rec["weight_g"] = _f(m["w"])
        rec["weight_flag"] = m["flag"]
        rec["lod"] = int(m["lod"]) if m["lod"] else None
        rec["ag_pct"] = _f(m["ag"])
        rec["cu_pct"] = _f(m["cu"])
        rec["minor_metals_raw"] = (m["tail"] or "").split() or None
        rec["line"] = line.rstrip()
        rows.append(rec)
    nrs = [r["nr"] for r in rows]
    if len(rows) != expected or nrs != list(range(1, expected + 1)):
        missing = sorted(set(range(1, expected + 1)) - set(nrs))
        raise SystemExit(f"{issue}: parsed {len(rows)} rows, expected "
                         f"{expected}; missing {missing[:20]}")
    return rows


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--issue", choices=sorted(ISSUES))
    args = ap.parse_args()
    for issue in ([args.issue] if args.issue else sorted(ISSUES)):
        rows = parse_issue(issue)
        stem, _, author, title = ISSUES[issue]
        out = CACHE / f"{stem}.parsed.json"
        out.write_text(json.dumps({
            "issue": issue, "author": author, "title": title,
            "series": "Metallanalyser av mynt (Numismatiska forskningsgruppen, "
                      "Stockholm University)",
            "rows": rows}, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        print(f"{issue}: {len(rows)} rows -> {out.name}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
