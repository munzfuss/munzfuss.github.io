# Schleswig and the town of Flensborg 1350-1460 — who held them, under which title

> Opened 2026-11-02 at the curator's request («треба чітко визначити
> приналежність в 1350-1460 рр»), to decide which of the Flensborg town coins
> (entity `flensborg_medieval`, Lindahl 1955 s. 74-76) belong on the Denmark
> page under SOURCES §13.16 (a hierarchical tie to Denmark AND a compatible
> standard).
>
> **Scope.** The holder of the Duchy of Schleswig and, separately, of the town
> of Flensborg, year by year 1350-1460, and the legal title each held it under
> (duke, pledge-holder, hereditary fief-holder of the Danish crown, the crown
> itself). **Excluded:** the duchy after 1460 (king and duke in one person) and
> the 1544 partition — `duchy_of_schleswig_entity.md`; the Flensborg coins'
> standard and typology — Lindahl 1955 / Jesse 1928, summarised in
> `build_lindahl_1955_seed.py` and the entity text in `issuing_entities.yml`;
> Holstein (an imperial fief, never in question here).
>
> **Status 2026-11-02:** sources gathered; the decision is the curator's (§4).
> The interim filter committed in `01aebf2` (`year_to: 1375`) rests on the
> premise «Flensborg was Danish until 1375», which §2 shows to be wrong for the
> town; see §4.

## §1. The constant: Schleswig was a Danish fief throughout

The duchy as such was held of the Danish crown for the whole window; what
changes is who held it and how. `duchy_of_schleswig_entity.md` Q1 has the
general statement (Wikipedia DA: «*var i modsætning til Holsten dansk
lensområde*»). The 1326 Constitutio Valdemariana forbade one person to be both
king and duke: Märcher 2018 (Denar til daler), s. 338: «*Konstitutionen forbød
at samme person kunne være hertug af Sønderjylland og dansk konge*»; Wikipedia
DE «Herzogtum Schleswig» §5.3: «*die Constitutio Valdemariana …, die eine
gemeinsame Regierung von Dänemark und Schleswig verbot*».

## §2. Year by year

