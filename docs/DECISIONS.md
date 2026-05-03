# Research Decisions Log

Chronological log of significant analytical and architectural decisions made during research. Each entry explains what was decided and why, so future sessions (human or AI) can understand the reasoning without re-deriving it.

---

## 2026-05 — Landing-page filter for unsorted-seed locations

`build_landing` now hides any location card whose coins include at least one entry under `fuss: seed_unsorted` (the bulk-import placeholder). Per-language pages still build and remain reachable by direct URL — only the landing card disappears.

The filter is automatic and idempotent: every build re-evaluates `visible_locations = [loc for loc in locations if not any(c.fuss == "seed_unsorted" for c in loc.coins)]`. As soon as a location's last seed entry is moved into a real Müntzfuß, the next build re-includes the card. No template or config edit needed at the threshold.

Build log surfaces the hidden set: «🙈 Landing hides 3 location(s) with unsorted seed entries: denmark, hamburg, lubeck».

## 2026-05 — Strict-cut Royal Danish coins move to denmark.yml

After the project picked up many Royal Danish Copenhagen issues during ucoin imports — some by mistake, some as «cross-mint context» for Holstein equivalents — settled on a **strict cut**: any pure Royal Danish issue (`mint: Kopenhagen`, `issuing_entity: danish_realm`, no Holstein-side Krause KM#) belongs in `data/locations/denmark.yml`, not in `schleswig_holstein.yml`.

This applied even to two coins previously argued to deserve the «cross-mint context» exception:
- **km-137-chr-iv-1644** (Hebræermønt 1644 Copenhagen — sister to km-32 Glückstadt Hebræermønt 1645)
- **km-303-fr-iii-1668** (Guldkrone Copenhagen 1668 — reformed continuation of km-40-2 Glückstadt Guldkrone 1657–1660)

Migrated in two rounds (commits `bd99259`, `47ac788`):
- Round 1 (21 coins): the entire Christian IV Kronemønt 1618–1624 series + 3 Reichsdukatenfuß ducats 1738–1749.
- Round 2 (25 coins): 23 km-x*** entries originally tagged as «mint: Glückstadt» but with ucoin Period = «Rigsdaler 1625-1699» / «Speciedaler 1582-1624» (= Royal Danish Copenhagen) — re-attributed to Kopenhagen + danish_realm. Plus the 2 cross-mint exceptions above.

ucoin's Period field is the canonical mint signal: pages 2940 / 1147 / 1115 / 846 / 647 / 646 / 374 are all Copenhagen; only page 2939 («Glückstadt 1617-1773») and 2995 («Holstein-Gottorp-Rendsburg 1716-1720») mark Holstein-mint coinage. KM-DK# in `catalog.others` alone is NOT evidence of Copenhagen mint — Krause assigned KM-DK# to many Glückstadt-mint coins as cross-references; it is the *absence* of a Holstein-side KM# combined with Copenhagen-period ucoin that disqualifies a coin from `schleswig_holstein.yml`.

## 2026-05 — Location id `schleswig` → `schleswig_holstein`

The location file covers BOTH Schleswig and Holstein duchies (and Royal Holstein, Gottorp, Sonderburg, Schauenburg-Pinneberg, etc.). Just `schleswig` is a misnomer; `holstein` would be just as wrong (Schleswig duchy mints — Schleswig itself, Tönning, Reinfeld — wouldn't fit). Settled on the proper compound `schleswig_holstein` (commit `25544eb`).

Touched 27 files: file rename, all `id: schleswig` → `id: schleswig_holstein`, all path strings in maintenance scripts, all CLI `--location` flags, Python identifiers (HOLSTEIN → SCHLESWIG_HOLSTEIN), and prose mentions in README/CLAUDE.md/docs that referred to the *file* (geographic «Schleswig» / «Schleswig-Holstein» mentions and HOLSTEIN_SOURCES / EASY_HOLSTEIN_MINTS mint constants left intact).

URL impact: live `/schleswig/` paths break and become `/schleswig_holstein/`. Acceptable since the project is in active development and no external linkers depend on stable URLs.

## 2026-05 — Bulk-import seed buckets into denmark/hamburg/lubeck

The ucoin categoriser had been holding 581 entries in three seed buckets (`H_DENMARK_SEED` 422, `X_HAMBURG_SEED` 80, `X_LUBECK_SEED` 79) marked «out of Schleswig scope but worth keeping for future location files». Bulk-imported all 581 into the corresponding location files (commit `1abbef8`):

- `denmark.yml` :  46 → 468 coins (curated 46 + 422 seed)
- `hamburg.yml` :   0 →  80 coins (NEW location file)
- `lubeck.yml`  :   1 →  80 coins (existing stub + 79 seed)

Each seed coin carries its raw ucoin data (km, denom, year, fineness, weight, diameter, url, tid) plus best-effort heuristic inference: ruler from Royal Danish reign chronology (or hanseatic city-state name), mint = location default, metal heuristic from fineness band. All values flagged `verified: false`; verification_note in DE/EN/UK explains the bulk-import status and what's pending.

Required infrastructure:
- A new placeholder fuss `seed_unsorted` in `data/shared/fuesse.yml` — empty `fractions`, so no soll/delta computation runs and the rendered tables show only what ucoin actually attests.
- Two new issuing entities `hanseatic_hamburg` and `hanseatic_lubeck` in `data/i18n/issuing_entities.yml`.
- Categoriser dispatcher reorder: direct ucoin-tid bridge now wins over MANUAL_OVERRIDES, so bulk-imported coins are recognised as «in base» on the next ucoin re-fetch instead of re-bucketing as seed. Net effect: every one of the 705 ucoin entries now resolves to processed_in_base; all active and seed bucket counts are 0.

Detailed per-coin work moves each seed entry into its proper Müntzfuß and flips `verified: true` for source-attested fields. See `docs/TODO.md` item D for the recommended order (Hamburg → Lübeck → Denmark) and the period→fuss mapping table for the Denmark cluster.

## 2026-05 — Christian IV's Kronemønt 1618 series is Royal Danish, not Holstein

`kronemont_chr_iv` — the 1618–1624 Christian IV Kronemønt programme — is **entirely Royal Danish Copenhagen**. All 18 coins (¼/½/1/2 Krone + Kroneskilling sub-units) live in `denmark.yml`. Glückstadt was founded in 1617 but its 1618 production focused on Reichsthaler/Skilling, not Krone-fractions. Wilcke I p. 152 documents the sub-Krone series without attributing it to Glückstadt; the Royal Danish Krause KM-DK# 56 ⅛ Krone was originally added to schleswig.yml as «mint Glückstadt provisionally entered», then audit revealed all 18 share that misattribution.

Three independent signals confirm Copenhagen for every coin in the series: (a) ucoin Period = «Speciedaler 1582-1624» (Royal Danish page, not Glückstadt), (b) Numista issuer_code = `danemark` with empty `numista_mints`, (c) Krause cross-references to KM-DK# numbers without any Holstein-side KM#.

In `schleswig_holstein.yml` the `kronemont_chr_iv` Münzfuß remains in `fuss_order` with the full historical fuss_periods description but zero coins — Vereinsmünzfuß / 30_thaler pattern: «the standard was in circulation, no Holstein issues struck». pdate_label appends «in Holstein keine eigenen Prägungen — siehe denmark.yml».

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
