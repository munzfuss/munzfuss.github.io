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
`variants.yml` rules. Query words of ≥3 letters match as prefixes
(«skiling*» finds Skillinger). Ranking is BM25; AND first, then OR to fill
the list. `--fts` passes FTS5 syntax through (quotes, `NEAR`, `OR`).

## Measurement (2026-10-19) — the go/no-go gate

22 passages already quoted in `refs_pool.yml`, sources across the pilot
corpus. For each: a query as a researcher would type it (modern spelling,
concept words — not the quoted string), and the single keyword the same
researcher would grep today. Gold = the passage carrying the quote, located
in the index and checked by a probe word. Queries written before the first run
and not tuned afterwards. «grep: gold hit» = a `grep -rIin -F` line inside the
gold passage (for one-file books this is generous: the researcher still has to
read every matching line, column «lines / files»).

| # | refs_pool key | query | grep | grep: gold hit | grep: lines / files | kb rank | kb rank (in work) |
|---|---|---|---|---|---|---|---|
| 1 | `secher-ccd-1-174-1563-firkantede-moent` | firkantet mønt vrage | `firkantede` | ❌ | 17 / 7 | 16 | 5 |
| 2 | `secher-ccd-1-359-1567-fald-rund-mynt` | fald rund mønt 3 mark sager | `rund mønt` | ❌ | 31 / 11 | 2 | 1 |
| 3 | `secher-ccd-3-523-1619-kobbermoent` | kobbermønt hvider blaffeter | `kobbermønt` | ❌ | 43 / 11 | 1 | 1 |
| 4 | `secher-ccd-4-138-1625-afsaettelse` | møntens afsættelse sexskilling | `afsættelse` | ❌ | 15 / 14 | >50 | >50 |
| 5 | `secher-ccd-5-143-1643-reces-mynten` | fremmede købmænd gangbar mønt | `gangbar mønt` | ❌ | 20 / 16 | 25 | 8 |
| 6 | `schou-1795-bd1-s82-myndtordning-1671-vardin` | vardein møntmester smeltning prøve | `vardein` | ❌ | 0 / 0 | 18 | 1 |
| 7 | `schou-1795-bd1-s80-forbud-1671-smaamoent` | forbud indførsel småmønt | `småmønt` | ❌ | 43 / 9 | >50 | 34 |
| 8 | `mordhorst-c5mord-reskript-1692-kroner` | reskript 1692 kroner markstykker | `markstykker` | ✅ | 152 / 45 | 1 | 1 |
| 9 | `wilcke-1919-guldriddere-1611` | guldridder karat 1611 | `guldridder` | ✅ | 38 / 19 | 1 | 1 |
| 10 | `wilcke-1919-metzner-1593-bestalling` | Metzner bestalling møntmester 1593 | `Metzner` | ✅ | 24 / 9 | 1 | 1 |
| 11 | `wilcke-1919-flemming-1607-slagskat` | slagskat Flemming gevinst | `slagskat` | ✅ | 107 / 15 | 1 | 1 |
| 12 | `wilcke-1924-kap2-3-gruener-forslag-1642` | Grüner forslag 1642 møntordning 1624 | `Grüner` | ✅ | 42 / 10 | 1 | 1 |
| 13 | `wilcke-1924-kap1-gottorp-1610-muenz-edict` | Gottorp daler 33 skilling lybsk Nabobyerne | `Nabobyer` | ✅ | 4 / 4 | >50 | 2 |
| 14 | `wilcke-1950-flensborg-1547-vaegt` | sølvgylden 14¼ lødig finvægt | `sølvgylden` | ❌ | 123 / 37 | 29 | 7 |
| 15 | `wilcke-1950-sundtold-1550` | sundtold nobel rhinske gylden | `sundtold` | ✅ | 46 / 15 | 2 | 2 |
| 16 | `galster-1934-junge-guldregnskab` | Goldgulden 18 Karat 72 Stück | `Goldgulden` | ❌ | 547 / 20 | >50 | 16 |
| 17 | `jensen-1971-hdy-guldgylden-1624-1633-underloedig` | Lilliendahl underlødig lødighed Lübeck | `Lilliendahl` | ✅ | 21 / 1 | 1 | 1 |
| 18 | `eriksson-2017-hans-skilling-hvid-luebsk` | hvid lübsk witten vikt | `witten` | ✅ | 419 / 46 | 1 | 1 |
| 19 | `gullbekk-2025-haandfaestning-1483-jaffngod` | jævngod mønt Bergen Oslo danske penninge | `jævngod` | ❌ | 6 / 4 | 4 | 1 |
| 20 | `holst-1936-lybsk-myntmark-192-penninger` | lybske myntmark 192 penninger | `192 penninger` | ✅ | 6 / 3 | 1 | 1 |
| 21 | `munro-2009-marc-de-troyes` | marc de Troyes grams | `marc de Troyes` | ✅ | 25 / 8 | 6 | 6 |
| 22 | `galster-nobel-1524-23-karat` | Jørgen Kock nobel 23 karat | `23 karat` | ✅ | 34 / 22 | 4 | 2 |

- grep finds the gold passage in **12/22**.
- kb, whole corpus: rank 1 in 9/22, top 10 in 14/22, top 50 in 18/22.
- kb restricted to the work (`--work`): rank 1 in **12/22**, top 10 in **19/22**.
- Of the 10 grep misses, kb has the passage in the top 10 in 3 (whole
  corpus) / 7 (within the work). Of the 12 grep finds, kb keeps 11 in the top 10.

The table is the second run: the first exposed a normaliser bug («14¼» was
tokenised as «141»); fixing it moved only case 14 (whole 30 → 29, in-work
11 → 7). No query was changed.

**What the grep misses were** (verified on the page text): line-break
hyphenation (1 «fir-/kantede», 14), old orthography (2 «rund mynt», 3
«kaabermønt», 5 «gangbar mynt», 6 «Vardin»), OCR damage (19 «jaffngod» read
as «slæderjcjjhgod» — kb finds it on the other query words), and different
compounding (7 «Smaa-Myndt», 16 «golt gulden»).

**Where kb still fails** — hypotheses, untested: case 4 (query «afsættelse» vs
text «afsettelse»: no æ/e fold; «sexskilling» vs «siuf skillinger»), 7 and 16
(compound in the query, two words in the text — would need compound
splitting or a decompounding variant list), 13 (whole-corpus rank dilution:
the passage is long and the query words are common). Whole-corpus ranking is
the weak point; within one work the ranking is good.

## Out of scope for the pilot

Vector embeddings (e.g. local bge-m3); OCR of the `rigsarkivet/` scans; the
`kb-ingest` / `kb-research` skills and a `source-researcher` agent; Hede and
Bruun (coin records, not prose).
