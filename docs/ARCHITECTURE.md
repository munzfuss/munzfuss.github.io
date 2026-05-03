# Architecture

## Pipeline

```
  ┌──────────────┐      ┌──────────────┐      ┌──────────────┐      ┌─────────┐
  │   A: source  │ ───▶ │  B: computed │ ───▶ │ C: categorized│ ───▶ │  HTML   │
  │   (YAML)     │      │  (in-memory) │      │  (in-memory) │      │ (site/) │
  └──────────────┘      └──────────────┘      └──────────────┘      └─────────┘
       edited              compute.py           categorize.py        location.html.j2
     by hand                                                          (Jinja2)
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
