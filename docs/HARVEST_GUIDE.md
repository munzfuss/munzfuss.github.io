# Harvest Guide — pulling per-coin data from external sources

> **Read this before adding a new data source.** This document captures
> the harvest patterns established during the §AZ source-survey work
> (2026-05-16, four-source pre-1541 harvest pass). It explains the
> tier-based source architecture, the tool fallback chain, common
> pitfalls, and the per-source playbook for each existing harvester so
> future sessions don't re-discover what's already figured out.
>
> Companion docs:
> - `docs/SOURCES.md` — per-source policy + known-issues log
> - `docs/research/denmark_pre_1541_source_survey.md` — canonical
>   example of a source-survey pass
> - `docs/PLAYBOOKS.md` PB-10 — committing harvest cache changes

## TL;DR

For per-coin coverage of a new scope (location × period):

1. **Survey first** — `docs/research/<location>_<period>_source_survey.md`
2. **Tier candidate sources** by access cost:
   - **Tier 1** — local caches (already harvested) — zero web cost
   - **Tier 2** — public HTML via Python urllib (direct fetch)
   - **Tier 3** — JS-rendered HTML via Chrome MCP (for discovery), urllib for known URLs
   - **Tier 4** — paywalled / Cloudflare-protected — defer or document as negative
3. Per source, build **three scripts** in `scripts/`:
   - `fetch_<source>_<scope>.py` — discover + fetch (with manifest)
   - `parse_<source>_<scope>.py` — HTML → structured JSON sidecars
   - `maintenance/build_<source>_<scope>_seed.py` — JSON → seed YAML
4. **Cache shape**: `scripts/cache/<source>/<scope>/` (submodule). Commit submodule first, then bump pointer in main repo (per PB-10).
5. **Seed output**: `data/seed/<source>/<scope>.yml` for §BF promotion.

## §AZ Tier matrix (Danish-realm 1514-1541 example)

| Tier | Source | Access | Entries | Lessons |
|---|---|---|---:|---|
| 1 | Bruun PDFs (`scripts/cache/bruun/lots/part*.json`) | local | 38 | Already parsed; filter by year+region |
| 1 | Wilcke 1950 (`scripts/cache/wilcke/.../pages/wilcke_*.txt`) | local | ordinance specs (no per-coin) | Master spec tables hand-extract into `fuesse.yml` |
| 2 | danskmoent.dk Galster | urllib | 79 | Uniform HTML, easy regex parse |
| 2 | Numista per-coin HTML | urllib + 30s pauses | 56 | NOT the v3 API — distinct route, no quota |
| 3 | NumisMaster MC_NNNNN | urllib for known IDs; Chrome MCP for search | 3 (sample) | Hub vs leaf IDs; JS-rendered search; pre-Krause «MB#» numbering |
| ✗ | ucoin.net | Cloudflare-blocked anonymously | (deferred) | §M ucoin harvest tracks ~50-req/session limit |

Total §AZ harvest: **176 entries across 4 active sources**.

## Decision tree — when adding a new harvest source

```
        Is the data ALREADY in a local cache?
                       |
            ┌──────────┴──────────┐
          yes                    no
           |                      |
   Tier 1: skip fetch,        Is the source HTML?
   write parse + seed-        ┌──────────┴──────────┐
   builder only             yes                    no
                             |                      |
                  Does urllib return 200       Other format
                  with full content?          (PDF/scan/image)
                  ┌──────────┴──────────┐         |
                yes                    no    See «PDF sources» below
                 |                      |
       Tier 2: fetch via         JS-rendered SPA?
       Python urllib with               |
       30s pauses + polite UA     ┌─────┴─────┐
                                yes           no
                                 |             |
                       Tier 3: Chrome MCP   Tier 4: skip
                       for discovery, then  (paywalled,
                       urllib for known     captcha-only,
                       per-coin URLs        non-public).
                                            Document as
                                            negative finding.
```

## Tool fallback chain

Per CLAUDE.md «Tool fallback chain — never stop on first failure»:

1. **WebSearch** — cheapest, find URLs + broad topical hits
2. **WebFetch** — single URL → small-model summary (often blocked by aggressive bot defences)
3. **Apify rag-web-browser** — bypasses some 403s via Apify infra
4. **Chrome MCP** (`mcp__Claude_in_Chrome__*`) — real Chrome session, bypasses all bot defences
5. **Python urllib direct** — for sources where direct HTTP works (verify with a single probe first)
6. **Ask user** — paste page HTML / screenshot into chat

For PDF content: use `pdf-viewer` MCP (`mcp__pdf-viewer__display_pdf` + `interact`).

## Common pitfalls (and fixes)

### Python urllib User-Agent encoding

Default urllib header encoding is **latin-1**. Special chars (em-dash `—`, ñ, etc.) raise `UnicodeEncodeError`. All fetches fail silently.

✗ Bad: `"Mozilla/5.0 (research — muentzfuesse project)"` (em-dash breaks it)
✓ Good: `"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7; rv:121.0) Gecko/20100101 Firefox/121.0"` (ASCII-only)

The §AZ Tier 3 first attempt failed all 48 fetches at the header-encoding step before any network round-trip. Detect via: if 100% failure rate, suspect UA encoding.

### Numista API budget rule

CLAUDE.md «Numista API budget» targets **`api.numista.com`** quota (200 free calls/24h). HTML scrape at **`en.numista.com/<N>`** is a distinct route with no per-request budget.

For bulk harvest: use HTML route. The §AZ Tier 3 harvest of 56 pages via `en.numista.com` did NOT touch the API quota.

### Numista session-cookie limit (~50 cumulative requests)

Per `docs/SOURCES.md §13.1`: ~50 cumulative requests per session-cookie trigger Cloudflare 403, regardless of pacing.

For >50 fetches:
- Wait ~24h between sessions (cookies reset)
- Use Chrome MCP (real browser, different rate limit)
- Pause 30-60s/page and stay under 50 cumulative per script run

The §AZ Tier 3 harvest (56 pages × 30s) completed with zero failures — under the 50-per-session threshold accounting for in-flight cookie state.

### Harness Bash `sleep` restrictions

Long leading `sleep N` commands are blocked by the harness. Solutions:
- Run sleep **inside Python** (`time.sleep()`) — works fine in `.venv/bin/python -c '...'`
- Run with `run_in_background: true` (script self-paces)
- Use `Monitor` with until-loop for completion signals
- Don't chain shorter sleeps to work around the block

### Chrome MCP JS-blocked queries

`javascript_tool` calls that return cookie/query-string data are blocked by the extension. Use:
- `find` tool (semantic NL query)
- `read_page` tool (accessibility-tree)
- `get_page_text` (plain text)

For URL/href extraction from rendered DOM: `read_page` with `ref_id` of the link element → returns the href attribute.

### Background-task progress tracking

`run_in_background: true` Bash tasks don't flush stdout until exit. To track progress mid-flight:
- Have the script write a tracking file (e.g. count of completed entries)
- Use `Monitor` with an until-loop checking that file
- Don't `tail -f` the output file — Python stdout buffering means it's empty until exit

### Submodule commit dance

`scripts/cache/` is a git submodule (private repo `munzfuss-harvest`). After adding cache files:

```bash
cd scripts/cache && git add <source>/<scope>/ && git commit -m "..." && cd ../..
git add scripts/cache scripts/<fetcher>.py ...  # bump submodule pointer + main scripts
git commit -m "seed(<source>): ..."
```

See PB-10 for full diagnosis when `git status` shows `modified: scripts/cache (new commits)`.

## Per-source playbook

### Hede 1957 — existing baseline

**Scope**: Christian III 1541+ through Christian X 1947 (Hede monograph window).
**Coverage gaps**: pre-Christian-III rulers (Hans, Christian II, Frederik I) NOT in Hede.

- Scripts: `scripts/fetch_hede.py`, `scripts/parse_hede.py`, `scripts/maintenance/build_hede_denmark_seed.py`
- Cache: `scripts/cache/hede/<basename>.htm` + `.json` + `_manifest.json`
- URL space:
  - Reign overviews: `/c3hede.htm`, `/c4hede1.htm`, …
  - Per-coin: `/chr/c<N>h<NUM>.htm`, `/fr/f<N>h<NUM>.htm`
  - Norway sub-folder: `/norge/…`

