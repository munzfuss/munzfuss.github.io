# Hierarchical metal tiers within one Müntzfuß — project convention

> **Codification of an existing pattern.** Several Müntzfüße in
> `data/shared/fuesse.yml` already mix multiple metal tiers within
> one Fuß — full-weight Kurantmünze (precious metal at the anchor
> fineness) above smaller Scheidemünze (the same precious metal at
> a reduced fineness) above pure Kupfer-/Bronze-Scheide (no
> precious metal). This pattern is the rule, not the exception:
> nearly every silver Fuß in the catalogue has a Scheidemünze
> sub-tier defined alongside its Kurant tier. **Krone-fod** extends
> the same pattern one rung up by adding a *gold* anchor tier above
> the silver tiers — but the modelling principle is identical.

## The pattern

A Müntzfuß is a *single* monetary standard established by *one*
legal act, accounting in *one* unit, with a *hierarchy of
denominations* across multiple metal tiers. The hierarchy
canonically runs from the anchor tier (the metal that defines the
Müntzfuß mathematically) downward through subsidiary tiers of
progressively lower fineness, ending in copper/bronze tokens that
carry no precious-metal content at all.

```
  anchor tier      most-precious metal at anchor fineness
       │                full-weight Kurant
       ▼
  sub-Kurant tier  same precious metal, reduced fineness
       │                still full-tariff but lighter
       ▼
  Scheide tier     same precious metal, deliberately under-weight
       │                deters melting; tokens of accounting value
       ▼
  Cu-Scheide tier  copper/bronze petty coins
                       pure tokens, no precious-metal anchor
```

Not every Fuß uses every tier. Mark-of-account era Fusses
(9¼-Thaler, 11⅓-Thaler, 18½-Thaler) typically have only the silver
anchor + silver Scheide tier. Christian IV's Krone (kronemont_chr_iv)
has the silver anchor + silver Scheide + sub-units. Krone-fod has
all four (gold anchor + silver Kurant + silver Scheide + bronze
Scheide). The pattern scales without breaking.

## How it's modelled in this project

### One `Fuss` entry per Müntzfuß

`fuesse.yml::<fuss_id>` holds one entry per Müntzfuß. The
`metal` field declares the **anchor metal** — the metal that
defines the standard mathematically (cf. `grid_unit_g` and
`grid_stops`). For silver-anchored Fusses this is `silver`; for
Krone-fod and Reichsgoldmünzfuß it is `gold`.

`fineness_standard` declares the **anchor tier's fineness**. The
silver-only Fusses use this for all their denominations (Scheide
tier coins have lower per-coin fineness, but the *target* of the
fineness measure is still the anchor). For multi-tier-metal Fusses
like Krone-fod, this is the gold tier's fineness; the silver
sub-tiers and the bronze tier are described separately.

### Per-fraction `soll_fein_g`

Each entry in `Fuss.fractions[<key>]` carries `soll_fein_g` — the
**target fine-metal weight for that denomination's tier**. The
fineness implied by this value can differ across fractions:

- 9¼-Thaler-Fuß, fraction «1/96» (1 Skilling): soll_fein_g
  encodes the silver content per Skilling at the Scheide-tier's
  reduced fineness — not the anchor fineness × the share.
- Krone-fod, fraction «20» (20 Kroner): soll_fein_g 8.0645 g —
  fine *gold*.
- Krone-fod, fraction «2» (2 Kroner silver): soll_fein_g 12.0 g —
  fine *silver*.
- Krone-fod, fraction «1/100» (1 øre bronze): soll_fein_g 0 —
  no precious-metal content.

Mixing gold-fein and silver-fein values in one Fuß's fraction
table is fine because the values are *targets per denomination*,
not derivations of a single anchor figure. The fraction key is
the abstract denomination (a share of the unit), the
`soll_fein_g` is the metal answer for that share within its
historical context.

### Per-coin `metal` and `fineness`

Each `Coin` carries its own `metal` (`silver | gold | billon |
copper`) and its own `fineness`. The render layer routes coins by
`kind` (kurant / scheide / tarif / gedenk) and by `metal` (copper
gets its own sub-bucket via `PhaseGroup.copper_coins`). This
gives every Fuß a clean per-tier breakdown on the rendered page:
the Kurant table holds the full-weight Kurant coins, the Scheide
table holds the under-weight Scheide coins, the copper table
holds pure Cu/Bronze tokens — regardless of how many metal tiers
the Fuß spans.

