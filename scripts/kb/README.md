# `scripts/kb/` — knowledge-base search over the harvest cache (pilot)

**Retrieval only.** `kb search` returns ranked, page-anchored passages — work,
PRINTED page where the corpus manifest establishes one, file path and line —
as the first step of the `cite-source` workflow. It never summarises or
answers. A hit is a pointer: the passage is then read in full in the file and
quoted verbatim per CLAUDE.md §5a. No RAG, no LLM synthesis (that would
collide with §0 / §0b and the verbatim-quote discipline).

```bash
.venv/bin/python scripts/kb/kb.py build                    # ~8 s, 10.5k passages
.venv/bin/python scripts/kb/kb.py search "kobbermønt hvider blaffeter"
.venv/bin/python scripts/kb/kb.py search "vardein smeltning" --work schou-1795
.venv/bin/python scripts/kb/kb.py search "sølvgylden" --lang da --limit 20
.venv/bin/python scripts/kb/kb.py search 'NEAR(kroner skiling*, 8)' --fts --work secher-ccd
.venv/bin/python scripts/kb/kb.py offsets wilcke-1950      # re-derive PDF→printed offsets
.venv/bin/python scripts/kb/kb.py refkeys                  # manifest vs refs_pool.yml drift
.venv/bin/python scripts/kb/kb.py extract-htm              # danskmoent .htm → text
.venv/bin/python scripts/kb/measure.py                     # the grep-vs-kb measurement
```

## Parts

| Path | What |
|---|---|
| `scripts/cache/_corpus.yml` | Corpus manifest, in the harvest submodule: one record per work — bibliography, languages, text-layer files and layout, PDF→printed page mapping with the basis it was established on, OCR note, `refs_pool` keys citing it. |
| `scripts/cache/_derived/danskmoent/` | Plain text of every cached danskmoent `.htm` (1029 files), one `.txt` per page, same relative path. Derived, never hand-edited; the `.htm` stays untouched. |
| `kb.py` | Normaliser, page splitter, FTS5 builder, `search`, `offsets`, `refkeys`, `extract-htm`. Stdlib `sqlite3` (FTS5 is compiled in, SQLite 3.53) + PyYAML; no other dependency. |
| `variants.yml` | Editable spelling-variant rules (Mynt/Mønt, Schilling/Skilling, Thaler/Daler, Reichs-/Richs-/Rigs-, ck→k, th→t, dt→t, …). |
| `eval_set.yml`, `measure.py` | The go/no-go measurement. |
| `_index/kb.sqlite` | The index — **gitignored**. |

**Why the index is gitignored, not in the submodule.** It is a pure function
of the manifest, the text layers and `variants.yml`, rebuilt in ~8 s; it is a
48 MB binary that changes wholesale on every rebuild (a new variant rule
re-normalises every row), so committing it would add tens of MB of
undiffable history to the private submodule each time a rule is tuned. The
manifest and the derived danskmoent text, by contrast, are small, diffable
and expensive-to-rediscover, so they live in the submodule.

## Passage unit and page anchoring

| Layout | Unit | Printed page |
|---|---|---|
| `file-per-page` (Secher, Schou) | one PDF page file | offset segments (Secher) / IIIF label (Schou) |
| `markers` (Wilcke 1919, 1950; Denar til daler; Galster 1934, 1973) | text between page markers | offset segments, or the marker's own printed number |
| `formfeed` (Munro, Hauberg, DCH 1904, Jensen, Eriksson, …) | form-feed page | offset segments |
| `section` (Wilcke II 1924) | ~25-line window | the section's printed range only — the HTML has no page breaks |
| `whole` (danskmoent, Bobzin, Mordhorst) | ~30-line window | none — web reproductions; the quote is the locator |

