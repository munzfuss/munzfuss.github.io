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
