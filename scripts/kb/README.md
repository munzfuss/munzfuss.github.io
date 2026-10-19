# `scripts/kb/` — knowledge-base search over the harvest cache (pilot)

**Retrieval only.** `kb search` returns ranked, page-anchored passages — work,
PRINTED page where the corpus manifest establishes one, file path and line —
as the first step of the `cite-source` workflow. It never summarises or
answers. A hit is a pointer: the passage is then read in full in the file and
quoted verbatim per CLAUDE.md §5a. No RAG, no LLM synthesis (that would
collide with §0 / §0b and the verbatim-quote discipline).

```bash
.venv/bin/python scripts/kb/kb.py build                    # ~9 s, 13k passages
.venv/bin/python scripts/kb/kb.py works                    # what is indexed: ids, kinds, page anchoring
.venv/bin/python scripts/kb/kb.py search "kobbermønt hvider blaffeter"
.venv/bin/python scripts/kb/kb.py search "vardein smeltning" --work schou-1795
.venv/bin/python scripts/kb/kb.py search "sølvgylden" --lang da --limit 20
.venv/bin/python scripts/kb/kb.py search "rosenobel ungersk dukat" --kind source   # act texts only
.venv/bin/python scripts/kb/kb.py search 'NEAR(kroner skiling*, 8)' --fts --work secher-ccd
.venv/bin/python scripts/kb/kb.py offsets wilcke-1950      # re-derive PDF→printed offsets
.venv/bin/python scripts/kb/kb.py refkeys                  # manifest vs refs_pool.yml drift
.venv/bin/python scripts/kb/kb.py extract-htm              # danskmoent + Hede .htm → text
.venv/bin/python scripts/kb/measure.py                     # the grep-vs-kb measurement
.venv/bin/python scripts/kb/audit_pages.py                 # refs_pool page hints vs the index (report)
```

## Researching a Müntzfuß (or any subject) with kb

The working recipe — used by the `research-dossier`, `fuss-description`,
`fuss-cite-audit` and `cite-source` skills, which point here. Checked
2026-10-19 on the Kronemønt 1618.

1. **Index.** `kb.py build` once per session (~9 s). `search` warns when the
   index is stale (normaliser, `variants.yml` or `_corpus.yml` changed, or a
   partial `build --work`) — rebuild then.
