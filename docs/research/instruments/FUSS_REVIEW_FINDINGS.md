# Per-Fuß review findings — what the instrument dossiers found about OUR coin data

> **Purpose.** While writing the per-instrument dossiers (`PLAN.md`), every session noticed
> things about `data/v2/final/*.yml` that the dossier itself cannot fix: coins sitting in
> `seed_unsorted` whose standard an act now names; coins classified under a Fuß whose grid
> is not theirs; a value in our data that the act or the source contradicts; a card figure
> that the act's text does not support. Those findings were reported in chat and in the
> dossiers' §7 — but a session that later «sorts» `seed_unsorted` or reviews one Fuß will
> not re-read twenty dossiers. **This file accumulates them in one place, keyed by the Fuß /
> entity the reviewer will be working on.** Opened 2026-10-15 on the curator's request.
>
> **Rules.** (1) Every row names the dossier section it comes from — the evidence lives
> there, this is the index. (2) A row is a *finding*, not a decision: no coin is moved, no
> value changed, by this file (§0b-1, §4 — `why` first, curator's «так» for errata and
> removals). (3) When a dossier adds a finding, add a row here in the same commit. (4) When a
> reviewer closes one, mark it ✔ with the commit, do not delete it. (5) Status glyphs: ☐ open ·
> ◐ partly handled · ✔ closed · ✖ rejected by the curator (keep the row with the reason).
> **Related:** `docs/TODO.md` §EA (the register / dossier work item); `PLAN.md` §3
> (non-instrument follow-ups); `docs/handoff.md` (session-level state).

## How to use this file when sorting `seed_unsorted` or reviewing a Fuß

1. Find the Fuß or entity below. Each row says which act's grid the coins rest on (dossier
   §4), which seed / final ids are affected, and what the source says against our data.
2. Open the dossier's §4 (the grid, recomputed) and §7 (our data) before touching a coin.
3. For a value finding (a weight, a fineness, a mintmaster), run
   `trace_coin.py why <seed-id> --field <name>` first — several of these values may already
   be curator calls that only *look* wrong.
4. Record the decision in `data/v2/classification_decisions/` / `merge_decisions/` /
   `_source_errata` as the pipeline requires, then mark the row here.

---

## A. Denmark (`danish_realm`) — silver, by period

### A1. Pre-1541: the Lovkompleks, the Klippinge, the war coin

