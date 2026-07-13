---
name: merge-candidate-table
description: >-
  Build a field-by-field comparison table between a coin RECORD under
  examination and its merge CANDIDATE(s), for reviewing a proposed merge BEFORE
  executing it. Clearly separates the record (📍) from the candidate(s) (🎯),
  marks every field match / missing / conflict, names the KEY catalogue
  identifier that justifies (or refutes) the merge per §9.4, and lists source
  links for both sides. Use when deciding whether a seed_unsorted /
  under-documented coin is the same as an existing final, or when comparing any
  two coin records before a merge — the read-only evidence step that feeds a
  curator verdict, then hands off to `v2-merge-coins` for execution. Trigger
  phrases: "порівняй ці монети", "побудуй таблицю порівняння", "таблиця
  мердж-кандидатів", "record vs merge-candidate", "compare coin records", "is
  this the same coin as", "дай таблицю по цих записах".
---

# merge-candidate-table — record vs merge-candidate comparison

**READ-ONLY.** This skill produces a comparison table + links for the curator to
review a proposed merge. It never edits data. Execution is `v2-merge-coins`
(same-entity / cross-entity merge_decisions); this is the evidence that precedes
that verdict. Read CLAUDE.md §9.4 (index-graph: same coin iff a catalogue base
unifies), §9a (multi-specimen), §0z (reader roles — this table is role-2, for the
user) first.

## When to use

- A `seed_unsorted` or under-documented coin might be the same as an existing
  classified final → show the evidence before merging.
- The user asks «is X the same coin as Y?» / «порівняй ці записи».
- Any pre-merge review where the curator needs to SEE, field by field, what
  matches and what doesn't — especially when the §9.4 graph-gate warns «no shared
  base» and the call rests on a specific catalogue key.

## The two roles — NEVER blur them

Every coin in the table is exactly one of:

- **📍 RECORD** — the coin under examination (the one you're deciding the fate
  of). Usually a `seed_unsorted` / sparse source record (a lone KMM object, a
  bare Numista type, an un-classified galster/bruun seed).
- **🎯 CANDIDATE** — an EXISTING classified final you're proposing to merge the
  record INTO. It is the richer, already-placed coin.

Mark them with the 📍 / 🎯 glyphs in the header row AND in the links block. If a
reader can't tell in one second which coin is being judged and which is the
target, the table has failed its job. When there are several candidates, give
each its own 🎯 column (or its own table).

## Step 1 — gather the data (both sides), from the SOURCE, verbatim (§0b)

**Record (📍)** — open the actual source, don't trust the rendered seed:
- KMM (`kmk-NNNNNN`): `scripts/cache/kmk/<id>.json` → `authority`, `nominal`
  (verbatim — «2 Ungarsk gylden» / «Dobbelt …»), `typeNumber` (the Schou/Hede
  tag), `creationEvents[].yearFrom`, `materials`, `measurements`,
  `drawingExists`, `objectIdentification`.
- Numista / NumisMaster / danskmoent: the parsed cache or the page itself.
- The V2 seed carries the normalised nominal + catalog — use it for the
  project-side view, but cite the cache for the verbatim.

**Candidate (🎯)** — the existing final's structured fields:
```
python3 -c "import yaml; d=yaml.safe_load(open('data/v2/final/<entity>.yml'));
[print(c.get('id'), c.get('nominal'), c.get('ruler'), c.get('year_label'),
 c.get('mint'), c.get('catalog'), [s.get('url') for s in (c.get('sources') or [])])
 for c in d['coins'] if c.get('id')=='<candidate-id>']"
```
Pull: `nominal`, `ruler`, `year_label`, `mint`, `catalog` (hede / schou / sieg /
km / fr — list-form), `fineness`, `weight_rough_g`, and every `sources[].url`.

Confirm the record's home entity + the candidate's entity — if they differ, the
merge is **cross-entity** (`_cross_entity.yml`), flag it in the verdict line.

## Step 2 — the table

One row per comparison field; two value columns (📍 record, 🎯 candidate); a
match column. Standard field order (drop rows that are empty on BOTH sides):

| Поле | 📍 ЗАПИС `<record-id>` (<source>) | 🎯 КАНДИДАТ `<cand-id>` (<type>) | збіг |
|---|---|---|---|
| Номінал | verbatim record nominal | candidate nominal | ✅/⬜/❌ |
| Правитель | ruler | ruler | … |
| **Каталог-ключ** (Schou / Hede / KM) | the record's index | the candidate's index | ✅ **← the load-bearing row** |
| Рік | year or «— нема» | year_label | … |
| Мінт | mint or — | mint | … |
| Вага / проба | weight / fineness or — | weight / fineness | … |
| Інші індекси (Hede/Sieg/KM/Fr) | — (record poorer) | full list | … |

