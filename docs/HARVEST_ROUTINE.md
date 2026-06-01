# Hourly autonomous harvest routine

> **Purpose.** Self-contained operational manual for an hourly cron-fired
> Claude session that executes ONE Numista batch + ONE ucoin batch per
> run, commits each, and reports updated coverage tables. Designed to
> work cold — no chat history, no project knowledge required beyond
> reading this file + `CLAUDE.md`.
>
> **Companion docs (do NOT need full read; section pointers used inline):**
> - `CLAUDE.md` — project conventions (atomic commits, English-only commit messages, never-push-without-permission, period-correct German orthography rule for any prose).
> - `docs/PLAYBOOKS.md` PB-10 — submodule-first-then-bump-pointer commit dance (referenced concretely below — no separate read needed).
> - `docs/SOURCES.md` §13.1 / §13.2 — Numista + ucoin known-issues log.
> - `docs/handoff.md` — session-state notes (read once at session start to confirm priority order; this file's logic supersedes the handoff for routine batching).
>
> **Scope.** This routine harvests **catalogue metadata only** — per-coin
> JSON sidecars into `scripts/cache/numista/<nid>.json` and
> `scripts/cache/ucoin/<tid>.json`. It does NOT touch seed builders,
> location YAMLs, or rendering. The seed pipeline consumes the cache
> downstream; this routine only feeds the cache.

---

## §0. Critical invariants (read before anything else)

1. **Branch model — the routine pushes AUTONOMOUSLY, but ONLY to its own branch + the submodule `main`; it NEVER writes the superproject `origin/main`.** This routine now runs in its OWN clone (`/Users/serg/Documents/GitHub/munzfuss.github.io`); the interactive / curation work lives in a SEPARATE clone (`/Users/serg/projects/muentzfuesse`) that pulls harvest changes when the curator decides. Because the two clones no longer share a working tree, the old shared-index race is gone; the only remaining race is push-level against the shared remote. The branch model removes it by construction:

   - **Superproject (`munzfuss.github.io`): the routine works on `harvest/auto`, never on `main`.** It pointer-bump-commits to `harvest/auto` and `git push origin harvest/auto`. The routine is the SOLE writer of `harvest/auto`, so the push is always a fast-forward — never rejected, never racing. `origin/main` stays single-writer (only the curation clone advances it), so the routine can NEVER race on, or corrupt, the deployable branch. Integration into `main` is the curation clone's job — a local `git merge origin/harvest/auto` (no PR); see §3.4.
   - **Submodule (`munzfuss-harvest`): the routine pushes directly to `main`.** The routine is the ONLY writer of the cache submodule (curation touches `data/**`, never the cache), so submodule `main` is single-writer too — direct push, no branch, no race.
   - **NEVER `git push origin main` in the superproject.** That is the one forbidden push. If you ever find yourself about to push the superproject `main`, stop — the routine's superproject pushes go to `harvest/auto` only.
   - **`harvest/auto` is append-only in the routine: never rebase it, never force-push it.** Just keep stacking pointer-bump commits and fast-forward-pushing. (Rebasing/force-pushing is unnecessary — see §1's preflight, which simply ensures the branch exists off the latest `origin/main`.)
   - **No per-run «wait for пуш» gate.** Cron-fired runs push `harvest/auto` + submodule `main` autonomously at end of run (§3, §5). The end-of-run report states what was pushed and the one-line integration command for the curator (§6.2 item 10). The CLAUDE.md global «never push autonomously» rule still governs the SUPERPROJECT `main` and the CURATION clone — this carve-out is scoped strictly to the routine pushing `harvest/auto` + submodule `main`.

2. **One Numista batch + one ucoin batch + one IKMK batch per run.** Do not exceed this. Numista + ucoin are Chrome-MCP scrapes through Cloudflare, hard-capped at **5 entries/batch** (context budget + politeness). IKMK is different: a plain `urllib` museum JSON API (`docs/IKMK_HARVEST.md`) — openly licensed (CC BY-SA 4.0), no Cloudflare, no observed rate limit, ID-list-from-search-queries rather than per-NID URLs — so its single batch is **200 entries/run** (§5.5.1), clearing the title-scoped backlog in a handful of runs. See §5.5 for the batch protocol. IKMK can be skipped per-run when no uncached IDs remain (§5.5.5).

3. **Batch size = 5 entries** (NIDs or TIDs). Hard cap. If a batch would close the bucket and only 3 remain, do those 3 — never extend past the bucket boundary into the next priority.

4. **Pacing = 31-60s between fetches** within a single batch. Random `sleep $((RANDOM % 30 + 31))` between calls. Do NOT skip pacing «to save time» — Cloudflare and ucoin's rate-limit defence fire fast.

5. **The routine's ONLY job is HARVEST + collecting cached data. It writes the cache; it never edits data, and it never interprets.** Two halves of this rule:
   - **Never edit `data/**`** — no YAML / seeds / location / `data/v2/**` files (incl. `data/v2/final`, `data/v2/seed*`, `data/v2/*_decisions`). Cache writes only.
   - **Never produce a VERDICT or DECISION — only raw EVIDENCE.** When a task needs a judgement about the data (which Müntzfuß, dual-vs-single nominal, is-this-a-duplicate, what's the correct value), the routine records the raw observation into the cache (a `_audit_context` field, or a dedicated evidence sidecar like `_ci_legend_evidence.json`) and STOPS. The interpretation + the resulting data edit are CURATION, done in an interactive session — never autonomously by the cron. «Harvest the legend» ✓; «decide the nominal» ✗. (Reference case: §5.6.)
   If the cache reveals a data anomaly (wrong year range, missing fineness), record it in `_audit_context` / the anomaly log — never propagate to seeds or data in this run.

6. **English-only commit messages** (CLAUDE.md «Git workflow» rule). Chat may be Ukrainian; commits are English.

7. **`scripts/cache/` is a submodule.** Every commit is a TWO-STEP dance,
   and BOTH steps commit with an EXPLICIT PATHSPEC (never a bare
   `git commit` — that commits the whole shared index, sweeping a
   parallel session's staged files; see §0.8 + CLAUDE.md «Surgical
   staging under a shared working tree»). Then a THIRD step pushes both
   (submodule `main` first, superproject `harvest/auto` second — per §0.1):
   - Step A: `cd scripts/cache && git add <explicit cache paths> && git commit <same explicit paths> -m "…" && git push origin main`
   - Step B: `cd /Users/serg/Documents/GitHub/munzfuss.github.io && git commit scripts/cache -m "data: bump cache pointer — …"` (scripts/cache is already tracked — pathspec-commit alone, no `git add` of anything else)
   - Step C: `git push origin harvest/auto` (fast-forward of the routine's own branch — never rejected).
   - Step A + B required for every commit; missing step B = pointer drift (next session sees `git status` warn `modified: scripts/cache (new commits)`). Push order is load-bearing: submodule `main` MUST be pushed before the superproject pointer that references it, else the curation clone pulls a dangling pointer.

8. **Surgical commits — stage ONLY the files you intend to commit.** With the branch model (§0.1) the routine has its own clone, so interactive / curation sessions no longer share this working tree — the original shared-index race that produced commit `2bfa76b` is structurally gone. The pathspec discipline below is RETAINED as cheap insurance against the one residual co-tenant: **two harvest runs overlapping in THIS clone** (a cron fire while a previous run is still finishing). Keep committing atomically by explicit pathspec so an overlapping run can never sweep your in-flight stage, and vice versa.

   **Concrete rules:**
   - **NEVER use `git add .` or `git add -A` or `git add -u`** — these blanket-stage everything dirty, including the parallel session's work.
   - **NEVER use `git commit -a`** — it auto-stages every tracked file with modifications.
   - **Always stage by explicit file path** — `git add numista/123.json numista/456.json scripts/cache/_harvest_handoff.json` (specific files) vs. `git add scripts/cache` (specific submodule pointer, single path).
   - **In Step B of the PB-10 dance**, stage ONLY `scripts/cache` — never `git add scripts/cache docs/`, never `git add scripts/cache assets/`, never any second path on the same `git add`. The cache-pointer commit's ONLY purpose is the pointer; if docs / assets / scripts changed, they go in SEPARATE commits.
   - **PRIMARY GUARD — commit with an EXPLICIT PATHSPEC, never a bare `git commit`.** A bare `git commit -m "…"` commits the ENTIRE shared `.git/index` — including files a PARALLEL session staged. The «stage by explicit path» rules above stop the routine from *staging* others' work, but a bare commit still sweeps what others already staged. So always name the paths on the commit itself: `git commit numista/<n1>.json <n2>.json -m "…"` (Step A) / `git commit scripts/cache -m "…"` (Step B). `git commit <pathspec>` commits ONLY those paths and leaves every other index entry untouched — race-proof regardless of the shared index's state. This is the canonical fix; see CLAUDE.md «Surgical staging under a shared working tree (Git safety protocol)». **This is exactly the bug that produced commit `2bfa76b` (2026-05-30)** — a routine cache-pointer bump bare-committed the shared index and swept a parallel session's `data/v2/final/*` + `scripts/maintenance/*` edits.
   - **Re-check `git status --short` IMMEDIATELY before each `git commit`** — secondary guard. With pathspec-commit the bare-index sweep can't happen, but the status check still catches «did my own paths end up as expected». Concurrent session edits between preflight and commit time are normal and — with pathspec-commit — harmless.
   - **If a bundle happens anyway** (commit got more files than intended), do NOT amend. Per CLAUDE.md «Git safety protocol», create a corrective commit:
     ```bash
     # Self-recovery — split a bundle into atomic commits (pathspec on
     # every commit so the split itself can't re-sweep the shared index):
     git reset --soft HEAD~1                  # un-commit, keep stages
     git reset HEAD                            # un-stage everything
     git commit <only-cache-pointer-path> -m "..."   # atomic harvest commit (pathspec)
     git commit <other-paths> -m "..."        # atomic OTHER commit, or leave for user
     ```
     The routine that caused commit `95b3f59` (2026-05-21) ran this recovery successfully — keep that pattern as the template.

   **Why this matters.** Each commit must be reviewable + revertable independently. A bundle of «cache pointer + 6 favicon assets + favicon-generator script» can't be cleanly rolled back if any one element turns out wrong, and the commit message can only describe one of them, leaving the others undocumented in git history.

9. **End-of-session protocol — commit AND push your changes (submodule `main` + superproject `harvest/auto`), leave `main` and everyone else's files alone.** Every session MUST close with:

   - **Commit ALL of the routine's own changes** — the submodule cache writes (`scripts/cache/<source>/*.json`), handoff (`scripts/cache/_harvest_handoff.json`), the superproject pointer bump, and `docs/anomaly_log.yml` if the routine wrote anomalies this run.
   - **Push autonomously per §0.1** — submodule `main` first (Step A), then superproject `harvest/auto` (Step C). NEVER push the superproject `main`. No «wait for пуш» gate; cron runs push on their own.
   - **DO NOT commit changes you did not make.** Use surgical staging per §0.8. In the steady state this clone is routine-only, so the working tree should be clean apart from the routine's own writes; if you see unexpected dirty files (e.g. a manual curator edit made in this clone by mistake), leave them untouched and surface them in the report.
   - **A non-clean working tree at session end is a yellow flag now, not green.** Since this clone is routine-only, leftover dirt usually means a bug in the commit dance — investigate rather than shrug it off.

   **Operational check before closing the session:**

   ```bash
   git status --short                 # expected: clean
   git log --oneline origin/harvest/auto..HEAD   # expected: empty (all pushed)
   cd scripts/cache && git log --oneline origin/main..HEAD && cd ../..   # expected: empty
   #
   # Forbidden at this point:
   #          - any modified file under scripts/cache/<source>/ (uncommitted cache write)
   #          - any modified scripts/cache/_harvest_*.json (uncommitted handoff)
   #          - scripts/cache itself showing «modified» (submodule pointer not bumped — step B missed)
   #          - HEAD ahead of origin/harvest/auto (commit not pushed — step C missed)
   #          - the routine sitting on `main` instead of `harvest/auto` (branch-model violation, §0.1)
   ```

   If any of those «forbidden» states surface, the routine has a bug — finish the commit + push dance before exiting.

10. **Tab reuse — reuse the SAME Chrome tab for every fetch in the run; never spawn new tabs.** Chrome MCP exposes `tabs_create_mcp` (open a new tab) and `tabs_close_mcp` (close one). The harvest routine MUST use `tabs_context_mcp(createIfEmpty: true)` once at preflight to attach to (or create) ONE tab, and then `navigate` within that same tab for every subsequent NID / TID in the batch. Do not call `tabs_create_mcp` to «start fresh» between fetches.

    **If a fetch fails** (Cloudflare challenge, rate-limit defence, broken markup): **first try clearing cookies** for the target domain (Chrome MCP exposes cookie removal via `javascript_tool` with a `document.cookie` clear pattern, or via the appropriate browser shortcut), then re-navigate in the SAME tab. Only as a LAST resort, close the current tab and let `tabs_context_mcp(createIfEmpty: true)` reattach. Do NOT proliferate tabs — each new tab burns user-visible UI real estate, breaks reasoning about which tab the routine is acting on, and forces the user to clean up afterwards.

    **Why this matters.** Multiple harvest runs over a day can leave dozens of tabs open in the user's actual Chrome window — visible clutter that is hard to triage post-hoc. Cookie-clear + tab-reuse keeps the browser footprint at exactly one tab regardless of how many fetches the routine performs.

---

## §1. Preflight (do this once at session start)

```bash
# 1. Confirm cwd is the ROUTINE clone root
pwd                                # must be /Users/serg/Documents/GitHub/munzfuss.github.io
test -d scripts/cache              # submodule present
test -f /tmp/save_numista.py       # per-NID saver (may need re-create — see §1a)
test -f /tmp/save_ucoin.py         # per-TID saver

# 2. BRANCH SYNC (before-task, per §0.1) — get onto harvest/auto and pull the submodule to its latest.
#    harvest/auto is APPEND-ONLY: never rebased, never force-pushed (§0.1). On first run it is created
#    off origin/main; thereafter it just accumulates. We do NOT rebase it onto origin/main — divergence
#    from main is fine, the curation clone absorbs it with a clean merge (§3.4). Harvest files
#    (cache pointer, anomaly_log) don't overlap curation files (data/**), so that merge is automatic.
git fetch origin
git checkout harvest/auto 2>/dev/null || git checkout -b harvest/auto origin/main   # create off main on first run
git merge --ff-only origin/harvest/auto 2>/dev/null || true   # absorb any prior pushed commits (sole writer → ff)
#   Submodule to latest main (single-writer → fast-forward; reset is safe since only the routine writes it):
cd scripts/cache && git fetch origin && git checkout main && git reset --hard origin/main && cd ../..

# 3. Confirm working tree is clean
git status --short                 # routine-only clone → expected clean; if dirty, inspect before proceeding

# 4. Confirm Chrome MCP is connected
# (use the tabs_context_mcp tool with createIfEmpty:true at the start of step-1 batch)

# 5. Refresh stale cached_count / cached_tids / gap lists in the audit
#    manifests from the actual on-disk cache, so §2.1's bucket picker does
#    not re-offer already-cached buckets and burn the run on defensive
#    sampling (anomaly audit_manifest_scope_drift:field=cached_count).
#    Idempotent + format-preserving — a no-op run leaves a zero-byte diff;
#    any changes it does make are part of THIS run and get committed with
#    the routine's normal cache commit (§3.1 / §5.1).
.venv/bin/python scripts/maintenance/refresh_audit_cached_counts.py --write
```

### §1a. Re-create `/tmp/save_*.py` if missing

`/tmp` is wiped on reboot. If either script is missing, re-create from the inline content below.

**`/tmp/save_numista.py`** — write via the Write tool:

```python
"""Save Numista per-NID JSON to scripts/cache/numista/<nid>.json."""
import json
import sys
import pathlib
from datetime import datetime, timezone

def main():
    payload = sys.stdin.read()
    try:
        d = json.loads(payload)
    except json.JSONDecodeError as e:
        print(f"ERROR: invalid JSON: {e}", file=sys.stderr)
        sys.exit(1)

    nid = d.get('id')
    if not nid:
        print("ERROR: no id in payload", file=sys.stderr)
        sys.exit(1)

    out = dict(d)
    out["_harvested_via"] = "chrome_mcp_html"
    out["_harvested_at"] = datetime.now(timezone.utc).isoformat()

    out_path = pathlib.Path('scripts/cache/numista') / f"{nid}.json"
    out_path.write_text(json.dumps(out, indent=2, ensure_ascii=False))
    print(f"saved {out_path} ({out_path.stat().st_size} bytes) — {out.get('title')}")

if __name__ == '__main__':
    main()
```

**`/tmp/save_ucoin.py`** — write via the Write tool:

```python
"""Save ucoin per-TID JSON with canonical-tid validation.

Aborts with exit 2 if _verified is false (canonical_tid != requested_tid)
— rate-limit defence likely fired, DO NOT save the page.
"""
import json
import sys
import pathlib
from datetime import datetime, timezone

def main():
    payload = sys.stdin.read()
    try:
        d = json.loads(payload)
    except json.JSONDecodeError as e:
        print(f"ERROR: invalid JSON: {e}", file=sys.stderr)
        sys.exit(1)

    requested_tid = d.get('requested_tid') or d.get('id')
    if not requested_tid:
        print("ERROR: no requested_tid / id in payload", file=sys.stderr)
        sys.exit(1)

    if not d.get('_verified'):
        canonical_tid = d.get('canonical_tid')
        print(f"⚠ ABORT: TID {requested_tid} FAILED canonical-tid check (canonical={canonical_tid}) — rate-limit defence likely fired. NOT saving.", file=sys.stderr)
        sys.exit(2)

    out = {
        "tid": requested_tid,
        "url": d.get("url"),
        "title": d.get("title"),
        "issuer_text": d.get("issuer_text"),
        "ruler_text": d.get("ruler_text"),
        "period": d.get("period"),
        "years_text": d.get("years_text"),
        "min_year": d.get("min_year"),
        "max_year": d.get("max_year"),
        "denomination": d.get("denomination"),
        "value_text": d.get("value_text"),
        "currency": d.get("currency"),
        "composition_text": d.get("composition_text"),
        "fineness": d.get("fineness"),
        "weight_g": d.get("weight_g"),
        "diameter_mm": d.get("diameter_mm"),
        "thickness_mm": d.get("thickness_mm"),
        "shape": d.get("shape"),
        "edge_text": d.get("edge_text"),
        "technique": d.get("technique"),
        "mint_text": d.get("mint_text"),
        "references_text": d.get("references_text"),
        "references_list": d.get("references_list", []),
        "obverse_text": d.get("obverse_text"),
        "reverse_text": d.get("reverse_text"),
        "_verified": True,
        "_canonical_tid": d.get("canonical_tid"),
        "_harvested_via": "chrome_mcp_html",
        "_harvested_at": datetime.now(timezone.utc).isoformat(),
        "_audit_context": d.get("_audit_context", "BR batch — ucoin per-TID harvest"),
    }

    out_path = pathlib.Path('scripts/cache/ucoin') / f"{requested_tid}.json"
    out_path.write_text(json.dumps(out, indent=2, ensure_ascii=False))
    print(f"saved {out_path} ({out_path.stat().st_size} bytes) — {out['title'] or out['denomination']}")

if __name__ == '__main__':
    main()
```

---

## §1.5. Handoff file — between-runs state

> **Path.** `scripts/cache/_harvest_handoff.json` (inside the submodule — ships with cache data, no extra main-repo commit needed; bumped naturally with each batch commit).

The handoff file carries forward what the next run needs to know without reading chat history: last batch labels, deferred IDs to retry, anomalies the previous run surfaced, audit-files-known-state notes, and a per-run history log.

### §1.5.1. Read at session start (after §1 preflight)

> **Path resolution — always use `git rev-parse --show-toplevel` as anchor.** The routine's PB-10 dance involves `cd scripts/cache` mid-flow; relative paths like `scripts/cache/_harvest_handoff.json` break if a handoff read/write runs while cwd is already inside the submodule. Anchoring at the git toplevel makes the path resolution cwd-independent. (Failure mode caught 2026-05-21 cron-run X/38: handoff appeared «missing» after a misordered cd; recovered via `git checkout` + manual run-entry merge.)

```bash
.venv/bin/python <<'EOF'
import json, pathlib, subprocess
repo_root = pathlib.Path(subprocess.check_output(
    ['git', 'rev-parse', '--show-toplevel'], cwd=pathlib.Path.cwd()
).decode().strip())
# If cwd is inside the submodule, --show-toplevel returns the submodule root.
# Walk up to find the main repo (handoff lives in scripts/cache/, which IS the submodule):
if (repo_root / 'scripts/cache/_harvest_handoff.json').exists():
    p = repo_root / 'scripts/cache/_harvest_handoff.json'                  # main-repo cwd case
elif (repo_root / '_harvest_handoff.json').exists():
    p = repo_root / '_harvest_handoff.json'                                 # submodule cwd case
else:
    p = None

if p is None or not p.exists():
    print('!!! Handoff file missing — fresh-start mode; proceed but flag at end-of-run.')
else:
    h = json.loads(p.read_text())
    print('Last run UTC:', h.get('last_run_utc'))
    print('Next batch labels:', h.get('next_numista_batch_label'), '/', h.get('next_ucoin_batch_label'))
    if h.get('priority_override'):
        print('!!! Priority override active:', h['priority_override'])
    deferred = h.get('deferred_ids', {})
    if deferred.get('numista') or deferred.get('ucoin'):
        print('Deferred IDs to retry this run:', deferred)
    pending = h.get('routine_doc_pending_updates', [])
    if pending:
        print('Routine-doc pending updates (FYI, do not block):', pending)
    fos = h.get('failed_open_recent_summary', {})
    if fos.get('numista') or fos.get('ucoin'):
        n_count = len(fos.get('numista', []))
        u_count = len(fos.get('ucoin', []))
        print(f'!!! Recent failed_open carry-over: {n_count} Numista, {u_count} ucoin — surface in §8 if user inspection still pending.')
EOF
```

Apply the read like so:

- **`next_numista_batch_label` / `next_ucoin_batch_label`** — use these verbatim as the new batch's `<letter>` / `<N>`. If you mint your own label (e.g. label already used in a concurrent session), record the alias in the new run's anomaly list.
- **`priority_override`** — if non-null, **honour it FIRST** for that source. E.g. `{source: "numista", bucket: "NO p4", reason: "user-requested closure push"}` → ignore §2.2's priority table and harvest from NO p4 this run.
- **`deferred_ids`** — retry these BEFORE picking fresh entries from the priority bucket. They represent NIDs/TIDs the previous run couldn't fetch (transient Cloudflare blocked, canonical-tid mismatch, etc.) and explicitly punted to «next hour». Drop a deferred ID from the list once it lands cleanly. If it fails again in this run, log it via §2.4 / §4.4 to `_failed_open_ids.json` for user review (NEVER mark as «deleted» — the upstream state is opaque to the routine).
- **`audit_files_known_state`** — read this BEFORE running §7.5 defensive sampling. If the audit notes say «denmark/p4 OOS-reclassified 2026-05-21», you don't need to re-verify; the upstream fix has landed.
- **`routine_doc_pending_updates`** — informational only; the routine itself does not edit `docs/HARVEST_ROUTINE.md` (that requires user review). If the list contains items, surface them in the end-of-run report so the user sees them.

### §1.5.2. Write right before the ucoin commit (§5.1)

The handoff file rides with the **ucoin commit** (the last commit of the run) so each run produces exactly two submodule commits — Numista cache, then ucoin cache + handoff bump. Write the file via Python `json.dump` AFTER ucoin saves complete but BEFORE the `cd scripts/cache && git add ucoin/...` line in §5.1. The ucoin commit's `git add` includes `_harvest_handoff.json` in the file list.

> **Path resolution — same `git rev-parse` anchor as §1.5.1.** The write step often runs immediately AFTER a `cd scripts/cache` for the Numista commit (Step A of §3.1). Cwd may be either the main repo or the submodule; the snippet must work in both.

```python
import json, pathlib, subprocess
from datetime import datetime, timezone

repo_root = pathlib.Path(subprocess.check_output(
    ['git', 'rev-parse', '--show-toplevel'], cwd=pathlib.Path.cwd()
).decode().strip())
# Resolve regardless of whether cwd is main-repo or inside submodule:
if (repo_root / 'scripts/cache/_harvest_handoff.json').exists():
    p = repo_root / 'scripts/cache/_harvest_handoff.json'
else:
    p = repo_root / '_harvest_handoff.json'   # submodule-cwd fallback

h = json.loads(p.read_text())

# Update top-level cross-run state
now = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')
h['last_run_utc'] = now
h['last_numista_batch_label'] = NUMISTA_BATCH_LABEL   # e.g. 'R'
h['last_ucoin_batch_label'] = UCOIN_BATCH_LABEL       # e.g. '32'
h['next_numista_batch_label'] = _increment_label(NUMISTA_BATCH_LABEL)  # 'R' → 'S'
h['next_ucoin_batch_label'] = str(int(UCOIN_BATCH_LABEL) + 1)          # '32' → '33'

# Carry deferred IDs forward / clear closed ones
h['deferred_ids']['numista'] = NUMISTA_DEFERRED_THIS_RUN
h['deferred_ids']['ucoin'] = UCOIN_DEFERRED_THIS_RUN

# Append this run to the history (cap to last 24 entries = 1 day)
new_run = {
    'run_utc': now,
    'trigger': 'cron-fired autonomous',  # or 'user-driven'
    'numista_batch': {
        'label': NUMISTA_BATCH_LABEL,
        'bucket': '<bucket-name>',
        'nids_saved': NIDS_THIS_RUN,
        'saved_count': len(NIDS_THIS_RUN),
        'deferred': NUMISTA_DEFERRED_THIS_RUN,
        'failed_open': NUMISTA_FAILED_OPEN_THIS_RUN,  # list of {id, reason, url_tried, ts}
    },
    'ucoin_batch': {
        'label': UCOIN_BATCH_LABEL,
        'period': '<period-name>',
        'tids_saved': TIDS_THIS_RUN,
        'saved_count': len(TIDS_THIS_RUN),
        'deferred': UCOIN_DEFERRED_THIS_RUN,
        'failed_open': UCOIN_FAILED_OPEN_THIS_RUN,    # list of {id, reason, url_tried, ts}
    },
    'anomalies': ANOMALIES_THIS_RUN,  # list of {type, detail, action_taken, follow_up}
    'notes': '<short freeform — closure note, defensive-sample positives, etc.>',
}
h['runs'].append(new_run)
h['runs'] = h['runs'][-24:]   # keep last 24 runs

p.write_text(json.dumps(h, indent=2, ensure_ascii=False) + '\n')
```

**The handoff file is bumped in the ucoin commit (§5.1), not the Numista commit.** This keeps each run's commit count at exactly two: Numista cache (§3.1), then ucoin cache + handoff (§5.1). Both pointer bumps in main repo follow per PB-10.

### §1.5.3. Label-increment rule

- Numista labels: single uppercase letter A-Z, then double letters AA-ZZ. `_increment_label('Q') == 'R'`, `_increment_label('Z') == 'AA'`, `_increment_label('AZ') == 'BA'`.
- ucoin labels: integer string. `int(label) + 1`.

### §1.5.4. Anomaly type vocabulary (for the `runs[].anomalies[].type` field)

> **Canonical vocab + lifecycle: `docs/ANOMALY_LOG.md`.** The same type strings are used here (handoff per-run snapshot) and in the persistent log. Keep the two in sync — when adding a new type, update both this table AND `docs/ANOMALY_LOG.md` §«Type vocabulary».

Use these stable strings so the next run can grep / match without prose parsing:

| Type | When |
|---|---|
| `audit_manifest_scope_drift` | §7.5 defensive sample shows a bucket's gap list contains OOS entries |
| `audit_manifest_label_mismatch` | A bucket's label disagrees with the source's own period title |
| `audit_manifest_period_boundary` | A specific entry's date falls outside its bucket's claimed period |
| `commit_footer_rejected` | Pre-commit or auto-mode classifier rejects the Co-Authored-By footer (or similar) |
| `cloudflare_challenge_cleared` | Cloudflare hit, but a single 90 s wait + retry succeeded → ID cached. TRANSIENT — handoff snapshot only, NOT promoted to persistent log |
| `cloudflare_challenge_persistent` | Cloudflare blocked the same source ≥2 times in this run despite 90s waits → fetch failed → §2.4 dual-write fires (raw log + anomaly_log) |
| `canonical_tid_mismatch_persistent` | ucoin save script returned exit 2 for ≥2 consecutive TIDs |
| `chrome_mcp_unavailable` | `list_connected_browsers` returned empty mid-run |
| `pre_commit_hook_failure` | `.githooks/pre-commit` failed validate/audit on unrelated files |
| `concurrent_session_conflict` | submodule needed rebase or main-repo had unrelated dirty edits |
| `url_open_failed` | Source returned 404 / persistent Cloudflare / canonical-id mismatch / redirect-to-landing / DOM-shape-unexpected for an ID that was in the audit's gap list. NEVER framed as «deleted» — upstream state opaque. Goes to both `_failed_open_ids.json` (raw) AND persistent anomaly log (`url_open_failed:source=X:id=Y` — auto-resolves when subsequent run successfully fetches the ID). |
| `priority_bucket_exhausted` | The current-priority bucket closed mid-run; routine moved to next priority |
| `doc_update_pending` | Routine surfaced a non-blocking «next session please update doc X» note |

For each anomaly, also fill `detail` (free-text), `action_taken` (what the routine did), and `follow_up` (what the user/next-session should do).

---

## §1.6. Anomaly log — persistent record

> **File:** `docs/anomaly_log.yml` (MAIN repo, not submodule).
> **Lib:** `scripts/lib/anomaly_log.py`.
> **Doc:** `docs/ANOMALY_LOG.md` (full schema + lifecycle + triage workflow).

The handoff's `runs[].anomalies[]` is a **per-run snapshot** that rolls off after 24 runs. The anomaly log is the **persistent record** — every non-transient anomaly the routine detects gets recorded there too, with stable id + occurrence counter + status lifecycle (open → acknowledged → in_progress → resolved/wontfix). This makes recurring patterns visible across sessions and gives the user a single place to triage chronic issues.

### §1.6.1. Transient vs persistent (decision rule)

| Anomaly auto-resolved within the SAME run | → handoff `runs[].anomalies[]` ONLY (per-run snapshot). Do NOT write to anomaly log. |
| Anomaly survives the run unresolved | → handoff `runs[].anomalies[]` AND `docs/anomaly_log.yml` via `al.record(...)`. |

Examples of **transient** (handoff only):
- Cloudflare interstitial cleared after single 90 s wait + cookie-clear.
- Single fetch 404'd but succeeded on retry within the same batch.

Examples of **persistent** (handoff + anomaly log):
- IKMK QUERIES false-positives (chronic; every IKMK batch hits them).
- ucoin BR-4 bucket scope drift (manifest enumerated pre-mission TIDs).
- ucoin bucket label mismatch (Hochstift vs City).
- ucoin per-TID period-boundary violation.

### §1.6.2. Write at detection time (NOT batched at run-end)

When the routine detects a persistent anomaly mid-run, write to the log **immediately** via:

```python
from scripts.lib import anomaly_log as al

al.record(
    type_="audit_manifest_scope_drift",
    key_dims={"source": "ikmk", "query": "hamburg"},
    summary="IKMK 'Hamburg' query returns OOS records.",
    detail="Batch W: 4 of 5 fetched mds_ids OOS via Hamburg query (Bundesrepublik commems, Byzanz).",
    affected_ids={"ikmk": [18203499, 18203500, 18203503, 18203512]},
    proposed_fix="Tighten Hamburg query in fetch_ikmk.py to issuer-scope or add post-fetch scope filter.",
    batch_label="W",
    full_context={"ikmk_batch": "W", "numista_batch": NUMISTA_BATCH_LABEL, "ucoin_batch": UCOIN_BATCH_LABEL},
)
```

The lib's `record()` either appends to the existing active entry (if same id + status ∈ {open, acknowledged, in_progress}) or creates a fresh active entry (if no entry OR latest is terminal — reopen-after-resolved per `docs/ANOMALY_LOG.md`).

**Stable-id derivation guideline: FINE granularity.** Different queries / buckets / per-TID violations get distinct `key_dims` → distinct stable ids. When an event affects multiple queries / buckets in one batch (e.g. «IKMK batch returned bad results for Hamburg AND Christian VIII queries»), call `al.record()` ONCE PER affected query — each call lands in its own log entry.

### §1.6.3. Read at preflight (alongside handoff §1.5.1)

After the handoff read, surface open anomalies for context:

```bash
.venv/bin/python <<'EOF'
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))  # adjust for cwd
from scripts.lib import anomaly_log as al

opens = al.open_anomalies()
print(f'Open anomalies: {len(opens)} (across {len(set(e["type"] for e in opens))} types)')
for e in sorted(opens, key=lambda x: x['occurrence_count'], reverse=True)[:8]:
    aff_summary = ', '.join(f'{k}:{len(v)}' for k, v in (e.get('affected_ids') or {}).items()) or 'none'
    print(f'  occ={e["occurrence_count"]:2d}  {e["id"]}  (affected: {aff_summary})')
EOF
```

These are **informational, not blocking**. The routine continues normally; the open count just appears in the end-of-run report. The user (or a separate triage session) handles state transitions via `al.mark_acknowledged()` / `al.mark_in_progress()` / `al.mark_resolved()` / `al.mark_wontfix()` per the workflow in `docs/ANOMALY_LOG.md`.

### §1.6.4. Commit anomaly log changes with the routine's normal commits

`docs/anomaly_log.yml` is in the MAIN repo, so its modifications appear in `git status` of the main repo (NOT the submodule). When the routine wrote new anomalies this run, the file shows up as `M docs/anomaly_log.yml` alongside `M scripts/cache` at Step B time.

**Commit it explicitly** alongside `scripts/cache` in the LAST main-repo pointer-bump commit of the run (typically the ucoin pointer bump in §5.2, since anomalies most commonly surface during the ucoin batch). Name BOTH paths on the commit (pathspec-commit per §0.8 — never a bare `git commit` that would also sweep a parallel session's staged files):

```bash
git commit scripts/cache docs/anomaly_log.yml -m "data: bump cache pointer — … (+ anomaly log)"
```

If anomalies surface during the Numista batch (rare but possible — e.g. cache-invalidation alarm), include `docs/anomaly_log.yml` in §3.2's Numista pointer bump too.

If `git status` shows `M docs/anomaly_log.yml` but you DON'T recognise the changes as yours-from-this-run, that's a concurrent-session conflict per §0.8 — investigate, don't bundle.

---

## §2. Pick the next Numista batch

### §2.1. Read the audit + cache state

```bash
.venv/bin/python <<'EOF'
import json, pathlib
num_cache = pathlib.Path('scripts/cache/numista')
bo6 = json.loads(pathlib.Path('scripts/cache/numista/_BO6_audit_2026-05-20.json').read_text())
bo7 = json.loads(pathlib.Path('scripts/cache/numista/_BO7_audit_2026-05-24.json').read_text())

# Walk priorities in order across BOTH manifests. First bucket with
# uncached NIDs wins. BO.6 priorities first (DK/NO/SH), then BO.7
# (German states). Smallest-uncached-first within each manifest to
# maximise closure rate.
priorities = [
    # (manifest_label, audit, path_into_in_scope_buckets)
    ('BO.6', bo6, ('denmark', 'p0_pre_lovkompleks')),  # standards-continuity context [1396, 1513)
    ('BO.6', bo6, ('norway', 'p2')),                    # post-OOS-cleanup pool
    ('BO.6', bo6, ('norway', 'p4')),                    # small bucket, easy closure
    ('BO.6', bo6, ('norway', 'p3')),                    # largest BO.6 pool
    # BO.7 German states (added 2026-05-24) — small first for fast closures
    ('BO.7', bo7, ('saxe_lauenburg_duchy',)),           # 17
    ('BO.7', bo7, ('brunswick_calenberg',)),            # 13
    ('BO.7', bo7, ('brunswick_grubenhagen',)),          # 15
    ('BO.7', bo7, ('bremen_archbishopric',)),           # 21
    ('BO.7', bo7, ('oldenburg_grand_duchy',)),          # 40
    ('BO.7', bo7, ('osnabruck_bishopric',)),            # 60
    ('BO.7', bo7, ('oldenburg_county',)),               # 61
    ('BO.7', bo7, ('brunswick_wolfenbuttel_duchy',)),   # 75
    ('BO.7', bo7, ('brunswick_luneburg_celle',)),       # 117
    ('BO.7', bo7, ('brunswick_luneburg_calenberg',)),   # 118
    ('BO.7', bo7, ('bremen_free_imperial_city',)),      # 118
    ('BO.7', bo7, ('lubeck_free_hanseatic_city',)),     # 129
    ('BO.7', bo7, ('hessen_kassel_landgraviate',)),     # 256
    ('BO.7', bo7, ('hessen_kassel_electorate',)),       # 282
    ('BO.7', bo7, ('hamburg_hanseatic_city',)),         # 303
    ('BO.7', bo7, ('brunswick_wolfenbuttel_principality',)),  # 753, save for last
]
for label, audit, path in priorities:
    cur = audit['in_scope_buckets']
    for k in path:
        cur = cur.get(k) or {}
    nids = cur.get('in_scope_nids') or cur.get('gap_nids') or []
    if not nids:
        continue
    uncached = [n for n in nids if not (num_cache/f'{n}.json').exists()]
    if uncached:
        bucket_name = '/'.join(path)
        print(f'>>> Next Numista batch: {label} {bucket_name}, {len(uncached)} uncached, take first 5:')
        print(uncached[:5])
        break
else:
    print('!!! All Numista buckets closed (BO.6 + BO.7) — switch strategy or stop')
EOF
```

The script walks BO.6 first, then BO.7, picks the first priority with uncached NIDs, and prints the next 5 to fetch. When a manifest is fully closed (every bucket in its priority list at 100% cached), the loop falls through to the next manifest. The `else` clause on the for-loop fires only when BOTH manifests are exhausted.

### §2.2. Numista priority order

**Manifest A — BO.6 (`_BO6_audit_2026-05-20.json`): Denmark + Norway + SH cluster.** Status as of 2026-05-24: all DK/NO buckets at 100 % (✅ CLOSED). SH cluster: 67/67 (✅ CLOSED).

| Priority | Bucket | Era | Status |
|---|---|---|---|
| 1 | DK p0_pre_lovkompleks 1396-1513 | Erik of Pommern → John I (Hans) | ✅ **CLOSED** (20/20) |
| 2 | NO p2 1513-1657 | C2 Oslo → F3 early Speciedaler | ✅ **CLOSED** (88/88) |
| 3 | NO p4 1697-1814 | C5 late → F6 1813 | ✅ **CLOSED** (78/78) |
| 4 | NO p3 1657-1697 | F3 mid → C5 Kongsberg | ✅ **CLOSED** (200/200) |
| — | DK p1/p2/p3/p4 + SH cluster (older priorities) | — | ✅ **CLOSED** |

**Manifest B — BO.7 (`_BO7_audit_2026-05-24.json`): German states (Hanseatic cities + Welf territories + Hesse-Kassel + Oldenburg + Saxe-Lauenburg + Osnabrück + Bremen).** All German lands inside the mission window 1559-1914. Added 2026-05-24. Strategy: smallest-uncached-first to maximise per-batch closure rate; large pools (Hessen-Kassel, Hamburg, Brunswick-Wolfenbüttel principality) come last.

| Priority | Bucket | Era | In-scope NIDs | Strategy |
|---|---|---|---:|---|
| 5 | saxe_lauenburg_duchy | 1605-1815 (Saxe-Lauenburg) | 17 | First to close after BO.6 — small bucket |
| 6 | brunswick_calenberg | early Calenberg-Hannover | 13 | Small, single-batch closure |
| 7 | brunswick_grubenhagen | Brunswick-Grubenhagen line | 15 | Small, ~3 batches |
| 8 | bremen_archbishopric | Bremen ecclesiastical | 21 | ~5 batches |
| 9 | oldenburg_grand_duchy | post-1815 Oldenburg | 40 | ~8 batches |
| 10 | osnabruck_bishopric | Osnabrück Hochstift | 60 | ~12 batches |
| 11 | oldenburg_county | pre-1815 Oldenburg | 61 | ~13 batches |
| 12 | brunswick_wolfenbuttel_duchy | Wolfenbüttel pre-principality | 75 | ~15 batches |
| 13 | brunswick_luneburg_celle | Brunswick-Lüneburg-Celle line | 117 | ~24 batches |
| 14 | brunswick_luneburg_calenberg | Brunswick-Lüneburg-Calenberg | 118 | ~24 batches |
| 15 | bremen_free_imperial_city | Bremen civic | 118 | ~24 batches |
| 16 | lubeck_free_hanseatic_city | Lübeck civic | 129 | ~26 batches |
| 17 | hessen_kassel_landgraviate | Hesse-Kassel pre-1803 | 256 | ~52 batches |
| 18 | hessen_kassel_electorate | Hesse-Kassel 1803-1866 | 282 | ~57 batches |
| 19 | hamburg_hanseatic_city | Hamburg civic | 303 | ~61 batches |
| 20 | brunswick_wolfenbuttel_principality | Wolfenbüttel post-1735 | 753 | Largest BO.7 pool — save for last (~151 batches) |
| — | bremen_verden_swedish | Swedish Bremen-Verden | 13 | ✅ **CLOSED** (13/13) |

When a bucket cached count == in_scope_total, the picker in §2.1 automatically moves to the next priority. Cron runs do not need manual intervention.

**Special case — when DK p1/p2/p3/p4 or SH cluster have new gap NIDs** (e.g. user added URLs to a manifest), prioritise those FIRST. Re-read `_BO6_audit_2026-05-20.json` + `_BO6_gaps_manifest_2026-05-19.json` and compare against actual cache contents before defaulting to BO.7 buckets. Adjust the §2.1 picker temporarily by inserting the new BO.6 entries above the BO.7 block, OR set `priority_override` in `_harvest_handoff.json` (per §1.5.1).

**Note on `p0_pre_lovkompleks`** — this bucket holds Danish coinage from Erik of Pommern (1396-1439) through Hans / John I (1481-1513) — strictly speaking outside the project's 1514 mission anchor, but kept in scope as **standards-continuity context** for understanding what immediately preceded the Christian II 1514 four-act Lovkompleks. The 20 NIDs were user-curated from the Numista DK catalogue page 1 listing (`?e=danemark&st=1-2-3-47-154-5-54&cat=y&p=1&q=200&s=c&o=y`, sorted year ASC). Defensive sampling §7.5 does NOT need to fire here — every NID was hand-verified against the listing-page text before being added to `in_scope_nids` (no false-positive risk).

### §2.3. Fetch each NID

Numista URL pattern is **bare**: `https://en.numista.com/<NID>` works — no slug needed. (UCoin's slug pattern is different — see §4.3.)

For each NID in the batch (5 entries):

**A. Navigate + extract via Chrome MCP `browser_batch`:**

```javascript
// JS extractor — paste verbatim into javascript_tool, swap NID
(()=>{
  const out={id:NID, url:location.href, title:document.title};
  const rows=document.querySelectorAll('table tr');
  const data={};
  rows.forEach(r=>{
    const th=r.querySelector('th, td:first-child');
    const td=r.querySelectorAll('td');
    if(th && td.length>=1){
      const key=th.innerText.trim();
      const val=td[td.length-1].innerText.trim();
      if(key) data[key]=val;
    }
  });
  out._raw_rows=data;
  return out;
})()
```

**B. Parse the `_raw_rows` keys** into the save payload:

- `Issuer` → `country`
- `King` / `Ruler` → `ruler`
- `Value` → `denomination`
- `Years` / `Year` → parse `year_first` / `year_last`. **The Numista field has THREE distinct shapes — DO NOT collapse them:**
  - **Single year** «1532» → `year_first: 1532`, `year_last: 1532`, `year_list: null`
  - **Dash-form range** «1649-1670» → continuous range, every in-between year was struck → `year_first: 1649`, `year_last: 1670`, `year_list: null`. Use this when the separator is a dash / hyphen / en-dash with no commas.
  - **Comma-form discrete years** «1496, 1502» / «1592, 1593, 1595» → DISCRETE strike years, the in-between years were NOT struck → `year_first: <min>`, `year_last: <max>`, `year_list: [<each year>]`. Use this when the separator is a comma. The `year_list` field is REQUIRED on this shape — without it the seed builder collapses to a continuous range, inventing years that were never struck (§4 «source years are immutable» violation in reverse).
  - **Mixed form** «1591-1593, 1595» → split into `year_list: [1591, 1592, 1593, 1595]` AND set `year_first` / `year_last` to overall min / max. Comma form takes precedence — any comma in the field → discrete mode.
- `Composition` → `metal` (silver/gold/billon/copper based on text), `fineness` (parse `.875` / `0.875` / `(.156 silver)`)
- `Weight` → `weight_g` (strip `g`)
- `Diameter` → `diameter_mm` (strip `mm`)
- `Shape` → `shape`
- `Technique` → `technique`
- `References` → `references_text` (raw) + `references_list` (split by `, `)
- `Mint` → `mintmaster` (when text encodes mintmaster init), else leave null

**C. Save via heredoc:**

```bash
cat <<'EOF' | python3 /tmp/save_numista.py
{
  "id": NID,
  "url": "https://en.numista.com/NID",
  "title": "DK/NO/SH ... - Ruler year-range",
  "country": "Denmark|Norway|...",
  "ruler": "Frederik I|Christian IV|...",
  "denomination": "1 Speciedaler|½ Sølvgylden|...",
  "year_first": YYYY,
  "year_last": YYYY,
  "year_list": null,
  "metal": "silver|gold|billon|copper",
  "fineness": 0.NNN,
  "weight_g": NN.NN,
  "diameter_mm": NN,
  "shape": "Round|Round (irregular)|...",
  "technique": "Hammered|Milled|...",
  "references_text": "Hede# X, KM# Y, ...",
  "references_list": ["Hede# X", "KM# Y"],
  "_audit_context": "BO.6 batch <letter> — short description for grep-ability"
}
EOF
```

**`year_list` field encoding** (per the §2.3 B rule above):
- `year_list: null` — for single-year + dash-form-range entries (the in-between years were struck).
- `year_list: [1496, 1502]` — for comma-form discrete entries (verbatim list of struck years, ascending).

**D. Pace 31-60s:**

```bash
sleep $((RANDOM % 30 + 31)) && echo "pacing done"
```

### §2.4. Handle URL-open failure (404 / persistent-block / canonical mismatch)

> **Never frame an unreachable ID as «deleted».** A 404 from Numista or ucoin may mean the entry was renamed, merged, moved behind auth, temporarily withdrawn for editing, or genuinely removed — **the routine cannot tell which**. The user needs to inspect each case manually. Do NOT remove the ID from the audit's `gap_nids` list; just record the failure and move on.

**On any of these conditions:**
- HTTP page returns «Page Not Found» / 404 layout
- Cloudflare challenge survives a 90 s wait + retry
- `/tmp/save_ucoin.py` exits with code 2 (canonical-tid mismatch) twice in a row

**Do all of:**

1. **Do NOT save the cache file** (no `<id>.json` written).
2. **Do NOT delete or modify the audit's `gap_nids` entry** — the ID stays a retry candidate.
3. **Append a structured record** to `scripts/cache/<source>/_failed_open_ids.json`:

   ```json
   {
     "id": 117344,
     "ts": "2026-05-21T15:23:00Z",
     "url_tried": "https://en.numista.com/117344",
     "reason": "404_page_not_found",         // see vocabulary below
     "batch_label": "T",                       // the run that hit it
     "details": "<one-line context if any>"
   }
   ```

   `reason` vocabulary (use these stable strings):

   | `reason` | Trigger |
   |---|---|
   | `404_page_not_found` | HTTP/page-layout 404 (title «Page Not Found» / empty result block) |
   | `cloudflare_persistent` | CF challenge survives 90 s wait + retry |
   | `canonical_id_mismatch` | `save_ucoin.py` exit 2 on retry (URL redirected to different TID) |
   | `redirect_to_landing` | Page renders the issuer-landing instead of the per-coin record |
   | `dom_structure_unexpected` | Extractor JS returned `null` for all key fields (page changed shape?) |
   | `other` | Anything else; populate `details` with a sentence |

4. **Track in this run's handoff entry** — append the ID to `runs[].numista_batch.failed_open[]` (or `ucoin_batch.failed_open[]` accordingly).
5. **Continue with the next NID/TID in the batch** — do NOT halt. The batch's saved-count for the day will be smaller; that's the honest record.
6. **Surface in the end-of-run report (§8)** — the «Failed to open this run» section lists each failed ID + reason for user analysis.

**Append snippet — writes BOTH the raw `_failed_open_ids.json` log AND the persistent anomaly log:**

```python
.venv/bin/python <<EOF
import json, pathlib, sys
from datetime import datetime, timezone

# Step a) raw structured failure log (legacy + audit-trail)
p = pathlib.Path('scripts/cache/numista/_failed_open_ids.json')
arr = json.loads(p.read_text()) if p.exists() else []
ts_now = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
arr.append({
    "id": NID,
    "ts": ts_now,
    "url_tried": URL,
    "reason": REASON,                  # one of the vocabulary above
    "batch_label": BATCH_LABEL,
    "details": DETAILS_STRING_OR_EMPTY,
})
p.write_text(json.dumps(arr, indent=2, ensure_ascii=False) + '\n')

# Step b) persistent anomaly log — recurring failures get visibility for triage
# Stable id: url_open_failed:source=numista:id=<NID> (reason in detail, NOT key_dims —
# same broken ID across different failure reasons is one triage target, not many).
sys.path.insert(0, str(pathlib.Path('.').resolve()))
from scripts.lib import anomaly_log as al
al.record(
    type_="url_open_failed",
    key_dims={"source": "numista", "id": str(NID)},
    summary=f"numista NID {NID} fails to fetch (last reason: {REASON!r}); ID remains in audit gap_nids as retry candidate, cache file absent.",
    detail=f"Batch {BATCH_LABEL}: {REASON} — url {URL}. {DETAILS_STRING_OR_EMPTY}".strip(),
    affected_ids={"numista": [NID]},
    proposed_fix=(
        "Open URL in browser to determine status (renamed/merged/moved/withdrawn/removed). "
        "If verified OOS, reclassify into audit's oos_excluded_nids slot."
    ),
    batch_label=BATCH_LABEL,
    run_utc=ts_now,
    full_context={"reason": REASON, "url_tried": URL},
)
EOF
```

(For ucoin failures use `source="ucoin"` + path `scripts/cache/ucoin/_failed_open_ids.json` — same shape.)

**Why the dual write.** `_failed_open_ids.json` is raw append-only structured evidence (one line per attempt, never collapsed). The anomaly log is the curated triage view (one entry per broken ID, with `occurrence_count` showing chronicity + lifecycle). Both are needed: raw data for forensic detail, log for «what should the user actually look at».

**Auto-resolve on subsequent successful fetch.** When a later run's save script succeeds writing `scripts/cache/<source>/<id>.json` for an ID that previously had an active `url_open_failed:source=<source>:id=<id>` entry, the routine MUST close that anomaly:

```python
from scripts.lib import anomaly_log as al
import json, pathlib

# After a successful save_*.py call (cache file just written):
stable_id = f"url_open_failed:source={SOURCE}:id={ID_AS_STR}"
existing = al.get_by_id(stable_id, include_archived=False)  # active only
if existing:
    al.mark_resolved(
        stable_id,
        resolution=f"Auto-resolved: cache file <id>.json written successfully in batch {BATCH_LABEL}.",
        resolved_by="harvest-routine-auto",
    )
```

Place this snippet in the save loop right after each successful save script call (`/tmp/save_numista.py` exit 0 or `/tmp/save_ucoin.py` exit 0). If no active entry exists for the ID, the routine is a no-op — cheap, safe.

**Commit-message note (within the §3.1 commit body):**
«N#XXXXX failed to open this run (reason: <reason>); logged to _failed_open_ids.json AND anomaly_log (url_open_failed). NID remains in audit gap_nids — retried next run, auto-resolves on success.»

### §2.5. Handle Cloudflare challenge (transient, single-retry path)

When the page returns a Cloudflare interstitial («Just a moment…», «Checking your browser», DOM has `<div class="cf-browser-verification">`):
- Wait 90 s (`sleep 90`).
- Reload the same URL.
- **If the retry succeeds** → continue normally (save cache, log nothing special). If the routine wants to flag the event as a notable transient for handoff snapshot, use type `cloudflare_challenge_cleared` (handoff-only, NOT promoted to anomaly log per the §1.6.1 transient rule).
- **If the retry fails too** → apply §2.4 with `reason: cloudflare_persistent`. The dual write there will record both to `_failed_open_ids.json` AND to the persistent anomaly log as `url_open_failed:source=X:id=Y`. Also append to `scripts/cache/numista/_rate_limit_events.json` for cross-session pattern analysis. Skip this NID for this run.

---

## §3. Commit the Numista batch

### §3.1. Submodule step (Step A of PB-10)

> **Surgical-commit rule (per §0.8) applies here.** Stage ONLY the per-NID cache files you saved this run, by explicit path. Do NOT `git add numista/`, do NOT `git add .`, do NOT use any glob that could pick up unrelated NIDs.

**Pre-commit sanity check (mandatory):**

```bash
cd scripts/cache
git status --short                 # inspect what's dirty BEFORE staging
# Expected output: ONLY your batch's `?? numista/<nid>.json` lines.
# If you see ANY other modifications (ucoin files, other audit files,
# anything else), STOP — investigate before staging. A concurrent
# session may have written there.
```

**Then stage + commit:**

```bash
cd scripts/cache && git add numista/<nid1>.json numista/<nid2>.json numista/<nid3>.json numista/<nid4>.json numista/<nid5>.json && git status --short && git commit numista/<nid1>.json numista/<nid2>.json numista/<nid3>.json numista/<nid4>.json numista/<nid5>.json -m "$(cat <<'EOF'
Numista BO.6 batch <letter> — <bucket-name> (<N> NIDs)

<2-line description of what cluster this batch covers — ruler, era,
notable Fuß / metal pattern>

N#<nid1>  <country> <denom> <ruler> <years> (<refs>) <fineness>/<weight>g
N#<nid2>  …
N#<nid3>  …
N#<nid4>  …
N#<nid5>  …

<optional 1-line note: bucket closure status, e.g. "p1 progress: 134/139 (5 left)">

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

The interim `git status --short` between `add` and `commit` confirms the staged area contains ONLY your 5 NIDs — if it shows extra items in the «to be committed» section, abort the commit and unstage (`git reset HEAD <unwanted-file>`).

**Push the submodule now (still inside `scripts/cache`)** — submodule `main` is single-writer (only the routine writes the cache), so this is always a fast-forward:

```bash
git push origin main               # submodule push FIRST, before the superproject pointer (§0.7 order)
```

**Important:** after `cd scripts/cache && git commit && git push`, you are STILL inside `scripts/cache`. The next `cd` returns to the main repo for Step B.

### §3.2. Main-repo pointer bump (Step B of PB-10)

> **Surgical-commit rule (per §0.8) applies here.** Stage ONLY the literal path `scripts/cache` — never `git add .`, never `git add scripts/cache docs/`, never any combined path on the same `git add` line. The cache-pointer commit's ONLY job is to bump the submodule reference; if `docs/` or `assets/` or other paths changed, they belong in SEPARATE commits handled by SEPARATE actors (or this routine commits its cache-pointer first, then leaves the unrelated changes for the user to triage).

**Pre-commit sanity check (mandatory):**

```bash
cd /Users/serg/Documents/GitHub/munzfuss.github.io
git status --short
# Expected output:
#   M scripts/cache         # ← yours (submodule pointer)
#   (anything else)         # ← NOT yours — leave it alone in Step B
```

If `git status` shows additional modified / untracked files beyond `scripts/cache`, those are concurrent-session work. **DO NOT stage them**. Proceed with the surgical `git add scripts/cache` only.

**Then commit:**

```bash
cd /Users/serg/Documents/GitHub/munzfuss.github.io && git status --short && git commit scripts/cache -m "$(cat <<'EOF'
data: bump cache pointer — Numista BO.6 batch <letter> (<bucket>, <N> NIDs)

scripts/cache: <one-line description of what this slice contains>.
<closure note if any, e.g. "DK p1 1513-1617 now 139/139 — Phase 1 COMPLETE">

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

The interim `git status --short` between `add` and `commit` confirms only `scripts/cache` is in the staged column (typically shown as `M  scripts/cache` after staging — note the two spaces vs one). If you see any other path in the «Changes to be committed» area, abort and unstage.

**Push the superproject branch now (Step C of §0.7) — fast-forward of `harvest/auto`, never rejected:**

```bash
git rev-parse --abbrev-ref HEAD    # MUST print "harvest/auto" — if it says "main", you violated §0.1; checkout harvest/auto first
git push origin harvest/auto       # NEVER `git push origin main`
```

**Sanity check after the commit + push:**

```bash
git log -1 --stat                  # the commit MUST show 1 file changed (scripts/cache)
git log --oneline origin/harvest/auto..HEAD   # MUST be empty (commit pushed)
git status --short                 # routine-only clone → expected clean
```

If `git log -1 --stat` shows more than 1 file changed, you bundled something — execute the §0.8 self-recovery recipe. If `origin/harvest/auto..HEAD` is non-empty, the push didn't land — re-run it.

### §3.3. Unexpected dirty files in this clone

This clone is routine-only (§0.1), so in the steady state `git status` shows nothing but the routine's own writes. If you DO see unexpected modifications — e.g. a curator accidentally edited here instead of the curation clone, or a half-finished prior run left state — they are NOT the routine's to commit. Common spots:
- `docs/` (a stray edit, or handoff state)
- `data/**` (a curation edit made in the wrong clone)
- `assets/` / `scripts/maintenance/` (one-off work)

**Do NOT touch any of these.** Stage only `scripts/cache` (+ `docs/anomaly_log.yml` when the routine wrote anomalies) in Step B, by explicit pathspec. Leave everything else dirty and flag it in the end-of-run report so the curator can move the stray edit to the correct clone. If an unrelated edit accidentally lands in your commit, use the §0.8 self-recovery to split.

### §3.4. Integration into `main` — the CURATION clone's job (NOT the routine's)

> The routine NEVER merges `harvest/auto` into `main` and NEVER pushes the superproject `main` (§0.1). This section documents what the curator runs in the OTHER clone (`/Users/serg/projects/muentzfuesse`) when they decide to pull harvest changes — it is here so the routine's end-of-run report (§6.2 item 10) can quote the exact command, and so the model is documented in one place.

In the curation clone, no PR needed:

```bash
cd /Users/serg/projects/muentzfuesse
git fetch origin
git merge origin/harvest/auto      # clean: harvest files (cache pointer, docs/anomaly_log.yml) don't
                                   # overlap curation files (data/**). Use --ff-only when main hasn't
                                   # diverged and you want linear history.
git submodule update --init        # pull the submodule pointer to the merged state
git push origin main               # curation clone is the SOLE writer of main → no race
```

**The one file both sides touch is `docs/anomaly_log.yml`** (routine appends anomalies; curator may resolve them). If that conflicts on merge, union the entries — keep the routine's new entries AND the curator's status transitions (per PB-10's «Recovery from a `git pull` MERGE» resolution). All other harvest files never conflict with curation.

Because the routine keeps `harvest/auto` append-only (§0.1), each integration brings in exactly the commits added since the last merge; the branch is long-lived and never reset.

---

## §4. Pick the next ucoin batch

### §4.1. Read the audit + cache state

```bash
.venv/bin/python <<'EOF'
import json, pathlib
uc = pathlib.Path('scripts/cache/ucoin')
audit2 = json.loads(pathlib.Path('scripts/cache/ucoin/_BR_audit-2_2026-05-20.json').read_text())
audit3 = json.loads(pathlib.Path('scripts/cache/ucoin/_BR_audit-3_2026-05-22_hanseatic.json').read_text())
audit4 = json.loads(pathlib.Path('scripts/cache/ucoin/_BR_audit-4_2026-05-24.json').read_text())

# Walk priorities across THREE manifests in defined order. First bucket
# with uncached TIDs wins. BR-audit-2 (DK periods) → BR-audit-3
# (Hanseatic) → BR-audit-4 (German states). Smallest-first within each
# manifest to maximise closure rate.
def _get_audit2(key):
    v = audit2['NEW_GAPS_DISCOVERED'].get(key) or {}
    return v.get('gap_tids') or []

def _get_audit3(key):
    return (audit3['buckets'].get(key) or {}).get('gap_tids') or []

def _get_audit4(key):
    return (audit4['buckets'].get(key) or {}).get('gap_tids') or []

priorities = [
    # (manifest_label, getter, bucket_key)
    # BR-audit-2 — DK periods
    ('BR-2', _get_audit2, 'DK_p1115_Rigsdaler_1699-1749'),
    ('BR-2', _get_audit2, 'DK_p846_Rigsdaler_1750-1812'),
    ('BR-2', _get_audit2, 'DK_p647_Rigsbankdaler_1813-1854'),
    ('BR-2', _get_audit2, 'DK_p1147_Rigsdaler_1625-1699'),
    # BR-audit-3 — Hanseatic Hamburg + Lübeck (audit-3 added 2026-05-22)
    ('BR-3', _get_audit3, 'hamburg_p904'),                # 34 TIDs, 1713-1772
    ('BR-3', _get_audit3, 'hamburg_p903'),                # 45 TIDs, 1773-1872
    ('BR-3', _get_audit3, 'german_empire_p468_hamburg'),  # 12 TIDs, 1873-1914
    ('BR-3', _get_audit3, 'lubeck_p1205'),                # 45 TIDs, 1620-1716
    ('BR-3', _get_audit3, 'lubeck_p1204'),                # 36 TIDs, 1717-1797
    ('BR-3', _get_audit3, 'german_empire_p469_lubeck'),   #  6 TIDs, 1901-1914
    # BR-audit-4 — German states (audit-4 added 2026-05-24) — smallest first
    ('BR-4', _get_audit4, 'oldenburg_p658'),               #   4 TIDs
    ('BR-4', _get_audit4, 'bremen_p1194'),                 #  12
    ('BR-4', _get_audit4, 'oldenburg_p976'),               #  35
    ('BR-4', _get_audit4, 'bremen_p3067'),                 #  39
    ('BR-4', _get_audit4, 'brunswick_luneburg_p1088'),     #  46
    ('BR-4', _get_audit4, 'brunswick_wolfenbuttel_p1146'), #  47
    ('BR-4', _get_audit4, 'brunswick_wolfenbuttel_p1154'), #  47
    ('BR-4', _get_audit4, 'brunswick_wolfenbuttel_p3283'), #  55
    ('BR-4', _get_audit4, 'osnabruck_p2988'),              #  55
    ('BR-4', _get_audit4, 'osnabruck_p3057'),              #  55
    ('BR-4', _get_audit4, 'brunswick_luneburg_p1082'),     #  61
    ('BR-4', _get_audit4, 'hesse_kassel_p899'),            #  62
    ('BR-4', _get_audit4, 'brunswick_p905'),               #  77
    ('BR-4', _get_audit4, 'osnabruck_p2989'),              #  77
    ('BR-4', _get_audit4, 'bremen_p1195'),                 #  93
    ('BR-4', _get_audit4, 'brunswick_luneburg_p1087'),     #  95
    ('BR-4', _get_audit4, 'brunswick_wolfenbuttel_p1145'), # 108
    ('BR-4', _get_audit4, 'brunswick_luneburg_p1089'),     # 122
    ('BR-4', _get_audit4, 'brunswick_wolfenbuttel_p1153'), # 124
    ('BR-4', _get_audit4, 'hesse_kassel_p1292'),           # 130
    ('BR-4', _get_audit4, 'brunswick_wolfenbuttel_p3284'), # 141
    ('BR-4', _get_audit4, 'brunswick_luneburg_p1083'),     # 159
    ('BR-4', _get_audit4, 'hesse_kassel_p2945'),           # 220, largest BR-4 pool
]
for label, getter, key in priorities:
    tids = getter(key)
    if not tids:
        continue
    uncached = [t for t in tids if not (uc/f'{t}.json').exists()]
    if uncached:
        print(f'>>> Next ucoin batch: {label} {key}, {len(uncached)}/{len(tids)} uncached, take first 5:')
        print(uncached[:5])
        break
else:
    print('!!! ALL ucoin priorities CLOSED (BR-2 + BR-3 + BR-4) — declare harvest complete OR add new buckets to §4.2.')
    print('!!! Known unresolvable-via-ucoin gaps (paper-source needed):')
    for k, v in audit3.get('in_scope_gaps_unresolvable_via_ucoin', {}).items():
        print(f'!!!   {k}: {v}')
EOF
```

### §4.2. ucoin priority order

DK-period priorities (audit-2 tracked) — current state as of 2026-05-22:

| Priority | Bucket | Era | Status |
|---|---|---|---|
| 1 | DK p1115 1699-1749 | F4 → C6 Reichsdukatenfuß | ✅ **CLOSED** (59/59) |
| 2 | DK p846 1750-1812 | F5 → C7 → F6 early | ✅ **CLOSED** (54/54) |
| 3 | DK p647 1813-1854 | Helstaten F6 → C8 | ✅ **CLOSED** (48/48) |
| 4 | DK p1147 1625-1699 | C4 late + F3 + C5 | ✅ **CLOSED** (211/211 verified 2026-05-22 page-by-page re-enum) |

When all four DK-period buckets are at 100 % cached, fall through to the Hanseatic buckets below. The authority is `scripts/cache/ucoin/_BR_audit-3_2026-05-22_hanseatic.json` — produced by a fresh Chrome-MCP listing-page enumeration covering the mission window 1559-1914.

Hanseatic priorities (audit-3 tracked) — added 2026-05-22:

| Priority | Bucket key | Listing URL | TIDs | Scope |
|---|---|---|---|---|
| 5 | `hamburg_p904` | `country=hamburg&period=904` | 34 | Hanseatic Hamburg 1713-1772 (Dreiling, Sechsling, Schilling, Doppelschilling, Mark, Thaler, Dukat). Lands in V2 entity `hanseatic_hamburg`. |
| 6 | `hamburg_p903` | `country=hamburg&period=903` | 45 | Hanseatic Hamburg 1773-1872 (same denomination range + ducat continuity). Lands in V2 entity `hanseatic_hamburg`. |
| 7 | `german_empire_p468_hamburg` | `country=german_empire&period=468` | 12 | Reichsgoldmünzfuß Hamburg sub-period 1873-1914 (2/5/10/20-Mark gold + silver Reichsmark). Lands in V2 entity `hanseatic_hamburg` (post-1871 sub-track). |
| 8 | `lubeck_p1205` | `country=lubeck&period=1205` | 45 | Hanseatic Lübeck 1620-1716 (Schilling, Mark, Thaler, Goldgulden, Dukat). Lands in V2 entity `hanseatic_lubeck`. |
| 9 | `lubeck_p1204` | `country=lubeck&period=1204` | 36 | Hanseatic Lübeck 1717-1797 / continuity to 1801 (Schilling, Mark, Thaler, Dukat). Lands in V2 entity `hanseatic_lubeck`. |
| 10 | `german_empire_p469_lubeck` | `country=german_empire&period=469` | 6 | Reichsgoldmünzfuß Lübeck sub-period 1901-1914 (2/3/5/10-Mark silver + gold). Lands in V2 entity `hanseatic_lubeck` (post-1871 sub-track). |

**Total Hanseatic harvest scope**: 178 unique TIDs (179 entries; 2 lubeck cross-period dupes via 1716/17 boundary).

**Unresolvable-via-ucoin gaps** (audit-3 documented; need paper-source for completion):
- **Hamburg pre-1713**: ucoin has no period earlier than p904. Mission years 1559-1712 (154 yr) uncovered — paper-source candidate: Behrens 1905 *Münzen und Medaillen der Stadt Hamburg*.
- **Lübeck pre-1620**: ucoin has no period earlier than p1205. Mission years 1559-1619 (61 yr) uncovered — paper-source: Behrens 1905 *Münzen und Medaillen der Lübecker*, Lübeck-Bisthum cabinet catalogues.
- **Lübeck 1798-1870**: 73-year gap between p1204 (ends 1797) and p469 (starts 1901). Helstaten-era + pre-Reichsmünzfuß silver coinage uncovered — paper-source.

For priorities 1-4, the `gap_tids` lists in audit-2 manifest are authoritative — pick first 5 uncached, fetch, save.

For priorities 5-10, the `gap_tids` lists in audit-3 manifest are authoritative — same shape, same harvest logic. The `_url_index.json` already carries every enumerated TID's URL (auto-populated when audit-3 was written), so no per-period listing-page re-enumeration is needed before the cron job fetches.

**Manifest C — BR-audit-4 (`_BR_audit-4_2026-05-24.json`): German states (Bremen + Brunswick lines + Hesse-Kassel + Oldenburg + Osnabrück + Lauenburg).** All German lands inside the mission window 1559-1914. Added 2026-05-24. Smallest-first strategy.

| Priority | Bucket key | TIDs | Scope |
|---|---|---:|---|
| 11 | `oldenburg_p658` | 4 | Oldenburg Grand Duchy 1871-1918 (Reichsmark-era KM# 200/201/202/203) — single closure batch |
| 12 | `bremen_p1194` | 12 | Bremen civic small bucket |
| 13 | `oldenburg_p976` | 35 | Oldenburg county / Grand Duchy slice |
| 14 | `bremen_p3067` | 39 | Bremen civic |
| 15 | `brunswick_luneburg_p1088` | 46 | Brunswick-Lüneburg slice |
| 16 | `brunswick_wolfenbuttel_p1146` | 47 | Wolfenbüttel slice |
| 17 | `brunswick_wolfenbuttel_p1154` | 47 | Wolfenbüttel slice |
| 18 | `brunswick_wolfenbuttel_p3283` | 55 | Wolfenbüttel slice |
| 19 | `osnabruck_p2988` | 55 | Osnabrück Hochstift |
| 20 | `osnabruck_p3057` | 55 | Osnabrück Hochstift |
| 21 | `brunswick_luneburg_p1082` | 61 | Brunswick-Lüneburg slice |
| 22 | `hesse_kassel_p899` | 62 | Hesse-Kassel landgraviate |
| 23 | `brunswick_p905` | 77 | Brunswick (early/general) |
| 24 | `osnabruck_p2989` | 77 | Osnabrück Hochstift |
| 25 | `bremen_p1195` | 93 | Bremen civic |
| 26 | `brunswick_luneburg_p1087` | 95 | Brunswick-Lüneburg slice |
| 27 | `brunswick_wolfenbuttel_p1145` | 108 | Wolfenbüttel slice |
| 28 | `brunswick_luneburg_p1089` | 122 | Brunswick-Lüneburg slice |
| 29 | `brunswick_wolfenbuttel_p1153` | 124 | Wolfenbüttel slice |
| 30 | `hesse_kassel_p1292` | 130 | Hesse-Kassel electorate |
| 31 | `brunswick_wolfenbuttel_p3284` | 141 | Wolfenbüttel slice |
| 32 | `brunswick_luneburg_p1083` | 159 | Brunswick-Lüneburg slice |
| 33 | `hesse_kassel_p2945` | 220 | Hesse-Kassel largest pool — save for last |
| — | `bremen_p655` | 4 | ✅ **CLOSED** (4/4) |
| — | `brunswick_p654` | 1 | ✅ **CLOSED** (1/1) |
| — | `lauenburg_p1788` | 12 | ✅ **CLOSED** (12/12) |
| — | `osnabruck_p3047` | 13 | ✅ **CLOSED** (13/13) — closed b105 (2026-05-24) |

For priorities 11-33, the `gap_tids` lists in audit-4 manifest are authoritative — same harvest logic as audit-2 / audit-3 (listing-page slug fetch via §4.3, per-TID save via §4.3 C).

The §4.1 picker walks BR-2 → BR-3 → BR-4 in priority order and picks the first bucket with uncached TIDs. Cron runs do not need manual intervention when one manifest fully closes.

### §4.3. ucoin URL pattern — MUST use slug-form

> **§13.1 known-issue.** ucoin no longer serves the bare `/coin/<TID>/` shortcut — it returns "Page Not Found". The only working pattern is `/coin/<slug>/?tid=<TID>`.

For each batch, fetch the slug→TID map FIRST from the listing page (once per period per run), then iterate per-TID:

**A. Listing-page anchor extraction (once per period per run) — PAGINATION-AWARE.**

> **§13.2 known-issue — listing pages paginate.** Large periods (e.g. `bremen_p1195`, 93 TIDs) split across multiple listing pages at ~48 entries/page; a batch's target TIDs can sit on page 2+. A SINGLE-page extraction would report those targets as `MISSING` and falsely defer the whole batch (caught 2026-06-01, run IQ/255). So the extractor MUST iterate `&page=N` until every wanted TID resolves OR no further page link exists. (`page=1` may be implicit / omittable; `?country=…&period=…&page=2` is the next page.)

**Loop (operational):**

1. Navigate to page 1: `https://en.ucoin.net/catalog/?country=denmark&period=<NNNN>`
2. Run the extractor below — it returns this page's `tid_to_url` map AND `has_next` (whether a next-page link exists).
3. Merge this page's map into an accumulator; check whether all wanted TIDs are now resolved.
4. If any wanted TID is still unresolved AND `has_next` → navigate to `…&period=<NNNN>&page=<next>` and repeat from step 2.
5. Stop when all wanted resolve, OR `has_next` is false. Only TIDs still unresolved after the LAST page are genuinely `MISSING`.

Run via `javascript_tool` on EACH page:

```javascript
(()=>{
  const anchors=Array.from(document.querySelectorAll('a[href*="/coin/"][href*="tid="]'));
  const tid_to_url={};
  for(const a of anchors){
    const m=a.getAttribute('href').match(/\/coin\/([^/]+)\/?\?tid=(\d+)/);
    if(m){ tid_to_url[m[2]]='https://en.ucoin.net/coin/'+m[1]+'/?tid='+m[2]; }
  }
  // Detect a "next page" link (pagination control). ucoin renders page links as
  // anchors carrying &page=N; "next" exists if any page number exceeds the current one.
  const curM=location.href.match(/[?&]page=(\d+)/);
  const cur=curM?parseInt(curM[1]):1;
  const pageNums=Array.from(document.querySelectorAll('a[href*="page="]'))
    .map(a=>{const mm=a.getAttribute('href').match(/[?&]page=(\d+)/);return mm?parseInt(mm[1]):0;});
  const maxPage=pageNums.length?Math.max(...pageNums):cur;
  return {page:cur, has_next: maxPage>cur, tid_to_url};
})()
```

Then resolve the batch against the ACCUMULATED map across all visited pages:

```javascript
// after merging every page's tid_to_url into `acc`:
const wanted=['TID1','TID2','TID3','TID4','TID5'];  // batch TIDs
const result={}; for(const t of wanted){ result[t]=acc[t]||'MISSING'; }
return result;
```

A TID that is still `MISSING` after the last page genuinely isn't in the listing (deleted / moved) — apply §4.4 (log to `_failed_open_ids.json`, keep as retry candidate). Do NOT defer the whole batch just because targets sat beyond page 1.

**B. Per-TID fetch via `browser_batch`:**

```javascript
// Paste verbatim — swap TID, no other change
(()=>{
  const url=location.href;
  const tidM=url.match(/tid=(\d+)/);
  const canonical=tidM?parseInt(tidM[1]):null;
  const out={requested_tid:TID, url, title:document.title, canonical_tid:canonical, _verified:canonical==TID};
  const lines=document.body.innerText.split('\n');
  const data={};
  for(const line of lines){
    const idx=line.indexOf('\t');
    if(idx>0){
      const k=line.slice(0,idx).trim();
      const v=line.slice(idx+1).trim();
      if(k && !data[k]) data[k]=v;
    }
  }
  out._fields=data;
  out.issuer_text=data['Country'];
  out.ruler_text=data['Ruler'];
  out.period=data['Period'];
  out.years_text=data['Years']||data['Year'];
  out.denomination=data['Denomination']||data['Value'];
  out.value_text=data['Value']||data['Denomination'];
  out.currency=data['Currency'];
  out.composition_text=data['Composition'];
  out.weight_g=parseFloat((data['Weight (g)']||data['Weight']||'').replace(',','.').replace(/[^0-9.]/g,''))||null;
  out.diameter_mm=parseFloat((data['Diameter (mm)']||data['Diameter']||'').replace(',','.').replace(/[^0-9.]/g,''))||null;
  out.thickness_mm=parseFloat((data['Thickness (mm)']||data['Thickness']||'').replace(',','.').replace(/[^0-9.]/g,''))||null;
  out.shape=data['Shape'];
  out.edge_text=data['Edge type']||data['Edge'];
  out.technique=data['Technique']||data['Mint Technique'];
  out.mint_text=data['Mint']||data['Mint mark'];
  out.references_text=data['Number'];
  const fM=(data['Composition']||'').match(/(\d+\.\d+|\.\d+)/);
  out.fineness=fM?parseFloat(fM[1]):null;
  const yM=(data['Years']||data['Year']||'').match(/(\d{4})\D*(\d{4})?/);
  out.min_year=yM?parseInt(yM[1]):null;
  out.max_year=yM?(yM[2]?parseInt(yM[2]):parseInt(yM[1])):null;
  return out;
})()
```

**C. Save via heredoc:**

The extractor returns rich field structure. Map it into the saver's input:

```bash
cat <<'EOF' | python3 /tmp/save_ucoin.py
{
  "requested_tid": TID,
  "_verified": true,
  "canonical_tid": TID,
  "url": "https://en.ucoin.net/coin/<slug>/?tid=TID",
  "title": "...",
  "issuer_text": "Denmark|Norway|...",
  "ruler_text": "Frederick IV|Christian VI|...",
  "period": "Rigsdaler (1699 - 1749)",
  "years_text": "1700 - 1705",
  "min_year": YYYY,
  "max_year": YYYY,
  "denomination": "8 skilling",
  "value_text": "8 skilling",
  "currency": "Danish rigsdaler",
  "composition_text": "Silver 0.562|Silver (Billon)|Copper|Gold",
  "fineness": 0.NNN,
  "weight_g": N.NN,
  "diameter_mm": NN,
  "thickness_mm": N.NN,
  "shape": "Round|...",
  "edge_text": "Smooth|Reeded|...",
  "mint_text": "Copenhagen|Altona|...",
  "references_text": "KM# NNN",
  "references_list": ["KM# NNN"],
  "_audit_context": "BR batch <N> — <period-name> <ruler> <years> <denom> KM-NNN <fineness>/<weight>g <Scheide|Kurant>"
}
EOF
```

**D. Pace 31-60s** between fetches (same as Numista).

### §4.4. URL-open failure handling (ucoin — same rule as §2.4)

The ucoin-specific failure modes are:
- HTTP page returns «Page Not Found» (slug URL is invalid)
- Cloudflare challenge survives 90 s wait + retry
- `/tmp/save_ucoin.py` exits with code 2 — the canonical_tid in the URL ≠ requested_tid (ucoin redirected; rate-limit defence often does that)

**Apply §2.4's dual-write pattern exactly**, writing to BOTH:
1. `scripts/cache/ucoin/_failed_open_ids.json` (raw structured log — same schema as Numista: id / ts / url_tried / reason / batch_label / details)
2. `docs/anomaly_log.yml` via `al.record(type_="url_open_failed", key_dims={"source": "ucoin", "id": str(TID)}, ...)` — persistent triage view

The TID stays a retry candidate in the audit's `gap_tids` — never removed by this routine. **Auto-resolve hook same as §2.4**: when a later run's `/tmp/save_ucoin.py` exit 0 writes `<TID>.json`, the routine MUST call `al.mark_resolved("url_open_failed:source=ucoin:id=<TID>", resolution="...")` to close the active anomaly log entry. If no active entry exists for the TID, the call is a no-op.

Per-TID retry rule: for `canonical_id_mismatch`, wait 90 s and try ONCE; if the second attempt also returns exit-2, log `reason: canonical_id_mismatch` and continue. Do NOT loop indefinitely.

Track in handoff `runs[].ucoin_batch.failed_open[]`; surface in §8 end-of-run report.

---

## §5. Commit the ucoin batch

Same shape as §3 (PB-10 dance), but for ucoin files + the handoff bump (per §1.5.2). **Same surgical-commit discipline applies — see §0.8 and §3.1's pre-commit sanity-check pattern.**

### §5.1. Submodule step (Step A)

> **Surgical-commit rule (per §0.8) applies here.** Stage ONLY the per-TID ucoin cache files you saved this run + the handoff file, by explicit path. Do NOT `git add ucoin/`, do NOT `git add .`.

**Pre-commit sanity check (mandatory):**

```bash
cd scripts/cache
git status --short                 # inspect what's dirty BEFORE staging
# Expected output:
#   ?? ucoin/<tid1>.json … ?? ucoin/<tid5>.json   ← your 5 TIDs
#   M  _harvest_handoff.json                       ← your handoff update
# If anything ELSE shows up (numista files from another session, audit
# files, etc.), STOP and investigate. Stage only your files explicitly.
```

**Then stage + commit:**

```bash
cd scripts/cache && git add ucoin/<tid1>.json ucoin/<tid2>.json ucoin/<tid3>.json ucoin/<tid4>.json ucoin/<tid5>.json _harvest_handoff.json && git status --short && git commit ucoin/<tid1>.json ucoin/<tid2>.json ucoin/<tid3>.json ucoin/<tid4>.json ucoin/<tid5>.json _harvest_handoff.json -m "$(cat <<'EOF'
ucoin BR batch <N> — <period-name> <slice-description> (<M> TIDs)

<1-2 line description of what cluster this batch covers>

TID <tid1>  <ruler> <years> <denom> KM-NNN <fineness>/<weight>g <kind>
TID <tid2>  …
TID <tid3>  …
TID <tid4>  …
TID <tid5>  …

<period> progress: <cached>/<total> cached (<remaining> left).

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

The interim `git status --short` between `add` and `commit` should show exactly 6 entries staged (5 ucoin TID files + 1 handoff file). If you see more, abort and unstage extras with `git reset HEAD <unwanted-file>`.

**Push the submodule now (still inside `scripts/cache`)** — single-writer fast-forward, before the superproject pointer (§0.7 order):

```bash
git push origin main
```

### §5.2. Main-repo pointer bump (Step B) + push (Step C)

> **Surgical-commit rule (per §0.8) applies here.** Stage ONLY the literal path `scripts/cache`. Same anti-pattern list as §3.2 — never blanket adds, never combined paths.

**Pre-commit sanity check (mandatory):**

```bash
cd /Users/serg/Documents/GitHub/munzfuss.github.io
git status --short
# Expected:  M scripts/cache  (yours — submodule pointer)
# Anything else dirty → leave alone, NOT your concern.
```

**Then commit:**

```bash
cd /Users/serg/Documents/GitHub/munzfuss.github.io && git status --short && git commit scripts/cache -m "$(cat <<'EOF'
data: bump cache pointer — ucoin BR batch <N> (<period> <slice>, <M> TIDs)

scripts/cache: <1-line description>. <period> progress: <cached>/<total>
cached (<remaining> left).

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

**Then push the branch (Step C) — fast-forward of `harvest/auto`:**

```bash
git rev-parse --abbrev-ref HEAD    # MUST print "harvest/auto"
git push origin harvest/auto       # NEVER `git push origin main`
```

**Sanity check after commit + push:**

```bash
git log -1 --stat                             # MUST show 1 file changed (scripts/cache)
git log --oneline origin/harvest/auto..HEAD   # MUST be empty (pushed)
```

If more than 1 file changed, you bundled — execute §0.8 self-recovery to split.

---

## §5.5. IKMK batch (Berlin Münzkabinett API)

Third source per run. IKMK Berlin (`ikmk.smb.museum`) is openly-
licensed (CC BY-SA 4.0 text + PDM 1.0 LOD ids; see
`docs/IKMK_HARVEST.md` §«Why this is OK to scrape (unlike Numista)»).
Different mechanics from Numista / ucoin:

- **No per-NID URL like Numista**; the search returns a list of
  IKMK-MDS-IDs, which then have JSON endpoints
  (`/object?id=<mds_id>&download=json_ext`).
- **Pre-existing harvest**: 7000+ records already cached as of
  2026-05-26 (`scripts/cache/ikmk/<mds_id>.json`); manifest at
  `scripts/cache/ikmk/_manifest.json` lists all known IDs across
  query buckets.
- **One-shot driver**: `scripts/fetch_ikmk.py` handles both
  discovery (search queries) and per-ID fetch.
- **No Cloudflare**: plain `urllib` works. Polite pacing built into
  the driver (0.5 s between fetches).

### §5.5.1. Batch shape

**200 new fetches per run.** IKMK is NOT subject to the 5-per-batch
Cloudflare cap that bounds Numista / ucoin — it is a plain `urllib`
museum JSON API with an openly-licensed reuse contract and **no
observed rate limit** (`docs/IKMK_HARVEST.md` §«Per-run batch size»
documents a 500-entry safe cap). We use **200/run** as a generous,
politeness-margined slice: at 0.5 s pacing ≈ 100 s wall-time, well
within one routine slot, and it clears the post-discovery in-scope
backlog in a handful of runs instead of hundreds. The driver's
`--limit N` counts only NEW cache writes (already-cached IDs skipped
without counting).

```bash
.venv/bin/python scripts/fetch_ikmk.py fetch --limit 200
```

This walks the manifest (`_manifest.json::ids` — already title-scoped
at discovery, see §5.5.2), skipping any IDs whose `<id>.json` already
exists and any in `oos_excluded_mds_ids`, fetching the next 200
uncached in-scope IDs, and stopping. (If a 429/503 ever fires, fall
back per `docs/IKMK_HARVEST.md` §«Throttle-recovery protocol».)

### §5.5.2. Pre-batch check — manifest freshness

Manifest is the list of IDs to fetch. If the manifest doesn't cover
the entities currently consumed by V2 location pages, re-discover
to expand it.

```bash
# How many IDs in manifest vs cached vs query coverage:
.venv/bin/python <<'EOF'
import json, pathlib
m = json.load(open('scripts/cache/ikmk/_manifest.json'))
cached = len(list(pathlib.Path('scripts/cache/ikmk').glob('[0-9]*.json')))
total = len(m['ids'])
gap = total - cached
print(f'manifest IDs: {total}  cached: {cached}  uncached: {gap}')
print(f'discover queries: {len(m["queries"])}  fetched_at: {m.get("fetched_at")}')
EOF
```

**When to re-discover** (run `scripts/fetch_ikmk.py discover`):

1. **uncached < 20** — about to run out of work; re-discover to top up
   the manifest with potentially-new IDs (IKMK adds records slowly,
   so usually 0-50 new appear per discovery pass).
2. **`fetched_at` older than 30 days** — periodic refresh in case
   IKMK published new records or updated existing.
3. **New entity added to project scope** — extend `QUERIES` list in
   `scripts/fetch_ikmk.py` first, then discover. As of 2026-05-26 the
   `QUERIES` list covers all V2 location-page consumed entities:
   royal_holstein / gottorp_duchy / danish_realm / danish_norway /
   sub-duchies (Sonderburg / Norburg-Plön / Glücksburg) /
   holstein_schauenburg_county (Stadthagen / Bückeburg / Rinteln /
   Hessisch Oldendorf) / schauenburg_pinneberg / rantzau_county /
   hanseatic_hamburg / hanseatic_lubeck / fuerstbisthum_luebeck /
   erzbisthum_bremen_verden / landgrafschaft_hessen_kassel /
   hochstift_osnabrueck / grafschaft_oldenburg /
   herzogtum_braunschweig_lueneburg / herzogtum_sachsen_lauenburg.

Discover is heavier (one HTTP POST per query, ~90 queries → ~90 s).
Don't run it every batch — only when the freshness rules above
trigger.

**Discovery is title-scoped (2026-05-30).** `discover()` reads the
`view=table` result list (which carries each record's title) and keeps
an ID only if its issuer-prefix is a known German/Scandinavian/HRE
issuer OR unknown (default-keep); it drops prefixes in the curated OOS
set `scripts/fetch_ikmk_oos_title_prefixes.json` (ancient Greek/Roman/
oriental cities, Islamic dynasties, foreign countries) that are NOT in
the empirical cached-keep set. So the manifest `ids` is already mostly
in-scope — fetch batches don't burn slots classifying obvious ancient/
foreign noise. The per-record entity filter (`_is_in_entity_scope`)
stays the final precise gate at fetch (it sees mint country + object
type, which the title alone cannot). `discover()` preserves the
accumulated `oos_excluded_mds_ids` skip-set across re-runs. Regenerate
the drop-set file from the purge data when scope changes (provenance
note in the file header).

### §5.5.3. Fetch the batch

```bash
.venv/bin/python scripts/fetch_ikmk.py fetch --limit 200
```

Expected output: «reached --limit 200; stopping. fetched=200 skipped=N
errors=0 (Xs).»

### §5.5.4. Commit the IKMK batch — PB-10 dance (Step A + Step B)

Same two-step dance as Numista (§3) and ucoin (§5):

```bash
# Step A — submodule commit
cd scripts/cache
ls -la ikmk/ | grep -E "^\-rw" | grep "\.json" | head -5  # confirm the 5 new JSONs are there
git add ikmk/<each-of-the-5-mds-ids>.json    # explicit paths, NEVER `git add ikmk/`
git status --short                            # confirm exactly 5 files staged
# Pathspec on commit too (§0.8 primary guard) — bare commit would sweep
# the shared index incl. a parallel session's staged files:
git commit ikmk/<each-of-the-5-mds-ids>.json -m "IKMK batch — <N> mds_ids (<entity-or-query-bucket>)"
git push origin main                          # submodule push FIRST (§0.7 order); single-writer fast-forward
```

Step A commit-message format: name the per-run label («IKMK batch
N»), the count, AND the dominant entity / query the batch fed (e.g.
«IKMK batch C — 5 mds_ids (holstein_schauenburg_county)» when the
5 IDs all came from queries that route to that entity). When the
batch crosses multiple buckets, name the dominant 2 — e.g. «IKMK
batch D — 5 mds_ids (royal_holstein + gottorp_duchy)».

```bash
# Step B — main-repo pointer bump (pathspec-commit; scripts/cache is
# tracked, so no `git add` needed — pathspec alone is race-proof)
cd /Users/serg/Documents/GitHub/munzfuss.github.io
git status --short                            # confirm only `scripts/cache (new commits)`
git commit scripts/cache -m "data: bump cache pointer — IKMK batch <N> (<bucket>, 5 mds_ids)"
# Step C — push the branch (NEVER `git push origin main`)
git rev-parse --abbrev-ref HEAD               # MUST print "harvest/auto"
git push origin harvest/auto
```

### §5.5.5. Skip conditions

Skip the IKMK batch this run when:

- **uncached = 0** AND last discover < 30 days → IKMK is fully
  harvested for current scope; nothing to do. Log «IKMK: skipped
  (fully harvested)» in the end-of-run report.
- **discover failed** (network / Cloudflare on `quick_search`) → log
  «IKMK: skipped (discover failed)» and continue to §6.
- **All 5 fetches errored** (consecutive HTTP errors) → suggests
  rate-limit or outage; log + skip remaining.

The IKMK batch is NOT a hard requirement for the run — Numista
and ucoin batches drive coverage; IKMK is supplementary museum-
catalogue enrichment. If skipped, just note in the end-of-run
report's «Push state» line.

### §5.5.6. Per-run labeling

IKMK batches use letter labels matching Numista's cadence so the
audit's «Δ this run» columns can attribute correctly. Track
the last-used label in `scripts/cache/_harvest_handoff.json::ikmk_last_label`
(creates field if missing). Increment alphabetically each run that
actually fetches.

---

## §5.6. §CI dual-denomination legend HARVEST (evidence-only — routine writes cache, never data)

> **Scope per §0.5.** §CI was originally written as a curation task
> (fetch a legend, THEN decide a nominal, THEN edit `data/v2/final`). Under the
> branch model that is forbidden: the routine harvests EVIDENCE into the cache;
> it does NOT interpret the evidence and does NOT touch `data/**`. The nominal
> decision is a separate curation step (below). When `priority_override` has
> `task: "§CI"`, run an evidence batch BEFORE the normal Numista/ucoin fronts.
> (As of 2026-06-01 the override is PARKED in `parked_curation_tasks` — re-activate
> it into `priority_override` only when you want the routine collecting §CI evidence.)

**The routine's half (HARVEST — cache only):**

- **Work-list:** `docs/cg_dual_denomination_verify.json` — 82 coins whose
  `nominal` carries two FULL denominations («4 Mark = 1 Krone»,
  «2 Krone (8 Mark)», «16 Rigsbankskilling = 5 Schilling Courant», …).
  Track progress in `_harvest_handoff.json::ci_evidence_ids` (list; create
  if missing) so each run picks the next ~8 unharvested entries.
- **Per coin** — fetch the actual coin legend via **Chrome MCP** (IKMK
  `ikmk.smb.museum`, danskmoent.dk, or the Numista per-coin page in Chrome).
  **Do NOT use the Numista API** (budget-bound per CLAUDE.md «Numista API budget»).
- **Record RAW evidence only — no verdict, no interpretation.** Append to the
  cache sidecar `scripts/cache/_ci_legend_evidence.json` (a list; create if
  missing), one record per coin:

  ```json
  {
    "coin_ref": "<entity>:<coin_id>",
    "current_nominal": "4 Mark = 1 Krone",
    "obverse_legend": "<verbatim legend text, or empty>",
    "reverse_legend": "<verbatim legend text, or empty>",
    "legible": true,
    "source_url": "https://ikmk.smb.museum/object?id=...",
    "harvested_at": "<UTC ISO>"
  }
  ```
  Record the legend **verbatim** as read from the coin. Do NOT decide
  «dual vs single», do NOT set or edit `nominal`, do NOT move anything to
  `note`. If the legend is illegible/undated, set `legible: false` and leave
  the legend strings empty — that is itself the evidence. Add the coin to
  `ci_evidence_ids`.
- This sidecar is a submodule cache write — it rides the run's normal
  cache commit (PB-10), exactly like `_failed_open_ids.json` / `_rate_limit_events.json`.

**The curation half (DECISION + DATA — NOT the routine; interactive / curation session):**

Reading the cached evidence, a curation session applies the nominal decision via
`_source_errata` on the coin (seed or final) — NOT by free-hand editing `nominal`:
  - legend shows **BOTH** denominations (genuinely dual-inscribed, e.g. the
    Rigsbankskilling Phase-2 dual face) → KEEP the dual `nominal`; no errata.
  - legend shows **ONE** → add `_source_errata: [{field: nominal, printed: "<current>",
    correct: "<inscribed denom>", reason: "<source> legend reads '<X>' only; '<Y>'
    is editorial equivalent", curator: <name>}]` + move the equivalent into `note`.
    `apply_source_errata` (seed_merge.py §CN) overwrites `nominal` LAST in the build,
    so it wins over the foundation-immutable value and survives regen — no DF1
    resolution needed.
  - illegible → leave as-is; record the gap.
  Cite the harvested legend in the coin `note`/`sources` per §5.

When `ci_evidence_ids` covers all 82, the routine's §CI harvest is done — clear
`priority_override` (or leave parked) and hand off to curation for the errata pass.

---

## §6. Render the coverage tables

After both batches commit, output BOTH tables in the exact format below. This is the user-facing deliverable; everything else above is plumbing.

### §6.1. Compute current numbers (with per-row Δ for THIS run)

The script accepts THREE id-list inputs at the TOP — fill them with the exact NIDs / TIDs / mds_ids you just saved in this run's Numista batch + ucoin batch + IKMK batch. The script then renders ALL THREE source tables (Numista BO.6 + BO.7, ucoin BR-audit-2 + BR-audit-3 + BR-audit-4, IKMK by query bucket) with a **«Δ this run»** column that tallies how many of those just-added IDs landed in each period/bucket.

If a batch was deferred (Cloudflare blocked, NID returned 404 and was logged to `_failed_open_ids.json` per §2.4 / §4.4) or skipped (IKMK per §5.5.5), DO NOT include it in the list — only IDs whose `<id>.json` was actually written this run.

```bash
.venv/bin/python <<'EOF'
import json, pathlib

# ============================================================
# FILL THESE IN at the start of each rendering call:
# ============================================================
NIDS_THIS_RUN = [82133, 82384, 98983, 99000, 50496, 55887, 55888]  # Numista batch
TIDS_THIS_RUN = [94070, 94098, 94099, 94100, 94101]                # ucoin batch
IKMK_IDS_THIS_RUN = [18201589, 18201591, 18201596, 18201699, 18201701]  # IKMK batch (empty list [] if skipped per §5.5.5)
NUMISTA_BATCH_LABEL = 'N'                                          # e.g. 'N', 'O', 'P'
UCOIN_BATCH_LABEL = '29'                                           # e.g. '29', '30', '31'
IKMK_BATCH_LABEL = 'J'                                             # alphabetical letter, matching Numista cadence (§5.5.6)
# ============================================================

def fmt_delta(n):
    return f'**+{n}**' if n > 0 else '—'

# === ucoin per-period ===
uc_cache = pathlib.Path('scripts/cache/ucoin')
audit = json.loads((uc_cache/'_BR_audit-2_2026-05-20.json').read_text())

UCOIN_PERIODS = [
    # (display_name, era, total, period_key_or_None_for_static_closed)
    ('DK p2940 Speciedaler 1582-1624', 'C4 pre-Kipper', 83, None),
    ('DK p1147 Rigsdaler 1625-1699', 'C4 late + F3 + Christian V', 211, None),
    ('DK p2995 HG-Rendsburg 1716-1720', 'Holstein-Gottorp under F4', 4, None),
    ('DK p1115 Rigsdaler 1699-1749', 'F4 → C6', 59, 'DK_p1115_Rigsdaler_1699-1749'),
    ('DK p846 Rigsdaler 1750-1812', 'F5 → C7 → F6 early', 54, 'DK_p846_Rigsdaler_1750-1812'),
    ('DK p647 Rigsbankdaler 1813-1854', 'Helstaten (F6 → C8)', 48, 'DK_p647_Rigsbankdaler_1813-1854'),
    ('DK p646 Rigsdaler rigsmønt 1854-1873', 'F7 → C9', 13, None),
    ('DK p374 Christian IX 1873-1906', 'Krone-era memorials', 9, None),
    ('DK p373 Frederik VIII 1906-1912', 'Krone-era full reign', 7, None),
    ('DK p220 Christian X 1912-1947', 'in-scope 1912-1914', 7, None),
    ('NO p2939 Glückstadt 1617-1773', 'DK-rule Glückstadt mint', 50, None),
    ('NO p2399 Speciedaler 1648-1699', 'F3 + C5', 153, None),
    ('NO p2400 Speciedaler 1699-1745', 'F4 + C6', 23, None),
    ('NO p1041 Rigsdaler 1746-1812', 'F5 → F6', 32, None),
    ('NO p883 Rigsbankdaler 1813-1815', 'NO under DK 1813-1814', 2, None),
    ('SH duchies Speciesbank 1787-1839', 'Speciesbank-era SH', 15, None),
]

# Per-row Δ for ucoin: tally how many TIDS_THIS_RUN landed in this period's gap_tids list.
# Static-closed periods (key=None) cannot receive deltas in this routine — they're already done.
tids_set = set(str(t) for t in TIDS_THIS_RUN)
ucoin_unmatched_tids = set(tids_set)  # track which TIDs we found a home for

print(f'### ucoin — per-period detailed coverage (post batch {UCOIN_BATCH_LABEL})')
print()
print(f'| # | Period | Era | Total | Cached | Gap | % | Δ b{UCOIN_BATCH_LABEL} | Status |')
print('|---|---|---|---:|---:|---:|---:|---:|---|')
total_in_scope = total_cached = total_delta = 0
closed_count = 0
for i, (name, era, total, key) in enumerate(UCOIN_PERIODS, 1):
    delta = 0
    if key and key in audit['NEW_GAPS_DISCOVERED']:
        v = audit['NEW_GAPS_DISCOVERED'][key]
        if 'gap_tids' in v:
            period_tids = set(str(t) for t in v['gap_tids'])
            uncached = sum(1 for t in v['gap_tids'] if not (uc_cache/f'{t}.json').exists())
            cached = total - uncached
            delta = len(period_tids & tids_set)
            ucoin_unmatched_tids -= period_tids
        else:
            cached = v.get('cached', 0)
    else:
        cached = total  # static-closed
    gap = total - cached
    pct = round(100 * cached / total) if total else 0
    status = '✅ CLOSED' if gap == 0 else ('⏳ untouched' if cached == 0 else '🔵 open')
    if delta > 0 and gap == 0:
        status = f'🎉 CLOSED! (b{UCOIN_BATCH_LABEL})'
    elif delta > 0:
        status = f'🔵 batch {UCOIN_BATCH_LABEL} here'
    if gap == 0: closed_count += 1
    total_in_scope += total
    total_cached += cached
    total_delta += delta
    print(f'| {i} | {name} | {era} | {total} | {cached} | {gap} | {pct}% | {fmt_delta(delta)} | {status} |')

gap = total_in_scope - total_cached
pct = round(100 * total_cached / total_in_scope)
print(f'| **TOTAL** | | | **{total_in_scope}** | **{total_cached}** | **{gap}** | **{pct}%** | **{fmt_delta(total_delta)}** | **{closed_count}/16 closed** |')

if ucoin_unmatched_tids:
    print()
    print(f'> ⚠ TIDs not matched to any tracked period: {sorted(ucoin_unmatched_tids)} '
          '— check audit-2 manifest; may be a new period that needs adding to UCOIN_PERIODS.')

# === Numista per-bucket ===
print()
print(f'### Numista — per-bucket detailed coverage (BO.6 v3, post batch {NUMISTA_BATCH_LABEL})')
print()
print(f'| # | Bucket | Era | In-scope | Cached | Gap | % | Δ batch {NUMISTA_BATCH_LABEL} | Status |')
print('|---|---|---|---:|---:|---:|---:|---:|---|')

num_audit = json.loads(pathlib.Path('scripts/cache/numista/_BO6_audit_2026-05-20.json').read_text())
num_cache = pathlib.Path('scripts/cache/numista')

NUMISTA_BUCKETS = [
    ('DK p0 pre-Lovkompleks (1396-1513)', 'Erik of Pommern → Christopher of Bavaria → C1 → John I (Hans)', ('denmark', 'p0_pre_lovkompleks')),
    ('DK p1 (1513-1617)', 'C2/C3/F1/F2 + C4 early', ('denmark', 'p1')),
    ('DK p2 (1617-1671)', 'C4 Kipper/Glückstadt/Gottorp + F3', ('denmark', 'p2')),
    ('DK p3 (1671-1791)', 'C5 Speciedaler → C7 Trade', ('denmark', 'p3')),
    ('DK p4 (1791-1914)', 'F6 → C10', ('denmark', 'p4')),
    ('NO p2 (1513-1657)', 'C2 Oslo → F3 early', ('norway', 'p2')),
    ('NO p3 (1657-1697)', 'F3 mid → C5 Kongsberg', ('norway', 'p3')),
    ('NO p4 (1697-1814)', 'C5 late → F6 1813', ('norway', 'p4')),
    ('SH cluster (5 issuers)', 'SH-danish_duchies + Gottorp + Glückstadt + Lübeck-Bish + HS-Pinneberg', None),
]

# SH-cluster from gaps manifest
gm = json.loads(pathlib.Path('scripts/cache/numista/_BO6_gaps_manifest_2026-05-19.json').read_text())
sh_all_nids = set()
for v in gm['sh_cluster_gaps'].values():
    sh_all_nids.update(v)
sh_total = len(sh_all_nids)
sh_cached = sum(1 for n in sh_all_nids if (num_cache/f'{n}.json').exists())

nids_set = set(NIDS_THIS_RUN)
numista_unmatched_nids = set(nids_set)

total_in_scope = total_cached = total_delta = 0
closed_count = 0
for i, (name, era, key) in enumerate(NUMISTA_BUCKETS, 1):
    delta = 0
    if key is None:  # SH cluster
        total = sh_total
        cached = sh_cached
        bucket_nids = sh_all_nids
    else:
        country, page = key
        info = num_audit['in_scope_buckets'][country][page]
        total = info['in_scope_total']
        nids = info.get('in_scope_nids') or info.get('gap_nids') or []
        bucket_nids = set(nids)
        if 'gap_nids' in info:
            uncached = sum(1 for n in nids if not (num_cache/f'{n}.json').exists())
            cached = total - uncached
        else:
            cached = sum(1 for n in nids if (num_cache/f'{n}.json').exists())
    delta = len(bucket_nids & nids_set)
    numista_unmatched_nids -= bucket_nids
    gap = total - cached
    pct = round(100 * cached / total) if total else 0
    status = '✅ CLOSED' if gap == 0 else ('⏳ untouched' if cached == 0 else '🔵 open')
    if delta > 0 and gap == 0:
        status = f'🎉 CLOSED! (batch {NUMISTA_BATCH_LABEL})'
    elif delta > 0:
        status = f'🔵 batch {NUMISTA_BATCH_LABEL} here'
    if gap == 0: closed_count += 1
    total_in_scope += total
    total_cached += cached
    total_delta += delta
    print(f'| {i} | {name} | {era} | {total} | {cached} | {gap} | {pct}% | {fmt_delta(delta)} | {status} |')

gap = total_in_scope - total_cached
pct = round(100 * total_cached / total_in_scope)
print(f'| **TOTAL** | | | **{total_in_scope}** | **{total_cached}** | **{gap}** | **{pct}%** | **{fmt_delta(total_delta)}** | **{closed_count}/{len(NUMISTA_BUCKETS)} closed** |')

if numista_unmatched_nids:
    print()
    print(f'> ⚠ NIDs not matched to any tracked bucket: {sorted(numista_unmatched_nids)} '
          '— check audit + gaps manifest; may be off-bucket or freshly-discovered scope.')

# === Numista BO.7 — German states per-issuer (added 2026-05-24) ===
print()
print(f'### Numista BO.7 — per-issuer coverage (German states, post batch {NUMISTA_BATCH_LABEL})')
print()
print(f'| # | Issuer | Total | Cached | Gap | % | Δ batch {NUMISTA_BATCH_LABEL} | Status |')
print('|---|---|---:|---:|---:|---:|---:|---|')

bo7_audit = json.loads(pathlib.Path('scripts/cache/numista/_BO7_audit_2026-05-24.json').read_text())

bo7_total_in_scope = bo7_total_cached = bo7_total_delta = 0
bo7_closed = 0
bo7_active = 0
bo7_issuer_order = [
    'saxe_lauenburg_duchy', 'brunswick_calenberg', 'brunswick_grubenhagen',
    'bremen_archbishopric', 'bremen_verden_swedish', 'oldenburg_grand_duchy',
    'osnabruck_bishopric', 'oldenburg_county', 'brunswick_wolfenbuttel_duchy',
    'brunswick_luneburg_celle', 'brunswick_luneburg_calenberg',
    'bremen_free_imperial_city', 'lubeck_free_hanseatic_city',
    'hessen_kassel_landgraviate', 'hessen_kassel_electorate',
    'hamburg_hanseatic_city', 'brunswick_wolfenbuttel_principality',
]
for i, issuer in enumerate(bo7_issuer_order, 1):
    info = bo7_audit['in_scope_buckets'].get(issuer) or {}
    nids = info.get('in_scope_nids') or info.get('gap_nids') or []
    total = info.get('in_scope_total', len(nids))
    if total == 0:
        continue
    bo7_active += 1
    bucket_nids = set(nids)
    cached = sum(1 for n in nids if (num_cache/f'{n}.json').exists())
    delta = len(bucket_nids & nids_set)
    numista_unmatched_nids -= bucket_nids
    gap = total - cached
    pct = round(100 * cached / total) if total else 0
    status = '✅ CLOSED' if gap == 0 else ('⏳ untouched' if cached == 0 else '🔵 open')
    if delta > 0 and gap == 0:
        status = f'🎉 CLOSED! (batch {NUMISTA_BATCH_LABEL})'
    elif delta > 0:
        status = f'🔵 batch {NUMISTA_BATCH_LABEL} here'
    if gap == 0: bo7_closed += 1
    bo7_total_in_scope += total
    bo7_total_cached += cached
    bo7_total_delta += delta
    print(f'| {i} | {issuer} | {total} | {cached} | {gap} | {pct}% | {fmt_delta(delta)} | {status} |')

bo7_gap = bo7_total_in_scope - bo7_total_cached
bo7_pct = round(100 * bo7_total_cached / bo7_total_in_scope) if bo7_total_in_scope else 0
print(f'| **TOTAL** | | **{bo7_total_in_scope}** | **{bo7_total_cached}** | **{bo7_gap}** | **{bo7_pct}%** | **{fmt_delta(bo7_total_delta)}** | **{bo7_closed}/{bo7_active} closed** |')

# === ucoin BR-audit-4 — German states per-bucket (added 2026-05-24) ===
print()
print(f'### ucoin BR-audit-4 — per-bucket coverage (German states, post batch {UCOIN_BATCH_LABEL})')
print()
print(f'| # | Bucket | Total | Cached | Gap | % | Δ b{UCOIN_BATCH_LABEL} | Status |')
print('|---|---|---:|---:|---:|---:|---:|---|')

br4_audit = json.loads(pathlib.Path('scripts/cache/ucoin/_BR_audit-4_2026-05-24.json').read_text())

br4_total_in_scope = br4_total_cached = br4_total_delta = 0
br4_closed = 0
br4_active = 0
br4_bucket_order = [
    # Smallest-first within BR-audit-4 (matches §4.1 picker order).
    'bremen_p655', 'brunswick_p654', 'lauenburg_p1788', 'osnabruck_p3047',  # already-closed first for visual baseline
    'oldenburg_p658', 'bremen_p1194', 'oldenburg_p976', 'bremen_p3067',
    'brunswick_luneburg_p1088', 'brunswick_wolfenbuttel_p1146',
    'brunswick_wolfenbuttel_p1154', 'brunswick_wolfenbuttel_p3283',
    'osnabruck_p2988', 'osnabruck_p3057', 'brunswick_luneburg_p1082',
    'hesse_kassel_p899', 'brunswick_p905', 'osnabruck_p2989',
    'bremen_p1195', 'brunswick_luneburg_p1087', 'brunswick_wolfenbuttel_p1145',
    'brunswick_luneburg_p1089', 'brunswick_wolfenbuttel_p1153',
    'hesse_kassel_p1292', 'brunswick_wolfenbuttel_p3284',
    'brunswick_luneburg_p1083', 'hesse_kassel_p2945',
]
for i, bkey in enumerate(br4_bucket_order, 1):
    info = br4_audit['buckets'].get(bkey) or {}
    # BR-4 buckets carry `enumerated_total` (NOT `in_scope_total`); oos-split
    # buckets (e.g. osnabruck_p3057) also carry `in_scope_total`. After a
    # cached_count refresh (scripts/maintenance/refresh_audit_cached_counts.py)
    # `gap_tids` holds ONLY the uncached TIDs and `cached_count`/`cached_tids`
    # are accurate. So compute total from in_scope_total → enumerated_total →
    # (gap ∪ cached); read `cached` from cached_count; NEVER fall back to
    # len(gap_tids) (that equals the uncached count post-refresh and drops
    # fully-cached buckets / undercounts — the §6.1 regression after the
    # 2026-05-30 refresh).
    gap_tids = [str(t) for t in (info.get('gap_tids') or [])]
    cached_tids = [str(t) for t in (info.get('cached_tids') or [])]
    all_tids = set(gap_tids) | set(cached_tids)
    total = info.get('in_scope_total') or info.get('enumerated_total') or len(all_tids)
    if total == 0:
        continue
    br4_active += 1
    cached = info.get('cached_count', len(cached_tids))
    delta = len(all_tids & tids_set)
    ucoin_unmatched_tids -= all_tids
    gap = total - cached
    pct = round(100 * cached / total) if total else 0
    status = '✅ CLOSED' if gap == 0 else ('⏳ untouched' if cached == 0 else '🔵 open')
    if delta > 0 and gap == 0:
        status = f'🎉 CLOSED! (b{UCOIN_BATCH_LABEL})'
    elif delta > 0:
        status = f'🔵 batch {UCOIN_BATCH_LABEL} here'
    if gap == 0: br4_closed += 1
    br4_total_in_scope += total
    br4_total_cached += cached
    br4_total_delta += delta
    print(f'| {i} | {bkey} | {total} | {cached} | {gap} | {pct}% | {fmt_delta(delta)} | {status} |')

br4_gap = br4_total_in_scope - br4_total_cached
br4_pct = round(100 * br4_total_cached / br4_total_in_scope) if br4_total_in_scope else 0
print(f'| **TOTAL** | | **{br4_total_in_scope}** | **{br4_total_cached}** | **{br4_gap}** | **{br4_pct}%** | **{fmt_delta(br4_total_delta)}** | **{br4_closed}/{br4_active} closed** |')

# === IKMK — per-query-bucket coverage (added 2026-05-27) ===
# IKMK's manifest groups mds_ids by query name (e.g. "Braunschweig",
# "Kopenhagen"). Same mds_id can appear in multiple buckets (Welf-
# dynasty cross-refs etc.), so per-bucket totals include duplicates;
# the **grand total** uses unique mds_id counts from the manifest's
# top-level `ids` field.
print()
print(f'### IKMK — per-query-bucket coverage (post batch {IKMK_BATCH_LABEL})')
print()
print(f'| # | Query bucket | Total | Cached | Gap | % | Δ b{IKMK_BATCH_LABEL} | Status |')
print('|---|---|---:|---:|---:|---:|---:|---|')

ikmk_cache = pathlib.Path('scripts/cache/ikmk')
ikmk_manifest = json.loads((ikmk_cache/'_manifest.json').read_text())
ikmk_ids_set = set(str(i) for i in IKMK_IDS_THIS_RUN)
ikmk_unmatched_ids = set(ikmk_ids_set)

# Render only non-empty buckets, sorted by gap descending (work-remaining
# first so the reader sees where the next batches should go). Closed
# buckets (gap=0, total>0) appear at the bottom of the active set.
ikmk_buckets_raw = []
for qname, ids in ikmk_manifest['queries'].items():
    total = len(ids)
    if total == 0:
        continue  # empty queries (returned no hits) skip the table entirely
    bucket_ids = set(str(i) for i in ids)
    cached = sum(1 for i in ids if (ikmk_cache/f'{i}.json').exists())
    delta = len(bucket_ids & ikmk_ids_set)
    ikmk_unmatched_ids -= bucket_ids
    ikmk_buckets_raw.append((qname, total, cached, delta, bucket_ids))

# Sort: rows with delta > 0 first (so this run's contributions are visible),
# then open rows by gap desc, then closed rows.
def _ikmk_sort_key(row):
    qname, total, cached, delta, _ = row
    gap = total - cached
    if delta > 0:
        return (0, -delta, -gap, qname)
    if gap > 0:
        return (1, -gap, qname)
    return (2, -total, qname)
ikmk_buckets_raw.sort(key=_ikmk_sort_key)

ikmk_closed = ikmk_active = 0
ikmk_bucket_total_sum = ikmk_bucket_cached_sum = ikmk_bucket_delta_sum = 0
for i, (qname, total, cached, delta, _bucket_ids) in enumerate(ikmk_buckets_raw, 1):
    ikmk_active += 1
    gap = total - cached
    pct = round(100 * cached / total) if total else 0
    status = '✅ CLOSED' if gap == 0 else ('⏳ untouched' if cached == 0 else '🔵 open')
    if delta > 0 and gap == 0:
        status = f'🎉 CLOSED! (b{IKMK_BATCH_LABEL})'
    elif delta > 0:
        status = f'🔵 batch {IKMK_BATCH_LABEL} here'
    if gap == 0: ikmk_closed += 1
    ikmk_bucket_total_sum += total
    ikmk_bucket_cached_sum += cached
    ikmk_bucket_delta_sum += delta
    print(f'| {i} | {qname} | {total} | {cached} | {gap} | {pct}% | {fmt_delta(delta)} | {status} |')

# Per-row totals include cross-bucket duplicates — the bucket-sum row
# is informational only. The authoritative TOTAL uses the manifest's
# unique-id pool.
ikmk_unique_total = len(ikmk_manifest['ids'])
ikmk_unique_cached = len(list(ikmk_cache.glob('[0-9]*.json')))
ikmk_unique_gap = ikmk_unique_total - ikmk_unique_cached
ikmk_unique_pct = round(100 * ikmk_unique_cached / ikmk_unique_total) if ikmk_unique_total else 0
ikmk_unique_delta = len(ikmk_ids_set & set(str(i) for i in ikmk_manifest['ids']))
print(f'| _bucket-sum_ | _includes cross-bucket dupes_ | _{ikmk_bucket_total_sum}_ | _{ikmk_bucket_cached_sum}_ | _{ikmk_bucket_total_sum - ikmk_bucket_cached_sum}_ | _—_ | _{fmt_delta(ikmk_bucket_delta_sum)}_ | _—_ |')
print(f'| **TOTAL (unique)** | | **{ikmk_unique_total}** | **{ikmk_unique_cached}** | **{ikmk_unique_gap}** | **{ikmk_unique_pct}%** | **{fmt_delta(ikmk_unique_delta)}** | **{ikmk_closed}/{ikmk_active} buckets closed** |')

# Re-print unmatched warnings AFTER all 4 tables have had a chance to claim IDs.
if numista_unmatched_nids:
    print()
    print(f'> ⚠ NIDs not matched to BO.6 OR BO.7 buckets: {sorted(numista_unmatched_nids)} '
          '— check audits / gaps manifest; may be off-bucket or freshly-discovered scope.')
if ucoin_unmatched_tids:
    print()
    print(f'> ⚠ TIDs not matched to BR-audit-2 OR BR-audit-4 buckets: {sorted(ucoin_unmatched_tids)} '
          '— check audits; BR-audit-3 Hanseatic buckets are tracked separately and may need adding here.')
if ikmk_unmatched_ids:
    print()
    print(f'> ⚠ IKMK mds_ids not matched to any non-empty query bucket: {sorted(ikmk_unmatched_ids)} '
          '— ID was saved this run but not present in any of the manifest queries. Check `_manifest.json` '
          'or re-run `scripts/fetch_ikmk.py discover` to refresh.')
EOF
```

**Note on the rendering scope.** The script above renders FIVE tables: BR-audit-2 (DK periods, 16 rows), BO.6 (DK+NO+SH, 9 rows), BO.7 (German states, 17 rows), BR-audit-4 (German states, 27 rows), IKMK (per-query-bucket, variable rows — only non-empty buckets are shown, sorted with this-run's buckets first then by gap descending). It does NOT render BR-audit-3 Hanseatic per-bucket (those 6 buckets sit between BR-2 and BR-4 in coverage but are tracked separately for now — surface them in the §8 headline-numbers line if needed). When a manifest is fully closed, its table still renders (all-CLOSED rows) — keeps the report shape stable across runs so the reader sees the same structure regardless of which fronts are active.

**Note on the IKMK bucket-sum vs. unique-total distinction.** IKMK query buckets often overlap — a Welf-dynasty piece can satisfy both «Braunschweig» and «Braunschweig-Lüneburg» queries — so summing per-bucket totals double-counts. The script emits TWO total rows: an italic `_bucket-sum_` row that mirrors the per-row arithmetic (informational, for catching scope drift between manifest and cache) and the bold authoritative `**TOTAL (unique)**` row that uses the manifest's top-level `ids` list as the unique pool. **Always cite the unique-total** in §8 headline numbers; the bucket-sum is debugging-only.

**Implementation note.** Maintain `NIDS_THIS_RUN`, `TIDS_THIS_RUN`, and `IKMK_IDS_THIS_RUN` as live variables during the batch flow:
- After each successful `save_numista.py` call, append the NID to a running list (e.g. `RUN_NIDS=()` Bash array, or just track in your scratchpad).
- After each successful `save_ucoin.py` call (exit code 0), append the TID.
- After each successful IKMK fetch (extract the mds_ids written by `scripts/fetch_ikmk.py fetch --limit 200` via `git status --short` on the submodule — the new `?? ikmk/<mds_id>.json` lines name the IDs added this run).
- Skip 404 cases and exit-2 (canonical-tid fail) cases — those are not «processed this run».
- When IKMK was skipped per §5.5.5, set `IKMK_IDS_THIS_RUN = []` and the table still renders for shape stability.
- At rendering time, paste the final lists into the script's top.

The unmatched-IDs warning at the bottom guards against scope drift — if a TID/NID/mds_id you saved doesn't show up in any tracked bucket, the audit needs updating OR the ID was saved outside the routine's intended scope.

### §6.2. Required output sections (in this order)

1. **Pre-tables one-liner** — what this run added, framed as a delta.
   Example: «Batch run 2026-05-21 14:00 UTC: Numista batch P added **+5** to NO p2; ucoin batch 31 added **+5** to DK p1115; IKMK batch J added **+5** mds_ids. All committed local.»

2. **ucoin BR-audit-2 coverage table** — 16 rows + TOTAL (DK periods), with the `Δ b<N>` column populated from §6.1's script.

3. **Numista BO.6 coverage table** — 9 rows + TOTAL (DK p0–p4 + NO p2–p4 + SH cluster).

4. **Numista BO.7 coverage table** — 17 rows + TOTAL (German states), populated by the §6.1 BO.7 block.

5. **ucoin BR-audit-4 coverage table** — 27 rows + TOTAL (German states), populated by the §6.1 BR-audit-4 block.

6. **IKMK per-query-bucket coverage table** — variable rows (one per non-empty query in `_manifest.json::queries`) + `_bucket-sum_` informational row + **TOTAL (unique)** row using the manifest's deduped `ids` pool. Sorted with this-run's contributions at the top, then open buckets by gap descending, then closed buckets. Populated by the §6.1 IKMK block.

   When a coverage manifest has zero activity AND zero gap (all-CLOSED, no delta this run), the table still renders — it stays in the report for shape stability across runs, so the reader sees the same five sections every time. The §6.1 script handles all five uniformly.

   **IKMK skipped per §5.5.5?** The table still renders against the existing manifest — `IKMK_IDS_THIS_RUN = []` means every row shows `Δ = —`. Don't omit the table just because no fetches happened; the static state IS the report.

7. **Full coverage inventory (ALL harvests — past + planned)** — run `.venv/bin/python scripts/maintenance/harvest_coverage.py` and include its three sections verbatim (defined in §6.5). This is the standing per-entity / per-specimen coverage across EVERY source ever harvested — distinct from the per-batch delta tables above, which only track the active enumeration fronts and so silently omit anything harvested outside a tracked bucket (notably the entire IKMK cache, which has no seed builder). It prints (a) the entity × source classified-specimen matrix, (b) each source's cached-vs-seeded footprint, (c) IKMK cache detail. Always include it, every run — it is the answer to «what locations + how many specimens do we actually hold, total».

8. **Headline numbers** (each line ends with a parenthetical run-delta — include each manifest with non-trivial state, omit ones that are 100 %-closed and untouched this run):
   - Numista BO.6 (DK + NO + SH) — total cached, remaining (Δ this run: +X)
   - Numista BO.7 (German states) — total cached, remaining (Δ this run: +X)
   - ucoin BR-audit-2 (DK periods) — total cached, remaining (Δ this run: +X)
   - ucoin BR-audit-3 (Hanseatic Hamburg + Lübeck) — total cached, remaining (Δ this run: +X)
   - ucoin BR-audit-4 (German states) — total cached, remaining (Δ this run: +X)
   - IKMK (museum catalogue) — total cached / unique pool, remaining (Δ this run: +X) — cite the **unique** pool, NOT the bucket-sum
   - Grand cumulative cached across all manifests (Δ this run: +X Numista, +Y ucoin, +Z IKMK = +W total)

9. **Failed-to-open this run** — list IDs that the routine could NOT fetch (404 / persistent Cloudflare / canonical mismatch / DOM unexpected). Pulled from this run's `runs[-1].numista_batch.failed_open[]` + `runs[-1].ucoin_batch.failed_open[]` + `_failed_open_ids.json` tail. **Omit the section entirely if both lists are empty** (the typical clean run).
   Shape per entry: `N#<id> — <reason> — <one-line context>`. Example:
   > ### ⚠ Failed to open this run (4)
   > - **Numista**:
   >   - N#117344 — `404_page_not_found` — Erik of Pommern Skærv per audit, but bare URL returns "Page Not Found". May be moved / renamed; needs manual check.
   >   - N#475742 — `redirect_to_landing` — URL bounced to /coins page instead of /475742 per-coin record.
   > - **ucoin**:
   >   - TID 94158 — `canonical_id_mismatch` — slug URL resolved to TID 94159 after redirect (twice in a row).

   Tells the user exactly which IDs to inspect manually. The IDs **remain in audit gap_nids/gap_tids** — they're retry candidates next hour. Routine does NOT mark them «dead».

10. **Push state + integration hint** — the routine already pushed this run (autonomous, per §0.1). State what landed and how the curator integrates:
    - «Pushed: submodule `main` + superproject `harvest/auto` (N commits this run).» Compute N via `git log --oneline origin/harvest/auto@{1}..origin/harvest/auto | wc -l` or simply the count committed this run.
    - One-line integration command for the curation clone (§3.4): «To pull into the project: `cd /Users/serg/projects/muentzfuesse && git fetch && git merge origin/harvest/auto && git submodule update --init` (no PR).»
    - If anything is UN-pushed (a push failed), say so explicitly and name the repo + branch — that's a bug to fix, not a «ready locally» state.

11. **Recommended next batches** — top 3 priorities for the NEXT hourly run, picking from whichever manifest's smallest open bucket is next per the §2.1 / §4.1 picker order (Numista + ucoin); for IKMK suggest «next 5 from manifest uncached pool» unless re-discovery is due per §5.5.2.

### §6.3. Status emoji legend (use consistently)

- ✅ `CLOSED` — cached == in_scope (gap = 0), no delta this run
- 🎉 `CLOSED! (batch <N>)` — closed THIS run (delta > 0 AND gap == 0) — auto-emitted by the script
- 🔵 `batch <N> here` — partially advanced THIS run (delta > 0 AND gap > 0) — auto-emitted
- 🔵 `open` — partial coverage, untouched this run
- ⏳ `untouched` — 0 cached, untouched this run
- ⚠ stragglers — special note for «closed except for N residual NIDs» edge cases (manual annotation)

### §6.4. Delta semantics — what counts

- A TID/NID/mds_id counts toward the delta only if its `<id>.json` was **written to disk this run** (save script exit 0 for Numista/ucoin; `fetched=` count in the `fetch_ikmk.py` summary for IKMK).
- IDs logged to `_failed_open_ids.json` are NOT included in delta (no file written; per §2.4 / §4.4). They surface in the §6.2 «Failed to open this run» section instead — visibility for the user without inflating progress numbers.
- Canonical-tid mismatch (save_ucoin exit 2) is NOT included.
- Cloudflare deferrals — IDs that you decided to retry next hour — are NOT included.
- IKMK batches skipped per §5.5.5 (already fully harvested / discover failed / consecutive errors) contribute zero delta — `IKMK_IDS_THIS_RUN = []`.
- Re-saves of an already-cached file (idempotent rewrite with same content) ARE counted as 0 delta for that period — the file already existed, the run didn't add new scope.

This keeps the delta semantics tight: **«items the routine demonstrably added to the cache this hour»**, nothing aspirational.

### §6.5. Full coverage inventory script (`harvest_coverage.py`)

`scripts/maintenance/harvest_coverage.py` (read-only, no writes) prints the **standing** coverage across ALL sources — independent of the active-front batch tables in §6.1–§6.2. Run it every end-of-run (§6.2 item 7) and include its output verbatim. Three sections:

- **A. Entity × source matrix** — `data/v2/seed/<source>/<entity>.yml` coin counts ARE the classified, in-scope, per-entity specimen coverage for the six seed-builder sources (bruun / galster / hede / numismaster / numista / ucoin). One row per political entity, one column per source, with row + column totals. This is the canonical «which locations, how many specimens».
- **B. Per-source footprint** — for every cache source: cached record files vs specimens seeded into V2. Flags any source cached but NOT enumerated by entity (no seed builder).
- **C. IKMK detail** — IKMK has no generic seed builder, so its cache is invisible to §A. Shows manifest-enumerated / actually-cached / **enumerated-but-unfetched gap** + by-mint-country + by-era. IKMK records expose mint COUNTRY (not city), so a precise per-entity split is impossible without a real builder — tracked as TODO §CH.

**Why this is separate from §6.1–§6.2.** Those per-batch tables answer «how is the *current* re-enumeration front progressing» — they are keyed by harvest bucket/period and silently omit any specimen harvested outside a tracked bucket. §6.5 answers «what locations and how many specimens do we actually hold, total, across every harvest past and planned». Both views are required; neither subsumes the other. Snapshot (2026-05-30): 6 368 classified specimens across 20 entities; IKMK 1 778 cached / 0 seeded / 4 498 enumerated-but-unfetched.

---

## §7. Error recovery

### §7.1. Pre-commit hook failure

`/Users/serg/Documents/GitHub/munzfuss.github.io/.githooks/pre-commit` runs `build.py --validate-only` + prose audits. If a commit fails:
- The cache files are still added but NOT committed.
- Inspect the failure (usually unrelated to cache changes — could be stale prose lint on existing YAMLs).
- Re-run the commit. If still failing AND the failure is in an unrelated file, use `--no-verify` ONLY if the user explicitly said so in chat. Otherwise leave the batch uncommitted and report at end of run.

### §7.2. Detached HEAD after submodule commit

The §1 preflight checks out submodule `main` (`git checkout main && git reset --hard origin/main`), so commits should land ON `main` — detached HEAD should not occur. If it does anyway (preflight skipped), recover before Step B:

```bash
cd scripts/cache
git status                         # confirms "HEAD detached at <sha>"
git checkout main                  # switch to main branch
git reset --hard <sha-of-new-commit>  # bring the new commit onto main
cd /Users/serg/Documents/GitHub/munzfuss.github.io
```

Then proceed with Step B (`git commit scripts/cache -m …` — pathspec-commit per §0.8).

### §7.3. Push rejected (unexpected — single-writer branches)

With the branch model (§0.1) both push targets are single-writer: submodule `main` (only the routine writes cache) and superproject `harvest/auto` (only the routine writes it). So `git push` should ALWAYS fast-forward. A `! [rejected] (fetch first)` means the single-writer assumption broke — almost certainly **a second harvest run overlapped in this clone** (cron fired before the previous run finished). Recover by fast-forwarding onto the peer run's commits:

```bash
# Submodule (origin main rejected):
cd scripts/cache
git fetch origin
git rebase origin/main             # replay THIS run's cache commits on top of the overlapping run's
# Per-NID/TID JSONs from two runs never touch the same file (different IDs), so this is conflict-free.
git push origin main
cd /Users/serg/Documents/GitHub/munzfuss.github.io

# Superproject (origin harvest/auto rejected):
git fetch origin
git rebase origin/harvest/auto     # replay this run's pointer bump on top
git push origin harvest/auto
```

The ONLY file two overlapping runs can both touch is `docs/anomaly_log.yml` (both append) and `scripts/cache/_harvest_handoff.json` (both write). If either conflicts, union the entries (keep both runs' new records) and continue. If resolution feels risky, leave it uncommitted and report — the curator resolves manually. (To avoid overlap entirely, ensure the cron interval exceeds a run's wall-clock, or add a lockfile guard.)

### §7.4. Chrome MCP disconnected

If `list_connected_browsers` returns empty or the user's extension is off:
- Do NOT fall back to WebFetch / Apify for ucoin — both fail Cloudflare 403.
- For Numista, WebFetch + Apify may work for sparse single-NID lookups but rate-limit fast.
- Best move: report «Chrome MCP unavailable this hour — skipped harvest run» and exit cleanly. Do NOT half-execute.

### §7.5. Defensive sampling — pre-harvest scope check (mandatory)

> **Trigger.** Any bucket whose `gap_nids` (Numista) or `gap_tids` (ucoin) list contains entries that have NEVER been touched in a prior batch — i.e. the routine is about to harvest «fresh» scope it hasn't previously verified.

The audit manifests were enumerated via client-side regex on listing-page HTML, and historical evidence (SOURCES.md §13.1 «year-regex false-positives») shows the enumeration occasionally mis-classifies post-1914 modern coins as in-scope. Before mass-harvesting any «fresh» gap list, do this **once**:

1. **Sample 1-2 NIDs from the head of the gap list** via Chrome MCP `browser_batch [navigate + minimal extractor]`. The extractor only needs `king`, `years`, `value` — no save call, no API budget.
2. **Cross-check the result against the mission scope** declared in `CLAUDE.md` §«Mission temporal scope» (German lands 1559-1914, Danish-realm 1514-1914).
3. **If sample falls outside mission window** (e.g. ruler is Margrethe II / Frederik IX / any post-1914 monarch):
   - DO NOT save any cache files from this gap.
   - Report the finding as an **Anomaly** in the end-of-run report (§8) with the sampled NID + ruler + year.
   - **Switch to the next priority bucket** for this run.
   - Open a tracking note: «BO.6 v3 audit's `<country>/<page>` gap suspect — sample N#XXX = <ruler> <years> OOS. Cleanup required before resuming this bucket.»
   - The user (or a maintenance follow-up) decides whether to reclassify the entire gap list as OOS or whether it's a mixed bucket.

**Why this matters.** The routine is autonomous; a silent harvest of OOS NIDs pollutes the cache with modern coins that the project will never use, AND silently inflates the «cached» counts in the coverage tables. The defensive sample costs ~30 s + 2 page loads — cheaper than every downstream consumer of `scripts/cache/numista/` having to filter OOS noise.

**When NOT to sample.** Buckets currently in-flight (e.g. NO p2 with 7 NIDs already cached from batch N) are already validated — the prior batches confirmed scope. Sample only when opening a fresh bucket whose first batch hasn't run yet.

**Example real case (2026-05-21, DK p4):**
The audit manifest's `denmark/p4` listed 20 «gap» NIDs as in-scope. The hourly routine sampled N#1461 → got «10 Kroner Margrethe II 2001-2002» → recognised OOS → switched to NO p2 for that hour's Numista batch → reported anomaly. Follow-up Chrome-MCP samples (N#1462, N#14840, N#137792) confirmed all 20 are Margrethe II 2001-2010. The audit was then patched to move the 20 NIDs into a new `oos_excluded_nids` slot with audit-trail reason; DK p4 now correctly shows 104/104 closed. Documented in SOURCES.md §13.1 as known-issue case.

---

## §8. End-of-run report template

Final response to the user follows this exact structure. The Δ-columns in all five tables come straight from §6.1's script output — do not hand-compute, the script already filled them.

```markdown
**Batch run <UTC timestamp>**: Numista batch <letter> added **+<N>** to <bucket>; ucoin batch <NN> added **+<M>** to <period>; IKMK batch <letter> added **+<K>** mds_ids (or «skipped per §5.5.5» with reason). All committed local (total **+<N+M+K>** entries this run).

### ucoin — per-period detailed coverage (post batch <NN>)

<16-row + TOTAL table from §6.1 — includes Δ b<NN> column>

### Numista — per-bucket detailed coverage (BO.6 v3, post batch <letter>)

<9-row + TOTAL table from §6.1 — includes Δ batch <letter> column>

### Numista BO.7 — per-issuer coverage (German states, post batch <letter>)

<17-row + TOTAL table from §6.1 — includes Δ batch <letter> column>

### ucoin BR-audit-4 — per-bucket coverage (German states, post batch <NN>)

<27-row + TOTAL table from §6.1 — includes Δ b<NN> column>

### IKMK — per-query-bucket coverage (post batch <letter>)

<variable-row table (one per non-empty query) + _bucket-sum_ row + TOTAL (unique) row from §6.1 — includes Δ b<letter> column. ALWAYS rendered, even when IKMK was skipped per §5.5.5 (all Δ cells will read «—»). Cite the **TOTAL (unique)** line in the headline numbers below, NOT the bucket-sum.>

### Headline numbers post-batches <letter> + <NN> + <ikmk-letter>

- **Numista BO.6** (DK + NO + SH): <cached>/<total>, **<remaining> left** (Δ this run: +<n1>)
- **Numista BO.7** (German states): <cached>/<total>, **<remaining> left** (Δ this run: +<n2>)
- **ucoin BR-audit-2** (DK periods): <cached>/<total>, **<remaining> left** (Δ this run: +<n3>)
- **ucoin BR-audit-3** (Hanseatic): <cached>/<total>, **<remaining> left** (Δ this run: +<n4>)
- **ucoin BR-audit-4** (German states): <cached>/<total>, **<remaining> left** (Δ this run: +<n5>)
- **IKMK** (museum catalogue, unique pool): <cached>/<total>, **<remaining> left** (Δ this run: +<n6>)
- **Grand cumulative**: <numista_cum> Numista + <ucoin_cum> ucoin + <ikmk_cum> IKMK = **<sum>** cached cumulatively (Δ this run: **+<n1+n2>** Numista, **+<n3+n4+n5>** ucoin, **+<n6>** IKMK = **+<total>** entries)

  Omit any line whose manifest is 100 %-closed AND untouched this run, to keep the headline list focused on active work.

<!-- §6.2 item 8 — Failed to open this run. Include ONLY when at least one failed_open[] is non-empty: -->
### ⚠ Failed to open this run (<K>)

- **Numista**:
  - N#<id> — `<reason>` — <one-line context>
  - …
- **ucoin**:
  - TID <id> — `<reason>` — <one-line context>
  - …

IDs remain in audit `gap_nids`/`gap_tids` — retried next run. Manual review: open each URL in browser to determine whether the entry is renamed / moved / withdrawn / genuinely removed. If verified OOS or merged, reclassify the ID in the audit JSON via the same pattern as the DK p4 / NO p2 cleanups (`oos_excluded_nids` slot with audit-trail reason).

<!-- Anomaly log status — ALWAYS include. Surfaces persistent log state for triage visibility. -->
### Anomaly log — open + new this run

- **Open anomalies (carry-over from previous runs):** <X> total — top 3 by occurrence count:
  - `<stable-id-1>` — occ=<N>, first_seen=<date>, last_seen=<date>
  - `<stable-id-2>` — …
  - `<stable-id-3>` — …
- **New entries created this run:** <Y> (stable ids: <comma-separated>)
- **Active-entry occurrences appended this run:** <Z>
- **Resolved this run (out-of-routine triage):** <W> — link to docs/anomaly_log.yml for detail
- **Triage queue:** see `docs/anomaly_log.yml` + `docs/ANOMALY_LOG.md` workflow.

  Compute via:
  ```python
  from scripts.lib import anomaly_log as al
  opens = al.open_anomalies()
  print(f'open={len(opens)}')
  for e in sorted(opens, key=lambda x: x['occurrence_count'], reverse=True)[:3]:
      print(f'  {e["id"]} occ={e["occurrence_count"]}')
  ```

  Omit the «Resolved this run» line when 0 (the routine never resolves; that's manual triage).

### Push state

**Pushed this run:** submodule `munzfuss-harvest` `main` + superproject `harvest/auto` (<N> commits). origin/main untouched (single-writer = curation clone, per §0.1).

**To integrate (curation clone, no PR):** `cd /Users/serg/projects/muentzfuesse && git fetch && git merge origin/harvest/auto && git submodule update --init`.

### Recommended next batches (priority order)

1. <next-Numista-batch> — <description>
2. <next-ucoin-batch> — <description>
3. <next-IKMK-batch (or «top up next 5 from manifest uncached pool» / «re-discover per §5.5.2 — manifest fetched_at older than 30 days»)>
```

**If a batch was skipped or partial** (Cloudflare blocked, Chrome MCP disconnected mid-run, etc.) — append a `### Anomalies` section listing what was deferred. The Δ-columns will then show smaller-than-target deltas (e.g. `+3` instead of `+5`); that's the honest record.

If anything went wrong mid-run, append a `### Anomalies` section listing what was skipped/deferred.

---

## §9. Stop conditions

The routine stops cleanly (returns success) under any of these:

- Both batches committed → emit §8 report → done.
- Numista buckets all closed AND ucoin periods all closed → emit final «harvest complete» report → suggest user moves to Phase 2 work (location seeding / classification).
- Chrome MCP unavailable → emit «skipped» report → done (will retry next hour).
- Rate-limit defence repeatedly fires (≥2 TIDs/NIDs in a row hit 90s wait) → finish current batch if possible, then stop early; report which NIDs were deferred.

The routine STOPS HARD (returns failure, do not commit) under:

- Cache directory not present (clone broken).
- Save script returns code 2 on every single TID (canonical-tid validation failing systemically — site under maintenance).
- Working tree is dirty with unrelated, uncommitted changes that would get bundled by Step B.

---

## §10. State files quick reference

| File | Purpose | Read-only or writable |
|---|---|---|
| `scripts/cache/ucoin/_BR_audit-2_2026-05-20.json` | 16-period DK enumeration + gap_tids lists (BR-audit-2 — manifest 1) | RO (this routine) |
| `scripts/cache/ucoin/_BR_audit-3_2026-05-22_hanseatic.json` | 6-bucket Hanseatic Hamburg + Lübeck enumeration + gap_tids (BR-audit-3 — manifest 2, added 2026-05-22) | RO |
| `scripts/cache/ucoin/_BR_audit-4_2026-05-24.json` | 27-bucket German-states enumeration + gap_tids (BR-audit-4 — manifest 3, added 2026-05-24; Bremen + Brunswick lines + Hesse-Kassel + Oldenburg + Osnabrück + Lauenburg) | RO |
| `scripts/cache/numista/_BO6_audit_2026-05-20.json` | 8-bucket DK + NO + SH enumeration + in_scope_nids / gap_nids (BO.6 — manifest 1) | RO |
| `scripts/cache/numista/_BO6_gaps_manifest_2026-05-19.json` | SH-cluster per-issuer gap lists (BO.6 supplementary) | RO |
| `scripts/cache/numista/_BO7_audit_2026-05-24.json` | 17-issuer German-states enumeration + in_scope_nids (BO.7 — manifest 2, added 2026-05-24; Hanseatic cities + Welf territories + Hesse-Kassel + Oldenburg + Saxe-Lauenburg + Osnabrück + Bremen) | RO |
| `scripts/cache/ikmk/_manifest.json` | IKMK enumeration: `queries` (dict of query-name → mds_id list, 90 buckets) + top-level `ids` (deduped unique pool) + `fetched_at` timestamp. Used by §5.5 IKMK batch + §6.1 IKMK coverage table. Re-fetched by `scripts/fetch_ikmk.py discover` when freshness rules in §5.5.2 trigger. | RO (this routine reads only; `discover` writes it) |
| `scripts/cache/ucoin/<TID>.json` | Per-TID harvested data | RW (this routine appends) |
| `scripts/cache/numista/<NID>.json` | Per-NID harvested data | RW |
| `scripts/cache/ikmk/<mds_id>.json` | Per-IKMK-mds_id harvested record (CC BY-SA 4.0 LOD) | RW (this routine appends) |
| `scripts/cache/ucoin/_failed_open_ids.json` | Append-only structured log of URL-open failures (404 / Cloudflare-persistent / canonical-mismatch / redirect-to-landing / DOM-unexpected). Each entry: `{id, ts, url_tried, reason, batch_label, details}`. NOT framed as «deleted» — upstream state opaque; surfaces in §8 report for manual user review. IDs stay in audit `gap_tids` as retry candidates. | RW (append-only) |
| `scripts/cache/numista/_failed_open_ids.json` | Same shape for Numista NIDs. | RW (append-only) |
| `scripts/cache/ucoin/_p<NNNN>_listing.json` | Optional: cached slug→TID map per period | RW (lazy) |
| `scripts/cache/_harvest_handoff.json` | Between-runs state (next batch labels, deferred IDs, anomaly log, audit-known-state notes) — see §1.5 | **RW (mandatory, every run)** |
| `docs/handoff.md` | Project-wide session-state pickup file | Read for context only; this routine does NOT update |

---

## §11. Worked example (one complete run, abbreviated)

For reference — what a successful run looks like end-to-end:

```
1. Preflight: pwd, save scripts present, Chrome connected ✓
   + branch sync (§1 step 2): git fetch; checkout harvest/auto; submodule → origin/main
2. Read scripts/cache/_harvest_handoff.json (§1.5.1):
   → next_numista_batch_label = "R"
   → next_ucoin_batch_label = "32"
   → priority_override = null
   → deferred_ids = {numista: [], ucoin: []}
   → audit_files_known_state has "denmark/p4 OOS-reclassified" → safe to use audit
3. Pick Numista batch: NO p2 priority #1 → next 5 uncached
   = [129036, 131961, 134252, 135242, 142680]  (example)
4. For each NID:
   a. browser_batch [navigate + extractor JS]
   b. save heredoc → /tmp/save_numista.py
   c. sleep 31-60s
5. Submodule commit + push origin main (Numista cache only) → main-repo pointer bump on harvest/auto → push origin harvest/auto
6. Pick ucoin batch: p1115 priority #1 → next 5 uncached
   = [94117, 94118, 94119, 94120, 94124]  (example)
7. Listing-page anchor fetch (once)
8. For each TID:
   a. browser_batch [navigate slug-URL + extractor JS]
   b. save heredoc → /tmp/save_ucoin.py
   c. sleep 31-60s
9. Update _harvest_handoff.json (§1.5.2):
   → last_run_utc = now
   → last_*_batch_label = R / 32
   → next_*_batch_label = S / 33
   → append run record to runs[] (with anomalies if any)
10. Submodule commit + push origin main (ucoin cache + _harvest_handoff.json) → main-repo pointer bump on harvest/auto → push origin harvest/auto
11. Render §6.1 tables + §8 report (delta-columns auto-populated from this run's IDs)
12. Report what was pushed + the curator's one-line integration command (§3.4). No «wait for пуш» gate — pushes already happened (§0.1).
```

Total wall time per run: ~12-18 min (10 fetches × ~45s pacing + ~3 min overhead). Cron firing at :00 every hour will not overlap.
