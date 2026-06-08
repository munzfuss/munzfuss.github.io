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
- 🟡 **nominal discriminator — IMPLEMENTED + dry-run regression FAILED → REVERTED, synonym
  table needs more folds first.** Built `match_pair`: `_nominal_wildcard_match` (bare «daler»/
  «gylden» vs a specific compound of the same unit + quantity → not a genuine difference, so
  «1 Daler»/«Speciedaler» and «Guilder»/«Rhinsk Gylden» don't split) + the discriminator
  (nominal genuinely differs AND `not _shares_type_level_catalog` → no_match; weak Schou/Sieg
  tie doesn't carry it). Dry-run on danish_realm (vs a baseline with the same synonym table):
  **unified 7874→7899, +25 merges blocked, ALL on pairs with NO catalogue overlap.** Diffed
  the with/without composed_of partitions — **~half the splits are FALSE** (same coin, label
  variance the synonym table doesn't fold yet):
    • trailing «dansk»/«danske» default qualifier — «6 Skilling dansk» split from «6 Skilling»,
      same for «8 Skilling dansk», «2 Mark danske», «4 Skilling dansk», «12 Skilling dansk»
      (NB «lybsk»/«norsk» ARE distinguishing — only «dansk/danske» is the droppable default);
    • spelling typo «Rigsbankdaler» vs «Rigsbanksdaler»;
    • «½ Krone» vs «Halvkrone»; «Løvedaler» vs «Lion Daler/Taler» (DA vs EN);
    • value-gloss tail «1 Krone, 4 Mark» / «1 Sovereign, 3 Guilder» (the «, N <denom>» annotation
      splits it from the bare form).
  LEGIT splits in the same run: «¼ vs ½ Portugaløser», «1 vs 2 Dukat», «1 vs 2 Ungersk gylden»,
  «4 Mark vs Speciedaler». **Reverted the discriminator code (NOT committed, data restored).**
  **Next:** extend `nominal_synonyms.py` for the FALSE-split categories above (strip trailing
  «dansk/danske»; «halvkrone»→«1/2 krone»; «løvedaler»≡«lion daler/taler»; «rigsbanksdaler»→
  «rigsbankdaler»; strip a trailing «, N <denom>» value-gloss), re-run the with/without dry-run
  until the split list is ALL-legit, THEN ship the discriminator + full re-merge. The
  discriminator code is reconstructable from this entry (wildcard helper + type-level-catalog
  gate, mirroring the §9.4 mint discriminator at `merge_seeds_cross_source.py` ~L1735). NB:
  KM-42's anomalies don't NEED this (weight-tier-1 + the re-validate pass handle them).
- 🟢 **Full Numista re-parse to materialize §9a accumulation across all entities**
  (follow-up to the multi-KM fix above). The parser/merge/hygiene code is shipped, but
  only danish_realm + gottorp_duchy seeds were re-run. To materialize lange/dav/fr multi-
  ref accumulation for the other 14 entities (16 multi-ref types beyond the 5 KM ones),
  run the FULL pipeline deliberately: `parse_numista --force` → `build_numista_seed` →
  `merge_seeds_cross_source` (all) → `absorb_seeds_into_final_v2` (all), with a coin-count
  + diff regression check per entity. NB: re-merge may resolve more cross-source dups
  (richer catalog refs) — expect small final-count drops (de-dup, not loss; verify
  composed_of preserves the absorbed seed ids).
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