A printed page is reported only where the manifest establishes it; elsewhere
the hit says «pdf N (printed page not established)». Offsets were found with
`kb.py offsets` (a scan of running-head numbers) and recorded with the number
of agreeing pages. Secher was also checked against the 32 page hints in
`refs_pool.yml`: 31 land on the computed page (or the quote runs onto the
next); the 32nd is a finding about the ref, not the offset (see handoff).
Secher Bd 6 has two fascicle wrappers bound in (pdf 178–181, 342–345), so its
offset steps −17 → −21 → −25.

## Normalisation

Applied identically to text and query: NFC; join line-break hyphenation
(«fir-⏎kantede» → «firkantede») and soft hyphens; re-join letter-spaced OCR
(«D e n a r»); lower-case; æ→ae ø→oe å→aa ä→ae ö→oe ü→ue ß→ss ſ→s œ→oe;
vulgar fractions split («14¼» → «14 1/4»); diacritics stripped; then the
`variants.yml` rules (the last one folds «ae» → «e», so modern «afsættelse»
meets old «afsettelse»). Query words of ≥3 letters match as prefixes
(«skiling*» finds Skillinger). A query word is also tried split in two where
both parts are indexed words (`compound_splits`, read from an `fts5vocab`
table): «småmønt» → the phrase «smaa moent», which matches «Smaa-Myndt»;
`--no-split` turns this off. Ranking is BM25; AND first, then OR to fill
the list. `--fts` passes FTS5 syntax through (quotes, `NEAR`, `OR`).

## Measurement — the go/no-go gate

Two sets of passages already quoted in `refs_pool.yml`, sources across the
pilot corpus. For each: a query as a researcher would type it (modern
spelling, concept words — not the quoted string), and the single keyword the
same researcher would grep today. Gold = the passage carrying the quote,
located in the index and checked by a probe word.

- **Set A** (`eval_set.yml`, 22 cases) — written first; its failures
  motivated the round-2 changes (æ/e fold, compound splitting), so on A
  those changes are fitted, not tested.
- **Set B** (`eval_set_b.yml`, 15 cases) — written after round 1 and BEFORE
  round 2, never used to design anything: the held-out check.

Queries were never changed after a run; only gold probes were corrected
where the OCR of the source spells the probe word differently («Grucis»,
«843.75», «slæderjcjjhgod»). «grep: gold hit» = a `grep -rIin -F` line
inside the gold passage — generous for one-file books, where the researcher
still reads every matching line (column «lines / files»).

### Summary

| | grep | kb whole corpus: rank 1 / top 10 / top 50 | kb `--work`: rank 1 / top 10 |
|---|---|---|---|
| A, round 1 | 12/22 | 9 / 14 / 18 | 12 / 19 |
| A, round 2 | 12/22 | 10 / 15 / 20 | 14 / 21 |
| B, before round 2 | 9/15 | 7 / 11 / 15 | 12 / 15 |
| B, round 2 (held out) | 9/15 | 8 / 13 / 15 | 12 / 15 |

Round 1 → table after the «14¼» fraction bug fix (it moved only A14).
Round 2 on the held-out set: whole-corpus top 10 up 11 → 13, within-work
unchanged at 15/15 (already full), two cases one or two ranks lower (B1 4 →
6, B9 18 → 19). Of grep's 16 misses across both sets, kb within the work has
15 in the top 10.

**What the grep misses were** (verified on the page text): line-break
hyphenation («fir-/kantede»), old orthography («rund mynt», «kaabermønt»,
«gangbar mynt», «Vardin», «Richsdaller», «fiereskillingstøcker», «Colnisk
Mark»), OCR damage («jaffngod» read as «slæderjcjjhgod», «Crucis» as
«Grucis») and compounding («Smaa-Myndt»).

**Still failing** — hypotheses, untested: A16 «Goldgulden» vs Middle Low
German «golt gulden» (split gives «gold»+«gylden»; d/t differ); A13 and B3
rank low across the whole corpus because the query words are common —
whole-corpus BM25 is the weak point; restricting to a work fixes most of it.

