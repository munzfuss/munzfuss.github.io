# Danish Krone-fod 1873-1914 — research note

> **Why this file exists.** User flagged the question «what Müntzfüße were
> introduced in Denmark between 1866 and 1914 — are any missing from the
> project?». Research below confirms the *one* major new standard in
> the period (the **Krone-fod** / Scandinavian gold-Krone, Coinage Act
> of 23 May 1873) and surfaces a tagging-vs-substance inconsistency in
> how we currently represent it. This is a research note for future
> implementation, not an applied change.

## Period inventory — what we currently have

`data/locations/denmark.yml` phases that touch any part of 1866-1914:

| Fuß | Phase | Years | Title |
|---|---|---|---|
| `reichsdukatenfuss` | D | 1813-1871 | Reichsdukat continuation |
| `pistolenfuss` | A | 1771-1870 | Christian d'or / Frederik d'or |
| `18_5_thaler` | A | 1813-1875 | Rigsbankdaler → Rigsdaler Rigsmønt → Krone reform |
| `30_thaler` | A | 1873-1947 | Skandinavische Krone-Mønt — 1 Krone = 100 Øre |
| `reichsgoldmuenzfuss` | A | 1873-1914 | Skandinavische Goldkrone — 10 / 20 Kroner |
| `seed_unsorted` | A / hede | 1500-1914 | catch-all (Bulk-seed) |

The 1866-1873 transition is covered by `18_5_thaler/A` (Rigsbankdaler era,
extended through the Krone reform of 1875). The 1873+ era is covered by
**two** entries — `30_thaler/A` and `reichsgoldmuenzfuss/A` — both
nominally the «Skandinavische Krone-Mønt». That's the inconsistency
this doc digs into.

## Finding — the Krone-fod is a **distinct Müntzfuß** we currently mis-tag

### What the law says

The Møntloven (Coinage Act) of **23 May 1873**, effective **1 January
1875**, replaced the Rigsdaler standard with a gold-Krone standard at
**2,480 Kroner per kilogram of fine gold** (i.e. 0.4032 g fine gold per
Krone). Adoption history:

- **5 May 1873** — Denmark + Sweden sign the Scandinavian Monetary
  Convention.
- **23 May 1873** — Denmark passes Møntloven.
- **1 January 1875** — new Krone system takes effect; Norway joins.
- **2 August 1914** — Danmarks Nationalbank suspends gold convertibility
  (start of WWI); de-facto end of the metallic standard.
- **1924** — formal dissolution of the Skandinavisk Møntunion.

The system is established by Denmark's own Coinage Act, not by the
German Münzgesetz of 1871/1873. Conversion to Rigsdaler Rigsmønt:
**2 Kroner = 1 Rigsdaler**. Conversion to Reichsmark (fixed by gold
parity): **8 Kroner = 9 Mark**, or 1 Krone = 1.125 Mark.

### Mathematics

| Standard | Anchor | Gold per kg fine |
|---|---|---|
| Reichsgoldmünzfuß (German Empire, 1871) | 2790 Mark / kg fine gold | 0.3584 g per Mark |
| **Krone-fod (Denmark/Sweden/Norway, 1873)** | **2480 Krone / kg fine gold** | **0.4032 g per Krone** |

Both standards run at .900 fineness gold but with different per-unit
weight grids. Mathematically they're related by the fixed 8:9 ratio,
but they are legally distinct systems with separate denomination
ladders, separate auxiliary-coin programmes, and separate legal
authorities (Reichstag in Berlin vs. Rigsdag in Copenhagen).

### How we currently model it

`data/shared/fuesse.yml::reichsgoldmuenzfuss` is defined as the **German**
Reichsgold standard:

```yaml
reichsgoldmuenzfuss:
  metal: gold
  grid_unit_g: 233.856     # Cölln Marck fein
  grid_stops: 1395          # = 2790 Mark / (Cölln Marck / kg)
  fineness_standard: 0.900
  fractions:
    "5":  ...    # 5 Reichsmark
    "10": ...    # 10 Reichsmark
    "20": ...    # 20 Reichsmark
```

