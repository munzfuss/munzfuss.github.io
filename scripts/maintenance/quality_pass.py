#!/usr/bin/env python3
"""
Quality pass over EN and UK translations.
Three layers:

  1. System-wide regex fixes for known bad patterns produced by previous
     auto-translation passes (double "надбавка", broken decimals, "the-engraver",
     "Двойна/Двойне" → "Подвійна/Подвійне", etc.).
  2. Vocabulary additions for German leak-words still left over.
  3. Hand-polished replacements for the worst coin.note items, applied via
     a small NOTES dict.

Idempotent: re-running just re-applies the same substitutions.
"""
from __future__ import annotations
import re
from pathlib import Path
from ruamel.yaml import YAML
from ruamel.yaml.scalarstring import LiteralScalarString


# ---------- 1. System-wide fixes (apply to EN and UK uniformly) ----------

def fix_decimal_glue(text: str) -> str:
    """Restore the missing space before ".NNN" decimal that earlier cleanup ate.
    e.g. 'fineness.875' → 'fineness .875';   'silver.562' → 'silver .562'
    Heuristic: if a letter (any script) is immediately followed by a literal
    period and 1-5 digits, insert a space."""
    return re.sub(r"([A-Za-zА-Яа-яЁёІіЇїЄєҐґÄÖÜäöüß])\.(\d{2,5})\b", r"\1 .\2", text)

def collapse_double_premium_uk(text: str) -> str:
    """Fix 'надбавка (надбавка (Aufgeld))' → 'надбавка (Aufgeld)'."""
    return re.sub(r"надбавк([ауи])\s*\(надбавка\s*\(Aufgeld\)\)",
                  r"надбавк\1 (Aufgeld)", text)


# ---------- 2. EN-only vocabulary patches ----------

