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

### Manual-override preservation (mandatory across ALL phases)

> **Rule.** Manual overrides of individual fields on existing entries are PERMITTED at every phase. When a curator edits a value in a generated file (e.g. corrects a `fineness`, fixes a `year_first`, switches an `issuing_entity`), **the generator MUST preserve that edit across subsequent regenerations**. The script never blindly overwrites curated data.

This invariant applies to ALL phase-transition scripts:
- **Phase 2 → 3 seed builders** (`scripts/maintenance/build_<src>_<loc>_seed.py`)
- **Phase 4 batch promotion scripts** (`scripts/oneoff/*.py` that touch `data/locations/*.yml`)
- **Audit / cleanup scripts** that modify YAML in place (e.g. `scripts/maintenance/thin_intra_subvariant_specimens.py`, `scripts/maintenance/split_multisource_weight_entries.py`)

The reason: curation is expensive (multi-session research, source-verification rounds, peer-reviewed prose). A naive rewrite that obliterates curated values forces re-doing weeks of work — exactly the failure mode this rule guards against.

**Reference implementation: `scripts/maintenance/build_hede_denmark_seed.py`** (4-mechanism merge). Any new seed builder must implement at minimum the first three:

1. **`CURATED_FIELDS`** — field-allowlist whose EXISTING value is ALWAYS preserved when present. Reference set: `{fuss, phase, fraction, issuing_entity, kind, note, mint_verified, verified}`. These encode human classification decisions the parser cannot reconstruct (which Münzfuß, which Phase, which kind=kurant/scheide/tarif/gedenk, etc.). Default placeholder values (`fuss: seed_unsorted` / `phase: <source>`) flow through normally; non-default values are sticky.

2. **`DEEP_MERGE_FIELDS`** — dict-valued fields where existing keys survive AND fresh keys are added. Reference set: `{catalog}`. Lets curation add Bruun / KM / Dav cross-refs on top of parser-derived Hede / Schou / Sieg defaults, without losing either side.

3. **`_VERIFIABLE_FIELDS`** — verified-wins-over-unverified rule per CLAUDE.md §4. Pairs measurement fields with their `*_verified` flags: `{fineness: fineness_verified, weight_rough_g: weight_rough_verified, diameter_mm: diameter_mm_verified, mint: mint_verified}`. When merging, an EXISTING source-attested value (`*_verified: true`) beats a FRESH `(?)`-marked (unverified, parser-inferred) value. The unverified reading must NOT overwrite a curated, source-cited one — guards against parser regressions clobbering hard-won citations.

4. **`_curation_holds: [<field-name>, ...]`** — per-entry escape hatch, optional. Private meta-field on a coin entry listing additional field names whose existing value should be preserved across regen even though they're not in `CURATED_FIELDS`. Use for one-off cases where curation customised a field outside the standard allowlist (e.g. cleaned up a `nominal`, switched to a multi-source `weight_rough_g[]` list shape). Stripped from rendered output; survives across regen because the merge writes it back.

**Orphan handling:** ids present in the existing seed but absent from fresh regen are KEPT verbatim and flagged as «orphan curated» in the run summary. The generator NEVER auto-deletes a curated entry — parser instability could otherwise silently drop shipped data. The curator decides manually whether each orphan stays or goes.

**Wholesale-write builders (existing technical debt):**
- ✓ `build_hede_denmark_seed.py` — full 4-mechanism merge (reference implementation)
- ✗ `build_bruun_denmark_seed.py` — wholesale write (acceptable today: no curation has occurred yet; all entries still `fuss: seed_unsorted`)
- ✗ `build_galster_denmark_seed.py` — same
- ✗ `build_numismaster_pre1541_seed.py` — same
- ✗ `build_numista_pre1541_seed.py` — same

**Upgrade trigger:** any of the 4 wholesale-write seeds must be promoted to merge-aware BEFORE the curator starts assigning fuss/phase to entries in it. Failure to upgrade in time = loss of curation on the next regen. The reference implementation in `build_hede_denmark_seed.py` is ~150 lines (the `_merge_one` + `_merge_seed` functions + the four constants); porting to a sibling builder is mostly mechanical.

