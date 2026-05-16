# Denmark pre-1541 source survey — alternatives to Hede

> **Status: PRELIMINARY survey 2026-05-16, per §BJ.** This file
> documents what data sources cover the 1514-1541 Denmark-track
> sub-window (the gap that §BI opened and that Hede 1957 itself does
> NOT cover — Hede's catalog starts at Christian III 1541). The
> survey informs §AZ (the catalog-import implementation task) by
> identifying which sources have machine-readable data + acceptable
> coverage + acceptable acquisition cost.
>
> **Not a finalised data-import yet.** This is reconnaissance. The
> per-source assessments below are based on a single survey session;
> each source's actual data-shape may have edge cases not surfaced
> here. Treat coverage estimates as «order of magnitude» until the
> actual harvest pass for that source runs.

## Scope

The 1514-1541 sub-window covers Denmark-Norway-track coinage under
three rulers:

  - **Christian II** (1513-1523, deposed) — DK + Norway + Sweden (Kalmar Union until 1523)
  - **Frederik I** (1523-1533) — DK + Norway, Duke of Schleswig + Holstein
  - **Christian III** (1534-1559; window cuts at 1541) — DK + Norway + Schleswig + Holstein

Mints active in the window (per Wilcke 1950 + Bruun lot data):

  - **Royal mints**: København (Klarekloster from 1541), Malmö (Skåne, Jørgen Kock mintmaster), Husum (Schleswig under Frederik I as Duke 1514), Gottorp (Schleswig duchy mint), Roskilde + Aarhus + Ribe + Stockholm + Visby (Christian III Grevens Fejde war-finance 1534-36)
  - **Civil-war mints** (1534-1536 Grevens Fejde): Roskilde Serridslev (siege), Aarhus, Ribe + Lübeck-aligned mints under Greve Christoffer

## Coverage matrix

| Source | Christian II 1513-1523 | Frederik I 1523-1533 | Christian III 1534-1541 | Norge 1513-1541 | Schleswig-Holstein 1514-1541 | Data shape |
|---|:-:|:-:|:-:|:-:|:-:|---|
| **Hede 1957** | ✗ | ✗ | ✓ (1541+ only) | ✗ | ✗ | parsed JSON, our existing cache |
| **Wilcke 1950** (local) | ✓ specs in master tables (p. 150-156) | ✓ specs in master table p. 187 + Husum p. 186 | ✓ Grevens Fejde p. 242 + 1541 ordinance p. 116 | passing references | partial (Husum 1514 only) | local TXT cache, parseable |
| **Bruun PDFs** (local 4 parts) | 13 lots with full specs + NGC grades | 13 lots (incl. Husum 1514 + Gottorp 1523-33) | 13 pre-1541 lots (Grevens Fejde mints, 1537 Joachimstaler, 1541 Mark) | (search needed) | yes (Husum + Gottorp lots) | parsed JSON `lots/part{1-4}.json` |
| **danskmoent.dk Galster index `c2galst.htm`** | ✓ FULL table 37-44 + 80-91 + Norge 164-174 | — | — | sub-section per coin | — | HTML table, parseable |
| **danskmoent.dk Galster index `f1galst.htm`** | — | ✓ FULL table 45-79 + Schleswig 115-128 + Norge 166-171 | — | sub-section per coin | sub-section per coin | HTML table, parseable |
| **danskmoent.dk Galster index `c3galst.htm`** | n/a | n/a | **DOES NOT EXIST** (HTTP 404) | — | — | — |
| **Schou 1926** (Internet Archive / paper) | ✓ comprehensive | ✓ comprehensive | ✓ comprehensive | ✓ Norge | ✓ partial | scan only; data extraction = OCR |
| **Sømod** (Jørgen Sømod, multiple works) | column-referenced on c2galst | column-referenced on f1galst | — | covers Norge | covers Slesvig-Holsten | print + danskmoent.dk article hosting |
| **Sieg-Møntkatalog** | ✓ densest single ref | ✓ densest single ref | ✓ densest single ref | partial | partial | print only (annual / periodic) |
| **Jensen-Skjoldager 2017/2021** | (Tronraneren 2021 mentioned for F-prefix?) | ✓ «Tronraneren» 2021 + L-prefix die varieties | — | covers via N-prefix (e.g. N-11) | — | print only, cited inline on Galster pages |
| **Schive 1865** «Norges Mynter» | — | — | — | ✓ Norway primary | — | scan only |
| **Lange 1908-12** | partial Holstein | partial Holstein | partial Holstein | — | ✓ primary for Holstein duchy | print only |
| **Numista** (Chrome MCP) | ~7 entries with brutto + finhed + cross-refs | ~14 entries with full specs | ~25 entries with full specs (pre-1541) | ~5 entries | ~5 entries | HTML scraping via Chrome MCP, no API |
| **lex.dk** | encyclopaedic context | encyclopaedic context | encyclopaedic context | — | — | HTML article, parseable |
| **Münzkabinett Berlin IKMK** | likely ≥1 specimen | confirmed Frederik I Goldgulden 1531 N#355730 image source | likely several specimens | possibly | possibly Lange-cited specimens | JSON API (`ikmk.smb.museum`), parseable |
| **Nationalmuseet i København** | image source on Numista (CC BY-SA 4.0) | image source on Numista | image source on Numista | — | — | online catalog at samlinger.natmus.dk (status to verify) |
| **ucoin.net** | (403 from anonymous fetch — Cloudflare) | (same) | (same) | — | — | HTML, but needs Chrome MCP per §13.1 |
| **numismaster.com** | (Krause-based; pre-1604 sparse) | (same) | (same) | — | — | commercial, low pre-1541 priority |

## Per-source detailed cards

### 1. Wilcke 1950 «Renæssancens Mønt- og Pengeforhold 1481-1588»

- **Local cache**: `scripts/cache/wilcke/renaessancens_moent_1950/pages/wilcke_7-{1..8}.txt` (PDF + parsed TXT).
- **Public-domain online**: hosted by danskmoent.dk in chapter form at `/wilcke/w7*.htm`.
- **Coverage 1514-1541**: ordinance-level specifications (Bruttovægt + Lødighed + Finvægt + Stkr/M. cølnsk) for:
  - 1513 Christian II Haandfæstning specs (Wilcke 7-2 p. 150)
  - 1514 «Brev Dines Blicher Malmø» (Wilcke 7-2 p. 152, p. 153)
  - 1518 Klipping ordinance (Wilcke 7-2 p. 157)
  - 1523 Christian II Sølvgylden specs
  - 25 Feb 1524 Frederik I ordinance (Wilcke 7-2 p. 184-187) — full table: Nobel, Sølvgylden ×3 fractions, Rhinsk Gylden, Mark Danske ×3 fractions, 4 ß, 4-Hvid ß, Hvid
  - Frederik I as Duke Husum 1514+ table (Wilcke 7-2 p. 186) — Mark lybsk ×3 fractions, 4 ß lybsk, 2 ß lybsk, 1 ß lybsk, Husumdaler ×2 variants 1522, Doppelschilling 1526
  - 1534-39 Grevens Fejde debasement table (Wilcke 7-3 p. 242)
  - 20 Sep 1541 Christian III Møntordning (Wilcke 7-4 p. 116)
- **Data shape**: per-entry: denomination, Stkr/cølnsk M, Bruttovægt g, Lod/Karat, ‰, Finvægt g, mintmark/mint. Excellent for ordinance-vs-specimen comparison.
- **Strengths**: ordinance-level legal authority; verbatim quotes of source documents; specifies mintmasters (Dines Blicher, Jørgen Kock, Mårtens, Reynold Junge, Poul Fechtel). Already in our cache.
- **Weaknesses**: thin on per-specimen specs (the «what the mint produced» vs «what the ordinance required» — Wilcke discusses the standards more than individual coins). No images.
- **Verbatim sample**: «*Vi Fr. ... at slaa, i Guld: Nobler (den vegne Mark skal holde 23½ Karat og skraade 16 Stkr.), Rinske Gylden (18 Karat, 72 Stkr.) ...*» (Wilcke 7-2 p. 184).

### 2. Bruun PDFs — Stack's Bowers L. E. Bruun Collection 2024-2026

- **Local cache**: `scripts/cache/bruun/part{1,2,3,4}.pdf` + parsed `scripts/cache/bruun/lots/part{1-4}.json` + page-text `scripts/cache/bruun/pages/part{1-4}.txt`.
- **Coverage 1514-1541**: **38 distinct lots** in the realm (DK + Norge + S-H + Sweden under C-II + Gotland):
  - Christian II: 13 lots (DK + Visby + Aarhus civil-war + S-H peripheral)
  - Frederik I: 13 lots (DK Goldgulden 1527 × 2, Husum 1514 Mark + ½M, Gottorp Goldgulden, Roskilde 1523 Skilling, Ribe 1524, Copenhagen ¼ Sølvgylden 1532)
  - Christian III pre-1541: 12 lots (1535 Klippinge — Roskilde + Aarhus, Stockholm 4 Skilling, Joachimstaler 1537 × 3 weight tiers, Gottorp Ducat 1534 Lange-17, Roskilde Goldgulden 1536 Lange-18, Mark 1541 Hede-3A first)
- **Data shape**: lot_no, page, weight_g, NGC grade, rarity flag, refs dict {Sieg, Schou, Bruun, Hede, KM, Fr, Lange, Dav, Galster}, body_excerpt with mintmaster + provenance + sale estimate.
- **Strengths**: per-specimen Brutto weight + NGC grade; dense cross-referencing (Sieg + Schou on 37/38 lots, Galster on most, Fr on gold, Lange on S-H, Dav on Taler-size silver); JSON already parsed — **no PDF re-extraction needed**.
- **Weaknesses**: limited to specimens that appeared in this auction series (not all known types); body_excerpts are auction-catalog narrative (occasionally needs cleanup); NGC-graded specimens skew toward high grades.
- **«MB#» identification — confirmed**: NOT Münzkabinett Berlin. The single MB# in the Bruun corpus appears on a Swedish Riksdaler 1534 (part 1 lot 1241: «MB-48; Dav-8692; SM-106(99); Delzanno-7; Hagander-3; Appelgren-479»). MB = Swedish-specific reference, most likely Tingström «Mynt och Medaljer» or Stiernstedt/Bonnier «Mynt-Bok» — IRRELEVANT to Denmark-Norway register.

### 3. danskmoent.dk Galster indexes `c2galst.htm` + `f1galst.htm`

- **URL**: `https://www.danskmoent.dk/c2galst.htm` + `https://www.danskmoent.dk/f1galst.htm`
- **`c3galst.htm` does NOT exist** (HTTP 404) — Christian III is treated under separate per-coin URLs without an aggregating Galster-index page (per-coin `chr/c3g*.htm` accessible by Galster number directly).
- **Format**: HTML `<table>` per page-section. Columns: Galster# · Schou# · Sømod# · Prægested (mint) · Nominal · Materiale · År · Bemærkninger. Each Galster# is a hyperlink to `chr/c2g<N>.htm` or `fr/f1g<N>.htm`.
- **Coverage**:
  - `c2galst.htm` — Christian II Danmark Galster 37-44 (København + Malmö), then 80-91 (Grevens Fejde-era Christian II «in exile» Aarhus + civil-war pieces), then Norge sub-section Galster 164-174 (Oslo + Bergen)
  - `f1galst.htm` — Frederik I Danmark Galster 45-79 (Malmö gold + København silver), then Schleswig-Holstein 115-128 (Husum + Gottorp), then Norge 166-171 (Oslo + Bergen)
- **Per-coin page shape** (sample `fr/f1g46.htm` Frederik I 1531 Goldgulden):
  - Header line: «Frederik 1., 1 Ungersk gylden 1531 København eller Malmø»
  - Description: «Forside: Portræt, bagside: våbenskjold (Galster 46, Schou 1, Jensen/Skjoldager T-41/45)»
  - **Bruttovægt**: 3,49g
  - **Finhed**: 0,986
  - **Finvægt**: 3,44g
  - Inscription + Latin / Danish translation
  - Litteratur block citing Ernst, Axel: NN&Aring; 1938 + Jensen, Niels Jørgen og Skjoldager, Mogens: Tronraneren (2021)
- **Norge sub-pages** (sample `norge/nc2g164.htm`):
  - «Christian 2., Oslo, Skilling, u. år»
  - «Forside: Oldenborgs våben på kors på skjold, bagside norske løve i skjold (Galster 164, Schive XV.7-9, Schou 18-24)»
  - **Vægt**: 1,70-2,17 g (range)
  - **Finhed**: 0,250
  - Cited from BR 910 (auction lot 266, 2022)
- **Strengths**: data shape is uniform across pages → parseable with one regex pass; cross-references to Schou + Schive (Norge) + Sømod + Jensen-Skjoldager are inline.
- **Weaknesses**: not all per-coin pages have full specs (some are just description + image); image URLs are inline but may need separate fetch; Galster numbering jumps gaps where types are skipped.

### 4. Schou 1926 «Beskrivelse af danske og norske mønter 1448-1814 og danske mønter 1815-1923»

- **Author**: Hans Henrik Schou (1858-1932), Danish industrialist + numismatist.
- **Publisher / year**: Copenhagen 1926. Replaces the 1791 Beskrivelse.
- **Coverage**: 475 years of Danish + Norwegian coinage (1448-1923 DK, 1448-1814 Norge). **Comprehensive for Christian II + Frederik I + Christian III**.
- **Online status**: Bibliographic record on danskmoent.dk (`/schou.htm`) confirms existence; Internet Archive lookup needs more specific query to confirm scan availability. **Likely accessible as a scan but not as parseable structured data.**
- **Method**: Schou's staniolaftryk (foil impressions) of coins in various Danish + Norwegian collections, now archived at Den Kongelige Mønt- og Medaillesamling København. Each Schou # corresponds to a specific specimen / die-variant.
- **Cross-referenced by**: Hede 1957 throughout; Galster pages (Schou column); Bruun (37/38 pre-1541 lots cite Schou).
- **Recommendation**: secondary cross-reference, NOT primary data source for our project. Use Galster + Bruun + Wilcke for specs; cite Schou for variant attribution.

### 5. Sieg-Møntkatalog (Sieg)

- **Author / publisher**: Kasper Sieg + family / Sieg numismatik publishing house, Denmark.
- **Format**: periodic price-catalog (annual or biennial). Print only.
- **Coverage**: comprehensive Danish-Norwegian coinage including pre-1541. **Densest single cross-reference** on Bruun lots (37/38 cite Sieg-N).
- **Online status**: publisher homepage exists but no online catalog. Subscriber-only digital edition possibly available.
- **Recommendation**: secondary cross-reference. Sieg# values are tracked via Bruun lots + danskmoent.dk Galster pages (Sieg column often visible inline). For our project Sieg# enters as a label, not as a primary fetcher target.

### 6. Jensen-Skjoldager 2017 / «Tronraneren» 2021

- **Authors**: Niels Jørgen Jensen + Mogens Skjoldager
- **«Tronraneren — Frederik 1.s danske mønter» (2021)** — Danish-language monograph specifically on Frederik I Danish coinage. Confirmed via inline citation on `fr/f1g46.htm`: «Jensen, Niels Jørgen og Skjoldager, Mogens: Tronraneren - Frederik 1.s danske mønter (2021)».
- **Earlier work 2017** — likely the source of T-prefix die-variant numbering (e.g. «T-41/45» on f1g46 = Tronraneren-trial-41 cf. 45).
- **Coverage**: Frederik I 1523-1533 comprehensively; Christian II partial via Norge N-prefix.
- **Online status**: print monograph; Google Books preview status unknown. **Cited inline by every danskmoent.dk Frederik I per-coin page.**
- **Recommendation**: primary die-variant authority for Frederik I; secondary for other rulers. Project should cite by author + page when prose mentions Jensen-Skjoldager.

### 7. Schive 1865 «Norges Mynter i Middelalderen»

- **Author / year**: Christian August Schive 1865.
- **Coverage**: Norwegian medieval + Renaissance coinage (Schive numbering, used on every Norge per-coin page on danskmoent.dk — e.g. «Schive XV.7-9» for Christian II Oslo Skilling, «Schive XVI.1» for Frederik I Oslo Firehvid).
- **Online status**: likely on Internet Archive as a scan (digitised 19th-c. work).
- **Recommendation**: primary Norwegian numismatic reference for the period. Project should cite as «Schive N.M.M.» when prose mentions Norwegian issues.

### 8. Lange 1908-12 «Sammlung Schleswig-Holsteinischer Münzen und Medaillen»

- **Author**: Christian Lange (Holstein)
- **Coverage**: Schleswig-Holstein numismatics 1481+ (cited in Wilcke p. 41 footnote 1). Used on Bruun S-H lots: Husum Mark 1514 (Lange-11), Gottorp Goldgulden 1523-33 (Lange-9a), Gottorp Ducat 1534 (Lange-17), Roskilde Goldgulden 1536 (Lange-18).
- **Already in project**: cited on Lübeck + Schleswig-Holstein pages.
- **Recommendation**: primary for S-H duchy mintages.

### 9. Numista (`en.numista.com`)

- **Coverage 1514-1541** (per Chrome MCP browse 2026-05-16 + user-provided inventory):
  - Christian II: ~7 entries with Sieg + Schou + MB + Fr cross-refs
  - Frederik I: ~14 entries (Goldgulden 1527 + 1531, Noble 1532, Sølvgylden tier 1532, Husum 1514 Schillings, Gottorp Goldgulden, etc.)
  - Christian III pre-1541: ~25 entries (Grevens Fejde mints 1535-36, Joachimstaler 1537, Gottorp Ducat 1534, 1541 Hede-3A as boundary)
  - Norway under DK: Christian II Skilling Oslo, Frederik I Skilling Bergen + Oslo, Christian III Skilling Oslo 1535 (Galster N-prefix)
- **Data shape**: brutto + finhed (when known) + diameter + obverse/reverse description + Latin lettering + translation + cross-refs (Fr, Galster, Schou, SIEG, MB, Hede, Lange, Dav EC) + photo credit (Münzkabinett Berlin or Nationalmuseet København).
- **Access**: Chrome MCP only per CLAUDE.md «Numista API budget» rule (May 2026 quota tight). Already started this session — page 1 catalog confirmed.
- **Recommendation**: USE LAST. Numista is user-edited, so cross-refs may have transcription errors; primary value is the photo + per-specimen weight when curated.

### 10. lex.dk (Den Store Danske / Trap Danmark)

- **Coverage**: encyclopaedic context. Articles consulted: «dukat» (Jørgen Steen Jensen, Nationalmuseet); ruler biographies «Christian II», «Frederik I», «Christian III»; topical «Grevens Fejde», «Joachimstaler», «Klippinge».
- **Data shape**: prose articles, sometimes with specs in passing.
- **Recommendation**: cite for contextual claims; no systematic per-coin data.

### 11. Münzkabinett Berlin (IKMK)

- **URL pattern**: `https://ikmk.smb.museum/object?id=XXXXXXXX` + JSON endpoint (per `docs/SOURCES.md §8.1`).
- **Coverage**: confirmed photo source on Numista entries (e.g. Frederik I 1531 Goldgulden N#428864 credits Münzkabinett Berlin). Likely has additional Christian II + Frederik I + Christian III specimens.
- **Recommendation**: secondary specimen-attestation source; useful for image + curator-provided specs. JSON endpoint enables structured fetch.

### 12. Nationalmuseet i København

- **Numista photo credits**: «Nationalmuseet i København (CC BY-SA 4.0)» appears on multiple pre-1541 entries.
- **Catalog**: separate from danskmoent.dk; likely at `samlinger.natmus.dk` or museum-specific URL.
- **Recommendation**: secondary specimen-attestation source. Status to verify in follow-up.

### 13. Sømod (Jørgen Sømod)

- **Bio**: `https://www.danskmoent.dk/soemod.htm` — Danish numismatist focused on DK + Norge + Slesvig-Holsten from late 1000s to present; «Det Store Projekt» multi-volume project from 2003.
- **Cross-referenced by**: `c2galst.htm` (Sømod column) — third spine cross-reference after Galster + Schou.
- **Coverage**: comprehensive across Christian II + Frederik I + Christian III; pre-1541 entries cite Sømod numbers (e.g. «Sømod 18» for c2g37).
- **Recommendation**: secondary cross-reference; cite by Sømod-N when known.

### 14. ucoin.net + numismaster.com

- **ucoin.net**: blocked by Cloudflare on anonymous fetch (HTTP 403). Project already has §M (ucoin Composition harvest) tracking ~490 uncached URLs — pre-1541 coverage status unverified. Likely thinner than Numista.
- **numismaster.com** (probed 2026-05-16 via Chrome MCP + Python urllib):
  - Krause-Mishler-based commercial catalog. Site tagline: «Expert pricing for U.S. coins, world coins and more with KM numbers.»
  - **Public HTML pages render skeleton/marketing content only** — actual coin data is behind a paid subscription (4 «Subscribe» mentions + 4 «Log in» mentions on the sample coin page `/coins/coins-10012282`). Body has no Denmark / KM / year tokens for anonymous fetchers.
  - Search form is AJAX-driven and either silently fails or returns results requiring authenticated session.
  - **KM numbering for Denmark begins ~1604** — pre-1541 coverage sparse-to-zero even with subscription per §BJ original prediction.
  - Verdict 2026-05-16: **NOT a usable source for §AZ**. Documented as negative finding; no harvester built.
- **Recommendation**: skip both for §AZ. ucoin defer to §M when Cloudflare cooldown allows; NumisMaster permanently out of scope (paywalled + non-overlapping window).

## Cross-reference key (resolved)

| Ref scheme | Meaning | Source work | Density on pre-1541 Bruun lots |
|---|---|---|---|
| **Bruun-NNNN** | Stack's Bowers L. E. Bruun coll-id | Bruun auction series | 38/38 |
| **Sieg-N** | Sieg-Møntkatalog | Sieg numismatik annual | 37/38 |
| **Schou-N** | Schou 1926 | Beskrivelse | 37/38 |
| **Galster-N** / **Galster UU-N** | Galster catalog | Various Galster works | most |
| **Fr-N** | Friedberg «Gold Coins of the World» | Standard reference | 6/38 (gold only) |
| **Dav-N** / **Dav EC I-N** | Davenport European Crowns | Standard reference | 5/38 (taler-size silver only) |
| **Lange-N** | Lange 1908-12 | Schleswig-Holstein monograph | 4/38 (S-H only) |
| **Hede-N** | Hede 1957 | Danish monograph | 3/38 (1541+ only) |
| **KM-N** | Krause-Mishler «Standard Catalog» | Modern catalog | 2/38 (rare pre-1604) |
| **MB-N** | Swedish-specific (likely Tingström / Stiernstedt) | — | 0/38 (Swedish only, ID-confirmed) |
| **Sømod-N** | Sømod | Multiple Sømod works | column on c2galst |
| **Jensen-Skjoldager T-N / N-N / F-N / L-N** | Tronraneren 2021 | Jensen-Skjoldager monograph | inline on f1g* pages |
| **Schive XV.N** | Schive 1865 | Norges Mynter i Middelalderen | inline on norge/* pages |
| **Ernst NNÅ-N** | Numismatisk Forenings Aarsskrift Ernst-articles | Periodical | inline on per-coin pages |
| **SM-N** | (Swedish) | — | Swedish lots only |
| **Delzanno-N** | (Swedish) | — | Swedish lots only |

## Harvest plan recommendation for §AZ

Three-tier import architecture, ordered by priority:

### Tier 1 — local-cache enrichment (zero web cost)

  - **Bruun parsed lots** already provide 38 pre-1541 specimens with full specs + cross-refs. **Promote these directly into curated `data/locations/denmark.yml` entries** per §BF when its data-population phase begins. No new fetcher needed.
  - **Wilcke 1950 chapters 7-2 + 7-3 + 7-4 master spec tables** provide ordinance-level Brutto + Finhed + Stkr/M for ~30 unique denom × ruler combinations. Hand-extract these into the `data/shared/fuesse.yml` definitions for Müntzfüße that cover the window (e.g. when the «1514 Lovkompleks» Fuß is defined per §BF, its Grundwerte come from Wilcke).

### Tier 2 — danskmoent.dk Galster page harvest

  - Walk `c2galst.htm` + `f1galst.htm` to enumerate all Galster# per ruler + Norge sub-pages.
  - For each Galster#, fetch `chr/c2g<N>.htm` or `fr/f1g<N>.htm` (or `norge/nc2g<N>.htm` for Norge).
  - Parse per-coin pages with a unified parser (data shape is consistent: ruler + nominal + year + mint + description + cross-refs + Bruttovægt + Finhed + Finvægt + Litteratur).
  - **Cache architecture**: new directory `scripts/cache/danskmoent/galster/` with file pattern `{ruler}g{N}.json` (e.g. `c2g37.json`, `f1g46.json`, `nc2g164.json`). Separate from `scripts/cache/hede/` because the data shape differs slightly (no Zincksamlingen list).
  - **Estimated page count**: ~50-80 pages for the 1514-1541 window.
  - **Tooling**: extend existing `scripts/fetch_hede.py` / `parse_hede.py` patterns; the data shape is similar enough that a parameterised parser is feasible.

### Tier 3 — Numista Chrome MCP cross-validation (LAST per user direction)

  - Browse the Denmark catalog page 1 (covers all pre-1541 entries — already done in this session).
  - For each Numista entry, capture the photo + per-specimen brutto + ucoin/Schou/Sieg/Galster/Fr cross-refs as `measurement_alts` on the corresponding curated entry from Tier 1 or Tier 2.
  - **No Numista API calls** — Chrome MCP only per user direction.
  - **Estimated page-fetch count**: ~50 pre-1541 entries × 1 fetch each = ~50 Chrome MCP navigations.

### NOT in this plan

  - Schou 1926 scan ingest — defer (cross-references sufficient via Galster + Bruun).
  - Sieg / Jensen-Skjoldager paper monographs — defer (not online).
  - ucoin / numismaster — deprioritised (limited pre-1541 value).
  - Münzkabinett Berlin IKMK harvest — defer to a future session as enrichment (specimens already covered via Numista's CC BY-SA 4.0 photo credit chain).

## Verification gaps still open

  - **Sieg-Møntkatalog 1957 vs current edition** — what's the latest edition + price? Affects whether project should consider buying a copy.
  - **Sømod numbering** scope — covers how many pre-1541 types? danskmoent.dk Sømod column on `c2galst.htm` suggests ≥21 entries; full count needs `f1galst.htm` + Christian III scope check.
  - **Christian III pre-1541 Galster pages** — without a `c3galst.htm` index, the per-coin pages need to be discovered via reign-overview `c3.htm` or per-Galster# brute-force enumeration (Galster 92-130 range covers Grevens Fejde + 1541+ per Bruun cross-refs).
  - **Internet Archive Schou 1926 confirmed scan URL** — needs specific Archive.org search.
  - **Jensen-Skjoldager 2017 vs 2021** distinction — the 2021 «Tronraneren» is confirmed; a 2017 earlier work is referenced on Bruun lots («Jensen-Skjoldager-L-01») but its title is uncertain.
  - **Nationalmuseet i København online catalog** URL pattern + structured-data accessibility — needs separate verification pass.

## Definition of done — assessment

§BJ closure criteria from the original TODO entry:

  - (a) per-source coverage assessment for ~5+ candidate sources — **DONE (14 sources covered)** ✓
  - (b) sample-coin data-shape comparison across sources — **DONE (Wilcke vs Galster vs Numista shown)** ✓
  - (c) recommendation for which source(s) §AZ should ingest — **DONE (Tier 1-3 plan above)** ✓
  - (d) MB# identification resolved — **DONE (Swedish-specific, not Münzkabinett Berlin)** ✓
  - (e) Christian II Galster URL pattern at danskmoent.dk identified or ruled out — **DONE (`c2galst.htm` + `chr/c2g<N>.htm` confirmed)** ✓
  - (f) Numista inventory snapshot preserved for future-session reference — **DONE (in §BJ TODO body)** ✓

§BJ ready to close. §AZ now has concrete architecture: Tier 1 (Bruun + Wilcke local), Tier 2 (danskmoent.dk Galster harvest with new `scripts/cache/danskmoent/galster/`), Tier 3 (Numista Chrome MCP enrichment).