EN_FIXES = [
    # restore "die-engraver" wrecked by an earlier "die→the" rule
    (r"\bthe-engraver\b", "die-engraver"),

    # German leftovers in EN
    (r"\bin keiner Online-Quelle\b", "in any online source"),
    (r"\bnicht online belegt\b", "not online documented"),
    (r"\bThaler-Species-Prägung\b", "Thaler Species issue"),
    (r"\bSpeciedaler-Prägung\b", "Speciedaler issue"),
    (r"\bDukatenprägung\b", "ducat issue"),
    (r"\bSilberprägung\b", "silver issue"),
    (r"\bKleinstes Silber-sub-unit\b", "smallest silver sub-unit"),
    (r"\bKleinstes Silber-Teilstück\b", "smallest silver sub-unit"),
    (r"\bKleinstscheidemünze\b", "smallest petty coin"),
    (r"\bKupfer-Silber-Legierungsbereich\b", "copper-silver alloy range"),
    (r"\btypisch\b", "typical"),
    (r"\bMehrere Varianten\b", "Several variants"),
    (r"\bMehrere\b", "Several"),
    (r"\bFrüheste(?:r|n)?\b", "Earliest"),
    (r"\bSchmaleres/breiteres\b", "narrower/broader"),
    (r"\bSchmaleres\b", "narrower"),
    (r"\bbreiteres?\b", "broader"),
    (r"\bweiterhin\b", "still"),
    (r"\bSP-Angabe\b", "SP designation"),
    (r"\bWertangabe\b", "value designation"),
    (r"\bin Doppelung\b", "doubled"),
    (r"\bFolge der\b", "a legacy of the"),
    (r"\bFolge des\b", "a legacy of the"),
    (r"\bScheidemz\.\b", "petty coin"),
    (r"\bReiner Kupferabzug\b", "pure copper striking"),
    (r"\bReiner\b", "pure"),
    (r"\bKupferabzug\b", "copper striking"),
    (r"\bStaatsbankrott\b", "state bankruptcy"),
    (r"\bFortsetzung the\b", "continuation of the"),
    (r"\bcontinuation the\b", "continuation of the"),
    (r"\bvolle\b", "full"),
    (r"\bvollen\b", "full"),
    (r"\bRegierung(?:szeit)?\b", "reign"),
    (r"\bsteht <i>not on the coin</i>\b", "<i>does not appear on the coin</i>"),
    (r"\bsteht <i>nicht auf der Münze</i>\b", "<i>does not appear on the coin</i>"),
    (r"\beigene[snr]? Stempel\b", "its own dies"),
    (r"\beigenem Stempel\b", "its own dies"),
    (r"\bStempel\b", "die"),
    (r"\bSignatur\b", "signature"),
    (r"\bdie rechnerische Zuordnung\b", "the arithmetic correspondence"),
    (r"\brechnerische Zuordnung\b", "arithmetic correspondence"),
    (r"\bZuordnung\b", "assignment"),
    (r"\bnumismatische Zuordnung\b", "numismatic assignment"),
    (r"\bgemeinem 9¼-Fuß\b", "common 9¼-Fuß"),
    (r"\bgemeinen 9¼-Fuß\b", "common 9¼-Fuß"),
    (r"\bKürzerer Jahrgang\b", "Shorter year-issue"),
    (r"\bgleiche Stempel wie\b", "the same dies as"),
    (r"\bgleichen Stempel wie\b", "the same dies as"),
    (r"\bStempel wie\b", "dies as"),
    (r"\bgemeinen\b", "common"),
    (r"\bgemeinem\b", "common"),
    (r"\bin Tönning\b", "in Tönning"),  # already correct, but normalize
    (r"\bin der Schlacht von\b", "at the battle of"),
    (r"\bbattle of\b", "battle of"),
    (r"\bin битва\b", "in the battle"),  # mixed leftovers
    (r"\bSchlacht\b", "battle"),
    (r"\bFriedrichs IV\.\s*", "Friedrich IV "),
    (r"\bFriedrichs VI\.\s*", "Friedrich VI "),
    (r"\bFrederiks IV\.\s*", "Frederik IV "),
    (r"\bFrederiks VI\.\s*", "Frederik VI "),
    (r"\bFrederiks VII\.\s*", "Frederik VII "),
    (r"\bChristians IV\.\s*", "Christian IV "),
    (r"\bChristians V\.\s*", "Christian V "),
    (r"\bChristians VIII\.\s*", "Christian VIII "),
    (r"\bChristians IX\.\s*", "Christian IX "),
    (r"\bKarl Friedrich's\b", "Karl Friedrich's"),  # ok
    # Fix "of the Friedrich" leftovers
    (r"\bof the Herzogs\b", "of the Duke"),
    (r"\bDukes death\b", "Duke's death"),
    # Various article cleanups
    (r"\bafter the Emporium Hamburg\b", "in Emporium Hamburg"),
    (r"\bafter Emporium Hamburg\b", "in Emporium Hamburg"),
    (r"\bafter Staatsbankrott\b", "after the state bankruptcy"),
    (r"\bnach Staatsbankrott\b", "after the state bankruptcy"),
    (r"\bafter Krause\b", "from Krause"),
    (r"\bweight after Krause\b", "weight per Krause"),
    (r"\bweight per Krause\b", "weight per Krause"),
    (r"\bbei der\b", "at the"),
    (r"\bbei dem\b", "at the"),
    # Hanseatic German -> English
    (r"\bhanseatischer Rechnung\b", "Hanseatic reckoning"),
    (r"\blübisch-hanseatischer Rechnung\b", "Lübeck-Hanseatic reckoning"),
    (r"\bLübisch-Hanseat\.\s*Tradition\b", "Lübeck-Hanseatic tradition"),
    (r"\bLübisch-Hanseat\.\b", "Lübeck-Hanseatic"),
    (r"\bDänisch-Hanseat\.\b", "Danish-Hanseatic"),
    # "1-Schilling-Münze" → "1-Schilling coin"
    (r"\b(\d+)-Schilling-Münze\b", r"\1-Schilling coin"),
    (r"\bMünze\b", "coin"),
    (r"\bMünzen\b", "coins"),
    # Standalone german residues
    (r"\bWenn\b", "If"),
    (r"\bDamals\b", "At the time"),
    (r"\bdamals\b", "at the time"),
    (r"\bnoch\b", "still"),
    (r"\bschon\b", "already"),
    (r"\bbereits\b", "already"),
    (r"\bjedoch\b", "however"),
    (r"\bdaher\b", "hence"),
    (r"\bdeshalb\b", "therefore"),
    (r"\bdarum\b", "for that reason"),
    (r"\bnach Analogie\b", "by analogy"),
    (r"\bnach dem Standard\b", "by the standard"),
    (r"\bnach Standard\b", "to the standard"),
    (r"\bin der Schwierigkeit\b", "in the difficulty"),
    (r"\bvor 1771\b", "before 1771"),
    (r"\bvor 1788\b", "before 1788"),
    (r"\bvor 1813\b", "before 1813"),
    (r"\bnach 1788\b", "after 1788"),
    (r"\bnach 1813\b", "after 1813"),
    (r"\bWichtig:\b", "Note:"),
    (r"\bwichtig:\b", "note:"),
    (r"\bAbgrenzung\b", "delimitation"),
    (r"\bUnterscheidung\b", "distinction"),
    # Correct "heavier as" → "heavier than" and "lighter as" → "lighter than"
    (r"\b(heavier|lighter|larger|smaller|earlier|later|wider|narrower) as\b",
     r"\1 than"),
    # HRRDN → Holy Roman Empire
    (r"\bHRRDN\b", "the Holy Roman Empire (HRR)"),
    (r"\bHRR\b(?!N)", "the Holy Roman Empire"),
    # Numista-Standardwert
    (r"\bNumista-Standardwert\b", "Numista standard value"),
    (r"\bNumista standard\b", "Numista standard"),
    # zeitgenössischen
    (r"\bzeitgenössischen?\b", "contemporary"),

    # Compound fragments still left
    (r"\bletzte Tönning-Prägung\b", "the last Tönning issue"),
    (r"\bletzte\b", "last"),
    (r"\bDual-Prägung\b", "dual issue"),
    (r"\bKriegsbeginn\b", "the start of the war"),
    (r"\bPreuß\.\s*Prägung\b", "Prussian issue"),
    (r"\bpreuß\.\s*Annexion\b", "Prussian annexation"),
    (r"\bpreußische\s+Annexion\b", "Prussian annexation"),
    (r"\bin Holstein erst\b", "in Holstein only"),
    (r"\bgeliefert\b", "supplied"),
    (r"\bMzz\.\s*", "Mintmark "),
    (r"\bHerz\b(?=[ ,)])", "Heart"),
    (r"\bKopenhagen-Werkstattseite\b", "the Copenhagen workshop side"),
    (r"\bGlückstadt-Prägung\b", "the Glückstadt issue"),
    (r"\bTönning-Prägung\b", "Tönning issue"),
    (r"\bWerkstattseite\b", "workshop side"),
    (r"\bSchmaleres Schild\b", "narrower shield"),
    (r"\bbreiteres Schild\b", "broader shield"),
    (r"\bKriegsprägung\b", "wartime issue"),
    (r"\bReverse\b", "reverse"),
    (r"\bleichtere Scheide-Große-Münze\b", "a lighter large petty coin"),
    (r"\bleichtere\b", "lighter"),
    # Feinheit → fineness
    (r"\bFeinheit\b", "fineness"),
    (r"\büber\b", "above"),
    (r"\bSchätzung\b", "estimate"),
    (r"\bwährend\b", "during"),
    (r"\bwar\b(?=\s)", "was"),
    (r"\büberwiegend\b", "predominantly"),
]

