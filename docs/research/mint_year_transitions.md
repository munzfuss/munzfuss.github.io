# Mint year-aware classification — researched transition dates

Source-of-truth for `scripts/lib/mint_registry.py::_MINT_REGISTRY[<mint>].year_overrides`.
Each entry has primary + corroborating source citations and a verbatim quote
where possible. Per CLAUDE.md §0 (no invention) — no transition lands in the
year-aware classifier without a documented source.

Convention (locked 2026-05-26):

- `year_to` is **exclusive** (year < cutoff → pre-period; year ≥ cutoff →
  post-period). Multi-year ranges that cross a cutoff are handled per
  `scripts/lib/v2_entity_classify.py` (currently: surface to curator;
  decision pending).

---

## ✅ Altona — 1640 (Schauenburg-Pinneberg → Royal Holstein)

**Cutoff: `year < 1640` → `schauenburg_pinneberg`; `year ≥ 1640` →
`royal_holstein`.**

### Historical context

Altona belonged to the County of Holstein-Pinneberg, ruled by the Schauenburg
(House of Schaumburg) dynasty, from the late mediaeval period until 1640.
Count Otto V von Schaumburg-Pinneberg ruled 1635–1640 and died childless
in 1640, extinguishing the male line of the House of Schaumburg. Holstein-
Pinneberg (including Altona) was then merged into the Duchy of Holstein
under Danish royal administration; Christian IV established Altona as a
royal mint shortly after.

### Sources

1. **Wikipedia EN — Altona, Hamburg**, accessed 2026-05-26 —
   <https://en.wikipedia.org/wiki/Altona,_Hamburg>:
   > «In 1640, Altona was part of Holstein-Glückstadt.»

   This places Altona explicitly within Holstein-Glückstadt (= royal-
   Holstein, the Danish king's portion centred on Glückstadt) in 1640.

2. **Wikipedia EN — House of Schauenburg**, accessed 2026-05-26 —
   <https://en.wikipedia.org/wiki/House_of_Schauenburg>:
   > «After the death in 1640 of Count Otto V without children, the
   > House of Schaumburg became extinct.»
   > «The County of Holstein-Pinneberg was merged with the Duchy of
   > Holstein.»

   Confirms 1640 as the dynastic extinction year. Holstein-Pinneberg
   merged into Holstein (Danish royal portion).

3. **Wikipedia EN — County of Schaumburg**, accessed 2026-05-26 —
   <https://en.wikipedia.org/wiki/County_of_Schaumburg>:
   > «After the childless death in 1640 of Count Otto V, the House of
   > Schaumburg became extinct.»

   Independent corroboration of the death year.

### Project-scope verification

V2 seed inventory currently holds 67 entries with mint=Altona AND
year_last < 1640 (Schauenburg era — Adolf XIII, Ernst III, Otto V) and
149 entries with year_first ≥ 1640 (Royal Holstein era — Christian IV
onward). NumisMaster + Bruun (when meta_line tags Schauenburg) already
classify Schauenburg-era Altona under `schauenburg_pinneberg`; the
year-aware classifier brings the remaining ucoin / Galster / V1-bootstrap /
Bruun-not-meta-tagged entries into agreement.

### Pending

- **Exact day/month in 1640** of Otto V's death (relevant only for
  border-case coins dated 1640 — none currently in scope per audit).
  Some sources cite November 1640; not verified against primary.
- **Disambiguation `schauenburg_pinneberg` vs `holstein_schauenburg_county`**:
  both entity tags exist in our schema; pre-1640 Altona uses
  `schauenburg_pinneberg` per current source-builder convention
  (NumisMaster + Bruun). Distinction between the two tags needs
  separate review; deferring for now.

---

## ⏳ Rinteln / Oldendorf / Stadthagen / Bückeburg — 1640 (deferred)

The same Otto V 1640 dynastic extinction divided the **non-Pinneberg**
portion of the Schaumburg counties between Lüneburg, Schaumburg-Lippe
(Bückeburg-centred), and the County of Schaumburg under Hesse-Cassel
personal union (Rinteln, Stadthagen, Oldendorf).

Project scope holds 5 Rinteln + 11 Oldendorf entries, ALL pre-1640.
No post-1640 entries → year-aware override is moot for our data right
now. The pre-1640 entity is `holstein_schauenburg_county` per current
registry. Documenting the eventual post-1640 destinations is deferred
until either we acquire post-1640 entries OR we wish to formally
declare the post-cutoff entity tag.

---

## ⏳ Rendsburg — 1716–1720 Holstein-Gottorp-Rendsburg (deferred)

Brief period during the Great Northern War when Duke Christian August
of Holstein-Gottorp held Rendsburg-area mint rights distinct from the
royal Danish administration. NumisMaster (4 entries) + Bruun + ucoin
attest 1716-1720 Rendsburg coinage with Gottorp issuer.

Deferred pending source verification — researching exact start /
termination dates of the Holstein-Gottorp-Rendsburg arrangement before
adding override.

---

## ⏳ Other mints in scope without immediate impact

| Mint | Transition | Project impact |
|---|---|---|
| Malmö | 1658-02-26 Treaty of Roskilde (Danish → Swedish) | 28 entries all pre-cutoff → already correctly `danish_realm`; no flip needed. Future post-cutoff entries would be out-of-scope. |
| Landskrona | Same as Malmö | 1 entry pre-cutoff → same. |
| Visby | 1645-08-13 Treaty of Brömsebro (Danish-Gotland → Swedish) | 6 entries pre-cutoff → already correct. |
| Haderslev | Pre/post-1660 royal/Gottorp split (Karlstad treaty) | 11 entries all pre-period; per V1 convention all tagged `royal_holstein`. No flip needed in current data. |
| Husum | 1864 Schleswig war (Danish → Prussian) | 14 entries all pre-1864 → already correct. |
| Flensburg | Same as Husum | 1 entry pre-1864 → already correct. |
| Christiania / Oslo / Bergen / Kongsberg | Always Danish-Norway 1380-1814 (within scope) | n/a — single-period in our window. |
| Hamburg, Lübeck | Always Hanseatic during scope | n/a. |

All these mints would benefit from documenting their boundary years
for future-proofing, but require no override in the current data
inventory.

---

## How to add a new transition

1. Research the exact transition year from primary or recognised
   secondary sources (Wikipedia is acceptable when it cites primary
   sources; the verbatim quote serves as locator per CLAUDE.md §5a).
2. Add the verbatim quote + accessed-date + URL to this document.
3. Pick the cutoff convention: `year < cutoff` → pre-entity, `year ≥
   cutoff` → post-entity (exclusive convention per 2026-05-26 user
   direction).
4. Add the override to `scripts/lib/mint_registry.py::_MINT_REGISTRY`
   under the relevant canonical mint key, in `year_overrides: [...]`.
5. Add test cases in `tests/test_classify_mint_year_aware.py`.
6. Run `scripts/maintenance/audit_entity_misclassifications.py`
   (dry-run, with year-aware enabled) to surface entries that would
   reclassify; review the list before --apply.
