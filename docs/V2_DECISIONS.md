# V2 Pipeline — Decisions Journal

> **Canonical record of every architectural decision made during the V2
> entity-keyed pipeline refactor.** Each item lists what was decided, why,
> when, and where it's encoded in code / data / docs. When changing or
> revisiting a decision, update HERE first and propagate references.
>
> `CLAUDE.md`, `docs/V2_PIPELINE.md`, `docs/ARCHITECTURE.md`, and
> `data/v2/README.md` REFERENCE this file for per-decision rationale. The
> journal is the authoritative log; supporting docs explain the
> implications.

## Table of contents

- [Pipeline shape](#pipeline-shape)
  - [D1 — 4-phase pipeline + render](#d1--4-phase-pipeline--render)
  - [D2 — Entity-keyed everywhere (Phase 3+)](#d2--entity-keyed-everywhere-phase-3)
  - [D3 — V1 as foundation, frozen post-bootstrap](#d3--v1-as-foundation-frozen-post-bootstrap)
  - [D4 — Curator never edits coin fields by hand](#d4--curator-never-edits-coin-fields-by-hand)
- [Schema](#schema)
  - [D5 — `issuing_entity: str | list[str]`](#d5--issuing_entity-str--liststr)
  - [D6 — `catalog.km: str | dict[str, str] | list[…]`](#d6--catalogkm-str--dictstr-str--list)
  - [D7 — `coin.phase: str | dict[str, str]`](#d7--coinphase-str--dictstr-str)
  - [D8 — Single-value catalog refs → `str | list[str]`](#d8--single-value-catalog-refs--str--liststr)
  - [D9 — `composed_of` + `promoted_to` bidirectional link](#d9--composed_of--promoted_to-bidirectional-link)
- [Matcher (Phase 3.2)](#matcher-phase-32)
  - [D10 — Match-strategy hierarchy](#d10--match-strategy-hierarchy)
  - [D11 — Unified id = `unified-<top-authority-member-id>`](#d11--unified-id--unified-top-authority-member-id)
  - [D12 — Authority order for source IDs](#d12--authority-order-for-source-ids)
  - [D13 — Entity → Krause-register mapping](#d13--entity--krause-register-mapping)
  - [D14 — Hede scope = `ruler` primary, `hede_volume` fallback](#d14--hede-scope--ruler-primary-hede_volume-fallback)
  - [D15 — Union-Find respects no_match transitivity](#d15--union-find-respects-no_match-transitivity)
- [Data preservation invariants](#data-preservation-invariants)
  - [D16 — Manual-override preservation](#d16--manual-override-preservation)
  - [D17 — Data-accumulation principle](#d17--data-accumulation-principle)
  - [D18 — Catalog ref accumulation = list-form on conflict](#d18--catalog-ref-accumulation--list-form-on-conflict)
  - [D19 — `year_ranges` UNION across members](#d19--year_ranges-union-across-members)
  - [D20 — Verification flags OR-merge](#d20--verification-flags-or-merge)
  - [D21 — Scalar gap-fill from authority order](#d21--scalar-gap-fill-from-authority-order)
- [Curator decision surfaces](#curator-decision-surfaces)
  - [D22 — Three decision files (committed)](#d22--three-decision-files-committed)
  - [D23 — `match_uncertainty/` (gitignored diagnostic)](#d23--match_uncertainty-gitignored-diagnostic)
  - [D24 — Three diagnostic channels in match_uncertainty](#d24--three-diagnostic-channels-in-match_uncertainty)
- [Workflow](#workflow)
  - [D25 — Idempotency invariant](#d25--idempotency-invariant)
  - [D26 — Phase 7 audit hard-blocks pre-commit](#d26--phase-7-audit-hard-blocks-pre-commit)
  - [D27 — Worktree branch = `feat/v2-pipeline`](#d27--worktree-branch--featv2-pipeline)
  - [D28 — Pre-1541 drafts flow through V2 normally](#d28--pre-1541-drafts-flow-through-v2-normally)
  - [D29 — Phase 4 «absorb» = match + accumulate; §8a auto-classify deferred](#d29--phase-4-absorb--match--accumulate-8a-auto-classify-deferred)
  - [D30 — Synthetic-bucket entities bypass merge_seed in regroup](#d30--synthetic-bucket-entities-bypass-merge_seed-in-regroup)
- [Deferred decisions](#deferred-decisions)

---

## Pipeline shape

### D1 — 4-phase pipeline + render

- **Decision (2026-05-18)**: V2 pipeline structure is 4 explicit phases plus render. The original 5-phase model (separate SEED + MERGED render layer) refactored into 4 phases after user clarification: cross-source merging belongs at Phase 3 (SEED → unified), fuss classification at Phase 4 (CURATED → final).
- **Phases**:
  1. **HARVEST** — `scripts/fetch_<src>.py` → `scripts/cache/<src>/*.{htm,pdf,json}` (raw)
  2. **SYNTHESIS** — `scripts/parse_<src>.py` → `scripts/cache/<src>/*.json` (typed)
  3. **SEED**
     - 3.1 per-resource: typed → `data/v2/seed/<source>/<entity>.yml`
     - 3.2 cross-source merge → `data/v2/seed_unified/<entity>.yml`
  4. **FINAL** — `data/v2/final/<entity>.yml` (absorbed into V1-foundation + new entries classified)
  - **Render** — `scripts/build.py` → `site/v2/<loc>/<lang>/`
- **Rationale**: Clean separation of «is this the same coin» (Phase 3.2) vs «which fuss» (Phase 4). Each phase has one driver script and one output type.
- **Encoded in**: [`docs/V2_PIPELINE.md`](V2_PIPELINE.md) §2, [`docs/ARCHITECTURE.md`](ARCHITECTURE.md) §«V2 entity-keyed pipeline».

### D2 — Entity-keyed everywhere (Phase 3+)

- **Decision (2026-05-17)**: From Phase 3 onwards, files are keyed by **political entity** (`issuing_entity`), NOT display location. Display pages declare `consumes_entities: [...]` and the build assembles per-page at render time.
- **Rationale**: One physical coin can render on multiple pages (e.g. Glückstadt 1622 8-Skilling → both DK realm and SH duchy pages). V1's location-keyed structure forced duplication or per-page hack patches. Entity-keyed solves cleanly: one canonical entry, N rendered surfaces via inverse-index assembly.
- **Encoded in**: V2_PIPELINE.md §1, build.py `_assemble_v2_location()`.

### D3 — V1 as foundation, frozen post-bootstrap

- **Decision (2026-05-18)**: V1 (`data/locations/<loc>.yml`, `data/seed/<src>/<loc>.yml`) is **frozen** after the 2026-05-18 bootstrap migration. It serves as the **foundation** that V2 final entries inherit (NOT just a verification anchor — V1's curated content IS V2's Phase 4 starting state). V2 pipeline adds enrichments via cross-source merge + new harvests; V1 entries' core fields (fuss/phase/kind) are NOT re-derived.
- **Rationale**: V1 accumulated years of §9a manual merges + fuss/phase assignments. Re-doing this from scratch would lose curatorial work. Treating V1 as «verified Phase 4 output» preserves that investment; V2 pipeline accumulates new data on top.
- **Encoded in**: V2_PIPELINE.md §8, ARCHITECTURE.md §«V1 as verification anchor», CLAUDE.md preamble.

### D4 — Curator never edits coin fields by hand

- **Decision (2026-05-18)**: Curator's role is restricted to **decisions**, not data edits. Three legitimate decision surfaces (see [D22](#d22--three-decision-files-committed)). All other content is script-derived.
- **Rationale**: Hand-editing coin fields breaks the idempotency invariant (D25) and creates data-divergence risk between V2 pipeline output and V2 curated state. Constraining curator to decisions keeps the pipeline pure-functional from raw data.
- **Preferred path**: encode curator intuitions as rules in scripts (`lib/v2_entity_classify.py`, `merge_seeds_cross_source.py`, etc.). Decision files are escape hatches for cases not yet practical to generalise.
- **Encoded in**: V2_PIPELINE.md §1, §9, CLAUDE.md preamble, data/v2/README.md.

---

## Schema

### D5 — `issuing_entity: str | list[str]`

- **Decision (2026-05-18, resolved §7a)**: `Coin.issuing_entity` accepts either a scalar string OR a list of strings. List form for joint-jurisdiction coins (e.g. Altona+Kopenhagen multi-mint Helstaten Speciedaler → `[danish_realm, royal_holstein]`).
- **Home-file rule**: when list-form, the coin lives in the **alphabetically-first** entity file. Build assembly's §3.10 inverse-index pass surfaces it on pages consuming any of the other listed entities.
- **Validator**: list must be non-empty, no duplicates, each tag must exist in `data/i18n/issuing_entities.yml`.
- **Encoded in**: [`scripts/lib/schema.py`](../scripts/lib/schema.py) `Coin.issuing_entity`, V2_PIPELINE.md §3.10.

### D6 — `catalog.km: str | dict[str, str] | list[…]`

- **Decision (2026-05-18, resolved §7.1)**: `CatalogRefs.km` accepts:
  - scalar `str` (bare, register inferred from entity context)
  - `dict[str, str]` (V2 explicit per-register namespacing, e.g. `{dk: '722', sh: '155'}` for cross-Krause-volume coins)
  - `list[str | KMRef]` (V1-legacy multi-KM list form)
- **Rationale**: KM registers restart per Krause volume (Denmark vs Schleswig-Holstein vs Norway). Dict form makes cross-volume identification explicit; bare form works when the entity's context is unambiguous. See D13.
- **Encoded in**: schema.py `CatalogRefs.km`, V2_PIPELINE.md §4, V2_PIPELINE.md §11.

### D7 — `coin.phase: str | dict[str, str]`

- **Decision (2026-05-18, resolved §7.2)**: `Coin.phase` accepts scalar OR per-location dict. Scalar = 90% case. Dict form (e.g. `{denmark: I, schleswig_holstein: II}`) when the same coin sits in different local periodisations across multi-consumer pages.
- **Resolver**: `scripts/lib/v2_resolver.resolve_phase_for_location(coin.phase, loc_id)`.
- **Encoded in**: schema.py `Coin.phase`, v2_resolver.py, V2_PIPELINE.md §5.

### D8 — Single-value catalog refs → `str | list[str]`

- **Decision (2026-05-18)**: Most single-value catalog refs in `CatalogRefs` are extended to `str | list[str]` so the cross-source merger can preserve multiple distinct values across members (D18). Per the data-accumulation principle (D17).
- **Promoted to list-form**: `lange`, `fr`, `dav`, `galster`, `galster_volume`, `jensen_skjoldager`, `schive`, `skaare`, `friedberg`, `davenport`, `mb`, `bruun_collection_id`, `bruun_lot`, `numista`.
- **Kept single-value (schema constraint)**: `bruun_part` (Literal), `bruun_lot_no` (int), `bruun_page` (int), `sieg_hede1971`, `schou_hede1971` (specimen-level hedeQUO1971 codes). Conflicts on these fields go to `merge_conflicts` diagnostic.
- **Encoded in**: schema.py `CatalogRefs`, CLAUDE.md «Data-accumulation principle».

### D9 — `composed_of` + `promoted_to` bidirectional link

- **Decision (2026-05-18, resolved §3.3)**: Every merge is recorded as a bidirectional link:
  - Host side (final / seed_unified): `composed_of: [member_id, …]`
  - Member side (seed): `promoted_to: <host_id>`
- Build assembly drops seeds with `promoted_to != None` from rendering (avoid duplicate alongside canonical host).
- **Derivation**: `scripts/maintenance/relink_promoted_v2.py` walks all `composed_of` lists and sets back-pointers. Idempotent.
- **Data-loss audit**: `relink_promoted_v2.py --audit` flags weight/fineness/source-URL values present in member seed but not in host (potential merge oversight).
- **CURATED_FIELDS membership**: both `composed_of` and `promoted_to` are in `lib/seed_merge.CURATED_FIELDS` so the bidirectional link survives every regen.
- **Encoded in**: schema.py `Coin.composed_of` + `Coin.promoted_to`, seed_merge.py, relink_promoted_v2.py, V2_PIPELINE.md §10 «Merge audit trail».

---

## Matcher (Phase 3.2)

### D10 — Match-strategy hierarchy

- **Decision (2026-05-18)**: Cross-source merger's match algorithm uses strict-primary + loose-fallback signal hierarchy.
- **Primary (all must NOT disagree; tri-state True/False/None per signal):**
  1. Metal — with billon/silver normalisation when fineness < 0.5
  2. Nominal — verbatim equality after period-spelling normalise (e.g. «Müntze» ↔ «Münze»)
  3. Catalog index chain — refs cross-checked with scope awareness (D13, D14); disagree → no_match; no_overlap → None
  4. Ruler — canonical-form equality
- **Fallback (supplemental):**
  5. Year-range overlap (≥1 year)
  6. Fineness within ±5 %
  7. Mint overlap
- **Decision matrix:**
  - Any primary False → no_match
  - primary_true == 4 AND fallback_false > 0 → low_confidence (curator surface)
  - fallback_false AND primary_true < 4 → no_match
  - primary_true ≥ 3 AND fallback_true ≥ 1 → **confident** (auto-merge)
  - primary_true ≥ 2 AND fallback_true ≥ 1 → low_confidence (curator surface)
  - else → no_match
- **Encoded in**: `scripts/maintenance/merge_seeds_cross_source.py::match_pair`, V2_PIPELINE.md §5.2.

### D11 — Unified id = `unified-<top-authority-member-id>`

- **Decision (2026-05-18)**: When N seed coins merge into a unified entry, the entry's id is `unified-<id-of-the-top-authority-member>`. Prefix `unified-` prevents collision with the seed-side id; the readable suffix keeps debugging easy.
- **Alternative considered**: deterministic hash `unified-<sha256_short>`. Rejected — harder to debug, no gain over authority-based for the few times the top-authority source genuinely disappears (rare).
- **Encoded in**: merge_seeds_cross_source.py `_unified_id_for_class`.

### D12 — Authority order for source IDs

- **Decision (2026-05-18)**: Source-id-prefix priority for unified id + scalar text gap-fill + catalog conflict resolution:
  1. `dk-hede-` — Hede 1971 (primary scholarly DK)
  2. `dk-bruun-` — Stack's Bowers Bruun auction
  3. `dk-numismaster-` — Krause-Mishler canonical
  4. `dk-numista-` — community Numista
  5. `dk-galster-` — Galster pre-1541
- **Rationale**: Hede 1971 is the canonical Danish scholarly catalogue; Bruun auction catalogues are well-edited primary sources; Krause is the canonical international catalogue; Numista is community-edited (lower authority for ambiguous cases); Galster fills the pre-1541 gap.
- **Encoded in**: merge_seeds_cross_source.py `_ID_AUTHORITY_ORDER` + `_authority_score`.

### D13 — Entity → Krause-register mapping

- **Decision (2026-05-18)**: Within one entity file, bare-form `catalog.km` is interpreted as the entity's natural Krause volume. The mapping:
  - `danish_realm` → `dk`
  - `danish_norway` → `no` (Krause has separate Norway volume)
  - `royal_holstein` / `gottorp_duchy` / `schauenburg_pinneberg` / `sonderburg_duchy` / `norburg_plon_duchy` / `glucksburg_duchy` / `rantzau_county` / `provisional_govt` / `holstein_schauenburg_county` → `sh` (Krause «German States — Schleswig-Holstein»)
  - `fuerstbisthum_luebeck` → `de-fbl`
  - `hanseatic_hamburg` → `de-hh`
  - `hanseatic_lubeck` → `de-hl`
  - `erzbisthum_bremen_verden` → `de-bv`
  - `herzogtum_braunschweig_lueneburg` → `de-bl`
  - `herzogtum_sachsen_lauenburg` → `de-sl`
  - `grafschaft_oldenburg` → `de-old`
  - `hochstift_osnabrueck` → `de-osnabr`
  - `landgrafschaft_hessen_kassel` → `de-hk`
  - `_unclassified`, `_deprecated_gesamtstaat` — no inference, bare KM stays bare
- **Rationale**: User reminder (2026-05-18): «KM різних локацій стартують з 1 (Ш-Г vs данія) — KM-DK#1 ≠ KM-SH#1». Entity-aware register inference prevents bare-KM clashes within one entity file when one source uses bare-form and another uses dict-form.
- **Encoded in**: merge_seeds_cross_source.py `_ENTITY_TO_KM_REGISTER`.

### D14 — Hede scope = `ruler` primary, `hede_volume` fallback

- **Decision (2026-05-18)**: Hede catalog refs scope-key derived from `coin.ruler` (normalised, lowercased) primarily; falls back to `catalog.hede_volume` URL code when ruler missing; falls back to bare `hede` only when both unavailable.
- **Rationale**: User reminder (2026-05-18): «Хеде клешить per ruler — Хеде#1 рулера_1 ≠ Хеде#1 рулера_2». Christian IV's Hede 156 (`c4h156`) ≠ Frederik III's Hede 156 (`f3h156`). Ruler is the authoritative scope signal; hede_volume code is its URL-friendly shorthand. Using ruler primary keeps the scope robust even when a source emits Hede ref without hede_volume.
- **Encoded in**: merge_seeds_cross_source.py `_catalog_refs`.

### D15 — Union-Find respects no_match transitivity

- **Decision (2026-05-18)**: When the matcher returns no_match for any pair, that pair is registered as a no_merge constraint in the union-find. Subsequent confident unions check every cross-class member pair against the no_merge set and refuse any union that would create a class containing a no_merge pair.
- **Rationale**: Without this, A↔B confident + A↔C confident + B↔C no_match would silently override B↔C's no_match via transitive union {A, B, C}. The matcher's explicit no_match is a strong constraint that must propagate.
- **Implementation**: Pre-pass registers all no_match pairs in union-find BEFORE attempting any union. Confident unions then attempt; `union(x, y)` checks every cross-class member pair before allowing the merge. Blocked unions surface in `match_uncertainty/<entity>.yml::transitivity_blocks`.
- **Encoded in**: merge_seeds_cross_source.py `UnionFind` + `process_entity`.

---

## Data preservation invariants

### D16 — Manual-override preservation

- **Decision (project-wide, pre-V2)**: Phase-transition scripts MUST preserve curator's manual edits across regenerations — never blindly overwrite. Mechanism: 4-mechanism merge in `lib/seed_merge.merge_seed`:
  1. `CURATED_FIELDS` allowlist (existing wins when present)
  2. `DEEP_MERGE_FIELDS` (dict deep-merge for catalog)
  3. `_VERIFIABLE_FIELDS` (verified-wins-over-unverified per §4)
  4. `_curation_holds: [...]` per-entry escape hatch
- **Encoded in**: lib/seed_merge.py, ARCHITECTURE.md §«Manual-override preservation», CLAUDE.md.

### D17 — Data-accumulation principle

- **Decision (2026-05-18)**: User-confirmed invariant: «має бути enrichment замість тихої втрати даних, ми не повинні втрачати дані, ми накопичуємо і групуємо, для показу фільтруємо, але в процесі нічого не повинно втратитись».
- **Rule**: Pipeline phases ACCUMULATE data; nothing is silently lost. Display layer FILTERS for presentation; data layer retains all variants. Scripts that silently overwrite when merging violate this invariant.
- **Resolution paths for data-loss cases**:
  1. Fix in code to accumulate (preferred — list-form, union, composed_of)
  2. Surface via `match_uncertainty/` for visibility
  3. Explicitly accepted by curator decision in `merge_decisions/` / `classification_decisions/`
- **Reference implementations**: D18, D19, D20, D21.
- **Encoded in**: CLAUDE.md «Data-accumulation principle» (top-level rule, paired with D16).

### D18 — Catalog ref accumulation = list-form on conflict

- **Decision (2026-05-18)**: When the cross-source merger encounters two members with different values for a catalog field that schema accepts as `str | list[str]` (D8), the output is list-form preserving all distinct values in authority order. KM is special-cased via `_merge_km_field` to preserve cross-register info (dict-form when ≥2 registers known).
- **Behavior**:
  - Single distinct value across members → bare-form (V1-compatible)
  - ≥2 distinct values → list-form, top-authority value FIRST
- **Encoded in**: merge_seeds_cross_source.py `_deep_merge_catalog` + `_merge_km_field`.

### D19 — `year_ranges` UNION across members

- **Decision (2026-05-18)**: `coin.year_ranges` from each member is unioned + de-overlapped + sorted.
- **Example**: Hede's `[[1591, 1593]]` + Numismaster's `[[1591,1591], [1592,1592], [1593,1593], [1595,1595]]` → `[[1591, 1593], [1595, 1595]]` (1591-1593 absorbs 1591/1592/1593 points; 1595 stands separate).
- `year_first` / `year_last` recomputed from the unioned envelope. `year_label` is top-auth wins (display string).
- **Encoded in**: merge_seeds_cross_source.py `_union_year_ranges`.

### D20 — Verification flags OR-merge

- **Decision (2026-05-18)**: Verification flags (`metal_verified`, `fineness_verified`, `weight_rough_verified`, `diameter_mm_verified`, `mint_verified`, top-level `verified`, `year_verified`) OR-merge across members. Any source's `True` attestation wins.
- **Rationale**: A source's verification confirmation should never be lost when a peer says `False`. Each source's attestation is independent; one positive confirmation suffices.
- **Encoded in**: merge_seeds_cross_source.py `_or_merge_verified`.

### D21 — Scalar gap-fill from authority order

- **Decision (2026-05-18)**: Scalar text fields (`fraction`, `nominal`, `ruler`, `mintmaster`, `inscription_obv`, `inscription_rev`, `metal`, `note`, `verification_note`, `issuing_entity`, `kind`, `fuss`, `phase`) gap-fill across members in authority order — the first non-None / non-empty value wins.
- **Conflicts** (≥2 distinct non-None values across members) are surfaced in `match_uncertainty/<entity>.yml::merge_conflicts` for visibility. Top-auth wins for the output value; alternative values logged.
- **Future work**: nominal-synonyms list for canonical name resolution (deferred — no V1 legacy list, build during Phase 8 consistency pass).
- **Encoded in**: merge_seeds_cross_source.py `_take_first_non_none` + `build_unified`.

---

## Curator decision surfaces

### D22 — Three decision files (committed)

- **Decision (2026-05-18)**: Curator input lives in exactly three places:
  1. **`data/i18n/issuing_entities.yml`** — which political entities the project supports (active entity set).
  2. **`data/v2/merge_decisions/<entity>.yml`** — Phase 3 cross-source merge confirmations:
     ```yaml
     merges:
       - members: [seed_a, seed_b]
         reason: "..."
     no_merges:
       - members: [seed_a, seed_b]
         reason: "..."
     ```
  3. **`data/v2/classification_decisions/<entity>.yml`** — Phase 4 fuss/phase assignments for ambiguous coins:
     ```yaml
     assignments:
       - coin_id: <unified-id-or-final-id>
         fuss: <fuss_id>
         phase: <phase_id>
         kind: <kurant|scheide|tarif|gedenk>
         reason: "..."
     ```
- **Preferred path always**: update script rules so the case becomes auto-handled. Decision files are escape hatches.
- **Encoded in**: V2_PIPELINE.md §5.2 (merge_decisions), §6 (classification_decisions), §9.

### D23 — `match_uncertainty/` (gitignored diagnostic)

- **Decision (2026-05-18)**: `data/v2/match_uncertainty/<entity>.yml` is **gitignored** and regenerated on every Phase 3.2 run. It surfaces low-confidence pairs + merge conflicts + transitivity blocks for INSPECTION, not curator input.
- **Distinction from D22**: decision files are committed + authoritative; match_uncertainty is regenerated diagnostic. Investigator reading match_uncertainty either:
  - adds an explicit decision to `merge_decisions/<entity>.yml`
  - OR extends the matcher rules in `merge_seeds_cross_source.py`
  - OR confirms the current state is correct (no action needed)
- **Encoded in**: `.gitignore` (`data/v2/match_uncertainty/`), merge_seeds_cross_source.py `_emit_match_uncertainty`.

### D24 — Three diagnostic channels in match_uncertainty

- **Decision (2026-05-18)**: `match_uncertainty/<entity>.yml` records three categories of «merger couldn't auto-route this without information loss»:
  1. **`low_confidence_pairs`** — pairs where matcher's primary signals < 3 (insufficient to confirm same physical coin). Resolution: add to merge_decisions OR extend matcher.
  2. **`merge_conflicts`** — successful merges where scalar fields disagreed across members (top-auth kept in output; alternative value logged here). Resolution: accept top-auth, OR fix the parser that emitted the wrong value, OR widen schema (D8 already covers most cases).
  3. **`transitivity_blocks`** — pairs the auto-rule called confident but were blocked because a no_match constraint exists elsewhere in the class (D15). Resolution: review whether the blocking no_match is correct or matcher false-failed.
- **Encoded in**: merge_seeds_cross_source.py `process_entity` + `_emit_match_uncertainty`.

---

## Workflow

### D25 — Idempotency invariant

- **Decision (2026-05-18)**: Every V2 phase-transition script is idempotent + merge-aware. Re-running on unchanged input produces ZERO file changes (verified via `git diff` + snapshot/diff -r). Scripts using merge_seed: `bootstrap_v2_final_from_v1.py`, `seed_v2_regroup.py`, `init_v2_locations.py`, `relink_promoted_v2.py`, `merge_seeds_cross_source.py`.
- **Mechanism**: `lib/seed_merge.merge_seed` (D16) + deterministic id ordering + sorted output + stable union-find roots.
- **Why this matters**: New harvest → parse → regroup → merge → absorb → relink → build chain runs automatically on any data change; curator edits at any phase are preserved.
- **Encoded in**: lib/seed_merge.py, every V2 maintenance script, ARCHITECTURE.md §«Idempotency invariant».

### D26 — Phase 7 audit hard-blocks pre-commit

- **Decision (2026-05-18, resolved §7.4)**: `scripts/audit_v2.py` (Phase 7, to-be-built) blocks `git commit` once added to pre-commit hook — NOT advisory (stricter than the originally-recommended advisory mode, per user direction).
- **Rationale**: V2 invariants (home-file rule, bidirectional link integrity, schema validation, cross-entity duplicate detection, V1↔V2 reconciliation status) must be checked at commit time so violations can't accumulate. Advisory mode would let invariants drift unnoticed.
- **Encoded in**: V2_PIPELINE.md §11.

### D27 — Worktree branch = `feat/v2-pipeline`

- **Decision (2026-05-18)**: V2 work lives on branch `feat/v2-pipeline`. The Claude worktree branch was renamed from `claude/sleepy-murdock-593353` → `feat/v2-pipeline` on 2026-05-18.
- **Rationale**: Aligns with the V2_PIPELINE.md plan's branch name; clearer to humans inspecting branches.
- **Encoded in**: git branch rename + handoff.md.

### D30 — Synthetic-bucket entities bypass merge_seed in regroup

- **Decision (2026-05-18, discovered during Step D audit landing)**: entity IDs starting with `_` (e.g. `_unclassified`, `_deprecated_gesamtstaat`) are SYNTHETIC BUCKETS for coins the mint-classifier couldn't route. They hold purely-uncurated escape-hatch data; merge_seed's CURATED_FIELDS preservation would WRONGLY preserve legacy seed-side tags (`schleswig_holstein_duchy`) on those entries instead of letting the regroup script replace them with the synthetic-bucket marker (`_unclassified`).
- **Implementation**: `seed_v2_regroup.py` checks `if entity_id.startswith("_")` → direct yaml write (no merge_seed). Coin lands in `_unclassified.yml` with `issuing_entity: "_unclassified"` (overriding any legacy V1 seed-side tag) — satisfies the home-file rule (D5) AND the entity-tag membership audit (I5 in audit_v2.py) which tolerates `_`-prefixed synthetic tags.
- **Encoded in**: `scripts/maintenance/seed_v2_regroup.py` (synthetic-bucket bypass branch).

### D29 — Phase 4 «absorb» = match + accumulate; §8a auto-classify deferred

- **Decision (2026-05-18)**: `absorb_seeds_into_final_v2.py` (Step B) implements two paths for unified seed entries:
  1. **Match** against existing final foundation → enrich (composed_of expansion + multi-source data accumulation per D17-D21). Foundation-immutable fields (D29-foundation list below) stay verbatim.
  2. **No match** → surface to `data/v2/classification_decisions/<entity>.yml::pending` for curator review.
- §8a Müntzfuß-disambiguation auto-classifier is **deferred** for the MVP. Curator either explicitly assigns (`assignments:`) or the matcher rules get extended so the coin absorbs into an existing final entry next run.
- **Foundation-immutable fields** (frozenset in absorb script): `fuss, phase, kind, fraction, nominal, ruler, mintmaster, issuing_entity`. Per DF1 these never change during absorb; if a curator wants Phase 4 to reclassify a V1-bootstrapped entry, that's explicit `classification_decisions/` action, not automatic.
- **Direct yaml write (not merge_seed)**: absorb writes the enriched coin list directly to `data/v2/final/<entity>.yml` because `merge_seed` treats empty `composed_of: []` on existing entries as «present» under CURATED_FIELDS preservation, which would block legitimate composed_of updates. Foundation preservation handled by `_FOUNDATION_IMMUTABLE_FIELDS` field-copy from existing entry; orphan curator data preserved by reading + enriching every existing entry (no entry dropped).
- **Encoded in**: `scripts/maintenance/absorb_seeds_into_final_v2.py`.

### D28 — Pre-1541 drafts flow through V2 normally

- **Decision (2026-05-18)**: V1's pre-1541 draft seed files (`data/seed/bruun/denmark_pre_1541.yml` + galster + numismaster + numista equivalents) flow into V2's Phase 3.1 seed yamls normally. V1's `_merge_seeds_into_raw` doesn't load them (location stem mismatch), but V2 does.
- **Rationale**: V2 covers ALL data, not just V1's active set. The pre-1541 drafts are valid harvested data; V2's sanitisation handles their non-canonical-schema fields (moves catalog-refs to nested `catalog:`, drops non-schema keys, coerces broken types like `bruun_part: 3 → 'III'`).
- **Encoded in**: `scripts/maintenance/seed_v2_regroup.py` (no V1-location filter); V2_PIPELINE.md §11 «Resolved decisions».

### D31 — «cf. X» refs don't belong in catalog index columns

- **Decision (2026-05-18)**: «cf. X» catalog references — both list-form (`catalog.others: ['KM-cf. 15', 'Lange-cf. 264a', 'KM-unlisted (cf. 136)']`) and scalar-form (`catalog.lange: 'cf. 445'`, `catalog.fr: 'cf. 3088'`) — are stripped from final yaml catalog fields. A «cf.» reference points at a similar OTHER coin, not at the entry's own catalogue index, so it doesn't belong in the catalog-column. Same rule extends to bare-`-unlisted` entries (`'KM-unlisted'`, `'Fr-unlisted'`, `'Lange-unlisted'`, `'Dav-unlisted'`, scalar `fr: 'unlisted'`, scalar `lange: 'unlisted'`) — «X-unlisted» is a negative claim («this coin is NOT in catalogue X»), equivalent to just not citing X, so it doesn't belong either.
- **Rationale (user, 2026-05-18)**: «KM-cf. 15 (silver) / Sieg-cf. 183.1 (silver) — такі cf посилання не потрібно писати в стовпці каталожних індексів, це ж індекс іншої схожої монети, не цієї, тому сюди воно не належить». Same logic from a follow-up: «Fr-unlisted – такі індекси не треба показувати, це те саме що не писати Fr індекс для цієї монети». The cf-relation, when historically load-bearing, lives in `note` prose framed as «closest-related reference is X (cf.)» — never as a positive index for THIS coin.
- **One-shot cleanup**: `scripts/oneoff/strip_cf_catalog_refs.py` — applied 2026-05-18 across V1 `data/locations/*.yml` (frozen but structural rule applies retroactively) and V2 `data/v2/final/*.yml`. ~100 strips total (cf-form + unlisted-form combined): 54 cf-form, ~44 unlisted-form. Three notes (gottorp km-189-karl-fr-1705 / km-203-karl-fr-1712 in both V1 and V2) had explanatory prose («Daher unsere catalog-Felder Lange "cf. 445"…») referencing the now-deleted fields; rewritten to keep the cf-relation as prose («Closest-related references are Lange 445 and Fr 3089 (cf.)») without referring to a catalog field.
- **Defensive filter**: `_deep_merge_catalog` in `merge_seeds_cross_source.py` (also used by `absorb_seeds_into_final_v2.py`) drops cf-form AND unlisted-form values at ingest time via `_SCALAR_CF_RE` + `_OTHERS_CF_RE`. Currently no seed carries these, but the filter prevents regression if a future Bruun-style harvester picks up Stack's-Bowers «Fr-cf. 3089» / Lange's «KM-unlisted» verbatim.
- **Encoded in**: `scripts/oneoff/strip_cf_catalog_refs.py` (one-shot cleanup); `scripts/maintenance/merge_seeds_cross_source.py::_deep_merge_catalog` (defensive filter); `CLAUDE.md` §«Anti-patterns to avoid» (after this decision lands, future sessions inherit the rule via the index entry below).

### D33 — Phase 3.2 matcher: reign-index ruler inference for cross-source pairs

- **Decision (2026-05-18)**: When `match_pair` evaluates the `ruler` primary signal and one or both coins lack a `ruler` field (the parser couldn't extract it — 533/859 = 62% of NumisMaster's Danish entries, similar gaps in other catalogs), the matcher falls back to looking up the coin's year(s) in an entity-scoped `{year → set(rulers)}` index built from members that DO carry attested rulers. The inferred value is adopted ONLY when every year the coin covers attests the SAME single ruler in the index — transition years (king-A dies + king-B crowned, e.g. 1648 / 1670 / 1808), separatist / co-regent windows, and parser-data anomalies (some source mislabelled a ruler for a specific year) end up with multi-element sets and the inference returns `None`. Per user direction 2026-05-18: «краще мати null і продовжити шукати правду ніж поставити неправдивий nonull value».
- **Two-pass index construction** (`_build_reign_index` in `merge_seeds_cross_source.py`):
  1. **Raw attestation pass** — each coin's `(year, normalised_ruler)` pair contributes to the index. Years where multiple distinct rulers are attested across the corpus get multi-element sets.
  2. **Contiguous-reign gap-fill pass** — for any gap year between min and max attested years, if the closest preceding AND closest following attested years both attest the SAME singleton ruler, fill the gap. Catches «1606 attests CHR IV, 1612 attests CHR IV → fill 1607-1611 with CHR IV» when no seed coin happens to be dated to in-between years. The bracket-pair check ensures fills never cross a reign transition or a multi-attest year.
- **Ruler normaliser hardening** (`_normalise_ruler`): strips trailing dots (`Christian IV.` → `christian iv`), drops `(reign-year)` parens, `, descriptive`-comma tails, `Issuer:` bleed-through from NumisMaster pages, `<year> - <year>` reign-tail residue, and `von/af/of/zu <house>` peerage suffixes before lowercasing + single-spacing. Without this, identical rulers fragment into 4+ Cyrillicised label variants per year and every year falsely registers as «multi-ruler».
- **Conflict-log normalisation**: `build_unified`'s scalar-conflict reporter (28 pre-D33 entries fell here) now compares ruler values via `_normalise_ruler` equivalence. Pure-punctuation variants («Frederik IV.» vs «Frederik IV») no longer pollute the conflict log — the merger still preserves the top-authority spelling verbatim in the output, only the diagnostic log is de-duped.
- **Stale `composed_of` purge in absorb script** (`absorb_seeds_into_final_v2.py`): when D33 unlocks a previously-blocked merger and consolidates two unified entries into one (`unified-denmark-numismaster-65046` + `unified-dk-hede-c4h134` → `unified-dk-hede-c4h134`), final entries whose `composed_of` referenced the disappeared `unified-*` id need that ref purged. The replacement id gets added by the normal match-pair pass; only the dangling reference is dropped. Without this purge, audit_v2 I2 «unknown composed_of id» fires after the first D33 run.
- **Effect on backlog (danish_realm)**: 383 low-confidence pairs → 20 residual (94.8% recovery). 0 confident merges → 136 confident merges. The 20 residual pairs are all coins whose year span touches a real-or-anomaly multi-ruler year (1648 / 1670 / 1606+1610 / etc.) — exactly the cases the user wanted to leave null. 0 fake-conflict noise in the merge_conflicts log.
- **Encoded in**: `scripts/maintenance/merge_seeds_cross_source.py` (`_build_reign_index`, `_infer_ruler`, `_normalise_ruler` extension, `match_pair` reign_index parameter, `process_entity` index construction, `build_unified` conflict-log normalisation); `scripts/maintenance/absorb_seeds_into_final_v2.py` (stale-purge + `stale_purged` stat). Future entities (royal_holstein, gottorp_duchy, schauenburg_pinneberg, etc.) get the benefit automatically — the index is rebuilt per-entity in `process_entity`.

### D38 — Per-source builders write canonical V2 entity tag via cache hints; classifier doesn't reach back to cache

- **Decision (2026-05-19)**: Entity classification from cache-derived hints (NumisMaster `country`, Bruun `region`, Numista `issuer`) lives at the **Phase 3.1a per-source builder layer**, NOT in the classifier (`lib/v2_entity_classify.py`). The builder reads cache (which it already does for every other field) and emits a canonical V2 `issuing_entity` tag directly in the V1 seed yaml. `seed_v2_regroup.py` then consumes the canonical tag through Tier-1 of `_normalise_entity_for_coin` («canonical V2 tag from V1 — preserve verbatim») — no cache-walk at the regroup layer.
- **Rationale**: linear pipeline principle. Phase N reads only Phase N-1's output. Having Phase 3.1b (regroup) reach back into Phase 2 cache breaks the layering and creates a hidden dependency. User direction 2026-05-19: «у нас же лінійний пайплайн, це має бути у того скрипта який такі ентіті з попередньої фази перетягує в наступну».
- **Refactor mechanic (NumisMaster, first real case)**: `build_numismaster_seed.py::COUNTRY_TO_ISSUING_ENTITY` was a 9-row table with the legacy `schleswig_holstein_duchy` catch-all on every SH cadet-line country, plus `norwegian_realm` (defunct alias). Rewritten to map each `country` value DIRECTLY to its canonical V2 entity:
  - `DENMARK` → `danish_realm`
  - `NORWAY` / `NORW AY` → `danish_norway`
  - `SWEDEN` → `danish_realm` (Christian II 1514-1523 only, Danish-rule scope)
  - `GLUCKSTADT` / `GLÜCKSTADT` → `royal_holstein` (Danish king's Holstein mint)
  - `SCHLESWIG-HOLSTEIN` (generic) → `royal_holstein`
  - `SCHLESWIG-HOLSTEIN-GOTTORP` / `HOLSTEIN-GOTTORP-RENDSBORG` → `gottorp_duchy`
  - `SCHLESWIG-HOLSTEIN-SONDERBURG` → `sonderburg_duchy`
  - `SCHLESWIG-HOLSTEIN-PLOEN` / `SCHLESWIG-HOLSTEIN-NORBURG` → `norburg_plon_duchy`
  - `SCHLESWIG-HOLSTEIN-GLUCKSBURG` → `glucksburg_duchy`
  - `SCHAUMBURG-PINNEBERG` → `schauenburg_pinneberg`
- Same fix applied to `build_numismaster_pre1541_seed.py` — pre-1541 SH-tagged entries route to `royal_holstein` (the SH cadet lines didn't exist yet — Christian III split happened 1544+).
- **Effect on backlog**: 426 `_unclassified` entries → **0**. Routing breakdown of the rerouted MCs (V2 seed/numismaster/):
  - `danish_realm: 805`, `danish_norway: 289`, `royal_holstein: 247`, `gottorp_duchy: 164`, `schauenburg_pinneberg: 99`, `sonderburg_duchy: 25`, `norburg_plon_duchy: 22`, `holstein_schauenburg_county: 16`, `glucksburg_duchy: 3`.
  - 27 entries that previously sat in `_unclassified.yml` (entity unknown → no foundation peer possible) found V1-foundation matches in their newly-correct entity files and auto-absorbed.
  - Remaining `_unclassified.yml` for ANY source: **0 files** (the file got fully consumed; regroup no longer generates one).
- **Wholesale rebuild was needed because `issuing_entity` lives in `CURATED_FIELDS`** in `lib/seed_merge.py` — the merge-preserves-existing rule would have kept old `schleswig_holstein_duchy` tags. `--no-merge` flag (auto-output rebuild path) wipes + writes fresh. For per-source NumisMaster builders this is safe: V1 NumisMaster seeds are AUTO-GENERATED, never curator-edited (curator edits flow into V2 final via `assignments` / `merge_decisions`).
- **Cache-fields available for future cache→entity inference at the builder layer (other sources)**: NumisMaster also has `political_period` (PL-codes — more granular than country) and `coinage_entity` (CG-codes — sub-categorisation). Bruun lots have `region` per lot (DENMARK / NORWAY / GERMANY / SCHLESWIG-HOLSTEIN). Numista API has `issuer.code` / `.name`; Numista HTML has `issuer_text`. Each is a candidate for the same builder-layer entity-tag pattern — apply when the per-source builder is touched next.
- **Encoded in**: `scripts/maintenance/build_numismaster_seed.py::COUNTRY_TO_ISSUING_ENTITY`; `scripts/maintenance/build_numismaster_pre1541_seed.py` (same logic, smaller scope). `seed_v2_regroup.py::_normalise_entity_for_coin` UNCHANGED — Tier-1 already preserved canonical V2 tags, the fix was upstream at the builder.

### D37 — Bulk-promote pending unified into final for empty-foundation entities

- **Decision (2026-05-19)**: When a V2 entity has NO V1 foundation at all — every unified entry is by definition «genuinely new» because there's nothing to potentially conflict with — the curator can assert this once via a top-level `bulk_promote_pending: true` flag in `data/v2/classification_decisions/<entity>.yml`. The absorb script then promotes ALL pending unified entries directly into the entity's `final/<entity>.yml` as initial foundation entries.
- **Motivation**: The default absorb path («match unified ↔ existing final via §5.2 hierarchy → enrich on match, route to pending on no-match») is correct when V1 foundation entries already cover the entity's scope. For freshly-created V2 entities (D35 Norge fix created `danish_norway` with zero V1 foundation; every unified entry lands in pending) the path produces a curator backlog of 100% of the unified entries — pointless friction. User direction 2026-05-19: «цих одразу можна запускати далі бо категорії не було і не повинно бути конфліктів».
- **Mechanic**:
  1. Curator sets `bulk_promote_pending: true` at the top of `classification_decisions/<entity>.yml`.
  2. `_bulk_promote_flag(entity_id)` reads the flag during `process_entity`.
  3. After the normal match-pass collects `unmatched_unified_ids`, the bulk-promote pass appends each as a new final entry with `composed_of: [<self-id>]` — self-promote marker that distinguishes V2-native foundation from V1-bootstrap-foundation (which has `composed_of: []`).
  4. Promoted entries go through `_enrich_final_entry(unified, [unified], entity_id)` so the on-disk field layout matches every other final entry's canonical shape — guarantees idempotency on re-runs (verified: `diff` after 2nd `--apply` run = 0).
  5. `unmatched_unified_ids` becomes `[]` after promotion; `classification_decisions/<entity>.yml` rewrites with empty `pending: []` and the flag preserved.
- **Fields the promoted entries carry**: everything the unified entry had — `nominal`, `ruler`, `year_first/_last/_ranges`, `metal`, `fineness`, `weight_rough_g`, `mint`, `mintmaster`, `catalog`, `sources`, `note`, `verified` flags. The classification-needing fields stay placeholders:
  - `fuss: seed_unsorted` (the sentinel for «no Müntzfuß assigned yet»)
  - `phase: <source-tag>` (`hede` / `numismaster` / `numista` / `bruun` / `galster` — derived from the seed authority)
  - `kind`: usually `kurant` (the seed builder's default; curator can refine)
- **Render behaviour**: coins with `fuss: seed_unsorted` skip soll/delta computation in the build (per `_compute_coin`); they don't render on any location page until a real `fuss` is assigned. The bulk-promote thus makes the entries «present in foundation, ready for classification» without polluting rendered output.
- **Path forward (deferred for these entries)**:
  - §8a auto-classifier (not yet built) will read the foundation, evaluate `fuss` candidates per metal + nominal + fineness + Δ-vs-Soll, and write `fuss/phase` in-place.
  - Or curator pins explicit values via `classification_decisions/<entity>.yml::assignments` per-coin entries.
  - Or the curator creates a display location (`data/v2/locations/norway.yml`) declaring `consumes_entities: [danish_norway]` so the entries surface on rendered pages once classified.
- **First real case (2026-05-19)**: `data/v2/classification_decisions/danish_norway.yml` set `bulk_promote_pending: true`; 438 unified entries promoted into `data/v2/final/danish_norway.yml` (439 total — the existing dk-tid-55898 from V1 stays unchanged). `pending: []` cleared. audit_v2 --quick: 0 violations.
- **Future enrichment correctness**: bulk-promoted entries become normal foundation. Future seed_unified passes' new unified entries match against them via the existing `match_pair` (`§5.2 hierarchy`) — `fuss/phase` fields are NOT in the matcher's primary or fallback signals, so placeholder values don't affect match correctness. New cross-source enrichments accumulate into existing bulk-promoted entries normally.
- **Encoded in**: `scripts/maintenance/absorb_seeds_into_final_v2.py` — `_bulk_promote_flag`, `process_entity` (bulk-promote pass after normal match-loop), `_emit_classification_decisions` (preserves the flag on rewrite). `data/v2/classification_decisions/danish_norway.yml` (first real curator entry).

### D39 — Bulk-promote `no_basic_peer_only` mode (D37 hardening)

- **Decision (2026-05-19)**: Extend D37's bulk-promote flag with a second mode that only promotes pending entries that have NO metal+nominal peer in the entity's existing foundation. Two accepted shapes:
  - `bulk_promote_pending: true` → mode «all» (original D37: promote every unmatched, used for empty-foundation entities)
  - `bulk_promote_pending: no_basic_peer_only` → mode «no_basic_peer_only» (D39: promote only the safely-«genuinely new» subset; D/E/H/C-category cases where a basic peer EXISTS stay in `pending` for curator review or matcher improvement)
- **Motivation**: After running cross-source merge for the 8 entities with non-empty V1 foundation (`danish_realm`, `royal_holstein`, `gottorp_duchy`, `schauenburg_pinneberg`, `sonderburg_duchy`, `norburg_plon_duchy`, `holstein_schauenburg_county`, `glucksburg_duchy`), the absorb pass surfaces 1746 unmatched unified entries. Splitting by category:
  - **N (no basic peer)** — 535 entries: nothing in foundation shares metal+nominal → genuinely new types → safe to bulk-promote.
  - **D / E / H / C (catalog disagree / ruler disagree / fallback disagree / low-conf-near)** — 583 entries: a metal+nominal peer EXISTS in foundation, but match_pair declined a confident match due to a fixable signal disagreement → silent promotion would create a duplicate.
  - Pure D37 mode «all» would conflate the two categories; D39 mode «no_basic_peer_only» splits them.
- **Mechanic**:
  1. `_bulk_promote_mode(entity_id)` returns `None` / `"all"` / `"no_basic_peer_only"` from the flag value.
  2. `_has_basic_peer(unified, finals, entity_id)` returns True iff any final entry shares the unified's metal AND nominal per `match_pair`'s primary signals.
  3. Bulk-promote loop in `process_entity` skips entries with a basic peer when mode is `"no_basic_peer_only"`; skipped entries stay in `unmatched` → routed to `pending` for curator review.
  4. Skipped entries remain visible in `data/v2/classification_decisions/<entity>.yml::pending` exactly as before — surfaces the matcher-improvement / curator-decision backlog without silently duplicating data.
- **Bug fixed alongside (writer round-trip)**: The `_emit_classification_decisions` writer originally collapsed the flag to literal `True` via `bool(existing.get("bulk_promote_pending"))`, which silently downgraded `no_basic_peer_only` → `true` (mode «all») on the first absorb run. After the fix, the writer preserves the original string value verbatim. Verified: 2nd `--apply` run is idempotent (`Bulk-promoted: 0`, `Newly absorbed: 0`, `Final entries after run` unchanged).
- **First real cases (2026-05-19)**: 8 entities flagged with `bulk_promote_pending: no_basic_peer_only`. 1st absorb run promoted **535** N-category entries into final; **583** D/E/H/C-category entries stay in `pending`. audit_v2 --quick: 0 violations. Per-entity breakdown — danish_realm: 0 promoted / 474 pending; royal_holstein: 265 / 55; gottorp_duchy: 135 / 25; schauenburg_pinneberg: 73 / 26; sonderburg_duchy: 22 / 3; norburg_plon_duchy: 21 / 0; holstein_schauenburg_county: 16 / 0; glucksburg_duchy: 3 / 0.
- **Path forward for the 583 pending**: matcher-rule improvements per category — D fixes a catalog-ref normalisation gap (e.g. KM with sub-variant suffix); E fixes a ruler inference (reign-index per D33); H surfaces a fallback-signal disagreement (e.g. weight class drift); C captures a near-confident match below the threshold. Each pending entry needs either (a) a matcher-rule fix that promotes it on next absorb, (b) a curator `assignments:` entry that classifies it explicitly, or (c) confirmation it IS genuinely new and the foundation peer is a different type (rare).
- **Encoded in**: `scripts/maintenance/absorb_seeds_into_final_v2.py` — `_bulk_promote_mode`, `_has_basic_peer`, `process_entity` (bulk-promote loop with mode branch), `_emit_classification_decisions` (writer preserves string value). 8 classification_decisions files carry the flag.

### D40 — Bulk-promote `no_match_primary_disagrees` mode (D39 extension)

- **Decision (2026-05-19)**: Add a fourth `bulk_promote_pending` mode that supersedes D39's «no_basic_peer_only» for entities whose pending backlog contains many «genuinely different sub-variant» cases that the matcher correctly declined to merge:

  - `bulk_promote_pending: no_match_primary_disagrees` → mode «no_match_primary_disagrees» (D40)

  Promotes a unified entry when EITHER (a) no basic peer (metal+nominal match) exists in foundation, OR (b) every basic peer's `match_pair` returned `decision: no_match` with at least one peer showing explicit primary-signal disagreement (`catalog: False` ≡ different KM/Hede/Sieg number → different sub-variant; `ruler: False` ≡ different reign attribution → different type). Keeps `low_confidence` decisions AND pure fallback-only disagreement cases in `pending` for curator review.

- **Motivation**: A 2026-05-19 categorisation pass of the 583 D39-leftover pending entries showed the dominant failure mode was D-category «catalog disagree» (459 = 78%) — entries with a basic peer but with EXPLICIT catalog refs that disagree. Concrete example: `unified-denmark-numismaster-117919` (NumisMaster MC for «16 Skilling 1625 KM-DK#107») vs foundation's `dk-tid-163039` («16 Skilling 1624-1625 KM-DK#92»). Same metal + same nominal + overlapping years — but DIFFERENT KM numbers. Krause-Mishler explicitly catalogues these as distinct sub-variants (different mint / mintmaster / die variant); merging them would conflate two real numismatic types into one. The matcher's «no_match: catalog disagree» response is correct — these aren't duplicates, they're new types that V2 should ingest as separate foundation entries.

- **Mechanic**:
  1. `_bulk_promote_mode` accepts a fourth string value `"no_match_primary_disagrees"`.
  2. `_all_basic_peers_no_match_primary(unified, finals, entity_id)` iterates basic peers and returns:
     - `None` — no basic peer at all (caller treats as D39's «no basic peer» case → promote)
     - `True` — every basic peer returned `decision: no_match` AND at least one had `primary["catalog"] is False` or `primary["ruler"] is False` (D + E category) → safe to promote
     - `False` — at least one peer returned `confident` / `low_confidence` (the C category, possible-duplicate), OR every peer's no_match was caused by fallback-only disagreement with primary all True/None (H category — suspicious, primary matches but year/weight diverged) → keep pending
  3. Bulk-promote loop branches on mode; D40 falls through to D39's promote path when peer-check is `True` or `None`.

- **Iterative convergence**: D40 is iterative — each absorb run promotes the «safely-different» cases, which become part of foundation; subsequent runs revisit remaining pending entries against the larger foundation. Some H-cases turn into D/E-cases when matched against the newly-promoted entries (different ruler now visible after multiple peers exist). 2026-05-19 first application: 1st run 490 promoted + 99 pending; 2nd run 59 more promoted + 40 pending; 3rd+ runs converged at 0 promoted / 40 pending. Total drain: **543 of 583 (93%)** across 5 entities. Stable convergence verified via 3 consecutive idempotent runs.

- **Why not just D37 mode «all»**: mode «all» would also promote H + C cases — including coins where the matcher said «primary signals match, fallback is suspicious» (H). Those are exactly the cases that MIGHT be duplicates (e.g. same coin with one source having sparser data). Keeping them in pending preserves curator visibility while D40 drains the «definitively different» 93% subset.

- **First real cases (2026-05-19)**: 9 entities flipped from `no_basic_peer_only` to `no_match_primary_disagrees`. Per-entity drain after convergence:
  - **danish_realm**: 386 promoted, 39 still pending (down from 474)
  - **royal_holstein**: 50 promoted, 1 still pending (down from 55)
  - **gottorp_duchy**: 25 promoted, 0 pending (fully drained from 25)
  - **schauenburg_pinneberg**: 26 promoted, 0 pending (fully drained from 26)
  - **sonderburg_duchy**: 3 promoted, 0 pending (fully drained from 3)
  - Others (norburg_plon_duchy / holstein_schauenburg_county / glucksburg_duchy / danish_norway): no change (D39 already fully drained on previous run)

  audit_v2 --quick: 0 violations. build --validate-only: clean.

- **Path forward for the remaining 40 pending**: H-category (primary True/None across all peers but fallback signals diverged) cases need either (a) a matcher rule that confidently UN-merges via stronger fallback weighting, OR (b) per-coin curator `assignments:` entries that classify them explicitly, OR (c) confirmation they're genuinely-new types with too-sparse data for the matcher to distinguish. Most of the 39 danish_realm leftovers fall in a recurring «Krone 16NN with year+fineness divergence vs Christian V 1691 Krone foundation» cluster — likely Christian IV / Frederik III era Krone variants whose NumisMaster ruler field is null. A targeted ruler-inference enhancement (extend D33 to NumisMaster entries via year→reign mapping when ruler is null and year is solidly in one reign) would unlock most of these.

- **Encoded in**: `scripts/maintenance/absorb_seeds_into_final_v2.py` — `_bulk_promote_mode` (4 modes), `_all_basic_peers_no_match_primary` (D40 peer-check helper), `process_entity` (bulk-promote loop branches). 9 classification_decisions files carry `bulk_promote_pending: no_match_primary_disagrees`.

### D41 — D33 ruler-inference extended to Phase 4 absorb

- **Decision (2026-05-19)**: D33 built the `{year → set(rulers)}` reign-index and ruler-inference machinery, but only the Phase 3.2 merger (`merge_seeds_cross_source.py::build_unified`) constructed + forwarded it to `match_pair`. Phase 4 absorb (`absorb_seeds_into_final_v2.py::process_entity`) called `match_pair` WITHOUT `reign_index`, so coins with `ruler: None` that the merger had inferred a ruler for were treated as ruler-unknown again at the absorb stage. D41 builds the same index in absorb and forwards it to every `match_pair` call (main match-pass loop + `_has_basic_peer` + `_all_basic_peers_no_match_primary`).

- **Motivation**: After D40 drained 543 of the 583 D/E pending entries, the 40 stable-pending residual contained two distinct shapes (categorisation pass 2026-05-19):
  - **6 cases** — NumisMaster MC entries with `ruler: null` whose year unambiguously maps to one reign. Example: `unified-denmark-numismaster-117920` («16 Skilling 1644, km=136.1»). The reign-index built from the corpus says `reign_index[1644] = {christian iv}` (singleton). With reign_index forwarded, `match_pair` infers ruler=Christian IV; suddenly the foundation peer `km-x033-chr-iv-1644-sixteen` (which has explicit `ruler: Christian IV.`) reaches `decision: confident` and gets absorbed. These 6 are the EASY unlock — pure inference plumbing, no semantic change.
  - **33 cases** — coins with ruler already attested but `low_confidence` decision on at least one peer (e.g. `unified-denmark-numismaster-41815` 10 Øre 1894-1905 Christian IX km=795.2 vs foundation km-795-2-chr-ix-1897 km=795.2: catalog matches, ruler matches, fineness matches, but `mint: False` — likely mint-normalisation gap «Kopenhagen» / «Copenhagen» / null). These need a different intervention (mint normaliser fix or per-coin curator `merges:` decision); D41 does NOT unlock them.

- **Mechanic**:
  1. Import `_build_reign_index` from `merge_seeds_cross_source` alongside the already-imported `match_pair`.
  2. In `process_entity`, build the index from BOTH `unified_entries` AND `final_entries` (both carry attested rulers — foundation has the V1-migrated ruler data, unified has cross-source-merged data). Single call: `reign_index = _build_reign_index(list(unified_entries) + list(final_entries), entity_id)`.
  3. `_has_basic_peer` and `_all_basic_peers_no_match_primary` signatures gain a `reign_index: dict | None = None` keyword parameter. Both forward to `match_pair(..., reign_index=reign_index)`.
  4. Three call sites in `process_entity` updated to pass `reign_index=reign_index`: the main match-pass loop (line 405), the D39 `_has_basic_peer` call (line 483), the D40 `_all_basic_peers_no_match_primary` call (line 494-495).

- **First real result (2026-05-19)**: 1st `--apply` run after D41 absorbed **6 newly-matched** entries (the forecast 6 in the categorisation pass). `Already absorbed (prev runs): 1373 → 2501` includes both the absorb cascade and the new D41 hits. Pending: **40 → 34** (-6 = 15% of the post-D40 residual). 2nd run idempotent (`Newly absorbed: 0`). audit_v2 --quick: 0 violations.

- **Path forward for the remaining 34**: 33 in danish_realm + 1 in royal_holstein. All are H-category (primary all True/None, fallback disagrees on mint or year-range) — typical pattern is «same KM#, same ruler, same fineness, but mint divergence». Likely paths: (a) `_normalise_mints` enhancement to handle Kopenhagen/Copenhagen/null gracefully; (b) per-coin curator `merge_decisions/<entity>.yml::merges` entries flagging «this NumisMaster MC = this foundation Hede coin». Tracked as a follow-up beyond §AZ Phase 4.

- **Encoded in**: `scripts/maintenance/absorb_seeds_into_final_v2.py` — import `_build_reign_index`, `process_entity` builds the index once, all three match-pair call sites forward it. The merger's reign-index implementation (`_build_reign_index`, `_infer_ruler`, normalisers) is REUSED VERBATIM from `merge_seeds_cross_source.py`; D41 is purely a plumbing extension, no algorithmic change.

### D42 — Mint spelling-alias normaliser (`_MINT_SPELLING_ALIASES`)

- **Decision (2026-05-19)**: Categorisation of the 34 D41-residual H-cases showed **27 of 33** (82%) were pure spelling-normalisation gaps — `Copenhagen` (NumisMaster English) vs `Kopenhagen` (project-canonical Danish/German), with 1 case of `Rendsborg` (Danish) vs `Rendsburg` (project-canonical German for SH towns). Same physical mint, different source-language label. `_normalise_mints` was lowercasing + stripping trailing parens but not handling cross-language aliases, so the set-intersection test failed and `match_pair` returned `low_confidence` (all 4 primary True, fallback fineness/years True, only `mint: False`). D42 adds a `_MINT_SPELLING_ALIASES` dict — sourcelanguage spelling → project canonical — applied inside `_normalise_mints` after the strip+lowercase step.

- **Mechanic**: Per-mint-town entry maps known cross-language variants to a single canonical lowercased form:

  ```python
  _MINT_SPELLING_ALIASES = {
      # Copenhagen — English / historical Danish / Latin
      "copenhagen": "kopenhagen",     # English (NumisMaster output)
      "københavn": "kopenhagen",      # modern Danish
      "kjøbenhavn": "kopenhagen",     # pre-1948 Danish spelling
      "hafnia": "kopenhagen",         # Latin (Christian IV legend variants)
      # Rendsburg — Danish vs project-canonical German
      "rendsborg": "rendsburg",
      # Helsingør — English / French aliases
      "elsinore": "helsingør",
      "elseneur": "helsingør",
  }
  ```

  Rule: keys lowercase; values lowercase. Match runs AFTER `.lower()` + paren-suffix strip in `_normalise_mints`. Add new variants ONLY when they refer to the SAME historical mint town — never collapse functionally-distinct mints into one canonical form.

- **First real result (2026-05-19)**: 1st re-merge after the alias fix consolidated 39 cross-source pairs at Phase 3.2 (unified count dropped: danish_realm 1412→1374, royal_holstein 355→354 — the alias-recovered mint signals upgraded 39 `low_confidence` merger pairs to `confident`). 1st absorb after re-merge: **3 newly absorbed**, **5 pending** (down from 34). Pending: danish_realm 5, royal_holstein 0 (fully drained).

  Aggregate post-alias drain across all 9 entities since the merger flag flip:
  - **Pre-D39**: 583 + 535 + (unclassified) = 1746 unmatched at first absorb
  - **Post-D39**: 535 promoted, 583 pending
  - **Post-D40**: 543 of those 583 drained, 40 pending
  - **Post-D41**: 6 of those 40 absorbed, 34 pending
  - **Post-D42**: 29 of those 34 absorbed (mostly via re-merger consolidation), **5 pending**

  Net 99.7% drain of the original pending backlog.

- **Path forward for the remaining 5**: Each has exactly ONE basic peer that returns `low_confidence` (the rest return `no_match` with explicit primary disagreement, which D40 would promote — but a single low-conf peer blocks the safe-promote check by design). The 5 cases are the «definitely-needs-human-judgment» residual:

  | Pending unified | KM | Issue |
  |---|---|---|
  | `numismaster-65367` | 525 (3 Krone 1726, FR IV) | Fineness divergence .993 vs .671 — one source has wrong metal class |
  | `numismaster-65899` | 499 (2 Ducat, FR IV) | Year divergence 1702 (NumisMaster) vs 1710 (foundation); same KM |
  | `dk-hede-c4h122` | 84 (8 Skilling CHR IV) | Mint divergence Frederiksborg (Hede) vs Kopenhagen (ucoin) — same KM |
  | `dk-hede-c4h97` | 41 (4 Skilling CHR IV) | Mint divergence Helsingør (Hede) vs Kopenhagen (ucoin) — same KM |
  | `dk-hede-c5h110` | 423 (8 Skilling CHR V 1693) | Fineness divergence (both Kopenhagen) |

  Resolution path is per-case curator action. For the 2 «same KM different mint» cases (c4h122, c4h97) the right answer is likely «merge with accumulated mint list per CLAUDE.md data-accumulation principle» — Hede has finer mint attribution than ucoin/Krause. For the 3 fineness/year divergences, the answer is «which source is correct?» — needs Wilcke 1950 or other authoritative reference. Phase 4 absorb has no per-coin override surface yet (analogous to Phase 3.2's `merge_decisions/<entity>.yml::merges`); deferred to a future `force_absorb` mechanic if the residual grows.

- **Encoded in**: `scripts/maintenance/merge_seeds_cross_source.py` — `_MINT_SPELLING_ALIASES` dict + `_normalise_mints` alias-lookup. Used by `_mints_overlap` (consumed by `match_pair` fallback signal). Phase 4 absorb consumes the fix transparently since it calls the same `match_pair` from the merger module.

### D36 — Curator merge decisions: smart override that doesn't block future enrichments

- **Decision (2026-05-18)**: When the auto-matcher cannot decide a pair (genuine numismatic ambiguity — e.g. NumisMaster's rolled-up multi-reign record vs Hede's per-reign split), the curator writes an explicit verdict in `data/v2/merge_decisions/<entity>.yml` with two surfaces:
  - `merges: [{members: [id_a, id_b], reason: ...}]` — force these into one unified class
  - `no_merges: [{members: [id_a, id_b], reason: ...}]` — forbid these from ever uniting
- **Smart-override mechanic (union-find semantics)**: both surfaces are loaded in the merger's pre-pass before any auto-rule fires. They land as union-find operations:
  - A `merges` entry calls `uf.union(a, b)` directly, creating an equivalence class. Crucially, the class is NOT closed — future auto-merge calls that confidently match ANY class member transitively pull the new coin in. If a Numista record next month auto-matches with `dk-hede-nc5h41` per the §5.2 hierarchy, it lands in the same class as `denmark-numismaster-110665` automatically — the curator's existing merge does not block legitimate enrichments.
  - A `no_merges` entry calls `uf.add_no_merge(a, b)` — registers a forbidden pair. The cross-class no_match check in `UnionFind.union` refuses any merge (direct or transitive) that would put both ids in the same class. Concretely: if I declared `no_merges: [nm-X, hede-Y]` and later a Numista entry auto-matches BOTH nm-X and hede-Y, the union-find blocks the second join, leaving nm-X and hede-Y in separate classes per curator intent.
- **Decision file is the durable record**: the file is checked into git and re-read on every Phase 3.2 run. The pipeline never «remembers» curator decisions out-of-band; they live in the file. Removing an entry removes the override.
- **First real case (2026-05-18)**: `data/v2/merge_decisions/danish_norway.yml` declares the verdict on the 2 ambiguous NumisMaster rollup cases the user reviewed:
  - **NM-110665 4 Mark ↔ nc5h41** = SAME coin (CHR V 1670-1674); **nf3h66** = SEPARATE (FR III 1669)
  - **NM-86229 8 Skilling ↔ nc6h2** = SAME coin (CHR VI 1730-1735); **nf4h17** = SEPARATE (FR IV 1727-1730); **nf4h16** = SEPARATE (FR IV 1727)

  Result: 2 forced merges applied + 3 no_merge constraints registered → `low_confidence_pairs: 0` for danish_norway. A side-effect of removing nf4h16 from contention: NM-86228 (a different NumisMaster MC#) auto-matched into the nf4h16 class confidently per the relaxed-threshold rules, picking up a new cross-source enrichment that the old «nf4h16 in unresolved low-conf cluster» state had been hiding.

- **Mental model for future curator entries**:
  1. Identify a coin pair the auto-matcher left as low_confidence or surfaced as ambiguous multi-candidate.
  2. Open both source URLs, confirm same-or-different physical type.
  3. Write the appropriate `merges` / `no_merges` entry with a reason that names the URLs, the catalog refs, and the numismatic rationale.
  4. Re-run `merge_seeds_cross_source.py --apply` → `absorb_seeds_into_final_v2.py --apply` → `relink_promoted_v2.py --apply`.
  5. Verify the unified entries reflect the curator intent and audit_v2 passes.

- **Pipeline-wide consequence**: the curator's authority surface is now fully expressed in two files per entity (`merge_decisions/<entity>.yml` + `classification_decisions/<entity>.yml` per D29). Coin-level fields stay script-derived per D24; only decisions on grouping + Müntzfuß-assignment need explicit curator input. Anything else should be a matcher-rule extension, not a per-entry override.
- **Encoded in**: `scripts/maintenance/merge_seeds_cross_source.py` — `_load_decisions` (already present from D22), `process_entity` (forced_merges / forced_no_merges application path). `data/v2/merge_decisions/danish_norway.yml` (first real curator entry).

### D35 — Norge misclassification fix + Frederick normaliser + strict DK-realm + weight-anchor

- **Decision (2026-05-18)**: Four further fixes to the Phase 3.2 matcher take the global low-confidence backlog from D34's 2 residual on danish_realm to **28 across 7 distinct null-side coins across danish_realm + danish_norway**. The new pairs surface because V2 seeds were rerouted from the Norge-misclassification fix below — they were always there, just hidden by the wrong-entity grouping.
- **Fix A — Norge misclassification override in `seed_v2_regroup.py`**: V1 seeds tagged ALL Hede danskmoent.dk entries (including the `nc*h`, `nf*h` Norge supplement) as `issuing_entity: danish_realm`. The V2 regrouper's Step-3 «preserve canonical V1 tag verbatim» rule kept those wrong tags. Added Step-3 «mint-authoritative override»: when V1's explicit issuing_entity is canonical AND the mint classifier returns a DIFFERENT canonical entity (e.g. mint=Christiania → `danish_norway`), the mint wins. 171 Hede Norge entries + 89 NumisMaster Norge entries + smaller counts from other sources properly routed to `danish_norway.yml` for the first time.
- **Fix B — «Frederick» → «Frederik» normalisation**: NumisMaster's Danish-realm pages render the Danish king's name as «Frederick» (English spelling with the `c`) rather than «Frederik» (Danish form). Without normalisation the reign index fragmented every transition year into duplicate ruler-attestation sets. `_normalise_ruler` extended to collapse `\bfrederick\b` → `frederik` after lowercasing — index multi-ruler-year count for danish_norway dropped from 76 → 7 after this single substitution.
- **Fix C — strict-DK-realm reign filter**: NumisMaster mis-labels Frederik VI as «Frederick IX» on 8 entries for years 1809-1810 (visual VI / IX confusion). Frederik IX reigned 1947-1972, never could have signed 1809 coins — pure parser bad data. `_build_reign_index` now drops attestations whose normalised ruler isn't in `_DK_RULER_REIGNS` when the entity is in `_DK_REALM_ENTITIES` (= `{danish_realm, danish_norway, royal_holstein}`, all under Danish monarchy). For non-DK entities (gottorp_duchy, schauenburg_pinneberg, etc.), the strict filter is OFF — their dukes have completely different reign timelines we don't yet table.
- **Fix D — weight-anchor tie-breaker for nominal disambiguation**: when the «single-candidate promote» post-pass would otherwise abstain due to MULTIPLE distinct attested nominals across candidates, check if the null-coin has a recorded weight AND exactly ONE candidate's weight matches within ±2 %. The weight signature is essentially the denomination signature in numismatics (1 Gulden ≈ 30 g, ½ Gulden ≈ 15 g — different orders of magnitude). One real case caught: `dk-galster-f1g-48` (1532 Frederik I silver, weight 45.58 g, nominal empty) had 5 Numista candidates with different Gulden subdenominations; only `dk-numista-476691` (1½ Gulden, weight 45.58 g) matched on weight → promoted.
- **Final cross-entity backlog (post-D35)**: 28 pairs across 7 distinct curator-decision coins. Breakdown:
  - **danish_realm (23 pairs, 5 coins)** — all are Galster Frederik I 1524 / 1532 entries with empty `nominal` (parser-gap on pre-modern Danish gulden entries in `parse_galster.py`). When parser is fixed to populate `nominal`, these auto-resolve via the existing post-pass rule. Until then, curator decision OR parser-cleanup.
  - **danish_norway (5 pairs, 2 coins)** — NumisMaster rolled-up multi-reign Norwegian coins: NM-110665 [1669-1680] 4 Mark spans the 1670 CHR V coronation, NM-86229 [1727-1735] 8 Skilling spans the 1730 CHR VI coronation. NumisMaster has ONE record per type covering both reigns; Hede correctly splits each into per-reign entries (`nf3h66` + `nc5h41`; `nf4h16` + `nf4h17` + `nc6h2`). Genuine numismatic curator decision: keep NumisMaster as a rollup record, or pick a primary Hede entry to merge with.
- **Encoded in**: `scripts/maintenance/seed_v2_regroup.py::_normalise_entity_for_coin` (Step-3 mint-override); `scripts/maintenance/merge_seeds_cross_source.py` — `_normalise_ruler` (Frederick fold), `_build_reign_index` (strict-DK + entity_id param), `_DK_REALM_ENTITIES` constant, post-pass weight-anchor in `process_entity`.

### D34 — D33 hardening: parser-anomaly filtering, transition-year inference, single-candidate promote

- **Decision (2026-05-18)**: D33's reign-index ruler inference is extended with three orthogonal hardening passes, taking the danish_realm low-confidence backlog from 383 (pre-D33) → 20 (D33-basic) → **2** (D34-hardened, both legitimate curator-decision cases per user direction).
- **Hardening A — Hede-volume-canonical attestation**: when building the reign index, an Hede seed's `ruler` field is OVERRIDDEN by the ruler derived from its `hede_volume` code (`c4h` → Christian IV, `f3h` → Frederik III, etc.). Real cases captured 2026-05-18 audit: `dk-hede-c9h1a` has `ruler: "Christian VIII."` but volume `c9h` = Christian IX; `dk-hede-f5h3ab` has year_first=1646 for a Frederik V volume (FR V reigned 1746-1766) — the volume code is parser-canonical, the ruler / year fields aren't. Reign-window filter drops `(year, ruler)` pairs whose year falls outside that ruler's reign — applies uniformly to Hede AND non-Hede sources, catching e.g. `denmark-numismaster-165534` attesting Frederik III for year 1633 (FR III reigned 1648-1670, 1633 attestation dropped). Source-of-truth: Wilcke 1950 / Hede 1957 Danish royal reign chronology (encoded as `_HEDE_VOLUME_TO_RULER` + `_DK_RULER_REIGNS` tables).
- **Hardening B — singleton-dominant inference for transition spans**: `_infer_ruler` was rewritten from «all years must be singleton, all agreeing on one ruler» to «≥1 singleton anchor + all singletons agree on one ruler R + every multi-ruler year's set must CONTAIN R». This allows a coin whose span includes a transition year (e.g. 1667-1670 with 1667-1669 attesting FR III alone and 1670 attesting both CHR V + FR III) to confidently infer FR III — the transition year's set is a superset of the singleton anchor. But still refuses inference for single-year-on-transition coins (e.g. a single-year-1648 coin has no singleton anchor → stays null) per user direction «краще null ніж неправдивий».
- **Hardening C — single-candidate cross-source promotion**: a post-pre-pass scans `low_confidence` pairs, identifies pairs where one side's `ruler` or `nominal` is null AND the other side attests a value, and checks the candidate set per (null_coin × field). When all attested values agree, promote ALL pairs for that coin to confident — the cross-source candidate has uniquely identified the missing attribute. When ≥2 distinct values attested (e.g. NM-65378 1648 1/4 Speciedaler with both `dk-hede-f3h47` FR III and `dk-hede-nc4h12` CHR IV as candidates — both physical types struck in calendar 1648 under different kings), the coin stays low_confidence for curator review.
- **Hardening D — overview-page filter**: `process_entity` drops Galster overview/index seeds (e.g. `dk-galster-f1galst` with nominal `«- oversigt efter Galster»` — a page-title bleed-through from `f1galst.htm`, not a real coin entry). The seed file itself stays untouched (parser-fix is a separate task); the matcher just skips overview entries so they don't generate spurious low-confidence pairs against real coins.
- **Final danish_realm backlog (post-D34)**: 2 pairs remaining, both = NM-65378 1648 1/4 Speciedaler vs its two equally-valid Hede candidates. This is the canonical «curator-decide» case the matcher correctly surfaces: NumisMaster has a single rolled-up record; Hede splits CHR IV's late issue (`nc4h12` 1629-1648) and FR III's early issue (`f3h47` 1648) as distinct types. The curator inspects the actual NumisMaster page and either picks one Hede entry to merge with via `merge_decisions/danish_realm.yml::merges`, or marks the pair as `no_merge` and leaves NM-65378 as a standalone «rollup» entry per project policy.
- **Encoded in**: `scripts/maintenance/merge_seeds_cross_source.py` — `_HEDE_VOLUME_TO_RULER` + `_DK_RULER_REIGNS` tables, `_hede_volume_to_ruler`, `_attestation_ruler` (volume-canonical override), `_build_reign_index` (reign-window filter), `_infer_ruler` (singleton-dominant rule), `process_entity` (overview-page filter + post-pre-pass single-candidate promote).

### D32 — Mintmaster initials live in `mintmaster` field, never in `mint`

- **Decision (2026-05-18)**: Parenthesised mintmaster initials embedded in the `mint` field (`mint: "Altona (FK VS)"`, `mint: [Altona (VS), Kopenhagen]`) are split — mint name stays in `mint`, initials move to the dedicated `mintmaster: str | None` field. The schema description was previously OK with the embedded shape («Each list entry may carry its own parenthetical mintmark / mintmaster annotation, e.g. ['Altona (VS)', 'Kopenhagen']») — overridden by user policy.
- **Rationale (user, 2026-05-18)**: «Altona (FK FF) – це в дужках мінт-мастер? таке не пишемо в "монетний двір"». Mint column should show the city; mintmaster has its own dedicated slot. Conflating the two pollutes the city-name and breaks any analytics keyed on bare mint (mint-count by city, cross-mint coin lookup, etc.).
- **Pattern recognised + extracted**: parens content of pure-alpha 1-3 «words» of 1-4 uppercase letters each (regex `^([^()]+?)\s*\(([A-Z][A-Z. ]{0,9})\)\s*$`) — matches `(FK VS)`, `(FK FF)`, `(FF)`, `(VS)`, `(HSK)`, `(IC)`. Parens containing digits (`(.1)`, `(.2, .3)`, `(683.1 M)`, `(683.2 IC)`) are NOT touched — those encode catalog sub-variant + mintmark mappings, a different mint-column issue still pending separate cleanup.
- **One-shot cleanup**: `scripts/oneoff/strip_mintmaster_from_mint.py` — applied 2026-05-18 across V1 + V2 final. 16 mint→mintmaster splits: km-733 / km-734 / km-737 / km-743 / km-761 / km-735 / km-726-2 / dk-tid-71072 (km-644). Multi-mint cases (mint=`[Altona (VS), Kopenhagen]`) keep all data — mint becomes bare list, mintmaster takes the single attested initials. No coin needed manual review (no multi-mint disagreements).
- **Schema update**: `scripts/lib/schema.py::Coin.mint` description rewritten to explicitly forbid the embedded-initials convention.
- **Encoded in**: `scripts/oneoff/strip_mintmaster_from_mint.py` (one-shot); `scripts/lib/schema.py` (schema docstring + Coin.mintmaster field already existed); `CLAUDE.md` §«Anti-patterns to avoid» entry (added with D31).

### D43 — Reader-facing nominal display normalisation (Danish-realm spelling + implicit «1 »)

- **Decision (2026-05-30)**: Two reader-facing nominal rules are now enforced on every rendered coin row — at seed-write time AND render time — plus a one-shot retro-fix over existing V2 data (361 nominal fields across 32 files):
  1. **Danish-realm spelling** — English «Noble» / «Rose Noble» / «Rosenoble» (Numista / NumisMaster / Friedberg) → Danish numismatic + project-canonical «Nobel» / «Rosenobel». Case- AND count-preserving: «2 Nobles» → «2 Nobel» (singular Danish noun after the count, per the nominal-field convention). Authority: Galster, danskmoent.dk/1nobel.htm + /1rosenobel.htm, our `nobel_fod` / `rosenobel_fod` Müntzfüße. Scope deliberately NARROW (noble family only) — we do NOT fold Thaler→Daler / Ducat→Dukat etc. for display (period-correct German/Danish forms stay per CLAUDE.md §2). Distinct from `nominal_synonyms.py`, which lowercases for cross-source MATCHING only.
  2. **Implicit «1 » count** — a bare denomination with no explicit count gets «1 » prepended («Noble» → «1 Nobel», «Doppelschilling» → «1 Doppelschilling», «Skilling Rigsmønt» → «1 Skilling Rigsmønt»). Per CLAUDE.md mathematically-verified register: every coin row carries an explicit count.
- **Rationale (user, 2026-05-30)**: «nobel чи noble – який варіант коректний для данії? … якщо номінал без числа це означає що до нього варто дописати одиничку … виправ всі наявні + онови скрипт щоб всі майбутні вже приходили правильними».
- **Guard-based, not allowlist**: the prepend rule was rewritten from the brittle exact-head allowlist (`_BARE_DENOMINATION_NOUNS`, removed) to a skip-list guard (`_should_prepend_one`), so qualifier-bearing + future denominations are handled by default. SKIP when: (1) explicit count already present — leading OR embedded digit / fraction glyph after paren-clarifiers like «(10 Ducats)» are stripped («Commemorative 2 Kroner», «Speciedaler / 3 Mark»); (2) leading roman-numeral count («IIII Skilling»); (3) leading fractional word («Halv ørtug», «Half Portugaloser»); (4) leading place/mint prefix («Oldenburg. Taler») or uncertain-mint «… eller …» leakage («Hamar (Norge) eller København, Søsling(?)»); (5) non-denomination placeholder («(?)», «Gold coin», «Medal»). Validated: 20/20 dangerous cases left untouched.
- **NARROW vs FULL normaliser**: `normalise_nominal_display()` (the two rules) runs at render + retro-fix; the FULL `_normalise_nominal()` (mojibake, year-strip, paren-translation-hint strip, fraction typography, abbrev-expand) runs only at seed-ingest on RAW source data. Keeping the retro-fix narrow avoided collaterally stripping meaningful paren-clarifiers — the full normaliser turns «4 Mark (Krone)» → «4 Mark» because «krone» sits in `_DENOMINATION_TRANSLATION_HINTS`, a latent pre-existing issue, out of scope here and NOT propagated to existing data.
- **Coverage**: source-citation `ref` text («Numista N#420401 — Noble - John I») and historical prose about the English Rose Noble (Edward IV 1465 model) are correctly NOT rewritten — neither is a nominal field, and «Rose Noble» is the correct English spelling for the historical coin there.
- **Encoded in**: `scripts/lib/v2_seed_writer.py` — `_NOMINAL_DISPLAY_SPELLING`, `_should_prepend_one`, `normalise_nominal_display` (public), spelling+guard wired into `_normalise_nominal`; `scripts/build.py` — render-time `normalise_nominal_display` call in V2 assembly; `scripts/oneoff/normalize_existing_nominals.py` — one-shot retro-fix (361 fields / 32 files).

### D44 — Absorb drops finals whose backing seed_unified has vanished (resolves DF1's additive-stickiness gap)

- **Decision (2026-06-10)**: Phase 4 absorb now DROPS a final entry when ALL hold: (a) it is pipeline-promoted (id form `unified-*`); (b) it has no live backing — neither its id nor any `composed_of` member resolves to a current `seed_unified` head/seed; (c) it carries no curation (`fuss` seed_unsorted/None, no `note`, no `_curation_holds`, no `promoted_to`, no curator-assigned phase — a bare seed-source phase tag like `kmk`/`bruun` is NOT curation). A V1-bootstrap foundation (real id) is the coin's OWN data and is NEVER dropped here; a curated entry whose backing vanished is KEPT (surfaced, not silently dropped).
- **Rationale**: absorb was additive/STICKY — when a `seed_unified` entry disappeared (its seed source deleted/filtered, or it was consolidated into another head by the merger), the corresponding final persisted. The existing "stale composed_of refs purged" step only trimmed dead REFS inside a surviving final; it never dropped a WHOLE unbacked final. That left 622 stale exonumia finals behind during the 2026-06-09 KMM-exonumia suppress (removed by hand) and, on first run of this fix, 17 more across the corpus (15 cross-source-consolidation duplicates + 2 sub-variant re-key dups). This is the §4/D-series "curated/verified wins" spirit applied to whole-entry lifecycle: never lose curator work to an automated pass, but don't keep uncurated pipeline residue whose source is gone. Narrows the DF1 immutability question — foundation classification is still immutable; this only removes uncurated `unified-*` rows with no source.
- **Two enforcement points (both feed the `stale_finals_dropped` stat)**: (1) an explicit filter on the freshly-built final set — catches stale finals that survive every other purge (the 622-exonumia shape); (2) a guard in the monotonic re-promotion pass that checks backing/curation directly on the prior-final entry — prevents resurrection of a final dropped by an EARLIER purge (stale-foundation / self-fold), which the explicit filter never sees. Backing is assessed AFTER enrichment refreshes `composed_of` via `new_links`, so a merely RE-KEYED unified (re-linked, present in the new final) never trips the guard.
- **Verification**: materialized 17 drops (commit `340219a`); 0 source-seed orphaned, 0 cross-entity duplicate, curator notes preserved. 19-case unit test.
- **Encoded in**: `scripts/maintenance/absorb_seeds_into_final_v2.py` — module-level `_SEED_TAG_PHASES`, `_final_is_curated`, `_final_has_live_backing`, `_is_vanished_stale_final`; the STALE-FINAL DROP block + monotonic-guard exclusion in `process_entity`; `stale_finals_dropped` stat. Test: `tests/test_absorb_stale_final_drop.py` (19 cases). Commits `78d54f2` (code+test), `340219a` (data −17).

### D45 — Schauenburg split into two regional entities; `holstein_schauenburg_county` umbrella retired

- **Decision (2026-06-10)**: The `holstein_schauenburg_county` umbrella (which conflated the Schauenburg dynasty's two geographic halves) is RETIRED and replaced by two entities, each carrying its own regional coinage tradition: **`grafschaft_schaumburg`** (Niedersachsen / Lower-Saxon ancestral county — mints Stadthagen/Bückeburg/Rinteln/Oldendorf, the 36-Mariengroschen-per-Reichsthaler tradition) and **`schauenburg_pinneberg`** (Holstein-Pinneberg — Altona, SH 9¼-Thaler-Fuß + the imperial 1/24-Thaler Gutegroschen). Display: the `holstein_schauenburg` location consumes BOTH entities (the full principality); the `schleswig_holstein` location consumes only `schauenburg_pinneberg` (the Holstein half) — exactly the multi-location-consume pattern already used for `royal_holstein` (on both the schleswig_holstein and denmark pages, the latter with a year window).
- **Rationale (user, 2026-06-10)**: «Гольштейн-Шаумбург дійсно поєднував дві частини: гольштейнську і нижньосаксонську, кожна з яких мала монетну традицію свого регіону … гольштейнська частина буде включена в фінальну сторінку шлезвіг-гольштейну (по аналогії як данські Ш-Г монети включені в сторінку данії), а окрема сторінка Гольштейн-Шаумбург включатиме обидві частини». The umbrella's name said "Holstein" but its definition covered both halves — a semantic mismatch that mis-presented the Niedersächsisch coinage as Schleswig-Holstein. Also fixed the concrete routing bug it caused (see below).
- **Routing is rule-driven, not manual**: `mint_registry.py` routes the 4 Niedersachsen mints → `grafschaft_schaumburg`, Altona/Pinneberg → `schauenburg_pinneberg`, and the Schauenburg issuer-name fallback → `schauenburg_pinneberg` (Holstein default); `entity_routing_rules.yml` rule `schauenburg_niedersaechsisch_denoms` `routes_to: grafschaft_schaumburg` for the Niedersächsisch denominations on mint-less pieces (1/24 Thaler stays placed by mint/issuer → pinneberg, per the 2026-05-29 §CE refinement). **`build_numismaster_seed` now applies `route_entity_with_rules`** (it previously routed only by mint/issuer, like a gap vs `build_numista_seed`) — this was the root of the 6-coin mis-route (2 Mariengroschen wrongly with the 4 imperial 1/24-Thaler). `build_bruun_denmark_seed` meta-tag `holstein-schauenburg` → `schauenburg_pinneberg`.
- **Migration**: the 123 `holstein_schauenburg_county` finals were moved VERBATIM (ids + curator notes preserved) to grafschaft (36) / pinneberg (88) by tradition+mint, then merge+absorb reconciled (composed_of already backs them → no dup re-promotion). Verified: 0 source-seed loss, 0 cross-entity duplicate, the km-135 «4 Mariengroschen = 1/9 Thaler» note survived; both pages render correctly (holstein_schauenburg 255 coins both parts; schleswig_holstein Niedersächsisch-absent). `test_entity_routing` updated (10 green). Git auto-detected the seed/seed_unified/classification renames county→grafschaft (70–94 % similar).
- **Encoded in**: `data/i18n/issuing_entities.yml` (+ `grafschaft_schaumburg`, − `holstein_schauenburg_county`); `scripts/lib/mint_registry.py` (4 NS mints + issuer-name fallback); `data/v2/entity_routing_rules.yml` (`routes_to`); `scripts/maintenance/build_numismaster_seed.py` (route_entity_with_rules wired in) + `build_bruun_denmark_seed.py` (meta-tag); `data/v2/locations/holstein_schauenburg.yml` (consumes both); `data/v2/{seed/*,seed_unified,final,classification_decisions}/grafschaft_schaumburg.yml` (new) + `…/holstein_schauenburg_county.yml` (deleted). Commit `997aa83`. **Follow-up open**: the `holstein_schauenburg` location's summary + phase prose still describe the pre-split bulk-seed model (see handoff 2026-06-10).

### D46 — Curator merge/split is a SKILL with a §9.4 over-merge gate + seed-id resolution; audits mirror the merger's `_expand_member`

- **Decision (2026-06-29)**: The curator merge/split flow is encoded as the **`v2-merge-coins`** skill (`.claude/skills/v2-merge-coins/`) and a read-only **`v2-audit`** skill, both version-controlled (`.gitignore` un-ignores `.claude/skills/`). Two guards are mandatory before any merge: (a) the **§9.4 over-merge gate** — `merge_helper.py graph` builds the catalogue index graph and STOPS a merge whose candidates share NO base index in ANY catalogue (i.e. fused on ruler+nominal+year alone); (b) **seed-id resolution** — `merge_helper.py resolve` maps any render/final/foundation id to the SEED id a `merge_decision` requires. A `merge_helper.py scan` proactively flags existing no-shared-base unified entries (the over-merge detector).
- **Rationale**: Two failures recurred and one shipped (caught + reverted same day) — a force-merge of three distinct gottorp John-Adolphus Thalers (KM 35/Lange 271 · KM 33/Dav 3688 · KM 41/Lange 274b) on ruler+nominal+year, and orphaned `merge_decision` members. Both are now structurally prevented, not relied on vigilance. The over-merge is exactly the §9.4 «distinct types unless one catalogue unifies» test, applied as a gate.
- **Audit/merger consistency rule**: a `merges`/`no_merges` member is a SEED id OR a **bare Hede code** that the merger's `_expand_member` (`merge_seeds_cross_source._expand_member_against`) expands to its sub-letter seeds (`dk-hede-c4h112` → `c4h112a`/`c4h112b`), grouping them so a `no_merges` never blocks the within-coin pair. **Every audit that checks member resolution MUST mirror `_expand_member_against`** — `validate_decisions.py --check-members`, `merge_helper.py audit`, and `audit_v2.py` I6 all do, so they never drift from the merger and never false-flag the intended bare-Hede shorthand. A bare Hede code is NEVER «re-pointed» to a flat sub-variant list (that would make a `no_merges` forbid the legitimate within-coin pair). I6 also resolves classification `coin_id`s against FINAL entry ids + `composed_of` members (how absorb applies them), not just seed/unified ids.
- **Encoded in**: `.claude/skills/v2-merge-coins/{SKILL.md,merge_helper.py}`, `.claude/skills/v2-audit/SKILL.md`, `.gitignore` (un-ignore `.claude/skills/`); `scripts/maintenance/validate_decisions.py` (`--check-members`, mirrors `_expand_member_against`); `scripts/audit_v2.py` (`_expands_to_seed` + final-id classification resolution); `.githooks/pre-commit` Check 5 (member-resolution HARD BLOCK since backlog = 0); CLAUDE.md «## Skills»; `docs/PLAYBOOKS.md` PB-1 pointer. Commits `b95cd4d` (skill), `1de7a4c` (audit-expansion fix + v2-audit + over-merge scan), `22d7ffc` (audit_v2 I6 + guard hard-block). The over-merge that triggered this: `85ac423` (wrong) → `03acfd5` (corrected to 3 coins).

### D47 — Removed the destructive `--no-merge` seed-builder flag (closed the last curation-safety bypass)

- **Decision (2026-07-15)**: Removed the `--no-merge` CLI flag + the `no_merge` parameter from all 8 V2 seed builders (`build_{hede_denmark,numista,numismaster,ucoin,kmk,ikmk,bruun_denmark,galster_denmark}_seed.py`) and from `lib.v2_seed_writer.write_v2_seed`. Every builder now UNCONDITIONALLY routes through `lib.seed_merge.merge_seed`, so curation preservation (`CURATED_FIELDS` + `DEEP_MERGE_FIELDS` + `_VERIFIABLE_FIELDS` verified-wins + `_curation_holds` + `_source_errata` via `apply_source_errata` + orphan-curated retention) can no longer be bypassed. No path wholesale-overwrites a seed any more.
- **Rationale**: `--no-merge` was the SINGLE bypass of the project's otherwise-uniform «never silently lose curation» invariant (HARD-BLOCKed everywhere else — `audit_lost_citations` pre-commit, I2 invariants, the manual-override-preservation rule). Under it the writer skipped BOTH the pre-process cross-entity purge AND `merge_seed`, writing fresh parser output wholesale → silently dropping `_curation_holds`, `_source_errata`, curated field overrides, and orphan-curated entries (types the parser no longer emits) for the ENTIRE entity, which then flowed through merger → absorb → build before anyone could notice. Low-probability (explicit opt-in) × catastrophic blast-radius (a whole entity's curation) × silent = textbook safety-rail profile. It was literally in the hede docstring's `Run:` examples (`--no-merge  # wholesale`), inviting copy-paste. Its documented legitimate uses are covered without it: verification = `--dry-run` (non-destructive, already exists); a genuine fresh rebuild = `rm -rf data/v2/seed/<src>/` then the normal builder (explicit, not a one-token footgun). Surfaced while analysing whether a `_source_errata` on a `seed_unsorted` hede coin survives downstream (it does — `apply_source_errata` runs LAST in `merge_seed`, `_source_errata` ∈ `_PRESERVE_ALWAYS_KEYS`, and merger+absorb regenerate `year_label`/`year_last`/`year_ranges` from the corrected `year_first`); the one residual hole was exactly `--no-merge`.
- **Distinct from `no_merges`**: the removed flag is unrelated to the `no_merges` curator decision pairs (`merge_decisions/<entity>.yml`) and the union-find `add_no_merge` / `explicit_no_merge` constraints — those are a different concept (negative merge authority) and are untouched.
- **Verification**: `py_compile` all touched files; full 547-test `unittest` suite OK; kmk + ucoin dry-run smoke (new `build_seed` signatures resolve, `merge_seed` path active); grep confirms 0 remaining `no_merge`-flag refs in builders/writer.
- **Encoded in**: `scripts/lib/v2_seed_writer.py` (param + docstring + the 3 `and not no_merge` conditionals removed), `scripts/lib/seed_merge.py` (docstring usage example updated), the 8 builders (argparse + call-site + `build_seed` signature). Supersedes the `--no-merge` mechanism named in earlier journal/TODO history (D-journal «wholesale rebuild» note above + the §BL closed-work record) — those describe a past state; the flag no longer exists.

---

## Deferred decisions

These items are recognised but intentionally left open until the relevant phase exposes the question concretely.

### DF1 — Foundation immutability (Phase 4)

- **Question**: Can Phase 4 «absorb» change `fuss` / `phase` / `kind` on a V1-foundation-inherited entry when new seed data suggests a different classification (§8a re-runs with more specimen Δ data)?
- **Current default**: foundation immutable — V1 author's classification wins, new data goes into multi-source weight/fineness lists but doesn't change the canonical fuss/phase.
- **Status**: open until Step B (`absorb_seeds_into_final_v2.py`) lands and we see how often it would fire.

### DF2 — Bootstrap script retirement timing

- **Question**: When does `bootstrap_v2_final_from_v1.py` retire? Post-Phase-9 (V1 archives, script unused) or earlier?
- **Current**: script remains idempotent + merge-aware, runs safely whenever invoked. Practically untouched after the 2026-05-18 initial run since V1 is frozen.
- **Status**: open. Probably auto-resolves at Phase 9 (script moves to `_archive_v1/maintenance/`).

### DF3 — Nominal synonyms list

- **Question**: Build a machine-readable list of nominal synonyms (e.g. «1 Speciedaler» ↔ «1 Speciesthaler») so the merger can canonicalise during merge instead of surfacing as conflict?
- **Search 2026-05-18**: No V1 legacy synonyms list found. Mentions exist in docs (free-form, not machine-readable).
- **Status**: deferred to Phase 8 consistency pass. Current behaviour (top-auth wins, conflict logged to `merge_conflicts`) is acceptable since synonyms don't cause data loss (only display preference).

### DF4 — Numista list-form vs explicit merge declaration

- **Resolved 2026-05-18 (see D8 / D18)**: schema extended to `str | list[str]` for `numista`. Cross-source merger accumulates distinct N#s into list-form when curator force-merges via `merge_decisions/`. Auto-matcher rejects same-N# disagreement (different N# = different physical coin until proven otherwise).
- Originally was deferred — now closed.

---

## Maintenance

- Add new decisions to the appropriate section (Pipeline shape / Schema / Matcher / Data preservation / Curator surfaces / Workflow).
- Use the next free `D<N>` number; never renumber existing entries (cross-references in code + commits would break).
- Use `DF<N>` for deferred decisions; promote to `D<N>` when resolved.
- Each entry includes: **Decision** (one-line summary + date), **Rationale**, **Encoded in** (paths to code/data/docs).
- When updating an existing decision, append a «Revised <date>:» note rather than rewriting.

The journal is plain Markdown — no machine-readable schema. Pre-commit prose lint applies normally; no special audit.