# ---------- 3. UK-only vocabulary patches ----------

UK_FIXES = [
    # Russisms — all forms of "Двойн-" root
    (r"\bДвойн([іаоуиеєю])\b", r"Подвійн\1"),
    (r"\bдвойн([іаоуиеєю])\b", r"подвійн\1"),
    (r"\bДвойно\b", "Подвійно"),
    (r"\bдвойно\b", "подвійно"),
    # Russism "аукційн-" (wrong adjective root) → "аукціонн-" (standard Ukrainian)
    (r"\bаукційн(\w*)", r"аукціонн\1"),
    (r"\bАукційн(\w*)", r"Аукціонн\1"),
    # Russism plural "дома" → Ukrainian "доми"
    (r"\bаукціонні дома\b", "аукціонні доми"),
    (r"\bмонети з двома вартостями\b", "монети з двома позначеннями вартості"),
    # "рідкі випадки/екземпляри..." (calque of рос. "редкие случаи") → "рідкісні"
    # only in "frequency" contexts, not in "liquid" contexts
    (r"\b(р)ідк([іа])\b(?=\s+(?:випадк|екземпляр|пам'ятк|знахідк|карбуван|номінал|монет|вид))",
     r"\1ідкісн\2"),

    # Decimal glue and other systemic
    # German residues in UK
    (r"\bin keiner Online-Quelle\b", "у жодному онлайн-джерелі"),
    (r"\bnicht online belegt\b", "не задокументовано онлайн"),
    (r"\bне online задокументовано\b", "не задокументовано онлайн"),
    (r"\bThaler-Species-Prägung\b", "карбування Thaler Species"),
    (r"\bSpeciedaler-Prägung\b", "карбування Speciedaler"),
    (r"\bDukatenprägung\b", "карбування дукатів"),
    (r"\bSilberprägung\b", "срібне карбування"),
    (r"\bKleinstes Silber-частка\b", "найменший срібний підрозділ"),
    (r"\bKleinstes Silber-Teilstück\b", "найменший срібний підрозділ"),
    (r"\bKleinstscheidemünze\b", "найдрібніша розмінна монета"),
    (r"\bKupfer-Silber-Legierungsbereich\b", "діапазон мідно-срібного сплаву"),
    (r"\btypisch\b", "типове"),
    (r"\bMehrere Varianten\b", "Кілька варіантів"),
    (r"\bMehrere\b", "Кілька"),
    (r"\bFrüheste(?:r|n)?\b", "Найраніший"),
    (r"\bSchmaleres/breiteres\b", "вужчий/ширший"),
    (r"\bSchmaleres\b", "вужчий"),
    (r"\bbreiteres?\b", "ширший"),
    (r"\bweiterhin\b", "далі"),
    (r"\bSP-Angabe\b", "позначення SP"),
    (r"\bWertangabe\b", "позначення вартості"),
    (r"\bin Doppelung\b", "у подвоєнні"),
    (r"\bFolge der\b", "як спадщина"),
    (r"\bFolge des\b", "як спадщина"),
    (r"\bScheidemz\.\b", "розмінна монета"),
    (r"\bReiner Kupferabzug\b", "чистий мідний відбиток"),
    (r"\bReiner\b", "чистий"),
    (r"\bKupferabzug\b", "мідний відбиток"),
    (r"\bStaatsbankrott\b", "державне банкрутство"),
    (r"\bFortsetzung\b", "продовження"),
    (r"\bvolle\b", "повний"),
    (r"\bvollen\b", "повний"),
    (r"\bRegierung(?:szeit)?\b", "правління"),
    (r"\bsteht <i>не на монеті</i>\b", "<i>на монеті не зазначено</i>"),
    (r"\bsteht <i>nicht auf der Münze</i>\b", "<i>на монеті не зазначено</i>"),
    (r"\bвласний Stempel\b", "власний штамп"),
    (r"\beigene[snr]? Stempel\b", "власний штамп"),
    (r"\bз eigenem Stempel\b", "з власним штампом"),
    (r"\beigenem Stempel\b", "власним штампом"),
    (r"\bStempel\b", "штамп"),
    (r"\bSignatur\b", "підпис"),
    (r"\brechnerische Zuordnung\b", "арифметичне віднесення"),
    (r"\bZuordnung\b", "віднесення"),
    (r"\bgemeinen 9¼-Fuß\b", "загальний 9¼-Fuß"),
    (r"\bgemeinem 9¼-Fuß\b", "загальний 9¼-Fuß"),
    (r"\bgleiche Stempel wie\b", "ті самі штампи, що"),
    (r"\bgleichen Stempel wie\b", "ті самі штампи, що"),
    (r"\bStempel wie\b", "штампи, що"),
    (r"\bgemeinen\b", "загальний"),
    (r"\bgemeinem\b", "загальний"),
    (r"\bin Tönning\b", "у Tönning"),
    (r"\bin der Schlacht von\b", "у битві біля"),
    (r"\bin битва від\b", "у битві біля"),
    (r"\bSchlacht\b", "битва"),
    (r"\bFriedrichs IV\.\s*", "Фрідріха IV "),
    (r"\bFriedrichs VI\.\s*", "Фрідріха VI "),
    (r"\bFrederiks IV\.\s*", "Фредеріка IV "),
    (r"\bFrederiks VI\.\s*", "Фредеріка VI "),
    (r"\bFrederiks VII\.\s*", "Фредеріка VII "),
    (r"\bChristians IV\.\s*", "Кристіана IV "),
    (r"\bChristians V\.\s*", "Кристіана V "),
    (r"\bChristians VIII\.\s*", "Кристіана VIII "),
    (r"\bChristians IX\.\s*", "Кристіана IX "),
    (r"\bDukes death\b", "смерті герцога"),
    (r"\bпісля аукціон Emporium Hamburg\b", "за аукціоном Emporium Hamburg"),
    (r"\bпісля аукціон\b", "за аукціоном"),
    (r"\bпісля Staatsbankrott\b", "після державного банкрутства"),
    (r"\bbei der\b", "при"),
    (r"\bbei dem\b", "при"),
    (r"\bhanseatischer Rechnung\b", "ганзейського рахунку"),
    (r"\blübisch-hanseatischer Rechnung\b", "любецько-ганзейського рахунку"),
    (r"\bLübisch-Hanseat\.\s*Tradition\b", "любецько-ганзейської традиції"),
    (r"\bLübisch-Hanseat\.\b", "любецько-ганзейський"),
    (r"\bDänisch-Hanseat\.\b", "дансько-ганзейський"),
    (r"\b(\d+)-Schilling-Münze\b", r"монета номіналом \1 Schilling"),
    (r"\bMünze\b", "монета"),
    (r"\bMünzen\b", "монети"),
    # German function words
    (r"\bWenn\b", "Якщо"),
    (r"\bDamals\b", "На той час"),
    (r"\bdamals\b", "тоді"),
    (r"\bnoch\b", "ще"),
    (r"\bschon\b", "вже"),
    (r"\bbereits\b", "вже"),
    (r"\bjedoch\b", "однак"),
    (r"\bdaher\b", "тому"),
    (r"\bdeshalb\b", "тому"),
    (r"\bdarum\b", "з цієї причини"),
    (r"\bnach Analogie\b", "за аналогією"),
    (r"\bnach dem Standard\b", "за стандартом"),
    (r"\bnach Standard\b", "за стандартом"),
    (r"\bWichtig:\b", "Важливо:"),
    (r"\bwichtig:\b", "важливо:"),
    (r"\bAbgrenzung\b", "розмежування"),
    (r"\bUnterscheidung\b", "розрізнення"),
    # Comparative repairs
    (r"\bваж(чий|чі|чого|чим|чим за) як\b", r"важ\1 за"),
    (r"\bлег(ший|ші|шого|шим|шим за) як\b", r"лег\1 за"),
    # HRRDN
    (r"\bHRRDN\b", "Священна Римська імперія (HRR)"),
    (r"\bHRR\b(?!N)", "Священна Римська імперія"),
    # Numista-Standardwert
    (r"\bNumista-Standardwert\b", "стандартне значення Numista"),
    # in перехідний рік
    (r"\bin перехідний рік\b", "у перехідний рік"),
    # typisch для
    (r"\btypisch для\b", "типове для"),
    # Reverse → ректальне → реверсі (locative for "на")
    (r"\bна реверс\b", "на реверсі"),
    (r"\bна аверс\b", "на аверсі"),
    # обертає → обертається (intransitive verb)
    (r"\bVereinsthaler утім обертає\b", "Vereinsthaler усе ж обертається"),
    (r"\bобертає й у\b", "обертається й у"),
    (r"\bобертає через\b", "обертається через"),
    (r"\bобертає в\b", "обертається в"),
    # Гольштейн поділено надвоє → розділений на дві частини
    (r"\bГольштейн поділено надвоє\b", "Гольштейн розділений на дві частини"),
    # «Чинна по Рейху»
    (r"\bЧинна по Рейху\b", "Діє в Рейху"),
    # «Базові значення · Kurantmøntfod» → «Базові значення Kurantmøntfod»
    (r"\bБазові значення · Kurantmøntfod\b", "Базові значення Kurantmøntfod"),
    # Apostrophe spacing fix
    (r"\bне підтверджено\b", "не підтверджено"),  # already correct
    (r"\bнепідтверджено\b", "не підтверджено"),
    # zeitgenössisch
    (r"\bzeitgenössischen?\b", "тогочасних"),
    # «Кронемьонтський» → краще збережемо власну форму
    (r"\bКронемьонтський тарифний стандарт\b", "Тарифний стандарт Kronemønt"),
    # «9¼-Талерний» → «9¼-талерний» для консистентності
    (r"\b9¼-Талерний стандарт\b", "9¼-талерний стандарт"),
    # Convertions left over
    (r"\bвідповідає 11⅓-Fuß\b", "відповідає 11⅓-Fuß"),

    # Compound fragments still left
    (r"\bletzte Tönning-Prägung\b", "останнє карбування в Tönning"),
    (r"\bletzte\b", "останній"),
    (r"\bDual-Prägung\b", "подвійне карбування"),
    (r"\bKriegsbeginn\b", "початок війни"),
    (r"\bPreuß\.\s*Prägung\b", "прусське карбування"),
    (r"\bpreuß\.\s*Annexion\b", "прусської анексії"),
    (r"\bpreußische\s+Annexion\b", "прусської анексії"),
    (r"\bin Holstein erst\b", "в Гольштейні лише"),
    (r"\bgeliefert\b", "постачалося"),
    (r"\bMzz\.\s*", "Монограма "),
    (r"\bHerz\b(?=[ ,)])", "Серце"),
    (r"\bKopenhagen-Werkstattseite\b", "копенгагенський цех"),
    (r"\bGlückstadt-Prägung\b", "ґлюкштатське карбування"),
    (r"\bTönning-Prägung\b", "карбування в Tönning"),
    (r"\bWerkstattseite\b", "цех"),
    (r"\bSchmaleres Schild\b", "вужчий щит"),
    (r"\bbreiteres Schild\b", "ширший щит"),
    (r"\bKriegsprägung\b", "воєнне карбування"),
    (r"\bleichtere Scheide-Große-Münze\b", "легша велика розмінна монета"),
    (r"\bleichtere\b", "легша"),
    (r"\bFeinheit\b", "проба"),
    (r"\büber\b", "над"),
    (r"\bSchätzung\b", "оцінка"),
    (r"\bwährend\b", "під час"),
    (r"\büberwiegend\b", "переважно"),
    # Fix remaining duplication
    (r"\bПодвійна деномінація\b", "Подвійна деномінація"),  # already correct
    (r"\bДвойна\b", "Подвійна"),
    (r"\bДвойне\b", "Подвійне"),
    # variant → варіант
    (r"\bлавровий вінок-варіант\b", "варіант із лавровим вінком"),
    (r"\bпальмовий вінок-варіант\b", "варіант із пальмовим вінком"),
    # misc
    (r"\bверхнє\b", "верхнє"),
    (r"\ballerdings\b", "проте"),
    (r"\baufweisen\b", "виявляти"),
    (r"\baufweist\b", "виявляє"),
]


