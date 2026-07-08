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
import sys
from pathlib import Path
import re
import json

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lib.paths import BRUUN_CACHE as CACHE_DIR  # noqa: E402

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
    # Aagaard cites a die-combination in a trailing paren — «74.1 (49-2/49-5)»,
    # «117.7 (69-GK4/69-GK10)» (year[-mintmaster]die / year[-mintmaster]die).
    # That is meaningful die-study data and is kept. The paren group requires
    # a DIGIT-led interior (`\(\d`) so editorial prose — «(Aagaard erroneously
    # gives a reference to Bruun-6436)», «(this example)» — is NOT captured.
    "Aagaard": re.compile(r"\bAagaard[\-:]?\s*(\d+(?:\.\d+)?(?:\s*\(\d[^)]*\))?)", re.IGNORECASE),
    "Dav":     re.compile(r"\bDav[\.\-:]?\s*(\d+[A-Za-z]*)", re.IGNORECASE),
    "Brekke":  re.compile(r"\bBrekke[\-:]?\s*(\d+[A-Za-z]*)", re.IGNORECASE),
    "Wilcke":  re.compile(r"\bWilcke[\-:]?\s*(\d+(?:\.\d+)?)", re.IGNORECASE),
    "Pn":      re.compile(r"\b(Pn\d+[A-Za-z]*)\b"),
    # Norwegian-medieval catalogues frequently cited alongside Sieg/Bruun
    # on pre-1541 Norwegian lots in the Bruun PDFs. Without these patterns
    # the parser silently drops 63+ Galster, 302+ NMD, 40+ Schive refs
    # (audit 2026-05-20 on Bruun-9295 KM/Schou/Sieg/Galster/NMD chain).
    "Galster":           re.compile(r"\bGalster[\-:]?\s*(\d+[A-Za-z]*)", re.IGNORECASE),
    "NMD":               re.compile(r"\bNMD[\-:]?\s*(\d+[A-Za-z]*)", re.IGNORECASE),
    "Schive":            re.compile(r"\bSchive[\-:]?\s*(\S+?)(?=[;,\s])", re.IGNORECASE),
    # FP — Friberg-Pedersen catalogue (Christian VII-specific Danish-Norwegian
    # «Skillingen, Specien og Kronen 1761-1813» by Bent Friberg & Tom Pedersen).
    # Cited as «FP-44.3», «FP-9.3», «FP-36». Appears on 42 Bruun lots, all
    # under Christian VII (1766-1808). Sub-variant decimals («.X») captured.
    "FP":                re.compile(r"\bFP[\-:]?\s*(\d+(?:\.\d+)?[A-Za-z]*)"),
    # «Jensen & Skjoldager» (the Norwegian Frederik I lejrskilling catalogue
    # by Niels Jørgen Jensen and Mogens Skjoldager). Bruun catalogue cites
    # as «Skjoldager-T21/25» / «Jensen & Skjoldager-...»; match the
    # standalone «Skjoldager» token since «Jensen» is too generic.
    "Skjoldager":        re.compile(r"\bSkjoldager[\-:]?\s*(\S+?)(?=[;,\s]|$)", re.IGNORECASE),
}

YEAR_RE = re.compile(r"\b(1[1-9]\d{2}|20\d{2})\b")
# Lower bound 1100: covers the full Scandinavian medieval-coinage horizon
# (early Norwegian penningar, Erik VII of Pomerania ND (1396-1439), etc.).
# Project's V2 scope filter (1514-1914) lives in `build_bruun_denmark_seed.py`
# and will drop OOS coins downstream — the parser itself has no business
# truncating year information.
#
# The earlier 1500-floor silently lost the year on every pre-1500 lot — the
# parser then fell through to whatever 1500+ year appeared next in the body
# (typically a catalog reference like «Beskrivelsen 1791» / «Bruun-1898» /
# Hede edition year). See `extract_year` below for the meta-line-priority
# logic that also immunises against future catalog-year traps.
YEAR_MIN = 1100
YEAR_MAX = 1980


