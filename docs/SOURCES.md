# Sources Catalogue — Numismatic Sources We Use

> **Purpose.** Master register of every external source the project
> draws on, with characterisation (what each source covers best),
> recommended access pattern (which tool works, which fails), and
> a quick-reference matrix mapping coin theme / period / location
> to the right place to look first.
>
> **Pipeline context.** Every source listed here is consumed via the
> project's 4-phase data pipeline (HARVEST → SYNTHESIS → SEED →
> CURATED) documented in `docs/ARCHITECTURE.md` §«Data pipeline — 4
> phases». This file describes the **sources themselves** (what they
> cover, how to read them); `docs/HARVEST_GUIDE.md` covers per-source
> Phase-1 mechanics (URL patterns, tool fallback chains, JS-SPA
> pitfalls); `docs/ARCHITECTURE.md` covers Phases 2-4 (parse, seed,
> curated promotion) including the `PHASE_AUDIT` recipe for verifying
> every seed entry traces to Phase-1 cache provenance.
>
> Operational tool-mechanics (WebSearch → WebFetch → Apify → Chrome
> MCP escalation chain, Numista API quota rules) live in `CLAUDE.md`
> sections «Tool fallback chain» and «Numista API budget».

---

## 0. Quick reference matrix

When researching a coin, consult sources in this order based on what you need:

| Need | First source | Second source | Third source |
|---|---|---|---|
| **Specimen-level catalogue (KM, Hede, Sieg, Lange, Fr, Schou, Aagaard, weight, NGC grade)** | Bruun PDF (Stack's Bowers Part I/II/III) | Numista N# page | ucoin tid page |
| **Pre-Krause «MB#» / Schleswig-Holstein-duchy 16th c. (1500-1604, before KM numbering begins for Denmark)** | NumisMaster MC_NNNNN page (§1.4) | danskmoent.dk Galster (`/chr/c2g*.htm`, `/fr/f1g*.htm`) | Bruun PDF (for specimen-level corroboration) |
| **Hede# verbatim text + sub-variant ranges (Christian IV / V / Frederik III/IV/V/VI / Christian VI/VII)** | danskmoent.dk/chr/c{4,5,7}h{N}.htm | Hede 1957 NNUM articles via danskmoent.dk/artikler/ | (paper) Hede 1978 |
| **Müntzfuß spec / mint history / standards taxonomy (Reichsthaler, Konventionsthaler, Specie, Krone, Kurant)** | Wikipedia DE (Reichstaler / Speciestaler / Leipziger Fuß / Konventionstaler / Sächsische Münzgeschichte / Zinnaer Münzfuß / Augsburger Reichsmünzordnung / Corona Danica) | Bobzin (hagen-bobzin.de) | Meyers eLexikon (elexikon.ch) |
| **Period-correct German numismatic vocabulary** | MGM Münzlexikon (mgmindex.de) | Schrötter, *Wörterbuch der Münzkunde* (paper, 1930) | DeWiki (dewiki.de) |
| **A danskmoent.dk article on topic X (Møntfod / reform / mint / nominal / Wilcke chapter)** | [`docs/danskmoent_index.md`](danskmoent_index.md) topic-lookup | `litt<letter>.htm` A–Z bibliography (de-facto article index) | — |
| **Danish-language sources (Forordninger, Reskripter, monographs)** | danskmoent.dk | lex.dk (Den Store Danske) | Wikipedia DA |
| **Auction house catalog images** | Bruun PDFs | Künker (kuenker-numismatik.de) | NGC PriceGuide / Greysheet (last resort) |
| **Museum specimen images / IDs** | IKMK Berlin (ikmk.smb.museum) | Nationalmuseet København (natmus.dk) | (none — local museums rarely indexed) |
| **Hoard finds / archaeology** | Lund University Research Portal (portal.research.lu.se) | videnskab.dk | (specialist journals, paper) |

---

## 1. Numismatic catalogues (specimen-level)

### 1.1 Numista — `en.numista.com`

**Coverage:** broad, user-edited catalogue, ~500 000 coin types globally. For our project: Denmark, Norway, Schleswig-Holstein-Gottorp, Hamburg, Lübeck, German states. Each entry has a stable `N#` ID.

**Strengths:**
- Stable URL pattern: `https://en.numista.com/{N}` or `https://en.numista.com/catalogue/pieces{N}.html`
- Cross-references KM#, Hede#, Sieg#, Lange#, Fr#, NGC ID
- Rough weights and finenesses
- Year ranges, mintage where known
- Mintmaster initials with full names

**Weaknesses & gotchas:**
- **User-edited** — sometimes wrong KM# attribution, wrong Lange# mapping, or wrong year range. **Cross-check with Bruun PDF / Hede before trusting.**
- Often **lumps multiple sub-variants under one N#** (e.g. KM# 170 1698+1700 share N# 319101; KM# 203 1710+1711 share N# 307281 but 1712 is missing). Use `Years` field to detect lumping.
- Sometimes **swaps Lange#-attribution between sister-types** when sub-variants differ on obverse only — saw this with KM# 188 (N# 319169 vs 319272 disagreed with Bruun on which is Lange-444 vs Lange-444A). When Bruun and Numista disagree, **Bruun wins** (specimen-level expert classification).

**Access pattern (in order of preference):**
1. **Chrome MCP** — `mcp__Claude_in_Chrome__navigate` + `javascript_tool` to extract `document.querySelector('main').innerText`. Cloudflare may challenge first request; wait ~5-10 s and retry. **Use this by default.** For catalogue enumeration (vs single-NID fetch), follow the canonical URL pattern in `docs/HARVEST_GUIDE.md §«Numista catalogue enumeration via /catalogue/index.php»` — it documents the right `st=`, `o=`, `e=`, pagination, and JS-extractor patterns proven through §BO.1 + §BO.5.
2. **WebFetch** — returns 403 most of the time. Skip.
3. **Apify rag-web-browser** — sometimes works, sometimes 403. Try if Chrome MCP unavailable.
4. **Numista REST API** (`api.numista.com/v3/...`) — works reliably but **counts against quota**. Free tier = 200/24h, monthly cap mentioned in CLAUDE.md as «scarce in May 2026». **Always ask the user before any bulk-fetch >5 calls.** Cached responses live in `scripts/cache/numista/<nid>.json` and are free to re-read.

**Catalogue enumeration vs per-NID fetch — two complementary routes:**
- **Per-NID fetch** (`https://en.numista.com/<N>` or `/catalogue/pieces<N>.html`): when you already have a known NID list, just need the per-coin data. Low Cloudflare risk; survives long sessions.
- **Catalogue enumeration** (`/catalogue/index.php?e=<code>&st=...&p=N&q=200&o=y`): when you need to DISCOVER NIDs in scope (coverage audits, gap detection). Medium-low Cloudflare risk if filtered properly; avoid `?ru=` parameter which fires the challenge. Full URL form documented in `HARVEST_GUIDE.md`.

Known quirks (year-filter only matches dated specimens, NID-digit false-positive risk, `e=danemark` vs `e=denmark` scope difference, etc.): see §13.1 below.

### 1.2 ucoin — `en.ucoin.net`

**Coverage:** secondary catalogue, similar scope to Numista but smaller. Stable `tid` IDs.

**Strengths:**
- Often has **fineness data Numista lacks** (e.g. .986 for KM# 64 family vs Hede's .979)
- URL is human-readable: `/coin/<country>-<denom>-<years>/?tid=NNNNN`
- Has its own KM-like internal IDs (UC#)

**Weaknesses:**
- Smaller catalog, more gaps
- Often agrees with Numista on KM# but disagrees with Hede on fineness/weight (independent reads of same primary catalogues)
- Cloudflare-protected

**Access:** WebFetch routinely returns 403 (Cloudflare-protected). No public API for the numismatic catalogue (`ucoinpy` is for the unrelated uCoin cryptocurrency, not this site). Chrome MCP is acceptable as a fallback for ucoin **catalogue pages** (`/coin/<…>?tid=NNNNN`) under the conditions below; for **personal-user pages** (collections, swaps, wishlists, user profiles) it is NOT acceptable — those carry separate consent expectations and our project doesn't need that data anyway.

Acceptable-use conditions for catalogue Chrome-MCP fallback:
- **Non-commercial research only** (this project is a scholarly numismatic register; that's the only use that this access policy covers)
- **Low volume** — single-page or small-batch lookups, not bulk crawls. If a task needs more than ~10 ucoin pages in a session, stop and ask the user
- **Rate limiting** — the natural pace of `browser_batch` sequences is fine; never parallelise dozens of `navigate` calls
- **Attribution** — every ucoin-derived field already lands in a `sources: [{type: ucoin, ref: 'tid=NNNNN', url: ...}]` entry on the coin record; that's our contract with the source and it's non-negotiable
- **Respect `robots.txt`** — if the file becomes reachable in future and disallows the path, the policy switches to ask-the-user

When the Cloudflare challenge resolves (typically a 5–10 s wait after `navigate`, then re-issue `get_page_text`) the catalogue page is reachable. When all paths fail, fall back to asking the user to paste the relevant page text.

The strict «no Chrome MCP» rule that briefly applied here was overly conservative — the third-party scraping write-up that motivated it (`geonode.com/blog/how-to-scrape-ucoin`) does NOT in fact quote any ToS clause forbidding research access, only speculates about it; and our use case (non-commercial research, catalogue specs only, attribution per coin) sits squarely inside the «conditionally acceptable» framework that write-up describes.

**Use as:** confirmation source — when ucoin's weight/fineness/diameter agrees with our value, that counts as a confirmation suitable for `*_verified: true`. When ucoin disagrees, record the divergence via `measurement_alts`.

### 1.3 Stack's Bowers — L. E. Bruun Collection (3 PDF catalogues) ⭐

**Coverage:** the world's largest private collection of Scandinavian numismatica (Bruun bequest, 1928), insured 500 m DKK ≈ USD 72.5 m, ~20 000 pieces, 15th–20th centuries. Sold across three Stack's Bowers auctions 2024–2025. **Most authoritative specimen-level source we have for Danish / Norwegian / Schleswig-Holstein gold and silver.**

**Four parts to date, four PDFs:**

| Part | Date | Venue | URL | Pages | Lots |
|---|---|---|---|---|---|
| **I** | 14 Sept 2024 | Odd Fellow Palæet, Copenhagen | [`SBG_Sept2024_LEBruun_Collection_Part_I_Catalog.pdf`](https://stacksbowers.com/wp-content/themes/stacksbowers/uploads/catalogs/SBG_Sept2024_LEBruun_Collection_Part_I_Catalog.pdf) | 392 | 1001–1286 |
| **II** | 14–15 Mar 2025 | Baur au Lac, Zurich | [`SBG_Mar2025_LEBruunPtII_WebCatalog_LR.pdf`](https://www.danskmoent.dk/pdf/SBG_Mar2025_LEBruunPtII_WebCatalog_LR.pdf) (mirrored on danskmoent.dk) | 356 | 13001–13263 + 14001–14287 |
| **III** | 28–30 Oct 2025 | Odd Fellow Palæet, Copenhagen | [`SBG_Oct2025_LE_Bruun_Coins_Part_III.pdf`](https://stacksbowers.com/wp-content/themes/stacksbowers/uploads/catalogs/SBG_Oct2025_LE_Bruun_Coins_Part_III.pdf) | 284 | 11001–11308 + 12001–12228 |
| **IV** | 24–25 Mar 2026 | Kosciuszko Foundation, NYC | [`SBG_Mar2026_BruunIV_Coins_Catalog.pdf`](https://stacksbowers.com/wp-content/themes/stacksbowers/uploads/catalogs/SBG_Mar2026_BruunIV_Coins_Catalog.pdf) | 128 | 17001–17291 + 18xxx |

Overview page: <https://stacksbowers.com/the-l-e-bruun-collection/>

**What each entry gives you (verbatim):**
- Coin type, year, mint, ruler
- KM#, Hede#, Sieg#, Lange#, Fr#, Schou#, Aagaard# (where applicable) — with `cf.` prefix for variants
- Weight (gms) of the actual specimen
- Mintmaster name (full, not just initials)
- NGC grade and any condition notes
- Bruun-collection-id (e.g. «Bruun-14527») — the stable identifier we use in `bruun_lot:` field
- Auction lot number (sequential, e.g. «14233»)
- Estimate (€)
- Curatorial commentary («Lustrous and very attractive», «Possibly Unique Die Combination», rarity context)

**The Bruun-id (collection-id) is permanent**; the auction-lot-id (sequential) is per-auction. Our YAML field `bruun_lot:` should always hold the **Bruun-id** for cross-auction stability.

**How to work with these PDFs (LEARNED THE HARD WAY):**

The pdf-viewer MCP (`mcp__pdf-viewer__display_pdf` + `interact`) **does NOT work for these files** — they are 29-44 MB and the viewer iframe times out at 8 s before the PDF finishes loading. Each `display_pdf` returns a viewUUID, but `interact` calls fail with `Viewer never connected for viewUUID ... (no poll within 8s)`. Do not waste turns retrying.

**Use this pattern instead:**

```bash
# 1. Download the PDF locally
curl -s -o /tmp/bruun_part2.pdf \
  "https://www.danskmoent.dk/pdf/SBG_Mar2025_LEBruunPtII_WebCatalog_LR.pdf"
```

```python
# 2. Extract via pypdf (already installed in .venv)
from pypdf import PdfReader
import re

reader = PdfReader('/tmp/bruun_part2.pdf')

# Find which pages contain a given lot number
for pn, page in enumerate(reader.pages, 1):
    text = page.extract_text() or ''
    if re.search(r'\b14527\b', text):
        print(f"Lot 14527 on page {pn}")
        print(text)
        break
```

Then clean up `/tmp/bruun_part*.pdf` after the verification session.

**Page mapping for our most-cited Christian-V Glückstadt + Karl-Friedrich Tönning lots in Part II** (already verified):
- p.129 lot 13175 → Bruun-6791 (Christian V, 1672-IW, KM-64.2, Hede-115A)
- p.131 lot 13180 → Bruun-6913 (Christian V, 1680-CW, KM-70.1, Hede-117)
- p.302 lot 14225 → Bruun-14486 (Friedrich IV, 1698, KM-170, Lange-426)
- p.305 lot 14230 → Bruun-14504 (Friedrich IV, 1700, KM-170, Lange-427)
- p.308 lot 14233 → Bruun-14527 (Karl Friedrich, 1705-BH, KM-188, Lange-444, Sieg-11.1)
- p.309 lot 14234 → Bruun-14528 (Karl Friedrich, 1705-BH, KM-188, Lange-444A, Sieg-11.2)
- p.309 lot 14235 → Bruun-14529 (Karl Friedrich, 1705, KM-189, Lange-cf. 445)
- p.309 lot 14236 → Bruun-14533 (Karl Friedrich, 1706, KM-189, Lange-445)
- p.309 lot 14238 → Bruun-14572 (Karl Friedrich, 1710-BH, KM-203, Lange-447)
- p.310 lot 14239 → Bruun-14580 (Karl Friedrich, 1711-BH, KM-203, Lange-447B)
- p.311 lot 14240 → Bruun-14593 (Karl Friedrich, 1712-BH, KM-203, Lange-cf. 447, Fr-unlisted)

**When Bruun and Numista disagree, Bruun wins.** Stack's Bowers had specimen in hand and expert curation; Numista is user-edited.

### 1.4 NumisMaster — `numismaster.com` 🔴 OFFLINE since ≤ 2026-08-07

> **STATUS: the site is DEAD.** Every URL — root and per-coin `MC_<N>` alike — now
> answers `302 → https://www.numismaticnews.net/pricing` (verified 2026-08-07).
> The dataset was acquired by NGC; the live successor surface is **§1.5 NGC World
> Coin Price Guide**, whose pages carry the «Powered by NumisMaster / specification
> data provided by Active Interest Media's NumisMaster» attribution.
>
> Consequences for this project:
> - `scripts/cache/numismaster/` is now a **frozen archive** (harvested 2026-05-16/17,
>   1981 MC_IDs). It can be re-parsed but **never re-fetched**. Treat a cache miss as
>   permanent — route the lookup to §1.5.
> - `scripts/fetch_numismaster*.py` paths are dead code for fetching; the parser
>   (`scripts/parse_numismaster.py`) remains valid against cached HTML.
> - The «Access pattern» section below is retained as **historical documentation** of
>   how the archive was built, NOT as a runnable procedure.
> - Authority note: NGC is **not an independent witness** to our NumisMaster cache —
>   it is the same dataset under new custody (NGC states it has «made adjustments or
>   edits to the prices, descriptions and specifications»). Agreement between the two
>   is one reading propagated twice, per the §13.12 derived-chain caveat. Where they
>   DISAGREE, NGC is the later editorial state and our cache is the 2026-05 snapshot.

**Coverage:** Krause-Mishler-based commercial catalogue (Librios-hosted, formerly the *Standard Catalog of World Coins* book series, North American Coins and Price, U.S. Coin Digest). Active Interest Media, Inc. Site tagline: «Expert pricing for U.S. coins, world coins and more with KM numbers.»

**Per-country catalog floors** (empirical, full Phase-1b inventory walk 2026-05-16):

| Country | Catalog floor | Mission window | In NumisMaster | Status |
|---|---:|---|---:|---|
| Denmark | 1591 (FR# 32 Guilder, Frederik II) | 1514-1914 | 1308 entries; ~1000 in-window across 40 pages | ✅ inventoried |
| Norway | 1608 (KM# 4 Lion Dalar, Christian IV) | 1514-1814 | 560 entries; ~340 in-window across 14 pages | ✅ inventoried |
| Sweden | 1573 (MB# 9001 2 Öre, Johan III) | 1514-1523 (Christian II Kalmar Union) | 954 entries; **0 in-window** | ✅ CLOSED negative finding |
| Schleswig-Holstein (9 cadet filters) | 1514 (MB# 10 2 Schilling Frederik I) | 1514-1864 | 562 entries across 23 pages | ✅ inventoried |

Pre-floor era (e.g. Christian II 1513-1523 Danish, Frederik I 1523-1533 Danish, all Norway pre-1608) is NOT in NumisMaster — route through **Bruun PDFs** (§1.3), **danskmoent.dk Galster** (§2 below), **Schive 1865** (Norway), or **Wilcke 1950** (ordinance specs) instead.

**Strengths (vs Numista):**
- Authoritative KM# attribution (commercial editorial process, not user-edited).
- Multiple pre-Krause numbering schemes coexist on the same UI: **MB#** (Madai-Bach for SH duchy), **FR#** (Friedberg for gold incl. Portugaloser), **C#** (Christensen, rare), alongside KM#.
- Cross-references inline (Schou, Lange, Friedberg, KM, MB, Hede, Dav).
- Obverse + Reverse legend transcriptions (Latin).
- Political-period attribution («Duchy», «Trade Coinage», «Standard Coinage» tags via Librios PL-/CG- codes) useful for issuing-entity classification.

**Weaknesses & gotchas:**
- **Catalog data is public; «Value information in US Dollars» price columns are subscription-gated.** Coin specs (Country, Catalog #, Date, Composition, Mass, Obverse / Reverse, General Note, Cross-refs) render publicly for anonymous fetchers.
- **Filter state is client-JS in session cookies, NOT URL-encoded.** URL keyword/searchstr/country/q params (e.g. `?id=-10012282&keyword=denmark`) are server-IGNORED — return the rotating 18-featured-coin sample. ASP.NET form-POST with `__VIEWSTATE` is also ignored (probed and verified: POST with `searchstr=schleswig` returns a card for country = KHIVA). Only the JS-driven sidebar checkbox + SEARCH-button click flow applies filters.
- **Session cookies cross-contaminate walks.** «Reset search» UI link clears only submitted-filter view, not the underlying cookie state — subsequent country additions OR with prior selections. Mandatory JS-console cookie + sessionStorage + localStorage clear between walks (see `docs/HARVEST_GUIDE.md` §«NumisMaster» «Step 0» for the canonical incantation).
- **NO `/sitemap.xml`** (returns 404 SPA shell).
- **Topology rectification (corrected post-Phase-1b)**:
  - **Geographic-hub URLs** (`-1005793` DK, `-1005794` GLÜCKSTADT, `-1005795` HG-Rendsborg, `-1006970` NORWAY, etc.) render decorative country-selector + «N-th Pattern: A» rows — **NO coin list**. «A»-letters are inert (no JS handler).
  - **`-10012282`** is the **GLOBAL coins-search facet** (alias `/coins`), NOT a HG-Rendsborg-specific leaf as earlier session-1 notes implied. Earlier observations of HG-Rendsborg results at this URL came from session-cookie carryover.
  - There is **no «leaf ID» concept** — all per-country filtering goes through the global coins-search via the sidebar checkbox state machine.
- Numbering hierarchy: each per-coin page has a stable `MC_NNNNN` identifier, distinct from the catalogue's KM#/MB#/FR#/C# attribution.

**Access pattern:**

1. **Per-coin pages (PUBLIC, urllib works fine)**: `https://numismaster.com/MC_<N>` renders full specs. No Cloudflare gate. Direct Python urllib with polite ASCII-only User-Agent works.
2. **Search results (Chrome MCP REQUIRED)**: enumeration via the JS-sidebar checkbox state machine. Canonical 6-step workflow with JS recipes in `docs/HARVEST_GUIDE.md` §«NumisMaster» — JS-clear cookies → Show More → click country checkbox via JS → verify match count → Sort=Date via `dispatchEvent('change')` → paginate `&pageno=N`. **DO NOT** use Chrome MCP `form_input` on the Sort dropdown — it can drop the active filter state.
3. **WebFetch**: catalog navigation returns skeleton without coin data (marketing-only). Per-coin MC_ URLs return full data.

**Acceptable-use** (per CLAUDE.md «non-commercial scholarly register» framing):
- Non-commercial research only.
- Per-coin pages via urllib at polite pacing (~30 s pauses recommended; site has no documented rate limit but be conservative).
- Search-form discovery via Chrome MCP — same as our ucoin acceptable-use framework.
- Attribution: every NumisMaster-derived field lands in `sources: [{type: literature, url: numismaster.com/MC_<N>, ref: '...'}]`.

**Use as:** comprehensive cross-reference for **MB#/FR# pre-Krause 1514-1604 Danish-realm + SH-duchy coins** + **KM# 1604-1914 Danish/Norge coinage** when validating Bruun/Hede/Galster attributions. Phase-1b two-session walk (2026-05-16) inventoried 562 SH + ~1000 DK + ~340 Norge entries in the cache; ~101 MC_IDs anchored in `mc_index.json` for Phase-4 urllib bulk fetch, ~1800 remaining text-dumped (KM/MB/FR/C# + denom + year + country_label captured but MC_NNNNN anchor extraction deferred).

**Project scripts:**
- `scripts/parse_numismaster.py` — sub-scope-aware parser: MC_<N>.html → `MC_<N>.parsed.json` sidecar (uses `lib.paths.NUMISMASTER_CACHE`)
- `scripts/maintenance/build_numismaster_seed.py` — parsed sidecars → entity-keyed seed YAML (merge-aware via `write_v2_seed`; the `_pre1541` builder was retired 2026-07-10, its 3 MB# coins fold into the `schleswig_holstein` sub-scope)
- **Cache root**: `lib.paths.NUMISMASTER_CACHE` = `scripts/cache/numismaster/`. Subdirectories:
  - `{schleswig_holstein,denmark,norway}/MC_<N>.{html,meta.json}` + `.parsed.json` — one subdir per sub-scope: harvest pages + parsed sidecars
  - `_walks/leaf_*.txt` — raw Chrome-MCP page-text dumps per filtered search-result page (Phase-1b output; provenance for `mc_index.json`)
  - `_walks/hub_*.txt` — geographic hub snapshots (documentation only)
  - `_walks/_phase_*.md` — process documentation (topology findings, session handoffs, final summary)
  - `mc_index.json` — consolidated MC_NNNNN inventory per country filter; the Phase-4 urllib fetch input

---

### 1.5 NGC World Coin Price Guide — `ngccoin.com/price-guide/world/` ⭐

**Coverage:** the **live successor to NumisMaster** (§1.4). NGC acquired the Active
Interest Media / NumisMaster catalogue; every price-guide page carries «Powered by
NumisMaster» and «Numismatic specification data and valuation estimates provided by
Active Interest Media's NumisMaster». Krause-numbered, world coins 1600→date (the
site's own claim; in practice earlier material appears — Lübeck `KM-A9` is dated
(1)603-(1)604, and the DENMARK region reaches 1591 as in §1.4).

**Why it matters to this project.** For Denmark / Norway / Schleswig-Holstein it adds
no new facts — that is exactly the frozen `scripts/cache/numismaster/` archive. Its
real value is **the German territories we never harvested from NumisMaster**, which
here are enumerable behind one plain GET loop.

**Region coverage (all mission locations present).** `GERMAN STATES` exposes **441**
regions, including: `BREMEN`, `BREMEN & VERDEN`, `VERDEN`, `HAMBURG`, `LÜBECK`,
`LUBECK`, `LAUENBURG`, `SAXE-LAUENBURG`, `OLDENBURG`, `OSNABRUCK`, `HESSE-CASSEL`,
`SCHAUMBURG-HESSEN`, `SCHLESWIG-HOLSTEIN` (+ `-GOTTORP`, `-PLOEN`, `-SONDERBURG`,
`-NORBURG`, `-GLUCKSBURG`), and the whole `BRUNSWICK-LÜNEBURG-*` cluster.
`DENMARK` exposes only three: `All Regions`, `GLÜCKSTADT`, `HOLSTEIN-GOTTORP-RENDSBORG`.

**Measured volumes** (binary-searched over the pager, 2026-08-07). Rows are **per-date
variants** (`duid`), not types (`cuid`) — on a Lübeck sample 200 rows collapsed to
**37 distinct types (≈5.4:1)**, so divide accordingly for the real fetch count:

| Region (country) | date-rows | types |
|---|---:|---:|
| DENMARK — All Regions | 3075 (123 pp.) | **1451** (exact — full walk) |
| HAMBURG | 1112 | ~205 (est.) |
| LÜBECK | 772 | **265** (exact — full walk) |
| BREMEN | 607 | ~112 (est.) |
| SCHLESWIG-HOLSTEIN-GOTTORP | 360 | ~67 (est.) |
| OLDENBURG | 240 | ~44 (est.) |
| LUBECK (no umlaut — a SEPARATE region) | 179 | ~33 (est.) |
| SCHLESWIG-HOLSTEIN | 170 | ~31 (est.) |
| LAUENBURG | 17 | ~3 (est.) |

> **The rows→types ratio is NOT constant across regions — do not extrapolate it.**
> Lübeck collapses 772 rows into 265 types (2.9:1 measured over the full walk;
> a 200-row sample had suggested 5.4:1). Denmark collapses 3075 rows into
> **1451** types — 2.12:1. An earlier revision of this table carried «~570» for
> Denmark, derived from Lübeck's sample ratio; the full walk showed that
> estimate was low by a factor of ~2.5. Every «est.» row above is the same
> untrustworthy arithmetic — walk the region before planning against it.
> `GLÜCKSTADT` (97 types) and `HOLSTEIN-GOTTORP-RENDSBORG` (4) are strict
> SUBSETS of DENMARK/All Regions, so they need no separate walk.

**Per-region field profiles differ sharply — Lübeck's profile does NOT generalise.**
Measured over the full harvests (n = 265 and n = 1105 respectively):

| | Lübeck | Denmark |
|---|---:|---:|
| fineness | 24 % | **77 %** |
| weight | 25 % | **80 %** |
| note present | 93 % | 43 % |
| **Behrens** `B-###` | **70 %** | **0** |
| Davenport | 101 | 197 |
| Hede / Sieg / Schou / Galster | 0 | **0** |
| ruler | 27 % | 38 % |

The two regions are near-opposites: Lübeck is metrologically thin but rich in
the Behrens catalogue key; Denmark is metrologically rich, and carries no
*Danish-tradition* catalogue key — no Hede, Sieg, Schou or Galster anywhere in
478 notes.

**That absence does NOT mean Denmark is unlinkable — KM does the job.** Measured
against `data/v2/final/` (danish_realm + danish_norway + royal_holstein +
gottorp_duchy + _unclassified):

| | |
|---|---:|
| NGC Denmark distinct KM# | 1039 |
| **link to our data by KM#** | **903 (87 %)** |
| add Davenport as a second key | **+0** — every Dav match was already a KM match |
| no link at all (new coverage) | 136 |
| our coins sitting under a shared KM# | 1815 |

So for Denmark, **KM is the working index-graph edge and Davenport is
corroboration, not a bridge**. What NGC would ADD to coins we already hold:
fineness on **327** (18 % of matched coins) and obverse legend on **326**, where
our record currently has nothing; weight on 108, diameter on 18, mint on 9.

> **Correction (2026-08-09).** An earlier revision of this section concluded from
> the missing Hede/Sieg/Schou that NGC supplies «NOT the cross-catalogue links
> the Danish pipeline runs on», and suggested skipping a Danish seed in favour of
> metrology-only enrichment. That was wrong: it silently equated «catalogue key»
> with «Danish-tradition catalogue key» and overlooked that KM — carried by 100 %
> of NGC types and 22 % of our final coins — already links 87 % of them. A Danish
> seed is worth building.

**A caveat on any bulk field comparison here: the KM join is ONE-TO-MANY.** 525
of our 1183 Danish KM keys map to more than one of our coins (mean 1.95, worst 9
— sub-variants sharing a base number). A naive cross-check of fineness over the
join reports «2358 agree / 942 diverge», but the 942 is counted per
(NGC type × our coin) pair, so one NGC entry meeting N sub-variants contributes
up to N. It is a join artefact, **not** 942 conflicts. Real divergences can only
be counted after the §9.4 index-graph fixes the mapping.

### Access surface — the complete picture (probed 2026-08-07)

**1. Listing (GET, the enumeration path).** The search form is ASP.NET WebForms with
`__VIEWSTATE`, but submitting **redirects to a clean, replayable GET**:

```
/price-guide/world/search/<page>/?country=<C>&region=<R>&denom=&date=&catalogInitials=&catalogNumber=
```

- `denom=` may be **empty** → full region enumeration. 25 rows/page.
- `<page>` increments directly; the on-page pager is postback-only but is not needed.
  A page past the end returns 0 `cuid` links — that is the terminator.
- `region=All+Regions` aggregates a whole country.
- Listing rows carry: KM#, year(range), denomination, composition, weight,
  obverse/reverse **descriptions**. NOT fineness, NOT legends.

**2. Detail page.** Slug shape
`/price-guide/world/{country}-{denom}-km-{km}-{years}-cuid-{N}-duid-{N}`.
One fetch per `cuid` suffices — the page renders the full date table for that type.
Adds over the listing: **Fineness, ASW, obverse/reverse Legend, `Note:`, price grid**.

**3. JSON service — typeahead only, NO data API.**
`/resources/services/coin-search/price-guide/world/search/?keywords=<q>` returns
`application/json`: `[{"CoinDescription": "...", "URL": "..."}]`. It is a **discovery**
endpoint (country / year-range / denomination combinations) with **no coin specs**.
Useful for enumerating the taxonomy, useless as a data source.
Probed and 404: `/api/*`, `/price-guide/*/api/`, `/umbraco/api/`, and every
`…/coin-search/…/{coin,detail,regions,denominations,countries}/` variant.

**4. No public catalogue API.** NGC's only documented API is the **Submission
Tracking API for authorized dealers** (grading submissions — not catalogue data).
No developer portal, no API key, no documented price-guide endpoint was found.
Third-party commercial scrapers exist on Apify, which is itself evidence that no
first-party bulk route is offered.

**5. `/sitemap.xml` exists but is USELESS for world coins.** It indexes 3 price-guide
sitemaps totalling ~120 885 URLs — **United States only**. The sole `/price-guide/world/`
entry is the landing page. World coins are not in any sitemap; pagination is the only
enumeration path.

**6. Cloudflare gates all non-browser access.** `curl` with a full browser header set
(UA + `Sec-Fetch-*` + `sec-ch-ua` + `Accept-Language`) still returns **403 «Just a
moment…»** (JS challenge). WebFetch likewise 403s. **Same-origin `fetch()` from an
already-cleared browser tab works perfectly** (verified: 200, 25 rows/page, and a
31-page + 25-detail-page walk completed without throttling or a re-challenge).

**`robots.txt`:** `Disallow: /` for **AhrefsBot only**; `User-agent: * → Allow: /`.
Our non-commercial scholarly use is on the permitted side of the commercial /
research line (per CLAUDE.md «Project-context note for access decisions»).

**Field fill-rates** — measured over a 25-page stratified sample of LÜBECK detail
pages. The metrological payload is **thin for small silver**; the catalogue-index and
design payload is **rich**:

| Field | Fill | Note |
|---|---:|---|
| Composition | 100 % | metal class only |
| KM# | 100 % | from the slug |
| `Note:` | 92 % | see below — the real prize |
| Obv/Rev Legend | 84 % | Latin transcription |
| — of which **Behrens** `B-###` | 64 % | |
| Fineness | **28 %** | present on big silver (e.g. DK 2 Krone 0.8590), absent on small |
| Weight | **28 %** | ditto |
| ASW | 12 % | |
| «Previous KM#» | 12 % | Krause renumbering provenance |

**Strengths:**
- **Behrens numbers for Lübeck** (`Ref. B-471, 472`) — the load-bearing Lübeck
  catalogue key we otherwise hold only on paper (§5). 64 % of sampled Lübeck notes.
- **Davenport** inline (`Dav. LS332`, `Dav. 627`, `Dav. #3516A`).
- **`Previous KM#` / `Prev. KM#`** — explicit Krause renumbering trail, directly
  feeding the §9.4 index-graph work and the §13.6 KM#-inflation problem.
- Free (no paywall) where NumisMaster gated pricing behind a subscription.
- Editorial notes of real substance: `Klippe`, `Joint issue with Hamburg`,
  `Issued for use in both Bremen and Lübeck`, mayor attributions with dates.

**Weaknesses & gotchas:**
- Fineness/weight missing on ~72 % of small-silver types (see fill-rate table).
- **Prices are OUT OF SCOPE** for this project regardless of availability (§7a).
- Derived-not-independent relative to our NumisMaster cache — see the §1.4 authority
  note. Authority score should be set **at or below** NumisMaster, never above.
- See §13.13 for the `LUBECK` / `LÜBECK` region split and other quirks.

**Use as:** primary route for **German-territory Krause/Behrens/Davenport
cross-reference** (Lübeck, Hamburg, Bremen, Oldenburg, Lauenburg,
Brunswick-Lüneburg, Hesse-Cassel, Osnabrück, Verden) — the gap our NumisMaster walk
never covered. For DK/NO/SH, prefer the existing cache and use NGC only to check
whether the editorial state changed after 2026-05.

---

## 2. Hede catalogue (via danskmoent.dk)

**Hede catalogue** = Holger Hede, *Danmarks og Norges mønter 1541-1814, 1814-1977* (1978) — the canonical Danish/Norwegian numismatic reference. Each Hede# uniquely identifies a coin type with sub-variant letters (115A vs 115B = different sub-types within Hede 115).

**Online manifestation:** `danskmoent.dk` (Dansk Mønt) hosts a web-edition of Hede plus Holger Hede's NNUM articles.

### 2.1 Per-coin Hede pages

URL pattern: `https://www.danskmoent.dk/chr/c{ruler-number}h{hede-number}.htm`

Examples:
- `c5h115.htm` = Christian V, Hede 115 (Glückstadt 1-Dukat 1672-1676)
- `c5h117.htm` = Christian V, Hede 117 (Glückstadt 1-Dukat 1680, 1685)
- `c5h118.htm` = Christian V, Hede 118 (Glückstadt 1-Dukat 1682, Vægterdukat)
- `c7h32.htm` = Christian VII, Hede 32 (Kopenhagen 4-Skilling Dansk 1783)

Each page gives: years, mint, weight (Bruttovægt), fineness (Finhed), fine weight (Finvægt), mintmaster initials, plus the Aagaard 2022 reference for further reading.

**404 means the Hede number doesn't have a published page** (not all numbers do). When 404, search for adjacent numbers.

**Access:** WebFetch works fine. No Cloudflare here.

### 2.2 NNUM articles (Hede 1957)

Hede published two specialised articles in NNUM 1957 that are essential references for the Krone family:

| Article | URL | Covers |
|---|---|---|
| «Kronemønten 1618-1771» | <https://danskmoent.dk/artikler/hedekron.htm> | All three silver Krone-Müntzfüße (Christian IV / Grobe / Fine), with Hede formulas, mint dates, special issues 1665 «Pumpbucksen», 2-Krone 1675, Skuemønter 1699 + 1746 |
| «Frederik III's guldkroner» | <https://danskmoent.dk/artikler/f3guldkr.htm> | Guldkrone-Fuß: København 1655 first issue, Glückstadt 1657-1660, two formulas (older 5.996g vs younger 5.590g), Forordning 2. Januar 1658, Commerce Collegium decision 14. Februar 1671 ending the program, Royal Resolution 2. September 1701 (Vestindiske Compagni 2-Guldkrone) |

**Use these whenever questions arise about Krone-family coinage.** They are the authoritative single source.

---

## 3. Wilcke series (via danskmoent.dk)

> **Full chapter-level index → [`docs/danskmoent_index.md`](danskmoent_index.md).**
> That file maps the entire digitised Wilcke corpus **and** the wider danskmoent
> article archive to topics («which link to read to study topic X»), and explains
> the site's navigation (the A–Z `litt<letter>.htm` bibliography is the de-facto
> article index — there is no site-wide article list). Consult it first when
> looking for a danskmoent article; the summary below is just the volume map.

**Wilcke** = Julius Wilcke, the foundational Danish numismatic-policy historian. **Seven volumes covering 1481-1914** (not three / 1588-1746 — corrected 2026-09-06). danskmoent digitises them chapter-by-chapter under `/wilcke/w<N><letter>.htm`, with a per-book cover/TOC at `w<N>.htm` (site root):

| Volume | Title | Cover / access |
|---|---|---|
| **Wilcke I** | *Christian IVs Møntpolitik 1588-1625* (Kbh 1919) | `w1.htm` · chapters `wilcke/w1a-g.htm` · PDF `pdf2/Wilcke_1.pdf` |
| **Wilcke II** | *Møntvæsenet under Christian IV og Frederik III 1625-1670* (Kbh 1924) | `w2.htm` · only `wilcke/w2d.htm` (Andre Møntsteder) as HTML |
| **Wilcke III** | *Kurantmønten 1726-1788* (Kbh 1927) | `w3.htm` · chapters `wilcke/w3a-g.htm` |
| **Wilcke IV** | *Specie- Kurant- og Rigsbankdaler 1788-1845* (Kbh 1929) | `w4.htm` · chapters `wilcke/w4a-s.htm` |
| **Wilcke V** | *Sølv- og Guldmøntfod 1845-1914* (Kbh 1930) | `w5.htm` · chapters `wilcke/w5a-e.htm` |
| **Wilcke VI** | *Daler, Mark og Kroner 1481-1914* (Kbh 1931) | `w6.htm` · type-monographs `wilcke/w6a-t.htm` |
| **Wilcke VII** | *Renæssancens Mønt- og Pengeforhold 1481-1588* (Kbh 1950) | `w7.htm` · PDF-only `pdf2/Wilcke 7-0.pdf … 7-8.pdf` |

**Useful for:** primary attestations of Forordninger and Patenter — e.g. Wilcke II Anm. 53 quotes the «åbent Brev af 12. Juli 1618» introducing Christian IV's Corona Danica. Wilcke VII is the reference for the **Danish lower-anchor** period (Christian II Lovkompleks 1514 → `Wilcke 7-2.pdf`; Christian III's Møntreform 1541 → `Wilcke 7-4.pdf`).

**Page-number trap:** secondary literature (especially Hede's 1957 footnotes) cites Wilcke I p. 152 for the «1618 small denominations slightly lower Müntzfod» claim, NOT for the patent date. The patent itself is at Wilcke I pp. 156-157 (cross-referenced in Wilcke II Anm. 53). Do not conflate these two facts.

**Access — the host actively defends itself, and the defence escalates.** Three
response codes to recognise:

- **`455 Security Incident Detected`** — a bare `curl`, or a default Python UA.
  The hard block.
- **`454` + an HTML page titled «Checking your browser…»** (7 296 bytes) — a JS
  challenge. A plain HTTP client cannot answer it.
- **`403`** on directory listings (`/wilcke/`). Individual files are fine.

**`curl` with a browser User-Agent and a same-site `Referer` can get you exactly
one file, and then stops working.** Observed 2026-09-23: this fetched the 15 MB
`pdf2/Wilcke_1.pdf` at `200`; some twenty minutes and a handful of requests
later the *identical* command returned `454`, as did every other PDF and `.htm`
on the host. Treat it as a one-shot that may or may not fire, never as a
harvesting route:

```bash
curl -sSL -A "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0 Safari/537.36" \
     -H "Referer: https://www.danskmoent.dk/wilcke.htm" \
     "https://www.danskmoent.dk/pdf2/Wilcke_1.pdf" -o W1.pdf
```

Always check what landed (`file W1.pdf`) — the challenge page is served with the
requested filename and a `200`-looking `-o`, so a failed fetch looks like a
successful one until you open it. Spaces in the Wilcke VII filenames are `%20`.

**The route that does not degrade:** open the site once in the in-app Browser
pane, then `fetch(url)` via `javascript_tool` — same-origin, the pane has already
passed the challenge. `pdf-viewer` MCP when it is connected. WebFetch is
unreliable here (failed 2026-09-06) but sometimes returns a usable summary of an
`.htm` page.

**So cache what you fetch.** Getting a Wilcke volume is the expensive step, not
reading it; a volume pulled into a session scratchpad is lost at session end and
the next session may not be able to re-fetch it at all. `scripts/cache/wilcke/`
is the place for one that will be cited repeatedly.

**Reading the scanned volumes.** The `/pdf2/` scans carry an **embedded OCR text
layer**, so `pypdf` reads them with no OCR pass of our own:

- `Wilcke_1.pdf` — 239 pages. **PDF index = printed page − 2** (index 150 =
  printed p. 152; index 155 = p. 157). Check the offset per volume before
  quoting a page.
- Tables need `page.extract_text(extraction_mode="layout")`; the default mode
  collapses the columns into unreadable runs.
- **The OCR mangles digits in dense tables** — commas and superscript/subscript
  fractions especially (`32,500` read as `82,500`; `859,375` as `8*>9,375`;
  `6²⁵⁷⁄₁₄₀₀` as `6267/hoo`). Never quote a figure straight from the text layer:
  recompute it from the printed fraction, or get eyes on the page.
- **The page scans are JBIG2**, so `pypdf.page.images` raises
  `DependencyError: jbig2dec binary is not available` — but that is a limitation
  of `pypdf`'s image EXPORT, not of rendering. **Render the page instead**, and
  read the PNG. Two routes, both verified 2026-09-23 on this very table:

  ```python
  import pypdfium2                                     # .venv, BSD-3/Apache-2.0
  pdf = pypdfium2.PdfDocument("W1.pdf")
  pdf[150].render(scale=3).to_pil().save("p152.png")   # ~0.3 s, 1711x1170 px
  ```

  and the `PDF_Tools` MCP's `render_pdf_page` (`page` is 1-indexed: page 151 =
  PDF index 150 = printed p. 152). Both reproduce the superscript/subscript
  fractions legibly where the OCR mangles them.

  **`PDF_Tools` is sandboxed** to `~/Documents`, `~/Downloads`, `~/Desktop` — it
  cannot read the repo or a session scratchpad, and refuses with a message
  naming the boundary. Either copy the PDF into `~/Downloads` first, or have the
  user widen `allowed_directories`. `pypdfium2` has no such restriction, runs
  from Bash, and needs no MCP — prefer it.

**Wilcke I, the two pages that keep coming up.** p. 152 is the **denomination
table** for Christian IV's kronemønt — per row: Jørgensen Beskr. Nr., legal
value in Rdlr, pieces per rough and per fine mark, Lødighed, and what one fine
mark was «udbragt til» in daler. It catalogues `Krone = 1½ Rdlr` (Nr. 104,
37,819 g / 32,500 g fine) and `½ Krone = ¾` (Nr. 105, 18,766 g / 16,127 g) as
**different coins**, not as a piece and its arithmetic half — Hede's
`12²⁵⁷⁄₇₀₀` is twice Wilcke's Nr. 104 figure, NOT his Nr. 105 (`12³²³⁄₇₀₀`).
p. 157 carries the **tariff chain of the Forordning af 1. maj 1618** — Mark =
20 ß, Daler = 84 ß, so Krone = 1½ Daler = 126 ß = 6,3 Marker — which is the
decree's own way of defining the standard.

---

## 3a. Jensen monographs (via danskmoent.dk) — the ducal Schleswig-Holstein authority

**Jørgen Steen Jensen**, long the Royal Coin Cabinet's numismatist at the
Nationalmuseet, is the modern authority on the ducal Schleswig-Holstein
coinages. danskmoent hosts two of his works **in full, free**:

| Work | Year | URL | Size |
|---|---|---|---|
| *Hertug Hans den Yngre* — sections Mønthistorie · **Katalog** · Aktstykker | København 1971 | <https://www.danskmoent.dk/pdf2/JSJ_HdY.pdf> | 18.7 MB, 91 pp. |
| *Sønderjyllands mønthistorie til 1864*, Sønderjyske Årbøger 114, pp. 7-60 | 2002 | <https://www.danskmoent.dk/pdf2/JSJ%20Sjylland.pdf> · also open-access at <https://tidsskrift.dk/soenderjydskeaarboeger/article/view/81297> | 44 MB, 54 pp. |

**Why these matter more than their page count suggests.** Jensen 1971 carries a
**per-specimen type catalogue** for Hans den Yngre and his five sons — the
Sønderborg, Nordborg, Glücksborg and Plön lines — of exactly the kind no online
catalogue has for these houses. Each entry gives the legends, the Lange number,
and then **every known specimen with its collection siglum and its weighed
mass**. That is the only weighed metrology this project has found for ducal
Sonderburg gold, and it is what settled the Goldgulden-vs-Ducat question in
§13.15.

**Collection sigla** (Jensen 1971 p. 137, «Møntsamlinger»), needed to read the
catalogue at all:

| | |
|---|---|
| **KM** | Den kongelige Mønt- og Medaillesamling, Nationalmuseet, København |
| **K** | Landesgeschichtliche Sammlung, Schleswig-Holsteinische Landesbibliothek — **holds the surviving part of Chr. Lange's own collection**, so a `K` specimen is often the very piece Lange described |
| **B** | Münzkabinett, Bode-Museum, Berlin |
| **BR** | L. E. Bruun's collection, Frederiksborg |
| **F** / **H** / **D** / **OD** / **OS** / **ST** / **A** / **E** | Flensburg · Hamburg · Dresden · Odense · Oslo · Stockholm · Ahlmann-Bank Kiel · Eremitage |

**Access.** danskmoent's host (simply.com) puts a «Checking your browser»
challenge in front of `curl` / `urllib`; the PDFs fetch fine from a real browser.
`WebFetch` refuses anything over 10 MB, and Chrome's PDF viewer does not expose
text to `get_page_text` — so the practical route is: download in a browser, then
extract locally with `pypdf`. Both files extract cleanly to text (Jensen 1971 →
150 k chars, Jensen 2002 → 108 k chars), including the catalogue tables.

**Companion free articles on the same site**, useful for the same polities:

- Axel Ernst, «Bidrag til Holsten-Gottorps ældre mønthistorie», NNUM 1956 pp. 237-249 — <https://www.danskmoent.dk/ernst/holstgot.htm>. Covers Adolf and **Johann Adolph (1590-1616)** in depth: mintmasters, Kreis probation records, speciedaler output figures. Does **not** reach Friedrich III (1616-1659).
- J. C. Moesgaard, «Gennem besværligheder til stjernerne — Christian Albrecht af Gottorps (1659-94) mønter og medaljer», NNUM 2006/1 pp. 24-27 — <https://www.danskmoent.dk/artikler/moesalbr.htm>.
- Per-ruler **concordance tables** with Sieg / Sømod / Storgaard / Jensen / **Lange** numbers, nominal, metal and year: <https://www.danskmoent.dk/hdy.htm> (Hans den Yngre) and <https://www.danskmoent.dk/alexander.htm> (Alexander). These are the fastest way to get a Lange number for a ducal Sonderburg type without the book.

---

## 4. Aagaard monographs (paper)

Sven Aagaard is the leading modern Danish numismatic researcher. Three relevant monographs (paper-only, not digital):

| Title | Year | Covers |
|---|---|---|
| *Frederik III Kronemønt København 1651-1670* | 2004 | Frederik III's Kronemønt continuation in Copenhagen, including the 1651-1652 transition from Christian-IV's Müntzformel (16.25g fine) to the new 10½-Krone-Fuß (14.964g fine) |
| *Frederik III Guldmønt og speciemønt 1648-1670* | 2011 | Frederik III's gold issues including Guldkrone tariff series and Speciedukat reform (Forordning 2. Januar 1658) |
| *Christian V — Kronemønt, speciedalere og dukater — Glückstadt 1671-1696* | 2022 | Glückstadt phase under Christian V — the 1671 Mint Ordinance formalising the 10½-Krone-Fuß, with full type catalogue 1671-1696 |

**Plus:** Sven Aagaard, «Beskrivelse af Christian IV's hebræermønter 1644-1648» — online at <https://www.danskmoent.dk/myst/aag1.htm>. Establishes the Hebræermønt as Torstenson-War coinage at concealed fineness, NOT a formal Müntzfuß-ordinance issue.

**Plus:** Ingvardson & Märcher 2010, «Christian 4.s guldmønt fra Esrum Møllegård», in *Danefæ — Skatte fra den danske muld*, Nationalmuseet, pp. 254-257 — bibliographical record at <https://portal.research.lu.se/en/publications/christian-4s-guldmønt-fra-esrum-møllegård>. Three Christian-IV double-Guldkroner 1628 (Hede 28) found at Esrum 2008-2011.

---

## 5. Standard reference catalogues

| Catalogue | Author / Year | Coverage | Access |
|---|---|---|---|
| **Schou** | H. H. Schou, *Beskrivelse af Danske og Norske Mønter 1448-1814 og Danske Mønter 1815-1923* (1926) | Danish + Norwegian standard type catalogue. Sub-numbers (Schou 39/40 for Pumphosenkrone 1665, Schou 11-15 for 2-Krone 1675) | paper-only |
| **Friedberg** | *Gold Coins of the World* (current ed. 9, 2017) | International gold-coin reference | paper-only; some lookup via Bruun PDFs which cite Fr# inline |
| **Lange** | **Christian Lange** (1845-1914), *Chr. Lange's Sammlung schleswig-holsteinischer Münzen und Medaillen*, **I-II, Berlin 1908-1912** (reprint 2010). Band I: 266 pp., plates 1-33 — Schauenburg dukes and counts before 1460. **Band II: 342 pp., plates 34-87 — the Oldenburg princely house in Schleswig-Holstein (Gottorp, Sonderburg, Norburg, Glücksburg, Plön), Schauenburg counts in Holstein-Pinneberg, Rantzau, medals.** | Schleswig-Holstein-specific catalogue, cited by Künker, Numista, Bruun and Jensen alike. Sub-letters (Lange 444 vs 444A vs 447B = Bruun-recognised sub-variants) | **CORRECTION 2026-09-04:** this row previously read «Aage Lange, *Sønderjyske og slesvig-holstenske Mønter 1522-1864*». No such work was found in any search; every citation traced (danskmoent's own bibliographies, Jensen 1971 «Lange nr. 527», Künker «Lange 449», Numista «Lange# 373») resolves to Christian Lange 1908-12. — **No free full text.** Google Books has Band II scanned but **snippet-only** (search works: «Goldgulden» → 12 pages, «Sonderburg Goldgulden» → pp. 2, 10, **322**); HathiTrust has the 1908 volume «Limited (search only)»; archive.org, NNP, Heidelberg digi.ub, ZVDD and the DDB have nothing. The work is public domain (author d. 22.12.1914, +70 = 1985) — the restriction is institutional caution, not copyright. To buy: original 2-vol set ~1 795 € (Breuer Münzen); a b/w reprint of both volumes from Münzen Möller; an original realised 750 € at Münzen & Medaillen 46 (2018). **If ever bought, Band II is the one this project needs.** Meanwhile many Lange numbers are obtainable free from danskmoent's per-ruler concordance tables and from Jensen 1971 (§3a). |
| **Sieg** | *Sieg Møntkatalog* (annual, 2018+) | Modern Danish + Norwegian catalogue, decimal sub-numbers (Sieg 11.1 vs 11.2 vs 11.6) | paper-only |
| **Brekke** | Ahlström / Brekke / Hemmingsson, *Norges Mynter / The Coinage of Norway* (1976, Stockholm) | Norwegian standard catalogue. Brekke# 31-36 = Norge 24-Skilling Dansk 1772-1788 | paper-only |
| **Hede** | Holger Hede, *Danmarks og Norges mønter 1541-1814, 1814-1977* (1978) | Danish + Norwegian — see § 2.1 above | partially via danskmoent.dk |

---

## 6. Encyclopedic + reference web sources

### 6.1 Wikipedia (DE / EN / DA / UK)

**Heavy users in our project:**

| Article | URL | Used for |
|---|---|---|
| Wikipedia DE «Reichstaler» | <https://de.wikipedia.org/wiki/Reichstaler> | 1566 Augsburger spec, 29.23g/889‰, «bis etwa 1700 Hauptmünze» |
| Wikipedia DE «Speciestaler» | <https://de.wikipedia.org/wiki/Speciestaler> | Hannover 1738-1802 8⁄9 fineness, Hamburg 110k 1730-1764, function-end ~1700 |
| Wikipedia DE «Leipziger Fuß» | <https://de.wikipedia.org/wiki/Leipziger_Fuß> | 16. Jan 1690 treaty, 1692 Leopold decree, 1738 Karl-VI Kommissionsedikt |
| Wikipedia DE «Konventionstaler» | <https://de.wikipedia.org/wiki/Konventionstaler> | 7. Nov 1750 Austria, 20. Sept 1753 Bavaria, spread to Saxony |
| Wikipedia DE «Sächsische Münzgeschichte» | <https://de.wikipedia.org/wiki/Sächsische_Münzgeschichte> | Zinna 1667 Saxon-Pivot, ⅔-Thaler as Hauptnominal, Bergbau-Speciesreichstaler |
| Wikipedia DE «Zinnaer Münzfuß» | <https://de.wikipedia.org/wiki/Zinnaer_Münzfuß> | 1667 Brandenburg+Saxony, 9-Fuß retained, 10½-Fuß for Scheidemünzen, 1668 Brunswick joins |
| Wikipedia DE «Augsburger Reichsmünzordnung» | <https://de.wikipedia.org/wiki/Augsburger_Reichsmünzordnung> | 1559 Ferdinand I edict, 1566 Reichsabschied accepting silver Thaler |
| Wikipedia DE «Corona Danica» | <https://de.wikipedia.org/wiki/Corona_Danica> | 1618 introduction, 1624/25 production end, Frederik III continuation 1651-52 |
| Wikipedia DE «Deutsche Währungsgeschichte vor 1871» | <https://de.wikipedia.org/wiki/Deutsche_Währungsgeschichte_vor_1871> | Wettiner+Welfen as main producers, gradual erosion |
| Wikipedia DE «Hamburger Bank» | <https://de.wikipedia.org/wiki/Hamburger_Bank> | 1619 founding, Mark Banco, 1875 absorption into Reichsbank |
| Wikipedia DE «Schleswig-Holsteinische Speciesbank» | <https://de.wikipedia.org/wiki/Schleswig-Holsteinische_Speciesbank> | 1776 Altona Bank founding |
| Wikipedia DA «Krone (møntenhed)» | <https://da.wikipedia.org/wiki/Krone_(møntenhed)> | Danish-language context for modern Krone vs historic Krone-Mønt |
| Wikipedia DE «Speciesbank» / «Königliche Münze zu Altona» | (linked) | Altona mint history, 1771 founding, 1863 closure |

**DeWiki «Taler»** — `dewiki.de/Lexikon/Taler` — German-language alternative encyclopaedia. Notably has «Vor allem die seit 1641 geprägten französischen Taler, die Écus blancs ... Hauptumlaufmünze» — supports our case for ⅔-Thaler / Écus blancs displacing Reichsthaler ~1700.

**Access:** WebFetch works for all Wikipedia. Use it freely.

### 6.2 lex.dk (Den Store Danske)

URL: <https://lex.dk/>

The current Danish national encyclopaedia (successor to Den Store Danske leksikon). Authoritative for Danish historical / numismatic terms.

Most used: <https://lex.dk/dansk_møntvæsen> — has the verbatim «Kroneudmøntningen blev fra 1692 afløst af kurantudmøntningen» and Møntloven 1873 references.

**Access:** WebFetch works.

### 6.3 MGM Münzlexikon — `mgmindex.de`

URL pattern: `https://www.mgmindex.de/index.php?title={Term}`

A specialised German numismatic dictionary («Münzen, Geschichte, Menschen»). Best for **period-correct German numismatic terminology** and the precise relationship between «Species», «Specie», «Speciestaler», «Reichsmünzfuß» etc.

Most used: <https://www.mgmindex.de/index.php?title=Species> — defines Species ↔ Rechnungsmünze (Zähltaler), and the «bis Mitte 18. Jh. = Speciestaler» binding.

**Access:** WebFetch works.

### 6.4 Meyers eLexikon — `elexikon.ch`

Online edition of *Meyers Großes Konversations-Lexikon*, 4. Auflage 1885-1892 — the period-XIX-c. German encyclopaedia.

Most used: <https://elexikon.ch/Leipziger+Münzfuß> — redirects to the «Münzfuß» main article (Bd. 11, S. 890), which has verbatim period descriptions of Zinna 1667, Leipziger 1690 + 1738 Reichsfuß-Erhebung, Konventions-Fuß 1753, Graumannscher 1750, Konvention 1763.

**Tool note:** WebFetch may return 403. Use Chrome MCP. The full-text content sits in `document.body.innerText` after the navigation loads.

**Use as:** verbatim period source — critical when modern Wikipedia summaries are too compressed.

### 6.5 Bobzin — `hagen-bobzin.de`

URL: <http://www.hagen-bobzin.de/hobby/muenzfuesse.html>

Hagen Bobzin's amateur but careful compilation of European currency standards. Lists every major Müntzfuß with adoption year and key parameters.

Most used:
- «Münzfüße» (linked above) — the Müntzfuß overview table
- **«Geschichte einiger europäischer Währungen» (<https://www.hagen-bobzin.de/hobby/muenzen.html>) ⭐ — a dated chronicle of European currency events, and a different page from the Münzfüße table.** This is the more productive of the two for origin questions: it carries ordinance-level parameters year by year. Delivered in the 2026-08-16 ducat-origins work: Venice striking ducats from *Hungarian* gold «ab 1284», the Venetian weight reduction «erst 1526 auf 3,49 g», and the 1559 Reichsmünzordnung in both of its own formulations («67 Dukaten auf die Mark Gold zu 23 Karat 8 Grän oder 67,944 Dukaten auf die feine Mark Gold»). See `docs/research/ducat_origins.md` §6h.
- «Währungen in Böhmen, Sachsen, Schlesien und Brandenburg» (<https://hagen-bobzin.de/hobby/waehrungen_boehmen_sachsen.html>) — Bohemia's 1325 florin imitations; used in `ducat_origins.md` §6f
- «Lübisches Münzsystem» (<https://www.hagen-bobzin.de/hobby/muenzverein_wendisch.html>) — Lübeck Mark-Lübisch system, Hamburger Bank-Fuß 1769 / Altonaer Bank-Fuß 1777

**Caveats:** dating sometimes coarse (e.g. 1753 Konventionsfuß without distinguishing Austria 1750 vs Bavaria 1753), and uses analytic-didactic labels («Schleswig-Holsteinischer Kurantfuß») not always period-attested. Cross-check against period sources (Meyers, Wikipedia DE).

**Access:** WebFetch works.

### 6.6 coingallery.de — `coingallery.de` ⭐

URL: <https://www.coingallery.de/index.htm>

A non-commercial German site on **coins and medals of the early modern age** — «*Diese nicht kommerzielle Website zeigt und erläutert Münzen und Medaillen der frühen Neuzeit*». Privately run, carefully sourced, and unusual in what it hosts.

**The valuable part is not the coin galleries but the text archive:**

- **«Numismatische Texte»** (<https://www.coingallery.de/Texte/index.htm>) — **full texts and long extracts of numismatic monographs and journal articles**, most as PDFs, each cross-linked to the site section it belongs to. Includes items that are otherwise hard to reach: Herzfelder on the imperial mints of Nördlingen and Augsburg (MBNG 42, 1924), Gebhart on Taler and Goldgulden striking in the 16th c. (1924), Jäger on the Schlick counts' coinage (BNZ 17/18, 1954), **Roswita Denk, «Das Münz- und Geldwesen Ferdinands I.»** (KHM Wien exhibition catalogue 2003) — directly relevant to the ducat's 1559 codification.
- **«Städte und ihre Münzen»** (<https://www.coingallery.de/stadt/index.htm>) — city coinages, and the host of **Wilhelm Jesse, *Der Wendische Münzverein* (1927) in full text** at <https://www.coingallery.de/stadt/ostsee/_jesse_wend_muenzverein.htm>. That page supplied the Rhenish gulden's whole ordinance ladder 1340-1490 and the Lübeck Troyes-mark note; see `docs/research/de_reichsdukatenfuss.md` §1 and `ducat_origins.md` §6c.
- **«Inhaltsverzeichnisse numismatischer Zeitschriften»** (<https://www.coingallery.de/zeitschriften/index.htm>) and **«Numismatische Schriftenverzeichnisse»** — tables of contents for numismatic journals and bibliographies. Useful for *locating* an article by year and volume before hunting the text.
- «Prägungen der Stadt Köln» with Noss index nos. 1-657 (1493-1793).

**Why it matters for us:** most of our German-side ordinance evidence is otherwise locked in printed monographs. This site is the one place found so far that puts that literature online in citable form.

**Caveats:** the texts are «*meist nur Auszüge, ohne Abbildungen und Fußnoten*» — extracts without illustrations or footnotes, so page-level citation must come from the printed original the page names. The transcriptions carry no pagination of their own; cite by article + section (see the §5a note on paper-only refs).

**Access:** plain static HTML, no bot defences. WebFetch works; the browser tools work better for long pages, since several run to hundreds of KB and WebFetch's summariser will truncate or conflate figures — the 2026-08-16 session had a summariser merge two unrelated numbers from this site before the raw text was read directly.

### 6.7 Künker — `kuenker-numismatik.de`

URL: <https://www.kuenker-numismatik.de/taler-praegungen/>

Künker is Germany's largest numismatic auction house. Their reference page on Taler-Prägungen has compact, well-written summaries with key dates.

Most used quote: «Konventionstaler ... 13⅓-Talerfuß ... anstelle des 1566 vereinbarten 9-Taler-Fußes» — clean expression of the 9-Fuß → 13⅓-Fuß substitution.

Also Künker auction archive: <https://www.kuenker.de/de/archiv/stueck/{N}> — useful for individual specimen photos and provenance.

**Access:** WebFetch works.

---

## 7. Auction houses

### 7.1 Stack's Bowers Bruun catalogues — see §1.3 above (primary specimen source)

### 7.2 Künker Auction Archive

<https://www.kuenker.de/de/archiv/stueck/{N}>

Individual auction lots with photos. Useful when an entry references a specific Künker provenance (e.g. KM# 154 specimen at Künker auction 2017).

**Access:** WebFetch works.

### 7.3 NGC PriceGuide — **moved to §1.5**

NGC is no longer merely an auxiliary price lookup: since NumisMaster went offline
(§1.4) it is the **live custodian of that catalogue**, so it now sits with the
catalogue sources. Full entry — access surface, API findings, region coverage,
measured volumes, field fill-rates — at **§1.5**.

Prices themselves remain **out of scope** for this project (§7a).

### 7.4 Greysheet — `greysheet.com`

<https://www.greysheet.com/prices/item/{slug}?gsid={N}>

Bulk numismatic price data. Last-resort confirmation source; rarely adds new info.

**Access:** WebFetch usually works.

### 7.5 coinsbook.net

<https://www.coinsbook.net/coins/{slug}>

European auction database. Useful for post-1700 Danish/German coins. Has mintmaster initial mappings sometimes missing elsewhere.

**Access:** WebFetch works.

### 7.6 ucoin auctions

ucoin (see §1.2) also has past-sale data per `tid` page. Useful for additional specimen weights.

---

## 8. Museum sources

### 8.1 IKMK Berlin — `ikmk.smb.museum`

Berlin Münzkabinett (Staatliche Museen zu Berlin). One of the world's premier coin collections.

URL pattern for individual coins: `https://ikmk.smb.museum/object?id={N}&download=json_ext` — returns the full record as JSON.

**Access notes:**
- Direct WebFetch on the JSON endpoint works
- For bulk lookups, use browser console (Chrome MCP) on the origin domain to bypass CORS issues — fetch script described in CLAUDE.md «Tools and resources»

**Use as:** authoritative museum-grade specimen images and metadata when you need photo confirmation.

Discovery quirks (full-text `quick_search` noise, year-only fetch filter, modern-geography mint-country geocoding, the 2026-05-29 scope-purge): see §13.8 below.

### 8.2 Nationalmuseet København — `natmus.dk`

Danish National Museum. Holds the largest Danish-coin collection and is the home of the Esrum Schatzfund Christian-IV-Doppelguldkronen (Hede 28, 1628).

Notable URLs:
- <https://natmus.dk/webdok/christian-4s-svindler-moent-fylder-400-aar/> — popular article on Christian-IV «svindler-mønt» (Corona Danica) 400-year anniversary
- (museum collection database not as web-scrapable as IKMK)

**Access:** WebFetch works for public-facing pages.

### 8.3 Royal Coin Cabinet, Copenhagen (KMM / KMK)

Den Kongelige Mønt- og Medaillesamling (KMM), part of Nationalmuseet — the world's most comprehensive Danish-coin collection (500 k+ objects). **Harvestability investigated 2026-06 — accessible via the Nationalmuseet open API, but the public records are mostly sparse.**

**Access route — open API, NOT Chrome.** `api.natmus.dk` (open since 2018, Swagger at `/swagger`, spec at `/swagger/docs/v1`). Two relevant search endpoints:
- `GET /search/public/simple?query=…&size=…&offset=…` — **currently broken** (HTTP 500, server-side Newtonsoft `JToken` cast bug). Do not use.
- **`POST /search/public/raw`** — **works (HTTP 200, no auth).** Raw Elasticsearch query DSL → standard `{hits:{total, hits:[{_index, _source}]}}` response. Index is `cumulus_public_assets`, 2 329 954 docs across all Nationalmuseet collections. This is the harvest route — plain `urllib`/`requests` POST with JSON body; no Chrome/Cloudflare involved.

**Enumeration — yes, by collection code.** Aggregating `collection.keyword` gives the per-collection counts; **`KMM` = 707 969 records** (largest collection). Filter `{bool:{must:[{term:{"collection.keyword":"KMM"}},{term:{"type.keyword":"object"}}]}}` → **639 600 object records** (the rest are `type:asset` = images). Paginate with `size` + `from` (ES default window `from+size` ≤ 10 000 — use `search_after` or a scroll/PIT for deeper enumeration). Text/field filters work (`{match:{nominal:"speciedaler"}}` → 1 245 hits; `nominal` / `materials` / `objectIdentification` / `protocol` / `foundEvents` / `creationEvents` / `measurements` / `descriptions` are real `_source` fields).

**Call limits.** No API key, no auth on `/search/public/raw`, no documented rate-limit. The API self-describes as «very much a work in progress … breaking changes [may] occur» — treat as fragile (the `simple` endpoint is already broken). Be polite (low rate, identifiable UA) as with IKMK.

**Data-richness — globally thin, but the in-scope subset is usable.** Across ALL 639 600 KMM object records the populated-field rates look poor (`nominal` 46 %, `materials` 18 %, dating 21 %, `measurements` 4 %, `descriptions` 0 %) — because the collection spans all eras/world coins (ancient → modern), most of which are minimally catalogued. **But the in-scope subset is far richer.** Sampling the **1560–1850 window** (filter `range:{"creationEvents.yearFrom":{gte,lte}}` — NB years are *strings*, so a lexicographic range leaks short years like Roman «181»; convert to int at harvest) → **41 355 records**, with these populated-field rates (use the TOP-LEVEL fields `authority` / `nation` / `place` / `typeNumber`, NOT `actor` or `creationEvents.placeElaborate` which are empty):

| field | populated | share | example value |
|---|---:|---:|---|
| `nation` (realm) | 39 193 | **95 %** | «Slesvig-Holsten» |
| `authority` (ruler) | 36 665 | **89 %** | «Johan Adolf» |
| `typeNumber` (catalogue) | 26 486 | 64 % | — |
| `materials` (metal) | 19 284 | 47 % | «sølv» |
| `place` (mint) | 11 330 | 27 % | «Holsten» |
| `measurements` (**weight only**) | 7 953 | 19 % | `{unit:"Gram", dimension:"Vægt", data:28.85}` — no diameter exists |
| `descriptions` / inscriptions | ~0 | 0 % | — |

Sampled records are genuinely in scope, e.g. «1/16 thaler, 1596/1597, **Johan Adolf**, Slesvig-Holsten, sølv» (Johann Adolf of Gottorp), «½ daler 1573», «4 skilling 1644». Noise to filter: `Regnepenning` (reckoning jetons → §9.2 exonumia) and string-range leakage (numeric year gate fixes it).

**Verdict.** Harvestable via `POST /search/public/raw` and **moderate value for our scope** (revised up from the global-stats first impression). Strengths: ruler (89 %) + realm (95 %) + often `typeNumber` (64 %) give a solid match/dedup signal against Hede/Bruun/Numista, and ~8 k in-scope specimens carry a weight. Gaps vs IKMK: `place`/mint only ~27 % (so entity classification leans on ruler+realm heuristics for the rest), **weight is the only measurement** (no diameter, no fineness), and **no inscriptions/legends** (0 %). If built: filter `collection=KMM` + `type=object` + numeric year-gate 1559/1514–1914 + drop exonumia nominals; map `measurements`→weight, `materials`→metal, `nominal`→denomination, `authority`→ruler, `place`→mint, `nation`→realm/entity hint, `typeNumber`→catalogue, `objectIdentification`→inventory, `foundEvents`→provenance note. The cross-source merger dedups against existing Danish/SH sources. **Full harvest strategy (API mechanics, `search_after` enumeration, dirty-`nation` scope filter, 4-phase pipeline plan, field mapping): `docs/KMK_HARVEST.md`.**

**Image presence is determinable from the cache (no page visit needed).** A KMM record's `related.assets[]` with `type: "still"` == the record HAS photo(s) on the natmus page; an empty/absent assets list == the page shows the «Genstanden er endnu ikke affotograferet» (not-yet-photographed) placeholder. **Verified by live spot-check 2026-06-08**: KMM 290904 (3 still-assets) renders 3 photos; KMM 123284 (0) renders the placeholder. `absorb_seeds_into_final_v2._kmm_specimen_has_image` reads exactly this. So an agent can answer «which specimens have images» from the cache, not only the user on the page. (`drawingExists` is a separate boolean for line-drawings.)

**KMM citation thinning (render declutter, 2026-06-08).** 79 % of all KMM citations carry NEITHER a weight NOR an image — bare «museum holds a specimen» records. `absorb._suppress_weightless_museum_overcollection` thins per coin by information class: **weight** (±image) → untouched (the §9a weight-specimen min/mid/max thinning owns those); **image-only** (no weight) → keep 3; **neither** → keep 1. Surplus hidden via `display: false` (data kept per §9a — NOT deleted; the URLs stay queryable). Weight presence is read from cache `measurements[dimension="Vægt"]` (`_kmm_specimen_has_weight`).

---

## 9. Academic / research repositories

### 9.1 Lund University Research Portal — `portal.research.lu.se`

Bibliographical records for Lund-affiliated researchers (e.g. Gitte Tarnow Ingvardson, Michael Märcher).

Most used: <https://portal.research.lu.se/en/publications/christian-4s-guldmønt-fra-esrum-møllegård> — Ingvardson & Märcher 2010 Esrum article record.

**Use as:** stable bibliographical handle for paper-only Danish numismatic articles.

### 9.2 Google Books

For 19th-c. Wilcke/Hede/Schrötter etc. snippets when no direct PDF exists.

---

## 10. Period archival sources (for hardcore verification)

These are **paper-only**, accessible only via specialist libraries:

| Source | Year | Use |
|---|---|---|
| Wilcke I/II/III | 1919/1924/late | Primary attestation of Forordninger 1588-1730 |
| Schou catalogue | 1926 | Type-level Danish numismatic catalogue |
| Hede 1978 | 1978 | The full canonical Hede catalogue (the danskmoent.dk web edition is a partial digitisation) |
| Schrötter, *Wörterbuch der Münzkunde* | 1930 | German numismatic dictionary, period-correct definitions |
| Aagaard monographs | 2004/2011/2022 | Modern Danish specialist research |
| Brekke, *Norges Mynter* | 1976 | Norwegian standard catalogue |
| Sieg Møntkatalog | annual | Modern Danish/Norwegian catalogue with .1/.2/.3 sub-variant numbering |

**When you absolutely need to verify a fact and online sources don't suffice:** ask the user. They have access to some of these in paper.

---

## 11. By-period quick lookups

| Period | First-line sources |
|---|---|
| **1559–1620 HRR / Reichsmünzordnung era** | Wikipedia DE «Augsburger Reichsmünzordnung», «Reichstaler»; danskmoent.dk Hede c4 series |
| **1618-1648 Christian IV Glückstadt + Tridecennium** | Wilcke I, danskmoent.dk Hede c4, Aagaard «Hebræermønter», Bruun PDF Part II |
| **1648-1670 Frederik III Glückstadt + Copenhagen** | Aagaard 2004 + 2011, danskmoent.dk Hede c5, Hede NNUM «Frederik III's guldkroner», Bruun PDF Part II |
| **1670-1696 Christian V Glückstadt** | Aagaard 2022, danskmoent.dk c5h*+c5mord, Bruun PDF Part II |
| **1696-1730 Frederik IV Tönning (Gottorp) + Holstein** | Bruun PDF Part II (KM# 169-180 family), Numista per N#, ucoin secondary |
| **1700-1750 Christian VI Copenhagen / Reichsdukatenfuß** | danskmoent.dk Hede c6, Wikipedia DE «Reichsdukatenfuß», Bobzin |
| **1750-1813 Frederik V / Christian VII Helstaten + Statsbankerot** | Wikipedia DE «Konventionstaler», Bobzin, danskmoent.dk Hede c7+ , lex.dk «dansk møntvæsen», Bruun PDF Part II/III |
| **1813-1875 Rigsbankdaler / Krone-reform** | lex.dk «Møntloven 1873», danskmoent.dk «aclove1.htm» (Møntlov register) |
| **Hamburg / Lübeck banco system** | Wikipedia DE «Hamburger Bank», Bobzin «Lübisches Münzsystem», Soetbeer 1869 + Shaw 1896 (refs in `german_fuesse-references.yml`) |

---

## 12. Cross-references in this project

- `docs/research/9_thalerfuss.md` — heavy use of Wikipedia DE Reichstaler / Speciestaler / Leipziger Fuß / Konventionstaler / Sächsische Münzgeschichte / Zinnaer / Augsburger; Bobzin; Meyers eLexikon; Künker; MGM «Species»; Hede (via danskmoent.dk)
- `docs/research/krone_muentzfuesse.md` — heavy use of Hede NNUM articles (Kronemønten + F3 Guldkroner); Wikipedia DE «Corona Danica»; Aagaard 2004/2011/2022; Wilcke I/II; Bruun PDF Part II/III; danskmoent.dk c5h{N}.htm pages
- `docs/research/hamburg.md` — Soetbeer 1869, Shaw 1896, Bindseil 2019, Bobzin, Wikipedia DE «Hamburger Bank»
- `docs/research/altona.md` — Wikipedia DE «Königliche Münze zu Altona», Schleswig-Holsteinische Speciesbank
- `data/locations/*-references.yml` and `data/shared/german_fuesse-references.yml` — bibliography slots for all of the above with verbatim quotes

---

## 13. Known-issues log — dated errata + quirks of the day

> **Purpose.** Every time a source publishes a wrong value, changes its
> URL scheme, gates behind a new bot-protection layer, or reveals an
> idiosyncratic cataloguing convention, log it here with a date. The
> goal is to **stop re-discovering the same quirks**: each entry below
> already cost a session of detective work, and the next session that
> hits the same pattern should recognise it in 30 s rather than 30 min.
>
> **Format per entry:**
> - Bold one-line description with date.
> - Specific case (coin id, URL, lot number, page) so the entry is
>   verifiable.
> - Diagnosis (what's actually wrong / different from naive read).
> - Workaround / decision (what we did + what future sessions should do).
> - Optional citation of the commit or audit that closed the case.
>
> **When to add an entry.** Anytime you spend > 15 min figuring out why
> a source gives a surprising answer. Even if the explanation feels
> obvious in hindsight — that hindsight is exactly what future-you
> won't have.
>
> **When NOT to add.** Trivial typos in a single coin record that get
> fixed inline. The threshold is «would another session hit this same
> pattern again». Pattern-level quirks belong here; per-coin one-offs
> belong in commit messages / coin `verification_note`.

### 13.1 Numista (en.numista.com)

**Numista 301740 publishes 0.49 g for Christian-IV Søsling 1640-48 — anomalous (2026-05-03 / 2026-05-13).**
Numista has two entries for the same physical coin under different Krause-volume registers:
- N# 199146 (KM-DK# 25, issuer «Glückstadt, City of») publishes weight 0.76 g — within Hede c4h178 envelope (Soll 0.704 g).
- N# 301740 (KM-SH# 87, issuer «Schleswig and Holstein, Danish duchies») publishes 0.49 g — **Δ ≈ −30 %, outside any specimen-variance band**. The same coin record at Numista carries a Hede#178B note in its body, so the catalogue knows it's the same type as the Hede entry; the 0.49 g reading is a user-edit error on the KM-SH side only.
*Diagnosis.* Numista's per-tid records are user-edited; cross-volume coins (Krause-Denmark + Krause-SH for one physical coin) get parallel records that drift independently. Always cross-check both KM-volume records before trusting either.
*Decision.* Both readings preserved in `weight_rough_g[]` per §9a (user instruction 2026-05-13: «якщо вага відрізняється, це просто такий артефакт з джерела»). The reader sees the variance; no «error» commentary in role-3 prose. — commit `8b4cab1`.

**Numista 108979 publishes 8.428 g for ⅙ Speciedaler 10-Schilling SH Courant — 38 % over Hede Soll (2026-05-13).**
KM-128 Christian VII 1787-96 ⅙ Speciedaler has Hede c7h42 Bruttovægt 6.129 g, Finhed 0.687, Finvægt 4.214 g. Three sources cluster (Hede 6.129 / ucoin 6.13 / Bruun Part II lot 13246 6.10). Numista 108979 publishes 8.428 g standalone.
*Diagnosis.* **8.428 ≈ Finvægt × 2.** Most likely the cataloguer typed Feinvægt × 2 into the weight field, OR confused with the adjacent denomination KM-130 ⅓ Speciedaler. Pure Numista user-edit artefact, not a real specimen weight.
*Decision.* Preserved with attribution; Numista N# stays as authoritative type-id for catalogue lookup independent of the weight cell. — commit `8b4cab1`.

**Numista cache (pre-2026-05-11) lacked the `Composition` field entirely (2026-05-11).**
Our `scripts/cache/ucoin/_url_index.json` schema only stored `denom / diameter_mm / fineness / km / source / url / weight_g / year`. Discovered via investigation of `dk-tid-163075` (10 Ducat 1588) whose ucoin page shows «Composition · Gold» but our local cache never captured it.
*Decision.* Built the dedicated `_composition.json` sidecar via `scripts/maintenance/ucoin_fetch_composition.py`; now stores composition + finer dimensions (thickness, edge_type, shape, alignment). See §13.2 for the resulting ucoin-harvest saga.

**Numista catalogue search `a=YYYY` year filter matches DATED specimens only — undated coins invisible (2026-05-18).**
The `/catalogue/index.php?...&a=YYYY` URL parameter filters per **specimen-level Date column entries that carry a literal year**, NOT by the type's `min_year`/`max_year` metadata. Concrete proof: NID 54915 «1 Søsling Christian IV first type» has `min_year=max_year=1602` in our cache but its per-specimen Date column reads «ND (1602)» (undated, attribution year). `?a=1602` returns **0 results** despite the type existing. `?a=1958` for NID 14546 (literal 1958 specimen) returns it correctly.
*Diagnosis.* Numista's search index keys off per-specimen Date entries; types whose specimens are all undated (the common case for pre-1650 small change) are completely invisible to `a=`. The §BO.1 step 2 sweep undercounted dramatically because of this.
*Decision.* For coverage audits, **use issuer-landing-page enumeration** (`<code>-1.html` or `?e=<code>&p=N&q=200`) with client-side year filtering on the row's display year. The listing page renders both dated AND ND-attributed specimens in row text, so client-side parsing catches both. See `docs/HARVEST_GUIDE.md` §«Numista catalogue enumeration» for the full pattern. — commit `8b60f2e`.

**Numista `?ru=` ruler filter trips Cloudflare aggressively (2026-05-17).**
Per-issuer + ruler combination URLs like `?mode=avance&e=danemark&ru=2385` (Christian II) fire Cloudflare's challenge on the FIRST call from a session where other parameters worked fine. The `ru=` parameter appears more weighted in Numista's anti-abuse heuristic than other form fields. Once tripped, requires 3-min cooldown + soft re-entry via plain landing page (`denmark-1.html`) before resuming.
*Diagnosis.* Probably a combination of (a) the parameter being relatively uncommon for human catalogue browsing (most users click ruler-page links rather than constructing `?ru=` URLs), (b) ruler-filter results are server-rendered with more JOIN cost, making them a high-leverage target for bot defence.
*Decision.* **Avoid `?ru=` for bulk enumeration.** Use issuer-landing-page pagination (low risk) + client-side ruler filtering on row text instead. Per-NID `/N` page fetches survive at low risk even after long sessions. — see HARVEST_GUIDE.md §«Cloudflare risk levels per URL form».

**Numista listing-page year regex false-positives on NID digit strings (2026-05-18).**
The simple year regex `\b(1[5-7]\d{2})\b` applied to a coin-row's innerText can match year-shaped substrings INSIDE the NID number itself. Concrete case: NID 158259 «Medal — Start of conflicts between Schleswig-Holstein and Denmark» — the substring «1582» inside «158259» matched the regex, classifying a 1848 medal as a 1582 SH-Danish-Duchies pre-1602 coin. Saved a bogus cache file that had to be deleted. NID 152374 has the same risk («1523» substring) but was already in cache with incorrect min_year=1523 from an earlier API harvest — actual year 1808-1839 (Frederik VI era).
*Diagnosis.* `\b` word-boundary doesn't help here because the year-shaped substring is at the start/middle of a digit run. The regex matches the first 4-digit year-shaped chunk in the row text — for some rows that's the NID itself (especially when `N# 158259` appears earlier in the row than the actual year column).
*Decision.* (a) Constrain the year-extraction regex to a section of the row text AFTER the title (e.g. after first `\n` past the title), OR (b) cross-verify suspect NIDs whose digit string overlaps the audit window via a single per-NID page fetch before treating them as in-window. The `_BO5_audit_2026-05-18.json` summary documents which audit-result NIDs are at risk. — commit `8b60f2e`.

**`st=` category-subtype filter is the key noise reducer for coverage audits (2026-05-18).**
The catalogue URL accepts `?st=1-2-3-47-154-5-54` (hyphen-separated subtype IDs) to filter the listing to coin subtypes only — excluding banknotes, tokens, medals, AND patterns/trial strikes (subtype 4, out of project scope per CLAUDE.md §9.1). For DK section this reduces the full listing 2212 → 868 entries (60 % noise drop) and yields the «in-scope coin types only» that we actually want to audit against cache.
*Discovery context.* User direction 2026-05-18 («тут ти можеш повимикати ті entries які нас не цікавлять і цим звузити пошук») pointed at the UI filter checkboxes, leading to the URL-parameter discovery. The category subtype IDs are visible by inspecting `<label><input type=checkbox value=NN>` elements on any issuer landing page.
*Decision.* Use `st=1-2-3-47-154-5-54` as the canonical coin-only filter for ALL future coverage audits. Documented in HARVEST_GUIDE.md §«Category subtype filter». Initial §BO.5 audit (without `st=`) over-counted the 1602-1914 gap by 42 entries (254 → 212 after refilter); those 42 were patterns/trial strikes that we wouldn't have harvested anyway. — commit `8b60f2e`.

**`e=denmark` vs `e=danemark` are different scopes — DON'T conflate (2026-05-18).**
The two issuer-code values look similar but resolve to different catalogue scopes:
- `e=danemark` = «Denmark» as a numismatic ISSUER (Kingdom of Denmark coinage only, narrow)
- `e=denmark` = «Denmark (section)» = country root including Greenland, Faroes, Schleswig duchies via cross-tagging, notgeld
The page title disambiguates: «Items from Denmark» (issuer) vs «Items from Denmark (section)» (root). Initial §BO.5 audit used the broader `e=denmark` and got 2212 entries; refined audit used `e=danemark` and got 868 (after `st=` filter). Both are valid for different audit goals — use `e=danemark` when you want strict Kingdom-of-Denmark scope, `e=denmark` when you want all DK-realm-affiliated tags.
*Decision.* Document the distinction; default to `e=danemark` for our project (we already handle SH-cluster separately under their own issuer codes per §BO.1). — codified in HARVEST_GUIDE.md §«Issuer code zoo». commit `8b60f2e`.

**Numista's `tri=date_asc` legacy sort parameter is broken — use `o=y` instead (2026-05-18).**
The form's `tri=date_asc` value (visible as a legacy option in the underlying form definition) produces ~26 partial results when combined with `ct=coin` — apparently a bug where only entries without a normalised currency-period anchor surface. Sometimes triggers Cloudflare on the malformed response.
*Decision.* Always use `o=y` (sort by year ascending) for date-ordered enumeration. Documented in HARVEST_GUIDE.md §«Sort orders». — commit `8b60f2e`.

**`t` and `t2` URL parameters are DIAMETER range, NOT year range (common confusion, 2026-05-18).**
The form fields `t` and `t2` look like they might be «year from / year to» — they're not. They're **diameter range** (mm). The catalogue page header confirms by rendering «Length or diameter: <t> × Width: <t2>» when both are set. Numista's catalogue search has NO year-range parameter, only single-year `a=`. For range audits, use issuer-landing pagination + client-side year filtering.
*Decision.* Documented in HARVEST_GUIDE.md §«Form field map» with explicit «NOT year range» warning. — commit `8b60f2e`.

**BO.6 v3 audit gained `denmark/p0_pre_lovkompleks` bucket — 20 Danish coins 1396-1513 for standards-continuity context (2026-05-21).**
The project's mission anchor is 1514 (Christian II Lovkompleks per CLAUDE.md §«Mission temporal scope»), so coins struck before that year are strictly out-of-scope for the rendered artefacts. However, understanding what coinage standards immediately preceded the 1514 four-act legal package is essential research context — what was Erik of Pommern (1396-1439) minting? What did Hans / John I (1481-1513) leave behind for Christian II to consolidate? User added a dedicated bucket on 2026-05-21 enumerated from the Numista DK catalogue page-1 listing (`?e=danemark&st=1-2-3-47-154-5-54&cat=y&p=1&q=200&s=c&o=y`, sorted year ASC). The 20 NIDs bracket the entire pre-Lovkompleks late-medieval window: Erik of Pommern (9 entries — Skærv, Brakteat «Hulpenning», Kobbersterling Naestved/Odense, Gold coin Lund, Sterling Naestved/Lund, Gros Gurre/Lund) + Christopher of Bavaria 1440-1448 (1 Hvid Malmo) + Interregnum 1448 (1 Hvid Malmo) + Christian I 1448-1481 (1 Hvid Malmo) + John I / Hans 1481-1513 (8: Goldgulden, Hvid Aalborg/Malmö, Skilling Copenhagen/Malmö, Noble, 2-Noble, 3-Noble). Bracketed by N#143452 (Skærv Erik 1396-1439) → N#428886 (2 Noble John I 1502).
*Decision.* Created as `denmark/p0_pre_lovkompleks` slot in audit JSON (not part of the BO.6 v3 original enumeration; appended after the fact 2026-05-21). PRIORITY-1 for Numista batches in HARVEST_ROUTINE.md §2.2 until closed (~4 hourly cron runs × 5 NIDs). Defensive sampling §7.5 does NOT need to fire for this bucket — every NID was hand-verified against the listing-page text before insertion (no false-positive risk from the year-regex enumeration that hit DK p4 and NO p2). Cached data will inform Phase 0 (pre-1514) descriptions on the Denmark display page — distinct from the rendered phases (which start at 1514) but referenced as «what came before» context. — bucket creation 2026-05-21.

**BO.6 v3 NO p2 in_scope_nids contained 105 pre-1513 entries — Norway pre-Lovkompleks Pennings + Hans-era coinage (2026-05-21 follow-up).**
The hourly harvest routine sampled N#117344 from NO p2 gap_nids and got «1 Penning - Haakon VI Magnusson 1355-1380» — same year-regex-false-positive shape as the DK p4 Margrethe II case below. Follow-up enumeration of the NO catalogue listing page (`?e=norvege&st=1-2-3-47-154-5-54&cat=y&p=2&q=200&s=c&o=y`) via Chrome MCP found that 114 of the 200 rows have first-year text < 1514. Cross-reference: 105 of NO p2's prior `in_scope_nids` were pre-1513 (¼ Penning ND 1205-1260 stretches up through Hans 1500-1513 Goldgulden and 1-Skilling). All 105 reclassified to `oos_excluded_nids`. Two Christian II 1513-1523 ND attributions (N#110323, N#124914) kept in-scope per established curation — the project's 1514 anchor is about the Lovkompleks framework, not a hard «zero coins minted before 1514» cut, and Christian II ND attributions span the legal-anchor year. **0 cached files needed deletion** — the routine's defensive sampling §7.5 prevented all cache writes for OOS NIDs.
*Diagnosis.* The BO.6 v3 client-side regex `?p=2&q=200&s=c&o=y` paginates by 200-item chunks sorted ascending; «page 2» of Norway naturally straddles the Penning→Speciedaler boundary because there are 200+ ND Penning types before 1513. The original «NO p2 (1513-1657)» label was a category guess, not a hard year filter. Listing-page year-regex matched any 4-digit substring in the row text — for «¼ Penning ND (1205-1260) … Skaare# 175, N# 122675», the regex picked up «1513» from somewhere (currency-period banner labels like «Penning (995-1387)» or page-header text «items 201-400 by year asc → reaches 1513») and mis-classified rows as in-scope.
*Decision.* Reclassified 2026-05-21 follow-up commit. NO p2 now correctly reports **88/27** (was 193/27); remaining uncached legit work: 61 NIDs. The routine's defensive-sampling rule (§7.5 of HARVEST_ROUTINE.md) was the catch mechanism — generalised pattern «sample-verify any fresh bucket before mass-harvest» works for both post-1914 (DK p4) and pre-1513 (NO p2) drift cases.

**BO.6 v3 DK p4 «gap» = 20 Margrethe II commemoratives (2001-2010), all post-1914 OOS (2026-05-21).**
The BO.6 v3 audit's `denmark/p4` bucket initially listed 124 in-scope NIDs with 20 «gap» entries. When the hourly harvest routine (`docs/HARVEST_ROUTINE.md`) tried to pick up that gap, it sample-verified N#1461 and found «10 Kroner Margrethe II 2001-2002» — completely outside the mission's 1791-1914 window. Chrome MCP follow-up samples (N#1462 Margrethe II 2004-2010, N#14840 Margrethe II 2004 Crownprince Wedding, N#137792 Margrethe II 2005 Ugly Duckling) confirmed the entire 20-NID list is post-1972. All 20: `[1461, 1462, 1463, 7434, 9399, 10404, 10603, 10648, 14558-14564, 14840, 31029, 37365, 37366, 137792]`.
*Diagnosis.* Same listing-page year-regex pattern as §13.1's earlier «year-substring inside NID» trap, but here it's a different failure mode: Margrethe II commemorative coin notes cite historic denominations (e.g. «in the tradition of the 1873 Krone-era…») and the BO.6 v3 client-side regex matched the historic year as the row's year. The coin's actual `min_year` (Margrethe II 1972-2024 reign) was overridden by the false-positive.
*Decision.* Reclassified all 20 NIDs out of `in_scope_nids` + `gap_nids` into a new `oos_excluded_nids` slot with full audit-trail reason. `denmark/p4` now correctly shows 104/104 closed (was 104/124 with 20 «stragglers»). The hourly routine's defensive check — sample-verify before mass-harvesting any «gap» bucket — caught this; future routines should always sample 1-2 NIDs from a previously-untouched bucket before fetching the rest. Audit-trail note added to the routine's §7 error-recovery section. — commit pending.

**Numista per-NID DOM = HTML `<table>` rows; use `table tr` not innerText regex (2026-05-19).**
Numista's per-coin page (`/N`) renders the spec block as a proper HTML `<table>` with `<th>` label + `<td>` value pairs. A naïve innerText extractor using `Label\nValue\n` regex on `document.body.innerText` works on SOME fields but fails inconsistently — line-break normalisation between cells is browser-rendering-dependent and one «Issuer» cell can return `null` while «Composition» returns OK. Reliable pattern:
```javascript
const dts = {};
document.querySelectorAll('table tr').forEach(tr => {
  const cells = tr.querySelectorAll('th,td');
  if (cells.length >= 2) {
    const k = cells[0].innerText.trim();
    const v = cells[1].innerText.trim();
    if (k) dts[k] = v;
  }
});
// then dts['Issuer'], dts['Composition'], dts['Weight'], …
```
Fields exposed: `Issuer`, `Type`, `Years` (NOT `Year` singular), `Value`, `Currency`, `Composition`, `Weight`, `Diameter`, `Shape`, `Demonetized`, `Number`, `Date`, `References`. Fineness extraction: parse the `Composition` value's parenthesised decimal — `Silver (.875)` → 0.875, `Gold (.980)` → 0.98; some entries store as `(875/1000)` so the regex needs to handle both decimal and fraction forms.
*Decision.* All per-NID extractors should use the `table tr` pattern; the innerText fallback only works for descriptive paragraphs (Obverse / Reverse prose blocks, NOT the spec table). — codified during BO.6 batch A.

**Numista `dav` (Davenport) ref captured in TWO formats — «EC II# N» + «EC II N» duplicate (2026-06-10).**
The Numista parser emitted the Davenport European-Crowns reference twice into one `catalog.dav` list — once with a stray `#` («EC II# 3656») and once without («EC II 3656») — the same ref (Davenport vol. II / III, number 3656) in two spellings. 218 entries across 9 numista seed entities carried the 2-element duplicate list. **Surfaced only on re-build:** the committed seeds predated the catalog-normalisation that collapses the `#` variant to the canonical scalar; the rendered final layer was always clean (the merger/absorb `_fold_catalog_indices` normalises the accumulated catalog, so final-layer `dav` had 0 duplicates).
*Diagnosis.* numista-parser-only artifact — other sources (hede/galster/ikmk/numismaster/bruun/ucoin) never carried the `EC II#` form. Pure seed-layer staleness, not a data error.
*Decision.* Materialized the seed-layer dedup (re-run `build_numista_seed` → scalar `dav`) — `b7b2165`, 9 entities. Aligns committed seeds with current builder output so future re-runs are clean diffs; no rendered-output change.

**Discrete issue-years lost by the thin chrome extractor — captured only the «Years» RANGE, not the date table (2026-06-10).**
The Numista «Years» feature field is the type's min/max RANGE («1496-1502»); the DISCRETE struck years live in a SEPARATE place — the «Manage my collection» date table (`table.collection`, first column: «Date / Undetermined / 1496 / 1502»). The HARVEST_GUIDE per-NID JS extractor read only `get('Years')`, so chrome-harvested entries got `year_first/year_last` but `year_list: null` → `build_numista_seed` fell back to a CONTINUOUS `year_ranges` `[[1496,1502]]`, falsely asserting strikings in 1497-1501. The whole downstream is already discrete-ready (`parse_numista_chrome` consumes `year_list`; `build_numista_seed` emits per-year `[[y,y]]`; the merger's `_union_year_ranges` prefers discretes) — the loss was purely at the HARVEST extraction step. **The v3 API does NOT help** — `parse_numista_api` hardcodes `year_list=null` (`/types/{id}` exposes only min/max; the discrete list needs the `/types/{id}/issues` endpoint, not currently fetched). Surfaced on the 1 Nobel John I (N#420401, «1496-1502» vs Numista's discrete 1496 + 1502).
*Fix (2026-06-10).* (a) HARVEST_GUIDE extractor now reads `table.collection` → `year_list` (empty = no dated issues → keep range, do NOT fabricate). (b) Re-harvested all 501 in-scope thin multi-year entries via Chrome MCP same-origin `fetch()` + DOMParser (≈30 NIDs/JS-call, 0.3 s internal pacing, 0 Cloudflare 403s through the logged-in session — see §13.2); 417 gained discrete years, 84 confirmed range-only. Propagated: 412 materialised into rendered finals across danish_norway + 5 German entities (gapped labels like «1622-1624, 1628-1629, 1631-1633» now render). **Residual:** 5 hanseatic_lubeck + 144 `_unclassified`-final coins whose numista seed routes to `_unclassified` (different entity bucket than their foundation) — blocked by the numista entity-routing backlog, NOT this fix; their `year_list` is in cache + `_unclassified` seed, ready for when they're classified.

### 13.2 ucoin (en.ucoin.net)

**ucoin slug-redirect-to-euro-cents is a RATE-LIMIT signal, not URL breakage (2026-05-13).**
Initial hypothesis (logged 2026-05-11 in `scripts/maintenance/ucoin_fetch_composition.py` header) was that ucoin restructured slugs and our heuristic-generated `_url_index.json` URLs no longer resolve. Symptom: pages built like `/coin/<slug>/?tid=<tid>` return HTTP 200 with a `<link rel=canonical>` pointing at a DIFFERENT tid — typically modern Euro-area pieces (50-euro-cent Ireland, 1-euro Italy, 1-euro Portugal). The canonical-tid validation guard correctly rejects these.
*Actual diagnosis (clarified 2026-05-13).* It's ucoin's anti-abuse rate-limit. After ~50 cumulative requests from one session-cookie ucoin starts serving wrong-tid canonical pages. Cookie clear resets the counter — and confirms it's rate-limit, not URL routing.
*Threshold measured 2026-05-13:*
| Pacing | First failure | Sustained ok | Effective rate |
|---|---|---|---|
| 2.5 s | req 37 | 36 in ~1.8 min | ~20 req/min |
| 10 s  | req 52 | 51 in ~9.4 min | ~5.4 req/min |
| 20 s  | session ended at req 42 with margin | 42 in ~14 min | ~3 req/min |
Slower pacing extends the ceiling marginally but the ~50-request session-cookie cap dominates.
*Decision.* `scripts/maintenance/ucoin_fetch_composition.py` keeps the canonical-tid guard (catches the bad-tid pages 100 %). Operational pattern: ≤ 45 fetches per cookie-cycle at 20 s pacing, then user clears cookies before resuming. The original «slug breakage» note in the script header is incorrect post-mortem — sluts ARE correct, the redirect is the rate-limit symptom. — commits `6db67f4`, `b4d925b`.

**Cloudflare bot-protection kicks in after sustained day-of activity (2026-05-13).**
After three productive sessions and ~130 cumulative requests in one day, session 4 was met with **HTTP 403 + Cloudflare «Just a moment… Performing security verification»** on every same-origin fetch. The page returns 200 in browser-with-JS but the verification challenge needs to complete; our `fetch()` from JS doesn't pass it. Cookie clear does NOT fix this — possibly makes it worse, since the `cf_clearance` cookie that proves prior challenge-pass is also wiped, forcing re-challenge with a now-suspect fingerprint.
*Decision.* On Cloudflare challenge, stop the harvest. Three resume paths: (a) wait ~24 h for IP cooldown, (b) user navigates to ucoin in a normal browser to manually complete the challenge — resulting `cf_clearance` cookie may pass through to automated requests, (c) switch network egress (VPN). The harvest is mechanical; pacing rule + canonical-tid guard preserves correctness; the bottleneck is anti-abuse throughput. — commit `bc4db51`, see TODO §M for the resumption playbook.

**ucoin Chrome MCP harvest at 31-60 s pacing — Cloudflare not a problem inside established user session (2026-05-18 / -19).**
The §M / §13.2 «deferred per Cloudflare» framing applies to ANONYMOUS fetches (Python urllib, WebFetch, Apify) — those hit 403. Chrome MCP routed through the user's already-logged-in Chrome session, however, never triggers the challenge. BR audit ran ~563 fetches across batches 1-16 (May 18-19, 2026) at 31-60 s random pacing — **0 canonical-TID failures**, 0 Cloudflare 403s. The §13.2 «~50-request session cookie cap» from 2026-05-13 was measured under tight pacing (2.5-20 s, where the 20 s case still hit limits at req 42); 31-60 s spacing appears to be below the rate-limit detection floor.

**ucoin catalogue listing pages PAGINATE — the slug→TID map needs all pages (2026-06-01).**
A period listing at `/catalog/?country=denmark&period=<NNNN>` splits across multiple pages at ~48 entries/page (e.g. `bremen_p1195` = 93 TIDs over 2 pages). A batch's target TIDs can sit on page 2+. The single-page anchor extractor (HARVEST_ROUTINE.md §4.3 part A) would then report those TIDs as `MISSING` and the routine would falsely defer the whole batch — even though the entries exist. Caught run IQ/255: all 5 batch-255 targets sat on page 2; the run detected the page-2 link, navigated `…&period=1195&page=2`, and completed normally. *Fix:* §4.3 part A is now pagination-aware — iterate `&page=N` accumulating the slug→TID map until every wanted TID resolves OR no further page link exists; only then treat residual TIDs as genuinely missing (§4.4). A TID absent after the LAST page is the real `MISSING` case, not one merely beyond page 1.
*Operational rule.* Chrome MCP + 31-60 s `sleep $((RANDOM % 30 + 31))` between fetches + canonical-tid guard via `/tmp/save_ucoin.py` = sustainable harvest pattern. Batch size of 40 TIDs per commit cycle ≈ 25-40 min wall time. The CLAUDE.md ucoin acceptable-use bound («≤ ~10 pages per session» for ad-hoc verification) still applies for non-research browsing; bulk catalogue harvest under the audit-driven BR workflow runs at higher volume because each fetch is contributing to a named TODO with provenance.
*Decision.* `docs/HARVEST_GUIDE.md` ucoin section updated from «deferred» to «active Chrome MCP route, 31-60 s pacing». — codified during BR batches 10-16; **done 2026-07-02** (the detailed «Per-source playbook → ucoin.net» section, the access-tier table row, and the «Future enrichment» continuation entry all now read ACTIVE).

**ucoin DOM = TAB-separated label/value pairs, NOT newline-separated — extractor regex must use `\t` (2026-05-19).**
First attempt at a ucoin extractor used the same pattern as Numista — `document.body.innerText` with regex `Label\n([^\n]+)`. Result: every field returned `null` despite the title rendering correctly. Dumping `document.body.innerText.slice(0, 2500)` revealed the actual structure:
```
Number	KM# 370
Country	Denmark
Period	Rigsdaler (1625 - 1699)
Ruler	Christian V
Currency	Danish rigsdaler
Composition	Silver 0.671
Weight (g)	22,27
Diameter (mm)	40,6
```
Labels and values are separated by a TAB character (`\t`), not newline. Reliable extractor:
```javascript
const g = (label) => {
  const re = new RegExp(label + '\\t([^\\n\\t]+)', 'i');
  const m = document.body.innerText.match(re);
  return m ? m[1].trim() : null;
};
const composition = g('Composition');           // "Silver 0.671"
const weight = parseFloat(g('Weight \\(g\\)').replace(',', '.'));  // 22.27
```
Also note: ucoin uses **comma as decimal separator** in numeric fields («22,27» not «22.27») — must `replace(',', '.')` before `parseFloat`. The fineness is embedded directly in the Composition value's metal-suffix (`Silver 0.671`), not in parens like Numista — extract via `/Composition[^\d]*(0?\.\d+|\d{2,3}\/\d{3})/`.
*Decision.* Per-TID extractor template lives inline in batch fetch loops; the `\t` separator + comma-decimal handling are mandatory. — codified during BR batch 16.

**ucoin listing-page slug collapse: same slug for N consecutive TIDs ≠ they share a URL (2026-05-19).**
The catalogue listing pages (`/catalog/?country=denmark&period=NNNN&page=N`) sometimes show clusters of 3-5 consecutive TIDs whose anchor extraction returns the *same* slug (e.g. TIDs 97399-97403 ALL appear with slug «denmark-1-krone-1675»; TIDs 97311/97312/97313 ALL show «denmark-1-krone-1680»). This is NOT a duplicate-coin artifact — these are distinct ucoin records that need different slug suffixes (`denmark-1-krone-1675-2`, `-3`, etc.) in their canonical URLs. The listing-page DOM exposes each anchor with the **bare slug stem** in the `href`, and ucoin's URL routing relies on the suffix to disambiguate. Building a URL as `/coin/<bare-slug>/?tid=<later-TID>` returns HTTP 200 + **«Page Not Found»** body — the bare slug routes only to the FIRST TID in the cluster; later TIDs return 404 because their actual canonical slug carries a `-N` suffix that the listing didn't expose.
*Diagnosis.* Listing-page anchor stripping at ucoin truncates the disambiguating numeric suffix from `<a href>` attributes, but the per-TID page redirector requires the full suffix to match. Likely an SEO-cleanup intent gone wrong — the listing wants «pretty» slugs but the page-router wasn't updated to be tolerant.
*Decision.* When listing-page extraction shows ≥2 TIDs sharing a slug stem, treat all but the lowest TID in the cluster as «slug unknown» — fetch them via search (`?tid=NNNNN` alone returns 404, not redirect, so can't shortcut) OR skip and recheck via the per-issuer Hede/KM cross-reference. For BR batch 16, this affected 5 TIDs (97400-97403, 99169) which were deferred to batch 17 for individual canonical-slug investigation. — flagged 2026-05-19.

**`a.href` survives, `a.getAttribute('href')` is sometimes neutered — Cloudflare query-string blackout (2026-05-19).**
When extracting TID+slug pairs from listing-page DOM via Chrome MCP, two superficially equivalent property reads produce different results:
- `a.getAttribute('href')` → sometimes returns `[BLOCKED: Cookie/query string data]` (a Claude in Chrome safety guard against query-string ingestion looking like cookie-stuffing? — unclear exact trigger). When this fires, the `tid=NNNNN` query parameter is stripped from the read.
- `a.href` (the property, not the attribute) → returns the fully-resolved URL string including query string. Safe to parse `tid=(\d+)` out of it.
The blocked-attribute case appears tied to Cloudflare-protected pages; same DOM read on an uncached page elsewhere returns the attribute fine. Don't fight it — just always use `a.href`.
*Reliable pattern:*
```javascript
document.querySelectorAll('a[href*="/coin/"]').forEach(a => {
  const h = a.href;  // property, NOT getAttribute
  const tm = h.match(/tid=(\d+)/);
  const sm = h.match(/\/coin\/([^\/?#]+)/);
  if (tm && sm) { /* record tid → slug */ }
});
```
*Decision.* Mandatory `a.href` (property) for all listing-page extraction. — codified during BR batch 16.

**`window.<global>` doesn't survive cross-page navigation — persist TID→slug maps to /tmp/*.json instead (2026-05-19).**
Tempting pattern: extract listing once, `window._batch_map = {...}`, then navigate per-TID and look up slugs from `window._batch_map`. Doesn't work — every `navigate` action discards the page's JS context entirely; `window._batch_map` becomes `undefined` on the new page. Even staying on the same domain doesn't help.
*Reliable pattern.* On enum phase, extract listing → return the JSON map → write to `/tmp/<batch>_slugs.json` via Bash heredoc. Then per-TID loop reads slugs from disk (or just inlines them into the navigate URL — Bash can substitute `${SLUGS[$tid]}` from a sourced shell array). Listing pages are expensive (also count against ucoin's per-session budget), so do the enum ONCE upfront with a TARGET-set filter:
```javascript
const TARGET = new Set(['97314', '97315', '97316', /* … */]);
document.querySelectorAll('a[href*="/coin/"]').forEach(a => {
  const tm = a.href.match(/tid=(\d+)/);
  const sm = a.href.match(/\/coin\/([^\/?#]+)/);
  if (tm && sm && TARGET.has(tm[1])) result[tm[1]] = sm[1];
});
```
This returns ONLY the slugs we need for the current batch, keeping the JSON small enough to round-trip cleanly through the tool's output truncation.
*Decision.* «Enum first, persist to /tmp, then iterate» is the canonical batch-fetch pattern. — codified during BR batch 16.

### 13.3 Bruun PDFs (Stack's Bowers L. E. Bruun Collection)

**Bruun parser pre-1500 year theft via Beskrivelsen + dashed catalog refs (2026-05-24).**
Three linked bugs in `scripts/bruun_parser/02_parse_lots.py` left every pre-1500 lot mis-dated. Discovered via `unified-dk-bruun-3831` (Hans Nobel) sitting under `seed_unsorted` with year_first=1791 despite meta_line clearly stating «<i>DENMARK. Noble, 1496. Malmö or Copenhagen Mint. Hans.</i>».
*Bug A — YEAR_RE 1500-floor.* Pattern `r"\b(1[5-9]\d{2}|20\d{2})\b"` started at 1500. Hans Nobel 1496, Hans Goldgulden 1481-1497, Erik VII Witten 1400, Christopher III 1440 etc. were silently ignored — parser fell through to whatever 1500+ year appeared next in body.
*Bug B — no meta_line priority.* Year extraction took FIRST match in `body_match[:600]` without checking meta_line first. Body typically carries catalog refs (Beskrivelsen 1791, Bruun-1898, edition years) — any of these could outrun the coin's actual year.
*Bug C — body fallback doesn't skip dashed catalog refs.* Even when meta-yearless, body fallback would capture «Dav-1311», «KM-543», «Bruun-3831» as if they were years.
*Bug D (builder-side mirror).* `scripts/maintenance/build_bruun_denmark_seed.py::parse_year` carried the same 1500-floor as defensive fallback regex, plus a pre-existing greedy `[01]?[01]\d\d` ND-medieval gate that false-positive-rejected «ND (1440)» / «ND (1496)» / «ND (1396)» because `[01]?` + `[01]` backtracking matched ANY 1-prefixed 4-digit.
*Diagnosis.* 15 pre-1500 lots affected across part1/2/3; 13 with confirmed wrong year, 2 with None. All in-scope coins now correctly classified to `nobel_fod` (Hans Nobel) / `reichsdukatenfuss` pre-I (Hans Goldgulden) etc.
*Fix.* Extracted `extract_year(meta_line, body_match)` standalone function. Widened YEAR_RE to `1[1-9]\d{2}` (1100+, full Scandinavian medieval — builder scope filter handles V2 truncation). Meta-line priority first, body fallback second. Body fallback skips matches preceded by `<Alpha>-`. Builder regex widened to `1[3-9]\d{2}`. ND-medieval gate tightened to `1[012]\d{2}` (only true 10xx/11xx/12xx). Comprehensive test suite (28 parser + 14 builder cases, real Bruun cache lots). — commits `70383cc` + `c230f7b` + cache regen `6e8d6b95`.

**Bruun «ND (…)» attribution flattened to a confident single year — range + undated-status lost (2026-06-16).**
A *correctly-read* year was still being mis-represented: Bruun marks undated coins «<i>ND (&lt;year(s)&gt;)</i>» — the year there is the cataloguer's *attribution*, not an inscription. Both `02_parse_lots.py` (sets `lot.year`) and the builder's `parse_year` flattened every such lot to the single **lower-bound** year, discarding (a) the range, (b) an abbreviated upper bound («<i>ND (1607-11)</i>» = 1607–1611, «<i>ND (ca. 1496-97)</i>» = 1496–1497), and (c) the undated/approximate status itself. Result: «<i>Goldgulden (Rhinsk Gulden), ND (ca. 1496-1497)</i>» (dk-bruun-3839/3840, Hans) rendered as a confident single-year «1496» strike. Discovered while auditing the year-widen of `unified-dk-hede-c7h13a`.
*Scope.* 84 in-scope «ND (…)» lots (1481–1914): 45 explicit ranges, 33 single-year attributions, 6 with «ca.» — incl. reign-window forms like «<i>ND (1481-1512)</i>» (Hans's full reign) that masqueraded as a confident 1481. Medieval «<i>ND (900-950)</i>» (251 lots) are unaffected — the lower-year class `1[3-9]\d{2}` excludes pre-1300, and the NDMED gate + 1481-floor scope filter already drop them.
*Fix.* New `parse_year_span(lot)` in `scripts/maintenance/build_bruun_denmark_seed.py`: detects an in-scope «ND (…)» meta_line, captures `year_first`/`year_last` (expanding an abbreviated upper bound via the lower year's century-prefix), and sets `year_verified=False`. A genuinely *dated* strike keeps the plain single year (no `year_verified` key → schema default). The `year_label` stays a clean decimal year/range («1496-1497») per §3a; the uncertainty rides the per-field `year_verified` flag → renderer emits the «(?)» marker (CLAUDE.md §4). The builder reads `meta_line` directly, so the seed is correct regardless of the still-flattened upstream `lot.year` (the «builder mirrors parser» pattern — here the builder is *ahead*; `02_parse_lots.py` is a candidate for the same range-capture if the cache is ever re-parsed).
*Propagation status.* Builder code fixed; the V2 Bruun seeds were **NOT** regenerated in the same commit — they are stale w.r.t. ~10 intervening builder/cache commits (`41efdf0` Aagaard→`others`, `4465c1b` km cross-register, cache re-parses `f5634abb`/`8af66ec`), so a clean regen folds that catch-up in too and then needs a `seed_unified` → `final` re-flow. The year fix lands in rendered data on the next *coordinated* Bruun regen (batched with the parked apply), not piecemeal. — builder commit (this change).

**Bruun parser adjacent-lot Friedberg bleed → phantom `friedberg` → wrong gold metal-inference (2026-07-17).**
`dk-bruun-7334` (Bruun IV lot 17113, «<i>6 Mark (Rejsedaler), 1704 … Dav-1289; KM-479.2; NMD-1A; Hede-38; Sieg-23.2; Schou-8; Bruun-7334</i>») was tagged `metal: gold` + `metal_verified: true` and surfaced in the *gold* seed_unsorted pass. The lot text carries **no Friedberg number**, yet the parsed `refs` held `friedberg: 230` — bled in from a **neighbouring lot** (user-confirmed). The bruun seed builder's metal-from-register inference reads a Friedberg number as a gold signal (Fr = gold catalogue) → inferred gold. The coin is unambiguously **SILVER**: Davenport 1289 indexes only large silver crowns, «Rejsedaler» = Speciedaler-class silver crown, 27.05 g = silver speciedaler weight. A commemorative Speciedaler for Frederik IV's 1704 Norway travel (Kingo hymn reverse).
*Fix (this pass).* Per-coin `_source_errata` on the bruun seed: `metal` gold→silver + drop the phantom `friedberg: 230`; reclassified → `9_25_thaler`/I/kurant (sibling 1704 Speciedalers km-480-2 / dk-tid-94244). The seed edit propagates through merger+absorb immediately. **NOT fixed (curator direction 2026-07-17): the Fr→gold metal-inference rule itself, and the parser-level adjacent-lot Friedberg bleed in `02_parse_lots.py`.** A bruun re-seed PRESERVES this erratum — `_source_errata` sits in `seed_merge._PRESERVE_ALWAYS_KEYS`, and the bruun builder goes through `write_v2_seed` → `merge_seed` like every other. (Corrected 2026-09-12; this note previously claimed the wholesale-write builder would revert it, which was false on both counts.) The parser bleed itself is still unfixed, so the erratum stays load-bearing. **Open scope question:** how many other bruun lots carry a bled Friedberg that silently gilded a silver coin — worth a sweep (`metal=gold` bruun seeds whose lot body_excerpt lacks «Fr-»).

**Cross-source merger: `friedberg` ↔ `fr` catalog-key synonym collision (2026-05-24).**
Numista API publishes Friedberg under `cat.fr`; Bruun PDF parser emits the same Friedberg under `cat.friedberg`. `_catalog_refs` carried both verbatim → zero shared keys → `primary["catalog"] = None` → match_pair couldn't merge. Same shape for `dav` (Numista) ↔ `davenport` (Bruun).
*Diagnosis.* Verified via match_pair simulation on Bruun-3831 vs Numista-420401: even with year-fix applied, refs `{friedberg:3, bruun_collection_id:3831, sieg:12, schou:2, galster:24}` vs `{fr:3, numista:420401}` had zero overlap.
*Fix.* Added `CATALOG_KEY_SYNONYMS = {friedberg → fr, davenport → dav}` mapping in `_catalog_refs`; when both synonyms attest the same key with different values, values are unioned per §«Data-accumulation principle». Tests: 15 cases. — commit `9076f65`.

**Nominal normalisation: «X» = «1 X» quantifier collision (2026-05-24).**
Bruun parser extracts denominations from meta_line without numeric prefix («Noble», «Speciedaler»). Numista API publishes with explicit «1 » prefix («1 Noble», «1 Speciedaler»). Pre-fix `normalise_nominal` handled cross-language synonyms (Noble↔Nobel, Thaler↔Daler) but NOT this implicit-one quantifier gap → `primary["nominal"] = False` → blocked merges.
*Fix.* Append `re.sub(r"^1\s+", "", s)` AFTER synonym substitution so «1 Rose Noble» → «1 rosenobel» → «rosenobel» works. Fractions «½ Ducat», multi-digit «10 Kroner», other quantities «2 Nobles» / «3 Nobles» (different denomination weights) stay distinct. Tests: 25 cases including real-world Bruun vs Numista pairs. — commit `d98fd77`.

**Ruler cross-language synonyms missing (Hans↔John I, Erik↔Eric, Margaret↔Margrethe) + trailing-dot bug (2026-05-24).**
Bruun writes «Hans» (Danish), Numista writes «John I (Hans I)» (English with Danish parenthetical). `_normalise_ruler` had `frederick → frederik` but no Hans↔John I mapping → primary["ruler"]=False → match_pair returned no_match. Parallel pre-existing bug: trailing-dot strip `re.sub(r"\.+$", "")` ran BEFORE whitespace strip, leaving «Christian IV.» with the dot intact when input was «Christian IV. (1588-1648)».
*Fix.* Added Hans/John I/II → hans, Eric → erik, Margaret → margrethe substitutions. Combined trailing-strip `[\s.]+$`. Tests: 17 cases. — commit `94ee8f8`.

**End-to-end verification.** `unified-dk-bruun-3831` (Hans Nobel) now in `nobel_fod` Phase I with `composed_of: [dk-bruun-3831, dk-numista-420401]`, multi-specimen weight `[14.67g (bruun), 14.75g (numista)]`, dual source citation. Pre-fix: sat in `seed_unsorted` with year 1791, isolated from Numista cluster. — commit `b753e40`.

**Bruun cataloguer copies adjacent KM-number from sister-lot (2026-05-10).**
2-Speciedaler 1663 (Frederik III) `body_excerpt` from `scripts/cache/bruun/lots/part4.json`: «<i>Dav-3547; KM-240; Hede-62A; Sieg-80.1</i>». The actual KM# for the 2-Speciedaler 1663 is **KM-241**; KM-240 is the 1-Speciedaler of the same year. Our parser captured the catalogue's printed text faithfully — the cataloguer at Stack's Bowers cited the 1-Speciedaler's KM number on the 2-Speciedaler lot, likely an «adjacent KM» editorial mistake, OR Bruun used an older Krause edition with different numbering.
*Diagnosis.* Bruun's specimen-level data (weight, grade, mintmaster, photo) is highly reliable. Bruun's catalogue-cross-references (KM#, Hede#, Sieg#) are mostly reliable but **NOT verbatim-authoritative** — cross-check against Numista + Hede before adopting Bruun-quoted catalogue numbers as canonical. Our initial reaction («it's a parser typo / OCR artefact») was a §0b violation — we wrote that as a confident claim before opening the cache file to check. — commit `37f5b6d`.
*Decision.* When Bruun's quoted KM disagrees with Numista AND Hede, trust the latter; record Bruun's verbatim in `note` as a documented divergence.

**Bruun catalogue intros DO NOT contain Plakat-2-December-1782 verbatim quote (2026-05-13).**
SH-references.yml::ref38 was a Stack's Bowers Bruun umbrella ref bundling all 4 PDFs. The only inline citation `<sup>[38]</sup>` (in courantdukatenfuss Phase II prose) backed the «<i>Gold aus der rauen Marck zu 75 Stück bei 21 Karat ausprägen</i>» quote — the verbatim Plakat 1782 wording. Full text search across all 4 cached Bruun PDF page-texts (`scripts/cache/bruun/pages/part*.txt`) returned 0 hits for «Plakat», «Brandon», «75 Stück», «21 carats».
*Diagnosis.* The quote's actual source is danskmoent.dk's «Møntforordninger m.v. under Christian 7.» article (lifted into `german_fuesse-references.yml::ref38`). The SH ref38 was a mis-citation — probably a copy-paste artefact when adding refs to the SH page. Bruun PDFs are auction catalogues with specimen-level descriptions; they don't quote primary-source ordinances from the 1780s.
*Decision.* Repurposed SH ref38 to mirror the danskmoent.dk source; Bruun stays cited inline in per-coin `sources[]` arrays with full part + lot + page detail (which is where Bruun's signal lives). Bibliography-level Bruun umbrella was dead weight (per CLAUDE.md §5a). — commit `91be769`.

**The pdf-viewer MCP doesn't work on the Bruun PDFs (2026-05-10).**
The 4 PDFs are 29-44 MB each. `mcp__pdf-viewer__display_pdf` returns a viewUUID but `interact` calls fail with `Viewer never connected for viewUUID … (no poll within 8s)`. The 8-second poll timeout is too tight for the iframe to finish loading.
*Decision.* Use the `curl → pypdf` pattern documented in §1.3 above (download, extract via `PdfReader`, search by lot number, clean up). Page mapping for the most-cited Karl-Friedrich-Tönning + Christian-V-Glückstadt lots is preserved in §1.3.

**Bruun PDFs live on TWO origins — Part II on danskmoent.dk collapsed under `_collect_sources` url-only dedup (2026-06-02).**
The 4 Bruun catalogue PDFs are hosted per-part on different origins: **Parts I, III, IV** on `stacksbowers.com/wp-content/.../catalogs/*.pdf`, but **Part II** on `danskmoent.dk/pdf/SBG_Mar2025_LEBruunPtII_WebCatalog_LR.pdf`. `merge_seeds_cross_source.py::_collect_sources` deduped sources from `_SINGLE_PAGE_HOSTS` (which includes the `danskmoent.dk` article-page host) by URL alone — so every Part-II lot of a type, sharing the ONE Part-II PDF URL, collapsed to a single citation (first-seen wins). Parts I/III/IV (stacksbowers, NOT a single-page host) were always correctly (url, ref, type)-keyed.
*Symptom.* Surfaced as 6 absorb "enrichment conflicts" where a re-clustered seed's Part-II anchor lot wasn't in the enriched final's sources — looked like §CQ re-clustering churn, but the root was the dedup mis-classification (which also silently dropped same-part Part-II lots at the merger layer project-wide).
*Diagnosis.* Verified host distribution by grepping seed/seed_unified PDF URLs (746 Part-II on danskmoent, 1430 Parts I/III/IV on stacksbowers); confirmed the lost lot lived in seed_unified but not final.
*Fix.* Guard `.pdf` URLs onto the multi-record (url, ref, type) path BEFORE the single-page-host check — host-agnostic, so a future danskmoent mirror of any part is covered. Recovers Part-II citations everywhere (danish_norway 248→281, danish_realm 590). — commit `7abc3f1`.
*Lesson.* A catalogue PDF is ALWAYS multi-record (one file, hundreds of lots, per-lot discriminator in `ref`) regardless of which host serves it. Don't let a host-substring whitelist override that.

### 13.4 Hede catalogue (danskmoent.dk per-coin pages)

**Hede silver-spec card describes a gold off-strike sub-variant inline — risk of wrong-metal weight (2026-05-13).**
Hede c4h47 (Frederik IV «16 Skilling 1713 København») publishes Bruttovægt 5.197 g, Finhed 0.625 (silver), Finvægt 2.247 g. The page's `description` field documents three Zincksamlingen specimens: «1713, Schou 1» (regular silver 16 Skilling), **«1713, Guldafslag, Schou 1a»** (gold off-strike), «1714, Schou 5», … The page text plainly states: «Dobbelte dukater prægedes med stempler til 16- og 12-skillingsmønter» — gold double ducats struck with 16- and 12-skilling dies.
The trap: a curator who reads only the spec card and not the description ingests «Hede 47 = 5.197 g + 0.625 fineness» onto a `metal: gold` entry that's actually the Guldafslag (Schou 1a) sub-variant — copying SILVER specs onto a GOLD coin. Confirmed in Bruun Part I lot 1133 (the gold Schou 1a specimen): weight 6.93 g, «<i>gold planchet struck to a Double Ducat weight standard with the dies customarily used for a 16 Skilling</i>».
*Diagnosis.* Hede's web edition embeds gold-off-strike variants inside the silver type's page when the dies are shared. The spec card is for the silver type only; gold-strike weights follow the Double-Ducat standard (~6.9 g), not the spec-card value.
*Decision.* When a Hede page lists «Guldafslag» / «Sølvafslag» / «cf.» variants in the Zincksamlingen list AND our coin matches one of those (by Schou sub-letter 1a, 1b, etc.), TREAT THE SPEC CARD AS WRONG-METAL — fetch the actual specimen weight from Bruun/IKMK and the canonical-anchor fineness from the relevant Müntzfuß. — commit `b0aa746` (the actual hede-47 case got converted from gold off-strike to silver Hede 47 per user direction; the lesson generalises).

**Hede sub-letter convention = mintmaster/mintmark variants within one type, shared spec (carry-over from research).**
A Hede page like c4h79 publishes ONE Bruttovægt / Finhed / Finvægt set for the entire type, then lists sub-letters A/B/C/D each with their own year-range + mintmark + Schou sub-cluster + Sieg sub-number. The sub-letters share the spec; they differ only by **monetary-officer iconography** (trefoil vs crossed gloves vs crossed clubs, etc.). Krause typically lumps these under one KM# but occasionally splits by year-window (e.g. KM-16.1 covers Hede 79A+B 1603-1613, KM-16.2 covers 79C+D 1618).
*Decision.* Per «one Krause KM = one entry» (Pattern B): fold all sub-letters sharing a Krause# into one curated entry with `catalog.hede: [79A, 79B]`. Case 9 closed by `6d7a087`.

**Per-variant Schou lists in «hhv. … og …» form were silently dropped by the parser (FIXED 2026-06-06).**
Danish per-sub-variant lines write the Schou dies as «Schou **hhv.** 6, 16-29 **og** 16-22» — `hhv.`/`henholdsvis` = «respectively» (one die-set per listed year), `og` = «and». The old `parse_hede._REFS_RE` required a digit *immediately* after the catalogue name, so the `hhv.` word broke the match at the start and the whole Schou set of that variant was lost; the chain separator class `[\-/,]` also didn't include ` og `, so even past `hhv.` the tail after `og` would drop. Simple `Schou 7-10` (no `hhv.`) parsed fine, so the loss was **selective** — e.g. Hede c5h90 A («Schou hhv. 6, 16-29 og 16-22») yielded only Hede+Sieg, no Schou. Scope: **99 by_letter variants across 878 pages** (81 the `hhv./og` form, the rest other formats). *Fix* (`49d4727`): regex skips `(?:hhv\.?|henholdsvis)\s*` after the catalogue name and accepts `\s+og` as a list separator (`_extract_refs` normalises `og`→comma). Re-parse → seed → merge → absorb recovered +85 seed `schou` values, 0 lost, final coin counts unchanged.
*Known-remaining (NOT covered by the fix — separate year-prefixed-Schou notation, 2 coins).* `f6h4` B writes «Schou **1829-37: 2**, 1838: 3» (year-range `:` die-no) and `c6h4` writes «Schou **1731,1** (lille krone), 1731,2 og 1732,3» (Schou year,running-no). The parser captures the leading year (`1829-37`, `1731`) as a Schou token. Pre-existing; left as-is pending a decision on whether the `year,no` form is a legitimate Schou notation (c6h4) or a mis-parse (f6h4).

### 13.5 Bobzin (hagen-bobzin.de)

**Hamburger Bankfuß: «1769 Hamburger 27⅝ / 1777 Altonaer 27¾» conflicts with Soetbeer 1869 (carry-over).**
Bobzin's table at <https://www.hagen-bobzin.de/hobby/muenzverein_wendisch.html> lists the Hamburger Bankfuß and Altonaer Bankfuß as two distinct standards with adoption dates 1769 and 1777 respectively. Soetbeer 1869 (Period-Hauptquelle, in `german_fuesse-references.yml::ref12`, S. 4) documents only ONE Hamburger Bankfuß at 27¾ M.B. / Cöllnische Marck and references no 1777 transition.
*Diagnosis.* Bobzin most likely conflates Hamburg's bid/ask spread (27⅝ M.B. on Ankauf, 27¾ M.B. on Verkauf — both from the 1770 Hamburg Bankreform) with two separate Banco-Füße, and dates the Altona bank's founding to 1777 instead of 1776.
*Decision.* For the 1726 Lübisch-Hamburger 34-Marck-Fuß, Bobzin remains reliable. For the 1769/1777 split, prefer Soetbeer 1869 (period primary source, Hamburg Commerz-Deputation archivist) + Meyers 1888/1907. The «two Bankfüße» rendition does NOT enter our prose. See ref8 caveat in `german_fuesse-references.yml`.

### 13.6 Cross-source: Krause register volumes (KM# inflation)

**Same physical coin can carry two different KM numbers across Krause-volume registers (carry-over).**
Krause-Mishler numbering restarts within each country / region. `KM-25` in the Krause-Denmark volume is an entirely different coin from `KM-25` in the Krause-Schleswig-Holstein volume. The same physical Christian-IV Glückstadt 1640-48 Søsling carries **KM-DK# 25** AND **KM-SH# 87** — same coin, two catalogue numbers from two different Krause editions.
*Decision.* Schema-level support via `KMRef {value, register}` (see `scripts/lib/schema.py`). Locations have a default `km_register` (`'DK'` for denmark.yml, `'SH'` for schleswig_holstein.yml). Render: bare «KM#» when single-entry in the page's default register; qualified «KM-DK#» / «KM-SH#» + tooltip when cross-register or multi-list. Same caveat applies to Hede / Sieg / Lange / Behrens — each catalogue's numbering is internal to that catalogue, and bare-numeric collisions are coincidences unless ruler + nominal + composition + year also align. — see CLAUDE.md §9 caveat «same KM# across different issuers / catalogues is NOT automatically the same type».

### 13.7 NumisMaster (numismaster.com)

**Public catalog data, paywalled price columns (2026-05-16).**
Initial probe of numismaster.com via Chrome MCP suggested entire site was paywall-gated (4× «Subscribe» + 4× «Log in» mentions on the `/coins/coins-10012282` sample page; search-form `Submit` button silently failed without authentication). The `/coins` landing page renders a marketing skeleton with no coin entries. First documented as a negative finding in `docs/research/denmark_pre_1541_source_survey.md` §14.
*Subsequent discovery.* User-supplied `MC_NNNNN` URL pattern (e.g. `https://numismaster.com/MC_66629`) reveals: **per-coin pages render full catalog data publicly** — Country / Catalog # / Political period / Coinage entity / Denomination / Date / Ruler / Mint / Composition / Mass / Fineness / Actual weight / Obverse + Reverse descriptions with Latin legend transcriptions / General Note with Sch# / L# / Fr# / KM# cross-refs. **Only the «Value information in US Dollars» price table is subscription-gated.** Survey doc corrected post-discovery; current §1.4 reflects the actual access split.
*Decision.* Per-coin pages → direct Python urllib with polite ASCII-only User-Agent. Search results → Chrome MCP only (JS-rendered MC_ links don't appear in server-rendered HTML).

**Hub vs leaf vs global-search topology — CORRECTED (Phase 1b, 2026-05-16).**
Earlier session-1 notes (the deprecated «leaf ID = -10012282 HG-Rendsborg» framing) were misled by session-cookie carryover. Phase-1b two-session walk established the actual three-URL-role topology:
- **Geographic-hub URLs** (`/?id=-<facet_id>`) — decorative country-selector pages with «N-th Pattern: A» rows. The «A» letters are visually-styled placeholders with NO JS handler (click test confirmed inert). **NO coin list** — these pages can't enumerate coins by themselves.
- **`/?id=-10012282`** (alias `/coins`) — the **GLOBAL coins-search facet**, NOT a HG-Rendsborg-specific leaf. The «HG-Rendsborg results» that an earlier session saw at this URL came from a session-cookie that already had HG-Rendsborg country-filter active.
- **`/?id=-10012282&advancedsearch=true&pageno=N`** — search-results page after a SEARCH-button submit. Filter state lives in server-side session associated with cookies — NOT URL-encoded.
*Diagnosis trap.* Anonymous urllib probe of any of these URLs returns the rotating 18-featured-coin sample regardless of `keyword=`/`searchstr=`/`country=`/`q=` URL params — those are server-ignored. Likewise an ASP.NET form-POST with `__VIEWSTATE` + `searchstr=schleswig` returns a card for country = KHIVA. **Filtering is JS-sidebar-AJAX only.**
*Decision.* Enumeration goes through the JS-sidebar checkbox state machine via Chrome MCP. Canonical 6-step workflow with JS recipes documented in `docs/HARVEST_GUIDE.md` §«NumisMaster» — JS-clear cookies → Show More → click country checkbox via JS-direct → verify match count → Sort=Date via `dispatchEvent('change')` → paginate `&pageno=N`.

**JS-SPA session-cookie cross-contamination (2026-05-16).**
NumisMaster's session cookies accumulate filter state across walks. The UI «Reset search» link only clears the SUBMITTED filter view — subsequent country selections OR with prior cookie state, inflating result counts. Earlier observations of «562 SH + 1308 DK + 560 Norge = 2430» combined counts were the symptom: not a sub-territory roll-up (as initially hypothesised), but a stale-cookie carryover.
*Diagnosis trap.* A session-2 walk that adds DENMARK on top of leftover SH-cluster filters reports 1870 matches (= DK 1308 + SH 562). Without clearing cookies, every subsequent country filter inherits the accumulator. Two distinct walks intended to be «alone» end up cross-contaminated.
*Decision.* Mandatory JS-console clearance between walks (clear `document.cookie` + `sessionStorage` + `localStorage`, then re-navigate `/coins`). Verified clean state shows the 5-country default list (AACHEN…ABKHAZIA) with NO active filter chips. **Per-card `country_label`** in result HTML is the authoritative disambiguator at parse phase — it self-identifies which filter the card matched regardless of cookie history.

**Sub-territory map for Schleswig-Holstein scope (2026-05-16).**
NumisMaster offers 9 country-filter entries that together cover «всі ці герцогства» for the SH 1514-1864 mission scope:
- `HOLSTEIN-GOTTORP-RENDSBORG` (facet `-1005795`) — 4 entries
- `GLÜCKSTADT` (facet `-1005794`) — 97 entries
- `SCHAUMBURG-PINNEBERG` — ~167 entries (Holstein-Schauenburg cadet)
- `SCHLESWIG-HOLSTEIN-GLUCKSBURG` — 4 entries
- `SCHLESWIG-HOLSTEIN-GOTTORP` (facet `-1006246`) — 176 entries
- `SCHLESWIG-HOLSTEIN-NORBURG` — 4 entries
- `SCHLESWIG-HOLSTEIN-PLOEN` (facet `-1006248`) — 20 entries
- `SCHLESWIG-HOLSTEIN-SONDERBURG` (facet `-1006249`) — 25 entries
- `SCHLESWIG-HOLSTEIN` (main) — 65 entries

Cadet lines NOT separately filterable (rolled up under the above): HOLSTEIN-PLON → SCHLESWIG-HOLSTEIN-PLOEN; HOLSTEIN-SCHAUENBURG → SCHAUMBURG-PINNEBERG; HOLSTEIN-SONDERBURG-PLON/-BECK → SCHLESWIG-HOLSTEIN-SONDERBURG; LÜBECK-BISHOPRIC-IN-HG-FAMILY → no separate entry. Total accumulated: **562 entries / 23 pages**.

**Sweden negative finding for Christian II Kalmar Union (2026-05-16).**
A clean SWEDEN-only walk with Sort=Date ascending confirmed the catalog jumps from MB# 9001 (Johan III 2 Öre 1573, single isolated entry) straight to KM# 1+ (Karl IX 1601+). **ZERO entries for Christian II era 1514-1523.** Krause numbering for Sweden begins ~1601; pre-Krause MB# coverage is essentially nil. The mission-scope sub-scope D «Sweden under Danish rule 1514-1523» is closed with 0 in-mission entries — route through Bruun PDFs (§1.3, Part I has 13 Christian II lots), Numista (§1.1), Schive 1865 (Norway-side cross-attestation), and direct museum catalogs.

**Pre-Krause numbering schemes seen on NumisMaster pages (2026-05-16 confirmation).**
KM (Krause-Mishler) numbering for Denmark begins ~1604 (Christian IV reign), for Norway ~1608, for Sweden ~1601. Pre-Krause coins are catalogued under:
- **MB# (Madai-Bach)** — Schleswig-Holstein duchy 16th-17th c. (e.g. MB# 33 Christian III 6 Pfennig 1534-1554, MC_167727; MB# 22 Witten Frederik I 1516)
- **FR# (Friedberg)** — gold coins, especially Portugaloser (e.g. FR# 32 DK Guilder 1591, FR# 62.1 Portugaloser 1591)
- **C# (Christensen)** — rare; seen on SCHLESWIG-HOLSTEIN-PLOEN C# 25 Ducat 1760
- **KM# Pn*** / **KM# Tn*** — pattern strikes / token notgeld (exclude per CLAUDE.md §9.1 / §9.2 at parse phase)
- **KM# A###** / **B###** / **C###** — variant suffixes for sub-types (e.g. A40.3 = variant of KM# 40)

*Decision.* When parsing NumisMaster `Catalog #:` field, branch on prefix: `KM#` → `catalog.km`; `MB#` → `catalog.mb`; `FR#` → `catalog.friedberg`; `C#` → `catalog.christensen`. Schema-level support via the seed builder. Pre-Krause SH coins default to `issuing_entity: schleswig_holstein_duchy` based on the «Political period: Duchy» Librios PL-code.

**`numismaster.com` URL pattern alphabet (final).**
- `/MC_<N>` — public per-coin page, full data (urllib OK)
- `/?id=-<facet>` — geographic-hub decorative page (no coin list)
- `/?id=-10012282` (alias `/coins`) — global coins-search facet (sidebar JS-filter)
- `/?id=-10012282&advancedsearch=true&pageno=<N>` — post-SEARCH paginated results (cookie-bound filter)
- `/coins/coins-<N>` — redirects back to `/coins` (legacy/dead URL pattern, ignore)
- `/api/...` — does not exist (no public API)
- `/sitemap.xml` — 404, no public sitemap

### 13.8 IKMK Berlin (ikmk.smb.museum)

**Discovery noise — full-text `quick_search` + year-only fetch filter let the cache fill with ~90 % out-of-scope records (2026-05-29).**
`scripts/fetch_ikmk.py` discovers ids via `quick_search_value=<query>` — a **full-text** search, so a query like «Hamburg» matches any record mentioning Hamburg anywhere (auction house, collector, find-spot), and «Kassel» pulls Napoleonic Westphalia (capital Kassel). The at-fetch scope gate `_is_in_mission_scope` filters **by year only**, so any record whose year falls in 1514-1914 passes regardless of issuer or object type. Net effect measured on the cache: of 7259 cached records only **1468** were German/Scandinavian coins; **5791** were out of scope — 4818 other-country coins (Turkey 2085, Greece 655, Iraq 521, Italy 399, Iran 269, …, mostly ancient/oriental), 710 exonumia, 263 None-country oriental (Abbasiden/Umayyaden/Sasaniden).
*Classification signals (the museum's own typology — authoritative, not heuristic).* `mint[].country_name_en` + `region_name` for issuer; `item.item_en` («Coin» vs «Medal»/«Minting Tools»/«Model»/«Tokens and Labels»/«Paper Money»/«Seal»/…) + `division.division_name_en` («Antiquity»/«Medieval Period»/«Modern Period»/«Medals») for object type.
*Geocoding trap.* IKMK tags `mint.country` by **modern** geography, so historical German/HRE territories surface under foreign flags: Silesia (Liegnitz und Brieg, Glogau) + Pomerania (Pommern-Stettin, Cammin, Rügenwalde) + Posen → `Poland`; Neuchâtel (Neuenburg, a Prussian principality 1707-1857) → `Switzerland`; Bohemia + Friedland/Sagan → `Czech Republic`; Steiermark/Tirol/Salzburg → `Austria`. A naïve «country ≠ Germany» drop loses real German-lands material — keep the borderline {PL, CH, CZ, AT, NL, BE, LU} set.
*«Token» ≠ small-change coin.* Circulating copper Pfennige are `item==Coin` in IKMK and stay in scope; the «Tokens and Labels» class is reserved for genuine non-money — Rechenpfennige (abacus counters), Münzmeisterjetons, Brot-/Bier-/Armen-/Gefängnis-marken. Don't equate the «-pfennig» in «Rechenpfennig» with a denomination.
*Scope-purge done 2026-05-29* (submodule commit `07014b3`). Keep-rule: `item==Coin` AND country ∈ {Germany, DK, NO, SE, IS, FI} ∪ borderline-HRE {PL, CH, CZ, AT, NL, BE, LU} ∪ None-country-with-German/Scandinavian-title; all exonumia dropped; Danish-colonial (Tranquebar/Vestindien/Guinea) rescued. Cache 103 MB → 28 MB. Dropped ids + reasons in `scripts/cache/ikmk/_oos_purged_by_scope_2026-05.json`; all 5791 added to manifest `oos_excluded_mds_ids` so the harvest routine will not re-fetch them. Deleted files recoverable via the submodule's history.
*Durable filter — landed 2026-05-29.* `fetch_ikmk.py` now gates fetch + `scan_cache` on `_is_in_entity_scope` (country + object-type), and the old year-only `_is_in_mission_scope` gate is removed. Keep-rule mirrors the purge: keep `item==Coin` of German lands + Scandinavia + borderline-HRE (+ Danish-colonial title rescue), drop other-country coins and all exonumia. **Year is NOT a drop criterion** — per the curator's multi-level scope (2026-05-29), the broad keep-scope is German/Scandinavian (and territories under their rule) in ANY era; pre-1514 / post-1914 records are future-useful context and must not be dropped. The active harvest concentration (1480-1914) governs which discovery buckets are prioritised, not what is rejected on fetch. `_record_oos` now logs a `reason` (`exonumia:…` / `other-country:…` / `none-oriental`) per excluded id.

### 13.9 danskmoent.dk Galster pages — single-coin pages disguised as denomination overviews (2026-06-10)

**Some `<denom>.htm` pages named like overviews are actually single-coin pages — the classifier was silently skipping them.**
`scripts/lib/galster_parsers/classify.py` rule 3 routes every page whose filename isn't a per-coin signature (`chr_`/`fr_`/`norge_`/`hansg`/`gotlg`) to the `reign_index` skip-parser, on the assumption that a bare `<denom>.htm` (`1nobel.htm`, `1daler.htm`, …) is a redundant table-of-contents whose coins each have their own page. True for most — but a denomination with **exactly one catalogued type** never got a dedicated per-coin page, so its `<denom>.htm` IS the coin page. Confirmed cases: **`2nobel.htm`** (Hans 2 Nobel 1502, Galster 26), **`3nobel.htm`** (Hans 3 Nobel 1496, Galster 25), **`6penning.htm`** (Erik af Pommern, Åbo), **`halvrhin.htm`** (Hans ½ Rhinsk gylden). These were skipped → never seeded → their danskmoent source never reached the coins (surfaced when the user noticed the 2/3 Nobel danskmoent link had «disappeared» — it was never actually attached).
*Fix (2026-06-10).* Conservative content carve-out in rule 3: a page routes to `standard` (not skip) when it has a ruler-keyword H1 (`## Hans, 2 Nobel 1502`), exactly ONE distinct Galster number, and none of the overview markers («Se også» / «ser således ud» / «Møntrækken» / a reign-range group header `Hans (1483-1513)`). Genuine overviews trip ≥1 guard. Dry-run over all 171 reign_index pages flipped exactly the 4 above; 167 untouched.
*Related gotcha.* The standard parser's year regex was `1[5-6]\d{2}` (1500-1699) — it dropped Hans-era 14xx years (3nobel's 1496), leaving an undated entry the seed builder then discarded for lack of a reign-volume anchor. Extended to `1[4-6]\d{2}` (standard.py + build_galster_denmark_seed.py). The galster number on these pages lives in the parsed `catalog_refs`, NOT the filename, so `coin_id` / `_build_sources` fall back to `catalog_refs.galster`.
*Forgery-year parentheticals (2026-06-10 follow-up).* danskmoent.dk writes «(YYYY er falsk)» when a year's only surviving specimens are forgeries — there was no genuine striking. The year regex grabbed those too (Hans 1 Nobel fr_hg24: «1496, 1502, (1508 er falsk)» → counted 1508 as legitimate). `_FORGERY_YEAR_PAREN_RE` in standard.py now strips a parenthetical containing BOTH a year AND `falsk*` before year extraction. Cache-wide scan: the only matching form is `(1508 er falsk)`, so exactly fr_hg24 re-parses to 1496, 1502; 0 other pages affected. NOTE: errata was the WRONG tool here — the source is correct («er falsk» is explicit), it was our parser that mis-read it; `_source_errata` is for catalogue-INDEX corrections, not year fields.

### 13.10 KMK (KMM Copenhagen) `typeNumber` — inconsistent + occasionally malformed catalogue strings (2026-06-24)

**KMM's `typeNumber` is curator free-text, not a normalised index.** The same Galster sub-variant appears in several spellings («G 57b», «G. 57B», «Galster 57b») and the field is occasionally malformed. Two malformed forms found on København 1524 Frederik I Søsling (all = Galster 57, which Galster 1972 split into 57A/57B groups — danskmoent `fr/f1g57.htm`): **«Galster 5 + B»** (309770; parser extracted bare `5`) and **«G. 567B»** (311330/311331; stray digit → `567B`). Both `f1g5.htm` and `f1g567.htm` are danskmoent **404** → the strings are mis-prints of `57B`.
*Consequences.* (a) The mixed case caused artificial bucket splits in §9a thinning once `galster` was added to `_subvariant_key` (57b vs 57B = two buckets). (b) The malformed `5`/`567B` looked like distinct Galster types.
*Fix (2026-06-24, curator-approved).* In `build_kmk_seed._catalog`: canonicalise galster sub-variant letter to UPPERCASE (scoped to galster — Hede/Lange/Schou sub-variant case is NOT uniformly uppercase in KMM, left as-is) + a builder-level `_KMM_GALSTER_ERRATA` map ({id: correct}) for the 3 malformed records → `57B`. Errata lives in the BUILDER, not a data-level `_source_errata` block, because these records thin into the 57B bucket and an entry-level carrier would not survive the next rebuild-from-cache (contrast §13.9: there errata was the WRONG tool because the *source* was right; here the source IS wrong, a catalogue-index mis-print → errata is correct).
*Related root cause.* The §9a thinning bucket key omitted `galster` entirely (a type-identity register like km/hede/sieg/schou) — distinct Galster types shared one bucket and collapsed. Added `galster` (+`lange` for thin_kmk_seed) to `_subvariant_key` in both `lib/seed_thin.py` and `thin_kmk_seed.py`. kmk seed 13819→14003 (+184 distinct types recovered).
*Latent (not fixed):* `unified-dk-galster-hg-238` (Hans) carries «Lagerqvist 9a-f» in its `catalog.galster` field — a Lagerqvist reference misfiled into the galster register.

### 13.11 danskmoent.dk Galster (`standard` shape) — catalogue parenthetical on a SEPARATE line is dropped → empty `catalog_refs` (2026-07-14)

**When the `(Galster N, Schou X, Sieg Y; …)` line sits on its OWN line — after the `Forside: … bagside: …` sentence AND a blank line — the standard parser never extracts it, so `catalog_refs` comes out empty (only the filename-derived Galster number survives).** Confirmed on `chr_c3g131.htm` (Christian III, 1 Rhinsk gylden 1536, Roskilde): `raw_text_excerpt` plainly holds «(Galster 131, Schou 1-7, Sieg 23; Reinhold Junge s. XX,18)», yet the parsed `catalog_refs` is `{}`.
*Root cause (verified, not hypothesised).* `scripts/lib/galster_parsers/standard.py::_parse_description_and_refs` scopes ref-extraction to the `Forside:` block only: `re.search(r"Forside:\s*(.*?)(?:\n\n|<HR>)", text, re.DOTALL)` with a NON-greedy `(.*?)`. On this page the block is «Forside: portræt, bagside: våbenskjolde.» followed by a blank line (`\n\n`), so the capture terminates at that blank line — BEFORE the standalone catalogue parenthetical. The `for pm in re.finditer(r"\(([^)]+)\)", desc)` loop then sees no parenthetical → no Schou/Sieg captured. Any `standard`-shape page whose catalogue line is a detached line has the same gap.
*Consequence.* The authoritative danskmoent Schou (and Sieg) range never reaches the galster seed. For c3g131 that left the coin (final `unified-dk-bruun-14770`, Roskilde 1536 Goldgulden) with `schou` sourced only from Bruun (specimen «Schou 4») + NumisMaster (spurious «Sch#1351 for no date issue» — out of range for Christian III, whose Schou runs per-regent ~1-77), instead of the type range **Schou 1-7** the page states.
*Interim fix (2026-07-14, this session).* Surgical, NOT a parser fix: hand-added `schou: 1-7` + `sieg: '23'` to the galster seed `dk-galster-c3g-131`; dropped the spurious `schou: '1351'` from numismaster seed `schleswig_holstein-numismaster-167746`; set `schou: 1-7` on the seed_unified member + final foundation `unified-dk-bruun-14770` (+ a `_curation_holds: {catalog}` note — NB the catalog hold does NOT survive absorb's main enrich re-derive, only the hygiene-fold; durability here comes from BOTH the foundation and its seed_unified member carrying `1-7`, which absorb unions to a clean `1-7`). These hand edits survive a source re-seed: both builders write through `write_v2_seed` → `lib.seed_merge.merge_seed`, which preserves `CURATED_FIELDS`, `_curation_holds` and `_source_errata`. (Corrected 2026-09-12 — this note previously called galster / numismaster «wholesale-write seeds» whose re-seed reverts hand edits; neither half was true.) A full MERGER re-run is otherwise SAFE for schou: `_deep_merge_catalog` unions Bruun's faithful specimen «Schou 4» with galster «1-7» → `['1-7', '4']`, but the very next line (`merge_seeds_cross_source.py:3350`) runs `_fold_catalog_indices` → `catalog_codes.normalise_numeric_index`, and since `schou ∈ _NUMERIC_INDEX_FIELDS` the plain `4` (∈ plain range `1-7`) is subsumed → clean `1-7`. The same subsumption runs at absorb (`_normalise_catalog`, `absorb_…:1485`) and render (`compute.py:663`), so `1-7` is stable end-to-end. (Corrected 2026-07-14 — an earlier draft of this note claimed «the merger has no schou-range-subsumption», which is FALSE; the rule already existed.)
*Proper root fix (DONE 2026-07-14 — commits `d3cb920` parser + `8d77786` cleaner + `67bdb7a9` cache + seed).* The naive «widen the `Forside:` capture to the first `<HR>`» idea was tested across ALL 118 standard pages and REJECTED: the widened region also holds prose / literature / neighbour parens («(Galster 30)» a neighbour, «(Galster: Unionstidens Udmøntninger side 59)» a book) that clobber the real value via the extractor's last-paren-wins overwrite — ~10 currently-correct pages regress. Instead `_parse_description_and_refs` now ANCHORS on the page's own Galster number (derived from the filename via the new `_galster_number_from_filename`) and is two-tier, legacy-first:
  - **Tier 1** — the legacy `Forside:`-narrow scan, byte-identical to before. Keeps every already-correct page unchanged, including multi-variant summary pages like `fr_f1g66` whose type paren «(Galster 66A-B)» sits in the Forside line (its per-variant «(Galster 66A, Schou …)» parens are NOT promoted — that Schou-union is a separate, still-deferred «accumulate» case).
  - **Tier 2** — fires ONLY when Tier 1 is empty (exactly the old-empty pages): `_find_canonical_index_paren` picks the pre-`<HR>` paren that names the page's Galster number AND carries the most catalogue keywords, so prose / neighbour parens can't clobber. Anchor matches the numeric base with optional letter suffix («Galster 92» in «92AB») but not an unrelated neighbour («125» ≠ 120).

  Migration gate (`tests/test_galster_canonical_paren.py` + a full-corpus diff of the new parser vs the committed cache): **unchanged 84, recovered 34, changed 0, LOST 0** — zero regressions. Re-parse (`parse_galster.py --force`) + re-seed recovered 29 Schou + 20 Sieg values across danish_realm / danish_norway / gottorp_duchy / royal_holstein; `_clean_catalogue_refs` reroutes bundled foreign refs (Hauberg → `others` on `gotlg146`) and drops abbreviated prose («mgl. hos» on `fr_f1g123`, via the extended `_PROSE_NOISE_RE`). c3g131 now derives Schou 1-7 + Sieg 23 natively, superseding the interim hand-edit above. (No merger rule is needed for the Bruun-«4»/galster-«1-7» union — the existing `normalise_numeric_index` subsumption already collapses it; see the interim-fix note above.)

  *Propagation status.* The rollout committed the SEED layer only; `seed_unified` / `final` were NOT re-derived because a full merger+absorb re-run currently carries unrelated pending cross-session reconciliation. The recovered refs are banked in the source layer and reach the finals of absorbed galster coins at the next deliberate coordinated re-flow. Still-deferred: the multi-variant Schou-**union** «accumulate» case (`fr_f1g66` / `fr_f1g73` / `fr_f1g63` — Schou split across several per-variant parens; Tier 1/2 keep only the summary or first paren, never the union).

### 13.12 Sieg — TWO numbering systems for Christian VII, and a derived source chain (2026-07-30)

**A bare «Sieg N» for a Christian VII coin is ambiguous: Sieg's 2001 catalogues renumbered that whole reign, and our two suppliers of Sieg numbers sit on opposite sides of the change.** danskmoent's Hede pages cite the PRE-2001 numbering; Stack's Bowers' Bruun catalogue cites the POST-2001 numbering. The renumbering is not an offset — it is a permutation: old 1-6 move to the new 30s while old 7 onward shifts down to 1, and old 5 / old 6 swap places (old 5 → new 35, old 6 → new 34).

*Concordance source.* danskmoent publishes the mapping in both directions at [konkord.htm#c7](https://www.danskmoent.dk/konkord.htm#c7), compiled by *Dansk Mønt* itself: «I Siegs kataloger 2001 er nummereringen af Christian 7.s mønter ændret». Harvested by `scripts/fetch_danskmoent_konkordans.py` → `scripts/cache/danskmoent/konkordans/konkord.{htm,json}` (57 old ↔ 57 new numbers; the parser checks the two printed tables are mutual inverses — they are). The same page also carries a Hauberg / Mansfeld-Büllner concordance for 1241-1375, outside our 1514 lower bound and consumed by nothing.

*Verified against our own data, not assumed.* For every Christian VII coin where a danskmoent-sourced and a Bruun-sourced Sieg number meet on the same Hede number in the Danish volume (n = **25**), `Bruun = table(danskmoent) + 1`, with **zero** exceptions. The decisive evidence that the table is the actual mechanism rather than arithmetic coincidence is the swap surviving: danskmoent 5 → Hede 8 → Bruun 36, while danskmoent 6 → Hede 7 → Bruun 35 — a plain offset can never send a larger input to a smaller output.

*The +1 residual is UNEXPLAINED.* Candidate readings, none verified: Bruun cites a later Sieg printing than the 2001 edition the Dansk Mønt table was compiled against; or one type was inserted at the head of the reign after compilation; or the table itself is off by one. Do NOT write the mapping into `catalog.sieg` as an erratum on this basis — the residual means we cannot yet convert one numbering to the other reliably, only recognise that two systems are in play.

*Consequence for §9.4 index-graph merges.* Two Sieg numbers differing by ~30 on Christian VII coins are **not** evidence of distinct types; they are the same type in two numbering systems. Conversely, two Christian VII coins agreeing on a bare Sieg number may be different types. Until the residual is resolved, **do not use Sieg as the load-bearing catalogue key for Christian VII** — this is exactly why the Rethwisch 1769 merges (`baa1cb8`) had to rest on Hede + concordant Schou, with the Sieg divergence recorded as unusable. Prefer Hede or Schou; where Sieg must be cited, record the edition (`sieg_hede1971` and friends exist for this).

*The wider point — Sieg → Hede → Schou is a DERIVED chain, not three independent witnesses.* Schou (1926) is chronological and enumerates die variants; Hede's systematics (mint / metal / series) rest substantially on Schou; Sieg groups by regent and nominal and uses Hede as its principal source. So **agreement between Sieg and Hede is not independent corroboration** — it can be one reading propagated twice. A §9.4 unifying edge contributed by a derived catalogue is weaker than the same edge from the catalogue it derives from, and an error in the middle link travels downstream (danskmoent documents exactly this: a Sieg editor working only from Hede's 2nd/3rd edition marked a Schou-attested Oldenburg type «hitherto unknown» and catalogued one ⅙ Thaler twice). Edition matters too: Hede has 1964 / 1971 / 1978 printings with changed numbering, so «Hede 4A» without an edition is strictly incomplete.

### 13.13 NGC World Coin Price Guide (ngccoin.com) — access + taxonomy quirks (2026-08-07)

**(a) `LUBECK` and `LÜBECK` are TWO SEPARATE regions with different contents.**
The `GERMAN STATES` region list carries both spellings as distinct filter values:
`LÜBECK` → 772 date-rows, `LUBECK` → 179. They are NOT aliases and NOT a superset /
subset — a harvest that takes only one silently loses the other. The same
umlaut-doubling appears elsewhere in the 441-region list (`LUNEBURG`/`LÜNEBURG`,
`BRUNSWICK-WOLFENBUTTEL`/`-WOLFENBÜTTEL`, `BRUNSWICK-LUNEBURG-CELLE`/`-LÜNEBURG-CELLE`),
so **treat every umlaut-bearing region name as a pair and walk both variants**.
Cost of missing it: ~19 % of Lübeck rows, silently.

**(a2) A region's `_listing_raw.json` duid count is NOT a row-completeness metric —
do not audit the harvest against it (2026-08-25).** The obvious check «listing says
this cuid has N duids, the parsed record has M date rows, so N−M rows are missing»
is wrong, and it manufactures a large, convincing, entirely fictional gap: run over
the Danish scope it reported 756 missing in-scope rows across 311 types. Verified
against the live site instead: cuid 1051684 is listed with 3 duids and its detail
page renders exactly ONE row («1645(q)») — and renders that same single row when
fetched at duid 1239857 and at duid 1239858 alike, i.e. **the duid in the URL does
not select or change anything**. cuid 1051500 is listed with 5 duids and both the
page and our cache hold 4 rows (1702IW / 1703IW / 1704IW / «1704IW Error FRID VI»).
The detail page is the authority for what rows a type has; the listing's `d` array
is a search-result artefact that does not map one-to-one onto them. This is the
same fact as (b) seen from the other side — one fetch per cuid is sufficient — so
audit completeness on **cuids covered**, never on duids.

**(a3) `DENMARK` has exactly two sub-regions and both are already covered by the
«All Regions» walk.** The taxonomy lists `GLÜCKSTADT` (97 types) and
`HOLSTEIN-GOTTORP-RENDSBORG` (4); `NORWAY` has none. All 101 cuids are present in
the `denmark` cache tree — the two sub-region directories hold a `_listing_raw.json`
from the 2026-08-09 pager walk and nothing else, which reads like an unfinished
harvest but is not one. `fetch_ngc.py status` reporting `types 0 / cached 0` for
them is that un-ingested listing, not a shortfall.

**(b) Listing rows are date-variants, not types — ~5.4:1.** Each row is a `duid`
(one date of one type); the type is the `cuid`. A Lübeck sample of 200 rows held only
37 distinct `cuid`s; the full 772-row walk yielded 265 types. Sizing a fetch job off
row counts overestimates by roughly 5×. Dedupe on `cuid` **before** fetching detail
pages — the detail page renders the whole date table for its type, so one fetch per
`cuid` is sufficient and per-`duid` fetching is pure waste.

**(c) Cloudflare blocks every non-browser client; in-page `fetch()` is the way.**
`curl` with a complete browser header set (UA, `Accept-Language`, `Sec-Fetch-*`,
`sec-ch-ua`, `Upgrade-Insecure-Requests`) still gets `403` + the «Just a moment…»
JS-challenge shell; WebFetch the same. A same-origin `fetch(url, {credentials:'include'})`
executed inside an already-cleared browser tab returns 200 and full HTML. No
re-challenge or throttling was observed across a 31-page listing walk plus 25 detail
fetches in one session. Do **not** budget time trying to defeat the challenge from
Python — drive the browser instead.

**(c2) Playwright does NOT work — tested exhaustively 2026-08-07, do not retry.**
Before adding `playwright` as a project dependency it was probed in a throwaway venv
across **seven** configurations. **All seven were blocked** by the Cloudflare
JS challenge (`BLOCK(cf-challenge)`, 0 rows, ~27-51 s each):

| # | Configuration | Result |
|---|---|---|
| 1 | bundled Chromium, headless | BLOCK |
| 2 | bundled Chromium, headless + `--disable-blink-features=AutomationControlled` + `navigator.webdriver`/`plugins`/`languages` init-script | BLOCK |
| 3 | bundled Chromium, **headed** | BLOCK |
| 4 | bundled Chromium, headed + stealth | BLOCK |
| 5 | `channel="chrome"` (the real Google Chrome binary), headless | BLOCK |
| 6 | `channel="chrome"`, **headed** | BLOCK |
| 7 | `launch_persistent_context` + `channel="chrome"`, headed, **two consecutive runs** on a warm on-disk profile | BLOCK both runs |

Config 3/4/6 genuinely used a full headed browser (`chromium-1223` was present
alongside `chromium_headless_shell-1223`, verified — not a silent headless fallback).
**Control test run at the same moment:** an in-page `fetch()` in the ordinary browser
tab returned `200` with 25 rows and no challenge. So the discriminator is
**automation/CDP detection, not a site-wide lockdown** — Cloudflare fingerprints the
Playwright-driven browser regardless of binary, headed-ness, stealth patches, or a
persisted profile. Stealth-plugin escalation was not pursued: it is an arms race with
no stable endpoint and no place in a scholarly pipeline.

**Consequence: there is no Python-driven fetcher for this source, at all.** Not
urllib, not requests, not Playwright. The only working route is the ordinary
browser session (Browser pane / Chrome MCP) driving in-page `fetch()`.

**(c3) The `catalogNumber` search filter returns FALSE NEGATIVES — never use it
to prove a coin is absent.** `?catalogInitials=KM&catalogNumber=<N>` finds
`KM 60.2` but returns **zero** hits for `KM 147` and `KM 616.6`, both of which
are demonstrably present in NGC and sit in our own harvested Denmark set. The
match appears to be an exact-string comparison against a differently-normalised
field. A 0-result therefore means nothing. To establish absence, walk the
region listing (which is complete: DENMARK returned exactly 25 rows on each of
123 pages = 3075, with page 124 empty) and check the harvested set.

**(c4) A KM# «missing» versus another source is almost always renumbering or
sub-variant granularity, not a gap.** Cross-checking NGC's Denmark against our
frozen NumisMaster cache showed 20 KM numbers present only in NumisMaster.
Nineteen were not gaps: **11** are recorded in NGC's own `Previous KM#` trail
(`KM 42` → `32.4`, `KM 203` → `194.2b`, `KM A193` → `192.2`), and **8** are base
numbers NGC has split into sub-variants (`KM 616` → `616.1`…`616.8`, `KM 340` →
`340.1`/`340.2`). Exactly **one** (`KM 755`, Rigsbankskilling 1852) is genuinely
absent. This is §9.4 in the wild — differing enumeration granularity between
catalogues is not evidence of distinct types, and NGC's renumbering trail is
what makes the difference legible. Check `previous_km` and sibling sub-variants
BEFORE calling anything a coverage gap.

**(c5) A DENOMINATION in the slug can masquerade as a year — read years only
after the catalogue number.** The slug shape is
`<country>-<denomination>-<catalogue>-<years>`, so a whole-slug year regex reads
`norway-1500-kroner-km-452-1993` as attesting **1500**. That drags eleven modern
Norwegian commemoratives (1992–2005) through a 1480–1814 filter, because each
one «starts» in 1500. Take the substring after the last `-km-`/`-mb-`/`-fr-`/`-c-`
segment; `fetch_ngc.py::years_from_slug()` does this. Cross-checked across every
walked scope: **Norway is the only one affected** (11 types); Denmark (1451) and
all eight Schleswig-Holstein regions came out identical either way, so no earlier
harvest needed redoing. Danish `1000`/`3000 Kroner` escape by luck — they fall
outside the `1[3-9]\d{2}` year pattern, and `1500 Kroner` does not.

**(c6) NORWAY is its own COUNTRY, not a DENMARK region.** Walking DENMARK/All
Regions yields zero Norwegian coins (verified: 0 of 1105 harvested Danish records
mention Norway). Norway must be walked as `country=NORWAY`, which has exactly one
region, `All Regions` — 597 types over 88 pages. Its catalogue floor is **1608**,
matching the NumisMaster finding in §1.4, so nothing exists there for the
1480–1608 stretch of the mission window.

**(d) The pager is postback-only, but the page URL is not.** The `1 2 3 … 123 Next`
control is an ASP.NET `__doPostBack` widget with no usable `href`. Ignore it:
`/price-guide/world/search/<N>/?…` works as a direct GET for any `N`. Terminate the
loop when a page yields **0** `cuid-…-duid-…` matches rather than trying to parse a
total-count or last-page number — neither is exposed in a stable place.

**(e) `/sitemap.xml` is a decoy for world coins.** It exists (200, valid
`sitemapindex`) and lists three price-guide sitemaps of ~120 885 URLs — all **United
States**. The only `/price-guide/world/` URL in any of them is the landing page.
Don't plan an enumeration around it.

**(f) The JSON endpoint is typeahead, not data.**
`/resources/services/coin-search/price-guide/world/search/?keywords=<q>` is real JSON
but returns only `CoinDescription` + `URL`. `?keywords=&country=DENMARK` returns `[]` —
it keys on the free-text `keywords` param alone and ignores structured filters. No
per-coin JSON endpoint exists; every `…/{coin,detail,regions,denominations,countries}/`
variant 404s to the SPA shell. A 404 here returns **HTTP 404 with an HTML body**, so a
probe script must check `content-type`, not just status.

**(g) Fineness/weight are absent on most small silver.** 28 % fill on a stratified
25-page Lübeck sample (present on large silver such as the DK 2 Krone at 0.8590 /
37.819 g, absent on Dreiling/Sechsling-class pieces). Plan seeds so those coins land
with `fineness_verified: false` and no fabricated canonical value — the §4 rules apply
unchanged. Do not infer the metrology from the composition string.

### 13.14 natmus.dk — the public ES endpoint is gone for good; the web object page is the surviving route (2026-08-29)

**`https://api.natmus.dk/search/public/raw` is dead, and the failure has
deteriorated since it was first recorded.** `docs/TODO.md` §DB logged HTTP 403
«Site Disabled» on 2026-07-19. Re-probed live 2026-08-29:

- **TLS now fails before HTTP.** The certificate `CN=api.natmus.dk`
  (DigiCert / GeoTrust TLS RSA CA G1) is valid `Feb 24 2026 – Aug 24 2026` — it
  **expired five days before the probe** and was not renewed. A plain `curl` /
  `urllib` request aborts at the handshake, so a caller sees a TLS error, not an
  HTTP status, and a probe that only inspects status codes reports nothing at all.
- **Ignoring the certificate, the service answers HTTP 403** with
  `<title>Web App - Unavailable</title>` — the Azure App Service is switched off,
  not rate-limiting and not misconfigured.
- **DNS still resolves** (`api.natmus.dk` → `nm-natreg-api-wa-prod.azurewebsites.net`
  → Azure West Europe, `52.178.114.226`), so name resolution is not a usable
  liveness signal here.

A lapsed certificate on top of a disabled app service is the signature of a host
nobody is maintaining. **Treat the ES route as permanently gone — not as an outage
to wait out.** `scripts/fetch_kmk.py` (both its `discover` and `fetch` phases) can
no longer harvest or refresh anything; it is kept only as the record of how the
43 033-object cache in `scripts/cache/kmk/` was built.

**The surviving route is the web object page.**
`https://samlinger.natmus.dk/KMM/object/<id>` returns HTTP 200, `text/html`,
~17–46 KB, **server-rendered** — the object record is already in the markup, so
plain fetching works and no browser automation is needed. `Accept: application/json`
does **not** switch it to JSON (still `text/html`); no JSON route has been found.
The page embeds the museum's own structured record as HTML-escaped JSON in its
«Rådata» section (Danish-keyed: `beskrivelser` / `klassifikationer` / `maalinger` /
`haendelser` / `materialer` / `identifikation`), which is strictly richer than the
visible `<div id="description">`. `scripts/fetch_kmk_web.py::parse_raadata` extracts
it; sidecars land at `scripts/cache/kmk/web/<id>.json`.

**Enumeration is the part that did NOT survive** — *partially resolved
2026-09-04, see below.* The ES `nation.keyword` aggregation that produced
`scripts/cache/kmk/_manifest.json` has no live backing endpoint, and the object
route is per-id only.

**UPDATE 2026-09-04 — the SPA's own search IS reachable, and it is a plain URL.**
The recon this note asked for was done from a browser: the front page's
«Museumsgenstande» tile points at `/objectbrowse`, and that view takes a
`keyword` query parameter:

```
https://samlinger.natmus.dk/objectbrowse?keyword=<term>
https://samlinger.natmus.dk/objectbrowse?keyword=<term1>,<term2>     # AND
```

Two syntax rules, both learned the hard way and neither documented:

- **Terms are ANDed with a COMMA.** `?keyword=Holsten-Gottorp,guld` → 12 objects.
- **A SPACE does not mean AND — it kills the query.** `?keyword=Gottorp 1619`,
  `?keyword=gylden Gottorp` and `?keyword=guldgylden Gottorp` all return **0**,
  including combinations that demonstrably exist. A hyphenated token
  (`Holsten-Gottorp`) is fine; a space-separated phrase is not. A zero here is
  therefore **not evidence of absence** — retry with commas before concluding
  anything.

Result links are `/kmm/object/<id>`, so a result page yields ids directly
(`document.querySelectorAll('a')` filtered on `/object/\d+/`). The result count
renders as «N genstande». Note the path casing differs between the two routes:
browse links emit lowercase `/kmm/object/<id>` while our stored citations use
`/KMM/object/<id>`; both resolve.

This gives back a **usable enumeration surface** for targeted lookups (not yet a
bulk-harvest one — no page-size parameter has been probed). Worked example that
motivated the recon: `?keyword=Holsten-Gottorp,guld` returns exactly 12 objects,
and all 12 are already in `scripts/cache/kmk/` — which is how we established
that a specific Gottorp gold coin (the unique 1619 guldgylden, Jensen 2002
p. 39, acquired 1998) is **not published online at all**, rather than merely
missing from our cache.

**Also confirmed 2026-09-04:** the object route now answers plain `curl` with
HTTP 200 (no browser needed), while `api.natmus.dk` still times out at the TLS
handshake. The split recorded above is stable.

**Politeness.** No auth, no documented rate limit. Serial fetch at ~0.6 s/object with
an identifiable UA ran 404 objects with 0 errors and 0 parse failures (2026-08-29).
Keep that posture: this is a non-commercial scholarly register and the museum is
running the last surviving public surface of a collection whose API they have
already switched off.

---

### 13.15 Krause / NGC / NumisMaster — a denomination with no parameter in the volume silently inherits the NEIGHBOURING denomination's (2026-09-04)

**The trap in one line: a catalogue that has no figure for a denomination does
not always leave the field empty — sometimes it fills it with the figure it does
have, and nothing in the record says so.**

**The case.** Five ducal Schleswig-Holstein gold coins carry `nominal:
1 Goldgulden` in our data and sat on `reichsdukatenfuss` because their only two
sources — NGC's World Coin Price Guide and NumisMaster, which is the same
lineage («powered by NumisMaster») — both publish **Mass 3.5 g · Fineness .986**,
i.e. the imperial ducat. They are:

| our id | issuer | KM | year | Fr |
|---|---|---|---|---|
| `unified-ngc-1156100` | Gottorp | 53 | 1619 | — |
| `unified-ngc-1157533` | Gottorp | 79 | 1627 | — |
| `unified-ngc-1156101` | Gottorp | 108 | 1664 | — |
| `unified-ngc-1161408` | Sonderburg | 10 | 1619 | 3099 |
| `unified-ngc-1206707` | Sonderburg | 24 | 1624 | 3100 |

**Why 3.5/.986 is not evidence here — measured, not argued:**

1. **The pair is the volume's blanket gold figure, not a per-type statement.**
   Across the whole NGC cache (2 205 records, 476 gold), `3.5 / .986` appears on
   **59 records: 43 Ducats, 7 Goldgulden, 9 unlabelled**. In the NumisMaster cache
   the same pair sits on **32 Ducats of the schleswig_holstein sub-scope** and on
   our five Goldgulden — verbatim identical.
2. **The same volume leaves most Goldgulden empty.** Of **20 Goldgulden** in the
   NGC cache, **13 carry no weight and no fineness at all** — including every
   royal Schleswig-Holstein Goldgulden (KM 30 1523, KM 39 1535, KM 42, KM 51,
   KM 57 1547), the very coins this project already has on `rhinsk_gylden_fod`
   with Bruun weights of 3.19-3.25 g.
3. **No Rhenish-gulden parameter exists anywhere in that dataset.** In 476 gold
   records there is not one entry in the 3.0-3.35 g band except the Danish
   12-Mark Courantdukat at 3.118 g — a different coin entirely.
4. **The catalogue contradicts itself where it can be checked.** Krause lists
   TWO gold coins of Christian Albrecht of Gottorp dated 1664 and gives both the
   same 3.5/.986: KM 108 «Goldgulden» and KM 109 «Ducat». KM 109 is independently
   weighed at **3.48 g** (Bruun lot 14218) and **3.50 g** (Künker 437/296) — the
   figure holds. KM 24 «Goldgulden» is independently weighed at **3.22 g** — the
   same figure is off by **−8.0 %**.
5. **Cross-checked against 17 coins where a real weighing exists**, NGC's 3.5 g
   deviates from reality by −0.3 % to −3.4 % (median −1.1 %) — *for ducats*. An
   8-12 % gap is not specimen tolerance; it is a different standard.

**What the coins actually weigh** (Jensen 1971 catalogue, §3a, plus one auction
specimen). Rhenish grid 72/rough Cologne mark = 3.2480 g; ducat grid 67/mark =
3.4904 g:

| weight | per mark | Δ vs Rhenish | Δ vs ducat | specimen |
|---:|---:|---:|---:|---|
| 3.22 g | 72.6 | −0.9 % | −7.8 % | Künker 176/5749 (2010) → Oslo Myntgalleri 42/414 (2026), Fr 3100 |
| 3.19 g | 73.3 | −1.8 % | −8.6 % | Lange 557a, coll. **K** (Lange's own collection) |
| 3.16 g | 74.0 | −2.7 % | −9.5 % | Lange 557b, KM, double-struck |
| 3.15 g | 74.2 | −3.0 % | −9.8 % | **Lange 527**, KM (GP 888, ex Mayntzhusen), the 1619 coin |
| 3.08 g | 75.9 | −5.2 % | −11.8 % | Lange 557b, Bode-Museum Berlin |

**Independent corroboration that these are Goldgulden, not ducats:**

- Numista's own currency header for the Danish duchies states **«1 Ducat = 2 Thaler · 1 Goldgulden = 1.5 Thaler»** — two denominations, ratio 1.333. By metal: ducat 3.4419 g fine vs Rhenish gulden 2.436-2.501 g fine → 1.38-1.41, consistent. At 3.5 g × .986 = 3.451 g fine the ratio would be **0.997**, i.e. the two would be the same coin and the tariff line meaningless. *This argument needs no weighing at all.*
- Jensen 1971: both Alexander variants were found c. 1912 in a **«guldgyldenfund»** in central Germany, deposited c. 1633 — they lay in a hoard of Goldgulden.
- A dedicated article exists: **H. Buchenau, «Schleswig-Holstein-Sonderburger Goldgulden», Blätter für Münzfreunde XV, N.F. II, Halle 1923, pp. 210-211.**
- The 1619 Sonderburg piece is illustrated in the Antwerp *Ordonnantie ende Placcaet des Conincx Inhoudende 't verbodt van de **goudtguldens van Duytschlandt*** (1627) — a prohibition of German **Goldgulden**.
- Jensen 2002 p. 39 independently records the **Gottorp 1619** piece as «**en unik guldgylden fra hertug Frederik 3. 1619**», acquired at auction in Osnabrück (Künker) spring 1998 for Den kgl. Mønt- og Medaillesamling.

**The general rule this case establishes.** When a catalogue prints metrology
for a denomination that its own volume otherwise does not parameterise, treat
the figure as **inherited from the neighbouring denomination until an
independent weighing confirms it**. The diagnostic is cheap and mechanical:

1. Group the source's own records by `(denomination, mass, fineness)`. A pair
   that recurs identically across *different* denominations is a default, not a
   measurement.
2. Check whether the same source leaves that denomination empty elsewhere. A
   catalogue that usually declines to guess, and guesses here, is guessing here.
3. Look for a derived field. NGC's `AGW 0.111 oz` is exactly
   `3.5 × .986 ÷ 31.1035` — computed from the stated pair, so it corroborates
   nothing.
4. Find one weighed specimen. Auction archives (acsearch, CoinArchives) and
   museum catalogues carry real masses; a type catalogue often does not.

**Do NOT read this as «NGC/NumisMaster are unreliable».** For ducats their
figure is accurate, verified here on 17 coins. The defect is narrower and more
insidious: **the absence of a parameter is not visible in the record**, so a
consumer cannot distinguish «the catalogue measured this» from «the catalogue
had nothing and reached for the nearest number».

**Consequence for our data:** the five carry a weight ~8-12 % too high and a
fineness that overstates their fine gold by ~20 %, and `weight_rough_verified` /
`fineness_verified` were set `true` by the NGC seed builder on those values.
See `docs/handoff.md` for the repair state.

### 13.16 Swedish issues on the Denmark page — scope is by CROWN HELD, tracked via ruler, not mint city (2026-09-11)

**Rule (curator, Serhii, 2026-09-11).** A polity's coins may appear in a
location register ONLY for the years the Danish king also held that polity's
crown. Personal union counts: while the Danish king wore the Swedish crown, the
Swedish issues are in scope. The test is applied to the **issuing crown (the
ruler)**, not the physical mint city — a Danish king's coin struck at an
occupied or contracted foreign mint stays Danish.

**Sweden timeline.** Kalmar Union: the Danish king held the Swedish crown under
Christian I (1457-1464, 1465-1467), Hans (1497-1501) and Christian II
(1520-1523). Sweden became permanently independent on **6 June 1523** (Gustav
Vasa elected; union dissolved). So any Swedish-crown issue dated **after 1523**
is out of Denmark scope.

**What was excluded (Tier 1, 12 finals, `data/v2/exclusions/danish_realm.yml`).**
All post-1523 Stockholm issues that had been ingested into `danish_realm` via the
IKMK/Bruun bulk harvests and rendered in the `seed_unsorted` holding pen:
Christian III 1535 ×3 (`dk-bruun-4232` = Galster 249, `kmk-139713`, `kmk-139714`
— these bear Christian III's NAME but were struck by Gustav Vasa's independent
Sweden during Grevens Fejde, so the crown was Vasa's), Erik XIV 1562, Johan III
1568-1586 ×4, Ulrika Eleonora 1719, Fredrik I 1731, Karl XIV Johan 1825, and
Gustav Vasa 1 Ørtug 1524-1527 (`kmk-316367` — added in a second pass; the
Swedish-mint scan missed it because its mint was spelled «Stokholm»).

**Not excluded — a Danish imitation, not a foreign issue.** `kmk-312155`
(«Æthelred» 1 Penning, mint Lund, 1.03 g) STAYS: the KMM record's `authority`
field reads «Æthelred, **imitation**» and `nation` = «Danmark» — an early Danish
imitation of an Anglo-Saxon penny struck at Lund (Becker Æ1/161), not an English
coin. **KMM `nation` is the COLLECTION nationality, not the issuing polity** (it
reads «Danmark» even on genuinely foreign pieces in the Royal cabinet); the
discriminator is `authority` + the «imitation» marker. So a genuine foreign issue
in the same collection — `kmk-529443` («Æthelred 2 den Rådløse», no imitation
marker → real English penny) and `kmk-578533` («Stralsund» civic witten) — is a
Tier-2 exclusion candidate despite `nation: Danmark`.

**Christian II 1535 Grevens Fejde — Danish, NOT excluded.** `dk-galster-c2g-85` /
`kmk-156732` / `kmk-156733` (Christian II 4 Skilling, Güstrow) assert the DANISH
crown, not a foreign one: struck by Albrecht VII of Mecklenburg IN CHRISTIAN II's
NAME during Grevens Fejde, reverse = Danish coat of arms, legend «IMMERITI
CARCERIS APVD HOLSATAS 3», catalogued Danish (Galster c2g, Sieg 1, Schou 18-36;
Kunzel, NNÅ 1985-86). Danish civil-war claimant coinage — in scope.

**What stays.** Union-era Swedish coins (Christian I / Hans Stockholm-Vesterås
Ørtug, 6 finals) — the Danish king then held the Swedish crown (note: those are
also pre-1514, below the mission floor — a separate axis). Danish-king coins with
a foreign/odd mint field (Hamburg, Mecklenburg, Wolfenbüttel under Christian IV
etc.) — Danish crown, so in scope; the mint field is a data-quality matter, not a
scope one.

**Not re-openable as a harvest gap.** The five un-ingested Swedish Galster pages
(`chr/c3g246-248,250,251.htm`, Gustav Vasa 1535) are deliberately NOT harvested
under this rule — do not add them.

**Tier 2 done (2026-09-11).** Five further foreign-crown intrusions excluded:
`kmk-529443` (Æthelred II England, Agnus Dei penny), `kmk-578533` (Stralsund
civic witten), `kmk-372890` (Rostock civic Skilling), `kmk-354873` (August III /
Poland-Danzig Solidus, Kopicki 348/3a), `kmk-175967` (Johann Albrecht I of
Mecklenburg Sechsling, Gaettens 182). The Christian II 1535 exile pieces were
reviewed and KEPT (Danish claimant coinage, above).

**Entity-routing filter — Sweden done (2026-09-12).** The root cause was
`scripts/lib/mint_registry.py` mapping «Stockholm» → `danish_realm`
unconditionally. Fixed with a `year_overrides` rule: Stockholm / Vesterås
year ≥ 1523 → the new out-of-scope `sweden` entity (`data/i18n/issuing_entities.yml`,
`out_of_scope: true`, consumed by no location); year < 1523 stays `danish_realm`
(Kalmar Union). The «Stokholm» KMM typo is now an alias. So a future re-harvest
routes post-1523 Stockholm issues to `seed/<src>/sweden.yml` (quarantined) instead
of `danish_realm`. Pinned by `tests/test_classify_mint_year_aware.py::TestStockholmSwedenTransition`.
Note: the `exclusions/` entries already keep the render clean regardless, because
they are applied on every absorb and key on stable seed ids — the filter merely
stops the seed itself from re-collecting the coins and auto-handles NEW post-1523
Swedish types.

**Follow-up (next pass).** The non-Swedish Tier-2 foreign mints have no
year-aware registry rule yet — England (`kmk-529443`, no place field → routed via
`nation`), Stralsund, Gdansk, Mecklenburg — but they are 1-offs already held off
the render by `exclusions/`; a registry/nation guard for them is low priority and
must NOT be city-blanket (Rostock carries both a civic issue AND a Danish
«Christian III» Hede-10 piece — city alone can't decide). Also: re-route the ~54
Holstein-Gottorp / Sønderborg ducal coins mis-bucketed into `danish_realm` (they
belong on the Holstein/Gottorp page); run the same ruler+mint scan on
`danish_norway` / `royal_slesvig` / `royal_holstein` + the IKMK builder; and the
`mint`-field data-quality debt (spurious «Hamborg»/«Mecklenburg» on genuine
Danish coins) plus the exonumia tokens in the `ruler` field.

---

## 13b. Which polity is harvested from which source

Per-source access notes live in this file; **per-polity coverage lives in
`docs/HARVEST_COVERAGE.md`** — a generated matrix of polities × sources
answering «which locations have we actually pulled from each source, and which
have we never touched?». Regenerate it after ANY harvest:

```bash
python scripts/audit_harvest_coverage.py
```

It also carries a **known-gaps** table: locations consciously deferred, recorded
so a deferral stays distinguishable from an oversight.

---

## 14. Operational status snapshot

Last reviewed: 2026-05-13.

| Source | Cache | Last fresh | Status | Notes |
|---|---|---|---|---|
| **Numista API** | `scripts/cache/numista/*.json` (683 entries) | 2026-05-12 | OK | Monthly quota active until May 2026; ask before > 5 live calls. |
| **ucoin composition** | `scripts/cache/ucoin/_composition.json` (219 entries) | 2026-05-13 | **paused** | Cloudflare challenge active; resume per §13.2 once cleared. |
| **ucoin URL index** | `scripts/cache/ucoin/_url_index.json` (~6 300 entries) | 2026-05-11 | OK for fetched, slugs validated on-fetch via canonical-tid guard. |
| **Bruun parsed lots** | `scripts/cache/bruun/lots/part{1,2,3,4}.json` | 2026-05-10 | OK | All 4 parts cached; pdf-viewer MCP unusable, use pypdf via curl-to-/tmp. |
| **Bruun page texts** | `scripts/cache/bruun/pages/part{1,2,3,4}.txt` | 2026-05-10 | OK | Used for full-text searches over auction-intro material. |
| **Hede HTML+JSON** | `scripts/cache/hede/*.{htm,json}` (~1 360 entries) | 2026-05-12 | OK | Comprehensive; per-coin re-parse via `scripts/parse_hede.py --force` if parser changes. |
| **IKMK Berlin** | `scripts/cache/ikmk/*.json` (1468 in-scope entries post-purge) | 2026-05-29 | OK | Scope-purged 2026-05-29 (7259→1468, dropped 5791 OOS — see §13.8). Direct WebFetch on `?download=json_ext` works; no rate-limit observed. |
| **danskmoent.dk Galster** | `scripts/cache/danskmoent/galster/*.{htm,json}` (110 pages) | 2026-05-16 | OK | Pre-Christian-III gap (Hede starts 1541); 79 entries for §AZ 1514-1541 window. Indexes `/c2galst.htm` + `/f1galst.htm`; per-coin `chr/c2g*.htm`, `fr/f1g*.htm`, `norge/n<r>g*.htm`. No `/c3galst.htm` (Christian III pre-1541 needs per-Galster# probing). |
| **danskmoent.dk concordance** | `scripts/cache/danskmoent/konkordans/konkord.{htm,json}` (1 page) | 2026-07-30 | OK | Sieg 2001 Christian VII renumbering (57 ↔ 57, both directions, self-checked as mutual inverses) + Hauberg/MB 1241-1375 (out of scope). Re-harvest via `scripts/fetch_danskmoent_konkordans.py`; `--parse-only` re-parses the cached page. See §13.12. |
| **Numista HTML (denmark_pre_1541)** | `scripts/cache/numista/denmark_pre_1541/*.{html,json}` (56 pages) | 2026-05-16 | OK | NOT the v3 API — direct HTML route at `en.numista.com/<N>`. Polite 30s pauses, ASCII-only User-Agent. 47 DK + 8 Norway for §AZ Tier 3. |
| **NumisMaster MC_ (legacy §AZ)** | `scripts/cache/numismaster/denmark_pre_1541/*.{html,json}` (3 entries) | 2026-05-16 | OK | Initial §AZ Tier 4 sample: MB#22 (Witten F.I 1516, MC_167729) + MB#33 (Chr.III 6 Pfg 1534-54, MC_167727) + MB#39 (Chr.III Goldgulden 1535, MC_167745). |
| **NumisMaster MC_ (Phase 1b inventory)** | `scripts/cache/numismaster/mc_index.json` (101 MC_IDs) + `_walks/*.txt` (28 page-text dumps) | 2026-05-16 | OK | Two-session inventory walk via Chrome MCP. Cumulative ~1900 in-window entries text-dumped (KM/MB/FR/C# + denom + year + country_label) across 4 sub-scopes. SH-cluster 562/562 walked + 101 MC_IDs anchored (HG-Rendsborg + GLÜCKSTADT). DK clean walk 40/53 pages (in-window 1591-1914). Norge clean walk 14/23 pages (in-window 1608-1813). Sweden 0 entries in Christian II window 1514-1523 — closed with negative finding. Remaining ~1800 MC_NNNNN anchors pending extraction before Phase-4 urllib bulk fetch. Cache root via `lib.paths.NUMISMASTER_CACHE`. |

| **NumisMaster (source site)** | — | 2026-05-17 | 🔴 **OFFLINE** | Site dead as of 2026-08-07 — all URLs 302 → numismaticnews.net/pricing. Cache is a permanent frozen archive; re-fetch impossible. Successor = NGC (§1.5). |
| **NGC World Price Guide** | *(not yet harvested)* | — | **surveyed** | Access surface fully mapped 2026-08-07 (§1.5 + §13.13). No API; browser-context `fetch()` only — Playwright tested in 7 configs and blocked in all, see §13.13(c2). Target = German territories absent from the NumisMaster walk. Fetcher not yet written. |

When the «Status» column shows anything other than `OK`, the affected harvest pipeline is blocked and TODO entries reference the recovery procedure.

---

When citing a new source for the first time, **add a ref-slot** in the appropriate references file (per CLAUDE.md §5 «Source hierarchy» / «Web-sourced facts → bibliography entry + inline `<sup>` citation, IMMEDIATELY»).
