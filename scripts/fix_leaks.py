#!/usr/bin/env python3
"""
Second-pass fix for stray German words that survived the initial
pattern translator. Operates on already-translated EN and UK fields
in data/locations/schleswig.yml — does NOT re-translate, only patches
the specific residues found by the audit.
"""
from __future__ import annotations
import re
from pathlib import Path
from ruamel.yaml import YAML
from ruamel.yaml.scalarstring import LiteralScalarString


# phrase → (en, uk) substitution applied to existing en/uk translations
EN_FIXES = [
    # longest/specific phrases first
    (r"\bStapelholm-Festung\b", "the Stapelholm fortress"),
    (r"\bbust of the Herzogs rechts\b", "bust of the Duke facing right"),
    (r"\bbust of the Herzogs links\b", "bust of the Duke facing left"),
    (r"\bdes Herzogs\b", "of the Duke"),
    (r"\bdem Herzog\b", "the Duke"),
    (r"\bder Herzog\b", "the Duke"),
    (r"\bKönigs-Speciedaler\b", "royal Speciedaler"),
    (r"\bKönigs(?:e|en)?\b", "king's"),
    (r"\bKönig(?:s|e|en|in)?\b", "king"),
    (r"\bHerzog(?:s|e|en|in|tum)?\b", "Duke"),
    (r"\bFestung\b", "fortress"),
    (r"\bder gemeinen\b", "the common"),
    (r"\bgemeinen\b", "common"),
    (r"\bim letzten Regierungsjahr\b", "in the final year of reign"),
    (r"\bim Jahr\b", "in the year"),
    (r"\bvorher\b", "previously"),
    (r"\bbisher\b", "so far"),
    (r"\bweiterhin\b", "still"),
    (r"\bfortgeführt\b", "continued"),
    (r"\bFortsetzung\b", "continuation"),
    (r"\bhielt\b", "kept"),
    (r"\bbesteigt\b", "ascends"),
    (r"\bDornenberg\b", "a thorny mountain"),
    (r"\bWolken\b", "clouds"),
    (r"\bWert\b(?![-\w])", "value"),
    (r"\bSilberprägung\b", "silver coinage"),
    (r"\bfiskalisch instabil\b", "fiscally unstable"),
    (r"\binstabil\b", "unstable"),
    (r"\bÜbergangsjahr\b", "transitional year"),
    (r"\bUmbenennung\b", "renaming"),
    (r"\bUmschrift\b", "circumscription"),
    (r"\bElefantenorden\b", "the Order of the Elephant"),
    (r"\bPalmkranz\b", "palm wreath"),
    (r"\bLorbeerkranz\b", "laurel wreath"),
    (r"\bSchmaleres(?:/breiteres)?\b", "narrower (or broader)"),
    (r"\bbreiteres?\b", "broader"),
    (r"\bschmaleres?\b", "narrower"),
    (r"\banderer\b", "another"),
    (r"\banderen\b", "other"),
    (r"\bjunger\b", "the young"),
    (r"\btypischer\b", "typical"),
    (r"\bTönning-Variationsbreite\b", "Tönning range of variation"),
    (r"\bVariationsbreite\b", "range of variation"),
    (r"\bAllegorische\b", "allegorical"),
    (r"\bschwerer als\b", "heavier than"),
    (r"\bschwerer\b", "heavier"),
    (r"\bleichter als\b", "lighter than"),
    (r"\bleichter\b", "lighter"),
    (r"\bSchild\b", "shield"),
    (r"\bWappen\b", "coat of arms"),
    (r"\bDatum\b", "date"),
    (r"\bPolitische Orientierung\b", "a political orientation"),
    (r"\bpolitische Orientierung\b", "a political orientation"),
    (r"\bLübeck Rechnung\b", "Lübeck reckoning"),
    (r"\blübischer? Rechnung\b", "Lübeck reckoning"),
    (r"\bRechnung\b", "reckoning"),
    (r"\bevtl\.\s*", "possibly "),
    (r"\brechts\b", "facing right"),
    (r"\blinks\b(?=\s*·|$|\s+(?:und|and))", "facing left"),  # not "links" in "Accounting links"
    (r"\bunter\b", "under"),
    (r"\bgelten\b", "apply"),
    (r"\bÜbergang\b", "transition"),
    (r"\bReichstaler\b(?!-)", "Reichsthaler"),
    (r"\bAufgeld\b", "premium (Aufgeld)"),
    # Tidy extra spaces
    (r"\s+", " "),
    (r"\s+([,.;:!?])", r"\1"),
]

