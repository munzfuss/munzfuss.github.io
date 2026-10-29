# Plan — uncertainty markers: «(?)» source-hedged vs «[ … ]» inferred

Curator direction 2026-10-29 (approved in chat). Today one «(?)» covers two
different things: a source that prints a value uncertainly («ND (ca. 1496-97)»,
«(ca1611)», «U.år (1523?)», «Christian 1?») and a value we infer when the source
gives none (reign window for an undated coin, the standard's fineness, a curator
compilation of several datings). The two are to be kept apart in the data, in
the tooltip and in the glyph. Finals are never cleaned by hand: every new field
is built from the members only, never from the final's stored copy.

## Stage A — the merger's year_verified rule (done in code 2026-10-29)

The OR-merge counted an absent `year_verified` (builders flag only the
unverified case, so absent = attested) as «no information». Three effects,
measured 2026-10-29 over 180 finals with «(?)» on the year:

1. one undated member beat several dated ones (Christian V 1671: Hede «u. år»
   vs Numista, ucoin, NGC, NumisMaster);
2. a member with no year at all (NGC) carries `year_verified: False` and put
   the class under «(?)»;
3. absorb OR-merges the final's own stored flag, so a False once written stays
   (`dk-tid-170107`: nine plain sources, «(?)»). Not fixed by a hand edit:
   it goes when the Fuß joins `_rebuild_scope.yml`, or when stage D renders
   from `uncertainty` instead of the flag.

Rule (`merge_seeds_cross_source._year_attestation`): a member attests when it
gives a year, is not held out (reign span, `year_demote`, `year_mark`) and its
flag is not False. Not an attestation: a single span from Numista / ucoin /
KMM / IKMK (they never flag undated coins); a KMM year whenever another member
is uncertain (curator: KMM writes approximate datings as plain years). A
source printing the year uncertainly next to a plain one is a conflict: the
year stays «(?)» and `year_conflict` keeps both sides (curator: the plain
source is not necessarily right; review later, volume unknown).

Measured effect before the re-flow: 52 finals lose a wrong «(?)» (33 where
every member with a year is plain, 19 plain vs our reign placeholder); 41 are
conflicts; 8 have only a Numista/ucoin/KMM span and keep «(?)». Only those in
rebuild-scope Fuß (or with a class now carrying an explicit True) change at
once.

## Status 2026-10-29

A ef7f9cd / 040c269; B e5de2e4 / 52ac105 (671 seed entries, 1306 finals); D 5a4bcec, bca7ea5 (inferred member years no longer make a conflict) and the metal / mint relevance fix. Open: NumisMaster ND marker text (needs parse_numismaster to record it); fineness from the standard (`standard`) not yet written anywhere; the 74 year conflicts await a review decision; finals whose year flag is stale with no unverified member wait for their Fuß's rebuild.

## Stage B — record HOW and BY WHOM a value is uncertain

New schema field `uncertainty: {field: [entry]}` on seeds (and, unioned, on
seed_unified / final), for year, ruler, mint, metal, fineness. Entry: `source`,
`kind: hedged | inferred`, `how` (ca, nd, query, range, after, reign, standard,
default, compiled), `as_printed` (the source's own text), `value`. Written by
each builder at the exact point where it sets `*_verified: False`; an inventory
script lists every such point so none is missed. `year_is_reign_span` becomes
one `inferred / reign` entry. Known gap: Numista and ucoin never mark undated
coins (Numista `is_dated` is cached for 140 types only).

## Stage C — merger and absorb

Union every member's entries, never collapse: several hedged sources, and
different ranges from different sources, all kept. A class where one source is
plain and another hedged is flagged (who is plain with what value, who hedged
and how) and listed by a report script — visible, not blocking. Absorb carries
`uncertainty` from the live members only, like `year_alts`.

## Stage D — render

«(?)» = a source prints the value uncertainly; «[ … ]» = we inferred it
([1396–1439], [København], [,875]). Mixed: the source decides the glyph, the
tooltip lists both. The tooltip is built from `uncertainty`: each source with
its printed text, each inference with its basis, and for a conflict the plain
sources too. Strings in `ui.yml`, four languages. The marker is driven by
`uncertainty` (member-built, correct in every Fuß), not by the self-unioned
flag (curator approved 2026-10-29).

## Stage E — checks and docs

Audit: every marked value has an entry, nothing lost in the merge. CLAUDE.md
§4, V2_DECISIONS, `reading-marker` skill. Both sites rebuilt, HTML diff
counted.

Each stage: code, tests, data in separate commits; data/v2 window agreed with
the peer session first.
