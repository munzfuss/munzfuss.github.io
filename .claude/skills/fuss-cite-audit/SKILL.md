---
name: fuss-cite-audit
description: >-
  READ-ONLY audit of EVERY citation belonging to one Müntzfuß on one location page —
  timeline row, section heading, card (left block + card text), everything inside
  «details» (background, instruments, phase descriptions, closing) and the Note of each
  coin in the fuss's table; the coin `sources` column is out of scope. Use for
  «перевір усі посилання стопи X на сторінці Y», «аудит цитат стопи», «чи коректні
  джерела в розділі стопи», «audit the citations of fuss X». Determines the page's
  languages from the site profile, compares citation counts per surface across those
  languages, finds language gaps in the data, runs the cite-source rules on every key,
  optionally checks each quote verbatim against scripts/cache, and writes a claim map
  for the sentence-vs-passage judgment. Reports a ranked findings table; fixes go
  through the `cite-source` skill.
---

# fuss-cite-audit — all citations of one Fuß on one page

The **page-level** companion of `cite-source`. That skill owns the rules for ONE citation
(pool entry shape, quote, translation, page hint, archive copy, prose marker); this skill
owns the **boundary** (what belongs to the fuss on the page), the **languages** of that
page, and the **cross-language and data-vs-render consistency** around the keys. Every rule
it checks per key comes from `.claude/skills/cite-source/SKILL.md` — read that first. When
the two disagree, `cite-source` is right and this helper is stale.

Reader of the report: role-2 (the curator, §0z). The audited text is role-3.

