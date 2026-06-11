# `nobel_fod` — the Danish gold Nobel standard (1496–1532): confirmed-source dossier

> **Status:** internal research dossier for future sessions. Every datum here is
> sourced (citation inline). NO invented data (§0). Where a figure is uncertain
> in the sources, that uncertainty is stated, not papered over. Compiled
> 2026-06-05 from internal project sources (Wilcke 1950 transcript, danskmoent
> deep-page cache) + web sources (Galster via danskmoent.dk, Numista, Stack's
> Bowers/NumisBids, da.wikipedia). Supersedes nothing — complements the fuss card
> `data/shared/fuesse.yml::nobel_fod` and the lineage note `docs/denomination_lineages.md`.
>
> **One-line summary:** the Danish Nobel is a heavy gold *Pragtmünze* (prestige
> coin, NOT circulation money) struck 1496–1532 by three kings, modelled — per
> Galster — NOT on the English Noble but on the **Dutch *groote gouden reaal* of
> 1487**. Its exact fineness is not firmly attested (Galster: «*maaske ogsaa i
> Finhed*» = "perhaps also in fineness"); the documented figures span **.9583
> (23 Karat, 1524 ordinance) — .979 (23½ Karat, 1514 ordinance + 1532 specimens)**,
> with the Dutch model nominally 24 Karat. The `.986` figure currently in the
> fuss card is the **Reichsdukat** gold standard (23 Karat 8 Grän), NOT the
> Nobel's — a mis-anchor (see §5).

---

## §1. The coins — type list (Galster / Schou)