### The Δ (delta) computation

`compute.py` derives delta from `weight_rough × fineness −
soll_fein_g`, with both the weight and fineness taken from the
*coin* (not the Fuß). The Fuß's `fineness_standard` is only used
for the few derivations that need an «expected fineness for this
Fuß» (e.g. the heuristic in §8a of CLAUDE.md). For all the
per-coin tier-specific computations, the coin's own fields carry
the truth.

This is the key property that makes the hierarchical-metal-tier
model work: **soll_fein_g per fraction is independent of
`fineness_standard`**. The Fuß-level fineness is a hint about the
anchor; per-fraction values handle the rest.

## Examples in the project

| Fuß | Anchor | Sub-Kurant | Scheide | Cu/Bronze |
|---|---|---|---|---|
| `9_thaler` (1566-1625) | silver .889 — Reichsthaler | — | silver, lower fin — Schilling/Hvid | — |
| `9_25_thaler` (1622-1875) | silver .875 — Speciedaler | silver — Mark (1/3 Sp) | silver — Skilling/Sechsling | — |
| `11_333_thaler` (1726-1813) | silver .73 — Rigsdaler Courant | — | billon — Skilling | — |
| `18_5_thaler` (1813-1875) | silver .875 — Rigsbankdaler | — | billon — Rigsbankskilling | — |
| `kronemont_chr_iv` (1618-1675) | silver .859 — Krone | silver, lower fin — Kroneskilling | — | — |
| `kronefod` (1873-1914) | **gold .900 — 10/20 Kroner** | silver .800 — 1/2 Kroner | silver .600/.400 — 25/10 øre | bronze — 5/2/1 øre |
| `reichsgoldmuenzfuss` (German Empire 1871) | gold .900 — 5/10/20 Mark | (silver Mark coins exist in real Germany but aren't yet modelled in the project) | | |

Reichsgoldmünzfuß is currently gold-only in the project because
we haven't done the German Empire location yet. When we do, it
will follow the same hierarchical pattern as Krone-fod.

## When NOT to follow this pattern

A new Müntzfuß **should NOT** be modelled as one Fuß with
hierarchical metal tiers when:

1. **The legal anchors are separate.** If two coexisting standards
   are established by *different* laws / decrees / mint
   ordinances, they're different Müntzfüße. Example: Christian V's
   silver Krone (`kronemont`, 1671 Mint Ordinance) and his gold
   `guldkrone` (different Patent) — both have «Krone» in the name
   but the legal acts differ; they're separate Fusses in the
   project.

2. **The accounting units are separate.** If one standard is
   accounted in Speciedaler and another in Rigsdaler Courant at
   a non-fixed exchange rate (Opgæld varying with market), they're
   different units even if minted in parallel. Example:
   `9_25_thaler` (Speciedaler) and `11_333_thaler` (Rigsdaler
   Courant) coexisted 1726-1813 — separate Fusses.

3. **No precious-metal anchor exists.** Pure fiat / token systems
   (post-1914 paper-money era; modern cupro-nickel coinage)
   wouldn't carry a `metal` anchor at all. The project's scope
   ends before this becomes relevant, but the schema reflects it
   (anchor metals are silver / gold, period).

## Operational implications

- **Adding a hierarchical Fuß**: list every denomination in
  `fractions`, give each its honest per-tier `soll_fein_g`.
  `fineness_standard` stays at the anchor-tier value;
  `fineness_display` text spells out the cascade.
- **Coin classification**: route by year+nominal as usual; the
  classifier's existing rules (gold Krone → kronefod;
  silver/billon Krone+Øre → kronefod; copper øre → kronefod) all
  land on the same Fuß, with per-coin `metal` + `kind` providing
  the rendering hint.
- **Render**: the existing categorize.py + render.py code handles
  multi-metal Fusses via its `kind` + per-coin `metal` routing.
  No template changes needed.

## Bibliography (project-internal)

- This convention codifies what's already in `data/shared/fuesse.yml`
  for the silver Fusses; the only new step in 2026-05 was extending
  it to the gold-anchored Krone-fod.
- See `docs/dk_kronefod_unity_analysis.md` for the comparative
  analysis that led to the merge.
- See `docs/dk_kronefod_1873_research.md` for the primary-source
  documentation of the Krone-fod system.
- Source schema: `scripts/lib/schema.py::Fuss` and
  `scripts/lib/schema.py::Fraction`.
