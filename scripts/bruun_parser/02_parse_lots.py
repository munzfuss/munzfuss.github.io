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
    # Oct 2026 Copenhagen Sess I (Denmark 14001-14226) + Sess II (Norway/Sweden/
    # Germany 15001-15188, medals 15189-15283). NB: 14001-14226 REUSES Part II's
    # lot numbers — a lot number is only unique together with its part.
    "part5": [(14001, 14500), (15001, 15500)],
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
    # PREFIX capture is `[A-Za-z]{0,3}` — Krause prefixes the number with a
    # register code on its non-circulation series: `Tn6` (token — the Danish
    # Rigsbanktegn), `PM13` (Swedish plate money), `A140`. The earlier
    # `[A-Za-z]?` allowed ONE letter, so every two-letter register was dropped
    # on the floor — 15 lots carried a KM the seed never saw.
    # `Pn` is excluded by the lookahead: Krause's pattern/presentation register
    # has its own ref key below, and folding it into `km` would manufacture
    # false unifying edges (§9.4 — `Pn10` recurs across reigns and volumes just
    # as bare numbers do, and a KM-base collision is exactly what the merger
    # treats as evidence of one coin).
    "KM":      re.compile(r"\bKM[#\-]?\s*(?!Pn)([A-Za-z]{0,3}\d+(?:\.\d+)?[A-Za-z]*(?:\.\d+)?)", re.IGNORECASE),
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
    # Krause's pattern / presentation register. The number may carry a SERIES
    # letter between «Pn» and the digits — `PnA16`, `PnH16`, `PnJ16`, `PnG16`
    # are all Frederik III 1659 pieces struck from the Ebenezerkrone dies. The
    # earlier `Pn\d+` demanded a digit straight after «Pn», so those nine lots
    # matched neither this pattern nor the KM one and the marker vanished
    # entirely — including on the four lots that reach the seed (1069, 1070,
    # 13140, 17069). That marker is the §9 item-5 GATE for the off-nominal
    # test, so losing it disarmed the test on exactly the coins it exists for.
    "Pn":      re.compile(r"\b(Pn[A-Za-z]?\d+[A-Za-z]*)\b"),
    # Norwegian-medieval catalogues frequently cited alongside Sieg/Bruun
    # on pre-1541 Norwegian lots in the Bruun PDFs. Without these patterns
    # the parser silently drops 63+ Galster, 302+ NMD, 40+ Schive refs
    # (audit 2026-05-20 on Bruun-9295 KM/Schou/Sieg/Galster/NMD chain).
    "Galster":           re.compile(r"\bGalster[\-:]?\s*(\d+[A-Za-z]*)", re.IGNORECASE),
    "NMD":               re.compile(r"\bNMD[\-:]?\s*(\d+[A-Za-z]*)", re.IGNORECASE),
    # Schive cites a PLATE and a number on it — «X:14», «XVIII:10-12»,
    # «T:7». All 40 mentions in the cache carry that shape, so the value is
    # captured as two groups and re-emitted canonically as «PLATE:NUMS»
    # (see `_schive_value`), which also folds the two spelling variants the
    # catalogue uses: «Schive-III-21» (hyphen separator, lot 12005) and
    # «Schive-pl. XIV , 38» (lot 1001, the only «pl.»-prefixed citation —
    # previously captured as the literal «pl.», losing the reference).
    #
    # `Schive\b` — the word boundary is REQUIRED: without it the pattern
    # matches inside the mintmaster surname «Schivern Knoph» (lot 13235)
    # and captured «rn» as a catalogue index.
    #
    # Requiring a plate+number also drops the two shapes that are NOT this
    # coin's own index, per CLAUDE.md anti-pattern §5: «Schive-cf. II:24»
    # (lot 12001) and «Schive-IX: cf. 1-2» (lot 12015) point at a similar
    # OTHER coin, and «Schive-Unlisted» (lot 12003) is the negative claim
    # that the coin is absent from Schive. None of the three is a positive
    # catalogue reference for the lot that carries it.
    "Schive":            re.compile(
        r"\bSchive\b[\-:]?\s*(?:pl\.\s*)?"
        r"(?P<plate>[IVX]+|T)\s*[:\-,]\s*(?P<nums>\d+(?:\s*[-/]\s*\d+)?)"),
    # FP — Friberg-Pedersen catalogue (Christian VII-specific Danish-Norwegian
    # «Skillingen, Specien og Kronen 1761-1813» by Bent Friberg & Tom Pedersen).
    # Cited as «FP-44.3», «FP-9.3», «FP-36». Appears on 42 Bruun lots, all
    # under Christian VII (1766-1808). Sub-variant decimals («.X») captured.
    "FP":                re.compile(r"\bFP[\-:]?\s*(\d+(?:\.\d+)?[A-Za-z]*)"),
    # «Jensen & Skjoldager» (the Norwegian Frederik I lejrskilling catalogue
    # by Niels Jørgen Jensen and Mogens Skjoldager). Bruun catalogue cites
    # as «Skjoldager-T21/25» / «Jensen & Skjoldager-...»; match the
    # standalone «Skjoldager» token since «Jensen» is too generic.
    #
    # The value must be a WELL-FORMED index — an optional single-letter
    # series prefix («T-22/26», «N-05», «L-01/L-34», «F- 53/F-57»; the
    # prefix may also run straight into the digits, «T21/25»), a number,
    # and any «/»-joined continuation. The earlier `(\S+?)` accepted any
    # non-space run, which produced two failure modes seen in the cache:
    #   * a bare «,» from running prose that cites the study without any
    #     index — «The most recent study, by Jensen & Skjoldager, again
    #     leans towards 4 Skilling» (lot 17035) — which then rendered as
    #     the catalogue index «, again leans towards 4 Skilling»;
    #   * a truncated «F-» on lot 11156, where the real ref is
    #     «Skjoldager-F- 53/F-57» and the lookahead cut at the space.
    "Skjoldager":        re.compile(
        # The catalogue NAME stays case-insensitive (inline flag) while the
        # series prefix stays strictly uppercase — a global IGNORECASE would
        # let `[A-Z]` swallow a lowercase prose word before the number.
        r"\b(?i:Skjoldager)[\-:]?\s*"
        r"((?:[A-Z]-?\s*)?\d+[A-Za-z]*(?:\s*/\s*(?:[A-Z]-?\s*)?\d+[A-Za-z]*)*)"),
}

