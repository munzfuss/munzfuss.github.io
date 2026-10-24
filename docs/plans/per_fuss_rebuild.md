# Per-Fuß rebuild: review finals one standard at a time, ship them to main by scope

Branch `rebuild-from-members`. Curator direction 2026-10-24. Scope: only the
entities of the Denmark page (`data/v2/locations/denmark.yml::consumes_entities`,
the page on danskmoent.github.io).

## Order of work (curator 2026-10-24)

1. **Review here first.** The finals of each named Fuß are reviewed on THIS
   branch, against the full rebuild (`ABSORB_NO_SELF_UNION=1`), so the review
   work stays on this branch. A separate branch for shipping comes only after.
2. Fuß order: `nobel_fod` (Nobelfod) → `rhinsk_gylden_fod` (Guldgyldenfod) →
   `luebischer_muenzfuss` (Lybsk møntfod); the next ones are chosen after these.
3. Then Fuß by Fuß: a Fuß reviewed here is carried into a NEW branch (cut
   from main) with the switch scoped to the reviewed Fuß and the scope recorded
   in the repository (curator 2026-10-24: «потстопово розбирати файнали тут і
   зливати це в нову гілку»). main gets that branch only when the curator says so.

| Fuß | finals on the Denmark page (main = here, 2026-10-24) | entities |
|---|---|---|
| nobel_fod | 7 | danish_realm 7 |
| rhinsk_gylden_fod | 20 | danish_realm 9, royal_slesvig 5, gottorp_duchy 3, sonderburg_duchy 2, danish_norway 1 |
| luebischer_muenzfuss | 28 | danish_realm 15, danish_norway 13 |

## State on 2026-10-24

- Every INPUT is committed on the branch: code, tests, skills, seeds,
  merge/classification decisions, `_recorded_removals.yml`. main has not moved
  since the merge base `de956d6`; the branch is 48 commits ahead.
- The DERIVED data (final, seed_unified, class_registry, classification
  decisions) is the uncommitted full rebuild of the Denmark page entities
  (`ABSORB_NO_SELF_UNION=1 scripts/run_v2_page.sh denmark --apply --twice`,
  fixed point). It is reproducible from the committed inputs.
- `verify_reflow.py` against HEAD: 2551 loss lines (454 FIELD EMPTIED,
  426 CATALOG SHRANK, 251 LIST SHRANK, 2 SEED DECLASSIFIED — one of them the
  Lybsk final `c-bbb03d20`, KMM 317652/3/4). That is the review volume; the
  hook blocks committing it as a whole, which is why it goes Fuß by Fuß.

## The switch (to build after the reviews)

- Today `SELF_UNION_ENABLED` is one global in absorb, read at four sites
  (`_own` ~672, the P1 enrich ~3631, the folded-self restore ~3738, the P5
  verbatim re-add ~4093). Replace with a per-final predicate `_rebuilds(fc)`:
  true when the whole set is on (`--no-self-union` / `ABSORB_NO_SELF_UNION=1`,
  unchanged), or when the final's Fuß is in the scope
  (`--rebuild-fuss a,b` / `ABSORB_REBUILD_FUSS=a,b`).
- A final's Fuß for the scope = the union of its stored `fuss` at HEAD and the
  fuss its seeds' classification decisions assign — so a final the rebuild
  declassifies (`c-bbb03d20`), or a coin a decision moves into the Fuß, stays
  in scope.
- The scope is recorded in the repository: `data/v2/_rebuild_scope.yml`
  (`fuss: [...]`). absorb reads it when no flag/env is given, so any run on main
  reproduces the same state; flag/env override it (the full set stays available
  here). That file is what tells main which Fuß are rebuilt.
- `scripts/run_v2_page.sh` passes the scope on.
- `verify_reflow.py --scope`: losses inside the scope are accepted only through
  `_recorded_removals.yml` (curator «так»); losses outside the scope (the
  background effect of the new code — Bruun «H-N»/Harck, ruler form in the
  merger, ruler from years) are listed separately.
