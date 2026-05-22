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

1. **NEVER push without explicit user permission in the chat.** The user must type «пуш» / «push» / «git push» / «запуш» or equivalent BEFORE any `git push` runs. Cron-triggered runs almost always finish with commits local-only. End-of-run report includes the line: «N commits ready locally — `git push` when ready (both repos).»

2. **One Numista batch + one ucoin batch per run.** Do not exceed this. Context budget + politeness to both sources require small slices.

3. **Batch size = 5 entries** (NIDs or TIDs). Hard cap. If a batch would close the bucket and only 3 remain, do those 3 — never extend past the bucket boundary into the next priority.

4. **Pacing = 31-60s between fetches** within a single batch. Random `sleep $((RANDOM % 30 + 31))` between calls. Do NOT skip pacing «to save time» — Cloudflare and ucoin's rate-limit defence fire fast.

5. **NEVER edit YAML / seeds / location files in this routine.** Cache writes only. If the cache reveals a data anomaly (wrong year range, missing fineness), record it in the per-entry `_audit_context` field — never propagate to seeds in this run.

6. **English-only commit messages** (CLAUDE.md «Git workflow» rule). Chat may be Ukrainian; commits are English.

7. **`scripts/cache/` is a submodule.** Every commit is a TWO-STEP dance:
   - Step A: `cd scripts/cache && git add … && git commit -m "…"`
   - Step B: `cd /Users/serg/projects/muentzfuesse && git add scripts/cache && git commit -m "data: bump cache pointer — …"`
   - Both steps required. Missing step B = pointer drift; the next session sees `git status` warn `modified: scripts/cache (new commits)`.

8. **Surgical commits — stage ONLY the files you intend to commit. Parallel sessions may be active.** Other Claude sessions (V2-pipeline, asset builds, documentation work) routinely run in this same working tree and leave their own modifications in flight. The harvest routine MUST commit atomically and MUST NOT bundle unrelated edits into its commits.

   **Concrete rules:**
   - **NEVER use `git add .` or `git add -A` or `git add -u`** — these blanket-stage everything dirty, including the parallel session's work.
   - **NEVER use `git commit -a`** — it auto-stages every tracked file with modifications.
   - **Always stage by explicit file path** — `git add numista/123.json numista/456.json scripts/cache/_harvest_handoff.json` (specific files) vs. `git add scripts/cache` (specific submodule pointer, single path).
   - **In Step B of the PB-10 dance**, stage ONLY `scripts/cache` — never `git add scripts/cache docs/`, never `git add scripts/cache assets/`, never any second path on the same `git add`. The cache-pointer commit's ONLY purpose is the pointer; if docs / assets / scripts changed, they go in SEPARATE commits.
   - **Re-check `git status --short` IMMEDIATELY before each `git commit`** — if you see modifications that aren't yours from this run, do NOT proceed; either skip the commit (leave files for the user to handle) or commit only your specific files by absolute path. Concurrent session edits between preflight and commit time are normal.
   - **If a bundle happens anyway** (commit got more files than intended), do NOT amend. Per CLAUDE.md «Git safety protocol», create a corrective commit:
     ```bash
     # Self-recovery — split a bundle into atomic commits:
     git reset --soft HEAD~1                  # un-commit, keep stages
     git reset HEAD                            # un-stage everything
     git add <only-cache-pointer-path>         # re-stage just the harvest part
     git commit -m "..."                       # atomic harvest commit
     git add <other-paths>                     # stage the unrelated stuff
     git commit -m "..."                       # atomic OTHER commit (or leave for user)
     ```
     The routine that caused commit `95b3f59` (2026-05-21) ran this recovery successfully — keep that pattern as the template.

   **Why this matters.** Each commit must be reviewable + revertable independently. A bundle of «cache pointer + 6 favicon assets + favicon-generator script» can't be cleanly rolled back if any one element turns out wrong, and the commit message can only describe one of them, leaving the others undocumented in git history.

---

## §1. Preflight (do this once at session start)

