# Rebuild a final from its members — plan

Branch `rebuild-from-members` (worktree `.claude/worktrees/rebuild-from-members`,
cut from `de956d6`; `scripts/cache` and `.venv` are symlinks to the main
checkout). Curator request 2026-10-22: «відділити ті дані що дають члени
нижчого рівня + курації … як легітимні, від тих які існують лише у файналі …
проаналізуємо, … легітимні … закріпимо, а лишаться нелегітимні — це і будуть ті
які треба видалити».

## The defect this removes

`absorb_seeds_into_final_v2.py` enriches a final with `members = [fc] + classes`
(line ~3366): the final is its own first member, so every value it ever held is
re-unioned on every run. A seed that leaves a class (relocation, split, fold
re-cut, §9a re-thin) therefore leaves its sources, readings, catalogue numbers,
mints and years behind forever. `_surgical_decontaminate` fires only when a
whole class leaves `composed_of`; `_prune_foreign_kmm_citations` covers KMM urls
only. Measured 2026-10-22 on `39d312f`: 947 sources on 394 finals are attested
by another final's class (G155 `c-afd707d6` carried 163 of G36's).

The prune patch (`$S/absorb_patch.py`, class_attestation `prune_moved`) treats
the symptom for `sources` and readings. This plan replaces it with the cause
fix: **a final is a function of its members, the curator's decisions, and an
explicit own layer — never of its previous self.**

## Terms

- `F` — a final entry as stored.
- `M(F)` — what absorb derives for `F` from its classes alone, plus the
  curator surfaces (classification decision, `_curation_holds` and the held
  values, exclusions, `_source_errata` already applied in the seeds).
- `O(F) = F − M(F)` — values that exist only on the final. The candidates.
- `G(F) = M(F) − F` — values a rebuild would ADD. Must be empty; anything here
  is absorb non-idempotency and is investigated before going on.
- Annotations — final-level metadata that is not coin data: `note`,
  `verification_note`, `_migration_note`, `v1_home_location`, `promoted_to`,
  `_entity_routing_hint`, `_weights_thinned`, `label`, `origin`, `legacy_id`.
  Carried verbatim; outside the union question.

## Stage 1 — measure `M(F)` and `O(F)` (read-only, no data change)

1. `scripts/lib/final_derivation.py::derive(fc, classes)` — calls
   `_enrich_final_entry` with a SKELETON in place of `fc`: identity
   (`id`, `label`, `origin`, `composed_of`), fuss / phase / kind,
   `_curation_holds` + the held fields' values, annotations. Nothing else of
   `fc` is visible to it.
2. `scripts/maintenance/audit_final_only.py` — per final, per field, the sets
   `O` and `G`. Fields: `sources` (key `(url, ref)`), `weight_rough_g` /
   `fineness` / `diameter_mm` (key `(value, source)`), `catalog`
   (`(register, value)`), `mint`, `year_ranges` (year set), `metal`, and the
   foundation-immutable scalars (`nominal`, `ruler`, `mintmaster(s)`,
   `issuing_entity`, `fraction`, `year_is_reign_span`), inscriptions.
   Output: summary table field × origin (promoted / foundation) and JSON.
3. Gate: `G` empty for every final (or each non-empty `G` explained and fixed
   in absorb first). Unit tests on a synthetic final: a seed that left takes
   its values; a held value stays; a foundation scalar shows up in `O`.

## Stage 2 — classify `O(F)` by evidence of legitimacy (read-only)

Per value, collect evidence, never guess (§0b):

| Evidence | Tool |
|---|---|
| Attested by another final's class (moved / twin) or by a class with no final (orphan) | `lib/class_attestation` |
| First commit the value appeared on this final, and the route (V1 bootstrap / restore: `214f991`, `e210ed6`, `e851d3f`, `10850ab`, `4831c21`; pipeline absorb; final-level fold `dedup_final_foundations`; hand edit) | history walk, seed-keyed (`$S/hist2.py`, `via.py` → a maintenance script) |
| A curator decision names it: `merge_decisions`, `classification_decisions`, `_recorded_removals`, `_retracted_refs`, exclusions, builder errata tables | `trace_coin why` on the seeds of `F` |
| The cited specimen exists in a harvest cache whose seed would belong to this class | per-source cache lookup |

Buckets:

- **L — legitimate, own.** Value from a V1 curator route or a curator hand
  edit, not attested by any class; foundation scalars (`nominal`, `ruler`, …
  of the 687 foundations); fold-inherited values whose folded final's seeds
  are still members of `F`; curator `mintmasters`.
- **I — illegitimate.** Value that reached `F` through the pipeline from a
  seed that is now in another final's class, or whose seed is excluded,
  retracted or no longer exists.
- **R — review.** Twins, orphans, V1-restore values that another final's
  class also attests (the 44 of 2026-10-22), unseeded values with no
  identifiable route, catalogue values that contradict the class.

Report grouped by bucket × field × cause with examples → curator.
Curator decides R group by group; R resolves into L or I.

## Stage 3 — fix L as an explicit own layer

Vehicle — **curator decision D1**:

- **A (recommended): a curator seed source**, `data/v2/seed/curator/<entity>.yml`.
  One entry per final with own data, stable seed id `cur-<…>`, carrying exactly
  the L values, each with its provenance (`_origin: v1 214f991`, `fold km-…`).
  Joined to its class by a `merge_decisions` entry (members are seed ids,
  §9b-stable). The merger never lets a curator seed found a class on its own;
  its authority ranks above every source for scalars (it holds the
  foundation's chosen `nominal` / `ruler`). Result: the rule «final = f(members)»
  has no exception; `trace_coin why` shows the curator seed like any other;
  the D49 registry counts it as a specimen.
- **B: an `_own:` block on the final entry**, carried verbatim by absorb like
  `_curation_holds` and fed to the enrichment as a pseudo-member. No merger
  change; but it lives on the final only and seed-level tools do not see it.

The migration is a SCRIPT (`migrate_own_layer.py`), not hand edits, so it can
be re-run on a newer main at landing. Gate: after migration,
`derive(F) == F` byte-for-byte for every final except the I values (and R not
yet decided). The rendered site of both profiles is byte-identical to before
migration.

## Stage 4 — switch absorb

`members = own + classes`; `fc` contributes identity, fuss / phase / kind,
holds and annotations only. Then remove what only compensated for the
self-union: `_prune_foreign_kmm_citations`, the prune patch (not shipped),
and — after measuring — `_surgical_decontaminate`. `verify_reflow` keeps the
«moved» classification (patch `$S/verify_patch.py`). Tests: the Stage-1 cases
plus a fixed-point test (second absorb run, zero diff).

## Stage 5 — verify (worktree, from committed data)

Re-flow from the committed `final` / `seed_unified`. The diff must equal the I
list exactly, field by field — nothing more, nothing less. Then
`verify_reflow` (0 losses; I recorded per curator approval),
`audit_lost_citations` 0, `audit_curation_loss`, `trace_coin snapshot` /
`diff` (no real loss outside I), the full unittest suite, both site builds
with an HTML diff in which every change maps to an I value.

## Stage 6 — land

1. Curator approves the I list (grouped, with examples) — §9b deliberate
   removal; recorded in `_recorded_removals.yml` where the hook needs it.
2. Commits on the branch: code (derive, audit, own-layer support; no data
   change) → own-layer migration (render byte-identical) → absorb switch +
   re-flow (deletions = I).
3. Main moves meanwhile: rebase, re-run the migration script on main's data,
   repeat Stage 5. Coordinate the `data/v2` write window with the other
   sessions before merging. Never push without «пуш».
4. Rebuild danskmoent; `docs/V2_DECISIONS.md` (new D-entry), `handoff.md`,
   `TODO.md`.

## Curator decision points

- D1 — own-layer vehicle (A curator seed / B `_own` block).
- D2 — each R group (twins, orphans, the 44 V1-restore pairs, unseeded
  without route, catalogue / mint contradictions).
- D3 — the final I list before it is removed.

## Known risks

- A full re-flow is slow; Stage 5 runs in the background.
- Scalars where members disagree and the foundation chose — the own layer
  must carry the choice with top authority, or the rebuild flips it.
- `catalog` merge (`_deep_merge_catalog`, sub-indices, `catalog_alts`) and
  year holds are the most intricate paths; Stage 1 measures them separately.
- `scripts/cache` is shared with the main checkout; read-only here.

## Stage 1 — results (2026-10-22, data at `de956d6`)

`scripts/lib/final_derivation.py` + `scripts/maintenance/audit_final_only.py`,
tests `tests/test_final_derivation.py` (7). Baseline check: absorb's own
enrichment (A) reproduces the stored final for 13 871 of 13 880 finals (the 9
others differ in `metal`, set by a pass outside enrichment) — the measurement
is faithful. Of 13 880 finals, 11 237 show some difference between A and the
skeleton derivation B. Categories (values / finals; foundation | promoted):

- **own — only the final supplies it** (the stage-2 candidates):
  `sources` 417/283 | 2 438/436; `catalog` 680/298 | 327/155; `mint`
  52/46 | 88/86; `year_ranges` 116/22 | 303/16 (years); readings
  (`weight`/`fineness`/`diameter`) ~40 values; scalars of the 687 V1
  foundations (`nominal` 110, `ruler` 269, `metal` 111, `issuing_entity`
  114, years 110, `fraction` 156, inscriptions ~90 each, `v1_home_location`
  687); on promoted finals `mintmaster` 228, `year_verified` 185, `note` 749.
- **relabel — same url, the final keeps an older ref text**: `sources`
  86/61 | 70/68 (e.g. «Hede nc4h10» vs the member's «Hede nc4h10A»).
- **diverged — a single-valued field the final froze, the members now give
  another value**: `ruler` 256 | 4 292 (spelling: final «Frederik III.» vs
  member «Frederik 3»), `verification_note` 523 | 5 648 (the per-source
  boilerplate of whichever member came first), `nominal` 126 | 88,
  `note` 25 | 164, verification flags ~300.
- **hidden — a member value the self-run does not show**: `catalog` 59/32 |
  101/38 (single-slot registers such as `bruun_lot_no`, where the final's
  value takes the slot), 3 others.

Consequence for stage 3: the own layer is not only lists. A rebuild without
it flips ~4 500 ruler spellings and ~6 000 verification notes on the page,
so «diverged» needs a rule (which value wins, and where that choice lives)
as much as «own» needs a home.
