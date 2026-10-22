# Rebuild a final from its members — plan (revision 2)

Branch `rebuild-from-members`, worktree `.claude/worktrees/rebuild-from-members`,
cut from `de956d6`; `scripts/cache` and `.venv` are symlinks into the main
checkout (read-only use). Curator direction 2026-10-22: separate what the
members (plus curator decisions) give from what exists only on the final; sort
the latter into legitimate and stale; make the legitimate part durable; delete
the stale part. Revision 2 (same day) replaces the imitation-based measurement
of revision 1 with the production pipeline itself as the oracle — curator:
«якщо запустити функцію формування файнала на наявних членах, він заново
сформується».

## 0. Goal and definition of done

**Invariant:** `final = f(members, curator decisions)` — nothing a final holds
may exist only because the final held it before.

**Done when**, on the branch rebased onto main:

1. absorb builds every final without the final among its own members
   (the switch below is the default);
2. a re-flow from HEAD changes the corpus by exactly the curator-approved
   removal list — nothing else, field by field;
3. every legitimate value that used to live only on the final has a
   pipeline source (seed / decision / rule) that `trace_coin why` names;
4. a second run is a zero diff (fixed point);
5. the code that only compensated for the self-union is gone.

## 1. Why this method

| Option | What it does | Verdict |
|---|---|---|
| A. Prune | keep the self-union, strip values another final's class attests | symptom only, `sources` + readings only; rejected |
| B. Imitation (revision 1, `lib/final_derivation`) | call a subset of absorb twice, compare | misses matching, normalisation, purges, decisions (9 `metal` mismatches); kept only as a per-value classifier |
| **C. Pipeline as oracle** | switch the self-union off in the real absorb, run it on the worktree, diff against HEAD | complete and exact; the diff is the candidate list and, iterated, the convergence measure |

The worktree exists so that C can run `--apply` freely; the shared tree is
never touched until landing.

## 2. Where a final's stored data re-enters the output (inventory)

Read in `absorb_seeds_into_final_v2.py` at `de956d6`; line numbers approximate.

| # | Path | Line | Fires |
|---|---|---|---|
| P1 | main enrichment `members = [fc] + classes` | ~3366 | every final, every run |
| P7 | inside `_enrich_final_entry`: foundation-immutable fields copied from `fc`; `note` / `verification_note` / inscriptions first-non-None with `fc` first; `label` / `origin` / bookkeeping copied | 577–1310 | with P1 |
| P8 | in-place normalisation of `fc` before enrichment (nominal adoption, mint split, catalogue normalise, flag rules) | ~2540 | every final |
| P2 | `_folded_self`: a folded self-foundation re-enriched from its own stored dict | ~2983, ~3472 | on a fold event |
| P3 | `curator_migrations`: a purged stale foundation's fields / sources carried to its host (`_apply_migrated_merge_fields`, bulk-promote stub) | ~2650–3540 | on a purge event |
| P4 | `cross_carry`: a relocated final's fields gap-filled onto its new host | ~2780 | on a relocation |
| P5 | monotonic guard: a prior final re-added VERBATIM | ~3767–3819 | when a re-run would drop a coin |
| P6 | curated shell kept (`_settle_curated_shell`) | ~3793 | on a superseded shell |

P1 + P7 are the steady-state self-union — the defect. P8 transforms, it does
not carry. P2–P6 are TRANSFER paths: they move a dying final's data onto a
surviving one; they fire on structural events, and in a fixed-point run their
counters are 0. They are measured separately (stage B logs their counters) and
revisited in stage F — once V1 data lives in a seed (stage D) most of P3 / P4
become redundant, because the data travels with its seed.

## 3. Ground rules for every run

- **Baseline is frozen**: the data of `de956d6` on this branch. Before EVERY
  measuring run: `git checkout -- data/v2/final data/v2/classification_decisions
  data/v2/seed_unified data/v2/class_registry` (CLAUDE.md §9b: re-flow from
  HEAD, never over a previous run's output — foundation-immutable fields and
  OR-merged flags otherwise survive and fake the result).
- Long runs (absorb over all entities, both site builds) in the background,
  logs to the scratchpad, no `| tail` on hook-bearing commits.
- Measurement is seed-keyed (`trace_coin snapshot` / `diff`) and at the end of
  the chain (rendered HTML), never by final id alone.
- Nothing from this branch reaches main before stage G.

## Stage A — the switch (code, no data change)

1. absorb: flag `--no-self-union` (and env `ABSORB_NO_SELF_UNION=1` for the
   prune-rerun child). With it, P1 passes `skeleton(fc)` instead of `fc`, both
   as `final_entry` and as `members[0]`. `skeleton` = identity (`id`, `label`,
   `origin`, `composed_of`, `legacy_id`, `class_id`), `fuss` / `phase` /
   `kind`, `_curation_holds` and every held field with its `_verified`
   companion — `lib/final_derivation.skeleton`, already tested.
