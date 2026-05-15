# Denmark-track Müntzfüße — preliminary year boundaries (1497–1873)

> **⚠️ STATUS: PRELIMINARY, NOT FULLY VERIFIED.**
>
> The dates collected below are the result of a **single-session
> reconnaissance pass** (2026-05-15 + 2026-05-16 extensions) drawing
> on our research dossiers (`moentordning_1541.md`,
> `christian_iii_danish_coinage_1534_1572.md`,
> `danish_royal_gold_1560_1648.md`), the Wilcke 1950 local cache,
> Numista catalog browsing via Chrome MCP, and a handful of targeted
> web fetches against danskmoent.dk and Wikipedia DE/DA.
>
> **Anchor-decision note 2026-05-16 (per §BI)**: the Denmark-track
> project anchor moved from 1541 to **1514** (Christian II Lovkompleks
> per Wilcke 1950 p. 183-186 verbatim). This file's per-Fuß
> boundaries continue to reflect the historical first-mintage / first-
> ordinance dates as documented — but the **project's lower-bound
> anchor** is now 1514 across CLAUDE.md mission, `denmark.yml`, seed
> builder, etc. Müntzfüße whose start predates 1514 (Rhinsk Gylden,
> Nobel/Guldreal) remain documented here for the Hans-era context but
> sit outside the project's data-coverage window.
>
> **No date below is yet binding.** Each Müntzfuß needs its OWN
> dedicated verification pass — opening the primary ordinance text,
> cross-checking against ≥2 independent secondary sources, surveying
> the cessation evidence (decree vs last mintage vs withdrawal-from-
> circulation), and resolving any ambiguity exposed by the cross-check.
>
> Until that per-Fuß verification lands, **treat these dates with
> suspicion**. Use them as starting hypotheses, not as facts.
> Specifically:
>
> - Do NOT inline-cite this file from rendered prose (`data/**/*.yml`)
>   or production artefacts. It is research-track-only scratchwork.
> - Do NOT promote any date here to a `year_from` / `year_to` field
>   on a Fuß definition or phase block without the per-Fuß
>   verification pass.
> - When the verification pass for a given Fuß completes, update this
>   file with the verified dates + the new source chain, and ADD a
>   per-Fuß «verified YYYY-MM-DD» marker. Dates without that marker
>   remain provisional.
>
> Verification confidence per entry (start / end) is marked at the
> bottom of each card: **HIGH** = anchored in a named primary
> ordinance + verbatim quote; **PROBABLE** = supported by secondary
> consensus but no primary anchor; **UNCERTAIN** = single-source or
> inferred.
>
> ---

## Context

These five Müntzfüße are the proposed coverage set for the
**1541–1566 Denmark-track gap** (TODO §BF, opened 2026-05-15 with
Highest-priority marker). They are:

  - **`dalerfod`** — Christian III's silver-Daler standard
  - **`flensborg_fod`** — Christian III's Schleswig-Holstein Lybsk-zone
  - **`rhinsk_gylden_fod`** — Imperial Reichsgulden imitation, Hans → C-IV
  - **`f2_guldkrone_fod`** — Frederik II 1563–64 French écu d'or imitation
  - **`reichsdukat`** (existing `reichsdukatenfuss`) — Reichsdukatenfuß in Denmark

The session also reached a per-Fuß **for / against** verdict on
treating `flensborg_fod` as a Müntzfuß separate from `dalerfod`
(rather than as a phase within it) — for 8 / against 4 → recommend
separate. That analysis is captured in this session's chat
transcript and summarised at the end of this file.

---

## 1. `dalerfod` — Christian-III-Dalerfod (silver Daler standard)

