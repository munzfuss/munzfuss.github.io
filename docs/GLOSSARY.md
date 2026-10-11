# Numismatic Glossary (DE / EN / UK)

Reference for consistent terminology across languages. Used when writing YAML i18n fields.

> **These are GENERIC terms only.** A NAMED standard (`Reichsdukatenfuß`, `Kurantmøntfod`,
> `9¼-Thaler-Fuß`), a named institution or a named decree never appears in this table and is
> never translated or transliterated in any language — a gloss may follow in parentheses after
> the original, never in place of it. See CLAUDE.md §2 tier 1-2 and the i18n policy.

## Münzfuß concepts

| DE (period-correct) | EN | UK |
|---|---|---|
| Müntzfuß | Münzfuß / coinage standard | стопа / монетна стопа |
| Kurantgeld | current money / full-value coinage | курантні гроші |
| Kurantmünze | kurant coin / full-value coin | курантна монета |
| Scheidemünze | Scheidemünze / small change / token coin | розмінна монета / білонна монета |
| Tarifmünze | tariff coin / fiat-valued coin | тарифна монета |
| Gedenkmünze | commemorative coin | пам'ятна монета |
| Probeprägung | pattern coin / trial strike | пробний карбунок |
| Rechnungseinheit | unit of account | розрахункова одиниця |
| Rechnungsmünze | money of account | рахункова монета |
| Handelsmünze | trade coin | торгова монета |
| Giralgeld | giro money / book money | безготівкові гроші |
| Bancovaluta | bank currency | банкова валюта |
| Banknote / Kassenanweisung | banknote / treasury note | банкнота / казначейський знак |
| Courant / Kurant | current / courant | курантний |
| Specie | specie | спеціє |
| Legation | legation | легація |

## Metals and weights

| DE | EN | UK |
|---|---|---|
| Feingehalt | fineness | проба |
| Feingewicht | fine weight | чиста вага |
| Raugewicht | gross weight | повна вага |
| Remedium | tolerance / allowance | допуск / ремедіум |
| Seigniorage / Schlagschatz | seigniorage | сеньйораж |
| Abschlag (Ggs. Vollprägung) | trial strike off-metal | відбитка в іншому металі |
| Gold | gold | золото |
| Silber | silver | срібло |
| Billon | billon | білон |
| Kupfer | copper | мідь |

## Weight units (historical)

| DE | EN | UK |
|---|---|---|
| Cöllnische Marck (233,856 g Silber, or 233,856 g Gold) | Cologne mark | кельнська марка |
| Wiener Marck (233,890 g) | Vienna mark | віденська марка |
| Bayrische Marck (233,950 g) | Bavarian mark | баварська марка |
| Lot (1/16 Mark = 14,616 g) | Lot (1/16 mark) | лот |
| Quintin (¼ Lot = 3,654 g, Cologne weight; not defined in the cached Wilcke text) | quintin (¼ lot) | квінтин |
| Karat | carat (gold) | карат |
| Grän (1/12 Karat) | grain (1/12 carat) | гран |
| Zollpfund (500 g, ab 1857) | Zollpfund (customs pound) | цольфунт |

## Denominations

| DE | EN | UK |
|---|---|---|
| Thaler | Thaler | талер |
| Speciesthaler / Speciestaler | Speciesthaler | спецієсталер |
| Kuranttaler | Kuranttaler / courant taler | курант-талер |
| Konventionsthaler | Convention thaler | конвенційний талер |
| Vereinsthaler | Union thaler (Vereinsthaler) | союзний талер |
| Gulden | Gulden | гульден |
| Kronthaler | Krone thaler | кронталер |
| Gute Groschen | good groschen | добрий гроше |
| Silbergroschen | silver groschen | срібний гроше |
| Mariengroschen | Mariengroschen | марієнгроше |
| Pfennig | pfennig | пфеніг |
| Kreutzer / Kreuzer | kreutzer | крейцер |
| Heller | heller | хелер |
| Schilling | schilling | шилінг |
| Sechsling (½ Schilling) | sechsling (half schilling) | зексьлінг |
| Dreiling (¼ Schilling) | dreiling (quarter schilling) | дрейлінг |
| Mark (Hamburg/Lübeck) | mark (Hanseatic) | марка (ганзейська) |
| Grote (Bremen) | grote | гроте |
| Schwaren (Bremen) | schwaren | шварен |
| Dukat | ducat | дукат |
| Friedrich d'or / Pistole | Friedrich d'or / pistole | пістоль |
| Louisdor | Louis d'or | луїдор |
| Skilling / Skilling Danske | skilling (Danish) | сколінг / сколінг данске |
| Rigsdaler | rigsdaler | рігсдалер |
| Rigsbankdaler | rigsbankdaler | рігсбанкдалер |
| Krone (dänisch, 4 Mark Danske) | krone (Danish, = 4 Danish mark) | крона (данська) |