### Bruun PDFs — already parsed

**Scope**: Stack's Bowers L. E. Bruun Collection 2024-2026, 4 PDF parts.
**Coverage**: per-specimen brutto + NGC grade + rarity + cross-refs (Sieg / Schou / Galster / Fr / Lange / Dav / KM / Hede).

- Parsed: `scripts/cache/bruun/lots/part{1,2,3,4}.json`
- Page text: `scripts/cache/bruun/pages/part{1,2,3,4}.txt`
- Raw PDFs: `scripts/cache/bruun/part{1,2,3,4}.pdf` (read via `pdf-viewer` MCP for new lots)

**Seed builder pattern**: `scripts/maintenance/build_bruun_denmark_seed.py` reads JSON, filters by year/region, normalises to project seed shape. Mirror for new scopes.

**Gotchas** (lessons from §AZ Tier 1):
- `region` field has typos: `"NORW AY "` (space-injected NORWAY)
- `ruler` field sometimes captures mintmaster: «Hans Seyer» → `ruler="Hans"`. Re-parse from `meta_line` for actual ruler
- `year` may be a stray catalog-ref token: Sieg-1535 on a medieval Penny lot → year=1535 spuriously. Reject `ND (1[01]\d\d-...)` ranges before trusting `year`

### Wilcke 1950 — already cached

**Scope**: J. Wilcke *Renæssancens Mønt- og Pengeforhold 1481-1588*, 8 chapter TXT files.
**Use case**: ordinance-level spec tables (Bruttovægt + Lødighed + Stkr/Mark) for `data/shared/fuesse.yml` Müntzfuß-definitions.

- Cache: `scripts/cache/wilcke/renaessancens_moent_1950/pages/wilcke_7-{1..8}.txt`
- No automated parser — hand-extract from chapter tables when defining Müntzfüße
- Companion: `docs/research/wilcke_1514_1541_specs.md` captures the canonical spec tables for §BF use

### IKMK Berlin — existing

**Scope**: Münzkabinett Berlin online catalog. Reference per `docs/SOURCES.md §8.1`.

- Scripts: `scripts/fetch_ikmk.py` + `scripts/audit_ikmk_index.py`
- URL pattern: `https://ikmk.smb.museum/object?id=18205NNNN` returns JSON
- Cache: `scripts/cache/ikmk/<id>.json`

### danskmoent.dk Galster page series (added 2026-05-16)

**Scope**: pre-Christian-III rulers (Hans 1497+, Christian II 1513-1523, Frederik I 1523-1533, Christian III pre-1541). Fills the gap Hede 1957 doesn't cover.

**Result**: 79 in-scope entries from 110 cached pages (1514-1541 window).

- Scripts: `scripts/fetch_galster.py`, `scripts/parse_galster.py`, `scripts/maintenance/build_galster_denmark_seed.py`
- Cache: `scripts/cache/danskmoent/galster/<basename>.htm` + `.json` + `_manifest.json`
- URL space:
  - Reign-level indexes: `/c2galst.htm` (Christian II), `/f1galst.htm` (Frederik I)
  - Per-coin: `/chr/c<N>g<NUM>.htm`, `/fr/f<N>g<NUM>.htm`
  - Norway sub-folder: `/norge/n<r>g<NUM>.htm`
  - Christian III pre-1541: probe range `/chr/c3g{92..135}.htm` (NO `/c3galst.htm` index page exists)
  - Companion articles: `/artikler/*.htm`, `/ernst/*.htm` (Ernst NN&Aring; reprints, Moesgaard 2018 PDF links)

- Per-coin data shape (sample `/fr/f1g46.htm`):
  - H1 line: «Frederik 1., 1 Ungersk gylden 1531»
  - Description block: «Forside: …, bagside: … (Galster 46, Schou 1, Jensen/Skjoldager T-41/45)»
  - Specs: `Bruttovægt: 3,49g`, `Finhed: 0,986`, `Finvægt: 3,44g`
  - Inscription with translation
  - Litteratur block (Ernst, Jensen-Skjoldager, etc.)

