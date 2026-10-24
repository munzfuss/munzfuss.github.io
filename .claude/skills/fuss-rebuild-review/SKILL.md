---
name: fuss-rebuild-review
description: >-
  Review one Müntzfuß for the per-Fuß rebuild from members (the switch in
  `data/v2/_rebuild_scope.yml`), or bring a `seed_unsorted` candidate into a
  Fuß that is already reviewed. REVIEW: re-flow the location's entities with
  the Fuß in scope, compare every final of the Fuß with `main` by seed id and
  field by field AND on the rendered page in every language, put the delta to
  the curator, record the decisions, add the Fuß to the scope file, log it in
  docs/plans/per_fuss_rebuild.md and commit. PROMOTE: a coin still in
  seed_unsorted that belongs to a reviewed Fuß — evidence table, curator
  verdict, classification (and merge) decision by seed id, re-flow, the same
  comparison, commit. Use for «розбери стопу», «переходимо до стопи X»,
  «перебудуй стопу з членів», «порівняй стопу з main», «що змінилось у стопі»,
  «додай стопу в список», «переведи цю монету з seed_unsorted у стопу»,
  «знайшли кандидата в стопу». Helper `fuss_compare.py` (data / build-base /
  page).
---

# fuss-rebuild-review — a Fuß rebuilt from members, compared with main

The branch rebuilds the finals of the Fuß listed in `data/v2/_rebuild_scope.yml`
from their members (no self-union with the stored copy); every other final keeps
the self-union. A Fuß enters the list only after its finals were compared with
`main` and the curator accepted every difference. Plan, state and review log:
`docs/plans/per_fuss_rebuild.md`. Rules that bind every step: CLAUDE.md §0b-1
(`trace_coin.py why` before calling a value wrong), §4 (verified flags, errata
only with «так»), §9b (seed ids; verify at the end of the chain against a
committed baseline), the Git-safety protocol (pathspec commits, `-F`,
background), never push, main only on the curator's word.

Helper: `.venv/bin/python .claude/skills/fuss-rebuild-review/fuss_compare.py
{data|build-base|page} …` — writes only under `output/fuss_compare/`.

## Mode REVIEW — one Fuß

1. **Start from HEAD.** The derived data (`final`, `seed_unified`,
   `classification_decisions`, `class_registry`) must equal HEAD; restore any
   changed file with `git restore --source=HEAD -- <path>` first. A run over a
   previous run's output measures nothing (§9b).
2. **Re-flow with the Fuß added**, through the environment, not the file:

   ```bash
   ABSORB_REBUILD_FUSS=<listed Fuß>,<new Fuß> scripts/run_v2_page.sh <location> --apply --twice
   ```

   Background it (~8 min a pass). Read the log: the «Rebuild from members:»
   line must name the intended set; `FIXED POINT` must be printed; the step
   times and the per-step «changed:» lines of pass 2 show which step, if any,
   moved the state a second time.
3. **Data comparison:**

   ```bash
   .venv/bin/python .claude/skills/fuss-rebuild-review/fuss_compare.py data <fuss> [--location <loc>]
   ```

   Read every line. It lists finals present on one side only, per final the
   seeds it composes, every field that differs, sources by URL **and** every
   key that differs on a shared URL (`ref` label, `display`, `type`), and the
   seeds that joined or left the Fuß. Also check that nothing OUTSIDE the
   Fuß moved: `git diff --stat -- data/v2` must touch only the Fuß's entities,
   and a quick per-Fuß count of changed finals vs HEAD must show the new Fuß
   only (the reviewed ones are already at HEAD).
4. **Page comparison**, every language of the site profile:

   ```bash
   .venv/bin/python .claude/skills/fuss-rebuild-review/fuss_compare.py build-base      # once per base SHA, background
   .venv/bin/python scripts/build.py --site danskmoent                                # background
   .venv/bin/python .claude/skills/fuss-rebuild-review/fuss_compare.py page <fuss>
   ```

   Repeat with `--site munzfuss` (and a munzfuss build) when the Fuß has
   entities on a munzfuss page. The coin tables live in `<lang>/t/<fuss>.html`,
   not in `index.html`; a section diff of `index.html` alone shows nothing.