## Rulers & titles (preserve literal form)

| German form | English form | Ukrainian form |
|---|---|---|
| Christian IV. | Christian IV | Крістіан IV |
| Friedrich III. | Frederik III | Фредерік III |
| Christian V. | Christian V | Крістіан V |
| Friedrich IV. | Frederik IV | Фредерік IV |
| Karl Friedrich | Charles Frederick | Карл Фрідріх |
| Christian VII. | Christian VII | Крістіан VII |
| Frederik VI. | Frederik VI | Фредерік VI |
| Christian VIII. | Christian VIII | Крістіан VIII |
| Frederik VII. | Frederik VII | Фредерік VII |
| Christian Albrecht | Christian Albrecht | Крістіан Альбрехт |

Note: keep `Frederik` (Danish) not `Friedrich` (German) for Danish kings. Keep "Christian" for Danish spelling where it matches.

## Mints

Keep literal German/Danish spelling across languages:
- Tönning (Tønning in Danish contexts)
- Altona
- Glückstadt
- Kopenhagen / København (context-dependent)
- Poppenbüttel
- Rendsburg (Holstein-Gottorp interim 1716–1720)
- Kongsberg (Norway)
- Hamburg (Hanseatic city — see `data/locations/hamburg.yml`)
- Lübeck (Hanseatic city — see `data/locations/lubeck.yml`)

## Political / territorial entities

| DE | EN | UK |
|---|---|---|
| Heiliges Römisches Reich (HRR) | Holy Roman Empire (HRE) | Священна Римська імперія (СРІ) |
| **1537–1814** · Königreich Dänemark und Norwegen (Dänisch-norwegischer Verbund) | Royal Danish-Norwegian Realm (Denmark-Norway) | Королівство Данії і Норвегії (Дансько-норвезький союз) |
| **1814–1864** · Dänischer Gesammtstaat (Helstaten) | Danish Unitary State (Helstaten) | Данська унітарна держава (Helstaten) |
| Schleswig-Holstein-Herzogthümer | Schleswig-Holstein duchies | Герцогства Шлезвіг-Гольштейн |
| Königliche Holsteinische Antheil | Royal Danish portion of Holstein | Королівсько-данська частина Гольштейну |
| Hansestadt | Hanseatic city | Ганзейське місто |
| Provinz Schleswig-Holstein | Province of Schleswig-Holstein | Провінція Шлезвіг-Гольштейн |

**Notes:**
- The Danish realm has two distinct period names that MUST NOT be conflated:
  - **1537–1814** (Reformation → Treaty of Kiel): «Königreich Dänemark und Norwegen» / «Royal Danish-Norwegian Realm» / «Королівство Данії і Норвегії». Used while Norway was part of the Danish dual monarchy. Acceptable shorthand: «Dänisch-norwegischer Verbund» / «Denmark-Norway» / «Дансько-норвезький союз».
  - **1814–1864** (post-Kiel → Second Schleswig War): «Helstaten» — the period-Danish term for the post-Norway centralised state including Schleswig-Holstein, Iceland, Greenland, Faroe Islands. DE «Dänischer Gesammtstaat» (period-correct double-«mm») is the canonical German rendition; EN «Danish Unitary State» (preferred) or «Danish composite state»; UK «Данська унітарна держава». Always preserve the Danish word «Helstaten» in parentheses as a proper-noun anchor.
