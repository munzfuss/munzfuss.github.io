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

## Data pipeline — 4 phases (HARVEST → SYNTHESIS → SEED → CURATED)

> **Canonical mental model for ALL external-source data flowing into the project.**
> Every byte of coin data that lands on a rendered location page has passed through these 4 phases in order. Skipping a phase or hand-writing data into a later phase without provenance from the earlier phase is forbidden — that bypass is what the «no synthesis without cache» rule (CLAUDE.md §0) is guarding against.
>
> Every transition between phases is **script-driven**. Manual data entry is reserved for project-internal annotation (fuss assignment, hintergrund prose) at Phase 4 ONLY. The pipeline is a **narrowing funnel**: widest at Phase 1, progressively filtered to project scope at each subsequent phase.

```
  Phase 1 HARVEST         Phase 2 SYNTHESIS         Phase 3 SEED           Phase 4 CURATED
  ════════════════        ═════════════════         ═════════════          ═════════════════
  fetch raw bytes    ──▶  parse + structure    ──▶  filter + reshape  ──▶  promote into Fuß
  from web/PDF/API        per-source schema         to Coin schema         + merge/enrich
                                                    + project scope        existing entries

  WIDEST data ────────────────────────────────────────────────────────▶ NARROWEST data
  (everything the     (typed, structured,           (scope-filtered,       (curated, fuss-
   source exposes)     all entries, all years)       Coin-schema YAML       assigned, sourced,
                                                     visible on web as      *_verified per
                                                     seed_unsorted)         CLAUDE.md §5)

  Output:                Output:                    Output:                Output:
  scripts/cache/         scripts/cache/             data/seed/             data/locations/
   <src>/<basename>.htm   <src>/<basename>.json      <src>/<loc>.yml        <loc>.yml
   <src>/<basename>.pdf   <src>/_parsed_index.json   data/seed/             data/locations/
   <src>/_manifest.json   data/seed/<src>/           <src>/<loc>_<scope>.yml <loc>-references.yml
                          (file per src+scope)

  Driver script:         Driver script:             Driver script:         Driver action:
  scripts/fetch_*.py     scripts/parse_*.py         scripts/maintenance/   manual edit + commit
                                                    build_<src>_<loc>_     (or batch-promotion
                                                    seed.py                 script)
```

### Phase 1 — HARVEST (raw fetch)

**Goal:** capture the **widest possible** raw data from the resource into a local cache that lives in the `munzfuss-harvest` submodule (mounted at `scripts/cache/`). Once a byte is in the cache, the project can iterate on parse/seed/curated logic indefinitely without re-hitting the network.

**Driver:** `scripts/fetch_<source>.py` (per resource). Idempotent — skips already-cached files. Writes a `_manifest.json` listing all discovered URLs/paths for reproducibility.

**Output:** raw artifacts in `scripts/cache/<source>/`:
- HTML pages: `<basename>.htm` / `.html` (one file per per-coin page, one file per overview page)
- PDFs: `<basename>.pdf` (e.g. Bruun auction catalogues)
- JSON from APIs: `<basename>.json` (e.g. IKMK Berlin object endpoints)
- For SPA / JS-rendered sources where Chrome MCP is required to render filtered views: `_walks/<filter>_pN.txt` raw page-text dumps preserve the SPA result for downstream parsing
- A `_manifest.json` listing every URL fetched + timestamp for re-run reproducibility

**Critical rule — preserve everything.** The cache stores «what the source actually said», not «what we think is in-scope». Year filters, denomination filters, ruler filters apply at LATER phases. Caching widely now means scope changes (e.g. extending mission anchor from 1559 to 1514) can re-filter without re-harvesting.

Detailed per-source playbook (URL patterns, tool fallback chains, known pitfalls per source): **`docs/HARVEST_GUIDE.md`**.

### Phase 2 — SYNTHESIS (parse + structure)

