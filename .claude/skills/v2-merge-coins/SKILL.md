---
name: v2-merge-coins
description: >-
  Merge or split coins in the V2 entity-keyed pipeline via merge_decisions —
  safely. Use whenever the curator decides that two-or-more coin records are
  the same coin (merge) or that an existing merged entry bundles distinct coins
  (split/un-merge). Encodes the §9.4 over-merge gate and the seed-id resolution
  step that prevent the two recurring failures: (a) over-merging records that
  share only ruler+nominal+year with no common catalogue index, and (b)
  leaving orphaned (non-resolving) members in merge_decisions. Trigger phrases:
  "merge these coins", "split this over-merge", "роби мердж", "це over-merge",
  "почисти orphan-и в merge-рішеннях".
---

# v2-merge-coins — safe merge / split in the V2 pipeline

Executable form of `docs/PLAYBOOKS.md` PB-1. The merger
(`merge_seeds_cross_source.py`) is an auto-matcher; this skill governs the
**curator override** layer (`data/v2/merge_decisions/<entity>.yml` →
`merges:` / `no_merges:`). Read CLAUDE.md §9.4 (sub-indices = one coin; the
index-graph rule) and §9a (multi-specimen preservation) first — they are the
law this skill enforces.

Helper: `python .claude/skills/v2-merge-coins/merge_helper.py {resolve|graph|audit} …`

## The two failure modes this skill exists to stop

1. **Over-merge by ruler+nominal+year.** Two records share metal + nominal +
   ruler + a close year but have NO overlapping catalogue index (one carries
   KM 33 / Dav 3688, the other Lange 274b — nothing to disagree on). The
   auto-matcher fuses them; a curator force-merge fuses more. They are
   *different coins*. (Real: gottorp John Adolphus Thaler KM 33 / KM 41 /
   Lange 274b fused into KM 35 — caught + reverted 2026-06-29.)
2. **Orphaned members.** A `merges:`/`no_merges:` member that resolves to NO
   seed — a folded final / V1 id (`km-305-2-fr-iii-1669`) or a typo. The merger
   silently skips it; the audit flags it.
   **NOT an orphan — a bare Hede code (`dk-hede-c4h112`).** The merger's
   `_expand_member` deliberately expands a bare Hede id to its sub-letter seeds
   (`c4h112a`/`c4h112b`) and treats them as ONE group, so the curator can decide
   at the «whole Hede 112» level. The audit mirrors this (`_expand_member_against`)
   and does NOT flag it. NEVER re-point a bare Hede code to a flat sub-variant
   list in a `no_merges` block — `[c4h112a, c4h112b, c4h116a]` would make the
   block forbid the legitimate within-coin pair c4h112a–c4h112b.

## MERGE — procedure

