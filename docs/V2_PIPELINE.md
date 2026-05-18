# V2 Pipeline — entity-keyed refactoring plan

> **Status (2026-05-18):** Architecture refined to 4-phase fully-automated
> pipeline; V1 reframed as **verification anchor** (not bootstrap input).
> Implementation in flight on branch `feat/v2-pipeline`. Phases 1, 2,
> partial 3, partial 4 + supporting infrastructure (schema, build
> pipeline, idempotent merge-aware regen, bidirectional link) landed.
> Outstanding: native Phase 3 cross-source merger, Phase 4 auto-classifier,
> first full-cycle reprocess + V1-vs-V2 diff verification.

## 1. Why

The V1 pipeline keys seed and curated files by display **location** —
`data/seed/<source>/<location>.yml`, `data/locations/<location>.yml`.
That assumption breaks for issues whose authority feeds multiple display
pages (Glückstadt-minted royal-Danish coins → both the Denmark page and
the Schleswig-Holstein page; Norway-under-Danish coins → the Denmark
page and a future Norway page).

V1 patches this with a cross-location coverage hack in `build.py` for
the Hede source only; every other source either gets manually duplicated
across location yamls or only appears on one page.

V2 fixes this at the architecture level — seed AND final coin files are
keyed by **political entity** (`issuing_entity`), and each display page
declares which entities it consumes. One canonical entry, N rendered
surfaces. The build assembly inverts at render time.

But the rename is only the surface change. The deeper rework is the
**fully automated, one-way, idempotent pipeline** with curator input
restricted to **decisions** (merge confirmations, classification
confirmations) — not data edits.

## 2. The 4-phase pipeline

```
  Phase 1                Phase 2                Phase 3                  Phase 4                  Render
  ═══════════════        ════════════════       ══════════════════        ══════════════════       ═════════════
  raw fetch              typed parse            seed per entity ×         final per entity         per-location
  per resource           per resource           resource + cross-         (fuss-distributed)       assembly
                                                source merge

  Output:                Output:                Output:                   Output:                  Output:
  scripts/cache/         scripts/cache/         data/v2/seed/             data/v2/final/           site/v2/<loc>/
   <src>/<basename>.htm   <src>/<basename>.json  <src>/<entity>.yml        <entity>.yml             <lang>/index.html
   <src>/<basename>.pdf   <src>/_parsed_index    + data/v2/seed_unified/  (was data/v2/
                                                 <entity>.yml              curated/ in transitional
                                                 (cross-source merged)     bootstrap state)

  Driver:                Driver:                Drivers:                  Driver:                  Driver:
  fetch_<src>.py         parse_<src>.py         build_<src>_seed_v2.py    classify_to_fuss_v2.py   build.py
                                                + merge_seeds_cross_      (script + curator        (consumes_entities
                                                 source.py                 decisions where           assembly)
                                                                           ambiguous)
```

**Each phase is fully script-driven. The curator never edits coin fields
by hand.** Curator input is restricted to two decision moments:

- **Phase 3 — merge confirmations**: «entry A and entry B describe the
  same physical coin» (declared so the script enriches both into one
  unified entry)
- **Phase 4 — classification confirmations**: «this coin belongs to
  Müntzfuß X, phase Y» (declared so the script assigns it; or update
  the auto-classify rules to cover the case)

Every phase output is **idempotent + merge-aware**: re-running on
unchanged input produces zero file changes; existing curator decisions
persist; orphan entries (in V2 but no longer in fresh input) stay
verbatim — no silent data loss.

## 3. Phase 1 — HARVEST

**Unchanged from V1.** `scripts/fetch_<source>.py` writes raw artifacts
to `scripts/cache/<source>/` (HTML, PDF, JSON from APIs). Idempotent
(skips already-cached files). Output preserves «what the source actually
said» without project-scope filtering.

Details: `docs/HARVEST_GUIDE.md`.

## 4. Phase 2 — SYNTHESIS (typed data)

**Unchanged from V1.** `scripts/parse_<source>.py` converts raw cache
into typed JSON sidecars (`scripts/cache/<source>/<basename>.json`)
plus aggregate `_parsed_index.json` cross-reference table. One file per
resource entry, mirroring the cache layout. Output preserves all entries
from the source — no year/mint/scope filters yet.