5. **Explain every difference before showing it.** For each row: why it
   changed (verify — the source, the members' values, `trace_coin.py why`),
   whether it is visible on the page, and a proposal. Typical causes found so
   far, each verified:
   - per-source `verification_note` templates gone (`1d41e14`) — data only;
   - a value main carried only through the self-union (a citation of another
     class, a stub the curator excluded, a `*_verified: true` no member
     gives) — the rebuild drops it;
   - a new catalogue index the members now give (Bruun parser: Harck,
     Delzanno, …);
   - the Bruun anchor moving to another cited lot (not a loss, `dc7eb7e`);
   - a citation LABEL changing under the same URL (the hand-written label of
     the final vs the seed's) — visible, and `record-diff-table` does not
     show it;
   - a change visible on ONE language only (the DE ordinal period).
6. **Present to the curator**: the page delta first (per language), then the
   data-only delta, then the open questions — one decision per question, with
   the proposal. Nothing is recorded before the curator's answer.
7. **Record the decisions** through their own surfaces: a removal →
   `_recorded_removals.yml` (only after «так»); a merge / split → the
   `v2-merge-coins` skill; a reading mark → `reading-marker`; a code rule
   (normalisation, guard) → code + test, measured on every source's values.
   A `verify_reflow` block is resolved by a recorded decision or a guard fix
   the curator agreed to — never `--no-verify`.
8. **Enter the Fuß in the scope file** (`fuss:` list,
   `# reviewed <date>`), restore the derived data to HEAD and re-flow WITHOUT
   the environment variable, so the committed state is the one main will
   reproduce from the file. The result must equal step 2's.
9. **Log it** in `docs/plans/per_fuss_rebuild.md` (table row ✅, a section with
   every difference and every curator decision behind it), then commit: code
   first, then the scope file + derived data + plan with one pathspec. Read
   `verify_reflow` in the hook output; confirm with `git log -1`.

## Mode PROMOTE — a seed_unsorted coin into a reviewed Fuß

The coin is in `seed_unsorted` on main as well (seeds are identical), so the
decision travels to main as an input file and the derived data is regenerated
there — safe, provided:

1. **Evidence**: `merge-candidate-table` — the record 📍 against the Fuß's
   finals it might join 🎯, `no_merges` checked first. When it joins no final,
   the table is against the Fuß's grid (Feingewicht Δ, §8a).
2. **Curator verdict** in chat.
3. **Decision by SEED id** (D49 stage 1), in the seed's own entity:
   - a new coin of the Fuß → `classification_decisions/<entity>.yml`
     `assignments:` (`coin_id: <seed id>`, `fuss`, `phase`, `kind`, `reason`
     with the curator and date);
   - joins an existing final → `merge_decisions/<entity>.yml` through
     `v2-merge-coins`, whole class in `members`.
4. **Re-flow from HEAD** with the scope FILE (the Fuß is already listed);
   the switch takes the coin into the rebuild by its decision
   (`_scope_decision_keys`).
5. **Compare** (`data` + `page`) for the Fuß AND for the Fuß the seed came
   from if it left another class: `fuss_compare.py data` lists it under
   LEFT / JOINED. A seed pulled out of a class of an unreviewed Fuß changes
   that Fuß — say so to the curator before committing.
6. **Log** under the Fuß's section of the plan (`promoted <seed> — <reason>`)
   and commit the decision with the derived data.

## Hard rules

- Seed ids only for every before/after statement (§9b); a final id may be
  renamed.
- Never compare against a run over a run; never measure a working tree that
  holds two experiments at once.
- Every page language, every site the Fuß renders on — a DE-only or
  label-only change is still a change.
- A difference is reported with its verified cause or labelled a hypothesis
  with what would settle it (§0b). The helper's output is evidence, not the
  verdict.
- The scope file changes only after the curator accepted the Fuß.
