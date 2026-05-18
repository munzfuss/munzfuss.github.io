# V2 entity-keyed pipeline — data root

V2 reprocesses ALL coin data through a 4-phase fully-automated pipeline
keyed by **political entity**. Display pages declare
`consumes_entities: [...]` and the build assembles per-location at
render time.

Full design + decisions → `docs/V2_PIPELINE.md`.
Full architecture → `docs/ARCHITECTURE.md` §«V2 entity-keyed pipeline».
**Canonical decisions journal** → `docs/V2_DECISIONS.md` (28 architectural decisions D1-D28 + 4 deferred DF1-DF4, each with rationale + code locations).

## Layout

```
data/v2/
├── seed/<source>/<entity>.yml         # Phase 3.1 — per-resource seed, entity-keyed
├── seed_unified/<entity>.yml          # Phase 3.2 — cross-source merged per entity (TO-BE-BUILT)
├── final/<entity>.yml                 # Phase 4 — fuss-distributed final state (currently `curated/`)
├── merge_decisions/<entity>.yml       # curator's Phase 3 merge confirmations (TO-BE-BUILT)
├── classification_decisions/<entity>.yml  # curator's Phase 4 fuss/phase confirmations (TO-BE-BUILT)
└── locations/<location>.yml           # Phase 5 inputs (display-meta + consumes_entities)
```

**Current transitional state** (pre-Phase 9):
- `seed/<source>/<entity>.yml` ← populated by `seed_v2_regroup.py` (post-processor over V1 seeds). Post-Phase 9, replaced by native V2 builders consuming parser cache directly.
- `curated/<entity>.yml` ← bootstrap-migrated from V1 curated on 2026-05-18. Will be regenerated as `final/<entity>.yml` by Phase 4 auto-classifier once it lands.
- `seed_unified/`, `final/`, `merge_decisions/`, `classification_decisions/` directories not yet present — created when Phase 3.2 + Phase 4 scripts ship.

V1 (`data/locations/`, `data/seed/<src>/<loc>.yml`) is **frozen** post 2026-05-18 — it serves as a **verification anchor** that V2's reprocessing of the same source data must reproduce (~1:1) before promotion (Phase 9). It continues to render the live site at unchanged URLs until promotion.

## Key conventions (recap of docs/V2_PIPELINE.md)

- **Each canonical coin lives in EXACTLY ONE entity file** (home-file
  rule). For multi-entity coins (`issuing_entity` list-form), the home
  file is the alphabetically-first entity. Build assembly's
  inverse-index pass surfaces secondary-entity coins on consumer pages.
- **`coin.issuing_entity: str | list[str]`** — list form for joint-
  jurisdiction coins (e.g. Altona+Kopenhagen mint →
  `[danish_realm, royal_holstein]`).
- **`catalog.km: str | dict[str, str]`** — dict form for cross-volume
  KM coins (e.g. `{dk: '722', sh: '155'}`).
- **`coin.phase: str | dict[str, str]`** — dict form only when the
  same coin needs different periodisation on different display pages.
- **`coin.composed_of: [seed_id, ...]`** + seed-side
  **`promoted_to: <host_id>`** — bidirectional merge audit trail. Set
  automatically by scripts; never edited by hand.

## Curator role

Curator **never edits coin fields by hand**. Curator input lives in
three decision surfaces only:

1. `data/i18n/issuing_entities.yml` — which political entities the
   project supports
2. `data/v2/merge_decisions/<entity>.yml` — Phase 3 cross-source
   merge confirmations (`merge: [seed_a, seed_b]` / `no_merge: [...]`)
3. `data/v2/classification_decisions/<entity>.yml` — Phase 4 fuss/
   phase confirmations for ambiguous coins

In every case the preferred path is **updating the script rules** so
the case becomes auto-handled. The decision files are escape hatches
for cases not yet practical to generalise.

All other contents under `data/v2/` (seed/, seed_unified/, final/,
locations/) are **fully script-derived** — running the pipeline scripts
twice in a row produces zero file changes (idempotent + merge-aware
via `lib/seed_merge.py`).
