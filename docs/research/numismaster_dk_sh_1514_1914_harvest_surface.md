# NumisMaster harvest surface — Schleswig-Holstein + Denmark-realm 1514-1914

> **Status: PRELIMINARY surface 2026-05-16.** This file scopes the
> expansion of the §AZ Tier-3 NumisMaster harvester from its current
> pre-1541 sample (3 cached MC_NNNNN entries) to **full mission-window
> coverage** for all Schleswig-Holstein issues regardless of ruler PLUS
> Denmark + Sweden + Norway under Danish rule (1514-1914 mission anchor).
>
> **Scope of THIS surface = cache acquisition only, RAW.** Goal of the
> first pass: pull **all `MC_<N>.html` files in mission window** into
> the local cache (`scripts/cache/numismaster/<sub_scope>/`) **with full
> page content preserved verbatim** — no stripping, no extraction, no
> trimming. Whatever bytes the NumisMaster server returns get written
> to disk as-is. The rationale: avoid re-hitting NumisMaster repeatedly
> during downstream data work (rate-limit + Cloudflare risk grows with
> cumulative traffic), AND avoid having to re-fetch if the parser
> evolves to need fields we initially ignored.
>
> Concretely:
> - **In scope:** Phase 1 (catalog walk → `leafs.json` + saved
>   raw-HTML of every hub/leaf search page visited), Phase 2 (per-leaf
>   MC_ID enumeration → `mc_index.json` + raw-HTML of every paginated
>   search page), Phase 3 (scope filter to decide what to fetch — by
>   year-range + ruler only, NO dedup against curated), Phase 4 (bulk
>   urllib fetch of `MC_<N>.html` → cache, **full response body**).
> - **Out of scope for this pass:** Phase 5 (parse HTML → JSON
>   sidecars), Phase 6 (seed builder), §BF promotion, AND dedup
>   against curated `data/locations/*.yml`. These run later from the
>   LOCAL cache, with no further NumisMaster traffic. Dedup logic
>   belongs to the parse/seed phase — at cache-acquisition time we
>   fetch every in-window MC_ID even if our curated data already has
>   it, because the raw page may carry obverse/reverse legends or
>   composition fields that enrich the existing entry.
>
> The previous source survey
> (`denmark_pre_1541_source_survey.md`, §14) marked numismaster.com as
> «NOT a usable source» based on probes of the `/coins/<facet_id>` and
> homepage routes. That verdict was **too pessimistic** — the
> per-coin `https://numismaster.com/MC_<N>` route does serve full
> public data (price columns gated, catalog data not). The §AZ work
> proved this with three cached Schleswig-Holstein entries (MB# 22,
> MB# 33, MB# 39 = Friedrich I Witten 1516, Christian III 6 Pfennig
> 1534-54, Christian III Goldgulden 1535). This surface scopes the
> full extension.
>
> **Not a finished harvest plan yet.** Phase 1 (catalog walk to
> enumerate leaf-IDs) has not run. Coverage / entry-count estimates
> are «order of magnitude» until the live walk runs.
>
> Companion docs:
> - `docs/HARVEST_GUIDE.md` — tier-based source architecture
> - `docs/SOURCES.md` §0 (quick-reference matrix) + per-source policy
> - `docs/research/denmark_pre_1541_source_survey.md` §14 — original
>   negative finding (now superseded for the `/MC_` route)

## 1 — Scope

### 1.1 Territorial scope (4 sub-scopes, all rooted in NumisMaster's «Country» facet)

