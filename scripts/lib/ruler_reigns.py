"""Shared reign-window table for Danish-Norwegian kings, plus
helpers that normalise English/Danish/Roman/Arabic ruler-name
variants down to the canonical key. Used by seed builders to
flag ruler-attribution errors in source data (e.g. ucoin's
2026-05-22-discovered «1807 4 Skilling — Frederick VI» when
Christian VII actually reigned through 13 March 1808).

Sources for reign dates:
  * https://en.wikipedia.org/wiki/List_of_Danish_monarchs
  * https://en.wikipedia.org/wiki/List_of_Norwegian_monarchs
    (personal union 1380-1814; same kings 1514-1814)

Each entry is `(year_first, year_last)` — inclusive boundaries
in the calendar-year sense. The accession year counts as «in
reign» even if the king took the throne in December; same for
the death year. Real-month-of-death precision (e.g. Christian
VII died 13 March 1808 — so 1808 coins after that point are
Frederik VI's) sits in `ACCESSION_MONTH` for the rare cases
where it matters in our scope.
"""
from __future__ import annotations

import re
from functools import lru_cache


# Reign-year windows. Coin minted within [year_first, year_last]
# (inclusive both ends) is attributable to this ruler. Coins
# struck at the boundary year (accession or death) carry an extra
# month-level disambiguator in `_ACCESSION_MONTH` below — see
# `reign_covers_year_strict()`.
#
# Canonical key shape: «<Christian|Frederik> <Roman-numeral>» (no
# trailing period). Norwegian-only kings (rare in this project)
# would go under a separate table; we don't have any in scope
# 1514-1914 because the personal union kept Danish kings on the
# Norwegian throne until 1814.
RULER_REIGNS: dict[str, tuple[int, int]] = {
    # Pre-1514 — relevant for the `denmark/p0_pre_lovkompleks`
    # bucket (Erik VII → Hans 1396-1513).
    "Erik VII":      (1396, 1439),
    "Christoffer III": (1440, 1448),
    "Christian I":   (1448, 1481),
    "Hans I":        (1481, 1513),  # also written «John I» in English ucoin

    # Post-Lovkompleks Christian-II line.
    "Christian II":  (1513, 1523),
    "Frederik I":    (1523, 1533),
    # Civil-war / interregnum 1534-1536 — Christian III acclaimed
    # 1534, crowned 1537, sole king after Reformation 1537. For
    # reign-window purposes we use 1534 as start (de facto rule).
    "Christian III": (1534, 1559),
    "Frederik II":   (1559, 1588),
    "Christian IV":  (1588, 1648),
    "Frederik III":  (1648, 1670),
    "Christian V":   (1670, 1699),
    "Frederik IV":   (1699, 1730),
    "Christian VI":  (1730, 1746),
    "Frederik V":    (1746, 1766),
    # Christian VII formally reigned to his death on 13 March 1808.
    # Frederik VI was Regent from 1784 → king from Christian VII's
    # death. Coins dated 1808 ambiguous unless month known; pre-1808
    # is unambiguously Christian VII.
    "Christian VII": (1766, 1808),
    "Frederik VI":   (1808, 1839),
    "Christian VIII": (1839, 1848),
    "Frederik VII":  (1848, 1863),
    "Christian IX":  (1863, 1906),
    "Frederik VIII": (1906, 1912),
    "Christian X":   (1912, 1947),  # post-1914 OOS but kept for completeness
}


# ── Ducal houses ──────────────────────────────────────────────────────
#
# The table above is the Danish-Norwegian kings, and until now it was the
# whole world: `reign_window("Frederik 3")` answered 1648-1670 whoever asked.
# That is wrong for a Gottorp coin, whose Friedrich III ruled 1616-1659, and
# the two collide by name alone — as do Friedrich II and Friedrich IV. The
# only thing that separates them is WHICH HOUSE the coin belongs to, so the
# ducal tables are keyed by issuing entity and callers pass it explicitly.
# Without a house the kings' table answers, exactly as before.
#
# Ducal names are compound («Johann Adolf», «Christian Albrecht»), not
# name-plus-numeral, so they need their own alias map rather than the
# numeral regex.
#
# Source for the Gottorp line: en.wikipedia.org/wiki/Duchy_of_Holstein-Gottorp,
# «Dukes of Schleswig and Holstein at Gottorp» / «… at Kiel».
HOUSE_REIGNS: dict[str, dict[str, tuple[int, int]]] = {
    "gottorp_duchy": {
        "Adolf I":           (1544, 1586),
        "Friedrich II":      (1586, 1587),
        "Philipp":           (1587, 1590),
        "Johann Adolf":      (1590, 1616),
        "Friedrich III":     (1616, 1659),
        "Christian Albrecht": (1659, 1694),
        "Friedrich IV":      (1694, 1702),
        "Karl Friedrich":    (1702, 1739),
        "Karl Peter Ulrich": (1739, 1762),
        "Paul":              (1762, 1773),
    },
}