```bash
# 1. Confirm cwd is repo root
pwd                                # must end in /muentzfuesse
test -d scripts/cache              # submodule present
test -f /tmp/save_numista.py       # per-NID saver (may need re-create — see §1a)
test -f /tmp/save_ucoin.py         # per-TID saver

# 2. Confirm working tree is clean (or only carrying expected v2-pipeline edits from concurrent sessions)
git status --short                 # if dirty, inspect; do not bundle unrelated changes into your commits

# 3. Confirm Chrome MCP is connected
# (use the tabs_context_mcp tool with createIfEmpty:true at the start of step-1 batch)
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

Use these stable strings so the next run can grep / match without prose parsing:

| Type | When |
|---|---|
| `audit_manifest_scope_drift` | §7.5 defensive sample shows a bucket's gap list contains OOS entries |
| `commit_footer_rejected` | Pre-commit or auto-mode classifier rejects the Co-Authored-By footer (or similar) |
| `cloudflare_challenge_persistent` | Cloudflare blocked the same source ≥2 times in this run despite 90s waits |
| `canonical_tid_mismatch_persistent` | ucoin save script returned exit 2 for ≥2 consecutive TIDs |
| `chrome_mcp_unavailable` | `list_connected_browsers` returned empty mid-run |
| `pre_commit_hook_failure` | `.githooks/pre-commit` failed validate/audit on unrelated files |
| `concurrent_session_conflict` | submodule needed rebase or main-repo had unrelated dirty edits |
| `url_open_failed` | Source returned 404 / persistent Cloudflare / canonical-id mismatch / redirect-to-landing / DOM-shape-unexpected for an ID that was in the audit's gap list. NEVER framed as «deleted» — upstream state opaque, user inspects manually via `_failed_open_ids.json` |
| `priority_bucket_exhausted` | The current-priority bucket closed mid-run; routine moved to next priority |
| `doc_update_pending` | Routine surfaced a non-blocking «next session please update doc X» note |

For each anomaly, also fill `detail` (free-text), `action_taken` (what the routine did), and `follow_up` (what the user/next-session should do).

---

## §2. Pick the next Numista batch

### §2.1. Read the audit + cache state

```bash
.venv/bin/python <<'EOF'
import json, pathlib
num_audit = json.loads(pathlib.Path('scripts/cache/numista/_BO6_audit_2026-05-20.json').read_text())
num_cache = pathlib.Path('scripts/cache/numista')

# Buckets are at audit['in_scope_buckets'][country][page]
# Each carries: in_scope_total + (in_scope_nids | gap_nids)
priorities = [
    ('denmark', 'p0_pre_lovkompleks', 20),  # NEW pri-1 2026-05-21: standards-continuity context, [1396, 1513)
    ('norway', 'p2', 88),     # 2nd: continue NO p2 (post-cleanup; was 193 before pre-1513 OOS reclassify)
    ('norway', 'p4', 78),     # 3rd: small bucket, easy closure
    ('norway', 'p3', 200),    # 4th: largest pool, save for last
]
for country, page, _ in priorities:
    info = num_audit['in_scope_buckets'][country][page]
    nids = info.get('in_scope_nids') or info.get('gap_nids') or []
    uncached = [n for n in nids if not (num_cache/f'{n}.json').exists()]
    if uncached:
        print(f'>>> Next Numista batch: {country}/{page}, {len(uncached)} uncached, take first 5:')
        print(uncached[:5])
        break
else:
    print('!!! All Numista buckets closed — switch strategy or stop')
EOF
```

The script picks the first priority with uncached NIDs and prints the next 5 to fetch.

### §2.2. Numista priority order

| Priority | Bucket | Era | Strategy |
|---|---|---|---|
| **1** | **DK p0_pre_lovkompleks 1396-1513** | **Erik of Pommern → John I (Hans)** | **Standards-continuity context — user-introduced 2026-05-21, ~4 batches to close (20 NIDs)** |
| 2 | NO p2 1513-1657 | C2 Oslo → F3 early Speciedaler | Continue from batch N (post-OOS cleanup: 88 in-scope, ~27 cached) |
| 3 | NO p4 1697-1814 | C5 late → F6 1813 | Small (78 NIDs), close it next |
| 4 | NO p3 1657-1697 | F3 mid → C5 Kongsberg | Largest pool (200), interleave |

When a bucket cached count == in_scope_total, move to the next priority.

**Note on `p0_pre_lovkompleks`** — this bucket holds Danish coinage from Erik of Pommern (1396-1439) through Hans / John I (1481-1513) — strictly speaking outside the project's 1514 mission anchor, but kept in scope as **standards-continuity context** for understanding what immediately preceded the Christian II 1514 four-act Lovkompleks. The 20 NIDs were user-curated from the Numista DK catalogue page 1 listing (`?e=danemark&st=1-2-3-47-154-5-54&cat=y&p=1&q=200&s=c&o=y`, sorted year ASC). Defensive sampling §7.5 does NOT need to fire here — every NID was hand-verified against the listing-page text before being added to `in_scope_nids` (no false-positive risk).

**Special case — when DK p1/p2/p3/p4 or SH cluster have new gap NIDs** (e.g. user added URLs to a manifest), prioritise those FIRST. Re-read `_BO6_audit_2026-05-20.json` + `_BO6_gaps_manifest_2026-05-19.json` and compare against actual cache contents before defaulting to NO buckets.

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
- `Years` / `Year` → parse `year_first` / `year_last` from format `"1649-1670"` or `"1532"`
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

**Append snippet:**

```python
.venv/bin/python <<EOF
import json, pathlib
from datetime import datetime, timezone