| Sub-scope | NumisMaster country label(s) | Temporal window | Notes |
|---|---|---:|---|
| **A. Schleswig-Holstein** — ALL rulers + sub-territories | `SCHLESWIG-HOLSTEIN`, plus cadet-line labels Glückstadt / Holstein-Gottorp / Holstein-Plön / Holstein-Schauenburg / Holstein-Sonderburg-Plön / Holstein-Sonderburg-Beck / Lübeck-Bishopric-in-HG-family | 1514-1864 | Includes royal-Danish issues struck in Holstein (Glückstadt royal mint 1623+) + ducal cadet lines under Oldenburg Haus. **Post-1864 mint closure**: Prussian annexation ended SH local minting; no SH-labelled coinage 1864-1914 expected in NumisMaster. Probe will confirm empty result. |
| **B. Denmark** | `DENMARK` | 1514-1914 | Royal-issue coinage, København + Helsingør + (war-time) Roskilde + Ribe + Aarhus + Husum (royal-side issues) |
| **C. Norway under Danish rule** | `NORWAY` | 1514-1814 | Treaty of Kiel 14 Jan 1814 ends Danish rule; post-1814 Norwegian coinage is Swedish-union / independent → OUT of scope. Mints: Oslo + Bergen + Kongsberg (Christian IV 1628+) |
| **D. Sweden under Christian II (Kalmar Union)** | `SWEDEN` | 1514-1523 | Christian II as Kalmar-Union king until Gustav Vasa breaks union June 1523. Mints: Stockholm + Västerås + Söderköping. Excludes ALL post-1523 Swedish issues (own dynasty) |

### 1.2 Temporal anchors

| Anchor | Year | Source | Why this anchor |
|---|---:|---|---|
| Lower (DK + SH + Norge + Sweden-DK) | **1514** | CLAUDE.md mission §«Mission temporal scope — dual anchor by jurisdiction» | Christian II Lovkompleks (Møntordning af Sommeren 1514 + Norge extension 3 August 1514) |
| Norway upper | **1814** | Treaty of Kiel 14 Jan 1814 | End of Danish-Norwegian double-monarchy |
| Sweden upper | **1523** | Election of Gustav Vasa as King of Sweden, 6 June 1523 | End of Kalmar-Union period that placed Sweden under Christian II |
| DK + SH upper | **1914** | CLAUDE.md mission §«Mission temporal scope» | End of precious-metal anchor era |

### 1.3 Out-of-scope (explicit)

- **Iceland / Færøerne / Greenland / Danish West Indies** under Danish rule — NOT requested in current scope; defer.
- **Pre-1514 Denmark/Norway/Sweden** — Galster + Hede pre-1541 already harvested under §AZ; pre-1514 sits below the mission anchor.
- **Post-1814 Norway** — Swedish-union (1814-1905) + independent (1905+).
- **Sweden 1523-1914** — Swedish dynasty post-Vasa, sits outside Danish-realm mission.
- **Post-1914 Denmark / Schleswig-Holstein** — mission upper bound is 1914.
- **Patterns / trial strikes / off-strikes / exonumia** — per CLAUDE.md §9 (exclusion rules); filter at parse time.

## 2 — NumisMaster catalog topology

### 2.1 What is known (from §AZ + cached data)

NumisMaster organises catalog content as **hub facets** (geographic / political intro pages, no coin list) and **leaf facets** (search-result pages listing MC_NNNNN per-coin entries). Per CLAUDE.md `docs/HARVEST_GUIDE.md` §«Per-source playbook — NumisMaster»:

```
URL pattern: https://numismaster.com/?id=-<facet_id>&advancedsearch=true&pageno=N
            └── JS-rendered search results; requires Chrome MCP for MC_ extraction
URL pattern: https://numismaster.com/MC_<N>
            └── per-coin page; PUBLIC HTML, Python urllib OK (no Cloudflare gate)
```

### 2.2 Known facet IDs (from §AZ)

| Facet ID | Label | Type | Notes |
|---|---|---|---|
| `-1005793` | DENMARK | **hub** | Geographic intro page; no coin list |
| `-1006970` | NORWAY | **hub** | Same |
| `-1005794` | GLÜCKSTADT | **hub** | Geographic; expected to roll up into leafs (Royal-DK-in-Glückstadt vs HG-Glückstadt) |
| `-10012282` | HOLSTEIN-GOTTORP-RENDSBORG | **leaf** | Search results visible; 3 MB#-numbered entries 1514-1541 sample |