— that's a Reichsmark-anchored Fuß. We then route Danish 1873-1914 gold
to this same `reichsgoldmuenzfuss/A` block via the comment in
`denmark.yml`:

> «Tagging-Konvention: Reichsgoldmünzfuß verwendet, da die Goldparität
> direkt an den Reichs-Goldmark angeknüpft ist (3 Krone = 4 Reichsmark).»

This works arithmetically (gold content is exactly fixed via the 8:9
ratio) — so a Danish 20 Kroner *does* contain 8.064 g fine gold, which
is also the fein-weight of 9 Reichsmark to 4 decimal places. But the
**denominations**, the **legal authority**, and the **auxiliary-coin
programme** are all distinct.

`30_thaler/A` is then used as the «Skandinavische Krone-Mønt» silver-
auxiliary bucket. `30_thaler` is itself a Reichsmark-derived silver
standard (Vereinsmünze, 1857; 30 Thaler = 1 Mark-Pfund fein in the
Vienna convention). Using it for Danish post-1873 silver Krone /
Øre coins is a stretch — those silver coins are NOT struck at the
30-Thaler ratio; they're struck under the same 1873 Møntlov as the
gold and use a different fineness ladder per denomination.

### What a clean model would look like

A dedicated **`kronefod`** Müntzfuß defined per the 1873 Møntlov,
with fractions matching the Danish denomination ladder:

```yaml
kronefod:
  name:
    de: Krone-Fuß (Skandinavische Müntzunion)
    en: Krone-fod (Scandinavian Monetary Union)
    uk: Krone-fod (Скандинавська монетна унія)
  historical_name: Krone-fod
  metal: gold
  grid_unit_g: 1000.0          # 1 kg fine gold
  grid_stops: 2480              # 2480 Kroner per kg fine
  fineness_standard: 0.900
  fractions:
    "5":  {soll_rau_g: 2.24,  soll_fein_g: 2.016}
    "10": {soll_rau_g: 4.4803, soll_fein_g: 4.0322}
    "20": {soll_rau_g: 8.9606, soll_fein_g: 8.0645}
  events:
    first_adoption: {anywhere: 1873, ...}
    first_mint:     {anywhere: 1873, ...}
    std_end:        {anywhere: 1914, note: «gold convertibility suspended»}
    demonetisation: {anywhere: 1924, note: «SMU formally dissolved»}
```

The silver/billon/bronze auxiliary coins (1/2 Kroner, 25/10/5 øre etc.)
are subordinate to this same Müntzfuß — they're issued under the same
Møntlov, with their own fineness ladders documented per-denomination
rather than as a single fineness_standard.

## Specifications of the coinage 1873-1914

All weights / diameters / finenesses below cite the Wikipedia /
Numista / coin-identifier sources listed in the bibliography. KM
numbers from Krause-Mishler.

### Gold (90% Au, 10% Cu — `kronefod` proper)

| Denom | Weight (rau) | Fine weight | Diameter | Mintage years | KM (Christian IX) | KM (Frederik VIII) | KM (Christian X) |
|---|---|---|---|---|---|---|---|
| 20 Kroner | 8.9606 g | 8.0645 g | 23 mm | 1873-1900 (Chr IX), 1908-1912 (Fr VIII), 1913-1917 (Chr X) | KM# 791 | KM# 810 | KM# 817 |
| 10 Kroner | 4.4803 g | 4.0322 g | 18.5 mm | 1873-1900 | KM# 790 | KM# 809 | — |
| 5 Kroner | (struck very late, post-1914) | | | | | | |

Standard formula: «2480 Kroner = 1 kg fein gold». So per coin:

- 10 Kr = 1/248 kg fein = 4.0322 g fein gold
- 20 Kr = 1/124 kg fein = 8.0645 g fein gold

### Silver «high» (.800 fineness — secondary Kurant tier)

