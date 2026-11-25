# Research library split: originals out of git, corpus text apart from coin data

Curator direction 2026-11-25. The harvest repo (`scripts/cache`, submodule
`munzfuss/munzfuss-harvest`, private) holds 13.8 GiB of tracked files, a
11.18 GiB pack, ~2× GitHub's recommended 5 GB, and grows with every work added
to the corpus. About 1.3 GB of it is coin data; the rest is research material.

Constraints set by the curator:

- local disk is enough as the primary store, provided the download URL of each
  original is recorded; a missing URL is normal and never an error;
- any second copy must be free; nothing paid;
- rewriting the munzfuss-harvest history (filter-repo + force-push) is agreed.

## Target layout — three tiers, split by artifact type

| Tier | What | Where | In git? |
|---|---|---|---|
| Originals | PDF, scans, ALTO XML — anything re-downloadable or irreplaceable but never edited | `~/munzfuss-library/` (`LIBRARY_ROOT`), same relative paths as today (`fogtman/d1/…pdf`) | no — manifest only |
| Corpus | text layers (`pages/*.txt`), page maps, `_index.json` / `_manifest.json`, READMEs, `_corpus.yml` | new private repo `munzfuss/munzfuss-corpus` (`CORPUS_ROOT`) | yes |
| Harvest | coin-source caches: parsed json/htm of Hede, Numista, KMM, Bruun lots, … | `munzfuss/munzfuss-harvest` (`HARVEST_ROOT`), as now | yes |
| Index | kb SQLite | local, rebuilt by `kb.py build` | no |

Split by type, not by use: Bruun and danskmoent are mixed — their PDFs go to
the library, their parsed json/htm stay in harvest.

### Second copy of the originals

GitHub Release assets in the private repo `munzfuss/munzfuss-library` (created
2026-11-25, README only, no source). Limits checked on docs.github.com: < 2 GiB
per file, 1000 assets per release, «no limit on the total size of a release,
nor bandwidth usage». Third fallback: the recorded origin URL.

- One release per top-level library directory; tag = that directory name
  (`secher`, `fogtman`, …).
- Asset name = the path below that directory with `/` → `--`
  (`secher/_pdf/bd1.pdf` → release `secher`, asset `_pdf--bd1.pdf`).
- ALTO XML (44 093 files) cannot be one asset per file (1000-asset cap): it is
  backed up as one `.tar.gz` per volume directory (`fogtman/d1/alto/` →
  asset `d1--alto.tar.gz`); the library keeps the unpacked directory.
- Why a separate repo, not releases on munzfuss-harvest: a release tag pins a
  commit, and a tag pointing into the pre-rewrite history would keep every
  removed blob alive on GitHub.
- Fallback backend if GitHub ever objects: a private Hugging Face dataset
  (100 GB free); the manifest does not change, only the backup location field.

### Manifest

`library_manifest.yml` in munzfuss-corpus, one record per file (or per ALTO
bundle):

```yaml
- path: secher/_pdf/bd1.pdf
  sha256: 995bfb28…
  bytes: 239369311
  source_url: https://upload.wikimedia.org/…bind_1…pdf   # optional
  fetched: 2026-10-13                                     # optional
  backup: {release: secher, asset: _pdf--bd1.pdf}        # absent = not yet backed up
```

### Tool — `scripts/library/library.py`

- `add <path> [--url U]` — hash, record; no URL → reported as «unknown», no error.
- `backup` — upload every record without `backup` (`gh release upload`), then
  check the asset's `digest` from the API equals the record's sha256.
- `fetch <path|--all>` — local → release → origin URL, sha256-checked; a
  mismatch from the origin is a warning (the origin changed the file), never a
  silent replace.
- `verify` — re-hash every local file against the manifest.
- `status` — files with a single copy (no backup and no URL), files missing
  locally, unrecorded files under `LIBRARY_ROOT`.

## Steps

Each step has its own check; the next one starts only after the check passes.

### 0. Back up Secher first — ✅ 2026-11-25