### 2.3 Known per-coin MC_ IDs (3, all SH duchy)

| MC_ID | Country | Cat# | Denom | Year | Ruler | Cached in §AZ |
|---|---|---|---|---:|---|:-:|
| 167727 | SCHLESWIG-HOLSTEIN | MB# 33 | 6 Pfennig | 1534-1554 | Christian III | ✓ |
| 167729 | SCHLESWIG-HOLSTEIN | MB# 22 | Witten | 1516 | Friedrich I | ✓ |
| 167745 | SCHLESWIG-HOLSTEIN | MB# 39 | Goldgulden | 1535 | Christian III | ✓ |

### 2.4 What is unknown (to discover in Phase 1)

The HARVEST_GUIDE says «600+ unique sub-territory IDs discovered under Denmark hub». That implies the catalog topology under each hub goes:

```
hub  -1005793 DENMARK
 ├── leaf -??????? Christian II 1513-1523
 │     └── MC_NNNNN per type
 ├── leaf -??????? Frederik I 1523-1533
 ├── leaf -??????? Christian III 1534-1559
 ├── …
 └── leaf -??????? Christian X 1912-1947  (cuts at 1914 for our scope)

hub  -1006970 NORWAY
 ├── leaf -??????? Christian II Norge
 ├── …
 └── leaf -??????? Frederik VI Norge (1808-1814)

hub  -1005793 → branch SCHLESWIG-HOLSTEIN
 ├── leaf -10012282 HOLSTEIN-GOTTORP-RENDSBORG  (known)
 ├── leaf -??????? HOLSTEIN-GOTTORP main line
 ├── leaf -??????? HOLSTEIN-PLÖN
 ├── leaf -??????? HOLSTEIN-SONDERBURG-PLÖN
 ├── leaf -??????? HOLSTEIN-SCHAUENBURG
 ├── leaf -??????? SCHLESWIG-HOLSTEIN royal (Glückstadt)
 ├── leaf -??????? LÜBECK-BISHOPRIC-IN-HG-FAMILY (if catalogued)
 └── leaf -??????? post-1864 PRUSSIAN-PROVINCE-SH
```

The exact tree shape will only be known once Chrome MCP walks the `/?id=-<hub>` JS-rendered pages. Phase 1 below documents the walk procedure.

## 3 — Phased harvest plan

### Phase 1 — Catalog walk (discover leaf IDs)

**Tooling**: Chrome MCP only (search results are JS-rendered; `urllib` returns skeleton).

**Sub-scope order (per user 2026-05-16):** A. SH first → B. DK → C. Norge → D. Sweden-CII. Each sub-scope completes Phase 1+2+3+4 before the next starts. This staging reduces per-batch failure-blast-radius and lets us tune fetch cadence based on early-sub-scope behaviour before the larger DK batch begins.

**Procedure**:

1. `list_connected_browsers` → `select_browser` → `tabs_context_mcp(createIfEmpty: true)`.
2. For each hub-ID in {`-1005793` DK, `-1006970` Norge, `-1005794` Glückstadt}: navigate to `https://numismaster.com/?id=<hub>` and read the page tree.
   - **Expectation**: a list of sub-territory / sub-period links (each a leaf with its own facet ID).
   - **Capture**: hrefs via `read_page` with `ref_id` of each link element. Build a `leafs.json` map: `{ "<label>": "<facet_id>", ... }`.
   - **Raw-page preservation**: write the full Chrome-rendered page (via `get_page_text` for plain-text + the accessibility-tree dump from `read_page`) into `scripts/cache/numismaster/_walks/hub_<hub_id>.txt` + `.snapshot.json` so the discovery process is reproducible without re-walking.
