# Reference artifacts (legacy HTML)

These are hand-built HTML artifacts from the research phase (claude.ai chat sessions before migration to this build pipeline). They are **read-only references** — the build system does not consume them directly.

Purpose: preserve the analytical content so it can be progressively migrated into YAML source data (`data/shared/` and `data/locations/`) as new locations are added.

## Files

### `muenzfuesse_v5.html` (57 KB, present)

Pan-German monetary standards overview, ca. 1566–1875. Contains 18 Münzfuß cards with mathematically verified data:

- Reichsmüntzfuß / 9-Thalerfuß (Hamburg, Lübeck: in Kraft bis 1875)
- Reichsdukatenfuß (23 Karat 8 Grän = 986 1/9 ‰)
- Burgundischer / Zinnaischer Fuß · 10½-Thalerfuß
- Leipziger / Torgauer Fuß · 12-Thalerfuß
- Graumannscher Fuß · 14-Thalerfuß (Preußen)
- Preußischer Banco-Fuß · 10⅔-Pfund-Banco-Fuß
- Conventions-Fuß · 20-Guldenfuß · 13⅓-Reichstaler-Fuß
- Konventionskuranttaler-Fuß · 13⅓-Thalerfuß
- Hannoverischer Cassengeld-Fuß · 12⅓-Thalerfuß
- Rheinischer 24-Guldenfuß (Bayern, Württemberg, Baden)
- Lübischer Courant-Fuß · 34-Markfuß (1726–1854) / 35-Markfuß (1855–1875)
- Hamburgische Bancovaluta (Reichstaler-Fuß 1619, Banco-Fuß 1769, Altonaer Fuß 1777)
- Bremische Louisdor- / Pistolenwährung · Thaler Gold
- Holsteinischer / Altonaer Thaler-Specie-Fuß · 9¼-Thalerfuß
- Dänisch-Norwegischer Courant-Fuß in Holstein/Schleswig
- Schleswig-Holsteinischer Courant-Fuß
- Süddeutscher Münzfuß · 24½-Guldenfuß
- Rigsbankdalerfuß · 18½-Thalerfuß
- Vereinsmünzfuß · 30-Thalerfuß · Zollpfundfuß
- Reichsgoldmünzfuß · 1395-Markfuß (Reichsmark 1871)

Each card includes: grid unit (Cöllnische Marck / Wiener Marck / Zollpfund), grid stops, fineness with period form display, Feingewicht calculation, Rechnungsfraktionen (denominational splits), and Territorien block showing which states used this standard when.

**Use as source material when:**
- Adding new location files (find which Münzfüße apply to that territory)
- Expanding `data/shared/stopes.yml` with fractions or descriptions
- Confirming pan-German context for a specific Münzfuß

### `lubeck_1750_1850_verified_complete.html` (18 KB, present)

Lübeck coin catalog 1749–1810, compiled from Numista (23 circulation types) + IKMK Berlin (37 specimens). Organized in three cards:

1. **Silver/Billon — 34-Mark-Fuß**: sorted by Feingewicht ascending, with Δg and Δ% columns vs. nominal standard. Includes: 1 Dreiling, 2 Sechsling, 4 Schilling, 8 Schilling, 16/32/48 Schilling.
2. **Speciesthaler — 9-Thalerfuß**: 1776 1-Thaler on the 9-Fuß (25.984 g fein), distinct from the Courant 34-MF system.
3. **Gold — Dukatfuß**: Lübeck dukaten 1730 (Jubilee), 1789–1801 (last mintings).

This artifact is the source material for a future `data/locations/lubeck.yml`.

## How to use these files

1. **When working on a new YAML location**, open the relevant reference HTML and find the block covering that territory's Münzfüße. Use it to seed phase definitions and coin lists.

2. **When verifying data**, cross-check the formulas/values in these artifacts against the YAML before deleting them. These encode many hours of empirical verification.

3. **Never edit these files.** They are frozen references. If a correction is needed, apply it to the YAML source data and run `python scripts/build.py`. Reference HTML stays as-is (it documents the research state at a point in time).

4. **When a reference HTML has been fully migrated to YAML**, its content is reproducible from the build pipeline. At that point, it can be moved to `reference/archived/` with a note pointing to the YAML files that replaced it.
