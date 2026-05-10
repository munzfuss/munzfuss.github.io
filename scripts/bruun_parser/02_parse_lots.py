"""
Stage 2 — parse every lot from extracted page text.

Inputs:  scripts/cache/bruun/pages/{partN}.txt for N in PART_LOT_RANGES below
Outputs: scripts/cache/bruun/lots/{partN}.json
         — list of lot dicts with refs/year/mint/grade/weight/rarity

Lot block format observed (Part I/II/III all the same):

    1016
    DENMARK. Speciedaler, MDCIII (1603). Copenhagen Mint. Christian IV . NGC MS-61.  KM-19;
    Dav-3512; Hede-51; Sieg-100; Schou-6; Bruun-4648. Weight: 27.44 gms. Engraved by Nicolaus Schwabe.
    A fascinating and  VERY RARE mule striking ...
    €35,000-€45,000
    From the L. E. Bruun Collection.

We capture per lot:
    lot_no                  — sequential auction lot number (1016)
    page                    — PDF page number where the lot starts
    region                  — first ALL-CAPS token before "." (DENMARK/NORWAY/SWEDEN/GERMANY/...)
    meta_line               — full first metadata line (region + denom + year + mint + ruler + grade)
    year                    — extracted 4-digit year (best-effort)
    mint                    — "Copenhagen Mint" / "Glückstadt Mint" / ...
    ruler                   — ruler name (Christian IV / Frederik III / Karl Friedrich / ...)
    grade                   — "NGC MS-61" / "PCGS AU-58" / etc.
    weight_g                — weight in grams if recorded
    rarity                  — "RARE" / "VERY RARE" / "EXTREMELY RARE" / "UNIQUE" if mentioned
    is_pattern              — True if Pattern / Pn-ref / Probe / Essai
    refs                    — dict {KM, Hede, Sieg, Lange, Bruun, Fr, Schou, Aagaard, Dav, ...}
    body_excerpt            — first 600 chars of the block — for downstream re-inspection

Re-run when stage 01 produces new pages/{partN}.txt files. The PARTS list at
top of stage 03 should also be updated when a new part appears.
"""
from pathlib import Path
import re
import json

CACHE_DIR = Path(__file__).resolve().parents[2] / "scripts" / "cache" / "bruun"
PAGES_DIR = CACHE_DIR / "pages"
LOTS_DIR = CACHE_DIR / "lots"
LOTS_DIR.mkdir(parents=True, exist_ok=True)

LOT_NUMBER_LINE = re.compile(r"^\s*(\d{4,5})\s*$")
PAGE_HEADER = re.compile(r"========== PAGE (\d+) ==========")

# Per-part lot number ranges (auction-sequence). Used to filter stray
# digit-only lines from being mis-recognised as lot numbers. When a new
# Bruun part is published, add its (slug → list of (lo, hi) ranges).
PART_LOT_RANGES: dict[str, list[tuple[int, int]]] = {
    "part1": [(1001, 1500)],                    # Sept 2024 Copenhagen   — 1001-1286
    "part2": [(13001, 13500), (14001, 14500)],  # Mar 2025 Zurich Sess I+II — 13001-13263 / 14001-14287
    "part3": [(11001, 11500), (12001, 12500)],  # Oct 2025 Zurich Sess I+II — 11001-11308 / 12001-12228
    "part4": [(17001, 17500), (18001, 18500)],  # Mar 2026 NYC Sess I+II — 17001-17291 / 18xxx
}


def _in_lot_range(slug: str, lot_no: int) -> bool:
    """True if `lot_no` falls inside one of `slug`'s declared auction ranges."""
    return any(lo <= lot_no <= hi for lo, hi in PART_LOT_RANGES.get(slug, []))