3. **Schleswig-Holstein** specifically: there is NO single hub ID — SH appears as a country-equal-to-Denmark sibling AND as a sub-territory under Denmark. Probe both:
   - `numismaster.com/?id=-1005793` (DK hub) → look for «SCHLESWIG-HOLSTEIN» / cadet-line labels in the link list
   - Search route `numismaster.com/?searchstr=SCHLESWIG&advancedsearch=true` → may surface stand-alone SH leaf IDs
4. **Sweden under Christian II**: search route `numismaster.com/?searchstr=Christian+II+Sweden&advancedsearch=true` OR via the SWEDEN hub (probably `-1005???`) → filter to 1514-1523 only (post-1523 Vasa-Swedish entirely out of scope).
5. **Cadet-line completeness rule (per user 2026-05-16):** every leaf-ID surfaced under SH, DK, Norge, Sweden-CII walks is harvested in full — even leafs reporting only 1-2 coins. No low-yield gatekeeping. The completeness is the point of this pass.

**Output artifact**: `scripts/cache/numismaster/leafs.json` — discovered leaf-IDs grouped by sub-scope (A/B/C/D from §1.1). Manual-curation step at end of Phase 1: the user reviews `leafs.json` and confirms which leafs to walk (in case the catalog surfaces unexpected sub-territories — e.g. «East-DANISH-WEST-INDIES» under DK hub that we explicitly exclude).

**Risk + mitigation**: NumisMaster search may have stale or sparse coverage for some sub-territories — e.g. Holstein-Sonderburg-Beck cadet line might not be catalogued. Document negative findings as «no leaf ID surfaced» rather than silently dropping; cross-check against Lange 1908-12 + Bobzin to confirm coverage gap is NumisMaster's (not ours).

### Phase 2 — Per-leaf MC_NNNNN enumeration

**Tooling**: Chrome MCP (search results JS-rendered).

**Procedure**:

1. For each leaf-ID confirmed in Phase 1: navigate to `https://numismaster.com/?id=<leaf>&advancedsearch=true&pageno=1`.
2. `find` tool with prompt: «coin entries with year ranges, return MC_NNNNN IDs and year ranges».
3. Paginate via `pageno=2..N` until results exhaust (HARVEST_GUIDE example showed pages 1-5+ on a populated leaf).
4. **Filter at this stage**:
   - For DK leaf: keep entries with `year_first >= 1514 AND year_last <= 1914`.
   - For Norge leaf: keep `year_first >= 1514 AND year_last <= 1814`.
   - For Sweden leaf: keep `year_first >= 1514 AND year_last <= 1523` AND ruler ∈ {Christian II}.
   - For SH leaf: keep `year_first >= 1514 AND year_last <= 1864`, ALL rulers regardless of cadet line.
5. **Raw-page preservation per leaf**: every paginated search page visited gets a Chrome-rendered snapshot saved into `scripts/cache/numismaster/_walks/leaf_<leaf_id>_p<N>.txt` + `.snapshot.json`. This lets future sessions re-extract MC_ID lists if the `find` query missed something, without re-hitting NumisMaster.

**Output artifact**: `scripts/cache/numismaster/mc_index.json` — `{ "<leaf_id>": [{ "mc_id": NNNNN, "year_first": YYYY, "year_last": YYYY, "denom": "...", "ruler": "..." }, ...] }`.

**Risk + mitigation**: `find` tool may miss MC_ links if pages have layout variations. Spot-check first 5 leafs by manually inspecting one page via `read_page` to confirm `find` extraction is complete. If gaps → fall back to `get_page_text` + regex on MC_NNNNN tokens. Because every page snapshot is cached (step 5), re-extraction does not require new fetches.

### Phase 3 — Scope filter (year-range + ruler ONLY, NO dedup)

**Tooling**: Python (no web access).

**Procedure**:

1. Load `mc_index.json` from Phase 2.
2. Apply the temporal + ruler filters per §1.1 as a safety net (already applied in Phase 2 but re-confirm):
   - Sub-scope A (SH): keep `year_first >= 1514 AND year_last <= 1864`.
   - Sub-scope B (DK): keep `year_first >= 1514 AND year_last <= 1914`.
   - Sub-scope C (Norge): keep `year_first >= 1514 AND year_last <= 1814`.
   - Sub-scope D (Sweden-CII): keep `year_first >= 1514 AND year_last <= 1523` AND ruler ∈ {Christian II}.
3. **NO dedup against `data/locations/*.yml`** — every in-scope MC_ID is fetched even if the project already has a curated entry for the same coin. Rationale: the raw page may carry fields (obverse/reverse legends, composition, Librios `political_period` codes) that enrich the existing entry; dedup decisions belong to the parse/seed phase, not cache-acquisition.
4. **Scale output**: build `mc_to_fetch.json = mc_index.json after year+ruler filter`. Report `len(mc_to_fetch)` per sub-scope so user can size Phase 4 batches.

**Risk + mitigation**: Phase 2's MC_ID enumeration may report year-ranges sloppily for types minted across decades (NumisMaster's `Date` field is a single string like `1534 - 1554`). Parser uses `year_first = min, year_last = max` from any 4-digit tokens. Edge cases (undated «n.d.» strikes, century-attributions) — capture into a separate `mc_undated.json` for manual review rather than silently dropping.

### Phase 4 — Per-coin urllib fetch (FULL RAW HTML)

**Tooling**: Python urllib (per HARVEST_GUIDE: `/MC_<N>` route does NOT require Chrome MCP; bot defences are on the search / `/coins/` routes only).

**Procedure**:

1. ASCII-only User-Agent (mandatory per HARVEST_GUIDE «Common pitfalls»).
2. 30s pauses between fetches (Numista session-cookie threshold lesson — NumisMaster may have similar limit; conservatively stay under 50/session, pause 30s).
3. **`run_in_background: true`** + progress tracking file (HARVEST_GUIDE «Background-task progress tracking»).
4. **Raw-preservation rule (critical, this is what makes the cache stable across parser revisions):**
   - Write the **full HTTP response body** to `MC_<N>.html` — no parsing, no stripping `<script>` tags, no truncation, no whitespace normalisation. `urllib.request.urlopen(...).read()` → file, byte-for-byte.
   - Save a sibling `MC_<N>.meta.json` with HTTP-level metadata: response `status`, `headers` (full dict including `Content-Type`, `Content-Length`, `Last-Modified`, `Server`, any `Set-Cookie` for debugging future Cloudflare issues), and the fetch wall-clock timestamp (`fetched_at`).
   - Do NOT pre-filter «extra» bytes (advertising blocks, JS-blocked subscription teasers, Librios CMS markup) — the page might use those for fields we don't yet extract. The parse phase decides what's signal vs noise; the cache phase preserves everything.
5. Cache shape: `scripts/cache/numismaster/<sub_scope>/MC_<N>.html` + `MC_<N>.meta.json` where `<sub_scope>` ∈ {`schleswig_holstein`, `denmark`, `norway`, `sweden_christian_ii`}.
   - Migrate existing `scripts/cache/numismaster/denmark_pre_1541/MC_167727,9,45.html` → `scripts/cache/numismaster/schleswig_holstein/`. For these three: the existing files are HTML-only (no `.meta.json`); re-fetch is OPTIONAL (we lose only the meta sidecar, not the HTML) — defer the re-fetch decision to when those three pages are next needed.
6. `_manifest.json` per sub_scope listing: every MC_ID, URL, fetched_at, response status, file size, HTTP `Content-Length` (for integrity check on re-runs). Top-level `_manifest.json` aggregates counts.

**Output artifact**: HTML + sibling `.meta.json` per MC_ID. Parser sidecars (`.json` data extraction) are produced **later in Phase 5**, NOT here — `.meta.json` is HTTP-metadata only.