**For Phase-4 batch promotion scripts** (`scripts/oneoff/*.py`): when modifying existing entries in `data/locations/<loc>.yml`, use ruamel.yaml's round-trip mode (`YAML(typ='rt')`) to preserve comments + key order + ONLY touch the fields the script's intent dictates. Never serialise-and-rewrite the whole entry — that pattern is what destroys manual customisations.

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

## V2 entity-keyed pipeline (in-flight refactor)

> **Canonical decisions journal: [`V2_DECISIONS.md`](V2_DECISIONS.md).** Every architectural decision (32 + 4 deferred) listed with rationale + code locations. Read that file first to understand WHY the pipeline is shaped this way; the section below describes WHAT it is.
>
> **Canonical statement of the V2 data pipeline.** 4 fully-automated
> phases produce `data/v2/final/<entity>.yml` from harvested raw data.
> Display pages declare `consumes_entities: [...]` and the build
> assembly produces per-location output at render time. Detailed plan
> + decisions: `docs/V2_PIPELINE.md`.

### Pipeline at a glance

```
Phase 1 HARVEST                fetch_<src>.py        → scripts/cache/<src>/*.{htm,pdf,json}
       ↓
Phase 2 SYNTHESIS              parse_<src>.py        → scripts/cache/<src>/*.json
       ↓
Phase 3.1 per-source SEED      seed_v2_regroup.py    → data/v2/seed/<src>/<entity>.yml
       ↓
Phase 3.2 cross-source MERGE   merge_seeds_cross_    → data/v2/seed_unified/<entity>.yml
                               source.py               + data/v2/match_uncertainty/  (gitignored)
       ↓
Phase 4 absorb into FINAL      absorb_seeds_into_    → data/v2/final/<entity>.yml
                               final_v2.py             + data/v2/classification_decisions/
       ↓
Phase 4b BIDIRECTIONAL LINK    relink_promoted_v2.py → data/v2/seed/<src>/<entity>.yml
                                                       (promoted_to set per seed entry)
       ↓
Render                         build.py              → site/v2/<loc>/<lang>/index.html
```

Bootstrap (one-shot, 2026-05-18, V1 frozen post-bootstrap):

```
data/locations/<loc>.yml  ──[bootstrap_v2_final_from_v1.py]──▶  data/v2/final/<entity>.yml
data/locations/<loc>.yml  ──[init_v2_locations.py]──────────▶  data/v2/locations/<loc>.yml
                                                                 (display-meta + consumes_entities)
```