# Observed source spellings → canonical key inside a house table. Lowercased,
# punctuation-stripped on lookup. Forms taken from the KMM and NGC records
# actually in the cache («Christian Albrecht af Holsten-Gottorp», «Johan
# Adolph», «Karl Frederik»).
_HOUSE_ALIASES: dict[str, dict[str, str]] = {
    "gottorp_duchy": {
        "adolf": "Adolf I",
        "adolf i": "Adolf I",
        "friedrich ii": "Friedrich II", "frederik ii": "Friedrich II",
        "frederik 2": "Friedrich II",
        "philipp": "Philipp", "philip": "Philipp",
        "johann adolf": "Johann Adolf", "johan adolf": "Johann Adolf",
        "johan adolph": "Johann Adolf", "johann adolph": "Johann Adolf",
        "friedrich iii": "Friedrich III", "frederik iii": "Friedrich III",
        "frederik 3": "Friedrich III", "frederick iii": "Friedrich III",
        "christian albrecht": "Christian Albrecht",
        "christian albert": "Christian Albrecht",
        "friedrich iv": "Friedrich IV", "frederik iv": "Friedrich IV",
        "frederik 4": "Friedrich IV",
        "karl friedrich": "Karl Friedrich", "karl frederik": "Karl Friedrich",
        "carl frederik": "Karl Friedrich", "charles frederick": "Karl Friedrich",
        "karl peter ulrich": "Karl Peter Ulrich",
        "paul": "Paul",
    },
}

_HOUSE_SUFFIX_RE = re.compile(
    r"\s+(?:af|von|of)\s+.*$", re.IGNORECASE)


def house_reign_window(ruler_raw: str | None,
                       house: str | None) -> tuple[int, int] | None:
    """Reign window for a ruler of a named ducal house, or None.

    Strips a trailing territorial epithet — «Christian Albrecht af
    Holsten-Gottorp» is the same man as «Christian Albrecht» — then looks the
    remainder up in that house's alias map. Returns None when the house is
    unknown or the name does not resolve, so a caller can fall through to the
    kings' table rather than guess.
    """
    if not ruler_raw or not isinstance(ruler_raw, str) or not house:
        return None
    aliases = _HOUSE_ALIASES.get(house)
    if not aliases:
        return None
    name = _HOUSE_SUFFIX_RE.sub("", ruler_raw.strip())
    name = name.replace(".", "").strip().lower()
    key = aliases.get(name)
    if key is None:
        return None
    return HOUSE_REIGNS.get(house, {}).get(key)


# Accession month for boundary-year disambiguation. Keyed by ruler
# name; value = (year, month) of accession. Coin year falling in
# the accession year BEFORE this month belongs to the PREDECESSOR;
# from this month onward to the new ruler. Currently the only
# scope-relevant boundary that needs month precision is Frederik
# VI's accession after Christian VII's death 1808-03-13.
_ACCESSION_MONTH: dict[str, tuple[int, int]] = {
    "Frederik VI": (1808, 3),  # post-Christian-VII death 13 March 1808
}


# Name-normalisation table — maps ucoin / numismaster / Bruun /
# Galster name forms (English vs Danish spellings, with or without
# trailing period) to the canonical key in `RULER_REIGNS`.
#
# Forms observed in real source data (2026-05-22 survey of ucoin
# cache):
#   ucoin English: «Frederick II», «Christian VI», «Christian V /
#                  Frederick III» (joint attribution)
#   ucoin Danish:  «Frederik VI», «Frederik VII» (occasional)
#   Hede / Galster: «Christian 3.» (Arabic numeral + period),
#                  «Frederik V.» (Roman + period)
#   English first-name aliases: «John I» = «Hans I»
_NAME_NORMALISE: dict[str, str] = {
    # English «Frederick» → Danish «Frederik» (canonical key form).
    "Frederick": "Frederik",
    # English «John» → Danish «Hans» (only Hans I 1481-1513).
    "John I": "Hans I",
}