User control here: **which fields are typed** (driven by what's in the
parser code, refined as needed when new field shapes appear in the
cache).

## 5. Phase 3 — SEED + cross-source merge

**Two sub-steps**, both script-driven:

### 5.1 Per-resource seed building

For each (source, entity) pair, a builder reads the typed parsed cache
and writes `data/v2/seed/<source>/<entity>.yml`. The builder:

- Filters by **project scope** (years, denominations, drops patterns +
  off-strikes per CLAUDE.md §9)
- Classifies by **political entity** via mint → entity lookup
  (`scripts/lib/v2_entity_classify.py`; see §10.1)
- Filters by **active entity set** (which political entities the project
  is currently supporting — controlled by `data/i18n/issuing_entities.yml`)
- Applies type coercion + field sanitisation (drops non-schema fields
  with diagnostic, normalises shapes like `bruun_part: 3 → 'III'`)
- Writes entries as raw seed data, **all with `fuss: seed_unsorted`** —
  no Müntzfuß assigned yet (that's Phase 4's job)

Each builder is idempotent + merge-aware via `lib.seed_merge.merge_seed()`.

**Curator control here:**
- The active entity set (`data/i18n/issuing_entities.yml`)
- The mint → entity classifier rules (`scripts/lib/v2_entity_classify.py`)
- Project scope filters (years, denomination exclusions) — embedded in
  the builder
- All «curator decisions» are encoded as **rules in scripts**, never as
  hand-edits to seed yaml entries

### 5.2 Cross-source merge to unified seed

For each entity, a separate script `merge_seeds_cross_source.py` reads
all `data/v2/seed/<source>/<entity>.yml` files and produces
`data/v2/seed_unified/<entity>.yml` with **one entry per physical coin**,
enriched with data from every source that catalogued it.

Merge rules:
- **Confident auto-merge**: same `catalog.km` + same `catalog.hede` +
  same `ruler` + overlapping `year_first` → script collapses to one
  entry with multi-source `weight_rough_g[]` / `fineness[]` /
  `diameter_mm[]` lists and combined `sources[]`
- **Low-confidence pair**: e.g. same KM but different rulers, or
  KM-canonical match but inconsistent weights → script surfaces for
  **curator decision**:
  - Curator confirms «yes, same coin» → adds a merge declaration
  - Curator confirms «no, different coins» → adds a no-merge declaration
    so the script doesn't keep asking
  - Curator improves the auto-merge rules so the case fires automatically
- **Manual merge declarations** live in `data/v2/merge_decisions/<entity>.yml`
  — one file per entity listing explicit `merge: [seed_id_a, seed_id_b]`
  pairs and `no_merge: [seed_id_a, seed_id_b]` exclusions. The merger
  reads these on every run; curator updates this file ONLY.

**Phase 3 output guarantees:**
- Every coin in `data/v2/seed_unified/<entity>.yml` has at least one
  source-attested weight (or `weight_rough_g: null` flagged for review)
- `composed_of: [seed_ids]` records the per-source seeds that fed this
  unified entry — full audit trail
- `fuss: seed_unsorted` for every entry — Phase 4 hasn't run yet

## 6. Phase 4 — Classification to Müntzfuß (final)

For each unified seed entry from Phase 3, classify into a Müntzfuß +
phase via `scripts/maintenance/classify_to_fuss_v2.py`:

- **Confident auto-classify**: apply CLAUDE.md §8a Müntzfuß-disambiguation
  pipeline (metal-mismatch → mint-name-mismatch → Δ-from-Soll → Brutto-
  gewicht pattern → fineness hint). Where unique candidate emerges →
  assign automatically.
- **Low-confidence**: surface for curator decision, written into
  `data/v2/classification_decisions/<entity>.yml` (analogous to
  `merge_decisions/`). Curator records `assign: {coin_id: {fuss: X,
  phase: Y}}` for ambiguous coins; or updates the auto-classify rules.

Phase 4 output: `data/v2/final/<entity>.yml` — coins distributed across
their Müntzfüße + phases, ready for render.

