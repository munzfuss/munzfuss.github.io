# Anomaly log — design + operating manual

> **Why this exists.** Without a persistent log, the same anomaly is
> rediscovered every hour by the cron-fired harvest routine, written into the
> per-run snapshot in `_harvest_handoff.json::runs[].anomalies[]`, and lost
> when the 24-run cap rolls it off. Nobody can see «is this a one-off or a
> chronic issue»; nobody can mark something as «in progress» or «fixed». This
> log fixes that — one persistent file in `docs/` with an explicit lifecycle.

**File:** `docs/anomaly_log.yml` (main repo, NOT submodule — see «Storage»
below for rationale).
**Writer / reader lib:** `scripts/lib/anomaly_log.py`.
**One-shot seed script:** `scripts/maintenance/backfill_anomaly_log.py`
(walks the handoff and reconstructs initial state; idempotent).

---

## Schema (one entry)

```yaml
- id: audit_manifest_scope_drift:query=hamburg:source=ikmk
  type: audit_manifest_scope_drift          # vocab below
  key_dims:                                  # determinant dimensions for stable id
    source: ikmk
    query: hamburg
  summary: |
    IKMK discover query «Hamburg» returns OOS records (fuzzy-search
    false-positives outside mission scope).
  status: open                               # open|acknowledged|in_progress|resolved|wontfix
  instance_first_seen: 2026-05-26T23:23:08Z  # for THIS instance (reopens get new timestamp)
  last_seen: 2026-05-27T19:22:57Z            # most recent occurrence
  occurrence_count: 4                        # # of times observed in this instance
  affected_ids:                              # accumulated union across occurrences
    ikmk: [18203249, 18203314, 18203325, ...]
    ucoin: []
  occurrences:                               # full per-run history
    - run_utc: 2026-05-26T23:23:08Z
      batch_label: '157'
      detail: |
        IKMK quick_search queries «Hamburg» + «Kassel» return Roman-era coins
        (pre-mission) — discovery is too broad. Affects batch C all 5 mds_ids.
      full_context:
        action_taken: Saved cache files; flagged in commit + end-of-run report.
        ikmk_batch: C
        numista_batch: EU
        ucoin_batch: '157'
    - run_utc: 2026-05-27T10:23:15Z
      …
  proposed_fix: |
    Tighten QUERIES in scripts/fetch_ikmk.py to constrain «Hamburg» by issuer
    (city of Hamburg, not curator/department keywords), OR add post-fetch
    scope filter before manifest indexing.
  resolution: null                           # filled at status:resolved/wontfix
  resolved_at: null
  resolved_by: null
```

### Status lifecycle

```
              ┌──────────┐
   detected → │   open   │
              └────┬─────┘
                   │  (triager has seen, not yet starting)
                   ▼
              ┌──────────────┐
              │ acknowledged │
              └────┬─────────┘
                   │  (triager starts implementation)
                   ▼
              ┌──────────────┐
              │ in_progress  │
              └────┬─────────┘
                   │  (fix landed or decision made)
        ┌──────────┴──────────┐
        ▼                     ▼
  ┌──────────┐           ┌──────────┐
  │ resolved │           │ wontfix  │
  └──────────┘           └──────────┘
```

`resolved` vs `wontfix`: both terminal. Use `wontfix` when the decision is
«this is acceptable / out of scope / will live with it» — makes
documented-decisions greppable separately from actual fixes.

### Reopen-after-resolved rule

Multiple entries with the **same `id`** are valid — one active + N archived.
`record()`'s decision tree:

```
record(type, key_dims, …)
  ↓
  compute stable_id from type + key_dims
  ↓
  find LATEST entry by instance_first_seen with this id
  ├── status ∈ {open, acknowledged, in_progress} → UPDATE in place:
  │     • bump last_seen + occurrence_count
  │     • append occurrence to occurrences[]
  │     • union affected_ids
  │     • optionally refresh summary / proposed_fix
  └── status ∈ {resolved, wontfix} OR no entry → CREATE NEW entry:
        • status: open
        • instance_first_seen: now
        • occurrence_count: 1
        • previous resolved/wontfix entry stays as archive
```