def _schive_value(m: "re.Match") -> str:
    """Canonical «PLATE:NUMS» from a Schive match.

    The catalogue writes the plate/number separator three ways — «X:14»
    (38 of 40 mentions), «III-21» (lot 12005) and «pl. XIV , 38» (lot
    1001) — for the same kind of reference. Emitting one form keeps the
    index comparable across lots. Only the plate/number separator is
    rewritten; a RANGE inside the number («XVIII:10-12») keeps its own
    hyphen.
    """
    return f"{m.group('plate')}:{re.sub(r'\\s+', '', m.group('nums'))}"


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
# Fallback for the cataloguers' slips (2026-10-17, 21 lots across Parts I-V,
# all a specimen weight that WEIGHT_RE missed): a decimal comma («3,46 gms»,
# the Swedish lots of Part V), a misspelt / mis-punctuated label («Weight 5.91»,
# «Weigt:», «Weight;», «Weigh:»), or a bare «15.51 gms.» right after the
# «Bruun-N» reference that closes the ref list. The bare form is accepted ONLY
# in that position, so a weight mentioned in the prose is never read.
WEIGHT_LOOSE_RE = re.compile(
    r"\bWeig\w*\s*[:;]?\s*(\d+(?:[.,]\d+)?)\s*(?:gms?|grams?)\b"
    r"|\bBruun-\s*\d+(?:\.\d+)?[.;]?\s+(\d+(?:[.,]\d+)?)\s*gms?\b",
    re.IGNORECASE,
)
GRADE_RE = re.compile(r"\b(NGC|PCGS|ICG|ANACS)\s+([A-Z]+(?:\-\d{1,2})?(?:\s+(?:DPL|DCAM|CAM|PL|FH|UCAM))?)\b")
RARITY_RE = re.compile(
    r"\b(EXTREMELY RARE|UNIQUE|VERY RARE|EXCESSIVELY RARE|EXTRAORDINARILY RARE|RARE|R{2,5})\b",
    re.IGNORECASE,
)
# Closing price estimate of a lot («€4,000-€6,000», «€900-€1,200»). Marks the
# end of the cataloguer's description; everything after it is provenance, page
# furniture, or the next lot's headline. Used to scope the §9.1 / §9.2 tests.
PRICE_LINE_RE = re.compile(r"[€$]\s*[\d.,]+\s*[-–]\s*[€$]\s*[\d.,]+")

