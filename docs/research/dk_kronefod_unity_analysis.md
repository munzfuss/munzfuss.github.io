# Krone-fod — one Müntzfuß or two? Analysis

> **The question.** We currently model the Danish 1873 monetary system
> as TWO separate Müntzfüße: `kronefod` (gold) and `kronefod_silver`
> (silver + bronze auxiliaries). User flagged the analogy with German
> Reichsmark, where 20/10 Mark gold + 5 Mark silver + Pfennig
> subsidiaries all live under ONE Reichsmünzfuß concept — and asked
> whether the split is justified or whether Krone-fod should likewise
> be modelled as one Müntzfuß with a hierarchy of denominations.

## The unity case (one Müntzfuß)

### Historical / legal arguments

1. **One coinage act.** Lov nr. 66 af 23. maj 1873 (Møntloven)
   establishes the gold standard, the silver Kurant tier (1/2 Kr),
   the silver Scheide tier (10/25 øre), and the bronze tier (1/2/5
   øre) in a **single piece of legislation**. There is no «Lov om
   Sølv-Krone-fod» separately. The four companion regulations
   (Bek. nr. 88, 115, 130, 156 af 1873) operate within the same
   law — they specify dies, mint procedure, legal-tender status,
   not separate standards.

2. **One accounting unit.** **100 øre = 1 Krone.** The silver 1
   Krone and the gold 10 Kroner are denominated in the **same
   unit**, related by a fixed factor of 10. There's no parallel
   accounting system like Speciedaler / Rigsdaler Courant in 1726,
   no Opgæld between gold-Krone and silver-Krone. A 2-Kroner
   silver piece IS 2 of the same units as a gold 20-Kroner piece.

3. **Monometallic gold anchor.** Krone-fod is a **gold standard**,
   not a bimetallic system. Silver and bronze coins are pure
   subsidiary (Scheidemünze) — they do NOT trade at par to their
   silver content. Their fineness was deliberately set BELOW the
   silver-equivalent of their tariff (.800 / .600 / .400 vs the
   gold value) precisely to ensure they don't get melted. This is
   the structural difference vs the Latin Monetary Union (which
   Denmark explicitly rejected per ref20 «Den skandinaviske flugt
   fra sølvet»): LMU had bimetallism with a fixed gold:silver
   ratio; Krone-fod has fiat-valued silver subsidiaries pegged
   directly to the gold Krone.

4. **Free convertibility at par.** Until 2 August 1914, silver and
   bronze coins were exchangeable for gold coins at face value on
   demand. Their value derives from the gold standard, not from
   their own metal content. Treating them as a separate Müntzfuß
   misrepresents this: they have no independent silver-content
   anchor — they're tokens of the gold Krone.

5. **Scholarly numismatic convention.** Hede, Galster, Wilcke,
   Aagaard and modern Danish coin catalogues describe «Krone-Mønt»
   or «Krone-fod» as ONE system with hierarchical denominations.
   Splitting into two Fusses is a project-specific schema artefact,
   not how numismatic literature categorises this.

6. **Reichsmark direct analogy.** German Reichsgoldmünzfuß (1871):
   - Gold: 5, 10, 20 Mark at .900
   - Silver Kurant: 1, 2, 5 Mark at .900 (yes, same fineness as
     gold — but as silver alloy)
   - Silver Scheide: 20, 50 Pfennig at .900 (later .625)
   - Billon / Cu: 1, 2, 5, 10 Pfennig

   Modern German numismatic scholarship treats this as ONE
   Reichsmünzfuß. Münzgesetz of 4 December 1871 + 9 July 1873
   cover both gold and silver in one legal framework. The
   parallel to Krone-fod is exact.

### Reader-experience argument

7. **Mental model.** A reader looking at the rendered Denmark page
   sees two adjacent sections labelled «Krone-Fuß · Skandinavische
   Müntzunion (Gold)» and «Krone-Fuß · ... (Silber + Bronze)».
   That naming strongly implies two systems. The historical truth
   is one system — and «splitting it visually to keep the schema
   happy» is the kind of project-meta leakage CLAUDE.md §0z warns
   against. Whether you call them «kronefod» and «kronefod_silver»
   in YAML doesn't matter to the reader; what they SEE is two
   blocks where there should be one.

## The split case (two Müntzfüße — status quo)

### Schema / technical arguments