This means «I fixed it last week» can transparently become «it came back —
fresh instance, fresh count, fresh investigation» without losing the
historical resolution record.

---

## Stable-id derivation rule

Format: `<type-slug>:<k1>=<v1>:<k2>=<v2>…` — kebab-case, keys sorted
deterministically.

**Granularity guideline: FINE.** Per user direction (2026-05-27): «краще
максимум деталей, ніколи не знаєш наперед що з цього буде потрібно для
фікса». Different queries / buckets / per-TID violations get distinct ids —
even when classified under the same `type`. Aggressive splitting is preferred
over premature merging.

**Examples by type:**

| Type | Stable id template | Notes |
|---|---|---|
| `audit_manifest_scope_drift` (IKMK) | `:source=ikmk:query=<query-slug>` | One entry per QUERIES name that misbehaves |
| `audit_manifest_scope_drift` (ucoin) | `:source=ucoin:bucket=<bucket-key>` | One entry per BR-audit bucket |
| `audit_manifest_label_mismatch` | `:source=ucoin:bucket=<bucket-key>` | Bucket label vs ucoin's own period title |
| `audit_manifest_period_boundary` | `:source=ucoin:bucket=<bucket-key>:tid=<tid>` | Per-TID date-bound violation |
| `commit_footer_rejected` | `:hook=<hook-name>` | When pre-commit or auto-mode rejects a commit shape |
| `chrome_mcp_unavailable` | `:source=ucoin` or `:source=numista` | When the routine can't reach Chrome MCP |

**Per-tid / per-batch dimensions** ARE included when they distinguish the
issue. Per-run timestamps / batch labels are NOT — those are occurrence
metadata, not identity.

### Type vocabulary

Stable strings (use these for `type:`); add new ones via this doc + a PR
update to keep them greppable:

| Type | When | Stable id shape |
|---|---|---|
| `audit_manifest_scope_drift` | A source's manifest enumerates entries that fall outside our mission window or non-project entities | `:source=X:query=Y` (IKMK) or `:source=X:bucket=Y` (ucoin/numista) |
| `audit_manifest_label_mismatch` | A bucket label disagrees with the source's own period title | `:source=X:bucket=Y` |
| `audit_manifest_period_boundary` | A specific entry's date falls outside its bucket's claimed period | `:source=X:bucket=Y:tid=N` |
| `commit_footer_rejected` | Pre-commit or auto-mode classifier blocked a commit's shape | `:hook=<hook-name>` |
| `cloudflare_challenge_cleared` | TRANSIENT — Cloudflare hit, but single 90 s wait + retry succeeded → ID cached this run. Handoff snapshot only, NOT logged here | (no log entry — transient) |
| `cloudflare_challenge_persistent` | Cloudflare blocked ≥2 fetches after 90 s waits → fetch failed → ID logged via `url_open_failed` (the failure mode escalates to that type) | (no direct entry; cascades to `url_open_failed`) |
| `canonical_tid_mismatch_persistent` | ucoin save returned exit 2 for ≥2 consecutive TIDs — usually rate-limit; escalates per-TID via `url_open_failed` | (cascades to `url_open_failed`) |
| `chrome_mcp_unavailable` | `list_connected_browsers` returned empty mid-run | `:routine=harvest` |
| `pre_commit_hook_failure` | `.githooks/pre-commit` failed on unrelated files | `:hook=<hook-name>` |
| `concurrent_session_conflict` | Submodule needed rebase, or main-repo had unrelated dirty edits | `:repo=<repo>` |
| `url_open_failed` | Per-ID failure (404 / persistent Cloudflare / canonical-id mismatch / redirect-to-landing / DOM-unexpected). One entry per broken ID across all failure reasons (different reasons = same triage target). **Auto-resolves on successful subsequent fetch.** | `:source=X:id=Y` |
| `priority_bucket_exhausted` | Current-priority bucket closed mid-run; routine moved to next priority (rarely worth logging unless it surfaces a manifest-design issue) | `:source=X:bucket=Y` |
| `doc_update_pending` | A non-blocking «next session please update doc X» note that survived the run | `:doc=<doc-path>` |

---

## Transient anomalies are NOT logged

