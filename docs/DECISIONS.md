# Research Decisions Log

Chronological log of significant analytical and architectural decisions made during research. Each entry explains what was decided and why, so future sessions (human or AI) can understand the reasoning without re-deriving it.

---

## 2026-03 — Bremen Thaler Gold silver Münzfuß (1840–1872) reconstruction

Bremen's silver Münzfuß from 1840 was reconstructed independently: **13⅓ aus der rauhen Kölner Mark at fineness 71/72 (= 23 Karat 8 Grän = Reichsdukat gold standard applied to silver)**.

- Empirical Feinsilber content of ~0.240216 g/Grote confirms this.
- The Jever 1764 4-Grote coin inscription «240 OBF FEIN MARC» independently documents the identical standard 76 years earlier — confirming it as an established North German coastal regional standard, not a Bremen innovation.
- Must be recorded as an **original reconstruction**, not citable secondary literature.

**When to note this**: in Bremen's YAML, the fuss block needs `verification_note` explaining this is a first-principles reconstruction from coin inscriptions + Jever precedent, not a published historical standard. User expects this transparency.

## 2026-03 — Bremen periodization before 1870

Before 25 July 1870 Verordnung, **Bremen had no formal Kurantwährung** — Pistole and foreign gold circulated de facto; Thaler Gold was *only a Rechnungseinheit*. Only with the 1870 Verordnung did Thaler Gold become gesetzliches Zahlungsmittel.

When working on Bremen data: pre-1870 coins labeled "Thaler Courant" (e.g., Bremer Bank banknotes) need a note explaining this reclassification happened in 1870 — the inscription predates formal currency status.

## 2026-03 — Gold:silver ratio in Bremen

The implied ratio in Bremen's Friedrich d'or = 5 Thaler Gold exchange rate is **~14.34:1** (older standard), consistent with Gresham's Law keeping silver in circulation while the 1840 market rate was ~15.5:1.

## 2026-04 — Kronemønt as a separate Münzfuß (not under 9¼)

Kronemønt (1618–1696) is classified as its **own fiscal Tarifmünze category**, not as "reduced 9¼-Fuß". Empirically ≈15.65 Kronen/Marck; ≈10.43-Thaler-Fuß-equivalent. But the fundamental point is that **the Krone was a Tarifmünze** — traded at a king-set value *above* silver content. The difference = Seigniorage, not market price.

Confusing it with a reduced Speciesthaler would misrepresent the economic mechanism. It gets its own fuss entry (`kronemont`) with `kind: tarif` for all its coins.

## 2026-04 — Lübeck 1776 Speciesthaler is 9-Fuß, not 34-Mark-Fuß

The 1776 Lübeck 1-Thaler (233.856 g ÷ 9) is on the 9-Thalerfuß. Should not be grouped with 34-Mark-Fuß Courant-standard coins — these are separate monetary populations and must be analyzed separately.

## 2026-04 — Hamburg Bancovaluta: pre/post-1769 are distinct phases

Hamburg Bancovaluta has two fundamentally different phases separated by the 1769 reform:
- **1619–1769 · Reichstaler-Fuß**: 1 Reichstaler (9-Fuß) = 3 Marck Banco; bank fund nominally backed by Reichstaler. But de facto circulation degraded (Zinnaischer + Leipziger Fuß coins mixed in), making reform in 1769 mandatory after Seven Years' War.
- **1769 · Hamburgischer Banco-Fuß**: 27⅝ Marck Banco per feine Marck; einlagen valued by Feinsilber, not nominal. 
- **1777 · Altonaer Banco-Fuß**: 27¾ Marck Banco — further refinement for Holstein.

When modeling Hamburg: these must be **three separate phases**, not one "Bancovaluta 1619–1875".

## 2026-04 — 13⅓-Thalerfuß: separate fuss from Konventionsfuß

Despite mathematical equivalence (3/4 × Konventionstaler = Kuranttaler), the **13⅓-Thalerfuß** (Konventionskuranttaler-Fuß) should be treated as a **distinct fuss**:
- As a rechnerische Einheit throughout Norddeutschland wherever Konventionsfuß was used but Groschen-Teilung (24/Taler) kept
- Specific prägungen: Sachsen-Weimar-Eisenach 1760 (explicit «13⅓ ST. EINE FEINE MARCK»), Hessen-Kassel 1776/78/79 Sterntaler, Oldenburg 1761–1765

The 17,53920 g Feingewicht value coincides with Bremen's Thaler Gold Raugewicht (986 1/9‰), which is a pure numerical coincidence — different logic (feine Marck-basis for Konv.kurant; rauhe Marck-basis for Bremen Gold).

## 2026-04 — KM# 176 Speciesthaler 1700 "Unterfuß" — non-standard anomaly

Bruun-14231, 26,14 g rau weighs significantly less than the 9¼-Fuß standard (29 g rau). Calculated at .875 fineness: Ist ≈ 22,87 g → implied 10,225-Fuß — **not 9¼**.