**Curator decisions for Phase 4 live in script rules + decision files,
NEVER as hand-edits on individual coin yamls.**

## 7. Render — assembly per display location

`scripts/build.py` reads `data/v2/locations/<loc>.yml` (display-meta +
`consumes_entities: [...]`) and assembles in-memory `raw['coins']` from
`data/v2/final/<entity>.yml` files. Two-pass walk per V2_PIPELINE.md §10.4:

- **Pass 1**: direct entity-membership (coins that live in a consumed
  entity file)
- **Pass 2**: inverse-index for multi-entity coins (whose list-form
  `issuing_entity` intersects with `consumes_entities` even when the
  home file isn't directly consumed)

Per-coin pre-filter drops coins whose `fuss` / `phase` / `year_first`
doesn't fit this page's phase definitions. Output:
`site/v2/<location>/<lang>/index.html`. Same Jinja template as V1.

## 8. V1 as verification anchor

V1 (`data/locations/<loc>.yml`, `data/seed/<source>/<location>.yml`) is
**frozen** after the 2026-05-18 bootstrap. It evolves only via new
harvest → new typed data → automatic Phase 2 → Phase 3 → Phase 4. V2's
job is to **reproduce V1's classifications** through the automated
pipeline using the same source data.

**First full-cycle run.** When Phases 3 + 4 are fully implemented, the
pipeline reprocesses ALL existing data (not just newly-harvested
records). The result should map ~1:1 onto V1 curated:

- Same coins → same Müntzfuß + phase assignments
- Same multi-specimen merges → same composed_of structure
- Same mint → entity classifications

**Divergence is signal**:
- V2 finds something V1 missed (genuinely new from pre-1541 sources etc.)
- V2 classifies something differently → either V1 was wrong, V2's rules
  are wrong, or there's legitimate ambiguity needing a decision
- V2 misses something V1 had → script gap to fix

A diff script (`scripts/maintenance/diff_v1_v2_curated.py`, to-be-built)
compares V1 curated against V2 final and lists every divergence for
review. Phase 9 promotion gate: «diff is zero or fully explained».

## 9. Curator role

**Curator never edits fields on coin entries.** Three legitimate
decision surfaces:

1. **Active entity set** — `data/i18n/issuing_entities.yml`. Decides
   which political entities the project currently supports.
2. **Phase 3 merge decisions** — `data/v2/merge_decisions/<entity>.yml`.
   Explicit `merge` / `no_merge` declarations for cases the
   cross-source-merge script can't auto-decide.
3. **Phase 4 classification decisions** —
   `data/v2/classification_decisions/<entity>.yml`. Explicit
   `assign: {coin_id: {fuss, phase, ...}}` for cases the auto-classifier
   can't determine.

In every case, **the preferred path is to update the script's rules**
so the case becomes auto-handled. The decision files are the escape
hatch when generalising a rule isn't yet practical.

## 10. Cross-references

- **Schema**: `scripts/lib/schema.py` — `Coin.issuing_entity: str | list[str]`,
  `Coin.phase: str | dict[str, str]`, `CatalogRefs.km: str | dict[str, str]`
- **Entity classifier**: `scripts/lib/v2_entity_classify.py` — mint →
  entity table extended over §3.1
- **Merge mechanism**: `scripts/lib/seed_merge.py` — 4-mechanism merge
  (CURATED_FIELDS, DEEP_MERGE_FIELDS, _VERIFIABLE_FIELDS, _curation_holds)
- **Resolvers**: `scripts/lib/v2_resolver.py` — per-location dict-form
  resolvers for `phase` + `catalog.km`
- **Build assembly**: `scripts/build.py::_assemble_v2_location`
- **Bidirectional link**: `scripts/maintenance/relink_promoted_v2.py` —
  `composed_of` ↔ `promoted_to` materialiser + data-loss audit
- **Detailed architecture**: `docs/ARCHITECTURE.md` §«V2 entity-keyed pipeline»

## 11. Resolved decisions (no further input needed)

Locked in across previous planning rounds:

- **`issuing_entity` schema** = `str | list[str]` (joint-jurisdiction
  multi-mint coins use list form; alphabetical-first element is home file
  per home-file rule)
- **`gesamtstaat` migration** = mint-driven decision tree
  (Altona → royal_holstein, Kopenhagen → danish_realm, Kongsberg/
  Christiania → danish_norway; multi-mint → alphabetical list)
- **Home-file rule** for multi-entity coins — alphabetical-first list
  element; build assembly inverse-index pass for secondary entities
- **`catalog.km` schema** = `str | dict[str, str]` (dict form for
  cross-Krause-volume coins)
- **`coin.phase` schema** = `str | dict[str, str]` (scalar default;
  dict override for per-location phase differences on multi-consumer
  coins)
- **V2 templates** share `templates/location.html.j2` with V1 (fork
  only on demand)
- **Pre-1541 absorption** — V1's pre_1541 draft seeds (bruun / galster /
  numista) flow into V2 normally. V2 takes over their scope.
