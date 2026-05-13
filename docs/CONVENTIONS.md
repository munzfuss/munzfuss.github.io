# YAML Conventions

Concrete rules for writing and editing data files.

## Formatting

- 2-space indentation (no tabs)
- Line length: no hard limit, but prefer ≤120 for readability
- Use `|` for multi-line strings when preserving newlines; use `>` for folded; use `"..."` for single-line with special chars
- Numbers without units: floats for measurements (`3.44191`), ints for years (`1689`)
- Dates: prefer free-form labels (`"ca. 1625"`, `"15. Juli 1726"`) in `*_label` fields; use integer years in `year_*` fields for sorting

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

### `de` (German) — period-correct
> Full orthography table + register rules: **CLAUDE.md §2 + §2a**. The full forbidden-forms table (Müntz/not Münz, biß/not bis, Marck/not Mark, Cöllnische Marck/not Kölnische Mark, etc.) is canonical there; the «Cyrillic-transliteration trap» check for uk renderings of German compounds also lives there. Keep the rendered output academic-register (§2a) — no colloquialisms, no editorial exclamations, no first-person voice.

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
- Мюнцфус (transliterated), талер, куранттaлер
- Rare terms: keep in German italics with Ukrainian gloss in parentheses on first use
- Speciestaler → спецієсталер; Kurantmünze → курантна монета; Scheidemünze → розмінна монета (білонна)
- Decimal comma (not period)

## Common term translations

See `docs/GLOSSARY.md` for the full mapping. Quick reference for YAML writing:

| de | en | uk |
|---|---|---|
| Müntzfuß | Münzfuß | Мюнцфус |
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
