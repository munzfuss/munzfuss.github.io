---
name: record-diff-table
description: >-
  Build a DIFFERENCE table between two coin records: four columns — field,
  record A, record B, comment / proposal — one row per field that differs, equal fields
  omitted. Source citations are compared by URL only; the citation label
  (`ref`) is ignored. Works on any two records at any layer and any revision:
  a final on `main` vs the same final in the working tree, a final vs another
  final, a seed vs a final, a seed_unified class vs a final. Use when the
  curator asks what changed in a record, what separates two records, or what
  to do about each difference («побудуй таблицю порівняння», «таблиця
  відмінностей», «порівняй ці записи», «що змінилось у цьому записі», «чим
  відрізняються», «diff these records», «що тут на main і що тут»). READ-ONLY.
  For a merge verdict (are these the same coin?) use `merge-candidate-table`,
  which shows every field and names the load-bearing catalogue key.
---

# record-diff-table — what differs between two records

**READ-ONLY.** Produces a table for the curator (role 2, CLAUDE.md §0z). It
never edits data; a proposal in the comment column is carried out only after
the curator agrees, through the surface that owns it (a `_curation_holds`
entry, `merge_decisions`, `_recorded_removals.yml`, `_source_errata` —
the last only with an explicit «так», §4).

## Shape (curator direction 2026-10-23)

- **Four columns:** поле · A · B · коментар. The field name comes first, the
  two records next, and the last column holds only the judgment or the
  proposal for that row (curator 2026-10-23: a separate field column keeps
  the comment clear).
- **Rows = only what differs.** An equal field is not a row.
- **Bold the differing part.** When only part of a row differs (a list with
  some elements on one side only), those elements are **bold** on the side
  that has them; the shared elements stay plain (curator 2026-10-23). The
  helper does this; keep it when retyping a cell.
- **Sources: the link, not the label.** Two citations with the same URL are
  the same citation, whatever their `ref` text says. A URL present on one
  side only is a row.
- No group letters or internal codes in the table or around it. Say in plain
  words what a row means.

## Procedure

1. **Name the two records.** Spec per side:
   `final:<entity>:<id>[@ref]`, `unified:<entity>:<id>[@ref]`,
   `seed:<seed-id>[@ref]`. No `@ref` = working tree; `@main`, `@HEAD`,
   `@<sha>` = that revision. A seed id is the stable handle (§9b); a final or
   unified id may have been renamed between revisions — if a spec is not
   found at one revision, resolve the seed with `trace_coin.py trace` first.

2. **Run the helper** (it raises on a missing record; never substitute a guess):

   ```bash
   .venv/bin/python .claude/skills/record-diff-table/diff_table.py <A> <B>
   ```

   Options: `--order` also lists lists that differ only in order (hidden by
   default — order carries no meaning in a final), `--ignore note,verification_note`
   skips fields, `--full` disables shortening, `--json` for further processing.
   A field whose shape changes (list → per-volume dict) is one row.

3. **Write the comment column** — replace each mechanical tag
   («лише в A», «лише в B», «відрізняється») with what the row means and,
   where something should happen, the proposal. Before the comment calls a
   value wrong, stale or missing, verify:
   - `trace_coin.py why <seed-id> --field <f>` — a curator decision may
     explain it (§0b-1);
   - the source itself: the seed entry, then `scripts/cache/<source>/…` (the
     cache carries more than the seed — e.g. a Numista record lists every
     catalogue reference and the issuer);
   - for a citation present on one side only: does the URL still exist on the
     other side under another form (old Numista `pieces<N>.html` vs `/<N>`),
     does a seed carry it, did it move to another final.
   A comment that is a hypothesis says so («гіпотеза: … — перевірити …», §0b).

4. **Present** the table in Ukrainian, then one or two sentences: what the
   rows add up to and what decision, if any, is the curator's. Values from
   the data stay verbatim (catalogue numbers, nominals, URLs); a foreign quote
   gets a Ukrainian translation after it.

## Notes

- Several rows often have one cause (a merger rule, a class split). Say it once
  under the table rather than in every row.
- Measurement lists (`weight_rough_g`, `fineness`, `diameter_mm`) are compared
  with their per-source attribution — a reading that moved from one source to
  another is a real difference (§9a).
- Scope: when the work is limited to one page's entities, compare only
  records of those entities (`data/v2/locations/<loc>.yml::consumes_entities`).
