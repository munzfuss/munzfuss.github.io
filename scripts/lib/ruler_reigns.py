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
    # Medieval rulers, for the reign-window placeholder of undated museum
    # pennies (curator 2026-10-17, undated-coins plan row 2). Kings from the
    # Danish regent list, da.wikipedia.org/wiki/Danmarks_regenter: Hardeknud
    # «1035-11-12 – 1042-06-08»; Magnus den Gode «Konge 1042 ved Hardeknuds
    # død», † 25.10.1047; Valdemar den Store «Konge over hele Danmark 23.
    # oktober 1157», † 12.5.1182; Christoffer 1. «Konge 29. juni 1252», †
    # 29.5.1259; Erik Menved «Konge 22. november 1286», † 13.11.1319;
    # Christoffer 2. 1320-1326 and 1329-† 2.8.1332 (one span here); «Den
    # kongeløse tid … 1332–1340»; Margrete 1. «Formynder for Olav Håkonsson
    # fra 3. maj 1376», † 28.10.1412.
    "Hardeknud":       (1035, 1042),
    "Magnus den Gode": (1042, 1047),
    "Valdemar I":      (1157, 1182),
    "Christoffer I":   (1252, 1259),
    "Erik VI":         (1286, 1319),  # Erik Menved
    "Christoffer II":  (1320, 1332),
    "Kongeløs tid":    (1332, 1340),
    "Margrete I":      (1376, 1412),
    # Jakob Erlandsen: «I 1249 blev han af paven indsat som biskop i
    # Roskilde», «I 1254 blev Jakob Erlandsen valgt til ærkebiskop i Lund»,
    # † 1274 (lex.dk/Jakob_Erlandsen). The KMM pennies give Roskilde, so the
    # span covers both sees; a rough placeholder, shown (?).
    "Jakob Erlandsen": (1249, 1274),
    # Norway: «Håkon 5. Magnusson var norsk konge i perioden 1299–1319»
    # (snl.no/Håkon_5._Magnusson).
    "Håkon V":         (1299, 1319),

    # Pre-1514 — relevant for the `denmark/p0_pre_lovkompleks`
    # bucket (Erik VII → Hans 1396-1513).
    "Erik VII":      (1396, 1439),
    "Christoffer III": (1440, 1448),
    "Christian I":   (1448, 1481),
    # Hans from 1483: the Rigsråd ruled 1481-1483 (below) and danskmoent dates
    # him «Hans (1483-1513)» (hans.htm) — curator 2026-10-20: «Rigsrådet це
    # 1481-1483, Hans 1483-1513». Sources writing 1481-1513 / 1482-1513 still
    # read as his reign through REIGN_SPAN_TOLERANCE.
    "Hans I":        (1483, 1513),  # also written «John I» in English ucoin
    # The Rigsråd's interregnum after Christian I's death. Its Hvide are
    # 1481-1483: «Bent Östergaard har visat att hviderna måste ha präglats
    # först 1481-1483 (Östergaard 1995)» (Eriksson 2017, Myntstudier, s. 4).
    # The Rigsråd's SKILLING is 1448 instead (Stefke 1995, same page) — the
    # 1448 interregnum. Every Rigsrådet coin in the data is a Hvid
    # (2026-10-17); a Rigsrådet skilling needs its own 1448 handling.
    "Rigsrådet":     (1481, 1483),

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
    # Sonderburg: Hans (Johann) der Jüngere received his third in the
    # Flensburg treaty of 27 Jan 1564 and died 9 Oct 1622 — «Im Flensburger
    # Vertrag (27.1.1564) überließ Kg. Friedrich II. von Dänemark seinem
    # jüngsten Bruder J. ein Drittel», † 9.10.1622 (H. W. Schwarz, «Johann der
    # Jüngere», Neue Deutsche Biographie 10, 1974, S. 534 f.,
    # deutsche-biographie.de/sfz53359.html). Full rule only from 1571 (same
    # article); the coinage window is the 1564-1622 span. His son Alexander
    # took Sønderborg at the division after his death and died 13 May 1627:
    # «Alexander (1573-1627) fik Sønderborg» (lex.dk, «sønderjyske
    # fyrstehuse»); death date de.wikipedia «Alexander (Schleswig-Holstein-
    # Sonderburg)». The other sons (1622/23) are not in the table yet.
    "sonderburg_duchy": {
        "Hans der Jüngere":  (1564, 1622),
        "Alexander":         (1622, 1627),
    },
    # Archbishopric of Bremen: Johann Friedrich of Holstein-Gottorp, from
    # 1596 — «gab er 1596 die Erzbischofswürde von Bremen an den
    # sechzehnjährigen Johann Friedrich ab» — † 3 Sept 1634 (de.wikipedia
    # «Johann Friedrich von Schleswig-Holstein-Gottorf»). Added 2026-10-19
    # for KMM 4 Skilling lybsk Jungk 316 (undated-coins plan row 8).
    "erzbisthum_bremen_verden": {
        "Johann Friedrich":  (1596, 1634),
    },
    # Schauenburg-Pinneberg: NumisMaster's ruler link «Ernst III 1601 - 1622»
    # (scripts/cache/numismaster/schleswig_holstein/MC_96084.html), requested
    # 2026-10-17 by the NGC-dates session for NGC «(after 1620)» KM 93-95.
    "schauenburg_pinneberg": {
        "Ernst III":         (1601, 1622),
    },
    # Kingdom of Norway after 1814 (entity `norway`). Reigns as kings of
    # Norway, en.wikipedia «List of Norwegian monarchs»: Charles II (XIII)
    # 4 Nov 1814 – 5 Feb 1818; Charles III John (XIV John) – 8 Mar 1844;
    # Oscar I – 8 Jul 1859; Charles IV (XV) «8 July 1859 – 18 September
    # 1872»; Oscar II – 1905; Haakon VII 18 Nov 1905 – 21 Sep 1957. Keys use
    # the Swedish numbering the coins and most sources print. Added
    # 2026-10-19 for KMM 673472/673473 «Carl 15.» (curator: «так»).
    "norway": {
        "Carl XIII":         (1814, 1818),
        "Carl XIV Johan":    (1818, 1844),
        "Oscar I":           (1844, 1859),
        "Carl XV":           (1859, 1872),
        "Oscar II":          (1872, 1905),
        "Haakon VII":        (1905, 1957),
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
    "schauenburg_pinneberg": {
        "ernst iii": "Ernst III", "ernst 3": "Ernst III",
    },
    "sonderburg_duchy": {
        # KMM «Hans den Yngre» (several spacings), NGC «Johann», German forms.
        # Only one Hans/Johann ruled Sonderburg.
        "hans den yngre": "Hans der Jüngere", "hans der jüngere": "Hans der Jüngere",
        "johann der jüngere": "Hans der Jüngere", "johann": "Hans der Jüngere",
        "johan": "Hans der Jüngere", "hans": "Hans der Jüngere",
        "alexander": "Alexander",
    },
    "norway": {
        # Swedish numbering (coins, Bruun, most of KMM) and Norwegian
        # numbering (KMM «Karl 3 Johan», «Karl 4»): Karl II = Carl XIII,
        # Karl III Johan = Carl XIV Johan, Karl IV = Carl XV. A bare «Oscar»
        # stays unresolved (I or II).
        "carl xiii": "Carl XIII", "karl xiii": "Carl XIII", "carl 13": "Carl XIII",
        "karl 13": "Carl XIII", "karl ii": "Carl XIII", "karl 2": "Carl XIII",
        "carl xiv johan": "Carl XIV Johan", "karl xiv johan": "Carl XIV Johan",
        "carl xiv": "Carl XIV Johan", "karl xiv": "Carl XIV Johan",
        "carl 14": "Carl XIV Johan", "karl 14": "Carl XIV Johan",
        "carl 14 johan": "Carl XIV Johan", "karl 14 johan": "Carl XIV Johan",
        "carl johan": "Carl XIV Johan", "karl johan": "Carl XIV Johan",
        "carl xiv jo": "Carl XIV Johan",
        "karl iii johan": "Carl XIV Johan", "karl 3 johan": "Carl XIV Johan",
        "oscar i": "Oscar I", "oscar 1": "Oscar I", "oskar i": "Oscar I", "oskar 1": "Oscar I",
        "carl xv": "Carl XV", "karl xv": "Carl XV", "carl 15": "Carl XV",
        "karl 15": "Carl XV", "karl iv": "Carl XV", "karl 4": "Carl XV",
        "oscar ii": "Oscar II", "oscar 2": "Oscar II", "oskar ii": "Oscar II", "oskar 2": "Oscar II",
        "haakon vii": "Haakon VII", "håkon vii": "Haakon VII",
        "haakon 7": "Haakon VII", "håkon 7": "Haakon VII",
    },
    "erzbisthum_bremen_verden": {
        "johann friedrich": "Johann Friedrich", "johan friedrich": "Johann Friedrich",
        "johan frederik": "Johann Friedrich", "johann frederik": "Johann Friedrich",
        "john frederick": "Johann Friedrich",
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
    name = re.sub(r"\s+", " ", name.replace(".", "")).strip().lower()
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
    # A bare «Hans» (KMM, Bruun, danskmoent write the king without a numeral)
    # is unambiguous: the table has one Hans, 1481-1513. «Hans?» (KMM's
    # uncertain attribution) is the same name with a doubt mark. «Johan» /
    # «Johann» are the Danish / German forms of the same king (IOHANNES on
    # the coins; KMM «Johan», Hvid Malmø; IKMK «Johann», København 1481).
    # «Johannes» stays out: KMM uses it for a medieval Odense penning.
    if re.fullmatch(r"(?i)(hans|john|johann?)\??", head):
        return "Hans I"
    _bare = _EXACT_BARE.get(_bare_key(head))
    if _bare is not None and _bare in RULER_REIGNS:
        return _bare
    if re.fullmatch(r"(?i)(rigsrådet|rigsraadet|riksrådet)\??", head):
        return "Rigsrådet"
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


# Names the kings' table holds under a single bearer, written without a
# numeral in the sources (KMM «Hans», «Rigsrådet»): the bare form IS the whole
# name, not a name with a qualifier dropped. Also the medieval names the
# numeral regex cannot read, and KMM's misspellings of a ruler's name
# (2026-10-17 survey of the Denmark-page undated coins) — each spelling exactly
# as KMM writes it, lower-cased, punctuation dropped, spaces collapsed.
_EXACT_BARE = {
    "hans": "Hans I", "john": "Hans I", "johan": "Hans I", "johann": "Hans I",
    "rigsrådet": "Rigsrådet",
    "rigsraadet": "Rigsrådet", "riksrådet": "Rigsrådet", "ridsrådet": "Rigsrådet",
    "hardeknud": "Hardeknud", "hardeknuyd": "Hardeknud",
    "magnus den gode": "Magnus den Gode", "magnud den gode": "Magnus den Gode",
    "valdemar i": "Valdemar I", "vardemar i": "Valdemar I",
    "valdemar den store": "Valdemar I",
    "christoffer 1": "Christoffer I", "chyristoffer 1": "Christoffer I",
    "christoffer i": "Christoffer I",
    "erik menved": "Erik VI", "ereik menved": "Erik VI", "erik vi": "Erik VI",
    "christoffer2": "Christoffer II", "chrstoffer 2": "Christoffer II",
    "ckristopher ii": "Christoffer II", "christopher ii": "Christoffer II",
    "christoffer 2": "Christoffer II", "christoffer ii": "Christoffer II",
    "kongeløs tid": "Kongeløs tid",
    "margrethe": "Margrete I", "margrete i": "Margrete I", "margrethe i": "Margrete I",
    "margrete 1": "Margrete I", "margrethe 1": "Margrete I",
    "jakob erlandsen": "Jakob Erlandsen",
    "håkon 5 magnusson": "Håkon V", "håkon v magnusson": "Håkon V",
    "kristian 1": "Christian I", "chrisytian 1": "Christian I",
    "chrtistian 4": "Christian IV", "chritian 4": "Christian IV",
}


def _bare_key(raw: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"[.,?]", " ", str(raw))).strip().lower()


def reign_lookup_is_exact(ruler: str | None) -> bool:
    """Did the reign lookup use the WHOLE ruler name, or drop a qualifier?

    `normalise_ruler_name` strips territorial and other qualifiers, so
    «Frederik III. von Gottorp» and «Frederik 3 som ærkebiskop» (Bremen,
    before he was king) both resolve to King Frederik III and come back with
    a window that is someone else's — or the same man's in another office.
    This test is deliberately strict: it passes only when the normalised name
    accounts for the entire raw name. It looks through the numeral form
    («Christian 4» = «Christian IV»), a trailing period, a doubt mark «?», and
    the single-bearer bare names in `_EXACT_BARE`. Moved here from absorb
    2026-10-17 so the merger and absorb share it.
    """
    if not ruler:
        return False
    norm = normalise_ruler_name(ruler)
    if not norm:
        return False
    if _EXACT_BARE.get(_bare_key(ruler)) == norm:
        return True
    raw = re.sub(r"[.,?]", " ", str(ruler)).lower().split()
    ref = str(norm).lower().split()
    if raw and ref and raw[-1].isdigit():
        raw = raw[:-1] + [ref[-1]]
    return raw == ref


def reign_window_exact(ruler_raw: str | None) -> tuple[int, int] | None:
    """`reign_window`, but only when the lookup used the whole name
    (`reign_lookup_is_exact`); None otherwise. Use this wherever a reign
    window is applied to data — a qualified name must not borrow a king's
    window."""
    return reign_window(ruler_raw) if reign_lookup_is_exact(ruler_raw) else None


_ALTERNATIVE_SPLIT_RE = re.compile(
    r"\s*(?:/|\beller\b|\bell\.|\boder\b|\bor\b|\s-\s|–)\s*", re.IGNORECASE)


# Issuing entities whose rulers ARE the Danish kings of `RULER_REIGNS` — the
# realm, Norway in the union, and the king's shares of Schleswig and Holstein.
# A same-named ruler of any other issuer is someone else: «Hans» on a Swedish
# coin is King Hans of Sweden 1497-1501, «Frederik 3» on a Bremen coin is the
# archbishop of 1634-1645, «Frederik 3» on a Gottorp coin the duke 1616-1659.
DANISH_CROWN_ENTITIES = frozenset({
    "danish_realm", "danish_norway", "royal_holstein", "royal_slesvig",
})


def reign_window_placeholder(ruler_raw: str | None,
                             entity: str | list | None = None) -> tuple[int, int] | None:
    """The year span to show for a coin NO source dates, from its ruler alone.

    Stricter than `reign_window` about whose window it is, looser about how
    many rulers the source names (absorb's placeholder, curator 2026-10-17):

      * the issuer decides whose table: a ducal house by `entity` or by a
        ruler string that names it («Frederik 3 af Slesvig-Holsten-Gottorp»
        → Duke Friedrich III, 1616-1659, not King Frederik III); the Danish
        kings only for `DANISH_CROWN_ENTITIES`; any other issuer → None (a
        Swedish «Hans», a Bremen «Frederik 3» are other men);
      * an alternative the source leaves open («Christian I/Hans ?», «Hans
        eller Christian 2», «Christian 3/4», «Frederik 7 eller Christian 9»)
        spans from the first reign's start to the last reign's end; a bare
        numeral («3/4») borrows the preceding name;
      * every part must be an exact name (`reign_lookup_is_exact`), so a
        qualified name («… som ærkebiskop», «… von Holsten-Gottorp» when the
        house table does not know him) yields None and the coin stays undated
        rather than borrowing someone else's reign.
    """
    if not ruler_raw or not isinstance(ruler_raw, str):
        return None
    ents = set(entity) if isinstance(entity, (list, tuple, set)) else ({entity} if entity else set())
    # A ducal house: by the issuing entity, or by a ruler string that itself
    # names the house («Frederik 3 af Slesvig-Holsten-Gottorp» on a
    # royal_holstein record).
    houses = [e for e in ents if e in HOUSE_REIGNS]
    for _pat, _h in ((r"gottorp", "gottorp_duchy"), (r"s[øo]nderb(?:o|u)rg", "sonderburg_duchy"),
                     (r"scha(?:u|ue)mburg|schauenburg|pinneberg", "schauenburg_pinneberg")):
        if re.search(_pat, ruler_raw, re.IGNORECASE) and _h not in houses:
            houses.append(_h)
    for h in houses:
        w = house_reign_window(ruler_raw.replace("?", "").strip(), h)
        if w is not None:
            return w
    # The kings' table only for an issuer of the Danish crown — matched by
    # entity, never by the name alone (curator 2026-10-17).
    if houses or not (ents & DANISH_CROWN_ENTITIES):
        return None
    # A bare «Johan» / «Johann» is King Hans only in the kingdoms: in the
    # duchies (royal_holstein / royal_slesvig) it can as well be Hans der
    # Jüngere of Sønderborg, whom NGC also writes «Johann».
    if (re.fullmatch(r"(?i)\s*johann?\s*\??\s*", ruler_raw)
            and not (ents & {"danish_realm", "danish_norway"})):
        return None
    parts = [p.strip(" ?") for p in _ALTERNATIVE_SPLIT_RE.split(ruler_raw) if p.strip(" ?")]
    if not parts:
        return None
    windows = []
    prev_name = None
    for part in parts:
        if part.isdigit() and prev_name:
            part = f"{prev_name} {part}"
        w = reign_window(part) if reign_lookup_is_exact(part) else None
        if w is None:
            return None
        windows.append(w)
        prev_name = part.split()[0]
    return (min(w[0] for w in windows), max(w[1] for w in windows))


# How far a source's range may sit from the reign table and still be read as
# «the reign, not a date». KMM writes Hans as 1483-1513, 1482-1513, 1481-1513
# and 1481-1512 (2026-10-19 survey: 250 records) — one man, the cataloguer's
# choice of accession year — so an exact match would miss most of them. The
# slack is also capped at a tenth of the reign: on a short reign a range a
# year or two inside it is a real issue span (Christian VIII «1841-1847»,
# Frederik VIII «1908-1912»), not the reign.
REIGN_SPAN_TOLERANCE = 2


def is_reign_span(ruler_raw: str | None, entity: str | list | None,
                  year_first: int | None, year_last: int | None) -> bool:
    """True when a source's year range is its ruler's reign window — a
    placeholder for an unknown date, not a dated attestation.

    Curator direction 2026-10-19: a reign window is shown when nothing better
    exists, but any narrower date from another source in the same class takes
    precedence. The merger uses this to hold such members back
    (`_year_demoted`), exactly like a curator `year_demote`.

    Whose reign is `reign_window_placeholder`'s call (entity-aware, exact
    names only). A single year is never a reign span; each end may sit up to
    `REIGN_SPAN_TOLERANCE` years — and at most a tenth of the reign — off
    the table.
    """
    if not isinstance(year_first, int) or not isinstance(year_last, int):
        return False
    if year_first >= year_last:
        return False
    w = reign_window_placeholder(ruler_raw, entity)
    if w is None:
        return False
    tol = min(REIGN_SPAN_TOLERANCE, (w[1] - w[0]) // 10)
    return abs(year_first - w[0]) <= tol and abs(year_last - w[1]) <= tol


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