Per **danskmoent.dk «1 Nobel»** (Hede/Galster overview, <https://www.danskmoent.dk/1nobel.htm>),
three rulers struck the Nobel across 36 years at three mints (primary Malmø;
secondary København, Ribe):

| Ruler | Year(s) | Mint | Galster | Schou | Note |
|---|---|---|---|---|---|
| **Hans** (1481–1513) | 1496 | Malmø / København | 24 | 2–3 | first Danish gold coin; first dated Danish coin |
| Hans | 1502 | Malmø / København | 24 | 2–3 | |
| Hans | *1508* | — | 24 | 2–3 | **flagged a forgery on the source page — NOT a genuine type** |
| **Christian II** (1513–1523) | 1516 | Malmø | 37 | 1 | |
| Christian II | 1518 | Malmø | 37 | 1 | |
| **Frederik I** (1523–1533) | 1532 | København / Malmø | 45 | 1 | first queen-portrait on a Danish coin (Jensen/Skjoldager T-91/96) |
| Frederik I | u.år (undated) | Ribe | 68 | 3, 4 | two inscription dies (var. A = Schou 3, var. B = Schou 4) |
| Frederik I | u.år (undated) | Ribe | 69 | 1 | «unik»; known mainly through cast (sølv) copies |

- Larger denominations exist for Hans: **2 Nobel** (Galster, Numista N#428886, 1502) and **3 Nobel** (Numista N#428914, 1496). No separate fineness is documented for the 2-/3-Nobel — they are weight multiples of the 1-Nobel (see §3). Source: Numista <https://en.numista.com/catalogue/danemark-1.html>.
- After 1532 no further Nobel coinage is documented; Christian III did not continue the line. The name later shifts: **«Senere ændredes betegnelsen til Rosenobel»** ("later the designation was changed to Rosenobel") — danskmoent.dk/1nobel.htm. The Rosenobel (Frederik II 1584 + Christian IV 1611–1629) is a SEPARATE Müntzfuß (`rosenobel_fod`, fineness .833) — see `docs/research/danish_royal_gold_1560_1648.md` §3.4 and `docs/denomination_lineages.md`. Do NOT conflate.

---

## §2. Origin & model — NOT the English Noble (Galster)

The most important correction the sources make against the common assumption:

> **«De har intet tilfælles med de engelske Noble (Rosenoble); men de svarer i
> Præg, Vægt og maaske ogsaa i Finhed nøje til den store Guldreal (groote gouden
> reaal), som 1487 prægedes i Holland.»**
> — Georg Galster, *Unionstidens Udmøntninger* (Danmarks Mønter), via
> <https://www.danskmoent.dk/galster/galkult.htm>

("They have nothing in common with the English Noble (Rosenoble); but they
correspond in design, weight and **perhaps also in fineness** closely to the
large gold real (groote gouden reaal), struck in Holland in 1487.")

- The Dutch model (*groote gouden reaal*, 1487): «**udmøntet af 24 Karat fint
  Guld, 16 1/2 paa en troysk Mark**», «**skulde veje 14,9g**» — i.e. 24-carat
  fine gold, 16½ to a troy mark, intended weight 14.9 g (same source).
- The name «Nobel» is «efter det ædle Metal» (after the noble metal):
  «*De smukke, anselige Noble, der bærer Aarstallet 1496, fik deres Navn efter
  det ædle Metal*» (galkult.htm).
- **Caveat on the conflicting «English model» claim.** Several tertiary sources
  (da.wikipedia «Nobel (mønt)», auction copy) say the Danish nobel imitated the
  English Noble/Rosenoble. Galster — the authoritative catalogue — explicitly
  REJECTS this («intet tilfælles med de engelske Noble») in favour of the Dutch
  *groote gouden reaal*. Prefer Galster; the «English model» line is the popular
  shorthand. (Both agree the *name* «Nobel» derives from the English coin's name.)

---

## §3. The standard — fineness, weight, mark divisor

**The fineness is the genuinely uncertain part — and the sources say so.** Galster
hedges («*maaske ogsaa i Finhed*»). The documented figures, by source:

| Fineness | = Karat | Source / context | Citation |
|---|---|---|---|
| ~1.000 (24 Karat) | 24 Karat | the **Dutch model** (groote gouden reaal 1487) the Danish nobel copies «perhaps also in fineness» | Galster, galkult.htm |
| **.979** | **23½ Karat** | **Christian II 1514 Møntordning** (Sommeren 1514, Dienis Blicher Brev, Malmø) — Nobel 16/Cölln. Mark, brutto 14.616 g, fein 14.310 g | Wilcke 7-2 (1950) p.152-153, via Suhm + Rigsarkivet T.K. — transcript `docs/research/wilcke_1514_1541_specs.md` |
| **.9583** | **23 Karat** | **Frederik I 1524 Møntordning** — «(Db.) Nobel» 16/Cölln. Mark, brutto 14.616 g, fein 14.007 g | Wilcke 7-2 (1950), same transcript |
| **.979** | 23½ Karat | **1532 specimens** (Galster 45 København/Malmø + Galster 69 Ribe) — danskmoent deep pages: «Bruttovægt 14,375g, Finhed 0,979, Finvægt 14,08g» | danskmoent.dk/fr/f1g45.htm + /fr/f1g69.htm (parsed cache `scripts/cache/danskmoent/galster/fr_f1g45.json`, `fr_f1g69.json`); corroborated by Numista N#428544 «Gold .979» |

**Reading of the fineness spread:** the standard drifts ~24K (Dutch model) → 23½K
(.979, 1514) → 23K (.9583, 1524) → back to .979 (1532 specimens). The
`wilcke_1514_1541_specs.md` note (line ~113) reads the 1532 .979 as «between the
1524 23-Karat (.958) and the 1531 23⅛-Karat (.986) figures — suggests intermediate
refinement attempt». Net: there is **no single fixed Nobel fineness** in the
sources — a range, which the fuss card honestly flags «ungewiß».

**Weight (brutto / fein), 1 Nobel:**
- Wilcke ordinance Soll: **14.616 g brutto** (= 233.856 / 16, i.e. 16 Nobel per
  Cöllnische Mark), 14.310 g fein @ .979 (1514) / 14.007 g fein @ .9583 (1524).
- danskmoent specimen standard: **14.375 g brutto**, 14.08 g fein @ .979.
- Dutch model: 14.9 g (16½ per troy mark).
- Surviving specimens (our data): 14.24 – 14.75 g (1-Nobel); 27.9 g (2-Nobel);
  44.72 g (3-Nobel) — per-Nobel 13.95–14.91 g, consistent with hand-struck
  *Pragtmünze* variance, not precise circulation strikes.

**Mark divisor:** 16 Nobel per **Cöllnische Mark** (233.856 g) per Wilcke; the
Dutch model used 16½ per **troy** mark. Metal: gold.

---

## §4. Nature & rarity — a prestige coin, not circulation money

- **Pragtmønter (prestige coins).** «*Pragtmønter*» — not struck for ordinary
  commerce (Galster, galkult.htm). Struck «*i Tilslutning til Udrustningerne til
  Sverigestoget*» (in connection with the armament for the Swedish campaign) —
  i.e. war-prestige / diplomatic gold, same source.
- **War finance — mercenary payment.** Hans struck gold «*i forbindelse med
  sine krige i Sverige og Ditmarsken … bl.a. til betaling af hans tyske
  lejetropper*» (in connection with his wars in Sweden and Dithmarschen, among
  other things to pay his German mercenaries). So the function was twofold:
  prestige/diplomatic AND a high-value medium to pay foreign troops. Source:
  danskmoent.dk «Møntvæsenet … under Christian 2.» <https://www.danskmoent.dk/c2njj.htm>.
- **Believed used as diplomatic gifts** to foreign dignitaries at court — Stack's
  Bowers (auction copy), <https://www.numisbids.com/n.php?p=lot&sid=8347&lot=1001>.
- **Rarity:** every Galster Nobel type is RRR. «Of all the Danish Nobles minted
  through the 1530s, **only ~20 survive**, the vast majority in the National
  Museum of Denmark» — Stack's Bowers / NGC. The Hans 1496 is **unique in private
  hands**; museum examples at Nationalmuseet (Copenhagen) + the Hermitage (St
  Petersburg), a third rumoured. Sources: NumisBids lot 1001; NGC
  <https://www.ngccoin.com/news/article/13205/bruun-realized-part-1/>.
- **Market (out of scope per §7a, recorded here only as a survival/rarity
  signal):** the L. E. Bruun Hans 1496 Noble (Galster 24 / Fr 3 / Sieg 12 /
  Schou 2, 14.67 g, NGC AU-55) sold for €1.2 M — a world record for any
  Scandinavian coin (NGC; Kristeligt Dagblad reports 8.9 M DKK,
  <https://www.kristeligt-dagblad.dk/kultur/guldmoent-fra-1496-blev-solgt-89-millioner-kroner>).

---

## §5. The `.986` mis-anchor (correction for the fuss card)

The fuss card `data/shared/fuesse.yml::nobel_fod` currently carries
`fineness_standard: 0.986` / «23 Karat 8 Grän». **That is the Reichsdukat /
Goldgulden gold standard, not the Nobel's documented fineness:**

- 23 Karat 8 Grän = 23⅔ Karat = 71/72 = **.98611** — the imperial gold standard
  fixed by the Augsburg Reichsmünzordnung of 1559 (67 Dukaten per rough Cöllnische
  Mark). It governs `reichsdukatenfuss`, not the Nobel. Cited:
  `docs/DECISIONS.md` («23 Karat 8 Grän = Reichsdukat gold standard») +
  `data/shared/fuesse.yml::reichsdukatenfuss`.
- The Nobel's actual documented fineness is **.979 (23½ Karat, Wilcke 1514 + 1532
  specimens)** and **.9583 (23 Karat, Wilcke 1524)** — §3.
- The card's `fineness_period: «23 Karat 8 Grän (Range .979–.995)»` mixes the
  Reichsdukat figure (.986) with the lower attested Nobel figure (.979) and an
  upper bound (.995) sourced only from the broad «English Sovereign/Noble tier»
  research note (`docs/TODO.md §646`), not a Danish source.

**Recommendation (pending curator decision, NOT yet applied):** re-anchor the
card to **.979 (23½ Karat, Wilcke 1514 Møntordning)** as the best-attested
nominal, drop the `.986` Reichsdukat figure, but KEEP an explicit uncertainty
note — the Nobel's true fineness is not firmly attested across all reigns
(Galster: «*maaske ogsaa i Finhed*»; the .9583↔.979↔24K spread is real). Do NOT
collapse to a single hard value. Soll fein then ≈ 14.08–14.31 g (per the .979
specimen / ordinance figures), not the card's 14.41 g (which derived from .986).

---

## §6. Sources (deduplicated, with the passage each backs)

1. **Georg Galster, *Unionstidens Udmøntninger. Danmark og Norge 1397–1540, Sverige 1363–1521*** (Dansk Numismatisk Forening, København, 1972; with English summary, 119 pp.) — THE authoritative catalogue. Accessed via danskmoent.dk transcriptions:
   - <https://www.danskmoent.dk/galster/galkult.htm> — Dutch-model statement («*intet tilfælles med de engelske Noble … groote gouden reaal … 24 Karat … 16 1/2 paa en troysk Mark … skulde veje 14,9g*»), Pragtmønter, Sverigestoget.
   - <https://www.danskmoent.dk/1nobel.htm> — full type list (Galster/Schou per ruler/year/mint); «*Senere ændredes betegnelsen til Rosenobel*»; 1508 = forgery.
   - Catalogue review: <https://tidsskrift.dk/historisktidsskrift/article/view/51708>. Galster bio: <https://lex.dk/Georg_Galster>.
2. **J. Wilcke, *Møntvæsenet i Danmark* 7-2 (1950)** — the 1514 + 1524 Møntordning Nobel specs (.979 / 23½ Karat; .9583 / 23 Karat). Internal transcript with page citations (p.152-153): `docs/research/wilcke_1514_1541_specs.md` (cites Suhm + Rigsarkivet T.K. Indk. Breve).
3. **danskmoent.dk deep pages** — specimen finhed .979:
   - <https://www.danskmoent.dk/fr/f1g45.htm> (Frederik I 1532, Galster 45): «*Bruttovægt 14,375g, Finhed 0,979, Finvægt 14,08g*».
   - <https://www.danskmoent.dk/fr/f1g69.htm> (Frederik I Ribe, Galster 69): same specs.
4. **Numista** — catalogue figures: N#420401 (Hans 1 Noble, Fr 3, 14.75 g) <https://en.numista.com/420401>; Christian II 1 Noble 1516-1518 (14.53 g, Fr 6); Frederik I 1532 1 Noble (Gold .979, 14.375 g, ⌀38 mm, Fr 12, Galster 45); index <https://en.numista.com/catalogue/danemark-1.html>.
5. **Stack's Bowers / NumisBids — L. E. Bruun lot 1001** (Hans Noble 1496, NGC AU-55): «first gold coin struck by Denmark … first dated Danish coin … only ~20 survive … unique in private hands … Nationalmuseet + Hermitage … gift for foreign dignitaries». <https://www.numisbids.com/n.php?p=lot&sid=8347&lot=1001> ; <https://auctions.stacksbowers.com/lots/view/3-1AKQTF/> ; record-sale: <https://www.ngccoin.com/news/article/13205/bruun-realized-part-1/>.
6. **da.wikipedia «Nobel (mønt)»** <https://da.wikipedia.org/wiki/Nobel_(m%C3%B8nt)> — general English-Noble background (the *name*'s origin); NOTE its «English model» framing is corrected by Galster (§2).
7. **Kristeligt Dagblad** — Hans 1496 sale 8.9 M DKK: <https://www.kristeligt-dagblad.dk/kultur/guldmoent-fra-1496-blev-solgt-89-millioner-kroner>.
8. **Internal cross-refs:** `data/shared/fuesse.yml::nobel_fod` (current card); `docs/denomination_lineages.md` (Nobel→Rosenobel family); `docs/research/danish_royal_gold_1560_1648.md` §3.4 (Rosenobel .833, distinct fuss); `docs/DECISIONS.md` (23K8G = Reichsdukat).

---

## §7. Open questions / leads for future sessions

- **Galster *Unionstidens Udmøntninger* full text** — only the danskmoent
  transcriptions are accessible online; the printed catalogue (1972) has the
  per-type fineness/weight tables. A paper-source page citation (§5a) would
  firm up the Hans/Christian-II Nobel fineness, which is currently inferred from
  the Dutch model + the 1514/1524 ordinances (Frederik-I-era), not directly
  attested for Hans 1496–1502.
- **Hans-era (1496–1502) direct fineness** is the biggest gap: the .979/.9583
  figures are Christian-II-1514 / Frederik-I-1524 ordinance values; applying
  them to Hans's 1496 strikes is cross-reign extrapolation. Galster's «perhaps
  also in fineness [24 Karat, like the Dutch model]» is the only Hans-era hint.
- **2-/3-Nobel fineness** — no source gives a distinct figure; treat as 1-Nobel
  multiples until a source says otherwise.
- danskmoent **c2njj.htm** was fetched (2026-06-05): NO Nobel fineness/weight
  figures (only the mercenary-payment context, now in §4). The Christian-II Nobel
  fineness gap therefore remains — Galster's printed catalogue is the place to close it.
- Update §5 in the artefact only on explicit curator approval — the .986→.979
  re-anchor is a card edit flagged here, not yet applied.
