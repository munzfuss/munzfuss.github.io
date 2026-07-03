---
name: fuss-description
description: >-
  Write, revise, and SCORE a Müntzfuß description (data/shared/fuesse.yml::<fuss>.description,
  de/en/uk) against a fixed 6-criterion rubric, returning X/10 so the work can loop until it
  clears a threshold (default 8+). Use when authoring a new fuss description, rewriting an
  existing one, or auditing whether a description meets the project's §7a (system-not-specimens),
  §0 (no invention), §5 (sourcing) and §0z (reader-voice) standards. The rubric checks: founding
  (how/why/by whom), role/function, per-phase distinguishing feature, no metric-fixation, every
  claim sourced, no specimen mentions. SCORING is a standalone READ-ONLY operation — a bare
  «оціни / score / rate» request returns just the X/10 + gap list and changes nothing; editing
  is a separate opt-in mode. Trigger phrases: "score the fuss description", "оціни опис стопи",
  "напиши/перепиши опис стопи", "покращ опис стопи до 8+", "describe this fuss", "rate the
  Müntzfuß description".
---

# fuss-description — author + score a Müntzfuß description

Executable form of CLAUDE.md **§7a** (Müntzfuß description scope — SYSTEM, not
specimens) + **§0 / §0b** (no invention, hypotheses labelled) + **§5 / §5b**
(source hierarchy, web-fact → refs_pool cite in the same change) + **§0z / §0a**
(reader voice). It governs ONE field: `data/shared/fuesse.yml::<fuss>.description`
(the `{de, en, uk}` prose block rendered under the Müntzfuß header). It does NOT
touch the Grundwerte card, phases, coins, or events.

The deliverable is a **score out of 10** against the six criteria below, plus a
concrete gap list, so a caller can loop `score → fix → re-score` until the
description clears the threshold. **Default ship threshold: 8.0** (tunable — the
project may raise it to 9 once descriptions routinely clear 8).

Helper (mechanical signal-scan, candidates not verdicts):
`python .claude/skills/fuss-description/describe_helper.py <fuss> [--lang de|en|uk] | --list`

## The six criteria (what a good description contains)

1. **Founding — how / why / by whom.** Which decree / ordinance / treaty /
   Reichsabschied / market forcing established the standard, under which ruler /
   authority, and the political-economic reason it came about. (§7a pillar 1.)
2. **Role / function.** What the standard was FOR — prestige tier, trade coin,
   daily Kurant, Scheidemünze, accounting unit, Bancovaluta — and its place
   relative to predecessor / parallel / successor standards (cross-reference via
   `[fuss:other_key]`). (§7a pillar 2 + 4.)
3. **Phases (only if the fuss has them).** Briefly, what KEY thing distinguishes
   each phase — the axis that makes them separate phases (a reform, a ruler
   change, a fineness step, a wartime re-issue, a jurisdiction shift). Name the
   differentiator per phase, not a specimen list.
4. **No metric-fixation.** The description must NOT dwell on weight / fineness /
   piece-count numbers that live (or will live) in the Grundwerte card. The ONLY
   metric allowed is a whole-standard defining value introduced by a NAMED law /
   decree (e.g. «72 Stück je Cölln. Marck rauh @ 18½ Karat per Wormser
   Reichsabschied 1495»). A bare «per Stück 3,248 g / 2,501 g fein» in the prose
   is a violation — that belongs in Grundwerte.
5. **Every statement sourced (§0).** Each non-trivial sentence carries a citation
   (inline `<sup>[ref:KEY]</sup>` → `data/shared/refs_pool.yml`, or a named
   source). Nothing invented — no unsourced motivation, intent, «first / only»,
   mintage. If a fact can't be sourced, state the gap («nach den vorliegenden
   Quellen nicht angegeben») — an honest gap beats a fabricated claim.