2. Nothing else changes: matching unified→final, P8, P2–P6, purges, decisions,
   thinning all run as before. The switch isolates P1 + P7.
3. Counters for P2–P6 printed per entity (folded-self restored, migrations
   applied, cross-carry applied, monotonic re-adds, shells kept).
4. Tests: the flag off is byte-identical to today on a fixture; the flag on
   drops a citation no class gives and keeps a held value.
5. Commit on the branch (code only).

## Stage B — first full run and its diff (the candidate list)

1. Reset data (§3). `trace_coin snapshot` → `before`.
2. Build both sites from the baseline into scratch output dirs (HTML
   baseline).
3. `absorb --apply --no-self-union` over all entities (background).
4. Measure:
   - `git diff --stat data/v2/final`, `verify_reflow` (losses = candidates),
     `trace_coin snapshot` → `after`, `trace_coin diff`;
   - both sites rebuilt; per-page HTML diff summary (rows changed, columns
     changed);
   - P2–P6 counters (expected 0 — any non-zero is investigated first).
5. A second run with the flag on, no reset: must be a zero diff (fixed point).
   A non-zero second diff is an idempotence bug, fixed before stage C.
6. Output: `candidates.json` — one row per (final, its seeds, field, value,
   direction removed/added/changed), the seeds being the stable handle (§9b).
   Plus memberless finals (no live class: the whole final is candidate) as
   their own group.
7. Cross-check with the stage-1 audit numbers; a large disagreement is
   explained before going on.

## Stage C — classify the candidates (read-only, evidence only)

Tool `scripts/maintenance/classify_self_union_diff.py` reads `candidates.json`
and attaches evidence per value:

| Evidence | Source |
|---|---|
| another final's class attests it (moved / twin), only an unfinaled class does (orphan), no class does | `lib/class_attestation` |
| first commit the value appeared on this final, and the commit's route | git history of `data/v2/final/<entity>.yml` (seed-keyed blocks; the history scripts of 2026-10-22 turned into a tool) |
| a curator decision names it | `trace_coin why` on the final's seeds: errata, holds, merge / classification decisions, exclusions, `_retracted_refs`, `_recorded_removals`, builder tables |
| the same url under a newer ref text in a member | relabel pairing (`final_derivation.classify`) |

Buckets:

- **S — stale.** Pipeline-route value now attested by another final's class;
  value whose seed is excluded, retracted or gone; the old text of a relabel.
- **L — legitimate.** V1 route (bootstrap `214f991`, restores `e210ed6`,
  `e851d3f`, `10850ab`, `4831c21`) not attested by any class; curator hand
  edit; transfer from a folded / purged final whose seed is still in this
  final's lineage.
- **D — diverged single-valued fields** (ruler spelling, verification note,
  nominal, note, flags): decided by a rule, not per value.
- **R — review.** Twins (home only in `seed_unsorted`), orphans (class with
  no final, e.g. 161 KMM korshvid under excluded `kmk-642893`), V1-restore
  values another final's class also attests (the 44 of 2026-10-22), no
  identifiable route, catalogue / mint values contradicting the class.

Report to the curator: per bucket × field × cause, counts and three examples
each, with sources. The curator decides each R group (→ S or L) and each D
rule. No data changes in this stage.

## Stage D — make the legitimate part derivable (loop)

Each sub-step ends with: reset (§3) → stage B run → the diff must shrink by
exactly the values that sub-step made derivable, and grow by nothing.

- **D1 — the V1 corpus becomes a seed source**, `data/v2/seed/v1/<entity>.yml`.
  A generator writes, per V1 foundation, ONE seed entry carrying its L values
  (scalars, sources, catalogue, years, readings) with per-value provenance
  (`_origin: <commit> <route>`); seed id = the foundation id (`km-…`, `hs-…`,
  stable). Written through `lib/v2_seed_writer.write_v2_seed` (merge-aware,
  CLAUDE.md «Manual-override preservation»). The merger discovers seed dirs
  itself; the seed joins its class by an explicit `merge_decisions` entry
  (members are seed ids), never by matcher luck. Authority: above every
  source for the descriptive scalars the V1 curator chose (`nominal`,
  `ruler`, `mintmaster`, `fraction`, years); measurements union as usual.
  A memberless foundation becomes a singleton class from its V1 seed.
  Gate before the switch: with the V1 seed added and the switch OFF, the
  render is byte-identical (union is idempotent) — this proves the seed
  carries nothing new.
- **D2 — transferred own values** (folds / purges / relocations): where the
  donor's seed is now a member, the value is already derivable; where it is
  not, it becomes a V1-seed value (curator-route) or S (pipeline route), per
  the curator's call in stage C.
