# Data layout — separating cache from code

> **Archived 2026-05-13.** Option A (separate sibling repo mounted as a
> submodule at `scripts/cache/`) has since been implemented. See
> `.gitmodules`, `CLAUDE.md` «Harvest submodule workflow», and
> `docs/DECISIONS.md`. This document is preserved as the historical
> record of the analysis that led to the decision; it is no longer
> active guidance.

## Problem statement

The repo currently mixes three categories of files in a single tree:

| Tier | Examples | Size | Tracked files | Mutable? |
|---|---|---:|---:|---|
| **Code** | `scripts/build.py`, `scripts/lib/*`, `templates/*` | ~200 KB | ~60 | yes, by hand |
| **Curated data** | `data/locations/*.yml`, `data/shared/*.yml`, `data/seed/*` | ~5 MB | ~35 | yes, by hand |
| **Raw cache** | `scripts/cache/{ikmk,hede,numista,bruun,ucoin}/*` | **125 MB** | **9,168** | regenerable by `fetch_*.py` |

The cache is 99 % of tracked files and is a build artifact — not human-edited source. It pollutes:

- `git log`, `git blame`, `git diff` (every IKMK JSON sweep dwarfs every prose edit)
- Clone time / GitHub UI load time on fresh checkouts
- Mental model — «is this file edited by hand or by a script?» requires opening every directory's README
- CI build time (Pages build doesn't need cache, but pulls 125 MB anyway)

## Goal

Split the repo so the daily commit / browse experience is on the **code + curated data** tier (~150 files, ~5 MB), and the regenerable cache lives outside that working surface. Constraint: **free hosting only**.

## Options evaluated

### A. Separate sibling git repo on GitHub (recommended)

Two repos on GitHub:
- `muentzfuesse` — code + `data/` + `templates/` + `config/` + `docs/`. Becomes ~5 MB.
- `muentzfuesse-cache` — `scripts/cache/{ikmk,hede,numista,bruun,ucoin}/*` and nothing else.

Local layout:
```
~/projects/
├── muentzfuesse/         ← main repo, cloned normally
└── muentzfuesse-cache/   ← cache repo, cloned alongside
```

Scripts that read cache resolve the path through one of:
- An env var `MUENTZFUESSE_CACHE_DIR` (defaults to `../muentzfuesse-cache`)
- A symlink: `muentzfuesse/scripts/cache → ../muentzfuesse-cache` (gitignored)

**Pros**
- Main repo shrinks 99 % in tracked-file count.
- Each repo's history is coherent — code commits vs cache sweeps no longer interleave.
- Pages build only needs main repo → CI clone shrinks from 125 MB → 5 MB.
- Both repos free on GitHub (size + bandwidth).
- Either repo can be rolled back, garbage-collected, or filter-repo'd independently.

**Cons**
- Two repos to clone on a fresh setup.
- Cross-repo commits when a fetch produces both new cache files AND a seed regen need coordinating (commit cache, then commit derived seed).
- Slightly heavier mental model on the «which repo is this file in» question — mitigated by a single doc + the env var.

### B. Git submodule

A sub-variant of A: the cache repo becomes a submodule mounted at `scripts/cache/`. Single clone with `--recursive` brings both; commits in main repo can pin a specific cache version.

**Pros**
- Path stays `scripts/cache/...`, no env var.
- Cache version is pinned in main repo's commit graph.

**Cons**
- Submodules are well-known to be friction-heavy: every cache regen requires committing in submodule first, then bumping the gitlink in main, then pushing both. Mistakes silently desync.
- Editing in both repos in one task is awkward.
- Detached HEAD state confuses git tooling.

**Verdict**: less ergonomic than (A) without meaningful upside for our usage.

### C. GitHub Releases / Pages / Wiki as data store

Push the cache as a versioned archive (`cache-2026-05-11.tar.gz`) to a GitHub Release of the main repo (or to a dedicated cache repo's Releases). Scripts download + extract on demand; CI doesn't need it.

**Pros**
- Single repo (or a near-empty cache repo).
- Releases versioning is built in.

**Cons**
- Loses per-file diff visibility — every cache fetch creates a new archive, no semantic «just two pages updated» view.
- Manual release management overhead.
- 2 GB-per-file GitHub release cap is plenty for now, but no incremental fetch.
- The cache IS valuable in diff form right now (e.g. catching parser regressions across re-fetches).

**Verdict**: works for offline-only archive but loses the «what changed in this fetch» signal we already use.

### D. Git LFS

Use Git LFS for cache files (HTML, JSON).

**Cons (single, decisive)**
- GitHub free LFS quota: 1 GB storage, 1 GB/month bandwidth. The IKMK cache alone (109 MB) plus monthly re-fetches by CI would blow the bandwidth quota in days. Paid LFS starts at $5/mo for 50 GB — outside the «free only» constraint.

**Verdict**: ruled out by the free-only constraint.

### E. External free storage (Cloudflare R2 / Backblaze B2 / Hetzner)

Push cache to S3-compatible storage.

**Pros**
- Cheap / free at small scale (R2 has 10 GB storage free, free egress).

**Cons**
- Adds an external service dependency outside git.
- Need API credentials in CI + locally.
- Different mental model — can't `git log` the cache.
- Sync tooling needed (rclone or similar).

**Verdict**: workable backup target but worse-than-A for active use.

### F. Don't store the cache at all — regenerate on demand

Scripts re-fetch from source every run.

**Cons (decisive)**
- Numista API has a strict daily quota — re-fetching 700 IDs per run would consume it.
- danskmoent.dk is a single-person volunteer site; hammering it on every parse is impolite.
- IKMK's 7,000 records take **hours** to re-fetch.
- Parser regressions would silently differ across runs (source pages can change).

**Verdict**: ruled out by source-side rate limits and reproducibility.

### G. Hybrid — small caches inline, IKMK out

Keep the small caches (Hede 12 MB, Bruun 6 MB, Numista 2.8 MB, ucoin 0.4 MB) in the main repo; move only **IKMK** (109 MB / 7,096 files — 90 % of the size and 78 % of the file count) to a separate `muentzfuesse-ikmk` repo or to GitHub Releases.

**Pros**
- Main repo drops from 125 MB / 9,168 files → 21 MB / 2,072 files (90 % size reduction, 77 % file-count reduction with a single split point).
- Hede + Bruun caches stay where they are — those are tightly coupled to the seed pipelines and «changing the parser + recommitting the parsed JSONs» is the natural workflow.
- Single small split → only one new repo to manage.

**Cons**
- Two stages of split: smaller wins now, full split later if needed.
- Asymmetric: «some caches are inline, one is external» is a slightly weird mental model.

**Verdict**: best 80/20 — captures most of the win with minimum coordination overhead. Recommended as the **first step**; a full split (option A) is the natural next step if and when the smaller caches grow.

## Recommendation: G first, A as the long-term destination

**Phase 1** (do this): split IKMK into `muentzfuesse-ikmk` (sibling repo). Single split point, immediate 90 % size win, minimal change to daily workflow. Set env var convention so paths are robust to either repo layout.

**Phase 2** (when needed): if the inline caches (Hede + Bruun + Numista + ucoin) grow past a threshold (e.g. >50 MB combined), do the full split → all caches in `muentzfuesse-cache`. The phase-1 env var pattern + the same migration steps apply.

## Phase 1 — action plan

### Step 1: prepare the new repo

```bash
# In the parent directory ~/projects/:
gh repo create muentzfuesse-ikmk --public \
    --description "IKMK Berlin numismatic-cabinet JSON cache for the muentzfuesse project"
git clone git@github.com:<user>/muentzfuesse-ikmk.git
cd muentzfuesse-ikmk
# Initial commit: README + LICENSE + .gitignore
```

The new repo's README explains:
- It's a derivative of `https://ikmk.smb.museum` JSON exports
- Cached for the muentzfuesse project's offline reproducibility
- License: data is CC-BY (per IKMK's terms); the cache structure is MIT (matches main)
- How to re-fetch: pointer to `scripts/fetch_ikmk.py` in the main repo

### Step 2: extract IKMK history from main repo

Use `git filter-repo` (NOT the older `filter-branch`) to extract only the IKMK subtree with its full history:

```bash
# In a fresh clone of muentzfuesse (NOT the working tree):
git clone git@github.com:<user>/muentzfuesse.git muentzfuesse-ikmk-extract
cd muentzfuesse-ikmk-extract
git filter-repo --path scripts/cache/ikmk/ --path-rename scripts/cache/ikmk/:
# Pushes ikmk subtree to the root of this clone, with history preserved.
git remote add ikmk git@github.com:<user>/muentzfuesse-ikmk.git
git push ikmk main --force
```

(`--force` is fine here: muentzfuesse-ikmk is empty.)

### Step 3: remove IKMK from main repo

Two options:
- **Soft**: keep `scripts/cache/ikmk/` in main but gitignore it; deletion only on next major cleanup.
- **Hard**: `git filter-repo --invert-paths --path scripts/cache/ikmk/` to scrub from history → repo size drops immediately on next GC.

Soft first (reversible). Hard once everything's verified.

### Step 4: wire scripts to the new path

Add to every script that reads IKMK cache:

```python
import os
from pathlib import Path
IKMK_CACHE = Path(os.environ.get(
    "MUENTZFUESSE_IKMK_CACHE",
    Path(__file__).resolve().parents[2].parent / "muentzfuesse-ikmk",
))
```

Default resolves to `../muentzfuesse-ikmk` relative to repo root, so a fresh sibling clone Just Works. Override via env var when the cache lives somewhere else (CI, alternate hosts).

Touched scripts (search for `scripts/cache/ikmk`):
- `scripts/fetch_ikmk.py`
- `scripts/match_ikmk_locations.py`
- `scripts/audit_ikmk_index.py`
- Any maintenance script under `scripts/maintenance/*ikmk*`

### Step 5: document in CLAUDE.md + ARCHITECTURE.md

- Add a «Repo layout» subsection to CLAUDE.md explaining the sibling-repo convention.
- Update `docs/ARCHITECTURE.md`'s pipeline section so the IKMK row points outside the repo.
- Note the env var override in `data/seed/hede/README.md`-style sidecar docs.

### Step 6: CI / Pages

- GitHub Actions build (`/.github/workflows/deploy.yml`) does NOT need IKMK cache — `scripts/build.py` reads `data/`, not `scripts/cache/`. No CI changes needed.
- If a future audit script needs IKMK in CI, it can clone the cache repo as part of the workflow (a few seconds, no auth needed for public repos).

### Step 7: verify

Acceptance criteria:
- [ ] `git ls-files | wc -l` in main repo drops from ~9,280 → ~2,200.
- [ ] `du -sh .git` in main repo shrinks (after `git gc --aggressive` if doing the hard cleanup).
- [ ] `python scripts/build.py` still passes — no cache dependency in the build path.
- [ ] `python scripts/match_ikmk_locations.py` still works with the cache at the new sibling path.
- [ ] `python scripts/fetch_ikmk.py` writes to the sibling repo cleanly.
- [ ] CI Pages build green on next push.

## Phase 2 — full cache split (optional, future)

When Hede + Bruun + Numista grow past comfort (rough trigger: combined > 50 MB or > 2,000 files):

- Repeat steps 1-4 for each remaining cache, all into one `muentzfuesse-cache` repo.
- OR fold the new caches into the already-existing `muentzfuesse-ikmk` repo and rename it to `muentzfuesse-cache`.
- Update env var to `MUENTZFUESSE_CACHE_DIR` (umbrella) and have each `scripts/parse_*.py` / `scripts/fetch_*.py` resolve its own subdir under it.

## Non-recommendations

- **Don't move `data/seed/` out.** It IS curated content per CLAUDE.md (the build reads it, the schema validates it, promotions originate from it). It belongs in the main repo.
- **Don't move `data/i18n/` or `data/shared/` out.** Same reason.
- **Don't move `scripts/maintenance/*` out.** The scripts are part of the project's reproducibility — they should live with the code that depends on their output shape.
- **Don't use Git LFS.** Free tier doesn't fit (see option D).
- **Don't introduce a database.** Per CLAUDE.md «Not a database. YAML is the storage layer.» This applies to canonical data; the cache stays file-based for diff-visibility on re-fetches.

## Decision pending

The user should pick:
1. **Phase 1 only** (split IKMK) — recommended starting point.
2. **Phase 1 → Phase 2** as a sequenced plan with a tripwire condition.
3. **Skip and tolerate** — defer the split if the current size isn't actually painful.

This doc stays in `docs/` as the durable record of the plan once chosen.
