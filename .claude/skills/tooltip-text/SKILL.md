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
6. **Each source on its own line** (curator 2026-11-02). Every statement that
   opens with a new bold source starts a new line; a plain connecting sentence
   before the first source («Датування зведене з датувань джерел.») keeps the
   first line. Further passages of the SAME work («Там само, [b]с. 47–48[/b]…»)
   stay on that work's line. In YAML the break is a real newline: `\n` inside a
   double-quoted scalar, or a line of a `|` block — never `\n` in a
   single-quoted scalar, which stays literal. Write it through `yaml_io` (it
   picks the quoting); a hand-typed `'…\n…'` renders the backslash.
7. **No headline.** The marker kinds open with their own bold line («Підозріле
   значення.», «Прогнозоване значення.», …, `MARK_HEAD` in app.js); do not
   repeat it.
8. **All four languages in the same edit** (de / en / uk / da), same sources,
   same quotes, same markup.
9. **No project meta** (§0z): no «we», no field names, no «curator decided».
10. **A measurement's `source` label is a designation only** (curator
    2026-11-02). The `source` of a `weight_rough_g` / `fineness` /
    `diameter_mm` reading is ONE string shown in every language (the
    «Обчислено з вагою з: …» tooltip prints it as is), so it carries no prose
    in any language — only what a reader can look up: publisher or author,
    year, and the number or page — «Bruun Part III, lot 11304», «Lindblad 2017
    (Metallanalyser av mynt 2017:3), Nr 88», «danskmoent.dk (Galster 28)».
    Name the source we actually read the figure in: a weight printed only in
    danskmoent's image caption is «danskmoent.dk (Galster N)», not the book
    whose illustration the page reproduces. A value set from the standard
    (no source prints it) is labelled with the Fuß name alone, which never
    translates — «Guldgyldenfod». Why a value is what it is («not stated on
    …», «illustration caption», «entered on curator request») belongs in
    `_curation_holds` / `verification_note`, never in the label.
11. **An inferred value's «[ ]» tooltip says where it comes from, not what it
    is** (curator 2026-11-03). The cell shows the value; the tooltip says that
    the sources give none and names the basis — the Fuß's parameters, the
    ruler's reign, the denomination's name — then each source's own words
    («u.år» with its translation). A basis the cell does not show stays (the
    weight's «1/71⅓ Cöllnische Marck»); the computed number does not. A
    dating compiled from several works keeps its own form. Texts:
    `ui.yml` `uncertainty.nosrc.*` / `uncertainty.basis.*` /
    `uncertainty.printed.*`, `source.fuss_value` / `source.fuss_basis` (a
    Fuß-name label in the value's and the derived values' tooltips); code:
    `render.py::uncertainty_mark`, `resolve_tips`.

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