**Risk + mitigation**: per-coin pages may have variant layouts for different eras (pre-1604 «MB#» numbering vs Krause «KM#» 1604+); since we save raw HTML the layout differences are deferred to Phase 5 parsing. No spot-test required for the cache phase itself — every byte that arrives is preserved as-is.

### Phase 5 — Parse + seed (DEFERRED — runs from local cache, no NumisMaster traffic)

**Out of scope for this surface.** Once Phase 4 completes the cache, parser + seed-builder run locally against `scripts/cache/numismaster/<sub_scope>/MC_*.html` without re-hitting NumisMaster. The scope notes here are kept as a forward reference so the cache shape collected in Phase 4 stays parser-ready.

Forward references (when this work is unfrozen later):

- Extend `scripts/parse_numismaster_pre1541.py` → rename/generalise to `scripts/parse_numismaster.py` (drop the `_pre1541` qualifier).
- Add KM# parser (currently only MB#).
- Add Madai-Bach «MB#» / Krause «KM#» / Schou «Sch#» / Lange «L#» / Friedberg «Fr#» / Sieg / Hede / Bruun cross-ref extraction.
- Handle Krause-volume disambiguation per CLAUDE.md §9 caveat (KM# scope tagged by `numismaster_country`).
- Handle post-1864 Prussian-province SH entries (Reichsmark era).
- Seed-builder: `scripts/maintenance/build_numismaster_seed.py` with `--sub-scope` flag → `data/seed/numismaster/{schleswig_holstein,denmark,norway,sweden_christian_ii}.yml`.
- Preserve Librios-internal codes (`PL...`, `CG...`) verbatim under `numismaster_political_period_id` / `numismaster_coinage_entity_id` — don't attempt to decode at seed time.

### Phase 6 — §BF promotion (out of harvest surface)

Seeds land in `data/seed/numismaster/*.yml`; promotion to curated `data/locations/*.yml` is a separate per-coin user-curation step tracked by the §BF TODO entry. This surface ends at Phase 4 (cache acquisition); Phase 5 (parse + seed) and §BF promotion are downstream activities run from the LOCAL cache.

## 4 — Scale estimate (order of magnitude)

| Sub-scope | Expected leaf IDs | Expected MC_ entries | Notes |
|---|---:|---:|---|
| A. Schleswig-Holstein | ~10-15 (royal + 7 cadet lines + post-1864) | ~600-1500 | Cadet-line catalogs are typically small (50-100 entries); royal-DK-in-SH is large (Glückstadt 1623-1813); post-1864 is German-Empire-Krause volume |
| B. Denmark | ~10-15 (one per ruler 1514-1914) | ~1500-3000 | 400 years of royal coinage; Krause catalog very dense for 1604+ |
| C. Norway under DK | ~8-12 | ~400-800 | Smaller scope (1514-1814 = 300 years), Norge-Hede 1971 already covers; expected overlap |
| D. Sweden under Christian II | ~1-2 | ~10-30 | Tiny window (9 years), few types known |
| **Total** | **~30-45 leafs** | **~2500-5300 MC_ entries** | Before dedup against curated; after dedup expect ~50-70% fresh |

**Budget implications**:

- Phase 1 (Chrome MCP catalog walk): ~30-45 leaf-page navigations + same-count of search-result-page reads. ~1-2 hours real-time.
- Phase 2 (MC_ID enumeration per leaf): ~30-45 leafs × ~2-5 pages each = ~100-200 Chrome MCP navigations. ~2-3 hours real-time.
- Phase 4 (urllib bulk fetch): ~2500-5300 fetches × 30s pause = **20-40 hours background runtime**. Run overnight in batches of ~500 (15-min batch buffers under conservative Cloudflare assumptions). Actual NumisMaster rate limit is unverified — test with first batch + look for 403s.
- Phase 5 (parser run): **deferred** — runs later from local cache, no further NumisMaster traffic.

**Stage gates**: ask user for go/no-go after Phase 1 (leafs.json review), after Phase 3 (scale + dedup report), and before each bulk-fetch batch in Phase 4. The session declares «done» after Phase 4 cache is in place — parsing runs in a separate session.

## 5 — Known pitfalls (transcribed from HARVEST_GUIDE + §AZ)

1. **Hub vs leaf ID confusion** — `-1005793` DK is a hub (geographic intro, no coin list). Don't try to enumerate MC_ from a hub URL.
2. **JS-rendered search results** — Chrome MCP mandatory for `/?id=-<leaf>` URLs; urllib returns skeleton-only.
3. **Per-coin route is public** — `/MC_<N>` works via urllib + ASCII UA. Don't waste Chrome MCP budget here.
4. **Latin-1 UA encoding** — pure-ASCII UA string only. Special chars (em-dash `—`, accented letters) silently fail.
5. **Krause-volume disambiguation** — KM# numbering restarts per country-volume; CLAUDE.md §9 caveat. Tag each seed entry's KM# with `numismaster_country` so cross-location dedup distinguishes DK-vol-KM#75 from SH-vol-KM#75.
6. **Pre-Krause MB# numbering** — Madai-Bach catalog covers SH-duchy 16th-17th c. NOT covered by KM. Both KM and MB appear on NumisMaster pages with the same UI; parser must accept both.
7. **«MB#» ambiguity** — Bruun data uses «MB#» for Swedish Tingström/Stiernstedt-Bonnier (`denmark_pre_1541_source_survey.md` §2 final note). NumisMaster's «MB#» = Madai-Bach (per §AZ Tier 4). **Different catalogues sharing the abbreviation**. The seed-builder must namespace these distinctly: `catalog.mb_madai_bach` ≠ `catalog.mb_tingstrom_sweden`. Cross-source merge logic at §BF promotion must NOT collide them.
8. **Norway in NumisMaster** — Norway is a separate hub from Denmark; Danish-rule period (1514-1814) is catalogued under the Norway hub WITH the ruler attribution still naming the Danish monarch. Don't filter out Norway entries that name «Christian IV» as ruler — they're in-scope for our Danish-rule window.
9. **Post-1864 Schleswig-Holstein** — under Prussian rule + German Empire. NumisMaster will catalog these under SCHLESWIG-HOLSTEIN country label OR under GERMAN STATES / GERMAN EMPIRE depending on year. Probe both during Phase 1.
10. **Anonymous-fetch dropped data** — if any per-coin page has a «Subscribe to view» block hiding fineness / mass / actual_weight, capture the absence as `null` + `fineness_verified: false`. Don't synthesise. Per CLAUDE.md §0.

## 6 — Open questions — RESOLVED (2026-05-16)

User decisions captured 2026-05-16, before Phase 1 start:

1. **Scale gate**: **staged sub-scope runs** — A. SH first → B. DK → C. Norge → D. Sweden-CII. Each sub-scope completes Phase 1+2+3+4 before the next starts.
2. **Cadet-line completeness**: **harvest ALL leafs without gatekeeping**, even those reporting only 1-2 coins. We need full data even if a single coin existed.
3. **Post-1864 SH**: **no Schleswig-Holstein minting happened post-1864** (Prussian annexation closed local mints). Probe is expected to return empty; we don't include 1864-1914 SH because no in-scope coins exist there.
4. **Sweden under Christian II**: **IN scope** — these were minted under Danish rule (Kalmar-Union period). Filter to 1514-1523 + ruler = Christian II. Post-1523 Vasa-Swedish OUT of scope.
5. **Dedup aggressiveness**: **NO dedup at cache-acquisition time**. Fetch every in-window MC_ID even if our curated `data/locations/*.yml` already has a curated entry for that coin. Raw cache integrity > minimising fetches. Dedup is parser/seed-phase work, not cache work.

**Additional user emphasis 2026-05-16**: «зберігай в кеш повністю всі дані які сторінка дає, в цій фазі важлива повнота даних» — full raw page content goes to cache, no stripping/trimming/extraction. Encoded in §3.4 step 4 «Raw-preservation rule».

## 7 — Scripts to add / extend

| Script | Status | Action | Phase |
|---|---|---|---|
| `scripts/fetch_numismaster.py` | NEW | Driver covering Phase 1 (Chrome MCP catalog walk → `leafs.json`), Phase 2 (per-leaf MC_ID enumeration → `mc_index.json`), Phase 4 (urllib bulk fetch → `MC_<N>.html` cache). Sub-commands or flags: `--walk-hubs`, `--enum-leafs`, `--fetch`. | 1, 2, 4 |
| `scripts/cache/numismaster/leafs.json` | NEW | Phase 1 output | 1 |
| `scripts/cache/numismaster/mc_index.json` | NEW | Phase 2 output | 2 |
| `scripts/cache/numismaster/<sub_scope>/` | NEW | Phase 4 cache dirs per sub-scope (migrate existing `denmark_pre_1541/MC_*` into `schleswig_holstein/`) | 4 |
| `scripts/cache/numismaster/<sub_scope>/_manifest.json` | NEW | Per-sub-scope manifest (URLs fetched, timestamps, last-batch status) | 4 |
| `scripts/parse_numismaster_pre1541.py` | EXISTS | **DEFERRED**: rename → `scripts/parse_numismaster.py`; generalise (KM# + MB# + post-1864 cross-refs). Runs later from local cache. | 5 |
| `scripts/maintenance/build_numismaster_pre1541_seed.py` | EXISTS | **DEFERRED**: rename → `build_numismaster_seed.py`; add `--sub-scope`. Runs later. | 5 |
| `data/seed/numismaster/<sub_scope>.yml` | — | **DEFERRED** — Phase 5 output, not produced in this pass | 5 |

## 8 — TODOs to open (after this surface is accepted)

Three new TODO entries proposed (each a separate session-bound unit):

- **§BI. NumisMaster harvest Phase 1+2 — catalog walk + MC_ID enumeration** (est: medium) — Chrome MCP walk per §3.1 + §3.2 above, staged in sub-scope order SH → DK → Norge → Sweden-CII. Writes `leafs.json` + `mc_index.json` + raw-page snapshots in `_walks/`. Stage gate: user reviews leaf list before Phase 4 commits to bulk fetch.
- **§BJ. NumisMaster harvest Phase 3+4 — scope filter + bulk cache fetch (raw HTML, full preservation)** (est: large) — depends on §BI output. Builds `mc_to_fetch.json` after year+ruler filter only (NO dedup against curated). Runs the background urllib loop populating `scripts/cache/numismaster/<sub_scope>/MC_<N>.html` + `MC_<N>.meta.json` with full HTTP response bodies preserved verbatim. Closes when all in-window `MC_<N>.html` files are cached + `_manifest.json` reconciled. **Stops at cache acquisition — no parsing, no seed, no curated-dedup.**
- **§BK. NumisMaster Phase 5 — parse + seed** (est: medium, **DEPENDS ON §BJ**) — generalises `parse_numismaster_pre1541.py` + `build_numismaster_pre1541_seed.py`, runs locally against the cache from §BJ. No NumisMaster traffic. Dedup against curated coins happens HERE, not at cache-acquisition time.

## See also

- `docs/HARVEST_GUIDE.md` — tier-based harvest architecture
- `docs/SOURCES.md` §6 + per-source policy
- `docs/research/denmark_pre_1541_source_survey.md` §14 — original (superseded for `/MC_` route)
- `scripts/cache/numismaster/denmark_pre_1541/` — 3 cached SH-duchy MC_ entries (pre-1541 sample)
- `scripts/parse_numismaster_pre1541.py` — parser baseline to extend
