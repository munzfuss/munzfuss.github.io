---
name: add-source-work
description: >-
  Bring a printed work (a PDF — monograph, journal article, offprint, catalogue,
  ordinance edition) into the harvest cache so the corpus search finds it:
  check it is not already cached, download it, check the text layer (a scan
  without OCR indexes empty), write the plain-text extract, establish the
  PDF → printed page mapping from the running heads, add the `_corpus.yml`
  record, rebuild and test the index, commit the cache submodule and bump its
  pointer. Use for «збережи цю працю до нас», «додай PDF у кеш / корпус»,
  «зроби текстову копію для пошуку», «чи є в нас ця книга / стаття»,
  «add this PDF to the corpus», «save this work», or whenever a useful PDF
  turns up during research and is not yet in `scripts/cache`. Helper
  `add_work.py {dupes|fetch|inspect|extract|offsets|entry|verify}`. Citing the
  work afterwards is the `cite-source` skill.
---

# add-source-work — a PDF into the cache and the corpus search

The corpus search (`scripts/kb/kb.py`, CLAUDE.md «Tool fallback chain», tier 0)
reads only what `scripts/cache/_corpus.yml` lists. A PDF lying in the cache
without a record is invisible to it; a record with a wrong page mapping makes
every later citation of that work cite the wrong page, and nothing flags it.
This skill is the one procedure for doing it right. Read `scripts/kb/README.md`
(record format) and `docs/PLAYBOOKS.md` PB-10 (cache commits) once.

Helper: `.venv/bin/python .claude/skills/add-source-work/add_work.py <cmd> …`
— paths are relative to `scripts/cache/`.

## When NOT to use

- A web page (HTML), not a PDF → it belongs in the cache too, but through the
  source's own fetcher and `kb.py extract-htm` (danskmoent, Hede).
- A source the project harvests in bulk (Bruun, Numista, KMM, IKMK) → its
  harvester and parser (`docs/HARVEST_GUIDE.md`), not a single corpus record.
- A paper-only work nobody has a copy of → nothing to cache; CLAUDE.md §5a.

## Procedure

1. **Is it already here?** `add_work.py dupes <author> <title word>` lists
   corpus records that match; after the download, `dupes … --pdf <file>`
   also finds the same file cached under another name. A different copy of a
   work already present (journal volume vs offprint, another scan) gets its
   OWN record that names the other in `basis` / `ocr` (the `hauberg-1886` /
   `hauberg-1886-saertryk` pair) — never overwrite the existing one.

2. **Where it goes.** Beside the works it belongs with, in the source's tree:
   danskmoent PDFs under `danskmoent/<topic>/`, Wilcke under `wilcke/…`, etc.
   File name `<author>_<year>_<short_title>.pdf`, ASCII, lower case.
   `add_work.py fetch <url> <dest>` downloads with a browser User-Agent
   (danskmoent answers bots with a challenge page), refuses to overwrite and
   refuses anything that is not a PDF. Downloading a file from a link the
   curator gave, or from the source the research is already reading, needs no
   extra confirmation; any other download is asked first (filename, source,
   size).

3. **Text layer.** `fetch` runs `inspect`: pages, characters per page, pages
   without text.
   - Every page empty → a scan without OCR. Stop: tesseract / ocrmypdf are not
     installed here. Ask the curator whether to OCR it (install, then
     `ocrmypdf -l dan+deu --skip-text in.pdf out.pdf`) or to cache it without
     a corpus record — and say plainly that a search miss in it means nothing.
   - Some pages empty → plates, title or blank pages, or pages the OCR missed.
     Look at them (`pdftoppm -f N -l N -r 90 -png`); if they are plates, say so
     in `ocr`.

4. **Extract.** `add_work.py extract <pdf>` writes `<name>.extract.txt` beside
   the PDF with one form feed per page (`layout: formfeed`) and checks the
   count equals the page count. Never hand-edit an extract.

5. **Page mapping.** `add_work.py offsets <name>.extract.txt` scans the running
   heads and prints contiguous runs of one offset (printed − pdf, negative
   when front matter precedes p. 1). Then READ the pages: the first and last
   page of every run and every page around a break (`kb.py page <pdf> N`).
   Record a segment only where you have seen the heads agree; a title page,
   unnumbered plates or an inserted section are outside every segment
   («not established» is honest, a guessed offset is not). An offprint with
   its own pagination: record its pages, and in `basis` say which copy a
   citation should use. Write in `basis` what you checked («pdf 3 = s. 2,
   pdf 65 = s. 64; pdf 1 is the journal title page»).

6. **The record.** `add_work.py entry --id … --segment FROM:TO:OFFSET …`
   prints a record; paste it into `scripts/cache/_corpus.yml` next to its
   relatives. Fields (full list in the file's header comment):
   - `id` — `<author>-<year>[-<distinguisher>]`, lower case, stable.
   - `title` — as printed, with the journal / series and the printed page
     range for an article; original language, never translated (§2 tier 1).
   - `citation` — the short form a page hint follows («Hauberg 1891, s. <printed>»).
   - `languages`, `kind` (source | register | literature | web | extract).
   - `source_url` — where the copy came from; this is what a citation links.
   - `ocr` — the quality note a reader needs before quoting: who OCR'd it,
     what is unreliable (legends, tables, Fraktur, numerals), where plates are.
   - `refs_match` — a regex that finds this work's entries in
     `data/shared/refs_pool.yml`; `refs_pool_keys: []` for a new work.

7. **Verify.** `add_work.py verify <id> "<a phrase you saw on a known page>"`
   rebuilds the index, runs `kb.py offsets <id>`, prints the refs_pool keys
   the regex finds, and searches the phrase in the work. The hit must report
   the printed page you read the phrase on. If not, step 5 is wrong.

8. **Commit — cache first, then the pointer** (PB-10, Git safety protocol).
   Inside `scripts/cache`, commit ONLY your files by explicit path (the PDF,
   the extract, `_corpus.yml`); other sessions leave untracked files there.
   Then in the main repo `git commit scripts/cache -m "chore: bump cache - …"`
   (background, no trailing `&`). Push only on the curator's «пуш».

9. **Report** to the curator: the work, its record id, pages, the mapping and
   what it rests on, OCR caveats, and what the work showed that matters for
   the task at hand. Citing it is `cite-source` — with the printed page from
   the mapping and a quote read from the page (image, when `ocr` says so).

## Hard rules

- Never record an offset you have not checked against the page heads.
- Never overwrite a cached PDF or extract; a second copy is a second file and
  a second record.
- A scan without a text layer is not indexed silently: OCR it or say it is
  unsearchable.
- `_corpus.yml` lives in the submodule: commit there by path, then bump the
  pointer. Never `git add -A` in either repo.
- Quote from the page, never from a search snippet or an unchecked OCR line.

## Worked example — Hauberg 1891 (2026-10-27)

`https://www.danskmoent.dk/pdf2/Hauberg%20Gulland.pdf` → `dupes hauberg` found
the two 1886 records, no 1891 → saved as
`danskmoent/hans_1481_1513/hauberg_1891_gullands_myntvaesen.pdf` (73 pages,
ABBYY OCR, text on every page) → `offsets`: −1 over pdf 1–73; pdf 1 is the
journal title page, so the segment is 2–73 → record `hauberg-1891`, `ocr`
noting the catalogue drawings and unreliable legends → `verify hauberg-1891
"Lillebusk"` → s. 66 (pdf 67), as read → cache commit `a73dd3a8d`, pointer
`dbfcebb`.
