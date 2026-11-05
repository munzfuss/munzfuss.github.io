---
name: coin-note
description: >-
  Write, change, shorten or move a coin's Note — the Note column of a coin table — in
  `data/v2/notes/<entity>.yml`, keyed by seed id (V2_DECISIONS D54), then re-flow and check it
  on the page. Encodes what belongs in a Note and what does not: only what the sources say
  about THIS coin (legend, images, likeness to other types, the coin's own history and
  standing), datings in the year tooltip, facts about the town / period / standard in the
  period description, no reference to another coin's Note. Trigger phrases: «напиши Note»,
  «перепиши / скороти нотатку», «додай до Note монети», «збери кандидатів на Note»,
  «write the coin note», «move this Note». Not for the year tooltip (`tooltip-text` /
  attributions), not for the period or Fuß prose (`fuss-description`), not for a citation by
  itself (`cite-source`).
---

# coin-note — the Note column, one coin at a time

The Note is curator prose about ONE coin. It has one home: `data/v2/notes/<entity>.yml`
(D54, curator 2026-11-05). Absorb sets the `note` of the final whose seeds include the
entry's `seed`, and the file wins over whatever the final carried.

Never write a Note on a seed (`note` there only gap-fills a final that has none — an
edit never reaches the page once the final has a Note) and never on a final (finals are
never edited by hand; the next absorb may keep or drop the edit unpredictably).

## What goes into a Note (curator 2026-11-05)

| Into the Note | Elsewhere |
|---|---|
| the legend(s) on the coin, read from a source scan, with variants | — |
| the images (arms, cross, mark, leaves, stars …) | — |
| likeness to another type, as a source states it (Lübeck / Hamburg types, a common type of a recess) | — |
| the denomination names different works give this coin | — |
| this coin's standing: commonest type, last of a series, first after X, number of dies, a hoard count for this type | — |
| — | **datings** and the argument behind them → year tooltip (`attributions/<entity>.yml` note, `tooltip-text` skill) |
| — | facts about the town's / ruler's coin **in general** (a ban on «Flensborg money», a parity of «Flensborg and Lübeck Witten», a rate of «Holsten ghelt») → the period description (`data/v2/locations/<loc>.yml` phases) |
| — | the standard's parameters, its origin and end → the card / Fuß description |
| — | a whole set of hoards or the extent of a coinage, when it does not single out this coin → leave out unless the curator asks |

Test for every sentence: *is the subject this coin, or a set the coin belongs to?* If the
source speaks of a set (all coins of a town, all Witten of the period), the sentence is
not this coin's — move it up a level or drop it.

Further rules:
- **Repeat, never point.** A fact shared by two coins is written in full in both Notes;
  never «as in Jesse 339» or «see the Witten above». A reader looking up one coin reads
  only its row.
- **Short.** Three or four sentences is the norm. A Note that has grown into a paragraph
  of argument has absorbed something that belongs in the tooltip or the period text.
- **No invention (§0)**, hedges attributed to their source (§2a: «за Nöbbe, імовірно»).
- **Every claim cited** with `<sup>[ref:KEY]</sup>`; keys made with the `cite-source`
  skill (one passage = one key, verbatim quote, page, translation, archive copy).
- **Legends from the scan**, not from OCR: open the page image (`pdftoppm -r 150 -f N -l N`)
  and read the letters; OCR of medieval Lombardic legends is unreliable.
- **Four languages together** (de / en / uk / da), same claims and same keys in each.
  uk: «данськ-», never «датськ-»; city names in the form of the power ruling them then.
- Proper names of instruments, standards and nominals per CLAUDE.md §2 / i18n.

## Procedure

1. **Find the seed.** The Note is keyed by a seed id that is in the coin's final:
   ```bash
   .venv/bin/python - <<'EOF'
   import sys; sys.path.insert(0,'scripts')
   from lib.v2_index import V2Index
   ix = V2Index.load(); print(ix.final_members['<final-id>'])
   EOF
   ```
   Prefer the seed of the source the Note mostly rests on (a literature seed such as
   `lindahl-1955-…`); any member works, but only ONE per final — two entries landing on
   one final stop absorb.
2. **Check what is there.** The final's current `note`, and whether the file already has an
   entry for any of its seeds. An old Note that lives only on the final (no entry) moves
   into the file when you edit it — copy it in, then change it.
3. **Collect** the source passages (local corpus first: `scripts/kb/kb.py search …`),
   sort each sentence by the table above, and show the curator the draft (uk) with sources
   when the change is more than a wording fix.
4. **Keys**: create or reuse them with `cite-source`; drop a key from `refs_pool.yml` only
   when nothing cites it any more (`grep -rn "ref:<key>" data/`).
5. **Write** the entry with `yaml_io` so the file stays canonical:
   ```python
   import sys, io; sys.path.insert(0, 'scripts')
   from lib import yaml_io
   from pathlib import Path
   import yaml
   p = Path('data/v2/notes/<entity>.yml')
   doc = yaml.safe_load(p.read_text()) if p.exists() else {'entity': '<entity>', 'notes': []}
   # replace or append {'seed': ..., 'curator': 'Serhii YYYY-MM-DD', 'note': {de, en, uk, da}}
   ```
   New files keep the header comment of the existing ones; check
   `yaml_io.round_trip_residual(p) == 0` and the trailing newline.
6. **Re-flow** the entity in the background — merger, then absorb:
   `merge_seeds_cross_source.py --entity <e> --apply` and
   `absorb_seeds_into_final_v2.py --entity <e> --apply`. Absorb prints
   «⚠ … Note(s) … reached no final» if a seed id is wrong.
7. **Verify**: `verify_reflow.py` (no losses); the final's `note` equals the file's; rebuild
   the site that shows the page (`--site danskmoent` for Denmark) and read the row's text in
   every language (`site-<site>/<lang>/t/<fuss>.html`); `cite_helper.py --page … --section
   fuss-<fuss>` for unresolved keys.
8. **Commit** `data/v2/notes/…`, the re-flowed `seed_unified` / `final`, and `refs_pool.yml`
   if keys changed — explicit pathspec, message from a file, in the background.

## Hard rules

- The Notes file is the only place a Note is written. Seed `note` and final `note` are not
  edited by hand.
- Datings stay out of the Note; general facts stay out of the Note.
- One seed per final in the file; never point from one Note to another.