_ARABIC_TO_ROMAN = {
    "1": "I", "2": "II", "3": "III", "4": "IV", "5": "V",
    "6": "VI", "7": "VII", "8": "VIII", "9": "IX", "10": "X",
}

_RULER_RE = re.compile(
    r"\b(Christian|Frederik|Frederick|Hans|Erik|Christoffer|John)\b"
    r"\s*"
    r"(\d+|[IVX]+)"
    r"\.?",
    re.IGNORECASE,
)


def normalise_ruler_name(raw: str | None) -> str | None:
    """Map any ruler-name variant to a canonical key for `RULER_REIGNS`.

    Returns None when the input doesn't contain a recognisable
    ruler-name token (allowing the caller to no-op rather than
    fabricate a reign window).

    Handles:
      * English «Frederick X» → «Frederik X»
      * Trailing period «Christian VII.» → «Christian VII»
      * Arabic numeral «Christian 3.» → «Christian III»
      * Alias «John I» → «Hans I»
      * Joint attribution «Christian V / Frederick III» — returns
        the FIRST name only; caller can treat joint cases via the
        full string passed in if needed.
    """
    if not raw or not isinstance(raw, str):
        return None
    # Joint-attribution form: take the first half before « / » so
    # «Christian V / Frederick III» → «Christian V».
    head = raw.split("/", 1)[0].strip()
    m = _RULER_RE.search(head)
    if not m:
        return None
    name, numeral = m.group(1), m.group(2)
    # Capitalise first letter; rest as-is (handles «christian» etc.).
    name = name[0].upper() + name[1:].lower()
    # English → Danish form.
    name = _NAME_NORMALISE.get(name, name)
    # Arabic → Roman.
    if numeral.isdigit():
        numeral = _ARABIC_TO_ROMAN.get(numeral, numeral)
    else:
        numeral = numeral.upper()
    candidate = f"{name} {numeral}"
    # Alias-pass for combined «Name Numeral» forms.
    candidate = _NAME_NORMALISE.get(candidate, candidate)
    if candidate in RULER_REIGNS:
        return candidate
    return None


def reign_window(ruler_raw: str | None,
                 house: str | None = None) -> tuple[int, int] | None:
    """Return `(year_first, year_last)` for the named ruler, or None
    when the ruler name doesn't resolve to any known entry.

    `house` is an issuing-entity tag. When given and known, that house's
    ducal table is consulted FIRST — «Frederik 3» is the Danish king
    1648-1670 or the Gottorp duke 1616-1659 depending on it. Omitting it
    keeps the historical behaviour: the kings' table only.
    """
    ducal = house_reign_window(ruler_raw, house)
    if ducal is not None:
        return ducal
    key = normalise_ruler_name(ruler_raw)
    if key is None:
        return None
    return RULER_REIGNS.get(key)


def reign_covers_year(ruler_raw: str | None, year: int | None,
                        tolerance: int = 0) -> bool | None:
    """True/False/None: does the ruler's reign cover `year`?

    * True  — year falls within (year_first, year_last) inclusive
              ±`tolerance` years.
    * False — year is OUTSIDE the reign even with tolerance
              (e.g. 1807 vs Frederik VI 1808-1839 → False).
    * None  — ruler name unrecognised OR year is None (insufficient
              data to decide).

    `tolerance` is intended for documented boundary cases — most
    callers should pass 0 (strict). The accession-month table is
    NOT consulted here; use `reign_covers_year_strict()` for that.
    """
    win = reign_window(ruler_raw)
    if win is None or year is None:
        return None
    yf, yl = win
    return (yf - tolerance) <= int(year) <= (yl + tolerance)


# ---------------------------------------------------------------------------
# Comparison KEY (distinct from `normalise_ruler_name` above)
# ---------------------------------------------------------------------------
# Two different jobs live in this module and must not be conflated:
#   * `normalise_ruler_name` produces a canonical DISPLAY name for the
#     RULER_REIGNS index — title case, «Christian IV».
#   * `normalise_ruler_key` (below) produces a lowercased MATCHING key for
#     cross-source comparison — «christian iv» — folding language variants
#     (Frederick / Friedrich / Fredrik → frederik, Charles / Carl → karl)
#     that the display name deliberately keeps apart.
# The key moved here from merge_seeds_cross_source in 2026-09-21: it was the
# last comparison normaliser still living in a caller rather than in the
# shared module (nominals delegate to lib/nominal_synonyms), and
# lib/seed_thin needs it to bucket by the same signals the merger matches on.
# Folding a German ruler form onto its Danish counterpart is safe because the
# POLITY is handled by the SCOPE of comparison, never by this key: the merger
# only ever compares coins within one issuing entity, and the kmk seeds are
# one file per entity, so thinning buckets are entity-scoped too.