2. **What is searchable.** `kb.py works` lists every work: id (for `--work`),
   kind (for `--kind`), languages, whether hits carry a printed page.
   Kinds: `source` (editions of the acts and accounts — Secher 1558–1660, Schou
   1670–, Hofholdningsregnskaber 1904, Galster 1934 on Junge's mint accounts),
   `register` (Mordhorst), `literature` (Wilcke 1919 / 1924 / 1950, Galster
   1936 / 1947 / 1973, Jensen, Denar til daler, Holst, Munro …),
   `catalogue` (Hede pages, Bruun Parts I–V), `web` (danskmoent, Bobzin),
   `extract`.
3. **The act first.** Search the instrument's words with its year, restricted
   to the editions: `kb.py search "kroner 1618 lødig mark" --kind source` →
   Secher Bd 3 p. 529–530 (open letter 1618, «kronerne halfanden rigsdaller …
   lødige mark»). Write period spelling or modern — both fold (Mynt/Mønt,
   Schilling/Skilling, Thaler/Daler, th→t, æ/ø/å, OCR «guiden»).
4. **Then the readings.** `--kind literature` for who discussed the act and
   with which figures (dossier C3 / C4 — who reproduced whom).
   Narrow with `--work wilcke-1919`; pin two words together with FTS:
   `kb.py search 'NEAR(krone* lødig*, 10)' --fts --work wilcke-1919` →
   p. 160 / 165 / 209.
5. **Then the coins.** `--kind catalogue`: Hede type pages (dates, mint marks,
   Schou / Sieg concordance, weight, fineness as Hede gives them) and Bruun lot
   texts (specimen weights, cataloguer's commentary). `kb.py search "krone 1618"
   --kind catalogue` → Hede 105A and the ¼ Krone 1618 page.
6. **Read, never quote the snippet.** Open `path:line`, read the whole page,
   copy verbatim; check every figure of an OCR'd work on the page image
   (`pdftoppm -f N -l N`). Cite the printed page the hit reports; Bruun as
   lot + printed page (`docs/SOURCES.md` §1.3).
7. **No hit ≠ no source.** Not indexed: rigsarkivet TK 160 (handwriting), the
   Bruun 1928 catalogue, paper-only works (Lange, Sieg, the printed Hede
   volumes), and any web page not in `scripts/cache`. Then use the web chain
   (CLAUDE.md «Tool fallback chain»); a page fetched for good belongs in the
   cache and in `_corpus.yml` (`docs/HARVEST_GUIDE.md`).
8. **Checking existing citations.** `audit_pages.py` scores every `refs_pool`
   key's quote against its page (a report; each MISMATCH needs the page read).

## Parts

| Path | What |
|---|---|
| `scripts/cache/_corpus.yml` | Corpus manifest, in the harvest submodule: one record per work — bibliography, languages, text-layer files and layout, PDF→printed page mapping with the basis it was established on, OCR note, `refs_pool` keys citing it. |
| `scripts/cache/_derived/danskmoent/`, `_derived/hede/` | Plain text of every cached danskmoent `.htm` (1029 files) and Hede page (857), one `.txt` per page, same relative path. Derived, never hand-edited; the `.htm` stays untouched. |
| `kb.py` | Normaliser, page splitter, FTS5 builder, `search`, `offsets`, `refkeys`, `extract-htm`. Stdlib `sqlite3` (FTS5 is compiled in, SQLite 3.53) + PyYAML; no other dependency. |
| `variants.yml` | Editable spelling-variant rules (Mynt/Mønt, Schilling/Skilling, Thaler/Daler, Reichs-/Richs-/Rigs-, ck→k, th→t, dt→t, …). |
| `eval_set.yml`, `eval_set_b.yml`, `measure.py` | The go/no-go measurement (set A, held-out set B). |
| `audit_pages.py` | Read-only audit: does each `refs_pool` key's quote sit on the page the key gives? |
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
| `markers` (Wilcke 1919, 1950; Denar til daler; Galster 1934, 1973; Bruun I–V) | text between page markers | offset segments, the marker's own printed number, or a running-head label (Bruun «Page 94 Stack's Bowers …») |
| `formfeed` (Munro, Hauberg, DCH 1904, Jensen, Eriksson, …) | form-feed page | offset segments |
| `section` (Wilcke II 1924) | ~25-line window, capped at ~1 500 characters (`chunk_chars`) — one line is one paragraph | the section's printed range only — the HTML has no page breaks |
| `whole` (danskmoent, Hede, Bobzin, Mordhorst) | ~30-line window | none — web reproductions; the quote is the locator |

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

**What the rules can and cannot do.** A rule folds spelling variants of ONE
word of ONE language that actually occur in the corpus — Mynt/Mønt,
Schilling/Skilling, Kaaber/Kobber (16th–17th-c. Danish for copper: Secher has
kaaber 40×, kaabber 12×, kobber 36×; rule added 2026-10-19, A/B unchanged).
Each rule is checked against the corpus and the measurement before it stays.
Words of DIFFERENT languages are not variants and get no rule: Kobber / Kupfer /
koppar / cuprum, Gylden / Gulden / florenus, Hvid / Witten — write them into
the query together (`kobber kupfer koppar`; without `--fts` the words are tried
with AND, then OR). `tests/test_kb_search.py` pins the folds that matter.

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
| A, round 3 | 12/22 | 10 / 16 / 21 | 15 / 22 |
| B, round 3 | 9/15 | 8 / 13 / 15 | 12 / 15 |
| A, round 4 (`--kind`) | 12/22 | 10 / 16 / 21 — same kind: top 10 19 | 15 / 22 |
| B, round 4 (`--kind`) | 9/15 | 8 / 13 / 15 — same kind: top 10 15 | 12 / 15 |
| A, round 5 (+Bruun, Hede; `chunk_chars`) | 12/22 | 10 / 16 / 20 — same kind: top 10 20 | 16 / 22 |
| B, round 5 | 9/15 | 7 / 13 / 15 — same kind: top 10 14 | 12 / 15 |

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

**Round 3 — A16 analysed** (curator 2026-10-19). The page (Galster 1934,
s. 108) failed on five mismatches at once, not on d/t alone: «gulden» rule
anchored at a word start, so «Goldgulden» was never folded; OCR reads
«gulden» as «guiden» (182× vs 30× in Galster 1934, also «Poul Guiden» =
Poul Gulden in Wilcke); «Stucken» escaped the Stück rule; Middle Low German
«kraet» (karat) and «golt» (gold). Measured one rule at a time on a scratch
index: «stuk» moved A16 within the work 16 → 3, «kraet» 3 → 1, «golt» put it
3rd across the corpus (the split «gold»+«gylden» needs «golt» folded);
«gulden» anywhere and «guiden» alone did not move A16 but are what the split
needs. Set B: no row changed. These five rules are fitted to A16 — B shows
they do no harm, not that they generalise.

**Round 4 — whole-corpus ranking analysed.** In every case where the gold
passage ranks low across the corpus, what outranks it are OTHER works on the
same subject (danskmoent pages, Galster, Wilcke, Denar til daler discussing
the very act the query targets), plus query words the gold passage lacks — not
one book flooding the list. Two remedies measured and rejected: a per-work
cap (A/B top 10 ±1, and it HIDES a work's 4th+ passage entirely — Munro 6 →
gone; kept as `--per-work N`, default off) and dropping single-digit query
tokens (no change; kept, it removes fraction-half noise). Adopted: a `kind`
per work in `_corpus.yml` (source = editions of acts / accounts, register,
literature, web, extract) and `--kind`. Restricting to the gold's kind lifts
top 10 to 19/22 (A) and 15/15 (B). This is an oracle measurement — the kind
is taken from the gold — but it is the choice a researcher makes knowingly
(«the act text» vs «what the literature says»).

**Still outside the top 10 within the kind** after round 4: A7 (Schou, OCR
«Smaa-N7yndt»; kind rank 25), A13 (Wilcke 1924, a 4 334-word section, common
words; >50), A14 (Wilcke 1950 table; 24). Within the work they are rank 1, 2
and 9.

**Round 5 — corpus extended, long paragraphs split** (2026-10-19). Two
changes, measured separately. (1) Bruun Parts I–V (Stack's Bowers text, kind
`catalogue`, printed page from the running head; offset to the PDF page is
constant per part: −24, −26, −18, −16, −16) and the 857 Hede pages from
danskmoent (kind `catalogue`). Alone this moved nothing in or out of any top
10 across the corpus; through BM25's corpus-wide term statistics it shifted
a few ranks by one or two (A5 within the work 8 → 10, A14 9 → 10, B9 within
the kind 10 → 11, A6 18 → 11 across the corpus). (2) `chunk_chars: 1500`
for Wilcke 1924, whose HTML holds one paragraph per line, so a 25-line
window ran to ~20 000 characters: A13 >50 → 15 across the corpus, >50 → 9
within the kind, 2 → 1 within the work; nothing else changed. Net: A within
the kind 19 → 20, B 15 → 14 (B9, rank 11).

Not indexed, with the reason: the rigsarkivet folio TK 160 (219 scans) is
16th-century German and Dutch chancery handwriting on microfilm — OCR cannot
read it, only handwriting recognition could; the 1928 Bruun catalogue has an
OCR layer whose columns come out interleaved.

**Embeddings: not justified.** Within the work every case of A and B is in
the top 10 (A 22/22, B 15/15). The remaining misses are ranking across works
on the same subject, which semantic similarity would make worse, not better.

## Page-hint audit — `audit_pages.py`

For every indexed work with established printed pages, each `refs_pool` key's
quote (first «<i>…</i>» of the da field) is scored against every page by the
share of its words; the verdict compares the claimed page with the best one.
A MISMATCH is a candidate: open the page before any fix, and fix through
`cite-source`. First run (2026-10-19): 222 keys with a quote and a page —
198 ok, 5 weak, 19 MISMATCH. Of the 19, six keys give a wrong page,
confirmed on the text (Wilcke 1919 s. 86 → 78, s. 73 → 74, s. 74 → 75 and s. 81 → 80;
Wilcke 1950 s. 184 → 183; two Wilcke 1924 keys «kap. II.7 (s. 258 ff.)»
whose passage is in B.7, s. 198–208); the seven Bruun keys all give the PDF
page, not the printed one (offset constant per part, quote verified on the
PDF page); six are false alarms — three tables whose OCR breaks the figures,
a page belonging to another work cited in the same entry, two quote words
fused with a footnote mark or a figure by the OCR.

### Set A, round 5

| # | refs_pool key | query | grep | grep: gold hit | grep: lines / files | kb rank | kb rank (same kind) | kb rank (in work) |
|---|---|---|---|---|---|---|---|---|
| 1 | `secher-ccd-1-174-1563-firkantede-moent` | firkantet mønt vrage | `firkantede` | ❌ | 17 / 7 | 22 | 9 | 5 |
| 2 | `secher-ccd-1-359-1567-fald-rund-mynt` | fald rund mønt 3 mark sager | `rund mønt` | ❌ | 31 / 11 | 2 | 1 | 1 |
| 3 | `secher-ccd-3-523-1619-kobbermoent` | kobbermønt hvider blaffeter | `kobbermønt` | ❌ | 43 / 11 | 1 | 1 | 1 |
| 4 | `secher-ccd-4-138-1625-afsaettelse` | møntens afsættelse sexskilling | `afsættelse` | ❌ | 15 / 14 | 1 | 1 | 1 |
| 5 | `secher-ccd-5-143-1643-reces-mynten` | fremmede købmænd gangbar mønt | `gangbar mønt` | ❌ | 20 / 16 | 28 | 10 | 9 |
| 6 | `schou-1795-bd1-s82-myndtordning-1671-vardin` | vardein møntmester smeltning prøve | `vardein` | ❌ | 0 / 0 | 17 | 5 | 1 |
| 7 | `schou-1795-bd1-s80-forbud-1671-smaamoent` | forbud indførsel småmønt | `småmønt` | ❌ | 43 / 9 | >50 | 26 | 1 |
| 8 | `mordhorst-c5mord-reskript-1692-kroner` | reskript 1692 kroner markstykker | `markstykker` | ✅ | 152 / 45 | 1 | 1 | 1 |
| 9 | `wilcke-1919-guldriddere-1611` | guldridder karat 1611 | `guldridder` | ✅ | 38 / 19 | 1 | 1 | 1 |
| 10 | `wilcke-1919-metzner-1593-bestalling` | Metzner bestalling møntmester 1593 | `Metzner` | ✅ | 24 / 9 | 1 | 1 | 1 |
| 11 | `wilcke-1919-flemming-1607-slagskat` | slagskat Flemming gevinst | `slagskat` | ✅ | 107 / 15 | 1 | 1 | 1 |
| 12 | `wilcke-1924-kap2-3-gruener-forslag-1642` | Grüner forslag 1642 møntordning 1624 | `Grüner` | ✅ | 42 / 10 | 1 | 1 | 1 |
| 13 | `wilcke-1924-kap1-gottorp-1610-muenz-edict` | Gottorp daler 33 skilling lybsk Nabobyerne | `Nabobyer` | ✅ | 4 / 4 | 15 | 9 | 1 |
| 14 | `wilcke-1950-flensborg-1547-vaegt` | sølvgylden 14¼ lødig finvægt | `sølvgylden` | ❌ | 123 / 37 | >50 | 31 | 10 |
| 15 | `wilcke-1950-sundtold-1550` | sundtold nobel rhinske gylden | `sundtold` | ✅ | 46 / 15 | 2 | 2 | 2 |
| 16 | `galster-1934-junge-guldregnskab` | Goldgulden 18 Karat 72 Stück | `Goldgulden` | ❌ | 547 / 20 | 4 | 1 | 1 |
| 17 | `jensen-1971-hdy-guldgylden-1624-1633-underloedig` | Lilliendahl underlødig lødighed Lübeck | `Lilliendahl` | ✅ | 21 / 1 | 1 | 1 | 1 |
| 18 | `eriksson-2017-hans-skilling-hvid-luebsk` | hvid lübsk witten vikt | `witten` | ✅ | 419 / 46 | 1 | 1 | 1 |
| 19 | `gullbekk-2025-haandfaestning-1483-jaffngod` | jævngod mønt Bergen Oslo danske penninge | `jævngod` | ❌ | 6 / 4 | 2 | 2 | 1 |
| 20 | `holst-1936-lybsk-myntmark-192-penninger` | lybske myntmark 192 penninger | `192 penninger` | ✅ | 6 / 3 | 1 | 1 | 1 |
| 21 | `munro-2009-marc-de-troyes` | marc de Troyes grams | `marc de Troyes` | ✅ | 25 / 8 | 6 | 6 | 6 |
| 22 | `galster-nobel-1524-23-karat` | Jørgen Kock nobel 23 karat | `23 karat` | ✅ | 34 / 22 | 4 | 2 | 2 |

### Set B (held out), round 5

| # | refs_pool key | query | grep | grep: gold hit | grep: lines / files | kb rank | kb rank (same kind) | kb rank (in work) |
|---|---|---|---|---|---|---|---|---|
| 1 | `secher-ccd-3-487-1618-soelvkrone` | sølvkrone 13¾ lod fint sølv halvanden rigsdaler | `sølvkrone` | ❌ | 22 / 8 | 8 | 3 | 1 |
| 2 | `secher-ccd-3-541-1619-rigsdaler-96-sk` | rigsdaler spansk matte otte realer skilling danske | `spansk matte` | ❌ | 1 / 1 | 1 | 1 | 1 |
| 3 | `secher-ccd-4-20-1622-tarif` | rosenobel ungersk dukat guldgylden mark danske | `rosenobel` | ✅ | 177 / 60 | 22 | 1 | 1 |
| 4 | `secher-ccd-1-210-1564-laan-klippinge` | låne klipping lensmænd rund mønt | `klippinge` | ✅ | 549 / 63 | 4 | 2 | 2 |
| 5 | `secher-ccd-3-309-1609-fremmed-smaamoent` | fireskillingstykker søslinger Hildesheim polske dütchen | `fireskillingstykker` | ❌ | 0 / 0 | 1 | 1 | 1 |
| 6 | `schou-1795-bd1-s81-myndtordning-1671-guld` | guldmønt dukat 23 karat 67 stykker kølnisk mark | `kølnisk mark` | ❌ | 1 / 1 | 2 | 1 | 1 |
| 7 | `schou-1795-bd1-s80-note-regl-1692` | kroner reglement 1692 halvskilling kobber | `halvskilling` | ❌ | 25 / 16 | 4 | 1 | 1 |
| 8 | `mordhorst-c5mord-reskript-1692-2-skilling` | toskilling godhed værdi kroner omkostninger | `omkostninger` | ✅ | 92 / 40 | 1 | 1 | 1 |
| 9 | `wilcke-1950-moentordning-1541` | møntordning 1541 Crucis 14½ lod | `Crucis` | ❌ | 24 / 5 | 23 | 11 | 5 |
| 10 | `wilcke-1950-tillaeg-1544` | guldengroschen 13½ lod 1544 | `Gyldengroschen` | ✅ | 21 / 11 | 1 | 1 | 1 |
| 11 | `galster-1934-junge-1545-tilladelse` | Junge tilladelse guldgylden Degener Flensborg | `Degener` | ✅ | 30 / 14 | 1 | 1 | 1 |
| 12 | `galster-1934-hertugdoemmer-lybsk-moentfod` | hertugdømmerne lybske møntfod privilegier 1460 | `lybske Møntfod` | ✅ | 2 / 2 | 1 | 1 | 1 |
| 13 | `eriksson-2017-hvid-soesling-skilling-penningar` | hvid fire penninge søsling skilling hovedvalør | `huvudvalören` | ✅ | 1 / 1 | 2 | 1 | 1 |
| 14 | `holst-norges-mynter-hamar-ingen-mynt` | Hamar biskop Magnus myntbrev Vincents Lunge | `Vincents Lunge` | ✅ | 12 / 5 | 7 | 5 | 2 |
| 15 | `wilcke-1919-van-campen-1596` | Geert van Campen møntmester 1596 specier | `van Campen` | ✅ | 7 / 5 | 1 | 1 | 1 |
