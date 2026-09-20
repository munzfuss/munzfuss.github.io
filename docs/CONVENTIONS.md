# YAML Conventions

Concrete rules for writing and editing data files.

## Formatting

- 2-space indentation (no tabs)
- Line length: no hard limit, but prefer ≤120 for readability
- Use `|` for multi-line strings when preserving newlines; use `>` for folded; use `"..."` for single-line with special chars
- Numbers without units: floats for measurements (`3.44191`), ints for years (`1689`)
- Dates: prefer free-form labels (`"ca. 1625"`, `"15. Juli 1726"`) in `*_label` fields; use integer years in `year_*` fields for sorting

## Programmatic edits — ALWAYS via `lib/yaml_io.py`, never ad-hoc round-trip

The project's data YAMLs are written by **two serializers with four distinct
format families** (three axes: serializer / line-width / ruamel sequence-offset).
Loading a file and re-dumping it through the WRONG config silently reformats the
**entire** file — a multi-thousand-line spurious diff from a one-field edit. This
has burned several sessions. The rule:

- **Never** instantiate a bare `ruamel.yaml.YAML()` / `yaml.dump(...)` with
  hand-typed `indent`/`width` to edit a data file. Route everything through
  `scripts/lib/yaml_io.py`, which **auto-detects the family from the path**.
- **Single-field edits → `yaml_io.edit_coin_field(path, coin_id, field, value)`.**
  It is line-based (no serialization round-trip), so it touches only the target
  field's line(s) — immune to the reformat trap regardless of family. `value` may
  be a scalar, a list (block-rendered; 1-element collapses to scalar), or `None`
  (remove the field). Pass `expect_contains=...` to assert you're editing the
  value you think you are.
- **Structural edits (add/remove/reorder coins) → `yaml_io.load()` / `save()`.**
  Family-aware: load returns `(ctx, doc)`, `save(ctx, path, doc)` writes with the
  file's own serializer + settings.

- **A line you compose yourself → `yaml_io.canonical_lines(path, field, value,
  indent)`.** It renders the key/value through the real serializer at the real
  column and hands back the lines to splice. Formatting the line by hand
  instead breaks nothing today — it is legal YAML and the build passes — but a
  scalar past the family's fold width raises the file's round-trip residual,
  and that is the spurious diff the NEXT structural edit reads past.

The families (path prefix → serializer / width / seq-offset): `data/v2/final/`
+ `data/v2/seed_unified/` + `data/v2/classification_decisions/` + `data/v2/seed/`
→ ruamel / 200 / seq4-off2 (the four were unified onto this profile in 2026-07,
curator decision B — the table here said PyYAML/120 until 2026-09-20, two
months in which `yaml_io.py`'s own docstring was right and this one was wrong); `data/locations/` → ruamel / 4096 / **seq2-off0** (dash-flush block
lists); `data/shared/` + `data/i18n/` → ruamel / 4096 / seq4-off2. The
`data/locations` (offset 0) and `data/shared` (offset 2) families LOOK alike but
reformat each other. `data/v2/match_uncertainty/` stays on PyYAML and is
gitignored, so it is measured by nothing and never appears in a diff.

**Two guards, and they fire on different things.**
`scripts/maintenance/test_yaml_io_roundtrip.py` pins each family's residual
baseline and catches a SERIALIZER-CONFIG regression — run it after touching
`yaml_io.py`. That trigger is right for what it guards and wrong for what
actually drifts: residual grows from editing DATA, not the module, so between
2026-07 and 2026-09 `data/shared/fuesse.yml` went from a residual of 0 to 614
lines without a word. The pre-commit hook's **Check 9**
(`check_yaml_residual.py --staged`) covers that half — a commit may leave the
existing backlog alone but may not add to it. `--scan` prints the whole table.

## File naming

