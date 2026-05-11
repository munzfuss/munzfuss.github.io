# scripts/maintenance/

Lifecycle-bound utilities. **Not part of the build.** Each script ran (or runs)
against a specific dataset / phase of the project; none are invoked
automatically. They live here — instead of being deleted — because the same
shape of work tends to recur (next bulk import, next translation drift sweep,
next ucoin re-link), and starting from a working ancestor beats starting from
a blank file.

## Decision rule

A script belongs in `scripts/maintenance/` when **either**:

1. It runs once on a specific dataset and the input is consumed/gone after
   the run (one-shot enrichment, classification pass, dedup pass).
2. It's idempotent and re-runnable, but lifecycle-bound to a phase that
   isn't part of the normal build flow (translation cleanup over hand-edited
   YAML, periodic catalog refresh).

Scripts that audit current state idempotently (the `audit_*.py` suite) and
scripts that fetch/enrich data for **new** locations (`fetch_numista_api.py`,
`enrich_from_numista.py`) stay in `scripts/` — they're part of the active
research workflow.

## Inventory (at time of organisation)

| script | purpose | when last needed |
|---|---|---|
| `classify_issuing_entity.py` | Bulk-assign `issuing_entity` to existing SH coins via heuristic ruler-name rules. | Once — after the field was added to the schema. |
| `dedupe_sources.py` | Merge duplicate `coin.sources[]` entries pointing to the same URL. | Once — cleanup after a bulk URL promotion. |
| `enrich_numista_id.py` | Extract Numista piece-id from each coin's source URL into `catalog.numista`. | Phase-1 of the Numista enrichment. |
| `enrich_numista_refs.py` | Merge per-piece catalog refs (KM#, Lange#, Hede#, Sieg#, …) from a cached Numista response into each coin's `catalog`. | Phase-2 of the Numista enrichment. |
| `quality_pass.py` | Regex-based cleanup of EN/UK auto-translation artefacts (German leak-words, broken decimals, …). | Re-run after each bulk translation drift. |
| `relink_ucoin.py` | Add provably-correct ucoin source URLs to existing coins — KM# + year overlap + denom-token agreement + weight/fineness within tolerance. | Phase-2 of the ucoin link-up. |
| `ucoin_fetch_composition.py` | Driver for ucoin composition / weight / diameter / edge / shape / alignment harvest via Chrome MCP. **Halted 2026-05-11**: ucoin's URL slug routing changed and our heuristic `_url_index.json` no longer resolves correctly (returns unrelated modern Euro coins for our DK/Lübeck/HH slugs). The 98 committed entries in `_composition.json` predate the breakage and are reliable; the canonical-tid validator inside `MEGA_FETCH_TEMPLATE` documents the regression. Resume when either ucoin restores slug routing or a new lookup strategy (sitemap / site-search / JSON API) is identified. |
| `ucoin_backfill_metal.py` | Apply harvested `_composition.json` to coin records: set `metal` (and `metal_verified`), set `fineness` (and `fineness_verified`) when missing, flag conflicts. | Re-run after each harvest expansion (currently sitting at 98 known-good entries). |

## Re-running

These scripts assume the **repo root** as cwd:

```bash
.venv/bin/python scripts/maintenance/quality_pass.py
```

If a script fails on first re-run after data has evolved, prefer **fixing the
script forward** over reverting the data — every run informs the next phase.