def extract_year(meta_line: str | None, body_match: str | None) -> int | None:
    """Extract a coin year from a lot's meta_line + body text.

    Priority rule (auction-cataloguer authoritative dating):
      1. Try meta_line first — the cataloguer's explicit dating sits here
         («DENMARK. Speciedaler, 1672. Glückstadt Mint. Christian V.»).
         The first YEAR_RE match in meta_line wins.
      2. Fallback to body_match[:600] when meta_line yields no year (e.g.
         purely descriptive meta «DENMARK. Speciedaler. Christian VII.»
         with the year elsewhere in the prose).

    Returns the first valid year (YEAR_MIN ≤ y ≤ YEAR_MAX) found in the
    priority order, or None.

    Failure mode this guards against (real Bruun lot 1001, Hans Nobel):
        meta_line:    "DENMARK. Noble, 1496. Malmö or Copenhagen Mint. Hans."
        body_excerpt: "...Beskrivelsen 1791-pl. 1, 2; Schive-pl. XIV, 38..."
    Old logic (first match in body_match): captured 1791 (catalog-year).
    New logic (meta first): captures 1496 (coin-year, correct).
    """
    if meta_line:
        for ym in YEAR_RE.finditer(meta_line):
            y = int(ym.group(1))
            if YEAR_MIN <= y <= YEAR_MAX:
                return y
    if body_match:
        body = body_match[:600]
        for ym in YEAR_RE.finditer(body):
            y = int(ym.group(1))
            if not (YEAR_MIN <= y <= YEAR_MAX):
                continue
            # Skip matches immediately preceded by `<Alpha>-` — catalog-ref
            # pattern like «Dav-1311», «KM-543», «Bruun-1898», «Hede-72»,
            # «Sieg-31», «Bru-1145». Body text typically carries dozens of
            # such refs; without this filter the body fallback would mistake
            # a catalog reference for the coin year. (Meta-line priority
            # above handles the more common Beskrivelsen / Schive trap with
            # space-separated year; this lookbehind closes the dash-form gap.)
            start = ym.start()
            if start >= 2 and body[start - 1] == "-" and body[start - 2].isalpha():
                continue
            return y
    return None



WEIGHT_RE = re.compile(r"\bWeight:\s*([\d.]+)\s*(?:gms?|grams?)\b", re.IGNORECASE)
GRADE_RE = re.compile(r"\b(NGC|PCGS|ICG|ANACS)\s+([A-Z]+(?:\-\d{1,2})?(?:\s+(?:DPL|DCAM|CAM|PL|FH|UCAM))?)\b")
RARITY_RE = re.compile(
    r"\b(EXTREMELY RARE|UNIQUE|VERY RARE|EXCESSIVELY RARE|EXTRAORDINARILY RARE|RARE|R{2,5})\b",
    re.IGNORECASE,
)
PATTERN_RE = re.compile(
    # Krause / English pattern markers
    r"\b(Pattern|Probe|Probestrike|Essai|Trial(?:\s+Strike)?|Pn\d+|"
    # Double-thickness die trial (French «Piéfort» / Danish-numismatic
    # «Piefort» / English-prose «Piedfort») — extra-thick planchet used
    # for collectors' presentation of a circulation die. Per CLAUDE.md
    # §9.1 these are trial strikes, not coins.
    r"Piefort|Piedfort|Pi[ée]fort|"
    # Off-metal strikes — Danish numismatic terms for «trial of a die
    # in a metal other than the circulation issue» (silver trial of a
    # gold die, etc.). Per CLAUDE.md §9.3 these are off-strike single
    # specimens, not circulating coins.
    r"S[øo]lvafslag|Guldafslag|Kroneafslag|"
    # Generic «off-metal strike» phrasing seen in Stack's Bowers catalogue
    # prose (Bruun catalogue uses this on cross-metal trial entries).
    r"off[\- ]metal\s+strike)\b",
    re.IGNORECASE,
)
MEDAL_RE = re.compile(r"\b(Medal(?:lion)?|Jeton|Token|Medaille)\b", re.IGNORECASE)