| Years | Duchy held by | Town of Flensborg held by | Title / tie | Source |
|---|---|---|---|---|
| c. 1340-1364 | Duke Valdemar (V/III) of Sønderjylland, Abel line; much of the land pledged | **The Holstein (Schauenburg) counts** — they walled the town c. 1345 «to secure their rule» | Duke = vassal of the crown; counts = pledge-holders | Wikipedia DE «Flensburger Stadtbefestigung»: «*Zur Mitte des 14. Jahrhunderts beherrschten die Schauenburger Grafen das Herzogtum Schleswig*»; «*Um ihre Herrschaft zu sichern … ließen die Brüder Heinrich von Holstein und Nikolaus von Holstein um 1345 die Stadt befestigen*». Dengang.dk «Flensborg – i begyndelsen (1)» (2010): «*Grev Henrik tillod, at borgerne byggede en mur rundt om byen*» |
| 1358 | (war) | Valdemar Atterdag raids the duchy | — | Dengang.dk: «*Valdemar Atterdag tog på togt i hertugdømmet i 1358*» |
| 1360 | Duke Valdemar and son Henrik bind themselves with the king at Kalundborg | — | vassal duke | Kroman 1971 (Rigslovgivning indtil 1400), s. 239: «*Kong Valdemar 4. Atterdag og hans søn hertug Kristoffer på den ene side og hertug Valdemar og hans søn Henrik af Sønderjylland …*» |
| 1364-1375 | Duke Henrik; the Holstein counts hold all South Schleswig in pledge | Holstein counts until late 1372 | as above | lex.dk «Henrik Valdemarsen» (summary; reuse restricted): the counts «*havde hele Sydslesvig i pant*»; Wikipedia DA «Henrik af Sønderjylland»: after 1364 «*sad Holstenerne inde med Syd- og størstedelen af Mellemslesvig*» |
| late 1372-1375 | Henrik submits to the king (1373) | **The king (Valdemar Atterdag)** takes Flensborg | crown | Dengang.dk: «*Valdemar erobrede i slutningen af 1372 med en stor troppestyrke Flensborg*»; Wikipedia DA «Henrik af Sønderjylland»: «*havde forliget sig med kongen, gav han sig ganske denne i vold*»; DBL (Kai Hørby) «Valdemar 4. Atterdag»: «*var ved sin død i færd med at vinde væsentlige dele af Sønderjylland tilbage til den danske krone*» |
| 1375 | Henrik dies (late summer); the Abel line extinct | — | — | Wikipedia DA: «*I eftersommeren 1375 døde hertugen*» |
| 1375-1386 | The Holstein counts take the duchy without a grant | Holstein counts («*da Valdemar Atterdag døde, gik alt hvad kongen havde erobret tabt*») | **no title** — seizure | Hauberg 1886, s. 153: «*Efter den sønderjydske Hertug Henriks Død i Aaret 1375 tiltoge de holstenske Grever sig Magten i Hertugdømmet*»; Dengang.dk; DBL Hørby: «*holstenerne (ud over deres panterettigheder) nu også arvede hertugdømmet*» |
| 1386 (15 Aug, Nyborg) → 1404 | Gerhard VI and the Rendsburg line, **hereditary fief of the Danish crown** | Holstein counts; Gerhard's 1398 privilege for the town | hereditary fief-holders of the crown | Hauberg 1886, s. 153: Margrethe «*nødt til at tilstaa dem denne Besiddelse som et arveligt og udeleligt Lehn*»; Wikipedia DE «Herzogtum Schleswig» §5.3: «*erwirkten die Schauenburger in Nyborg ihre erbliche*» [Belehnung]; Wikipedia EN «Treaty of Nyborg (1386)»: signed «*on 15 August 1386*»; Dengang.dk: «*Fra Gerhard stammer det ældst bevarede privilegiebrev af 1398 for Flensborg*» |
| 1404-1409 | Gerhard VI killed in Dithmarschen 1404; widow Elisabeth for the minor sons | Elisabeth | fief-holders (minority) | Wikipedia DE «Herzogtum Schleswig» §5.3: «*Als der Schauenburger Gerhard VI. 1404 in Dithmarschen umkam*»; ADB «Adolf VIII.» (Jansen 1875, Bd 1 S. 110): «*1404 von den Dithmarschen erschlagenen*» |
| 1409 (Sept, Hindsgavl) → 1431 | war between the crown and the counts from 1409/10 | **The Danish crown** — pledged to Margrethe/Erik 1409; Kolding 1411 for five years; Duburg built 1411; held through 1431 | crown, first as pledge, then by possession | Hanserecesse I/6 (Koppmann 1889), s. 27 n. 3: «*Flensburg war König Erich 1409 Sept. 21 auf ein Jahr verpfändet worden und der Vertrag zu Kolding 1411 Mrz 24 hatte es ihm auf fünf Jahre gelassen*»; Dengang.dk: «*I september 1409 blev der på Hindsgavl afsluttet overenskomst, hvor Elisabeth pantsatte Flensborg og Nyhus til dronningen*»; Wikipedia DE «Flensburg»: «*Im selben Jahr wurde die Duburg auf dem Marienberg errichtet*» |
| 1421 | Fehmarn arbitration splits | the counts' arbiters order the king to surrender Flensborg — i.e. the king holds it | — | Hanserecesse I/7 (Koppmann 1893), s. 196: «*das Herzogthum Schleswig den Holstenherren zuerkannte und dem König die Herausgabe Flensburgs und Niehuus auferlegte*» |
| 1424 (Ofen) | Sigismund's court: the duchy adjudged AWAY from the counts | king | — | Hanserecesse I/7, Einleitung (pdf 18, printed page not established): «*auf dem Rechtstag zu Ofen, Juni 24—28, wird das Herzogthum Schleswig den Holstenherren abgesprochen*» |
| 1431 | the counts take the town (Palm Sunday) and the castle (7 Sept) | **Holstein counts** | conquest | ADB «Adolf VIII.»: «*die Einnahme Flensburgs, in das die beiden Grafen am Palmsonntag einzogen*»; Hanserecesse II/1 (Ropp 1876), s. 10 (25 Apr 1431): «*dass die Herzöge auch die Burg einzunehmen hoffen*»; s. 39: «*am 7. Sept. erfolgten Falles von Flensburg*» |
| 1435 (Vordingborg) | Adolf VIII keeps Schleswig as far as he holds it, for life + two years to his heirs | Adolf VIII | life tenure by treaty | ADB «Adolf VIII.»: «*Schleswig, so weit er es besetzt hat, sammt Fehmarn und Friesland auf Lebenszeit … und seinen Erben noch zwei Jahre nach seinem Tode überläßt*» |
| 1440 (30 Apr, Kolding) → 1459 | Adolf VIII, **hereditary fief of the Danish crown** | Adolf VIII | hereditary fief-holder | ADB «Adolf VIII.»: «*Am 30. April 1440 überträgt ihm Christof … zu Kolding das „Herzogthum zu Schleswig“ … zu einem „rechten Erblehn“*»; Hanserecesse II/2 (Ropp 1878), s. 288 n. 1: «*H. Adolf erhielt hier die Belehnung mit Schleswig*» |
| 1459 (4 Dec) | Adolf VIII dies; the Schauenburg line in Schleswig extinct | — | — | ADB: «*1459 Dec. 4 des guten Herzogs Tod*» |
| 1460 (Ribe, 5 Mar) | Christian I elected duke — king and duke in one person | the king-duke | crown | Andersen 1989 (Rigslovgivning 1397-1513), nr. 26, s. 118: «*Kristian 1.s privilegium til Slesvig, Holsten og Stormarn*» (5 marts 1460) |