| St | Finding | Ids / scope | Evidence | Dossier |
|---|---|---|---|---|
| ☐ | **No 1514–17 Skilling / Hvid / Blaffert / Penning under `8_5_gylden_fod` A1** — the small coin of the complex (the sort actually struck in quantity, per Galster) is absent from the render; seeds to be traced | `8_5_gylden_fod` A1 | 1514 act: Skilling 88/M 6 lod, Hvid 220/M 5 lod | `1514_moentordning_malmoe.md` §7, §8.6 |
| ☐ | **The 8½-Gylden-fod card text gives the 1 Aug 1513 small-coin figures (Skilling 96/M 5¾ lod, Hvid 222/M 4½ lod) as the 1514 ordinance's** — 1514 has 88/M 6 lod and 220/M 5 lod | `denmark.yml` 8½-Gylden-fod card | Wilcke VII s. 154 (image) | `1514_moentordning_malmoe.md` §8.1 (curator 2026-10-13: deferred to the per-Fuß review) |
| ☐ | **No 2-Mark, Mark, ½-Mark, 4 ß, 4-Hvid Skilling or Hvid of 1524–31 under `8_gylden_fod`** — only 14-Penning pieces and the 1532 fractions are there | `8_gylden_fod` A1 | the Kongebrev 1524 grid | `1524_moentordning_frederik_i.md` §7, §8.3 |
| ☐ | **The Sølvgylden 8/M at 14 lod stands only in the Rigsraad's letter (25 Feb 1524), which Galster calls without practical effect; the executed Kongebrev has Mark pieces instead** — the 8-Gylden-fod card rests on the letter | `8_gylden_fod` card | Wilcke VII s. 184–187 | `1524_moentordning_frederik_i.md` §8.2 |
| ✔ | «Separate act of 26 Feb 1524» for the 14-Penning piece in `denmark.yml` / `wilcke_1514_1541_specs.md` was a misreading of Wilcke's table (the line is 25/2) — specs file corrected; **bar title in `denmark.yml` left as is per the curator** | 8-Gylden-fod bar title | Wilcke VII s. 187 (image) | `1524_moentordning_frederik_i.md` §8 |
| ☐ | **The Lejrskilling 1523** (`unified-dk-bruun-3957`, `unified-kmk-367942`, `-46705`, `unified-dk-numista-152267`) — all `seed_unsorted`; no Fuß card covers it (a war coin outside 1514 and 1524); **Numista's .250 fineness disagrees with Wilcke's assay 6¼ lod = 390,6 ‰** (59/M, 3,98 g, 1,547 g fine); and the act's «hele ß» (4 Hvide) vs the 10-Hvid rating — at 1,547 g fine only the 10-Hvid rating is consistent | 4 entries | Wilcke VII s. 174–175, 187, 192–193 | `1523_valvation_klippinge.md` §4.3, §7 |
| ☐ | **Christian III's war coin 1535–36** (2 Mark / Mark / 4 ß 1535, 2 ß / 1 ß 1536, Joachimsdaler 1537): 18 coins under `8_daler_fod`, the mass in `seed_unsorted` (76 × 4 ß 1535, 51 × 2 ß 1536, 39 × 1 ß 1536, 8 × Mark 1535 …) — **their standard is Junge's war grid (16 / 32 per mark at 6½ lod; 4 ß at 4 lod), demonetised by half on 21 Oct 1537, NOT the 8-Daler-fod of 1541** | `8_daler_fod` + `seed_unsorted` | Wilcke VII s. 249–252; Galster 1934 (Junge's accounts, not in hand) | `1537_reces_moentens_afsaettelse.md` §4.2, §7; `../moentordning_1541.md` §6 |
| ☐ | **`unified-kmk-331973` «1 Penning», Lund, Hans 1483–1513 under `luebischer_muenzfuss` I** — KMM 331973 «Hbg. 1» is a Hauberg 1885 (1241–1377) per-mint type number (Lund 1 exists under eight rulers), not a Hans coin; no Lund mint under Hans (closed early 1440s); KMM's sibling «Christian 2 · Hbg. 4, MB 558» = Christoffer II shows the same ruler-field slip. Exclude / declassify / keep — curator | `luebischer_muenzfuss` I | Hauberg 1886 s. 136; Jensen, Hikuin 35 (2008) s. 158–159; danskmoent konkord.htm | `../luebischer_muenzfuss.md` §6d |

### A2. Frederik II, 1559–1588

| St | Finding | Ids / scope | Evidence | Dossier |
|---|---|---|---|---|
| ☐ | **The whole Frederik II round-coin series 1559–78 sits in `seed_unsorted`** — Hede f2h8, f2h9a/b, f2h10, f2h11, f2h13, f2h14, f2h15, f2h18ab, f2h19, f2h22 and c. 90 KMM Mark / Skilling 1560–63. Standards: Mark 1559 = the 1544 grid (24/M 13½ lod); **round Mark 1563 at ca. 10⅖ lod (650 ‰; Hede 9B .649)** — an assay, no ordinance; the 1572 act re-rates them all at half | `seed_unsorted` | Wilcke VII s. 312, 315 (image), 329; Secher I nr. 609 | `1572_aabent_brev_moentens_omsaettelse.md` §7; `1563_klippinge_syvaarskrigen.md` §4.2 |
| ☐ | **The silver Klippinge 1563–65** (`unified-dk-hede-f2h13` 2 Mark, `-f2h14` Mark, `-f2h15` 4 ß — `kind: scheide`; c. 40 KMM «1 Mark 1563», «klipping; 11 Skilling 1564–65», «2 Skilling klipping» — `kind: kurant`, the builder default) — all `seed_unsorted`; their grid is the order of 13 June 1563: **Mark 34/M at 7 lod, 2 Mark 17/M at 7 lod, 4 ß 88/M at 4 lod**; progressively debased after (no figures); Scheidemünze under §6 | `seed_unsorted` | Wilcke VII s. 312, 315 (image) | `1563_klippinge_syvaarskrigen.md` §4.1, §7 |
| ☐ | **`dk-hede-f2h15` (4 Skilling 1563) carries 6,878 g in the Hede seed — the Mark Klipping's weight; Hede's page prints only «Finhed: 0,437», no weight; `why` shows no decision.** The order's 4 ß is 2,657 g. Do not cite 6,878 g for the 4 ß; where the seed value came from is untraced | `dk-hede-f2h15` weight | `scripts/cache/hede/f2h15.htm` | `1563_klippinge_syvaarskrigen.md` §4.4 D3, §8.5 |
| ☐ | **Flensborg 1566–67 (Køppelin)**: `unified-dk-hede-f2h30a` 1 Skilling Lybsk 1566 (.391, 1,856 g = Wilcke's assay row) sits under `9_thaler` I `scheide` (`royal_slesvig`); `unified-dk-numista-313332` 1 Schilling 1566, 1571 `seed_unsorted`. The coin's standard is «som Lybecksk og Hamburgsk Skrot» by reference (ß 126/M, Søsling 208/M at 5¼ lod); whether a Hanse-standard ß belongs under a 9-Thaler-Fuß phase is open | `royal_slesvig` | Wilcke VII s. 351–352 (image) | `1563_klippinge_syvaarskrigen.md` §4.3, §7 |
| ☐ | **The Frederiksborg small coin 1582–85** (Mark `hede-23-fr-ii-1582`; 8 ß `unified-dk-hede-f2h24`, `-f2h26`; 2 ß `-f2h27`; 1 ß `-f2h28`; Hvid `-f2h29`) is classified under **`9_thaler` I** (the 1572 daler's standard) although struck on the 12 Jan 1582 grid (Mark 9 lod 15 gren = 614,58 ‰ at the old weight; 2 ß 5 lod 100/M; 1 ß 3 lod 132/M; Hvid 2 lod 12 gren 370/M) — own standard or `kind: scheide` under the daler is the curator's call | `9_thaler` I | Wilcke 7-6 s. 398–399, 407 (image) | `1582_befaling_poul_gulden.md` §7, §8.3 |
| ☐ | No Fuß cites the 1572 act or the 1582 act yet (`fuesse.yml` / `denmark.yml`); the keys exist | cards | — | `1572_…` §7, `1582_…` §7 |

### A3. Christian IV, 1588–1625

| St | Finding | Ids / scope | Evidence | Dossier |
|---|---|---|---|---|
| ☐ | **The 1594–1601 small coin (Metzner / van Campen / Schwabe)** — `hede-69-chr-iv-1596` Mark, `hede-71-…` 4 ß, `hede-72-…` 2 ß, `unified-dk-hede-c4h67` 2 ß 1594–96, `-c4h68` 1 ß 1595 under **`9_thaler` I** `scheide`; `unified-dk-hede-c4h70` 8 ß 1596, `-c4h73` 1 ß 1596, `-c4h45` specie 1596 «IIII MARCK DANSKE» and c. 40 KMM 1 ß / 2 ß 1594–95 `seed_unsorted`. Their grid is the 1582 one re-issued for Metzner (1594 / 1597) — the same question as the 1582–85 row. **The 4 ß 1596 is in neither ordinance** (Hede c4h71) | `9_thaler` I + `seed_unsorted` | Wilcke I s. 60 (image); Wilcke VII s. 407 | `1593_bestalling_metzner.md` §4.2, §7 |
| ☐ | **Species 1596–1600 carry both .888 and .937** by source (`dk-tid-173642`, `dk-tid-163067`, `unified-dk-hede-c4h46`, `-c4h47`); the 1597 daler assayed at 14 5/18 lod = 892,36 ‰ (Beskrivelsen) sits between them; no Danish act names the specie's fineness 1588–1602 | species 1596–1600 | Wilcke I s. 60 (image) | `1593_bestalling_metzner.md` §4.2 |
| ☐ | **The silver of 8 Sept 1602 is two standards in one act** — grov Mark 25/M at 9½ lod (593,75 ‰) and the fine tier (Mark 38/M, 8 ß 80/M, 4 ß 160/M at 14 2/9 lod = 888,89 ‰); 2 ß 4¾, 1 ß 2¾, Søsling 2, Hvid 1½ lod. No Fuß cites the act; the 1602–07 coins' classification (Hede c4h … Mark 1602/1604, 4 ß 1604, fine 8 ß 1606, fine Mark 1606–07) is open | 1602–07 silver | Wilcke I s. 65, 69 (images) | `1602_forordninger_moentreform.md` §4.2, §7 |
| ☐ | **Helsingør 1607–09 (Flemming)**: `unified-dk-hede-c4h95a` Mark (.888, 6,154 g = 1602 fine Mark; mint list Helsingør + Kopenhagen), `-c4h96` 8 ß, `-c4h97` 4 ß (.888, 1,462 g = 1602 fine 4 ß), `-c4h98` Mark 1607/1609 (.593, 9,354 g = 1602 grov Mark, `kurant`), `dk-tid-163034` 8 ß lumping Hede 93/96/122 across 1607–1642 — all under `9_thaler` I; `unified-dk-hede-c4h78b` 4 ß 1609 Helsingør (.453 = grov 4 ß) and c. 80 KMM objects `seed_unsorted`. Grid = 1602 by reference (Flemming's ordinance sets none) | `9_thaler` I + `seed_unsorted` | Wilcke I s. 77 | `1607_muentzordnung_flemming.md` §4.1, §7 |
| ☐ | **`km-4-chr-iv-1608` Løvedaler 1608 (Hede 65, 25,61 g) sits under `9_thaler` I kurant** — a Dutch-pattern export coin at **9 per Troy mark, 12 lod (750 ‰), 27,34 g / 20,51 g fine**, rated 50⅔ / 52 ß d.; not a 9-Thaler-Fuß coin | `km-4-chr-iv-1608` | Wilcke I s. 18, 96 (image) | `1607_muentzordnung_flemming.md` §4.2, §7 |
| ☐ | **`unified-dk-bruun-5845` 3 Speciedaler 1607–14 carries «Kopenhagen» + mintmaster «Hans Flemming»** — mint from one member, mintmaster from another (Flemming's mint is Helsingør; the København species are Schwabe's). Same pattern to check on `dk-tid-163074` (2 Speciedaler, Helsingør + Kopenhagen, Flemming) and `unified-dk-hede-c4h53c` (Helsingør + Kopenhagen, Flemming) | 3 entries | Wilcke I s. 91; Hede c4h63 | `1607_muentzordnung_flemming.md` §4.4 D6, §7 |
| ☐ | **Species 1608–21 carry both .875 and .888** (`unified-dk-hede-c4h53c`, `unified-dk-bruun-4811` .875; `dk-tid-173642`…). The daler's TARGET 1609 was 14 4/18 lod (888,88 ‰; Kreis Reichsthaler) / 14 3/18 with remedium; the OUTCOME per Flemming's own account 1610–15 was 14 lod (875); no act names it | species 1608–21 | Wilcke I s. 94–96 (image) | `1607_muentzordnung_flemming.md` §4.2, §4.4 D1 |
| ☐ | **The fine 4 ß of 9 Aug 1609 at 172/M (1,360 g / 1,209 g fine)** has no entry distinguished from the 160/M type (1,462 g) — Hede 97 / KMM 4 ß 1609 may mix both | 4 ß 1609 | Wilcke I s. 95–97 | `1607_muentzordnung_flemming.md` §4.2 |
| ☐ | **Hede c4h96 «8 ß 1608 … 23 294 daler»** ≠ Wilcke's table cell 22 644 (1608); hypothesis: Hede summed 1608 + 1609 (22 644 + 650). Not a data error, but do not cite Hede's mintage as the 1608 figure | Hede c4h96 note | Wilcke I s. 84, 97 (image) | `1607_muentzordnung_flemming.md` §4.4 D4 |
| ☐ | **The 12 ß / 8 ß of 1619–23 (Frederiksborg) and 1624 (København, Hede 128 ff.)** at 76 / 115 per mark 13¾ lod — placed under `kronemont_chr_iv`; whether they are Krone-tier or daler-tier coin is the curator's call; the Rigsraad's Betænkning of 15 Feb 1625 (Reich standard «udi schrot oc korn») is a demand, not an act — whether to cite it on the 9-Thaler Periode V card | `kronemont_chr_iv` | Secher IV nr. 107 (image); Wilcke I s. 228–230 | `1624_moentordning_kobenhavn.md` §7 |
| ☐ | **Nomenclature 1618**: the act's «Krone» = the catalogue's double Krone (1½ Rdl.), the act's «½ Krone» = the catalogue's Krone (Hede 44). `kronemont_chr_iv` Grundwerte (18,909 g / 16,250 g) are the act's ½ Krone. Any card text that says «Krone» must say which | `kronemont_chr_iv`, `guldkrone` cards | Secher III nr. 487; Wilcke I s. 151–152 (image) | `1618_kronemoent_indfoerelse.md` §7 |
| ☐ | **The kroneskilling of 1619 are split between `kronemont_chr_iv` I and `9_thaler` I by denomination name, not by grid**: `km-x030-chr-iv-1619` 8 Skilling 1619 (.859, 2,93–3,15 g = the April 1619 ⅛ Dlr. at 74¼/M) and `dk-tid-163014` 2 Skilling 1619/1624 (.859, 0,787 g = the April 2 Kr ß) sit under `9_thaler` I; `unified-dk-hede-c4h111` / `-c4h113` / `-c4h116a` / `km-81` / `km-82` under `kronemont_chr_iv` I. All are Krone-system coin (13¾ lod) | 7 entries | Wilcke I s. 164, 184 (images) | `1619_kroneskilling_instruks.md` §4.1, §4.3, §7 |
| ☐ | **Two different 1-ß coins in 1619**: the April kroneskilling at 13¾ lod, 594/M (0,394 / 0,338 g — Hede 113, `unified-dk-hede-c4h113`) and the November Anordning's 1 ß at **5 lod**, 447 3/16/M (0,523 / 0,163 g — Hede 118–119, `unified-dk-hede-c4h118`, `-c4h119a`, .312). The 5-lot ß is not a Krone-fraction; its placement under `9_thaler` I is as arbitrary as under `kronemont_chr_iv` | 3 entries | Wilcke I s. 183–184 | `1619_kroneskilling_instruks.md` §4.4 D7 |
| ☐ | **`km-81-chr-iv-1620` 4 Kroneskilling 1620–21 carries .437 and .859 and weights 0,83–1,46 g** — the .437 / 1,462-g readings are the 1618 grov 4 ß (106/M at 7 lod), the .859 / 1,05-g ones the Anordning's 4 Kron ß (222 213/350/M); likewise `unified-ngc-1050580` 4 ß 1619 (.437, 1,462 g) under `kronemont_chr_iv` is the 1618 type. One row, two grids | 2 entries | Wilcke I s. 162, 184 | `1619_kroneskilling_instruks.md` §7 |
| ☐ | **`unified-dk-hede-c4h103` Hvid 1619 at 5,82 g is the COPPER Hvid of the Frdg. 8 April 1619 § 3 (40/M = 5,846 g, Jørg. 159)**, not the 1½-lot billon Hvid of Nov 1619 (474/M, 0,493 g); `unified-ngc-1049834` «Denning 1619» at 5,8 g / .888 is not a Denning weight (48 per daler ≈ 0,6 g) — identify | 2 entries | Wilcke I s. 164, 169–170, 184 | `1619_kroneskilling_instruks.md` §4.4 D8, §7 |

### A4. Frederik III – Christian V, 1648–1700

| St | Finding | Ids / scope | Evidence | Dossier |
|---|---|---|---|---|
| ☐ | **The 1671 small coin is its own tier** — 4 ß at 10⅔ Rdl., 2 ß 11, 1 ß 12, Søsling 13⅓ Rdl. per mark fine (Myndt-Ordning 22 March 1671) — NOT 9¼; in final partly under `9_25_thaler`, mostly `seed_unsorted`: **86 × 2 Skilling, 44 × 1 Skilling, 78 × 1 Krone, 34 × 4 Mark of 1671–92** | `seed_unsorted` + `9_25_thaler` | Schou I s. 80–82 (IIIF images) | `1671_myndt_ordning.md` §7 |
| ☐ | The `9_25_thaler` card (Danish specie 1671–92: 8 3/32 at 14 lod) and the 10½-Krone-Fuß card can now cite the act's own text instead of the Mordhorst umbrella key | cards | `schou-1795-bd1-s81-*` keys | `1671_myndt_ordning.md` §7 |
| ☐ | **Kroner and Mark pieces from 1693 belong to the 13-Krone standard (`kronemont_fine`), not to `kronemont` (10½)** — in final: 1 × `kronemont_fine`, but 2 × 1 Krone, 2 Krone, 3 / 4 / 6 Krone 1693–99 under `kronemont` and 10 × 1 Krone + 7 × 4 Mark `seed_unsorted`; the 3 Krone 1699 is Hede's Skuemønt exception; 2 ß 1693–1700 (13 `seed_unsorted`, 1 under `9_25_thaler`) at 10 Rdl. 64 ß; copper ½ ß 1693–1700 (8 `seed_unsorted`) | `kronemont` / `kronemont_fine` | Mordhorst c5mord (the reskript's digest); Hede 1957 | `1692_reskript_ny_moentanordning.md` §7 |
| ☐ | **`kronemont_fine` Grundwerte: Hede's printed 14,984 g fine is 0,007 g under his own formula** (13⅓ lod × 13/M = 14,991 g; = 10 Rdl. 38,4 ß — matches the reskript's 10 Rdl. 38 ß) — flag on the card, no change | `kronemont_fine` card | Hede 1957 | `1692_reskript_ny_moentanordning.md` §4 |

## B. Norway (`danish_norway`)

| St | Finding | Ids / scope | Evidence | Dossier |
|---|---|---|---|---|
| ☐ | **No Fuß card covers the Norwegian 4-Hvid tiers of 1524–32** (Hamar 1524 = the Danish 96/M at 5 lod; Oslo 1525 112/M at 4 lod, 1526 at 3½ lod; Bergen 1527 106/M at 4½ lod — Wilcke; Holst reads 126; Hvid 320/M at 3½ lod). Our Bergen Skilling / 4 Hvid / Hvid 1523–33 all `seed_unsorted`; no Oslo-minted entries by that mint name (check KMM with mint «Akershus» / blank). The 1551 letter tariffs the 4-Hvid piece at 36 = 1 Joachimsdaler | `danish_norway` `seed_unsorted` | Wilcke VII s. 196–204, 305 (table s. 198 image); Holst | `1524_norske_moentbreve_frederik_i.md` §7, §6 |
| ☐ | The Hamar «Klipping søsling» 1531–32 and «1 Mark Christiania / Hamar 1531–32» are the bishop's / Christian II's-invasion coinage (Holst §VI), not the 1524–27 acts' | 2 entries | Holst | `1524_norske_moentbreve_frederik_i.md` §7 |
| ☐ | The Bergen Skilling «1533, 1537» is Holst's Christian III issue (Junge's crew 1537, dated 1533 by die-cutter's error) | 1 entry | Holst | `1524_norske_moentbreve_frederik_i.md` §7 |
| ☐ | **The whole Christiania small coin 1641–1670 sits in `seed_unsorted`** — 2 ß 1643–70 (Hede nc4h17, nf3h70: .281, 1,299 g = 180/M at 4½ lod), 1 ß 1643–48 (nc4h18: .156, 0,921 g = 254/M at 2½ lod), 8 ß and 4 ß 1643–44 at .750 (Bruun 9496 / 9470, KMM, Numista), c. 50 KMM objects. No Fuß carries the 1643 standard (the 1624 lineage's Christiania phase, or the 1648 København grid as successor, are the candidates) | `danish_norway` `seed_unsorted` | Wilcke II kap. II.3, II.7 (tables s. 172–173 missing from the HTML) | `1643_muentzordnung_christiania.md` §7 |
| ☐ | **Hede nc4h14 «8 Skilling 1641–1644» at .875 spans two standards** — 1641–42 at 14 lod (the 1630 grid «udi Rixdalers Verdt»), 1643–44 at 12 lod (the 1643 act); nc4h16 2 ß 1641–42 .875 and the NGC 4 ß 1641–42 .875 are the 1641 standard | `seed_unsorted` | Wilcke II kap. II.3 | `1643_muentzordnung_christiania.md` §7 |
| ☐ | **Norwegian 1 ß / 2 ß after 1671** (nf3h70 «1648–1670» ends there): the 1671 act's small-coin lines apply to Christiania too | — | Schou I s. 81; Wilcke II kap. II.7 | `1671_myndt_ordning.md` §7 |

## C. Gold

| St | Finding | Ids / scope | Evidence | Dossier |
|---|---|---|---|---|
| ☐ | **1497 Stockholm Møntanordning says «atten gradh oc en gren» = 18¼ karat**, and Wilcke VII s. 121 n. 1 expressly retracts the 18½ of Wilcke VI / Schive — but `rhinsk_gylden_fod.md` (§§1, 4, 12, rows «72 / 18½»), the key `wilcke6-hans-moentanordning-1497-sverige` and the «1497 anticipates 1559» parallel all carry 18½ | `rhinsk_gylden_fod` phase 0 texts + 1 key | Wilcke VII s. 116–117, 121 n. 1 | `1497_moentanordning_stockholm.md` §7, §8.1 |
| ☐ | **Hans' Swedish Ørtug / ½ Ørtug (Galster hg-233/234/236/238, KMM) and Christian I's Ørtug** sit in `danish_realm` `seed_unsorted` — whether an «Ørtug» standard (1480: 135/M Stockholm at 8 lod; 1497) gets a card is a curator scope call (SOURCES §13.16: scope by crown held) | `seed_unsorted` | Wilcke VII s. 118–119, 124 (image) | `1480_moentordning_arboga.md` §7 |
| ☐ | **Nobel 1524: the Rigsraad's letter (23 kt) had «ingen praktisk betydning» (Galster); the Kongebrev restores 23½ kt** — the `nobel_fod` I card and the 1524 phase text must not present 23 kt as an executed standard | `nobel_fod` I | Wilcke VII s. 184–187; Galster | `1524_moentordning_frederik_i.md` §7 |
| ☐ | **Flensborg 1546–47**: Blaffert 1546 (`unified-kmk-131480`, `-131481`), Søsling 1545 (`unified-kmk-139673`, `-411793`), ½ Gulden 1547 (`unified-dk-numista-153862`) unclassified; the Bestalling's small coin is «equal to Hamburg / Lübeck / Lüneburg» by reference | `royal_slesvig` | Wilcke VII s. 282–284 (image) | `1547_bestalling_flensborg.md` §7 |
| ☐ | **The 1602 gold** (`reichsdukatenfuss` I–III, `115_5_daler_fod` I; the 8 / 6 / 4 Dlr. Klipping) rests on C (8 Sept 1602) and the 1604 reduction — see `../daler_klippe_1604.md`; the 1604 nedsættelse «næppe … varig Betydning» (Wilcke) | gold cards 1602–05 | Wilcke I s. 65, 69, 80 | `1602_forordninger_moentreform.md` §7 |
| ☐ | **Hans de Wullers / Køppelin / Hammer war gold 1563–64** (ungersk, Krone, Guldgylden Klippinge) — covered by `f2_guldkrone_fod`, `rhinsk_gylden_fod` III, `reichsdukatenfuss`; the Flensborg 1566 line and the 1571 Wardein visit are not gold | — | Wilcke VII s. 320–326 | `1563_klippinge_syvaarskrigen.md` (excluded) |

## D. Duchies (`gottorp_duchy`, `royal_slesvig`, `royal_holstein`)

| St | Finding | Ids / scope | Evidence | Dossier |
|---|---|---|---|---|
| ☐ | **The Gottorp Steinbeck / Slesvig small coin 1596–1608** (Søsling, Sechsling, Schilling, 2 Skilling, 1/16 and 1/32 Thaler — c. 50 KMM / NGC / Numista objects, Lange 287–312) all `seed_unsorted`. No ducal act sets a grid; the Kreis valuations are the standard of reference: Kiel 13 June 1605 (2 ß = 20 Pf., 1 ß = 9, Sechsling 4); Gardelegen 25 Nov 1609 (Doppelschilling 153/M at 14–14 4/18 lod, Sgr. 234 / 116 / 360 per mark) | `gottorp_duchy` `seed_unsorted` | Wilcke I s. 86–87, 105 | `1610_forordninger_gottorp.md` §4, §7 |
| ☐ | **`km-21-ja-1606` (Thaler 1608–09) names mintmaster «Heinrich Puls»** — Wilcke (after Lange) has Matz Puls 1596–1605 and 1607–, Heinrich at Slesvig only from 1622; «Jonas Georgen(s)» on `km-25-ja-1611`, `unified-dk-bruun-14114`, `-14118`, `-14124` is from Bruun / Krause, not in Wilcke. Lange's *Nachrichten* (the officials) is paper-only | 5 entries | Wilcke I s. 87 | `1610_forordninger_gottorp.md` §4.3 D5, §5 |
| ☐ | The Gottorp Thaler 1606–12 under `9_thaler` I (`km-16-`, `-21-`, `-25-`, `-27-`, `-32-`, `-34-`, `-35-ja-…`) — the Kreis Reichsthaler target 14 4/18 lod; no ducal grid in hand | `9_thaler` I | Wilcke I s. 96 | `1610_forordninger_gottorp.md` §7 |
| ☐ | **Royal-share course chain** 1609 → 1610 → 1616 (68 / 74 / 80 ß d.) and the duchies' 37⅓ ß l.: the Mark pieces' tariff moves while the grid does not — a card that gives «Mark = 16 ß» for 1609–18 is wrong for the realms (17 → 18½ → 20 ß) | DK Mark 1609–18 | Secher III nr. 295, 318, 433 | `1607_muentzordnung_flemming.md` §3, §6 |
| ☐ | **The Altona Kipper small coin 1611–21** (`schauenburg_pinneberg`): 2 ß / Doppelschilling 1611–20 (`unified-dk-numista-137301`, `-137302`, `unified-ikmk-18285689`, c. 30 `hs-ikmk-182857xx` 1618–20 at 1,36–2,14 g), Groschen 1612–18 (`unified-dk-numista-137300`), Schreckenberger 1621 (`unified-schleswig_holstein-numismaster-96074`, `-96075`) — all `seed_unsorted`. Their standard is the de Valentza / Dionis farm: **Schreckenberger 47/M at 9 3/18 lod (1616) → 8 lod (1617); Fürstengroschen 192/M at 8 lod**; the Kreis Reichsthaler (`9_thaler`) is what they were rated against, not their grid. The specimen weights' fall 2,5 → 1,4 g is the 1617–20 debasement | `schauenburg_pinneberg` `seed_unsorted` | Wilcke I s. 34–36 (images) | `1616_contract_schauenburg_altona.md` §4, §7 |
| ☐ | **Altona mintmaster names on our Thaler rows** (`km-74-ernst-iii-1615` Henning Hanses ✓ Wilcke; `km-106-ernst-1620` / `unified-ikmk-18285689` Christoph Feistel; `km-130-ernst-iii-1622a` Thomas Eisenbein) come from Lange / Krause — Wilcke names Hanses (1616), Dionis as «Møntfaktor» (1617–19), Isenbehn / Kostede (before 1605); do not read Dionis as the Thaler mintmaster | 4 entries | Wilcke I s. 34–37, 88 | `1616_contract_schauenburg_altona.md` §4.3 D6 |
| ☐ | **Glückstadt (`royal_holstein`) starts 1619, not 1623** — Dionis's Denning privilege 7 July 1619 (480 / 232 per mark at 14 lod 4 gren) is the entity's first instrument; our `royal_holstein` KMM rows «(?) 1600–1616» and 1/16 Thaler 1608–09 need the Glückstadt / Altona / Krempe attribution checked | `royal_holstein` | Wilcke I s. 171 | `1616_contract_schauenburg_altona.md` §3 P; 1619 dossier (queued) |

## E. Cross-cutting

| St | Finding | Scope | Evidence | Dossier |
|---|---|---|---|---|
| ☐ | **KMM objects come in as `kind: kurant` by builder default** — the Klippinge 1563–65, the Steinbeck small coin, the 1594–1609 Skillinger are Scheidemünze under §6; a sorting pass should set `kind` from the act's tier, not from the default | all KMM seeds in `seed_unsorted` | — | `1563_…` §7, `1610_…` §7 |
| ☐ | **Stage 5 citations**: acts named on the Denmark page without a ref (3 Aug 1514, Easter 1515, 24 Aug 1515, 1518, 26 Feb 1524, 3 Feb 1609, 2 Jan 1658, 14 Feb 1671, 11 March 1675, 31 Dec 1692) now have keys — cite them from `denmark.yml` / `fuesse.yml` in all four languages | pages | refs_pool | `PLAN.md` §3 |
| ☐ | **Source-internal discrepancies** that affect figures a reviewer might copy are tabled in each dossier's «⚠ Source-internal discrepancies» block (1563 §4.4, 1593 §4.3, 1607 §4.4, 1610 §4.3) — read them before taking a figure from a dossier table | — | — | the dossiers |

---
*Rows added 2026-10-15 from dossiers 1–20 (1480 → 1610) and the chat findings of the sessions
of 2026-10-13/15. Next dossiers add their rows here in the same commit (PLAN §3).*