**Step 0 — resolve every input to SEED ids.** The curator/user names coins by
whatever id they see (render id, KM#, Hede#, a final-page id). merge_decisions
reference **seed** ids only (`data/v2/seed/<src>/<entity>.yml`). Run:

```
python .claude/skills/v2-merge-coins/merge_helper.py resolve <entity> <id> [<id> …]
```

- `✓ … -> [seed ids]` → use those seed ids.
- `⚠ … UNRESOLVED` → the id is a folded former-final or a typo. Do NOT put it in
  the decision. Find the real seed (try the KM/Hede via `graph`, or grep
  `data/v2/seed/*/<entity>.yml`). If it is a former-final whose seed is already
  among the other members, it is *redundant* — drop it.
- `⚠ … (non-seed members: …)` → a final id resolved through composed_of to
  something that is not a current seed → investigate before using.

**Step 1 — §9.4 over-merge gate (MANDATORY).** Build the index graph:

```
python .claude/skills/v2-merge-coins/merge_helper.py graph <entity> <seed id> [<seed id> …]
```

- **SHARED base index** links the candidates (`hede base 121 <- [a, b]`, or one
  catalogue gives them a single base with sub-letters) → merge is plausible per
  §9.4. Proceed.
- **NO shared base index** → STOP. If the only commonality is ruler+nominal+year
  this is failure mode #1. Surface the graph to the user and get an explicit
  per-case verdict (§8a / §0). Never force a merge the graph cannot justify.
- Remember §9.4's caveat: two candidates are *distinct types* only when EVERY
  catalogue separates them; ONE catalogue unifying them (e.g. Lange base, even
  if Krause+Dav split) is enough to merge. The graph shows which.

**Step 2 — write the merge_decision** in `data/v2/merge_decisions/<entity>.yml`
(create from a sibling if absent; top-level `merges:` / `no_merges:` lists of
`{members: [seed ids], reason: >- …}`). The `reason` must state the §9.4
justification (which catalogue unifies them) + cite the indices accumulated
list-form per §9a. For a SPLIT of a spurious auto-merge, add a
`no_merges:` pair for the bad edge instead (see SPLIT below).

**Step 3 — flow it through:**

```
python scripts/maintenance/merge_seeds_cross_source.py --entity <entity> --apply
python scripts/maintenance/absorb_seeds_into_final_v2.py  --entity <entity> --apply
```

Watch the merger summary: `Forced merges (decisions): N` / `Forced no_merges: N`
must match what you added. Any `⚠ merge member 'X' absent from seed — skipped`
means Step 0 was not done — fix the id and re-run.

**Step 4 — verify (§9a data preservation + no regression):**

- The merged seed_unified entry carries every member's km/hede/sieg/lange/dav
  list-form, every weight reading, every source (eyeball the entry).
- `python scripts/maintenance/audit_lost_citations.py` → `0 missing`.
- `python scripts/audit_v2.py` → I-invariant count not worse than before
  (I4/I6 are pre-existing debt; your change must not add to them).
- **Foundation trap:** if a curated/legacy final coin (`km-NN-…`) absorbed the
  merge, its stored catalog can re-grab a member on the NEXT absorb (it matches
  by km-base). After a split especially, open the final entry and confirm its
  `composed_of` + `catalog` describe ONLY the intended coin; if a foundation
  was poisoned by a prior over-merge, reset its `km`/`composed_of`/year to the
  one coin by hand, then re-absorb. (Real: gottorp `km-35-ja-1611`, 2026-06-29.)
- `python scripts/build.py` → exit 0.

**Step 5 — commit** with pathspec (Git safety protocol): the merge_decision +
seed_unified + final + classification_decisions for that entity only. English
`data:` message documenting the §9.4 justification.

## SPLIT / un-merge — procedure

When an existing entry bundles distinct coins (over-merge):

1. `graph` the bundled members → confirm NO shared base index (else they may be
   one coin after all).
2. Add `no_merges: [{members: [seedA, seedB], reason}]` for the spurious edge(s)
   — the minimum set that the union-find needs to break (the matcher keeps coin
   1 apart from coin 2 on KM/Dav conflict; you usually only block the
   no-shared-index pair). Remove any wrong force-`merges` you added earlier.
3. Re-merge + re-absorb (Step 3). Confirm the seed_unified split into the
   intended N entries.
4. **Foundation cleanup (Step 4 trap):** the split rarely propagates to a
   poisoned final foundation automatically — reset it by hand (see above), then
   re-absorb. Newly-separated coins land in `pending` unless the entity
   `bulk_promote_pending` says otherwise; that is correct (they await
   classification) and is NOT data loss — verify the seeds + sources survive in
   the new entries / pending list.
5. Verify (Step 4) + commit (Step 5). Be honest in history: a wrong-merge
   commit followed by a correction commit is the §0b trail.

## ORPHAN audit / heal (standing maintenance)

```
python .claude/skills/v2-merge-coins/merge_helper.py audit [<entity>]   # exit 1 if any
```

The audit already honours `_expand_member` — a flagged member is a TRUE orphan
(expands to no seed). `resolve` it and classify:
- **redundant** (a former-final / V1 id whose underlying seed is already another
  member of the same block, e.g. `km-305-2-fr-iii-1669` whose `dk-bruun-6712` is
  in the merge) → drop the line. Verify the coin's data already lives in the
  merged entry first (§9a). This is a no-op for the pipeline (the merger was
  already skipping it) — confirm by a date-only seed_unified diff.
- **typo / relocated** → fix to the correct seed id, or drop if the coin moved
  entity (cross-entity merge already re-homed it).
- **unknown** → do not touch; surface to the user.

Do NOT «re-point» a bare Hede code — it is the intended shorthand the merger
expands; it is not flagged. After dropping/fixing, re-merge + re-absorb the
entity and verify (Step 4). Goal: `audit` exits 0.

## Hard rules

- merge_decision members are SEED ids OR a bare Hede code (the merger expands the
  latter to its sub-variants). Never a final/foundation id, never a render id,
  never a folded V1 km-id. `resolve` first, always.
- No merge without the §9.4 `graph` gate. "Same ruler + same nominal + same
  year" is NOT a merge justification on its own.
- A `no_merges` member that does not resolve is an inactive safeguard — treat
  audit exit 1 as a real defect, not noise.
- Curator judgement decides ambiguous §9.4 cases (§8a). Surface the graph; do
  not guess.
