---
name: reading-marker
description: >-
  Put, change, or remove a curation mark on one measured reading (weight, fineness, diameter) in
  the V2 pipeline — «(!)» erroneous, «(*)» suspect, «(§)» template — so that it survives every
  re-flow and renders with the right tooltip. Use when a reading contradicts its type, a source
  value is shown to be wrong, a published figure is the standard's computed target rather than a
  weighing or assay, or an existing mark's reason needs rewording. Trigger phrases: «познач як
  підозріле», «це помилкове значення», «це шаблонне значення», «додай (*) / (!) / (§)»,
  «mark this reading suspect / erroneous / template», «зніми позначку», «онови тултіп позначки».
  Not for the «(?)» marker (that is a field's `*_verified: false` flag, not a reading mark) and
  not for correcting the value or a catalogue index itself (that is `_source_errata`).
---

# reading-marker — curation marks on measured readings

A mark says something about **one reading from one source**, not about the coin.
It lives on that reading in the **seed of the source that published it** and
flows seed → `seed_unified` → `final` through merge and absorb. The list of
kinds is `seed_merge._CURATION_MARK_KEYS`; the merger, the thinner, the render
and pre-commit Check 10 all read that one list.

## When to use

- A reading does not fit its type and the cause is unknown → **suspect (*)**.
- A reading has been **shown** to be wrong (a source's arithmetic, a transferred
  standard value, a demonstrable misprint) → **erroneous (!)**.
- A source prints the standard's computed **target** as if it were a specimen
  figure (e.g. Galster's 14,375 g / .979 for the Nobel) → **template (§)**.
- An existing mark's reason is outdated or needs another language.

## When NOT to use

- The field is merely unsourced or inferred → `<field>_verified: false`, which
  renders «(?)». Not a reading mark.
- The **value or catalogue index** printed by the source is wrong and must be
  replaced → `_source_errata` (needs the curator's explicit in-chat approval,
  CLAUDE.md §4). A mark keeps the value visible; an erratum replaces it.
- The whole coin is out of scope → `data/v2/exclusions/` (PB-12).
- You want to hide a reading → never. Marks keep readings visible (§4).

## What each kind does

| Kind | Glyph | Render | Δ / arithmetic | Matching | Thinning |
|---|---|---|---|---|---|
| `erroneous` | (!) | struck through | **excluded** | excluded | never dropped |
| `suspect` | (*) | struck through | kept | kept | never dropped |
| `template` | (§) | normal | kept (Δ ≈ 0 by construction) | kept | never dropped |

Precedence in one display group: erroneous > suspect > template. The tooltip
opens with a generic bold headline per kind («Помилкове / Підозріле / Шаблонне
значення.»), rendered by `assets/app.js` — do NOT repeat it in the reason.

## Procedure

1. **Check for an existing decision** — `trace_coin.py why <seed-id> --field <f>`
   (CLAUDE.md §0b-1). If a curator call already explains the value, stop and
   surface it; do not stack a mark on top of an erratum.
2. **Find the seed reading.** `trace_coin.py trace <any id>` → the seed id and
   file (`data/v2/seed/<source>/<entity>.yml`). The mark goes on the reading
   whose `source` published the value — never on `final`, never on
   `seed_unified` (both are regenerated; a mark written there is erased by the
   next absorb).
3. **Choose the kind** from the tables above. Unsure between (*) and (!)? It is
   (*) until the error is demonstrated.
4. **Write the reason** — four languages (de / en / uk / da), reader-facing
   (§0z), sourced (§0), one paragraph:
   - first sentence: a short thesis in plain text («Надважкий екземпляр.»,
     «Не результат визначення проби.»), no own headline line, no «Підозріло:»;
   - then the evidence: the value, what it is compared with, and where from;
   - for (*), end with what remains open («… однаково можливі, і жодне з них не
     доведене.»). Numbers: comma decimals in de/uk/da, point in en.
5. **Edit through `yaml_io`.** Turn the scalar or the list into list form if
   needed and render the block with `yaml_io.canonical_lines(path, field,
   value, indent=…)`; never hand-type the folded lines (Check 9 blocks a raised
   round-trip residual).
6. **Re-flow the entity** — `merge_seeds_cross_source.py --entity <e> --apply`,
   then `absorb_seeds_into_final_v2.py --entity <e> --apply` (absorb thins; no
   separate step). Background both.
7. **Verify** — `audit_curation_marks.py` must report the mark reaching final;
   `git diff data/v2/final` should show only the mark (plus anything the
   re-flow legitimately changed — read it). Rebuild and hover the tooltip.
8. **Commit** seed + seed_unified + final with an explicit pathspec, `data:`
   prefix, the reason's source in the message.

Removing a mark is the same procedure with step 4 replaced by deleting the key
from the seed reading.

## A mark on the YEAR (not on a measurement)

A source's year that must not drive the displayed year, but must stay visible
with a marker, is handled by the year analogue of the reading marks
(2026-10-15, founding case: the Münzkabinett Berlin's «um 1506» on the
Frederik I Gottorp Goldgulden, Galster 122):

1. On the SEED entry of the source that published the year, add
   `year_mark: {kind: suspect | erroneous, reason: {de, en, uk, da}}`
   (schema `YearMark`; rendered with `yaml_io.canonical_lines`). It sits in
   `seed_merge.CURATED_FIELDS`, so a re-seed keeps it.
2. Keep that member's year out of the year union with a `year_demote` entry in
   `merge_decisions/<entity>.yml` (the year is demoted, never deleted).
3. The merger (`_collect_year_alts`) emits `year_alts: [{value, source, kind,
   reason}]` on the unified class; absorb unions the live members' alts onto
   final; the template shows the value beside the year as a muted chunk with
   «(*)» / «(!)» and the reason in the tooltip (`MARK_HEAD` headline applies).
   An alt whose value is already in the year label is not shown.
4. Re-flow (merger + absorb), rebuild, hover the marker. The reason is
   reader-facing prose with sources named (§0z), not a project note.

## A mark on the RULER

Same shape as the year (2026-10-16, founding case KMM 331973 «Hans» on a
Hauberg-numbered Lund penning): `ruler_mark: {kind, value?, reason}` on the
SEED (in `CURATED_FIELDS`); the merger emits `ruler_alts`, absorb unions them,
the template shows the value muted beside the ruler with «(*)» / «(!)». When an
erratum replaces the seed's ruler, put the printed ruler in `value`. NOTE:
`ruler` is foundation-immutable in absorb — a corrected ruler must also be set
on the existing final entry (yaml_io line edit), or it never reaches the render.

## A mark on the MINT

`mint_mark: {kind, value?, reason}` on the SEED (in `CURATED_FIELDS`), the same
shape as `ruler_mark` (2026-10-18, founding case Bruun Part V lot 14206 printing
«Copenhagen Mint» for the Altona Rejsedaler 1788, Hede 25). The difference from
year and ruler: an **erroneous** mint mark is presentational ONLY (curator
2026-10-18). `seed_merge.apply_mint_mark` moves the printed mint into
`mint_mark.value` and clears `mint` — at seed write (merge_seed) and again when
the merger loads seeds — so the value takes part in nothing: not the class's
mints, not matching, not entity routing. The merger emits `mint_alts`, absorb
unions them, and the template shows the value muted beside the mint with «(!)».
A **suspect** mint mark keeps the mint in play (like a suspect reading).
A builder may set the mark from its own table (Bruun: `_BRUUN_LOT_MINT_MARKS`,
routing on `route_mint` that ignores the marked value); a hand-written mark on
a seed works too, but the seed's `issuing_entity` is only re-derived on the
next builder run. Not a substitute for `_source_errata` when the curator wants
the value replaced rather than shown.

## A mark on a CATALOGUE NUMBER

`catalog_marks: [{register, value, kind, reason?}]` on the SEED (in
`CURATED_FIELDS`; schema `CatalogMark`), 2026-10-20, founding case Numista
476697 / 476698 printing «Galster 48» for the ½ Sølvgylden 1532 (Galster 49).
`register` is the CatalogRefs field (`galster`, `schou`, …), `value` the number.

- `suspect` «(*)» / `erroneous` «(!)» (reason required): the printed number.
  `seed_merge.apply_catalog_marks` takes it out of the seed's `catalog` (at seed
  write and at merger load), so it neither justifies nor refutes a merge; the
  merger emits `catalog_alts`, absorb carries them from the live members, and
  the Catalog column shows the number muted with its mark.
- `unverified` «(?)» (no reason): the coin's attributed number that no source
  prints for it. Also kept out of matching (bring the merge with a
  `merge_decision`); the merger puts it into the class catalog and lists it in
  `catalog_unverified` — UNLESS another member carries the same number unmarked,
  in which case the attested number wins and the «(?)» goes (§4).

Check 10 verifies the marked number reaches final (as an alt, or in the
catalog); verify_reflow counts a number moved into `catalog_alts` as attested,
not lost. Not a substitute for `_source_errata` when the curator wants the
printed number replaced and not shown.

## Hard rules

- A mark is written on the SEED reading only. Anything in `final` without a
  seed counterpart is lost on the next absorb (the 2026-09-28 Nobel case).
- Never a mark to hide, soften, or «fix» a value — marks annotate, they do not
  replace. Replacing is `_source_errata`, with curator approval.
- Never invent the reason. If the evidence is only «it looks odd», that is a
  suspect mark with exactly that stated, not a narrative.
- New reading-mark kind? Add it to `seed_merge._CURATION_MARK_KEYS`, `compute.py`'s
  precedence, the template's `msign`, `app.js`'s `MARK_HEAD`, and this table —
  nothing else hard-codes the list.
