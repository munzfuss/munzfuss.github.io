"""Shared constants used by multiple Galster parser shapes.

These are deliberately kept tiny — most parsing logic stays inside
each shape's own module. Anything that grows to >10 LOC and is used
by ≥2 shapes belongs here.
"""
from __future__ import annotations

import re

# Sentinel emitted by `parse_galster._normalise_text` to mark <HR>
# section boundaries in the flattened plain text. Used by spec-block /
# description / litteratur parsers to delimit semantic regions.
HR_SENTINEL = "§§HR§§"

# Spec-block regex patterns. Each tuple is (pattern, output_key).
# Value normalisation (comma→dot, float-cast) is per-module since
# field-name post-processing varies slightly across shapes.
# NB: the «æ» in Vægt is written three ways across the cache — the literal
# «æ», the entity «&aelig;» (→ æ after unescape), and, on ~139 pages the
# fetcher decoded with the wrong charset, the replacement char U+FFFD (the
# original byte is lost, but the ASCII digits of the weight survive intact).
# So every vægt pattern accepts [æe�] to recover the number regardless.
SPEC_PATTERNS: list[tuple[str, str]] = [
    (r"Bruttov[æe�]gt:\s*([\d.,]+)\s*g", "bruttovaegt_g"),
    (r"Finhed:\s*([\d.,]+|\d+\s*[KkLl]od|\d+\s*K(?:arat)?(?:\s*\d+\s*[Gg]r[äa]n)?)", "finhed"),
    (r"Finv[æe�]gt:\s*([\d.,]+)\s*g", "finvaegt_g"),
    (r"Diameter:\s*([\d.,]+)\s*mm", "diameter_mm"),
    # Bare «Vægt 3,172 g» — article/uniquum pages (e.g. norge/hansGej) give a
    # single specimen weight without the «Bruttovægt:» label or a colon. Maps
    # to bruttovaegt_g (it IS the specimen's gross weight). The lookbehinds keep
    # it from stealing the tail of «Bruttovægt:» / «Finvægt:», which the two
    # labelled patterns above already own; this bare form only fires when
    # neither prefix precedes «Vægt».
    (r"(?<![Bb]rutto)(?<!Fin)(?<!fin)V[æe�]gt:?\s+([\d.,]+)\s*g", "bruttovaegt_g"),
]

# Spec lines SPEC_PATTERNS cannot read, because they print a range, a «ca.»
# figure, an average or a sub-type assay instead of one figure (measured on
# the cache 2026-11-05; curator decisions of the same day):
#   «Bruttovægt: 0,75-1,33g, gennemsnitligt 1,01g»      (epomg7 / 10 / 14 / 15)
#   «Bruttovægt (13 eksemplarer): 1,87g-2,38g, gennemsnit: 2,11g»   (bajg18)
#   «Vægt: 1,96-2,95g» · «Vægt 6,75-7,19g» · «Vægt: 1,70-2,17gg»
#   «Vægt mellem 1,83g og 2,28g»                        (fr/f1g64)
#   «Bruttovægt: ca. 0,73g»                             (norge/nf1g171)
#   «Finhed: 0,606-0,857» · «Finhed: 0,000-0,212»       (epomg4 / epomg5)
#   «Lødighed (prøve af Schou 60) 0,140»                (fr/f1g57)
# Each pattern stays on one line ([ \t], never \s) so a label never borrows a
# figure from the next spec line (Galster 172's «Finvægt \n 5,86g» table).
_N = r"(\d+[,.]\d+)"
_WEIGHT_LABEL = r"(?:Bruttov[æe�]gt|(?<![Ff]in)V[æe�]gt)(?:[ \t]*\([^)\n]*\))?[ \t]*:?[ \t]*"
_WEIGHT_RANGE_RE = re.compile(
    _WEIGHT_LABEL + r"(?:mellem[ \t]+)?" + _N + r"[ \t]*g?[ \t]*(?:-|–|og)[ \t]*" + _N + r"[ \t]*g")
_WEIGHT_CA_RE = re.compile(_WEIGHT_LABEL + r"ca\.[ \t]*" + _N + r"[ \t]*g")
_WEIGHT_AVG_RE = re.compile(r"gennemsnit(?:ligt)?[ \t]*:?[ \t]*" + _N + r"[ \t]*g")
_FINHED_RANGE_RE = re.compile(r"Finhed[ \t]*:[ \t]*" + _N + r"[ \t]*(?:-|–)[ \t]*" + _N)
_LOEDIGHED_RE = re.compile(r"Lødighed[ \t]*(?:\(([^)\n]*)\))?[ \t]*:?[ \t]*" + _N)


def _f(s: str) -> float:
    return float(s.replace(",", "."))


