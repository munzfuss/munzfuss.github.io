# Architecture

## Pipeline

```
  ┌──────────────┐      ┌──────────────┐      ┌──────────────┐      ┌─────────┐
  │   A: source  │ ───▶ │  B: computed │ ───▶ │ C: categorized│ ───▶ │  HTML   │
  │   (YAML)     │      │  (in-memory) │      │  (in-memory) │      │ (site/) │
  └──────────────┘      └──────────────┘      └──────────────┘      └─────────┘
       edited              compute.py           categorize.py          render.py
     by hand                                                          (Jinja2)
```

### Layer A — Source data

Hand-edited YAML. The only layer humans modify.

- `data/shared/stopes.yml` — global Münzfuß definitions
- `data/shared/glossary.yml` — term translations
- `data/locations/<location>.yml` — per-location phases + coins
- `data/i18n/ui.yml` — UI strings
- `data/i18n/boilerplate.yml` — recurring methodological paragraphs
- `config/theme.yml` — colors, typography

### Layer B — Computed

For each coin, derive fields from raw input using `stopes.yml` lookups:

| Field | Formula |
|---|---|
| `weight_fein` | `weight_rough × fineness` |
| `soll_fein` | lookup in `stopes[coin.stope].fractions[coin.fraction]` |
| `delta_g` | `weight_fein − soll_fein` |
| `delta_pct` | `delta_g / soll_fein × 100` |
| `within_remedium` | `abs(delta_pct) ≤ 1.0` (boolean) |
| `implied_stope` | for silver kurant: `233.856 / weight_fein`; for gold: `233.856 / weight_rough` |

