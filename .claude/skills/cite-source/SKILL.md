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
2. **Page hint is mandatory for any paginated work** (PDF book, journal, auction catalogue,
   ordinance gazette): a concrete page, not a range or «passim». A web reproduction of a
   paginated work still needs the print page if the reproduction gives it; if it does not
   (danskmoent's Ernst articles), the gap is reported to the curator, not filled. Unpaginated
   web pages need no page — the quote is the locator.
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

## Workflow (WRITE / FIX)

1. `cite_helper.py --usage KEY` (existing key) — who cites it, for which claim.
2. Open the source; copy the passage; note the page.
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
