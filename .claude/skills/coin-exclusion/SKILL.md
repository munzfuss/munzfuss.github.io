---
name: coin-exclusion
description: Exclude a coin record (or one KMM specimen inside a record) from the render through `data/v2/exclusions/<entity>.yml` — undocumented stubs, worn / fragmented / undeterminable KMM objects, patterns, off-strikes, off-nominal pieces, exonumia, out-of-scope records. Picks the RIGHT block (`exclusions:` for a whole seed, `specimens:` for one KMM object folded into a multi-specimen seed), writes the entry through yaml_io, re-flows, and checks that the coin actually left final. Use for «виключи», «виключи як undocumented stub», «прибери цю монету / цей запис KMM», «це фрагмент / зіпсована монета, виключи», «exclude this coin», «remove from the render». Executable form of PB-12 / CLAUDE.md §9.
---

# coin-exclusion — remove a record from the render, the right way

Rules: CLAUDE.md §9 (what may be excluded), PB-12 (procedure), §9b (seed ids).
Every exclusion needs the curator's word in chat; the reason quotes it.

## The trap this skill exists for

`data/v2/exclusions/<entity>.yml` has TWO blocks that look alike:

| block | key | removes | when |
|---|---|---|---|
| `exclusions:` | `id: <seed id>` (`kmk-310127`) | the whole seed → its final, when the seed is the class's only member or `scope: member` | a record is useless on its own: a lone KMM object, a stub, a pattern |
| `specimens:` | `kmm: <object number>` (`310127`) | ONE KMM object's citation inside a seed that folds several objects | a KMM seed groups 40 objects of one find and only some are bare |

`specimens:` is guarded: a specimen with a weight or a photo is never
stripped, and a coin is never left without a source. So a lone KMM record
written under `specimens:` changes NOTHING — the re-flow runs clean, the
coin stays, and it looks as if the exclusion worked (2026-11-25, five KMM
records; the same mix-up happened before).

**Decide by the seed, not by the source:** `trace_coin.py trace kmk-<n>`.
- the seed id exists (`kmk-<n>` is its own seed) → `exclusions:` with `id: kmk-<n>`;
- the KMM object is one `sources` entry of another seed (`kmk-<m>`, `m ≠ n`)
  → `specimens:` with `kmm: <n>`.

A KMM object number from a URL `samlinger.natmus.dk/KMM/object/<n>` is the
seed id `kmk-<n>` only when the seed builder did not fold it into another;
check with `grep -l "id: kmk-<n>$" data/v2/seed/kmk/*.yml`.

## Procedure

1. **Resolve.** `trace_coin.py trace <seed-id>` for each record: entity,
   class, final, Fuß, number of sources. A class with other members: the
   exclusion takes only this record (`scope: member`); say so to the curator
   if the class would lose its only weight or image.
2. **Read the record** (`scripts/cache/kmk/<n>.json`): inventory number,
   nominal, authority, typeNumber, weight — the reason quotes them.
3. **Write** through `scripts/lib/yaml_io.py` (`load` / `save`, the file
   keeps its residual 0), at the END of the right block:

   ```yaml
   exclusions:
     - id: kmk-310127
       category: undocumented_stub   # pattern · off_strike · off_nominal · exonumia · undocumented_stub · out_of_scope · duplicate_noise
       scope: member
       reason: KMM FP 7234.11, «2 skilling(?)», …; <the curator's ground>. Curator (Serhii) <date>.
       curator: Serhii
       date: '<YYYY-MM-DD>'
   ```

4. **Re-flow** the entity (background): merger `--entity <e> --apply`, absorb
   `--entity <e> --apply`. Absorb must print `curator exclusions: dropped N`
   with N = the number added; `⚠ exclusion id matched nothing` = step 1 wrong.
5. **Verify** — not optional, this is where the trap shows:
   - `trace_coin.py trace <seed-id>` → `final — none —` for each;
   - `verify_reflow.py` → the removals under CURATOR EXCLUSIONS, nothing under LOSSES;
   - `git diff --stat data/v2/final/<entity>.yml` is NOT empty. An empty
     final diff after an exclusion means it did not apply.
6. **Commit** exclusions + seed_unified + final with one pathspec, `data:`
   message naming the records and the ground. Rebuild the page (danskmoent
   in the background) if any of them rendered.

## Not this skill

- Hiding one wrong reading → `reading-marker`; a wrong value → `(!)` / `_source_errata`.
- Two records being one coin → `v2-merge-coins`.
- Stopping a future harvest from bringing the record back → also fix the
  parser / builder filter (PB-12 step 4); the exclusion alone does not.
