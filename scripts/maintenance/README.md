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
| `harvest_coverage.py` | Read-only standing coverage report across ALL sources (HARVEST_ROUTINE §6.5): (A) entity × source classified-specimen matrix from `data/v2/seed/`, (B) per-source cached-vs-seeded footprint, (C) IKMK cache detail (un-seeded → uncovered by entity). `--json` for machine output. Run every harvest end-of-run + ad-hoc to answer «what locations / how many specimens do we hold, total». | Every routine run (§6.2 item 7); added 2026-05-30. |
| `classify_issuing_entity.py` | Bulk-assign `issuing_entity` to existing SH coins via heuristic ruler-name rules. | Once — after the field was added to the schema. |
| `dedupe_sources.py` | Merge duplicate `coin.sources[]` entries pointing to the same URL. | Once — cleanup after a bulk URL promotion. |
| `enrich_numista_id.py` | Extract Numista piece-id from each coin's source URL into `catalog.numista`. | Phase-1 of the Numista enrichment. |
| `enrich_numista_refs.py` | Merge per-piece catalog refs (KM#, Lange#, Hede#, Sieg#, …) from a cached Numista response into each coin's `catalog`. | Phase-2 of the Numista enrichment. |
| `quality_pass.py` | Regex-based cleanup of EN/UK auto-translation artefacts (German leak-words, broken decimals, …). | Re-run after each bulk translation drift. |
| `relink_ucoin.py` | Add provably-correct ucoin source URLs to existing coins — KM# + year overlap + denom-token agreement + weight/fineness within tolerance. | Phase-2 of the ucoin link-up. |
| `heal_hede_retracted_refs.py` | Remove seed catalogue values the danskmoent parser has RETRACTED, and write `data/v2/_retracted_refs.yml` so `verify_reflow.py` can tell the removal from real loss. Needed because `catalog` is deep-merged and list-capable: a parser fix that stops emitting a wrong value cannot remove it, only a heal can — and the heal makes a register shrink, which is exactly what the gate blocks. Removes ONLY a value that is in the seed, absent from the current parse, AND present in the previous parse (cache submodule git HEAD) — that third condition is what keeps it off curator additions and other sources' contributions. Run right after `parse_hede.py --force` + `build_hede_denmark_seed.py`, while the submodule still holds the pre-fix parse. | Once, 2026-08-07 (17 fields, off-strike asides). |
| `heal_hede_sibling_schou.py` | Strip Schou values a danskmoent seed borrowed from a SIBLING Hede on the same multi-Hede page. Needed because `catalog` is in the hede builder's `DEEP_MERGE_FIELDS` and `schou` is list-capable, so a re-seed UNIONS and can only add — the stale value survives every regeneration. Matters beyond display: `schou/<ruler>` is a matcher key, so a borrowed number is a FALSE §9.4 unifying edge. Removes ONLY a value that is both absent from the sub-Hede's own `by_hede` refs and present in a sibling's; anything else is printed for review, not guessed at. | Once, 2026-08-07 (12 seeds). A re-run still reports `c5h40` — that one is builder-side, do NOT loop on it; see the docstring. |
| `thin_intra_subvariant_specimens.py` | Apply per-(coin, sub-group) DROP lists encoded in the script body to trim `weight_rough_g` + matching `sources[]` to `min / middle-by-index / max` triples. Enforces CLAUDE.md §9a «Intra-sub-variant thinning» when one coin entry accumulates ≥5 specimens from a single resource (IKMK / Bruun / ucoin / Numista) within one sub-variant tag and fineness is uniform/absent. Idempotent — re-running after a clean pass is a no-op. **Per audit pass:** when `audit_health.py` flags new buckets, extend the `DROPS` dict and re-run. | Once after the 2026-05-09 IKMK sweep (km-46 / km-5 / km-9 SH); extend per audit. |
| `ucoin_fetch_composition.py` | Driver for ucoin composition / weight / diameter / edge / shape / alignment harvest via Chrome MCP. **Halted 2026-05-11**: ucoin's URL slug routing changed and our heuristic `_url_index.json` no longer resolves correctly (returns unrelated modern Euro coins for our DK/Lübeck/HH slugs). The 98 committed entries in `_composition.json` predate the breakage and are reliable; the canonical-tid validator inside `MEGA_FETCH_TEMPLATE` documents the regression. Resume when either ucoin restores slug routing or a new lookup strategy (sitemap / site-search / JSON API) is identified. |
| `ucoin_backfill_metal.py` | Apply harvested `_composition.json` to coin records: set `metal` (and `metal_verified`), set `fineness` (and `fineness_verified`) when missing, flag conflicts. | Re-run after each harvest expansion (currently sitting at 98 known-good entries). |
| `reroute_orphan_unified_into_foundation.py` | Re-route standalone `unified-X` final entries (bulk-promoted orphans, `fuss=seed_unsorted`) into matching foundations when post-promotion matcher improvements (D32 / D40 / catalog-tolerance) now return `confident` for a previously `no_match` pair. Year-span filter (TOLERANCE=2 yr) blocks over-aggregated unifieds. Companion to `absorb_seeds_into_final_v2.py` — run reroute first, then absorb to enrich. | Re-run whenever matcher rules evolve and new orphans become re-routable. First pass 2026-05-23 routed 115 orphans across 8 entities; ~1212 remain genuinely new pending classification. |
| `refresh_audit_cached_counts.py` | Recompute `cached_count` / `cached_tids` / `gap_tids` (ucoin) and `cached_count` / `gap_nids` (Numista) in the harvest audit manifests (`scripts/cache/{ucoin,numista}/_{BR,BO}*.json`) from the actual on-disk cache, so the routine's bucket picker stops re-offering already-cached buckets (anomaly `audit_manifest_scope_drift:field=cached_count`). Auto-detects ucoin-flat (BR-4/BR-3), Numista-flat (BO.7) + nested (BO.6) schemas; skips prose audits; preserves gap order + `oos_excluded_tids` + each file's format. Dry-run by default; `--write` persists; idempotent. **Wired into the harvest routine's §1 preflight** (`HARVEST_ROUTINE.md`). | Every cron-session preflight; manual `--write` anytime the audit counts drift. |
| `audit_hede_seed_loss.py` | **Hede parser→seed data-loss tracker.** Re-derives, per danskmoent.dk Hede cache page, why it is / isn't in `data/v2/seed/hede/*.yml`: `sub_letter_loss` (seeded but HTML sub-letters not captured), `field_swap` (parser put nominal in the mint slot → builder skips), `oos_post_1914` / `exonumia` (correctly absent), `in_scope_absent` (has nominal+mint but no single spec block / multi-coin / undated — needs per-case review). Run before any sub-variant-loss work — the hand-written loss breakdown in handoff goes stale as parser fixes ship. `--json` / `--category X`. | Whenever auditing Hede parser coverage; current state (2026-06-07): 515 OK, 3 sub-letter-loss, 12 field-swap, 93 in-scope-absent, 25 oos, 14 exonumia. |
| `audit_entity_misclassifications.py` | **Find + relocate entity-misclassified seeds.** Scans `data/v2/seed/<src>/<entity>.yml` for coins whose mint (via `mint_registry`) or an `entity_routing_rules.yml` rule maps to a DIFFERENT entity than their current file; `--apply` moves them (removes from wrong file, merges into the right one). **Two non-obvious invariants — get either wrong and you lose or resurrect data:** (1) The **current file (coins LEAVING) is written by a DIRECT canonical dump, never `merge_seed`** — `merge_seed` preserves entries the fresh list no longer produces as `orphan_curated` (lib/seed_merge.py §2), so feeding it the removal would re-append the very coins you are removing and they'd live in TWO entity files at once. Only the **expected file (coins ARRIVING) goes through `merge_seed`** (so curator edits on a coin already there survive). (2) Both writes MUST use the canonical ruamel serializer (`_canonical_seed_yaml` → width 200 / indent 2·4·2 / preserve_quotes) and read round-trip — PyYAML `safe_dump(width=120)` re-flows every long string, so moving 56 coins once produced a 570 000-line diff (real change ~1.5k). Pinned by `tests/test_relocate_serializer_canonical.py`. Cascade after `--apply`: `merge_seeds_cross_source.py --apply` then `absorb_seeds_into_final_v2.py --apply`. | Whenever routing rules change or a mint alias is added; serializer fixed 2026-09-13. |
| `catalog_graph.py` | **Catalog-conflict disambiguation visualizer.** Emits a self-contained interactive HTML graph (`output/catalog_graph.html`, gitignored) where vertices = catalog index values (KM/Hede/Sieg/Dav/Schou, namespaced per ruler) and edges = indices that co-occur on one source record (thickness = N sources, colour = source). Bold-black ✔ edges = curator identity verdicts (`CURATOR_LINKS`); `CURATOR_DISTINCT` pairs draw none. Hand-curated state lives in the script body: `COMPONENTS` (the nominal+ruler tangles to resolve), `CURATOR_LINKS` / `CURATOR_DISTINCT` (verdicts), `PROCESSED` (green-hub set). Used to resolve «is this one coin or several different KM/Hede?» before promoting `merge_decisions/<entity>.yml`. Carries the worked record of the 9-component 2026-06-06/07 pass. **Reusable** — add a new `COMPONENTS` entry for the next conflict batch; mirror verdicts into `docs/handoff.md`. (Promoted from the gitignored `scripts/oneoff/` 2026-06-07 so it survives.) | Whenever the merger surfaces a new catalog-index identity ambiguity. |

## Re-running

These scripts assume the **repo root** as cwd:

```bash
.venv/bin/python scripts/maintenance/quality_pass.py
```

If a script fails on first re-run after data has evolved, prefer **fixing the
script forward** over reverting the data — every run informs the next phase.
