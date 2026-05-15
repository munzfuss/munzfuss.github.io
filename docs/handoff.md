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