Scheidemünzen have `weight_fein` and `soll_fein` but `within_remedium` is computed differently (typically negative — that's the design). `implied_stope` is conceptually invalid for Scheide and should be null.

Optional debug dump: `output/debug/<location>.computed.json`.

### Layer C — Categorized

Group computed coins:

```
location
  └─ stopes[]
      └─ stope
          └─ phases[]
              └─ phase (id, title, date_range, description)
                  ├─ kurant_coins[]    (sorted by year_first)
                  ├─ scheide_coins[]
                  └─ tarif_coins[]     (rare, only Kronemønt-like)
```

Each level carries resolved i18n text (the target language is selected before rendering).

### Layer HTML — Rendered

Jinja2 templates consume the categorized tree. One render per (location, language).

- `landing.html.j2` — root index, lists locations
- `location.html.j2` — single location page
- `partials/stope_card.j2` — one stope block
- `partials/phase_block.j2` — one phase within stope
- `partials/subcat_divider.j2` — Kurant/Scheide divider
- `partials/coin_row.j2` — single `<tr>`

## Schema (Pydantic models, `scripts/lib/schema.py`)

```python
class I18nText(BaseModel):
    de: str
    en: str | None = None
    uk: str | None = None
    # Fallback order: target → en → de. `de` is mandatory; EN/UK fall back.

class Fraction(BaseModel):
    name: str                  # "1/1", "2/3", "1/12" etc.
    soll_rau_g: float | None   # gold: required; silver: optional
    soll_fein_g: float

class Stope(BaseModel):
    id: str                    # "reichsdukatenfuss"
    name: I18nText
    metal: Literal["silver", "gold"]
    grid_unit_g: float         # 233.856 for Cöllnische Marck
    grid_stops: float          # 9.25, 67, etc.
    fineness_standard: float   # 0.875, 0.98611...
    fractions: dict[str, Fraction]
    description: I18nText | None = None

class Phase(BaseModel):
    id: str                    # "A", "B"...
    from_label: str            # "ca. 1625" — free-form display
    to_label: str              # "15. Juli 1726"
    year_from: int             # 1625 — for sorting, bounds checking
    year_to: int               # 1726
    title: I18nText
    description: I18nText | None = None
    context: I18nText | None = None  # longer `<details>` block

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
    others: list[str] = []

class Coin(BaseModel):
    id: str                       # "km-146-chr-albrecht-1689"
    stope: str                    # FK to stopes
    phase: str                    # FK to phases (within this location's stopes)
    nominal: str                  # exactly as on coin
    year_label: str               # "1689", "1787–1808", "1771 (frozen)"
    year_first: int               # 1689, 1787, 1771 — sort key
    year_last: int | None = None
    ruler: str | None = None      # standard spelling
    mint: str | None = None
    mintmaster: str | None = None # MM initials / name
    catalog: CatalogRefs
    metal: Literal["silver", "gold", "billon", "copper"]
    fineness: float | None = None # null for copper; (?) if estimated
    fineness_verified: bool = True
    weight_rough_g: float | None = None
    weight_rough_verified: bool = True
    diameter_mm: float | None = None
    kind: Literal["kurant", "scheide", "tarif", "gedenk"]
    fraction: str | None = None   # "1/12", "1/1" — for soll lookup
    inscription_obv: str | None = None
    inscription_rev: str | None = None
    note: I18nText | None = None
    sources: list[str]
    verified: bool = True
    verification_note: I18nText | None = None

class Location(BaseModel):
    id: str
    name: I18nText
    summary: I18nText
    stope_usage: list[StopeUsage]  # which global stopes are used + phase defs

class StopeUsage(BaseModel):
    stope: str                     # FK
    phases: list[Phase]
    coins: list[Coin]
```

## Build script (`scripts/build.py`)

```python
def main():
    args = parse_args()
    
    # Load shared
    stopes = load_stopes("data/shared/stopes.yml")
    glossary = load_glossary("data/shared/glossary.yml")
    ui = load_i18n("data/i18n/ui.yml")
    boilerplate = load_i18n("data/i18n/boilerplate.yml")
    theme = load_theme("config/theme.yml")
    
    locations = load_locations("data/locations/", filter=args.location)
    languages = args.lang or ["de", "en", "uk"]
    
    for loc in locations:
        validate(loc, stopes)                        # schema + cross-ref checks
        computed = compute(loc, stopes)              # A → B
        if args.debug:
            dump_json(computed, f"output/debug/{loc.id}.computed.json")
        categorized = categorize(computed)           # B → C
        if args.debug:
            dump_json(categorized, f"output/debug/{loc.id}.categorized.json")
        
        for lang in languages:
            resolved = resolve_i18n(categorized, lang, fallback_chain=[lang, "en", "de"])
            html = render_location(resolved, ui[lang], theme, lang=lang)
            write(f"site/{loc.id}/{lang}/index.html", html)
    
    landing = render_landing(locations, ui, theme, languages)
    write("site/index.html", landing)
    copy_assets("templates/assets/", "site/assets/")
```

## Data validation (build-time checks)

- Every `coin.stope` must exist in `stopes.yml`
- Every `coin.phase` must exist in that location's `phases` for that stope
- `coin.year_first` must be within `phase.year_from ≤ year_first ≤ phase.year_to`
- `coin.fraction` (if given) must exist in `stope.fractions`
- Unique `coin.id` within a location
- `I18nText.de` always non-empty (DE is the canonical source)
- Warnings for: missing `verification_note` when `verified: false`; missing source URLs

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

Adding `data/locations/bremen.yml` is additive — nothing in existing code changes. The build script iterates `data/locations/*.yml` automatically. Landing page is regenerated.

If Bremen introduces a stope not yet in `stopes.yml`, add the mathematical definition there once; subsequent locations can reference it. E.g., Bremen's reconstructed 13⅓ silver-Münzfuß at 71/72 fineness becomes a global entry.

## Language fallback

Primary language = DE (source research language). Fallback chain: `target → en → de`. Missing EN/UK translations fall through to DE with a class marker `.untranslated` that the style can make visible (e.g., subtle yellow background) during development. For production, the fallback is silent.

## Non-goals (scope boundaries)

- Not a search engine. No client-side search over coins.
- Not a database. YAML is the storage layer. Don't shoehorn in SQLite or JSON-APIs.
- Not a CMS. Edits are code commits.
- Not multi-user. Single researcher + Claude Code sessions.
- No JavaScript-heavy interactions. Language switch is a link; sort/filter (if added) must degrade gracefully.