p = pathlib.Path('scripts/cache/numista/_failed_open_ids.json')
arr = json.loads(p.read_text()) if p.exists() else []
arr.append({
    "id": NID,
    "ts": datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
    "url_tried": URL,
    "reason": REASON,                  # one of the vocabulary above
    "batch_label": BATCH_LABEL,
    "details": DETAILS_STRING_OR_EMPTY,
})
p.write_text(json.dumps(arr, indent=2, ensure_ascii=False) + '\n')
EOF
```

**Commit-message note (within the §3.1 commit body):**
«N#XXXXX failed to open this run (reason: <reason>); logged to _failed_open_ids.json for user review. NID remains in audit gap_nids — retried next run unless reclassified.»

### §2.5. Handle Cloudflare challenge (transient, single-retry path)

When the page returns a Cloudflare interstitial («Just a moment…», «Checking your browser», DOM has `<div class="cf-browser-verification">`):
- Wait 90 s (`sleep 90`).
- Reload the same URL.
- **If the retry succeeds** → continue normally (save cache, log nothing special).
- **If the retry fails too** → apply §2.4 with `reason: cloudflare_persistent`. Also append to `scripts/cache/numista/_rate_limit_events.json` for cross-session pattern analysis. Skip this NID for this run.

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
cd scripts/cache && git add numista/<nid1>.json numista/<nid2>.json numista/<nid3>.json numista/<nid4>.json numista/<nid5>.json && git status --short && git commit -m "$(cat <<'EOF'
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

**Important:** after `cd scripts/cache && git commit`, you are STILL inside `scripts/cache`. The next `cd` returns to the main repo for Step B.

### §3.2. Main-repo pointer bump (Step B of PB-10)

> **Surgical-commit rule (per §0.8) applies here.** Stage ONLY the literal path `scripts/cache` — never `git add .`, never `git add scripts/cache docs/`, never any combined path on the same `git add` line. The cache-pointer commit's ONLY job is to bump the submodule reference; if `docs/` or `assets/` or other paths changed, they belong in SEPARATE commits handled by SEPARATE actors (or this routine commits its cache-pointer first, then leaves the unrelated changes for the user to triage).

**Pre-commit sanity check (mandatory):**

```bash
cd /Users/serg/projects/muentzfuesse
git status --short
# Expected output:
#   M scripts/cache         # ← yours (submodule pointer)
#   (anything else)         # ← NOT yours — leave it alone in Step B
```

If `git status` shows additional modified / untracked files beyond `scripts/cache`, those are concurrent-session work. **DO NOT stage them**. Proceed with the surgical `git add scripts/cache` only.

**Then commit:**

```bash
cd /Users/serg/projects/muentzfuesse && git add scripts/cache && git status --short && git commit -m "$(cat <<'EOF'
data: bump cache pointer — Numista BO.6 batch <letter> (<bucket>, <N> NIDs)

scripts/cache: <one-line description of what this slice contains>.
<closure note if any, e.g. "DK p1 1513-1617 now 139/139 — Phase 1 COMPLETE">

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

The interim `git status --short` between `add` and `commit` confirms only `scripts/cache` is in the staged column (typically shown as `M  scripts/cache` after staging — note the two spaces vs one). If you see any other path in the «Changes to be committed» area, abort and unstage.

**Sanity check after the commit lands:**

```bash
git log -1 --stat                  # the commit MUST show 1 file changed (scripts/cache)
git status --short                 # unrelated dirty files remain dirty (correct — not your concern)
```

If `git log -1 --stat` shows more than 1 file changed, you bundled something — execute the §0.8 self-recovery recipe.