| Boundary | Year | Type | Source |
|---|---|---|---|
| **Start** | **1541** | Legal (Møntordning) | **Møntordning af 20. september 1541** (Christian III) + companion **Forordning «Om Maal og Vægt» af 20. marts 1541**. Rigsarkivet T.K. nr. 160 pp. 16–22; Wilcke 1950 ch. IV pp. 4–13 verbatim. |
| **End** | **1582** | Legal (Møntordning — superseded) | **Møntordning af 12. januar 1582** (Frederik II). Reset 1 Daler = 3 Mark Danske → 1 Daler = 4 Mark. Wilcke 7-6 p. 33: «*Allerede 12. Januar 1582 foreligger Kongens Afgørelse … befaler Kongen følgende Mønter*»; Galster (galshist.htm): «*vende tilbage til 'mønten, som før gik' og dele daleren i 4 mark*». |

**Confidence: start HIGH, end HIGH.**

**Important context:** the 1572 «Elfsborgs løsen» Speciedaler (f2h17)
is a SYMBOLIC first specie strike toward imperial 9-Fuß alignment
under Frederik II, but the Danish realm-standard formally remained
on dalerfod metrics until the 1582 Møntordning. The Augsburger
Reichsmünzordnung 1559 and the Reichsmüntz-Abschied 1566 are
imperial acts that did NOT supersede dalerfod in Denmark — they
governed the empire, while Denmark continued on its own track.