def apply_substitutions(text: str, rules: list, decimal_fix: bool, double_premium: bool) -> str:
    if not text:
        return text
    if decimal_fix:
        text = fix_decimal_glue(text)
    if double_premium:
        text = collapse_double_premium_uk(text)
    for pat, rep in rules:
        text = re.sub(pat, rep, text)
    # Clean double spaces (but NOT spaces before periods that touch decimals)
    text = re.sub(r"  +", " ", text)
    return text


# ---------- 4. Hand-polished coin notes ----------

NOTES_OVERRIDES = {

    "km-174-fr-iv-1699": {
        "en": "The smallest silver sub-unit of the period.",
        "uk": "Найменший срібний підрозділ цього періоду.",
    },

    "km-181-fr-iv-1702": {
        "en": (
            "Posthumously struck after the death of Friedrich IV at the battle "
            "of Klissow on 19 July 1702 · «<i>Commemorative issue on the Duke's "
            "death</i>» · mintmaster Hans Heinrich Lüders · 3/2 × Thaler Species "
            "standard yields the expected 37.93 g fine · Bruun lot 14232."
        ),
        "uk": (
            "Карбовано посмертно після загибелі Фредеріка IV у битві біля "
            "Кліссова 19 липня 1702 р. · «<i>Commemorative issue on the Duke's "
            "death</i>» · монетник Hans Heinrich Lüders · 3/2 × стандарту "
            "Thaler Species дає очікувану чисту вагу 37,93 г · Bruun, лот 14232."
        ),
    },

    "km-124-chr-v-1787": {
        "en": (
            "Reverse legend: <b>«2 ½ SCHILLING COURANT»</b> — <u>without a SP "
            "designation</u>; a petty coin. The arithmetic correspondence "
            "1/24 Thaler Species = 2½ Schilling Courant (via 60 Sch.C. = 1 Sp.) "
            "<i>does not appear on the coin</i> — it is only an accounting "
            "equivalent within the 9¼-Fuß."
        ),
        "uk": (
            "Легенда реверса: <b>«2 ½ SCHILLING COURANT»</b> — <u>без позначення "
            "SP</u>; розмінна монета. Арифметичне віднесення "
            "1/24 Thaler Species = 2½ Schilling Courant (через 60 Sch.C. = 1 Sp.) "
            "<i>на монеті не зазначене</i> — це лише розрахунковий еквівалент "
            "у межах 9¼-Fuß."
        ),
    },

    "km-120-chr-v-1787": {
        "en": (
            "= 1 Schilling Courant doubled; <b>no 1-Schilling coin was struck</b> "
            "— a legacy of the Lübeck-Hanseatic tradition."
        ),
        "uk": (
            "= 1 Schilling Courant у подвоєнні; <b>монету номіналом 1 Schilling "
            "не карбували</b> — спадщина любецько-ганзейської традиції."
        ),
    },

    "km-118-chr-v-1787": {
        "en": "<b>Petty coin</b> · pure copper striking.",
        "uk": "<b>Розмінна монета</b> · чистий мідний відбиток.",
    },

    "km-116-chr-v-1787": {
        "en": "<b>Petty coin</b> · pure copper striking.",
        "uk": "<b>Розмінна монета</b> · чистий мідний відбиток.",
    },

    "km-693-fr-vi-1819": {
        "en": (
            "The earliest Frederik VI Speciedaler issue after the state "
            "bankruptcy · ⌀ 37 mm."
        ),
        "uk": (
            "Найраніше карбування Speciedaler за Фредеріка VI після державного "
            "банкрутства · ⌀ 37 мм."
        ),
    },

    "km-720-chr-v-1840": {
        "en": "Several variants (KM# 720.1 / 720.2 / 720.3) · ⌀ 38.68 mm.",
        "uk": "Кілька варіантів (KM# 720.1 / 720.2 / 720.3) · ⌀ 38,68 мм.",
    },

    "km-158-fr-iv-1696": {
        "en": (
            "A shorter year-issue, with its own dies · mintmaster Hans Heinrich "
            "Lüders (Tönning)."
        ),
        "uk": (
            "Коротший річний випуск, з власними штампами · монетник Hans "
            "Heinrich Lüders (Tönning)."
        ),
    },

    "lange-438-fr-iv-1701-placeholder": {
        "en": "Emporium Hamburg auction 69 (2013) · variant with its own dies.",
        "uk": "Аукціон Emporium Hamburg 69 (2013) · варіант із власними штампами.",
    },

    "km-x001-fr-iii-1659": {
        "en": (
            "A narrower/broader shield variant (A/B) · still the «IS» signature · "
            "year next to the shield · .671 · 22.272 g (Numista) · Type A "
            "(small shield) and Type B (broad shield) · "
            "<b>Glückstadt Kronen-Fuß</b> as in Type I."
        ),
        "uk": (
            "Варіант із вужчим/ширшим щитом (A/B) · досі підпис «IS» · рік "
            "поруч зі щитом · .671 · 22,272 г (Numista) · Тип A (малий щит) "
            "і Тип B (широкий щит) · <b>ґлюкштатський Kronen-Fuß</b> як у Типі I."
        ),
    },

    "km-77-1-chr-v-1686": {
        "en": (
            "Palm-wreath variant; KM# 77.1 carries the year in the "
            "circumscription, KM# 77.2 next to the Order of the Elephant · "
            ".671 · 22.272 g (Numista) · the palm-wreath variant continues "
            "the Glückstadt Kronen-Fuß under Christian V."
        ),
        "uk": (
            "Варіант із пальмовим вінком; KM# 77.1 містить рік у коловій "
            "легенді, KM# 77.2 — поруч з Орденом Слона · .671 · 22,272 г "
            "(Numista) · варіант із пальмовим вінком продовжує "
            "ґлюкштатський Kronen-Fuß за Кристіана V."
        ),
    },

    "km-155-fr-iv-1695": {
        "en": (
            "«IIII SCHILLING» + date · actual weight 2.54–2.60 g recorded at "
            "Emporium Hamburg auction 69 (2013) · mintmaster H. H. Lüders · "
            "<b>not «Danske»</b> — the Lübeck reckoning was a political "
            "orientation towards the Holy Roman Empire (HRR)."
        ),
        "uk": (
            "«IIII SCHILLING» + дата · фактична вага 2,54–2,60 г за аукціоном "
            "Emporium Hamburg 69 (2013) · монетник H. H. Lüders · "
            "<b>не «Danske»</b> — любецький рахунок був політичною "
            "орієнтацією на Священну Римську імперію (HRR)."
        ),
    },

    "km-185-karl-fr-1703": {
        "en": (
            "A continuation of the Lübeck reckoning under Karl Friedrich · "
            "mintmaster Bastian Hille the Younger · ⌀ 22 mm (Numista)."
        ),
        "uk": (
            "Продовження любецького рахунку за Карла Фрідріха · монетник "
            "Bastian Hille молодший · ⌀ 22 мм (Numista)."
        ),
    },

    "km-160-fr-iv-1697": {
        "en": (
            "Mintmaster Hans Heinrich Lüders · «<i>Extremely rare Taler</i>» "
            "(Bruun) · <b>the first Thaler Species of Friedrich IV at Tönning</b> "
            "· follows the common 9¼-Fuß like the Danish royal Speciedaler · "
            "Bruun lot 14224."
        ),
        "uk": (
            "Монетник Hans Heinrich Lüders · «<i>Extremely rare Taler</i>» "
            "(Bruun) · <b>перший Thaler Species Фрідріха IV у Tönning</b> · "
            "наслідує загальний 9¼-Fuß, як данський королівський Speciedaler · "
            "Bruun, лот 14224."
        ),
    },

    "km-164-fr-iv-1698": {
        "en": (
            "The Stapelholm fortress on the reverse · 8 Schilling = "
            "2/3 Mark lübisch = 1/6 Rigsdaler Specie · Bruun lot 14228."
        ),
        "uk": (
            "Стапельгольмська фортеця на реверсі · 8 Schilling = "
            "2/3 Mark lübisch = 1/6 Rigsdaler Specie · Bruun, лот 14228."
        ),
    },

    "km-167-fr-iv-1698": {
        "en": (
            "Mintmaster Hans Heinrich Lüders · «<i>Very rare, particularly in "
            "this fantastic condition</i>» · a full Thaler Species issue from "
            "Tönning · Bruun lot 14229."
        ),
        "uk": (
            "Монетник Hans Heinrich Lüders · «<i>Very rare, particularly in "
            "this fantastic condition</i>» · повний випуск Thaler Species у "
            "Tönning · Bruun, лот 14229."
        ),
    },

    "km-176-fr-iv-1700": {
        "en": (
            "<b>Anomalous issue</b>: rough weight 26.14 g ≠ the 29.20 g of the "
            "Thaler Species of 1697/1698. If fineness .875 is assumed, then "
            "22.87 g fine → ≈ 10.23-Thaler-Fuß, <u>not the 9¼-Fuß</u>. "
            "Possibly a transition by Friedrich IV to a «reduced Tönning "
            "Thaler Species» in the last year of his reign before his death "
            "in 1702; the primary specification (mint ordinance) is "
            "<i>not available online</i> · Bruun lot 14231."
        ),
        "uk": (
            "<b>Аномальне карбування</b>: повна вага 26,14 г ≠ 29,20 г у "
            "Thaler Species 1697/1698. Якщо припустити пробу .875, то 22,87 г "
            "чистого → ≈ 10,23-Thaler-Fuß, <u>не 9¼-Fuß</u>. Імовірно, "
            "перехід Фрідріха IV до «зниженого тьоннінзького Thaler Species» в "
            "останній рік правління перед загибеллю 1702 р.; первинна "
            "специфікація (монетний ордонанс) <i>у мережі недоступна</i> · "
            "Bruun, лот 14231."
        ),
    },

    "km-183-karl-fr-1703": {
        "en": (
            "«I SCHILLING» + date · Tönning mint · Numista standard value: "
            "0.90 g / ⌀ 18 mm."
        ),
        "uk": (
            "«I SCHILLING» + дата · монетний двір Tönning · стандартне "
            "значення Numista: 0,90 г / ⌀ 18 мм."
        ),
    },

    "km-212-karl-fr-1711": {
        "en": (
            "Bust of the Duke facing right · reverse: a crowned Schleswig shield."
        ),
        "uk": (
            "Бюст герцога праворуч · реверс: коронований шлезвізький щит."
        ),
    },

    "km-80-chr-v-1694": {
        "en": (
            "Laurel-wreath variant · mintmaster Christian Winnecke sr. (C-W), "
            "mintmark ♡ (Heart) for the Copenhagen workshop side (but supplied "
            "for the Glückstadt issue)."
        ),
        "uk": (
            "Варіант із лавровим вінком · монетник Christian Winnecke ст. "
            "(C-W), монограма ♡ (Серце) для копенгагенського цеху (однак "
            "постачалася для ґлюкштатського карбування)."
        ),
    },

    "km-743-fr-vii-1849": {
        "en": (
            "«1 RIGSBANKDALER 30 SCHILL COURANT» · ⌀ 30.6 mm · the dual issue "
            "after the start of the war was struck only at Copenhagen."
        ),
        "uk": (
            "«1 RIGSBANKDALER 30 SCHILL COURANT» · ⌀ 30,6 мм · подвійне "
            "карбування після початку війни велося лише в Копенгагені."
        ),
    },

    "km-x002-1866": {
        "en": (
            "<sup>(*)</sup> A Prussian issue from 1861, but valid in Holstein "
            "only from 24 Aug. 1866 after the Prussian annexation. · "
            "<b>Petty coin</b> · = ¼ Groschen = 1/120 Thaler · reference "
            "weight with a tolerance of 4.31–4.73 g."
        ),
        "uk": (
            "<sup>(*)</sup> Прусське карбування з 1861, але в Гольштейні чинне "
            "лише з 24 серпня 1866 після прусської анексії. · "
            "<b>Розмінна монета</b> · = ¼ Groschen = 1/120 Thaler · "
            "референсна вага в межах 4,31–4,73 г."
        ),
    },

    "km-63-chr-v-1672": {
        "en": (
            "= 1 Krone = ⅔ Speciedaler (nominal) · obverse «PIETATE ET "
            "IUSTITIA» · reverse «IIII · MARCK · DANSKE» · "
            "<b>Glückstadt Kronen-Fuß</b>: 4 Marck Danske as the ⅔ Speciedaler "
            "equivalent but at reduced fineness (.671 instead of the pure "
            ".875 silver of the Thaler Species) — hence an actual fine weight "
            "of ca. 14.94451 g instead of 16.85449 g. The Colleconline "
            "specimen at 20.9 g carries jewellery traces and is therefore "
            "worn; the Numista standard weight for Christian V's Krone "
            "(KM# 370, 378 etc.) confirms 22.272 g."
        ),
        "uk": (
            "= 1 Krone = ⅔ Speciedaler (номінально) · аверс «PIETATE ET "
            "IUSTITIA» · реверс «IIII · MARCK · DANSKE» · "
            "<b>ґлюкштатський Kronen-Fuß</b>: 4 Marck Danske як еквівалент "
            "⅔ Speciedaler, але зі зниженою пробою (.671 замість чистого "
            ".875 срібла Thaler Species) — звідси фактична чиста вага бл. "
            "14,94451 г замість 16,85449 г. Екземпляр Colleconline вагою "
            "20,9 г має сліди ювелірної обробки, тому зношений; стандартна "
            "вага Numista для Krone Кристіана V (KM# 370, 378 та ін.) "
            "підтверджує 22,272 г."
        ),
    },
}


