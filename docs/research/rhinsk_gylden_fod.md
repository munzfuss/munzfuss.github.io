# Rhinsk-Gyldenfod — the Danish Rhenish-gulden gold standard

> **Quick-reference dossier** for the `rhinsk_gylden_fod` Müntzfuß and,
> crucially, for telling the Danish **Rhinsk Gylden** (Rhenish, .75) apart
> from the **Ungersk Gylden / Dukat** (Hungarian, .986 → `reichsdukatenfuss`).
> Built 2026-06-12 after two specimens (Hans ~1497 N#355730, Frederik I 1527
> Galster 59) were found misrouted to `reichsdukatenfuss` because Numista's
> generic "Goldgulden" label hides the fineness distinction.
>
> Ordinance-level spec TABLES (Bruttovægt / Finvægt / stkr-per-mark for each
> issue) live in [`research/wilcke_1514_1541_specs.md`](research/wilcke_1514_1541_specs.md)
> §1-2 — this doc does NOT duplicate them; it adds the standard's definition,
> the classification method, the coinage chronology, and the sources.

## 1. The standard (academic source of record)

**Rhinsk Gylden = 18 Karat (.750) · 72 Stück je Cöllnische Marck rauh ·
3,249 g rauh / 2,437 g fein.** A trade-gold coin of the **Rhenish-Gulden
(Rheingulden) tradition** for the German / north-German market — distinct
from the higher-fineness Hungarian Dukat.

Source of record — **Wilcke 1950** (J. Wilcke, *Renæssancens Mønt- og
Pengeforhold 1481-1588*, København 1950; local cache
`scripts/cache/wilcke/renaessancens_moent_1950/pages/wilcke_7-*.txt`):

- **Frederik I Møntordning, 25 February 1524**, Wilcke **7-2 p. 184**,
  verbatim: «*Vi Fr. … at slaa, i Guld: Nobler (… 23½ Karat … 16 Stkr.),
  **Rinske Gylden (18 Karat, 72 Stkr.)** …*». → refs_pool key
  `wilcke-rhinsk-gylden-1524-standard`.
- **Christian II Møntordning, Sommeren 1514** (Dines Blicher Brev, Malmö),
  Wilcke **7-2 p. 152-153**: Rhinsk Gylden already listed at 72/Mark, 18
  Karat, .750. (Spec table in `wilcke_1514_1541_specs.md` §1.)
- Wilcke 7-2 p. 362-367 derives the fineness explicitly: «*… Gyldenens
  Finhed er derfor slet og ret 18 Karat*».
- Metric anchor: **Wormser Reichsabschied 1495** (Imperial Rhenish-Gulden
  norm, 770 ‰) — cited in the fuss prose as `denmark-ref29-no-url`.

## 2. Rhinsk vs Ungersk — the discriminator is FINENESS, not weight or name

| | **Rhinsk Gylden** (rhinsk_gylden_fod) | **Ungersk Gylden / Dukat** (reichsdukatenfuss) |
|---|---|---|
| Tradition | Rhenish (Rheingulden) | Hungarian-Venetian ducat |
| Fineness | **18 Karat = .750** | **23 Karat 8 Grän = .986** |
| Stk / Cölln. Marck | 72 | 67 |
| Brutto / Fein | 3,249 g / 2,437 g | 3,49 g / 3,44 g |
| Imperial codification | Wormser Rezeß 1495 | Augsburger Reichsmünzordnung 1559 |

The weights overlap enough (~3.2 vs ~3.5 g) that **weight alone does not
decide** a worn specimen; **fineness is the clean discriminator**, and
Numista's generic **"Goldgulden"** label does NOT carry it. **Do not route
a Danish gold gulden by the Numista name** — use the per-coin
**Galster / danskmoent** classification, which states "Rhinsk" vs "Ungersk"
explicitly. This is the trap that misrouted N#355730 and Galster 59.

**Classification recipe** (for the open ~58-coin seed_unsorted gold sweep):
1. Find the coin's **Galster** number (catalog.galster + galster_volume).
2. Open its danskmoent page (`danskmoent.dk/fr/<volume><number>.htm`, e.g.
   `hg27`, `f1g59`, `f1g46`) — the title says «… Rhinsk gylden» or
   «… Ungersk gylden».
