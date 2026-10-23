# Rebuild a final from its members — plan (revision 3)

Branch `rebuild-from-members`, worktree `.claude/worktrees/rebuild-from-members`,
cut from `de956d6`; `scripts/cache` and `.venv` are symlinks into the main
checkout (read-only use). Curator direction 2026-10-22: separate what the
members (plus curator decisions) give from what exists only on the final; sort
the latter into legitimate and stale; make the legitimate part durable; delete
the stale part. Revision 2 made the production pipeline the oracle. Revision 3
(2026-10-23) follows a strict review of revision 2 against the code and the
data; its measured corrections are marked **[rev3]**. Curator direction
2026-10-23: normalisation of nominal, ruler, mint and catalogue indices moves
to an early stage of the pipeline.

## 0. Goal and definition of done

**Invariant:** `final = f(members, curator decisions)` — nothing a final holds
may exist only because the final held it before.

**Done when**, on the branch rebased onto main:

1. absorb builds every final without the final among its own members, on
   EVERY path that re-enters a stored final (P1, P2, P5 — §2);
2. a re-flow from HEAD changes the corpus by exactly the curator-approved
   removal list — nothing else, field by field, and the rendered pages by
   exactly the rows that list implies;
3. every legitimate value that used to live only on the final has a
   pipeline source (seed / decision / rule) that `trace_coin why` names;
4. a second run is a zero diff (fixed point);
5. the code that only compensated for the self-union is gone;
6. **[rev3]** a guard stops the drift from re-accumulating: a commit that
   changes `data/v2/final` must be explainable by seeds, `seed_unified` or
   decisions in the same commit, or be a re-flow (pre-commit check).

## 1. Why this method

| Option | What it does | Verdict |
|---|---|---|
| A. Prune | keep the self-union, strip values another final's class attests | symptom only, `sources` + readings only; rejected |
| B. Imitation (revision 1, `lib/final_derivation`) | call a subset of absorb twice, compare | misses matching, normalisation, purges, decisions; kept only as a per-value classifier and a regression test |
| **C. Pipeline as oracle** | switch the self-union off in the real absorb, run it on the worktree, diff against HEAD | complete and exact; the diff is the candidate list and, iterated, the convergence measure |

**Measured 2026-10-23:** an unchanged `absorb --apply` over the baseline
`de956d6` leaves ZERO changed files. The baseline is a fixed point, so every
line of a stage-B diff is attributable to the switch alone.

## 2. Where a final's stored data re-enters the output (inventory)

`absorb_seeds_into_final_v2.py` at `de956d6`; line numbers approximate.

| # | Path | Line | Fires |
|---|---|---|---|
| P1 | main enrichment `members = [fc] + classes` | ~3366 | every final, every run |
| P7 | inside `_enrich_final_entry`: `_FOUNDATION_IMMUTABLE_FIELDS` copied from `fc` **regardless of `origin`**; `note` / `verification_note` / inscriptions first-non-None with `fc` first; `label` / `origin` / bookkeeping copied | 577–1310 | with P1 |
| P8 | in-place normalisation of `fc` before enrichment (nominal adoption, mint split, catalogue normalise, flag rules) | ~2540 | every final — transforms, does not carry |
| P2 | `_folded_self`: a folded self-foundation re-enriched from its OWN STORED dict as `members[0]` | ~2983, ~3472 | **every run** (control: danish_realm 25 folded) |
| P3 | `curator_migrations`: a purged stale foundation's fields / sources carried to its host | ~2650–3540 | **every run** (control: danish_realm 9, royal_holstein 2) |
| P4 | `cross_carry`: a relocated final's fields gap-filled onto its new host | ~2780 | on a relocation |
| P5 | monotonic guard: a prior final re-added VERBATIM from the stored file | ~3767–3819 | **every run** (control: danish_realm 9, royal_holstein 2) |
| P6 | curated shell kept (`_settle_curated_shell`) | ~3793 | on a superseded shell |

**[rev3] Correction.** Revision 2 claimed P2–P6 are silent in a fixed-point
run. The control run shows the steady state is an in-run cycle: fold / purge
drop a final and P2 / P5 bring the STORED copy back, so the file is unchanged
only because the two cancel. P2 and P5 are therefore self-union entrances in
their own right; the switch (stage A) must cover them, or ~40 finals keep
their stale data through every run.

**[rev3] The scalar face of the same defect.** P7 freezes `nominal`,
`ruler`, `mintmaster`, `issuing_entity`, `fraction` on PROMOTED finals too:
4 261 promoted finals carry a `ruler` their own class no longer gives
(«Karl X» vs «Karl X Gustav»). A promoted final has no curator layer in these
fields (corrections go through seed errata and reach the class), so for
`origin: promoted` the class must win; for `origin: foundation` the V1 value
is the curator's and stays. The winner rule depends on `origin`.

## 3. Ground rules for every run

- **Baseline is frozen**: the data of `de956d6` on this branch. Before EVERY
  measuring run: `git checkout -- data/v2/final data/v2/classification_decisions
  data/v2/seed_unified data/v2/class_registry` (CLAUDE.md §9b).
- Long runs (absorb over all entities, both site builds) in the background,
  logs to the scratchpad, no `| tail` on hook-bearing commits.
- Measurement is seed-keyed (`trace_coin snapshot` / `diff`) and at the end of
  the chain (rendered HTML), never by final id alone.
- **[rev3]** `verify_reflow` / Check 7 block list shrinkage and emptied
  scalars only; a scalar CHANGE («Frederik III.» → «Frederik 3») is `moved`
  and `note` is excluded. Every stage therefore has its own hard gate: the
  HTML diff of both sites must equal the expected row list, or the stage does
  not pass.
- Nothing from this branch reaches main before stage G, except stage N
  (normalisation), which lands first and on its own.

## Stage N — normalisation at the seed level **[rev3, first, lands on main]**