_REGNAL_ARABIC_ROMAN = {
    1: "i", 2: "ii", 3: "iii", 4: "iv", 5: "v", 6: "vi", 7: "vii", 8: "viii",
    9: "ix", 10: "x", 11: "xi", 12: "xii", 13: "xiii", 14: "xiv", 15: "xv",
    16: "xvi", 17: "xvii", 18: "xviii", 19: "xix", 20: "xx",
}


def _regnal_arabic_to_roman(s: str) -> str:
    """Convert a TRAILING 1-2-digit regnal number to roman for MATCHING.
    ucoin / Numista write «Christian 4» / «Frederik 3»; Hede / Bruun write
    «Christian IV» / «Frederik III» — same monarch, but the arabic-vs-roman
    numeral fragments every Danish king (≈19k coins). Canonicalise to roman.

    GUARDS (so two different rulers are never folded):
      • only a TRAILING number is converted (with optional «?»), so
        «Karl 3 Johan» (embedded → Karl XIV Johan) is left alone;
      • the name-part must carry NO other digit and NO joint/uncertain
        separator («eller» / «or» / «/»), so «Frederik 7 eller Christian 9»
        is left alone;
      • numbers outside 1-20 are left as-is.
    Matching only — the stored ruler keeps its source form.
    """
    m = re.match(r"^(.+?)\s*(\d{1,2})\??$", s)
    if not m:
        return s
    name = m.group(1).strip()
    if not name or re.search(r"\d", name):
        return s
    if any(tok in name for tok in (" eller ", " or ", "/")):
        return s
    roman = _REGNAL_ARABIC_ROMAN.get(int(m.group(2)))
    return f"{name} {roman}" if roman else s