PATTERN_RE = re.compile(
    # Krause / English pattern markers.
    #
    # `Pn\d+` was an alternative here until 2026-08-01 and is deliberately gone:
    # CLAUDE.md §9 item 1 states that a bare Krause `Pn*` number is NOT on its
    # own sufficient to skip a lot, because Krause files unique FULL-VALUE show
    # coins — Portugaløser, multi-Ducat gold — under `Pn` as well. Keying on it
    # made the parser drop exactly those. Five lots were suppressed by that
    # alternative and by nothing else, all of them full-weight gold at 3.39-3.47 g
    # per stamped ducat (canonical 3.490) and all catalogued in three or more
    # independent registers: Bruun-6082/6083/6084/6174 (the 1653 and 1655
    # ½ Portugaløser / 5 Ducats, Fr 98 and Fr 106) and Bruun-7296 (10 Ducats
    # 1699, Fr 213, Kold 149a). Their nominal equals their bullion value, so the
    # §9.5 off-nominal test does not exclude them either — they are coins, and
    # the curator decides their fate in the normal triage.
    #
    # Every other suppression stands on Bruun's own wording and is unaffected:
    # «Pattern» (52), «off-metal strike» (24), «Trial» (8), «Piefort» (4).
    r"\b(Pattern|Probe|Probestrike|Essai|Trial(?:\s+Strike)?|"
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
    r"off[\- ]metal\s+strike|"
    # Stack's Bowers also describes the same thing WITHOUT naming it: a
    # planchet of one metal struck with another denomination's dies. Lot 1133
    # (Bruun-7396) reads «a gold planchet struck to a Double Ducat weight
    # standard with the dies customarily used for a 16 Skilling» — the gold
    # off-strike of the silver Hede 47, KM-Unlisted / Fr-Unlisted, two
    # specimens traced. Per §9.3 that is an off-strike, not a coin, but none
    # of the Danish terms above appear in the English prose. Across all 1649
    # parsed lots this phrase matches exactly two: 1133 and 13239 (the latter
    # already caught by «Off-Metal Strike» in its meta line), so it adds no
    # false positives. Cataloguers describe a normal gold coin as «struck in
    # gold», not as «a gold planchet».
    r"(?:gold|silver)\s+planchet)\b",
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
        # Sanity: lot number normally increases (auction sequence). A lower
        # number is accepted only as a REAL out-of-order lot start — the
        # two-column layout that the block-end test below handles also puts
        # lot N physically after N+1 (Part V: 14046 after 14048, 14087/14088
        # after 14089) — recognised by the same signature: next non-blank
        # line is a region META line, and the number was not parsed yet.
        if lots and lot_no <= lots[-1]["lot_no"]:
            k = i + 1
            while k < n and not flat[k][1].strip():
                k += 1
            is_real_start = (
                k < n
                and META_LINE_RE.match(flat[k][1].strip())
                and all(l["lot_no"] != lot_no for l in lots)
            )
            if not is_real_start:
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
                if _in_lot_range(slug, next_lot):
                    # Ascending sequence → next-lot boundary (the common case).
                    if next_lot > lot_no:
                        break
                    # Descending / out-of-order lot number. A two-column PDF
                    # layout places lot N-1/N-2 physically AFTER lot N, so the
                    # ascending test alone never breaks there and the following
                    # lot's whole block — including its catalogue refs — bleeds
                    # into THIS lot (real case: lot 12088 ½ Dukat wrongly grabbed
                    # Dav-3621 from the descending neighbour 12087 Speciedaler).
                    # Break only on a REAL lot start: a lot-number line whose
                    # next non-blank line is a region META line. That signature
                    # distinguishes a genuine lot boundary from a stray 4-5 digit
                    # number occurring inside the body prose.
                    k = j + 1
                    while k < n and not flat[k][1].strip():
                        k += 1
                    if k < n and META_LINE_RE.match(flat[k][1].strip()):
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
                # Collapse whitespace the PDF line-wrap leaves INSIDE an
                # index («F- 53/F-57» → «F-53/F-57»); the value is a single
                # catalogue token, never a phrase.
                if k == "Skjoldager":
                    refs[k] = re.sub(r"\s+", "", mm.group(1))
                elif k == "Schive":
                    refs[k] = _schive_value(mm)
                else:
                    refs[k] = mm.group(1)
        # Year — meta_line first (cataloguer's authoritative dating),
        # body_match fallback. See `extract_year` for the failure modes
        # this guards against (pre-1500 floor + catalog-year traps).
        year = extract_year(meta_line, body_match)
        # Weight
        wmatch = WEIGHT_RE.search(body_match)
        weight_g = float(wmatch.group(1)) if wmatch else None
        if weight_g is None:
            lm = WEIGHT_LOOSE_RE.search(body_match)
            if lm:
                weight_g = float((lm.group(1) or lm.group(2)).replace(",", "."))
        # Grade
        gmatch = GRADE_RE.search(body_match)
        grade = f"{gmatch.group(1)} {gmatch.group(2)}" if gmatch else None
        # Rarity
        rarity = None
        rmatch = RARITY_RE.search(body_match)
        if rmatch:
            rarity = rmatch.group(1).upper()
        # Pattern flag (§9.1 patterns / trial strikes) + §9.2 medallic exonumia.
        #
        # Both tests run against the lot's DESCRIPTION only, not the whole
        # collected block. A lot block runs to the next lot-number line, so it
        # swallows whatever sits between the two: the closing «From the L. E.
        # Bruun Collection.» sentinel, `Ex: <provenance>` lines, page furniture
        # — and, crucially, the catalogue's section HEADLINE for the FOLLOWING
        # lot. Those headlines are written in Stack's Bowers' sales voice
        # («Extremely Rare and Historically Interesting Pattern», «Highly
        # Desirable Presentation Off-Metal Strike in Gold») and they precede the
        # lot they describe, so they can only ever land on the PREVIOUS lot's
        # block. Matching PATTERN_RE against the full block therefore excluded
        # the innocent neighbour: 20 lots were flagged by a trigger that appears
        # nowhere in their own description, among them 13262 (KM-154a, NGC
        # MS-65) and 13186 (KM-A433, the Hede-39 specimen cited in CLAUDE.md
        # §0b-1). The price line closes the description — it is present on every
        # lot that carries the sentinel, and earlier — so cut there.
        pm = PRICE_LINE_RE.search(body_match)
        desc_match = body_match[: pm.start()] if pm else body_match
        is_pattern = bool(PATTERN_RE.search(desc_match))
        # §9.2 exonumia — a «medallic» type that neither Krause (KM) nor Sieg
        # lists as a circulation coin is a medal, not a coin, and must not reach
        # the coin table. Real coins described as «medallic» in prose (e.g. lot
        # 11268 «2 Ducats 1711» KM-498, lot 11297 «Speciedaler 1800» KM-138.5)
        # DO carry a KM or Sieg number, so requiring BOTH absent keeps them.
        # Fires on lot 17105 Bruun-7235 («enigmatic equestrian medallic type
        # ... exists in silver struck from the same dies», KM-Unlisted /
        # Sieg-Unlisted). The seed builder drops any is_pattern lot.
        if (re.search(r"\bmedallic\b", desc_match, re.IGNORECASE)
                and not refs.get("KM") and not refs.get("Sieg")):
            is_pattern = True
        # §9.2 exonumia — a lot whose TITLE (the meta segment before the grade
        # / first catalogue ref) names a «Medal». Part V (Oct 2026) is the first
        # Bruun sale with a medal session (lots 15189-15283); 91 lots match, 0
        # in Parts I-IV. Title-only on purpose: the medal session also holds
        # real coins (15207 ¼ Speciedaler 1685, 15247 Platina 1830) that a
        # lot-range or body-prose test would drop.
        title_m = re.search(r"\b(?:NGC|PCGS|ANACS)\b|;", desc_match)
        title = desc_match[: title_m.start()] if title_m else desc_match[:200]
        if re.search(r"\bMedal\b", title, re.IGNORECASE):
            is_pattern = True
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
        # Second tier — the meta line was cut by a PDF line break, so the
        # « <X> Mint» token sits on the NEXT physical line and never reached
        # `meta_line` (which is one physical line by construction). Re-run the
        # structured pattern against the LEADING portion of `body_match`,
        # which is the same text already de-wrapped and de-hyphenated above
        # («Wolfenbüt -\ntel Mint» → «Wolfenbüttel Mint»).
        #
        # Real case (verified 2026-07-25): lots 13108 / 13109 / 13110, all
        # «DENMARK. Speciedaler (Reichstaler), 1627. Wolfenbüt -\ntel Mint».
        # meta_line stopped at «Wolfenbüt -», and the third tier below could
        # not recover it either because MINT_RE's hardcoded city list has no
        # Wolfenbüttel — so the mint was silently lost. NOTE the root cause is
        # the truncated meta_line plus the whitelist gap, NOT a missing
        # de-hyphenation: `body_match` was already correctly de-hyphenated.
        #
        # Window-limited to the meta line's own span (its length plus one
        # wrapped line) so this cannot re-introduce the Bruun-3725 failure the
        # META_MINT_RE comment describes, where an unrelated mint named later
        # in the historical prose gets grabbed.
        if mint is None and meta_line:
            window = body_match[:len(meta_line) + 80]
            mm_wrapped = META_MINT_RE.search(window)
            if mm_wrapped:
                mint = mm_wrapped.group(1).strip() + " Mint"
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
