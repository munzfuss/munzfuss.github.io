# Pending audits and longer-term TODO

> **Read this at session start** — the entries below are open audit items
> that have not been actioned. CLAUDE.md links here so they don't get
> forgotten across sessions. When an item is done, move it to the
> "Done" section at the bottom (with the commit SHA) so we have a record.

## Open

### D. Triage `seed_unsorted` coins in denmark / hamburg / lubeck  *(opened 2026-05-04)*

**Background.** After bulk-importing 581 ucoin entries into proper
location files (commit `1abbef8`), three locations carry coins under
the placeholder `seed_unsorted` Müntzfuß:

- `data/locations/denmark.yml`     — 422 seed entries (years 1582–1875)
- `data/locations/hamburg.yml`     —  80 seed entries (years 1726–1873)
- `data/locations/lubeck.yml`      —  79 seed entries (years 1620–1797)

Each seed entry carries raw ucoin data (km, denom, year, fineness,
weight, diameter, url, tid) plus best-effort heuristic inference for
ruler/mint/metal. Every value flagged `verified: false`.

**Done criterion (per location).** All seed entries reclassified into
their proper Müntzfuß and gain `verified: true` for source-attested
fields. The location automatically reappears on the landing page once
its `seed_unsorted` count reaches zero — the build script
(`scripts/build.py::build_landing`) hides any location with even a
single seed entry, then re-checks on every build. No template/config
edit needed when the threshold is crossed.

**Recommended order.**

1. **Hamburg (80, smallest)** — needs new Hamburg-specific Müntzfüße
   defined in `data/shared/fuesse.yml` first (Bankthaler / Speciesthaler /
   Mark-Courant standards). Triage by ucoin Period + Hede equivalents.
2. **Lübeck (79)** — needs Wendisch-Lübisch Münzfüße defined (the
   existing 11_333_thaler proxy is incorrect for most Lübeck coins).
   The 1 already-curated entry (km-168-1-1752) is the model.
3. **Denmark (422, largest)** — most coins fit existing fuesse:
   - period_2940 (Speciedaler 1582-1624) → 9_25_thaler / 9_thaler
   - period_1147 (Rigsdaler 1625-1699) → 9_25_thaler / kronemont
   - period_1115 (Rigsdaler 1699-1749) → 9_25_thaler / reichsdukatenfuss
   - period_846  (Rigsdaler 1750-1812) → 11_333_thaler / 18_5_thaler
   - period_647  (Rigsbankdaler 1813-1854) → 18_5_thaler
   - period_646  (Rigsdaler rigsmønt 1854-1873) → 30_thaler
   - period_374  (Christian IX 1873-1906) → reichsgoldmuenzfuss
   Some need new Royal Danish standards added (Kurantmøntfod 1726+).

---

### C. Bremen-Archbishopric Frederick (II/III) coinage 1641–1643  *(opened 2026-05-03)*

**Surfaced during.** Cross-check of the 3 Numista issuer-list pages
linked from item B (now closed). The Bremen-archbishopric page
returned 3 Frederick III Bremen issues — historically connected to
our Holstein register because Frederick III held the Bremen
archbishopric (as Frederick II) before becoming Danish king in 1648.

**3 coins to model into a future `data/locations/bremen.yml`:**

| Coin | KM# | Numista | Metal / spec |
|---|---|---|---|
| 1 Thaler Frederick of Dänemark 1641 | KM# 38 | N#129848 | Silver .888, 29.23 g, Dav CCT# 5078/5078A, Jungk# 363… |
| 2 Schilling Frederick II 1641–1643 | KM# 36 | N#429659 | Silver |
| 1/16 Thaler 1641–1643 | KM# 37.1 | N#394107 | Silver, 1.57 g, ⌀19.3 mm, Jungk# 366–371 |

These are **NOT in scope of `schleswig_holstein.yml`** — Bremen archbishopric
is a distinct ecclesiastical territory, not a Schleswig-Holstein
duchy. They would belong in a separate `bremen.yml` location.

The user opened these as part of TODO B research; recording here so
the link from B's closure isn't lost. Whenever Bremen comes up as a
new location target, this is the seed list.

**Done criterion.** Bremen location file created with these 3 coins
(plus whatever else the bremen.yml scoping work surfaces) — OR an
explicit decision that Bremen stays outside the project scope.

---

## Done

### A. Verify continuous year-ranges for gaps  *(closed 2026-05-03)*

**Outcome.** All 15 coins audited against Numista `_issues.json` cache:

- **10 confirmed continuous** — Numista per-year breakdown explicitly
  enumerates every year in the declared range (no gaps):
  km-137117 (1589–1601), km-5-ja (1594–1605), km-103 (1671–1682),
  km-8-ernst (1600–1609), km-25 (1640–1648), km-155 (1695–1702),
  km-185 (1703–1710), km-183 (1703–1709), km-735 (1842–1848),
  km-193 (1706–1712).
- **4 «is_dated: false»** — Numista records the type as a single
  range without per-year split (per-year breakdown unavailable from
  Numista; left as continuous, undocumented gaps possible):
  km-3-ja (1590–1616), km-137419-ernst (1601–1622),
  km-278283-ernst (1601–1622), km-137112-otto (1567–1576).
- **1 special** (km-120-chr-v-1787) — its Numista link N#34037 was
  incorrect (pointed to Mauritius ½ Rupee 1946); removed. No correct
  Numista entry found for Christian VII 2 Sechsling Tower Hill 1787–1800.
  ucoin tid 90571 records as range 1787–1800 without per-year split —
  left as continuous.

All 15 entries gained a `verification_note` documenting the audit so
future re-runs of similar checks won't re-flag them. Per-coin notes
quote the audit date (2026-05-03) and the source consulted, satisfying
the original done-criterion: «range confirmed against an explicit
source».

---

### B. Investigate Frederick III silver «1 Krone» 1659–1660 (N#313341)  *(closed 2026-05-03)*

**Outcome.** N#313341 turned out to be a **duplicate Numista listing
of our existing `km-x001-fr-iii-1659`** (Type II, Hede 153A). Numista
carries two parallel entries for the same Davenport-3675 type:
N#111285 under the «City of Glückstadt» issuer (KM# B43) and N#313341
under the «Schleswig-Holstein duchies» issuer (KM# 95). The km-x001
entry already cites both Numista IDs in `sources` and explicitly
documents the duplication in its body note («same coin, duplicate
Numista listing»).

**Cross-check of the 3 research links** (all Frederick III, ru=437):
- `schleswig_holstein_danish_duchies` (3 hits): all 3 already in base
  — km-90 (1 Sechsling), km-x001 (1 Krone, this item), km-103 (4 Marck
  Danske, listed under Christian V on Numista despite the FRIII filter)
- `gluckstadt_city` (9 hits): all 9 already in base — Guldkrone,
  1/16 Speciedaler, both 4-Mark-Dansk types, Speciedaler 1664-66,
  ⅛ Reichs Daler, both 1/16-Thaler bust types, 1 Ducat 1666-69
- `bremen_archbishopric` (3 hits): not in base, not in Holstein scope
  — moved to Item C as seed for a future `bremen.yml`

**Net result.** No new Holstein coin to add from item B. The «silver
Krone» discovery turned into a Numista-duplicate normalisation that
was already done.

(none yet)
