# Architecture

## Pipeline

```
  ┌──────────────┐      ┌──────────────┐      ┌────────────────┐      ┌──────────┐
  │   A: source  │ ───▶ │  B: computed │ ───▶ │ C: categorized │ ───▶ │   HTML   │
  │    (YAML)    │      │  (in-memory) │      │   (in-memory)  │      │  (site/) │
  └──────────────┘      └──────────────┘      └────────────────┘      └──────────┘
       edited              compute.py           categorize.py        location.html.j2
      by hand                                                            (Jinja2)
```

### Layer A — Source data

Hand-edited YAML. The only layer humans modify.

- `data/shared/fuesse.yml` — global Münzfuß definitions (currently 12 fuesse, including the placeholder `seed_unsorted`)
- `data/shared/mints.yml` — mint metadata (nomisma.org references where available)
- `data/locations/<location>.yml` — per-location phases + coins
- `data/locations/<location>-references.yml` — bibliography sidecar (refs cited inline as `<sup>[N]</sup>`)
- `data/i18n/ui.yml` — UI strings (column headers, badges, buttons)
- `data/i18n/issuing_entities.yml` — political-entity metadata (royal_holstein, gottorp_duchy, danish_realm, hanseatic_hamburg, hanseatic_lubeck, …)
- `config/theme.yml` — colors, typography

### Layer B — Computed

For each coin, derive fields from raw input using `fuesse.yml` lookups:

| Field | Formula |
|---|---|
| `weight_fein` | `weight_rough × fineness` |
| `soll_fein` | lookup in `fuesse[coin.fuss].fractions[coin.fraction]` |
| `delta_g` | `weight_fein − soll_fein` |
| `delta_pct` | `delta_g / soll_fein × 100` |
| `within_remedium` | `abs(delta_pct) ≤ 1.0` (boolean) |
| `implied_fuss` | for silver kurant: `233.856 / weight_fein`; for gold: `233.856 / weight_rough` |
| `catalog_groups` | grouped catalog refs (KM#, Hede#, Sieg#, Schou#, etc.) parsed from `coin.catalog` for rendering |

Scheidemünzen have `weight_fein` and `soll_fein` but `within_remedium` is computed differently (typically negative — that's the design). `implied_fuss` is conceptually invalid for Scheide and rendered as `—`.

When a measurement field is given as a list of `{value, source}` entries (instead of a scalar), the computer normalises it with `normalise_field` and renders alt-source tooltips per reading.

Coins assigned to `fuss: seed_unsorted` (the bulk-import placeholder) skip soll/delta computation — `seed_unsorted` has empty `fractions`, so no lookup runs and the delta column is blank.

Optional debug dump: `output/debug/<location>.computed.json`.

### Layer C — Categorized

Group computed coins:

```
location
  └─ fuss_order[]                  # rendered in this order
      └─ fuss
          └─ phases[]
              └─ phase (id, title, year_from..year_to, description, optional context)
                  ├─ kurant_coins[]   (sorted by year_first)
                  ├─ scheide_coins[]
                  └─ tarif_coins[]    (rare, only Kronemønt-like)
```

Each level carries resolved i18n text (the target language is selected before rendering).

### Layer HTML — Rendered

Jinja2 templates consume the categorized tree. One render per (location, language).

- `templates/landing.html.j2` — root index, lists locations as cards
- `templates/location.html.j2` — single location page (phases, coin tables, references, methodology)
- `templates/partials/` — reserved for future reusable blocks; currently empty (location.html.j2 inlines everything)

The landing index hides any location that has at least one coin under `fuss: seed_unsorted` — that location's per-language pages still build and are reachable by direct URL, the card just doesn't render. As soon as the location's last seed entry is reclassified into a real Müntzfuß, the next build re-includes the card automatically.

## Schema (Pydantic 2 models, `scripts/lib/schema.py`)

The actual schema is the source of truth — this is a summary. Key types:

```python
class I18nText(BaseModel):
    de: str
    en: str | None = None
    uk: str | None = None
    # Fallback order: target → en → de. `de` is mandatory; EN/UK fall back.

class Fraction(BaseModel):
    name: str | None = None    # "1/1", "2/3", "1/12"
    soll_rau_g: float | None   # gold: required; silver: optional
    soll_fein_g: float

class Fuss(BaseModel):
    name: I18nText
    historical_name: str | None = None
    metal: Literal["silver", "gold"]
    grid_unit_g: float          # 233.856 for Cöllnische Marck
    grid_stops: float           # 9.25, 67, etc.
    fineness_standard: float    # 0.875, 0.98611...
    fineness_display: str | None = None
    description: I18nText | None = None
    grundwerte: Grundwerte | None = None  # rendered "base values" block
    fractions: dict[str, Fraction]
    events: FussEvents | None = None       # first_adoption, first_mint, last_mint, std_end, demonetisation
    # `id` is set on load from the dict key.

class Phase(BaseModel):
    id: str                     # "A", "B", …
    year_from: int
    year_to: int
    from_label: str             # "ca. 1625" — free-form display
    to_label: str               # "15. Juli 1726"
    title: I18nText
    description: I18nText | None = None
    context: I18nText | None = None  # longer `<details>` block
    mt_caption: I18nText | None = None  # caption for the per-phase table

class CatalogRefs(BaseModel):
    km: str | None = None
    lange: str | None = None
    hede: str | None = None
    sieg: str | None = None
    schou: str | None = None
    fr: str | None = None
    dav: str | None = None
    bruun_lot: str | None = None
    numista: str | None = None    # N#XXXXXX
    others: list[str] = []        # «KM-DK# 56», «Aagaard-1.1», «Lange# 80 A», …

class CoinSource(BaseModel):
    type: Literal["numista", "ucoin", "auction", "museum", "literature", "web"]
    url: str | None = None
    ref: str | None = None
    note: str | None = None

class Coin(BaseModel):
    id: str                       # "km-146-chr-albrecht-1689" / "km-x031-chr-iv-1618-eighth"
    fuss: str                    # FK to fuesse
    phase: str                    # FK to phases (within this location's fuesse)
    kind: Literal["kurant", "scheide", "tarif", "tarif_subunit", "gedenk"]
    nominal: str                  # exactly as on the coin
    year_label: str               # "1689", "1787–1808", "1771 (frozen)"
    year_first: int
    year_last: int | None = None
    year_ranges: list[tuple[int, int]] | None = None  # explicit non-contiguous spans
    ruler: str | None = None      # standard spelling
    mint: str | None = None
    mint_verified: bool = True
    mintmaster: str | None = None
    catalog: CatalogRefs
    metal: Literal["silver", "gold", "billon", "copper"]
    fineness: float | list[FieldValue] | None = None  # scalar OR per-source list
    fineness_verified: bool = True
    weight_rough_g: float | list[FieldValue] | None = None
    weight_rough_label: I18nText | None = None        # for ranges like "2,54–2,60 g"
    weight_rough_verified: bool = True
    diameter_mm: float | list[FieldValue] | None = None
    diameter_mm_verified: bool = True
    fraction: str | None = None   # "1/12", "1/1" — for soll lookup
    issuing_entity: str | None = None  # FK to issuing_entities.yml
    fuss_refs: list[str] | None = None  # cross-reference Münzfüße that also covered this coin
    inscription_obv: str | None = None
    inscription_rev: str | None = None
    note: I18nText | None = None
    sources: list[CoinSource]
    verified: bool = True
    verification_note: I18nText | None = None

class Location(BaseModel):
    id: str
    name: I18nText
    summary: I18nText
    fuss_order: list[str]                       # render order of fuesse
    timeline: Timeline | None = None            # per-location timeline schematic
    fuss_periods: dict[str, FussPeriod]         # per-fuss framing within this location
    phases: dict[str, list[Phase]]              # per-fuss list of phases (in order)
    coins: list[Coin]
    methodology_heading: I18nText | None = None
    methodology: I18nText | None = None
```

For the FieldValue / Timeline / Grundwerte / FussEvents / FussPeriod sub-types and the cross-reference validators, read `scripts/lib/schema.py` directly — it is short and self-documenting.

## Build script (`scripts/build.py`)

Top-level entry point. Pseudocode of what `main()` does (real names, not aliased):

```python
def main():
    args = parse_args()
    fuesse = load_fuesse()
    ui = load_ui()
    issuing_entities = load_issuing_entities()
    theme = load_theme()
    locations = load_locations(filter_id=args.location)        # auto-discovers data/locations/*.yml

    if not cross_ref_check(locations, fuesse):                  # phase ↔ fuss validation
        sys.exit(1)
    if args.validate_only:
        return

    languages = [args.lang] if args.lang else DEFAULT_LANGS

    for loc in locations:
        build_location(loc, fuesse, theme, ui, languages, env,
                       debug=args.debug, repo_url=args.repo_url,
                       issuing_entities=issuing_entities, base_url=base_url)

    if len(locations) > 1 or not args.location:
        build_landing(locations, ui, theme, languages, env,
                      repo_url=args.repo_url, base_url=base_url)
        # build_landing internally filters out locations that still
        # carry coins under fuss=seed_unsorted (placeholder bucket).

    generate_assets(theme)
```

Per-location rendering inside `build_location` calls `compute_location()` (A → B), then `categorize()` (B → C), then renders `location.html.j2` once per language.

## Seed pipelines (external sources → location pages)

When an external numismatic catalogue (Hede 1971, ucoin, Bruun, IKMK, …) contains coins that belong on a location page, the data passes through a fixed four-tier pipeline before reaching the rendered HTML. Each tier writes a file the next tier reads, so the transformation is inspectable at every step and re-runnable from any tier.

```
  ┌───────────────┐    ┌──────────────────┐    ┌─────────────────┐    ┌──────────────────┐    ┌──────────┐
  │  Tier 0       │    │  Tier 1          │    │  Tier 2         │    │  Tier 3          │    │   HTML   │
  │  raw fetch    │───▶│  typed parse     │───▶│  Coin-schema    │───▶│  build merge     │───▶│  (site/) │
  │  (HTML / API) │    │  (per-page JSON) │    │  seed (YAML)    │    │  + render        │    │          │
  └───────────────┘    └──────────────────┘    └─────────────────┘    └──────────────────┘    └──────────┘
  scripts/fetch_*.py   scripts/parse_*.py   scripts/maintenance/    scripts/build.py
  scripts/cache/       scripts/cache/       data/seed/<src>/<loc>.yml + canonical
  <src>/<basename>     <src>/<basename>     ↑                       data/locations/<loc>.yml
  .htm / .json         .json + _parsed_     filtering happens HERE
                       index.json           (year cap, mint, dedup)
```

**Tier 0 — raw fetch.** `scripts/fetch_<source>.py` discovers + downloads pages from the source's published surface and caches each as `scripts/cache/<source>/<basename>.htm` (or `.json` for JSON APIs). Idempotent: skips already-cached files. The cache is the project's own copy of the source, so subsequent tiers can re-run without re-hitting the network.

Concrete: `scripts/fetch_hede.py` runs `discover` (probes `/{ruler}hede{N}.htm` overviews and walks them for per-coin URLs) → `fetch` (downloads each unique URL). Writes `_manifest.json` for reproducibility.

**Tier 1 — typed parse.** `scripts/parse_<source>.py` reads each cached page and emits a sibling `<basename>.json` with structured fields the project's tooling can query: ruler, mint, years + rarity, nominal, specs (Bruttovægt / Finhed / Finvægt / Marken-fin-udbragt-til), catalog refs (Hede, Schou, Sieg, …), litteratur, eksemplarer. A side-car `_parsed_index.json` aggregates a `composite_key → canonical_file` map so cross-references resolve cleanly.

Concrete: `scripts/parse_hede.py` parses the 669 Hede pages into typed JSON (97% coverage on years, 100% on ruler + catalog refs, 74% on specs). Multi-Hede pages (one page covering Hede 61/62AB/63/64) get `specs.by_hede` keyed by the sub-Hede tag preceding each spec block.

**Tier 2 — Coin-schema seed.** `scripts/maintenance/build_<source>_<location>_seed.py` filters the typed cache to a particular location's scope and shapes each accepted entry into a Coin-schema YAML record. Filtering decisions (year cap, mint set, canonical-resolution dedup, multi-nominal split rules) live HERE — at this tier, never in the build script. The output file IS the canonical intermediate the build reads; the build trusts what's in it.

Concrete: `scripts/maintenance/build_hede_denmark_seed.py` consumes Tier-1 JSON + the aggregate index and writes `data/seed/hede/denmark.yml`. Three filters apply:
- **Mint**: Danish royal mints only (København / Frederiksborg / Helsingør / Kbh+Altona). Glückstadt / Altona / Flensborg / Haderslev belong to a future `schleswig_holstein.yml` seed.
- **Canonical resolution**: cross-reference sub-Hedes (e.g. f3h68's mention of Hede 61/62AB/63) emit only from the canonical owner (f3h62); footnote pages (c4h111note) emit nothing on top of c4h111.
- **Year scope**: `--year-to <YEAR>` cap (default 1914 — project scope per CLAUDE.md). Stored in the seed file's header as `scope_year_to: <YEAR>` so a future reader knows the scope without re-running.

**Tier 3 — build merge.** `scripts/build.py::_merge_seeds_into_raw(loc_id, raw)` runs once per location during `load_locations`. It scans `data/seed/*/<loc_id>.yml`, and any file whose stem matches the location id has its `coins:` list appended to the location's own coins **before** pydantic `Location(...)` validation. Duplicate ids, missing fuss / phase references, and chronology mismatches are caught in the existing schema check — no separate seed-validation pass.

The build is silent for locations with no matching seed file. When a non-empty seed merge happens, the build prints one line summarising sources + counts, e.g.:

```
🌱 denmark: merged 373 seed coins (373 from hede)
```

**Rendering separation.** Seed coins land in the location's `seed_unsorted` fuss bucket but a **separate phase per source** keeps them visually distinct in the rendered HTML: ucoin seeds → `phase: A`, Hede seeds → `phase: hede`. The location's `phases.seed_unsorted` list defines one Phase entry per source with its own title (`Bulk-Seed · ucoin` / `Bulk-Seed · Hede 1971 (danskmoent.dk)`) so each pile renders in its own sub-section without intermixing rows.

**Promotion path (out of seed → into a real Müntzfuß).** Once a seed coin is researched enough to assign a Müntzfuß and phase:
1. Cut the YAML block from the seed file (or just leave it — the build is idempotent).
2. Paste into `data/locations/<loc>.yml` under the chosen fuss + phase coin block.
3. Drop `fuss: seed_unsorted` / `phase: <source>`; set the real fuss + phase.
4. Cross-check the source page linked in `sources[0]`; flip `*_verified: true` field-by-field per CLAUDE.md §5.
5. Re-run `python scripts/build.py --validate-only` to catch chronology / cross-ref drift.

Seeds are append-only intake. Promotions move coins *out* of the seed bucket into proper periodisation; the seed file shrinks as more entries are properly classified, but never grows by hand-editing (only by re-running the generator).

**Per-source documentation.** Each source's pipeline is described in detail in its own doc:
- Hede 1971 (danskmoent.dk): `data/seed/hede/README.md` (filtering decisions + coverage stats + promotion-path checklist)
- Bruun (Stack's Bowers Part II): `data/seed/bruun/README.md` (formerly active; now empty after all 7 territories were promoted)
- ucoin (legacy bulk imports): `docs/IKMK_HARVEST.md` + `scripts/audit_ucoin_categories.py` docstring

## Data validation (build-time checks)

Run via `python scripts/build.py --validate-only`.

- Pydantic schema validation per location file (types, required fields, literals)
- Every `coin.fuss` must exist in `fuesse.yml`
- Every `coin.phase` must exist in that location's `phases[coin.fuss]`
- `coin.fraction` (if given) must exist in `fuss.fractions`
- Unique `coin.id` within a location
- `I18nText.de` always non-empty (DE is the canonical source)
- Issuing-entity FKs resolve against `data/i18n/issuing_entities.yml`
- Duplicate-key check in source YAML (catches typos that would silently overwrite)

## ucoin-categorisation pipeline (`scripts/audit_ucoin_categories.py`)

Out-of-band tool — not part of the build. Reads the cached ucoin URL index (`scripts/cache/ucoin/_url_index.json`) plus all location YAMLs, and bins each entry into:

```
Active triage (Holstein candidates from new harvests):
  B_HOLSTEIN_NEW · C_HOLSTEIN_KM_VARIANT · D_DENMARK_HOLSTEIN_MINT
  · E_DENMARK_AMBIGUOUS · J_HOLSTEIN_TO_ADD

Future-location seed (ungrouped — currently all 0 since the seed
buckets were bulk-imported into denmark/hamburg/lubeck.yml):
  H_DENMARK_SEED · X_HAMBURG_SEED · X_LUBECK_SEED

Silently dropped (audit trail in commit history):
  processed_in_base   — already attached to a base coin via tid bridge
  data_quality_skip   — the single MANUAL_OVERRIDES entry for tid 163671
```

Decision precedence:

1. Direct ucoin-tid bridge — if any location's `coin.sources[].url` contains `tid=NNNN`, silently drop (already in base).
2. MANUAL_OVERRIDES — defensive guards for entries with corrupt source data.
3. Hanseatic source filter — split by city (Hamburg / Lübeck).
4. Strict KM+denom+year+fineness match against base — silent drop (already in base).
5. KM-overlap fallback — B/C/D/E for Holstein candidates; H_DENMARK_SEED for everything else.

After every bulk-import or manual coin addition, re-run the categoriser; the dropped count grows and the active buckets re-stabilise.

## GitHub Actions (deploy)

```yaml
name: Build and deploy
on:
  push:
    branches: [main]
permissions:
  contents: read
  pages: write
  id-token: write
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: {python-version: '3.12'}
      - run: pip install -r requirements.txt
      - run: python scripts/build.py
      - uses: actions/upload-pages-artifact@v3
        with: {path: site/}
  deploy:
    needs: build
    runs-on: ubuntu-latest
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    steps:
      - uses: actions/deploy-pages@v4
        id: deployment
```

## Scaling to new locations

Adding `data/locations/bremen.yml` is additive — nothing in existing code changes. The build script iterates `data/locations/*.yml` automatically (skipping `*-references.yml` sidecars). Landing page is regenerated with the new card (provided the new location has no coins under `seed_unsorted`).

If the new location uses a Münzfuß not yet defined, add the mathematical definition to `data/shared/fuesse.yml` once; subsequent locations can reference it. E.g., Bremen's reconstructed 13⅓ silver-Münzfuß at 71/72 fineness becomes a global entry (see `docs/DECISIONS.md`).

If the new location involves a new political entity, add it to `data/i18n/issuing_entities.yml` (see how `hanseatic_hamburg` / `hanseatic_lubeck` were added).

## Language fallback

Primary language = DE (source research language). Fallback chain: `target → en → de`. Missing EN/UK translations fall through to DE silently in production.

## Non-goals (scope boundaries)

- Not a search engine. No client-side search over coins.
- Not a database. YAML is the storage layer. Don't shoehorn in SQLite or JSON-APIs.
- Not a CMS. Edits are code commits.
- Not multi-user. Single researcher + Claude Code sessions.
- No JavaScript-heavy interactions. Language switch is a link; sort/filter (if added) must degrade gracefully.