**Match markers:**
- **✅ match** — the two values agree. Reserve **bold + a «← ключ» note** for the
  ONE catalogue index that *uniquely identifies the type* (Schou N, KM N, Hede
  N) — that row is why the merge is legitimate (§9.4). A shared Schou/KM/Hede
  base is the merge's backbone; nominal + ruler alone are NOT (that's the
  over-merge trap).
- **⬜ missing** — present on one side, blank on the other. This is NOT a
  disqualifier: it just means the record is poorer (typical for sparse KMM
  stubs). State «запис без року / лише Schou» in the note — it explains WHY the
  merge still holds (the record is a thin attestation of the same type).
- **❌ conflict** — both sides carry the field and they genuinely disagree on a
  *verified* value (different KM base that no catalogue unifies, different metal,
  fineness off > ~2 %). One real ❌ on a load-bearing field KILLS the merge — it
  means distinct types (§9.4) or a different coin. Surface it, don't bury it.

Sub-index nuance (§9.4): a value INSIDE a range/list counts as ✅, not ❌ —
«Schou 3» ∈ «Schou 3-4» (Hede 8B) or ∈ a candidate's `schou: [3, 7, 10-11]` is a
match on the sub-variant, not a conflict. Say so («3 ∈ …; Hede 8B = Schou 3-4»).

Close the table with a one-line verdict: what the load-bearing match is, why the
⬜ rows don't disqualify, whether it's same-entity or cross-entity, and what the
merge ADDS (usually: the KMM/Numista specimen + its citation, §9a).

## Step 3 — the links block (record vs candidate, explicitly separated)

Always two clearly-labelled groups. Give the record its own source; give the
candidate ALL its source URLs (danskmoent Hede page, Bruun PDF, NumisMaster,
Numista) — those let the user open both and eyeball the coins.

```
🔗 Запис (📍): [KMM 137159](https://samlinger.natmus.dk/KMM/object/137159)
🔗 Кандидат 🎯 `km-46` (Hede 18): [danskmoent c4h18](https://www.danskmoent.dk/chr/c4h18.htm) ·
   [Bruun Part I, lot 1020](<pdf-url>) · [NumisMaster MC_65617](https://numismaster.com/MC_65617)
```

URL patterns: KMM `samlinger.natmus.dk/KMM/object/<id>` · danskmoent Hede
`danskmoent.dk/chr/c4hNN.htm` (Chr IV) / `/fr/…` (F.II/III) / `/norge/…` (NO) ·
Numista `en.numista.com/<nid>` · NumisMaster `numismaster.com/MC_<n>`.

## Worked example (the one the user approved, 2026-07-13)

📍 `kmk-137159` (KMM, «2 Ungarsk gylden», Schou 2, Chr IV, no year/weight) vs
🎯 `km-46` (Hede 18 = 2 Ungersk Gylden 1608, København, Schou 2, Sieg 141, KM 46,
Fr 36, .972, 6.98 g):

| Поле | 📍 kmk-137159 | 🎯 km-46 (Hede 18) | збіг |
|---|---|---|---|
| Номінал | 2 Ungarsk gylden («Dobbelt») | 2 Ungersk Gylden | ✅ |
| Правитель | Christian IV | Christian IV | ✅ |
| **Schou** | **2** | **2** | ✅ **← унікальний ключ** |
| Рік | — нема | 1608 | ⬜ запис без року |
| Мінт | — | København | ⬜ |
| Вага / проба | — / — | 6,94-6,98 g / .972 | ⬜ |
| Hede / Sieg / KM / Fr | — (лише Schou) | 18 / 141 / 46 / 36 | ⬜ |

Verdict: no ❌; the load-bearing **Schou 2** uniquely = the 2-Ungersk 1608 (Hede
18); the ⬜ rows just mean the KMM record is a thin attestation. Same-entity
(danish_realm). Merge adds the KMM specimen (§9a). → hand off to `v2-merge-coins`.

## Hard rules

- 📍 vs 🎯 must be unambiguous in the header AND the links. Never present a
  candidate as if it were a source of the record (a comparison peer ≠ a source).
- The verdict rests on a **load-bearing catalogue key** (§9.4), never on
  nominal+ruler+year alone — call that key out in bold.
- ⬜ (missing on the sparse side) never disqualifies; only a real ❌ on a verified
  field does. Don't let a poorer record read as a mismatch.
- Cite the SOURCE verbatim for the record (§0b) — open the cache/page, don't
  paraphrase the normalised seed.
- This skill STOPS at the table + verdict. It does not merge. Route execution to
  `v2-merge-coins` (and note same-entity vs cross-entity there).