Helper (candidates, not verdicts — §0b):
```
.venv/bin/python .claude/skills/fuss-cite-audit/fuss_cite_audit.py \
    --fuss rhinsk_gylden_fod --location denmark \
    [--site danskmoent] [--verbatim] [--claims uk] [--out <scratchpad>]
```
~20 s (it runs the build's own coin assembly); `--verbatim` adds ~1 min.

## When to use

- The curator asks to check all references / quotes / sources of one standard on one page:
  «запусти аудит всіх цитат стопи X на сторінці Данії», «перевір посилання в розділі X»,
  «чи все гаразд із джерелами в цій стопі».
- **After a large rewrite** of one Fuß (card text, phase descriptions, a batch of coin notes)
  and before telling the curator it is done — the cross-language counts and the claim map
  catch what a key-by-key lint does not.
- **Before a fix campaign** on a Fuß's bibliography — the ranked table is the work list
  that `cite-source` then executes key by key.
- When a Fuß renders on **two pages / sites** (e.g. Guldgyldenfod on danskmoent and on
  Schleswig-Holstein): run it once per page — the boundaries and the languages differ.

## When NOT to use

- **One key, or one sentence** → `cite-source` directly (`cite_helper.py KEY`, `--usage KEY`).
- **Writing or fixing** citations → `cite-source` (WRITE / FIX). This skill changes nothing.
- **Coin `sources` column**, `weight_rough_g[].source`, other per-specimen attributions —
  pipeline data, not bibliography; out of scope here as in `cite-source`.
- **Scoring the content of the description** (founding / role / phases …) →
  `fuss-description`. This skill checks that what is said is cited correctly, not whether
  enough is said.
- **A research dossier** (`docs/research/`) → `research-dossier`.
- **A whole page at once** — run per Fuß; one report per section keeps the findings
  actionable.

## Step 1 — languages of the page (never assume)

The languages come from the **site profile** that publishes the location
(`config/sites/<id>.yml::languages`, root language `root_lang`), not from a fixed list:
danskmoent publishes Denmark in `da, de, en, uk`; munzfuss publishes its pages in
`de, en, uk` (no `da`). The helper picks the profile; pass `--site` when a location is on
more than one. Consequences:

- A missing language field in the data matters only if the site renders that language —
  and it is **silent** there: the renderer falls back to another language. The helper's DATA
  block lists those gaps; the rendered page will not show them.
- Translation checks run per page language: a Danish quote needs a translation in every
  page language except `da`.
- If a page language is not built, the helper says so — rebuild (`build.py --site <id>`,
  background) before auditing; an old build audits old text.

## Step 2 — the boundary (what belongs to the fuss)

Everything the reader sees as part of this standard on this page:

| surface | rendered (per language) | data |
|---|---|---|
| timeline row | the `tl-label` link to `#fuss-<fuss>` and its bar | `<loc>.yml::timeline.bars[id=<fuss>]` |
| heading + card | `<section id="fuss-<fuss>">` up to `<details>` | `fuesse.yml::<fuss>` (name, grundwerte rows, card text / description, closing) |
| details | the inline `<details>` + lazy `<lang>/t/<fuss>.html` outside the table | `<loc>.yml::fuss_periods.<fuss>` (background, instruments, closing), `phases.<fuss>[].description` |
| coin Note | every `<tr>` of the lazy table (`c-note` cell) | `note` of every coin the BUILD assembles for the page with `fuss: <fuss>` |

Notes:
- Coins are taken from `build._assemble_v2_location()` — the build's own selection
  (consumes_entities windows, exclusions, phase compatibility), never re-derived by hand. A
  coin of the same fuss that this page drops (e.g. Gottorp after 1656 on Denmark) is out of
  scope here and in scope on the page that shows it.
- Shared `fuesse.yml` rows can be scoped to one page: «in boundary data but not rendered
  here» is then expected, not an error — check the row's scope before reporting it.
- A key that is also cited by another Fuß is still in scope; any fix to it must go through
  `cite_helper.py --usage KEY` (cite-source rule) because it changes the other section too.
- Text of OTHER fusses that only links to this one (`fuss-xref`) is out of scope.

## Step 3 — run the helper and read its blocks

1. **RENDERED** — citations per surface and language. Every surface must have the same count
   in every page language; `← DRIFT` is a real defect (a cite missing in one language) unless
   the build is stale. `key-set drift` = the same count but different keys. `PROSE` lines are
   quotes in the rendered text without a `(«…»)` translation (language detection is
   heuristic: a German quote in the `de` field, or a numeric table, is a false positive).
2. **DATA** — language fields missing for page languages, per-field count drift, unresolved
   `[ref:KEY]`, and keys present on one side only.
3. **KEYS** — `cite_helper.lint` (the cite-source rules) reconciled to the page languages,
   plus: several passages in one key, no translation in ANY form vs. translation under an old
   label (formula drift only), missing archive copy, label before the quote, long text after
   the quote (analysis in the entry). Messages identical across languages are merged into
   `[de,en,uk] …`.
4. `--verbatim` — every quote fragment searched in `scripts/cache`. A miss is a candidate:
   OCR variants (ℳ→$, ‰→°/oo, broken hyphenation, spaced «G ylden») and uncached sources
   (Wikipedia, tekstnet, tidsskrift) are the usual causes. Close each miss by opening the
   source — the PDF page image for an OCR doubt, the live page for an uncached one.
   To find where a missed quote actually sits (and whether the key's page is right),
   `scripts/kb/kb.py search "<distinctive words>" --work <id>` folds OCR and spelling
   variants; `scripts/kb/audit_pages.py --work <id>` checks every key's page at once.
5. `--claims <lang>` — the claim map: for every citation point, the sentence it follows and
   the cited key's quote + translation. **This is the judgment step the script cannot do**:
   read each pair and ask «does this passage say what this sentence claims?» (cite-source:
   «never cite a key for a claim its passage does not make»). Typical finds: the quote omits
   the very number the sentence states; a coin-note figure not in the passage; a key whose
   body describes a different scope than the sentence uses it for.

## Step 4 — the report (READ-ONLY; change nothing)

Rank by the cite-source priorities, group keys that share one defect, and keep the table
short enough to act on:

```
FUSS rhinsk_gylden_fod · PAGE denmark (danskmoent: da/de/en/uk) — 58 keys, 94 cite points
Verified: counts equal in all languages · 0 unresolved · quotes verbatim (N OCR variants)
 #  key(s)                                finding                                      prio
 1  danskmoent-1rhinsk-gylden             no quote; body scope ≠ the 4 claims it backs high
 2  10 keys (list)                        several passages in one key                  high
 3  27 keys (list)                        foreign quote, no translation                high
 5  wilcke-1950-moentordning-1514         quote omits «72» the sentence states         medium
 9  34 keys                               no archive copy                              medium
11  8 keys                                old translation label                        low
Out of scope, noticed: <item> (which page it belongs to)
```

Then propose the fix order and STOP for the curator. Fixes run through `cite-source`
(WRITE / FIX), one key at a time, `--usage` first; archive copies that need Save Page Now
need the curator's yes; after the fixes, re-run this audit — the after-run must be clean or
each remaining flag explained.

## Hard rules

- **READ-ONLY.** No edit to `refs_pool.yml`, prose or data in this skill.
- **The boundary is the rendered page plus the build's coin selection** — not a grep of the
  YAML for the fuss name, and not the section HTML alone (the lazy table holds the details
  body and the coin notes).
- **Languages from the site profile**, never a fixed `de/en/uk/da`.
- **A helper flag is a candidate.** Every finding in the report has been checked against the
  entry text and, for content claims and verbatim misses, against the source (§0b).
  Language-detection flags and OCR misses are routinely false — say which were dismissed.
- **Per-key rules live in `cite-source`.** Do not restate or override them here; if a rule
  changes there, this skill follows.