- Locations: `data/locations/<short-name>.yml` — lowercase. Compound region names use **underscores** (`schleswig_holstein.yml`), not hyphens — keeps file ids and URL paths uniform with Python identifiers used in maintenance scripts (`SCHLESWIG_HOLSTEIN`).
- References sidecar: `data/locations/<short-name>-references.yml` — single hyphen separator marking the sidecar. Build pipeline auto-attaches it when present.
- Shared: `data/shared/<purpose>.yml`
- IDs inside files: same convention (lowercase, underscores for compound names).

## Coin IDs

Unique within a location. Pattern: `<km>-<ruler-short>-<year_first>[-variant]`

Examples:
- `km-146-chr-albrecht-1689`
- `km-138-1-chr-vii-1787`
- `km-721-chr-viii-1841-fk`
- `km-73-fr-iv-1698-stapelholm`

Variant suffix for disambiguation when the base ID collides (e.g., multiple entries for same KM + year).

## Inline i18n (Strategy A)

Every translatable field is an object:

```yaml
title:
  de: "Etablierung unter dänischer und gottorpischer Herrschaft"
  en: "Establishment under Danish and Gottorp rule"
  uk: "Становлення під данським і готторпським правлінням"
```

**DE is mandatory.** EN/UK can be omitted during drafting — build falls back to EN then DE with an `.untranslated` class marker.

For short fields, inline flow style is acceptable:

```yaml
title: {de: "Phase A", en: "Phase A", uk: "Фаза А"}
```

For paragraphs, use block style with `|` or `>`:

```yaml
description:
  de: |
    Ausführliche Beschreibung, mehrzeilig.
    Zweite Zeile bleibt als zweite Zeile.
  en: |
    Detailed description, multi-line.
    Second line stays a separate line.
```

## Which fields are translated

**Translate (i18n object):**
- `title`, `subtitle`, `description`, `context`, `summary`
- `note` (Bemerkung)
- `verification_note`
- Phase labels that are content (not structural IDs)

**Do NOT translate (literal string):**
- `nominal` — coin inscription, preserved as-is (e.g., `"8 Skilling Danske"`, `"VIII SCHILLING"`)
- `inscription_obv`, `inscription_rev` — literal coin legends
- `ruler` — standard academic spelling, same across languages (`"Christian VII."`, `"Friedrich IV."`)
- `mint` — place name (`"Tönning"`, `"Altona"`)
- `mintmaster` — initials or name
- Catalog references (`km`, `lange`, etc.)
- `year_label` — date formats are handled by the formatter if needed
- Technical Münzfuß names (`"9¼-Fuß"`) — identical across languages
- `sources` — URLs and citations, literal
- Numerical values (numbers) — formatter handles decimal separator

## Translation style

Each language follows its own orthographic conventions:

### `de` (German) — source form first, period register as house style
> Full orthography table + register rules: **CLAUDE.md §2 + §2a**. The three tiers — source form untouchable in quotes / titles / URLs / named instruments; standard names identical across all three languages; period register RECOMMENDED (never mandatory) in our own DE prose — are canonical there, together with the preferred-form table (Müntz, biß, Marck, Cöllnische Marck, …); the «Cyrillic-transliteration trap» check for uk renderings of German compounds also lives there. Keep the rendered output academic-register (§2a) — no colloquialisms, no editorial exclamations, no first-person voice.

Quick illustrative anchors:
- Müntz, biß, Marck, Cöllnische Marck, Thaler, Courant, Pfund Banco
- Danish terms preserved: Rigsdaler, Kurantmøntfod, Forordning
- Historical place spellings: Tönning, Altona, Glückstadt

### `en` (English) — modern scholarly
- Münzfuß (keep German term), Thaler (keep German), Groschen
- "Speciestaler" for Speciesthaler when referring to coin
- Danish terms preserved as in German
- Transliterate only where English has a standard form