Likely a one-off "reduzierter Tönning-Speciestaler" under Friedrich IV. in his last year before death at Klissow (19 July 1702). No secondary literature explanation available online. Must be flagged as `verified: false` with detailed `verification_note`.

## 2026-04 — KM# 152, 154, 154a (pre-1841 Rigsbankskilling) are NOT dual-denominated

Initially marked with `(?)` pending verification. Confirmed by Numista legend transcripts:
- Pre-1841: «*16* REICHS=BANK SCHILLING. [Jahr]. [MM]» — **single inscription**
- Post-1841 (Forordning 18. Dez. 1841, Christian VIII.): dual-inscribed with Schleswig-Holstein Schilling Courant

KM# 152/154/154a belong to 18½-Fuß Phase A with `nominal: "16 Reichsbank Schilling"` (single). Dual-denom begins with KM# 721/733/734/737 in Phase B.

Serhii explicitly requested that `(?)` markers must be removed once verified — don't leave speculative markers in place after confirmation.

## 2026-04 — Coin Nominal field: only literal inscription

**Principle established, then applied retroactively to 7 rows**:

Only what is engraved on the coin goes in `nominal`. Calculated equivalents → `note`.

Fixes applied:
- KM# 82 «8 Skilling Dansk (= 4 Skilling Lybsk = 1/12 Speciedaler)» → «8 Skilling Danske»
- KM# 42.1 «1/16 Speciedaler (= 3 Skilling Lybsk)» → «1/16 Reichsthaler Holstein-Dänisch» (matching actual legend MONNO GLVCKSTAD...XVI·E·REIC·HS·DA)
- KM# 124/150 «1/24 Thaler Species ↵ 2½ Schilling Courant» → «2½ Schilling Courant» (coin says only "2½ SCHILLING COURANT" without SP-Angabe)
- KM# 250 «24 Skilling Danske (Rigsort = ¼ Rigsdaler Courant)» → «24 Skilling Danske» («Rigsort» is a historiographical nickname, never engraved)

Rule: always verify against actual coin inscription (from museum catalog, auction transcript, high-res photo). If uncertain, mark `verified: false` on the nominal itself.

## 2026-04 — "Schillingfuß" is not a real Münzfuß

Early drafts labeled small Billon coins as being "in Schillingfuß". **This is wrong** — Münzfuß is defined by the head silver coin (Speciestaler). Schilling is a nominal *within* that Münzfuß, not a separate fuss.

All 7 Tönning Scheidemünzen (KM# 155, 158, 183, 185, 212, Lange 438, KM# 164 variant) are now correctly classified as belonging to 9¼-Fuß with `kind: scheide`.

## 2026-04 — Kurant vs Scheide as sub-category of phase

Within each phase of a fuss, coins are further split into:
- ✦ Kurantmünzen (green divider): vollwertig, nominal ≈ silver content
- ∘ Scheidemünzen (amber divider): nominal > silver content, local only

This is economic, not decorative. **Mandatory** for any phase that has both categories. Separation reveals when/how Seigniorage was built into the system.

## 2026-04 — 3 Pfennig Preußen 1861–1873 valid in Holstein only from 1866

Numista shows emission dates 1861–1873 for Prussian 3 Pfennig, but in Holstein it became gültig only after Preußen-Annex 24. Aug. 1866. Year label should reflect Holstein-validity, with a footnote.

General principle: **location-specific validity takes precedence over emission period** when the coin belongs in that location's data. A Prussian 1861 coin is not "in Holstein 1861" unless it actually circulated there before annexation.

## 2026-04 — Separate tables for Kurant/Scheide within phases

After noting the conceptual importance of the Kurant/Scheide distinction, implemented as visual split in rendered HTML:
- Green-left-border divider for Kurant sub-block
- Amber-left-border divider for Scheide sub-block
- Each sub-block is a full `<table>` with its own thead — easier to scan at a glance

Added CSS classes `.mt-subcat.kurant` and `.mt-subcat.scheide`. Template enforces this structure automatically.

## 2026-04 — Architecture migration to YAML + build pipeline

Direct HTML editing hit scaling limits. Moving to:
- YAML source data in `data/`
- Pydantic-validated schema
- Python build pipeline → HTML output
- GitHub Actions for deploy

Target: current 180KB Schleswig HTML reproduced 1:1 by build script, then i18n (DE/EN/UK) and landing page added. Subsequent locations (Bremen, Hamburg, Lübeck) require only new YAML files, no code changes.

---

## Decision template for future entries

```markdown
## YYYY-MM — [Short title]

[One-paragraph summary of the question and decision.]

[Reasoning: what evidence drove the decision, what alternatives were considered.]

[Scope: which files/fields are affected.]

[Validation: how to verify the decision is still correct if questioned later.]
```
