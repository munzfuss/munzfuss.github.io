---
name: cite-source
description: >-
  Create, fix or AUDIT a source citation: the `data/shared/refs_pool.yml` entry (the
  bibliography line) AND the `<sup>[ref:KEY]</sup>` marker plus any quoted passage in the
  rendered prose that cites it. Use whenever a fact enters rendered text from a source
  («додай посилання», «процитуй джерело», «онови посилання», «перевір посилання / список
  джерел», «чи коректні посилання в розділі X», «додай архівну копію», «додай переклад
  цитати»). Encodes CLAUDE.md §5 / §5a / §5b and the curator's later rules in one place:
  one passage = one key, verbatim quote as locator, mandatory page hint for paginated works,
  a translation after every foreign-language quote (in the pool AND in prose), the original
  title untranslated, a Wayback archive copy next to every web link, all four languages in
  lock-step. Helper `cite_helper.py` lints keys / a whole section and flags candidates.
---

# cite-source — how a citation is written in this project

A citation has **two halves**, and both are written in the same change:

- **(A) the prose side** — the sentence in `data/shared/fuesse.yml` / `data/v2/locations/*.yml`
  that states the fact, the `<sup>[ref:KEY]</sup>` marker after it, and (optionally) a quoted
  passage in the sentence itself;
- **(B) the pool side** — the entry `data/shared/refs_pool.yml::KEY` that renders in the
  page's «Джерела / Quellen / Sources / Kilder» list.

Reader: role-3 (§0z) for both halves — the end-reader sees them as a finished reference
work. No project-meta, no «we», no explanation of why the citation exists.

Helper (candidates, not verdicts):
```
.venv/bin/python .claude/skills/cite-source/cite_helper.py KEY [KEY …]
.venv/bin/python .claude/skills/cite-source/cite_helper.py --fuss nobel_fod [--location denmark]
.venv/bin/python .claude/skills/cite-source/cite_helper.py --page site-danskmoent/uk/index.html --section fuss-nobel_fod
```

## When to use

- **Any new fact entering rendered text from a source** — a Fuß description, a period
  text, a phase background, a timeline bar, a closing, a grundwerte line. The pool entry
  and the `<sup>[ref:KEY]</sup>` are written in the same change as the sentence (§5).
- **Quoting a source in prose** — the quote needs its translation in every field whose
  language it is not in, and must match the cited key's passage.
- **Editing or trimming an existing pool entry, or re-pointing a citation** — run
  `--usage` first: a key is shared across Füße and pages.
- **Auditing a few keys or one passage** — «чи коректне це посилання», «чи є переклад /
  архівна копія», «чи є дублі»: `cite_helper.py KEY …` or `--page … --section …`.
- **Adding archive copies** to existing entries, or after a source site changes / dies.
- **Before committing any `refs_pool.yml` change** — lint the touched keys.

## When NOT to use

- **Coin-row source attribution** (`coin.sources[]`, `weight_rough_g[].source`) — that is
  pipeline data written by the seed builders, not a bibliography entry.
- **Legacy per-location `<loc>-references.yml` `[N]` refs** — §5a's shape applies, but new
  citations go to the pool; migrate rather than extend the legacy file.
- **Research dossiers (`docs/research/*.md`)** — quotes + page hints per §5a, but no pool
  entry is needed unless the fact also reaches the rendered page (`research-dossier`).
- **Chat** — quoting a source to the curator follows the chat rule (Ukrainian translation
  right after the quote), not the pool shape.