### `uk` (Ukrainian)
- **A named standard is NEVER transliterated or translated away.** `Reichsdukatenfuß`,
  `Kurantmøntfod`, `9¼-Thaler-Fuß` keep their original form in Ukrainian text, per
  CLAUDE.md §2 tier 2 + the i18n policy. A Ukrainian gloss may follow **in parentheses
  after** the original on first use — «Reichsdukatenfuß (імперська дукатна стопа)» —
  but **never in place of it**. «Мюнцфус» and friends are transliterations, i.e.
  translations, and are forbidden as replacements. (Measured 2026-09-02: the data
  carries zero «Мюнцфус» — this line documents established practice, it does not
  change it.)
- The GENERIC concept, as opposed to a named standard, does translate normally:
  «стопа» / «монетна стопа» for Müntzfuß-as-a-common-noun. That is what the corpus
  uses (116 inflected occurrences).
- Coin denominations in flowing historical prose may be localised — «талер»,
  «дукат», «спецієсталер». In FORMAL slots (Rechnungsfraktionen, Grundwerte rows,
  structured key/value pairs, table headers) the period form stays intact per the
  i18n policy.
- Rare terms: keep in German italics with Ukrainian gloss in parentheses on first use
- Kurantmünze → курантна монета; Scheidemünze → розмінна монета (білонна)
- Decimal comma (not period)

## Common term translations

See `docs/GLOSSARY.md` for the full mapping. Quick reference for YAML writing:

| de | en | uk |
|---|---|---|
| Müntzfuß (generic) | Münzfuß / coinage standard | стопа / монетна стопа |
| *a NAMED standard* | *unchanged* | *unchanged — gloss in parens only* |
| Kurantmünze | current coin / full-value coin | курантна монета |
| Scheidemünze | small change / token coin | розмінна монета |
| Feingehalt | fineness | проба |
| Feingewicht | fine weight | чиста вага |
| Raugewicht | gross weight | повна вага |
| Cöllnische Marck | Cologne mark | кельнська марка |
| Münzmeister | mintmaster | монетний майстер |
| Prägung | strike / mintage | карбування |
| Rechnungseinheit | unit of account | розрахункова одиниця |
| Probeprägung | pattern / trial strike | пробний карбунок |
| Reichsdukatenfuß | Imperial ducat standard | імперський дукатний стандарт |

## Number formatting

Numbers in YAML are plain JSON numbers:

```yaml
weight_rough_g: 3.44191
weight_rough_g: 25.28173
```

The build-time formatter produces:
- `de`: `25,28173 g` (comma)
- `en`: `25.28173 g` (period)
- `uk`: `25,28173 г` (comma + Ukrainian unit)