- Avoid UK transliterations like «Гезамтштат» (DE→UK calque, awkward) or verbose «сукупно-державний устрій» — use «Данська унітарна держава (Helstaten)».
- Spell out HRR/СРІ in tooltips and prose where the abbreviation isn't already in context (reader may be unfamiliar). Acceptable in inline tags / short labels.

## Phase & period markers

| DE | EN | UK |
|---|---|---|
| Phase | Phase | Фаза |
| ab, von, seit | from, since | з, від |
| biß (period-correct) / bis | until | до |
| ca. | c. / ca. | бл. / приб. |
| geprägt | minted / struck | карбовано |
| eingeführt | introduced | впроваджено |
| aufgehoben | abolished | скасовано |
| umbenannt | renamed | перейменовано |

## Methodological terms

| DE | EN | UK |
|---|---|---|
| Soll | target / nominal | цільове |
| Ist | actual | фактичне |
| Remedium | tolerance | допуск |
| Fuß-Äquivalent | fuss equivalent | еквівалент стопи |
| Silberparität | silver parity | срібний паритет |
| Kursverhältnis | exchange rate | курсове співвідношення |
| Gold-Silber-Ratio | gold-silver ratio | відношення золота до срібла |
| Legende | legend (inscription) | легенда (напис) |
| Abschnitt (da. Afsnit) | exergue (the lower part of the field under the main scene) | екзерг (нижній відрізок поля під основною сценою) |
| Obverse / Vorderseite | obverse | аверс / лицева сторона |
| Reverse / Rückseite | reverse | реверс / зворотна сторона |
| Stempelschneider | die-cutter | різьбяр штемпелів |
| Münzmeister (MM) | mintmaster | монетний майстер |

## Phrases and connectors

| DE | EN | UK |
|---|---|---|
| «nicht auf der Münze» | "not on the coin" | «не на монеті» |
| «Rechnungsäquivalent» | "accounting equivalent" | «розрахунковий еквівалент» |
| «historiographischer Beiname» | "historiographical nickname" | «історіографічна назва» |
| «innerhalb Remedium» | "within tolerance" | «в межах допуску» |
| «dual-denominiert» | "dual-denominated" | «подвійно деноміновано» |
| «nach Analogie zu» | "by analogy to" | «за аналогією до» |
| «in keiner Online-Quelle belegt» | "not documented in online sources" | «не задокументовано в онлайн-джерелах» |

## Ukrainian wording decisions (curator-corrected, 2026-10)

Each row is a choice the curator made while correcting a text, so the same stumble is not
repeated in the next fuss. «Don't write» is what read badly or wrongly; «Write» is the decision.
These rules concern the UK fields; the DE / EN / DA fields get the equivalent change in the
same edit (every wording edit goes into all languages).