Anything auto-resolved within the **same run** stays in
`_harvest_handoff.json::runs[].anomalies[]` (per-run snapshot) and does NOT
escalate to `docs/anomaly_log.yml`. Examples:

- Cloudflare interstitial that cleared after a single 90 s wait + cookie-clear.
- A single fetch that 404'd once but succeeded on retry within the same batch.
- A canonical-tid mismatch that resolved on second attempt.

The persistent log is for issues that **survive the run unresolved** — chronic
patterns worth triaging across multiple sessions. The persistence threshold
is what makes the count meaningful.

`backfill_anomaly_log.py`'s classifier table includes an explicit SKIP rule
for `cloudflare_challenge_persistent` records found in handoff history,
documenting this in code.

---

## Storage decision: main repo, not submodule

`docs/anomaly_log.yml` lives in the **main repo**, NOT in
`scripts/cache/` (the harvest submodule).

**Rationale:**

- **Submodule lifecycle is push-by-routine.** Cron-fired routines commit and
  the user pushes. There's no human review step on individual cache entries
  (nor should there be — 11000+ JSON files).
- **Anomaly log requires human triage.** Triager opens the file, picks an
  entry, plans a fix, commits a status transition. That's the same workflow as
  `docs/TODO.md` and `docs/handoff.md` — operational/curatorial artifacts that
  live in the main repo.
- **Build-script doesn't read it.** The anomaly log is operating-context, not
  rendered content. Same as TODO.md / handoff.md — they live in `docs/` because
  they're for humans + sessions to read, not for the build pipeline to consume.

The handoff (`_harvest_handoff.json`) stays in the submodule because it IS
push-by-routine state with no review semantics.

---

## API — `scripts/lib/anomaly_log.py`

### Writer (called by routines that detect anomalies)

```python
from scripts.lib import anomaly_log as al

al.record(
    type_="audit_manifest_scope_drift",
    key_dims={"source": "ikmk", "query": "hamburg"},     # stable-id determinants
    summary="IKMK 'Hamburg' query returns OOS records.",  # short; updated on each call
    detail="Batch W returned 4× post-1914 commems via Hamburg query.",  # this occurrence
    affected_ids={"ikmk": [18203499, 18203500, 18203503, 18203512]},   # per-source lists, unbounded
    proposed_fix="Tighten Hamburg query in fetch_ikmk.py to issuer-scope.",
    batch_label="W",
    run_utc="2026-05-27T19:22:57Z",
    full_context={"action_taken": "...", "numista_batch": "FO"},
)
```

Returns the stable id. Idempotent in the sense that repeat calls with same id
update the same active entry (not creating duplicates).

### Reader (called by routine preflight + end-of-run report)

```python
opens = al.open_anomalies()                          # all active
opens_ikmk = al.open_anomalies(filter_type="audit_manifest_scope_drift")
counts = al.summary_counts()                          # {status: count} across active + archived
entries = al.get_by_id(stable_id, include_archived=True)
```

### Triager state transitions (manual, out-of-routine)

```python
al.mark_acknowledged(stable_id, note="seen, will batch with sibling fix")
al.mark_in_progress(stable_id, note="branch feat/anomaly-fix-ikmk-hamburg open")
al.mark_resolved(stable_id, resolution="Hamburg query now filters to issuer=city_of_hamburg.")
al.mark_wontfix(stable_id, resolution="Acceptable noise — downstream filter strips OOS anyway.")
```

All four enforce «target must be the latest entry AND status must currently
be active». If the latest entry is already terminal, you don't transition it
back — instead, the next `record()` call will spawn a fresh active instance.

**`resolved_in_commit` is deliberately NOT recorded.** Git history on
`docs/anomaly_log.yml` provides the commit trail via `resolved_at` timestamp —
no need for a manual SHA reference field that would require a two-commit
dance (commit fix → record SHA → commit log update).

### Auto-resolve pattern (machine-driven `mark_resolved`)

Some anomaly types resolve themselves when downstream conditions change — the
routine should `mark_resolved()` them automatically without waiting for human
triage.

**Canonical case: `url_open_failed:source=X:id=Y`.** A previous run failed to
fetch the ID. A subsequent run's save script succeeds writing `<id>.json`. The
moment that cache write lands, the active anomaly is moot — auto-resolve it:

```python
# Inside the save loop, right after successful save_*.py exit 0:
stable_id = f"url_open_failed:source={source}:id={id_str}"
existing = al.get_by_id(stable_id, include_archived=False)  # active only
if existing:
    al.mark_resolved(
        stable_id,
        resolution=f"Auto-resolved: cache file written successfully in batch {batch_label}.",
        resolved_by="harvest-routine-auto",
    )
```

No-op if no active entry exists for the ID. Cheap and safe to call on every
successful save.

**Distinguishing `resolved_by`.** Human triagers use `resolved_by="manual"`
(default) or a name like `"serhii"`. Automatic resolvers pass
`resolved_by="harvest-routine-auto"` (or analogous routine-specific tag).
Grepping `resolved_by` in the log separates the two — useful when reviewing
whether a fix actually fixed a chronic issue, or whether the issue just
stopped triggering by coincidence.

**Adding new auto-resolve hooks.** When designing a new anomaly type, decide:
is there a downstream signal that proves «this anomaly is no longer true»? If
yes, wire an auto-resolver at the point where that signal becomes detectable
(usually the success path of whatever the routine was trying to do). Document
the hook in the type table above (last column: stable id shape + auto-resolve
trigger).

---

## Triage workflow (out-of-routine)

1. **Survey:** `git pull && less docs/anomaly_log.yml`, OR
   ```bash
   python -c "from scripts.lib import anomaly_log as al; \
              [print(e['id'], e['occurrence_count']) for e in al.open_anomalies()]"
   ```
   Sort by `occurrence_count desc` to see chronic issues first.

2. **Pick one.** Read its `proposed_fix`, look at `affected_ids` for sample
   evidence, decide on approach.

3. **Mark in-progress** before starting:
   ```python
   al.mark_in_progress("audit_manifest_scope_drift:query=hamburg:source=ikmk",
                       note="implementing post-fetch scope filter in fetch_ikmk.py")
   ```
   Commit just that log change as «anomaly: mark X in_progress».

4. **Implement the fix.** Normal feature workflow — code changes, tests, commits.

5. **Close the loop:**
   ```python
   al.mark_resolved("audit_manifest_scope_drift:query=hamburg:source=ikmk",
                    resolution="Added _is_in_mission_scope() filter in fetch_ikmk.py:save_record(); …")
   ```
   Commit as «anomaly: resolve X».

If the same anomaly recurs after resolution (new batch detects it again):
`record()` notices the latest entry is terminal and spawns a fresh active
instance — the previous resolved entry stays as archive. The next triager
sees both: «this was 'fixed' on date X but came back on date Y».

---

## Migration / first-time setup

Run once:

```bash
.venv/bin/python scripts/maintenance/backfill_anomaly_log.py
```

This walks `scripts/cache/_harvest_handoff.json::runs[].anomalies[]` and emits
classified entries. Classification rules are hand-written for known anomaly
shapes (IKMK query false-positives, ucoin bucket scope drift, etc.); new
historic shapes that don't match any classifier are reported as
«Unclassified» in the script output — surface them, then either add a new
classifier rule and re-run, or hand-record them via `al.record()` in a REPL.

The backfill is **idempotent**: re-running on an already-populated log will
inflate `occurrence_count` and append duplicate occurrences (since each
historic record gets re-classified into the existing active entry). Don't
re-run unless you mean to. The output's before-vs-after counts make double-runs
obvious.

---

## Open questions / future work

- **Auto-stale detection.** Should an open entry that hasn't had a new
  occurrence in N days auto-transition to `acknowledged`? Currently NO — all
  state transitions are manual. Decision deferred until backlog stabilises and
  we know what «stale» means in practice.
- **Affected-ids cap.** Currently unbounded per user direction («записуй всі,
  що нам 100 чи 1000 чисел»). Revisit if the log grows past a few MB.
- **Per-id occurrence cap.** Same — unbounded. Each occurrence's
  `full_context` carries useful detail; trimming the tail might lose
  triage-relevant evidence.
- **Cross-link to commits.** `resolved_in_commit` field deliberately absent.
  If we later want first-class commit linkage, the migration is straightforward
  (add field, fill from `git log -- docs/anomaly_log.yml`).
