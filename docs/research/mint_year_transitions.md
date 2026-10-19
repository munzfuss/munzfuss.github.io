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

## ✅ Kongsberg — 1815 (Danish-Norway → Kingdom of Norway, curator 2026-10-19)

New entity `norway` (out of scope, renders on no page) for Norway after the
Treaty of Kiel (14 January 1814). Cutoff `year_from: 1815`: the first
Norwegian coins after 1814 are dated 1816 — Numista N# 49457, 1 Skilling
1816, Carl XIII, KM 284, Kongsberg (https://en.numista.com/49457); Wikipedia
EN «Norwegian speciedaler», Coins: «In 1816, coins in circulation from the
previous currency remained in circulation, with only 1 skilling coins being
minted.» No 1814 or 1815 Norwegian coin in any of our caches (KMM, Bruun,
Numista, NGC, NumisMaster, ucoin; checked 2026-10-19). Curator rule: if the
first issue is 1815 or later, the cutoff is 1815.

Mints: Kongsberg is the only one operating in Norway after 1814 (no
post-1814 coin with another mint in our data); Christiania moved to
Kongsberg in 1686 (no.wikipedia «Den Kongelige Mynt»: «I 1686 ble
«Mynten» flytten til Kongsberg»). The registry's other Norwegian mints
(Christiania, Bergen, Gimsø, Nidaros) need no override.

Mechanism: the Kongsberg `year_overrides` and the year-aware «Norge»
nation rule route by mint / nation; `mint_registry.norway_split_entity`,
applied by the seed writer to every source, routes by date whatever the
signal (Bruun region NORWAY, Numista issuer «Norway»), counts a range that
opens in 1814 and runs on as post-1814 (KMM 471237, 2 Krone «1814-1914»
jubilee), and keeps a coin naming a Danish king in `danish_norway` (KMM
148142 «1 Rigsbankdaler, Frederik 6, 1834, Kongsberg» — curator to review).
Merger: `norway` shares Krause's Norway register `nor`.

Impact 2026-10-19: 203 seeds (KMM 185, Bruun 18) → `norway`; 197 finals,
classification kept (kronefod 121, 18_5_thaler 21, 9_25_thaler 1).

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

## ✅ Rendsburg — 1716–1720 is ROYAL DANISH, no override needed (closed 2026-07-29)

**The Gottorp premise was wrong.** The earlier note here read: «Brief period
during the Great Northern War when Duke Christian August of Holstein-Gottorp
held Rendsburg-area mint rights distinct from the royal Danish administration.
NumisMaster (4 entries) + Bruun + ucoin attest 1716-1720 Rendsburg coinage with
Gottorp issuer.» Checked at the curator's request; it does not hold, and it
mis-stated what Bruun and ucoin say.

**The coins are Frederik IV's.** danskmoent catalogues them in the *Frederik IV*
volume — Hede 60 (1 Dukat 1718-1719), Hede 61 (½ Dukat 1719), Hede 62
(12 Skilling 1716-1720), Hede 63 (1 Skilling 1719-1720) — and Bruun, ucoin,
Numista and ~50 KMM specimens all name Frederik IV as ruler. danskmoent even
names the mintmaster of the 1720 skilling: Bastian Hille at Rendsborg. The
12-skilling pieces were reduced to 10 skilling by the Danish ordinance of
15 July 1726, a royal act over royal money.

**The Gottorp label exists in exactly one place**: NumisMaster's `country` field
reads «HOLSTEIN-GOTTORP-RENDSBORG» on four records, all with `ruler: None`. That
is a Krause section heading, not a statement about the issuer. Those four were
the «4 entries» the old note cited.

**The politics rule it out.** Rendsburg was the Danish crown's second-largest
fortress, rebuilt by Christian V in 1690-1695 (Kron- and Neuwerk on both banks
of the Eider). Denmark stripped Gottorp of its SCHLESWIG share in 1713 — the king
as liege lord revoked the ducal fief «wegen Felonie» — while Gottorp's HOLSTEIN
share remained with Karl Friedrich until the Treaty of Frederiksborg in 1720.
Christian August was regent of a duchy that had just lost Schleswig; a Gottorp
mint operating inside a Danish royal fortress in those years is not tenable.

**Outcome**: no year-override for Rendsburg. The flat `royal_holstein` entry in
`mint_registry` is correct — Krause files these in the Schleswig-Holstein volume
because they are Holstein coinage OF THE DANISH KING. The four misfiled
NumisMaster records were merged into their Hede classes via `_cross_entity.yml`
(2026-07-29).

Sources: de.wikipedia.org/wiki/Festung_Rendsburg ·
de.wikipedia.org/wiki/Schleswig-Holstein-Gottorf ·
de.wikipedia.org/wiki/Herzogtum_Holstein · danskmoent.dk/f4.htm ·
danskmoent.dk/nedsat.htm

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
| Christiania / Oslo / Bergen / Gimsø / Nidaros / Hamar | Danish-Norway up to 1814 | No post-1814 coins: Kongsberg was the only Norwegian mint after 1814. Post-1814 coins of any Norwegian mint would still go to `norway` via `norway_split_entity` (see Kongsberg section). |
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
