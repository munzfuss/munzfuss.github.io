# IKMK ↔ schleswig_holstein.yml — match report


169 IKMK records (Schleswig-Holstein-* + Holstein-Schauenburg in scope 1566–1914) matched against `data/locations/schleswig_holstein.yml`.


* **Strict match (catalogue-ref overlap)**: 10
* **Fuzzy match (high-confidence same coin, score≥7)**: 6
* **New Lange-# variant (IKMK has a Lange # we don't catalogue)**: 55 specimens across **12 unique Lange #**
* **Weak candidate (partial signal, score 4-6, no Lange#)**: 98
* **No match**: 0


## Strict matches — enrichment candidates


IKMK records sharing a Lange / Hede / Davenport reference with one 
of our coins. The `ikmk_adds` column shows fields IKMK provides that 
we currently lack on the matched coin.


| IKMK | year | our coin | reason | IKMK adds |
|---|---|---|---|---|
| [18284402](https://ikmk.smb.museum/object?id=18284402) | 1619-1619 | `km-9-hans-jr-sonderb-1619` | strict by lange 533a | inscription_obv, inscription_rev, diameter_mm |
| [18284403](https://ikmk.smb.museum/object?id=18284403) | 1619-1619 | `km-9-hans-jr-sonderb-1619` | strict by lange 533a | inscription_obv, inscription_rev, diameter_mm |
| [18284692](https://ikmk.smb.museum/object?id=18284692) | 1619-1619 | `km-9-hans-jr-sonderb-1619` | strict by lange 533a | inscription_obv, inscription_rev, diameter_mm |
| [18284693](https://ikmk.smb.museum/object?id=18284693) | 1619-1619 | `km-9-hans-jr-sonderb-1619` | strict by lange 533a | inscription_obv, inscription_rev, diameter_mm |
| [18284694](https://ikmk.smb.museum/object?id=18284694) | 1619-1619 | `km-9-hans-jr-sonderb-1619` | strict by lange 533a | inscription_obv, inscription_rev, diameter_mm |
| [18284695](https://ikmk.smb.museum/object?id=18284695) | 1619-1619 | `km-9-hans-jr-sonderb-1619` | strict by lange 533a | inscription_obv, inscription_rev, diameter_mm |
| [18284696](https://ikmk.smb.museum/object?id=18284696) | 1619-1619 | `km-9-hans-jr-sonderb-1619` | strict by lange 533a | inscription_obv, inscription_rev, diameter_mm |
| [18284714](https://ikmk.smb.museum/object?id=18284714) | 1621-1621 | `km-11-hans-jr-sonderb-1620` | strict by lange 542c | inscription_obv, diameter_mm |
| [18206321](https://ikmk.smb.museum/object?id=18206321) | 1664-1664 | `km-56-fr-iii-1666` | strict by lange 65 | inscription_obv, inscription_rev |
| [18206117](https://ikmk.smb.museum/object?id=18206117) | 1671-1671 | `bruun-14681-christian-glb-1672` | strict by lange 737 | inscription_rev, diameter_mm |

## Fuzzy matches (score≥7) — likely correct, spot-check


| IKMK | year | our coin | reason | IKMK adds |
|---|---|---|---|---|
| [18286827](https://ikmk.smb.museum/object?id=18286827) | 1620-1620 | `km-137411-ernst-1620` | fuzzy score=8 (year 1620≈1620, ruler ernst/schaumburg, weight 0.69≈0.68) | inscription_obv, inscription_rev, diameter_mm |
| [18286836](https://ikmk.smb.museum/object?id=18286836) | 1620-1620 | `km-137411-ernst-1620` | fuzzy score=8 (year 1620≈1620, ruler ernst/schaumburg, weight 0.68≈0.68) | inscription_obv, inscription_rev, diameter_mm |
| [18286846](https://ikmk.smb.museum/object?id=18286846) | 1620-1620 | `km-137411-ernst-1620` | fuzzy score=7 (year 1620≈1620, ruler ernst/schaumburg, nominal 'pfennig') | diameter_mm |
| [18286854](https://ikmk.smb.museum/object?id=18286854) | 1620-1620 | `km-137411-ernst-1620` | fuzzy score=7 (year 1620≈1620, ruler ernst/schaumburg, nominal 'pfennig') | diameter_mm |
| [18286856](https://ikmk.smb.museum/object?id=18286856) | 1620-1620 | `km-137411-ernst-1620` | fuzzy score=7 (year 1620≈1620, ruler ernst/schaumburg, nominal 'pfennig') | diameter_mm |
| [18286857](https://ikmk.smb.museum/object?id=18286857) | 1620-1620 | `km-137411-ernst-1620` | fuzzy score=7 (year 1620≈1620, ruler ernst/schaumburg, nominal 'pfennig') | diameter_mm |

## New Lange-# variants (potential YAML additions)


IKMK records that share ruler+year+line with one of our coins but cite a Lange # we don't have catalogued. These are *separate types* in Lange's classification — not duplicates of our existing entries. Worth adding to YAML as new coins (or, if Krause groups them under one KM #, as Lange-sub-variant notes).


Grouped by Lange # — 12 unique #s, 55 total specimens. Specimens of the same Lange # are usually multiple physical coins of the same type held in IKMK.


| Lange # | specimens | year(s) | ruler-line | sample IKMK |
|---|---:|---|---|---|
| `Lange (cf-only)` | 23 | 1618,1619,1620,1621 | sonderburg | [18284398](https://ikmk.smb.museum/object?id=18284398), [18284404](https://ikmk.smb.museum/object?id=18284404), [18284691](https://ikmk.smb.museum/object?id=18284691) |
| `Lange 339b` | 2 | 1618 | gottorf | [18284946](https://ikmk.smb.museum/object?id=18284946), [18285050](https://ikmk.smb.museum/object?id=18285050) |
| `Lange 339c` | 8 | 1619 | gottorf | [18285061](https://ikmk.smb.museum/object?id=18285061), [18285062](https://ikmk.smb.museum/object?id=18285062), [18285091](https://ikmk.smb.museum/object?id=18285091) |
| `Lange 34e` | 1 | 1623 | — | [18202375](https://ikmk.smb.museum/object?id=18202375) |
| `Lange 532` | 1 | 1618 | sonderburg | [18284272](https://ikmk.smb.museum/object?id=18284272) |
| `Lange 532b` | 3 | 1618 | sonderburg | [18284395](https://ikmk.smb.museum/object?id=18284395), [18284396](https://ikmk.smb.museum/object?id=18284396), [18284397](https://ikmk.smb.museum/object?id=18284397) |
| `Lange 533` | 3 | 1619 | sonderburg | [18284399](https://ikmk.smb.museum/object?id=18284399), [18284400](https://ikmk.smb.museum/object?id=18284400), [18284401](https://ikmk.smb.museum/object?id=18284401) |
| `Lange 535a` | 1 | 1618 | sonderburg | [18284698](https://ikmk.smb.museum/object?id=18284698) |
| `Lange 535b` | 3 | 1618 | sonderburg | [18284699](https://ikmk.smb.museum/object?id=18284699), [18284700](https://ikmk.smb.museum/object?id=18284700), [18284701](https://ikmk.smb.museum/object?id=18284701) |
| `Lange 536a` | 3 | 1619 | sonderburg | [18284707](https://ikmk.smb.museum/object?id=18284707), [18284709](https://ikmk.smb.museum/object?id=18284709), [18284710](https://ikmk.smb.museum/object?id=18284710) |
| `Lange 536b` | 6 | 1619 | sonderburg | [18284702](https://ikmk.smb.museum/object?id=18284702), [18284703](https://ikmk.smb.museum/object?id=18284703), [18284704](https://ikmk.smb.museum/object?id=18284704) |
| `Lange 944a` | 1 | 1622 | schaumburg | [18219260](https://ikmk.smb.museum/object?id=18219260) |

## Weak candidates (score 4-6, no Lange #)


Partial signal only — year + ruler-line. No Lange # in IKMK literatur to cross-walk against. Manual research needed; could be either an existing coin (we'd need to look up by inscription / weight pattern) or a new entry.


| IKMK | year | nominal | best our coin | reason |
|---|---|---|---|---|
| [18219857](https://ikmk.smb.museum/object?id=18219857) | 1666-1666 | Dukat | `km-56-fr-iii-1666` | weak score=5 (year 1666≈1666, nominal 'dukat', weight 3.43≈3.48) |
| [18285689](https://ikmk.smb.museum/object?id=18285689) | 1618-1618 | Doppelschilling (1/16 Tal | `km-137411-ernst-1620` | weak score=5 (year 1618~1620, ruler ernst/schaumburg) |
| [18285701](https://ikmk.smb.museum/object?id=18285701) | 1618-1618 | Doppelschilling (1/16 Tal | `km-137411-ernst-1620` | weak score=5 (year 1618~1620, ruler ernst/schaumburg) |
| [18285708](https://ikmk.smb.museum/object?id=18285708) | 1619-1619 | Doppelschilling (1/16 Tal | `km-137411-ernst-1620` | weak score=6 (year 1619≈1620, ruler ernst/schaumburg) |
| [18285714](https://ikmk.smb.museum/object?id=18285714) | 1619-1619 | Doppelschilling (1/16 Tal | `km-137411-ernst-1620` | weak score=6 (year 1619≈1620, ruler ernst/schaumburg) |
| [18285715](https://ikmk.smb.museum/object?id=18285715) | 1619-1619 | Doppelschilling (1/16 Tal | `km-137411-ernst-1620` | weak score=6 (year 1619≈1620, ruler ernst/schaumburg) |
| [18285716](https://ikmk.smb.museum/object?id=18285716) | 1619-1619 | Doppelschilling (1/16 Tal | `km-137411-ernst-1620` | weak score=6 (year 1619≈1620, ruler ernst/schaumburg) |
| [18285717](https://ikmk.smb.museum/object?id=18285717) | 1619-1619 | Doppelschilling (1/16 Tal | `km-137411-ernst-1620` | weak score=6 (year 1619≈1620, ruler ernst/schaumburg) |
| [18285718](https://ikmk.smb.museum/object?id=18285718) | 1619-1619 | Doppelschilling (1/16 Tal | `km-137411-ernst-1620` | weak score=6 (year 1619≈1620, ruler ernst/schaumburg) |
| [18285719](https://ikmk.smb.museum/object?id=18285719) | 1619-1619 | Doppelschilling (1/16 Tal | `km-137411-ernst-1620` | weak score=6 (year 1619≈1620, ruler ernst/schaumburg) |
| [18285720](https://ikmk.smb.museum/object?id=18285720) | 1619-1619 | Doppelschilling (1/16 Tal | `km-137411-ernst-1620` | weak score=6 (year 1619≈1620, ruler ernst/schaumburg) |
| [18285721](https://ikmk.smb.museum/object?id=18285721) | 1619-1619 | Doppelschilling (1/16 Tal | `km-137411-ernst-1620` | weak score=6 (year 1619≈1620, ruler ernst/schaumburg) |
| [18285722](https://ikmk.smb.museum/object?id=18285722) | 1619-1619 | Doppelschilling (1/16 Tal | `km-137411-ernst-1620` | weak score=6 (year 1619≈1620, ruler ernst/schaumburg) |
| [18285723](https://ikmk.smb.museum/object?id=18285723) | 1619-1619 | Doppelschilling (1/16 Tal | `km-137411-ernst-1620` | weak score=6 (year 1619≈1620, ruler ernst/schaumburg) |
| [18285724](https://ikmk.smb.museum/object?id=18285724) | 1619-1619 | Doppelschilling (1/16 Tal | `km-137411-ernst-1620` | weak score=6 (year 1619≈1620, ruler ernst/schaumburg) |
| [18285754](https://ikmk.smb.museum/object?id=18285754) | 1620-1620 | Doppelschilling (1/16 Tal | `km-137411-ernst-1620` | weak score=6 (year 1620≈1620, ruler ernst/schaumburg) |
| [18285773](https://ikmk.smb.museum/object?id=18285773) | 1620-1620 | Doppelschilling (1/16 Tal | `km-137411-ernst-1620` | weak score=6 (year 1620≈1620, ruler ernst/schaumburg) |
| [18285774](https://ikmk.smb.museum/object?id=18285774) | 1620-1620 | Doppelschilling (1/16 Tal | `km-137411-ernst-1620` | weak score=6 (year 1620≈1620, ruler ernst/schaumburg) |
| [18285782](https://ikmk.smb.museum/object?id=18285782) | 1620-1620 | Doppelschilling (1/16 Tal | `km-137411-ernst-1620` | weak score=6 (year 1620≈1620, ruler ernst/schaumburg) |
| [18285789](https://ikmk.smb.museum/object?id=18285789) | 1620-1620 | Doppelschilling (1/16 Tal | `km-137411-ernst-1620` | weak score=6 (year 1620≈1620, ruler ernst/schaumburg) |
| [18285792](https://ikmk.smb.museum/object?id=18285792) | 1620-1620 | Doppelschilling (1/16 Tal | `km-137411-ernst-1620` | weak score=6 (year 1620≈1620, ruler ernst/schaumburg) |
| [18285797](https://ikmk.smb.museum/object?id=18285797) | 1620-1620 | Doppelschilling (1/16 Tal | `km-137411-ernst-1620` | weak score=6 (year 1620≈1620, ruler ernst/schaumburg) |
| [18285803](https://ikmk.smb.museum/object?id=18285803) | 1620-1620 | Doppelschilling (1/16 Tal | `km-137411-ernst-1620` | weak score=6 (year 1620≈1620, ruler ernst/schaumburg) |
| [18285805](https://ikmk.smb.museum/object?id=18285805) | 1620-1620 | Doppelschilling (1/16 Tal | `km-137411-ernst-1620` | weak score=6 (year 1620≈1620, ruler ernst/schaumburg) |
| [18285814](https://ikmk.smb.museum/object?id=18285814) | 1620-1620 | Doppelschilling (1/16 Tal | `km-137411-ernst-1620` | weak score=6 (year 1620≈1620, ruler ernst/schaumburg) |
| [18285818](https://ikmk.smb.museum/object?id=18285818) | 1620-1620 | Doppelschilling (1/16 Tal | `km-137411-ernst-1620` | weak score=6 (year 1620≈1620, ruler ernst/schaumburg) |
| [18285902](https://ikmk.smb.museum/object?id=18285902) | 1620-1620 | Doppelschilling (1/16 Tal | `km-137411-ernst-1620` | weak score=6 (year 1620≈1620, ruler ernst/schaumburg) |
| [18285911](https://ikmk.smb.museum/object?id=18285911) | 1620-1620 | Doppelschilling (1/16 Tal | `km-137411-ernst-1620` | weak score=6 (year 1620≈1620, ruler ernst/schaumburg) |
| [18285912](https://ikmk.smb.museum/object?id=18285912) | 1620-1620 | Doppelschilling (1/16 Tal | `km-137411-ernst-1620` | weak score=6 (year 1620≈1620, ruler ernst/schaumburg) |
| [18285913](https://ikmk.smb.museum/object?id=18285913) | 1620-1620 | Doppelschilling (1/16 Tal | `km-137411-ernst-1620` | weak score=6 (year 1620≈1620, ruler ernst/schaumburg) |
| [18285916](https://ikmk.smb.museum/object?id=18285916) | 1620-1620 | Doppelschilling (1/16 Tal | `km-137411-ernst-1620` | weak score=6 (year 1620≈1620, ruler ernst/schaumburg) |
| [18285918](https://ikmk.smb.museum/object?id=18285918) | 1621-1621 | Doppelschilling (1/16 Tal | `km-137411-ernst-1620` | weak score=6 (year 1621≈1620, ruler ernst/schaumburg) |
| [18285924](https://ikmk.smb.museum/object?id=18285924) | 1621-1621 | Doppelschilling (1/16 Tal | `km-137411-ernst-1620` | weak score=6 (year 1621≈1620, ruler ernst/schaumburg) |
| [18285931](https://ikmk.smb.museum/object?id=18285931) | 1621-1621 | Doppelschilling (1/16 Tal | `km-137411-ernst-1620` | weak score=6 (year 1621≈1620, ruler ernst/schaumburg) |
| [18286200](https://ikmk.smb.museum/object?id=18286200) | 1621-1621 | Doppelschilling (1/16 Tal | `km-137411-ernst-1620` | weak score=6 (year 1621≈1620, ruler ernst/schaumburg) |
| [18286201](https://ikmk.smb.museum/object?id=18286201) | 1621-1621 | Doppelschilling (1/16 Tal | `km-137411-ernst-1620` | weak score=6 (year 1621≈1620, ruler ernst/schaumburg) |
| [18286202](https://ikmk.smb.museum/object?id=18286202) | 1621-1621 | Doppelschilling (1/16 Tal | `km-137411-ernst-1620` | weak score=6 (year 1621≈1620, ruler ernst/schaumburg) |
| [18286203](https://ikmk.smb.museum/object?id=18286203) | 1621-1621 | Doppelschilling (1/16 Tal | `km-137411-ernst-1620` | weak score=6 (year 1621≈1620, ruler ernst/schaumburg) |
| [18286204](https://ikmk.smb.museum/object?id=18286204) | 1621-1621 | Doppelschilling (1/16 Tal | `km-137411-ernst-1620` | weak score=6 (year 1621≈1620, ruler ernst/schaumburg) |
| [18286205](https://ikmk.smb.museum/object?id=18286205) | 1621-1621 | Doppelschilling (1/16 Tal | `km-137411-ernst-1620` | weak score=6 (year 1621≈1620, ruler ernst/schaumburg) |
| [18286206](https://ikmk.smb.museum/object?id=18286206) | 1621-1621 | Doppelschilling (1/16 Tal | `km-137411-ernst-1620` | weak score=6 (year 1621≈1620, ruler ernst/schaumburg) |
| [18286207](https://ikmk.smb.museum/object?id=18286207) | 1621-1621 | Doppelschilling (1/16 Tal | `km-137411-ernst-1620` | weak score=6 (year 1621≈1620, ruler ernst/schaumburg) |
| [18286208](https://ikmk.smb.museum/object?id=18286208) | 1621-1621 | Doppelschilling (1/16 Tal | `km-137411-ernst-1620` | weak score=6 (year 1621≈1620, ruler ernst/schaumburg) |
| [18286209](https://ikmk.smb.museum/object?id=18286209) | 1621-1621 | Doppelschilling (1/16 Tal | `km-137411-ernst-1620` | weak score=6 (year 1621≈1620, ruler ernst/schaumburg) |
| [18286210](https://ikmk.smb.museum/object?id=18286210) | 1621-1621 | Doppelschilling (1/16 Tal | `km-137411-ernst-1620` | weak score=6 (year 1621≈1620, ruler ernst/schaumburg) |
| [18286211](https://ikmk.smb.museum/object?id=18286211) | 1621-1621 | Doppelschilling (1/16 Tal | `km-137411-ernst-1620` | weak score=6 (year 1621≈1620, ruler ernst/schaumburg) |
| [18286228](https://ikmk.smb.museum/object?id=18286228) | 1618-1618 | 1/24 Taler (Groschen) | `km-137411-ernst-1620` | weak score=5 (year 1618~1620, ruler ernst/schaumburg) |
| [18286248](https://ikmk.smb.museum/object?id=18286248) | 1618-1618 | 1/24 Taler (Groschen) | `km-137411-ernst-1620` | weak score=5 (year 1618~1620, ruler ernst/schaumburg) |
| [18286251](https://ikmk.smb.museum/object?id=18286251) | 1618-1618 | 1/24 Taler (Groschen) | `km-137411-ernst-1620` | weak score=5 (year 1618~1620, ruler ernst/schaumburg) |
| [18286284](https://ikmk.smb.museum/object?id=18286284) | 1618-1618 | 1/24 Taler (Groschen) | `km-137411-ernst-1620` | weak score=5 (year 1618~1620, ruler ernst/schaumburg) |
| [18286289](https://ikmk.smb.museum/object?id=18286289) | 1618-1618 | 1/24 Taler (Groschen) | `km-137411-ernst-1620` | weak score=5 (year 1618~1620, ruler ernst/schaumburg) |
| [18286294](https://ikmk.smb.museum/object?id=18286294) | 1618-1618 | 1/24 Taler (Groschen) | `km-137411-ernst-1620` | weak score=5 (year 1618~1620, ruler ernst/schaumburg) |
| [18286306](https://ikmk.smb.museum/object?id=18286306) | 1616-1619 | Arendschilling (Escalin) | `km-74-ernst-iii-1615` | weak score=6 (year 1616≈1615, ruler ernst/schaumburg) |
| [18286307](https://ikmk.smb.museum/object?id=18286307) | 1616-1619 | Arendschilling (Escalin) | `km-74-ernst-iii-1615` | weak score=6 (year 1616≈1615, ruler ernst/schaumburg) |
| [18286326](https://ikmk.smb.museum/object?id=18286326) | 1616-1619 | Arendschilling (Escalin) | `km-74-ernst-iii-1615` | weak score=6 (year 1616≈1615, ruler ernst/schaumburg) |
| [18286334](https://ikmk.smb.museum/object?id=18286334) | 1616-1619 | Arendschilling (Escalin) | `km-74-ernst-iii-1615` | weak score=6 (year 1616≈1615, ruler ernst/schaumburg) |
| [18286342](https://ikmk.smb.museum/object?id=18286342) | 1616-1619 | Arendschilling (Escalin) | `km-74-ernst-iii-1615` | weak score=6 (year 1616≈1615, ruler ernst/schaumburg) |
| [18286356](https://ikmk.smb.museum/object?id=18286356) | 1616-1619 | Arendschilling (Escalin) | `km-74-ernst-iii-1615` | weak score=6 (year 1616≈1615, ruler ernst/schaumburg) |
| [18286362](https://ikmk.smb.museum/object?id=18286362) | 1616-1619 | Arendschilling (Escalin) | `km-74-ernst-iii-1615` | weak score=6 (year 1616≈1615, ruler ernst/schaumburg) |
| [18286369](https://ikmk.smb.museum/object?id=18286369) | 1616-1619 | Arendschilling (Escalin) | `km-74-ernst-iii-1615` | weak score=6 (year 1616≈1615, ruler ernst/schaumburg) |
| [18286372](https://ikmk.smb.museum/object?id=18286372) | 1616-1619 | Arendschilling (Escalin) | `km-74-ernst-iii-1615` | weak score=6 (year 1616≈1615, ruler ernst/schaumburg) |
| [18286375](https://ikmk.smb.museum/object?id=18286375) | 1616-1619 | Arendschilling (Escalin) | `km-74-ernst-iii-1615` | weak score=6 (year 1616≈1615, ruler ernst/schaumburg) |
| [18286654](https://ikmk.smb.museum/object?id=18286654) | 1621-1621 | 4 Groschen | `km-137411-ernst-1620` | weak score=6 (year 1621≈1620, ruler ernst/schaumburg) |
| [18286660](https://ikmk.smb.museum/object?id=18286660) | 1621-1621 | 4 Groschen | `km-137411-ernst-1620` | weak score=6 (year 1621≈1620, ruler ernst/schaumburg) |
| [18286674](https://ikmk.smb.museum/object?id=18286674) | 1621-1621 | Doppelschilling (1/16 Tal | `km-137411-ernst-1620` | weak score=6 (year 1621≈1620, ruler ernst/schaumburg) |
| [18286681](https://ikmk.smb.museum/object?id=18286681) | 1621-1621 | Schilling (1/21 Taler) | `km-137411-ernst-1620` | weak score=6 (year 1621≈1620, ruler ernst/schaumburg) |
| [18286687](https://ikmk.smb.museum/object?id=18286687) | 1621-1621 | Schilling (1/21 Taler) | `km-137411-ernst-1620` | weak score=6 (year 1621≈1620, ruler ernst/schaumburg) |
| [18286694](https://ikmk.smb.museum/object?id=18286694) | 1621-1621 | Schilling (1/21 Taler) | `km-137411-ernst-1620` | weak score=6 (year 1621≈1620, ruler ernst/schaumburg) |
| [18286696](https://ikmk.smb.museum/object?id=18286696) | 1621-1621 | Schilling (1/21 Taler) | `km-137411-ernst-1620` | weak score=6 (year 1621≈1620, ruler ernst/schaumburg) |
| [18286698](https://ikmk.smb.museum/object?id=18286698) | 1621-1621 | Fürstengroschen (12 meißn | `km-137411-ernst-1620` | weak score=6 (year 1621≈1620, ruler ernst/schaumburg) |
| [18286700](https://ikmk.smb.museum/object?id=18286700) | 1621-1621 | Fürstengroschen (12 meißn | `km-137411-ernst-1620` | weak score=6 (year 1621≈1620, ruler ernst/schaumburg) |
| [18286703](https://ikmk.smb.museum/object?id=18286703) | 1621-1621 | Fürstengroschen (12 meißn | `km-137411-ernst-1620` | weak score=6 (year 1621≈1620, ruler ernst/schaumburg) |
| [18286704](https://ikmk.smb.museum/object?id=18286704) | 1621-1621 | Fürstengroschen (12 meißn | `km-137411-ernst-1620` | weak score=6 (year 1621≈1620, ruler ernst/schaumburg) |
| [18286705](https://ikmk.smb.museum/object?id=18286705) | 1621-1621 | Fürstengroschen (12 meißn | `km-137411-ernst-1620` | weak score=6 (year 1621≈1620, ruler ernst/schaumburg) |
| [18286709](https://ikmk.smb.museum/object?id=18286709) | 1619-1619 | 1/24 Taler (Groschen) | `km-137411-ernst-1620` | weak score=6 (year 1619≈1620, ruler ernst/schaumburg) |
| [18286716](https://ikmk.smb.museum/object?id=18286716) | 1619-1619 | 1/24 Taler (Groschen) | `km-137411-ernst-1620` | weak score=6 (year 1619≈1620, ruler ernst/schaumburg) |
| [18286720](https://ikmk.smb.museum/object?id=18286720) | 1619-1619 | 1/24 Taler (Groschen) | `km-137411-ernst-1620` | weak score=6 (year 1619≈1620, ruler ernst/schaumburg) |
| [18286724](https://ikmk.smb.museum/object?id=18286724) | 1619-1619 | 1/24 Taler (Groschen) | `km-137411-ernst-1620` | weak score=6 (year 1619≈1620, ruler ernst/schaumburg) |
| [18286735](https://ikmk.smb.museum/object?id=18286735) | 1619-1619 | 1/24 Taler (Groschen) | `km-137411-ernst-1620` | weak score=6 (year 1619≈1620, ruler ernst/schaumburg) |
| [18286738](https://ikmk.smb.museum/object?id=18286738) | 1619-1619 | 1/24 Taler (Groschen) | `km-137411-ernst-1620` | weak score=6 (year 1619≈1620, ruler ernst/schaumburg) |
| [18286752](https://ikmk.smb.museum/object?id=18286752) | 1619-1619 | 1/24 Taler (Groschen) | `km-137411-ernst-1620` | weak score=6 (year 1619≈1620, ruler ernst/schaumburg) |
| [18286755](https://ikmk.smb.museum/object?id=18286755) | 1619-1619 | 1/24 Taler (Groschen) | `km-137411-ernst-1620` | weak score=6 (year 1619≈1620, ruler ernst/schaumburg) |
| [18286759](https://ikmk.smb.museum/object?id=18286759) | 1620-1620 | 1/24 Taler (Groschen) | `km-137411-ernst-1620` | weak score=6 (year 1620≈1620, ruler ernst/schaumburg) |
| [18286763](https://ikmk.smb.museum/object?id=18286763) | 1620-1620 | 1/24 Taler (Groschen) | `km-137411-ernst-1620` | weak score=6 (year 1620≈1620, ruler ernst/schaumburg) |
| [18286771](https://ikmk.smb.museum/object?id=18286771) | 1620-1620 | 1/24 Taler (Groschen) | `km-137411-ernst-1620` | weak score=6 (year 1620≈1620, ruler ernst/schaumburg) |
| [18286782](https://ikmk.smb.museum/object?id=18286782) | 1620-1620 | 1/24 Taler (Groschen) | `km-137411-ernst-1620` | weak score=6 (year 1620≈1620, ruler ernst/schaumburg) |
| [18286784](https://ikmk.smb.museum/object?id=18286784) | 1620-1620 | 1/24 Taler (Groschen) | `km-137411-ernst-1620` | weak score=6 (year 1620≈1620, ruler ernst/schaumburg) |
| [18286786](https://ikmk.smb.museum/object?id=18286786) | 1620-1620 | 1/24 Taler (Groschen) | `km-137411-ernst-1620` | weak score=6 (year 1620≈1620, ruler ernst/schaumburg) |
| [18286788](https://ikmk.smb.museum/object?id=18286788) | 1620-1620 | 1/24 Taler (Groschen) | `km-137411-ernst-1620` | weak score=6 (year 1620≈1620, ruler ernst/schaumburg) |
| [18286798](https://ikmk.smb.museum/object?id=18286798) | 1620-1620 | 1/24 Taler (Groschen) | `km-137411-ernst-1620` | weak score=6 (year 1620≈1620, ruler ernst/schaumburg) |
| [18286821](https://ikmk.smb.museum/object?id=18286821) | 1620-1620 | 1/24 Taler (Groschen) | `km-137411-ernst-1620` | weak score=6 (year 1620≈1620, ruler ernst/schaumburg) |
| [18286826](https://ikmk.smb.museum/object?id=18286826) | 1620-1620 | 1/24 Taler (Groschen) | `km-137411-ernst-1620` | weak score=6 (year 1620≈1620, ruler ernst/schaumburg) |
| [18286829](https://ikmk.smb.museum/object?id=18286829) | 1620-1620 | 1/24 Taler (Groschen) | `km-137411-ernst-1620` | weak score=6 (year 1620≈1620, ruler ernst/schaumburg) |
| [18286831](https://ikmk.smb.museum/object?id=18286831) | 1620-1620 | 1/24 Taler (Groschen) | `km-137411-ernst-1620` | weak score=6 (year 1620≈1620, ruler ernst/schaumburg) |
| [18286832](https://ikmk.smb.museum/object?id=18286832) | 1620-1620 | 1/24 Taler (Groschen) | `km-137411-ernst-1620` | weak score=6 (year 1620≈1620, ruler ernst/schaumburg) |
| [18286834](https://ikmk.smb.museum/object?id=18286834) | 1620-1620 | 1/24 Taler (Groschen) | `km-137411-ernst-1620` | weak score=6 (year 1620≈1620, ruler ernst/schaumburg) |
| [18286838](https://ikmk.smb.museum/object?id=18286838) | 1620-1620 | 1/24 Taler (Groschen) | `km-137411-ernst-1620` | weak score=6 (year 1620≈1620, ruler ernst/schaumburg) |
| [18286841](https://ikmk.smb.museum/object?id=18286841) | 1620-1620 | 1/24 Taler (Groschen) | `km-137411-ernst-1620` | weak score=6 (year 1620≈1620, ruler ernst/schaumburg) |