def parse_extra_specs(text: str, specs: dict) -> None:
    """Add to `specs` what the single-figure SPEC_PATTERNS miss (see above).

    - a weight range → `bruttovaegt_range_g: [min, max]` (only when no single
      weight was read);
    - «ca. N g» → `bruttovaegt_g` + `bruttovaegt_approx` (same keys as the
      sub-section path of fr/f1g48);
    - an average weight → `bruttovaegt_avg_g` (cache only: not a specimen
      weight, the seed does not carry it);
    - a fineness range → `finhed_range: [lo, hi]`, `finhed` keeping the lower
      bound it held before;
    - «Lødighed (prøve af …) N» → `loedighed` + `loedighed_note`.
    """
    if "bruttovaegt_g" not in specs:
        m = _WEIGHT_RANGE_RE.search(text)
        if m:
            specs["bruttovaegt_range_g"] = [_f(m.group(1)), _f(m.group(2))]
        else:
            m = _WEIGHT_CA_RE.search(text)
            if m:
                specs["bruttovaegt_g"] = _f(m.group(1))
                specs["bruttovaegt_approx"] = True
    m = _WEIGHT_AVG_RE.search(text)
    if m and ("bruttovaegt_range_g" in specs or "bruttovaegt_g" in specs):
        specs["bruttovaegt_avg_g"] = _f(m.group(1))
    m = _FINHED_RANGE_RE.search(text)
    if m:
        specs["finhed_range"] = [_f(m.group(1)), _f(m.group(2))]
    if "finhed" not in specs:
        m = _LOEDIGHED_RE.search(text)
        if m:
            specs["loedighed"] = _f(m.group(2))
            if m.group(1):
                specs["loedighed_note"] = m.group(1).strip()

# Mint-name vocabulary shared by every shape's mint parser.
#
# It used to live as three separate copies — `grevenfejde._MINT_WORD`,
# `standard._MINT_WORD` and an inline list inside
# `standard._parse_mint_line`. They drifted, and the drift was not
# cosmetic: a name missing from a list does not make the parser return
# «unknown», it makes it return the first name it DOES know from
# anywhere on the page. Measured on the committed cache (2026-08-21):
#
#   norge_nc2g172  source «Hamar eller Oslo (Norge)»      → parsed «Oslo»
#   norge_nc2g174  source «Hamar (Norge) eller København» → parsed «København»
#   norge_nha_g159 source «Hvid, Nidaros … Nidaros (Norge)» → parsed None
#   solvmont       source «Sølvmønt (?) u. år, Christiania» → parsed None
#   norge_hansg157 body «Hans, Hvid, Nidaros», page-title
#                  «Hans, Hvid Bergen»                    → parsed «Bergen»
#
# The last one is the reason this is one list and not three: the coin
# line said Nidaros, «Nidaros» was in no vocabulary, and the search fell
# through to a name that appears only in the page's title label.
#
# NOTE (§0): names are recognised, NEVER canonicalised here. Galster
# writes «Oslo» and «Nidaros»; the sidecar keeps the source's own
# spelling and `lib/v2_seed_writer._canonicalise_mint` maps it to the
# project form later. Phase 2 records what the page says.
MINT_WORD = (
    r"(?:København|Kobenhavn|Malmø|Malmö|Malmo|Husum|Gottorp|Roskilde|"
    r"Aarhus|Ribe|Bergen|Oslo|Visby|Stockholm|Flensborg|Landskrona|"
    r"Landskrone|Helsingør|Lund|Kalundborg|Kgs\.\s*Lyngby|"
    # Norwegian mints of the Galster «Norge» volume — absent from all
    # three legacy copies, which is what produced the misreads above.
    r"Hamar|Christiania|Nidaros|Kongsberg|"
    # Grevens-Fejde only: the Mecklenburg strikes.
    r"Güstrow|Mecklenburg|"
    # The Union kings before Hans (Erik af Pommern, Christoffer af Bayern)
    # and their Swedish / Finnish mints.
    r"Næstved|Naestved|Odense|Randers|Gurre|Aalborg|Vesterås|Åbo|Århus|Ronneby)"
)

# «A eller B» — Galster's own marker that the mint is not settled. Both
# arms are kept verbatim so the ambiguity survives into the seed and is
# not silently resolved to one town (§4: an uncertain attestation must
# not be promoted to a certain one).
MINT_ALTERNATIVE = rf"{MINT_WORD}(?:\s*\([^)]*\))?\s+eller\s+{MINT_WORD}"


# The Assens-find table of hansg31 (Galster 31), one row per Schou number:
#   « Schou \n Antal ex. \n Vægt, gennemsnit \n Finhed \n\n 125 \n 144 \n
#     0,73g \n 0,245-0,260 \n\n 127 \n 68 \n 0,77g \n … »
# A row is Schou number, count, average weight, and optionally a fineness or
# fineness range. The finenesses are assays of the find's groups; the
# averages are not specimen weights (curator 2026-11-05) and stay in the cache.
_SCHOU_TABLE_HEAD_RE = re.compile(
    r"^[ \t]*Schou[ \t]*\n[ \t]*Antal ex\.[ \t]*\n[ \t]*V[æe�]gt, gennemsnit[ \t]*\n"
    r"[ \t]*Finhed[ \t]*\n", re.MULTILINE)


def parse_schou_find_table(text: str) -> list[dict]:
    m = _SCHOU_TABLE_HEAD_RE.search(text)
    if not m:
        return []
    body = text[m.end():].split(HR_SENTINEL, 1)[0]
    toks = [t.strip() for t in body.split("\n") if t.strip()]
    rows: list[dict] = []
    i = 0
    while i + 2 < len(toks):
        schou, count, avg = toks[i], toks[i + 1], toks[i + 2]
        am = re.fullmatch(_N + r"g", avg)
        if not (schou.isdigit() and count.isdigit() and am):
            return []
        row = {"schou": schou, "count": int(count), "avg_g": _f(am.group(1))}
        i += 3
        if i < len(toks):
            fm = re.fullmatch(_N + r"(?:[ \t]*(?:-|–)[ \t]*" + _N + r")?", toks[i])
            if fm:
                row["finhed"] = [_f(x) for x in fm.groups() if x]
                i += 1
        rows.append(row)
    return rows