# Ref tokens — case-sensitive prefix; case-insensitive search (with hyphen optional)
#
# Suffix-letter capture is `[A-Za-z]*` (zero-or-more) so multi-letter Krause /
# Lange / Hede sub-variant suffixes (e.g. Lange-430AA, Hede-23AB) capture in
# full. The earlier `[A-Za-z]?` pattern stopped after one letter and silently
# collapsed «430AA» → «430A», which bridged distinct Krause types under the
# same parsed token (TODO J item 1, surfaced via km-165 / KM-166 audit).
REF_PATTERNS = {
    "KM":      re.compile(r"\bKM[#\-]?\s*([A-Za-z]?\d+(?:\.\d+)?[A-Za-z]*(?:\.\d+)?)", re.IGNORECASE),
    "Hede":    re.compile(r"\bHede[\-:]?\s*(\d+[A-Za-z]*(?:[\-/]\d+)?)", re.IGNORECASE),
    "Sieg":    re.compile(r"\bSieg[\-:]?\s*(\d+(?:\.\d+)?[A-Za-z]*)", re.IGNORECASE),
    "Lange":   re.compile(r"\bLange[\-:]?\s*(\d+[A-Za-z]*)", re.IGNORECASE),
    "Bruun":   re.compile(r"\bBruun[\-:]?\s*(\d+[A-Za-z]*)", re.IGNORECASE),
    "Fr":      re.compile(r"\bFr[\.\-:]?\s*(\d+[A-Za-z]*(?:\.\d+)?)", re.IGNORECASE),
    "Schou":   re.compile(r"\bSchou[\-:]?\s*(\d+[A-Za-z]*(?:[\-/]\d+)?)", re.IGNORECASE),
    "Aagaard": re.compile(r"\bAagaard[\-:]?\s*(\d+(?:\.\d+)?(?:\s*\([^)]+\))?)", re.IGNORECASE),
    "Dav":     re.compile(r"\bDav[\.\-:]?\s*(\d+[A-Za-z]*)", re.IGNORECASE),
    "Brekke":  re.compile(r"\bBrekke[\-:]?\s*(\d+[A-Za-z]*)", re.IGNORECASE),
    "Wilcke":  re.compile(r"\bWilcke[\-:]?\s*(\d+(?:\.\d+)?)", re.IGNORECASE),
    "Pn":      re.compile(r"\b(Pn\d+[A-Za-z]*)\b"),
}

YEAR_RE = re.compile(r"\b(1[5-9]\d{2}|20\d{2})\b")
WEIGHT_RE = re.compile(r"\bWeight:\s*([\d.]+)\s*(?:gms?|grams?)\b", re.IGNORECASE)
GRADE_RE = re.compile(r"\b(NGC|PCGS|ICG|ANACS)\s+([A-Z]+(?:\-\d{1,2})?(?:\s+(?:DPL|DCAM|CAM|PL|FH|UCAM))?)\b")
RARITY_RE = re.compile(
    r"\b(EXTREMELY RARE|UNIQUE|VERY RARE|EXCESSIVELY RARE|EXTRAORDINARILY RARE|RARE|R{2,5})\b",
    re.IGNORECASE,
)
PATTERN_RE = re.compile(r"\b(Pattern|Probe|Essai|Trial|Pn\d+|Probestrike)\b", re.IGNORECASE)
MEDAL_RE = re.compile(r"\b(Medal(?:lion)?|Jeton|Token|Medaille)\b", re.IGNORECASE)

# First metadata line shape: "REGION_TOKEN. <denomination_year>. <mint>. <ruler>. <grade>."
# Region token is uppercase, possibly multi-word ("DUCHY OF SCHLESWIG", "HOLSTEIN-GOTTORP", "DANISH WEST INDIES")
META_LINE_RE = re.compile(
    r"^([A-ZÆØÅÜÖ][A-ZÆØÅÜÖ ,\-\(\)']+?)\.\s*(.+?)$"
)
MINT_RE = re.compile(r"\b((?:Copenhagen|Glückstadt|Glueckstadt|Glykstad|Altona|Christiania|Kongsberg|Berlin|Aarhus|Odense|Lund|Malmo|Stockholm|Uppsala|Frankfurt|Hamburg|Lübeck|Schleswig|Husum|Helsingør|Hanover|Riga|Reval)\s+Mint)\b", re.IGNORECASE)


def split_pages(slug: str) -> list[tuple[int, str]]:
    text = (PAGES_DIR / f"{slug}.txt").read_text()
    parts = re.split(r"========== PAGE (\d+) ==========", text)
    pages = []
    for i in range(1, len(parts), 2):
        pages.append((int(parts[i]), parts[i + 1]))
    return pages