1. **Pydantic schema enforces one metal per Fuss.**
   ```python
   class Fuss:
       metal: Literal["silver", "gold"]
       fineness_standard: float
   ```
   A single Fuss declares ONE metal and ONE primary fineness. To
   represent gold .900 + silver .800/.600/.400 + bronze in a
   single Fuss requires bending these fields away from their
   semantics.

2. **`fineness_standard` mismatch.** The gold Krone is at .900;
   silver Kurant at .800; silver Scheide at .600 / .400; bronze
   isn't even a fineness-bearing alloy in the same sense. There
   is **no single number** that meaningfully captures «the»
   fineness of Krone-fod. Even the existing kronefod_silver
   record uses a workaround: `fineness_standard: 0.8` (the
   primary silver tier) with a `fineness_display` text that lists
   the lower-tier exceptions. Combining gold + silver under one
   fuss inflates this workaround.

3. **Per-fraction `soll_fein_g` covers it, BUT.** Each fraction
   already specifies its own Soll-Fein independently. A combined
   `kronefod` could have:
   ```yaml
   fractions:
     "5":      {soll_rau_g: 2.24,   soll_fein_g: 2.016}    # gold
     "10":     {soll_rau_g: 4.4803, soll_fein_g: 4.0322}   # gold
     "20":     {soll_rau_g: 8.9606, soll_fein_g: 8.0645}   # gold
     "1":      {soll_fein_g: 6.0}                            # silver !
     "2":      {soll_fein_g: 12.0}                           # silver !
     "1/4":    {soll_fein_g: 1.452}                          # silver Scheide
     "1/10":   {soll_fein_g: 0.580}                          # silver Scheide
     "1/20":   {soll_fein_g: 0.0}                            # bronze
     ...
   ```
   This is technically valid YAML and validates against the
   schema. BUT the resulting Soll-values mix gold-fein (a yellow
   metal weight) with silver-fein (a white metal weight) in the
   same Fuß record. Downstream computation works; downstream
   *display* breaks (the Grundwerte block has a single `badge` →
   «Gold» or «Silber + Bronze» — one or the other, not both).

4. **Project consistency.** Every other Müntzfuß in
   `data/shared/fuesse.yml` is monometallic. Reichsgoldmünzfuß
   (German Empire), Reichsdukatenfuss, Pistolenfuß, Kronemont,
   Kronemont_fine, Guldkrone — each is one metal. The
   Reichsmark-silver-Kurant coins, if/when we model Germany,
   would go to a separate `reichssilberfuss` (not yet added). So
   the project's existing convention IS to split metals; combining
   Krone-fod alone would be inconsistent with everything else.

5. **Categorize routing.** `categorize.py` routes coins by `kind`
   (kurant / scheide / tarif / gedenk) and within scheide also by
   `metal` (copper / bronze split out). Mixing gold-kurant with
   silver-kurant in one Fuss makes the rendered «Kurantmünzen»
   sub-block visually mix yellow and white pieces in a single
   table — that may or may not be desired, but it's a visible
   layout change.

6. **Refactor cost.** ~54 coins were just migrated to the split
   model (commit 5111c56). Reverting to combined adds at least
   another migration step plus seed-builder and classifier rule
   updates. Not large in absolute terms, but a regression of
   recently-shipped work.

7. **Selective precedent.** «Subsidiary coinage under a separate
   subsidiary standard» IS a pattern used in numismatic catalogue
   work — see e.g. Krause-Mishler's separation of «Mark Banco
   Hamburg gold» from «Mark Banco silver» as separate entries.
   It's not historically wrong to model them separately as long
   as the linkage is clearly stated.

## Hybrid options (not currently used)

### Option C: combined `kronefod` with hierarchical denominations

Merge to one Fuß. fuss.metal=gold (the legal anchor).
fineness_standard=.900 (the gold standard).
fractions include all gold + silver + bronze with per-fraction
soll_fein_g (gold-fein for gold, silver-fein for silver, 0 for
bronze). fineness_display text explains the per-denomination
ladder. Grundwerte block lists every denomination.

Pros: matches historical/legal reality; one section on rendered
page; cross-language analogy with Reichsmünzfuß works.