**Summary for the town, by title:**

| Years | Flensborg under | Tie to the Danish crown |
|---|---|---|
| c. 1340-1372 | Holstein counts (pledge-holders) inside the duke's fief | indirect: a Danish fief, held by pledge-holders of its vassal duke |
| 1372-1375 | the king | direct |
| 1375-1386 | Holstein counts, no title | contested — a Danish fief seized without a grant |
| 1386-1409 | Holstein counts, hereditary fief | formal vassals of the crown |
| 1409-1431 | the king | direct |
| 1431-1440 | Holstein counts / Adolf VIII (life tenure from 1435) | by treaty with the crown |
| 1440-1459 | Adolf VIII, hereditary fief | formal vassal of the crown |
| 1460- | the king as duke | direct |

## §3. The Flensborg coins against §2

| Coin (our final) | Lindahl 1955 | Hauberg 1886 / Galster 1936 | Numista | Under whom, by each dating |
|---|---|---|---|---|
| Hvid/Witten, two leopards, Jesse 339 (`c-9ed6691b`) | ca. 1350 – recess 1379/81 (s. 74) | ca. 1388-1395, after the 1386 fief (Hbg s. 154; Galster: «*nach der Verleihung 1386*») | ND 1359-1378 | Lindahl/Numista: the counts as pledge-holders (to 1372) + the king 1372-75 + the counts untitled 1375-81. Hauberg/Galster: fief-holders after 1386 |
| Viertelwitten, Jesse 340 (`c-6f2070e7`) | as above (s. 75) | Topenning, ca. 1388-1395 (Hbg s. 154) | — | as above |
| Witten, nettle leaf, Jesse 371 (`c-f7114763`) | after recess 1379/81 (s. 75) | after 1375, before the counts' recognised possession, i.e. before 1386 (Hbg s. 153); Galster «*nach 1375*» | — | untitled counts 1375-1386 (both datings agree on that interval) |
| Dreling, Jesse 427 (`c-fae94ebf`) | after recess 1392 (s. 76; n. 4: perhaps ten years earlier) | ca. 1400, contemporary with the Lübeck dreilinge of 1403 (Hbg s. 155-156) | ND 1400-1425 | fief-holders 1386-1409 |

The documentary record of the coinage itself (Jesse 1928, s. 69, 86):
Flensburg money is first recorded 1358 («*1358 zuerst urkundlich*»), tested at
Lübeck 1359, and banned with Kiel's and Itzehoe's in 1369 — all in the years
the counts held the town. The coins name the town and the Holstein lords
(«MONETA HOLSACIE»), never the king.

## §4. What this means for the page — for the curator

1. **The interim filter's premise is wrong for the town.** «Before 1375 =
   Danish» holds for the duke, not for Flensborg: the town was the counts'
   from c. 1345 to late 1372 and theirs again from 1375. Under the
   *factual-power* reading, the only Danish-held window before 1409 is late
   1372-1375, and no Flensborg type is dated into it alone; the leopard hvid
   and viertelwitten (1350-1381) are counts' coinage under that reading too.
