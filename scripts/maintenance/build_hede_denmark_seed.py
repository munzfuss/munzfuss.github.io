"""Build a Coin-schema seed YAML for `data/locations/denmark.yml`
from the parsed Hede catalogue cache (`scripts/cache/hede/*.json`).

Each parsed Hede entry whose mint is a Danish royal mint (København /
Frederiksborg / Helsingør) becomes a Coin-shaped entry in the seed.
Multi-Hede pages (specs.by_hede with ≥2 sub-variants) expand into one
entry per sub-Hede when the page's joined nominal can be split on the
comma-list pattern «X, Y, Z og W <Denom>»; otherwise the entry is
skipped for manual review.

The output is consumed by `scripts/build.py` as an auto-merged seed
side-car for the location page (`data/locations/denmark.yml`) — see
`scripts/build.py::_merge_seeds_into_raw`. The seed file is the
canonical intermediate: filtering by year + mint happens HERE so the
file the build reads is already scoped to what should ship.

Conventions match the existing ucoin-derived bulk block in
`denmark.yml`:
  * id: `dk-hede-<volume><number>` (e.g. `dk-hede-c5h120`)
  * fuss: `seed_unsorted`, phase: `A` — the catch-all bucket
  * All `*_verified` flags set to `false`
  * sources: type=literature pointing to the danskmoent.dk URL

The `--year-to` flag (default 1914 — the project's scope upper
bound per CLAUDE.md) caps the seed at that year inclusive; entries
whose `year_first` is after the cap are dropped. Stored in the
seed file's header for traceability so the next reader knows what
scope the file represents without re-running.

Curation-preserving merge
-------------------------

The seed file is generator-output, but it accumulates HUMAN CURATION:
every coin in the existing seed has at least `fuss` + `phase` set
to a real classification (not `seed_unsorted` / `hede`), most also
have `fraction` set, some have non-default `issuing_entity` or
`kind`, and a handful have manually-customised nominal / catalog /
note / sources fields.

A naive rewrite would obliterate that curation every time the
generator runs. To avoid that, the generator now MERGES its fresh
output against the existing on-disk seed (when one is present):

  * `CURATED_FIELDS` (fuss, phase, fraction, issuing_entity, kind,
    note, mint_verified, verified) — if the existing entry has a
    non-default value, that value is preserved; the fresh value is
    discarded.
  * `DEEP_MERGE_FIELDS` (catalog) — keys from the existing entry are
    preserved, keys from fresh are added when not already present.
    Lets curation add Bruun citation fields (km, dav, bruun_*) on
    top of parser-derived Hede / Schou / Sieg defaults.
  * Per-entry escape hatch: `_curation_holds` — a private meta-field
    on a coin entry naming additional fields whose values should be
    preserved across regen. Two accepted shapes (both yield the same
    frozen-field set via `set(...)` parsing):

      List form (legacy, bare names — backward-compatible):
        _curation_holds: [fineness, fineness_verified, verification_note]

      Dict form (PREFERRED — carries «why» rationale per field):
        _curation_holds:
          fineness: "Canonical .98611111 Müntzfuß-anchor per CLAUDE.md §4"
          fineness_verified: ~                  # null = freeze without commentary
          verification_note: "Extended with Müntzfuß-anchor rationale"

    Used when curation also customised a field outside CURATED_FIELDS
    (cleaned up the nominal, switched to a multi-source weight list,
    dropped a default verification_note after manual confirmation).
    Curator authoring a NEW hold SHOULD use dict-form with a reason
    so future sessions understand the manual override without
    archaeological reconstruction.
  * `_VERIFIABLE_FIELDS` (fineness / weight_rough_g / diameter_mm /
    mint) — verified-wins-over-unverified rule per CLAUDE.md §4:
    when both candidates carry a value, and the EXISTING side is
    source-attested (`*_verified: true`) while FRESH is unverified
    (`(?)` marker — flag absent or false), the existing value
    survives. The unverified fresh reading must NOT overwrite a
    curated, source-cited one — this guards against parser /
    canonical-anchor regressions clobbering hard-won citations.
  * Everything else flows from fresh — so parser fixes, weight
    refinements, and added sub-types all reach the seed
    automatically without manual re-curation.
  * New ids (in fresh but not existing) — added with default
    `seed_unsorted` / `hede` (signals pending curation).
  * Removed ids (in existing but not in fresh) — kept verbatim and
    flagged as «orphan curated» in the run summary. The user may
    decide to drop them manually; the generator never drops a
    curated entry on its own (parser instability could otherwise
    silently delete shipped data).

`--no-merge` runs the legacy wholesale-rewrite behaviour (used by
the dry-run / verification path; never recommended for the canonical
seed file).

Run:
    python scripts/maintenance/build_hede_denmark_seed.py
    python scripts/maintenance/build_hede_denmark_seed.py --year-to 1900
    python scripts/maintenance/build_hede_denmark_seed.py --no-merge  # wholesale
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
from pathlib import Path

from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap, CommentedSeq

# Words inside a nominal that should NOT be Title-Cased ("og" = Danish
# «and», kept lowercase per period-form usage).
_NOMINAL_LOWERCASE_WORDS = {"og", "und", "and"}

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lib.catalog_codes import catalog_from_ref_dict  # noqa: E402
from lib.paths import HEDE_CACHE, PROJECT_ROOT as PROJECT  # noqa: E402
from lib.v2_entity_classify import classify_mint_to_entity  # noqa: E402
from lib.v2_seed_writer import write_v2_seed  # noqa: E402
from lib.note_extract import source_note  # noqa: E402


def _classify_hede_entity(mint, hede_volume: str | None):
    """Hede coin → V2 issuing_entity.

    Mint-driven via the centralised classifier when mint is available
    (covers Altona/Glückstadt → royal_holstein, Kongsberg/Christiania
    → danish_norway, Rendsborg → gottorp_duchy, etc.).

    Volume-prefix fallback for entries lacking explicit mint:
      `nc*h` (Norge under Christian) / `nf*h` (Norge under Frederik) →
      danish_norway (Hede 1971's Norge sub-pages). Everything else
      defaults to danish_realm.
    """
    if mint:
        result = classify_mint_to_entity(mint)
        if result:
            return result
    if hede_volume and hede_volume.startswith(("nc", "nf")):
        return "danish_norway"
    return "danish_realm"



# Hede entries representing proof / trial / pattern strikes (Danish
# «Prøvemønt», «Probe», unique-specimen-only museum holdings) that the
# project explicitly excludes per CLAUDE.md §9 — they were not struck
# for circulation, so they don't belong in the location's coin table.
# Each entry is the Hede page id as cached under scripts/cache/hede/
# (e.g. `c4h20`). The skip happens early in the seed-build loop so
# the entries never reach the curation-merge step.
_KNOWN_PROOF_PATTERNS: set[str] = {
    # Christian IV.
    "c4h20",   # «Guldmønt U.år» Kbh, Hede 20 / Schou 8 / Sieg 159 —
               # Prøvemønt efter engelsk forbillede; Unik in
               # Den Kgl. Mønt- og Medaillesamling København.
    "c4h21",   # «Guldmønt u. år» Kbh, Hede 21AB / Schou 10-12 / Sieg 158 —
               # Prøvemønt efter engelsk forbillede; RRR/Unik in
               # Den Kgl. Mønt- og Medaillesamling København. Per Anders
               # Harck (2000): Hede Nr. 20-22 are all proof strikes from
               # the same period (portrait type 4 / reverse of type 6).
    "c4h22",   # «Guldmønt, U.år» Kbh, Hede 22 / Schou 13 / Sieg 157 —
               # «Prøvemønt efter engelsk forbillede»; Unik in Den Kgl.
               # Mønt- og Medaillesamling København. Forsidestempel
               # shared with 8 Skilling 1606 (Hede 93). Same Harck-2000
               # proof cluster as c4h20 + c4h21.
}


# Fields whose existing-entry value is ALWAYS preserved across regen
# when present (i.e. when the existing value differs from what the
# fresh generator would emit). These represent human curation
# decisions that the parser/cache cannot reconstruct:
#   * fuss — which Müntzfuß this coin belongs to (default
#     `seed_unsorted` signals pending curation; any other value is
#     a curated decision)
#   * phase — phase-within-fuss label (default `hede`; curated to
#     I, II, III, pre-I, IV, …)
#   * fraction — canonical Müntzfuß fraction this coin represents
#   * issuing_entity — danish_realm / royal_holstein / gesamtstaat /
#     provisional_govt — curatorial decision about political
#     attribution that depends on context the parser doesn't see
#   * kind — kurant / scheide / tarif / gedenk — economic-category
#     classification per CLAUDE.md §6
#   * note — historical / methodological annotations
#   * mint_verified / verified — flags flipped after manual
#     verification work; never auto-reset
CURATED_FIELDS = frozenset({
    "fuss",
    "phase",
    "fraction",
    "issuing_entity",
    "kind",
    "note",
    "mint_verified",
    "verified",
})

# Fields whose VALUE is a dict that is DEEP-MERGED rather than
# replaced. Keys present in the existing entry are preserved;
# keys present in fresh but missing in existing are added.
# `catalog` is the only such field in practice — curation often
# adds Bruun citation keys (km, dav, bruun_collection_id,
# bruun_part, bruun_lot_no, bruun_page) on top of the Hede /
# Schou / Sieg keys the parser supplies.
DEEP_MERGE_FIELDS = frozenset({
    "catalog",
})

# Per-entry meta-field name. When set on a coin entry, lists
# additional field names whose existing-entry value should be
# preserved across regen even though they're not in CURATED_FIELDS.
# Stripped from the output entry (private to the merge logic;
# survives across regen because the merge writes it back).
_CURATION_HOLDS_KEY = "_curation_holds"

# Verifiable measurement fields paired with the boolean flag that
# tracks «is this value source-attested or just inferred?». The
# verified-wins-over-unverified rule below uses this pairing.
#
# Per CLAUDE.md §4, `*_verified: false` (or absent) means the value
# renders with the `(?)` marker — it's a placeholder / canonical-
# anchor / curator-inferred reading, NOT a direct source attestation.
# When two merge candidates disagree on a field's value AND the
# existing one is source-attested (`*_verified: true`) while the
# fresh-regen one is unverified, the existing source-attested value
# wins — fresh's `(?)`-marked value MUST NOT overwrite a sourced one.
_VERIFIABLE_FIELDS = {
    "fineness": "fineness_verified",
    "weight_rough_g": "weight_rough_verified",
    "diameter_mm": "diameter_mm_verified",
    "mint": "mint_verified",
}

# Mints accepted into the Denmark seed. Hede 1971 («Danmarks og
# Norges mønter») by definition only catalogues Danish-Norwegian
# state coinage — every mint listed here is a Danish-royal mint,
# even when located physically in Holstein (Glückstadt, Altona,
# Flensborg, Haderslev, Rendsborg, Rethwitsch were all founded /
# operated by the Danish crown). The Holstein-mint locations stay
# in this set because the COIN'S political attribution is the
# Danish state regardless of where the strike happened — and that's
# what the Denmark page is documenting.
#
# Schleswig-Holstein-LOCAL issuers (Gottorp duchy, Sonderburg duchy,
# Norburg-Plön, Glücksburg, Rantzau county, Schauenburg-Pinneberg)
# are NOT in Hede — they're covered by Lange 1908/1912 and will get
# their own seed pipeline pointed at schleswig_holstein.yml.
#
# Christiansstad is region-ambiguous (Skåne when Danish, post-1658
# Swedish) and is left out to avoid silent mis-attribution.
DK_MINT_DE = {
    # Denmark proper
    "København": "Kopenhagen",
    "K�benhavn": "Kopenhagen",  # mojibake variant seen in some headers
    "Kåbenhavn": "Kopenhagen",  # ditto, alt-decoding
    "Frederiksborg": "Frederiksborg",
    "Helsingør": "Helsingør",
    # Danish-royal mints in the Holstein territories
    "Glückstadt": "Glückstadt",
    "Altona": "Altona",
    "Flensborg": "Flensburg",
    # Haderslev — carved out from the «German for SH mints» convention
    # (user direction 2026-05-22). Rationale: (1) the town has been in
    # Denmark since 1920 and the current Danish-official name is
    # Haderslev; (2) Hede 1971 — our primary Danish-source-of-record
    # — uses «Haderslev» verbatim in page text; (3) majority of our
    # data (Bruun + Numista + Galster + ucoin) already carries
    # «Haderslev» (31 occurrences vs 15 for the German exonym);
    # (4) our mission frame is Danish-Norwegian-realm coinage where
    # Danish names are period-historically appropriate. The other
    # SH-Holstein mints (Flensburg, Glückstadt, Altona, Rendsburg,
    # Rethwisch) stay German per the existing convention — those
    # towns are German today.
    "Haderslev": "Haderslev",
    "Rendsborg": "Rendsburg",
    "Rethwitsch": "Rethwisch",
    # Danish-royal mints in the Norwegian realm (1380–1814).
    # These are recognised as part of the Dansk Mønt corpus per
    # Hede 1971's full title «Danmarks og Norges mønter»; coins
    # struck at these mints carry Norwegian legends but are
    # catalogued in the same registry. The issuing-entity tag is
    # assigned downstream by retag_entities.py.
    "Kongsberg": "Kongsberg",
    "Christiania": "Christiania",
    "Gimsø": "Gimsø",       # Christian III Norge silver mint (pre-1559),
                              # «Gimsø Kloster» on Skien fjord — added 2026-05-17 per §BG
                              # to capture 4 Hede Norge entries (nc3h1-4).
    "Poppenbüttel": "Poppenbüttel",
}


# Split a multi-mint string («København og Kongsberg»,
# «Altona, Kopenhagen, Kongsberg») into individual segments. Hede uses
# Danish/German conjunctions «og» / «und» / «&» / «,» between mints.
_MINT_SEP_RE = re.compile(r"\s+(?:og|und|and|&)\s+|\s*,\s*", re.IGNORECASE)


def _normalize_mints(mint_clean: str) -> list[str] | None:
    """Map a possibly multi-mint raw Hede string to a list of
    canonical mint names. Returns the de-duplicated list in source
    order, or None when no segment matches the DK/SH/NO mint set."""
    parts = _MINT_SEP_RE.split(mint_clean)
    out: list[str] = []
    for part in parts:
        part = part.strip(" (),;.").strip()
        if not part:
            continue
        for canon, normalised in DK_MINT_DE.items():
            if canon.lower() in part.lower():
                if normalised not in out:
                    out.append(normalised)
                break
    return out or None

# Roman numerals 1..10 for ruler-name rendering. Hede pages write
# «Christian 5.» / «Frederik 3.»; downstream YAML uses the standard
# numismatic Roman form.
_ARABIC_TO_ROMAN = {
    1: "I", 2: "II", 3: "III", 4: "IV", 5: "V",
    6: "VI", 7: "VII", 8: "VIII", 9: "IX", 10: "X",
}


# Reign spans for Danish kings — used as a fallback year window when
# Hede publishes an «u. år» (undated) entry that yields no parseable
# year tokens. The seed needs year_first / year_last so the
# `seed_unsorted` phase A cross-ref check passes (1500-1914 window);
# anchoring the coin to its ruler's reign keeps the placeholder
# honest and rolls into the right phase on promotion.
_RULER_REIGN: dict[str, tuple[int, int]] = {
    "c3h": (1534, 1559),  # Christian III.
    "f2h": (1559, 1588),  # Frederik II.
    "c4h": (1588, 1648),  # Christian IV.
    "f3h": (1648, 1670),  # Frederik III.
    "c5h": (1670, 1699),  # Christian V.
    "f4h": (1699, 1730),  # Frederik IV.
    "c6h": (1730, 1746),  # Christian VI.
    "f5h": (1746, 1766),  # Frederik V.
    "c7h": (1766, 1808),  # Christian VII.
    "f6h": (1808, 1839),  # Frederik VI.
    "c8h": (1839, 1848),  # Christian VIII.
    "f7h": (1848, 1863),  # Frederik VII.
    "c9h": (1863, 1906),  # Christian IX.
    "f8h": (1906, 1912),  # Frederik VIII.
    "c10h": (1912, 1947), # Christian X.
    "f9h": (1947, 1972),  # Frederik IX.
}


def _titlecase_nominal(nominal: str) -> str:
    """Capitalise the first letter of each token in the nominal, but
    leave joiners («og», «und») lowercase. Preserves digits, slashes,
    «½», «¼», etc. untouched."""
    if not nominal:
        return nominal
    parts = re.split(r"(\s+)", nominal)  # keep separators
    out = []
    for p in parts:
        if not p or p.isspace():
            out.append(p)
            continue
        lower = p.lower()
        if lower in _NOMINAL_LOWERCASE_WORDS:
            out.append(lower)
            continue
        # Skip pure-digit / fraction tokens
        if re.match(r"^[\d\W]+$", p):
            out.append(p)
            continue
        out.append(p[0].upper() + p[1:])
    return "".join(out)


def _normalise_ruler(raw: str | None) -> str | None:
    if not raw:
        return None
    m = re.match(r"^\s*(Christian|Frederik)\s+(\d{1,2})\.?\s*$", raw)
    if not m:
        return raw.strip()
    name, num = m.group(1), int(m.group(2))
    roman = _ARABIC_TO_ROMAN.get(num)
    return f"{name} {roman}." if roman else raw.strip()


# Gold-marker tokens. When a nominal contains any of these and the
# fineness is high (≥ 0.85) we tag the coin gold; otherwise silver.
# «Krone(r)» is ambiguous (Christian IV silver Kronemont vs Christian
# IX/X gold Krone), so the rule layers on the ruler: «Krone(r)» is
# gold only for Christian IX / Christian X / Frederik VIII / Frederik IX.
#
# Renaissance gold tokens — Hede's pre-1591 catalogue records
# Christian III / Frederik II / early Christian IV gold via period
# names: «Ungersk Gylden» (Hungarian ducat-pattern), «Rhinsk
# Gylden» (Rhenish florin), «Goldgulden», «Portugaløser» (10-
# Dukat presentation piece), «Rosenobel» (English-pattern rose
# noble), «Guldmønt» (literally «gold-coin» when the type lacks a
# proper denomination). All gold; specimens commonly run 3-35 g at
# .75-.986 fineness.
#
# Sølvgylden («silver-gylden») is a specific Christian III tariff
# coin in SILVER at ~29 g and ~.89 fineness — the «sølv» prefix
# overrides the Gylden gold-marker.
_GOLD_NOMINAL_TOKENS = (
    "Dukat", "dukat", "Pistole", "pistole",
    "d'or", "Frederik d'or", "Christian d'or",
    "Guldkrone", "Guldcrone", "Guldmønt", "Guldmoent",
    "Kurantdukat", "Speciedukat",
    "Ungersk Gylden", "Rhinsk Gylden", "Goldgulden",
    "Portugaløser", "Portugaloser",
    "Rosenobel",
)
_KRONE_GOLD_RULERS = {"Christian IX.", "Christian X.", "Frederik VIII.", "Frederik IX."}


def _infer_metal(nominal: str, ruler: str | None, fineness: float | None) -> str:
    n = (nominal or "").lower()
    # «Sølvgylden» (Christian III's silver tariff piece) precedes the
    # «Gylden» gold-marker check — explicit silver override.
    if "sølvgylden" in n or "soelvgylden" in n:
        return "silver"
    if any(tok.lower() in n for tok in _GOLD_NOMINAL_TOKENS):
        return "gold"
    # Krone-fod (post-1873) has TIERED metal — gold only for 5/10/20
    # Kroner (Hauptkurant), silver Kurant for 1/2 Kroner. The earlier
    # «any «krone» + Krone-fod ruler → gold» rule mis-routed 2-Kroner
    # silver commemoratives (Christian IX 1888 jubilee, Christian X
    # 1912 tronskifte, etc.) to gold. Gate gold-routing on the
    # specific gold-tier denominations.
    if re.search(r"\bkrone(r)?\b", n) and ruler in _KRONE_GOLD_RULERS:
        if re.match(r"^(5|10|20)\s+kroner?\b", n):
            return "gold"
        # «1 Krone» / «2 Kroner» → silver Kurant tier of Krone-fod
        return "silver"
    # øre denominations — Krone-fod subsidiary tiers:
    #   25 / 10 øre = silver Scheide (.600 / .400)
    #   5 / 2 / 1 øre = bronze
    if re.search(r"\bø?re\b", n):
        m = re.match(r"^(\d+)\s+ø?re\b", n)
        if m and int(m.group(1)) in (1, 2, 5):
            return "copper"
        return "silver"
    # Speciedaler / daler / rd / rigsdaler / rigsbankdaler / mark /
    # skilling / hvid — all silver or billon. Fineness gates
    # billon below.
    if fineness is not None:
        if fineness < 0.30:
            return "billon"
    return "silver"


# danskmoent.dk deep pages state the COIN'S OWN metal as a literal Danish
# word in exactly two structural slots: the planchet-material phrase
# («Firkantet blanket, guld») or a bare spec-block line («Kobber» on its
# own line, right above «Vægt:»). That word is the SOURCE-OF-RECORD for
# the metal class and must override the nominal-token heuristic, which
# can't tell a 0,833 gold daler (Christian IV's firkantede gulddalere,
# Hede 10-13) from a 0,833 silver piece, nor an 11,7 g copper Sechsling
# (Hede 46/47, struck for Schleswig-Holstein) from silver. Both were
# defaulted to «silver» with metal_verified=True — a §0b over-claim
# corrected here by reading the page's own word.
#
# CRITICAL — scan ONLY those two structural slots, never free prose.
# A page's body prose routinely names a SECONDARY metal that belongs to
# an off-strike / pattern, NOT to the coin:
#   • «Eksemplarer i sølv … betragtes af Hede som afslag» — Sølvafslag of
#     a GOLD Dukat (f4h2-5); the coin is gold, the silver pieces are
#     §9.3 off-strikes we filter out.
#   • «2 ensidige prøveafslag i tin» — tin Tinafslag pattern of a SILVER
#     Speciedaler (c8h3a-f); the coin is silver, not tin.
# A whole-text scan flips these the wrong way. The planchet-phrase +
# bare-line restriction matches the coin's own physical description and
# structurally excludes off-strike / comparative / bibliographic prose.
# (Audit 2026-06-09: the 5 metal over-merge flags + 0 regressions.)
_METAL_TEXT_MAP = {
    "guld": "gold", "sølv": "silver", "soelv": "silver",
    "kobber": "copper", "bronze": "bronze",
    "billon": "billon",
}
# «bronze» is a distinct schema metal class (Literal in schema.py — 259
# uses), NOT collapsed to copper: danskmoent.dk distinguishes «Kobber»
# (copper — Frederik VI / Christian VIII Rigsbankskilling) from «Bronze»
# (the 1856+ Rigsmønt-reform small coinage, Hede c9h6/7, f7h16/17).
# Cross-source matching treats bronze≡copper as one base-metal tier
# (see merge_seeds_cross_source._normalise_metal) so the stored precise
# value never blocks a merge with a coarser «copper» museum tag.
# «tin» is intentionally absent — it is not a valid schema metal and the
# only tin mentions in scope are Tinafslag off-strikes (prose, excluded).
_METAL_WORD = r"(guld|sølv|soelv|kobber|billon|bronze)"
# The metal must appear as the LEADING token of the coin's physical-
# description line — three structural shapes danskmoent.dk uses, all
# stating the coin's OWN metal. Free-prose mentions (off-strikes,
# forgeries, comparisons, companion denominations) are mid-sentence and
# never match these, so they're structurally excluded.
#
# Slot 1 — planchet phrase: «… blanket, guld» / «(Unii) Klipping, guld».
_METAL_PLANCHET_RE = re.compile(
    r"\b(?:blanket|klipping\w*|planchet)\s*,\s*" + _METAL_WORD + r"\b",
    re.IGNORECASE,
)
# Slot 2 — leading spec line: metal word opens the line (after an optional
# «YYYY,» / «YYYYa,» date prefix) and is immediately closed by «.» or «,»:
#   «Kobber. Vægt 14,616g» · «Kobber. Forside …» · «1842, Kobber. Forside»
# The trailing «[.,]» requirement rejects prose openers like «Sølv blev
# brugt …» (metal followed by a space+word, not punctuation).
_METAL_LEAD_RE = re.compile(
    r"^\s*(?:\d{4}[a-z]?\s*,\s*)?" + _METAL_WORD + r"\s*[.,]",
    re.IGNORECASE | re.MULTILINE,
)
# Slot 3 — bare spec line: the metal word alone on its own line
# (danskmoent.dk renders «<LI>Kobber» → a standalone «Kobber» line).
_METAL_BARE_LINE_RE = re.compile(
    r"^\s*" + _METAL_WORD + r"\s*$", re.IGNORECASE | re.MULTILINE
)


def _metal_from_text(parsed: dict) -> str | None:
    """Return the metal class the danskmoent.dk page states for the COIN
    ITSELF — from the planchet phrase, a leading spec line, or a bare
    spec line — or None when no slot is present (or slots disagree).

    Deliberately ignores free prose so a secondary metal belonging to an
    off-strike («Sølvafslag», «prøveafslag i tin»), a contemporary forgery
    («forfalskning af kobber»), a companion denomination («20 kroner af
    guld») or an «also exists in gold» note («Findes også i guld») cannot
    masquerade as the coin's own metal. Stops at «Litteratur:» so
    bibliographic titles («Guldudmøntningen i Haderslev») are out of
    range. «Sølvafslag»/«Guldafslag» are single tokens — the \\b after the
    metal word means they never match either."""
    raw = parsed.get("raw_text") or ""
    if not raw:
        return None
    body = re.split(r"Litteratur:", raw, maxsplit=1)[0]
    hits = set()
    for rx in (_METAL_PLANCHET_RE, _METAL_LEAD_RE, _METAL_BARE_LINE_RE):
        for m in rx.finditer(body):
            hits.add(_METAL_TEXT_MAP[m.group(1).lower()])
    if len(hits) == 1:
        return next(iter(hits))
    return None  # silent, or slots disagree → defer to heuristic


_ZINC_RE = re.compile(r"(?:^|[.;,]\s*)Zink\b", re.IGNORECASE | re.MULTILINE)


def _page_is_zinc(parsed: dict) -> bool:
    """True when the danskmoent.dk page states the coin's composition is
    zinc («Zink»). Danish zinc circulation coins are all 20th-c (interwar
    aluminium-bronze era / 1941-45 WWII-occupation small change) — past
    the 1914 mission bound — and «zinc» is not a schema metal. A dateless
    zinc page (e.g. Hede c10h35, defaulted to the 1912-1947 Christian-X
    reign window so the year-cap can't catch it) is therefore dropped from
    the seed; the raw harvest cache keeps it. Restricted to the spec body
    (pre-«Litteratur:») so a bibliographic title can't trip the match."""
    raw = parsed.get("raw_text") or ""
    if not raw:
        return False
    body = re.split(r"Litteratur:", raw, maxsplit=1)[0]
    return bool(_ZINC_RE.search(body))


def _infer_kind(metal: str, nominal: str, ruler: str | None, fineness: float | None) -> str:
    """Default = kurant. Lower-tier silver / billon Skilling drops to
    scheide. Christian IV Krone (Kronemont, 1618-1645) is tarif."""
    n = (nominal or "").lower()
    if ruler == "Christian IV." and re.search(r"\bkrone\b", n):
        return "tarif"
    if metal == "billon":
        return "scheide"
    if metal == "silver" and fineness is not None and fineness < 0.55:
        return "scheide"
    return "kurant"


# Splits «1, 2, 3 og 4 Speciedaler» / «1 og 2 Dukat» / «1/2, 1 og 2
# Dukat» / «1, 2, 5, 10 Dukat» (no «og») into per-sub-Hede nominals.
# Returns a list of full denomination strings (e.g. ["1 Speciedaler",
# "2 Speciedaler", "3 Speciedaler", "4 Speciedaler"]).
#
# Two patterns supported in the numeric prefix:
#   - Comma/space/slash-separated list ending in «og N»
#     («1, 2, 3 og 4 Speciedaler» — Hede's standard list format)
#   - Plain comma-separated list without «og»
#     («1, 2, 5, 10 Dukat» — used on f3h10)
# Each number element may be a bare integer OR a fraction («1/2»).
_NUM_TOKEN = r"\d+(?:/\d+)?"
_NOMINAL_LIST_RE = re.compile(
    r"^\s*("                                 # group 1: numbers section
    r"" + _NUM_TOKEN + r"(?:[\s,/]+" + _NUM_TOKEN + r")*(?:\s+og\s+" + _NUM_TOKEN + r")?"
    r")\s+"
    r"([A-Za-zæøåÆØÅ\.\- ]+?)(?:,.*)?$"        # group 2: denomination
)


def _split_multi_nominal(nominal: str, count_expected: int) -> list[str] | None:
    """Return per-sub-Hede nominals when nominal is a comma-list.
    Returns None when the parse doesn't match `count_expected`.

    Handles fraction multipliers (e.g. «1/2 Dukat») by capturing each
    number token in `_NUM_TOKEN` form.

    Special case: when nominal is a SINGLE denomination (just «1 Skilling»,
    no «og» / multi-list) but count_expected > 1, treats the by_hede
    entries as sub-letter variants of the same denomination and emits
    the same nominal for each. This covers pages like c3h6 («1 Skilling»
    with Hede 6A + 6B sub-letters)."""
    if not nominal:
        return None
    m = _NOMINAL_LIST_RE.match(nominal.strip())
    if not m:
        return None
    numbers_part = m.group(1)
    denom = m.group(2).strip()
    # Strip a trailing «, København» / similar embedded into denom.
    denom = re.split(r",\s*", denom, maxsplit=1)[0].strip()
    nums = re.findall(_NUM_TOKEN, numbers_part)
    # Same-denomination sub-letter case: single multiplier, multiple
    # by_hede entries — replicate the nominal for each.
    if len(nums) == 1 and count_expected > 1:
        return [f"{nums[0]} {denom}"] * count_expected
    if len(nums) != count_expected:
        return None
    return [f"{n} {denom}" for n in nums]


def _build_year_fields(years: list[dict]) -> dict:
    if not years:
        return {}
    yrs = sorted({int(y["year"]) for y in years})
    if not yrs:
        return {}
    year_first = yrs[0]
    year_last = yrs[-1]
    # Group consecutive years into ranges
    ranges: list[list[int]] = []
    start = yrs[0]
    prev = yrs[0]
    for y in yrs[1:]:
        if y == prev + 1:
            prev = y
            continue
        ranges.append([start, prev])
        start = y
        prev = y
    ranges.append([start, prev])
    # Label: comma-list of ranges
    label_parts = [
        str(a) if a == b else f"{a}–{b}"
        for a, b in ranges
    ]
    year_label = ", ".join(label_parts)
    out: dict = {
        "year_label": year_label,
        "year_first": year_first,
    }
    if year_last != year_first:
        out["year_last"] = year_last
    if len(yrs) > 1:
        # A Hede sub-variant's year list is ALWAYS a discrete enumeration
        # of individually-struck years (comma-separated in the source),
        # never a continuous-mintage span. Emit ONE singleton [y, y] per
        # attested year so the cross-source merger's `_union_year_ranges`
        # classifier treats them as DISCRETE attestations. A consecutive
        # run collapsed to a single multi-year range [[lo, hi]] would be
        # mis-read as a LOOSE span and could be displaced by a wider
        # discrete envelope, silently dropping an interior year (the
        # c7h13C «1798» case: «1798, 1799» displaced by the cluster's
        # [1795, 1801] envelope, 1798 lost). Render-time
        # `_format_year_label` folds the singletons back into «1798-1799»
        # for display, so storage stays honest while the label stays
        # compact. (`ranges` above remains gap-grouped for the label only.)
        out["year_ranges"] = [[y, y] for y in yrs]
    return out


_DANSKMOENT_BASE = "https://www.danskmoent.dk"


def _danskmoent_url(basename: str) -> str:
    """Reconstruct the per-coin URL from a cache basename.

    Path conventions on danskmoent.dk:
      • `/c{N}hede.htm` / `/f{N}hede.htm` — Hede-overview index (ROOT
                                 level, NOT under /chr or /fr).
                                 Empirically verified 2026-05-22:
                                 `/chr/c3hede.htm` → 404,
                                 `/c3hede.htm` → 200.
      • `/chr/c{N}h{num}.htm`   — Christian N main-realm deep page
      • `/fr/f{N}h{num}.htm`    — Frederik N main-realm deep page
      • `/norge/nc{N}h{num}.htm`, `/norge/nf{N}h{num}.htm`
                                 — Norge sub-catalogue (personal-union
                                   Norwegian volume of the same monarch's
                                   reign); leading `n` marker
    Fallback to bare root path for any unmatched basename (manifest
    contains a few entries like `f4hkr5.htm` that don't fit the
    standard volume pattern).
    """
    # Hede-overview index pages live at the site root, not in
    # /chr or /fr subdirectories. Match BEFORE the volume-prefix
    # routing below.
    if re.match(r"^n?[cf]\d+hede$", basename):
        return f"{_DANSKMOENT_BASE}/{basename}.htm"
    if basename.startswith(("nc", "nf")):
        return f"{_DANSKMOENT_BASE}/norge/{basename}.htm"
    if basename.startswith("c"):
        return f"{_DANSKMOENT_BASE}/chr/{basename}.htm"
    if basename.startswith("f"):
        return f"{_DANSKMOENT_BASE}/fr/{basename}.htm"
    return f"{_DANSKMOENT_BASE}/{basename}.htm"


def _build_coin(
    *,
    hede_volume: str,
    hede_number: str,
    parsed: dict,
    spec: dict,
    nominal_override: str | None = None,
    mint_normalised: str | list[str],
    years_override: list[dict] | None = None,
    catalog_refs_override: dict | None = None,
) -> dict | None:
    """Assemble one Coin-schema dict from a parsed-page entry + a
    specific spec block. Returns None when essential fields are
    missing or unrecoverable (e.g. nominal parse failure).

    Per-letter sub-variants (by_letter pages) pass `years_override` +
    `catalog_refs_override` so each letter coin carries its own year
    list + Hede/Sieg sub-numbers while sharing the page-level spec.
    """
    nominal_raw = nominal_override or parsed.get("nominal") or ""
    # Strip trailing «, København» / «, Glückstadt» / «, Frederiksborg»
    # mint segments that the H1 parser absorbed into nominal.
    nominal = re.split(r",\s*[A-ZÆØÅa-zæøå]", nominal_raw, maxsplit=1)[0].strip()
    nominal = re.sub(r"\s+", " ", nominal).strip(" ,.")
    if not nominal or len(nominal) < 3:
        return None
    nominal = _titlecase_nominal(nominal)
    ruler = _normalise_ruler(parsed.get("ruler"))
    fineness = spec.get("finhed") if spec else None
    brutto = spec.get("bruttovægt_g") if spec else None
    # Index-stub coins (parse_hede.py emits these for deep-page-absent
    # Hede rows) carry an authoritative metal token from the overview
    # table's metal column. Trust that over the nominal-token heuristic
    # — Hede's own table is the source-of-record for «Guld / Sølv /
    # Kobber / Bronze». For real deep-page parses (no
    # `metal_from_index`), fall through to the heuristic.
    is_index_stub = parsed.get("_source_type") == "index_stub"
    metal_from_index = parsed.get("metal_from_index") if is_index_stub else None
    metal_from_text = _metal_from_text(parsed) if not is_index_stub else None
    if metal_from_index:
        metal = metal_from_index
    elif metal_from_text:
        metal = metal_from_text
    else:
        metal = _infer_metal(nominal, ruler, fineness)
    # Billon downgrade — applies whatever the «silver» reading's origin.
    # danskmoent.dk labels any silver-alloy piece «sølv» loosely (e.g.
    # f6h7 «1 Skilling, Altona, sølv» at finhed 0,138); the fineness is
    # the precise discriminator and below the billon threshold the coin
    # is billon, not silver. Gold/copper/tin readings are unaffected —
    # only «silver» is subject to the fineness check.
    if metal == "silver" and fineness is not None and fineness < 0.30:
        metal = "billon"
    kind = _infer_kind(metal, nominal, ruler, fineness)
    coin_id = f"dk-hede-{hede_volume}{hede_number.lower()}"

    cm = CommentedMap()
    cm["id"] = coin_id
    cm["fuss"] = "seed_unsorted"
    # Source-specific phase under seed_unsorted so the Hede-derived
    # rows render in their own sub-section on the location page,
    # cleanly separated from the older ucoin bulk block (phase=A).
    # Both phases live inside seed_unsorted (the catch-all bucket
    # awaiting Müntzfuß reclassification); the separation is
    # cosmetic-but-honest about provenance, not analytical.
    cm["phase"] = "hede"
    cm["kind"] = kind
    cm["nominal"] = nominal
    year_block = _build_year_fields(years_override or parsed.get("years") or [])
    if year_block:
        cm["year_label"] = year_block["year_label"]
        cm["year_first"] = year_block["year_first"]
        if "year_last" in year_block:
            cm["year_last"] = year_block["year_last"]
        if "year_ranges" in year_block:
            yr_seq = CommentedSeq()
            for pair in year_block["year_ranges"]:
                inner = CommentedSeq(pair)
                inner.fa.set_flow_style()
                yr_seq.append(inner)
            cm["year_ranges"] = yr_seq
    else:
        # Undated Hede entry («u. år» — uden årstal). Anchor to the
        # ruler's reign window so the placeholder year_first sits
        # inside seed_unsorted/A's [1500, 1914] cross-ref window AND
        # is at least *plausible* for promotion. Per CLAUDE.md §3a
        # year_label MUST be plain decimal years/range — no «u. å.»
        # prefix, no «ND», no «ca.». Year-level uncertainty is
        # surfaced via `year_verified: false`, which the renderer
        # turns into a `(?)` span next to the year column.
        reign = _RULER_REIGN.get(hede_volume)
        if reign:
            cm["year_label"] = f"{reign[0]}-{reign[1]}"
            cm["year_first"] = reign[0]
            cm["year_last"] = reign[1]
        else:
            # Last-resort: no reign data → reign-window unknown.
            # Use the lowest plausible anchor (1500) as year_first
            # and leave year_label as a single year placeholder; the
            # `(?)` marker on year_verified=false signals the gap.
            cm["year_label"] = "1500"
            cm["year_first"] = 1500
        cm["year_verified"] = False
    if ruler:
        cm["ruler"] = ruler
    if isinstance(mint_normalised, list):
        seq = CommentedSeq(mint_normalised)
        seq.fa.set_flow_style()
        cm["mint"] = seq
    else:
        cm["mint"] = mint_normalised

    catalog = CommentedMap()
    catalog["hede"] = hede_number
    catalog["hede_volume"] = hede_volume
    refs = catalog_refs_override or parsed.get("catalog_refs") or {}
    # GENERIC catalogue mapping (§CJ): Schou/Sieg/Fr/Dav/Km/Galster/Bruun →
    # typed; any other code the parser surfaces → `others` (never dropped).
    # `Hede` is set above from hede_number (authoritative); the `Frederik` key
    # is a known parser false-positive (king name «Frederik 2.» mis-matched as
    # a catalogue, fixed in parse_hede.py 2026-05-25; the old `Frederik → fr`
    # mapping was anyway semantically wrong — Friedberg is a gold-coin global
    # catalogue, not a ruler-attribution). Both are dropped here.
    _HEDE_REF_MAP = {
        "Schou": "schou", "Sieg": "sieg", "Fr": "fr", "Dav": "dav",
        "Km": "km", "Galster": "galster", "Bruun": "bruun_collection_id",
    }
    mapped = catalog_from_ref_dict(
        refs, _HEDE_REF_MAP, drop_keys={"Hede", "Frederik"}
    )
    for field, value in mapped.items():
        if field == "others":
            bucket = catalog.setdefault("others", [])
            for tok in value:
                if tok not in bucket:
                    bucket.append(tok)
        else:
            catalog[field] = value
    cm["catalog"] = catalog

    cm["metal"] = metal
    if fineness is not None:
        cm["fineness"] = fineness
    if brutto is not None:
        cm["weight_rough_g"] = brutto

    # Müntzfuß yield («Marken fin udbragt til N speciedaler/rd.kr/...»)
    # — per-Hede attested ratio of fine-silver Mark to N units of the
    # era's accounting denomination. Authoritative input for the §8a
    # auto-classifier: each canonical Müntzfuß in `data/shared/fuesse.yml`
    # has an identifying N-per-Mark-fein ratio (9¼ → 9.25 speciedaler,
    # 11⅓ → 11.333 rigsdaler-kurant, 18½ → 18.5 rigsbankdaler, etc.).
    # When this field is present, classification is direct lookup; when
    # absent, fallback to fineness/weight-Δ math against fuss Soll.
    yld = spec.get("marken_fin_udbragt_til") if spec else None
    if yld and yld.get("value") is not None and yld.get("unit"):
        ym = CommentedMap()
        ym["value"] = yld["value"]
        ym["unit"] = yld["unit"]
        if yld.get("basis"):
            ym["basis"] = yld["basis"]
        if yld.get("unit_raw") and yld.get("unit_raw") != yld.get("unit"):
            ym["unit_raw"] = yld["unit_raw"]
        cm["hede_muentzfuss_yield"] = ym

    # Per CLAUDE.md §4: a value directly attested by an acceptable
    # source is sufficient to flip its `*_verified` flag. Hede 1971
    # publishes `finhed` and `bruttovægt_g` per page; both are
    # source-attested. The overall `verified` flag stays false (it
    # signals «full per-coin sanity check done», not «any source
    # confirms any field»). `mint_verified` also stays false here —
    # mint extraction is parser-heuristic and can drift.

    sources = CommentedSeq()
    src = CommentedMap()
    src["type"] = "literature"
    if is_index_stub:
        # Index stub — deep page doesn't exist on danskmoent.dk; the
        # citation must point at the overview catalogue page that
        # actually attests this row. `_source_index` carries the
        # basename of that overview file (e.g. «c3hede.htm»).
        overview_basename = (parsed.get("_source_index") or "").replace(".htm", "")
        if overview_basename:
            src["url"] = _danskmoent_url(overview_basename)
        else:
            src["url"] = _danskmoent_url(parsed["id"])
        src["ref"] = (
            f"danskmoent.dk overview {overview_basename} "
            f"(Hede {hede_volume}{hede_number} — Tiefenseite fehlt)"
        )
    else:
        src["url"] = _danskmoent_url(parsed["id"])
        # Domain-first label per CONVENTIONS.md §«Source-ref label shape»:
        # the domain (the actual link target) leads, the catalog basename
        # follows in parens as sub-resource disambiguator. Reads as «which
        # domain → which page on it», the natural navigation order.
        src["ref"] = f"danskmoent.dk (Hede {hede_volume}{hede_number})"
    sources.append(src)
    cm["sources"] = sources

    # V2-native entity classification: mint-driven first
    # (royal_holstein for Altona/Glückstadt, danish_norway for
    # Kongsberg/Christiania, gottorp_duchy for Rendsborg etc.),
    # volume-prefix fallback for Norge sub-pages (`nc*h` / `nf*h`).
    cm["issuing_entity"] = _classify_hede_entity(
        mint_normalised, hede_volume
    )
    cm["verified"] = False
    if fineness is not None:
        cm["fineness_verified"] = True   # Hede page directly publishes
    if brutto is not None:
        cm["weight_rough_verified"] = True   # Hede page directly publishes
    # metal_verified: when Hede publishes fineness or weight on the page,
    # the metal is IMPLICITLY attested by the same source (a .985 reading
    # on a Dukat page is the source telling us the coin is gold; a .875
    # on a Speciedaler is the source telling us silver). Flip the flag
    # whenever either measurement is source-attested. This avoids
    # rendering «Silber (?)» / «Gold (?)» on Hede-only coins whose
    # fineness column already shows a source-cited value (user-reported
    # 2026-05-20 on KM-340 c5h2 Christian V Dukat .979/.980).
    #
    # For index-stub coins, the overview table's metal column is the
    # source-of-record — flip metal_verified even though
    # fineness/weight stay null.
    if fineness is not None or brutto is not None or metal_from_index or metal_from_text:
        cm["metal_verified"] = True
    cm["mint_verified"] = False  # parser-heuristic; not flipped here
    vn = CommentedMap()
    if is_index_stub:
        # Index-stub: danskmoent.dk overview-table attestation only;
        # deep page absent. Weight + fineness unknown; nominal, metal,
        # year, mint and Sieg-ref carry over from the index row. Full
        # per-specimen verification depends on the §AZ paper-source
        # import (Hede 1971 physical book + Galster 1965).
        index_note = parsed.get("index_note") or ""
        idx_basename = parsed.get("_source_index", "danskmoent.dk overview")
        vn["de"] = (
            f"Hede-Index-Stub: Nur die Übersichtsreihe von {idx_basename} "
            f"belegt diesen Eintrag (Hede-Tiefenseite fehlt auf "
            f"danskmoent.dk). Gewicht und Probe nicht erfasst; "
            f"vollständige Per-Münze-Verifikation hängt am §AZ Paper-Source-"
            f"Import (Hede 1971 + Galster 1965)."
            + (f" Anmerkung im Index: «{index_note}»" if index_note else "")
        )
        vn["en"] = (
            f"Hede index stub: only the overview-table row of {idx_basename} "
            f"attests this entry (Hede deep page absent from "
            f"danskmoent.dk). Weight and fineness not captured; full "
            f"per-coin verification depends on the §AZ paper-source import "
            f"(Hede 1971 + Galster 1965)."
            + (f" Index note: «{index_note}»" if index_note else "")
        )
        vn["uk"] = (
            f"Hede index-stub: тільки рядок огляду {idx_basename} "
            f"підтверджує цей запис (deep-сторінка Hede відсутня на "
            f"danskmoent.dk). Вага та проба не зафіксовані; повна "
            f"покоінна верифікація залежить від §AZ paper-source імпорту "
            f"(Hede 1971 + Galster 1965)."
            + (f" Коментар з індексу: «{index_note}»" if index_note else "")
        )
    else:
        vn["de"] = (
            "Hede-Seed: Müntzfuß-Zuordnung, Phase und Per-Münze-Verifikation "
            "stehen noch aus; Daten direkt aus danskmoent.dk übernommen."
        )
        vn["en"] = (
            "Hede seed: Müntzfuß assignment, phase and per-coin verification "
            "are still outstanding; data lifted directly from danskmoent.dk."
        )
        vn["uk"] = (
            "Hede-seed: призначення Müntzfuß, фази та покоінна верифікація "
            "ще очікуються; дані взято безпосередньо з danskmoent.dk."
        )
    cm["verification_note"] = vn
    # _source_note candidate (Phase-1, commit 80a1b62): danskmoent's coin
    # `description` (Danish), cleaned + language-tagged for the later note-
    # selector. Non-schema (underscore) → stripped before the strict Coin schema
    # at final/render. Wiring here (the deferred follow-up) makes a re-seed
    # reproduce it durably instead of dropping the one-off population.
    _sn = source_note(parsed.get("description"), "da")
    if _sn:
        cm["_source_note"] = _sn
    return cm


def _load_existing_seed() -> tuple[CommentedMap | None, dict[str, CommentedMap]]:
    """Load the on-disk seed (if present) and index its coins by id.

    Returns (root_doc, coins_by_id). Root_doc is None when no seed
    exists yet (fresh project / first run). Coins_by_id is a dict
    keyed by `coin.id` whose values are the ruamel CommentedMap
    instances, preserving comments and key order for the entries
    we'll carry through unchanged.
    """
    if not OUT_FILE.exists():
        return None, {}
    yaml = YAML(typ="rt")
    yaml.preserve_quotes = True
    doc = yaml.load(OUT_FILE.read_text(encoding="utf-8"))
    if doc is None or "coins" not in doc:
        return None, {}
    by_id: dict[str, CommentedMap] = {}
    for c in doc["coins"]:
        cid = c.get("id")
        if cid:
            by_id[cid] = c
    return doc, by_id


def _merge_one(existing: CommentedMap, fresh: CommentedMap) -> CommentedMap:
    """Merge `fresh` (regenerator output) into `existing` (the curated
    on-disk entry), per the rules documented in the module docstring.

    The merge preserves the curated entry's identity (same id, same
    container) and updates source-derived fields from fresh while
    holding curated fields stable.
    """
    holds = set(existing.get(_CURATION_HOLDS_KEY) or [])
    # CURATED_FIELDS are always preserved if present in existing; absence
    # means the field simply hasn't been curated yet, so taking fresh's
    # default value is the right move (typically a sentinel like
    # `seed_unsorted` / `hede`).
    # `_curation_holds` is stronger: it freezes the existing entry's
    # STATE for that field — present-value stays, absence stays absent.
    # Use this for the rare case where curation REMOVED a default field
    # (e.g. f7h3 drops verification_note after manual verification) or
    # REPLACED a parser-output (e.g. c4h52 cleans `2 Speciedaler 1603`
    # to `2 Speciedaler`).
    fresh_keys = set(fresh.keys())
    existing_keys = set(existing.keys())

    for key in fresh_keys:
        if key == _CURATION_HOLDS_KEY:
            continue  # never flows from fresh; survives via existing
        if key in holds:
            # Frozen field: existing state wins (present-or-absent).
            # When the field is absent from existing, we explicitly do
            # NOT inherit it from fresh — the curator removed it on
            # purpose.
            continue
        if key in CURATED_FIELDS:
            # Soft-curated field: existing wins if present, otherwise
            # inherit the fresh default (which signals "needs curation"
            # via the seed_unsorted/hede sentinels).
            if key in existing_keys:
                continue
            existing[key] = fresh[key]
            continue
        if key in DEEP_MERGE_FIELDS:
            # Deep-merge dict: existing keys win, fresh keys fill gaps.
            ex_v = existing.get(key)
            fr_v = fresh.get(key)
            if isinstance(ex_v, dict) and isinstance(fr_v, dict):
                for sub_k, sub_v in fr_v.items():
                    if sub_k not in ex_v:
                        ex_v[sub_k] = sub_v
            elif ex_v is None and fr_v is not None:
                existing[key] = fr_v
            continue
        if key in _VERIFIABLE_FIELDS:
            # Verified-wins-over-unverified rule (per CLAUDE.md §4):
            # when both candidates have a value for a measurement
            # field (fineness / weight / diameter / mint), and the
            # EXISTING side is source-attested (`*_verified: true`)
            # while FRESH is unverified (`(?)` marker — absent flag
            # or false), keep the source-attested existing value. The
            # fresh regen's inferred / canonical-anchor reading must
            # NOT overwrite a curated, source-cited one.
            verified_flag = _VERIFIABLE_FIELDS[key]
            existing_verified = bool(existing.get(verified_flag))
            fresh_verified = bool(fresh.get(verified_flag))
            if (
                key in existing_keys
                and existing_verified
                and not fresh_verified
            ):
                continue
        # Default: fresh wins.
        existing[key] = fresh[key]

    # Drop existing-only keys ONLY if they're neither curated nor in
    # the per-entry holds set. (E.g. if the fresh output stopped
    # emitting some field that wasn't curated, the regen should also
    # drop it from the merged entry — keeps the seed honest about
    # what the parser currently produces.)
    drop_candidates = existing_keys - fresh_keys
    for key in drop_candidates:
        if key == _CURATION_HOLDS_KEY:
            continue
        if key in CURATED_FIELDS or key in holds:
            continue
        del existing[key]

    return existing


def _merge_seed(coins_fresh: list[CommentedMap]) -> tuple[
    list[CommentedMap], dict[str, int]
]:
    """Merge freshly-generated coins against the existing on-disk
    seed. Returns (merged_coins, merge_stats).

    Merge stats keys:
      merged_existing — count of existing entries we merged fresh into
      added_new       — count of fresh entries with no existing match
      orphan_curated  — count of existing entries with no fresh match
                        (curation may have shipped an entry the parser
                        can't currently produce; we keep them and warn)
    """
    _, existing_by_id = _load_existing_seed()
    fresh_by_id: dict[str, CommentedMap] = {c["id"]: c for c in coins_fresh}

    stats = {"merged_existing": 0, "added_new": 0, "orphan_curated": 0}
    out: list[CommentedMap] = []

    # 1. For every fresh entry, either merge into existing or keep as-is.
    for cid, fresh in fresh_by_id.items():
        if cid in existing_by_id:
            merged = _merge_one(existing_by_id[cid], fresh)
            out.append(merged)
            stats["merged_existing"] += 1
        else:
            out.append(fresh)
            stats["added_new"] += 1

    # 2. Orphan curated entries — present in existing but not fresh.
    #    Keep them verbatim; the user may have curated an entry the
    #    parser doesn't currently produce, and silent drop would be a
    #    data-loss event.
    orphan_ids = set(existing_by_id) - set(fresh_by_id)
    for cid in sorted(orphan_ids):
        out.append(existing_by_id[cid])
        stats["orphan_curated"] += 1

    return out, stats


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--year-to", type=int, default=1914,
        help=(
            "Drop entries whose year_first is after this year (inclusive). "
            "Default 1914 — the project's scope upper bound per CLAUDE.md. "
            "Set higher to include modern issues (post-Reichsgoldmünzfuß-era)."
        ),
    )
    ap.add_argument(
        "--year-from", type=int, default=1514,
        help=(
            "Drop entries whose year_first is before this year. Default 1514 "
            "— Christian II Lovkompleks anchor (the four-act legal package per "
            "Wilcke 1950 p. 183-186 verbatim: Møntordning af Sommeren 1514 in "
            "Malmø (Dienis Malmö mintmaster Brev, both metals: Nobler 23½ "
            "Karat 16/Mark + Rhinsk Gylden 18 Karat 72/Mark) + Møntordning af "
            "3. August 1514 for Norge + Kvittering Paasketid 1515 + Sjælland "
            "åbent Brev af 24. August 1515). First comprehensive Danish-Norwegian "
            "legal act for both metals + both kingdoms. Project lower bound for "
            "Denmark-Norway per CLAUDE.md mission statement (German-lands track "
            "uses 1559 Augsburger Reichsmüntzordnung anchor instead — dual-"
            "jurisdiction anchor model). Note: Hede 1957 itself starts at "
            "Christian III (1534+) and does NOT catalogue pre-Christian-III "
            "rulers — the 1514-1540 sub-window will be empty until a "
            "separate Galster + Jensen-Skjoldager catalog import lands "
            "(sibling TODO §BJ). NOT a Hede extension."
        ),
    )
    ap.add_argument(
        "--no-merge", action="store_true",
        help=(
            "Skip the curation-preserving merge against the existing "
            "on-disk seed and overwrite wholesale with fresh output. "
            "Destructive — only use for verification / dry-run paths "
            "where you also pass a non-default output location. The "
            "default behaviour merges (preserves curated fields, adds "
            "new entries, keeps orphaned curated entries)."
        ),
    )
    args = ap.parse_args()
    year_to = args.year_to
    year_from = args.year_from
    merge = not args.no_merge

    parsed_files = sorted(p for p in HEDE_CACHE.glob("*.json") if not p.name.startswith("_"))
    if not parsed_files:
        print(f"No parsed JSON found in {HEDE_CACHE}", file=sys.stderr)
        return 1

    # Load the aggregate canonical-resolution index built by
    # parse_hede.py — composite Hede key («c4h111», «f3h68») →
    # canonical file owning that key. Used to filter out duplicates:
    # «c4h111» and «c4h111note» both describe Hede 111; only the
    # canonical (c4h111) emits a seed entry. Multi-Hede pages like
    # f3h68 only emit their own primary number, not the cross-
    # referenced Hede 61 / 62AB / 63 specs (those belong to f3h62).
    index_path = HEDE_CACHE / "_parsed_index.json"
    if not index_path.exists():
        print(f"Aggregate index missing — run parse_hede.py first", file=sys.stderr)
        return 1
    aggregate_idx = json.loads(index_path.read_text(encoding="utf-8"))
    # file basename → set of Hede sub-numbers that file canonically owns
    canonical_subs: dict[str, set[str]] = {}
    for composite_key, summary in aggregate_idx.items():
        # Extract the sub-Hede portion from composite key
        # «c4h111» → «111», «f3h62ab» → «62ab», «c10h35» → «35»,
        # «nc5h42» → «42» (Norge — same shape, optional `n` prefix).
        m = re.match(r"^n?[cf]\d+h(.+)$", composite_key)
        if not m:
            continue
        sub_num = m.group(1).lower()
        canonical_subs.setdefault(summary["file"], set()).add(sub_num)

    coins: list[CommentedMap] = []
    stats = {
        "considered": 0,
        "kept": 0,
        "skipped_no_mint": 0,
        "skipped_non_dk_mint": 0,
        "skipped_no_specs": 0,
        "skipped_no_nominal": 0,
        "skipped_multi_nominal_unparseable": 0,
        "skipped_out_of_scope_year": 0,
        "skipped_zinc_20c": 0,
        "skipped_non_canonical": 0,
        "skipped_cross_reference_subhede": 0,
        "skipped_proof_pattern": 0,
    }
    skipped_mints: dict[str, int] = {}
    # Seed-ids of zinc pages we skip — passed to write_v2_seed as
    # exclude_ids so a previously-seeded stale entry (e.g. c10h35, whose
    # misparsed metal=copper / placeholder year=1912 evade the generic
    # filters) is purged from the existing seed, not orphan-preserved.
    zinc_drop_ids: set[str] = set()

    for p in parsed_files:
        d = json.loads(p.read_text(encoding="utf-8"))
        stats["considered"] += 1
        # Skip known proof / trial / pattern strikes — CLAUDE.md §9
        # explicitly excludes them from the location coin table.
        if d["id"] in _KNOWN_PROOF_PATTERNS:
            stats["skipped_proof_pattern"] += 1
            continue
        # Skip files that aren't canonical for any Hede number (e.g.
        # c4h111note — a footnote page where c4h111 owns the actual
        # Hede 111 entry).
        owned_subs = canonical_subs.get(d["id"], set())
        if not owned_subs:
            stats["skipped_non_canonical"] += 1
            continue
        raw_mint = (d.get("mint") or "").strip().lstrip("),.;- ").strip()
        # «Ruler, NOMINAL» pages have no top-level mint — it lives per-variant
        # in by_letter[*]["mint"] (parser Part 2). Defer the no-mint skip so the
        # by_letter path below can use the per-letter mint; only the default /
        # by_hede single-mint paths still require a top-level mint.
        by_letter_mints = any(
            lv.get("mint") for lv in (d.get("by_letter") or {}).values()
        )
        mint_normalised: str | list[str] | None = None
        # A denomination-shaped mint («1 Speciedaler») is a stale field-swap
        # artefact (parser Part 1 fixed the source of these) — ignore it.
        if raw_mint and not re.match(r"^\d+\s+[A-Za-zæøå]", raw_mint):
            # Strip leading «NN, » prefix («23, København» → «København»),
            # then trailing punctuation.
            mint_clean = re.sub(r"^\d+\s*,\s*", "", raw_mint).rstrip(".;,)").strip()
            # Match against DK / SH / Norway mint set. Multi-mint Hede strings
            # («København og Kongsberg», «Altona, Kopenhagen, Kongsberg») return
            # a list — preserved so every parallel-strike city renders.
            mints_list = _normalize_mints(mint_clean)
            if mints_list:
                mint_normalised = mints_list[0] if len(mints_list) == 1 else mints_list
            else:
                skipped_mints[mint_clean] = skipped_mints.get(mint_clean, 0) + 1
        if mint_normalised is None and not by_letter_mints:
            stats["skipped_no_mint"] += 1
            continue

        hede_volume = d.get("ruler_volume") or ""
        if not hede_volume:
            continue
        # Zinc composition → 20th-c out-of-scope (past the 1914 bound);
        # dropped here because a dateless zinc page is reign-window-
        # placeholdered to the ruler's reign start, so the year-cap below
        # can't catch it (e.g. c10h35 → 1912).
        if _page_is_zinc(d):
            stats["skipped_zinc_20c"] += 1
            zinc_drop_ids.add(f"dk-hede-{d['id']}")
            continue
        specs = d.get("specs") or {}

        if "default" in specs:
            spec = specs["default"]
            nums = d.get("hede_numbers_filename") or d.get("hede_numbers_title") or []
            if not nums:
                # Derive from id («c5h120» → «120»)
                m = re.match(r"^n?[cf]\d+h(\w+)$", d["id"])
                nums = [m.group(1)] if m else []
            if not nums:
                stats["skipped_no_specs"] += 1
                continue
            hede_number = nums[0]
            # Letter-grouped sub-variants: when the page emits a
            # by_letter block, generate one coin per letter with the
            # SHARED spec but per-letter years + Hede sub-letter +
            # sub-Sieg refs. The bare numeric Hede key (e.g. «16») is
            # NOT emitted in this case — only the letter-suffixed keys
            # («16A», «16B») which carry the actual data.
            by_letter = d.get("by_letter") or {}
            if by_letter:
                for letter, lv in sorted(by_letter.items()):
                    sub_hede = f"{hede_number}{letter}"
                    if sub_hede.lower() not in owned_subs:
                        stats["skipped_cross_reference_subhede"] += 1
                        continue
                    # Per-letter (sub-variant) mint when the parser recovered one
                    # (78A København, 78B Helsingør differ) — falls back to the
                    # top-level mint for ordinary by_letter pages that share one.
                    letter_mint = mint_normalised
                    if lv.get("mint"):
                        lm = _normalize_mints(str(lv["mint"]))
                        if lm:
                            letter_mint = lm[0] if len(lm) == 1 else lm
                    if letter_mint is None:
                        stats["skipped_no_mint"] += 1
                        continue
                    coin = _build_coin(
                        hede_volume=hede_volume,
                        hede_number=sub_hede,
                        parsed=d,
                        spec=spec,
                        mint_normalised=letter_mint,
                        years_override=lv.get("years"),
                        catalog_refs_override=lv.get("catalog_refs"),
                    )
                    if coin is None:
                        stats["skipped_no_nominal"] += 1
                        continue
                    if coin.get("year_first") and (
                        coin["year_first"] > year_to
                        or coin["year_first"] < year_from
                    ):
                        stats["skipped_out_of_scope_year"] += 1
                        continue
                    coins.append(coin)
                    stats["kept"] += 1
                continue
            if hede_number.lower() not in owned_subs:
                stats["skipped_cross_reference_subhede"] += 1
                continue
            coin = _build_coin(
                hede_volume=hede_volume,
                hede_number=hede_number,
                parsed=d,
                spec=spec,
                mint_normalised=mint_normalised,
            )
            if coin is None:
                stats["skipped_no_nominal"] += 1
                continue
            if coin.get("year_first") and (
                coin["year_first"] > year_to
                or coin["year_first"] < year_from
            ):
                stats["skipped_out_of_scope_year"] += 1
                continue
            coins.append(coin)
            stats["kept"] += 1
        elif "by_hede" in specs:
            by_hede = specs["by_hede"]
            # Prefer the parser-emitted per-Hede nominal (one «nominal»
            # field inside each by_hede spec). When ALL entries carry
            # a nominal, we don't need the weight-sort multi-nominal
            # split heuristic — use parser data directly. Falls back to
            # the legacy split logic when nominals are absent (older
            # cached parses or pages without a clear descriptive list).
            entries_with_nominal = [
                (sub_num, sub_spec, sub_spec.get("nominal"))
                for sub_num, sub_spec in by_hede.items()
            ]
            if all(n for _, _, n in entries_with_nominal):
                # Direct per-Hede emission with parser-attested nominals.
                sub_items_paired = [
                    ((sub_num, sub_spec), nominal)
                    for sub_num, sub_spec, nominal in entries_with_nominal
                ]
            else:
                # Legacy weight-sort + split fallback for pre-fix cache
                # entries.
                sub_items = sorted(
                    by_hede.items(),
                    key=lambda kv: kv[1].get("bruttovægt_g", 0) or 0,
                )
                count = len(sub_items)
                nominal_parts = _split_multi_nominal(d.get("nominal") or "", count)
                if nominal_parts is None:
                    # Can't split cleanly — skip the whole page for
                    # manual review.
                    stats["skipped_multi_nominal_unparseable"] += 1
                    continue
                sub_items_paired = list(zip(sub_items, nominal_parts))
            for (sub_num, sub_spec), nominal in sub_items_paired:
                if sub_num.lower() not in owned_subs:
                    stats["skipped_cross_reference_subhede"] += 1
                    continue
                # Per-Hede catalog refs (Schou / Sieg / Fr) — parser
                # extracts them from each sub-Hede's label line when
                # present. Falls back to page-aggregated refs only
                # when the parser couldn't pull per-Hede data (older
                # cached parses or label-format variants).
                sub_refs = sub_spec.get("catalog_refs")
                # Per-Hede years (parser emits when letter-block matched
                # for `specs.by_hede` shape). Falls back to the page-
                # aggregate `parsed["years"]` inside `_build_coin` only
                # when sub_spec has no per-letter year attestation —
                # avoids leaking legal-act years («møntordning 1544»)
                # from the page-scan into every sub-letter row.
                sub_years = sub_spec.get("years")
                coin = _build_coin(
                    hede_volume=hede_volume,
                    hede_number=sub_num,
                    parsed=d,
                    spec=sub_spec,
                    nominal_override=nominal,
                    mint_normalised=mint_normalised,
                    catalog_refs_override=sub_refs,
                    years_override=sub_years,
                )
                if coin is None:
                    stats["skipped_no_nominal"] += 1
                    continue
                if coin.get("year_first") and (
                    coin["year_first"] > year_to
                    or coin["year_first"] < year_from
                ):
                    stats["skipped_out_of_scope_year"] += 1
                    continue
                coins.append(coin)
                stats["kept"] += 1
        else:
            stats["skipped_no_specs"] += 1
            continue

    # V2-native write: delegate to shared `write_v2_seed`, which groups
    # by `issuing_entity`, applies lib.seed_merge.merge_seed per-entity
    # for curation preservation, and writes
    # `data/v2/seed/hede/<entity>.yml`. Internal `_merge_seed` (OUT_FILE-
    # based, V1-location-keyed) is no longer called — the shared
    # writer's merge has the same CURATED_FIELDS / DEEP_MERGE_FIELDS /
    # `_curation_holds` semantics applied per-entity.
    coins.sort(key=lambda c: (
        c.get("year_first") or 0,
        c.get("ruler") or "",
        c.get("catalog", {}).get("hede_volume", ""),
        c.get("catalog", {}).get("hede", ""),
    ))
    merge_stats = None  # Reported per-entity by write_v2_seed
    scope_note = (
        "Hede 1971 seed via danskmoent.dk parser cache "
        f"({HEDE_CACHE.relative_to(PROJECT) if HEDE_CACHE.is_relative_to(PROJECT) else HEDE_CACHE}). "
        f"Scope: {year_from} <= year_first <= {year_to}. Per-entry "
        "curation: fuss/phase/fraction/issuing_entity/kind/note/"
        "*_verified flags survive regen; `_curation_holds: {field: "
        "why, ...}` for per-entry escape hatches. Fresh entries appear "
        "with `fuss=seed_unsorted, phase=hede` as the curation signal."
    )
    write_v2_seed(
        coins,
        source_name="hede",
        source_label="Hede 1971 (danskmoent.dk cache)",
        scope_note=scope_note,
        dry_run=False,
        # `--no-merge` instructs writer to BYPASS merge_seed's curation
        # preservation (CURATED_FIELDS / DEEP_MERGE_FIELDS) and write fresh
        # data wholesale. Previously this flag also triggered dry_run=True
        # via `dry_run=not merge`, which made --no-merge a NO-OP (writer
        # never wrote). Now it writes the wholesale-fresh data as
        # intended. Use with care — destructive for any curator overrides
        # carried in the existing seed YAML.
        no_merge=not merge,
        extra_top_level={
            "scope_year_from": year_from,
            "scope_year_to": year_to,
        },
        exclude_ids=frozenset(zinc_drop_ids),
    )

    print()
    print("Stats:")
    for k, v in stats.items():
        print(f"  {k:40s} {v:5d}")
    if merge_stats is not None:
        print()
        print("Merge stats (curation-preserving):")
        for k, v in merge_stats.items():
            print(f"  {k:40s} {v:5d}")
        if merge_stats.get("orphan_curated", 0):
            print(
                f"  ⚠ orphan_curated > 0: {merge_stats['orphan_curated']} "
                f"existing entries have no fresh-regen match. They were "
                f"KEPT verbatim (the parser may have temporarily lost a "
                f"page); review with `git diff` if the count is unexpected."
            )
    print()
    print(f"Top skipped non-DK mints (first 15):")
    for m, c in sorted(skipped_mints.items(), key=lambda kv: -kv[1])[:15]:
        print(f"  {c:4d}  {m!r}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