### §3.3. Unrelated changes (concurrent V2-pipeline edits, asset builds, etc.)

Other sessions may have left modifications in:
- `docs/` (documentation updates, handoff edits, etc.)
- `data/v2/` (V2-pipeline classification work)
- `scripts/run_*.sh` (pipeline orchestration)
- `assets/` (favicons, illustrations)
- `scripts/maintenance/` (new one-off scripts being built)

**Do NOT touch any of these.** Stage only `scripts/cache` in Step B. The other sessions will commit their own work in their own time. If a concurrent edit accidentally lands in your commit (race condition between preflight and commit), use the §0.8 self-recovery to split.

---

## §4. Pick the next ucoin batch

### §4.1. Read the audit + cache state

```bash
.venv/bin/python <<'EOF'
import json, pathlib, re
audit2 = json.loads(pathlib.Path('scripts/cache/ucoin/_BR_audit-2_2026-05-20.json').read_text())
audit3 = json.loads(pathlib.Path('scripts/cache/ucoin/_BR_audit-3_2026-05-22_hanseatic.json').read_text())
url_index = json.loads(pathlib.Path('scripts/cache/ucoin/_url_index.json').read_text())
uc = pathlib.Path('scripts/cache/ucoin')

# DK-period priorities (audit-2-tracked).
dk_priorities = [
    'DK_p1115_Rigsdaler_1699-1749',
    'DK_p846_Rigsdaler_1750-1812',
    'DK_p647_Rigsbankdaler_1813-1854',
    'DK_p1147_Rigsdaler_1625-1699',
]
for k in dk_priorities:
    v = audit2['NEW_GAPS_DISCOVERED'].get(k) or {}
    if 'gap_tids' in v:
        uncached = [t for t in v['gap_tids'] if not (uc/f'{t}.json').exists()]
    else:
        # p647 has no gap_tids list — enumerate via listing page once first.
        uncached = []
    if uncached:
        print(f'>>> Next ucoin batch: {k}, {len(uncached)} uncached, take first 5:')
        print(uncached[:5])
        break
else:
    # All DK-period priorities are closed. Fall through to the
    # audit-3 Hanseatic buckets (per 2026-05-22 enumeration).
    hanseatic_priority = [
        'hamburg_p904',                # 34 TIDs, 1713-1772
        'hamburg_p903',                # 45 TIDs, 1773-1872
        'german_empire_p468_hamburg',  # 12 TIDs, 1873-1914 Reichsgoldmünzfuß
        'lubeck_p1205',                # 45 TIDs, 1620-1716
        'lubeck_p1204',                # 36 TIDs, 1717-1797
        'german_empire_p469_lubeck',   #  6 TIDs, 1901-1914 Reichsgoldmünzfuß
    ]
    for bkey in hanseatic_priority:
        b = audit3['buckets'].get(bkey) or {}
        tids = b.get('gap_tids') or []
        uncached = [t for t in tids if not (uc/f'{t}.json').exists()]
        if uncached:
            print(f'>>> Next ucoin batch: ucoin/{bkey}, {len(uncached)}/{len(tids)} uncached, take first 5:')
            print(uncached[:5])
            break
    else:
        print('!!! ALL ucoin priorities CLOSED — declare harvest complete OR add new buckets to §4.2.')
        print('!!! Known unresolvable-via-ucoin gaps (paper-source needed):')
        for k, v in audit3['in_scope_gaps_unresolvable_via_ucoin'].items():
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

### §4.3. ucoin URL pattern — MUST use slug-form

> **§13.1 known-issue.** ucoin no longer serves the bare `/coin/<TID>/` shortcut — it returns "Page Not Found". The only working pattern is `/coin/<slug>/?tid=<TID>`.

For each batch, fetch the slug→TID map FIRST from the listing page (once per period per run), then iterate per-TID:

**A. Listing-page anchor extraction (once per period per run):**

Navigate to: `https://en.ucoin.net/catalog/?country=denmark&period=<NNNN>`

Run via `javascript_tool`:

```javascript
(()=>{
  const anchors=Array.from(document.querySelectorAll('a[href*="/coin/"][href*="tid="]'));
  const tid_to_url={};
  for(const a of anchors){
    const m=a.getAttribute('href').match(/\/coin\/([^/]+)\/?\?tid=(\d+)/);
    if(m){ tid_to_url[m[2]]='https://en.ucoin.net/coin/'+m[1]+'/?tid='+m[2]; }
  }
  const wanted=['TID1','TID2','TID3','TID4','TID5'];  // batch TIDs
  const result={};
  for(const t of wanted){ result[t]=tid_to_url[t]||'MISSING'; }
  return result;
})()
```