3. Cross-check fineness if given: .75 → Rhinsk; .986 → Ungersk.
4. Route: Rhinsk → `rhinsk_gylden_fod`; Ungersk/Dukat → `reichsdukatenfuss`.

## 3. Danish Rhinsk Gylden coinage chronology (who struck it, with Galster)

| Ruler | Year | Galster | Note |
|---|---|---|---|
| **Hans** | **~1497** (undated) | **27A / 27B** | Malmø/København; «den ældste [guldmønt] i Skandinavien» — oldest gold coin in Scandinavia; struck for mercenary pay in the Sten-Sture war. N#355730, Sieg 10, Schou 1-7, Fr 4. |
| Frederik I | 1527 | 59 | Malmø, mintmaster Jørgen Kock. Sieg 35, Schou 1-3, Fr 10. |
| Christian III | 1536 (Roskilde) | 131 | danskmoent corrects Galster's "Gottorp" → Roskilde; .764. |
| Christian III | 1546 (Flensburg) | — | Hede c3h14/c3h15 (1 + 2 Rhinsk Gylden), .75; mintmark Reynold Junge. |
| Frederik II | 1563-1564 | — | Hede f2h3 / f2h6, .77, standardisation; 2,501 g fein. |
| Christian IV | 1625-1632 | — | Hede c4h29 (1625/27/28/32), .76 (wartime); end of the line. |

So the standard runs **~1497 (Hans) → 1632 (Christian IV)** with hiatuses;
Hans ~1497 is the documented start (corrected 2026-06-12 from the earlier
"Frederik I 1527" and the still-earlier wrong "reichsdukatenfuss de-facto
1481" that actually cited this Rhinsk coin).

## 4. The parallel Ungersk / Dukat line (for contrast → reichsdukatenfuss)

| Ruler | Year | Galster | Note |
|---|---|---|---|
| Christian II | 1513 | c2g-89 / c2g-90 | 1 + 2 Ungersk gylden — **earliest documented Danish Ungersk** = the reichsdukatenfuss de-facto anchor. |
| Frederik I | 1531 | 46 | «Ungersk gylden», .986, 3.49 g (danskmoent f1g46). |
| Christian III | 1557 | — | Hede c3h1 / c3h2 (1 + 2 Ungersk Gylden), København. |

De jure imperial codification of the Ungersk/Dukat standard: **Augsburger
Reichsmünzordnung, 19 August 1559**.

## 5. Sources

- **Wilcke 1950**, *Renæssancens Mønt- og Pengeforhold 1481-1588* — ch. 7-1
  (Kong Hans, 1481-1513), 7-2 (Christian II + the 1514/1524 ordinances).
  Local cache `scripts/cache/wilcke/.../wilcke_7-{1,2}.txt`; PDFs at
  `danskmoent.dk/pdf2/Wilcke%207-{1,2}.pdf`. The 1524 standard quote is
  7-2 p. 184.
- **danskmoent.dk** per-coin pages — the authoritative Rhinsk-vs-Ungersk
  label: `fr/hg27.htm` (Hans Rhinsk), `fr/f1g59.htm` (Frederik I 1527
  Rhinsk), `fr/f1g46.htm` (Frederik I 1531 Ungersk), `chr/c3h15.htm`
  (Christian III 1546 Rhinsk). refs_pool keys
  `danskmoent-hans-rhinsk-gylden-1497`, `danskmoent-f1-rhinsk-gylden-1527`,
  `danskmoent-c3-rhinsk-gylden-1546`.
- **Galster**, *Unionstidens Udmøntninger* — the catalogue whose numbering
  (hg = Hans, f1g = Frederik I, c2g = Christian II, c3g = Christian III)
  fixes each coin's Rhinsk/Ungersk identity.
- Ordinance spec tables: [`research/wilcke_1514_1541_specs.md`](research/wilcke_1514_1541_specs.md) §1-2.

## 6. Known stale references to fix

- `docs/research/denomination_lineages.md` (≈L88-89, L143-155) still calls **Hans's
  1481-1513 gold "Ungersk Gylden (~3,49 g fein, .986)"** and uses it as the
  Goldgulden→Reichsdukat pattern exemplar. Per this dossier that is the
  **Rhinsk** coin (.75); the Ungersk exemplar should be Christian II 1513.
  Update when that doc is next touched.