- **V1 freeze** — `data/locations/`, `data/seed/<src>/<loc>.yml` get
  no new edits. Only new harvest + parser output evolve. V2 is the
  forward-going surface; V1 is verification anchor.
- **Curator-edits-via-rules** — curator never edits coin fields by
  hand. Decisions go into rules (preferred) or explicit decision files
  (escape hatch).
- **Audit hard-block** from Phase 7 onwards — `audit_v2.py` blocks
  pre-commit (stricter than the originally-recommended advisory mode).

## 12. Implementation status

Landed:
- [x] Phase 1, Phase 2 — unchanged from V1, shared
- [x] Phase 3.1 (per-resource seed entity-keyed output) — via
  `scripts/maintenance/seed_v2_regroup.py` post-processor over V1 seeds.
  Native `--v2` builders post-Phase 9 will replace the post-processor.
- [x] Schema extensions: list-form `issuing_entity`, dict-form `phase`
  and `catalog.km`, `composed_of` + `promoted_to`
- [x] Build assembly: two-pass walk + per-coin phase pre-filter,
  CLI flags `--v1-only` / `--v2-only`
- [x] Idempotent merge-aware regen for migrate_curated_to_v2,
  seed_v2_regroup, init_v2_locations
- [x] Bidirectional `composed_of` ↔ `promoted_to` link
  (`relink_promoted_v2.py`) + data-loss audit
- [x] Mint → entity classifier
  (`scripts/lib/v2_entity_classify.py`)

Pending:
- [ ] Phase 3.2 — cross-source merge to `data/v2/seed_unified/<entity>.yml`
  (script + merge_decisions file format)
- [ ] Phase 4 — fuss classification to `data/v2/final/<entity>.yml`
  (script + classification_decisions file format; §8a integration)
- [ ] Directory rename `data/v2/curated/` → `data/v2/final/` (after
  Phase 4 lands; until then `curated/` holds the bootstrap-migrated
  state that serves as «Phase 4 equivalent» for V1-migrated coins)
- [ ] `audit_v2.py` — home-file rule, bidirectional link integrity,
  cross-entity duplicate detection. Hard-block from this point.
- [ ] `diff_v1_v2_curated.py` — V1 anchor vs V2 final comparator
- [ ] First full-cycle reprocess + V1-vs-V2 diff review

Deferred to Phase 9 (promotion):
- [ ] Native `--v2` flag on V1 builders (replaces seed_v2_regroup
  post-processor)
- [ ] Retirement of `migrate_curated_to_v2.py` (V1 archives off)
- [ ] Promotion `mv data/v2/* data/`, archive V1, update CI

## 13. Promotion-gate criteria (Phase 9)

V2 ready for promotion when:

1. V1 vs V2 final diff is **zero or fully explained** (every
   divergence has a recorded reason — V1 bug, V2 rule gap, legitimate
   ambiguity with curator-confirmed decision)
2. All curator decisions encoded in script rules OR explicit decision
   files (no orphan hand-edits)
3. `audit_v2.py` passes hard-block on every invariant
4. Visual review of `site/v2/<loc>/<lang>/` for every location matches
   or exceeds `site/<loc>/<lang>/`
5. Explicit user signal «фліпай V2»