| Denom | Weight (rau) | Fine weight | Diameter | Mintage years | KM (Christian IX) |
|---|---|---|---|---|---|
| 2 Kroner | 15.0 g | 12.0 g | 31 mm | 1875-1899 (Chr IX), 1903 commemorative (Chr IX), 1906 commemorative (Fr VIII), 1912 (Fr VIII), 1915-1916 (Chr X) | KM# 798.1 |
| 1 Krone | 7.5 g | 6.0 g | 25 mm | 1875-1898 | KM# 797.1 |

### Silver «lower» (.600 fineness — Scheidemünze tier)

| Denom | Weight (rau) | Fine weight | Diameter | Mintage years | KM (Christian IX) |
|---|---|---|---|---|---|
| 25 Øre | 2.42 g | 1.452 g | 17 mm × 1.3 mm | 1874-1905 (Chr IX), 1907-1911 (Fr VIII) | KM# 796.1 |
| 10 Øre | (similar profile, .400 per some sources, .600 per others — needs verification) | | | 1874-1905 | KM# 795.1 |

Note: the Danish Wikipedia article reports the silver fineness ladder
as **«0.800 for 2-kronen til 0.400 for 10-øren»** (i.e. 2 Kr at .800,
descending to .400 on the 10 øre). The English-Wikipedia 25-øre
article reports the 25-øre as .600. The two sources are consistent if
the ladder is: 2 Kr / 1 Kr = .800, 25 øre = .600, 10 øre = .400. To
confirm exactly, the Sieg-Møntkatalog or the original Møntlov text is
needed.

### Bronze (95% Cu, 4% Sn, 1% Zn — copper auxiliary tier)

| Denom | Weight | Diameter | Mintage years |
|---|---|---|---|
| 5 øre | 8 g | (per Wikipedia DA, 27 mm typically) | 1874-1923 |
| 2 øre | 4 g | (per Wikipedia DA) | 1874-1923 |
| 1 øre | 2 g | (per Wikipedia DA) | 1874-1923 |

## Recommended implementation (deferred — this is a research note)

If/when this is acted on:

1. **Add `kronefod` to `data/shared/fuesse.yml`** with the gold-only
   primary spec above. Three fractions: 5, 10, 20 Kroner.
2. **Add auxiliary silver/billon/bronze sub-rates** either as separate
   fractions under `kronefod` (e.g. «1/4» for 25 øre at the .600
   silver rate) OR — more honestly — as separate sub-fusses
   `kronefod_silver` / `kronefod_billon` / `kronefod_bronze`, since
   their fineness varies per denomination and the «one fineness, many
   fractions» model from `9_25_thaler` etc. doesn't fit.
3. **Reroute the existing post-1873 entries** from
   `reichsgoldmuenzfuss/A` to `kronefod/A` in `data/locations/denmark.yml`.
   Update `denmark.yml`'s `fuss_order`, `fuss_periods`, and `phases`.
4. **Keep `reichsgoldmuenzfuss` for actual Reichsmark coins** (none
   currently in `denmark.yml`; would apply to a future Holstein /
   Reichsgold-era German Imperial page).
5. **Update `30_thaler/A`** to drop the «Skandinavische Krone-Mønt»
   framing — the 30-Thaler Fuß is Vereinsmünze territory (1857-1873),
   not Krone-Mønt. Either retire its Danish-side application
   altogether or restrict it to pre-1873 Vereinsthaler holdings.

For Holstein (1864 Prussian / 1871 German Empire-side) coinage in this
period: a separate Holstein-on-Prussia-page eventually wants
**Reichsgoldmünzfuß proper** (the existing fuss). That's a different
question than Denmark proper.

## Other potential 1866-1914 standards we examined and ruled out

- **Latin Monetary Union (1865)** — Denmark explicitly **rejected**
  joining (bimetallism rejected as «økonomisk ufornuftigt» — see the
  danskmoent.dk «Den skandinaviske flugt fra sølvet» article). Not a
  Danish Müntzfuß.
- **Vereinsmüntzvertrag (1857)** — Denmark did NOT join the
  Vereinsmünze. Holstein issues 1857-1864 used the Schleswig-Holstein
  Courant standard (see schleswig_holstein.yml). After 1864 Holstein
  followed Prussia/Reichsmark, not Denmark proper.
