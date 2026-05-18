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

**V2 entity-keyed refactor in flight (2026-05-18 session).** Phases 0,
1, 2, 3 (seed regrouper), 4, 5 landed; V2 renders to
`site/v2/<loc>/<lang>/` alongside V1. Phase 6 (bidirectional link),
Phase 7 (`audit_v2.py`) deferred to follow-up sessions. Phase 8 = user
review iteration (km-120 already addressed; 5+ open punch-list items);
Phase 9 = explicit «фліпай V2» promotion. Worktree branch
`feat/v2-pipeline` is the V2 working line. Detailed status in the
**«V2 pipeline refactor»** section near the bottom of this file. All
other workstreams below paused during V2 unless user redirects.

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

## V2 pipeline refactor — Phases 0–2 + 4 + 5 landed (2026-05-18)

The 2026-05-18 session executed the autonomous-portion of the V2
entity-keyed refactor. **V1 remains the live source of truth.** V2
files live in `data/v2/`, render to `site/v2/<loc>/<lang>/`, both build
in one `python scripts/build.py` invocation.

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

**Phases completed this session (8 commits on the worktree branch):**

| Phase | What |
|---|---|
| 0 | Skeleton `data/v2/{seed,curated,locations}/`, audit + V1-side fix for 3 coins missing `issuing_entity`, V2_PIPELINE.md decision-update |
| 1 | `scripts/maintenance/migrate_curated_to_v2.py` — 1317 V1 curated coins → 20 entity files. 11 list-form joint-mint, 1 dup-collision split (km-683-1 DK + SH), 3 joint-mint scalar candidates flagged |
| 2 | `scripts/maintenance/init_v2_locations.py` — 12 V2 location display-meta files with auto-derived `consumes_entities` |
| 5 | Schema: `Coin.issuing_entity: str | list[str]`, `Coin.phase: str | dict[str, str]`, `CatalogRefs.km: + dict[str, str]`, `Coin.composed_of` + `Coin.promoted_to`. New `scripts/lib/v2_resolver.py` |
| 4 | `scripts/build.py` `--v1-only` / `--v2-only` flags + `_assemble_v2_location()` two-pass (direct + inverse-index) + per-coin phase pre-filter. Timeline + template updated for list-form `issuing_entity` |
| km-120 fix | V1 mint correction (`Royal Mint (Tower Hill)` → `Altona` per Numista N#31895) + V2 regen → `_deprecated_gesamtstaat.yml` retired |
| 3 | `scripts/lib/v2_entity_classify.py` (mint → entity classifier) + `scripts/maintenance/seed_v2_regroup.py` (V1 seed yamls → V2 entity-keyed seed yamls). hede 884 + numismaster 1667 = 2551 seeds regrouped; bruun/galster/numista currently only have pre_1541 draft files which V1 doesn't load (and V2 skips). |

**Build results — V1 + V2 co-existence works (after Phase 3 seeds landed):**
- `site/<loc>/<lang>/`: V1 unchanged (DK 2502, SH 842)
- `site/v2/<loc>/<lang>/`: V2 curated + entity-keyed seeds (DK 2914, SH 485)
- Pre-filter drops 22 coins on V2 DK + 12 on V2 SH (cross-page-phase
  incompatibility — SH-page Phase II/III Helstaten coins rendering on DK;
  Haderslev 1591-1593 outside SH reichsdukatenfuss Phase I)

**Outstanding manual decisions for user in Phase 8 (V1 → V2 visual review):**
1. `km-120-chr-v-1787` (Christian VII 2-Sechsling, Tower Hill London mint)
   currently `_deprecated_gesamtstaat`. Probably should be `royal_holstein`
   (struck for SH circulation by outsourced contractor mint).
2. `km-683-1-fr-vi-1813` dup-collision — DK side carries Bruun-specimen
   1813 only; SH side is the consolidated 1813-1819 multi-mint type.
   §9a manual merge needed in `data/v2/curated/danish_realm.yml`.
3. 4 single-Kopenhagen Helstaten coins (`km-743 / km-770 / km-x001 / km-x002`)
   were on V1 SH page; in V2 they live in `danish_realm.yml` as scalar
   and only appear on DK. Consistency-pass: re-tag as
   `[danish_realm, royal_holstein]` if SH visibility desired.
4. 11 list-form Helstaten coins use SH-page Phase II/III (e.g.
   `phase: II` for 18_5_thaler). On V2 DK they're dropped because DK
   has Phase I only. To make them render on BOTH: convert their `phase`
   to dict-form `{denmark: I, schleswig_holstein: II}` per §5.
5. 7 scalar `royal_holstein` SH-V1 coins (`km-721-3-chr-viii-1842`,
   `km-733`, `km-734`, `km-735-2`, `km-737`, `km-760-2`, `km-761-1`):
   same Phase II/III on DK drop pattern; consider Phase 5 dict-form
   if DK rendering wanted.
6. 6 royal_holstein DK-V1 Haderslev coins (`hede-1`, `hede-3`, `hede-6`,
   `hede-7b`, `hede-8b`, `hede-156`) — 5 dropped on V2 SH because year
   1591-1593 falls outside SH reichsdukatenfuss Phase I range
   [1600, 1726]. Either widen SH Phase I year_from to 1591 (or 1559
   per German-lands anchor), or accept those don't show on SH.

**Phase 3 follow-ups (within Phase 8 user-review iteration):**
- `data/v2/seed/numismaster/_unclassified.yml` holds 429 numismaster
  coins tagged `schleswig_holstein_duchy` without mint. Per-coin review
  to decide which entity (gottorp_duchy default? royal_holstein? sub-
  duchy?) — or extend the mint classifier with year + ruler awareness.
- 347-coin SH visibility deficit vs V1: numismaster/schleswig_holstein
  seed coins whose explicit `issuing_entity` is `danish_realm` (V1 tag
  preserved) now render only on V2 DK, not V2 SH. Re-tag selectively
  to `[danish_realm, royal_holstein]` if SH visibility desired (per
  V2_PIPELINE.md §3.5 joint-jurisdiction).
- When bruun/galster/numista pre-1541 seeds get promoted to active V1
  set (after §AZ Galster + Jensen-Skjoldager catalog import), re-run
  `seed_v2_regroup.py --apply` to pick them up.

**Deferred phases (follow-up sessions):**
- **Phase 6** — `scripts/maintenance/relink_promoted_v2.py` derives
  `seed.promoted_to` from curated `composed_of` lists.
- **Phase 7** — `scripts/audit_v2.py` covering home-file rule,
  multi-entity validity, mint↔entity consistency, broken composed_of /
  promoted_to refs, cross-entity duplicate detection. Hard-blocks
  pre-commit per §7.4 user decision.

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
