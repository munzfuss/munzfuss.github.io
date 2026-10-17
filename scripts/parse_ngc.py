#!/usr/bin/env python3
"""NGC World Coin Price Guide — Phase 2 SYNTHESIS.

Reads the Phase-1 harvest records (``scripts/cache/ngc/<region>/cuid_<N>.json``,
written by the browser loop via ``ngc_receiver.py``) and emits a typed sidecar
``cuid_<N>.parsed.json`` per coin type.

The whole point of this phase is the **``Note:`` field**, which is where NGC's
real value for this project sits. It is free text, but highly patterned, and it
carries the catalogue keys the rest of our sources do not give us:

    Ref. B-805a; Dav. 623. Varieties exist.
    Ref. B-136e; Dav. LS328. Prev. KM#16. Broad flan. Arms of Mayor Gotthard...
    Ref. B#317-25, 326b,c.
    Ref. B-471, 472. Varieties exist. Previous KM#9. Dreiling.

**Behrens** (``B-###`` / ``B####``) is the load-bearing Lübeck catalogue key we
otherwise hold only on paper, and ``Previous KM#`` is an explicit Krause
renumbering trail that feeds the §9.4 index-graph work and the §13.6
KM#-inflation problem.

**Nothing is discarded.** Every span the parser does not claim is preserved
verbatim in ``note_residual``, and ``note_raw`` always keeps the original. A
parser that silently drops what it does not understand would quietly corrupt
the record (CLAUDE.md §0b); an honest leftover is auditable.

Usage::

    python scripts/parse_ngc.py --region 'LÜBECK' [--force] [--stats]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from fetch_ngc import region_dir  # noqa: E402

# --- Note-field patterns -------------------------------------------------
# Behrens: "B-471, 472" / "B-805b,c" / "B#317-25, 326b,c" / "B-186. 187"
_BEHRENS_HEAD = re.compile(r"\bB[-#]\s?(\d[\w,.\-\s]*?)(?=(?:;|$|\.\s+[A-Z(]|\bDav\b|\bFr\b|\bPrev))",
                           re.IGNORECASE)
_DAV = re.compile(r"\bDav\.?\s*#?\s*((?:LS)?[A-Z]?\d+[A-Z]?)", re.IGNORECASE)
_FR = re.compile(r"\bFr\.?\s*(\d+[A-Za-z]?)")
_PREV_KM = re.compile(r"\bPrev(?:ious)?\.?\s*KM\s*#?\s*([\w.]+)", re.IGNORECASE)
_PREV_FR = re.compile(r"\bPrev(?:ious)?\.?\s*Fr\.?\s*#?\s*([\w.]+)", re.IGNORECASE)
_BARE_KM = re.compile(r"(?<!Prev)(?<!Previous)\bKM\s*#\s*([\w.]+)", re.IGNORECASE)

# Descriptive flags that matter for §9 (fabric / strike) and §9.4 (variants).
# These are SIGNALS for the curator's §9 pass, never verdicts on their own —
# §9.1 is explicit that a marker alone does not exclude a coin.
_FLAGS = {
    "varieties_exist": re.compile(r"\bVarieties exist\b", re.I),
    "klippe": re.compile(r"\bKlippe\b", re.I),
    "broad_flan": re.compile(r"\bBroad flan\b", re.I),
    "thick_flan": re.compile(r"\bThick flan\b", re.I),
    "restrike": re.compile(r"\bRestrike\b", re.I),
    "joint_issue": re.compile(r"\b(?:Issued for use in both|struck for use in both)\b", re.I),
    # §9.3 off-metal strike — the Guldafslag / Sølvafslag class
    "off_metal_strike": re.compile(r"\boff[- ]metal strike\b", re.I),
    "mule": re.compile(r"\bMule\b", re.I),
    "uniface": re.compile(r"\bUniface\b", re.I),
    "wire_money": re.compile(r"\bWire money\b", re.I),
    # §9.5 off-nominal presentation: a normal-diameter piece struck on a
    # multiple-thickness planchet (piedfort). NGC writes it as
    # "Size as 1/2 Ducat, 4 times thickness" / "but double thickness".
    "multiple_thickness": re.compile(r"\b(?:double|triple|\d+\s*times)\s+thickness\b", re.I),
    # dual-denominated pieces — bears on §1 (what goes in `nominal`)
    "dual_denominated": re.compile(r"\bDual denominated?\b", re.I),
}
# "Struck at Altona" / "Struck in Copenhagen for the Danish West Indies Company"
# / "Struck at Copenhagen, Altona and Kongsberg" / "Struck at Altona and
# Oldendorf mints" / "1786 date struck at Poppelbüttel, others struck at Altona".
#
# The previous single-name version silently lost every mint after the first.
# Measured on the committed cache (2026-08-21): 15 records name more than one
# mint and 10 of them lost at least one — including the five reading "Struck at
# Copenhagen, Altona and Kongsberg", which came back as bare "Copenhagen". That
# truncation is what left `km-616-chr-v-1771` looking as though its stored
# Kongsberg had no source: NGC states it plainly and the parser dropped it.
#
# It was also case-SENSITIVE, so the five lowercase "struck at ..." notes
# matched nothing at all. Case-insensitivity is applied to the verb only —
# `re.I` on the whole pattern would make the capitalised-name class match
# lowercase words and swallow the rest of the sentence.
_NGC_MINT_NAME = r"[A-ZÆØÅÄÖÜ][\w.\-]*(?:\s+[A-ZÆØÅÄÖÜ][\w.\-]*)*"
_STRUCK_AT = re.compile(
    r"\b[Ss]truck\s+(?:at|in)\s+("
    + _NGC_MINT_NAME
    + r"(?:\s*,\s*(?:and\s+)?" + _NGC_MINT_NAME + r")*"
    + r"(?:\s+and\s+" + _NGC_MINT_NAME + r")?"
    + r")"
)
# A trailing "Mint"/"Mints" is a common noun, not part of the town name
# ("Christiania Mint", "Altona and Oldendorf mints").
_NGC_MINT_SUFFIX = re.compile(r"\s+Mints?$", re.IGNORECASE)
# "Similar type with very minor differences also struck at Kongsberg Mint and
# listed under Denmark as KM#Tn1" — a cross-reference to a DIFFERENT type, not
# a statement about this coin's mint. Five records carry it. The old pattern
# missed them by accident (lowercase verb); now that the verb matches, the
# exclusion has to be explicit or the parser would start attributing another
# type's mint to this one.
_NGC_OTHER_TYPE = re.compile(r"\bSimilar\s+type\b", re.IGNORECASE)


def _struck_at_mints(residual: str) -> tuple[object | None, str]:
    """Collect every mint NGC states for THIS coin, in source order.

    Returns `(value, residual)` where value is a str for one mint, a list
    for several, and None when the note names none. Clauses describing a
    different type are left in `residual` verbatim — they are real
    information about a neighbouring KM#, just not this coin's mint.
    """
    mints: list[str] = []
    spans: list[tuple[int, int]] = []
    for m in _STRUCK_AT.finditer(residual):
        sentence = residual[:m.start()].rsplit(".", 1)[-1]
        if _NGC_OTHER_TYPE.search(sentence):
            continue
        # The name class admits an internal "." so abbreviations survive, which
        # means a sentence-ending period is inside the capture and the next
        # sentence's first word looks like one more mint. Cut at the sentence
        # break, then trim the punctuation before the "Mint" suffix test —
        # "Christiania Mint." has to reach that test as "Christiania Mint".
        span = re.split(r"\.\s", m.group(1))[0]
        for name in re.split(r"\s*,\s*|\s+and\s+", span):
            name = _NGC_MINT_SUFFIX.sub("", name.strip(" .,;")).strip(" .,;")
            if name and name not in mints:
                mints.append(name)
        spans.append((m.start(), m.end()))
    for start, end in reversed(spans):
        residual = residual[:start] + " " + residual[end:]
    if not mints:
        return None, residual
    return (mints[0] if len(mints) == 1 else mints), residual
# Mayor attributions carry abbreviated nobiliary particles ("Gotthard v. Höveln"),
# so the name span must tolerate a '.' — stopping at the first period loses ~1 in 5.
_MAYOR = re.compile(
    r"\bArms of (?:Mayor\s+)?((?:[^.;()]|\.(?=\s*[A-ZÄÖÜ]))+?)\s*\((\d{4})\s*-\s*(\d{2,4})\)")

# A year, not required to end on a word boundary. NGC writes the date table
# cell as year + mintmaster initials run together — «1711IW», «1671GK»,
# «1691CW», «1659IW» — so a trailing `\b` never matched and the year was lost:
# 40 records carried a perfectly legible date the parser did not read. Digit
# guards on both sides still refuse to pick a year out of a longer number.
_YEAR = re.compile(r"(?<!\d)(1[3-9]\d{2})(?!\d)")


def _split_behrens(blob: str) -> list[str]:
    """Expand a Behrens blob into individual index tokens.

    "471, 472"        -> [471, 472]
    "805b,c"          -> [805b, 805c]      (letter suffixes share the number)
    "317-25, 326b,c"  -> [317-25, 326b, 326c]  (ranges kept verbatim)
    "186. 187"        -> [186, 187]        (source uses '.' as a separator)
    """
    out: list[str] = []
    last_num: str | None = None
    for tok in re.split(r"[,\s]+|(?<=\d)\.\s+", blob):
        tok = tok.strip(" .,;")
        if not tok:
            continue
        if re.fullmatch(r"\d+[a-z]?(?:-\d+[a-z]?)?", tok, re.I):
            out.append(tok)
            m = re.match(r"(\d+)", tok)
            last_num = m.group(1) if m else last_num
        elif re.fullmatch(r"[a-z]", tok, re.I) and last_num:
            # bare letter continuation: "805b,c" -> the 'c' means 805c
            out.append(f"{last_num}{tok}")
        else:
            out.append(tok)
    return out


def parse_note(note: str | None) -> dict:
    if not note:
        return {"note_raw": None, "catalog_refs": {}, "flags": {}, "note_residual": None}
    residual = note
    refs: dict[str, list[str]] = {}

    def claim(pattern: re.Pattern, key: str, expand=None) -> None:
        # Scan the REMAINING text, not the original: "Prev. KM#16" must be
        # claimed once as previous_km, not a second time as a bare KM
        # cross-reference. Matching against `note` throughout double-counted
        # every renumbering note (98 phantom km_cross_ref on the Lübeck pilot).
        nonlocal residual
        vals: list[str] = []
        while True:
            m = pattern.search(residual)
            if not m:
                break
            raw = m.group(1)
            vals.extend(expand(raw) if expand else [raw.strip(" .,;")])
            residual = residual[:m.start()] + " " + residual[m.end():]
        vals = [v for v in dict.fromkeys(vals) if v]
        if vals:
            refs[key] = vals

    claim(_BEHRENS_HEAD, "behrens", _split_behrens)
    claim(_DAV, "dav")
    claim(_FR, "fr")
    claim(_PREV_KM, "previous_km")
    claim(_PREV_FR, "previous_fr")
    claim(_BARE_KM, "km_cross_ref")

    flags: dict[str, object] = {}
    for name, pat in _FLAGS.items():
        m = pat.search(residual)
        if m:
            flags[name] = True
            residual = residual[:m.start()] + " " + residual[m.end():]
    struck_at, residual = _struck_at_mints(residual)
    if struck_at:
        flags["struck_at"] = struck_at
    m = _MAYOR.search(residual)
    if m:
        flags["mayor_arms"] = {"name": m.group(1).strip(),
                               "from": int(m.group(2)),
                               "to": int(m.group(3)) if len(m.group(3)) == 4
                               else int(m.group(2)[:2] + m.group(3))}
        residual = residual[:m.start()] + " " + residual[m.end():]

    residual = re.sub(r"\bRef\.?\s*", " ", residual)
    residual = re.sub(r"[\s.;,]+", " ", residual).strip(" .,;")
    return {"note_raw": note, "catalog_refs": refs, "flags": flags,
            "note_residual": residual or None}


# Leading year digits the coin does not show, which the catalogue supplies in
# parentheses: «(1)604», «(16)19», «(15)93 (cc)», «(160)9 (b)». Unwrapped only
# when a digit or Z follows, so a mintmark «(c)» or a range «(1618-22)» is left
# alone.
_IMPLIED_DIGITS = re.compile(r"\((\d{1,3})\)(?=[\dZ])")

# A year token in which the coin's own Z-shaped 2 is printed as «Z»: «16Z4»,
# «16ZZ», «165Z», «15Z5». Krause writes the 2 the way the die cut it, and the
# meaning is attested twice over in our caches: NumisMaster's KM 101 Speciedaler
# page heads its date table «1624 - 1634» and lists the rows «16Z4 … 16Z7», and
# Numista issues carry `"year": 1622` beside `"comment": "(16)ZZ"`. Uppercase
# only: that is the only form in the corpus, and it is the form both sources
# resolve. Lowercase «z» or «xx» are left unread.
_Z_YEAR = re.compile(r"(?<![0-9A-Za-z])1[0-9Z]{3}(?![0-9A-Za-z])")


# A parenthesised prefix written in front of a year that is already complete:
# «(1)1604 (c)» (Schaumburg KM 7, cuid 1154787; NumisMaster prints the same
# cell). «11604» is no year, and the type's other cells — «(1)604 (p)», «1604
# (p)» — read 1604, so the prefix is a doubled digit and is dropped.
_DOUBLED_PREFIX = re.compile(r"\((\d{1,3})\)(?=(\d{4})(?!\d))")

# An undated coin the catalogue attributes to a span or an approximate year:
# «(1618-22)», «(1590-1616)», «(ca1566-70) (d)», «(ca1611)», «(c.1620)»,
# «(ca.1640)». The span is carried whole; it is an attribution, not a date on
# the coin, so the record is marked `year_attributed` (→ year_verified: false).
# «(after 1620)» is NOT a span and is not matched here.
_ATTRIBUTED = re.compile(
    r"\((?:c(?:a)?\.?\s*)?(1\d{3})(?:-(\d{2}|\d{4}))?\)")


def normalise_date(s: str) -> str:
    """NGC date cell → the same cell with the year written in plain digits.

    Two Krause conventions are resolved, both verified against a second
    source (see `_IMPLIED_DIGITS`, `_Z_YEAR`), plus the doubled prefix of
    `_DOUBLED_PREFIX`; everything else passes through.
    """
    s = _DOUBLED_PREFIX.sub(
        lambda m: "" if m.group(2).startswith(m.group(1)) else m.group(0), s)
    s = _IMPLIED_DIGITS.sub(r"\1", s)
    return _Z_YEAR.sub(lambda m: m.group(0).replace("Z", "2"), s)


def _attributed_years(s: str) -> list[int] | None:
    """Every year of an attributed span in a (normalised) cell, else None."""
    m = _ATTRIBUTED.search(s)
    if not m:
        return None
    a, b = int(m.group(1)), m.group(2)
    if b is None:
        return [a]
    end = int(b) if len(b) == 4 else int(str(a)[:2] + b)
    return list(range(a, end + 1)) if end >= a else None


def parse_years(rec: dict) -> dict:
    """Year span from the date table, falling back to the heading date line.

    «16Z4» was once treated here as an unreadable digit and dropped. It is
    not: Z is the coin's Z-shaped 2 (curator, 2026-10-17; corroborated by
    NumisMaster and Numista — see `_Z_YEAR`). With the «(16)19» form, which
    was likewise unread, it left 113 records with no year at all (2026-10-17).
    Cells still unread — «16xx», «160(0?)», «ND», «Rare»
    — contribute no year, and a «z» left after normalisation still flags the
    record as partially illegible.
    """
    raw = [d.get("year_mint") or "" for d in (rec.get("dates") or [])]
    if not raw and rec.get("date_line"):
        raw = [rec["date_line"]]
    years, illegible, rewritten = [], False, []
    attributed_only = None
    for s in raw:
        s2 = normalise_date(s)
        if s2 != s and s not in rewritten:
            rewritten.append(s)
        span = _attributed_years(s2)
        if span:
            years.extend(span)
            attributed_only = attributed_only is not False
            if s not in rewritten:
                rewritten.append(s)
            continue
        # An unread digit left after normalisation — «166z». The
        # `\d[a-z]` alternative that used to sit here read the mintmaster
        # initials in «1711IW» as a damaged digit.
        if re.search(r"\bz\b|\dz|z\d", s2, re.I):
            illegible = True
        found = [int(y) for y in _YEAR.findall(s2)]
        if found:
            attributed_only = False
        years.extend(found)
    out = {"year_first": min(years) if years else None,
           "year_last": max(years) if years else None,
           "years_all": sorted(set(years)) or None}
    if illegible:
        out["year_partially_illegible"] = True
    if attributed_only:
        # Every year comes from an attribution («(1618-22)», «(ca1611)»):
        # the coin carries no date (§3a — the span stays, the (?) renders).
        out["year_attributed"] = True
    if rewritten:
        out["dates_as_printed"] = rewritten
    return out


def sift_fineness(value):
    """Split NGC's ``Fineness`` into a usable reading and an unusable one.

    Returns ``(usable, unusable_raw)`` — exactly one is non-None.

    NGC's own spec table sometimes prints a number in ``Fineness:`` that cannot
    be a fineness. On the Norwegian gold off-strikes struck from Speciedaler
    dies it reads «Fineness: 35.5000» (cuid 1099232), «58.0» on two different
    nominals, and «40.7» on four — a 12-Ducat, a 3-Ducat and two 2-Ducats
    alike, so it is not a per-piece weight either. What the field actually
    holds on those pages cannot be determined from the page, and guessing
    would be invention (§0b) — so this function does NOT reinterpret it. It
    only refuses to pass an impossible fineness downstream, and hands the raw
    value back so the record keeps it (§0b: an honest leftover is auditable).

    Accepted encodings, all of which real NGC records use:
      * fraction     — ``0 < v <= 1``   (.979, .875 — the overwhelming majority)
      * per mille    — ``500 <= v <= 1000`` (979, 875)

    Anything else is unusable. Karat is deliberately NOT accepted: no record in
    the corpus states a genuine karat fineness here, and the only two values in
    that band (14.65 and 17.5) belong to the same defective off-strike family.
    Widen this if a real karat-bearing record ever turns up.
    """
    if value is None:
        return None, None
    try:
        v = float(value)
    except (TypeError, ValueError):
        return None, value
    if 0 < v <= 1 or 500 <= v <= 1000:
        return v, None
    return None, v


def parse_record(rec: dict) -> dict:
    out = {k: rec.get(k) for k in (
        "cuid", "url", "region", "country", "heading", "date_line",
        "catalog_scheme", "catalog_number", "composition", "fineness",
        "weight_g", "asw_oz", "agw_oz", "diameter_raw", "obverse",
        "obverse_legend", "obverse_inscription", "reverse", "reverse_legend",
        "reverse_inscription", "edge", "ruler", "subject", "mint", "designer",
        "dates")}
    for k in ("weight_g", "asw_oz", "agw_oz"):
        if out.get(k) is not None:
            try:
                out[k] = float(out[k])
            except (TypeError, ValueError):
                pass
    out.update(parse_years(rec))
    out.update(parse_note(rec.get("note")))
    # Fineness gets a sanity gate — NGC prints unusable values on some pattern
    # pages; the raw number is preserved rather than dropped (see sift_fineness).
    usable, unusable = sift_fineness(out.get("fineness"))
    out["fineness"] = usable
    if unusable is not None:
        out["fineness_unusable_raw"] = unusable
        out.setdefault("flags", {})["fineness_unusable"] = True
    # the coin's own catalogue index, from the heading
    if rec.get("catalog_scheme") and rec.get("catalog_number"):
        out["catalog_own"] = {rec["catalog_scheme"].lower(): rec["catalog_number"]}
    out["is_pattern_number"] = bool(
        re.match(r"pn", str(rec.get("catalog_number") or ""), re.I))
    out["_parsed_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--region", required=True)
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--stats", action="store_true")
    args = ap.parse_args()

    d = region_dir(args.region)
    srcs = sorted(d.glob("cuid_*.json"))
    srcs = [p for p in srcs if not p.name.endswith(".parsed.json")]
    if not srcs:
        sys.exit(f"no harvest records under {d}")

    n = 0
    stats: Counter = Counter()
    residuals: Counter = Counter()
    for p in srcs:
        outp = p.with_suffix(".parsed.json")
        if outp.exists() and not args.force:
            continue
        rec = json.loads(p.read_text(encoding="utf-8"))
        parsed = parse_record(rec)
        outp.write_text(json.dumps(parsed, ensure_ascii=False, indent=1,
                                   sort_keys=True) + "\n", encoding="utf-8")
        n += 1
        for k in parsed.get("catalog_refs", {}):
            stats[k] += 1
        for k in parsed.get("flags", {}):
            stats[f"flag:{k}"] += 1
        if parsed.get("note_residual"):
            residuals[parsed["note_residual"][:60]] += 1
    print(f"[{args.region}] parsed {n} records -> *.parsed.json")
    if args.stats:
        print("\ncatalog-ref / flag coverage:")
        for k, c in stats.most_common():
            print(f"  {k:<24}{c:>5}")
        print(f"\nunclaimed note residuals ({len(residuals)} distinct, "
              f"kept verbatim in note_residual):")
        for s, c in residuals.most_common(20):
            print(f"  {c:>3}  {s}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