If any TID returns `MISSING`, the period listing doesn't cover it — it might be on a different page or has been deleted. Log + skip.

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

**Apply §2.4 exactly**, writing to `scripts/cache/ucoin/_failed_open_ids.json` (NOT the Numista file). Append a structured record with the same schema (id / ts / url_tried / reason / batch_label / details). The TID stays a retry candidate in the audit's `gap_tids` — never removed by this routine.

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
cd scripts/cache && git add ucoin/<tid1>.json ucoin/<tid2>.json ucoin/<tid3>.json ucoin/<tid4>.json ucoin/<tid5>.json _harvest_handoff.json && git status --short && git commit -m "$(cat <<'EOF'
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

### §5.2. Main-repo pointer bump (Step B)

> **Surgical-commit rule (per §0.8) applies here.** Stage ONLY the literal path `scripts/cache`. Same anti-pattern list as §3.2 — never blanket adds, never combined paths.

**Pre-commit sanity check (mandatory):**

```bash
cd /Users/serg/projects/muentzfuesse
git status --short
# Expected:  M scripts/cache  (yours — submodule pointer)
# Anything else dirty → leave alone, NOT your concern.
```

**Then commit:**

```bash
cd /Users/serg/projects/muentzfuesse && git add scripts/cache && git status --short && git commit -m "$(cat <<'EOF'
data: bump cache pointer — ucoin BR batch <N> (<period> <slice>, <M> TIDs)

scripts/cache: <1-line description>. <period> progress: <cached>/<total>
cached (<remaining> left).

Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>
EOF
)"
```

**Sanity check after commit:**

```bash
git log -1 --stat                  # MUST show 1 file changed (scripts/cache)
```

If more than 1 file changed, you bundled — execute §0.8 self-recovery to split.

---

## §6. Render the coverage tables

After both batches commit, output BOTH tables in the exact format below. This is the user-facing deliverable; everything else above is plumbing.

### §6.1. Compute current numbers (with per-row Δ for THIS run)

The script accepts two integer-list inputs at the TOP — fill them with the exact NIDs / TIDs you just saved in this run's Numista batch + ucoin batch. The script then renders both tables with a **«Δ this run»** column that tallies how many of those just-added IDs landed in each period/bucket.

If a batch was deferred (Cloudflare blocked, NID returned 404 and was logged to `_failed_open_ids.json` per §2.4 / §4.4), DO NOT include it in the list — only IDs whose `<id>.json` was actually written this run.

```bash
.venv/bin/python <<'EOF'
import json, pathlib

# ============================================================
# FILL THESE IN at the start of each rendering call:
# ============================================================
NIDS_THIS_RUN = [82133, 82384, 98983, 99000, 50496, 55887, 55888]  # Numista batch
TIDS_THIS_RUN = [94070, 94098, 94099, 94100, 94101]                # ucoin batch
NUMISTA_BATCH_LABEL = 'N'                                          # e.g. 'N', 'O', 'P'
UCOIN_BATCH_LABEL = '29'                                           # e.g. '29', '30', '31'
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
print(f'| **TOTAL** | | | **{total_in_scope}** | **{total_cached}** | **{gap}** | **{pct}%** | **{fmt_delta(total_delta)}** | **{closed_count}/8 closed** |')

if numista_unmatched_nids:
    print()
    print(f'> ⚠ NIDs not matched to any tracked bucket: {sorted(numista_unmatched_nids)} '
          '— check audit + gaps manifest; may be off-bucket or freshly-discovered scope.')
EOF
```

**Implementation note.** Maintain `NIDS_THIS_RUN` and `TIDS_THIS_RUN` as live variables during the batch flow:
- After each successful `save_numista.py` call, append the NID to a running list (e.g. `RUN_NIDS=()` Bash array, or just track in your scratchpad).
- After each successful `save_ucoin.py` call (exit code 0), append the TID.
- Skip 404 cases and exit-2 (canonical-tid fail) cases — those are not «processed this run».
- At rendering time, paste the final lists into the script's top.

