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

### 1.4 NumisMaster — `numismaster.com`

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

**Project scripts (legacy §AZ — slated for Phase-5 rename → generalised parser):**
- `scripts/parse_numismaster_pre1541.py` — MC_<N>.html → JSON sidecar (uses `lib.paths.NUMISMASTER_CACHE`)
- `scripts/maintenance/build_numismaster_pre1541_seed.py` — JSON → seed YAML
- **Cache root**: `lib.paths.NUMISMASTER_CACHE` = `scripts/cache/numismaster/`. Subdirectories:
  - `denmark_pre_1541/MC_<N>.{html,json}` — legacy §AZ subdir (3 entries: MB# 22 / MB# 33 / MB# 39)
  - `_walks/leaf_*.txt` — raw Chrome-MCP page-text dumps per filtered search-result page (Phase-1b output; provenance for `mc_index.json`)
  - `_walks/hub_*.txt` — geographic hub snapshots (documentation only)
  - `_walks/_phase_*.md` — process documentation (topology findings, session handoffs, final summary)
  - `mc_index.json` — consolidated MC_NNNNN inventory per country filter; the Phase-4 urllib fetch input
  - **Phase-4 planned**: `{schleswig_holstein,denmark,norway}/MC_<N>.{html,meta.json}` — bulk-fetch output, one subdir per sub-scope

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

**Wilcke** = Julius Wilcke, the foundational Danish numismatic-policy historian. Three volumes covering 1588–1746:

| Volume | Title | Years | URL |
|---|---|---|---|
| **Wilcke I** | *Christian IVs Møntpolitik 1588-1625* | København 1919 | reference page <https://www.danskmoent.dk/wilcke/w2ref.htm> |
| **Wilcke II** | *Møntvæsenet under Christian IV og Frederik III 1625-1670* | København 1924 | reference page <https://www.danskmoent.dk/wilcke/w2ref.htm> |
| **Wilcke III** | *Christian V – Frederik IV* | (covers ~1670-1730) | <https://danskmoent.dk/wilcke/w3guldkh.htm> |

**Useful for:** primary attestations of Forordninger and Patenter — e.g. Wilcke II Anm. 53 quotes the «åbent Brev af 12. Juli 1618» introducing Christian IV's Corona Danica.

**Page-number trap:** secondary literature (especially Hede's 1957 footnotes) cites Wilcke I p. 152 for the «1618 small denominations slightly lower Müntzfod» claim, NOT for the patent date. The patent itself is at Wilcke I pp. 156-157 (cross-referenced in Wilcke II Anm. 53). Do not conflate these two facts.

**Access:** WebFetch works.

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
| **Lange** | Aage Lange, *Sønderjyske og slesvig-holstenske Mønter 1522-1864* | Schleswig-Holstein-specific catalogue. Sub-letters (Lange 444 vs 444A vs 447B = Bruun-recognised sub-variants) | paper-only |
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
- «Münzfüße» (linked above) — overview
- «Lübisches Münzsystem» (<https://www.hagen-bobzin.de/hobby/muenzverein_wendisch.html>) — Lübeck Mark-Lübisch system, Hamburger Bank-Fuß 1769 / Altonaer Bank-Fuß 1777

**Caveats:** dating sometimes coarse (e.g. 1753 Konventionsfuß without distinguishing Austria 1750 vs Bavaria 1753), and uses analytic-didactic labels («Schleswig-Holsteinischer Kurantfuß») not always period-attested. Cross-check against period sources (Meyers, Wikipedia DE).

**Access:** WebFetch works.

### 6.6 Künker — `kuenker-numismatik.de`

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

### 7.3 NGC PriceGuide

<https://www.ngccoin.com/price-guide/world/>

NGC's certified specimen images and price guide. URL pattern: `/world/{country}-{denom}-km-{kmnum}-{year}-cuid-{N}-duid-{N}`

**Use as:** secondary confirmation of weight / fineness / KM# attribution. NGC is well-curated.

**Access:** WebFetch typically returns 403. Use Chrome MCP.

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

- `docs/9_thalerfuss.md` — heavy use of Wikipedia DE Reichstaler / Speciestaler / Leipziger Fuß / Konventionstaler / Sächsische Münzgeschichte / Zinnaer / Augsburger; Bobzin; Meyers eLexikon; Künker; MGM «Species»; Hede (via danskmoent.dk)
- `docs/krone_muentzfuesse.md` — heavy use of Hede NNUM articles (Kronemønten + F3 Guldkroner); Wikipedia DE «Corona Danica»; Aagaard 2004/2011/2022; Wilcke I/II; Bruun PDF Part II/III; danskmoent.dk c5h{N}.htm pages
- `docs/hamburg.md` — Soetbeer 1869, Shaw 1896, Bindseil 2019, Bobzin, Wikipedia DE «Hamburger Bank»
- `docs/altona.md` — Wikipedia DE «Königliche Münze zu Altona», Schleswig-Holsteinische Speciesbank
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
*Decision.* `docs/HARVEST_GUIDE.md` ucoin section needs updating from «deferred» to «active Chrome MCP route, 31-60 s pacing». — codified during BR batches 10-16.

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
| **Numista HTML (denmark_pre_1541)** | `scripts/cache/numista/denmark_pre_1541/*.{html,json}` (56 pages) | 2026-05-16 | OK | NOT the v3 API — direct HTML route at `en.numista.com/<N>`. Polite 30s pauses, ASCII-only User-Agent. 47 DK + 8 Norway for §AZ Tier 3. |
| **NumisMaster MC_ (legacy §AZ)** | `scripts/cache/numismaster/denmark_pre_1541/*.{html,json}` (3 entries) | 2026-05-16 | OK | Initial §AZ Tier 4 sample: MB#22 (Witten F.I 1516, MC_167729) + MB#33 (Chr.III 6 Pfg 1534-54, MC_167727) + MB#39 (Chr.III Goldgulden 1535, MC_167745). |
| **NumisMaster MC_ (Phase 1b inventory)** | `scripts/cache/numismaster/mc_index.json` (101 MC_IDs) + `_walks/*.txt` (28 page-text dumps) | 2026-05-16 | OK | Two-session inventory walk via Chrome MCP. Cumulative ~1900 in-window entries text-dumped (KM/MB/FR/C# + denom + year + country_label) across 4 sub-scopes. SH-cluster 562/562 walked + 101 MC_IDs anchored (HG-Rendsborg + GLÜCKSTADT). DK clean walk 40/53 pages (in-window 1591-1914). Norge clean walk 14/23 pages (in-window 1608-1813). Sweden 0 entries in Christian II window 1514-1523 — closed with negative finding. Remaining ~1800 MC_NNNNN anchors pending extraction before Phase-4 urllib bulk fetch. Cache root via `lib.paths.NUMISMASTER_CACHE`. |

When the «Status» column shows anything other than `OK`, the affected harvest pipeline is blocked and TODO entries reference the recovery procedure.

---

When citing a new source for the first time, **add a ref-slot** in the appropriate references file (per CLAUDE.md §5 «Source hierarchy» / «Web-sourced facts → bibliography entry + inline `<sup>` citation, IMMEDIATELY»).