def patch_notes(coin) -> int:
    cid = coin.get("id")
    if cid not in NOTES_OVERRIDES:
        return 0
    override = NOTES_OVERRIDES[cid]
    if override is None:
        return 0
    note = coin.get("note")
    if not isinstance(note, dict):
        return 0
    n = 0
    for lang, text in override.items():
        text = text.strip()
        note[lang] = LiteralScalarString(text) if "\n" in text else text
        n += 1
    return n


# ---------- Walker ----------

def walk_and_fix(node):
    fixed = 0
    if isinstance(node, dict):
        if "de" in node and isinstance(node.get("de"), str):
            for lang, rules in (("en", EN_FIXES), ("uk", UK_FIXES)):
                t = node.get(lang)
                if not isinstance(t, str) or not t:
                    continue
                new = apply_substitutions(t, rules,
                                          decimal_fix=True,
                                          double_premium=(lang == "uk"))
                if new != t:
                    node[lang] = LiteralScalarString(new) if "\n" in new else new
                    fixed += 1
        else:
            for v in node.values():
                fixed += walk_and_fix(v)
    elif isinstance(node, list):
        for v in node:
            fixed += walk_and_fix(v)
    return fixed


def main():
    yaml = YAML()
    yaml.preserve_quotes = True
    yaml.width = 10000
    yaml.indent(mapping=2, sequence=4, offset=2)

    total_fixed = 0
    total_overrides = 0
    for path in ("data/locations/schleswig_holstein.yml", "data/shared/fuesse.yml"):
        p = Path(path)
        data = yaml.load(p.read_text(encoding="utf-8"))
        # System fixes
        n = walk_and_fix(data)
        total_fixed += n
        # Per-coin overrides
        for coin in data.get("coins", []) or []:
            total_overrides += patch_notes(coin)
        with open(p, "w", encoding="utf-8") as f:
            yaml.dump(data, f)
        print(f"{path}: {n} fields adjusted by system fixes")
    print(f"\n{total_overrides} coin-note fields replaced by hand-polished overrides")


if __name__ == "__main__":
    main()