Cons: stretches the schema's monometal assumption; `Grundwerte.
badge` can only say «Gold» (the primary anchor) which under-sells
the silver/bronze tiers; mixed-metal coin table in one section
breaks visual convention with other Fusses.

### Option D: combined with explicit «subsidiary» marker on fractions

Same as C but add a `Fraction.metal_override` field to the schema:
```python
class Fraction:
    soll_fein_g: float
    soll_rau_g: float | None = None
    metal_override: Literal["silver", "gold", "billon", "copper"] | None = None
```

Lets each fraction declare its own metal; Grundwerte rendering
walks fractions and groups them by metal_override for display.

Pros: cleanest data model — captures «1 Krone silver» and «10
Krone gold» as fractions of the same Fuß with distinct metals.

Cons: schema change ripples to every Fuß; needs render template
update; not a 10-minute change.

## Recommendation

**Keep the split** (Option A — status quo), but **strengthen the
narrative linkage** in both Fuss descriptions to make the unity
crystal clear at the reader-text level. Reasons:

1. The split is consistent with the project's existing convention
   (every other Müntzfuß is monometallic). Breaking the convention
   for Krone-fod alone would create an outlier and surprise readers
   who navigate from kronemont/guldkrone (silver/gold split) to
   Krone-fod (mixed).

2. The schema's `Fuss.metal` + `Fuss.fineness_standard` fields
   carry strong semantics. Workarounds (option C) put strain on
   downstream rendering. Option D (schema extension) is a future
   refactor opportunity but not justified by this one case alone.

3. The reader-experience concern (point 7 of the unity case) is
   real but mitigable:
   - Both fuss_periods narratives already say «<b>Krone-fod ·
     Skandinavische Müntzunion (Gold/Silber+Bronze)</b>» —
     emphasising they're TWO ASPECTS of ONE union.
   - The kronefod_silver hintergrund already cross-references
     `<code>kronefod</code>` for the gold side.
   - The 1873 Mønlov is cited in BOTH (ref18), making clear the
     legal unity.

4. If the user wants stronger unity signalling on the page, the
   cheap fix is rendering-side: add a shared parent heading
   «Krone-fod · Skandinavische Müntzunion (1873-1914)» above the
   two sub-sections in the timeline + page layout, with the two
   Fusses rendered as sub-blocks. This is a template change, not
   a data refactor — but it's not currently planned.

**If the user disagrees** and wants a true single-Fuss model, the
preferred path is **Option D** (schema-extended), not Option C
(workaround under existing schema). Option C papers over the
mismatch; Option D properly captures «one Fuß, hierarchical metals».

## Decision pending

User to pick:

- **A (status quo)** — split into kronefod + kronefod_silver, with
  strong cross-narrative linkage already in place. No changes.
- **B (timeline + page-level grouping only)** — keep the two
  Fusses in YAML but render them under a shared parent heading on
  the page + group them on the timeline. Template change, low
  cost (~ 1 commit).
- **C (combined kronefod under existing schema)** — merge to one
  Fuß; metal=gold; fractions include silver Soll-Fein. Workaround
  for the schema's monometallic assumption; cosmetic display
  issues likely.
- **D (schema-extended combined)** — add `Fraction.metal_override`
  to the schema; one `kronefod` Fuß holds all denominations with
  proper per-fraction metal. Cleanest data model; biggest refactor
  (schema, render template, downstream tooling).

## Bibliography (referenced from earlier research note)

See `docs/research/dk_kronefod_1873_research.md` for the full bibliography
(refs 18-23 in `data/locations/denmark-references.yml`). Key
sources for this analysis specifically:

- [Den skandinaviske flugt fra sølvet — danskmoent.dk](https://www.danskmoent.dk/artikler/flugt.htm) — explicit Latin-Monetary-Union rejection rationale; documents the monometallic-vs-bimetallic distinction.
- [Den Skandinaviske Møntunion — Wikipedia DA](https://da.wikipedia.org/wiki/Den_Skandinaviske_M%C3%B8ntunion) — describes Krone-Mønt as «en fælles møntenhed kronen, der hvilede på guldfoden, med underdelingsmønter i sølv og bronze» — i.e. ONE monetary unit with subdivisions.
- [Møntlove 1813-1875 — danskmoent.dk](https://www.danskmoent.dk/artikler/aclove1.htm) — legal index showing the 1873 Mønlov as one act.
- Münzgesetz 4. Dezember 1871 + 9. Juli 1873 (German Empire) — parallel «one law, multiple denomination tiers» pattern.