- **Auditing ALL citations of one Fuß on one page** (timeline, card, details, coin notes,
  across the page's languages) → `fuss-cite-audit`, which applies this skill's rules to
  every key and adds the boundary, cross-language counts and claim map. Fixes it finds
  come back here.
- **Scoring a Fuß description's content** — that is `fuss-description`; use this skill for
  the citations it adds.

## Modes

- **AUDIT** («перевір посилання», «чи все коректно») — READ-ONLY. Run the helper, open each
  flagged entry, verify against the source (§0b), report a numbered table of findings ranked
  by priority. Change nothing.
- **WRITE / FIX** — create or repair entries. Run the helper before and after; the after-run
  must be clean or each remaining flag explained.

## (B) The pool entry — exact shape

One key = ONE passage of ONE work (curator 2026-10-07). Two passages of the same book
(different pages, or two sentences of one web page) are two keys. Never bundle passages,
never let two keys quote the same or overlapping text — if a later key needs a fact the
earlier key's passage already carries, cite the earlier key instead.

Key: `{author-or-publisher}-{year}-{topic}` lowercase-hyphenated, semantic, stable, never
renumbered (`wilcke-1950-nobel-1514`, `galster-nobel-1524-23-karat`).

Order of elements, identical in all four languages:

```
<b>Surname, First name</b>: <i>Original title</i>[, vol][ (Place Year)][, chapter][, page] —
<a href="LIVE" target="_blank">short-url</a> (<a href="WAYBACK" target="_blank">ARCHIVE-LABEL</a>)[ (PD-mark)].
«<i>verbatim quote</i>»[ (page if not given above)][ (TR-LABEL «translation»)].
```

Rules, each one a past failure:

1. **Author bold, title italic, title in the ORIGINAL language and wording** — never
   translate or partially translate a title or an auction-lot title («Denmark, Noble 1496,
   Hans» stays English in the uk entry). Tier-1 per §2.
2. **Page hint is mandatory for a paginated work WE READ** (PDF book, journal scan, auction
   catalogue, ordinance gazette): a concrete page, not a range or «passim».
   **Cite what you read** (curator 2026-10-12): when the text was read in a web
   reproduction (danskmoent's Ernst / Galster pages), the reproduction IS the cited source —
   link it, archive it, and the verbatim quote is the locator; no page is required and
   none is invented. Name the original publication as the reproduction states it
   («Nordisk Numismatisk Årsskrift 1948, s. 1–38» — an article range is fine here, it is
   bibliographic data, not a locator). The reproduction's own fidelity to the print is
   its responsibility, not ours. Unpaginated web pages likewise need no page.
3. **Verbatim quote, ~25 words** (a guideline — a little more to keep one passage intact is
   fine; a stack of passages is not). Copy it from the source/cache, never from memory.
   Mark omissions with `…` (or `[…]` when the source's own style uses it). Cut parts the
   citing prose does not use — but check the citing sentences first (helper `--usage`).
4. **Translation after every quote that is not in the field's language**:
   `de (dt.: «…»)` · `en (transl.: «…»)` · `uk (перекл.: «…»)` · `da (overs.: «…»)`.
   - A Danish quote: de/en/uk translate, **da carries the original only**.
   - An English quote: de/uk/da translate, en does not.
   - French / Dutch / German / Latin: every field except the one in that language.
   - The translation is faithful to the quote, keeps its `…`, keeps proper names and
     instrument names in their tier-1 form (Møntordning, Rhinsk Gylden, Noble).
   - Context the quote needs (e.g. «from the instruction after the ordinance of
     14 December 1489») goes after the translation, separated by `;`.
5. **No label before the quote** — no «Verbatim:», «Ordret:», «Цитата:». The guillemets and
   italics already mark it.
6. **Archive copy next to every web link** (curator 2026-10-12). Label:
   `de Archivkopie vom 09.10.2025` · `en archived copy of 9 Oct 2025` ·
   `uk архівна копія від 09.10.2025` · `da arkiveret kopi fra 9.10.2025`.
   - Find a snapshot through the **Wayback UI**, not the API: open
     `https://web.archive.org/web/2026/<live-url>` in the browser pane — it redirects to the
     nearest snapshot (`/web/<timestamp>/…`) or says «has not archived that URL».
     `archive.org/wayback/available` and `/cdx/` are often 429 / «Temporarily Offline»
     while the UI works; their failure is NOT evidence that no snapshot exists.
   - For a PDF, verify the snapshot is the file, not a stub:
     `curl -s -r 0-1023 -L -o /tmp/x "https://web.archive.org/web/<ts>id_/<url>"` →
     `application/pdf`, starts `%PDF`.
   - A JS page (auction sites): open the snapshot and confirm the quoted text is in it.
   - **No snapshot → ask the curator before Save Page Now** (`web.archive.org/save/<url>`):
     it submits a URL to an outside service. After saving, use the returned timestamp.
   - When several keys share one live URL, add the archive link to all of them in the
     same change (helper reports the siblings).
7. **Fixed formulae per language** (keep the corpus uniform):

   | | de | en | uk | da |
   |---|---|---|---|---|
   | volume | Bd. II | vol. II | т. II | bd. II |
   | chapter | Kap. 2 | ch. 2 | розд. 2 | kap. 2 |
   | page | S. 153 | p. 153 | с. 153 | s. 153 |
   | reproduced web text | Text wiedergegeben auf | text reproduced at | текст відтворено на | teksten gengivet på |
   | public domain | (gemeinfrei) | (public domain) | (public domain) | (fri af ophavsret) |
   | Copenhagen (imprint) | København | Copenhagen | Копенгаген | København |

8. **No analysis in the entry** (§5a): no «proves», no multi-sentence scope note, no
   cross-reference to another ref. An optional scope note ≤ 80 characters may follow the
   quote. Catalogue numbers are allowed here (they are the locator) — unlike in Fuß prose.
9. **All four languages (de/en/uk/da) in the same edit**, identical facts, identical quote,
   identical links.
10. **The source itself before the entry** (§0b): open the page / PDF / cache and copy the
    passage. A web fact gets its entry in the SAME change as the prose that uses it (§5).

## (A) The prose side

- The marker goes right after the sentence (or clause) the passage backs:
  `…normiert den Nobel<sup>[ref:wilcke-1950-nobel-1514]</sup> und …`. Several sources
  stack: `<sup>[ref:a]</sup><sup>[ref:b]</sup>`.
- A **quote in the prose** follows the same translation rule as the pool, but with a bare
  parenthesis and no label: `«<i>Der er ikke bevaret nogen dansk Møntordning fra Kong
  Hans</i>» («No Danish Møntordning from King Hans has been preserved»)`. The da field keeps
  a Danish quote without translation; every field translates a quote not in its language.
- A quote in prose must be the same wording as (or a sub-passage of) the cited key's quote —
  the reader who opens the source note must find it.
- Same sentence, same citations in all four languages (`audit_i18n.py` checks the count).
- No catalogue numbers in Fuß prose (§7a) — they live in the pool entry.
- Never cite a key for a claim its passage does not make. Before re-pointing or trimming a
  key, list every sentence that cites it (`cite_helper.py --usage KEY`) — a key is shared
  across pages.

## Finding the passage — `kb search`

The harvest cache has a full-text index over every work with a text layer (Secher, Schou,
Wilcke 1919 / 1924 / 1950, Mordhorst, Galster, Denar til daler, Munro, Bobzin, Bruun I–V, Hede, danskmoent
pages …; the list and each work's page mapping: `scripts/cache/_corpus.yml`). It folds old
spellings, line-break hyphenation and common OCR slips, so it finds «Myndt-Ordning» for
«møntordning», «kaabermønt» for «kobbermønt», «fir-/kantede» for «firkantede», which a
plain `grep` misses (measured: `scripts/kb/README.md`).

```
.venv/bin/python scripts/kb/kb.py build                                     # once per session, ~8 s
.venv/bin/python scripts/kb/kb.py search "kobbermønt hvider" --work secher-ccd
.venv/bin/python scripts/kb/kb.py search "vardein smeltning" --work schou-1795 --limit 20
.venv/bin/python scripts/kb/kb.py search 'NEAR(kroner skiling*, 8)' --fts --work secher-ccd
```

- **Restrict to the work** (`--work`, ids in `_corpus.yml`) whenever you know it — ranking
  across the whole corpus is the weak point; within one work the passage is usually rank 1.
  Not sure which work? `--kind source` limits to editions of the acts and accounts
  (Secher, Schou, …), `--kind literature` to the studies.
- A hit prints `work · p. N · path:line`. **p. N is the PRINTED page** where the manifest
  establishes the PDF→print offset; otherwise the hit says «printed page not established» —
  then find the page on the scan, never compute one.
- **Never quote the snippet.** It is normalised context; open the file at `path:line`, read the
  whole passage, copy it verbatim (rule 3). For OCR'd works check doubtful letters and every
  figure against the page image (`ocr` note in `_corpus.yml`).
- Secher prints the SOURCE's page breaks in brackets («[s. 161]») — those are not Secher's
  page; cite the page the hit reports (Secher's own pagination).
- AUDIT mode: `kb search` with a distinctive phrase of a key's quote shows whether the quote
  sits on the page the key claims; `scripts/kb/audit_pages.py` runs that check over every
  key of every indexed work (a report — each MISMATCH still needs the page read).
- Bruun Parts I–V: cite **lot + PRINTED page** («Bruun Part II, lot 13163, p. 94»); the hit
  reports the printed page (running head «Page N»). The PDF page is higher by a constant per
  part (I +24, II +26, III +18, IV +16, V +16); `scripts/lib/bruun_pages.py` converts. Parts II
  and V reuse lot numbers 14001–14226 — always name the part.
- No hit ≠ no passage: the rigsarkivet scans (handwriting, no text layer) and the 1928 Bruun
  catalogue are not indexed, and heavy OCR damage can defeat any normalisation.

## Workflow (WRITE / FIX)

1. `cite_helper.py --usage KEY` (existing key) — who cites it, for which claim.
2. Find the passage — with `kb search` when the work is in the harvest cache (see «Finding
   the passage» below). Open the file at the reported line, copy the passage from THERE,
   take the page the hit reports. A hit is a pointer, never the quote.
3. Search the pool for the same work and passage (`cite_helper.py --work "<url or title>"`)
   — reuse a key whose passage already carries the claim; never create an overlapping one.
4. Find / verify the archive snapshot (rule 6).
5. Write the entry in de/en/uk/da through `scripts/lib/yaml_io.py` `load()`/`save()`
   (round-trip residual of refs_pool is 0 — the diff shows only your lines). Add the prose
   marker and any prose quote + translation in all four languages.
6. `cite_helper.py KEY` → clean; `scripts/build.py --validate-only`; `scripts/audit_i18n.py`.
7. Rebuild the page that shows it (danskmoent: `build.py --site danskmoent`, background) and
   read the rendered list item.
8. Commit (pathspec, `-F`, background).

## Audit report format

```
SECTION: fuss-nobel_fod (danskmoent uk) — 42 refs, 0 unresolved
 #  key                                   finding                               prio
 7  danskmoent-1nobel                      Danish quote untranslated in de/en/uk high
 6/14 wilcke-1950-nobel-1514 / -moentordning-1514  overlapping passage p.153    high
 34 ernst-1948-ribe-…                      paginated, no page hint (none online) gap
```
Priorities: missing translation / overlapping passage / wrong claim → high; missing archive
copy → medium; long quote, label, formula drift → low; unsourceable page → reported gap.