**Goal:** convert the raw cache into typed, structured records the project's tooling can query. **One file per resource entry, mirroring the cache layout** — every `<basename>.htm` gets a sibling `<basename>.json` sidecar. The output preserves ALL entries from the source — no year/mint/scope filters applied yet. Often the synthesis contains entries broader than the project's stated scope (e.g. post-1914 DK coins in Hede parsed JSON), on purpose.

**Driver:** `scripts/parse_<source>.py` (per resource). Reads `scripts/cache/<source>/*.htm` → emits `scripts/cache/<source>/<basename>.json` + aggregate `_parsed_index.json` mapping `<basename>` → canonical entry metadata.

**Output:**
- Per-entry typed sidecars in `scripts/cache/<source>/<basename>.json`: ruler, mint, year, nominal, specs (Bruttovægt / Finhed / Finvægt), catalog refs (Hede, Schou, Sieg, KM, MB, Fr, …), per-specimen details, literature citations
- Aggregate index `_parsed_index.json` resolving cross-references (e.g. a Hede page covering «Hede 61/62AB/63/64» expands into 4 per-Hede-number index entries even though the source has only one .htm file)

**Example:** `scripts/parse_hede.py` parses 689 Hede HTML pages into 671 typed JSON sidecars + 927 `_parsed_index.json` entries (the index expands multi-Hede pages into per-number records). Coverage: 97% years, 100% ruler + catalog refs, 74% specs.

**Critical rule — synthesis is broader than project scope.** A synthesis output that contains 1500-2025 entries when project scope is 1514-1914 is correct, not bloated. Filters apply at Phase 3.

### Phase 3 — SEED (filter + reshape to Coin schema)

**Goal:** filter the typed synthesis to a particular location's project scope and reshape each accepted entry into the project's `Coin` schema (Pydantic models at `scripts/lib/schema.py`). This is where year-range cutoffs, mint-set filters, canonical-resolution dedup, and multi-nominal split rules apply. The output IS the canonical intermediate the build trusts; the build script just appends it to the location's coins[] without further filtering.

**Driver:** `scripts/maintenance/build_<source>_<location>_seed.py` (per source × location). Reads `scripts/cache/<source>/*.json` → writes `data/seed/<source>/<location>.yml` (or `<location>_<scope>.yml` for scope-narrowed sub-windows).

**Output:** `data/seed/<source>/<location>.yml` — one YAML file per (source, location) tuple. Format:

```yaml
status: seed
source: <human-readable source name>
generated_at: <ISO-8601 timestamp>
scope_year_from: <YYYY>      # project filter applied here
scope_year_to: <YYYY>
scope_note: §<TODO-id> — <one-line description of the scope decisions>
coins:
  - id: <loc>-<src>-<canonical-cache-key>
    fuss: seed_unsorted         # phase-3 placeholder, awaits phase 4
    phase: <source>             # rendered as «Bulk-Seed · <Source>» sub-section
    ... # full Coin-schema record
```

The `fuss: seed_unsorted` + `phase: <source>` combination is the **phase-3 marker**. The build's `_merge_seeds_into_raw` automatically appends every `data/seed/*/<location>.yml` to the matching location's coins[] before schema validation, with the seed-unsorted Fuß rendering as a separate clearly-marked sub-section («Bulk-Seed · Hede 1971», «Bulk-Seed · Bruun», …) per Müntzfuß category on the rendered page.

**Filename convention:**
- `<location>.yml` — full project scope (e.g. `data/seed/hede/denmark.yml` covers Hede 1541-1914 mission window)
- `<location>_<scope>.yml` — narrower sub-window or per-task scope (e.g. `data/seed/bruun/denmark_pre_1541.yml` covers only 1514-1541 §AZ-anchor window)

**Critical rule — every seed entry MUST trace to a cache file.** The Phase-2 cache is the authoritative source. If a seed YAML has a coin with no corresponding `scripts/cache/<src>/<basename>.json` provenance, it's a §0 «no invention» violation. The cache-backing audit in any session can verify 100% provenance — see PHASE_AUDIT below.