UK_FIXES = [
    (r"\bStapelholm-Festung\b", "Стапельгольмська фортеця"),
    (r"\bStapelholm fortress\b", "Стапельгольмська фортеця"),  # in case it already translated the en variant
    (r"\bбюст Herzogs rechts\b", "бюст герцога праворуч"),
    (r"\bбюст Herzogs links\b", "бюст герцога ліворуч"),
    (r"\bHerzogs\b", "герцога"),
    (r"\bHerzog(?:e|en|in|tum|s)?\b", "герцог"),
    (r"\bKönigs-Speciedaler\b", "королівський Speciedaler"),
    (r"\bKönigs(?:e|en)?\b", "королівський"),
    (r"\bKönig(?:s|e|en|in)?\b", "король"),
    (r"\bFestung\b", "фортеця"),
    (r"\bder gemeinen\b", "загальний"),
    (r"\bgemeinen\b", "загальний"),
    (r"\bim letzten Regierungsjahr\b", "в останній рік правління"),
    (r"\bim Jahr\b", "у році"),
    (r"\bvorher\b", "раніше"),
    (r"\bbisher\b", "до цього часу"),
    (r"\bweiterhin\b", "далі"),
    (r"\bfortgeführt\b", "продовжено"),
    (r"\bFortsetzung\b", "продовження"),
    (r"\bhielt\b", "тримало"),
    (r"\bbesteigt\b", "сходить на"),
    (r"\bDornenberg\b", "тернову гору"),
    (r"\bWolken\b", "хмарах"),
    (r"\bWert\b(?![-\w])", "вартість"),
    (r"\bSilberprägung\b", "срібного карбування"),
    (r"\bfiskalisch instabil\b", "фіскально нестабільний"),
    (r"\binstabil\b", "нестабільний"),
    (r"\bÜbergangsjahr\b", "перехідний рік"),
    (r"\bUmbenennung\b", "перейменування"),
    (r"\bUmschrift\b", "колова легенда"),
    (r"\bElefantenorden\b", "Орден Слона"),
    (r"\bPalmkranz\b", "пальмовий вінок"),
    (r"\bLorbeerkranz\b", "лавровий вінок"),
    (r"\bSchmaleres(?:/breiteres)?\b", "вужчий (або ширший)"),
    (r"\bbreiteres?\b", "ширший"),
    (r"\bschmaleres?\b", "вужчий"),
    (r"\banderer\b", "інший"),
    (r"\banderen\b", "інший"),
    (r"\bjunger\b", "молодий"),
    (r"\btypischer\b", "типовий"),
    (r"\bTönning-Variationsbreite\b", "діапазон варіацій Tönning"),
    (r"\bVariationsbreite\b", "діапазон варіацій"),
    (r"\bAllegorische\b", "алегоричний"),
    (r"\bschwerer als\b", "важчий за"),
    (r"\bschwerer\b", "важчий"),
    (r"\bleichter als\b", "легший за"),
    (r"\bleichter\b", "легший"),
    (r"\bSchild\b", "щит"),
    (r"\bWappen\b", "герб"),
    (r"\bDatum\b", "дата"),
    (r"\bpolitische Orientierung\b", "політична орієнтація"),
    (r"\bPolitische Orientierung\b", "політична орієнтація"),
    (r"\bLübeck Rechnung\b", "любецький рахунок"),
    (r"\blübische[rnms]? Rechnung\b", "любецький рахунок"),
    (r"\bRechnung\b", "рахунок"),
    (r"\bevtl\.\s*", "можливо, "),
    (r"\brechts\b", "праворуч"),
    (r"\blinks\b(?=\s*·|$|\s+(?:і|і також))", "ліворуч"),
    (r"\bunter\b", "за"),
    (r"\bgelten\b", "діють"),
    (r"\bÜbergang\b", "перехід"),
    (r"\bReichstaler\b(?!-)", "Reichsthaler"),
    (r"\bAufgeld\b", "надбавка (Aufgeld)"),
    # Tidy
    (r"\s+", " "),
    (r"\s+([,.;:!?])", r"\1"),
]


def apply_fixes(text: str, rules: list[tuple[str, str]]) -> str:
    if not text:
        return text
    for pat, rep in rules:
        text = re.sub(pat, rep, text, flags=re.IGNORECASE)
    return text.strip()


def fix_i18n_block(block, rules_map):
    if not isinstance(block, dict):
        return 0
    fixed = 0
    for lang in ("en", "uk"):
        t = block.get(lang)
        if not t:
            continue
        new = apply_fixes(t, rules_map[lang])
        if new != t:
            block[lang] = LiteralScalarString(new) if "\n" in new else new
            fixed += 1
    return fixed


def walk(node, rules_map):
    fixed = 0
    if isinstance(node, dict):
        if "de" in node and isinstance(node.get("de"), str):
            fixed += fix_i18n_block(node, rules_map)
        else:
            for v in node.values():
                fixed += walk(v, rules_map)
    elif isinstance(node, list):
        for v in node:
            fixed += walk(v, rules_map)
    return fixed


def main():
    rules_map = {"en": EN_FIXES, "uk": UK_FIXES}
    total = 0
    for path in ("data/locations/schleswig.yml", "data/shared/fuesse.yml"):
        yaml = YAML()
        yaml.preserve_quotes = True
        yaml.width = 10000
        yaml.indent(mapping=2, sequence=4, offset=2)
        data = yaml.load(Path(path).read_text(encoding="utf-8"))
        n = walk(data, rules_map)
        with open(path, "w", encoding="utf-8") as f:
            yaml.dump(data, f)
        print(f"{path}: {n} EN/UK fields patched")
        total += n
    print(f"\nTotal: {total} fields polished")


if __name__ == "__main__":
    main()
