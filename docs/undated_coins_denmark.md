# Undated coins on the Denmark page — groups and plan

> Working plan, opened 2026-10-17 on the curator's request («приймемо цю таблицю
> як план дій … по кожному рядку по черзі»). One row at a time; each row's
> decision is the curator's. Index entry: `docs/TODO.md` §EB.

## Where the number comes from

The Denmark page assembly (`scripts/build.py::_assemble_v2_location`) drops a
coin for one of three reasons. Counted 2026-10-17 after commit `80d1dd4`:

| Reason | Coins | Nature |
|---|---|---|
| year outside the entity's consume-window (`danish_norway` after 1814, `royal_holstein` after 1864, …) | 341 | page scope by design — not a loss |
| no year information | 185 | this plan |
| out-of-scope metal (paper money etc.) | 16 | page scope by design |

Already done before this plan: KMM `sluttid`-only years read (`aeab3e2`),
reign-window placeholder (?) for an undated coin whose ruler is known, chosen
by issuer (`c6202fa`, `80d1dd4`) — 1776 → 542 drops.

## The 185, by what could date them

| # | Group | Coins | What could date them | Status |
|---|---|---|---|---|
| 1 | Ruler of another house, no reign table | 61 (78 by the wider match) | reign tables for Sønderborg, Plön/Norburg, Schaumburg-Pinneberg, Oldenburg, Gottorp prince-bishops, Rantzau — each with a source; or entity re-routing | **done 2026-10-17** (57 stubs excluded, Sønderborg table) |
| 2 | Medieval rulers (before 1481) | 44 (28 truly) | dated by reign windows (?) | **done 2026-10-17** |
| 3 | No ruler, no catalogue | 29 (36 by re-count) | Kobbersterling and MB-numbered pennies dated | **done 2026-10-17** (the rest left undated) |
| 4 | Catalogue index matching a dated type | ~12 (4 real) | systemic merger fix first, pairs after | **merger fixed 2026-10-18**; 3 of 4 pairs now dated through their type; `unified-kmk-307517` (Gaute Ivarsson, Galster 177) left |
| 5 | «Aahuset L. Chr. Larsen» | 8 | probably a private issuer — unchecked | **done 2026-10-19** — 8 excluded as `exonumia` |
| 6 | Unambiguous misspellings of Danish kings | ~6 | aliases in the normaliser («Chrtistian 4», «Chritian 4», «Chrisytian 1», «Kristian 1», «Ridsrådet») | **done 2026-10-17** (in row 2); «Johan» Hvid Malmø (690101) left — see row 8 |
| 7 | Years printed in the ruler string | 5 | «Hans den Yngre af Slesvig-Holsten-Sønderborg 1564-1622» — KMM's own reign years, as (?) | **done 2026-10-17** by the row-1 Sønderborg table |
| 8 | Bare «Christian» / «Frederik» | 6 | ambiguous without other data | **done 2026-10-19** except the assumptions (three Gottorp «Frederik», two «Johan Frederik» without index) |
| 9 | Modern / foreign («Margrethe 2», «Carl 15.») | 4 | outside the page | **done 2026-10-19** — 4 excluded as `out_of_scope` |

Count after rows 1–4 (danskmoent build 2026-10-19): **66** undated (from 185).
**Since 2026-10-19 undated coins are no longer dropped** (curator): they render
in their source's `seed_unsorted` pen with an empty year; a classified undated
coin is shown there on the page only (build log lists it). The table above is
now a list of coins without a year, not of coins missing from the page.

Groups overlap at the edges (a record can be both «other house» and «years in
the ruler string»); counts are from one classification pass.

Separate finding, handed to a parallel session 2026-10-17: the NGC parser does
not read dates printed with a letter for a digit («16Z4(a)» = 1624).

## Row 1 — rulers of other houses (analysis 2026-10-17)

78 records match a non-royal ruler name. They are of two kinds:

**A. 58 empty KMM stubs.** Inventory-list objects from the accessions of
1883–84 (`GP 888.x`, 41) and 1888–89 (`GP 982.x`, 17): `nation: Slesvig-Holsten`,
`workDescription: Mønt`, an `authority` — and nothing else: no nominal, no
year, no weight, no catalogue index, no image check done. 50 of them sit in
`royal_holstein` only because the KMM builder's nation fallback routes
«Slesvig-Holsten» there, although the authority names another issuer:
Schaumburg-Pinneberg counts (Adolf XIII, Ernst III, Otto V, Otto VI, Justus
Herman), Ditlev Rantzau, Anton Günther (Oldenburg), Gottorp dukes and the
Gottorp prince-bishops (Christian Albert, Karl Peter Ulrik, Johan Frederik,
August Frederik, Christian August), Alexander (Sønderborg?). 8 sit in
`norburg_plon_duchy` (Hans Adolf of Plön, August of Nordborg).
Even with a reign window they would render as rows «(?) · reign (?)» with
nothing else.

**B. 20 records with a nominal.** 12 Sønderborg (Hans den Yngre, «Johann»:
2 / 4 Schilling), 4 NGC royal_holstein (Friedrich I / II with MB numbers —
row 4 merge candidates), 1 Gottorp (Johan Friedrich, 4 Skilling lybsk,
Jungk 316), 3 danish_realm «Johan / Johannes» pennies (medieval — row 2).

Options for the curator (row 1):
- A: (a) re-route each stub to its issuer's entity by an entity-routing rule
  keyed on the KMM authority (most then leave the Denmark page by the issuer's
  consume-window); (b) exclude them as empty stubs (the 2026-10-15 category-C
  precedent, `docs/research/luebischer_muenzfuss.md` §6b); (c) date them by
  new house tables and keep them.
- B: a Sønderborg reign table (Hans den Yngre 1564–1622; source to be cited),
  then the existing placeholder rule dates the 12; the NGC four go to row 4.

**Decision and outcome (curator 2026-10-17: «Виключи 58 порожніх заглушок …
як порожні (як категорію C 2026-10-15); і додай таблицю Sønderborg з
джерелом»).**
- A: 57 excluded as `undocumented_stub` (49 in `exclusions/royal_holstein.yml`,
  8 in the new `exclusions/norburg_plon_duchy.yml`). The 58th candidate,
  `kmk-83149` «Alexander» (GP 982.173), has a weight and typeNumber «Lange»
  (no number), so it is not empty and stays — open.
- B: `sonderburg_duchy` reign table, Hans (Johann) der Jüngere 1564–1622
  (NDB 10, 1974, S. 534 f.); 12 Sønderborg coins now carry 1564–1622 (?).
  Commit `697bcee` (code + exclusions) and the re-flow after it.
- Left over: the 4 NGC royal_holstein Friedrich I / II records → row 4;
  the 3 danish_realm «Johan / Johannes» pennies → row 2; Sonderburg KM 11
  (NGC 1172866 + numismaster-120993 vs km-11-hans-jr-sonderb-1620) needs a
  merge decision (found by the NGC session).

## Row 2 — medieval rulers (analysis 2026-10-17)

After row 1 the page has **111** undated coins. The «medieval» pattern of the
first pass also caught later rulers whose names contain «erik» (Frederik …);
re-sorted:

**Truly before 1481 — 28 records**, all KMM, almost all find-protocol (FP)
objects without weight or image:

| Ruler as KMM writes it | Records | Index | Note |
|---|---|---|---|
| Christoffer II («Christoffer2», «Ckristopher II», «Chrstoffer 2») | 10 | MB 533–640 | MB numbers sit in Christoffer II's ranges of the Hauberg/MB concordance (konkord.htm) |
| «Johan», Saxkøbing penning | 2 | MB 569–570, MB 578 + Hbg 1 | MB 578 = Christoffer II, Saxkøbing, Hbg 1 (konkord.htm) — Christoffer II's era |
| Christoffer I («Chyristoffer 1») | 1 | MB 083, Hbg 5 | |
| Erik Menved («Ereik Menved») | 1 | MB 441 | |
| Hardeknud («Hardeknuyd») | 1 | Hbg 39 | |
| Magnus den Gode («Magnud den Gode») | 1 | — | |
| Valdemar I («Vardemar I»), «Valdemarerne?» | 3 | Hauberg Tab. II 13 (one) | |
| Jakob Erlandsen (archbishop of Lund) | 3 | Jesse 262 (one) | |
| Margrethe (I) | 3 | — | Brakteater |
| «Kongeløs tid» | 1 | L.E.B. 3690 | the interregnum 1332–1340 |
| Håkon V Magnusson (Norway) | 2 | — | empty GP 982 stubs |
| «Johannes», Odense | 1 | Hbg VIII.5 | has a weight |
| «Æthelred», Lund | 1 | Becker Æ1/161 | English type (Becker's Æthelred imitations) |
| «Øystein?», Norway | 1 | — | Brakteat |

**Not medieval — move to other rows:** «Kristian 1», «Chrisytian 1» (Hvid
Malmø, Christian I) and «Johan» Hvid Malmø (690101 — Hans = Johannes) → row 6
(aliases); «Frederik IX.» 2 Øre → row 9; «Frederik» 2 Schilling lybsk Gottorph,
«Frederik III.», «Johan Frederik», «Karl Frederik» Søsling → rows 1/8.
**Six more empty GP 888 / GP 982 stubs** of the row-1 kind were missed by the
row-1 match: «Karl Frederik» ×4 (royal_holstein), «Frederik Karl» (Nordborg),
«Peter Frederik Vilhelm» — same criteria as the 57 excluded.

**What the page already does with pre-1481 coins:** 11 dated ones render, all
in `seed_unsorted` (Erik VII, the 1448 interregnum Hvid, the Lund penning
1241–1377). The seed_unsorted phases open at 1480 and these sit as «year
outside phase» advisories.

Options for the curator (row 2):
- (a) leave the 28 undated — they stay off the page; nothing to do;
- (b) date them: add the medieval kings (and the archbishop) to the reign
  table, each with a source, plus the misspelling aliases; they then render
  in `seed_unsorted` like the 11 already there;
- (c) exclude them explicitly as `out_of_scope` (before the page's span) —
  and decide whether the 11 dated pre-1481 coins follow, for consistency.

**Decision and outcome (curator 2026-10-17: «Датуй 28 середньовічних: додай
середньовічних королів і архієпископа до таблиці правлінь з джерелами та
аліаси описок; і виключи 6 порожніх заглушок GP 888/982»).**
- `lib/ruler_reigns.py` (`8e0c1e9`): Hardeknud, Magnus den Gode, Valdemar I,
  Christoffer I, Erik VI Menved, Christoffer II (1320–1332, one span),
  Kongeløs tid, Margrete I (from 1376), with da.wikipedia «Danmarks regenter»;
  Jakob Erlandsen 1249–1274 (lex.dk — Roskilde 1249, Lund 1254, † 1274);
  Håkon V 1299–1319 (snl.no). KMM's misspellings as exact aliases; also
  «Kristian 1», «Chrisytian 1», «Chrtistian 4», «Chritian 4», «Ridsrådet»
  (row 6, done here).
- Left undated on purpose: «Valdemarerne?» (2), «Johan» Saxkøbing (2 — the
  MB numbers put them in Christoffer II's Saxkøbing series, but the name is
  not his), «Johannes» Odense, «Æthelred» (English type), «Øystein?».
- 6 more empty stubs excluded (5 royal_holstein, 1 norburg_plon_duchy).

## Row 3 — no ruler, no catalogue (analysis 2026-10-17)

After row 2 the page has **76** undated coins; **36** carry no ruler (`None` /
`?`). Not all are «no catalogue»: re-sorted by what the record still holds.

| Sub-group | Records | What is there | Could date it |
|---|---|---|---|
| a. Sæby Kirke excavation (FP 9374.x) | 17 | nominal only (Hulpenning, Hvid, Skilling, Søsling, 2 Skilling, «skilling eller moderne mønt»); no weight, image, mint | no — the nominals span centuries |
| b. Kobbersterling | 3 | nominal (FP 9197.2–3 Tyvelse, FP 9177.10 Sanderumgård «?») | **yes**: Erik af Pommern's copper sterlings, «dateres … til ca. 1420-1430/35» (Jensen, Hikuin 35, 2008, s. 158, after Moesgaard 2005) |
| c. Penning with MB numbers | 3 | MB 261; MB 266-269; MB 285, 287, 319-320 | **yes**: the Hauberg/MB concordance (danskmoent konkord.htm) gives ruler and mint per MB number — MB 261 and 266-269 = Erik Klipping, Slesvig (1259–1286); MB 285–320 = Erik Menved, Lund (1286–1319) |
| d. Penning, Hbg 1, Roskilde | 1 | Hauberg 1885 per-ruler number | no — «Roskilde 1» exists under every ruler |
| e. Korshvid | 1 | nominal, very copper-rich, Øm kloster | rough: Korshvide of Christoffer, Rigsrådet, Christian I and Hans, all Malmø (danskmoent, quoted in luebischer_muenzfuss.md) — 1440–1513 |
| f. NGC | 3 | 1/16 Thaler KM 25 Sonderburg «16Z5»; 2 Ducat KM 327; 10 Ducat KM PnA19 | the first dates as 1625 once Sonderburg is re-flowed (held for a merge decision); the other two NGC pages give no date; PnA19 is a Krause Pn number (§9 item 5 gate) |
| g. Græse find penning | 1 | 0,36 g, «stående frelser/kors», image | the Græse hoard is dated by its finds (Niels / Erik Emune — Galster 1955); not attempted |
| h. Tranquebar lead piece | 1 | Pb, «VF-DAN-NES-BOR», «Bgs. mgl.» | colonial Danish India — scope question, not a date question |
| i. Nothing left | 6 | «(?)», «MB» without number, «?» | no |

**Two pipeline defects found here (beyond row 3):**
1. *Thinning merges different types.* `kmk-138263` is the keeper of a bucket of
   ruler-less weightless pennies and carries `mb: [285, 500, 566-567]` salvaged
   from the dropped records — Erik Menved (MB 285) and Christoffer II
   (MB 566-567) in one record (`lib/seed_thin.thin_safe` + `_salvage_unique`:
   the bucket key does not separate records whose catalogue indices differ
   when the ruler is absent).
2. *Comma-continued numbers are dropped.* KMM «MB 285, 287; 319-320» is split
   on «,»; «287» has no prefix and is lost (`build_kmk_seed._catalog`).

**Cross-check of row 2 by the concordance:** the MB numbers confirm the KMM
ruler for Christoffer II (MB 533, 541, 566-567, 580, 589, 595, 606), Christoffer
I (MB 083) and Erik Menved (MB 441) — but **MB 640** (`kmk-298884`, KMM
«Christoffer2», Lund) is «Skåne under Magnus Smek, Lund 2» (1332–1360) in the
concordance, not Christoffer II. Our data now shows it 1320–1332 (?).

**Decision and outcome (curator 2026-10-17: «Датуй Kobbersterling … і пенінги
з номерами MB через конкорданс, виправ MB 640 за конкордансом; два дефекти
пайплайну … — окремою сесією»).**
- `lib/mb_concordance.py` (`65d740f`): MB number → the concordance row's ruler,
  years and mint; Kobbersterling → ca. 1420–1435. Wired into absorb's
  placeholder before the ruler window, for the Danish crown's issuers only.
- Dated (?): 3 Kobbersterlinge 1420–1435; MB 261 and MB 266–269 1259–1286;
  «Johan» Saxkøbing MB 569–570 / MB 578 1319–1332 (concordance years).
- MB 640: `kmk-298884` ruler «Christoffer2» → «Magnus Smek» by `_source_errata`
  (seed) and in the final; now 1332–1360 (?).
- Left undated: `kmk-138263` (its MB list mixes Erik Menved and Christoffer II
  — the thinning defect; the KMM print «MB 285, 287; 319-320» also falls into
  the concordance's Lund gap 319–320), the Sæby Kirke excavation coins, the
  «Hbg 1» Roskilde penning, the rest of the sub-groups a/d/g/h/i.
- The two pipeline defects went to the session «KMM: thinning merges MB types;
  'MB 285, 287' lost».

## Row 4 — catalogue index matching a dated type (analysis 2026-10-17)

Four real candidates once nominal and ruler are required to fit (bare numbers
across catalogues collide constantly — Schou 6 sits on dozens of types):
`unified-kmk-317773` + `unified-kmk-307517` → `unified-dk-bruun-9248` (Galster
177, Gaute Ivarsson Hvid); `unified-kmk-332024` «Christian» → `unified-dk-hede-
c4h134a` (Hede 134, 2 Skilling — «Christian» is ambiguous); `unified-kmk-317111`
«Søren Nordby» → `unified-dk-bruun-4125` (Galster 144, Visby); `unified-kmk-
307062` «Christian» Hvid Malmø → `unified-kmk-122558` (Galster 23). Rejected:
Schou 6 (Christian III only), «Margrethe 2» Hede 6 (row 9), Hbg 1 Roskilde.

**The systemic finding.** The same scoped index stands in several separate
classes: Hede 134 (c4h134a + ~9 KMM classes), Galster 23 (4 KMM classes +
`unified-kmk-741073` «Hans» G23 under 11½-Markfod), Galster 144 (3 classes),
Hede 148 (`unified-dk-hede-c4h148` vs `unified-kmk-122209`). The index scoping
in `_catalog_refs` is right; `match_pair(dk-hede-c4h134a, <KMM seed>)` shows
three rule-level causes: (1) a number inside a range of the same catalogue
(Schou 32 ∈ «29-32») counts as «catalog disagree»; (2) catalog + nominal +
ruler without year or metal abstains; (3) the weight tier-1 disambiguator
(Δ > 5 % with < 2 shared refs) blocks worn museum specimens. A bare «Christian»
correctly does not match «Christian IV».

**Decision (curator 2026-10-17):** no pair merges for now; a separate session
investigates and fixes the cause systemically, respecting that numbering
restarts differently per catalogue (proposed as «Merger: same scoped index
fails to merge»). The four pairs are re-checked after that fix.

**After the merger fix (2026-10-18):** `unified-kmk-332024`, `unified-kmk-317111`,
`unified-kmk-307062` and `unified-kmk-317773` are no longer undated. Left:
`unified-kmk-307517` (KMM «Gaute Ivarsson», Galster 177, Nidaros, in
`danish_norway`) and `unified-kmk-150268` («Hans; ærkebiskop Gaute Ivarsson»,
Hvid, Schou 6).

## Row 5 — «Aahuset L. Chr. Larsen» (analysis 2026-10-19)

Eight KMM objects, one accession group (KP 1332.36a–h, protocol III p. 23):
2 Kroner, 1 Krone, 50 / 25 / 10 Øre in «messing» (brass), 5 / 2 / 1 Øre in
«blik» (tinplate); motif «LCL»; `workDescription: Mønt`; no year, weight or
image. `authority` is a business name, not the crown; the denominations are
of the 1873 Kroner system, but the state struck those values in silver and
bronze, never in brass or tinplate. A web search found nothing on the firm
(2026-10-19). Same shape as the 33 private tokens excluded on 2026-09-13
(`exclusions/danish_realm.yml`, `exonumia`, e.g. «Østerbros
Husholdningsforening» 1 / 2 / 5 / 10 Øre). They escaped TODO DC's authority
pattern because the name carries none of `selskab|forening|fabrik|…`.

Options: (a) exclude the eight as `exonumia` (§9.2), like the 2026-09-13 set;
(b) leave them undated (they stay off the page either way).

## Row 8 — bare and house names (analysis 2026-10-19)

| Record | KMM | Reading | Could date it |
|---|---|---|---|
| `kmk-133321` | «Christian», «Danmark ?», FP 9374.116 | Sæby Kirke excavation (row 3a), nothing else | no |
| `kmk-430264` | «Frederik», Holsten-Gottorp, 4 skilling lybsk, «rytter» | Gottorp duke Friedrich — II (1586–87), III (1616–59) or IV (1694–1702) | every dated Gottorp «Friedrich» 2 / 4 Schilling lybsk in final is Friedrich III (4, 1616–1659) — an assumption by analogy, not a source |
| `kmk-687750`, `kmk-687751` | «Frederik», Danmark, place «Gottorph», 2 schilling lybsk | same; they sit in `danish_realm` | same analogy; plus relocation to `gottorp_duchy` |
| `kmk-372978` | «Karl Frederik», place «Slesvig-Holsten-Gottorp», Søsling lybsk | Duke Karl Friedrich (1702–1739, already in the Gottorp table) | yes, once relocated to `gottorp_duchy`; then off the page by the 1656 window |
| `kmk-122261`, `kmk-122262`, `kmk-354144`, `kmk-353471` | «Johan Frederik (af Gottorp)», 4 skilling lybsk; two carry «Jungk 316» | Johann Friedrich of Holstein-Gottorp, archbishop of Bremen (1596–1634, Numista 129842); Jungk = *Die Bremischen Münzen* (1875) | yes, once relocated to `erzbisthum_bremen_verden` (where his other 25 coins are) with a Bremen reign entry; off the Denmark page (entity not consumed) |
| `kmk-690101` | «Johan», Malmø, hvid | King Hans (IOHANNES), 1481–1513 | yes, ruler correction «Johan» (!) → «Hans» (?), seed `_source_errata` |
| `kmk-83149` | «Alexander», Slesvig-Holsten, «Lange» without number, silver, 0,0 g | Duke Alexander of Sønderborg | yes, a Sønderborg table entry with a source |

## Row 9 — modern and foreign (analysis 2026-10-19)

| Record | KMM | Reading |
|---|---|---|
| `kmk-673472`, `kmk-673473` | «Carl 15.», Norge, Species | Carl XV, 1859–1872 — Norway under Sweden, after `danish_norway`'s 1814 window |
| `kmk-716178` | «Margrethe 2», 20 kr, «påklistret billede af Jellingestenen», `Mønt/Polet` | a modern 20-krone piece with a pasted picture; after 1914 |
| `kmk-299333` | «Frederik 9», 2 øre | 1947–1972; after 1914 |

All four are outside the mission's 1914 upper bound and off the page anyway.
Options: (a) exclude as `out_of_scope`; (b) leave undated.

## Side finding — finals left behind by a vanished class (2026-10-19)

Four of the 66 (`unified-kmk-740345/7/9/51`, Rytterpenning) are finals whose
class no longer exists: the seed was thinned into a sibling (`kmk-740347` →
`kmk-166757`). The scan over every final: **54 such finals outside
`_unclassified`** (842 inside it), three causes — Hede sub-letter splits
(8, e.g. `unified-dk-hede-nc5h32` next to `unified-dk-hede-nc5h32a`, July
2026, `202a5c1`), KMM thinning (14), seed gone (32). Absorb keeps them on
purpose (`_final_is_curated`: a fuss or a note), but never migrates that
curation to the successor, so 22 render as duplicates of a same-class
successor and **9 carry a classification their successor lacks** (Hede nc5h32,
nc5h37, nc5h56, nc5h68, nc5h69 under `9_25_thaler` I while the
`…a` class sits in `seed_unsorted`; two `9_thaler` II 1/16 Speciedaler;
two Braunschweig ikmk). Not a row of this plan — a pipeline defect for its own
session.

**Decision and outcome, rows 5, 8, 9 (curator 2026-10-19: «роби всі крім тих
де припущення»; «Johan» → Hans by the ruler normaliser, not by an erratum;
undated coins must still reach the page).**
- `33994e6` (code): Alexander of Sønderborg 1622–1627; new Bremen table,
  Johann Friedrich 1596–1634; bare «Johan» / «Johann» = King Hans in
  `danish_realm` / `danish_norway` only (in the duchies a bare Johann can be
  Hans der Jüngere); «Johannes» left out.
- `5793d28` (data): row 5 — the eight Aahuset pieces `exonumia`; row 9 — four
  `out_of_scope`; `kmk-372978` → `gottorp_duchy` (1702–1739 (?), off the page
  by the 1656 window); `kmk-354144` + `kmk-353471` (Jungk 316) →
  `erzbisthum_bremen_verden` as one class (1596–1634 (?), entity not on the
  page); `kmk-690101` Hvid Malmø now 1481–1513 (?) (the re-flow in `fea1313`
  already carried it).
- build fix (undated coins render, see above).
- Left: `kmk-430264`, `kmk-687750`, `kmk-687751` (Gottorp «Frederik» — II, III
  or IV), `kmk-122261`, `kmk-122262` («Johan Frederik» without index — Bremen
  or Lübeck bishopric), `kmk-133321` (nothing to date it).
- `kmk-83149` «Alexander» relocated `royal_holstein` → `sonderburg_duchy`
  (curator 2026-10-19), now 1622–1627 (?).
- Found on the way: seed `kmk-122261` lists `kmk-354144` in `_thinned_from`
  while `kmk-354144` is still its own seed, so KMM 354144 is cited on two
  finals — KMM thinning, same family as the vanished-class finals above.