**Example filters** (from `scripts/maintenance/build_hede_denmark_seed.py`):
- **Mint**: Danish royal mints only (København / Frederiksborg / Helsingør / Kbh+Altona). Glückstadt / Altona / Flensborg / Haderslev belong to a separate `schleswig_holstein.yml` seed
- **Canonical resolution**: cross-reference sub-Hedes (f3h68's mention of Hede 61/62AB/63) emit ONLY from the canonical owner (f3h62); footnote pages (c4h111note) emit nothing on top of c4h111
- **Year scope**: `--year-to <YEAR>` cap (default 1914, mission upper bound per CLAUDE.md); stored in seed file's `scope_year_to: <YEAR>` so future readers don't need to re-run

### Phase 4 — CURATED (promote into a Müntzfuß + merge with existing)

**Goal:** move researched seed entries OUT of the `fuss: seed_unsorted` bucket INTO the correct Müntzfuß with proper Phase periodisation, assign curated narrative (`hintergrund` / `description` / `closing` prose), validate cross-references, and resolve duplicates against existing curated entries.

**Driver:** typically a manual edit + commit on `data/locations/<loc>.yml`, OR a batch-promotion script (e.g. `scripts/oneoff/<promotion_task>.py`) for cluster moves. The action is the same either way:

1. Cut (or copy) the YAML block from `data/seed/<src>/<loc>.yml`
2. Paste into `data/locations/<loc>.yml` under the chosen `coins:` of the target `phases.<fuss>` entry
3. Replace `fuss: seed_unsorted` + `phase: <source>` with the real `fuss: <muentzfuss_id>` + `phase: <I|II|A|B|…>`
4. Cross-check the source page linked in `sources[].url`; flip `*_verified: true` field-by-field per CLAUDE.md §5 (mint_verified, fineness_verified, weight_rough_verified, etc.)
5. Merge with existing curated entries per CLAUDE.md §9a (multi-specimen merge — preserve all per-specimen weights/grades/citations in list form) and §9.4 (duplicate detection by catalog index — same KM# / Hede# / Sieg# is a dup; different index = different type)
6. Re-run `python scripts/build.py --validate-only` to catch chronology / cross-ref drift

**Critical rule — Phase 4 enriches, never invents.** All curated YAML edits must trace either:
- to the seed entry's provenance chain (cache → synthesis → seed), OR
- to a fresh web-research citation added to `data/locations/<loc>-references.yml` with inline `<sup>[N]</sup>` in the prose (per CLAUDE.md §5)

Direct typing of coin specs into `data/locations/*.yml` without one of those two provenance trails is forbidden. Audit: `scripts/audit_prose.py` + `scripts/audit_health.py` flag entries lacking source attribution.

### Rendering separation

Seed coins land in the location's `seed_unsorted` fuss bucket but a **separate phase per source** keeps them visually distinct in the rendered HTML: ucoin seeds → `phase: A`, Hede seeds → `phase: hede`. The location's `phases.seed_unsorted` list defines one Phase entry per source with its own title (`Bulk-Seed · ucoin` / `Bulk-Seed · Hede 1971 (danskmoent.dk)`) so each pile renders in its own sub-section without intermixing rows.

The landing page hides any location with at least one `fuss: seed_unsorted` coin (per «Layer C — Categorized» rules above). The card re-appears automatically once the last seed-bucket coin is promoted into a real Müntzfuß.

### PHASE_AUDIT — verifying cache-backing for any seed

Before declaring a seed file «done», every coin entry MUST have a discoverable Phase-2 cache provenance. Audit recipe (Python, runs in seconds against the submodule):

```python
import re, json
from pathlib import Path

# Example for hede/denmark.yml
ids = re.findall(r'^  - id:\s*(dk-hede-\S+)', Path("data/seed/hede/denmark.yml").read_text(), flags=re.M)
idx = json.loads(Path("scripts/cache/hede/_parsed_index.json").read_text())
orphans = []
for cid in ids:
    bn = cid.removeprefix("dk-hede-")
    parent = re.sub(r'[a-z]$', '', bn)   # strip sub-letter suffix (f2h8a → f2h8)
    if bn in idx or parent in idx: continue
    if (Path("scripts/cache/hede") / f"{bn}.htm").exists(): continue
    orphans.append(cid)
print(f"{len(ids) - len(orphans)} / {len(ids)} cache-backed")
```

A non-zero `orphans` count = a coin in seed without cache provenance = §0 violation. Verified on 2026-05-16: all 853 entries across `denmark`/{hede,bruun,galster,numismaster,numista} seeds = 100% cache-backed. False-positives come from regex edge cases (PDF-extracted line-break-hyphenated tokens, sub-letter splits, subdir-prefixed filenames) and are NOT actual gaps.

### Promotion path (Phase 3 → Phase 4) detailed

Seeds are append-only intake; promotions move coins **out** of the seed bucket into proper periodisation. The seed file shrinks as entries get classified, but never grows by hand-editing — only by re-running the Phase-3 generator.

Per CLAUDE.md §9 — when promoting, apply these placement rules:
- **Correct Fuß** by actual Münzfuß (not where it «seems to fit»)
- **Correct chronological Phase** within that Fuß (year_first determines phase)
- **Correct kind** (kurant / scheide / tarif / gedenk)
- Run §8a Müntzfuß-disambiguation pipeline when sources don't directly attest the placement
- §9a multi-specimen merge when promoting a coin that already has a curated entry

### Per-source documentation

Each source's pipeline specifics live in `docs/HARVEST_GUIDE.md` §«Per-source playbook». Additional per-source docs:
- Hede 1971 (danskmoent.dk): `data/seed/hede/README.md` (filtering decisions + coverage stats + promotion-path checklist)
- Bruun (Stack's Bowers Part I-IV): `data/seed/bruun/README.md` (per-territory promotion log)
- NumisMaster (Librios): `docs/HARVEST_GUIDE.md` §«NumisMaster» (canonical 6-step Chrome MCP workflow + JS recipes; Phase 1b 2026-05-16 inventory state)
- ucoin (legacy bulk imports): `docs/IKMK_HARVEST.md` + `scripts/audit_ucoin_categories.py` docstring
- Galster (danskmoent.dk): `docs/HARVEST_GUIDE.md` §«danskmoent.dk Galster page series»

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

## Harvest cache (submodule)

`scripts/cache/` is a **git submodule** pointing at a separate **private** repo (`munzfuss/munzfuss-harvest`). The submodule carries the regenerable artefacts of network fetches and PDF parses (Hede HTML+JSON, IKMK JSON, Numista JSON, Bruun parsed lots, ucoin URL index). The main repo stays slim; the build pipeline doesn't read this cache — only fetchers / parsers / audits / maintenance scripts do.

### First clone on a new machine

```bash
git clone --recursive https://github.com/munzfuss/munzfuss.github.io.git
```

Already cloned without `--recursive`? Initialise the submodule after the fact:

```bash
git submodule update --init
```

The submodule URL is HTTPS to a private repo, so the first clone will prompt for GitHub credentials (or use SSH if you've set up SSH agent).

### Build doesn't need the submodule

`python scripts/build.py` (validation, render, full build) does NOT read `scripts/cache/`. The build pipeline works on a clone WITHOUT the submodule initialised — `scripts/cache/` is just an empty directory. The CI deploy workflow (`.github/workflows/deploy.yml`) uses `actions/checkout@v4` with the default `submodules: false`, so Pages deploys are unaffected by the harvest split.

Only these workflows need the submodule:

- Re-parsing Hede (`scripts/parse_hede.py`)
- Re-fetching from any source (`scripts/fetch_*.py`)
- Running audits (`scripts/audit_*.py`)
- Most `scripts/maintenance/*` lifecycle scripts

### Committing harvest changes — see PB-10

When a session changes cache contents (typical trigger: `parse_hede.py --force` after a parser fix updates 100+ Hede JSON files), follow the two-step submodule-first-then-pointer-bump dance documented in **`docs/PLAYBOOKS.md` PB-10 «Committing harvest cache changes»**.

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
