---
name: tooltip-text
description: >-
  Write or revise the TEXT of a tooltip on the coin tables — a «(?)» / «[ ]»
  uncertainty, a (*) / (!) / (§) mark reason, a year note, a curated
  attribution note, a regent bracket or silver-traces explanation, a ui.yml tooltip
  string — so that the reader sees at a glance who says what: the source in
  bold, its verbatim words in italics, a translation after every quote not in
  the field's language, all four languages in lock-step. Use for «напиши /
  перепиши тултіп», «текст тултіпа», «поясни це в тултіпі», «джерела жирним,
  цитати курсивом», «додай пояснення в тултіп», «покращ видимість тултіпа»,
  or whenever a change you make puts new reader-facing text into a tooltip.
  Not for the bibliography (`cite-source`), not for Note-column prose
  (`<sup>[ref:KEY]</sup>` citations, also `cite-source`), and not for
  deciding WHETHER a value deserves a mark (`reading-marker`, §4).
---

# tooltip-text — how a tooltip's text is written

A tooltip is role-3 text (§0z): the end reader sees it, never the chat. It
explains ONE value in a table cell: why it is uncertain, inferred, marked,
or what a bracket means. It is short, sourced (§0), and formal (§2a).

## The markup

`assets/app.js` (`appendMarkup`) turns two tags into elements — never HTML,
the text stays data:

| tag | renders | use it for |
|---|---|---|
| `[b]…[/b]` | **bold** | the source: author / work, year, locator — `[b]Galster 1973, с. 23[/b]`, `[b]Lindahl 1955 (NNÅ 1955), s. 80[/b]`, `[b]danskmoent.dk[/b]`, `[b]IKMK Berlin[/b]` |
| `[i]…[/i]` | *italic* | the source's own words, verbatim, WITH their guillemets — `[i]«Finhed: spor af sølv»[/i]` |

A newline (`\n` in a computed string, `&#10;` inside a template attribute)
starts a new line.

**Where it works:** tooltips inside the coin tables (`.mt-scroll`), which go
through the portal — every marker kind and every plain tooltip there. A
tooltip OUTSIDE the tables (timeline bars, filter chips, card rows) is a CSS
`::after` and would show the tags raw: write it without markup.

## Rules

1. **Source bold, words italic, nothing else styled.** Our own connecting
   sentence («Карбовано в імʼя Erik VII; фактичною регенткою була
   Margrete I…») stays plain. Do not bold a value or a conclusion.
2. **Bold = the designation a reader can look up:** surname or publisher, year,
   and the locator (page, number) when there is one. Same form as the
   pipeline's own tooltips (`scripts/lib/render.py::uncertainty_mark`).
3. **Italic = verbatim only**, copied from the source or cache (§0b), with its
   original spelling (§2 tier 1). A paraphrase is never italic.
4. **Translation** after every quote not in the field's language, in
   parentheses, plain: `[i]«Finhed: spor af sølv»[/i] (перекл.: «проба: сліди
   срібла»)` — `de (Übers.: …)` · `en (transl.: …)` · `uk (перекл.: …)`; the
   `da` field keeps a Danish quote untranslated. A short quote may take the
   bare parenthesis the render code uses (`(«…»)`).
5. **One source per statement.** «[b]A[/b]: [i]«…»[/i]. [b]B[/b]: …» — never
   «A and B say …». A computation is attributed as such («errechnet aus …»),
   not dressed as a source.
6. **No headline.** The marker kinds open with their own bold line («Підозріле
   значення.», «Прогнозоване значення.», …, `MARK_HEAD` in app.js); do not
   repeat it.
7. **All four languages in the same edit** (de / en / uk / da), same sources,
   same quotes, same markup.
8. **No project meta** (§0z): no «we», no field names, no «curator decided».

## Where tooltip text lives (edit it there, never in `site/`)

| text | surface |
|---|---|
| ui strings (regent bracket, silver traces, marker defaults) | `data/i18n/ui.yml` |
| a class's compiled dating / attribution (→ `year_note`) | `data/v2/attributions/<entity>.yml::note` |
| a mint / ruler / reading mark reason | the SEED entry's `mint_mark` / `ruler_mark` / reading mark (`reading-marker` skill) |
| uncertainty entries («(?)», «[ ]») | built by `render.py::uncertainty_mark` from `Coin.uncertainty` — fix the builder or the seed entry's `as_printed` |
| a fineness given as traces | the seed's `fineness_trace` (source + `as_printed`) |

Data YAML is edited through `scripts/lib/yaml_io.py` (`load`/`save`, or
`canonical_lines` for a line you write) — Check 9 blocks a raised round-trip
residual. A seed field the builder would overwrite gets a dict-form
`_curation_holds` reason.

## Procedure

1. Find the surface (table above) and read the current text in all languages.
2. Open each source and copy the passage (§0b) — `kb.py search` first.
3. Write the four fields by the rules; translations faithful, names tier-1.
4. Re-flow if the surface is pipeline data (merge + absorb of the entity);
   rebuild the page (danskmoent in the background).
5. Verify in the preview: hover the marker, read the portal's `innerHTML` —
   `<b>` around each source, `<i>` around each quote, no raw `[b]`.
6. Commit with an explicit pathspec.

## Example (the regent bracket, ui.yml `ruler.regent.margrete_i`, uk)

```
Карбовано в імʼя Erik VII; фактичною регенткою була Margrete I (до її смерті
1412 р.). [b]Galster 1973, с. 23[/b]: [i]«Dronning Margrethe genopretter
møntvæsenet i Erik af Pommerns navn 1397»[/i] (перекл.: «Королева Маргрете
відновлює монетну справу в імʼя Еріка Померанського 1397»). Рік смерті:
[b]danskmoent.dk[/b], [i]«Margrethe 1. (1375-1412)»[/i].
```
