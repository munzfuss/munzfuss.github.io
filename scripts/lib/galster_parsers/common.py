"""Shared constants used by multiple Galster parser shapes.

These are deliberately kept tiny — most parsing logic stays inside
each shape's own module. Anything that grows to >10 LOC and is used
by ≥2 shapes belongs here.
"""
from __future__ import annotations

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