The unmatched-IDs warning at the bottom guards against scope drift — if a TID/NID you saved doesn't show up in any tracked bucket, the audit needs updating OR the ID was saved outside the routine's intended scope.

### §6.2. Required output sections (in this order)

1. **Pre-tables one-liner** — what this run added, framed as a delta.
   Example: «Batch run 2026-05-21 14:00 UTC: Numista batch P added **+5** to NO p2; ucoin batch 31 added **+5** to DK p1115. Both committed local.»

2. **ucoin coverage table** — 16 rows + TOTAL, with the `Δ b<N>` column populated from §6.1's script (exactly as printed).

3. **Numista coverage table** — 8 rows + TOTAL, with the `Δ batch <letter>` column populated similarly.

4. **Headline numbers** (each line ends with a parenthetical run-delta):
   - Phase 1 (DK + SH) Numista — total cached, remaining (Δ this run: +X)
   - Phase 2 (NO) Numista — total cached, remaining (Δ this run: +X)
   - ucoin Phase 1 — total cached, remaining (Δ this run: +X)
   - Grand cumulative cached (Δ this run: +X from Numista, +Y from ucoin = +Z total)

5. **Failed-to-open this run** — list IDs that the routine could NOT fetch (404 / persistent Cloudflare / canonical mismatch / DOM unexpected). Pulled from this run's `runs[-1].numista_batch.failed_open[]` + `runs[-1].ucoin_batch.failed_open[]` + `_failed_open_ids.json` tail. **Omit the section entirely if both lists are empty** (the typical clean run).
   Shape per entry: `N#<id> — <reason> — <one-line context>`. Example:
   > ### ⚠ Failed to open this run (4)
   > - **Numista**:
   >   - N#117344 — `404_page_not_found` — Erik of Pommern Skærv per audit, but bare URL returns "Page Not Found". May be moved / renamed; needs manual check.
   >   - N#475742 — `redirect_to_landing` — URL bounced to /coins page instead of /475742 per-coin record.
   > - **ucoin**:
   >   - TID 94158 — `canonical_id_mismatch` — slug URL resolved to TID 94159 after redirect (twice in a row).

   Tells the user exactly which IDs to inspect manually. The IDs **remain in audit gap_nids/gap_tids** — they're retry candidates next hour. Routine does NOT mark them «dead».

6. **Push state** — exactly one sentence: «N commits ready locally — `git push` when ready (both repos).» Compute N via `git log --oneline origin/main..HEAD | wc -l` from main repo + same from submodule, sum.

7. **Recommended next batches** — top 3 priorities for the NEXT hourly run.

### §6.3. Status emoji legend (use consistently)

- ✅ `CLOSED` — cached == in_scope (gap = 0), no delta this run
- 🎉 `CLOSED! (batch <N>)` — closed THIS run (delta > 0 AND gap == 0) — auto-emitted by the script
- 🔵 `batch <N> here` — partially advanced THIS run (delta > 0 AND gap > 0) — auto-emitted
- 🔵 `open` — partial coverage, untouched this run
- ⏳ `untouched` — 0 cached, untouched this run
- ⚠ stragglers — special note for «closed except for N residual NIDs» edge cases (manual annotation)

### §6.4. Delta semantics — what counts

- A TID/NID counts toward the delta only if its `<id>.json` was **written to disk this run** (save script exit 0).
- IDs logged to `_failed_open_ids.json` are NOT included in delta (no file written; per §2.4 / §4.4). They surface in the §6.2 «Failed to open this run» section instead — visibility for the user without inflating progress numbers.
- Canonical-tid mismatch (save_ucoin exit 2) is NOT included.
- Cloudflare deferrals — IDs that you decided to retry next hour — are NOT included.
- Re-saves of an already-cached file (idempotent rewrite with same content) ARE counted as 0 delta for that period — the file already existed, the run didn't add new scope.

This keeps the delta semantics tight: **«items the routine demonstrably added to the cache this hour»**, nothing aspirational.

---

## §7. Error recovery

### §7.1. Pre-commit hook failure

`/Users/serg/projects/muentzfuesse/.githooks/pre-commit` runs `build.py --validate-only` + prose audits. If a commit fails:
- The cache files are still added but NOT committed.
- Inspect the failure (usually unrelated to cache changes — could be stale prose lint on existing YAMLs).
- Re-run the commit. If still failing AND the failure is in an unrelated file, use `--no-verify` ONLY if the user explicitly said so in chat. Otherwise leave the batch uncommitted and report at end of run.