6. **No specimen mentions (§7a).** No individual coin — no Bruun lot, single-piece
   weight or grade, «sole surviving» / «unique» specimen, cabinet provenance, or
   one-issue mintmaster. Only the standard as a whole. **Catalogue index numbers
   written into the PROSE — «Hede f2h3», «Galster 131», «KM 138.2» — are also
   specimen/issue-level and do NOT belong in a fuss description.** The attestation
   travels via the `<sup>[ref:KEY]</sup>` citation (whose `refs_pool.yml` body MAY
   name the catalogue number as a locator, §5a); the prose names only the standard,
   the ruler, the period and the fineness step. A catalogue number in the description
   text is a C6 hit; the same number inside a `[ref:KEY]` body is a correct citation,
   not a hit. (Curator direction 2026-07-03 — this tightens §7a's older «catalogue
   TYPE numbers are allowed» reading, which applied to coin-row attestation, not to
   the system-level description prose.)

## Scoring rubric — 10 points

Score the **content** (the claims), which must be parallel across de/en/uk. Score
the richest language (usually de) and confirm en/uk carry the same claims +
citations (cross-language count drift is `audit_i18n`'s job, not this rubric).

| # | Criterion | Max | Award / deduct |
|---|---|---:|---|
| C1 | Founding (how/why/by whom) | 2.0 | 0.7 instrument named (decree/treaty/market forcing) · 0.7 ruler/authority named · 0.6 WHY (the forcing). Each part only counts if sourced. |
| C2 | Role / function | 2.0 | 1.0 monetary function stated · 1.0 placed vs ≥1 other standard (cross-ref). |
| C3 | Phase differentiators | 1.5 | If phases exist: 1.0 = each phase's key differentiator named · 0.5 = the differentiating axis is explicit. **If NO phases: award the full 1.5** (N/A, not a penalty). |
| C4 | No metric-fixation | 1.5 | Start 1.5; **−0.5** per weight/fineness/carat/piece number that is NOT a whole-standard, law-anchored defining value (i.e. duplicates Grundwerte). Floor 0. |
| C5 | Every claim sourced (§0) | 2.0 | Start 2.0; **−0.5** per load-bearing claim (founding fact, motivation, role claim, «first/only») with no citation. **Hard cap: any INVENTED claim** (unsourced motive/mintage/singularity) → C5 ≤ 1.0. Unresolved `[ref:KEY]` → −0.5 each. |
| C6 | No specimen mentions | 1.0 | Start 1.0; **−0.5** per specimen-level intrusion in the PROSE (auction lot, single-piece measure/grade, unique-specimen claim, one-issue mintmaster, provenance, **or a catalogue index number — «Hede f2h3», «Galster 131», «KM 138.2»**). A catalogue number inside a `[ref:KEY]` body is NOT a hit. Floor 0. |

**Threshold: ship at ≥ 8.0.** Below 8: the description has a real gap in founding,
role, sourcing, or scope — fix and re-score. A 10 means all six fully met with no
gap; 8-9 means substantively complete with only minor polish left.

## Workflow

**Two independent modes — pick by what the user asked, do NOT auto-chain them.**
- **SCORE** is the default for a rating request («оціни опис стопи», «score / rate the
  description», «яка оцінка опису X»). It is **strictly READ-ONLY — it reads and reports
  X/10 + the gap list, and changes NOTHING**. Stop after emitting the score; do not open
  an editor, do not «fix» anything, do not build. A bare score request ends at the score.
- **EDIT** runs ONLY when the user asks to write / revise / improve / raise the score
  («напиши / перепиши / покращ опис до 8+»). It internally SCOREs first, then edits.
- When unsure which the user wants, SCORE (read-only) and ask before editing.

**SCORE mode** — «оціни опис стопи X» (READ-ONLY, no edits, no build):
1. `describe_helper.py <fuss>` — read the mechanical signals (bare metrics,
   specimen flags, citation coverage, founding/role/phase presence, unresolved refs).
2. Read the actual `description.{de,en,uk}` in `fuesse.yml`.
3. **Verify sources (§0b) before scoring C5** — for each cited `[ref:KEY]`,
   confirm it resolves in `refs_pool.yml`; for each uncited load-bearing sentence,
   decide if it's genuinely unsourced. Do NOT award C5 on faith.
4. Apply the rubric → emit the score block (format below). Signals from the helper
   are candidates: a flagged bare metric that IS law-anchored keeps its C4 point; a
   catalogue number the helper finds only inside a `[ref:KEY]` body (never in the
   prose) is a citation, not a C6 hit — but a catalogue number in the prose text IS.

**EDIT mode** — «напиши/перепиши/покращ опис»:
1. SCORE first (get the baseline + gap list).
2. Fix each lost-point gap, lowest-hanging first:
   - Missing founding/role/phase content → ADD it, sourced. If you must look a
     fact up on the web, add the `refs_pool.yml` entry + inline `<sup>[ref:KEY]</sup>`
     in the SAME edit (§5b) — never defer the citation.
   - Bare metrics (C4) → cut them (they're in Grundwerte) unless you can anchor
     them to a named law and they define the whole standard.
   - Specimen intrusions (C6) → cut; the specimen belongs on its coin row.
   - Uncited claims (C5) → cite, or if unsourceable, rewrite as an honest gap /
     remove. **NEVER invent a source or a fact to raise the score** (§0) — that
     is the one move that fails the whole skill.
   - Keep the three languages in lock-step (same claims, same `[ref:KEY]` set).
3. `python scripts/build.py --location <a location that consumes this fuss>` +
   `scripts/audit_i18n.py` (0 inconsistencies) after edits.
4. **Re-score.** If < threshold, loop to step 2. Stop when ≥ threshold OR when the
   only remaining gap is an honest unsourceable fact (cap the score, explain, and
   surface to the user — do not invent to close it).

**LOOP** (the caller's `while score < 8`): SCORE → EDIT → build → re-SCORE. Each
pass must move ≥1 criterion up with real, sourced content — if a pass can't raise
the score without inventing, STOP and report the ceiling.

## Output format (emit this every SCORE)

```
FUSS: <key> — <name>
SCORE: 6.5 / 10   (threshold 8.0 → NOT YET / ✓ CLEARS)
  C1 Founding      1.4/2.0  — «why» (economic forcing) stated but unsourced
  C2 Role          2.0/2.0  ✓
  C3 Phases        1.0/1.5  — Phase II differentiator named, not sourced
  C4 No-metrics    1.0/1.5  — «3,248 g / 2,501 g fein» duplicates Grundwerte (−0.5)
  C5 Sourcing      1.0/2.0  — 2 uncited load-bearing claims: «…», «…»
  C6 No-specimens  0.5/1.0  — specimen intrusion «Bruun lot 4602» (−0.5)
GAPS (each → +points, do lowest-effort first):
  1. [C6] strip «Bruun lot 4602» — belongs on the coin row.            (+0.5)
  2. [C4] cut «3,248 g / 2,501 g fein» — Grundwerte owns it.           (+0.5)
  3. [C5/C1] source the «wartime financing» motive or cut it.          (+1.0)
CEILING NOTE: <only if a gap is genuinely unsourceable — name it>
```

## Hard rules

- **Never invent to raise the score (§0).** An unsourceable founding motive stays
  a labelled gap; a fabricated «to fund the war» that isn't in a source fails the
  skill even if it would score 10. The score measures sourced completeness, not
  prose that merely *sounds* complete.
- **Web fact → `refs_pool.yml` entry + inline `<sup>[ref:KEY]</sup>` in the same
  change (§5b).** A claim added without its citation is a §0 regression the next
  session can't distinguish from invention.
- **System-level only (§7a).** No specimens; no catalogue index numbers in the prose
  (they belong on the coin row — cite via `[ref:KEY]` instead); no weight/fineness
  numbers except a named-law whole-standard value; the description documents the
  STANDARD, the coin rows document the pieces.
- **Reader voice (§0z / §0a).** No «our card», «this artefact», «we classify»,
  «Phase B of our periodisation», project-meta, or `data/...yml` paths in the
  prose. A numismatist reading the page must understand every sentence with no
  knowledge that a project exists.
- **Three languages in lock-step.** Score the content once; the same claims and
  the same `[ref:KEY]` set must appear in de/en/uk. de uses period orthography
  (§2: Müntz, Thaler, biß, Cöllnische Marck); en/uk use modern orthography.
- **The helper flags candidates, not verdicts.** Verify every flagged metric /
  specimen / uncited claim against the actual text + sources before it moves the
  score.
```