| Don't write (UK) | Write | Why |
|---|---|---|
| «пробірний аналіз», «пробірний акт» | «визначення проби»; «акт перевірки проби» | «пробірний» reads as «пробірка» (test tube), not as «проба» (fineness) |
| «вагомий» about weight («вагомі нобелі») | «важкий» («особливо важкі нобелі») | «вагомий» means influential, not heavy |
| «грейн», «грейнів» (1/12 карата) | «гран»: «10 гранів», «10½ грана» | the project already uses «гран» for Grän (see the term table and the 5760-гран figures); «гран» is the unit of mass, not «грань» (facet) |
| «нобельне золото» | «благородне золото»; «fint nobel Guld» («чисте благородне золото») | the direct translation of «nobel» is «благородний» |
| «Ribe карбував …» (a town as the subject, without saying it is a town) | «монетний двір у місті Ribe карбував …»; «нобелі з Ribe» | a reader who does not know Ribe takes it for a person |
| «відносять до …», «вважають …» (impersonal, when it is the project's own conclusion) | «можна вважати …», «технічно можна вважати …» | the conclusion is ours; the sentence says so with a modal, not an anonymous «they» |
| «напевно», «схоже», «мабуть» with no attribution | «імовірно» / «ймовірно»; «напевно» only when it renders a source's own «sikkert» and is attributed («за Wilcke … напевно») | §0b and §2a: certainty and hedging belong to the source, not to the text; «схоже» is conversational |
| «потрійні» for a weight | «втричі важчі за норму» (or «у середньому близько трьох лотів проти одного») | «потрійний» reads as a denomination (3 Nobel); weight and denomination are different things |
| «Період дії: 1496 → 1532» when the bar shows the years of striking | «Період карбування: 1496 → 1532»; «Період дії» only for legal validity | the two are different (coinage 1496–1532, legal basis from 1514) |
| a foreign-language quotation alone | the quotation in the source language, then the translation in parentheses in the field's language | applies to Danish, Dutch, French, English quotes in UK / DE / EN prose; in the DA field only non-Danish quotes need a translation |
| «Pragtmønter» without a gloss | «Pragtmønter» («парадні монети») on first mention; DE «Prunkmüntzen», EN «show coins», DA «pragtmønter» | the source's own term is kept; the gloss is ours |
| «Lod» in prose when a WEIGHT is meant | «лот» (1/16 кельнської марки) | «Lod» stays as the period form only in formal slots (a silver fineness «14 Lod»); weight in prose is «лот» |
| naming a decree in Ukrainian («Монетний ордонанс») | the original form in every language («Møntordning Christian II 1514», «Kongebrev», «Rigsraadets Brev») | CLAUDE.md §2 tier 1; a generic descriptor («королівський лист») may be translated |

**A gap in the record.** Write «з джерел невідомо» / «в джерелах не засвідчено» (DE «ist aus den Quellen
nicht bekannt», EN «is not known from the sources», DA «vides ikke ud fra kilderne»), never the
colloquial «джерела не кажуть» («the sources do not say»): sources do not speak, the record has a gap.

**Numbers in text.** Fineness derived from carats is written to five decimals («23½ Karat =
.97917», never «.979» as if exact); fine weight likewise («14,3115 g»). Source readings keep
the source's own figure.

**Layers of one description.** The card prose is a short summary of the standard; the phase
descriptions («details») carry the circumstances; do not duplicate a norm text in both — the
instrument block carries the norm.

## UI labels (for `data/i18n/ui.yml`)

| key | de | en | uk |
|---|---|---|---|
| nav.home | Startseite | Home | Головна |
| nav.language | Sprache | Language | Мова |
| col.nominal | Nominal | Denomination | Номінал |
| col.year | Jahr | Year | Рік |
| col.ruler | Herrscher | Ruler | Правитель |
| col.catalog | Katalog | Catalog | Каталог |
| col.metal | Metall | Metal | Метал |
| col.rough | Rau | Gross | Повна вага |
| col.fine | Fein | Fine | Чиста вага |
| col.diameter | Ø | Ø | Ø |
| col.mint | Müntzstätte | Mint | Монетний двір |
| col.note | Bemerkung | Note | Примітка |
| col.fuss | Soll · Δ · Fuß | Target · Δ · Fuss | Ціль · Δ · Стопа |
| col.source | Quelle | Source | Джерело |
| label.kurant | Kurantmünzen — Vollwertmünzen | Kurant coins — full-value coinage | Курантні монети — повноцінна монета |
| label.scheide | Scheidemünzen — Kleingeld | Scheide coins — small change | Розмінні монети — дрібні гроші |
| kurant.desc | Vollwertig · Nennwert ≈ Silberwert · vom Staat ohne oder mit geringem Aufschlag ausgegeben | Full value · face value ≈ silver content · issued without or with minor premium | Повноцінні · номінал ≈ вміст срібла · випущені без або з незначною надбавкою |
| scheide.desc | Billonmünzen · Nennwert > Silberwert · Differenz deckt Seigniorage-Gewinn der Krone · nur im lokalen Umlauf | Billon coins · face value > silver content · difference is state seigniorage · local circulation only | Білонні монети · номінал > вміст срібла · різниця — сеньйораж держави · лише локальний обіг |

This table is the canonical source; `data/i18n/ui.yml` copies it. Keep both in sync (or treat `ui.yml` as primary and auto-generate this table during updates).