def parse_part(slug: str) -> list[dict]:
    """Walk pages in order; identify lot-number lines; collect text until next lot-number or page break."""
    pages = split_pages(slug)
    lots: list[dict] = []

    # Build a flat (page, line) sequence
    flat: list[tuple[int, str]] = []
    for page_no, txt in pages:
        for ln in txt.splitlines():
            flat.append((page_no, ln))

    i = 0
    n = len(flat)
    while i < n:
        page_no, ln = flat[i]
        m = LOT_NUMBER_LINE.match(ln)
        if not m:
            i += 1
            continue
        lot_no = int(m.group(1))
        # Sanity: lot number must increase monotonically (auction sequence)
        if lots and lot_no <= lots[-1]["lot_no"]:
            # Likely a stray digit-only line; skip
            i += 1
            continue
        # Filter implausibly small/large numbers — must fall in declared ranges
        if not _in_lot_range(slug, lot_no):
            i += 1
            continue

        # Collect block lines until next lot-number-line OR after we've seen
        # a price line + "From the L. E. Bruun Collection." sentinel
        block_lines: list[str] = []
        block_pages: set[int] = {page_no}
        j = i + 1
        while j < n:
            p2, ln2 = flat[j]
            block_pages.add(p2)
            if LOT_NUMBER_LINE.match(ln2):
                m2 = LOT_NUMBER_LINE.match(ln2)
                next_lot = int(m2.group(1))
                # Heuristic: next lot if it's plausibly the next sequence number
                if next_lot > lot_no and _in_lot_range(slug, next_lot):
                    break
            block_lines.append(ln2)
            j += 1
            # safety cap: a single lot block shouldn't exceed ~150 lines
            if len(block_lines) > 200:
                break

        body = "\n".join(block_lines).strip()
        # Normalize body for regex matching: collapse PDF line-break hyphenation
        # ("Bru-\nun-7701" → "Bruun-7701", "Bru -\nun-7951" → "Bruun-7951",
        # "Wolfenbüt-\ntel" → "Wolfenbüttel") and then join newlines so word-
        # boundary anchors like \bFrederik V\b match across the original
        # "Frederik \nV" line splits. Constrain both sides to letters so digit
        # spans like "ducat - 1604" don't get glued.
        body_match = re.sub(
            r"([A-Za-zÄÖÜäöüß])\s*-\s*\n\s*([a-zäöüß])", r"\1\2", body
        )
        body_match = re.sub(r"\s+", " ", body_match)
        # Find the metadata line — usually the first non-blank line after lot#,
        # starting with an ALL-CAPS region token
        region = None
        meta_line = None
        for bl in block_lines[:8]:
            bl_s = bl.strip()
            if not bl_s:
                continue
            m_meta = META_LINE_RE.match(bl_s)
            if m_meta:
                region = m_meta.group(1).strip()
                meta_line = bl_s
                break
        # Refs
        refs = {}
        for k, pat in REF_PATTERNS.items():
            mm = pat.search(body_match)
            if mm:
                refs[k] = mm.group(1)
        # Year (prefer year inside parens, e.g. "MDCIII (1603)" or "Speciedaler, 1672")
        year = None
        for ym in YEAR_RE.finditer(body_match[:600]):
            y = int(ym.group(1))
            if 1500 <= y <= 1980:
                year = y
                break
        # Weight
        wmatch = WEIGHT_RE.search(body_match)
        weight_g = float(wmatch.group(1)) if wmatch else None
        # Grade
        gmatch = GRADE_RE.search(body_match)
        grade = f"{gmatch.group(1)} {gmatch.group(2)}" if gmatch else None
        # Rarity
        rarity = None
        rmatch = RARITY_RE.search(body_match)
        if rmatch:
            rarity = rmatch.group(1).upper()
        # Pattern flag
        is_pattern = bool(PATTERN_RE.search(body_match))
        # Mint
        mint = None
        mmint = MINT_RE.search(body_match)
        if mmint:
            mint = mmint.group(1)
        # Ruler — heuristic: look for KING_NAME inside body, ".[ruler] ."
        ruler = None
        rulers = [
            "Christian III", "Christian IV", "Christian V", "Christian VI", "Christian VII",
            "Christian VIII", "Christian IX", "Christian X",
            "Frederik II", "Frederik III", "Frederik IV", "Frederik V", "Frederik VI",
            "Frederik VII", "Frederik VIII", "Frederik IX",
            "Frederick II", "Frederick III", "Frederick IV", "Frederick V", "Frederick VI",
            "Frederick VII", "Frederick VIII", "Frederick IX",
            "Friedrich II", "Friedrich III", "Friedrich IV",
            "Karl Friedrich", "Carl Friedrich",
            "Christian Albrecht",
            "Margrethe II", "Hans", "Adolf", "Johann Adolf",
            "Håkon VII", "Olav V", "Harald V",
            "Oskar I", "Oskar II", "Karl XV", "Karl XIV Johan", "Gustav V",
        ]
        for r in rulers:
            if re.search(rf"\b{re.escape(r)}\b", body_match):
                ruler = r
                break

        lots.append({
            "lot_no": lot_no,
            "page": page_no,
            "page_span": sorted(block_pages),
            "region": region,
            "meta_line": meta_line,
            "ruler": ruler,
            "year": year,
            "mint": mint,
            "grade": grade,
            "weight_g": weight_g,
            "rarity": rarity,
            "is_pattern": is_pattern,
            "refs": refs,
            "body_excerpt": body[:600],
        })

        i = j

    return lots


def main():
    for slug in PART_LOT_RANGES:
        print(f"=== {slug}")
        lots = parse_part(slug)
        out = LOTS_DIR / f"{slug}.json"
        out.write_text(json.dumps(lots, indent=2, ensure_ascii=False))
        print(f"  lots: {len(lots)}")
        print(f"  → {out}")
        # quick region distribution
        from collections import Counter
        regions = Counter(l["region"] or "?" for l in lots)
        print(f"  top regions:")
        for reg, ct in regions.most_common(15):
            print(f"    {ct:>4}  {reg}")


if __name__ == "__main__":
    main()