Never write numbers as strings unless absolutely necessary (e.g., ranges: `"2,54–2,60 g"` for a range must be a string because it's not a single number).

## Ranges

For weight ranges (e.g., KM# 155 real-world weight 2.54–2.60 g), store as string in a dedicated field:

```yaml
weight_rough_g: null
weight_rough_label:
  de: "2,54–2,60 g"
  en: "2.54–2.60 g"
  uk: "2,54–2,60 г"
weight_rough_verified: false
verification_note:
  de: "Realgewicht-Spanne nach Emporium Hamburg Auktion 69 (2013)"
```

For calculations, use midpoint or minimum with a `verification_note` explaining.

## Timeline display anchor vs. standard start (pre-1514 Danish fusses)

The Denmark timeline (`data/v2/locations/denmark.yml::timeline`) starts at the
**1514 Christian-II-Lovkompleks anchor** — the first comprehensive
Danish-Norwegian Møntordning. Some fusses we document have a *standard* that
began **before** 1514 (e.g. `nobel_fod`, first struck 1496 under Hans). The
convention for those:

- **The timeline bar starts at 1514** (the bar's `year_from`), because the
  shared timeline needs one realm-wide anchor and we cannot extend it below
  ~1500 without pulling in a large body of still-unclassified pre-Reformation
  silver coinage that would clutter the page.
- **The fuss description, phase windows and coin specimens are NOT truncated
  at 1514** — they cover the standard from its real start year (the nobel
  description opens «1496–1532»; the phase `from_label` is 1496; the 1496/1502
  Hans specimens render in the coin table). Only the *timeline visualisation*
  is anchored at 1514.
- **Framing of the 1514 Møntordning in prose:** it *de jure* formalised a
  standard already struck *de facto* since 1496 — NOT a retroactive
  application. (Wilcke 7-2 confirms the Summer-1514 Dienis-Blicher-Brev at
  Malmø specifies the Nobel: «16 Stk. paa Marken, 23½ Karat».) The fineness of
  the pre-1514 issues is not independently attested — mark those coin rows
  `fineness_verified: false`.

## Unverified fields marker

```yaml
fineness: 0.5
fineness_verified: false
verification_note:
  de: "Feingehalt nicht in Online-Quelle belegt. Schätzung .500–.625 (Billon) nach Analogie zu KM-186 (CoinVarieties: 'billon')."
  en: "Fineness not documented in online sources. Estimated .500–.625 (Billon) by analogy to KM-186 (CoinVarieties classification: 'billon')."
  uk: "Проба не задокументована в онлайн-джерелах. Оцінка .500–.625 (білон) за аналогією до KM-186."
```

Build script renders `(?)` marker next to the value; tooltip shows the note.

Per-field verified flags currently supported by the schema:
`verified` (overall), `mint_verified`, `fineness_verified`,
`weight_rough_verified`, `diameter_mm_verified`. Each defaults to `True`;
explicitly set to `False` for any value not directly attested by a source.

## Bulk-imported seed coins

Coins imported in bulk from ucoin (currently in `denmark.yml`,
`hamburg.yml`, `lubeck.yml` — see `docs/TODO.md` item D) carry:

```yaml
fuss: seed_unsorted          # placeholder — no fractions, no soll/delta
phase: A                     # single placeholder phase
verified: false              # plus all per-field _verified: false
verification_note:
  de: "Bulk-Import aus ucoin tid NNNN als Seed-Eintrag — vollständige Verifikation per Hede/Wilcke/Bruun ausstehend, Müntzfuß-Klassifikation noch nicht zugewiesen (provisorisch unter «seed_unsorted» geführt)."
```

When triaging a seed coin into its proper Müntzfuß: change `fuss` to the
real one, set `phase` accordingly, replace the bulk-import
`verification_note` with the per-coin rationale, and flip the
`*_verified` flags for each field that's now source-attested.
A location's landing card reappears automatically once it has zero
seed_unsorted coins (see `scripts/build.py::build_landing`).

## Sources

Always provide at least one source. Prefer URLs. Format:

```yaml
sources:
  - type: numista
    url: "https://en.numista.com/catalogue/pieces32842.html"
  - type: auction
    ref: "Bruun Part II, Lot 14465"
    note: "Stack's Bowers Zürich 14–15 March 2025"
  - type: museum
    ref: "IKMK Berlin 18218478"
    url: "https://ikmk.smb.museum/object?id=18218478"
  - type: literature
    ref: "Lange 372"
    note: "Lange: Skandinaviske Mønter 1908/12 (offline)"
```

### Source-ref label shape (rendered as link text in the «Джерела» column)

The `ref` field on a `sources[]` entry is the LINK LABEL that appears in the coin's «Джерела» column. Keep it minimal — describing the coin in the label is the `note` field's job, not the link's.

**Default shape: bare resource name.**

```yaml
sources:
  - type: numista
    url: https://en.numista.com/420365
    ref: Numista                 # ← just the resource name
```

**Domain / resource name comes FIRST.** When the label needs more than the bare resource name (multiple sources from the same resource, or a domain that hosts multiple catalogues like danskmoent.dk → Hede / Galster / Wilcke / NNUM), the resource name leads and the catalog-ref / page-id / lot-id follows in parens (or after a comma for Bruun's standard tuple form):

| Resource | Disambiguator | Label shape |
|---|---|---|
| Numista | N# (page id) | `Numista 420365` |
| ucoin.net | `tid` query param | `ucoin tid 162999` |
| Bruun PDFs (Stack's Bowers) | Bruun collection-id + part / lot | `Bruun Part II, lot 14465` (already standard via Bruun seed builder) |
| IKMK Berlin | object id | `IKMK Berlin 18218478` |
| danskmoent.dk (Hede / Galster / Wilcke) | catalog basename in parens AFTER the domain | `danskmoent.dk (Hede c4h26)`, `danskmoent.dk (Galster 47)`, `danskmoent.dk (Wilcke 1923)` |

**Forbidden #1 — catalog-ref FIRST, domain in parens.** Example caught 2026-05-19:

```yaml
ref: Hede c4h26 (danskmoent.dk)        # ✗ NO — reads as «Hede» being the resource and «danskmoent.dk» as a sub-detail
ref: danskmoent.dk (Hede c4h26)        # ✓ YES — domain (the actual link target) first, catalog ref as disambiguator
```

Why: the LINK target is the domain. A reader scanning the «Джерела» column sees a list of where they can go — the domain is the navigation atom. The catalog ref tells them WHICH page on that domain.

**Forbidden #2 — descriptive prose in the parenthetical.** Examples caught 2026-05-19:

```yaml
ref: "Numista 420365 (KM-73 Gold Krone Christian IV, both 26A+26B)"    # ✗ NO
ref: "Numista 420365"                                                   # ✓ YES (or `Numista (KM-DK 73)` per §BU once auto-derived)

ref: "Bruun Part IV, lot 17076, p. 53 (Hede 26B, ohne Mzz, 1667/6 overdate)"   # ✗ NO
ref: "Bruun Part IV, lot 17076, p. 53 (Hede 26B)"                              # ✓ YES — keep ONLY the sub-index disambiguator
```

Parenthetical content rule: **sub-index disambiguator ONLY**. When the same resource has ≥2 sources on one coin and they differ on a sub-variant axis (Hede sub-letter A/B/C, Krause KM cross-volume, Dav sub-variant), the parens carry that exact sub-index — nothing else. Mintmaster initials, overdate markers, die-variant prose, grade qualifiers, RR / Unik rarity flags — all belong in the coin's `note` field, never in the link label.

The `(KM-73 Gold Krone Christian IV, both 26A+26B)` part of the rejected Numista label was coin-describing prose. The `(Hede 26B, ohne Mzz, 1667/6 overdate)` part of the rejected Bruun label is mostly coin-describing — only `Hede 26B` is the actual sub-index that distinguishes this Bruun lot from its peer (`Bruun Part I, lot 1089` = Hede 26A). The `ohne Mzz, 1667/6 overdate` clauses must move to `note` if they aren't already there.

**Future refinement (tracked in `docs/TODO.md` §BU)** — render-time auto-derivation of the sub-index portion. The convention above describes the manually-curated form; once §BU lands, the curator drops the manual sub-index entirely and the renderer computes it from `catalog.km` dict-form / `catalog.hede` list-form / `_compute_coin` cross-source group analysis.

## Cross-references

When a coin's note refers to another coin, use its ID:

```yaml
note:
  de: |
    Stempelvariante von [km-188-karl-fr-1705]. Siehe auch
    [km-189-karl-fr-1705-variant] für die ohne MM-Signatur.
```

Build script renders `[coin-id]` as internal anchor link. (Optional Phase 2 feature; initially render as plain text.)

## Sorting and ordering

Within YAML files, order entries intuitively (chronologically, by logical grouping). The build script re-sorts for display, so YAML order is for human editors only.

- Phases: by `year_from`
- Coins within phase: by `year_first`, then by catalog (KM#)

## Comments

YAML comments (`# ...`) are welcome for rationale:

```yaml
- id: km-176-fr-iv-1700
  # Non-standard Unterfuß — Friedrich IV. reduced Speciestaler in last year
  # before his death at Klissow (19 July 1702). No secondary literature.
  nominal: "1 Speciestaler"
  verified: false
  ...
```

These are for humans, not rendered.

## Validation errors you'll see

Common build-time errors and their meaning:

- `KeyError: coin references fuss 'X' but not in fuesse.yml` — typo in `coin.fuss` or new fuss needs adding to shared
- `ValidationError: coin year_first=1842 outside phase A range [1813, 1841]` — wrong phase assignment
- `ValidationError: I18nText.de is required` — missing German text (DE is canonical)
- `DuplicateIDError: coin 'km-138-1-chr-vii-1787' defined twice` — same coin ID in file
- `UnknownFraction: fraction '3/7' not in fuesse[9_25_thaler].fractions` — need to add this fraction to shared fuss definition or it's a data error

When in doubt, run `python scripts/build.py --validate-only` and read the full error.

## Script directory layout

Three tiers under `scripts/`, picked by *recurrence pattern*:

- **`scripts/`** — actively used by the build / research workflow. Re-runnable, idempotent, useful right now: `build.py`, the `audit_*.py` validators, `fetch_numista_api.py`, `enrich_from_numista.py`, `build_ucoin_url_index.py`. Also library code under `scripts/lib/`.
- **`scripts/maintenance/`** — lifecycle-bound utilities that aren't part of the build flow but are kept for re-use when the same shape of work recurs (next bulk import, next translation drift sweep, next ucoin re-link). See `scripts/maintenance/README.md` for the per-script log. **Committed** to the repo.
- **`scripts/oneoff/`** — truly throwaway scratch (hardcoded inputs already gone, data migrations consumed, one-time fixes). **Gitignored.** Past examples (now deleted): `cleanup_sources.py`, `migrate_notes.py`, `fix_wrong_numista_urls.py`, `add_new_coins.py` (Gottorp import).

Decision tests for a new script:

- *Will this run regularly as part of build / audit / data refresh?* → `scripts/`.
- *Will this run again on the next phase of similar work, but not on every build?* → `scripts/maintenance/`.
- *Single-shot, hardcoded to data already gone / consumed?* → `scripts/oneoff/` (gitignored).

## Fuß prose surfaces on a location page — which field actually renders

`templates/location.html.j2` (fuss title block) picks ONE of two fields and the
order is not obvious:

```jinja
{% if sp and sp.hintergrund %}   {# .psub — the per-location FussPeriod #}
{% elif sg.fuss.description %}   {# only when hintergrund is absent #}
```

**`hintergrund` wins.** A location whose `fuss_periods.<fuss>` block carries a
`hintergrund` will NEVER render `description` in that block — not the shared
`data/shared/fuesse.yml` one, and not the per-location `description` override
either, even though `_resolve_fuss_with_overrides` faithfully applies it.

Consequences worth knowing before editing:

| field | where it lives | renders when |
|---|---|---|
| `hintergrund` | `fuss_periods.<fuss>` | always, if present — short summary (1-3 sentences) |
| `details` | `fuss_periods.<fuss>` | in the «Details» toggle (`.fuss-hintergrund`) — the place for long-form per-location history |
| `description` | `fuesse.yml` or the `fuss_periods` override | ONLY when the page has no `hintergrund` for that fuss |

So: to change what a **location page** shows for a fuss, edit `hintergrund`
(short) and `details` (long). Editing `description` alone changes nothing there —
it changes the OTHER pages, the ones without a `hintergrund`.

Found 2026-08-16: a rewritten Danish `fuss_periods.reichsdukatenfuss.description`
produced no visible change, and the pre-existing override text turned out never to
have rendered either. Verify a prose edit on the built page, not in the YAML.
