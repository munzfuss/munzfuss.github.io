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

## Current focus

**V2 entity-keyed refactor — architecture refined 2026-05-18 to
4-phase fully-automated pipeline with V1 reframed as VERIFICATION
ANCHOR (not bootstrap input).** Curator no longer edits coin fields
by hand; curator input is restricted to (a) which entities the project
supports, (b) Phase 3 merge confirmations, (c) Phase 4 classification
confirmations — all encoded in script rules or explicit decision
files. Worktree branch `feat/v2-pipeline` is the V2 working line.
Detailed plan: `docs/V2_PIPELINE.md`. Detailed architecture:
`docs/ARCHITECTURE.md` §«V2 entity-keyed pipeline». All other
workstreams below paused during V2 unless user redirects.

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
the 1541-1566 portion (christian_iii_dalerfod definition + fuss_periods
A1/A2 + seed-coin promotion c3h3-3A/3B + c3h4/5/7 + 4 new refs); the
pre-1541 portion (Christian II 1513-1523 + Frederik I 1523-1533)
becomes a fifth sub-task pending §AZ (Galster + Jensen-Skjoldager catalog import — new source family, not a Hede extension).

**Open §BF design question — Flensborg post-1544 track (Phase A3/A4)**:
separate `christian_iii_flensborg_fod` Müntzfuß for Lybsk-aligned
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

## Recent state changes (this session)

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

* **Main repo**: ~4 commits ahead of `origin/main` not pushed (user
  has not granted push permission this turn). Last push was earlier
  this session at commit `4d59131`. Newest commits cover case 8 +
  TODO §R, ref21 page hints + TODO §S, verified-wins rule + CLAUDE.md
  §4 update, 45-entry legacy cleanup.
* **Submodule `scripts/cache/`**: clean, no pending submodule
  commits.

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
| Phase 1 (bootstrap) | `migrate_curated_to_v2.py` — 1317 V1 curated coins → 20 entity files. Idempotent merge-aware via `lib/seed_merge.py` |
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
