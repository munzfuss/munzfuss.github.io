# Sources Catalogue — Numismatic Sources We Use

> **Purpose.** Master register of every external source the project
> draws on, with characterisation (what each source covers best),
> recommended access pattern (which tool works, which fails), and
> a quick-reference matrix mapping coin theme / period / location
> to the right place to look first.
>
> Operational tool-mechanics (WebSearch → WebFetch → Apify → Chrome
> MCP escalation chain, Numista API quota rules) live in `CLAUDE.md`
> sections «Tool fallback chain» and «Numista API budget». This file
> covers the **sources themselves**: their content, biases, gaps,
> and how to read them.

---

## 0. Quick reference matrix

When researching a coin, consult sources in this order based on what you need:

| Need | First source | Second source | Third source |
|---|---|---|---|
| **Specimen-level catalogue (KM, Hede, Sieg, Lange, Fr, Schou, Aagaard, weight, NGC grade)** | Bruun PDF (Stack's Bowers Part I/II/III) | Numista N# page | ucoin tid page |
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
1. **Chrome MCP** — `mcp__Claude_in_Chrome__navigate` + `javascript_tool` to extract `document.querySelector('main').innerText`. Cloudflare may challenge first request; wait ~5-10 s and retry. **Use this by default.**
2. **WebFetch** — returns 403 most of the time. Skip.
3. **Apify rag-web-browser** — sometimes works, sometimes 403. Try if Chrome MCP unavailable.
4. **Numista REST API** (`api.numista.com/v3/...`) — works reliably but **counts against quota**. Free tier = 200/24h, monthly cap mentioned in CLAUDE.md as «scarce in May 2026». **Always ask the user before any bulk-fetch >5 calls.** Cached responses live in `scripts/cache/numista/<nid>.json` and are free to re-read.

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

**Access:** WebFetch returns 403; Chrome MCP works (note: Numista is *not* a sanctioned Chrome-MCP scraping target — see CLAUDE.md «Tools and resources» — but ucoin.net is fine for Chrome-MCP fallback when WebFetch fails).

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

### 8.2 Nationalmuseet København — `natmus.dk`

Danish National Museum. Holds the largest Danish-coin collection and is the home of the Esrum Schatzfund Christian-IV-Doppelguldkronen (Hede 28, 1628).

Notable URLs:
- <https://natmus.dk/webdok/christian-4s-svindler-moent-fylder-400-aar/> — popular article on Christian-IV «svindler-mønt» (Corona Danica) 400-year anniversary
- (museum collection database not as web-scrapable as IKMK)

**Access:** WebFetch works for public-facing pages.

### 8.3 Royal Coin Cabinet, Copenhagen (KMK)

The Kongelige Mønt- og Medaillesamling (KMK). Hosted within Nationalmuseet. Records typically only accessible through Nationalmuseet pages.

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

When citing a new source for the first time, **add a ref-slot** in the appropriate references file (per CLAUDE.md §5 «Source hierarchy» / «Web-sourced facts → bibliography entry + inline `<sup>` citation, IMMEDIATELY»).