- **D3 — rules for D:** ruler spelling (one canonical form, applied in the
  merger; the curator picks the form); `verification_note` generated
  deterministically from the members (rule to agree — e.g. from the
  highest-authority member, or composed per source); nominal / note
  divergences reviewed as a list.
- **D4 — relabel:** the member's current ref text wins; nothing to do beyond
  confirming it renders the same citation.
- **D5 — holds:** already in the skeleton; check every held field survives.

The loop ends when the stage-B diff equals S ∪ (R decided S).

## Stage E — curator approval of the removal list

The remaining diff, grouped (bucket, field, cause) with examples and counts,
goes to the curator. Recording: §9b requires every deliberate removal
recorded for Check 7. Option to agree then: per-value `_recorded_removals`
entries generated from the approved list, or a `verify_reflow`
classification «stale after a seed left» driven by the same evidence
(revision-1 patch `$S/verify_patch.py`), the list itself still approved
group by group. No `--no-verify`.

## Stage F — make it the default, remove the compensations

1. The switch becomes the default; the flag is removed.
2. Remove, each measured by a stage-B run (zero diff expected):
   `_prune_foreign_kmm_citations`; `_surgical_decontaminate`; P3 / P4 where
   the V1 seed now carries the data; P2 / P5 / P6 reviewed one by one (they
   may still be needed for coins whose class vanished).
3. The stage-1 imitation (`audit_final_only`) either becomes a regression
   check (A == B for every final) or is deleted.

## Stage G — landing

1. Rebase onto main. Every data step is a script (V1 seed generator, merge
   decisions, rules), so it is re-run on main's data, then stages B / E
   verification again.
2. Commits (pathspec, `-F`, background): (1) code — switch off by default,
   tools, tests; (2) V1 seed + merge decisions + rules — render
   byte-identical; (3) switch on + re-flow — the approved removals, recorded.
3. Coordinate the `data/v2` write window with the other sessions before the
   merge into main. Never push without «пуш».
4. Rebuild danskmoent; `docs/V2_DECISIONS.md` new D-entry,
   `docs/ARCHITECTURE.md` (absorb no longer self-unions; V1 is a source),
   `docs/handoff.md`, `docs/TODO.md`.

## Curator decision points

| When | Decision |
|---|---|
| after B | nothing — numbers only, unless P2–P6 fire or the second run is not a fixed point |
| after C | each R group → stale or legitimate; the D rules (ruler form, verification-note rule) |
| D1 | V1 as a seed source (recommended) vs an `_own` block on the final |
| E | the final removal list, group by group; the recording mechanism |
| G | the landing window |

## Risks

- **Main moves meanwhile.** Mitigation: every step scripted, re-run on main
  at landing; the rebase is the last step, not the first.
- **V1 seed authority** could override a better source value on a scalar the
  V1 curator never really chose (bootstrap defaults). Stage C separates V1
  values that were curated from bootstrap defaults by route; defaults go to
  S or R, not to the seed.
- **Memberless finals** (~150) are 100 % candidate in stage B and swamp the
  report — reported as their own group.
- **Catalogue merge** (`_deep_merge_catalog`, sub-indices, single-slot
  registers) and year holds are the intricate paths; the stage-B diff is read
  per register.
- **Run time.** Absorb over all entities plus two site builds per iteration;
  all in the background, one git op at a time.

## Stage 1 of revision 1 — results kept for reference (2026-10-22, `de956d6`)

`scripts/lib/final_derivation.py` + `scripts/maintenance/audit_final_only.py`,
tests `tests/test_final_derivation.py` (7). Absorb's own enrichment reproduces
13 871 of 13 880 stored finals (9 differ in `metal`, set outside enrichment).
11 237 finals differ between A (`[fc] + classes`) and B (skeleton + classes)
(values / finals; foundation | promoted):

- own: `sources` 417/283 | 2 438/436; `catalog` 680/298 | 327/155; `mint`
  52/46 | 88/86; `year_ranges` 116/22 | 303/16; V1 scalars (`nominal` 110,
  `ruler` 269, `metal` 111, `issuing_entity` 114, years 110, `fraction` 156,
  `v1_home_location` 687); promoted `mintmaster` 228, `year_verified` 185,
  `note` 749.
- relabel (`sources`): 86/61 | 70/68.
- diverged: `ruler` 256 | 4 292 (spelling «Frederik III.» vs «Frederik 3»),
  `verification_note` 523 | 5 648, `nominal` 126 | 88, `note` 25 | 164,
  flags ~300.
- hidden: `catalog` 59/32 | 101/38 (single-slot registers).

These are the expectation stage B is cross-checked against, not a result.
