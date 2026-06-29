---
name: v2-audit
description: >-
  Read-only health review of the V2 entity-keyed coin pipeline. Use to check the
  state of merge-decisions, find over-merges (records fused on ruler+nominal+year
  with no shared catalogue index — the gottorp class), verify pipeline invariants,
  and confirm no citation/data loss — BEFORE shipping or when something looks off.
  Surfaces problems and routes each to its fix; it never edits data. Trigger
  phrases: "audit the pipeline", "check merge health", "find over-merges",
  "перевір пайплайн", "є over-merge десь?", "почисти/перевір merge-рішення",
  "health check". Remediation is the v2-merge-coins skill, not this one.
---

# v2-audit — V2 pipeline health review (read-only)

This skill RUNS checks and INTERPRETS them; it changes nothing. Every finding
routes to a fix (usually the **v2-merge-coins** skill). Run the whole suite for
a full review, or a single check when chasing one thing.

## The suite

Run from the repo root with the project venv (`.venv/bin/python`).

### 1. Merge-decision member resolution (orphans)
```
.venv/bin/python scripts/maintenance/validate_decisions.py --check-members
```
Every `merges`/`no_merges` member must resolve to a seed id OR a bare Hede code
the merger expands (`_expand_member_against`). A flagged member is a TRUE orphan
— a folded final / V1 id (`km-305-2-fr-iii-1669`) or a typo. **A bare Hede code
(`dk-hede-c4h112`) is NOT flagged** — it is the intended shorthand. Fix: the
v2-merge-coins orphan-heal (drop-if-redundant / fix-typo). Same check runs
ADVISORY in `.githooks/pre-commit`; promote it to a HARD BLOCK once it reads 0.

### 2. Over-merge scan (the gottorp class)
```
.venv/bin/python .claude/skills/v2-merge-coins/merge_helper.py scan <entity>
```
Flags seed_unified entries whose members carry catalogue indices but share NO
base in ANY catalogue (KM 33 + Lange 274b + KM 41 with nothing in common) —
i.e. merged on ruler+nominal+year alone. This is exactly the failure that fused
the gottorp John-Adolphus Thalers. Run per entity (danish_realm ≈ 68 candidates,
gottorp_duchy ≈ 4). **Expect false positives** — a legit no-index museum specimen
merged in, or a curator-approved cross-catalogue identity (KM 41 ≡ Lange 274b).
Judge each with `merge_helper.py graph` + §9.4; split real ones via v2-merge-coins.
To stop a vetted no-shared-index merge from re-flagging, record it as a force
`merges:` decision (a documented curator identity).

### 3. V2 structural invariants
```
.venv/bin/python scripts/audit_v2.py            # full (I1–I7); --quick for pre-commit subset
```
I2 = every `composed_of` resolves to a current seed_unified entry; I4 = every
final coin schema-validates; I6 = decision references resolve. Note the standing
baseline (I4/I6 are pre-existing debt) — your concern is whether a change made it
WORSE, so compare counts before/after, don't read the absolute number as new.

### 4. Citation / data preservation (§9a)
```
.venv/bin/python scripts/maintenance/audit_lost_citations.py     # 0 missing expected
```
A final entry must carry every source its composed_of members carry. Heal a
real loss with `--apply` (it unions). Also the hard-block on a staged final in
pre-commit (Check 6).

### 5. Project health dashboard
```
.venv/bin/python scripts/audit_health.py --fast        # build / counts / cache / TODO / git
.venv/bin/python scripts/audit_prose.py --staged       # §0a/§0z/§2a rendered-prose lint
.venv/bin/python scripts/audit_i18n.py                 # DE/EN/UK consistency
```

## Reading the results

Present a short consolidated verdict, not raw dumps. For each non-clean check:
name the finding, say whether it is NEW (regression) or standing debt, and route
it. Typical routing:

| finding | route |
|---|---|
| orphan merge-decision member | v2-merge-coins → orphan-heal (drop / fix) |
| over-merge candidate (real)   | v2-merge-coins → split |
| over-merge candidate (vetted) | record a force-`merges:` so it stops re-flagging |
| I2 dangling composed_of       | re-absorb the entity; investigate the dangling id |
| lost citation                 | `audit_lost_citations.py --apply` |
| I4 schema-invalid coin        | usually a pending unclassified coin missing year_label — note, don't mass-fix |

## Hard rules

- This skill is READ-ONLY. It never edits data or runs merger/absorber `--apply`.
  All remediation is a separate, deliberate step (v2-merge-coins or a targeted fix).
- An over-merge flag is a CANDIDATE, not a verdict — confirm with §9.4 (`graph`)
  + curator judgement before any split.
- Report regressions vs standing debt distinctly; never present the I4/I6 baseline
  as something this run introduced.