### §7.2. Detached HEAD after submodule commit

If `cd scripts/cache && git commit` lands on a detached HEAD (e.g. the submodule pointer was not on a branch), recover before Step B:

```bash
cd scripts/cache
git status                         # confirms "HEAD detached at <sha>"
git checkout main                  # switch to main branch
git reset --hard <sha-of-new-commit>  # bring the new commit onto main
cd /Users/serg/projects/muentzfuesse
```

Then proceed with Step B (`git add scripts/cache && git commit …`).

### §7.3. Concurrent-session conflict on submodule

If another session pushed cache changes after you cloned, the submodule may need a rebase:

```bash
cd scripts/cache
git fetch origin
git rebase origin/main             # pull peer's commits + replay yours
# if conflicts: investigate; do NOT auto-resolve cache file conflicts
# (a per-NID JSON should not be edited by two sessions simultaneously)
cd /Users/serg/projects/muentzfuesse
```

If conflict resolution feels risky, leave the cache uncommitted and report. The user will resolve manually.

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

Final response to the user follows this exact structure. The Δ-columns in both tables come straight from §6.1's script output — do not hand-compute, the script already filled them.

```markdown
**Batch run <UTC timestamp>**: Numista batch <letter> added **+<N>** to <bucket>; ucoin batch <NN> added **+<M>** to <period>. Both committed local (total **+<N+M>** entries this run).

### ucoin — per-period detailed coverage (post batch <NN>)

<16-row + TOTAL table from §6.1 — includes Δ b<NN> column>

### Numista — per-bucket detailed coverage (BO.6 v3, post batch <letter>)

<8-row + TOTAL table from §6.1 — includes Δ batch <letter> column>

### Headline numbers post-batches <letter> + <NN>

- **Phase 1 (DK + SH) Numista**: <cached>/<total>, **<remaining> left** (Δ this run: +<n1>)
- **Phase 2 (NO) Numista**: <cached>/<total>, **<remaining> left** (Δ this run: +<n2>)
- **ucoin Phase 1**: <cached>/<total>, **<remaining> left** (Δ this run: +<n3>)
- **Grand total**: <numista_cumulative + ucoin_cumulative> cached cumulatively (Δ this run: **+<n1+n2>** Numista, **+<n3>** ucoin = **+<total>** entries)

<!-- §6.2 item 5 — Failed to open this run. Include ONLY when at least one failed_open[] is non-empty: -->
### ⚠ Failed to open this run (<K>)

- **Numista**:
  - N#<id> — `<reason>` — <one-line context>
  - …
- **ucoin**:
  - TID <id> — `<reason>` — <one-line context>
  - …

IDs remain in audit `gap_nids`/`gap_tids` — retried next run. Manual review: open each URL in browser to determine whether the entry is renamed / moved / withdrawn / genuinely removed. If verified OOS or merged, reclassify the ID in the audit JSON via the same pattern as the DK p4 / NO p2 cleanups (`oos_excluded_nids` slot with audit-trail reason).

### Push state

**<N> commits ready locally** — `git push` when ready (both repos: `cd scripts/cache && git push && cd /Users/serg/projects/muentzfuesse && git push`).

### Recommended next batches (priority order)

1. <next-Numista-batch> — <description>
2. <next-ucoin-batch> — <description>
3. <third-priority>
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
| `scripts/cache/ucoin/_BR_audit-2_2026-05-20.json` | 16-period enumeration + gap_tids lists | RO (this routine) |
| `scripts/cache/numista/_BO6_audit_2026-05-20.json` | 8-bucket enumeration + in_scope_nids / gap_nids | RO |
| `scripts/cache/numista/_BO6_gaps_manifest_2026-05-19.json` | SH-cluster per-issuer gap lists | RO |
| `scripts/cache/ucoin/<TID>.json` | Per-TID harvested data | RW (this routine appends) |
| `scripts/cache/numista/<NID>.json` | Per-NID harvested data | RW |
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
5. Submodule commit (Numista cache only) + main pointer bump
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
10. Submodule commit (ucoin cache + _harvest_handoff.json) + main pointer bump
11. Render §6.1 tables + §8 report (delta-columns auto-populated from this run's IDs)
12. Wait for user "пуш" before any push
```

Total wall time per run: ~12-18 min (10 fetches × ~45s pacing + ~3 min overhead). Cron firing at :00 every hour will not overlap.
