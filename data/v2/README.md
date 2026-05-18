# V2 entity-keyed pipeline — data root

V2 re-keys SEED (Phase 3) and CURATED (Phase 4) data from
`<location>.yml` to `<political_entity>.yml`. Display pages declare
`consumes_entities: [...]` and Phase 5 (MERGED) assembles per-page in
memory from N entity files.

Full design + execution plan → `docs/V2_PIPELINE.md`.

## Layout

```
data/v2/
├── seed/<source>/<entity>.yml      # Phase 3 SEED, entity-keyed
├── curated/<entity>.yml            # Phase 4 CURATED, entity-keyed
└── locations/<location>.yml        # Phase 5 inputs (display-meta + consumes_entities)
```

V1 (`data/locations/`, `data/seed/`) remains the source of truth and the
rendered live site (`site/<loc>/...`) until the user signals «фліпай V2»
(Phase 9 in the plan). Until then V2 lives in parallel and renders to
`site/v2/<loc>/...`.

## Key conventions (recap of V2_PIPELINE.md)

- Each curated coin lives in **exactly one** entity file (home-file rule,
  §3.10). For multi-entity coins, the home file is the alphabetically-first
  entity in the `issuing_entity` list.
- `coin.issuing_entity: str | list[str]` — list form for joint-jurisdiction
  coins (e.g. Altona+Kopenhagen → `[danish_realm, royal_holstein]`).
- `catalog.km: str | dict[str, str]` — dict form for cross-volume coins
  (e.g. `{dk: '722', sh: '155'}`).
- `coin.phase: str | dict[str, str]` — dict form only when the same coin
  has different periodisations on different display pages.
- `coin.composed_of: [seed_id, ...]` and seed-side `promoted_to: <curated_id>`
  carry the bidirectional seed↔curated link.