**Finding.** The finals carry canonical forms the seeds never received.
`ruler: Frederik 3` (the museum's spelling) sits 1 074× in the KMM seed of
danish_norway, 410× in its `seed_unified`, 60× in its final; the finals were
re-spelled «Frederik III.» by June 2026 passes on `data/v2/final/*` alone
(`a777b9a` and the «bulk canonicalisers» it names). A rebuild from members
reverts ~4 500 rulers on the pages — not because a rule is undecided, but
because the fix lives at the wrong layer. The same question is asked for
nominal, mint and catalogue indices (curator 2026-10-23).

**Where.** `lib/v2_seed_writer.write_v2_seed` is the one point every source
passes (CLAUDE.md «every seed builder is merge-aware»), and it already holds
the nominal / mint / catalogue hygiene that absorb P8 imports
(`_normalise_nominal`, `_extract_mint_from_nominal`, `_canonicalise_mint`,
`_normalise_catalog`). The merger is the second point (per-class synthesis).
Rule: a value is normalised ONCE, at the writer, and the merger / absorb
re-apply the same function only as an idempotent no-op guard.

**Steps.**

1. Inventory: every commit in history that changed `data/v2/final/*` without
   a seed / `seed_unified` change in the same commit (`git log` filter), and
   what it did (ruler forms, mint spellings, nominal tails, catalogue
   folds). Each is either reproduced at the writer or classified stale.
2. Ruler: one canonical DISPLAY form at the writer (`lib/ruler_reigns` has
   the KEY normaliser `normalise_ruler_name`; the display form «Name Roman.»
   plus `ruler_verified` for uncertain attributions, as `a777b9a` did on
   finals). Joint / ambiguous forms untouched, as then.
3. Nominal, mint, catalogue: confirm the writer's hygiene equals what absorb
   P8 still does on finals; move any P8-only rule down; P8 becomes a no-op
   guard.
4. §9b trap: each changed normaliser is run old vs new over the DISTINCT
   values of EVERY seed (all sources) and the list of differing results is
   read; the count must be what was intended.
5. Re-seed → merge → absorb. Expected: `seed_unified` changes (canonical
   forms), finals CHANGE ONLY where the final was never re-spelled (the 60
   «Frederik 3» etc.), render diff = those rows. `verify_reflow` 0 losses.
6. Commit on the branch, then land on main FIRST (independent of the switch;
   shrinks the stage-B diff by thousands of rows; avoids a long-lived
   divergence from a moving main).

## Stage A — the switch (code, no data change)

1. absorb: flag `--no-self-union` (env `ABSORB_NO_SELF_UNION=1` for the
   prune-rerun child). With it:
   - P1 passes `skeleton(fc)` as `final_entry` and `members[0]`;
   - **[rev3]** P2 enriches `[skeleton(restored), unified]`, not the stored
     dict;
   - **[rev3]** P5 re-adds `skeleton(prior)` enriched from its live members,
     never the verbatim prior; a prior with no live member is reported, not
     re-added silently.
2. **[rev3] The skeleton is a per-field policy, not a key list:**

   | Field | Policy |
   |---|---|
   | `id`, `label`, `origin`, `composed_of`, `legacy_id`, `class_id` | carry |
   | `fuss`, `phase`, `kind` | carry (decisions re-apply on top) |
   | `_curation_holds` + each held field and its `_verified` companion | carry |
   | `note` (curator prose; 801 promoted finals hold one their class lacks) | carry until stage D moves it to its source; never dropped |
   | `_weights_thinned`, `_entity_routing_hint`, `_migration_note`, `v1_home_location`, `promoted_to`, `mintmasters` | carry (bookkeeping / curator-filled, no member supplies them) |
   | `nominal`, `ruler`, `mintmaster`, `issuing_entity`, `fraction`, `year_is_reign_span` | foundation: carry (V1 curator); promoted: derive (class wins) |
   | `verification_note` | derive (per-source boilerplate of the members) |
   | `sources`, readings, `catalog`, `mint`, years, `metal`, flags, inscriptions | derive |

3. Nothing else changes: matching, P8, P3 / P4 / P6, purges, decisions,
   thinning run as before. Counters for P2–P6 printed per entity.
4. Tests: flag off is byte-identical to today on a fixture; flag on drops a
   citation no class gives, keeps a held value, keeps `note`, lets the class
   win `ruler` on a promoted final and the foundation win it on a V1 one;
   P5 re-adds a skeleton, not the prior.
5. Commit on the branch (code only).

## Stage B — first full run and its diff (the candidate list)

0. **[rev3]** One merger dry-run over the baseline: `seed` ↔ `seed_unified`
   consistency (the control run proved only `seed_unified` ↔ `final`).
1. Reset data (§3). `trace_coin snapshot` → `before`.
2. Build both sites from the baseline into scratch output dirs.
3. `absorb --apply --no-self-union` over all entities (background).
4. Measure: `git diff --stat data/v2/final`; `verify_reflow` (losses AND
   `moved` scalars, both read); `trace_coin diff`; both sites rebuilt and
   diffed per page (rows, columns); P2–P6 counters.
5. Second run, flag on, no reset: zero diff, or the idempotence bug is fixed
   before stage C.
6. Output `candidates.json`: one row per (final, its seeds, field, value,
   direction), seed-keyed. Memberless finals (110 with no class) and the
   **[rev3]** 43 head-departed finals (§C, group H) as their own groups.
7. Cross-check against the revision-1 audit; a large disagreement is
   explained first.

## Stage C — classify the candidates (read-only, evidence only)

Tool `scripts/maintenance/classify_self_union_diff.py` attaches evidence per
value: attestation by another final's class / an unfinaled class / none
(`lib/class_attestation`); first commit and route in the history of
`data/v2/final/<entity>.yml` (seed-keyed blocks; the 2026-10-22 scratch
history scripts made a tool); curator decisions via `trace_coin why`; relabel
pairing (`final_derivation.classify`).

Buckets:

- **S — stale.** Pipeline-route value now attested by another final's class;
  seed excluded, retracted or gone; the old text of a relabel; a promoted
  final's frozen scalar that its class has since corrected.
- **L — legitimate.** V1 route (`214f991`, `e210ed6`, `e851d3f`, `10850ab`,
  `4831c21`) not attested by any class; curator prose; transfer from a folded
  / purged final whose seed is still in this final's lineage.
- **H — head departed [rev3].** 43 promoted finals whose `label` names a head
  seed no longer in any of their classes (a Hede sub-letter split, e.g.
  `c-6c39ea13` «unified-dk-hede-nf3h38»: composed of `kmk-278488` alone, yet
  carrying 11 Hede citations and the Hede ruler; the Hede coin renders twice).
  Not a value removal: a merge of the remaining seed into the head's class, or
  an exclusion — routed to `v2-merge-coins`, curator per case (24
  danish_norway, 16 danish_realm, 3 royal_holstein).
- **R — review.** Twins (home only in `seed_unsorted`), orphans (class with no
  final, e.g. 161 KMM korshvid under excluded `kmk-642893`), V1-restore values
  another final's class also attests (the 44 of 2026-10-22), no identifiable
  route, catalogue / mint values contradicting the class.

Report per bucket × field × cause, counts and three examples each, with
sources. The curator decides each R group and each H case. No data changes.

## Stage D — make the legitimate part derivable (loop)

Each sub-step: reset → stage-B run → the diff shrinks by exactly that
sub-step's values and grows by nothing.

- **D1 — the V1 corpus becomes a seed source**, `data/v2/seed/v1/<entity>.yml`.
  One seed entry per V1 foundation with its L values and per-value provenance
  (`_origin: <commit> <route>`), written through `write_v2_seed`.
  **[rev3]** Seed id `v1-<foundation id>`: 273 of the 687 foundation ids ARE
  ucoin seed ids (`dk-tid-…`, `lu-tid-…`, `hb-tid-…`), so the bare id
  collides. `v1-` gets an explicit place in the merger's `_ID_AUTHORITY_ORDER`
  (above every source for the descriptive scalars the V1 curator chose;
  measurements union as usual). The seed joins its class by an explicit
  `merge_decisions` entry. **[rev3] Identity:** per D49 addendum 3 a
  foundation keeps its `km-…` id because «id == member class» misread as a
  self-link; a V1 seed inside a class does not change that — the foundation
  stays `origin: foundation` with its own id and lists the class in
  `composed_of`; nothing is re-keyed. A memberless foundation becomes a
  singleton class of its V1 seed.
  Gate before the switch: V1 seed added, switch OFF → render byte-identical.
- **D2 — transferred own values** (folds / purges / relocations): derivable
  where the donor's seed is a member; otherwise a V1-seed value (curator
  route) or S (pipeline route), per stage C.
