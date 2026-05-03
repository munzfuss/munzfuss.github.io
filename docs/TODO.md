# Pending audits and longer-term TODO

> **Read this at session start** — the entries below are open audit items
> that have not been actioned. CLAUDE.md links here so they don't get
> forgotten across sessions. When an item is done, move it to the
> "Done" section at the bottom (with the commit SHA) so we have a record.

## Open

### A. Verify continuous year-ranges for gaps  *(opened 2026-05-02)*

**Problem.** Many coins in `data/locations/schleswig.yml` carry
`year_first` + `year_last` as a continuous range (e.g. `1813-1819`,
`1590-1616`). For some types the actual mintage was **non-continuous**
— e.g. KM #683.1 was struck only in **1813, 1818, 1819**, not every
year 1813→1819. Recording it as a continuous range overstates the
issuance and is silently wrong. CLAUDE.md §4 ("Source years are
immutable") forbids both narrowing AND inflating; a continuous range
when the source documents gaps is inflation.

**Scope (snapshot 2026-05-02).** 15 base coins have a continuous range
of ≥5 years and no `year_ranges` block. Worst offenders:

| coin_id | nominal | range | span |
|---|---|---|---|
| km-3-ja-1590 | 1½ Thaler | 1590-1616 | 26y |
| km-137419-ernst-1601 | 1 Thaler | 1601-1622 | 21y |
| km-278283-ernst-1601 | 1 Thaler | 1601-1622 | 21y |
| km-120-chr-v-1787 | 2 Sechsling | 1787-1800 | 13y |
| km-137117-adolph-xiv-1589 | 1 Groschen | 1589-1601 | 12y |
| km-5-ja-1594 | 1/16 Thaler | 1594-1605 | 11y |
| km-103-fr-iii-dk-1671 | 4 Marck Danske | 1671-1682 | 11y |
| km-137112-otto-iv-1567 | 1 Pfennig | 1567-1576 | 9y |
| km-8-ernst-1600 | 1 Groschen | 1600-1609 | 9y |
| km-25-chr-iv-1640 | 1 Søsling Lybsk | 1640-1648 | 8y |
| km-155-fr-iv-1695 | IIII Schilling | 1695-1702 | 7y |
| km-185-karl-fr-1703 | 4 Schilling | 1703-1710 | 7y |
| km-183-karl-fr-1703 | 1 Schilling | 1703-1709 | 6y |
| km-735-chr-v-1842 | 1 Rigsbankdaler + 30 Schill. Courant | 1842-1848 | 6y |
| km-193-karl-fr-1706 | 6 Pfennigs | 1706-1712 | 6y |

**How to verify (cheapest first).**

1. **Numista cache** — check `scripts/cache/numista/<nid>.json` for `min_year/max_year` (already cached for many) and `<nid>_issues.json` for per-year issuance breakdown (138 of 542 coins have it cached). The `_issues.json` lists each documented year as a separate entry, which is what we need.
2. **ucoin cache** — `scripts/cache/ucoin/_url_index.json` already gives us the type-issuance year range per ucoin entry; for discrete years we need to fetch the actual ucoin coin page (Markdown via Apify, or browser via Chrome MCP). Cheap.
3. **Hede / Bruun catalogues** — paper sources cited in coin notes; reliable but requires manual lookup.

**Suggested workflow.**
- Start with the worst spans (≥10y) since those are most likely to have gaps.
- For each, fetch the `_issues.json` from cache OR the ucoin page; see which years actually appear.
- If gaps are confirmed: update `year_label`, set `year_last`, add `year_ranges: [[...], [...]]`.
- If continuous mintage is confirmed: leave as-is and add a brief note in `verification_note` so we don't re-check it.

**Don't burn Numista API quota on this** without explicit user
permission (per CLAUDE.md "Numista API budget" rule, May-2026-bound).
Use cached `_issues.json` files where available; for the rest, prefer
ucoin pages via Chrome MCP / Apify.

**Done criterion.** All coins with continuous ≥5y range either:
- have a `year_ranges` block reflecting the actual mintage, OR
- have a `verification_note` confirming the continuous range was checked
  against an explicit source.

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

These are **NOT in scope of `schleswig.yml`** — Bremen archbishopric
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
