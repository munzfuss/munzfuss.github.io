#!/usr/bin/env python3
"""Strip project-internal scaffolding out of `verification_note` prose.

WHY (TODO §W step 2)
--------------------
A 2026-05-11 backfill (commit 91d20f1) wrote ~100 verification_notes that
explained an inferred fineness by citing the project's own rulebook:

    «Per Projekt-Konvention (CLAUDE.md §4) auf den kanonischen
     Müntzfuß-Wert (9_thaler, Anker 0.8889) gesetzt; …»

That is the §0z failure in its purest form — a note about a coin naming
an AI-internal document. The migration script was a one-shot in /tmp and
is gone, and no live generator reproduces the wording, so the strings are
frozen in `data/v2/final/**` and can only be fixed there. Absorb gap-fills
`verification_note` (`_enrich_final_entry`) rather than overwriting it, so
a rewrite here survives a re-flow; empirically these notes have survived
every re-flow since May.

The rewrite keeps the ONE fact the §4 pointer was carrying — that the
value is inferred from the standard rather than attested by a source —
and drops where that convention is written down. `fineness_verified:
false` continues to carry the same distinction machine-readably.

Four families, plus fixes that ride along in the same strings:

  1   canonical fineness            (61 notes)
  1b  strict-single-fineness tier   (32 notes)
  2   Krone-Fuß tier + envelope      (6 notes)
  3   a session diary entry          (1 note)

Riding along, because they sit inside the very sentences being rewritten:
  * `9_thaler` and friends — machine fuss ids leaking into reader prose;
    replaced by the display name from `data/shared/fuesse.yml::<id>.name`,
    which §2 tier 2 keeps identical across languages.
  * `fuesse.yml: fineness_display`, `fineness_verified: false`,
    `Im Coin-Datensatz`, `TODO-A-Audit`, `_issues.json` — further §0z
    leaks the old linter could not see.
  * `Mønlov` → `Møntloven` (Danish is mønt + lov; see TODO §W step 7).
  * Decimal separators: comma in de/uk, period in en (§3). The backfill
    wrote periods everywhere.
  * «специмен-толерантність» / «Soll» — calques, replaced by Ukrainian.

WRITING STRATEGY
----------------
Line-based, in the spirit of `lib/yaml_io.edit_coin_field` — no
serialisation round-trip, so the rest of the file is byte-for-byte
untouched (`lib/yaml_io` documents why a round-trip through the wrong
settings reflows an entire 24k-line file). `edit_coin_field` itself
cannot be used: it handles scalars and lists, and `verification_note` is
a nested {de,en,uk} mapping whose values fold across lines.

Usage
-----
    .venv/bin/python scripts/maintenance/rewrite_verification_notes.py
    .venv/bin/python scripts/maintenance/rewrite_verification_notes.py --apply
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
V2 = ROOT / "data" / "v2"
ROOTS = (V2 / "seed", V2 / "seed_unified", V2 / "final")
FUESSE = ROOT / "data" / "shared" / "fuesse.yml"

FOLD_WIDTH = 200  # lib/yaml_io ruamel_seed profile


def fuss_names() -> dict[str, str]:
    """id -> display name. §2 tier 2: one string across all languages."""
    doc = yaml.safe_load(FUESSE.read_text()) or {}
    out = {}
    for fid, body in doc.items():
        if not isinstance(body, dict):
            continue
        nm = body.get("name")
        if isinstance(nm, str):
            out[fid] = nm
        elif isinstance(nm, dict) and nm.get("de"):
            out[fid] = nm["de"]
    return out


def num(value: str, lang: str) -> str:
    """Decimal separator per §3: comma in de/uk, period in en."""
    return value.replace(".", ",") if lang in ("de", "uk") else value


def delta(raw: str, lang: str) -> str:
    """«-1.31%» -> «−1,31 %» (true minus, non-breaking space)."""
    v = raw.lstrip("-−+")
    sign = "−" if raw.lstrip().startswith(("-", "−")) else "+"
    return f"{sign}{num(v, lang)} %"


KIND = {
    "Scheide": {"de": "Scheidemünze", "en": "Scheidemünze", "uk": "розмінна монета"},
    "Kurant": {"de": "Kurantmünze", "en": "Kurantmünze", "uk": "курантна монета"},
    "gedenk": {"de": "Gedenkmünze", "en": "commemorative issue", "uk": "пам'ятна монета"},
}


def build_replacements(names: dict[str, str]) -> list[tuple[re.Pattern, callable]]:
    W = r"[\s\n]+"  # a fold point is whitespace, possibly a newline + indent

    def rx(template: str) -> re.Pattern:
        return re.compile(W.join(map(re.escape, template.split())).replace(r"\ ", " "))

    def pat(template: str) -> re.Pattern:
        """Template with {} placeholders -> regex tolerant of YAML folds.

        An apostrophe is written doubled inside a single-quoted YAML scalar
        («Stack''s Bowers»), so it has to match either form.
        """
        parts = template.split("{}")
        body = "(.+?)".join(
            W.join(re.escape(w) for w in p.split()).replace("'", "(?:''|')")
            for p in parts)
        return re.compile(body, re.DOTALL)

    def name_of(fid: str) -> str:
        return names.get(fid, fid)

    out: list[tuple[re.Pattern, callable]] = []

    # ---- family 1b FIRST: its text contains family 1's opening ----------
    for lang, tmpl, make in (
        ("de",
         "Probe nicht direkt belegt. Per Projekt-Konvention (CLAUDE.md §4) für "
         "strikt-monoprobe Müntzfüße der Kategorie 1 ({}, Anker {}) auf den kanonischen "
         "Müntzfuß-Wert gesetzt; Δ {}% gegen den Soll-Wert liegt im ±2-%-Streifen der "
         "zulässigen Spezimen-Toleranz, also widerspricht der angenommene Wert keinem "
         "belegten Datum.",
         lambda m: (f"Probe nicht direkt belegt; aus dem kanonischen Müntzfuß-Standard "
                    f"({name_of(m.group(1))}, Anker {num(m.group(2), 'de')}) übernommen — "
                    f"dieser Fuß kennt nur eine einzige Probe. Δ {delta(m.group(3), 'de')} "
                    f"gegen den Soll-Wert liegt in der Spezimen-Toleranz.")),
        ("en",
         "Fineness not directly attested. Per project convention (CLAUDE.md §4) set to the "
         "canonical Müntzfuß value for strict-single-fineness Category-1 standards ({}, "
         "anchor {}); Δ {}% against the soll value sits within the ±2 % specimen-tolerance "
         "envelope, so the assumed value contradicts no sourced datum.",
         lambda m: (f"Fineness not directly attested; taken from the canonical Müntzfuß "
                    f"standard ({name_of(m.group(1))}, anchor {m.group(2)}) — this standard "
                    f"has a single fineness throughout. Δ {delta(m.group(3), 'en')} against "
                    f"the soll value is within specimen tolerance.")),
        ("uk",
         "Проба не засвідчена джерелом. За проєктною конвенцією (CLAUDE.md §4) для "
         "строго-однопробних стоп Категорії 1 ({}, якірна проба {}) встановлена на канонічне "
         "значення стандарту; Δ {}% проти Soll лежить у смузі ±2 % допустимої "
         "специмен-толерантності, тож припущене значення не суперечить жодному "
         "задокументованому показнику.",
         lambda m: (f"Проба не засвідчена джерелом безпосередньо; узята з канонічного "
                    f"стандарту ({name_of(m.group(1))}, якір {num(m.group(2), 'uk')}) — ця "
                    f"стопа має єдину пробу. Δ {delta(m.group(3), 'uk')} проти нормативу — "
                    f"у межах допуску зразка.")),
    ):
        out.append((pat(tmpl), make))

    # ---- family 1 -------------------------------------------------------
    for lang, tmpl, make in (
        ("de",
         "Probe nicht direkt belegt. Per Projekt-Konvention (CLAUDE.md §4) auf den "
         "kanonischen Müntzfuß-Wert ({}, Anker {}) gesetzt; Δ {}% gegen den Soll-Wert liegt "
         "im ±2-%-Streifen der zulässigen Spezimen-Toleranz.",
         lambda m: (f"Probe nicht direkt belegt; aus dem kanonischen Müntzfuß-Standard "
                    f"({name_of(m.group(1))}, Anker {num(m.group(2), 'de')}) übernommen. "
                    f"Δ {delta(m.group(3), 'de')} gegen den Soll-Wert liegt in der "
                    f"Spezimen-Toleranz.")),
        ("en",
         "Fineness not directly attested. Per project convention (CLAUDE.md §4) set to the "
         "canonical Müntzfuß value ({}, anchor {}); Δ {}% against the soll value sits within "
         "the ±2 % specimen-tolerance envelope.",
         lambda m: (f"Fineness not directly attested; taken from the canonical Müntzfuß "
                    f"standard ({name_of(m.group(1))}, anchor {m.group(2)}). "
                    f"Δ {delta(m.group(3), 'en')} against the soll value is within "
                    f"specimen tolerance.")),
        ("uk",
         "Проба не засвідчена джерелом. За проєктною конвенцією (CLAUDE.md §4) встановлена на "
         "канонічне значення стандарту ({}, якірна проба {}); Δ {}% проти Soll лежить у смузі "
         "±2 % допустимої специмен-толерантності.",
         lambda m: (f"Проба не засвідчена джерелом безпосередньо; узята з канонічного "
                    f"стандарту ({name_of(m.group(1))}, якір {num(m.group(2), 'uk')}). "
                    f"Δ {delta(m.group(3), 'uk')} проти нормативу — у межах допуску зразка.")),
    ):
        out.append((pat(tmpl), make))

    # ---- family 2 -------------------------------------------------------
    def tier(raw: str, lang: str) -> str:
        m = re.match(r"(.+?)\s+(Scheide|Kurant|gedenk),\s*(\.\d+)", raw.strip())
        if not m:
            return raw.strip()
        return f"{m.group(1)} {KIND[m.group(2)][lang]}, {m.group(3)}"

    out += [
        (pat("Proba kanonisch aus Krone-fod-Tier ({}) abgeleitet — Mønlov 23. Mai 1873 "
             "(fuesse.yml: fineness_display). Im Coin-Datensatz nicht aus einer Quelle "
             "(Hede / Sieg / Schou) direkt belegt; Δ-Berechnung fällt innerhalb ±0,3 % des "
             "Soll-Feingewichts, daher mit ±2 %-Envelope nach CLAUDE.md §4 konsistent. "
             "Flagge bleibt fineness_verified: false bis zur Quellen-Attestation."),
         lambda m: (f"Probe aus dem Krone-Fuß abgeleitet ({tier(m.group(1), 'de')}), "
                    f"festgelegt durch die Møntloven af 23. maj 1873. Für dieses Stück nicht "
                    f"aus einer Quelle (Hede / Sieg / Schou) direkt belegt; die Δ-Rechnung "
                    f"bleibt innerhalb 0,3 % des Soll-Feingewichts.")),
        (pat("Fineness canonically inferred from the Krone-fod tier ({}) — Mønlov of 23 May "
             "1873 (fuesse.yml: fineness_display). Not directly attested for this coin record "
             "by a source (Hede / Sieg / Schou); arithmetic check falls within ±0.3 % of the "
             "Soll-Feingewicht, consistent with the ±2 % envelope per CLAUDE.md §4. Flag "
             "stays fineness_verified: false until a source attestation is added."),
         lambda m: (f"Fineness inferred from the Krone-Fuß tier ({tier(m.group(1), 'en')}), "
                    f"set by the Møntloven af 23. maj 1873. Not directly attested for this "
                    f"piece by a source (Hede / Sieg / Schou); the Δ calculation stays within "
                    f"0.3 % of the soll fine weight.")),
        (pat("Проба канонічно виведена з тиру Krone-fod ({}) — Mønlov 23 травня 1873 р. "
             "(fuesse.yml: fineness_display). У записі монети безпосередньо джерелом "
             "(Hede / Sieg / Schou) не атестована; арифметична перевірка дає Δ у межах ±0,3 % "
             "від Soll-Feingewicht, що узгоджується з ±2 %-конвертом за CLAUDE.md §4. "
             "Прапорець fineness_verified: false до додавання атестації з джерела."),
         lambda m: (f"Проба виведена з тиру Krone-Fuß ({tier(m.group(1), 'uk')}), "
                    f"встановленого Møntloven af 23. maj 1873. Для цього примірника джерелом "
                    f"(Hede / Sieg / Schou) не засвідчена; розрахунок Δ лишається в межах "
                    f"0,3 % від нормативної чистої ваги.")),
    ]

    # ---- family 3: a session diary; only two facts are the reader's -----
    out += [
        (pat("TODO-A-Audit (2026-05-03) gegen Numista _issues.json: alle 8 Jahre von 1695 bis "
             "1702 explizit aufgeführt, keine Gap-Marker — Zeitraum als continuous bestätigt. "
             "Eine zuvor eingetragene Raugewichts-Spanne 2,54–2,60 g und eine "
             "analogie-geschätzte Feingehalts-Spanne .500–.625 wurden 2026-05-10 entfernt, da "
             "keine zugängliche Quelle die Werte direkt belegte (per CLAUDE.md §0)."),
         lambda m: ("Jahresspanne 1695–1702 durchgehend belegt (Numista führt alle acht Jahre "
                    "einzeln auf). Raugewicht und Feingehalt sind in den vorliegenden Quellen "
                    "nicht angegeben.")),
        (pat("TODO A audit (2026-05-03) against Numista _issues.json: all 8 years from 1695 to "
             "1702 explicitly enumerated, no gap markers — range confirmed as continuous. A "
             "previously-stated rough-weight range of 2.54–2.60 g and an analogy-estimated "
             "fineness range of .500–.625 were removed on 2026-05-10 because no accessible "
             "source directly attested the values (per CLAUDE.md §0)."),
         lambda m: ("Year range 1695–1702 attested continuously (Numista lists all eight years "
                    "individually). Rough weight and fineness are not given in the available "
                    "sources.")),
        (pat("Аудит TODO A (2026-05-03) проти Numista _issues.json: усі 8 років від 1695 до "
             "1702 явно перелічено, без gap-маркерів — діапазон підтверджено як continuous. "
             "Раніше вказаний діапазон повної ваги 2,54–2,60 г та оцінений за аналогією "
             "діапазон проби .500–.625 видалено 2026-05-10, бо жодне доступне джерело прямо не "
             "підтверджувало ці значення (за CLAUDE.md §0)."),
         lambda m: ("Діапазон 1695–1702 засвідчено суцільно (Numista наводить усі вісім років "
                    "окремо). Повна вага і проба у наявних джерелах не вказані.")),
    ]

    # ---- family 3a: the same diary shape, parameterised over years -----
    out += [
        (pat("TODO-A-Audit (2026-05-03) gegen Numista _issues.json: alle {} Jahre von {} bis {} "
             "explizit aufgeführt, keine Gap-Marker — Zeitraum als continuous bestätigt."),
         lambda m: (f"Jahresspanne {m.group(2)}–{m.group(3)} durchgehend belegt (Numista führt "
                    f"alle {m.group(1)} Jahre einzeln auf).")),
        (pat("TODO A audit (2026-05-03) against Numista _issues.json: all {} years from {} to {} "
             "explicitly enumerated, no gap markers — range confirmed as continuous."),
         lambda m: (f"Year range {m.group(2)}–{m.group(3)} attested continuously (Numista lists "
                    f"all {m.group(1)} years individually).")),
        (pat("Аудит TODO A (2026-05-03) проти Numista _issues.json: усі {} років від {} до {} "
             "явно перелічено, без gap-маркерів — діапазон підтверджено як continuous."),
         lambda m: (f"Діапазон {m.group(2)}–{m.group(3)} засвідчено суцільно (Numista наводить "
                    f"усі {m.group(1)} років окремо).")),
    ]

    # ---- family 3b: the no-per-year-breakdown variant -------------------
    out += [
        (pat("TODO-A-Audit (2026-05-03): Numista führt diesen Typ als einen Range {} ohne "
             "per-year-Aufteilung (is_dated: false); per-year-Breakdown nicht verfügbar — "
             "Zeitraum als continuous belassen, undokumentierte Lücken möglich."),
         lambda m: (f"Numista führt den Typ als geschlossene Spanne {m.group(1)} ohne "
                    f"Einzeljahre; ob innerhalb der Spanne Jahre ohne Karbung liegen, ist aus "
                    f"den vorliegenden Quellen nicht zu entnehmen.")),
        (pat("TODO A audit (2026-05-03): Numista records this type as a single range {} without "
             "per-year split (is_dated: false); per-year breakdown unavailable — range left as "
             "continuous, undocumented gaps possible."),
         lambda m: (f"Numista records the type as a closed range {m.group(1)} without "
                    f"individual years; whether any year within the range saw no striking is "
                    f"not determinable from the available sources.")),
        (pat("Аудит TODO A (2026-05-03): Numista фіксує тип як один range {} без розщеплення "
             "per year (is_dated: false); per-year breakdown недоступний — діапазон збережено "
             "як continuous, можливі недокументовані пропуски."),
         lambda m: (f"Numista подає тип як суцільний проміжок {m.group(1)} без окремих років; "
                    f"чи були в межах проміжку роки без карбування, з наявних джерел не "
                    f"встановити.")),
    ]

    # ---- family 4: notes citing «§4» directly ---------------------------
    out += [
        (pat("Sovereign fineness not attested in the Danish sources (Hede «Finhed ?»); set to "
             "the canonical sovereignfod anchor .9166 (22 kt English Unite that Christian IV "
             "deliberately copied, 1606) per §4 — fineness_verified false."),
         lambda m: ("Probe in den dänischen Quellen nicht angegeben (Hede «Finhed ?»); aus dem "
                    "kanonischen Sovereign-Fuß-Anker .9166 übernommen — 22 Karat nach dem "
                    "englischen Unite, dem Christian IV. 1606 folgte.")),
        (pat("Feingehalt .770 = kanonische Rhinskgyldenfod-Phase-I-Probe (≈ 18½ Karat, "
             "Frederik II.). danskmoent.dk/Hede geben nur das Gewicht (3,27 g); die Probe folgt "
             "aus dem Standard (§4), daher fineness_verified=false."),
         lambda m: ("Probe .770 = kanonische Rhinskgyldenfod-Phase-I-Probe (≈ 18½ Karat, "
                    "Frederik II.). danskmoent.dk und Hede geben nur das Gewicht (3,27 g); die "
                    "Probe folgt aus dem Standard, nicht aus einer Quelle.")),
        (pat("Fineness .770 = the canonical Rhinskgyldenfod Phase-I fineness (≈ 18½ carats, "
             "Frederik II). danskmoent.dk/Hede give the weight only (3.27 g); the fineness "
             "follows from the standard (§4), so fineness_verified=false."),
         lambda m: ("Fineness .770 = the canonical Rhinskgyldenfod Phase-I fineness (≈ 18½ "
                    "carats, Frederik II). danskmoent.dk and Hede give the weight only "
                    "(3.27 g); the fineness follows from the standard, not from a source.")),
        (pat("Проба .770 = канонічна проба Rhinskgyldenfod Фаза I (≈ 18½ карат, Frederik II). "
             "danskmoent.dk/Hede дають лише вагу (3,27 г); проба випливає зі стандарту (§4), "
             "тому fineness_verified=false."),
         lambda m: ("Проба .770 = канонічна проба Rhinskgyldenfod Фаза I (≈ 18½ карат, "
                    "Frederik II). danskmoent.dk і Hede подають лише вагу (3,27 г); проба "
                    "випливає зі стандарту, а не з джерела.")),
    ]

    # ---- family 5: a pointer at our own documentation -------------------
    out += [
        (pat("Projekt-Dokumentation `fuesse.yml` `guldkrone.events.first_adoption.note` zitiert "
             "bereits Ingvardson & Märcher 2010 zur Christian-IV-Predecessor-Continuity."),
         lambda m: ("Zur Kontinuität mit dem Christian-IV-Vorläufer siehe Ingvardson & Märcher "
                    "2010.")),
        (pat("The project's own `fuesse.yml` `guldkrone.events.first_adoption.note` already "
             "cites Ingvardson & Märcher 2010 on Christian IV predecessor continuity."),
         lambda m: ("On continuity with the Christian IV predecessor see Ingvardson & Märcher "
                    "2010.")),
        (pat("У `fuesse.yml` `guldkrone.events.first_adoption.note` уже цитується Ingvardson & "
             "Märcher 2010 щодо continuity Christian-IV-предтечі."),
         lambda m: ("Щодо спадкоємності з попередником доби Кристіана IV див. Ingvardson & "
                    "Märcher 2010.")),
    ]

    # ---- family 6: the seed-builder boilerplates (TODO §W step 1) -------
    # Wall-to-wall §0z: pipeline stage names, workflow steps, a schema value
    # and an internal doc path, in a note about a coin. The builders emit the
    # corrected wording now; these patterns heal the three existing layers so
    # no re-flow is needed (and no unrelated cache drift gets imported).
    for old, new in [
        ("Bruun-Seed: spezifikische Münzfuß- und Phase-Zuordnung sowie Per-Münze-Verifikation "
         "stehen noch aus; Daten direkt aus dem Bruun-Auktionskatalog (Stack's Bowers "
         "L. E. Bruun Collection 2024-2026) übernommen. Brutto-Gewicht ist ein "
         "per-Specimen-Wert; Feingehalt fehlt in Bruun-Daten und folgt aus dem Wilcke "
         "1950-Ordonnance-Spezifikations-Tabel (s. docs/research/moentordning_1541.md).",
         "Daten aus dem Bruun-Auktionskatalog (Stack's Bowers, L. E. Bruun Collection "
         "2024-2026) übernommen. Das Brutto-Gewicht ist ein Einzelstück-Wert; einen "
         "Feingehalt gibt Bruun nicht an, er folgt aus der Ordonnanz-Spezifikationstabelle "
         "bei Wilcke 1950. Der Müntzfuß dieses Stücks ist noch nicht bestimmt."),
        ("Bruun seed: Müntzfuß and phase assignment plus per-coin verification are still "
         "outstanding; data taken directly from the Bruun auction catalogue (Stack's Bowers "
         "L. E. Bruun Collection 2024-2026). Brutto weight is a per-specimen value; fineness "
         "is not in Bruun data and follows from the Wilcke 1950 ordinance specification table "
         "(see docs/research/moentordning_1541.md).",
         "Data taken from the Bruun auction catalogue (Stack's Bowers, L. E. Bruun Collection "
         "2024-2026). The gross weight is a single-specimen value; Bruun gives no fineness, so "
         "it follows from the ordinance specification table in Wilcke 1950. The Müntzfuß of "
         "this piece is not yet determined."),
        ("Bruun-seed: призначення Müntzfuß і фази та покоінна верифікація ще очікуються; дані "
         "взято безпосередньо з аукціонного каталогу Bruun (Stack's Bowers L. E. Bruun "
         "Collection 2024-2026). Brutto-вага це per-specimen значення; проба відсутня в "
         "Bruun-даних і випливає з таблиці специфікацій ордонансів Wilcke 1950 "
         "(див. docs/research/moentordning_1541.md).",
         "Дані взято з аукціонного каталогу Bruun (Stack's Bowers, L. E. Bruun Collection "
         "2024-2026). Повна вага — значення одного примірника; проби Bruun не подає, вона "
         "випливає з таблиці специфікацій ордонансів у Wilcke 1950. Müntzfuß цього "
         "примірника ще не визначено."),
        ("Galster-Seed: spezifikische Münzfuß- und Phase-Zuordnung sowie Per-Münze-Verifikation "
         "stehen noch aus; Daten direkt aus den danskmoent.dk-Galster-Seiten (Hosting der "
         "Galster-Numismatik) übernommen. Cross-references aus dem H1 + Beschreibungsblock "
         "automatisch extrahiert (Schou, Sieg, Jensen-Skjoldager, Schive, etc.).",
         "Daten aus den Galster-Seiten auf danskmoent.dk übernommen; die Katalog-Querverweise "
         "(Schou, Sieg, Jensen-Skjoldager, Schive u. a.) stammen aus der Überschrift und dem "
         "Beschreibungsblock der Seite. Der Müntzfuß dieses Stücks ist noch nicht bestimmt."),
        ("Galster seed: Müntzfuß and phase assignment plus per-coin verification are still "
         "outstanding; data taken directly from the danskmoent.dk Galster-page series (hosting "
         "Galster numismatic catalog). Cross-references from H1 + description block extracted "
         "automatically (Schou, Sieg, Jensen-Skjoldager, Schive, etc.).",
         "Data taken from the Galster pages on danskmoent.dk; the catalogue cross-references "
         "(Schou, Sieg, Jensen-Skjoldager, Schive and others) come from the page heading and "
         "description block. The Müntzfuß of this piece is not yet determined."),
        ("Galster-seed: призначення Müntzfuß і фази та покоінна верифікація ще очікуються; дані "
         "взято безпосередньо зі сторінок Galster на danskmoent.dk (хостинг каталога Galster). "
         "Cross-references з H1 + блоку опису витягнуто автоматично (Schou, Sieg, "
         "Jensen-Skjoldager, Schive, тощо).",
         "Дані взято зі сторінок Galster на danskmoent.dk; каталожні перехресні посилання "
         "(Schou, Sieg, Jensen-Skjoldager, Schive та інші) походять із заголовка та блоку опису "
         "сторінки. Müntzfuß цього примірника ще не визначено."),
        ("KMK-Seed: Datensatz aus der Kgl. Münz- und Medaillensammlung (Nationalmuseet "
         "Kopenhagen, api.natmus.dk). Felder museumsbelegt; Müntzfuß/Phase noch unklassifiziert "
         "(seed_unsorted) bis zur Phase-4-Zuordnung.",
         "Datensatz aus der Kgl. Münz- und Medaillensammlung (Nationalmuseet Kopenhagen, "
         "api.natmus.dk); die Felder sind museumsbelegt. Der Müntzfuß dieses Stücks ist noch "
         "nicht bestimmt."),
        ("KMK seed: record from the Royal Coin Cabinet (Nationalmuseet Copenhagen, "
         "api.natmus.dk). Fields museum-attested; Münzfuß/phase unclassified (seed_unsorted) "
         "pending Phase-4 assignment.",
         "Record from the Royal Coin Cabinet (Nationalmuseet Copenhagen, api.natmus.dk); the "
         "fields are museum-attested. The Müntzfuß of this piece is not yet determined."),
        ("KMK-сід: запис із Королівського мюнцкабінету (Nationalmuseet Копенгаген, "
         "api.natmus.dk). Поля музейно-засвідчені; Müntzfuß/фаза некласифіковані "
         "(seed_unsorted) до Phase-4.",
         "Запис із Королівського мюнцкабінету (Nationalmuseet, Копенгаген, api.natmus.dk); "
         "поля засвідчені музеєм. Müntzfuß цього примірника ще не визначено."),
        ("IKMK-Seed: Datensatz aus dem Interaktiven Katalog des Münzkabinetts Berlin "
         "(ikmk.smb.museum, CC BY-SA 4.0). Felder museumsbelegt; Müntzfuß/Phase noch "
         "unklassifiziert (seed_unsorted) bis zur Phase-4-Zuordnung.",
         "Datensatz aus dem Interaktiven Katalog des Münzkabinetts Berlin (ikmk.smb.museum, "
         "CC BY-SA 4.0); die Felder sind museumsbelegt. Der Müntzfuß dieses Stücks ist noch "
         "nicht bestimmt."),
        ("IKMK seed: record from the Berlin Münzkabinett online catalogue (ikmk.smb.museum, "
         "CC BY-SA 4.0). Fields museum-attested; Münzfuß/phase unclassified (seed_unsorted) "
         "pending Phase-4 assignment.",
         "Record from the Interactive Catalogue of the Münzkabinett Berlin (ikmk.smb.museum, "
         "CC BY-SA 4.0); the fields are museum-attested. The Müntzfuß of this piece is not yet "
         "determined."),
        ("IKMK-сід: запис з онлайн-каталогу Münzkabinett Berlin (ikmk.smb.museum, CC BY-SA "
         "4.0). Поля музейно-засвідчені; Müntzfuß/фаза некласифіковані (seed_unsorted) до "
         "Phase-4.",
         "Запис з інтерактивного каталогу Münzkabinett Berlin (ikmk.smb.museum, CC BY-SA 4.0); "
         "поля засвідчені музеєм. Müntzfuß цього примірника ще не визначено."),
    ]:
        out.append((pat(old), (lambda n: (lambda m: n))(new)))

    # ---- family 7: boilerplates citing docs/TODO section ids -----------
    # Same treatment as family 6. Kept in every one: provenance, the
    # source-reliability caveat (ucoin is user-edited, NumisMaster is
    # commercial — §5 tier information the reader needs), the named
    # primary sources the entry has NOT been checked against, and for the
    # Hede stubs which overview page attests it and what would fill the
    # gap. Dropped: the «§BF»/«§BK»/«§AZ» backlog ids and the «-Seed:»
    # stage labels.
    for old, new in [
        ("ucoin-Seed: user-edited Münzkatalog (ucoin.net). Per-Münze-Verifikation gegen "
         "Primärquellen (Hede / Sieg / Lange / NumisMaster / Bruun) vor §BF-Promotion.",
         "Daten aus dem benutzergepflegten Münzkatalog ucoin.net. Gegen die Primärquellen "
         "(Hede / Sieg / Lange / NumisMaster / Bruun) noch nicht geprüft."),
        ("ucoin seed: user-edited coin catalogue (ucoin.net). Per-coin verification against "
         "primary sources (Hede / Sieg / Lange / NumisMaster / Bruun) before §BF promotion.",
         "Data from the user-edited coin catalogue ucoin.net. Not yet checked against the "
         "primary sources (Hede / Sieg / Lange / NumisMaster / Bruun)."),
        ("ucoin-seed: користувацький каталог монет (ucoin.net). Покоінна верифікація проти "
         "первинних джерел (Hede / Sieg / Lange / NumisMaster / Bruun) перед §BF-промоцією.",
         "Дані з користувацького каталогу монет ucoin.net. Проти первинних джерел "
         "(Hede / Sieg / Lange / NumisMaster / Bruun) ще не звірено."),
        ("NumisMaster-Seed (§BK Phase 5): Krause-Mishler-basiertes kommerzielles Katalog "
         "(Librios). Per-Münze-Verifikation gegen Primärquellen (Hede / Sieg / Lange / "
         "Wilcke / Schive) vor §BF-Promotion.",
         "Daten aus dem NumisMaster-Katalog (Librios), einem kommerziellen "
         "Krause-Mishler-Werk. Gegen die Primärquellen (Hede / Sieg / Lange / Wilcke / "
         "Schive) noch nicht geprüft."),
        ("NumisMaster seed (§BK Phase 5): Krause-Mishler-based commercial catalogue "
         "(Librios). Per-coin verification against primary sources (Hede / Sieg / Lange / "
         "Wilcke / Schive) before §BF promotion.",
         "Data from the NumisMaster catalogue (Librios), a commercial Krause-Mishler work. "
         "Not yet checked against the primary sources (Hede / Sieg / Lange / Wilcke / "
         "Schive)."),
        ("NumisMaster-seed (§BK Phase 5): Krause-Mishler-базований комерційний каталог "
         "(Librios). Покоінна верифікація проти первинних джерел (Hede / Sieg / Lange / "
         "Wilcke / Schive) перед §BF-промоцією.",
         "Дані з каталогу NumisMaster (Librios) — комерційного видання на основі "
         "Krause-Mishler. Проти первинних джерел (Hede / Sieg / Lange / Wilcke / Schive) "
         "ще не звірено."),
    ]:
        out.append((pat(old), (lambda n: (lambda m: n))(new)))

    # Hede index stubs: one template per language, the source page name is
    # the variable. 72 pages × 3 = 216 of the 222 distinct strings.
    out += [
        (pat("Hede-Index-Stub: Nur die Übersichtsreihe von {} belegt diesen Eintrag "
             "(Hede-Tiefenseite fehlt auf danskmoent.dk). Gewicht und Probe nicht erfasst; "
             "vollständige Per-Münze-Verifikation hängt am §AZ Paper-Source-Import "
             "(Hede 1971 + Galster 1965)."),
         lambda m: (f"Nur die Übersichtsreihe von {m.group(1)} belegt diesen Eintrag; die "
                    f"Hede-Tiefenseite fehlt auf danskmoent.dk. Gewicht und Probe sind dort "
                    f"nicht angegeben; sie wären den gedruckten Ausgaben Hede 1971 und "
                    f"Galster 1965 zu entnehmen.")),
        (pat("Hede index stub: only the overview-table row of {} attests this entry "
             "(Hede deep page absent from danskmoent.dk). Weight and fineness not captured; "
             "full per-coin verification depends on the §AZ paper-source import "
             "(Hede 1971 + Galster 1965)."),
         lambda m: (f"Only the overview-table row of {m.group(1)} attests this entry; the "
                    f"Hede deep page is absent from danskmoent.dk. Weight and fineness are "
                    f"not given there; they would have to be taken from the printed "
                    f"Hede 1971 and Galster 1965.")),
        (pat("Hede index-stub: тільки рядок огляду {} підтверджує цей запис (deep-сторінка "
             "Hede відсутня на danskmoent.dk). Вага та проба не зафіксовані; повна покоінна "
             "верифікація залежить від §AZ paper-source імпорту (Hede 1971 + Galster 1965)."),
         lambda m: (f"Цей запис підтверджує лише рядок оглядової таблиці {m.group(1)}; "
                    f"поглибленої сторінки Hede на danskmoent.dk немає. Вага і проба там не "
                    f"наведені; їх довелося б брати з друкованих Hede 1971 та "
                    f"Galster 1965.")),
    ]

    # ---- family 5: the German term in ENGLISH and UKRAINIAN notes --------
    # The Denmark page publishes as its own Danish-branded site, so its
    # English and Ukrainian prose no longer calls the concept «Müntzfuß».
    # These notes come from seed-builder templates (already updated); the
    # strings below are the copies frozen in data/v2/**, which absorb
    # gap-fills rather than overwrites — so a rewrite here survives a
    # re-flow, and without it the existing ~9 000 rows would keep the old
    # wording for ever. GERMAN notes are untouched: each pattern matches
    # its own language's sentence, never the de twin.
    for tmpl, repl in (
        # kmk / bruun / galster / ikmk all end on this one sentence
        ("The Müntzfuß of this piece is not yet determined.",
         "The coinage standard of this piece is not yet determined."),
        ("Müntzfuß цього примірника ще не визначено.",
         "Стопу цього примірника ще не визначено."),
        ("Hede seed: Müntzfuß assignment, phase and per-coin verification",
         "Hede seed: coinage-standard assignment, phase and per-coin verification"),
        ("Hede-seed: призначення Müntzfuß, фази та покоінна верифікація",
         "Hede-seed: призначення стопи, фази та покоінна верифікація"),
        ("Numista seed: Müntzfuß and phase assignment plus per-coin",
         "Numista seed: coinage-standard and phase assignment plus per-coin"),
        ("Numista-seed: призначення Müntzfuß і фази та покоінна",
         "Numista-seed: призначення стопи і фази та покоінна"),
        # frozen in the data only — no live generator emits this one
        ("Müntzfuß assignment and per-coin verification against Hede / Schön / Bruun "
         "are still outstanding.",
         "Coinage-standard assignment and per-coin verification against "
         "Hede / Schön / Bruun are still outstanding."),
        ("Призначення Müntzfuß і покоінна верифікація за Hede / Schön / Bruun "
         "ще очікуються.",
         "Призначення стопи і покоінна верифікація за Hede / Schön / Bruun "
         "ще очікуються."),
    ):
        out.append((rx(tmpl), lambda m, t=repl: t))

    # ---- family 5b: the same term inside notes THIS script itself wrote ---
    # «the canonical Müntzfuß standard» was also a tautology in English —
    # a Müntzfuß IS the standard. The Ukrainian twins of these were already
    # phrased with «стопа» by the earlier families, which is why only the
    # English side appears here.
    for tmpl, repl in (
        ("taken from the canonical Müntzfuß standard",
         "taken from the canonical coinage standard"),
        ("inferred from Müntzfuß convention:",
         "inferred from coinage-standard convention:"),
        ("harvested 2026-05-21 for Müntzfuß genealogy understanding). Specific "
         "Müntzfuß and phase assignment plus per-coin verification still outstanding.",
         "harvested 2026-05-21 to understand the genealogy of the standards). "
         "The specific coinage-standard and phase assignment, and per-coin "
         "verification, are still outstanding."),
        ("харвест 2026-05-21 для розуміння Müntzfuß-генеалогії). Специфічне "
         "Müntzfuß і phase призначення та покоінна верифікація очікуються.",
         "харвест 2026-05-21 для розуміння генеалогії стоп). Призначення "
         "конкретної стопи і фази та покоінна верифікація ще очікуються."),
    ):
        out.append((rx(tmpl), lambda m, t=repl: t))

    return out


def _needs_quoting(text: str) -> bool:
    """A YAML plain scalar cannot contain «: » or « #», or lead with an
    indicator character. Every replacement below is plain-safe; this is the
    guard that keeps it that way if someone edits the wording later."""
    return (": " in text or " #" in text
            or text[:1] in "-?:,[]{}#&*!|>'\"%@`" or text.endswith(":"))


class _Stripped:
    """Match proxy whose groups come back without surrounding whitespace.

    The fold-tolerant patterns join words with `\\s+`, which drops the space
    that preceded a `{}` placeholder — so the capture starts with it. Left
    unstripped that produced «Anker  0,8889» (doubled space) and «Δ − -1,31 %»
    (the sign logic saw " -1.31" and could not strip the minus behind the
    space). Stripping once here fixes every family at the source.
    """

    __slots__ = ("_m",)

    def __init__(self, m):
        self._m = m

    def group(self, i):
        g = self._m.group(i)
        return g.strip() if isinstance(g, str) else g


def refold(raw: str, start: int, end: int, text: str) -> str:
    """Re-emit `text` over [start, end) preserving the `key:` and indent.

    Handles both plain and single-quoted source scalars. Family 2 is stored
    single-quoted because the ORIGINAL text contained «fuesse.yml:
    fineness_display» — a «: » that forces quoting. The rewrite removes it, so
    the value becomes plain-safe and the quotes go with it; emitting plain is
    also what ruamel would produce on the next absorb.
    """
    head = raw.rfind("\n", 0, start) + 1
    line = raw[head:start]
    m = re.match(r"^(\s*)([a-z]{2}): (')?$", line)
    if not m:
        return raw[:start] + text + raw[end:]
    if m.group(3):  # value opens with a quote
        if raw[end:end + 1] == "'":
            end += 1  # whole value matched — drop the quotes with it
        else:
            # The match covers only the FIRST segment of a longer quoted
            # scalar (km-137419 carries a year-range note AND a fineness
            # note in one value). Splice in place and leave the quoting
            # alone; a lone apostrophe would break the scalar, so guard.
            assert "'" not in text, f"apostrophe inside quoted scalar: {text[:60]!r}"
            return raw[:start] + text + raw[end:]
    assert not _needs_quoting(text), f"replacement needs quoting: {text[:60]!r}"
    indent, key = m.group(1), m.group(2)
    cont = indent + "  "
    words, lines, cur = text.split(" "), [], f"{indent}{key}: "
    for w in words:
        if cur.strip() and len(cur) + len(w) + 1 > FOLD_WIDTH:
            lines.append(cur.rstrip() + " ")
            cur = cont
        cur += w + " "
    lines.append(cur.rstrip())
    return raw[:head] + "\n".join(lines) + raw[end:]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--apply", action="store_true", help="write changes (default: dry run)")
    args = ap.parse_args()

    reps = build_replacements(fuss_names())
    grand = 0
    targets = sorted(q for r in ROOTS for q in r.rglob("*.yml"))
    for path in targets:
        raw = path.read_text()
        before = raw
        n = 0
        for rx, make in reps:
            while True:
                m = rx.search(raw)
                if not m:
                    break
                raw = refold(raw, m.start(), m.end(), make(_Stripped(m)))
                n += 1
        if n:
            grand += n
            print(f"  {n:4}  {path.name}")
            if args.apply:
                yaml.safe_load(raw)  # parse guard before touching disk
                path.write_text(raw)
        else:
            assert raw == before
    print(f"{'applied' if args.apply else 'would rewrite'}: {grand} strings")
    if not args.apply:
        print("(dry run — pass --apply to write)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