- **D3 — `verification_note`** derived from the members by one rule (to agree
  with the curator: highest-authority member's text, or composed per source).
  Ruler / nominal / mint forms are stage N, already landed.
- **D4 — `note`** on promoted finals: moved to the V1 seed where the route is
  V1, kept as carry where it is a curator edit on the final (CLAUDE.md
  forbids hand edits of coin fields — each such note is listed for the
  curator), S where it is a copied source text the class now lacks.
- **D5 — relabel:** the member's current ref text wins.
- **D6 — holds:** already in the skeleton; every held field survives.

The loop ends when the stage-B diff equals S ∪ (R decided S) ∪ (H resolved).

## Stage E — curator approval of the removal list

The remaining diff, grouped (bucket, field, cause) with examples and counts.
Recording per §9b for Check 7: per-value `_recorded_removals` entries
generated from the approved list, or a `verify_reflow` classification «stale
after a seed left» driven by the same evidence (revision-1 patch
`$S/verify_patch.py`); the list itself approved group by group. No
`--no-verify`.

## Stage F — default on, compensations out, guard in

1. The switch becomes the default; the flag is removed.
2. Remove, each measured by a stage-B run (zero diff expected):
   `_prune_foreign_kmm_citations`; `_surgical_decontaminate`; P3 / P4 where
   the V1 seed now carries the data; P2 / P5 / P6 reviewed one by one.
3. **[rev3] Guard:** pre-commit check — a staged `data/v2/final/*` change
   without a staged seed / `seed_unified` / decision change must be a re-flow
   (absorb from HEAD reproduces it); otherwise HARD BLOCK with the list of
   final-only edits. This is what would have caught the June passes.
4. `audit_final_only` becomes the regression test (A == B for every final)
   or is deleted.

## Stage G — landing

1. Rebase onto main (stage N is already there). Every data step is a script
   (V1 seed generator, merge decisions), so it is re-run on main's data, then
   stages B / E verification again.
2. Commits (pathspec, `-F`, background): (1) code — switch off by default,
   tools, tests, guard; (2) V1 seed + merge decisions — render
   byte-identical; (3) switch on + re-flow — the approved removals, recorded.
3. Coordinate the `data/v2` write window with the other sessions before the
   merge into main. Never push without «пуш».
4. Rebuild danskmoent; `docs/V2_DECISIONS.md` new D-entry (self-union
   removed; V1 is a source; normalisation at the writer; the guard),
   `docs/ARCHITECTURE.md`, `docs/handoff.md`, `docs/TODO.md`.

## Not in scope (named so nobody looks for them)

`relink_promoted_v2.py` (Phase 4b, writes `promoted_to` into seeds) and
`data/v2/match_uncertainty/` do not influence a final's content; untouched.

## Curator decision points

| When | Decision |
|---|---|
| N | the canonical ruler display form; which final-only passes are reproduced |
| after B | nothing — numbers only, unless the second run is not a fixed point |
| after C | each R group → stale or legitimate; each H case; the `verification_note` rule |
| D1 | V1 as a seed source (recommended) vs an `_own` block on the final |
| D4 | each `note` that is a hand edit on a final |
| E | the final removal list, group by group; the recording mechanism |
| G | the landing window |

## Risks

- **Main moves meanwhile.** Stage N lands first; every later data step is
  scripted and re-run at landing; the rebase is the last step.
- **V1 seed authority** could override a better source value on a scalar the
  V1 curator never chose (bootstrap defaults). Stage C separates curated V1
  values from bootstrap defaults by route; defaults go to S or R.
- **Memberless finals** (110) and head-departed finals (43) swamp a flat
  report — each is its own group.
- **Catalogue merge** (`_deep_merge_catalog`, sub-indices, single-slot
  registers) and year holds are the intricate paths; the stage-B diff is read
  per register.
- **Run time.** Absorb over all entities plus two site builds per iteration;
  all in the background, one git op at a time.

## Revision history

- rev. 1 (2026-10-22): imitation-based measurement (`lib/final_derivation`,
  `audit_final_only`, 7 tests, `dd15775`). Results kept as the expectation
  stage B is cross-checked against: 11 237 of 13 880 finals differ between
  `[fc] + classes` and skeleton + classes; own `sources` 417/283 (foundation)
  | 2 438/436 (promoted), `catalog` 680/298 | 327/155, `mint` 52/46 | 88/86;
  relabel 86/61 | 70/68; diverged `ruler` 256 | 4 292, `verification_note`
  523 | 5 648; hidden `catalog` 59/32 | 101/38.
- rev. 2 (2026-10-22): the pipeline as oracle (`72cb093`).
- rev. 3 (2026-10-23): corrections from the strict review — P2 / P5 fire
  every run (control: zero diff but 25 + 9 + 9 in danish_realm); diverged
  scalars are June final-only normalisation (stage N, first); skeleton as a
  per-field policy incl. `note`; winner rule by `origin`; group H (43);
  `v1-` seed id prefix (273 collisions); HTML diff as a hard gate; the
  no-final-only-edits guard.

## Stage N — step 1 results (2026-10-23, history up to `de956d6`)

**Final-only commits.** 747 commits touched `data/v2/final/*`; 298 of them
changed NO seed / `seed_unified` file. By what they did (subject-keyed,
`$S/classify_commits.py`): decisions re-applied by absorb (exclusions /
classification / merges) 103 — legitimate; per-coin curator fixes written
on the final 98 — stage C sorts them (hold, V1 seed, or stale); prose
passes 35 — `255426e` (904 Claude-translated `_source_note`s applied to
finals, «builder-wiring … stay follow-ups»), `064bfe9` / `a523b0f` /
`e430d33` / `7a831dc` (Danish backfill into notes and verification notes),
`be563e1` / `02a6eb8` (§0z scaffolding stripped) — the origin of the
5 648 diverged `verification_note`s and most of the 801 class-less notes;
pipeline outputs 30 — legitimate; normalisation passes 18 — `7e95732`
(Frederik, 3 249), `917b7a6` (Christian, 4 065), `a777b9a` (annotated /
uncertain kings + `ruler_verified`), `2e38175` (Hans — the only one that
also fixed the builder), `0aa8b69` (numeric catalogue indices, 905),
`24b8855` (Aagaard), `92557b3` (Davenport fold), `1612a01` / `730d93f`
(cf / unlisted / mintmaster-in-mint strips), `f4e7bc1` (NGC grade
markers), `46914ae` (nominal capitalisation); V1 route 14.

Of the normalisation passes, the catalogue ones are already in
`lib/catalog_codes` / the writer's `_normalise_catalog` (D31 and later);
the nominal / mint ones in the writer; **ruler has no writer-level
canonicaliser at all** — every seed still carries the source's form.

**Ruler canonical display form — prototype measured over every seed**
(`$S/ruler_forms.py`): 929 distinct (entity, ruler) forms; in the four
Danish-crown entities the June rule («Name Roman.» for exact king forms,
Arabic / Roman / English / with or without period; `?` → `ruler_verified:
false`) would change 17 470 seed entries across 60 distinct forms
(«Christian 4» 5 108, «Frederik 3» 3 090, «Christian V» 679, «Frederick
III» 278, …) and leave 2 279 untouched (already canonical, Gottorp dukes
such as «Frederik 3 af Slesvig-Holsten-Gottorp», compounds, institutions,
«?»). Two divergences from the June passes to decide: «Friedrich I/II» (27)
and «Johann» (2) inside Danish-crown entities — the prototype maps them to
«Frederik …» / «Hans», the June passes left them.

**Notes.** `note` and `verification_note` are generated or translated at
the final layer only (`255426e`); the seeds carry `_source_note` (da). To
be derivable they need a source: a per-seed translation table consumed by
the merger (or the V1 seed where the note is V1's), and a
`verification_note` composed by one rule from the members — stage D3 / D4.

## Stage N — done on the branch (2026-10-23)

Code: `lib.ruler_reigns.canonical_ruler_display` + the writer's
`_canonicalise_ruler` (fresh coins and the orphan-curated pass), 10 tests;
`canonicalise_seed_rulers.py` (one-shot, batched line edits through
`yaml_io`); `final_diff_candidates.py` (every differing value, seed-keyed).
Data: 17 442 seed entries in 26 files, 82 forms; seed_unified of the four
Danish-crown entities re-merged. **Measured:** the finals did NOT change
(ruler is frozen on a final by P7 — the June forms are already there, and
a final that never got the June pass keeps its old form until stage B);
verify_reflow 0 losses; trace diff 0 real losses; munzfuss render
byte-identical except the build date. One pipeline consequence for the
curator: «Hans?» → «Hans» (unverified) let the merger join KMM 317652 /
317653 / 317654 («1 Hvid(?)») to the Galster 31 Hvid class `c-bbb03d20`;
three seed_unsorted rows gone from the Denmark page.

Not landed on main yet (the curator is away; the branch carries it — see
the handoff). Stage A code is ready (`--no-self-union`, P1 / P2 / P5,
6 tests); stage B runs next from the stage-N commit.

## Stage B — results (2026-10-23, from `cb36693`)

`absorb --apply --no-self-union` over all entities from the committed
stage-N state; merger dry-run first (seed ↔ seed_unified consistent).

- **8 052 of 13 880 finals change; no coin gone or new.** Per field
  (removed / added; foundation | promoted): `sources` 503/86 | 2 490/70;
  `catalog` 680/59 | 316/101; `mint` 52/0 | 96/14; readings ~55 | 0;
  `ruler` – | 1 294/1 277 (stage N already settled the Danish forms — what
  is left is the German-states English form «John Frederick (Johann
  Friedrich)» → the class's «Johann Friedrich», and the like);
  `verification_note` 621/523 | 5 648/5 648 (the September Danish backfill
  lives on the finals only); `mintmaster` – | 226/3; `nominal` – | 88/88;
  flags: `mint_verified` – | 156/156 (true → false: absorb's P8
  sources-imply-mint rule flipped the stored final each run and the skeleton
  does not carry the flip), `metal_verified` 20 | 51, `diameter_mm_verified`
  30 | 76, `year_verified` 18/23 | 176/5; V1 foundations lose their
  bootstrap-era scalars where no member gives them: `metal` 111, `nominal` /
  `year_*` 110, inscriptions ~100, `fineness_verified` 121, `mint_verified`
  123, `verified` 115; `year_ranges` foundation 44 removed / **544 added**
  (the classes carry years the V1 curator's range did not — review).
- `verify_reflow`: 1 420 loss lines, 997 moved, 2 494 coins; `trace_coin
  diff`: 5 066 seeds on a final with fewer sources, 0 lost finals, 0
  reclassified. `candidates.json` has every value (seed-keyed).
- **Transfer paths with the switch:** fold 25 / purge 9 / guard 9 as before;
  the 9 + 1 guard re-adds have NO live class and come back as stored
  (reported by the new counter) — these are the curated shells / V1-direct
  entries the guard exists for.
- **Fixed point:** a second run reproduces every coin byte-for-byte as a
  SET; `danish_realm.yml` alone differs in ENTRY ORDER (the fold drops 25
  entries in run 1 and 22 in run 2 and re-appends them). Pre-existing: the
  fold / guard cycle fires every run; content is stable. Noted, not fixed
  here. A key-order regression (the skeleton lost the stored key order and
  moved `nominal` / `ruler` below `id`) was fixed before this run.
- **Render:** munzfuss 125 of 146 pages, danskmoent 101 of 105 — the
  `(?)` marker flips and citation counts reach most tables; read per
  category in stage C, not per page.

## Stage B (run 4) + stage C — results (2026-10-23, from `ff62927` + P8 fix)

Two switch fixes after run 2 / 3: the HEAD class is the first member (28
nominals / 6 rulers on two-class finals came from the wrong class), and
absorb's in-place normalisation of a final (`_normalise_final_entry`:
nominal adoption / hygiene, mint split and spelling, catalogue, flag rules)
runs on the rebuilt entry too. Run 4: **7 994 finals change, 0 coins gone or
new; fixed point as coin sets** (danish_realm entry order still shifts by
the fold / re-append cycle). Removed values classified without the git
route (`classify_self_union_diff.py --no-history`):

| bucket | values | what it is | next |
|---|---|---|---|
| D-promoted-class-wins | 7 709 | a promoted final's frozen scalar / flag where its class now says otherwise: `verification_note` 5 557 (which member's boilerplate), `ruler` 1 285 — **«Christian 4» → «Christian IV.» 220, «Frederik 3» → «Frederik III.» 175 … i.e. finals the June passes missed now get the canonical form from stage N**; `mintmaster` 225 (mint names in the mintmaster field: «Trankebar» 74, «Lübeck» 27 — class has none); `mint_verified` 156 true→false (the 2026-10-06 `_members_decline` guard, correct); `nominal` 53 («1 Ducat» vs class «1 Ducat (3.5)», «1 Thaler» vs «1 Thaler = 36 Grote» — the class's form needs the writer's splitter, D3) | accept as the class's; list the 53 nominals for the curator |
| R (foundation) | ~1 600 | V1 foundation data no class carries: `catalog` 375, `sources` 278, `metal` 108, years 87, inscriptions 90+91, flags ~330 — the V1 curator's record | → **D1 V1 seed** (dry run: 676 entries, 14 entities, `build_v1_seed.py`) |
| R (promoted) | ~300 | `sources` 97, `catalog` 67, `mint` 37 («Christiania?», «Ulæselig møntmestermærke») with no attesting class and no curator layer | curator review, or the git route (slow pass) |
| S-moved | 1 494 | attested by ANOTHER final's class: `sources` 835 + 96, `catalog` 208 + 265, `mint` 36 + 10, `year_ranges` 44 | stale — removal list |
| R-orphan | 1 390 | only a class with no final attests it (1 387 on `c-afd707d6` / `c-bbb03d20`: the KMM korshvid under excluded `kmk-642893`) | curator: exclusion or merge |
| D-foundation | 637 | `verification_note` 523 (V1 curator prose), years 20, flags ~50 | carry on foundations (skeleton gains `verification_note`, inscriptions, years for `origin: foundation`), or V1 seed |
| S-relabel | 128 | same url, older ref text | stale |
| S-recorded | 106 | named in `_recorded_removals` / `_retracted_refs` | stale, already agreed |
| R-twin | 96 | home only in `seed_unsorted` | curator (merge candidates) |
| H | 89 | the 43 head-departed finals (Hede sub-letter split) | `v2-merge-coins`, per case |
| H-stale-v1-twin | 70 | 3 memberless V1 foundations whose own id is a seed living in a class homed on another final (`dk-tid-70750` → `c-e40c23a1` royal_holstein) | fold / delete |
| FLAG | 38 | class-attested yet removed: single-page-url relabels the dedup keeps under the other ref, two-class scalars, Oldenburg English rulers | inspect one by one |

Skeleton refinement that follows from D-foundation: a V1 foundation keeps
`verification_note`, `inscription_obv/rev` and its years as its own (they
are the V1 curator's), which empties most of that bucket without a seed.

## Stage C, second pass — curator decisions and harvest coverage (2026-10-23)

Curator: **D1 deferred — V1 is not touched**; the expectation is that the
harvests made after V1 cover the V1 data in full. And: merge / no_merge
decisions bind. Measured:

- **Decisions as evidence.** Every `merges` / `no_merges` entry (all
  entities + `_cross_entity`), members expanded as the merger expands them.
  20 moved values sit across a curator **no_merge** (the separation is
  deliberate — stale, confirmed); 1 moved value sits across a curator
  **merge** (`dk-tid-163034`'s ucoin citation lives on a final whose seeds
  the curator joined with this one — the pipeline did not apply it; review).
- **Harvest coverage of V1 foundation data** (`_loosely_covered`: same url
  under another ref, same catalogue number in another register form /
  sub-variant, same reading under another label, a year inside the class's
  range): of the foundation values the rebuild removes and no class attests
  exactly, 3 are covered loosely, **437 are not** (`catalog` 269, `sources`
  168 — on foundations that HAVE classes), and **103 sit on foundations with
  no class at all**.
- **The 110 memberless foundations** (`audit_memberless_foundations.py`,
  against HEAD): **78 are V1 twins of a harvested seed** (`hs-ikmk-NNN` ↔
  `ikmk-NNN`, `dk-tid-NNN` ↔ ucoin; the seed's class has its OWN promoted
  final — the coin renders twice; 1 006 removed values belong to these
  twins, bucket H-stale-v1-twin); **13 have a same-entity class sharing a
  type-level catalogue number** (km-104-hede-56b → Hede 56a `c-5d564c17`,
  km-395-1 → Hede 23ab, km-750-1 → Hede f7h1a, km-760 → Hede f7h8, …; absorb's
  self-foundation fold had skipped several of them as «curator classification
  clash» — the join is a merge decision + a classification call, not a V1
  seed); 3 have a candidate in another entity (km-733 → `c-58969558`
  danish_realm, km-695 → f6h26a, km-683-1 → Bruun 8026); **16 have no
  harvested counterpart** (10 without a catalogue number, 6 without a
  candidate — the genuinely V1-only coins, e.g. the five Frederik VI
  Rigsbanktegn `hede-18…22`, `hede-134b`, `dk-tid-79158`).

So the harvests do cover the memberless coins in 94 of 110 cases — through a
twin or a catalogue tie — and the 437 + 103 uncovered VALUES are mostly the
V1 curator's own citations (coinsbook, NGC price guide, Bruun lots as
`bruun_lot_no`) and catalogue registers the harvests never carry (`others:
Brekke# 31–36`, `bruun_collection_id`). Those stay the curator's call
(stage E), unless a V1 seed is revisited later.

**Bucket totals, this pass:** D-promoted 7 709 · S-moved 1 437 (+20 no_merge)
· R-orphan 1 390 · H-stale-v1-twin 1 006 · D-foundation 637 · R 440 ·
R-v1-uncovered 437 · S-relabel 128 · S-recorded 106 · R-v1-memberless 103 ·
R-twin 96 · H 89 · S-covered 39 · FLAG 38 · S-v1-covered 3 ·
R-merge-decision-not-applied 1.

## The whole chain, from the committed state (2026-10-23) — verdict

Curator question: is the difference huge because not everything was
applied, or is it the real difference to work with? Measured with
`scripts/run_v2_pipeline.sh --apply --skip-build` (merge → absorb → §9a thin
→ classify → relink), twice each, from the committed data:

- **Control (today's absorb, self-union on): ZERO change** after pass 1 and
  pass 2. HEAD is the pipeline's fixed point — there is nothing left to
  apply; thinning, classification and relink add nothing.
- **With the self-union off (`ABSORB_NO_SELF_UNION=1`): exactly the stage-B
  run-4 table** — 7 994 finals, same values field by field; the other
  steps change nothing on top of absorb. Fixed point as coin sets
  (danish_realm entry order only).

**So the difference is real, and it is not huge where it matters.** Of the
7 994 finals:

| what changed on the final | finals | nature |
|---|---|---|
| only the derived `verification_note` text (which member's boilerplate) | 5 241 | derived; the class's choice is as good as the frozen one |
| derived text + verification flags, nothing else | 5 505 (incl. the row above) | derived |
| `ruler` form, no data change | 1 200 | 1 199 of the 1 292 ruler pairs are the canonical Danish-king form reaching finals the June passes missed — a stage-N improvement, not a loss |
| **substantive data or scalar changes** | **1 289** | the working set |

The 1 289: `sources` removed on 800 finals (2 993 values), `catalog` on 447
(986), `mint` on 140 (148), readings on ~40, `year_ranges` on 12; scalars —
`mintmaster` 227 (mint names in the wrong field), `nominal` 59, V1
foundations losing `metal` 111 / years 110 / inscriptions 102 (mostly the
78 V1 twins and the 16 V1-only coins). By entity: danish_realm 438,
schauenburg_pinneberg 133, royal_holstein 119, herzogtum_braunschweig_
lueneburg 117, danish_norway 104, gottorp_duchy 90, danish_india 74.
Classified in `self_union_removals_review.md`: S (stale) 1 714 values,
H / H-stale-v1-twin 1 095, R 2 466 + R-orphan 1 390, D 8 346, FLAG 38.

## «Not everything applied» — the search, and switch run 3 (2026-10-23)

Curator: the flag case shows the rebuild had not applied everything that
forms a final; look for more. Method: every place absorb reads the STORED
final — directly (`final_entry.get`: holds, id, composed_of, a held
`year_label` only) or as `members[0]` (`_take_first_non_none`, the year
union, the mint-flag guard) — and every field the later passes read
(P8, fraction inference, assignments, guards). Each read that is neither
member data nor a curator decision is state the self-union used to carry.
Found and fixed in the switch, with tests (13):

| carried now | why it is the final's own, not a member's |
|---|---|
| `year_is_reign_span` (all finals) | absorb's own bookkeeping; the reign-span override recognises a placeholder by it |
| `*_verified` on a foundation | the V1 curator's claims |
| every explicit `*_verified: false` (all finals) | a claim of non-attestation no member can supply; the schema default is true, so dropping it upgrades the value silently (§4); a member that attests still wins through the OR-merge |
| `fraction` (all finals) | never seed data: absorb's inference or the curator; inference re-runs and corrects legacy shapes |
| `inscription_obv/rev`, `weight_rough_label`, `verification_note`, `year_first/last/ranges/label` on a foundation | V1 curator prose and years, read from `members[0]`; the same set `_MIGRATION_PRESERVED_FIELDS` carries on a purge |

Deliberately NOT carried: a foundation's `sources`, `catalog`, readings,
`mint`, `metal` — source data the harvests are expected to cover (curator
2026-10-23); and the P3 residue — values once migrated from purged V1
foundations onto their hosts (`mintmaster: «Trankebar»` ×74, inscriptions
and flags on promoted finals) — which only the self-union kept alive;
`note` among them IS carried.

**Switch run 3 (full chain, `8264777`):** 7 665 finals change (from
7 994), 0 gone / new, fixed point as coin sets; substantive 1 269.
Marks: Check 10 clean, `*_alts` and reading marks identical to HEAD.
Notes: 27 on Nobelfod / Guldgyldenfod coins and 2 383 elsewhere — all
identical (curator 2026-10-23: the Nobelfod / Guldgyldenfod notes are
verified and never go on a removal list). Flags left: promoted
`mint_verified` true→false 156, `diameter_mm_verified` 63, `metal_verified`
43, `weight_rough_verified` 39, `fineness_verified` 16 — the class's claim
under the 2026-10-06 `_members_decline` rule; foundation `mint_verified`
true→false 40 — their V1 `mint` (no class) is gone and the empty-mint rule
resets the flag; `year_verified` 7. Buckets: D-promoted 7 484, S-moved
1 429 (+20 no_merge), R-orphan 1 390, R-v1-uncovered 437, H-stale-v1-twin
268 (the twins' own-record values now stay: 1 006 → 268), R 195, S-relabel
128, S-recorded 106, R-v1-memberless 103, R-twin 96, H 88, S-covered 39,
D-foundation 37, FLAG 25.

## Curator decisions without a surface — `audit_final_edit_survival.py` (2026-10-23)

Every decision surface the pipeline applies was checked on the switch
output against HEAD and reproduces exactly: exclusions (511 coins — 8
prøvemønter, 193 undocumented stubs, 39 off-strikes, 45 exonumia, 6
counterfeits — and 291 KMM specimens: 0 violations), merges / no_merges /
year_demote (`seed_unified` byte-identical after the merger re-run),
absorb's own matching and folds (`composed_of` identical on all 13 880),
classifications and promotions (fuss / phase / kind identical, 0 coins gone
or new), recorded removals (688 field removals: 682 clean, 2 present on
HEAD already), retractions (0 citations left), seed-level errata / holds /
marks (Check 10), final-level holds (carried).

What no surface covers is an edit made on a final by hand. The new tool
walks every final-only commit (298 since the V2 bootstrap) and reports
what a rebuild undoes in both directions — an added value HEAD still holds
that the rebuild lacks, a deleted value absent at HEAD that the rebuild
brings back — attributed to its commit. Totals: 209 493 edited values kept,
3 217 added-then-undone, 70 deleted-then-back; 59 commits concerned. Most
of the 3 217 are pipeline outputs or the known R-v1 / D buckets (the 758
promotions' boilerplate `verification_note` 683, the pending drain 310, the
V1 restores 213 + 69 + 56 + 24, the Danish note backfill 78 + 19). The
genuine per-coin curator decisions the rebuild undoes are few and concrete:

| commit | decision | undone | surface it needs |
|---|---|---|---|
| `baa587f`, `edf779c`, `9a3a0e4`, `eefddf5` | Guldgyldenfod nominals: «1 Rhinsk Gylden» → «1 Goldgulden» (c4h29, f2h3, f2h7g, f2h6), «1 Gulden» → «1 Ungersk Gylden» (numista 428864), «1 Gold Gulden» (bruun-4057), «8 Skilling» (f6h31), c9h1a «2 Christian D'or» / «Christian VIII.» | class form comes back | `_curation_holds: {nominal}` on the final, or the writer's nominal synonyms |
| `0aa8b69` (18), `24b8855` (5) | Sieg / Schou numbers moved to an edition register (`sieg_hede1971`), Aagaard refs consolidated | the class's `sieg: 116` etc. come back beside | the edition split belongs in the writer / `catalog_codes` (stage N, catalogue) |
| `7e95732`, `a777b9a` (7) | annotated kings «Frederick III (Frederik III)», «Frederick I (Friedrich I)», «Frederick VI of Denmark (…)», and the KMM typos «Frederikg 4», «Frederik VVI» | source form comes back | extend `canonical_ruler_display` to the annotated Danish-king forms (June pass A); the two typos → KMM builder errata |
| `d410c68` | c4h144a year 1629 after the Schou-58 split; kmk-158132 ruler | class years come back | hold on `year_*`, or the split as a merge decision |
| `95f4d35`, `fc5a619`, `a2e1952`, `69255e4`, `26c903d`, `e07029d`, `efbc228`, `15e398c` | over-merge residue removed by hand (c5h56 Bruun lot 1122, c7h13a NumisMaster MC_65502 / MC_145357, f3h68a KM 261, c7h7 Bruun lot 17138, km-104-hede-56b Bruun 5607 …) | the class still carries it, so it comes back | the residue lives in the CLASS: a merge decision (split) or seed errata; a ledger entry alone is not applied by absorb — proposal: absorb applies `kind: field` removals from `_recorded_removals` at enrichment, then a recorded hand deletion reproduces itself |
| `1a2e482`, `aab9d06`, `8266c1e`, `ace1c6a`, `58f1a4b` | curator-added citations on finals (KMM 137163 / 156724 / 156783 by merge, Stack's Bowers auction link on km-a47, Numista 420365, Bruun 7656) | not on any class | the KMM ones are merge decisions whose seeds should be in the class — check why not; the rest are V1-style curator citations (R-v1) |

Totals for the curator: ~25 commits, ~120 values. The rest of the undone
values are the buckets already on the review.

## `main` vs the rebuild — decision groups (2026-10-23)

Curator: compare what the rebuild produces here with the finals on the main
branch (its local commits included), together with the hand-edit findings;
analyse and group, then walk the groups and fix the finals' legal form —
useful values get a hold or the like so they survive, and the difference of
that branch from this one is declared garbage on that branch. **Only the
finals the Denmark page renders count** (curator, same day): the entities in
`data/v2/locations/denmark.yml::consumes_entities` — danish_realm,
danish_norway, royal_holstein, royal_slesvig, gottorp_duchy, sonderburg_duchy,
norburg_plon_duchy, glucksburg_duchy, christian_ii_supporters,
christian_ii_reconquest, norby_gotland; the other entities are unprocessed
and their state does not matter.

**Base.** `main` is `de956d6` exactly: no commits past the branch point, the
main checkout's `data/v2` byte-identical to it (checked as files). This branch
adds one data commit over it, stage N (`9b603b5`, canonical Danish kings in
every seed + re-flow), so «main vs rebuild» = «HEAD vs rebuild» + the stage N
delta. The delta is 1 194 ruler forms on the finals and ONE class change:
«Hans?» «1 Hvid(?)» (`unified-kmk-317652`, three KMM records) became «Hans»
with `ruler_verified: false`, which the matcher may no longer treat as a
disagreement (§4), so it joined the documented Hvid class (`c-bbb03d20`,
46 members, luebischer_muenzfuss) — the one coin «gone».

**Tool.** `scripts/maintenance/group_rebuild_diff.py` takes the per-value diff
(`final_diff_candidates.py --base main`), the evidence buckets
(`classify_self_union_diff.py --base main --no-history`) and the hand-edit
audit (`audit_final_edit_survival.py --json`) and sorts every value into a
decision group; `--location denmark` keeps the page's entities; every row
carries the hand-edit commit(s) that put or took the value. Report:
`docs/plans/main_vs_rebuild_groups.md` (counts, per entity, per field, the
legal form proposed per group, full lists for the C / E groups, the
per-commit landing table). The join covers all 3 217 undone additions and 42
of the 70 undone deletions (the other 28 are the «added» partners of rows
counted on the removed side). Whole corpus for reference: 11 895 values on
7 666 finals (A 6 825 · B 3 587 · C 197 · D 1 172 · E 114).

Denmark page — 4 970 values on 2 020 finals, 1 coin gone, 0 new:

| class | meaning | values | finals |
|---|---|---|---|
| A | nothing to decide (gain or same value in another form) | 1 336 | 1 293 |
| B | garbage on main — the self-union kept it alive | 2 601 | 571 |
| C | keep — needs a surface | 158 | 115 |
| D | V1 record not carried — deferred («v1 поки не чіпаємо») | 773 | 398 |
| E | review | 102 | 59 |

Groups, in the order the curator can walk them:

- **A1** 29 notes gain `da` from the class; **A2** 1 194 canonical rulers;
  **A4** 107 relabels; **A5** 6 pure gains.
- **B1** 1 390 citations on 7 finals are the KMM undocumented stubs the
  curator EXCLUDED on 2026-10-16/20 (`undocumented_stub`, scope member:
  kmk-642162 ×725 urls, 395587, 186398, 642893 …) — all 502 classes that
  reach no final are explained by an exclusion; main still shows their
  citations on the Numista / Galster Hvid finals only because of the
  self-union. **B2** 785 values of members now in another final; **B3** 42
  recorded removals; **B4** 15 place names in `mintmaster`; **B5** 40 covered
  in another form; **B6** 214 `*_verified` true → the class's false; **B8**
  23 Bruun anchor specimens (the final still cites Bruun); **B9** 92
  template-for-template notes (absorb's «Hede seed: … pending» boilerplate
  vs the class's source template — the 2026-09 Danish backfill landed on the
  boilerplate, the class template has its own `da`).
- **C0** 48 values / 26 finals from the hand-edit commits (table per commit
  in the report: a2e1952 over-merge split residue 11, 11f2f2a gap-fill,
  51ff425 ucoin readings on dk-tid-70750/1, 69255e4 fold 5, 24b8855
  Aagaard 4, 26c903d / d410c68 / fc5a619 3 each, …); **C1** 34 nominal
  pairs (writer normalisation or hold — several class forms are junk:
  «1 Ducat (3.5)»); **C2** 7 ruler regressions («Frederick III (Frederik
  III)», «Frederikg 4», «Frederik VVI»); **C3** 14 finals lose their ruler
  outright (NGC / Bruun / KMM singletons whose builder sets none); **C4** 5
  notes lose `da`; **C5** 5 curated note texts (Nobelfod fineness notes,
  c3bd650 / 7a831dc); **C6** 6 real mintmaster names; **C7** 39 hand-deleted
  values that come back from the class (0aa8b69 Sieg registers 18, 7e95732 /
  a777b9a annotated kings 7, edf779c 5, baa587f 4 …).
- **D1** 117 values on 51 V1 twins; **D2** 132 on 20 memberless foundations;
  **D3** 341 V1 sources / catalog on seeded foundations; **D4** 13 own-record
  readings; **D5** 109 V1 citations restored onto promoted hosts (restore-v1
  2026-05-27: old `catalogue/pieces` urls, bare «Numista» / «ucoin», NGC
  price guide, «KM-DK#»); **D6** 61 V1 values migrated onto promoted hosts
  (inscriptions, mint, metal). **Visible:** 42 finals lose `metal` with
  nothing in its place (D2 20, D6 18, D1 3, D4 1) — the empty metal column
  is the one D consequence a reader sees.
- **E1** 14 rulers where the class names another person («Adolf» → «Johann
  Adolf», «Hans» → «Alexander», «Frederik III» → «Christian August» …);
  **E2** 71 values on 31 head-departed finals; **E3** 10
  own-attested-yet-removed; **E4** 6 residual; **E5** the stage-N
  auto-merge.

Next: walk the groups with the curator — B is the removal list (stage E),
C gets its surfaces (stage D), D needs the one decision on `metal` / `mint`
for foundations, E is per case.

## Group C — the surface for each value (2026-10-23, Denmark page)

Curator: walk the C groups and decide the surface for each. Every row was
traced to its seed, its class, the final that holds it now, the exclusions
and the decisions (`C_facts.py` in the session scratchpad). What a final
can carry under the switch: a field in `_curation_holds` travels with its
`_verified` companion and wins as a scalar (nominal, ruler, mintmaster,
verification_note) or is unioned as a list (sources, catalog) — a hold
KEEPS a value, it never removes one that a class still carries.

### C0 — hand edits (48 rows / 26 finals): what is left after the facts

| case | fact | surface |
|---|---|---|
| `c-551b645c` (Hede c4h144a) loses its years | the hold names `year_ranges` only; the stored final has no `year_ranges` key (single year), so the skeleton carries nothing and the year-hold path reads None | **switch defect — fix**: a hold on any `year_*` carries the whole year family (`year_first/last/label/ranges`); 14 finals in scope hold years, this is the only one without the family |
| `km-a47-chr-iv-1608` Stack's Bowers auction link (8266c1e) | no seed carries the url | `_curation_holds: {sources: …}` on the final (kept and unioned) |
| `c-2a9ecadd` (c7h13a) Bruun anchor lot 11295 / page 147 / part III | the Part III specimen is `dk-bruun-7928`, IN the class, cited in `sources`; the class anchor is now 7940 (lot 1155) | B8 — nothing lost; the anchor rule can be fixed later |
| `c-2a9ecadd` ucoin 79169 + NumisMaster MC_65502 | both sit in `c-9a93ce8c` (NGC 1050294, danish_realm, seed_unsorted) — the same 1 Speciedaler 1795-1801 | **decision**: cross-entity merge of `c-9a93ce8c` into c7h13a (`_cross_entity.yml`), or no_merge |
| `c-2a9ecadd` MC_145357 | a no_merge decision sends it to `c-b20deed6` | B — garbage on main |
| `c-131a7eb9` (c4h38 ½ Dukat 1647) Bruun anchor 5814 / lot 1046 | `dk-bruun-5814` now sits with Hede c4h40 (`c-360d09ec`, also ½ Dukat 1647); the class keeps 5815 | **decision**: is Bruun 5814 c4h38 or c4h40 (merge-candidate table), else B8 |
| `km-577-1-fr-v-1755` Bruun 7656 (typo fix 58f1a4b) | 7656 sits with Hede f5h40a whose final is the V1 twin `dk-tid-78763` | D1 — two V1 foundations of one coin; the fold decision |
| `km-104-hede-56b` Bruun 5607 | 5607 sits with Hede c4h56a (`c-5d564c17`) | D1 — V1 twin |
| `dk-tid-70750/1` ucoin readings | V1 twins (H-stale-v1-twin) | D1 |
| `dk-tid-130240` cites Hede c9h1 (784179d) | the coin is Christian VIII 2 D'Or 1841-47 (Hede c8h1); the rebuild cites c8h1 | B — the hand citation was wrong |
| Aagaard# ×3, Harck-29.1 (V1 foundations' `others`) | V1 catalogue refs the harvests do not carry | D3 — the foundation-catalog decision (or `catalog` holds) |
| `km-105` others «KM# 73», «Numista N#308517» | duplicates of `km` / `sources` | B |
| `km-733-chr-v-1842` mint Altona | foundation mint not carried | D4 |
| `c-43d7dead` NumisMaster MC_110722 | the merger places it with Hede nf3h21 | B2 unless the curator disagrees with the class |
| relabels (KMM 137163 / 156724 / 156783, Numista 420365, f5h37b, c4h25, ucoin 163663, Numista 308517) | same url, the class's ref text; the hand refs' «(Inv. …, Schou N)» annotations go | A4 |
| mintmaster «the elder» → «the Elder», «Jacob Schwieger» → «… (IS)» | class richer | A |
| `km-105` Numista 301630 (old url) | no seed | D5 |

### C1 — nominal (34)

- **Dual-denomination forms from the class (11)** — «⅛ Speciedaler = 12
  Skilling», «16 Skilling = 1 Mark», «¼ Ducat (3 Mark)», «½ Kurant Dukat
  (1 Rixdaler)», «1 Rigsdaler Courant (6 Mark Rejsedaler)», «1 Hvid = 4
  Pennings», «Gros = 9 Pennings», «1 Sterling = 3 Pennings», «1 Reisedaler =
  6 Mark», «1/24 Specie, 2½ schilling», «6 Pfennig, Sechsling». The writer
  keeps a dual equivalence on purpose (`split_nominal_annotations` leaves
  «X = Y» and «(N denom)», §9.5); the hand forms were simplifications.
  Nothing to decide unless one separator is wanted («X / Y» — 72 Numista
  «=» seeds in scope; then a writer rule).
- **Head-class choice (5)** — «1 Speciedaler» → «1 Taler» ×2 (the final's
  id is the IKMK class while its label names Hede nf3h8/nf3h33; four other
  classes say Speciedaler), «(?)» ×2 (a nominal-less KMM head), «1
  Sechsling» → «1 Søsling lybsk». **Switch fix**: the head class is the one
  the final's `label` names, else the highest-authority class; «(?)» / None
  never wins a scalar. Same fix removes most of B9.
- **Curator forms (7)** — «1 Goldgulden» ×5 (Hede «Rhinsk Gylden», Bruun
  «Gold Gulden», Numista «Gulden», NumisMaster «Guilder»; curator baa587f /
  eefddf5), «1 Ungersk Gylden» (Galster «Ungersk gylden», KMM «Guldgylden»
  / «Ungarsk dukat»; 9a3a0e4), «2 Christian d’Or» (typography). Surface:
  `_curation_holds: {nominal: <reason>}` on the 7 finals now; a writer
  synonym («Rhinsk Gylden» → «Goldgulden») if the family grows.
- **Class wins (5)** — «5 Ducat» → «½ Portugaløser» ×2, «20 Ducat» → «2
  Portugaløser» (NGC, the Portugaløser rule), «2 Dukat» → «3 Dukat» (Hede
  c5h43), «1 Landskrone» → «1 Søsling» (KMM 591617). A.
- **Writer strip rule (1)** — «1½ Gulden (1.5)»: Numista's «(N)» suffix, 9
  seeds in scope («¼ Ducat (0.875)», «1 Goldgulden (1.5)»). Writer.
- **Per case (3)** — «8 Rigsbankskilling» vs Hede «8 Skilling» (f6h31;
  Bruun / Numista / NGC say Rigsbankskilling — hold, or a Hede-level
  erratum); «½ Sølvgylden» (KMM, Galster «Halv Sølvgylden») vs Numista «½
  Gulden» (authority picks Numista — hold if the Danish name is wanted);
  «5 Skilling» vs KMM «0,5 Skilling» (kmk-326593, 1751-1762 — which is
  right?).

### C2 — ruler regressions (7)

103 Numista seeds in scope carry annotated forms («Frederick III (Frederik
III)», «Frederick I (Friedrich I)», «Frederick VI of Denmark (Friedrich VI
von Dänemark)») that `_KING_DISPLAY_RE` does not match; they surface on a
final only where Numista is the sole class (5). **Surface**: extend
`canonical_ruler_display` — strip « of Denmark / of Norway», take the
parenthesised alternative when it is the Danish form — and re-run the seed
migration (stage N, pass 2). The two KMM typos («Frederikg 4» kmk-349954,
«Frederik VVI» kmk-309754; the only ones in the KMM seeds) need an erratum
— a KMM builder table keyed by record id, or `_source_errata` on the seed —
which needs the curator's yes (§4).

### C3 — ruler lost (14)

Classes made only of NGC / NumisMaster records (`ruler: None` — the NGC
page and listing carry no ruler; 611 + 528 such seeds in danish_realm, 268
+ 252 in danish_norway). The finals' rulers came from the June gap-fill /
V1. **Surface options**: (a) a writer rule for Danish-crown entities —
when every year of the record falls inside one reign, `ruler` = that king
(canonical) with `ruler_verified: false` (inferred from the date, not read;
renders «(?)»); transition years stay None; (b) holds on the 14 finals.
(a) covers the ~1 700 seeds and every future harvest; (b) covers these 14.

### C4 — `da` lost (5)

Seven seeds (3 Bruun, 3 KMM, 1 Numista) still carry the pre-`da` builder
note; every other seed in scope has `da`. **Surface**: re-generate the
note on those seeds (builder output, not curated) — no decision.

### C5 — curated notes (5)

Nobelfod / Guldgyldenfod fineness notes («Finheden er ikke attesteret på
stykket; …», «Finheden .770 = den kanoniske finhed …») on `c-3fc323e5`,
`c-59881f83`, `c-621e8b09`, `c-bc790ea1`, `c-f9c15578` (c3bd650, 7a831dc).
**Surface**: `_curation_holds: {verification_note: …}` on the 5 finals.

### C6 — mintmaster (6)

«Christian Wineke, the Elder» (c5h56, c5h58), «lensmand Søren Norby»
(Galster f1g-67), «Ole Varberg» (f6h17): no seed carries them — holds (4).
«Hans Schierven Knoph (HSK)» vs Bruun 7752 «Hans Schievern Knoph» (a
letter swap in one Bruun record wins by id order) and «Johan Friedrich
Freund (IFF)» vs «… Freund» (two Bruun records, initials present / absent):
**surface** either an erratum on dk-bruun-7752 + a hold, or a mintmaster
alias table in the writer (name ↔ initials, the stage N «mint / mintmaster»
item) that settles both and the next ones.

### C7 — hand deletions that return (39)

- rulers (7) → C2; «Christian 4» ×2 are A2 (both finals are «Christian IV.»
  on the rebuild — a join artefact in the report).
- nominals (7) → the C1 holds.
- catalog (24): 18 are Sieg / Schou numbers Hede 1971 prints, which the
  Hede builder emits under `sieg` / `schou` and the June edit moved to
  `sieg_hede1971` / `schou_hede1971`; the merger now lists both editions
  under `sieg` («['100', '116']» = Bruun's modern number beside Hede's).
  **Surface**: the Hede builder writes `sieg_hede1971` (and
  `schou_hede1971` for a Hede range such as «3-4», «10-12») — a stage N
  catalogue rule; no per-coin decision. `c-af6febe0` sieg 108 is the same
  case; km-15 Aagaard is list-form now (A).
- `km-105` ucoin 163663 returns because the merger keeps `dk-tid-163663` in
  the c5h120 class; the June edit called it foreign — **decision**: a
  no_merge [dk-tid-163663, dk-hede-c5h120], or accept.

### Decisions asked

1. C1 curator forms: holds on the 7 finals (Goldgulden ×5, Ungersk Gylden,
   Christian d’Or) — yes / writer synonym instead.
2. C1 dual-denomination forms: keep the class form (writer rule as is) or
   one canonical separator.
3. C1 per case: «8 Rigsbankskilling», «½ Sølvgylden», «0,5 Skilling».
4. C2: the two KMM typo errata.
5. C3: writer rule (a) with `ruler_verified: false`, or holds (b).
6. C5 / C6: the 5 note holds and the 4 mintmaster holds; errata vs alias
   table for Knoph / Freund.
7. C0: cross-entity merge of `c-9a93ce8c` into c7h13a; Bruun 5814 — c4h38
   or c4h40; no_merge for ucoin 163663 on c5h120.
8. C7: Hede builder → `sieg_hede1971` / `schou_hede1971`.

No decision needed (switch defects, done next): the year-family hold, the
head-class choice + «(?)» rule, the `da` re-generation, the «(N)» strip.

### Switch run 6 — the four defects fixed (2026-10-23, `9e35959` … `da6e9e3`)

Fixed with tests: a hold on any `year_*` carries the year family (c4h144a
keeps 1629); the head class is the class the final's `label` names (exact
or its sub-letter class), then by authority, then the final's own id — an
IKMK class no longer outranks the Hede class of `unified-dk-hede-nf3h8`;
a placeholder «(?)» never wins a scalar when another class has a value,
and stays only when no class has one (the schema requires `nominal`; run 4
lost it on two `_unclassified` finals); the writer strips Numista's
bare-number value tail («1½ Gulden (1.5)», 44 seeds re-written in place).
Full chain twice from the committed state: 0 coins gone / new, 7 664
finals change against HEAD, marks Check 10 clean, both sites build;
danish_realm still differs between the two passes by entry order only.

Denmark page against `main`: 4 954 values on 2 019 finals — A 1 336 ·
B 2 590 · C 150 · D 773 · E 105 (was 4 970 / A 1 336 · B 2 601 · C 158 ·
D 773 · E 102). C1 29 (the «1 Taler» pair, the two «(?)» and the «(1.5)»
are gone), B9 82 (the Hede-headed multi-class finals keep absorb's
boilerplate's head now; the rest are single-class finals whose own
template replaces the boilerplate). The decisions asked above stand.

## Empty duplicates — memberless finals of the Denmark page (2026-10-23)

`scripts/maintenance/find_empty_duplicates.py [main] [out.json]`. A final with
no member after the rebuild keeps only its skeleton. It is an EMPTY DUPLICATE
when every value it had on `main` (source URLs, catalogue values, readings,
metal) sits on another final of the rebuild (the host: found by a specific
URL — one shared by ≤4 finals — or by Bruun-collection / Numista number).
Hede-1971 keys count as covered by the host's `sieg` / `schou`. Mint,
mintmaster and nominal are reported, never decisive. Curator: an empty
duplicate's disappearance is fine once its data is proven to live elsewhere;
collect them, do not walk them one by one.

23 memberless finals on the page.

**Empty duplicates — candidates to mark «disappearance OK» (8)**

| final | coin | host |
|---|---|---|
| danish_realm dk-tid-70750 | 3 Rigsbankskilling 1842 | royal_holstein c-e40c23a1 |
| danish_realm dk-tid-70751 | 3 Rigsbankskilling 1842 | royal_holstein c-d3ce70e2 |
| danish_realm dk-tid-79158 | ½ Speciedaler 1769 | royal_holstein c-44a9c52f |
| danish_realm km-104-hede-56b-chr-iv-1627 | 2 Speciedaler 1624–1634 | c-5d564c17, km-x035-chr-iv-1647 |
| danish_realm km-577-1-fr-v-1755 | ½ Skilling 1751–1762 | dk-tid-78763, royal_holstein c-44a9c52f |
| royal_holstein km-760-fr-vi-1854 | 1 Rigsdaler Rigsmønt 1854 | c-5cab1a08 |
| danish_realm km-797-1-chr-ix-1875 | 1 Krone 1875 | c-dbaa3e31, km-797-2-chr-ix-1898 — only «metal gold» differs; both hosts silver |
| royal_holstein km-90-fr-iii-dk-1658 | 1 Sechsling 1658–1660 | c-1ca3c112, c-3774a0e1 — only «metal billon» differs; hosts silver |

**A host exists, but values on `main` are on no other final (8)** — values
V1 carried that no seed and no other final has:

| final | values found nowhere else |
|---|---|
| hede-18-fr-v-1749 (2 Ducat 1749) | Bruun 7670 |
| hede-18-fr-vi-1814 (16 Skilling Rigsbanktegn 1814) | metal silver; its only URL-host dk-tid-79558 is a 12 Skilling copper — host suspect |
| km-750-1-fr-vii-1850 (2 Frederik d'Or) | Bruun 8203 |
| gottorp km-188-karl-fr-1705-v1 (1 Dukat 1705) | Bruun lot 14528 |
| royal_holstein km-733-chr-v-1842 | NGC page duid-1238262 (the seed carries duid-1238261) |
| royal_holstein km-683-1-fr-vi-1813 | Heritage + Stack's auction URLs, Bruun 8025 (a pattern in the lot cache), KM 683.2 |
| royal_holstein km-695-fr-vi-1820 | Heritage + Stack's auction URLs, Bruun lot 8110, Sieg 30 |
| royal_holstein km-721-chr-v-1841 | infinitycoins.com URL |

**No host at all — the coin itself exists only as this record (7)**:
hede-134b-chr-v-1677 (4 Skilling 1677–1678, lead, Bruun 6905),
hede-19-fr-vi-1813 / hede-20-fr-vi-1813 / hede-21-fr-vi-1815 /
hede-22-fr-vi-1815 (12 / 6 / 4 / 3 Skilling Rigsbanktegn, Bruun 8006 / 8007 /
8023 / 8024), km-395-1-chr-v-1688 (2 Ducats 1688, Bruun 7081, KM 395.1),
gottorp km-x009-fr-iv-1701 (4 Schilling 1701–1702, numisbids lot 1676). None
of these Bruun numbers is in the Bruun lot cache, in any seed or in any
other final. Removing the shell removes the coin from the page.

**Done 2026-10-23 (curator «так»):** the 8 empty duplicates are recorded in `data/v2/_recorded_removals.yml` as `kind: empty_duplicate` (keyed by final id, with hosts). Absorb drops such a final only while it has no live member and every host is a final; verify_reflow excuses it on the same condition. Re-run on danish_realm + royal_holstein removed exactly these 8 and changed nothing else.