### Set A, round 2

| # | refs_pool key | query | grep | grep: gold hit | grep: lines / files | kb rank | kb rank (in work) |
|---|---|---|---|---|---|---|---|
| 1 | `secher-ccd-1-174-1563-firkantede-moent` | firkantet mønt vrage | `firkantede` | ❌ | 17 / 7 | 16 | 5 |
| 2 | `secher-ccd-1-359-1567-fald-rund-mynt` | fald rund mønt 3 mark sager | `rund mønt` | ❌ | 31 / 11 | 2 | 1 |
| 3 | `secher-ccd-3-523-1619-kobbermoent` | kobbermønt hvider blaffeter | `kobbermønt` | ❌ | 43 / 11 | 1 | 1 |
| 4 | `secher-ccd-4-138-1625-afsaettelse` | møntens afsættelse sexskilling | `afsættelse` | ❌ | 15 / 14 | 1 | 1 |
| 5 | `secher-ccd-5-143-1643-reces-mynten` | fremmede købmænd gangbar mønt | `gangbar mønt` | ❌ | 20 / 16 | 26 | 8 |
| 6 | `schou-1795-bd1-s82-myndtordning-1671-vardin` | vardein møntmester smeltning prøve | `vardein` | ❌ | 0 / 0 | 18 | 1 |
| 7 | `schou-1795-bd1-s80-forbud-1671-smaamoent` | forbud indførsel småmønt | `småmønt` | ❌ | 43 / 9 | 47 | 1 |
| 8 | `mordhorst-c5mord-reskript-1692-kroner` | reskript 1692 kroner markstykker | `markstykker` | ✅ | 152 / 45 | 1 | 1 |
| 9 | `wilcke-1919-guldriddere-1611` | guldridder karat 1611 | `guldridder` | ✅ | 38 / 19 | 1 | 1 |
| 10 | `wilcke-1919-metzner-1593-bestalling` | Metzner bestalling møntmester 1593 | `Metzner` | ✅ | 24 / 9 | 1 | 1 |
| 11 | `wilcke-1919-flemming-1607-slagskat` | slagskat Flemming gevinst | `slagskat` | ✅ | 107 / 15 | 1 | 1 |
| 12 | `wilcke-1924-kap2-3-gruener-forslag-1642` | Grüner forslag 1642 møntordning 1624 | `Grüner` | ✅ | 42 / 10 | 1 | 1 |
| 13 | `wilcke-1924-kap1-gottorp-1610-muenz-edict` | Gottorp daler 33 skilling lybsk Nabobyerne | `Nabobyer` | ✅ | 4 / 4 | >50 | 2 |
| 14 | `wilcke-1950-flensborg-1547-vaegt` | sølvgylden 14¼ lødig finvægt | `sølvgylden` | ❌ | 123 / 37 | 34 | 9 |
| 15 | `wilcke-1950-sundtold-1550` | sundtold nobel rhinske gylden | `sundtold` | ✅ | 46 / 15 | 2 | 2 |
| 16 | `galster-1934-junge-guldregnskab` | Goldgulden 18 Karat 72 Stück | `Goldgulden` | ❌ | 547 / 20 | >50 | 16 |
| 17 | `jensen-1971-hdy-guldgylden-1624-1633-underloedig` | Lilliendahl underlødig lødighed Lübeck | `Lilliendahl` | ✅ | 21 / 1 | 1 | 1 |
| 18 | `eriksson-2017-hans-skilling-hvid-luebsk` | hvid lübsk witten vikt | `witten` | ✅ | 419 / 46 | 1 | 1 |
| 19 | `gullbekk-2025-haandfaestning-1483-jaffngod` | jævngod mønt Bergen Oslo danske penninge | `jævngod` | ❌ | 6 / 4 | 2 | 1 |
| 20 | `holst-1936-lybsk-myntmark-192-penninger` | lybske myntmark 192 penninger | `192 penninger` | ✅ | 6 / 3 | 1 | 1 |
| 21 | `munro-2009-marc-de-troyes` | marc de Troyes grams | `marc de Troyes` | ✅ | 25 / 8 | 6 | 6 |
| 22 | `galster-nobel-1524-23-karat` | Jørgen Kock nobel 23 karat | `23 karat` | ✅ | 34 / 22 | 4 | 2 |