2. **Under the *formal-fief* reading** — the one the page already applies to
   Gottorp (on the page until 1656 as the crown's vassal) and the one
   SOURCES §13.16 states («the land was a Danish fief or otherwise
   subordinate») — the whole window except **1375-1386** is a Danish fief held
   by someone with a title from the crown or its duke. Only the nettle-leaf
   witten (Jesse 371) falls wholly inside the untitled 1375-1386 interval,
   by both Lindahl's and Hauberg's dating.
3. The two readings give opposite page contents:
   - factual power → no Flensborg coin on the page;
   - formal fief → the leopard hvid, viertelwitten and dreling on the page,
     the nettle-leaf witten off it (or on it, if a fief seized and
     regranted in 1386 is read as continuous).
   The curator decides; the consumes `year_to` in `denmark.yml` then becomes
   either the entity's removal or an exclusion of Jesse 371 alone.

## §5. Open questions

- **Who held Flensborg 1350-1357 exactly — the counts or duke Valdemar?** The
  1345 walls and «*Zur Mitte des 14. Jahrhunderts*» point to the counts; no
  source here dates the town's hand-over year by year. *Settled by:* the
  Flensborg Stadtgeschichte (e.g. Flensburg — Geschichte einer Grenzstadt,
  1966) or Danmarks Riges Breve for the 1340s-1350s pledge deeds.
- **Did the king hold Flensborg continuously 1411/1416-1431?** Kolding 1411
  gave it for five years; the 1421 award and the 1431 siege show the king
  still holding it, the years between are not checked. *Settled by:*
  Hanserecesse I/6-I/7 for 1416-1420.
- **When exactly did the counts retake Flensborg after 1375?** Dengang.dk says
  only that the king's conquests were lost at his death and «*Nyhus faldt
  samme efterår*». *Settled by:* a regional history or the 1376 sources.
- **Lindahl vs Hauberg/Galster on the order of the leopard and nettle-leaf
  types** — unresolved in the literature; Lindahl 1955 is the later revision
  and Jesse 1928 (s. 86) already discusses Flensburg 339/340 under 1367.
  This matters only under the formal-fief reading (§4.2).

## §6. Provenance notes

- Dengang.dk is an unsigned popular-history site (2010); it is used here only
  where it agrees with a scholarly source or gives a dated event the others
  do not contradict (1372, 1398, 1409 Hindsgavl). Its 1409 pledge agrees with
  Hanserecesse I/6 s. 27 n. 3.
- Wikipedia DE «Flensburger Stadtbefestigung» and «Flensburg» are unsourced at
  the sentence level for the 1345 walls; treat as secondary.
- lex.dk «Henrik Valdemarsen» was read in summary only (the site restricts
  reuse); its pledge statement agrees with Wikipedia DA «Henrik af
  Sønderjylland».
- Hauberg 1886 and Galster 1936 give one dating scheme (Galster follows
  Hauberg); Lindahl 1955 revises it. They are not independent on the
  typology.

Web sources read 2026-11-02:
https://de.wikipedia.org/wiki/Herzogtum_Schleswig ·
https://de.wikipedia.org/wiki/Flensburger_Stadtbefestigung ·
https://de.wikipedia.org/wiki/Flensburg ·
https://de.wikipedia.org/wiki/Flensburger_Wappen (the town seal of 1386 is the
first attestation of the arms; the nettle leaf added 1480 or 1495) ·
https://da.wikipedia.org/wiki/Henrik_af_S%C3%B8nderjylland ·
https://lex.dk/Henrik_Valdemarsen ·
https://biografiskleksikon.lex.dk/Valdemar_4._Atterdag ·
https://dengang.dk/flensborg-i-begyndelsen-1/ ·
https://de.wikisource.org/wiki/ADB:Adolf_VIII. ·
https://en.wikipedia.org/wiki/Treaty_of_Nyborg_(1386) (its infobox says 1384,
its text 15 August 1386 — the text agrees with Hauberg's 1386).
Local: Hauberg 1886, Galster 1936 (galtysk), Märcher 2018, Kroman 1971,
Andersen 1989, Jesse 1928, Hanserecesse I/6, I/7, II/1, II/2 — all in
`scripts/cache`, found with `kb.py search`.

## §7. Cross-references

- `duchy_of_schleswig_entity.md` — the duchy as an entity, 1460 onwards.
- `docs/SOURCES.md` §13.16 — the page-inclusion test.
- `data/v2/locations/denmark.yml` — the `flensborg_medieval` consumes entry.
- `data/i18n/issuing_entities.yml::flensborg_medieval` — its description
  (written before this dossier; its «under the Sønderjylland dukes and the
  Holstein counts» quote from Märcher 2018 s. 368 stands).