Every script is idempotent + merge-aware per D25; every transition preserves data per D17 «Data-accumulation principle». Audit (`scripts/audit_v2.py`) hard-blocks pre-commit on V2 path touches per D26.
>
> **V1 is reframed as a verification anchor**, not a bootstrap input.
> V1 curated (`data/locations/`) is frozen after the 2026-05-18 bootstrap.
> V2 reprocesses ALL data — existing + newly-harvested — through the
> 4-phase pipeline. The first full-cycle run is expected to map ~1:1
> onto V1 curated (it's the same source data, just through a new path);
> any divergence is signal for either a V1 bug, a V2 rule gap, or a
> legitimate ambiguity needing a recorded decision. Promotion gate
> (Phase 9) requires the V1↔V2 diff to be zero or fully explained.
>
> **Curator never edits coin fields by hand.** Curator input is
> restricted to: (a) which political entities the project supports,
> (b) Phase 3 merge confirmations for cases the cross-source-merge
> script can't auto-decide, (c) Phase 4 classification confirmations
> for cases the auto-classifier can't determine. In every case the
> preferred path is updating script rules so the case becomes
> auto-handled; explicit decision files are the escape hatch.

### V2 pipeline shape — strict one-way, script-driven, idempotent

```
  Phase 1                  Phase 2                  Phase 3                  Phase 4                  Render
  HARVEST                  SYNTHESIS                SEED + cross-source       FINAL (fuss-distrib.)    per-location assembly
  ══════════               ══════════════           ══════════════════        ══════════════════       ══════════════════
  raw fetch            ──▶ typed parse          ──▶ per-resource seeds    ──▶ §8a auto-classify    ──▶ build assembly
  per resource             per resource             + cross-source merge       + decision files         from N entity files
                                                    → unified per entity

  Output:                  Output:                  Output:                   Output:                  Output:
  scripts/cache/           scripts/cache/           data/v2/seed/             data/v2/final/           site/v2/<loc>/<lang>/
   <src>/<basename>.htm     <src>/<basename>.json    <src>/<entity>.yml         <entity>.yml             index.html
   <src>/<basename>.pdf     <src>/_parsed_index     data/v2/seed_unified/    (curator-readable,        + data/v2/locations/
                                                    <entity>.yml             never hand-edited)        <loc>.yml display-meta

  Driver:                  Driver:                  Drivers:                  Driver:                  Driver:
  fetch_<src>.py           parse_<src>.py           build_<src>_seed_v2.py    classify_to_fuss_v2.py   scripts/build.py
                                                    + merge_seeds_cross_      (consumes Phase 3        (consumes_entities
                                                     source.py                 + classification_         assembly + §3.10
                                                    (curator input via         decisions/<entity>.yml    inverse-index)
                                                     merge_decisions/         escape-hatch file)
                                                     <entity>.yml)
```

Where the curator can intervene (decision files, NEVER field-edits):

| Phase | Decision-file path | What it carries |
|---|---|---|
| 3 (cross-source merge) | `data/v2/merge_decisions/<entity>.yml` | Explicit `merge: [seed_id_a, seed_id_b]` + `no_merge: [...]` pairs for low-confidence cases the script can't auto-decide |
| 4 (fuss classification) | `data/v2/classification_decisions/<entity>.yml` | Explicit `assign: {coin_id: {fuss: X, phase: Y}}` for ambiguous coins; preferred path is generalising the rule |
| 5 (display assembly) | `data/v2/locations/<loc>.yml` `consumes_entities: [...]` | Which entities feed each rendered page (init_v2_locations preserves manual overrides) |

### Idempotency invariant

**Every V2 phase-transition script is idempotent + merge-aware.** Running any of them twice in a row produces zero file changes (verified by `git diff data/v2/`).

Shared mechanism: `lib/seed_merge.merge_seed()` (see §«Manual-override preservation» above). For every fresh-derived coin entry, the merger:

1. Looks up the coin's id in the existing on-disk yaml
2. If found: applies the 4-mechanism merge (CURATED_FIELDS, DEEP_MERGE_FIELDS, _VERIFIABLE_FIELDS, `_curation_holds`)
3. If new: adds fresh
4. Orphan curated entries (in existing but no longer in fresh) are kept verbatim — no silent data loss

`composed_of` + `promoted_to` are members of CURATED_FIELDS so the bidirectional link survives every regen.

### Phase 3 — SEED + cross-source merge

**3a. Per-resource seed building.** Each (source, entity) pair gets a builder writing `data/v2/seed/<source>/<entity>.yml`. The builder:

- Filters by **project scope** (year range, drops patterns / off-strikes per CLAUDE.md §9)
- Classifies by **political entity** via `scripts/lib/v2_entity_classify.py` (mint → entity table)
- Filters by **active entity set** (`data/i18n/issuing_entities.yml`)
- Applies field sanitisation + type coercion (drops non-schema fields with diagnostic; `bruun_part: 3 → 'III'`; null-nominal → '(?)' placeholder; etc.)
- Writes all entries with `fuss: seed_unsorted` — Phase 4 assigns fuss

**Transitional state (pre-Phase-9):** `scripts/maintenance/seed_v2_regroup.py` is the current driver — a **post-processor** over V1's location-keyed seed yamls. Post-Phase 9, each V1 builder gains a `--v2` flag (or sibling `build_<src>_seed_v2.py`) so V2 derives directly from parser cache.

**3b. Cross-source merge to unified seed.** `scripts/maintenance/merge_seeds_cross_source.py` (to-be-built) reads all `data/v2/seed/<source>/<entity>.yml` files for one entity and produces `data/v2/seed_unified/<entity>.yml` — one entry per physical coin, enriched from every source that catalogued it:

- **Confident auto-merge**: same `catalog.km` + same `catalog.hede` + same `ruler` + overlapping `year_first` → collapse to one entry. Multi-source `weight_rough_g[]` / `fineness[]` / `diameter_mm[]` lists preserve every reading per CLAUDE.md §9a multi-specimen rule. `sources[]` is the union.
- **Low-confidence pair**: surfaces for curator decision via `data/v2/merge_decisions/<entity>.yml`. Curator writes `merge: [seed_a, seed_b]` (confirm) or `no_merge: [seed_a, seed_b]` (explicit reject so the script doesn't keep asking). Or updates auto-merge rules to generalise the case.
- Records `composed_of: [seed_ids]` on every unified entry — full provenance.

### Phase 4 — Classification to Müntzfuß (final)

`scripts/maintenance/classify_to_fuss_v2.py` (to-be-built) reads `data/v2/seed_unified/<entity>.yml` and produces `data/v2/final/<entity>.yml` with each coin assigned to its Müntzfuß + phase:

- **Confident auto-classify**: applies CLAUDE.md §8a Müntzfuß-disambiguation pipeline (metal mismatch → mint-name mismatch → Δ-from-Soll → Bruttogewicht pattern → fineness hint). Where a unique candidate emerges, assigns automatically.
- **Low-confidence**: surfaces for curator decision via `data/v2/classification_decisions/<entity>.yml`. Curator writes `assign: {coin_id: {fuss, phase, fraction, kind, ...}}` — or updates the auto-classify rules to cover the pattern.
- §6 (kind kurant/scheide/tarif/gedenk) is also auto-determined here from nominal + fineness + fuss-Soll comparison.

`data/v2/final/<entity>.yml` is the final per-entity dataset that the build consumes. It is **never hand-edited** — all of its content is derived from upstream phases + decision files.

### Render — assembly per display location

`scripts/build.py` reads `data/v2/locations/<loc>.yml` (display-meta + `consumes_entities: [...]`) and assembles in-memory `raw['coins']` from `data/v2/final/<entity>.yml` files. Two-pass walk per V2_PIPELINE.md §3.10:

- **Pass 1**: direct entity-membership (coins that live in a consumed entity file)
- **Pass 2**: inverse-index for multi-entity coins (whose list-form `issuing_entity` intersects with `consumes_entities` even when the home file isn't directly consumed)
- Per-coin pre-filter drops coins whose `fuss` / `phase` / `year_first` doesn't fit this page's phase definitions

Output: `site/v2/<location>/<lang>/index.html`. Same Jinja template as V1.

### V1 as verification anchor

V1 (`data/locations/<loc>.yml`, `data/seed/<source>/<location>.yml`) is **frozen** after the 2026-05-18 bootstrap. It evolves only when new harvest yields new typed data automatically flowing through Phase 2 → 3 → 4. V2's job is to **reproduce V1's classifications** via the automated pipeline using the same source data.

**First full-cycle run.** When Phases 3.2 (cross-source merger) + 4 (auto-classifier) are fully implemented, the pipeline reprocesses ALL existing data. Expected result: ~1:1 mapping onto V1 curated. Differences = either V2 finds something V1 missed (legit new from pre-1541 sources etc.), V1 was wrong, V2's rules are wrong, or legitimate ambiguity needing a decision-file entry.

A diff script (`scripts/maintenance/diff_v1_v2_final.py`, to-be-built) compares V1 curated against V2 final and lists every divergence for review. **Promotion gate (Phase 9): «diff is zero or fully explained».**

### Script inventory + when to re-run each

After **new harvest data** (`scripts/cache/<src>/` updated):
1. `scripts/parse_<src>.py` — re-typify the new cache entries (V1 + V2 share parser cache)
2. `scripts/maintenance/build_<src>_<loc>_seed.py` (V1 builder) + V2 equivalent — refresh per-resource seeds; merge-aware
3. `scripts/maintenance/merge_seeds_cross_source.py --apply` (Phase 3.2) — re-merges cross-source per entity
4. `scripts/maintenance/classify_to_fuss_v2.py --apply` (Phase 4) — re-classifies seed_unified → final
5. `scripts/maintenance/relink_promoted_v2.py --apply` — bidirectional link audit
6. `python scripts/build.py` — renders both V1 + V2

After **curator decision file edits** (`data/v2/merge_decisions/` or `classification_decisions/`):
1. Re-run from the corresponding phase script
2. `python scripts/build.py`

After **V1 phase definition / `phases:` block changes** (rare):
1. `scripts/maintenance/init_v2_locations.py --apply` — re-derives V2 display-meta; preserves manual `consumes_entities` overrides
2. `python scripts/build.py`

### Merge audit trail — bidirectional link

> **Every Phase 3 cross-source merge IS recorded in the data, not just in commit messages.**

The `composed_of` ↔ `promoted_to` link encodes every merge that has happened:

- **Final / seed_unified side**: every entry has `composed_of: [per_resource_seed_id, …]` listing the per-source seed entries the merger absorbed.
- **Per-resource seed side**: `promoted_to: <unified_or_final_id>` points back. Build assembly drops seeds with `promoted_to != None` from rendering (otherwise they'd render duplicate alongside the canonical host).
- **Derivation**: `scripts/maintenance/relink_promoted_v2.py` walks all composed_of lists and sets the back-pointers. Idempotent. Catches stale links automatically.

**Data-loss invariant** — when a unified or final entry claims to absorb a seed, the host entry must carry the seed's data. `relink_promoted_v2.py --audit` flags every potential loss:

- Weight readings present in seed but not in host `weight_rough_g[]`
- Fineness values present in seed but not in host
- Source URLs present in seed but not in host `sources[]`

Phase 3.2 / Phase 4 scripts MUST produce hosts that pass this audit (no silent data loss). When a host fails the audit, either the script has a bug or the curator's merge decision was overly aggressive — either way the audit surfaces the regression on the next CI / pre-commit run.

### Transitional state (pre-Phase 9)

Currently `data/v2/curated/` holds the bootstrap-migrated output (1317 V1 curated coins folded into entity-keyed files via `bootstrap_v2_final_from_v1.py` on 2026-05-18). Once Phase 3.2 + Phase 4 land + the first full-cycle reprocess passes the V1↔V2 diff, this directory renames to `data/v2/final/` and the bootstrap migrate script retires.

Until then, `data/v2/curated/` serves as «Phase 4 equivalent» for V1-migrated coins, alongside `data/v2/seed/` which serves as «Phase 3.1 output» via the post-processor. The pipeline mechanics (merge, idempotency, link audit) are already in place; what remains is the explicit Phase 3.2 + Phase 4 scripts that derive `seed_unified/` and `final/` from upstream phases automatically.

Post-Phase 9 (promotion):
- Each V1 builder gains a `--v2` flag (or sibling V2 builder) so Phase 3.1 derives directly from parser cache without going through V1 seed yamls
- `bootstrap_v2_final_from_v1.py` retires (V1 archives off to `data/_archive_v1_*/`)
- `data/v2/*` → `data/*` (V2 becomes the primary)
- `seed_v2_regroup.py` retires (replaced by native V2 builders)

### Reference docs

- `docs/V2_PIPELINE.md` — full plan with phase-by-phase execution, resolved decisions, promotion-gate criteria
- `scripts/lib/seed_merge.py` — 4-mechanism merge module (CURATED_FIELDS / DEEP_MERGE_FIELDS / _VERIFIABLE_FIELDS / _curation_holds); `composed_of` + `promoted_to` are in CURATED_FIELDS so the bidirectional link survives every regen
- `scripts/lib/v2_resolver.py` — per-location dict-form resolvers (`phase`, `catalog.km`) + V2 migration breadcrumb strip-set
- `scripts/lib/v2_entity_classify.py` — mint → entity classification table
- `scripts/maintenance/relink_promoted_v2.py` — bidirectional link materialiser + data-loss audit
- `data/v2/README.md` — directory layout + key conventions recap

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