@lru_cache(maxsize=None)
def normalise_ruler_key(ruler):
    """Canonicalise a ruler string for cross-source comparison.

    @lru_cache: pure str→str (ruler is a scalar string or None). Profiling
    the royal_holstein merge showed this called 1.55 M times costing 21 s
    uncached — the same shape as `_normalise_nominal`, which costs 0.28 s
    BECAUSE it is cached. match_pair re-normalises the same handful of ruler
    strings across every O(n²) pair; memoising collapses that to one compute
    per distinct ruler. (2026-06-04 perf pass.)

    Variants normalised to the same form (so reign-index queries +
    cross-source matcher hits don't fragment over spelling artefacts):

      «Christian IV.»     →  «christian iv»
      «Christian IV»      →  «christian iv»
      «Christian IV. (1588-1648)»  →  «christian iv»
      «Christian VII, der …»  →  «christian vii»
      «Frederik IV 1699 - 1730»  →  «frederik iv»  (NumisMaster reign-bleed)
      «Christian VII 1766 - 1808 Issuer: Danish …»  →  «christian vii»  (NumisMaster Issuer-bleed)
      «Friedrich III. von Schleswig-Holstein-Gottorp»  →  «frederik iii»

    Returns lowercased, trailing-period-stripped, single-spaced.
    """
    if not ruler:
        return ""
    s = str(ruler)
    # Drop parenthetical reign annotations, e.g. «(1588-1648)»
    s = s.split("(")[0]
    # Drop comma-tail descriptive epithets, e.g. «Christian VII, der …»
    s = s.split(",")[0]
    # Drop «Issuer:» bleed-through from NumisMaster pages
    s = re.split(r"\s+Issuer\s*:", s, maxsplit=1)[0]
    # Drop trailing «1699 - 1730» reign-year tail (NumisMaster mass-pollution
    # already handled by parse_numismaster._clean_ruler, but defensive here
    # so older seeds + future sources stay normalised)
    s = re.sub(r"\s+\d{4}\s*-\s*\d{0,4}\s*$", "", s)
    # Drop «von <house>» / «af <kingdom>» trailing peerage
    s = re.split(r"\s+(?:von|af|of|zu)\s+", s, maxsplit=1)[0]
    # Strip trailing dots + whitespace, normalise internal whitespace.
    # Combined `[\s.]+$` handles the «Christian IV. (1588-1648)» path
    # where split("(")[0] leaves «Christian IV. » — trailing space had
    # to be stripped BEFORE the dot-strip could catch the dot, otherwise
    # «christian iv.» leaked through with dot intact.
    s = re.sub(r"[\s.]+$", "", s)
    s = re.sub(r"\s+", " ", s)
    s = s.lower()
    # English / parser-artefact spelling normalisations. The Danish
    # form is «Frederik» (no `c` before `k`); some sources / parsers
    # render it «Frederick» which fragments index attestation. Same
    # for «Christian» (no variant) — kept for symmetry future-proof.
    # «Frederick»(en) / «Friedrich»(de) / «Friederich»(typo) → «frederik»
    # (Danish canonical). MATCHING-only spelling fold. Safe despite German
    # «Friedrich» rulers being distinct people from Danish «Frederik»: the
    # matcher is per-entity (cross-entity Friedrichs never compared) and
    # match_pair's year/catalog fallback separates same-name-same-numeral
    # rulers within an entity (e.g. _unclassified «Friedrich III» 1491 vs
    # 1888 → years disagree → no_match). Verified per-entity 2026-06-03.
    # «Fredrik»(sv/no) + «Friedric»(truncation typo) joined the alternation
    # 2026-07-30: the fold covered every foreign spelling EXCEPT the two the
    # Scandinavian sources actually use, so KMM's «Fredrik 5» / «Carl Friedric»
    # fragmented from every other source's «Frederik V» / «Karl Friedrich».
    # Longer alternatives stay first — «friedrich» must win over «friedric».
    s = re.sub(r"\b(?:frederick|friedrich|friederich|friedric|fredrik)\b",
               "frederik", s)
    # Cross-language ruler-name synonyms — different sources use the
    # English vs Danish/Norwegian form for the same monarch.
    #
    #   «John I» / «John I (Hans I)» (Numista English) ↔ «Hans» (Bruun,
    #       Hede, danskmoent.dk Danish form). Hans of Denmark (1455-1513)
    #       reigned 1481-1513 as Hans / Johann / John I.
    #   «John II» (Sweden side via Kalmar Union) — same Hans, period
    #       Swedish attestation. Same canonical.
    #   «Eric» ↔ «Erik» (Erik VII of Pomerania, Erik XIV, etc.)
    #   «Margaret» ↔ «Margrethe» (Margrethe I, Margrethe II).
    #
    # Canonical form is the Danish (matches Hede/Galster/our project YAML).
    # The parenthetical clipping above («John I (Hans I)» → «John I») runs
    # before lowercase, so by the time we get here the input is the bare
    # English form.
    if s in ("john i", "john ii"):
        s = "hans"
    s = re.sub(r"\beric\b", "erik", s)
    s = re.sub(r"\bmargaret\b", "margrethe", s)
    # Leading ruler-TITLE strip — «Hertug …»/«Herzog …»/«Duke …»/«Ærkebisp …»
    # /«Erkebisp …»/«Archbishop …» are not part of the identity (the name
    # discriminates). Folds «Hertug Johan Adolf» → «johan adolf» and
    # «Ærkebisp Johann Friedrich» → «johann friedrich» (Bremen-Verden
    # archbishop — now safe to fold with the Frederik spelling work below).
    s = re.sub(r"^(?:hertug(?:en)?|herzog|duke|ærkebisp(?:pen)?|erkebisp|archbishop)\s+", "", s)
    #   «Johan Adolf» / «Johan Adolph» / «Johan Adolg»(typo) / «Johann Adolf»
    #   / Adolph — Danish «Johan»(1n) vs German «Johann»(2n) + adolf/adolph
    #   spelling of the SAME Holstein-Gottorp duke (r. 1590-1616). Reign-
    #   window + entity survey (2026-06-03) confirms every NO-NUMERAL form
    #   is this one duke (gottorp/royal_holstein/danish_realm, 1579-1615).
    #   The numeral-lookahead guard keeps «Johann Adolph I» (Holstein-
    #   Norburg-Plön, 1690) DISTINCT; the per-entity matcher prevents the
    #   pre-existing gottorp↔norburg_plön «johann adolf» label overlap from
    #   cross-merging. «John Adolphus» (English) is handled by the next sub.
    s = re.sub(r"\bjohann?\s+adol(?:f|ph|g)\b(?!\s+[ivx]\b)", "johann adolf", s)
    #   «John Adolphus» (Numista English) ↔ «Johann Adolf» (German) —
    #   Johann Adolf von Holstein-Gottorp, Duke 1590-1616. Verified safe by
    #   reign-window + entity survey (2026-06-03): the bare «John Adolphus»
    #   form appears only in gottorp_duchy 1590-1611 = this one duke.
    #   GUARDS (negative lookahead on a trailing roman numeral):
    #     - «John Adolphus I» (Holstein-Norburg-Plön, 1690) — a DIFFERENT
    #       duke — stays untouched (the «I» blocks the match).
    #     - Bare «Adolf» (grandfather Adolf I, 1544-1586), Schauenburg counts
    #       «Adolf XIII/XIV», «Hans Adolf», «Adolf Friedrich» are different
    #       strings → never touched.
    #   The matcher is per-entity, so even the pre-existing «johann adolf»
    #   gottorp↔norburg_plön label overlap can't cross-merge.
    s = re.sub(r"\bjohn adolphus\b(?!\s+[ivx]\b)", "johann adolf", s)
    #   «John/Johan/Johann Frederik» — Danish «Johan»(1n)/English «John» vs
    #   German «Johann»(2n) of the SAME compound-name ruler (Friedrich→
    #   frederik already applied above). Per-entity matcher + reign window
    #   verified one ruler per entity (e.g. Bremen-Verden archbishop Johann
    #   Friedrich 1596-1622). Numeral guard keeps «Johann Frederik I»
    #   (Saxony elector, 1535) DISTINCT; bare «Johan»/«John» (Hans the
    #   Younger / John I of Denmark) is untouched (only the +Frederik
    #   compound folds).
    s = re.sub(r"\bjoh(?:n|an|ann)\s+frederik\b(?!\s+[ivx]\b)", "johann frederik", s)
    #   «Christian Albert»(en) ↔ «Christian Albrecht»(de) — Christian Albrecht
    #   von Holstein-Gottorp, Duke 1659-1695. Reign-window + entity survey
    #   (2026-06-03): both forms = this one duke (gottorp/royal_holstein/
    #   danish_realm/hamburg, 1661-1694). Fold to the German canonical.
    #   Targets only the «Christian Alb…» compound, so bare «Albrecht»
    #   (Wallenstein etc.), «Johan Albrecht I», «Albrecht II. Alcibiades»
    #   are untouched; numeral guard reserves any future «Christian Albrecht I».
    s = re.sub(r"\bchristian\s+alb(?:recht|ert)\b(?!\s+[ivx]\b)", "christian albrecht", s)
    # Cross-language ruler-NAME translations — NAME component only, the
    # regnal NUMERAL is preserved (user direction 2026-06-09: «імʼя не може
    # йти окремо від порядкового номера»). Numista publishes English ruler
    # names; NumisMaster / Bruun / Hede the German/Danish form. Folding the
    # NAME (not the numeral) lets «Charles Frederick» ≡ «Karl Friedrich»
    # and «Francis William» ≡ «Franz Wilhelm» merge, while «George IV»
    # stays ≠ «Charles II» (different name → «georg iv» ≠ «karl ii») and
    # «Frederik VI» stays ≠ «Frederik IX» (different numeral). The POLITY is
    # handled by the per-entity matcher — same name+numeral in two
    # different issuing entities is never compared (so a same-named ruler
    # of two different lands cannot cross-merge). Whole-word, German-states
    # canonical (every Charles/Karl, George/Georg, etc. in scope is a
    # German/Norwegian/Swedish ruler — there is no Danish «Karl»).
    # «Carl» joined 2026-07-30, same gap as «Fredrik» above: the ENGLISH
    # spelling folded to the canonical while the SCANDINAVIAN one did not, so
    # KMM's «Carl XIV Johan» / «Carl XI» / «Carl Frederik» never matched the
    # «Karl …» every other source publishes.
    s = re.sub(r"\b(?:charles|carl)\b", "karl", s)
    s = re.sub(r"\bgeorge\b", "georg", s)
    s = re.sub(r"\bwilliam\b", "wilhelm", s)
    s = re.sub(r"\bfrancis\b", "franz", s)
    s = re.sub(r"\bernest\b", "ernst", s)
    s = re.sub(r"\baugustus\b", "august", s)
    s = re.sub(r"\bhenry\b", "heinrich", s)
    s = re.sub(r"\berich\b", "erik", s)
    s = re.sub(r"\badolphus\b", "adolf", s)
    # Arabic→roman regnal numeral (Christian 4 → christian iv, etc.) — LAST,
    # after spelling/synonym folds, so the name-part is already canonical.
    s = _regnal_arabic_to_roman(s)
    return s