- Tests: a scoped final equals the full rebuild; an out-of-scope final equals
  the self-union run; the existing `--no-self-union` tests pass unchanged.

## Shipping into the new branch (after the switch)

1. Snapshot the full rebuild (scratchpad, not the repo) as the reference.
2. Derived data back to HEAD; scoped run with the reviewed Fuß list; the
   scoped finals must equal the snapshot; the rest is the code's background,
   measured here for the first time.
3. Commit the scoped derived data with `_rebuild_scope.yml`; Check 7 passes
   once in-scope removals are recorded and out-of-scope losses are resolved.
4. Into the new branch (and later main, on the curator's word) by merge; conflicts in derived files are resolved by re-running the
   chain, never by text merge.

## Risks

- Background of the new code on unreviewed Fuß: class moves make stale-purge
  drop a departed seed's exclusive values; `verify_reflow` catches it.
- `rhinsk_gylden_fod` spans royal_slesvig / gottorp / sonderburg, which also
  render on the Schleswig-Holstein page (munzfuss) — out of focus, but it
  changes there too.
- A merge / no_merge for one Fuß can take a member out of a class of another;
  re-check after each decision.
- Deferred, outside the three Fuß: the KMM «24 Skilling» Hede Norge 2 class
  `c-691aa453` broke up after merge `1b8c617`.

## Review log

(one line per final: id · verdict · surface used · commit)

### nobel_fod

Rebuild vs main, 2026-10-24 (record-diff-table). `note` is identical on all
seven; every difference is in fields no page renders.

- `c-6e11667e` 1 Nobel 1532 · `verification_note` gone (Numista template) · accepted · `1d41e14`
- `c-fabbb039` 1 Nobel 1524-1525 · `verification_note` gone (Galster template) · accepted · `1d41e14`
- `c-ba11e1f9` 1 Nobel 1524 (Galster 68, no specimen known) · `verification_note` gone (Galster template); `metal_verified` absent = schema default true; `weight_rough_verified` false from the Galster seed (no weight on either side) · accepted · `1d41e14`
- `c-3fc323e5` 1 Nobel 1516, 1518 (Christian II) · `verification_note` gone, incl. the curator sentence on the .979 anchor (`40c5dd8`); the .979 itself stays, inferred, `fineness_verified: false`, under its hold · accepted · `1d41e14`
- `c-bc790ea1` 1 Nobel 1496, 1502 · `verification_note` gone, incl. the curator sentence «fineness of the pre-1514 Nobler not given in the sources» (`c3bd650`); the hold keeping an empty fineness removed (no member gives a fineness, so it was a no-op) · accepted · `1d41e14` + hold removal in the uncommitted rebuild
- `c-f9c15578` 2 Nobel 1502 · as `c-bc790ea1` · accepted
- `c-59881f83` 3 Nobel 1496 · as `c-bc790ea1` · accepted

Curator decisions behind these lines (2026-10-24):
- The .979 on the Nobels was never a source value: no member seed (Galster,
  Numista, Bruun, KMM) carries a fineness. It was an inferred anchor
  (`40c5dd8`), removed from the three Hans Nobels in `c3bd650`. The holds that
  kept the empty field are dropped: the rebuild leaves it empty by itself.
- `verification_note` is not rendered anywhere. The builders' per-source
  template is removed from the builders and the seeds (`1d41e14`); only notes
  about the record stay (Hede index stubs, NGC norm notes, Metallanalyser).
  For the switch: on main, finals outside the scope keep their stored note
  (self-union) — only the rebuilt Fuß lose it.
- Open, outside this review: CLAUDE.md §4 still says `verified: false` comes
  with a `verification_note` that renders as the «(?)» tooltip; the build
  never did that.
- The hold removals live only in the uncommitted rebuild; they are recorded
  here so the shipping run in the new branch repeats them.