`secher/_pdf/bd1–6.pdf` (1.47 GB) are gitignored and existed only on this Mac
(origin: Wikimedia Commons, URLs and sha256 in `secher/bd<N>/_index.json`;
the six local hashes match those records, checked 2026-11-25).

- Uploaded as release `secher` in munzfuss-library, assets `_pdf--bd1.pdf` …
  `_pdf--bd6.pdf`.
- **Check:** each asset's API `digest` = the sha256 below — passed, all six equal.

| asset | bytes | sha256 |
|---|---:|---|
| `_pdf--bd1.pdf` | 239369311 | `995bfb28749e48ee57c4e124f371d66b581009158a01c19c6a52903cd43e357a` |
| `_pdf--bd2.pdf` | 396414231 | `809067585cdf7f57d7381b83e7147260ab24f4d5f3fd82c5234c086a98655113` |
| `_pdf--bd3.pdf` | 237136432 | `cd9adcf86c0537cd3d13feb36dfabcdf227a6f3b989c845c13ed0e5928225fb7` |
| `_pdf--bd4.pdf` | 231246500 | `f09ac2a47e8258b6c28145a4441d3acead9a6d650ad42790f6b89a7569b6591f` |
| `_pdf--bd5.pdf` | 212927328 | `73e96cd7832110339d961f61018bf214cf5179e34d0c115ee48c4b124471c599` |
| `_pdf--bd6.pdf` | 152090443 | `378a18982da155ddbb327ff73de9c252c8af49ecca8832d75cdd9250d499e0cb` |

### 1. Tool + `LIBRARY_ROOT` — ✅ 2026-11-25

- `LIBRARY_ROOT` / `CORPUS_ROOT` in `scripts/lib/paths.py`, resolved like
  `HARVEST_ROOT` (env → `local.env` → default `~/munzfuss-library`,
  `~/munzfuss-corpus`), so every worktree and session shares one copy.
- `scripts/library/library.py` with the five commands; unittest on a temp
  library (add without URL, verify catches a changed byte, fetch order,
  status lists single-copy files).
- **Check:** tests green; `library.py status` on an empty root runs clean —
  passed (`tests/test_library.py`, 9 tests; `GhBackend.assets('secher')`
  reads the six live digests).
- Manifest default: `CORPUS_ROOT/library_manifest.yml`. Until step 5 makes
  `~/munzfuss-corpus` a repo, init it as a local git repo in step 2 so the
  manifest is versioned from its first record.

### 2. Build the library by COPYING (not moving) the originals — ✅ 2026-11-25

- Copy every PDF and ALTO tree out of `scripts/cache` into `LIBRARY_ROOT`,
  same relative paths. The cache stays intact until step 7.
- Manifest generated with sha256; `source_url` / `fetched` taken from
  `_corpus.yml`, `_index.json`, `_manifest.json` where they name the file;
  otherwise left empty.
- **Check:** `library.py verify` clean; file count and byte total equal the
  cache's (`git ls-files` PDFs: 309 today; ALTO: 44 093); `status` lists how
  many have no URL.
- Done with `scripts/library/import_from_cache.py` (APFS clones,
  `cp -c`, so no extra disk). Also taken: rigsarkivet scans (one bundle for
  `tk_160_diverse_moentsager/pages`, three loose jpg). Result: 396 records,
  17.39 GB — 324 files (315 tracked PDFs + 6 Secher + 3 scans) and 72 bundles
  (71 ALTO trees, 46 336 XML; 1 scan tree, 219 jpg). `verify`: 396 ok.
  `~/munzfuss-corpus` is a local git repo holding only the manifest for now.