- Parser quality (110-page corpus): ruler 92%, year 83%, mint 91%, cross-refs 57%, specs 42% (empty pages are companion-article links, correctly skipped)

### Numista per-coin HTML route (added 2026-05-16)

**Scope**: Numista catalog cross-reference + photo source + per-specimen brutto + diameter + obverse/reverse lettering.

**Result**: 56 entries from `en.numista.com/<N>` HTML pages (47 Denmark + 8 Norway, 1514-1541 + boundary 1541 Hede-validation).

- Scripts: `scripts/fetch_numista_pre1541.py`, `scripts/parse_numista_pre1541.py`, `scripts/maintenance/build_numista_pre1541_seed.py`
- Cache: `scripts/cache/numista/denmark_pre_1541/n<N>.html` + `.json`
- URL pattern: `https://en.numista.com/<N>` direct per-coin page
- Catalog browse: `/catalogue/index.php?e=<country>&...&p=<N>&q=<per_page>` (use Chrome MCP)

**N# list compilation**:
1. Browse catalog page via Chrome MCP → `find` tool for coin links
2. Capture hrefs via `read_page` with `ref_id`
3. Hardcode N# list in the fetcher script
4. Run with 30s pauses + ASCII-only UA

**Parser data shape**:
- `<th>Field</th><td>Value</td>` table for Features
- References: `<a class="fiche_catalogue">SIEG</a>#&#8239;C2-1` style
- Obverse / Reverse: `<h3>Obverse</h3>` block with description + Script + Lettering + Translation
- King names have whitespace padding + parenthesised native form: «Frederick I                    (Frederik I)» — collapse whitespace + strip parens

### NumisMaster MC_NNNNN (added 2026-05-16)

**Scope**: KM-based commercial catalog. Pre-1604 sparse, but Schleswig-Holstein-duchy uses pre-Krause «MB#» (Madai-Bach) numbering.

**Result**: 3 entries (initial sample), full sub-territory walk deferred.

- Scripts: `scripts/parse_numismaster_pre1541.py`, `scripts/maintenance/build_numismaster_pre1541_seed.py` (no fetcher — pages added on demand)
- Cache: `scripts/cache/numismaster/denmark_pre_1541/MC_<N>.html` + `.json`

**URL patterns** (DO NOT confuse hub vs leaf IDs):
- **Per-coin page**: `https://numismaster.com/MC_<N>` — PUBLIC, full data (only price columns are subscription-gated)
- **Search results**: `https://numismaster.com/?id=-<facet_id>&advancedsearch=true&pageno=N` — JS-rendered, requires Chrome MCP for MC_ link extraction

**Catalog hierarchy**:
- **Hub IDs** (geographic intro pages, NOT coin lists):
  - `-1005793` = DENMARK
  - `-1006970` = NORWAY
  - `-1005794` = GLÜCKSTADT
- **Leaf IDs** (coin search results):
  - `-10012282` = HOLSTEIN-GOTTORP-RENDSBORG (search results visible)
  - 600+ unique sub-territory IDs discovered under Denmark hub
- Distinguishing: leaf-ID page has MC_NNNNN coin entries via Chrome MCP `find`; hub-ID page has «century intro», maps, geographic links