# First metadata line shape: "REGION_TOKEN. <denomination_year>. <mint>. <ruler>. <grade>."
# Region token is uppercase, possibly multi-word ("DUCHY OF SCHLESWIG", "HOLSTEIN-GOTTORP", "DANISH WEST INDIES")
META_LINE_RE = re.compile(
    r"^([A-ZÆØÅÜÖ][A-ZÆØÅÜÖ ,\-\(\)']+?)\.\s*(.+?)$"
)
MINT_RE = re.compile(r"\b((?:Copenhagen|Glückstadt|Glueckstadt|Glykstad|Altona|Christiania|Kongsberg|Berlin|Aarhus|Odense|Lund|Malmo|Stockholm|Uppsala|Frankfurt|Hamburg|Lübeck|Schleswig|Husum|Helsingør|Hanover|Riga|Reval)\s+Mint)\b", re.IGNORECASE)
# Mint named in the cataloguer's structured meta-line, positioned after the
# denomination/year segment («… Næstved Mint. …», «… Copenhagen Mint. …»).
# Preferred over the body search (MINT_RE), which scans the whole prose and
# mis-grabs an unrelated mint mentioned in the historical discussion when the
# coin's own mint is absent from MINT_RE's hardcoded list (real case Bruun-3725
# Witten: meta «Næstved Mint» — Næstved unlisted — but the body discussion said
# «Lund» → wrong `mint: Lund Mint`). Anchored on the «. » segment boundary; the
# captured token may be a dual mint («Altona / Poppenbüttel», «Malmö or
# Copenhagen») preserved verbatim (the entity classifier splits on «/ or »).
# A truncated line-break meta («Copen-») carries no « Mint» token and correctly
# falls through to the body reassembly.
META_MINT_RE = re.compile(
    r"\.\s*([A-ZÆØÅ][A-Za-zæøåüö]+"
    r"(?:(?:\s*/\s*|\s+or\s+|\s+and\s+)[A-ZÆØÅ][A-Za-zæøåüö]+)?)\s+Mint\b"
)


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
        # Refs. Mask parenthetical spans for MOST refs: a catalogue
        # cross-reference or editorial correction prints OTHER catalogues'
        # numbers inside a paren note — e.g.
        #   «… Aagaard-106.1 (Aagaard erroneously gives a reference to
        #    Bruun-6436); Bruun-6435. …»
        # A naïve search grabs the bracketed «Bruun-6436» (it precedes the
        # real standalone «Bruun-6435»), mislabelling the coin with the very
        # number the note flags as wrong. Length-preserving mask keeps the
        # \b word boundaries and string offsets intact.
        # EXCEPTION: Aagaard runs against the UNMASKED text because its
        # citation legitimately carries a trailing die-combination paren
        # («74.1 (49-2/49-5)») that we keep; its own pattern requires a
        # digit-led interior so editorial prose parens are still dropped.
        body_for_refs = re.sub(r"\([^)]*\)", lambda m: " " * len(m.group(0)), body_match)
        refs = {}
        for k, pat in REF_PATTERNS.items():
            text = body_match if k == "Aagaard" else body_for_refs
            mm = pat.search(text)
            if mm:
                refs[k] = mm.group(1)
        # Year — meta_line first (cataloguer's authoritative dating),
        # body_match fallback. See `extract_year` for the failure modes
        # this guards against (pre-1500 floor + catalog-year traps).
        year = extract_year(meta_line, body_match)
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
        # Mint — prefer the cataloguer's structured meta-line «<X> Mint»
        # (authoritative, positioned right after the year); fall back to the
        # body search only when the meta names no mint or is truncated mid-word
        # («Copen-» across a line break). The body-only search mis-fires on lots
        # whose own mint is absent from MINT_RE's list — see META_MINT_RE.
        mint = None
        if meta_line:
            mm_meta = META_MINT_RE.search(meta_line)
            if mm_meta:
                mint = mm_meta.group(1).strip() + " Mint"
        if mint is None:
            mmint = MINT_RE.search(body_match)
            if mmint:
                mint = mmint.group(1)
        # Ruler — heuristic: look for KING_NAME inside body, before
        # mintmaster/engraver/provenance annotations. The pre-Mintmaster
        # cut is critical: Bruun lots routinely include lines like
        # «Mintmaster: Hans Glaser» / «Engraver: Hans zum Busch» /
        # «Ex: Hans Henning Sale» whose personal-name tokens would
        # otherwise be captured as the ruler when the cataloguer's own
        # ruler attribution is missing or typo'd.
        #
        # Real-world failure (Bruun lot 14215, KM-94 1 Ducat 1642):
        # meta_line was truncated to «GERMANY . Schleswig-Holstein-
        # Gottorp. Ducat, 1642-HG.» — no ruler. The body says
        # «Friederich III» (typo, extra 'e') which didn't match the
        # canonical «Friedrich III» pattern. The matcher then fell
        # through to «Mintmaster: Hans Glaser» and recorded
        # `ruler: Hans` — a wrong attribution that broke cross-source
        # merging downstream. Fix: (1) cut at the markers below,
        # (2) include common typos as aliases, (3) sort the rulers
        # list by descending length so multi-word names («Christian
        # Albrecht», «Karl XIV Johan») win over the bare «Christian»
        # / «Karl» prefixes.
        # Cut at markers that introduce NON-ruler personal-name tokens
        # (mintmaster, engraver, provenance, auction-house signatures).
        # «Privy mark:» / «Date Source:» are deliberately NOT cut here —
        # the ruler often appears AFTER them on the same line:
        # «DENMARK. Gold 2 Krone, 1628. Copenhagen Mint; Privy mark:
        # flower. Christian IV. NGC ...» — cutting at «Privy mark:»
        # would lose the ruler.
        ruler_zone = body_match
        for marker in ("Mintmaster:", "Mintmasters:",
                       "Engraver:", "Engravers:",
                       "Ex:", "From the L. E. Bruun"):
            idx = ruler_zone.find(marker)
            if idx != -1:
                ruler_zone = ruler_zone[:idx]
        # (regex pattern, canonical name) — typo aliases map to the
        # canonical Danish/German form so downstream consumers see
        # consistent spelling.
        ruler_patterns = [
            # Multi-word names FIRST so the substring match doesn't
            # short-circuit on a bare «Christian» / «Karl» prefix.
            ("Christian Albrecht", "Christian Albrecht"),
            ("Karl XIV Johan", "Karl XIV Johan"),
            ("Carl XIV Johan", "Karl XIV Johan"),  # Bruun spelling
            ("Karl Friedrich", "Karl Friedrich"),
            ("Carl Friedrich", "Carl Friedrich"),
            ("Johann Adolf", "Johann Adolf"),
            # Ordinal-bearing names — longer ordinals before shorter.
            ("Christian VIII", "Christian VIII"),
            ("Christian VII", "Christian VII"),
            ("Christian III", "Christian III"),
            ("Christian IV", "Christian IV"),
            ("Christian IX", "Christian IX"),
            ("Christian X", "Christian X"),
            ("Christian V", "Christian V"),
            ("Christian VI", "Christian VI"),
            ("Frederik VIII", "Frederik VIII"),
            ("Frederik VII", "Frederik VII"),
            ("Frederik II", "Frederik II"),
            ("Frederik III", "Frederik III"),
            ("Frederik IV", "Frederik IV"),
            ("Frederik IX", "Frederik IX"),
            ("Frederik V", "Frederik V"),
            ("Frederik VI", "Frederik VI"),
            ("Frederick VIII", "Frederik VIII"),
            ("Frederick VII", "Frederik VII"),
            ("Frederick II", "Frederik II"),
            ("Frederick III", "Frederik III"),
            ("Frederick IV", "Frederik IV"),
            ("Frederick IX", "Frederik IX"),
            ("Frederick V", "Frederik V"),
            ("Frederick VI", "Frederik VI"),
            ("Friedrich II", "Friedrich II"),
            ("Friedrich III", "Friedrich III"),
            ("Friedrich IV", "Friedrich IV"),
            # Typo aliases (canonical spelling on right):
            ("Friederich II", "Friedrich II"),
            ("Friederich III", "Friedrich III"),
            ("Friederich IV", "Friedrich IV"),
            ("Frederich II", "Friedrich II"),
            ("Frederich III", "Friedrich III"),
            ("Frederich IV", "Friedrich IV"),
            # Single-word — last, so they don't pre-empt the multi-words.
            ("Håkon VII", "Håkon VII"),
            ("Olav V", "Olav V"),
            ("Harald V", "Harald V"),
            ("Oskar II", "Oskar II"),
            ("Oskar I", "Oskar I"),
            ("Karl XV", "Karl XV"),
            ("Carl XV", "Karl XV"),  # Bruun spelling → canonical
            ("Karl XIII", "Karl XIII"),
            ("Carl XIII", "Karl XIII"),
            ("Karl XII", "Karl XII"),
            ("Karl XI", "Karl XI"),
            ("Karl X", "Karl X"),
            ("Karl IX", "Karl IX"),
            ("Gustav V", "Gustav V"),
            ("Margrethe II", "Margrethe II"),
            ("Adolf", "Adolf"),
            ("Hans", "Hans"),
        ]
        ruler = None
        for pattern, canonical in ruler_patterns:
            if re.search(rf"\b{re.escape(pattern)}\b", ruler_zone):
                ruler = canonical
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