- URLs: `source_url` (re-downloadable byte for byte) 6 — Secher only;
  `work_url` (the work's page, informational) 167; no `_corpus.yml` work 42
  (Bruun auction PDFs and LEB 1928, Wilcke 1919 PDF, wayback PDFs,
  rigsarkivet). Enriching these is optional — after step 3 every file has a
  release copy.

### 3. Back up everything

- `library.py backup` — per-directory releases, ALTO bundles.
- **Check:** `status` reports zero single-copy files; a spot `fetch` of three
  files from release into a temp root matches sha256.

### 4. Point the code at the library

- Inventory of code that opens a local PDF / ALTO (candidates from a grep on
  2026-11-25, to be read one by one — many only mention a `.pdf` URL):
  `scripts/kb/kb.py`, `scripts/kb/layout_extract.py`,
  `.claude/skills/add-source-work/add_work.py`,
  `scripts/bruun_parser/01_extract_text.py`, `scripts/fetch_schou.py`,
  `scripts/fetch_secher.py`, `scripts/parse_tietjen.py`,
  `scripts/maintenance/build_lindahl_1955_seed.py`,
  `scripts/maintenance/build_metallanalyser_seed.py`,
  `.claude/skills/merge-candidate-table/compose_images.py`.
- Each one reads originals from `LIBRARY_ROOT`; a missing file says
  «run `library.py fetch <path>`», not a bare FileNotFoundError.
- **Check:** `kb.py page <pdf> <n> --mode layout` works with the cache's PDFs
  renamed away; unittest suite green.

### 5. Create munzfuss-corpus

- Proposed per-directory split (to confirm before moving):
  - corpus: `fogtman`, `schou`, `hanse`, `kancelliets_brevboeger`, `secher`,
    `norske_rigsregistranter`, `literature`, `rigslovgivning`, `wilcke`,
    `norges_gamle_love`, `munro`, `wayback` (PDF part), `_corpus.yml`;
  - harvest: `hede`, `numista`, `kmk`, `numismaster`, `ucoin`, `ikmk`, `bruun`
    (lots json), `danskmoent` (htm/json), `auctions`, and every other
    coin-source cache;
  - each mixed directory listed with its file-type split before the move.
- New repo with the corpus text (no PDF, no ALTO); `kb.py` reads works from
  `CORPUS_ROOT`, coin catalogues still from `HARVEST_ROOT`.
- **Check:** `kb.py build` gives the same work count (173) and the same hit
  set on five fixed test queries as before the split.

### 6. Guard

- pre-commit in munzfuss-harvest and munzfuss-corpus: refuse `*.pdf`,
  `alto/*.xml`, and any file > 50 MB; message points to `library.py add`.
- `add-source-work` skill: download into `LIBRARY_ROOT`, `library.py add`
  with the URL, text into the corpus repo.
- **Check:** a test commit with a dummy PDF is refused.

### 7. Rewrite munzfuss-harvest history

- Before: a bare mirror clone of munzfuss-harvest archived locally
  (`git clone --mirror`, tar) and kept until step 8 is verified.
- `git filter-repo` removing every path that moved to the library or the
  corpus; force-push.
- Consequence to accept: commits of the main repo before the rewrite point at
  harvest commits that no longer exist in the rewritten repo; old checkouts
  resolve the cache only from the archived mirror.
- Re-clone the submodule in the main checkout, bump the pointer, commit.
- **Check:** pack size on GitHub (`gh api repos/munzfuss/munzfuss-harvest
  --jq .size`) roughly 1.3–2 GB; `audit_health.py --fast` clean; a full build
  identical to before.

### 8. Docs

CLAUDE.md «Harvest cache», `docs/ARCHITECTURE.md` §«Harvest cache
(submodule)», `docs/PLAYBOOKS.md` PB-10, `scripts/kb/README.md`, the
`add-source-work` skill. Then the archived mirror may be deleted (curator's call).

### Optional

Time Machine on any external disk the curator already owns covers the whole
Mac, not only the library.

## Log

- 2026-11-25 — plan written; munzfuss-library created (private); Secher
  upload done, all six asset digests equal the local sha256.
- 2026-11-25 — step 1: `LIBRARY_ROOT` / `CORPUS_ROOT` in `paths.py`,
  `scripts/library/library.py`, `tests/test_library.py`.
- 2026-11-25 — step 2: library built, 396 records, verify clean.