- **Rigsdaler Rigsmønt rebranding (1854/1873)** — same Müntzfuß
  (18½-Thaler-Fuß), accounting unit rename. Already documented in
  `18_5_thaler/A`.

So the **only** monetary regime introduced in Denmark in 1866-1914
is the Krone-fod of 1873. It IS in our project, but mis-tagged as
the German Reichsgoldmünzfuß.

## Bibliography

Primary / authoritative:

- Møntloven of 23 May 1873 — original text not freely online; cited
  via secondary sources.
- Skandinavisk Møntkonvention, 5 May 1873 (Stockholm) — bilateral
  Sweden-Denmark; Norway acceded 1875.

Wikipedia / Lex (Danish encyclopaedia, Gyldendal):

- [Den Skandinaviske Møntunion — Wikipedia DA](https://da.wikipedia.org/wiki/Den_Skandinaviske_M%C3%B8ntunion)
- [Den Skandinaviske Møntunion — Lex.dk](https://lex.dk/Den_Skandinaviske_M%C3%B8ntunion)
- [Krone — møntenhed — Lex.dk](https://lex.dk/krone_-_m%C3%B8ntenhed)
- [Øre — møntenhed — Lex.dk](https://lex.dk/%C3%B8re_-_m%C3%B8ntenhed)
- [Dansk møntvæsen — Lex.dk](https://lex.dk/dansk_m%C3%B8ntv%C3%A6sen)
- [Møntunion — Lex.dk](https://lex.dk/m%C3%B8ntunion)
- [Scandinavian Monetary Union — Wikipedia EN](https://en.wikipedia.org/wiki/Scandinavian_Monetary_Union)
- [Danish krone — Wikipedia EN](https://en.wikipedia.org/wiki/Danish_krone)
- [Danske kroner — Wikipedia DA](https://da.wikipedia.org/wiki/Danske_kroner)
- [Twenty-five øre (Danish coin) — Wikipedia EN](https://en.wikipedia.org/wiki/Twenty-five_%C3%B8re_(Danish_coin))
- [Øre (møntenhed) — Wikipedia DA](https://da.wikipedia.org/wiki/%C3%98re_(m%C3%B8ntenhed))

Numismatic / catalogue:

- [Numista — 20 Kroner Christian IX 1873-1900](https://en.numista.com/catalogue/pieces41928.html) (KM# 791)
- [Numista — 20 Kroner Christian X](https://en.numista.com/25627)
- [Numista — 10 Kroner Christian IX 1873-1900](https://en.numista.com/26768) (KM# 790)
- [Numista — 2 Kroner Christian IX](https://en.numista.com/8493) (KM# 798.1)
- [Numista — 25 Øre Christian IX](https://en.numista.com/catalogue/pieces9392.html) (KM# 796.1)
- [Numista — 10 Øre Christian IX](https://en.numista.com/catalogue/pieces5567.html) (KM# 795.1)
- [Numista — 1 Øre Christian IX](https://en.numista.com/catalogue/pieces5265.html)
- [ucoin — 20 kroner 1873-1900 Christian IX](https://en.ucoin.net/coin/denmark-20-kroner-1873-1900/?tid=49677)
- [ucoin — 10 kroner 1873-1900](https://en.ucoin.net/coin/denmark-10-kroner-1873-1900/?tid=49671)
- [ucoin — 25 øre 1874-1905](https://en.m.ucoin.net/coin/denmark-25-ore-1874/?cid=49653)

Specialist numismatic articles (Danish):

- [Den skandinaviske flugt fra sølvet — danskmoent.dk](https://www.danskmoent.dk/artikler/flugt.htm) — the most thorough account of the 1872-1873 deliberations + the rejection of LMU + the gold-Krone-Mønt-rationale, with the 1:15.5 ratio context.
- [50 øre eller 1/2 krone — danskmoent.dk](https://www.danskmoent.dk/artikler/pf50ore.htm) — note that a 50 øre denomination was discussed but NOT struck under Christian IX (introduced later in 1920s).
- [Mønthistorie — Nibe Møntklub](https://www.nibemontklub.dk/moenthistorie-2/)
- [Mønthistorie — helmer-c.dk](https://www.helmer-c.dk/Econhist/mnt-his.htm)
- [Danmarks mønthistorie — monthuset.dk](https://www.monthuset.dk/hvordan-samler-man/danmarks-monthistorie)
- [Møntenheder — Thorvaldsens Museum arkivet](https://arkivet.thorvaldsensmuseum.dk/artikler/moentenheder)

Central-bank / academic:

- [Danmarks Nationalbank — Historical coins](https://www.nationalbanken.dk/en/what-we-do/notes-and-coins/historical-coins) — short overview confirming «With the Danish Coinage Act of 1873, Denmark switched to basing its monetary system on the gold standard, and rigsdaler were replaced by kroner.»
- [Kim Abildgren — A chronology of Denmark's exchange-rate policy 1875-2003](https://www.econstor.eu/bitstream/10419/82375/2/386525536.pdf) — primary academic chronology, deeper detail than encyclopaedias.
- [The Scandinavian Currency Union, 1873-1924 (dissertation)](https://ex.hhs.se/dissertations/594631-FULLTEXT01.pdf) — full PhD-level treatment of the SMU's economic mechanics.
- [BIS — HMFS Denmark](https://www.bis.org/ifc/hmfs/hmfs_dk.pdf) — Bank for International Settlements historical monetary and financial statistics for Denmark.

For pre-1873 background (already in our project's scope):

- The Hede 1971 cache + the Wilcke II 19th-c. extension (already
  parsed at `scripts/cache/hede/`) covers the Rigsbankdaler era +
  the Krone-reform period bookend on the Danish side.

## Status

**Implemented 2026-05-11.** The refactor described above is now live:

- `data/shared/fuesse.yml` gains `kronefod` (gold, 5/10/20 Kr) and
  `kronefod_silver` (silver Kurant 1/2 Kr + Scheide 25/10 øre +
  bronze 5/2/1 øre).
- `data/locations/denmark.yml` `fuss_order` now contains
  `kronefod` and `kronefod_silver` in place of `reichsgoldmuenzfuss`
  and `30_thaler`. Phase blocks for the two new fusses replaced the
  old «tagging convention» ones.
- 31 + 24 = 55 coins migrated across `data/locations/denmark.yml`
  and `data/seed/hede/denmark.yml` via the migration script
  `scripts/maintenance/migrate_dk_kronefod_refactor.py`. Two
  fineness-mistagged silver-marked coins (actually gold 10/20 Kr)
  were corrected in the process.
- 14 fraction-strings were remapped from the old 30-Thaler-style
  notation (1/12, 1/24, 1/96, 1/192) to the new Krone-anchored
  notation (1/10, 1/4, 1/50, 1/100).
- `scripts/maintenance/classify_dk_seeds.py` updated:
  PHASES gains kronefod / kronefod_silver entries, gold-classifier
  routes 1873-1914 «Krone» to kronefod, silver/billon/copper goes
  to kronefod_silver via both the explicit Krone/Øre rule and the
  Scheidemünze year-window fallback.
- `scripts/maintenance/infer_dk_seed_fractions.py` gains
  `kronefod` (5/10/20 Kr identity) and `kronefod_silver` (1/2 Kr
  identity + per-N-Øre → 1/(100/N) for 25/10/5/2/1 øre).
- `reichsgoldmuenzfuss` and `30_thaler` remain *defined* in
  `fuesse.yml` but are no longer referenced by `denmark.yml` —
  reserved for a future Holstein-under-Reichsmark page and for
  Vereinsthaler-era coverage respectively.

Final coin distribution on the Denmark page after the refactor:

  reichsdukatenfuss    316
  9_25_thaler          283
  9_thaler             150
  kronemont            117
  18_5_thaler           64
  11_333_thaler         60
  kronemont_chr_iv      59
  kronefod_silver       38   (was bucketed in 30_thaler)
  kronemont_fine        27
  pistolenfuss          21
  kronefod              16   (was bucketed in reichsgoldmuenzfuss)
  guldkrone              8
  courantdukatenfuss     5

Build clean across 12 locations × 3 languages.