**Verification gaps:**
  - The 1582 ordinance text itself has not been read in primary form
    (we have Galster's paraphrase + Wilcke 7-6 p. 33 commentary).
  - The phase-A2 1544 debasement (mf 9.481) is sometimes cited as a
    separate «Forordning af 27. september 1544» — that secondary
    document needs its own primary-source verification.

---

## 2. `flensborg_fod` — Christian-III Schleswig-Holstein Lybsk-zone

| Boundary | Year | Type | Source |
|---|---|---|---|
| **Start** | **1547** | Legal (Bestalling) | **Bestalling og Møntordning af 22. januar 1547** for Jørgen Kock the Younger as Flensborg mintmaster. Rigsarkivet T.K. nr. 160 pp. 28–29; Wilcke 1950 pp. 25–26 verbatim. Establishes parallel dual-zone: Daler finhed 14¼ Lod (890,625 ‰), sub-Mark in Lybsk ß «als Hamburg, Lübeck und Lüneburg». |
| **End** | **1571** | Mint closure (de facto) | Permanent closure of the Flensborg royal mint. Galster (galshist.htm): «*blev slået skillinge og søslinge fra 1566 til 1571, da mønten blev nedlagt for stedse*» — "closed permanently". |

**Confidence: start HIGH, end PROBABLE.**

**Alternative start consideration:** 1545 (opening of the Flensborg
mint under Jørgen Degener, with Tyde Knipensen as kautionist for
2000 Gylden working capital). Recommend 1547 as the legal start of
the dual-zone Fuß proper; the 1545 opening predates the formal
Bestalling.

**Important continuity note:** the structural Lübisch-zone lineage
continues through Hertug Adolph's Gottorp duchy mint (1544+), then
re-codified by Christian V (1671) → 22.04.1726 Hamburg-Lübeck-
Schleswig 34-Marck-Fuß → 1813 Rigsbankforordning crystallizes the
18½-Thaler-Fuß. These successor standards are SEPARATE Müntzfüße,
not extensions of `flensborg_fod`. This Fuß ends with the Flensborg
mint closure 1571.

**Verification gaps:**
  - Did Hertug Adolph's Gottorp mint continue striking at the same
    14¼-Lod / 24-ß-Lybsk standard 1572–1580? If yes, the de facto
    end of «Christian-III-Flensborg-fod» persists past the royal
    mint closure as a ducal-zone standard, and our Fuß's `year_to`
    might need extension.
  - The 1547 Bestalling text has been read via Wilcke 1950
    secondary capture — primary manuscript at Rigsarkivet T.K. nr.
    160 pp. 28–29 (we have the cached scans, not yet OCR'd for the
    full text).

---

## 3. `rhinsk_gylden_fod` — Imperial Reichsgulden / Rhenish Gulden imitation in Denmark

| Boundary | Year | Type | Source |
|---|---|---|---|
| **Start** | **1497** | Legal (Møntordning, Danish-side) | **Møntordningen af 4. december 1497** under Kong Hans, authorising «pa Rinske Gylden slagh» at 17–17¾ karat. Wilcke 7 (danskmoent.dk/wilcke/w7hans.htm): «*Kong Hans mønte ret rhinske Gylden*». Foreign model: 1490 Rhenish Princes' Gulden (4-elector Münzverein, 71⅓ pieces per Cölln. Mark, 18½ karat). |
| **End** | **1632** | Last attested mintage (no formal cessation) | Last Christian IV Rhinsk Gylden strike. Galster (galsfre2.htm): «*Endelig lod Christian IV ved sin indtræden i kejserkrigen 1625 og derefter 1627, 1628 og 1632 slå rhinske gylden, ialt henved 35.000 stk.*» Practice ceases after 1632 with the de facto end of the imperial Reichsgulden tradition during the Thirty Years' War. |

**Confidence: start HIGH, end HIGH.**

**Important coverage breakdown** (intermittent strikes over 135 years):

  - 1497 Hans (Møntordning 4 Dec, Swedish-campaign batch ~150 000 stk per Hvitfeldt)
  - ~1500 Hans (Ditmarsken war additional batch)
  - 1500–1533: gap (no Rhinsk Gylden under Christian II or Frederik I in Hede cache — possible Reformation-era gap, possible cataloguing gap; open research item)
  - 1546 Christian III (Flensborg, 0.750 finhed — pre-Augsburger sub-standard)
  - 1563–64 Frederik II (København, 0.770 — par-Ferdinand 1559)
  - 1584 Frederik II (Frederiksborg, specs not in cache — confirms post-Augsburger continuation)
  - 1625, 1627, 1628, 1632 Christian IV (København, 0.760 — kejserkrigen finance)

**Verification gaps:**
  - The 4 December 1497 Møntordning text has not been read in
    primary form by this project (we have Wilcke's paraphrase via
    danskmoent.dk).
  - Pre-1497 origin point — the 1490 Rhenish Princes' Gulden vs
    earlier 14th-century Köln-Mainz-Trier Münzverein — is foreign
    background, not Danish-track. Our `year_from: 1497` should
    remain the Danish-side anchor.
  - No formal Danish cessation decree identified — assumption is
    that the Thirty Years' War (1618–1648) collapsed the imperial
    framework that gave the Rhinsk Gylden its legitimacy.

---

## 4. `f2_guldkrone_fod` — Frederik II 1563–64 French écu d'or imitation

| Boundary | Year | Type | Source |
|---|---|---|---|
| **Start** | **1563** | First mintage (no formal decree found) | Bremerholm goldsmith-workshop initiative under mintmasters Hans Willers, Hans Köpelin, Laudris Hammer. danskmoent.dk/f2flens.htm: «I GOLT GILDEN, I DOK KATE or I GOLT KRONE» — workshop branding, no separate Møntordning known. Political context: Syvårskrigen war finance (war declared 3 August 1563). Foreign model: French écu d'or per Nuremberg 1551 assay (Galster 1959, 22⅓-karat = 0.9305, 70 pieces/Cölln. Mark fein). |
| **End** | **1564** | Last mintage (no formal cessation) | Issuance discontinues as Syvårskrigen progresses. Frederik II's later 1584 gold issues (Frederiksborg-press) reintroduce Guldkrone under different metric (not continuous with 1563–64). |

**Confidence: start PROBABLE, end PROBABLE.**

**Caution — minimal Fuß construct.** Only 2 years of activity, only
2 distinct types (f2h2 1563 + f2h5 1564), no formal Bestalling
identified. Open question for the per-Fuß design pass: does this
warrant its own Fuß card, or should it sit in `seed_unsorted` with
a `historical_note: "1563-64 écu-imitation phase, no surviving formal
ordinance"`? Decision deferred to §BF implementation queue when this
specific Fuß comes up for handling.

**Verification gaps:**
  - No archival search yet for any Bremerholm workshop authorisation
    document. Possible that an order from the Rentekammer / Danske
    Kancelli authorised the workshop's gold-coin production for war
    finance, but no such document has been located.
  - Galster 1959 (*Danske efterligninger af fremmed mønt fra nyere
    tid*, Nationalmuseets Arbejdsmark, p. 108) is the secondary
    anchor for the French écu d'or model identification — needs
    primary verification.

---

## 5. `reichsdukat` / `reichsdukatenfuss` — Reichsdukatenfuß in Denmark

**Start verified 2026-05-15 → re-anchored 2026-05-16** (per §BI Denmark-track anchor decision).

| Boundary | Year | Type | Source |
|---|---|---|---|
| **Start (project anchor 2026-05-16)** | **1514** | First formal Danish gold-standard spec (Lovkompleks) | **Christian II Møntordning af Sommeren 1514** (Wilcke 1950 p. 183-186 verbatim) — Dienis-Malmö-Brev specifies **Nobler 23½ Karat 16 Stkr./Marken + Rhinsk Gylden 18 Karat 72 Stkr./Marken**, with Rigsrådets Raad og Samtykke. First formal Danish gold-fineness law. The Nobler at 23½ Karat = 0.979 fineness establishes the ≥23-Karat upper-band that the later Reichsdukatenfuß coins (.986) adhere to. The 1514 Nobler is DOUBLE-noble weight (~14.6 g brutto at 16/Mark) — not yet a single-Goldgulden, but the fineness anchor of the Reichsdukatenfuß family is set here. |
| (Earliest single-Goldgulden, finhed UNVERIFIED) | **1481–1513** | First Danish «Goldgulden» catalog entry — predates 1514 anchor | **John I (Hans) Goldgulden** (Numista N#355730, Fr# 4), ND 1481–1513, brutto 3.3 g, finhed NOT recorded. Legend «MONET AVREA REGNI DACIE». **Sits outside the 1514 project anchor** — Hans-era context only, not in project data window. |
| (Earliest single-Goldgulden, post-anchor) | **1527** | Frederik I 1 Goldgulden Malmö — finhed not recorded | Numista N#433743, Fr# 10, brutto 3.28 g, mint Malmö, legend «MON AVR MAL 1527». First post-1514 single-Goldgulden in Denmark, but Numista records no fineness. UNVERIFIED metric. |
| **First verified .986 strike** | **1531** | First Danish mintage at the verified Reichsdukatenfuß metric (verified .986) | **Frederik I 1531 Ungersk Gylden** (Galster 46 / Schou 1 / Jensen-Skjoldager T-41/45), brutto 3.49 g, finhed 0.986 (23⅛ K), fein 3.44 g, mint København or Malmø. Source: danskmoent.dk/fr/f1g46.htm + Numista N#428864 (Fr# 11, Galster UU# 46). lex.dk «dukat» (Jørgen Steen Jensen, Nationalmuseet): «*I Danmark kom der første gang i 1531 en guldmønt af vægt som en dukat*». First single-Goldgulden in Denmark at canonical Reichsdukatenfuß metric. |
| **End** | **1802** | Last Danish mintage | Last Altona Reichsdukat per Galster (galsfre2.htm): «*den sidste 1802*». Final Altona issues: 1791, 1792, 1794, 1802. Last København Kurantdukat (21-karat variant): 1785. |
| (External anchor) | (1871 / 1873) | Imperial / Danish reform | Imperial: Münzgesetz 4 December 1871 (Reichsgoldmark introduction). Danish: Møntloven af 23 May 1873 (gold-Krone reform, effective 1 January 1875). Denmark ceased Reichsdukat mintage 71 years before the 1873 Krone reform. |

**Confidence: start HIGH** (Christian II Lovkompleks 1514 — Wilcke 1950 verbatim primary citation, per §BI anchor decision); **first verified .986 HIGH** (Frederik I 1531 Galster 46); **end HIGH** (last Danish strike documented).

**Note on 1514 vs 1531 distinction**: 1514 is the **legal anchor** (Christian II ordinance sets the 23½K-fineness floor and authorises Goldgulden / Nobler / Rhinsk Gylden mintage). 1531 is the **first verified .986-finhed Goldgulden strike**. Both are Reichsdukatenfuß-class — 1514 establishes the legal framework, 1531 is the first specimen-attested coin at the canonical 67/Mark fein metric. The project's data-window opens at 1514 per §BI; the project's earliest curated coin would be the 1531 Frederik I Goldgulden — subject to §AZ Galster + Jensen-Skjoldager catalog import landing. Until §AZ lands, the project's earliest Hede-cached entry is c3h1 1557 (Hede 1957 monograph itself does not cover pre-Christian-III rulers).

### Pre-1557 verification (added 2026-05-15)

Initial pass (this file's original draft) listed **1557** as the start year, based on the project's Hede cache. User pushback: «*чи покривають ті роки наші дані?*» triggered a deeper search that surfaced the earlier Frederik I 1531 issue catalogued by Galster 46 — outside Hede 1957's own scope (Hede 1957 starts at Christian III; pre-Christian-III rulers are catalogued separately in Galster 1959-1960 + Jensen-Skjoldager 2021, sibling §AZ).

**Pre-1531 evidence (none at Reichsdukatenfuß metric — HIGH confidence):**

| Ruler | Year | Coin | Brutto g | Finhed | Standard family |
|---|---|---|---:|---:|---|
| Kong Hans | 1496 | Dobbeltnobel/Guldreal | ~15 | 0.995 (23⅞ K) | English Sovereign / Maximilian-I-Großgulden |
| Kong Hans | ~1497–1500 | Rhinsk Gylden | 3.249 | 0.750 (18 K) | Rhenish Gulden tradition — dukat *weight*, NOT dukat fineness |
| Christian II | ~1514 | (Db.) Guldreal | 14.616 | ≈0.958 (23 K) | Sovereign metric |
| Frederik I | 1524 | (Db.) Nobler | 14.616 | 0.979 (23⅛ K) | Dukat fineness at DOUBLE-noble weight — not a Reichsdukat |
| Frederik I | 1527 | Rhinsk Gylden (Malmø) | 3.249 | 0.750 (18 K) | Rhenish — fineness too low |
| **Frederik I** | **1531** | **Ungersk Gylden (København or Malmø)** | **3.49** | **0.986 (23⅛ K)** | **Reichsdukatenfuß — exact** |
| Frederik I | 1531 | Rhinsk Gylden (Gottorp) | 3.249 | 0.750 (18 K) | Rhenish — fineness too low |
| Frederik I | 1532 | Nobel | ~7.78 | ~0.979 | Dukat fineness at half-noble weight — not a Reichsdukat |
| Christian III | 1557 | Ungersk Gylden (c3h1) | 3.49 | 0.986 | Reichsdukatenfuß continuation |

**Pre-Hans rulers** — Christopher of Bavaria (1440–1448) and Christian I (1448–1481): no gold issues documented in any source consulted. The 41-year gap 1440–1481 has zero attested Danish royal gold mintage.

**Erik VII (Erik of Pommern, 1397–1439) — NEW finding 2026-05-15** (correcting earlier dossier claim that «*no gold under Erik of Pomerania*»):

| Parameter | Value |
|---|---|
| Issuer | Denmark · Eric VII (Erik of Pommern) (1397–1439, Kalmar Union) |
| Mint | **Lund** (legend «HONETA LVNDENS») |
| Years | ND 1397–1439 |
| Weight | **9.85 g** |
| Diameter | 23 mm |
| Fineness | Not recorded by Numista — UNVERIFIED |
| Catalog refs | Numista N#426966, NO Friedberg# (outside the standard catalog) |
| Photo source | Nationalmuseet i København (CC BY-SA 4.0) |
| Obverse legend | «ERICVS REX D S N» (Erik King of Denmark / Sueciae / Norvegiae — invokes Kalmar Union) |
| Reverse legend | «HONETA LVNDENS» (Lund Mint) |

**Metric classification** — 9.85 g does NOT match any standard XV-c. gold denomination:
  - NOT Reichsdukatenfuß / Florentine fiorino (~3.5 g)
  - NOT English Noble (~7.78 g) or Sovereign (~15 g)
  - NOT Rhenish Gulden (~3.25 g)
  - Likely a sui-generis Kalmar-Union-period Danish gold piece, possibly ~3× Goldgulden equivalent or a «Storgylden» Lund-mint denomination. Galster's Lund-mint volume would be the primary attestation; absence of Friedberg# suggests rarity and likely unique-specimen status in the Nationalmuseet i København cabinet.

**Implication for the project**: Erik VII is the **earliest documented Danish royal gold issuer**, predating Hans (1481–1513) by 42–82 years. Wilcke 1950's framing of Hans as «første Møntreformator» on gold was a **synthesis simplification**, not a primary-source-attested statement of Hans-as-first. Numista's catalog cross-checked against Nationalmuseet attribution gives the Erik VII Lund issue clear standing as an earlier-than-Hans Danish gold mintage — though metric-classification remains open.

**§0b discipline note**: our previous dossiers (`christian_iii_danish_coinage_1534_1572.md` §3, `danish_royal_gold_1560_1648.md`) both repeated the «no pre-Hans gold» claim based on Wilcke alone. The claim was **hypothesis dressed as fact** — Numista + Nationalmuseet evidence falsifies it. The error is recorded here publicly per §0b discipline; companion dossiers will be updated in a follow-up commit when the per-Fuß verification pass for `reichsdukat` reaches the Erik-VII section.

### Earliest-vs-codification design question — RESOLVED 2026-05-16 via §BI

Earlier draft listed four candidates; §BI anchor decision (2026-05-16) selects **1514** as the project-wide anchor on the basis that:

- **1514** Christian II Lovkompleks is the **first formal Danish gold-standard ordinance** with Rigsrådets Raad og Samtykke. Establishes the legal framework for the entire Goldgulden / Nobler / Rhinsk Gylden lineage. Independently corroborated by Numista's currency-taxonomy boundary («Penning 825-1513 → Gulden 1513-1572»). Wilcke 1950 p. 183-186 verbatim. **PROJECT ANCHOR.**
- 1531 — first verified .986 Goldgulden strike (Frederik I, Galster 46). **First specimen-attested Reichsdukatenfuß coin in Denmark.** Sits 17 years inside the 1514 project window.
- 1557 — first Hede-cached entry (c3h1 Christian III Ungersk Gylden). **Current data-coverage start in our cache**, pending §AZ Galster + Jensen-Skjoldager catalog import (Hede 1957 itself doesn't extend earlier).
- 1559 — imperial codification (Augsburger Reichsmünzordnung). **Imperial framework**, not Danish anchor.

### Imperial vs Danish-track `year_to` decision

Project's existing bar `reichsdukatenfuss` has `year_to: 1871`
(imperial Münzgesetz anchor). This is conservative — it covers the
empire-wide formal end. Per Denmark-track logic, **`year_to: 1802`**
would be data-track-correct (last Danish strike). The choice is a
design decision pending: stick with the imperial-framework reading,
or switch to the Danish-track reading.

The current bar_title already documents the actual minting span:
«*struck in the Kingdom of Denmark into the 19th century — Copenhagen
royal mint and Altona mint (the last Holstein-side Reichsdukaten
under Christian VII, KM#650, 1791–1802) · empire-wide ends with the
Coinage Act of 4 December 1871*». If we move `year_to` to 1802, the
bar_title needs rewriting to drop the imperial-end reference.

### Verification gaps (still open)

  - **Frederik I + Christian II catalog import** (§AZ): Hede 1957
    monograph does NOT cover pre-Christian-III rulers, so this is
    not a Hede-extension task but a new-source-family import from
    Galster 1959-1960 + Jensen-Skjoldager 2021 (cited inline at
    danskmoent.dk/fr/f1g*.htm series). Adding these into the project
    cache (architecture TBD per §AZ) would let Frederik I 1531
    Goldgulden and Christian II Nobler / Db. Guldreal enter the
    curated DK table — separate data-import task, not blocking the
    `year_from: 1514` anchor decision itself.
  - **Mint distinction for the 1531 issue**: Galster does not
    cleanly separate København vs Malmø for Frederik I 1531
    Ungersk Gylden. Jørgen Koch operated Malmø; Anders Bilde
    operated København. Both are documented at the same time
    striking other gold types; the 1531 Ungersk Gylden mint
    attribution remains uncertain.
  - **No primary verification of the 1802 «last Altona Reichsdukat»
    date** — Galster is secondary. The Hede page for KM#650 would
    be the primary anchor.

---

## Summary table

| Fuß | Start | End | Duration | Start confidence | End confidence |
|---|---|---|---|---|---|
| `dalerfod` | 1541 | 1582 | 41 yr | HIGH | HIGH |
| `flensborg_fod` | 1547 | 1571 | 24 yr | HIGH | PROBABLE |
| `rhinsk_gylden_fod` | 1497 | 1632 | 135 yr | HIGH | HIGH |
| `f2_guldkrone_fod` | 1563 | 1564 | 2 yr | PROBABLE | PROBABLE |
| `reichsdukat` (project anchor, §BI 2026-05-16) | **1514** | 1802 | 288 yr | HIGH | HIGH |
| `reichsdukat` (first verified .986 strike) | 1531 | 1802 | 271 yr | HIGH | HIGH |
| `reichsdukat` (imperial-framework) | 1559 | 1871 | 312 yr | HIGH | HIGH |

---

## `flensborg_fod` vs `dalerfod` — separation analysis (session 2026-05-15)

The for / against accounting for treating `flensborg_fod` as its own
Müntzfuß rather than as a phase within `dalerfod`:

### For (8)

1. **Different mathematical constant** — mf 8.982 (Flensborg) vs mf 8.827 (Royal 1541) vs mf 9.481 (Royal 1544). These are distinct Cölnsk-Vægt formulas.
2. **CLAUDE.md §7 explicitly requires** — «*Fuesse are universal mathematical constructs: Cöllnische Marck ÷ N. The 9¼-Fuß is the same everywhere. Defined once.*» One Fuß = one formula.
3. **Different legal anchor** — Bestalling 22 January 1547 (Rigsarkivet T.K. nr. 160 pp. 28–29), separate document from the 20 September 1541 Møntordning.
4. **Different account-of-record** — Royal: 1 Daler = 3 Mark Danske = 48 ß d. Ducal: 1 Sølvgylden = 24 ß Lybsk «als Hamburg, Lübeck und Lüneburg». Two distinct monetary-accounting systems within the same kingdom.
5. **Galster directly separates them** — «*Kun gennem daleren var der fællesskab i mønt med kongerigerne*» — commonality existed ONLY at the Daler-head level; sub-denominations were separate.
6. **Different politico-economic motivation** — Royal: post-Reformation centralisation. Ducal: parity with Hansestädten after 1544 Gottorp partition. Different goals.
7. **Different mint + mintmaster lineage** — Flensborg (new mint, opened 1545) vs København (Klarekloster, Povel Fechtel). Independent mintmaster track.
8. **Genealogical root of the dualism** — per dossier §7.1, the 1547 Flensborg standard is the structural ancestor of the 18½-Th-Fuß / 34-Marck-Fuß family that formalises 1726 → 1813 Helstaten. Folding it into `dalerfod` loses the narrative thread.

### Against (4)

1. **Small data volume** — 7 seed coins for the Flensborg track. A full Fuß card with phases + hintergrund may be heavyweight for this scale.
2. **Single monarch → single political will** — Christian III signed BOTH documents (1541 + 1547). Not two competing kings, one ruler with two minted-realm domains.
3. **Shared Cölnsk-Vægt weight basis** — both standards keep the 233.856 g Cölln. Mark as denominator.
4. **Fragmentation risk** — if «different mf → separate Fuß» is applied consistently, every Forordning of 1544 (mf 9.481) should be a separate Fuß rather than an A2 phase.

### Counter-arguments to «against»

  - (1) Other Fuß cards have comparable small data: `kronemont_chr_iv` (3 types), `kronemont_fine` (~7 types). Not blocking.
  - (2) A single monarch CAN run multiple Müntzfüße simultaneously — Christian IV has Kronemønt (1618–52) + Speciedaler (1644+) + Reichsdukatenfuß (1603+) + Guldkrone (1619–48) concurrently. Precedent exists.
  - (3) Shared denominator ≠ shared numerator. Different mf values = different Fuß.
  - (4) The distinguishing criterion is type-of-change: 1544 debasement keeps the denomination (Mark Danske at 14½ → 13 Lod) → same monetary order with debasement → PHASE. 1547 Flensborg introduces a new denomination (Sølvgylden) + a new account system (Lybsk ß) → NEW Fuß.

### Verdict

For : against = 8 : 4, with arguments (2) and (8) being the
structurally decisive ones. Recommendation: **separate Fuß
`flensborg_fod`** (option (a) from §BF). User verdict to be
confirmed before data edit.

---

## Cross-references

  - **TODO §BF** — Highest priority Denmark 1541–1566 gap. This file is research input for §BF.
  - **TODO §BD** — Danish Müntzfuß names (`-fod` not `-Fuß`). Once §BD architecture lands, the file's `f2_guldkrone_fod` etc. become canonical.
  - **TODO §AV** — Guldkrone-fod design question. `f2_guldkrone_fod` interacts with this entry.
  - **TODO §AW** — Rhinsk Gylden Fuß design question. `rhinsk_gylden_fod` is the candidate from this analysis.
  - **TODO §AY** — Frederik II 3 Mark one-off (f2h8). Resolved in `danish_royal_gold_1560_1648.md` §1.4 as silver speciedaler, not gold Fuß candidate.
  - `docs/research/moentordning_1541.md` — primary dossier for `dalerfod` + `flensborg_fod`.
  - `docs/research/christian_iii_danish_coinage_1534_1572.md` — wider 1534–1572 context.
  - `docs/research/danish_royal_gold_1560_1648.md` — primary dossier for `rhinsk_gylden_fod` + `f2_guldkrone_fod` + `reichsdukat`.

---

## Next per-Fuß verification steps

For each Müntzfuß listed above, the verification pass should:

  1. **Read the start-anchor primary document** in full (Møntordning,
     Bestalling, Forordning — whichever applies). For `dalerfod`,
     this is Wilcke 7-4 (already verbatim-captured). For
     `flensborg_fod`, the 22 January 1547 Bestalling text in
     Rigsarkivet T.K. nr. 160 pp. 28–29 (cached scans available).
     For `rhinsk_gylden_fod`, the 4 December 1497 Hans Møntordning
     (only via Wilcke paraphrase so far). For `f2_guldkrone_fod`,
     search archives for any Bremerholm workshop authorisation. For
     `reichsdukat`, no Danish-side start decree expected — but
     verify Christian III had no explicit pre-1559 Ungersk-Gylden
     Bestalling.

  2. **Identify the end-anchor primary document** (cessation
     decree if one exists; last-mintage record if cessation is
     informal). For `dalerfod`: 1582 Frederik II Møntordning text.
     For `flensborg_fod`: any 1571 closure document at Rigsarkivet.
     For `rhinsk_gylden_fod`: no cessation expected; document the
     1632 last strike and the Thirty-Years-War political context.
     For `f2_guldkrone_fod`: same as above. For `reichsdukat`:
     the decision between `year_to: 1802` (Danish-track) vs `1871`
     (imperial-framework).

  3. **Cross-check against ≥2 independent secondary sources** —
     Wilcke + Galster + Wikipedia DE/DA + lex.dk where they
     overlap. Flag any inter-source date conflict for resolution.

  4. **Update this file** with the verified dates + the new source
     chain. Add a per-Fuß «verified YYYY-MM-DD» marker. Until that
     marker is added, dates here remain PRELIMINARY.

  5. **Then promote** to `year_from` / `year_to` fields on the
     Müntzfuß definition or phase block in `data/shared/fuesse.yml`
     and `data/locations/denmark.yml`.