### Set B (held out), round 2

| # | refs_pool key | query | grep | grep: gold hit | grep: lines / files | kb rank | kb rank (in work) |
|---|---|---|---|---|---|---|---|
| 1 | `secher-ccd-3-487-1618-soelvkrone` | sølvkrone 13¾ lod fint sølv halvanden rigsdaler | `sølvkrone` | ❌ | 22 / 8 | 6 | 1 |
| 2 | `secher-ccd-3-541-1619-rigsdaler-96-sk` | rigsdaler spansk matte otte realer skilling danske | `spansk matte` | ❌ | 1 / 1 | 1 | 1 |
| 3 | `secher-ccd-4-20-1622-tarif` | rosenobel ungersk dukat guldgylden mark danske | `rosenobel` | ✅ | 177 / 60 | 23 | 1 |
| 4 | `secher-ccd-1-210-1564-laan-klippinge` | låne klipping lensmænd rund mønt | `klippinge` | ✅ | 549 / 63 | 4 | 2 |
| 5 | `secher-ccd-3-309-1609-fremmed-smaamoent` | fireskillingstykker søslinger Hildesheim polske dütchen | `fireskillingstykker` | ❌ | 0 / 0 | 1 | 1 |
| 6 | `schou-1795-bd1-s81-myndtordning-1671-guld` | guldmønt dukat 23 karat 67 stykker kølnisk mark | `kølnisk mark` | ❌ | 1 / 1 | 1 | 1 |
| 7 | `schou-1795-bd1-s80-note-regl-1692` | kroner reglement 1692 halvskilling kobber | `halvskilling` | ❌ | 25 / 16 | 3 | 1 |
| 8 | `mordhorst-c5mord-reskript-1692-2-skilling` | toskilling godhed værdi kroner omkostninger | `omkostninger` | ✅ | 92 / 40 | 1 | 1 |
| 9 | `wilcke-1950-moentordning-1541` | møntordning 1541 Crucis 14½ lod | `Crucis` | ❌ | 24 / 5 | 19 | 4 |
| 10 | `wilcke-1950-tillaeg-1544` | guldengroschen 13½ lod 1544 | `Gyldengroschen` | ✅ | 21 / 11 | 1 | 1 |
| 11 | `galster-1934-junge-1545-tilladelse` | Junge tilladelse guldgylden Degener Flensborg | `Degener` | ✅ | 30 / 14 | 1 | 1 |
| 12 | `galster-1934-hertugdoemmer-lybsk-moentfod` | hertugdømmerne lybske møntfod privilegier 1460 | `lybske Møntfod` | ✅ | 2 / 2 | 1 | 1 |
| 13 | `eriksson-2017-hvid-soesling-skilling-penningar` | hvid fire penninge søsling skilling hovedvalør | `huvudvalören` | ✅ | 1 / 1 | 2 | 1 |
| 14 | `holst-norges-mynter-hamar-ingen-mynt` | Hamar biskop Magnus myntbrev Vincents Lunge | `Vincents Lunge` | ✅ | 12 / 5 | 7 | 2 |
| 15 | `wilcke-1919-van-campen-1596` | Geert van Campen møntmester 1596 specier | `van Campen` | ✅ | 7 / 5 | 1 | 1 |

## Out of scope for the pilot

Vector embeddings (e.g. local bge-m3); OCR of the `rigsarkivet/` scans; the
`kb-ingest` / `kb-research` skills and a `source-researcher` agent; Hede and
Bruun (coin records, not prose).