**Per-coin data shape**:
- Country / Catalog # (KM# or MB# Madai-Bach pre-Krause) / Political period / Coinage entity / Denomination / Date / Ruler / Mint
- Composition / Mass / Fineness / Actual weight (fein) / Melt value
- Obverse + Reverse descriptions + legend transcriptions (Latin)
- General note with cross-refs (Sch# Schou, L# Lange, Fr# Friedberg)

**Workflow**:
1. Chrome MCP navigate to leaf-ID search URL: `/?id=-<facet>&advancedsearch=true&pageno=1`
2. `find` tool: query for «coin entries with year ranges 1500-1550» → returns MC_NNNNN IDs with year context
3. For pre-window MC_NNNNN IDs, fetch `https://numismaster.com/MC_<N>` via Python urllib (works fine — no Cloudflare gate on per-coin pages)
4. Parse + seed

**Pre-Krause «MB#» numbering**: Madai-Bach catalog covers Schleswig-Holstein-duchy 16th-17th c. coins NOT covered by KM. Both KM and MB appear on NumisMaster pages with the same UI («Catalog #: MB# 33»).

### ucoin.net (deferred per §M)

**Scope**: user-edited catalog overlapping Numista coverage.

**Status**: Cloudflare-blocked on anonymous fetches (HTTP 403). Project's §M (ucoin Composition harvest) tracks ~490 uncached URLs. Resume conditions: ~24h cooldown, IP switch, or manual Cloudflare-challenge pass via normal browser.

Per-session limit: ~50 cumulative requests at any pacing 2.5-20 s.

## Cache directory conventions

```
scripts/cache/   ← git submodule (munzfuss-harvest private repo)
├── hede/
│   ├── _manifest.json
│   ├── c<N>hede<P>.htm                       # overview pages
│   ├── c<N>h<NUM>.htm + .json                # per coin
│   └── norge/                                # Norway sub-folder
├── bruun/
│   ├── part{1,2,3,4}.pdf                     # raw
│   ├── lots/part{1,2,3,4}.json               # parsed
│   └── pages/part{1,2,3,4}.txt               # page text
├── wilcke/
│   └── renaessancens_moent_1950/
│       ├── wilcke_7-{1..8}.pdf
│       └── pages/wilcke_7-{1..8}.txt
├── ikmk/
│   └── <id>.json                             # IKMK Berlin
├── danskmoent/
│   └── galster/
│       ├── _manifest.json
│       ├── c2galst.htm + f1galst.htm         # reign-level indexes
│       └── (chr|fr|norge)_<basename>.htm + .json
├── numista/
│   ├── <N>.json                              # legacy API-derived
│   └── denmark_pre_1541/
│       └── n<N>.html + .json                 # HTML-route harvest
├── numismaster/
│   └── denmark_pre_1541/
│       └── MC_<N>.html + .json
├── ucoin/
│   └── … (see docs/SOURCES.md)
└── rigsarkivet/
    └── tk_160_diverse_moentsager/            # archive page scans + JSON index
```

## Seed YAML schema

Required fields per coin entry (mirror existing `data/seed/hede/denmark.yml`):

```yaml
- id: dk-<source>-<NN>               # e.g. dk-galster-c2g-37 / dk-numista-264676 / dk-bruun-14708
  fuss: seed_unsorted                # until §BF promotes
  phase: <source>                    # «bruun» / «galster» / «numista» / «numismaster»
  kind: kurant                       # | scheide | tarif | gedenk
  nominal: …
  year_label: …
  year_first: …
  year_last: …
  year_ranges: [[YYYY, YYYY], ...]
  ruler: …
  mint: …
  catalog:                           # all available cross-refs
    sieg: …
    schou: …
    galster: …
    friedberg: …                     # gold only
    lange: …                         # S-H only
    davenport: …                     # Taler-size silver only
    hede: …                          # 1541+ only
    km: …                            # 1604+ usually
    mb: …                            # pre-Krause SH duchy
    bruun_collection_id: …
    numista: …
    numismaster_mc: …
  metal: gold | silver | billon | copper
  fineness: 0.NNN                    # null if not attested
  weight_rough_g: N.NN               # null if not attested
  issuing_entity: danish_realm | norwegian_realm | schleswig_holstein_duchy
  verified: false                    # until §BF promotes
  fineness_verified: bool
  weight_rough_verified: bool
  mint_verified: bool
  sources:
    - type: literature
      url: https://...               # if applicable
      ref: …
  verification_note:
    de: …                            # source-specific note
    en: …
    uk: …
```

Optional source-specific enrichment fields (carry through if present):
- `mintmaster` (Bruun, Galster, Numismaster)
- `rarity` / `ngc_grade` (Bruun)
- `bruun_collection_id` / `bruun_part` / `bruun_lot_no` / `bruun_page` (Bruun)
- `inscription` / `obverse` / `reverse` (Galster, Numista, Numismaster)
- `photo_credit` / `numista_rarity_index` (Numista)
- `political_period` / `coinage_entity` (Numismaster)

## Extending to a new period or location

1. **Survey**: write `docs/research/<location>_<period>_source_survey.md` first
2. **Tier candidate sources**: 14-source matrix in `denmark_pre_1541_source_survey.md` is a template
3. **Pick most similar existing harvester as template** (the four added in §AZ — `fetch_galster.py`, `fetch_numista_pre1541.py`, `parse_numismaster_pre1541.py` plus the existing `fetch_hede.py` cover all major patterns)
4. **Copy + adapt** fetch/parse/build_seed scripts. Source-specific data-shape changes mostly live in the parser.
5. **Test on a sample** (5-10 pages) before full harvest
6. **Submodule commit pattern** per PB-10

## Extending an existing harvest

For pulling MORE entries from an already-harvested source (e.g. additional Schleswig-Holstein sub-territories from NumisMaster):

1. Read the source's existing fetcher script to understand URL pattern + ID list
2. Use Chrome MCP to navigate the search URL + `find` tool to extract new MC_ links
3. Add IDs to the harvester's list
4. Run harvester — already-cached entries skip automatically, only new ones fetch
5. Parser + seed builder are idempotent — rerun to pick up new entries
6. Commit submodule first, then bump pointer in main repo

## When NOT to harvest

Skip a source when:
- **Paywall** on per-coin data (subscriber-only). NumisMaster's price columns are gated; the catalog data itself is public — distinguish carefully.
- **CAPTCHA** on per-page access. Bot defences that require a human in the loop block both urllib and Chrome MCP automation paths.
- **Out-of-scope KM numbering**. Krause-Mishler numbering for Denmark starts ~1604; pre-1541 KM# coverage is sparse-to-zero. Search for the pre-Krause alternative numbering (MB# Madai-Bach, MNI# etc.) before assuming the source has nothing.
- **Already covered**. If another source has the same coins with the same cross-references, the marginal value of a new harvest is low. Document as «covered by source X».

Document negative findings in the source survey for future-session reference — don't make the next person re-discover the dead end.

## Anti-pattern catalog

- **Hardcoded base URL in three places**: keep BASE constant in fetcher, reuse via import in parser + seed-builder if they need it (mostly they don't).
- **Single big script**: split into fetch + parse + seed-builder so each step is rerunable in isolation.
- **No manifest**: write `_manifest.json` listing discovered URLs so re-runs can verify completeness.
- **Mixed cache shapes**: per-source cache dir + consistent `.html`/`.pdf` + `.json` sidecar pattern. Don't mix raw and parsed into the same file.
- **Trusting `lot.year` blindly**: always validate against `meta_line` / context (Bruun parser sets year=stray-catalog-ref-token on medieval Penny lots).
- **Trusting `lot.ruler` blindly**: re-parse from `meta_line` body when source has «Hans Seyer» mintmaster vs «Hans» king ambiguity.
- **Latin-1 User-Agent**: ASCII-only UA strings or all fetches silently fail.

## Future enrichment opportunities (open)

These were identified during §AZ but deferred:

- **NumisMaster full Schleswig-Holstein walk** — 600+ sub-territory IDs under Denmark hub; current §AZ Tier 4 captures only Holstein-Gottorp-Rendsborg sample. Future session: walk each leaf ID via Chrome MCP + harvest MC_NNNNN pages.
- **ucoin.net resume** — §M tracking ~490 uncached URLs; resume when Cloudflare cooldown passes.
- **Hans 1496-1513 + Erik VII 1397-1439 backfill** — pre-1514 outside §BI anchor but valuable research-doc context. Could be added as `data/seed/<source>/denmark_pre_1514_outliers.yml` for completeness.
- **Münzkabinett Berlin IKMK full Denmark walk** — IKMK has Christian II / Frederik I / Christian III specimens that would enrich photo + curator-spec data. Current `scripts/cache/ikmk/` has partial coverage.

## See also

- `docs/SOURCES.md` — per-source policy, URL patterns, known-issues log
- `docs/PLAYBOOKS.md` PB-2 (ucoin harvest session), PB-10 (committing harvest cache)
- `docs/research/denmark_pre_1541_source_survey.md` — canonical survey example
- `docs/research/wilcke_1514_1541_specs.md` — ordinance-spec companion to harvested coin data
