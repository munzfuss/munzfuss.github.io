# Session handoff

> **Read at session start, alongside `CLAUDE.md` + `docs/TODO.md` + `docs/SOURCES.md` §13-§14 + `docs/PLAYBOOKS.md`. Glance at `docs/DECISIONS.md` and the latest `docs/notes/YYYY-MM-DD.md` for rationale + recent context.**
>
> Short-term state for the next agent (or future-me) to pick up cold:
> *what was I doing, what's next, what's blocking, what's freshly
> committed but not yet pushed*. This is NOT the place for stable
> conventions (those go in `CLAUDE.md`) or long-term audit items with
> design context (those go in `docs/TODO.md`). Keep it lean — when an
> entry stops being relevant to the immediate next steps, prune it.
>
> **Maintenance discipline**: update at task / chapter boundaries, when
> direction shifts, or when you notice the gap between «what I'd want
> next session to know» and «what's recorded». A typical entry survives
> a few sessions before either being completed (delete) or promoted to
> `docs/TODO.md` (with full context).

## 2026-06-25 — catalogue «/»=«and» split fix + §DA Table A/B (verdicts pending)

> **UNPUSHED** — slash chain a32d944→5a391e6→97a0157→`5f8c2d1`→`8abf341`. `git push` pending.
>
> **Catalogue «/» = «and» split — FINAL (`5f8c2d1` code+tests, `8abf341` data heal).**
> Evolution across the session: a32d944 split on EVERY «/» → produced prefix-less
> «96|T-91»; I interim-fixed it to «keep tight slash whole» (a32d944) and corrected my
> wrong «range» label (5a391e6/97a0157); **user then settled the semantics — «/» = «та»
> (and)**, superseding keep-whole. Final rule in `lib/catalog_codes.split_multi_ref`
> (both surfaces delegate): split on «/», RE-ATTACH the leading alpha prefix of the
> first member to any bare-numeric continuation → Jensen-Skjoldager «T-91/96» = [«T-91»,
> «T-96»]. Number-list guard keeps non-number «/» whole (publisher «Divo/S», «#»-labelled
> tokens); dash «T-81 - T-88» is a separate range notation, untouched; km keeps its own
> split. **Data heal (`8abf341`):** the old code had ALREADY split these into prefix-less
> lists in the seeds — galster `['T-91','96']`/`['T-41','45']`/`['T-31','35']` + Bruun
> `['T21','25']`/`['T-22','26']` — propagated to seed_unified + final. normalise_catalog
> can't re-heal (the «/» is gone), so a one-time nearest-preceding-prefix heal via
> `lib/yaml_io.py` fixed all 4 danish_realm layers (incl. the merged unified-dk-bruun-4056
> `['T21','25','T-22','26']` → mixed dash styles preserved per §0). Blast radius = J-S
> only, danish_realm only; 0 bare-continuation J-S left; build + validate + 357/357.
>
> **§DA remaining cases — re-investigated from source, awaiting verdicts.** Presented
> two tables in chat (NOT yet acted on, no data touched):
> - **Table A (11 coins, real errors):** **(A1) DONE (`cec33b1` cleaner, `6845b0a`
>   data).** `_reroute_foreign_catalogue_refs` → `_clean_catalogue_refs` (galster/
>   sieg/schive/schou/J-S): drops Danish prose («mangler hos», «adskillige
>   katalognumre, se side …», «; unik»), extracts «hhv. X og mangler»→X, routes
>   Ernst (+ existing Hildebrand/Lagerqvist/Rasmusson/Hauberg)→others. Fixed all 7
>   (f1g-168 galster→168, f1g-49 J-S dropped, c2g-172 schive→XV.5, hg-159/hg-155
>   schive→XIV.* + Ernst→others, f1g-78/f1g-74 schou→13/3). Seed cleaned + re-merged
>   (clean) + final patched SURGICALLY (a full re-absorb drifted an unrelated 10-Ducat
>   1604 entry — avoided). test_galster_catalogue_clean (9 tests). **(A2) DONE (`9bc6d09` filter, `18b3002`
>   data).** build_numista_seed had NO §9 filter (build_hede does); added
>   `_excluded_strike_reason` pre-screen (KM «Pn…»/«(OM)» + title «pattern/trial
>   strike»/off-metal/afslag) — caught 34 numista sidecars, all verified genuine.
>   Removed the 10 currently-seeded unambiguous ones (titles say pattern/trial/off-
>   metal, all standalone): user-flagged 314921 + 345593 (was rendering on denmark),
>   + 314933 (was rendering on oldenburg/german_empire), + 7 Bremen/Brunswick dormant.
>   **Batch-2 RESOLVED (`5660be5` + `43bbb7e`/`59d4c2b`).** Two sub-classes split by
>   curator 2026-06-25:
>   • **3 Portugaløsers KEPT** (387243/387448/427984) — unique FULL-VALUE gold show
>     coins (nominal IS the bullion denomination; «1 Portugaløser» = 10 ducats), could
>     circulate at face value (user: «нехай будуть у нас»). 387243/387448 standalone,
>     427984 merged in `unified-dk-bruun-6273`.
>   • **468992 EXCLUDED — §9 OFF-NOMINAL** — title «5 Ducats» (pure ducat weight) but
>     value.raw «1 Krone» (KM PnJ16): a 1-Krone struck in 5-ducat gold; same metal (not
>     off-metal) but would NOT circulate at its stamped nominal → out of scope. Standalone,
>     removed from 3 layers.
>   Filter changes: (a) dropped the bare Krause «Pn» trigger (it conflates die-trials
>   with full-value pieces) — keys on TITLE («pattern/trial strike»/«(Pattern)»/off-metal/
>   afslag) + «(OM)» KM; (b) added an OFF-NOMINAL rule (`32e485e`) — title leading segment
>   exactly «N Ducat(s)/Dukat» AND value.raw non-bullion AND «Pn» in KM (the «Pn» gate per
>   user — keeps overweight/tariff/bad-data out). Verified: still catches all 10
>   already-removed strikes; catches exactly 468992 off-nominal; does NOT touch the 181
>   genuine Ducat coins, «¼ Ducat / 3 Mark» tariff coins, or the 3 Portugaløsers.
>   **Class codified as CLAUDE.md §9 item 5 (`b387ab1`)** with all caveats (off-nominal =
>   nominal≪metal; Scheidemünze is the opposite §6; not dual-denom/equivalent; not
>   overweight/tariff/bad-data). Item 1 (patterns) refined: bare «Pn» not sufficient to
>   skip. Tests + full suite 382/382.
>   (A3) `31393` sieg «SD# 44» → strip stray «#» → «SD 44»; `km-x000-fr-iii-1644` ucoin
>   lange «280 ff.» = prose range-pointer → «280»+note.
> - **Table B (7 coins, faithful to source, NOT errors):** `307035` hede «C4 80.C»
>   (reign-disambiguated, our convention `c4h80.C`); 6× numista lange «… var.»
>   (16b/271/28/331/358 C IV/399 A — legit variant citations, distinct from cf./
>   unlisted that D31 filters). Recommend leave as-is.
> - Next: user verdicts on A3 (sieg «SD# 44» → «SD 44»; ucoin lange «280 ff.» → «280»+note).
>   A1 + A2 (incl. batch-2 Portugaløser KEPT) done; Table B = leave-as-is.

## 2026-06-25 — night: galster foreign-catalogue reroute + catalogue-hygiene audit (§DA)

> **All UNPUSHED** (this night added 4: `9558e85` docs → `1a03f3e`). `git push` pending.
>
> **Autonomous night work** (user: «лишаю тебе на night work, продовжуй доки не завершиш»).
> Stayed inside guardrails: no push, no new errata beyond curator-approved, ambiguous
> catalogue-semantics DOCUMENTED not guessed.
>
> **Galster foreign-catalogue reroute — FIXED** (`e2e3727` builder, `1a03f3e` data).
> 5 Hans (hg-) Galster coins crammed foreign catalogues into `galster`/`sieg`:
> hg-233/234/236/238 had galster «233, Hildebrand 715, Rasmusson ill. 17,
> Lagerqvist 4» (danskmoent COMMA-JOINS cross-refs into the galster string);
> hg-141 had sieg «Hauberg 102». These rendered as «Galster Lagerqvist 4» on the
> denmark page. `build_galster_denmark_seed._reroute_foreign_catalogue_refs` splits
> on comma + routes foreign-NAME-whitelist parts (Hildebrand/Lagerqvist/Rasmusson/
> Hauberg) to `others`; real index stays typed, legit Sieg «[2015] 8» kept. Applied
> surgically to the danish_realm seed (ruamel round-trip) — NOT via `--no-merge`,
> which had a collateral `mint_verified:true→false` flip on a danish_norway coin.
> Re-flowed danish_realm (merge+absorb, 0 stale dropped); rendered «Lagerqvist 4»
> now a plain `others` entry. Verified end-to-end.
>
> **Broader finding → TODO §DA — CORRECTED 2026-06-25 (§0b).** The whitespace scan
> surfaced 688 values, which I FIRST mis-documented as «~677 need curator judgment».
> On verification (when the user asked me to double-check) that was **~93% false-
> positive**: ~640 are LEGITIMATE source notation — chiefly **569 Davenport
> volume-series** (`dav` «EC II 3529» etc.; numista emits «Dav <series>» codes and
> `numista_canonical.py:99-106` routes them to `dav` BY DESIGN) + 44 spaced
> sub-variants (source's literal «762 b») + 16 year/range/yearbook annotations + 11
> Galster-UU sub-series. The **genuine issues are only ~30**: ucoin `km` «UC# N»
> (12, internal id misfiled), bare-dash empties (6), bruun/galster parser garbage
> (~10), lange «N var.» (6, policy), «; unik» (2). Lesson: «contains whitespace» is
> NOT a bad-index signal (Davenport volumes/sub-letters legitimately have spaces) —
> verify the source mapping before flagging. Full corrected breakdown in TODO §DA.
>
> **2 stale royal_holstein assignments retargeted** (`60b7fcf`). The full re-flow's
> «Curator assignments unmatched: 2» were c4h8b + bruun-14770 — coins that folded
> into heads c4h8a (Ungersk Gylden) / c3h14 (Rhinsk Gylden); the assignments still
> targeted the dead pre-fold ids. Classification was never at risk (curated finals
> are guard-preserved), but retargeted c4h8b→c4h8a / bruun-14770→c3h14 to clear the
> debt. Render-neutral (coin-id set unchanged); unmatched 2→0.

## 2026-06-24 (later) — §9a salvage + galster-key fix + full re-flow shipped

> **All UNPUSHED** (30 ahead of origin; this session added 6: `c199b93`→`9e8b6f7`).
> `git push` pending — no «пуш» yet.
>
> **§9a thinning now SALVAGES dropped specimens' distinguishing data** (`c199b93`
> code+test). Before: thinning a ≥5 bucket to min/middle/max dropped every other
> specimen wholesale, losing any distinct catalogue index (the `others`
> sub-catalogue: schrötter#/olding#/dorfmann#/galster sub-variants) or fineness/
> diameter the reps lacked. Now `_salvage_unique(reps, dropped)` (`lib/seed_thin.py`)
> unions distinct catalogue indices onto reps[0] + fills fineness/diameter only when
> reps lack it; redundant weight + per-specimen sources still shed. Wired into both
> `thin_coins` + `thin_kmk_seed.thin`. 7 unit tests (`tests/test_seed_thin.py`).
>
> **galster-key fix (`66649db` code, `381f35a` seeds; kmk 13819→14003).** The salvage
> exposed a latent bug: the thinning bucket key (`_subvariant_key` in both thinners)
> OMITTED `galster` (a type-identity register, like km/hede/sieg/schou; thin_kmk_seed
> also lacked `lange`). So distinct Galster types (57 Kbh-Søsling vs 63 Malmö-Søsling
> vs 104 ChrIII-4Sk) shared one bucket → collapsed → salvage unioned their galster
> onto one rep → f1g-57 bloated to [5,57,57A,57B,63,104,567B] → 7 transitive
> over-merges. Added galster (+lange) to both keys → over-merge resolved (f1g-57 →
> [57,57A,57B]), +184 distinct Galster types recovered. Verified vs danskmoent:
> f1g57 = «Søsling 1524 København, Galster split into 57A/57B groups».
> Plus two KMM `typeNumber` data fixes in `build_kmk_seed._catalog` (curator-approved):
> galster sub-variant case-norm (57b→57B; scoped to galster — Hede/Lange/Schou case
> convention NOT uniformly uppercase) + builder-level source errata for 3 malformed
> strings (309770 «Galster 5 + B», 311330/311331 «G. 567B» → 57B; f1g5/f1g567 both
> danskmoent-404). Errata in the BUILDER not data-`_source_errata` because these thin
> into the 57B bucket and an entry-level carrier wouldn't survive the next rebuild.
>
> **TOOLING LESSON (merge carry-forward):** when a builder's catalog OUTPUT changes
> (errata/case-norm/key change), a routine `--write` (merge) deep-merges the stale
> on-disk catalog value with the fresh one → list-form bloat (e.g. galster ['5','57B']).
> For a non-curated source (KMK/IKMK) flush with `--write --no-merge` once; then
> routine `--write` is idempotent again. Verified: post-flush `--write` holds 14003,
> 0 bloat.
>
> **denmark UK preamble** (`9df01d6`): «sjælland-ський åbent Brev» (Cyrillic-suffix
> hybrid, §2 trap) → «зеландський відкритий лист» (descriptive, parallel to «норвезький
> ордонанс»). DE/EN keep the Danish proper name. Only the preamble; the 5 other UK
> occurrences already used clean «Sjælland åbent Brev».
>
> **FULL RE-FLOW DONE (`9e8b6f7`)** — merger+absorb all 22 entities, propagating the
> thinning + galster fix to `final/`. Merger 24266 seeds → 15433 unified (8763
> confident folds, 963 conflicts logged to match_uncertainty, no coin loss). Absorb
> final 15152; **522 stale non-curated `seed_unsorted` stubs dropped** (their backing
> specimens were §9a-thinned — EMPIRICALLY verified 0 curated entries in the drop set
> via `_is_vanished_stale_final`'s `not _final_is_curated` guard; curated finals that
> lost backing are RETAINED). Build clean; audit §9a = 0 remaining ≥5 buckets / 0
> same-weight dups. The big line-diff (−82k) is the thinning finally reaching final/.
>
> **Minor open (out of scope, flagged not fixed):** `unified-dk-galster-hg-238` (Hans)
> carries «Lagerqvist 9a-f» in its `catalog.galster` field — a Lagerqvist ref misfiled
> into the galster register. Not touched.
>
> **Pre-existing backlog (NOT from this session):** audit_health shows 588 prose-lint
> errors (§W cleanup) + 1 i18n error — coin-data re-flow doesn't touch prose surfaces.

## 2026-06-24 — V1 layer fully removed; all consumers migrated to V2

> **Commits UNPUSHED** (this session added 9: `366c9f4` reference/ → `30a4718`
> docs). `git push` pending — no «пуш» yet.
>
> **V1 is gone.** V2 (`data/v2/{locations,final}/`) is the sole pipeline. Proven
> empirically before each removal: a full default build is **byte-identical**
> (44 HTML files, manifest sha1 `91357407…038a15`) with vs. without each removed
> piece. What was removed + how:
> - **Empirical proof first**: re-ran ALL 10 V2 seed builders with `data/seed/`
>   moved aside → each reproduced its committed coin-id set 1:1 from cache
>   (`data/seed/` was V1-anchor, not a live input).
> - **kmk-seed «staleness» was a FALSE alarm, now permanently fixed**
>   (investigated 2026-06-24, §0b). The committed seed was never stale — it was
>   deliberately curated: bare builder emits ~41490 raw museum specimens;
>   `822833d` thinned to the §9a envelope, `a80019b` dropped exonumia. The
>   thinning used to be a SEPARATE post-pass (`thin_kmk_seed.py`), so a bare
>   `build_kmk_seed.py --write` regressed it — which is why the last coordinated
>   re-seed (`3486bf0`) skipped kmk. **Fixed `12575db`**: `build_kmk_seed.py`
>   now calls `thin_kmk_seed.thin()` itself (scope→exonumia→§9a in one run,
>   idempotent, `--no-thin` escape). Seed resynced to the builder output
>   (`d547bec`, 13796→13819, render-neutral). **Safe to `--write` now; re-seed =
>   no-op.**
> - **ikmk over-sampling — RESOLVED (full §9a thin)** (2026-06-24): ikmk also
>   over-sampled (4354, biggest bucket 734 uncatalogued «1/24 Taler» 1619; reached
>   final as a 63-weight coin). New shared `lib/seed_thin.py` (§9a min/middle/max,
>   optional `catalogued_only` gate) wired into `build_ikmk_seed.py`. First pass
>   used the catalogued-only gate (→ 4328, only −26 — the 734 uncatalogued bucket
>   stayed); curator then chose the FULL thin (`catalogued_only=False`) since an
>   uncatalogued museum record carries no distinguishing signal beyond the
>   sub-variant key + weight. ikmk seed now **1273** (4354→1273, −3081; the
>   734-bucket → ≤3 per mint-keyed sub-variant). KMK uses its own no-gate
>   `thin_kmk_seed.py` (committed envelope 13819). Both builders self-filtering +
>   content-idempotent (only `generated_at` churns, as for every V2 seed). All
>   render-neutral (data/v2/final/ untouched; resyncs on next coordinated re-flow).
>   The `catalogued_only` gate stays as an opt-in for future uncertain sources.
> - `366c9f4` reference/ HTML artifacts · `ba528a9` seed_v2_regroup.py +
>   build_numista_pre1541_seed.py (no callers) · `1deb8ff` build.py V1 render path
>   (−458 lines: load_locations, _merge_seeds_into_raw, --include-v1/--v1-only,
>   V1 cross_ref/render/landing; landing+worker now V2-only) · `adb3b34`
>   `data/seed/` · `de7affd` the 12 `data/locations/<loc>.yml` coin yamls.
> - **KEPT**: the 11 `data/locations/<loc>-references.yml` bibliography sidecars
>   (shared with V2 via `load_v2_locations`).
> - **Consumers migrated** (`4c8505d` + `b99d131`): audit_prose + audit_i18n
>   (pre-commit) now scan `data/v2/locations/` + `data/v2/final/` (curated coins
>   only — skip `_unclassified` + `seed_unsorted`; V1 parity ≈ V1 hit counts);
>   audit_fuss_anchors + audit_ucoin_categories + fetch_numista_api + the
>   yaml_io roundtrip test re-pointed to `data/v2/final/` (or `-references` for
>   the ruamel_loc roundtrip case).
> - **RETIRED notes** (`c855710` + bootstrap in `b99d131`): 8 V1-era one-time
>   passes (enrich_*, dedupe_sources, classify_issuing_entity, ucoin_backfill_metal,
>   bruun 04_cross_match, bootstrap_v2_final_from_v1) — kept for reference.
> - **Docs** (`30a4718`): CLAUDE.md, ARCHITECTURE, V2_PIPELINE, HARVEST_GUIDE,
>   build_numismaster docstring updated to «V1 removed / V2 sole pipeline / native
>   builders». V2_DECISIONS (immutable journal) + TODO (curator list) left as-is.
>
> **Note**: `scripts/oneoff/` scratch scripts still reference `data/locations/`
> coin yamls — that's fine (throwaway tier; breaking on removal is expected).
> The prose/i18n audits surfaced a real **curated-prose backlog** (1238 hits)
> they couldn't see while stuck on frozen V1 — that's a separate cleanup, not a
> migration artifact.

## 2026-06-23 — 4 mixed cross-source dups merged (c5h56, f2h8, f6h31, f7h8) — durable

> **18 commits UNPUSHED** (this turn added `673bf03`). `git push` pending.
>
> **4 «mixed» dup candidates consolidated** (curator-confirmed by image). Distinct
> from the stale-Hede-orphan pattern — these were fragmented across sources/entities
> at the seed_unified level. Each merged into ONE host with §9a list-form catalog
> accumulation, durable via `merge_decisions` (so a future re-flow reproduces them):
> - **c5h56** Christian V «2 Dukat» Hede 56 → host `unified-dk-hede-c5h56`; km-458
>   (KM 458, Bruun 7243) folded in; KM 416.2/458 accumulate.
> - **f2h8** Frederik II «3 Mark» (≡ 1 Speciedaler) Hede 8/8A/8B → host
>   `unified-dk-hede-f2h8`; manual f2h8b (Hede 8B, Bruun 4422 + Numista 142126) folded.
> - **f6h31** Frederik VI «8 Rigsbankskilling» KM 152 Hede 31 → host
>   `unified-dk-hede-f6h31`; 3 heads united (same Bruun lot 17159); metal silver→**billon**
>   (0.375-fine = billon; fixed at the Hede SEED via `_curation_holds:{metal}` so the
>   merger keeps billon — danskmoent's loose «sølv» was the silver source).
> - **f7h8** Frederik VII «1 Rigsdaler» Rigsmønt 1854-55 KM 760.1/760.2 → CROSS-ENTITY
>   merge (Kopenhagen danish_realm + Altona royal_holstein clusters) into ONE multi-mint
>   `unified-dk-hede-f7h8` in **royal_holstein** (overlap-home per c7h33/c8h11a, renders
>   on both pages); issuing_entity joint `[danish_realm, royal_holstein]`; phase DICT
>   `{denmark: I, schleswig_holstein: III}` (curator). `_cross_entity.yml` pulls the
>   Cph cluster out of danish_realm (no fragment there).
>
> **Method (NEW memory lesson):** these deletions removed finals that fold REAL
> seed-backed heads → seed_unified must be made consistent (else fragments). A full
> `merger+absorb` re-flow does that BUT also materialises every pending decision in the
> entity (surfaced last-session items). Solution: re-flow to compute the hosts, then
> **transplant** only the 4 hosts into a backup-restored committed state, judge by
> **semantic-diff** (`scripts/oneoff/semantic_diff.py`) not the line diff — the line
> churn is YAML-anchor renumbering (cosmetic). Semantic diff confirmed EXACTLY these
> 4 coins changed. Build clean (denmark/SH); f7h8 renders on both pages, f6h31 billon,
> c5h56 dup row gone.
>
> **TWO OPEN FOLLOW-UPS surfaced (not in this commit — need curator calls):**
> 1. **c5h56 host carries KM 346, which is actually Hede 3** (`unified-dk-bruun-6808`
>    «2 Ducats» 1673 — a SEPARATE type). Looks like a pre-existing Hede-3-into-56 leak
>    from an older merge. NOT touched. → remove KM 346 from c5h56?
> 2. **danish_realm has 2 pending fragments** from LAST session's decisions that a
>    future coordinated re-flow WILL surface (a full `merger+absorb danish_realm`
>    materialised them this session, then I transplanted them back to committed):
>    `unified-kmk-301777` «1 Skilling» 1771 (bruun-7774 no_merge → correct separation,
>    seed_unsorted) + `unified-kmk-175833` «3 Skilling» 1812 (f6h14-adjacent, seed_unsorted).
>    Both need classification when the next danish_realm coordinated re-flow lands.

## 2026-06-22 — metal-conflict guard + bruun-7774 metal fix + 4 cross-entity-dup consolidation (durable)

> **9 commits UNPUSHED.** All verified (build + tests + empirical re-flow). `git push` pending.
>
> **Metal-conflict guard in `_collect_metal`** (commits `f71601a` + `eb80d9b`).
> When >=2 composed_of members are `metal_verified:True` but disagree on metal,
> the merger/absorb now RAISE `MetalConflictError` (stop → curator decides) —
> it once silently shipped KMM «sølv» over Hede «copper». EXCEPTION: thin-line
> alloy pairs `{silver,billon}` + `{bronze,copper}` WARN + pick by authority
> (bronze IS a copper alloy; museums tag bronze «kobber»). c9h18b «2 Øre» CIX
> resolved this way → bronze (Hede auth 5 > KMM 0). `_THIN_LINE_METAL_PAIRS` is
> the list; new pairs go there. Unit tests `tests/test_metal_conflict_guard.py`.
>
> **bruun-7774 «1 Skilling» 1771 silver→copper** (commit `4a86564`). The guard
> exposed a stale-FINAL bug: the coin was silver but is COPPER (KM 616; ucoin +
> NumisMaster×9 + KMM×4 + Bruun). Silver came from an old over-merge with a
> silver «1 Skilling (?)» group (kmk-301777 et al., KMM-flagged «(?)»). Fix:
> `no_merge` (dk-bruun-7774 ↔ kmk-301777) + metal→copper + drop the stale
> composed_of link. The silver «(?)» group stays a separate seed_unified entry.
>
> **4 cross-entity-id dups consolidated into royal_holstein** (commit `c910fd0`).
> c8h11a / f6h9 / f6h14 / f6h17 each had a stale danish_realm copy + a seed-backed
> royal_holstein copy. Merged each into ONE royal_holstein entry (copper, joint-ie
> → renders on denmark Pass-1 windowed ≤1864 + SH Pass-1; data unioned; clean Hede
> token). **c8h11a is the project's FIRST per-location phase DICT**
> `{denmark: I, schleswig_holstein: II}` (1842 ∈ denmark 18_5_thaler I but SH II).
> One-off: `scripts/oneoff/consolidate_cross_entity_dups_20260622.py` (gitignored).
>
> **Durability — analysed + PROVEN** (the deletion un-folded 2 KMM specimens that
> would PROMOTE as silver fragments on denmark; confirmed empirically). Fix:
> kmk-131538 «3 Skilling» (metal None) → `_cross_entity.yml` fold into RH f6h14;
> kmk-175835 «1 Rigsbankskilling» «sølv» → §9.3 Sølvafslag-exclude via
> `build_kmk_seed.py::_KMM_DROP_IDS` (KMM tags it a coin «sølv», not «afslag» →
> type-filter missed it) + removed from kmk seed / DR seed_unified / f6h17. Proven
> via backed-up full re-flow: merger folds/excludes → danish_realm absorb 0
> fragments; absorb `_enrich_final_entry` preserves all foundation enrichment 1:1.
> New tooling-lesson in memory: «deleting a stale final copy that folded museum
> specimens un-folds them → fragments».

## 2026-06-17 (later) — CI build fix (ruamel) + Hede discrete-year root fix (c7h13a 1798)

> **CI deploy was RED since ≥2026-06-11 — FIXED (commit `6f787bd`, UNPUSHED).**
> Root: the build path top-level-imports `ruamel.yaml` (via `lib/v2_resolver.py`,
> `lib/seed_merge.py`, `lib/v2_seed_writer.py`) but `requirements.txt` never listed
> it — CI's `pip install -r requirements.txt` lacked it, so every push failed at
> the «Validate data» step (`build.py --validate-only`) with `ModuleNotFoundError`
> before any render. Local `.venv` has ruamel 0.19.1, which masked the gap. Fix:
> added `ruamel.yaml>=0.17`. Verified: full `--include-v1` build + `--validate-only`
> both exit 0 locally. **The push of this WILL turn CI green again.**
>
> **Hede discrete-year root fix + c7h13a 1798 RESOLVED (commits `8571258` code+tests
> / `58bc460` data, UNPUSHED).** `build_hede_denmark_seed.py::_build_year_fields`
> collapsed a consecutive year run into a loose `year_first/year_last` span (emitted
> `year_ranges` only with gaps), so the merger could displace it under a wider
> discrete envelope and drop an interior year — c7h13C «1798, 1799» lost 1798.
> Fix: emit one singleton `[y,y]` per attested year (Hede lists are always discrete
> enumerations); `_format_year_label` folds them back to «1795-1799, 1801» for
> display. Materialised: re-seed hede (3 entities, year-only diff: 262 hdr + 1510
> singletons, 0 drift) → re-merge → re-absorb (curation-loss gate REAL-LOSS=0, 4
> benign year-add). Three bonus label corrections (nf3h69 1649-1668→discrete gaps,
> c5h126a/c5h107 1693-1696→1693-1694,1696, c8h3a 1840-1848→discrete) — now-discrete
> Hede years let the merger displace masking ucoin/Numista loose spans (§3a/§4).
> 58 tests green; rendered + verified denmark + SH de/en/uk. Full §CX write-up in TODO.
>
> **Push state:** 3 commits UNPUSHED this turn — `6f787bd` (ruamel) `8571258` (Hede
> fix+tests) `58bc460` (Hede data). No submodule change this turn. `git push` pending.

## 2026-06-16 (later) — Bruun ND-year parser fix (committed) + N#131730 over-merge root-diagnosed (§CW)

> **Bruun «ND (…)» year parser FIXED — commit `2efdb80` (UNPUSHED).** New
> `parse_year_span(lot)` in `build_bruun_denmark_seed.py`: an «ND (…)» attribution
> now captures the full range (incl. abbreviated upper bound, `ND (1607-11)`→1611)
> + sets `year_verified=False` → «(?)» marker; dated strikes keep the plain single
> year. 84 in-scope ND lots affected (45 ranges / 33 single / 6 ca.). `year_label`
> stays a clean decimal per §3a. Logged `docs/SOURCES.md` §13.3.
> **Builder code ONLY — the V2 Bruun seeds are NOT regenerated.** Running the
> builder revealed the seeds are STALE w.r.t. ~10 intervening builder/cache commits
> (`41efdf0` Aagaard→`others`, `4465c1b` km cross-register, cache re-parses
> `f5634abb`/`8af66ec` Aagaard die-combos + FP refs + one new lot dk-bruun-6435 +
> a metal flip). A clean regen folds that catch-up in AND then needs a
> `seed_unified`→`final` re-flow — so it's deliberately deferred to the next
> *coordinated* Bruun regen (batch with the parked apply), not bundled into a
> «year-fix» commit. Verified the fix produces correct ranges on the real cache
> lots before reverting the contaminated regen.
>
> **N#131730 over-merge ROOT-DIAGNOSED → new TODO §CW (UNPUSHED docs).** The
> «missing discrete years» question (user) led to: `unified-dk-hede-c7h13a` is a
> **2+2 over-merge** of two distinct Christian-VII-Altona «1 Speciedaler» types —
> **Hede 13** domestic Speciedaler (danskmoent verified: no KM/Dav, 1795-1801;
> members dk-hede-c7h13a + c7h13b) + the **Albertsdaler** trade coin (KM 640/640.2,
> Dav EC III 1310, 1781-1796; members dk-numista-131730 + denmark-numismaster-145357).
> Merger matched on nominal+ruler+mint+metal; no trade-coin-vs-domestic discriminator.
> **This REFINES the earlier handoff follow-up:** c7h13a's spurious-1781 widen is
> the Albertsdaler over-merge (§CW), NOT a §CU reign-window member — the session's
> year-hold (1795,1797,1799,1801) only MASKS the symptom; the over-merge persists
> (c7h13a still carries dav EC III 1310 + km 640/640.2). The cache 131730.json has
> only min/max (no discrete list) but that's moot — fix the over-merge (split +
> re-flow) before re-harvesting the Albertsdaler's discrete years onto its OWN entry.
> §0b: my earlier «KM-640 cross-register collision» hypothesis was WRONG (Hede 13A
> has no KM at all; match fired on primary signals).
>
> **Numista year_list re-harvest gap ROOT-FOUND → new TODO §CX (UNPUSHED docs).**
> Tracing «why no discrete years for 131730» revealed the 2026-06-10 «501-entry»
> year_list re-harvest covered **danish_norway + 5 German entities only** — the
> Danish-crown track was NEVER re-harvested: range-only-no-`year_list` counts
> royal_holstein 102/154, danish_realm 248/516, gottorp 55/93 (control danish_norway
> 4/365 ✅). ~400+ ungapped Danish-crown numista entries; 131730 is just one. The
> machinery (extractor `d4d1ca8`, Priority-0 queue `handoff_numista_year_list_reharvest.yml`)
> all works — it just never ran on this entity track.
>
> **✅ DONE THIS SESSION (UNPUSHED):**
> - **§CW Albertsdaler split** — committed `2324dc9`. no_merges in
>   merge_decisions/royal_holstein.yml + re-ran merger/absorb royal_holstein;
>   c7h13a now domestic (dav EC III 1313, 0.875/28.893, hede 13A-D), Albertsdaler
>   consolidated onto c7h22ab (km 640.1/640/640.2, Dav EC III 1310). Fixed the
>   absorb's recurring km str-repr corruption on c7h13a + km-696 by hand (0 str-repr
>   left). Build clean (denmark 2081 / SH 727), renders verified on both pages.
> - **§CX harvest** — collected 456 Danish-crown range-only NIDs, queued, drained
>   in-session via Chrome MCP (0.35s, 0 errors): 218 gained discrete `year_list`,
>   238 range-only. Caches committed in submodule `2758b6d41`; queue drained.
>   Cache→Downloads→disk transport (Blob `a.click()`) worked around the
>   javascript_tool ~1.5KB result-truncation.
>
> - **km str-repr (form #2) durable fix** — committed `441b285`. Root:
>   `_merge_km_field` (~2620) now iterates a list-valued register instead of
>   `str()`-ing it whole. Heal: `normalise_catalog` explodes any str-repr element
>   (both top-level-list and register-dict-internal shapes), runs on every
>   absorb/merge/seed-write. `fix_corrupted_km_repr.py` shares the predicate; 0
>   corrupted finals. 10 unit tests (`tests/test_km_str_repr_form2.py`). Integration:
>   re-absorb royal_holstein (previously corrupted c7h13a + double-wrapped km-696)
>   → **0 str-repr** (verified, then reverted to keep the §CW final; the only diff
>   was a benign c7h13a km `{sh:[…]}`→bare-list normalisation).
> - **§CU year-mute mechanism** — curator `year_demote` in `merge_decisions`.
>   `process_entity` stamps `_year_demoted` on named reign-window members;
>   `_union_year_ranges` (now `_collect()` + two-pass) holds them to a last-resort
>   pass (span never widens, years not deleted); `build_unified` propagates the
>   flag to wholly-muted unified entries. 3 culprits declared in
>   `merge_decisions/danish_realm.yml` (galster-hg-27, numista-355730, kmk-279179).
>   40 union tests pass; light-integration confirms bruun-3839→1496, c9h16a→1874-1905.
>   MECHANISM committed; MATERIALISATION deferred to the coordinated re-flow (full
>   bruun-3839 1496-1497 also needs the Bruun re-seed), and the per-case year-holds
>   on bruun-3839 + km-795 stay until then (remove WITH the re-flow so they don't
>   OVERRIDE the mute). §CU updated.
>
> - **✅ COORDINATED RE-FLOW DONE (2026-06-17)** — full pipeline re-run, all 22
>   entities, materialising every deferred fix. Phases: submodule `c18232a7d`
>   (numista parsed-sidecar year_list backfill — §CX Phase-2 that the harvest had
>   skipped: build_numista_seed reads `numista/parsed/<NID>.json`, NOT the raw
>   cache the §CX patch wrote) → `3486bf0` re-seed all sources → `68fae2f` merge
>   (+ year_demote for 4 ND-swallow culprits) → `968af94` absorb (+ retired the
>   bruun-3839/km-795/c7h13a holds). Build clean (denmark 2076 / SH 726 stable;
>   German pages grew with the curator-approved ucoin +1136→+273 final). 0 str-repr.
>   Verified: bruun-3839 → 1496-1497, km-795 → 1874-1905 discrete, Albertsdaler
>   c7h22ab → 1781,1784,1786,1796, the 4 ND-swallow coins → their dated years.
>   Gate widens (34) = Bruun-ND honest-range improvements (single→range, desired)
>   + the 4 fixed swallows; metal bruun-3931 gold→silver = correction (Silver Gulden).
>   **NEW class found + fixed (ND-swallow):** an UNDATED Bruun specimen's broad
>   «ND (1670-99)» range (year_verified=False) was swallowing dated discretes of
>   its merged cluster → demoted via year_demote (same §CU mechanism).
>   **Edge case (was flagged) — ✅ RESOLVED at the root 2026-06-17** (commits
>   `8571258` fix+tests / `58bc460` data): c7h13a's missing 1798 was a Hede-seed
>   bug, not a union one — `_build_year_fields` collapsed consecutive runs
>   (13C «1798, 1799») to a loose span the merger could displace. Fix emits
>   discrete singleton `year_ranges`; c7h13a now renders «1795-1799, 1801».
>   See §CX in TODO.md for the full write-up.
>
> **Push:** the re-flow commits (submodule `c18232a7d` + main through `968af94`)
> were PUSHED 2026-06-17 (submodule `e5cd0b774`, main `d36a536` merging #17).

## 2026-06-16 — overlap-home architecture + merger stage of the global apply DONE; absorb DEFERRED (UNPUSHED, e8de501 + e414a0a + 8d882fe + 1a8097b)

> **✅ FULL APPLY COMPLETE — ALL 22 ENTITIES (end of 2026-06-16, commit 2cf628d).**
> The global apply was extended from the Danish trio to the whole corpus: full
> merger --apply (26007 seeds → 16470 unified) + full absorb --apply, all 22
> entities. Build clean, 38 commits, NOTHING PUSHED. The other 19 entities'
> rendered SETS are unchanged (per-location assembled counts identical to
> baseline — bremen 128, brunswick 524, gottorp/holstein_schauenburg/lubeck/
> oldenburg/osnabrueck/hamburg/hesse/german_empire/lauenburg all stable); their
> file diffs are field-level catalog-normalise + enrichment refresh, no coin
> adds/drops. 0 km hybrids + 0 str-repr km across ALL finals.
> **Follow-up (non-blocking): the migration×full-absorb interaction re-introduces
> c7h13a's year-widen (spurious 1781) + a km str-repr on every full absorb — it
> was data-fixed each time (year 1795-1801 + register-keyed km). The durable fix:
> (a) add the str-repr-explosion (form #2, `fix_corrupted_km_repr.py` logic) to
> `catalog_codes.normalise_catalog` alongside the form-#1 dict-fold; (b) close the
> year-hold gap so the override freezes year_first/last (not just year_label) for
> a migrated foundation. Both surfaced only on c7h13a (the one migrated coin with
> a register-keyed SH km + a §CU reign-window member).**
>
> --- Danish-trio detail (still valid, now part of the full apply): ---
> All goals materialised + verified on BOTH denmark + schleswig_holstein pages:
> - **KM631** → ONE coin `unified-dk-hede-c7h33a` in royal_holstein:
>   11_333_thaler/I, joint `[danish_realm, royal_holstein]`, km
>   [631,631.1,631.2,631.3], year held 1778-1785 (§CU — the kmk-122886
>   reign-window 1766-1808 suppressed). Renders on both pages via Pass 1.
> - **Frederik D'or** → ONE coin `unified-dk-hede-f7h1b` (royal_holstein), both pages.
> - **Royal-Danish** mint → Kopenhagen (numista re-seed) materialised.
> - 7 curated c7h/dk-tid finals migrated dr→royal_holstein (ie→joint); c7h33c
>   folded into KM631; c7h11c consolidated into dk-tid-79168.
> - **c7h13a** year-hold 1795-1801 (Hede 13A-D) — suppressed a spurious 1781
>   widen that had dropped it from the 9¼-Fuß phase-III window; renders again.
> - The **km cross-register code bug FIXED at source** (commit 4465c1b): the
>   absorb no longer emits the hybrid `{'sh':[...], 'value':X, 'register':Y}`;
>   0 residual hybrids; km-696 / c5h121 / c7h13a resolve on both pages. (This
>   was a PRE-EXISTING latent bug the apply surfaced — `fix_corrupted_km_repr.py`
>   38f4f67 had only data-patched c5h121; the absorb re-corrupted it every run
>   until this fix.)
>
> Build: denmark 7640 drop / 2084 assembled, SH 982 / 727; id-set deltas sane
> (bulk-promotes + consolidations + migrations); no regression. **`git push`
> when ready.** Remaining follow-ups (separate, non-blocking): §CV (generalise
> `_home_entity` to consumes-map-driven, also schauenburg_pinneberg); §CU
> (systemic reign-window year-union downweight, so per-case year-holds like
> KM631/c7h13a become unnecessary).

**Architecture fix (the curator's home-file model).** A coin's `issuing_entity`
may be a list (joint mint = circulation in several political entities); the
VALUE keeps the full set, but the HOME FILE must be the overlap entity that
maximises page-coverage. `royal_holstein` is the SH∩Denmark overlap (consumed
by BOTH pages), so a coin with royal_holstein in its IE must home to
`royal_holstein.yml` to render on both via Pass 1 (not the fragile Pass-2
intersection). Shipped:
- `_home_entity` royal_holstein-priority (e8de501) — was `sorted(ie)[0]`
  (alphabetical → danish_realm). Migrated the 7 already-joint misfiled finals
  (6 danish_realm + 1 danish_norway) → royal_holstein; verified 7/7 on both
  pages. **General consumes-map-driven rule (also schauenburg_pinneberg) = TODO §CV.**
- cross-entity stamp derives issuing_entity from MINT, not scalar target
  (e414a0a) — so a joint cross-entity-merged coin keeps joint VALUE + homes to
  the mint-derived overlap entity.
- Re-seed numista (8d882fe) + hede (1a8097b): joint coins re-home to
  royal_holstein. Critically — `_home_entity` is consulted ONLY at the seed
  WRITE step; the merger writes seed_unified + absorb writes final BY
  PROCESSING ENTITY, so raw seeds must re-home first (and a cross-entity
  decision's target_entity IS its home file → KM631 target corrected
  danish_realm→royal_holstein).

**Merger stage DONE (1a8097b), scoped to the Danish trio** (danish_realm,
royal_holstein, danish_norway — all affected members live there). Verified: KM631
→ ONE coin `unified-dk-hede-c7h33a` in royal_holstein (joint VALUE, km
[631,631.1,631.2,631.3], 12 members); Frederik D'or → ONE `unified-dk-hede-f7h1b`
royal_holstein (9 members); fragments absorbed; 0 «absent» warnings.

**Absorb DEFERRED — drift review needed first.** The full re-derive of the trio
surfaced accumulated drift since the 2026-06-09 re-merge. The per-entity
`audit_curation_loss.py` OVER-reports it (a re-homed coin reads as a danish_realm
loss though it's gained in royal_holstein — verified f6h14/f6h17 keep full
catalog+weights there). Genuine items to vet before `absorb --apply`:
- **4 §CU reign-window year-widens** (km-695-4 →1820, f5h24 →1763, danish_norway
  kmk-149434 →1643, kmk-194284 →1648) — same class as bruun-3839/km-795; need
  per-case `_curation_holds` (the year-hold override cebf090 handles them) OR
  the §CU systemic fix. (c4h8a Ungersk 8A+8B→1591-1593 is a LEGIT accumulation,
  not pollution.)
- **catalog/measurement drops** (kmk-149272 hede127; c7h29/c4h68/c5h74 weights/
  fineness) — confirm drift-correction (stale re-grouped-member data) vs §9a
  regression.
- **3 metal flips** (dk-tid-71072/78931/79553 billon→silver; km-358 silver→billon)
  — confirm verified-wins drift-correction vs regression.
**Drift review DONE (2026-06-16) — all ~12 genuine items BENIGN.** Verified per-item:
4 year-widens are legit type-spans/accumulation NOT reign-windows (no §CU holds
needed); catalog drop (kmk-149272 hede127) is stale (no current member attests
it); measure drops are rounding artifacts (c7h29 0.563→0.562) / re-grouped-member
data (c4h68) / §9a thinning (c5h74); metal flips are §4 verified-wins corrections
(billon→silver ×3 via Hede/NumisMaster verified) — and km-358 silver→billon is a
CORRECTION (ucoin mislabelled silver but its own fineness 0.281 = billon). The
per-entity audit over-reported re-homed coins as losses. NO §9a regression, NO §CU
pollution.

**BUT `absorb --apply` (trio) revealed a real CROSS-ENTITY CURATION-MIGRATION gap
— reverted.** When a hede SEED re-homed danish_realm→royal_holstein (the 26-coin
re-seed) but its CURATED final + classification stayed in danish_realm, the absorb
drops the danish_realm final (backing gone) AND bulk-promotes a FRESH royal_holstein
final WITHOUT the curation → fuss/phase LOST (KM631 c7h33a went 11_333_thaler/I →
seed_unsorted; c7h11c vanished). The absorb finals + classification_decisions
pending-regen were `git checkout`-reverted; back to the correct pre-absorb state.

**8 curated re-homed coins need their curation to follow to royal_holstein BEFORE
absorb:** unified-dk-hede-c7h33a/c7h33c/c7h26/c7h28 + dk-tid-79553 (11_333_thaler I),
unified-dk-hede-c7h13a (9_25_thaler III), dk-tid-79166/79168 (9_25_thaler II). Fix
= EITHER add royal_holstein `classification_decisions` assignments {coin_id, fuss,
phase, kind} for each (the bulk-promote then applies them — established mechanism,
but coin_id must match the royal_holstein seed_unified id post-re-home) OR migrate
the 8 finals danish_realm→royal_holstein with ie→joint (like the 7 in e8de501).
The assignment route is cleaner. **This is a focused continuation — do NOT rush at
turn-end.**

### ⚠ APPROACH CORRECTED 2026-06-16 — the assignment route below was TESTED and is INSUFFICIENT; use MIGRATION

**Tested in-session (then reverted):** adding the 7 royal_holstein
`classification_decisions` assignments + `absorb --apply` (trio) gave a PARTIAL,
messy result — only 4 of 7 landed in royal_holstein (c7h33a/c7h26a/c7h11a/c7h11b);
**c7h28 + c7h13a stayed in danish_realm** (their CURATED danish_realm finals are
spared by the stale-final-drop, so they persist there and the rh assignment can't
displace them); **c7h35 + c7h11c vanished** (sub-variant fold). Root cause: the
assignment+bulk-promote route only works when the old curated final is dropped —
but a curated final is SPARED, so it stays in danish_realm and the coin is NOT
re-homed.

**CORRECT route = MIGRATE the curated finals** danish_realm→royal_holstein with
`issuing_entity → [danish_realm, royal_holstein]` (the same surgical move proven
for the original 7 in e8de501, verified 7/7 on both pages), THEN absorb (the
migrated rh final is the foundation the re-homed seed_unified enriches; the dr side
loses backing → stale-drops cleanly). Migrate the danish_realm finals for:
unified-dk-hede-c7h33a (KM631; c7h33c folded in) / c7h26 / c7h28, dk-tid-79553,
unified-dk-hede-c7h13a, dk-tid-79166, dk-tid-79168. **Also:** KM631 (c7h33a)
carries a PRE-EXISTING reign-window year 1766-1808 (member kmk-122886, Hede 33A,
year_verified anchor) — it should be 1778-1785; add a §CU `_curation_holds:
{year_ranges, year_label}` on the migrated KM631 final (year-hold override
cebf090). And confirm the c7h11c/c7h35 sub-variant folds (Hede 11C / 35 — distinct
rows or correct fold?). The fuss/phase/kind VALUES in the block below are still
correct (reuse them for the migrated finals' fields, NOT as assignments):

~~Paste these 7 assignments into classification_decisions/royal_holstein.yml~~
(SUPERSEDED — values-reference only):

```yaml
- coin_id: unified-dk-hede-c7h33a    # KM631 (was danish_realm c7h33a+c7h33c)
  fuss: 11_333_thaler
  phase: I
  kind: scheide
  reason: '11⅓-Thaler Kurantmøntfod scheide. Curation follows the hede SEED re-home danish_realm→royal_holstein 2026-06-16 (overlap-home rule e8de501); fuss/phase carried from the pre-re-home danish_realm final. KM631 2 Skilling Christian VII (Hede 33A/B/C).'
- coin_id: unified-dk-hede-c7h26a    # was danish_realm unified-dk-hede-c7h26
  fuss: 11_333_thaler
  phase: I
  kind: scheide
  reason: '11⅓-Thaler scheide; curation follows hede SEED re-home 2026-06-16.'
- coin_id: unified-dk-hede-c7h28
  fuss: 11_333_thaler
  phase: I
  kind: scheide
  reason: '11⅓-Thaler scheide; curation follows hede SEED re-home 2026-06-16.'
- coin_id: unified-dk-hede-c7h35     # was danish_realm dk-tid-79553
  fuss: 11_333_thaler
  phase: I
  kind: scheide
  reason: '11⅓-Thaler scheide; curation follows hede SEED re-home 2026-06-16 (V1 dk-tid-79553 backing now in c7h35).'
- coin_id: unified-dk-hede-c7h13a
  fuss: 9_25_thaler
  phase: III
  kind: kurant
  reason: '9¼-Thaler kurant; curation follows hede SEED re-home 2026-06-16.'
- coin_id: unified-dk-hede-c7h11a    # was danish_realm dk-tid-79166
  fuss: 9_25_thaler
  phase: II
  kind: kurant
  reason: '9¼-Thaler kurant; curation follows hede SEED re-home 2026-06-16 (V1 dk-tid-79166 backing now in c7h11a).'
- coin_id: unified-dk-hede-c7h11b    # was danish_realm dk-tid-79168
  fuss: 9_25_thaler
  phase: II
  kind: kurant
  reason: '9¼-Thaler kurant; curation follows hede SEED re-home 2026-06-16 (V1 dk-tid-79168 backing now in c7h11b).'
```

**CAVEATS to check during verify (not blockers, but confirm):**
- **`unified-dk-hede-c7h11c`** (a migrated final, fuss 9_25_thaler) has NO backing in
  royal_holstein seed_unified (the c7h11 seed_unified is a/b/**d**, no c · h11c — it
  folded). On absorb it will consolidate into a c7h11 peer or orphan. CONFIRM whether
  Hede 11C is genuinely a distinct sub-variant that should stay a separate row (then
  it needs its own seed/handling) or correctly folds. The bad-absorb «c7h11c vanished»
  was this fold.
- **km-683/695/721/760/761** (migrated V1-curated finals, no seed backing) are
  orphan-curated → absorb SPARES them (curated, not vanished-stale) → preserved. f6h15
  has backing → preserved. Confirm all 7 migrated finals survive the absorb.

**Sequence:** paste the 7 assignments → `absorb --apply` (danish_realm, royal_holstein,
danish_norway) → `audit_curation_loss.py` (should now show 0 real loss beyond the
benign re-homes) → `build --include-v1` → verify: KM631 → ONE coin
`unified-dk-hede-c7h33a` 11_333_thaler/I royal_holstein on BOTH pages; the 7 c7h/f6
assignments + migrated finals keep their fuss; FrD'or one coin; drop counts don't grow
vs baseline (denmark 7626 / SH 985); spot-check the c7h11c fold → commit. seed_unified
is committed (correct merge, KM631/FrD'or united); finals are at the correct
pre-absorb state. Everything revertible; nothing pushed (31 commits local).

## 2026-06-15 — curation-loss field-diff GATE CLOSED (UNPUSHED, 4b466b2 + fce45f1 + cebf090)

The pre-apply gate is now COMPLETE — supersedes the earlier «verified safe»
caveat in the KM 631 entry below, which only covered entry-DROPS, not
field-level overwrites. New tool `scripts/maintenance/audit_curation_loss.py`
(pure compute via `process_entity`, never writes) diffs the would-be-written
final against the current final on the RE-DERIVED loss-risk fields (year_*,
mint, metal, catalog xsrc, fineness/weight/diameter), skipping
`_curation_holds`-protected fields. Field-category map (from reading
`_enrich_final_entry`): IMMUTABLE (fuss/phase/kind/fraction/nominal/ruler/
mintmaster/issuing_entity) + GAP-FILL (note/verification_note/inscription_*) +
UNION (sources/composed_of) are SAFE; only the RE-DERIVED set can lose curation.

**Full-project result: exactly 2 absorb-stage losses**, both year-widening from
a reign-window composed member — `unified-dk-bruun-3839` (galster-hg-27
1481-1513 v=false widened curated 1497) + `km-795-1-chr-ix-1874` (hede-c9h16a
1863-1906 would back-date the decimal 10 Øre, struck only from 1874). Both
PROTECTED via dict-form `_curation_holds` (curator kept 1497 for bruun-3839).
Everything else benign: 155 Royal-Danish→Kopenhagen mint folds (VERIFIED
against the live Numista source N#18277 = «Royal Danish Mint (Den Kongelige
Mønt), Copenhagen, Denmark (1739-date)» — harvester stored only the institution
name `mints[].name`, registry recovers the city the source states; 121 are
list-form where Kopenhagen is already present from a Hede/Bruun co-member) + 1
benign Malmø→Malmö diacritic (bruun-3839) + 1 year-ADD enrichment. Post-fix
audit: **REAL LOSS widen=0/cat-drop=0/measure-drop=0/metal=0**.

**Mechanism fix shipped (cebf090):** `_curation_holds` on year was INSUFFICIENT
— the held branch did `_union_year_ranges(members)`, folding foundation year
INTO the member union, so it froze only the display label while year_first/last
still leaked to the reign window (and year_first drives §8.2 phase). Changed to
OVERRIDE: a frozen year is authoritative, member ranges don't widen it. Blast
radius 0 (these 2 are the only year-hold entries).

**Deferred systemic follow-up (TODO §CU):** the root cause is `_union_year_ranges`
blindly unioning reign-window placeholder members (year_verified=false full-reign
span like galster-hg-27; OR a loose Hede sub-variant span like c9h16a, v=None)
with tighter same-type attestations. A clean systemic rule (downweight
full-reign-span members when tighter attestations exist) would self-heal future
cases without per-entry holds, but the two pollution signatures differ
(v=false reign-anchor vs v=None loose-range) → needs careful design +
regression testing. Per-case holds suffice for now.

## 2026-06-15 — KM 631 cross-entity merge decision DECLARED (UNPUSHED, 022a754)

KM 631 (2 Skilling, Christian VII, Hede 33 with sub-variants 33A/33B/33C,
struck 1778-1785 at Altona AND Kopenhagen) was fragmented into 3 final rows:
`unified-dk-hede-c7h33a` (Hede 33A, KM 631/631.1, danish_realm) +
`unified-dk-hede-c7h33c` (Hede 33C, KM 631.3, danish_realm) +
`unified-denmark-numismaster-58049` (+ numista N#42563, no Hede, royal_holstein,
seed_unsorted). Split = cross-letter (Hede 33A/C, §9a gate won't unite on RAW
overlap — same class as Frederik D'or) + cross-entity (Altona numismaster/numista
copies bucketed to royal_holstein by mint). Fix = `_cross_entity.yml` force-union
of all 12 seed members, **target_entity: danish_realm** (Danish-realm coinage, Hede
c7h volume); the build's `_derive_issuing_entity` (bd9126b) then renders it joint
[danish_realm, royal_holstein] via the Altona mint → both pages. Pre-scan verified:
9 members home=danish_realm, 3 (numismaster-58048/58049, numista-42563)
home=royal_holstein pulled+excluded. fuss/phase carry from the c7h33a/c7h33c
foundation (11⅓-Thaler I) + their classification_decisions assignments.
**Declarative — materialises on the global merger --apply.** Resolves the
2026-06-14 «single royal_holstein» mis-model flagged in the Royal Danish entry.

**Pre-apply curation-loss gate — VERIFIED SAFE (read-only absorb --dry-run).**
danish_realm/royal_holstein/danish_norway all report «Stale finals dropped (no
backing): 0» → absorb undoes NO curation; curator assignments apply (4+6+0, phase
re-tags survive); net final deltas +22/+4/+1 are legitimate monotonic-guard
re-promote + de-dup reconciliation (current final is behind the pipeline), NOT
loss; 5 enrichment conflicts logged to match_uncertainty (surfaced, not lost). The
km-repr fix survives (seed_unified already clean → absorb reconstructs clean km).
**CAVEAT:** this dry-run reads CURRENT seed_unified, which does NOT yet carry the
KM 631 / Frederik D'or merges — those materialise only after merger --apply. Full
apply effect (new merges + Royal Danish→Kopenhagen rebuild) needs merger --apply
first, then absorb, to be diffable end-to-end. Tree is clean → a verification apply
is fully revertible via `git checkout`.

## 2026-06-15 — issuing_entity derivation for SH-struck crown coins SHIPPED (UNPUSHED, bd9126b)

`build.py::_derive_issuing_entity` (+ `_CROWN_MINT_REALM`): at assembly, a coin
with `issuing_entity == danish_realm` struck at a crown-owned Holstein mint
(Altona/Glückstadt) gets its issuing_entity recomputed as the union of mint-
realms → **Holstein-only strike = royal_holstein; Altona+Kopenhagen = [danish_
realm, royal_holstein]**. Criterion = issuer + circulation, NOT bare mint-
location (curator decision): the issuer-owns-mint guard holds because the crown
owned those mints, and `royal_holstein ⊂ danish_realm` politically so a duchy-
only strike is PURE royal_holstein not joint. Scoped to danish_realm (Pass 1/2
curated only; seed entries untouched) → commission strikes of other issuers at
Altona (Schaumburg-Pinneberg pre-1640, Plön, 1848 Provisional Govt) keep their
own entity. Applied in the two-pass: Pass-2 intersection tests the derived ie
(SH page picks them up) + the resolved coin carries it. Render-only, durable
(absorb's foundation-immutable ie never sees it). Effect: **29 coins (22 joint
+ 7 pure royal_holstein)** now render on BOTH Denmark + SH; km-743 (Copenhagen-
only) stays danish_realm; 1126 Copenhagen-only realm coins unchanged. Verified:
full build clean, ALL per-location drop counts unchanged (no regression).
**Deep-analysis note:** `classify_mint_to_entity` itself encodes the flawed
bare-mint criterion → it would misclassify Altona-struck Danish *seeds* as
royal_holstein; make it issuer-aware (KM register / denomination / ruler) before
the seed-builders become authoritative.

## 2026-06-15 — SH 11⅓ collapse + 18½ per-page phase derivation SHIPPED (UNPUSHED, dc24d7f + fcbf5fe)

Phases are location-local generalisations over a global Müntzfuß (§7); a build
drop fires when a coin's stored scalar `phase` isn't among the consumer page's
windows for that fuss (`build.py:1005-1023`), so cross-periodised coins vanish
from one page. Source review (Wilcke `/wilcke/w3f1.htm`, danskmoent Møntlove)
established the SH 11⅓ sub-phases 1773/1788 are political/institutional, NOT
standard changes (kurant never abolished — «man hang stadig ved Kuranten»;
Altona struck 11⅓ to 1812).

**SHIPPED (dc24d7f):** SH `phases.11_333_thaler` collapsed 3→1 `I[1726-1813]`
(matches DK); 6 coins re-tagged phase II→I (direct final edits + durable
`classification_decisions` assignments); the «retired/only-until-1788» claim
corrected on every surface (SH closing/timeline + DK phases/timeline/
fuss_periods) → Speciedaler became Holstein's PRIMARY from 1788 but the kurant
itself continued; refs_pool gained `wilcke-1788-speciebank-kurant` +
`sh-speciesbank-1788`. Build: drops DECREASED (denmark 7652→7646, SH 991→986),
citations resolve, no stale claims.

**SHIPPED — 18½-Thaler via per-page phase derivation (commit fcbf5fe, option b).**
The first-tried «add 1841/1854 phases to DK» was BROKEN (narrowing DK's single
phase I[1813-1875] dropped its phase-I coins with years 1842+, +52 regression,
proven by build → reverted). The fix is build-side: `build.py`
`_DERIVE_PHASE_FROM_YEAR = {"18_5_thaler"}` — for that fuss the assembly COMPUTES
each coin's phase per consumer page from `year_first` against THAT page's
windows (stored phase wins only as a boundary tiebreaker). No phase-window
edits, no coin re-tag, denmark.yml untouched. On the Denmark page 18½ keeps its
single wide I[1813-1875] so every 18½ coin (incl. SH-periodised stored-II/III
dual-mint coins) derives to I and renders; on the SH page each derives to its
finer I/II/III/IV year-window. Verified: full V2 build clean; drops decreased
(denmark 7646→7626, SH 986→985) and unchanged on every other location; km-721/
760/761/683 render on BOTH pages.

**Other granularity desyncs — widen `_DERIVE_PHASE_FROM_YEAR` per fuss after
review:** 9¼, 9-Thaler, kronemont, reichsdukatenfuss, courantdukatenfuss,
guldkrone, kronemont_chr_iv all have differing DK↔SH windows; adding each fuss
key to the set resolves it the same way. Do a quick per-fuss «realm-wide law vs
political event» sanity check + a build-drop diff before widening (deliberate,
not blanket). The 2 refs `danskmoent-moentlove-1841` +
`forordning-rigsdaler-rigsmont-1854` were prepared then removed — not needed by
the derivation approach (no DK phase prose added); re-add only if the DK 18½
prose is later expanded.

## 2026-06-14 — KM render-leak fix + two pipeline fixes staged for the coordinated apply (UNPUSHED)

10 commits unpushed (origin/main..HEAD). This session, in order of the user's reports:

1. **KM str-repr corruption — FIXED + applied (commit 38f4f67).** 6 V2 final
   entries carried a `catalog.km` list whose first element was a Python
   str-repr of the real KMRef-list (`"['63', {'value':'103','register':'DK'}]"`),
   a leftover from the 2026-05-31 «44-false-positive» `str(km_list)` bug
   (the write path is long fixed; only the baked data remained). Repaired via
   `scripts/maintenance/fix_corrupted_km_repr.py` (faithful explode+dedup, no
   register re-adjudication). Trigger coin c5h121 now renders «KM-DK# 103 ‖
   KM-SH# 63». seed_unified was already clean; only final changed. Verified:
   0 leaks across schleswig_holstein + denmark, 3 langs.

2. **2 Frederik D'or Hede 1B+1C merge — DECLARED, NOT applied (commit 17b4e69).**
   User: «це одна монета». Diagnosed (empirically via `match_pair`): the
   auto-matcher's §9a `_has_type_strong_agreement` gate uses RAW catalog
   overlap, so sub-variants (Hede 1B vs 1C, KM 750.2 vs 750.3) don't overlap →
   pair drops to low_confidence → never unites. Mint was NOT the blocker
   (both carry Altona). Same cross-letter class as Ungersk Gylden 8A/8B.
   Fix = per-entity `merge_decisions/royal_holstein.yml::merges` (9 source
   seeds). Dry-run preview confirms one unified entry, no catalog conflicts.
   Takes effect on the next merger+absorb apply.

3. **Numista «Royal Danish» mint — registry fix DORMANT, NOT propagated (commit c9d9f8d).**
   «Royal Danish» = «Royal Danish Mint» (Den Kongelige Mønt) = Kopenhagen,
   verified via Numista cache (`mints[].name`, `mint_text`). The seed writer's
   « Mint»-strip reduced the API name to «Royal Danish», absent from the
   registry → surfaced as a bogus mint on 418 V2 entries (all sourced from
   numista). Fixed at the single source of truth: added «royal danish» +
   «royal danish mint» to the kopenhagen alias set in `mint_registry.py`.
   Dormant for render (build reads final mint as-is). User chose to defer
   propagation to the coordinated apply. **At apply:** the 24 numista seeds
   carrying `['Altona','Royal Danish']` become `['Altona','Kopenhagen']` →
   `classify_mint_to_entity` returns `[danish_realm, royal_holstein]` (multi)
   instead of scalar `royal_holstein`. **KEEP this — do NOT drop Copenhagen.**
   §0b CORRECTION (2026-06-15): an earlier caveat here hypothesised the
   Copenhagen was a «spurious Numista guess» to authority-drop. That was a
   hypothesis-as-conclusion and was REFUTED on verification: for 19 of the 24,
   Copenhagen is independently confirmed by Bruun and/or NumisMaster (and Hede
   for KM 631) — they split the KM sub-variants by mint (.1=Kopenhagen,
   .2=Altona, etc.). These are GENUINE multi-mint Altona+Copenhagen types, so
   the `[danish_realm, royal_holstein]` joint classification is CORRECT (they
   render natively on both pages). The other 5 (KM 600/651/767/763/958) have no
   independent corroboration but no refutation either → keep per §0b. NOTE: KM
   631 is therefore a genuine joint coin — the «single royal_holstein, denmark
   consumes it» modeling chosen on 2026-06-14 was under the wrong premise;
   joint `[danish_realm, royal_holstein]` is the accurate model (pending user
   confirmation).

**→ The «coordinated full apply» now bundles 3 things** (all gated on the
curation-loss audit, TODO #6 / parked task #4-#8): (a) Ungersk Gylden
cross-entity merge (commit 431a18b, `_cross_entity.yml`); (b) Frederik D'or
merge (17b4e69); (c) Royal Danish seed-rebuild (re-run `build_numista_seed.py`
from cache — NO live API — then merger+absorb). Sequence: curation audit →
re-run numista seed-builder → full merger `--apply` (no `--entity`, so the
cross-entity source-side excludes apply) → absorb dry-run gate → absorb
`--apply` → build `--include-v1` → verify. The merger/absorb REBUILD fresh
from members, so stale «Royal Danish» is replaced (not appended) once the
seed source is fixed — addresses the «additive-only» concern.

## Denmark gold-gylden Rhinsk/Ungersk reclassification — SHIPPED 2026-06-12, UNPUSHED (commit 682e5e5 + d4d7e3a + eefddf5)

Discriminator between `rhinsk_gylden_fod` (Rhenish gylden, .75 / 18 Karat /
72 per Cölln. mark — **academic source: Wilcke 1950 w7-2 p.184 «Rinske
Gylden (18 Karat, 72 Stkr.)»**, ref `wilcke-rhinsk-gylden-1524-standard`) and
`reichsdukatenfuss` (Ungersk/Dukat, .986) is FINENESS, not weight. Numista's
generic "Goldgulden" label hides this → systematic misrouting. danskmoent/
Galster classify each coin (Galster 27 = Rhinsk; Galster 46 / c2g-89 =
Ungersk). Fixed so far:
- Frederik I 1527 (Galster 59) → rhinsk_gylden_fod (commit eefddf5).
- Hans ~1497 N#355730 (Galster 27, danskmoent hg27 «den ældste i
  Skandinavien») → rhinsk_gylden_fod; now the EARLIEST Danish Rhinsk Gylden
  (commit 682e5e5). reichsdukatenfuss de-facto anchor corrected 1481→1513
  (Christian II Ungersk Galster c2g-89, already on the fuss) — the old prose
  wrongly used the Hans Rhinsk coin as the .986 anchor.

**OPEN follow-up (flagged, not done): ~58 seed_unsorted gold gylden/dukat
coins** on danish_realm carry the same Numista-"Goldgulden" ambiguity (e.g.
f2h7e Ungersk / f2h7g Rhinsk 1584, kmk-137161/2 Ungersk 1592, kmk-575432
Frederik I 1531 Ungersk). A Rhinsk-vs-Ungersk classify sweep by
danskmoent/Galster fineness is the next batch task. Mechanism reminder: a
coin only renders on its bar if `phase` is defined for that fuss AND
year_first is within the phase year-envelope (±1) — extend the phase/bar
year_from when a coin predates it (build.py:1005-1023). Duplicates across
sources merge via `promoted_to` + `composed_of` (Pass 1 skips promoted).

## Fuss cross-reference system — SHIPPED 2026-06-11, UNPUSHED (commit 451d0f0; TODO §CT closed)

Prose references a Müntzfuß by stable id now — `[fuss:KEY]` — not a
hand-written `<code>Name</code>` span. Post-render resolver
`scripts/lib/fuss_refs.py::process_html(html, lang, name_map)` (mirrors
`refs_pool`, called at both build.py post-render sites) substitutes the
EFFECTIVE name (per-location `fuss_periods[KEY].name` override layered
over global `fuesse[KEY].name`) and links to `#fuss-KEY` when that card
is on the page (plain `<code>` otherwise; unknown key → visible §0
placeholder). build_landing gained a `fuesse` param for the global-name
map. Migration `scripts/maintenance/migrate_fuss_xrefs.py` (idempotent)
converted 168 refs across fuesse.yml + V1/V2 location yamls. Tests
`tests/test_fuss_refs.py` 7/7. Payoff proven in render: same
`[fuss:reichsdukatenfuss]` → «Rigsdukatfod» (linked) on Denmark,
«Reichsdukatenfuß» (plain) on Hamburg. Cross-PAGE linking deferred (would
need a key→owning-location map). Full spec + as-built:
`docs/fuss_cross_refs_design.md`. **Next:** if a new fuss is referenced
in prose, just write `[fuss:newkey]` — no name, no `<code>`. Optional
follow-up noted in design doc: an `audit_prose.py` rule flagging NEW
hand-written `<code>fuss-name</code>` spans to stop the convention
eroding.

Also this session (2026-06-11), earlier commits 4a86665 / 8428c9f /
627c4a8: Nobel/Rosenobel prose polish — UK «сучасн-»→«тогочасн-» where
period-relative; rosenobel «contemporary→earlier nobel_fod» factual fix;
«Reichsdukat»→«Dukat» (Danish coin name) in the Nobelfod description.

## KMM impossible-year guard — galster-hg-31 1581 fixed (2026-06-11) — SHIPPED, UNPUSHED (4 commits: d5eea8e/bc4a341 then revised fbc926c/d73819c)

Closes the kmk-297794 «1513-1581» quirk surfaced by the Hans Galster-volume
session. Root cause: 25 KMM (natmus) records carry a `creationEvent` with
`yearFrom > yearTo` (raw inversion). The old `build_kmk_seed._year` only
swapped, so an impossible value survived (Hans hvid 1581/1513 → 1513-1581;
1581 is 68y after Hans †1513). New guard: swap when the implied span ≤ 20y
(ordering slip — 7 records, all within reign), else DROP the event's year
(year=None — 18 records, all impossible: truncated yearTo 152/58/675/…,
post-reign yearFrom). Builder fix `d5eea8e`; data `bc4a341`.

- **Materialised** by patching the in-seed records' year fields directly
  (full `build_kmk_seed` re-run RE-INFLATES — thinning is a separate step;
  danish_realm dry-run shows 32215 vs thinned 9630, so DON'T full-rebuild
  to materialise a few rows — patch the thinned seed with the canonical
  ruamel config `typ=rt, preserve_quotes, width=200, indent(2,4,2)` or the
  whole file reformats) → re-merge + re-absorb danish_realm + danish_norway.
  galster-hg-31 1 Hvid Hans now reads 1481-1513; page has 0 year-«1581».
- **REVISED — null → reign-window anchor (`fbc926c` + `d73819c`).** The first
  approach NULLED the year on dropped events. That removed the coin's ONLY
  merger fallback signal, so 6 same-type museum specimens (Christian-IV
  Hede-67 2-Skilling etc.) that share a type-level catalogue but carry no
  fineness/mint stopped merging and surfaced as standalone seed_unsorted
  finals — a regression. Fix: a dropped-all-year record now anchors to the
  named ruler's reign window via `lib.ruler_reigns.reign_window`
  (year_verified=False) — plausible-but-estimated, so the §9a multi-specimen
  merge fires again without the garbage value. 191584 now re-merges into a
  4-member Christian-IV group (year 1588-1648 unverified). Bare-«Hans»
  (no ordinal) doesn't resolve a reign → stays year-None, harmless (merges
  via Galster).
- **❌ CORRECTED — the «KMM Arabic-vs-Roman ruler-scope gap» I flagged here
  earlier DOES NOT EXIST.** I asserted it WITHOUT verifying (§0b lapse).
  `merge_seeds_cross_source._normalise_ruler` ALREADY folds Arabic↔Roman:
  `_normalise_ruler("Christian 4") == _normalise_ruler("Christian IV.") ==
  "christian iv"` → same scope key. The real reason those specimens stood
  alone was the year-null regression above (matcher requires primary +
  ≥1 fallback; nulling the year left primary_true=4 / fallback=0 →
  «insufficient signals» → no_match). Now fixed by the reign-window anchor.
  NB: they still don't merge with the CURATED `c4h67` — but that's a genuine
  metal disagreement (KMM silver vs curated billon), correctly blocked.

## Numista discrete-year (year_list) harvest gap — 501 re-harvested (2026-06-10) — SHIPPED, 3 main + 1 submodule UNPUSHED

User noticed Numista DOES give discrete struck years (1496, 1502) — in the
«Manage my collection» date table — but our data showed the continuous
range «1496-1502». Diagnosed: loss is at the HARVEST step, not the parser.
The thin BO.1/chrome extractor (HARVEST_GUIDE) read only the «Years» range
feature, never the `table.collection` date column, so 501 in-scope
multi-year types had `year_first/last` but `year_list: null` →
`build_numista_seed` fell back to a continuous `year_ranges`. The whole
downstream was already discrete-ready (`parse_numista_chrome` consumes
`year_list`; seed builder emits `[[y,y]]`; merger's `_union_year_ranges`
prefers discretes). The v3 API does NOT help (`parse_numista_api` hardcodes
`year_list=null`; discrete list needs the un-fetched `/types/{id}/issues`).

- **Harvest (`submodule 93b0460d`, cache pointer `<bumped>`):** re-harvested
  all 501 via Chrome MCP same-origin `fetch()` + DOMParser of
  `table.collection` (≈30 NIDs/JS-call, 0.3 s pacing, 0 Cloudflare 403s).
  **417 gained discrete years, 84 confirmed range-only** (kept, NOT
  fabricated). year_list written to raw cache + parsed sidecars.
- **HARVEST_GUIDE extractor upgraded** (`docs`) to capture `year_list` from
  the date table — durable fix so future harvests + re-harvests get it.
- **Materialised (`012fb9e`):** re-parse (surgical — deleted only the 501
  sidecars, re-parsed WITHOUT --force to avoid surfacing 575 unrelated
  newly-parseable types) → re-merge + re-absorb. **412 propagated** into
  rendered finals across danish_norway + bremen_verden + oldenburg +
  braunschweig_lueneburg + sachsen_lauenburg + osnabrueck (gapped labels
  render). danish_norway −3 = lossless Hans-1-Hvid consolidation (the
  prior Galster-volume fix reaching this entity; seed 3903/3903).
- **Residual (entity-routing backlog, NOT this task):** 5 hanseatic_lubeck
  + 144 `_unclassified`-final coins whose numista seed routes to
  `_unclassified` (≠ their foundation's entity) — year_list is in cache +
  `_unclassified` seed, propagates once they're classified. See SOURCES §13.1.
- **Method gotcha for next time:** `parse_numista.py --force` re-parses the
  WHOLE cache and surfaces newly-parseable types (575 → _unclassified, +
  stray hamburg/danish_norway final churn). For a targeted re-parse, delete
  only the target sidecars and run WITHOUT --force.

## Hans Galster volume-scope fix — 1 Nobel year + 31 split-dup consolidations (2026-06-10) — SHIPPED, 2 main UNPUSHED

User flagged: 1 Nobel Hans (Galster 24) rendered «1496-1502» (continuous)
but sources attest discrete 1496 + 1502. Root cause was a **cross-source
matcher gap**, not the year-merge rule (`_union_year_ranges` is correct):
the coin was SPLIT across two finals — `unified-dk-bruun-3831`
(Bruun+Numista+KMM; Numista's loose min/max `[[1496,1502]]` drove the
year) and `unified-dk-galster-hg-24` (discrete `[[1496,1496],[1502,1502]]`).
They never merged because `_catalog_refs` derives the Galster volume-scope
from the ruler via a regex requiring a NUMERAL — **Hans has no ordinal**,
so his refs stayed bare `galster` while the Galster-source entry sat in
`galster/hg`; same Galster 24 → no catalog tie → `no_match`.

- **Fix (`a37c821`):** make the ordinal optional in the volume-derivation
  regex; map no-ordinal Hans → `hg`. Now bruun/kmk/numista Hans galster
  refs scope to `/hg` and merge with Galster-source entries.
- **Data (`bc6dc40`):** re-merge + re-absorb. 1 Nobel now ONE entry,
  `year_label '1496, 1502'` (discrete wins — period not wider than
  discrete min-max), galster source + Galster 24 + schou 2,3 all unified.
  68 Hans bare-galster seed refs re-scoped; **31 stale Hans foundations
  consolidated into peers** (1 Nobel/24, 1 Skilling/29, Goldgulden/27,
  1 Hvid/31 +17 KMM specimens, …) — all same-galster-number same-type
  (verified: every galster-31 member is Hans 1 Hvid; 0 wrong-ruler merge;
  seed conservation 12819/12819, 0 loss).
- **Surfaced (NOT fixed — pre-existing KMM quirk):** `kmk-297794` (Hans
  1 Hvid, Galster 31) carries a loose KMM date «1513-1581», so the
  consolidated `unified-dk-galster-hg-31` year_label widened to
  «1481-1581» (1581 ≫ Hans †1513). A KMM date-field error on one
  specimen, not a merge defect. Candidate for a KMM date-sanity pass.

## Galster single-coin overview-page recovery: 2/3 Nobel danskmoent source (2026-06-10) — SHIPPED, 3 main + 1 submodule UNPUSHED

User flagged that the danskmoent.dk source on **2 Nobel** (Hans 1502,
N#428886) + **3 Nobel** (Hans 1496, N#428914) had vanished. Root cause:
the Galster classifier (`scripts/lib/galster_parsers/classify.py` rule 3)
routes any non-per-coin-filename page to the `reign_index` skip-parser as
a redundant overview. `1nobel.htm` IS a genuine multi-reign overview, but
`2nobel.htm` / `3nobel.htm` are **single-coin pages** (one catalogued
type each → danskmoent never split a dedicated per-coin page), so they
were silently dropped from the seed and never reached the coins.

- **Fix (`c63779a`):** conservative content-based carve-out in rule 3 —
  ruler-keyword H1 + exactly one Galster number + no overview markers
  («Se også» / «ser således ud» / «Møntrækken» / reign-range header)
  → route to `standard`. Dry-run over all 171 reign_index pages: exactly
  4 flip (2nobel, 3nobel, 6penning, halvrhin), all genuine single-coin;
  167 true overviews untouched. Also extended the galster year regex
  `1[5-6]→1[4-6]` (standard.py + build_galster) so Hans-era 14xx years
  parse — 3nobel's 1496 was being dropped (→ no seed). Blast radius:
  only fr_hg24 (1 Nobel Hans) gains its genuine 1496 year. `_build_sources`
  now falls back to catalog_refs.galster + omits empty volume parenthetical.
- **Data (`99a1c69` + cache `bbad3177`):** re-parse → galster seed (+2
  entries) → merge danish_realm → absorb. 2 Nobel gains catalog galster 26
  + danskmoent/2nobel.htm; 3 Nobel gains schou 1 + danskmoent/3nobel.htm +
  mint union [Kopenhagen, Malmö]. Both render on the Denmark page (verified).
- **6penning** (Erik af Pommern, Åbo, pre-1481) + **halvrhin** (Hans ½
  Rhinsk gylden, u.år) re-parse as single-coin but stay out of seed scope
  (undated, no reign-volume anchor → builder drops them).
- **Forgery-year drop (`3deea9d` + cache `afc092d`, data `e080583`).** Hans
  1 Nobel (fr_hg24) carried 1508 — danskmoent flags «(1508 er falsk)»
  (the only 1508-dated specimen is a forgery). Fixed via PARSER, not
  errata (the source is correct, the parser mis-read it; errata is for
  catalogue-index corrections). `_FORGERY_YEAR_PAREN_RE` strips a paren
  with year+falsk before year extraction; cache-wide only `(1508 er falsk)`
  matches → only fr_hg24 affected. year_label 1496,1502,1508 → 1496,1502.

## Source-quality + Schauenburg entity split (2026-06-10) — SHIPPED, all local/UNPUSHED (`git rev-list --count origin/main..HEAD` for the live count)

Six discrete tasks this session, all committed locally, **0 pushed** (push
needs explicit user OK). Pre-commit hook + V2 build clean throughout.

**(1) Bruun nominal-normalization restored — `f252733` (code) + `7f54d64` (data).**
The Bruun seed builder had lost its display-nominal layer: fresh entries went
in raw (no implicit-«1», roman not converted, fraction glyphs, NAME-parens,
ø-spelling) while 1099 existing entries carried normalized forms — a naive
re-run would degrade all of them. Added `_bruun_display_nominal()` +
`extra_curated_fields=frozenset({"nominal"})` threaded through
`merge_one`/`merge_seed`/`write_v2_seed` (default empty → no-op for other
builders) so existing nominals are soft-preserved, fresh ones normalized.
**parse_metal now runs on the RAW denomination** (parens intact) BEFORE the
display strip — the descriptive paren carries the metal signal («12 Mark
(Courant Ducat)»→gold, «8 Skilling (klippe)»→silver); running it on the
stripped nominal had regressed 3 metals. Proven 0 semantic diff on re-run.
`7f54d64` re-serialized the last PyYAML-style bruun seed (danish_realm) to
ruamel — corpus format consistency.

**(2) Absorb drops finals whose backing vanished — `78d54f2` (code+test) +
`340219a` (data, −17).** Absorb was additive/sticky: a final persisted even
when its backing seed_unified entry disappeared (the 622-exonumia hand-removal
case). New drop: a `unified-*` final with NO live backing AND no curation
(fuss seed_unsorted/None, no note/_curation_holds/promoted_to/curator-phase)
is dropped — two enforcement points (explicit filter on the new final set +
monotonic-guard exclusion so a final dropped by an earlier purge isn't
resurrected). Module-level `_final_is_curated`/`_final_has_live_backing`/
`_is_vanished_stale_final` + 19-case unit test (`tests/test_absorb_stale_final_drop.py`).
Materialized 17 drops (15 cross-source-consolidation dups + 2 sub-variant
re-key dups: dk-hede-f3h135→f3h135a/b, dk-galster-f1g-66→f1g-66c); verified 0
seed orphaned, 0 cross-entity dup, note preserved.

**(3) Re-serialize remaining stale seeds — `fe6574c`.** 5 seed files still in
old PyYAML dash-at-parent style (3 kmk + 2 numismaster) → ruamel round-trip,
0 semantic diff. Pure format (a builder re-run was wrong: kmk writes 0 files
without parse-cache, numismaster re-run is a real data change). Corpus now
uniformly ruamel.

**(4) NGC grade-colour → copper — `ec63ace` (code) + `9720042` (data).**
parse_metal reads the NGC/PCGS colour suffix (Brown/BN/RB/RD, anchored to
«NGC <grade> <colour>» so prose «brown patina» never false-matches) →
("copper", False), placed after explicit metal-words, before the weak
denom heuristics. 24 in-scope flips (Danish bronze Øre, copper Rigsbanktegn,
small Rigsbankskilling, 1677 siege klippe dk-bruun-7277, 1602 copper Penny).
Knock-on: corrected metal unblocked 5 cross-source merges (Bruun KM-entry ↔
Numista N#-entry, e.g. KM-754=N#43524) — verified 0 loss, 0 dup.

**(5) Schauenburg 2-entity split — `997aa83`.** The old
`holstein_schauenburg_county` umbrella conflated two regional traditions →
split into **`grafschaft_schaumburg`** (Niedersachsen, 36 coins —
Stadthagen/Bückeburg/Oldendorf/Rinteln, Mariengroschen tradition) +
**`schauenburg_pinneberg`** (Holstein, 246 — Altona, SH-Courant + imperial
1/24). holstein_schauenburg page consumes BOTH; schleswig_holstein consumes
only the Holstein half (mirrors royal_holstein-on-denmark). Mechanism:
new entity in issuing_entities; mint_registry (4 NS mints→grafschaft;
Schauenburg issuer-name fallback→pinneberg); routing-rule routes_to
grafschaft; **`build_numismaster_seed` now applies route_entity_with_rules**
(was the 6-coin mis-route bug); bruun meta-tag→pinneberg. 123 county finals
migrated verbatim (ids+notes preserved) then merge+absorb reconciled;
test_entity_routing 10 green. See V2_DECISIONS D45 (+ D44 for the absorb drop).

**(6) numista dav-dedup refresh — `b7b2165` (9 entities).** Re-running
build_numista_seed materialized a stale catalog.dav: a 2-elem list with the
SAME Davenport ref in two formats («EC II# 3656»+«EC II 3656») → scalar.
218 entries, 0 other field changed. Seed-layer hygiene only — rendered final
was already clean (absorb's `_fold_catalog_indices` normalizes on accumulate).
numista-only quirk; ikmk/numismaster/bruun verified 0 non-Schauenburg drift.

**CLOSED later in the session (the deferred clean-up, all committed):**
- ✅ **galster 66A/66B genuinely lost — recovered** (`1b9e479` fix + `4c170ca`
  data). NOT a re-key: 66A-B (pre-coronation Electus variant) ≠ 66C. Cause:
  the `seed_merge` supersession-drop keyed on id-STRING and dropped
  `dk-galster-f1g-66` (catalog «66A-B») as if `…-66c` superseded it. Fixed
  catalogue-aware (`_own_cat_has_subletter`). Full re-run of hede+galster
  found NO other dropped sub-variants — blast radius was exactly this 1 coin.
- ✅ **holstein_schauenburg page prose rewritten** (`388e6bb`). Summary →
  historical two-part principality (drop «104-piece pending / IKMK
  undistinguished»); phase prose cleaned of §0z project-meta (source
  file-paths / «Build-Assembly» / «Bulk-Seed» pipeline labels); §2-clean,
  renders both parts.
- ✅ **audits run** — `audit_prose` / `audit_i18n` on the new prose
  (grafschaft_schaumburg desc + rewritten summary/phases): 0 new violations,
  i18n-clean.
- ✅ **SOURCES §13.1** numista EC II# quirk (`9b9d413`); **memory
  tooling_lessons** scoping-bug entry (config-dir auto-revert).

**OPEN / next:**
- 🟡 **Systemic §2 «Taler» → «Thaler» normalisation (curator decision).**
  Project-wide: ~1000+ `nominal: … Taler` (178 «1 Taler», 857 «1/24 Taler»,
  …) + 657 §2 note-prose errors (`audit_prose` backlog). The nominal field
  uses «Taler» pervasively while §2 wants «Thaler» in DE prose — the audit
  flags notes, not nominals. NOT introduced by recent work; needs a deliberate
  project-wide pass (nominals + notes together) or an explicit «keep Taler in
  nominals» convention. The 1 holstein_schauenburg `audit_prose` hit
  (unified-dk-bruun-14913 note) is one instance, left as-is pending this call.
- 🟢 Pre-existing standing TODOs untouched: schou-only (17) catalog-noise;
  ~8 genuine catalog over-merges.

## composed_of re-validate + full re-merge (2026-06-09) — SHIPPED, 3 commits UNPUSHED

The absorb stage is additive + STICKY: once a unified entry lands in a
foundation's `composed_of`, no later run re-checked whether it still
belonged. Earlier mis-groupings (and V1-bootstrap composed_of carried
forward) persisted forever — KM 42 «8 Skilling» (`dk-tid-163034`) had
dragged in «1 Denning» (0.44 g) + «4 Skilling lybsk» (1.822 g) + two
«6 Skilling», polluting the 8-Skilling weight envelope.

**(A) `_revalidate_composed_of` — `51a609c` (absorb code + danish_realm final).**
New absorb-stage pass (default on; `--no-revalidate` to skip). Evicts a
composed_of member iff its normalised nominal GENUINELY differs from the
foundation's AND the two share NO agreeing type-level catalogue — the SAME
nominal discriminator shipped in `match_pair`, applied to existing
membership. **Uses the merge module's synonym-aware `_normalise_nominal`
(imported as `_mg_normalise_nominal`), NOT v2_seed_writer's bare one** —
else synonym pairs («1 Ducat» vs «1 Dukat») false-evict (caught in dry-run:
18→12 once the normaliser was fixed). The weight-tier disambiguator is
DELIBERATELY NOT used (same-nominal weight divergence = specimen variance,
not a different coin; verified 24/38 weight-tier drops were same-nominal).
Evicted members are surgically decontaminated off the host
(`_surgical_decontaminate`: only their EXCLUSIVE weight/source values
removed — orphan + remaining-member data preserved per §9a; twin-
independent, no clean-snapshot needed), dropped from composed_of, and
force-promoted standalone (reuses the over-merge-purge `forced_evict_promote`
path) so they re-home; the discriminator then blocks re-absorption.
danish_realm: 12 evictions / 8 hosts → 10 re-homed standalone + 2 matched
into correct existing finals; **0 coins lost**.

**(B) Nominal folds — `1d08444` (`lib/nominal_synonyms.py`).** Two residual-
edge folds for the discriminator (issuer-PREFIX «Oldenburg. Taler» was
already handled by `_strip_region_prefixes`): worth-equivalence tail strip
(`= …` → "", handles «1 Thaler = 1/14 Cölln. Mark» + the trailing weight-
standard gloss) + `_strip_mint_suffix` (drops trailing «. <Mint>[ og <Mint>]»
when the segment is mint-only — «4 Skilling Rigsmønt. København og Altona»
→ «4 skilling rigsmont»; conservative, leaves «100 Rd. Conr.» / «Cölln. Mark»).

**(C) Full re-merge + re-absorb — `2fcde35` (22 seed_unified + 5 final + 19 cd).**
Materialises the discriminator + both folds across ALL 22 entities (prior
ship covered only 4). 26651 seeds → 17337 unified (9314 merges). **Seed
conservation verified — ZERO seeds lost everywhere**; only `_unclassified`
grew (+322 newly-harvested seeds entering the merge → classification
backlog, NOT a loss). danish_norway/royal_holstein/bremen_verden finals
net −6/−1/−1 from legitimate cross-source de-dup (all underlying seeds
confirmed still reaching a final). KM 42 stays clean (idempotent).

**Deferred / open after this task:**
- **`_unclassified` +322 classification backlog** — newly-harvested seeds
  now in `seed_unified/_unclassified.yml` awaiting entity routing.
- **General re-validate re-homing across transitive over-merges** — the
  current pass evicts identity-mismatches one-level; a transitivity-aware
  variant (re-home dropped members that themselves anchor a sub-cluster)
  was scoped but deferred as regression-prone — own focused session.
- «= X» / «Rd. Conr.» nominals beyond the folds above are curator-territory
  (genuinely ambiguous worth-equivalences) — left as-is.

## Catalog-index normalization + KMM thinning (2026-06-08) — SHIPPED, 5 commits UNPUSHED

Started as the «1 Speciedaler Christian IV (Hede 55)» 3-problem task, grew into a
project-wide index refactor + a museum-citation declutter. **All committed locally,
UNPUSHED (48 total unpushed). Pre-commit hook passed throughout; full V2 build clean,
0 `schou#`/`sieg#` overflow site-wide.**

**(A) Catalog-index normalization — `17c7e91` (code) + `75734e6` (data, all entities).**
- `lib/catalog_codes.py::normalise_catalog()` — folds `others: <code># N` overflow
  into its typed list-field (case-insensitive code, guarded against cf-/unlisted-),
  + case-insensitive value de-dup («Hede 55C» + «55c» → one «55C»). Wired into EVERY
  catalog-write chokepoint: `seed_merge.merge_one` (post deep-merge), `v2_seed_writer`
  pre-write hygiene, `merge_seeds_cross_source.build_unified`, `absorb._enrich_final_entry`
  + a blanket pass over every final entry (catches V1-carryover foundations).
- **Restart-scope registry in `_catalog_refs`** (the §9.4 core): two records sharing an
  index VALUE match only when they share its RESTART scope. Empirically measured:
  **Hede 59 %, Schou 64 %, Sieg 42 %** of distinct values span ≥2 reigns → **per-ruler**
  (`<idx>/<ruler>`); **KM 43 %** spans ≥2 entities → per-register; Galster per-volume;
  Friedberg/Davenport/Numista/Bruun/Lange/NMD/Schive/Skaare/mb (~0 %) → global/bare.
  **Sieg + Schou were BARE before (a §9.4 cross-reign collision bug); now ruler-scoped.**
  `_catalog_chain_consistent` value-compare + both SUB_VARIANT_REFS membership tests
  made scope-aware (`k.split("/",1)[0]`) + case-insensitive.
- Rollout regression analysis (`scripts/oneoff/analyze_index_rollout_regressions.py`,
  gitignored): **0 cross-ruler false-merges**; contained to 3 Danish entities (others 0
  grouping change); 66 §9a museum-specimen consolidations; flagged «anomalies» all
  accounting-equivalent nominals (12 RD Courant = 2 RD Species; 4 Mark = 1 Speciedaler;
  16 Skilling = 1 Mark) + billon/silver — catalog-driven per §9.4. No over-merges.

**(B) natmus errata — `18a5fbe`.** KMM 275643 «2 Skilling 1625» typeNumber «Hede 141»
is wrong (Hede 141 = 8 Skilling 1630, confirmed by genuine specimen KMM 190547 +
danskmoent c4h141; a 2-Skilling 1625 is uniquely Hede 134; natmus's OWN sibling
KMM 335046 is tagged «H. 134A»). `_source_errata` hede 141→134 on the kmk seed
(durable, survives rebuild via `_PRESERVE_ALWAYS_KEYS`). Specimen now groups with
Hede 134; KMM 190547 stands alone as Hede 141.

**(C) KMM museum-citation thinning — `7d37a92` (code) + `758cfba` (data).** 3-category
declutter in `absorb._suppress_weightless_museum_overcollection`, keyed by what each
KMM record carries (image read from cache `related.assets[type=still]` — VERIFIED
equal to the natmus page: 290904 shows 3 photos / 123284 shows «Genstanden er endnu
ikke affotograferet»):
- WEIGHT (±image): untouched — the §9a weight-specimen thinning owns those; always shown.
- IMAGE only (no weight): keep 3 (lowest object-id), hide rest.
- NEITHER (79 % of all KMM cites): keep 1, hide rest.
Hidden via `display: false` (data kept §9a — not deleted); 3266 surplus hidden, 0 weight
hidden. Constants `_KEEP_KMM_IMAGE_ONLY=3` / `_KEEP_KMM_PURE=1`.

**(D) Verified-mint divergence disqualifier — `775660e` (code) + `e8f6215` (data).**
RESOLVED the 290904 question + the whole Christian-IV Wolfenbüttel war-coinage cluster.
`match_pair` now blocks a merge when both coins have VERIFIED disjoint scalar mints AND
no strong TYPE-level catalogue tie (KM/Hede/Galster/Dav/Fr/Lange — not Schou/Sieg). So
the Wolfenbüttel coins (mint Wolfenbüttel verified) no longer false-merge into København
Hede 55 (mint Kopenhagen verified) via colliding Schou. `_shares_type_level_catalog`
tolerates case-insensitive + numeric-core + bare-vs-dot-parent («579»≡«579.1»). Full
re-merge of all 22 entities: **0 verified-mint splits of legit groups** (the 1 candidate
was a dot-parent gap, fixed); effect contained to danish_realm. KMM 290904 + 291969 now
separate seed_unsorted Wolfenbüttel coins; KMM 348808 (genuine Hede 55) stays in c4h55;
foundation mint cleaned [Kopenhagen, Wolfenbüttel] → Kopenhagen. 3 no_merges added
(290904↔348808, 290904↔c4h55, 348808↔291969).

**DONE this session (latest first):**
- ✅ **Nominal discriminator SHIPPED** (`fb7bc80` code, `a6e7f8b` data). `match_pair` now
  blocks a merge when normalised nominals GENUINELY differ (synonym folds + daler/gylden
  wildcard exclude label-variance) AND there's no TYPE-LEVEL catalogue tie (shared KM/Hede/
  Galster/Dav/Fr/Lange/N#, not a weak per-reign Schou/Sieg) — mirrors the §9.4 mint
  discriminator. Caught + fixed a Halvkrone/1½ collision: the «Halv-X» fold now consumes the
  implicit-one («1 Halvkrone»=½ krone, not «1 1/2 krone»). Full re-merge + re-absorb (15
  entities): NET de-dup (table folds > discriminator splits) — danish_realm final 7482→7455,
  royal_holstein 944→941, danish_norway 2101→2099, gottorp +1; 11 entities unchanged.
  Validate + build OK. ~2 residual edge false-splits left (see 🟢 below).
- ✅ **Mixed-number fraction fix** (`6238372`). `normalise_nominal` garbled «1½ Thaler» →
  «11/2 daler» (no separator between whole part + vulgar fraction). Now inserts a zero-width
  space before ANY unicode fraction following a digit (½⅓⅔¼¾⅕⅖⅗⅘⅙⅚⅛⅜⅝⅞) → «1 1/2», and the
  leading-«1 » strip gains `(?!\d)` so «1 1/2» isn't collapsed to «1/2». 0 corruption left;
  «1½» now matches the spelled «1 1/2». Maintenance-side — materializes a few 1½↔1-1/2 de-dup
  matches on the next full re-merge.
- ✅ **Full Numista re-parse materialization** (submodule `b77926fe` 398 sidecars; main
  data commit + classification_decisions). RE-PARSE only (no re-harvest — cache unchanged,
  0 API quota). `parse_numista --force` → `build_numista_seed` → `merge` (15 entities) →
  `absorb` (15). Materialized: 398 types' §9a multi-ref list-form (hede/sieg/schou/km/lange/
  fr/dav) + the session's synonym/Dav-fold/KM-hygiene across all entities. Side-effects of
  the full --force: **+322 newly-parsed types → `_unclassified`** (harvested-but-never-parsed;
  NOT rendered) + **+13 new coins → landgrafschaft_hessen_kassel** (final 77→86, pending
  classification). De-dup from richer refs: danish_realm 7492→7482, royal_holstein 946→944,
  danish_norway 2102→2101 (correct merges, NOT loss; validate OK, build OK).
- ✅ **Davenport volume-fold** (`bc1f9d7` code, `92557b3` data). «EC II» = Davenport
  «European Crowns 1600-1700» (a VOLUME, not a source artifact; numbering continuous, so
  «Dav 3668» = «EC II 3668»). `normalise_catalog` step 4 drops a bare «N» from the dav
  list when a volume-qualified «<VOL> N» (EC/GT/SG/BrSL) with the same trailing number is
  present; bare-with-no-match is kept. Materialized on 145 coins / 9 entities (148 bare
  lines, pure deletion, no re-convergence). This bare+qualified accumulation was a
  side-effect of the multi-KM session's dav accumulation.
- ✅ **Nominal synonym table**
- ✅ **Numista multi-KM support + §9a catalogue accumulation** (`29b5de2` code, `c42c31d`
  data, submodule `d283dd2a`). `numista_canonical.parse_references` (API+chrome) now
  ACCUMULATES every distinct catalogue value into a deduped list instead of first-wins —
  a single Numista type can cite multiple KM (406.1/406.2 mint sub-variants, or 106/56
  across two Krause editions). KM comma-decimals normalise to dots (404,1→404.1).
  `seed_merge` catalog deep-merge UNIONs list-capable sub-fields (was existing-key-wins,
  which silently dropped the fresh 2nd KM); frozen-catalog curation still wins.
  `catalog_codes.normalise_catalog` km hygiene: slash-scalar 683.1/683.2 → list, comma→dot,
  dedup. Materialized for danish_realm + gottorp_duchy (5 types render multi-KM, verified;
  resolved a dup 207063↔65186, 7493→7492 no loss; 683 slash-scalar fixed). **Other 14
  Numista entities' seeds REVERTED** — their lange/dav/fr §9a accumulation (21 multi-ref
  types total: lange 7, dav 6, km 5, fr 2) materializes on the next FULL pipeline run
  (parse --force → build_numista_seed → merge → absorb ALL entities); code is committed.
- ✅ **Catalog-index sort + range-collapse** (`94d6213`). `compute._compute_catalog_groups`
  now expands every index value to its integer members (existing ranges + overlapping/
  adjacent inputs merge: `23-24`+`25-26`+`26` → `23-26`), collapses runs of ≥3 consecutive
  ints into `min-max`, keeps 1-2 runs as individual numbers, and sorts the whole group.
  Applies to ALL index groups (Schou/Sieg/KM/Hede/Lange/…); non-integer tokens (93A, 77.1,
  register-qualified) never collapse and keep parent-before-sub-variant order. Verified on
  KM-42: `Schou# 21, 24, 25, 28, 32-36, 40, 42, 46-48, 51, 52, 56-59, 61, 62, 64, 68, 71-76,
  83, 89, 90, 93, 95, 97-99`. NB: a 2-element run renders as two numbers per the ≥3 rule
  (one-line threshold change if the user later wants ≥2).
- ✅ **Rhinsk Gylden fuss fix** (`896ffef` classifier, `2dc3adf` data). Christian III 1546
  Flensburg gold Rhinsk Gylden (Hede c3h14 «1 Rhinsk Gylden» + c3h15 «2 Rhinsk Gylden»)
  were mis-placed in the SILVER `8_daler_lybsk_fod` by the over-broad Flensborg mint-anchor
  rule (§8a metal-mismatch). Root-cause fix: `allowed_metals` gate on `_MINT_BOUND_FUSSES`
  bindings (gold can't match a silver Fuß). Moved both → `rhinsk_gylden_fod` phase 0 (joins
  the 1536 Roskilde galster-c3g-131; Δ −1.7 % vs soll). Added fraction '2' (soll 6.496/5.002),
  new ref `danskmoent-c3-rhinsk-gylden-1546` (Galster 130, NFM XII s.10), denmark.yml Phase-0
  prose (bar year_to 1536→1546 + title + description + hintergrund + pdate hiatus 27y→17y).
  Verified via computed JSON: both under rhinsk_gylden_fod phase 0, fraction 1/2. The 3
  seed_unsorted Rhinsk Gylden (f2h7g, galster-hg-27, galster-hg-gej) are a SEPARATE
  classification thread — not touched.
- ✅ **§9a weight-thinning → pipeline** (`fb91804` code, `264c4a8` data). `FieldValue.
  display:bool=True` + `compute.normalise_field` skips display:false + `absorb._suppress_
  weightless_museum_overcollection` now thins the weight-giving KMM bucket (≥5 → keep
  min/middle/max by weight, hide the dropped citations + their weight readings by value;
  catalog untouched). 1320 display:false across danish_realm/danish_norway/royal_holstein,
  0 deletions. Verified end-to-end: KM-42 weight column 44→5 readings. **CAVEAT surfaced:**
  the kept min for KM-42 is 0.44 g = the «Denning» anomaly — thinning correctly keeps the
  envelope extremes, so sticky wrong-type specimens now show as min/max. → the re-validate
  pass below is now also needed to keep the thinned envelope CLEAN.

**OPEN / next (all user-directed this session — designs captured, NOT yet built):**
- 🟡 **re-validate-composed_of absorb pass (HIGHEST leverage — now doubly motivated).** The
  absorb NEVER re-validates existing composed_of members (only adds), so historical bad
  merges are STICKY — they survive every re-run + every new discriminator. This is why
  c4h55's foundation mint stayed polluted, and why KM-42 (`dk-tid-163034`, 8 Skilling
  Christian IV) STILL carries 2 wrong-type specimens despite weight-tier-1 already
  rejecting them: **KMM 137199 «Denning» 0.44 g «Sch 83»** (Russian-kopeck imitation) +
  **KMM 591520 «4 Skilling Lybsk Rytterpenning» 1.822 g «Sch 42»** — both merged via a
  bare-Schou collision with the Hede-93 Schou cross-refs. NOW the weight-thinning surfaces
  the 0.44 Denning as the displayed min, so this pass is the clean-up. The fix: an absorb
  pass that re-runs `match_pair(member, foundation)` over every existing composed_of member
  and DROPS those now `no_match`. Self-heals the whole sticky class (KM-42 anomalies via
  weight-tier-1, Wolfenbüttel residue via mint discriminator). Uses only SAFE existing
  discriminators — no synonym risk. MUST dry-run with a printed drop-list for review.
- 🟢 **Residual discriminator edge false-splits (curator-mergeable, low priority).** After
  shipping (below), ~2 edge categories still split as FALSE on danish_realm: a trailing
  «. <mint>» annotation («4 Skilling Rigsmønt. København og Altona» vs «4 Skilling Rigsmønt»)
  and «= X» equivalence nominals («12 Rigsdaler courant = 2 Rigsdaler» vs «2 Rigsdaler»). Too
  niche/risky for a broad fold; if they surface as real duplicates, merge via
  `merge_decisions/`. The forgery splits («1 Skilling samtidig forfalskning» vs «1 Skilling»)
  are arguably LEGIT (distinct items) — leave.
- 🟡 **Classify the 13 new Hesse-Kassel Numista coins** (`data/v2/classification_decisions/
  landgrafschaft_hessen_kassel.yml` pending list). They entered as `seed_unsorted` in the
  full re-parse below — assign fuss/phase (or fix matcher rules) per PB Phase-4. The 322
  new `_unclassified` Numista types are NOT rendered and need no action unless a future
  classification pass routes them.
- 🟢 **Rhinsk Gylden seed_unsorted tail (follow-up to the c3h14/c3h15 fix above).** 3 gold
  Rhinsk Gylden still sit in `seed_unsorted`: `f2h7g` (Frederik II), `galster-hg-27`,
  `galster-hg-gej`. They belong in `rhinsk_gylden_fod` too — classify them (the metal-gate
  fix means a re-run of auto_classify won't mis-route them to silver). «1 Denning» (c4h169)
  = Russian-kopeck-imitation trade coin (1619 Glückstadt) — stays soll-less, NOT Rhinsk.
- 🟢 **Foundation-mint pollution (systemic note).** c4h55's foundation had accumulated a
  wrong mint (Wolfenbüttel) from historical bad merges; the absorb matches against the
  STORED foundation mint (re-derives only in enrich, AFTER matching), so the pollution
  survived re-runs until cleaned by hand. Other foundations may carry similar pollution —
  a «re-validate existing composed_of members against the current matcher» absorb pass
  would self-heal both this and the sticky-member problem.
- 🟢 `mb` index (24 % xEntity, 0 % xRuler) left bare — verify restart axis + scope if
  per-region.

## Soll/Δ-gap sweep (2026-06-07) — 8 coins fixed, 16 surfaced

User flagged on the rendered Denmark page: rows with weight+fineness (so a
Feingewicht is computed) but blank Soll/Δ. Root cause: the build's `_compute_coin`
needs `coin.fraction` to be a key in `fuss.fractions`; many coins had
`fraction: None` (or a fraction the fuss didn't define). **Audit any time with
`scripts/maintenance/audit_hede_seed_loss.py`-style logic OR the inline check
(weight+fineness present, fuss≠seed_unsorted, fraction not in fuss.fractions).**

**FIXED (commits b79ae73, b59267b):** Nobel 2/3 (added nobel_fod fractions «2»/«3»
= 2x/3x the per-Nobel Soll, §0 computation attribution) + 7 coins where the fuss
already defined the key, fraction just None → set deterministic Δ-verified value:
rhinsk_gylden_fod «1»; 8_daler_fod 1 Gulden «1» / 8 Skilling «1/6» (1 Daler=48 Sk);
18_5_thaler 8 Rigsbankskilling «1/12» (8/96) / 16 Rbsk «1/6» (16/96). All Δ within
tolerance.

**SURFACED — 16 coins still soll-gap, need curator decision (NOT auto-set):**
  - `reichsdukatenfuss` «4 Speciedaler» (unified-dk-numista-117501) — LIKELY
    MIS-CLASSIFIED: silver .875 4-Speciedaler (fein 100.71 ≈ 4× 9¼-Speciedaler)
    sitting under a GOLD Dukat fuss. Re-classify to 9_25_thaler «4» (or 9_thaler)?
  - `11_333_thaler` «3 Krone» (numismaster-65368) — gold .993, fein 44.97; ratio
    under this fuss unclear (possible gold-under-silver-fuss mismatch).
  - Scheidemünze / billon sub-denoms where a full-Kurant Soll would be misleading
    (the −% IS the seigniorage per §6 — curator call whether to show it):
    `8_daler_fod` 1 Hvid / 1 Penning / 2 Skilling ×5; `9_thaler` 1 Denning;
    `9_25_thaler` 3 Skilling Lybsk ×5 (Lybsk-skilling ratio needed);
    `8_daler_lybsk_fod` 2 Rhinsk Gylden.
  - Note: fraction auto-derivation (`absorb`/`lib.fraction_infer`) only runs on
    newly-absorbed entries + can't resolve sub-unit ratios (8 Rbsk→1/12) — a
    general «derive fraction over ALL final entries + sub-unit ratio table» pass
    is the proper long-term fix.

## Current focus

**V2 entity-keyed refactor — architecture refined 2026-05-18 to
4-phase fully-automated pipeline with V1 reframed as FOUNDATION
(V1 final yamls become V2 final starting state; V2 accumulates
enrichments on top, never overwrites).** Curator no longer edits
coin fields by hand; curator input is restricted to (a) which entities
the project supports, (b) Phase 3 merge confirmations, (c) Phase 4
classification confirmations — all encoded in script rules or
explicit decision files. Worktree branch `feat/v2-pipeline`.
**Canonical decisions journal: `docs/V2_DECISIONS.md`** (28 + 4
deferred). Detailed plan: `docs/V2_PIPELINE.md`. Detailed
architecture: `docs/ARCHITECTURE.md` §«V2 entity-keyed pipeline».
All other workstreams below paused during V2 unless user redirects.

**§CT — Hede parser data-loss audit (2026-06-06). Catalog-graph tool
(`scripts/maintenance/catalog_graph.py` — promoted from gitignored
`scripts/oneoff/` on 2026-06-07; committed + inventoried in the
maintenance README) surfaced 3 parser losses. Status mixed:**
- **SHIPPED (`49d4727` + cache `f71534b08`, committed, UNPUSHED):**
  per-variant Schou «hhv. … og …» list drop (81 by_letter variants).
  Safe — adds Schou values to existing entries, no id change.
- **SHIPPED — year-prefix Schou (`090b033` + cache `00cd21fb4`):**
  «Schou 1829-37: 2» (year-range : die) / «Schou 1731,1» (Schou
  year,running-no) — systemic `:`-sep + `_strip_year_tokens` (1500-1950,
  Dav exempt). id-safe (0 by_letter changes). f6h4b → 2,3 ; c6h4 →
  1,2,3 landed via 2 targeted seed edits (catalog is DEEP_MERGE so the
  cleaned fresh value couldn't overwrite the stale existing one).
- **SHIPPED — by_letter year-less recovery, Option B (`3fee3fa` + cache
  `62ce09dc2`):** `_extract_letter_groups` no longer requires a year on
  the variant line → +33 pages / +51 seed sub-variant entries (c4h117 →
  117A/117B etc.). The id change (bare `dk-hede-c4h112` → `c4h112a/b`)
  is handled WITHOUT changing the id mechanism (user steer):
  (a) `lib/seed_merge.py` supersession-drop (uncurated bare with FRESH
  sub-letter siblings is dropped — no bare+subletter dup);
  (b) `merge_seeds_cross_source.py::_expand_member` — a merge_decision
  member that is a now-absent Hede bare expands to its sub-letters
  (`dk-hede-c4h112` → {`c4h112a`,`c4h112b`}); genuinely-missing →
  warn+skip (no KeyError). force_union unions all; no_merge pairs only
  across DISTINCT original members. Result: c4h112 «Hede 112 = KM 68»
  applies to both 112A+112B; Hede 117 unifies 117A+117B (the «117B
  dropped» was a stale-merge artifact — clean run unions all). Verified
  via dry-run: 0 by_letter regressions, 0 unified entries lost, +12 net,
  schema OK.
- **REMAINING loss — RE-AUDITED 2026-06-07 (the old «76/53/22/16» count
  was STALE; c4h163/c4h164 are seeded now).** Run
  `scripts/maintenance/audit_hede_seed_loss.py` for the live breakdown.
  Current (662 cache pages): **515 OK, 3 sub_letter_loss, 12 field_swap,
  93 in_scope_absent, 25 oos_post_1914, 14 exonumia.** The actionable
  buckets:
  - **field_swap — Part 1 (nominal) + Part 2 (mint) SHIPPED 2026-06-07
    (commits 3cc3272, 5f6ed52). RESOLVED.** Recovered +34 seed coins
    (danish_realm +20, royal_holstein +14); audit OK 515→526, field_swap
    12→0. Part 2 mechanic: parse_hede.py recovers the mint from the per-variant
    A)/B)/C) lines when the H1 is mint-less — PER-LETTER on by_letter pages
    (78A=København, 78B=Helsingør; verbatim so the builder's _normalize_mints
    matches), AGGREGATE multi-mint on single-coin pages (c7h35). Builder
    by_letter path uses the per-letter mint (fallback to top-level), no-mint
    skip deferred when by_letter supplies mints. Verified 0 removed / 0
    existing-coin mint changes. **Still at the seed layer — run merger→absorb
    to render.** REMAINING field-swap residue: c4h53 (by_hede — needs
    per-spec-group mint, each by_hede group can span mints) + 5 no-variant-mint
    pages (c3h23, f6h1, f6h5, f6h26, f7h7 — no recognised mint on their lines;
    nominal fixed by Part 1, stay absent). Historical detail below:
  - **(superseded) field_swap Part 1-only note (commit 3cc3272).**
    Pages whose descriptor line is «Ruler, NOMINAL» (comma right after the
    ruler, NO mint; mint per-variant on A)/B)/C) lines) had the NOMINAL
    field-swapped into `mint`. parse_hede.py now extracts nominal correctly
    (new `_is_denomination` guard; lone denom-shaped segment after the
    ruler-comma = nominal, not mint). Verified: exactly the 13 pages change
    (nominal set, mint→None), 0 regressions on 843 others. audit field_swap
    12→0. **Part 2 (mint recovery, ~32 coins) NOT done — the real blocker.**
    These pages still don't seed: the mint now lives on the per-variant lines
    and must be recovered PER SUB-VARIANT (78A=København, 78B=Helsingør —
    NOT one aggregate). The simple aggregate-mint version was implemented +
    REVERTED after spot-check showed it mis-assigns (78A shown as Helsingør;
    also `display_for_alias` «Kopenhagen» gets dropped by the builder's
    _normalize_mints which keys on verbatim «København»). Correct Part 2 needs:
    (a) per-letter mint in `_extract_letter_groups` (scan each A)/B)/C) body
    for a registry mint, store VERBATIM); (b) per-hede mint for by_hede pages
    (c4h53); (c) builder by_letter + by_hede paths use the per-sub-variant mint
    (with fallback to top-level). Blast radius: ALL ~80 by_letter pages gain a
    `mint` key → must dry-run measure existing-coin mint changes before shipping.
    Affected field-swap pages: c3h23, c4h53, c4h78, c8h3, f6h24/26/27, f6h5,
    f7h1/4/6/7 (+ bonus mint-less recoveries c7h35, c8h1, f7h11/16/17).
  - **sub_letter_loss (3):** c4h163 (missing B — «Fortuna til randen for
    neden», empty sub-variant line), f4h44 (missing B), f5h3 (A vs B case).
  - **in_scope_absent (93):** mostly pages with no single `specs.default`/
    `specs.by_hede` block, multi-coin pages («1, 2 og 3 speciedaler»),
    undated «u.år» pages, or sub-variant-only «None»-nominal pages
    (c4h124-136, c5h131-135). Per-case review; lower priority.
  - **51 case-mismatched hede sub-letters** (kmk lowercase «119b» vs hede
    «119B») — graph fixed; DATA still case-split. Systemic fix pending
    (normalise hede sub-letter to uppercase at merger ingest / per-builder).
- **Curator verdicts (catalog_graph.py, 2026-06-06).** Two journals:
  `CURATOR_LINKS` = IDENTITY (✔-edge, → `merge_decisions::merges`):
  Hede 96 = KM 42; KM 80.1 = Hede 117/Sieg 41; KM 80.2 = Hede 116/Sieg 40;
  Hede 118 = KM 66; Hede 119 = KM 67; **Hede 108 = 109 = 110 = KM 259**
  (2 Mark Frederik III — all one coin); **Hede 93 = KM 32; Hede 91 = KM
  32.1** (8 Skilling Christian IV — Hede 96 = KM 42 above); **Hede 90 = 94 =
  KM 401** (1 Krone Christian V — all one coin despite the Hede 90/94 split;
  Dav 3642/3643/3645 hang off KM 401.x); **Hede 27 = KM 419 = KM 416** (2 Dukat
  Christian V — Hede 27 carries TWO KM numbers, unusual but factual);
  **Hede 26 = KM 413; Hede 31 = KM 415** (1 Dukat Christian V);
  **Hede 87 = 91 = 95 = KM 186-family = KM 192-family** (1 Krone Frederik III
  = 4 Mark Danske — ALL one coin despite two KM families + three Hede; f3h91
  nominal printed «4 Mark» — surface nominal divergence in match_uncertainty).
  `CURATOR_DISTINCT` = DIFFERENT-COIN (no edge, → `merge_decisions::no_merges`):
  Hede 10 ≠ Hede 14 (2 Dukat Frederik V); Hede 91 ≠ 93 ≠ 96 (8 Skilling Chr IV
  — KM 32.1 / KM 32 / KM 42); **Hede 27 ≠ 56 ≠ 58** (2 Dukat Christian V —
  three distinct coins); **Hede 26 ≠ 29 ≠ 31 ≠ 32** (1 Dukat Christian V — four
  distinct coins; KM 412 + KM A433 also separate. CAVEAT: shared «Schou 8»
  vertex bridges Hede 29↔32 but per curator is most-likely a DIFFERENT die for
  each — not evidence of identity). Hub colouring driven by `PROCESSED` — **ALL
  9 components done (green ✓) as of 2026-06-07.** STANDING TASK (user): work
  through ALL graph cases, recording each verdict — **COMPLETE**.
  **PROMOTED to `merge_decisions/danish_realm.yml` (2026-06-07, commit 80026ab):**
  3 merges (comp 1/2/4 all-one-coin) + 14 no_merges (comp 3/5/7/8/9 distinctness).
  seed_unified re-merged 7908→7895 (−13); verified 0 outsiders, all no_merge pairs
  distinct. **NOT promoted (catalog-attribution, need §4 _source_errata not merge):**
  comp 3 Hede96=KM42 (numista-15669 labels itself Hede 93A), comp 7 Hede26=KM413 /
  Hede31=KM415, comp 8 Hede27=KM419 — these reassign a KM our data attributes to a
  DIFFERENT Hede, so merging would unite curator-distinct coins. See FINAL-CONSOLIDATION below.
- **Graph node-merge rules (`scripts/maintenance/catalog_graph.py`):** per-ruler
  namespacing; Hede sub-letters → one base vertex (case-insensitive
  119A=119a); Schou dies → one set-vertex per Hede; **Sieg dot-sub-numbers
  → one base vertex** (32.1-32.4 → «Sieg 32.x», sub-classes of one coin —
  unlike KM, whose .N can be different coins per §9.4); Dav EC-volume
  prefix stripped; `_resolve_member` self-heals merge-shifted unified-ids.

**SUPERSEDED — the old «Component-5 cross-Hede DATA merge» note (2026-06-06,
«merge 116+117+numista-197176»).** The later SYSTEMATIC component-5 verdict
(catalog_graph pass, user msg «2 скілінга це дві різні монети») is the opposite:
Hede 116 (KM 80.2 / Sieg 40) ≠ Hede 117 (KM 80.1 / Sieg 41) — TWO distinct coins.
This also matches the already-committed Group-B decisions (which keep KM 80.1 /
MC_65041 separate from Hede 116). The split verdict is now pinned via
`merge_decisions::no_merges` (comp 5, commit 80026ab). Do NOT resurrect the
old merge — it was wrong.

**PENDING — FINAL-LAYER CONSOLIDATION of the comp-1/2/4 merges (2026-06-07).**
The seed_unified merge is done (merge_decisions + commit 80026ab), but the
`final/danish_realm.yml` layer still has each merged coin SPLIT across multiple
foundations with CONFLICTING fuss — the merge surfaced a bulk-promote
mis-classification. `absorb` is foundation-immutable (DF1): it flags
«curator classification clash» and SKIPS (won't auto-consolidate). The
`classification_decisions::assignments` mechanism ADDS new finals (for
genuinely-new coins) — it does NOT reclassify/merge EXISTING clashing
foundations. So consolidation needs either a new foundation-merge step or
manual foundation surgery. Curator-guided fuss (user 2026-06-07: «з кронами
ясно kronemont; з марками менш очевидно, не критично, якщо неясно лишай
seed_unsorted»):
  - comp 2  1 Krone Christian V 1690-92  → `kronemont/II` (clear: majority +
            Hede pieces already kronemont/II; precedent «1 Krone Chr V 1676-78»).
  - comp 4  2 Mark Frederik III 1665-67  → `kronemont/I` (clear: all 3 final
            entries already agree kronemont/I; precedent «2 Mark Frk III 1652»).
  - comp 1  1 Krone Frederik III 1652-53 → `kronemont`, phase AMBIGUOUS: Hede
            piece f3h91 = kronemont/I, ucoin piece tid-97152 = kronemont_chr_iv/II;
            both phases' data list «1 Krone Frk III 1652-1653». 9_25_thaler/I
            (numista-143477) is the clear mis-classification (Krone ≠ Speciedaler).
            Needs Hede standard-param check to settle I vs chr_iv/II.

**§CR + §CP/§CQ — KMK (8th specimen source) SHIPPED to final + pages
(2026-06-02/03). All committed locally, UNPUSHED.** Chain of work this
session:
- **Thinning** (`scripts/maintenance/thin_kmk_seed.py`, commit 822833d):
  KMK seed 42182 → 14443 per §9a weight-variance envelope (sort by
  weight, keep min/middle/max per ≥5 sub-variant bucket; id-sorted
  reps when no member has a weight). KMK `measurements` only ever
  carries `Vægt` (weight); ~14 % of object records carry it.
- **Merger hardened for scale** (59faeb4 + 0c26500 + 5a8d9d6): (a)
  memoise `_catalog_refs` (≈2.2×) GATED behind `_CATALOG_REFS_MEMO_ENABLED`
  — merger opts in per-entity-clear, absorb/audit/build leave it off
  (id(coin) reuse across entities would otherwise corrupt — the bug
  that inflated a danish_realm fold count 1→17); (b) **component-scoped
  no_merge** — PASS 1 collects confident+low only, PASS 2 registers
  no_merge ONLY within confident-connected components (≈0.5 % of O(n²))
  — fixes the real OOM that killed danish_realm (89.7M no_match
  frozensets ≈ 11 GB); (c) **PASS 1 parallelised** across cpu-1 worker
  processes (byte-identical, ~3.2×+; threshold `MERGE_PARALLEL_THRESHOLD`
  default 4000). Full re-merge now minutes, not 40-50 min.
- **`_collect_sources` .pdf fix** (7abc3f1) — THE root cause of the
  §CP/§CQ "conflicts": Bruun **Part II** PDF is the sole Bruun catalogue
  hosted on `danskmoent.dk/pdf/` (Parts I/III/IV on stacksbowers.com),
  so the `danskmoent.dk` single-page-host substring mis-classified it →
  url-only dedup collapsed every Part-II lot of a type to ONE citation.
  Guard `.pdf` URLs onto the multi-record (url,ref,type) path. Recovers
  Part-II citations project-wide (danish_norway 248→281). See
  SOURCES §13.
- **seed_unified regenerated** (9d8e08e) + **absorb --apply** (88aa100):
  9947 KMK bulk-promoted to V2 final (16957 total), 593 genuinely-new
  → `data/v2/classification_decisions/` pending (await curator
  fuss/phase). 50 enrichment conflicts remain — ALL benign specimen-
  level Bruun part/lot/page (anchor kept, alternatives in sources[];
  verified 0 citation loss). 1 benign self-foundation fold + 1 stale-
  purge (danish_realm).
- **KM-461 1699 2-Ducat corrected** (bb939ec): was the lone genuine
  conflict — V1 mis-tagged the Frederik IV 1699 *tronskifte* (throne-
  change) 2-Dukat as Christian V / Hede c5h-3 (c5h-3 is the unrelated
  1673 2-Dukat, Sieg 118). Now ruler=Frederik IV, hede_volume=f4h,
  rationale in `_curation_holds`; id slug `km-461-chr-v-1699` kept
  stable. Verified on rendered denmark page (tronskifte note + Frederik
  IV + recovered Bruun Part II lot 14032 all render).
- **Log-hygiene DONE** (a7967a9): `_deep_merge_catalog` no longer logs
  specimen-level `bruun_part/lot_no/page` disagreements as merge
  conflicts (they're expected multi-specimen, anchor + sources[]
  lossless per §9a — already excluded from MATCHING, now from the
  conflict LOG too). Verified all 50 were uniformly that pattern across
  1603→1874 (0 genuine among them). Output byte-identical (diagnostic /
  gitignored only). Genuine single-value conflicts (sieg_hede1971 /
  schou_hede1971 / hede_volume) still logged.
- **german_empire V2 final** (a8ffee0): absorb created it (27
  Reichswährung coins promoted); was untracked after the dir-pathspec
  absorb commit — now committed.
- **Next:** (a) `git push` main (15 commits UNPUSHED; submodule
  `scripts/cache` untouched this session → main only); (b) the 593
  KMK-pending coins in `classification_decisions/` await curator
  fuss/phase assignment (Phase 4).

**Mission temporal scope — Denmark-track anchor rescoped 1541 → 1514
on 2026-05-16 per §BI.** Denmark-Norway track lower bound = **1514**
(Christian II Lovkompleks: Møntordning af Sommeren 1514 Kopenhagen +
Møntordning af 3. August 1514 for Norge + Kvittering Paasketid 1515 +
Sjælland åbent Brev af 24. August 1515 — per Wilcke 1950 p. 183-186
verbatim); German-lands track unchanged at **1559 (1566)** (Augsburger
Reichsmüntzordnung). The 1541 Møntordning is now correctly framed as
the THIRD major Danish-Norwegian Møntordning in the Christian-II-
Lovkompleks lineage, not the first. TODO §BC closed; §BI in progress;
CLAUDE.md mission statement updated; `--year-from` default in seed
builder updated 1541→1514; seed regenerated; denmark.yml header /
timeline / summary deck rewritten. **Schleswig-Holstein + all German-
jurisdiction pages NOT touched** — they keep their 1559/1566 anchor
unchanged per §BI's explicit scope-restriction.

**§BI residual sub-tasks** (still in progress):
- Update `denmark_fuesse_year_boundaries.md` reichsdukat section to
  reference 1514 Lovkompleks as the verified first formal Danish
  gold-standard spec (Nobler 23½K 16/Mark establishes 23½K floor).
- Update `moentordning_1541.md` header annotation: position as
  Christian-III's-third Møntordning in Lovkompleks lineage.
- Update §BF scope-note: «1541-1566 gap» becomes «1514-1566 gap».
- Open sibling TODO for **Galster + Jensen-Skjoldager catalog import**
  (Christian II 1513-1523 + Frederik I 1523-1533 coverage — empty
  1514-1540 sub-window until that import lands). NOT a Hede extension
  — Hede 1957 itself does not catalogue pre-Christian-III rulers.

**§BF Denmark 1541-1566 gap (now «1514-1566 gap»)** sequenced AFTER
§BI lands. Original §BF four operational sub-tasks remain valid for
the 1541-1566 portion (8_daler_fod definition + fuss_periods
A1/A2 + seed-coin promotion c3h3-3A/3B + c3h4/5/7 + 4 new refs); the
pre-1541 portion (Christian II 1513-1523 + Frederik I 1523-1533)
becomes a fifth sub-task pending §AZ (Galster + Jensen-Skjoldager catalog import — new source family, not a Hede extension).

**Open §BF design question — Flensborg post-1544 track (Phase A3/A4)**:
separate `8_daler_lybsk_fod` Müntzfuß for Lybsk-aligned
sub-Mark + 14¼ Lod Daler, OR same Fuß with mint differentiation. Per
`moentordning_1541.md` §7.1 the 1547 Flensborg dual-zone is the
genealogical seed of later `18_5_thaler` / `34_marck` family vs
`9_thaler` family — likely deserves its own Fuß. Verdict pending.

**E1 NO-KM dedup audit on `data/locations/denmark.yml`** (parallel
front, separate from §BC follow-up) — methodology is per-case, with
explicit «за / проти merge» analysis, source links provided up-front
so the user can verify visually before any merge. Cases 1-9 of 46
done (case 9 = c4h79A/B/C/D folded into KM-16.1 + KM-16.2 as two
parallel merges, multi-source `weight_rough_g`/`fineness` preserved
per §9a). Next: **case 10 — c4h84 [A B]**.

The list of 46 cases is generated dynamically by the audit script
(see «Helper queries» section below); the per-case order isn't fixed
but reflects the `dup_pairs_denmark.txt` enumeration.

## Pending verifications awaiting user input

1. **ucoin Composition harvest** (3 productive sessions 2026-05-13;
   paused on Cloudflare). Three sessions cumulative: 121 new sidecar
   entries (98 → 219), 178 metal-field updates. Rate-limit threshold
   characterised: ~50 cumulative requests per session-cookie at any
   pacing 2.5-20 s. Session 4 attempt hit **Cloudflare bot-
   protection challenge** (HTTP 403 + «Just a moment…») which cookie-
   clear cannot bypass. Resume conditions: wait ~24h for Cloudflare
   cooldown, or pass the challenge manually via normal browser
   navigation, or switch IP. ~490 uncached ucoin URLs remain. See
   TODO §M for full details.

2. **Seed audit snapshot** (post-case-9 cleanup) — 605 total Denmark
   Hede-seed entries; 195 auto-suppressed, 9 metal-mismatch guard, 6
   weight-mismatch guard, 1 year-mismatch guard, 394 wholly uncurated.
   Of the 16 guard-survivors, 3 appear to be **false-positive weight-
   guards triggered by outlier values in curated `weight_rough_g[]`
   lists** (km-25 [.49], km-128 [8.428], hede-47 [6.93]); 1 metal-
   mismatch (c5h128 → km-79 SH) may be a billon/silver labelling drift
   that should have caught the fineness-similarity escape hatch but
   didn't. Worth a focused turn before continuing per-case dedup.
   Audit script: `scripts/oneoff/audit_seed_survivors.py` (gitignored).

2. **Case 8 retrospective rigor check** (in flight) — user pushed back
   that case 8 (Hede 59 → KM-100 / KM-135) skipped the per-case «за /
   проти» discipline. I provided all KM-100 source links; awaiting
   user's verdict on whether the «Numista 109973 Bust type I =
   Hede 59A + 59B» mapping is acceptable on year-span-match alone,
   or needs direct obverse-design verification. Same question stands
   for KM-135 (Hede 59C 1646 — no Numista entry, sourced only from
   curator's prior «KM-DK# 135» note).

   ⇒ If user accepts: continue to case 9.
   ⇒ If not: revisit case 8, possibly partial rollback + verification.

2. **«Curated (legacy scalar)» legacy cleanup verification** — just
   purged 45 placeholder entries from `fineness` lists in denmark.yml
   per the new verified-wins-over-unverified rule. Build clean, render
   correct (sample-checked hede-44). User asked for verification
   before any push. ⇒ Awaiting «OK to push» or further checks.

## Harvest routine — anomaly investigation (2026-05-29)

Investigated the autonomous harvest routine's self-logged anomalies
(`scripts/cache/_harvest_handoff.json::runs[].anomalies`). Two systemic,
one class transient.

- **IKMK discovery noise → ✅ scope-purged.** `fetch_ikmk.py` uses
  full-text `quick_search` + a **year-only** fetch filter, so the cache
  had filled to ~90 % out-of-scope. Purged 5791/7259 records (cache
  103→28 MB), kept 1468 German/Scandinavian coins + borderline-HRE.
  Landed on **main** (submodule commit `07014b3`, superproject pointer
  bump `651633d`) — not the worktree, due to a `cd /main` slip; curator
  accepted keeping it there. Keep-rule + verification recorded in
  `scripts/cache/ikmk/_oos_purged_by_scope_2026-05.json` and SOURCES.md
  §13.8. **Durable filter landed** (commit `48dc101`, worktree branch):
  `fetch_ikmk.py` now gates fetch + `scan_cache` on `_is_in_entity_scope`
  (country + object-type); the year-only `_is_in_mission_scope` gate is
  removed. Per the curator's multi-level scope (2026-05-29) year is NOT a
  drop criterion — German/Scandinavian (+ lands under their rule) of ANY
  era are broad keep-scope; only other-country coins + exonumia are
  dropped. Validated: entity-only filter flags just 2 of 1478 cached (a
  British Sovereign + a Koch medal — routine-added OOS the old year gate
  let slip), keeps all 326 German/Scandinavian records outside 1514-1914.
- **ucoin `osnabruck_p3057` skip-loop (occ≥10) → ✅ fixed.** Bucket
  «Bishopric of Osnabrück 1482-1661» — first gap-TIDs were pre-1559 OOS,
  so the picker re-offered + skipped it every run. Re-enumerated per-TID
  years via the ucoin listing (Chrome, 2 pages, 55 TIDs) and split
  `_BR_audit-4_2026-05-24.json::osnabruck_p3057.gap_tids` into 29
  in-scope (1631-1662) + 26 `oos_excluded_tids` (1482-1541). gap_tids now
  lists only the in-scope set, so the routine harvests the 1631-1662
  coins and the skip-loop ends. Committed on the **worktree** branch
  (submodule `417ab9d`, pointer bump `620241f`). Since reconciled:
  `origin/main` was merged into the branch (`f989f9b`), unioning the
  IKMK purge (origin) with this p3057 split in submodule merge `d385a7a`;
  a follow-up normalised the audit JSON back to the routine's indent=2
  (`e475a36` / pointer `04a17a7`). The branch's cache submodule now
  carries both changes.
- **Transient (no action):** chrome-mcp-disconnect (16:34 run),
  cloudflare interstitials (auto-cleared), `osnabruck_p2988` audit label
  drift («Hochstift» vs «City of Osnabrück»).

## Harvest coverage state — ucoin + Numista (2026-05-20)

> **For the next harvest session**: detailed snapshot of where every
> ucoin period and Numista bucket stands. Full per-NID gap manifests
> live in `scripts/cache/{ucoin,numista}/_BR_audit-2_2026-05-20.json`
> + `_BO6_audit_2026-05-20.json`. Don't re-enumerate — use the gap
> lists directly. Period IDs map to `?country=X&period=N` URLs on
> ucoin.net catalog. **31 local commits ready to push** at session-
> handover snapshot (`af737ee` → `dad58eb`).

### ucoin — 15 of 15 periods verified (BR audit-2 complete)

✅ **Verified clean (10 periods, exact page-by-page match):**

| Period | Era | Cached / Total |
|---|---|---:|
| DK p2940 Speciedaler 1582-1624 | Christian IV pre-Kipper | 83 / 83 |
| DK p2939 Glückstadt 1617-1773 | DK-rule Glückstadt mint | 50 / 50 |
| DK p2995 HG-Rendsburg 1716-1720 | Holstein-Gottorp under F4 | 4 / 4 |
| DK p374 Christian IX 1873-1906 | Krone-era memorials | 9 / 9 |
| DK p373 Frederik VIII 1906-1912 | Krone-era full reign | 7 / 7 |
| DK p646 Rigsdaler rigsmønt 1854-1873 | F7 → C9 | 13 / 13 |
| NO p2399 Speciedaler 1648-1699 | F3 + Christian V | 153 / 153 |
| NO p2400 Speciedaler 1699-1745 | F4 + C6 | 23 / 23 |
| NO p1041 Rigsdaler 1746-1812 | F5 → F6 | 32 / 32 |
| NO p883 Rigsbankdaler 1813-1815 | NO under DK 1813-1814 only | 2 / 2 |
| SH-cluster `?country=schleswig_holstein` | Speciesbank-era SH 1787-1839 | 15 / 15 |

🔵 **In-scope subset clear (1 period):**

| Period | In-scope cached | Out-of-scope uncached |
|---|---:|---:|
| DK p220 Christian X 1912-1947 | 7 (1912-1914 window, all major denoms) | 23 (post-1914 OOS — Margrethe II era; no fetch needed) |

⚠️ **Real gap periods (4) — 150 TIDs total**:

| Period | Era | Cached / Total | Gap | Priority |
|---|---|---:|---:|:---:|
| DK p1147 Rigsdaler 1625-1699 | C4 late + F3 + Christian V | 201 / 211 | **10** | A — near-closure |
| DK p846 Rigsdaler 1750-1812 | F5 → C7 → F6 early | 20 / 54 | **34** | B — ongoing |
| **DK p1115 Rigsdaler 1699-1749** | **F4 → Christian VI** | **0 / 59** | **59** | **C — FULL UNTOUCHED** |
| **DK p647 Rigsbankdaler 1813-1854** | **Helstaten F6 → C8** | **1 / 48** | **47** | **D — NEAR-FULL UNTOUCHED** |

**ucoin gap details**:
- p1147: 4 known on page 1 (`96989`, `96438`, `96455`, `96986` — Skilling/Hvid Scheide); 6 more need page-2-5 re-enum to identify
- p846: 34 TIDs listed in audit-2 manifest (8/24/4/2-Skilling + 1-Mark + 8-Skilling Bornholm Speciesbank + 1/6-Rigsdaler family)
- p1115: 59 TIDs listed in audit-2 manifest (Frederik IV + Christian VI Reichsdukatenfuß-era — Speciedaler + Krone + Dukat + Skilling)
- p647: 47 TIDs listed in audit-2 manifest (Frederik VI Rigsbankdaler post-1813 reform + Christian VIII 1839-1848)
- All four gap manifests in `scripts/cache/ucoin/_BR_audit-2_2026-05-20.json` under `NEW_GAPS_DISCOVERED`

### Numista — 8 of 8 buckets enumerated (BO.6 v3 complete)

✅ **Verified clean (5 buckets, 671 NIDs):**

| Bucket | In-scope / Cached | Status |
|---|---:|---|
| DK p2 (1617-1671) | 200 / 200 | ✅ CLOSED (prior BO.5) |
| DK p3 (1671-1791) | 200 / 200 | ✅ CLOSED (prior BO.5) |
| DK p4 (1791-1914) | 124 / 104 (+20 Margrethe II false-pos OOS) | ✅ effectively CLOSED |
| SH cluster (5 issuers) | 67 / 67 | ✅ CLOSED batches A+B |
| DK p1 (1513-1617) | 139 / 125 | 🔵 14 left (last leg — batch K closes it) |

⏳ **Untouched (3 buckets, 471 NIDs — all NO):**

| Bucket | Era | Gap | Pages | URL filter |
|---|---|---:|---:|---|
| NO p2 (1513-1657) | C2 Oslo → F3 early | 193 | 1 | `?e=norvege&st=1-2-3-47-154-5-54&cat=y&p=2&q=200&s=c&o=y` |
| NO p3 (1657-1697) | F3 mid → C5 Kongsberg | 200 | 1 | `&p=3` |
| NO p4 (1697-1814) | C5 late → F6 1813 | 77 | 1 | `&p=4` (78 in-scope, only N#487340 cached) |

**Numista gap details**:
- DK p1: 14 NIDs listed in `_BO6_gaps_manifest_2026-05-19.json::denmark_gaps_by_page.p1.gap` (filter to uncached — 14 of 93 original)
- NO p2-p4 in-scope NID lists in `_BO6_audit_2026-05-20.json::in_scope_buckets.norway`
- Real Phase 2 Numista gap = **14 (DK p1) + 470 (NO p2-4) = 484 NIDs**

### Headline numbers post-audit-2

| Resource | Cache total | In-scope cached | Real gap | % done |
|---|---:|---:|---:|---:|
| **ucoin** | 660 TIDs (incl. 4 batch 25 + audit verification) | 656 / 807 | **150** | **81%** |
| **Numista** | 1058 NIDs | 697 / 1181 | **484** | **59%** |

### Recommended next-session work order

0. **Numista `year_list` backfill** (HIGH — added 2026-05-22 per user N#420401 audit; **WIRED into the routine 2026-06-05**) — 122 cache entries with multi-year ranges and NO `year_list` field. Each needs a Numista-page recheck to distinguish dash-form continuous range from comma-form discrete years. Queue in `docs/handoff_numista_year_list_reharvest.yml` (sorted by year gap descending). **Why it sat at 0/122 for two weeks despite «HIGH»:** the routine batches off HARVEST_ROUTINE.md + `_harvest_handoff.json::priority_override`, NOT this handoff prose (HARVEST_ROUTINE.md §0 «this file's logic supersedes the handoff for routine batching»); priority_override was never set; and the §2.1 picker only fetches *uncached* NIDs, so a re-read of already-cached NIDs was structurally unreachable. **Fix:** added as **§2.2 Priority 0 (STANDING)** — every cron run drains 5 from the queue (re-read + §2.3-B `year_list` encoding) before any BO.7 enumeration, until empty (~24 runs). After the queue closes, re-build the affected Numista seeds + re-merge so the discrete `year_list` reaches the rendered table. Removes the §4 «source years are immutable» violation that turned N#420401's «1496, 1502» into a continuous 1496-1502 range.
1. **ucoin p1147 closure** — 10 TIDs (4 known + re-enum p2-5 for remaining 6). Closes the DK Rigsdaler 1625-1699 bucket entirely.
2. **ucoin p846 closure** — 34 TIDs of Frederik V → Christian VII Skilling/Mark Convention era. Mostly 8-Skilling + 1/6-Rigsdaler variants.
3. **Numista DK p1 closure** — 14 NIDs to close pre-1617 DK Reichsdukatenfuß gold + post-1572 First Speciedaler.
4. **ucoin p1115 OPEN** — 59 NEW TIDs (FULL bucket; Frederik IV + Christian VI Reichsdukatenfuß-era).
5. **ucoin p647 OPEN** — 47 NEW TIDs (Frederik VI Helstaten + Christian VIII 1839-1848).
6. **Numista NO p2-p4** — 470 NIDs across 3 pages (largest single remaining bucket).

### Audit cache files (canonical references)

- `scripts/cache/ucoin/_BR_audit-2_2026-05-20.json` — full per-period enumeration verification, ALL gap TID lists
- `scripts/cache/numista/_BO6_audit_2026-05-20.json` — full per-bucket enumeration with in-scope NID lists for DK p1-p4 + NO p2-p4 + SH cluster
- `scripts/cache/numista/_BO6_gaps_manifest_2026-05-19.json` — original BO.6 v2 explicit gap lists (still valid for SH-cluster + DK p1)

### Technical lessons captured this session (in SOURCES.md §13)

- §13.2 ucoin: listing-page slug-collapse trap (`?text-content-filter` solution), `\t`-separated DOM table layout, comma decimal separator, `a.href` vs `a.getAttribute('href')` Cloudflare query-string blackout, `window.<global>` doesn't survive navigation
- §13.1 Numista: per-NID DOM = HTML `<table>` rows + `<th>`/`<td>` extraction beats innerText regex; listing-page year-regex false-positives (DK p4 = 20 Margrethe II false-pos caught)
- PB-10 (PLAYBOOKS): detached-HEAD recovery + parallel-session rebase collision recovery

### Source-quirks pinpointed this session

- ucoin systematic ruler-misattribution: 4 instances flagged in `_audit_context` for seed corrections (KM-260 «Christian IV» 1665 → actually F3; KM-308 1669 «C5» → actually F3; KM-324 ND-1670 «F3» → actually C5; KM-631 1778-1785 «C9» → actually C7; KM-598 1764 «C9» → actually F5)
- DK p846 «sidecar 86» was inflated — actual listing total = 54 (SH-Holstein cross-leak in §M-era sidecar)
- DK p4 «20-NID gap» = all Margrethe II post-1972 false-positives (year-regex matched historic refs in modern descriptions) — effectively CLOSED

---

## Recent state changes (this session)

* **D39 — bulk_promote `no_basic_peer_only` mode + writer-bug fix**
  (2026-05-19). Extends D37 with a second mode that promotes ONLY
  unmatched unified entries with no metal+nominal peer in foundation;
  D/E/H/C-category cases (catalog/ruler/fallback disagree, low-conf
  near) stay in pending. Writer-bug fixed alongside:
  `_emit_classification_decisions` previously collapsed the flag to
  literal `True` via `bool(...)`, silently downgrading D39 →
  D37-mode-all on the first absorb. 1st `--apply`: 535 N-cases
  promoted across 8 entities, 583 D/E/H/C stay pending. 2nd
  `--apply`: idempotent (0 newly absorbed, 0 newly promoted).
  audit_v2 --quick: 0 violations. See V2_DECISIONS D39 for full
  per-entity breakdown.
* **D38 — NumisMaster builder routes country → canonical V2 entity**
  (2026-05-19). `COUNTRY_TO_ISSUING_ENTITY` mapping refactored to use
  9 canonical V2 entities directly (instead of legacy
  `schleswig_holstein_duchy` alias). Per-cadet-line routing:
  `royal_holstein` / `gottorp_duchy` / `schauenburg_pinneberg` /
  `sonderburg_duchy` / `norburg_plon_duchy` / `glucksburg_duchy`.
  Cascading rebuild: 426 `_unclassified` entries re-routed, V2
  unified regenerated, V2 final absorb-pass surfaces new pending
  for curator review. TODO §BT lists the 4 remaining builders
  (Hede/Bruun/Galster/Numista pre1541) that need similar treatment.
* **Per-case dedup methodology established** (user direction): each
  case gets full source links provided up-front, «за / проти merge»
  written out, user verifies visually before action. Auto-batching
  forbidden.
* **C-bucket auto-suppression in `build.py::_merge_seeds_into_raw`** —
  build-time filter that drops seed coins whose Hede catalog ref is
  already covered by a curated entry. Three safety guards layered on:
  metal-mismatch (cf-companion citations), weight-mismatch (>25 %
  ratio indicates cross-register KM clash or different denomination),
  year-mismatch (>10y with u.år exception). Fineness-similarity
  escape hatch on metal-mm guard for billon/silver labelling drift.
* **Cross-location seed coverage**: denmark seed entries get
  cross-checked against ALL location yamls' curated Hede refs (not
  just denmark's own) — fixes the «Glückstadt Hede entry lives in
  schleswig_holstein.yml curator but in denmark seed» pattern.
* **Bare-basename auto-suppression**: when curator has `hede: '107B'`,
  seed entry `dk-hede-c5h107` (bare basename, parser artefact) is
  also auto-suppressed alongside the explicit `dk-hede-c5h107b`.
* **KM register-aware architecture**: `KMRef {value, register}`
  schema; `Location.km_register: 'DK'`/`'SH'`; render shows bare
  «KM#» when single-entry in page default register, qualified «KM-DK#»
  + tooltip when cross-register or multi-list. Applied to case 7
  (Hede 178 → KM-DK# 25 + KM-SH# 87 same coin in two Krause volumes).
* **Verified-wins-over-unverified merge rule** (codified just now):
  CLAUDE.md §4 + `_VERIFIABLE_FIELDS` in seed builder's `_merge_one`.
  Drops `(?)`-marked values when source-attested candidate exists.
  Followed by legacy-data cleanup (45 «curated (legacy scalar)»
  fineness entries purged).
* **Proof-strike exclusion**: `_KNOWN_PROOF_PATTERNS = {"c4h20"}` in
  seed builder + explicit drop from seed yaml. CLAUDE.md §9 forbids
  proof / trial strikes; mechanism is ready for future entries.
* **«Back-to-top» floating button** in `assets/app.js`: appears at
  `max(viewport, 0.15 × page-height)` scroll threshold; custom RAF
  smooth-scroll with sub-linear duration capped 900 ms.

## Open TODOs added this session

| § | Topic |
|---|---|
| §N | ucoin↔Krause KM-attribution conflicts (earlier session, ongoing) |
| §O | Numista weight typos vs Hede Bruttovægt |
| §P | Denmark DK vs DK+ entity audit (1773 Helstaten cutoff) |
| §Q | Pull Hede / Numista commentary material into coin notes |
| §R | Backfill canonical fineness on `fineness: null` coins (Cat-1 fuesse) |
| §T | Keyword search across coins on a location page |
| §U | Per-specimen Δ-computation needs explicit weight+fineness lineage |
| §V | Numista / ucoin cache coverage audit (no auto-merge pipeline yet) |
| §W | Clean up §0z violations surfaced by scripts/audit_prose.py (873 hits, 663 errors) |
| §X | Fix cross-language inconsistencies surfaced by scripts/audit_i18n.py (76 hits, 43 errors) |
| §Y | Fuß-event vs coin-data span audit (timeline-bar accuracy) — kronemont_chr_iv + 9_thaler-SH outliers |

All entries carry their own design sketches in `docs/TODO.md`;
this list exists only to anchor «what's open» on a quick read.

## Local commit state

* **Main repo**: working tree clean. Recent commits on
  `feat/v2-pipeline` not pushed (user has not granted push
  permission this turn):
  - `917452c` audit(i18n): tighten R5 — flag only Mfuß-compound translations, not bare «стопа»
  - `66a2adc` build: bump scripts/cache → galster JSON regenerations (parser refactor outputs)
  - `5df8370` build: V2 default at /, V1 fallback under /v1/ (D44)
  - `c020d11` build(v2): default bulk_promote_pending → no_basic_peer_only for steady-state
  - `07b88cb` build(v2): expand Bruun year window to 1914 + schema cleanups
* **Submodule `scripts/cache/`**: 7 commits ahead of `origin/main`
  (parse(galster) regen + earlier parse(bruun) Galster/NMD/Schive/
  Skjoldager ref patterns + parse(hede) multi-Hede header layout +
  re-parse 87 hede files + extended marken_fin_udbragt_til). Push
  needs `git -C scripts/cache push origin HEAD:main` once user
  approves; superproject pointer already references the new head
  (`3f566216`).

## Recent changes — URL routing (2026-05-20)

* **V2 → root default, V1 → /v1/ fallback** (`5df8370`, D44).
  V2 pages now render at `site/<loc>/<lang>/index.html`; V1 pages
  move to `site/v1/<loc>/<lang>/index.html`. Two landings:
  `site/<lang>/index.html` lists V2 locations (default),
  `site/v1/<lang>/index.html` lists V1. Root `index.html` redirects
  to default; `/v1/index.html` redirects to V1 fallback. Both
  subtrees emitted on every build; `--v1-only` / `--v2-only` flags
  preserved.
* **V2 invariants audit clean** post-routing (I1-I6 all pass:
  3475 final coins, 3097 unified, 4560 seed, 22 entity tags).

## Helper queries (audit reproducibility)

```bash
# Current dedup-audit candidate file (stale after auto-suppress work
# — regenerable on demand from a sweep script if needed):
#   /tmp/dup_pairs_denmark.txt
# Generated against denmark.yml + seed in a previous session;
# entirely-pending NO-KM cases extracted via the same script.

# Quick «what's the next NO-KM case» check:
python3 -c "
import yaml, re, json
from pathlib import Path
loc = yaml.safe_load(Path('data/locations/denmark.yml').read_text())
seed = yaml.safe_load(Path('data/seed/hede/denmark.yml').read_text())
seed_by_id = {c['id']: c for c in seed.get('coins', [])}
# … (see audit script in chat history)
"
```

The full enumeration script is reproduced in the chat from this
session — search for «E1 NO-KM entirely-pending cases» if context
is preserved, or regenerate by walking the `dup_pairs_denmark.txt`
buckets.

## V2 pipeline refactor — architecture refined 2026-05-18

Late 2026-05-18 session refined the architecture into a **4-phase
fully-automated pipeline with V1 as verification anchor**. Earlier in
the session the autonomous-portion of the original 10-phase plan
landed (Phases 0-2 + 4 + 5 + bidirectional link). After user feedback
on idempotency, merge auditability, and curator-edits-via-rules, the
plan reorganised:

**New 4-phase model:**
1. Raw → typed (per resource) — script-only, unchanged
2. Typed → seed per (entity × resource) — script-only, V2 entity-keyed
3. Per-resource seeds → unified per entity (cross-source merge) — script auto-merges where confident; low-confidence cases surface for explicit curator decision in `data/v2/merge_decisions/<entity>.yml`
4. Unified seed → final fuss-distributed — script applies §8a auto-classify where confident; ambiguous cases surface for curator decision in `data/v2/classification_decisions/<entity>.yml`

**V1 = verification anchor.** V1 (`data/locations/`, `data/seed/<src>/<loc>.yml`) frozen post-bootstrap. V2 reprocesses ALL source data — existing + newly-harvested — through the 4-phase pipeline. First full-cycle run expected to map ~1:1 onto V1 curated. Promotion gate (Phase 9): «V1↔V2 diff is zero or fully explained».

**Curator role:** never edits coin fields by hand. Three decision surfaces only: (a) `data/i18n/issuing_entities.yml` (active entity set), (b) Phase 3 merge decisions, (c) Phase 4 classification decisions. Preferred path is always to update script rules so the case becomes auto-handled.

**Resolved 2026-05-18** (all 4 pending §7 decisions closed; added to
V2_PIPELINE.md §7a):
- `catalog.km` schema = `str | dict[str, str]` (dict form for cross-volume
  KMs); see `scripts/lib/v2_resolver.resolve_km_for_location`
- `coin.phase` = `str | dict[str, str]` (scalar default + dict per-location
  override); see `scripts/lib/v2_resolver.resolve_phase_for_location`
- V2 shares `templates/location.html.j2` with V1 (forked only the
  entity-badge cell to render N badges for list-form `issuing_entity`)
- `audit_v2.py` hard-blocks pre-commit from Phase 7 onwards (stricter
  than the original §7.4 «advisory» recommendation)

**Landed this session (16 commits on `feat/v2-pipeline`):**

| Stage | What |
|---|---|
| Phase 0 (bootstrap) | Skeleton `data/v2/`, audit + V1-side fix for 3 missing `issuing_entity` tags |
| Phase 1 (bootstrap) | `bootstrap_v2_final_from_v1.py` — 1317 V1 curated coins → 20 entity files. Idempotent merge-aware via `lib/seed_merge.py` |
| Phase 2 (bootstrap) | `init_v2_locations.py` — 12 V2 location display-meta files with `consumes_entities`. Preserves manual overrides on re-run |
| Schema | `Coin.issuing_entity: str | list[str]`, `Coin.phase: str | dict[str, str]`, `CatalogRefs.km: + dict[str, str]` + 7 new catalog refs (galster / friedberg / schive / skaare / etc.). `Coin.composed_of` + `Coin.promoted_to` |
| V2 build | `scripts/build.py --v1-only` / `--v2-only` + `_assemble_v2_location()` two-pass (direct + inverse-index) + per-coin phase pre-filter. Timeline + template updated for list-form `issuing_entity` |
| km-120 fix | V1 mint correction (`Royal Mint (Tower Hill)` → `Altona` per Numista N#31895) + V2 regen → `_deprecated_gesamtstaat.yml` retired |
| Phase 3.1 (new model) | `lib/v2_entity_classify.py` (mint → entity classifier) + `seed_v2_regroup.py` (V1 seeds → V2 per-entity-per-source seed yamls). Sanitisation moves catalog refs to nested `catalog:`, drops non-schema fields, coerces broken types. 2727 seed coins across hede/numismaster/bruun/galster/numista classified |
| Pipeline idempotency | All V2 scripts now merge-aware via `lib/seed_merge.merge_seed()`: re-runs produce zero file changes; curator edits in CURATED_FIELDS persist; orphan entries preserved verbatim |
| Phase 6 link | `relink_promoted_v2.py` — bidirectional `composed_of` ↔ `promoted_to` materialiser + `--audit` data-loss detection (flags weight/fineness/source-URL values present in seed but not in canonical host) |
| Doc refresh | V2_PIPELINE.md rewritten to 4-phase model; ARCHITECTURE.md §«V2 entity-keyed pipeline» extended; data/v2/README.md + CLAUDE.md preamble updated |

**Build results — V1 + V2 co-existence works:**
- `site/<loc>/<lang>/`: V1 unchanged (DK 2502, SH 842) — frozen verification anchor
- `site/v2/<loc>/<lang>/`: V2 bootstrap state (DK 3087, SH 485)
- Pre-filter drops 22 coins on V2 DK + 12 on V2 SH (cross-page-phase
  incompatibility — SH-page Phase II/III Helstaten coins rendering on DK;
  Haderslev 1591-1593 outside SH reichsdukatenfuss Phase I)

**Outstanding edge cases — DO NOT manually fix; encode as decision-file entries OR script-rule extensions:**
1. `km-120-chr-v-1787` — V1 mint corrected this session via the legacy data-edit path. Going forward, mint corrections like this come from upstream (parser cache should reflect the source's stated mint; the V1-author's «Royal Mint (Tower Hill)» was a hand-edit on top of source data).
2. `km-683-1-fr-vi-1813` dup-collision — DK side carries Bruun-specimen 1813 only; SH side is the consolidated 1813-1819 multi-mint type. **Goes into `data/v2/merge_decisions/danish_realm.yml`** when Phase 3.2 lands — explicit `merge: [dk-bruun-..., dk-numista-22803-..., dk-hede-f6h24a, ...]` declaration.
3. 4 single-Kopenhagen Helstaten coins (`km-743 / km-770 / km-x001 / km-x002`) — they were on V1 SH page despite single-Kopenhagen mint. V2 mint→entity classifier puts them in `danish_realm` (correct per §3.1 strict reading). If user wants SH visibility, the entity classifier rule should explicitly extend for «post-1813 Kopenhagen-mint Helstaten coins → joint `[danish_realm, royal_holstein]`». Goes into `lib/v2_entity_classify.py` — NOT hand-edits on individual coins.
4. 11 list-form Helstaten coins + 7 scalar `royal_holstein` SH-V1 coins use SH-page Phase II/III for `18_5_thaler`. On V2 DK they're dropped because DK has Phase I only. Resolution: Phase 4 auto-classifier needs to know about the dict-form `phase: {denmark: I, schleswig_holstein: II}` pattern — should detect when the same Müntzfuß has different periodisation across consumer pages and emit dict-form `phase` automatically. Goes into the classifier rules.
5. 6 royal_holstein DK-V1 Haderslev coins (`hede-1`, `hede-3`, `hede-6`, `hede-7b`, `hede-8b`, `hede-156`) — 5 dropped on V2 SH because year 1591-1593 falls outside SH reichsdukatenfuss Phase I range [1600, 1726]. Resolution: either widen SH Phase I in `data/v2/locations/schleswig_holstein.yml::phases` (config), or extend the auto-classifier to handle the cross-rendering case automatically.
6. 429 numismaster `_unclassified.yml` (schleswig_holstein_duchy tag without mint) — entity classifier rule needs extension for «numismaster `schleswig_holstein_duchy` without mint → consult ruler-era heuristic → assign». Phase 3.1 rule update, not per-coin manual.

**Pending scripts (4-phase model completion):**
- **`scripts/maintenance/merge_seeds_cross_source.py`** (Phase 3.2) — reads `data/v2/seed/<src>/<entity>.yml` (per-resource seeds), applies confident-merge rules + reads `data/v2/merge_decisions/<entity>.yml` for explicit curator confirmations, writes `data/v2/seed_unified/<entity>.yml` (one entry per physical coin, multi-source enriched).
- **`scripts/maintenance/classify_to_fuss_v2.py`** (Phase 4) — reads `seed_unified/`, applies §8a Müntzfuß-disambiguation pipeline + reads `data/v2/classification_decisions/<entity>.yml`, writes `data/v2/final/<entity>.yml` (fuss-distributed). Also auto-detects cross-page-phase-mismatch cases and emits dict-form `phase` for affected coins.
- **`scripts/maintenance/diff_v1_v2_final.py`** — compares V1 curated (`data/locations/`) against V2 final (`data/v2/final/`), lists every divergence. Phase 9 promotion-gate: «diff is zero or fully explained».
- **`scripts/audit_v2.py`** (Phase 7, hard-block pre-commit per §7.4) — home-file rule, bidirectional link integrity, cross-entity duplicate detection, V1↔V2 reconciliation status.
- **Native V2 builders** (post-Phase 9) — replace `seed_v2_regroup.py` post-processor with proper V2 builders consuming parser cache directly.

**Migration of bootstrap state to new model:** the current `data/v2/curated/<entity>.yml` files (bootstrap-migrated from V1 curated) will be **replaced** by `data/v2/final/<entity>.yml` (regenerated from Phase 3.2 + Phase 4 scripts) once those scripts ship. Until then, `curated/` serves as «Phase 4 equivalent» for V1-migrated coins.

**Anything touching** `_merge_seeds_into_raw` / `_assemble_v2_location` /
`scripts/lib/v2_resolver.py` / `data/v2/curated/*.yml` /
`data/v2/locations/*.yml` / `data/v2/seed/` (when Phase 3 lands) needs
to keep V1 + V2 co-existence working until the explicit «фліпай V2».

## Quirks / known traps

* **ruamel.yaml round-trip on `denmark.yml`**: re-dumping the whole
  file via `yaml.dump(doc, file)` flattens the coin list indent from
  `  - id:` to `- id:` (loses 2-space). Use line-level surgery
  (regex / sed-style) for in-place edits instead. Caught and reverted
  during the 45-entry cleanup this session.
* **`scripts/cache/numista/*.json`**: cached entries reachable via
  pypdf-style local search; live API calls subject to user's
  per-session budget (per CLAUDE.md «Numista API budget» rule,
  May 2026 quota). The «cache → check first, ask before live
  fetch» pattern is enforced.
* **Push permission is per-turn**: «push» as a verb in any earlier
  turn does NOT carry to future turns. Always wait for an explicit
  per-turn push request.
