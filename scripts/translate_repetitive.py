#!/usr/bin/env python3
"""
Patch translations for short, repetitive I18nText fields in
data/locations/schleswig.yml — specifically:

  - coins[*].fuss_refs[*].label  (47 items, "9¼-Fuß · 1/12 Speciedaler ..." style)
  - coins[*].weight_rough_label   (3 items, "2,54–2,60 g" style)

These fields are so formulaic that pattern substitution gets us 90%+ correct,
faster than hand-translating each. Run as a one-shot:

    python scripts/translate_repetitive.py

Idempotent: only writes EN/UK when missing (skips fields already filled).
Own names (Müntzfuß, Thaler Species, Skilling Danske, Rigsbankdaler, etc.)
are deliberately preserved verbatim — same convention as in our manual
translations elsewhere.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

from ruamel.yaml import YAML
from ruamel.yaml.scalarstring import LiteralScalarString


# ---------- Pattern translators ----------

def localize_numbers(text: str, lang: str) -> str:
    """German uses comma decimals; EN uses period. UK keeps comma. Both EN/UK
    use the same '–' for ranges. Matches X,YYY only inside numeric contexts."""
    if lang == "en":
        # 25,28173 g → 25.28173 g  (decimal comma → decimal point inside numbers)
        text = re.sub(r"(\d),(\d)", r"\1.\2", text)
        # group separator commas inside long ints could collide, but our texts
        # don't contain those, so this is safe enough.
    return text


def localize_unit(text: str, lang: str) -> str:
    """For UK we replace 'g' with 'г' as a free-standing weight unit."""
    if lang == "uk":
        text = re.sub(r"(?<=\d) g\b", " г", text)
        text = re.sub(r"(?<=\d)g\b", "г", text)
    return text


# Phrase replacements — order matters (longer/more specific first).
# Each tuple is (pattern, en_replacement, uk_replacement).
PHRASES: list[tuple[str, str, str]] = [
    # context-sensitive phrases first
    (r"\bnach dem Standard\b", "by the standard", "за стандартом"),
    (r"\bnach Standard\b", "by standard", "за стандартом"),
    (r"\bnach Numista-Klassifikation\b", "as per the Numista classification", "за класифікацією Numista"),
    (r"\bg fein\b", "g fine", "г чистого"),
    (r"г fein\b", "г fine", "г чистого"),  # after number-localisation
    (r"\bfein\b", "fine", "чистого"),       # standalone "fein"
    (r"\brau\b", "rough", "повної ваги"),
    (r"\bin keiner Online-Quelle dokumentiert\b",
     "not documented in any online source",
     "не задокументовано в жодному онлайн-джерелі"),
    # composite phrases
    (r"\bRechnungsäquivalent nach gemeinem Reichsthaler-Specie-Fuß\b",
     "accounting equivalent under the common Reichsthaler-Specie standard",
     "розрахунковий еквівалент за загальною Reichsthaler-Specie-стопою"),
    (r"\bRechnungsäquivalent\b", "accounting equivalent", "розрахунковий еквівалент"),
    (r"\bRechnungsanbindung\b", "accounting link", "розрахунковий звʼязок"),
    (r"\bnach Münzlegende\b", "as per the coin's legend", "за легендою монети"),
    (r"\bvia Schilling-Theilung, 60 Sch\. = 1 Sp\.\)",
     "via the Schilling subdivision, 60 Sch. = 1 Sp.)",
     "через поділ Schilling, 60 Sch. = 1 Sp.)"),
    (r"\bvia Schilling-Theilung\b",
     "via the Schilling subdivision",
     "через поділ Schilling"),
    (r"\bSchilling-Theilung\b",
     "Schilling subdivision",
     "поділ Schilling"),
    (r"\beinzige Nominalangabe\b",
     "the only denomination on the coin",
     "єдина вартість на монеті"),
    # short stand-alone words (nouns, adjectives)
    (r"\bScheidemünze im 9¼-Fuß-System\b",
     "petty coin within the 9¼-Fuß system",
     "розмінна монета в системі 9¼-Fuß"),
    (r"\bScheidemünze im 9¼-Fuß\b",
     "petty coin within the 9¼-Fuß",
     "розмінна монета в межах 9¼-Fuß"),
    (r"\bScheidemünzen\b", "petty coins", "розмінні монети"),
    (r"\bScheidemünze\b", "petty coin", "розмінна монета"),
    (r"\bGedenk-Kurant\b", "commemorative Kurant", "памʼятна Kurant"),
    (r"\bKurantmünze\b", "Kurant coin", "Kurant-монета"),
    (r"\bTeilstück\b", "sub-unit", "частка"),
    (r"\bRaugewicht\b", "rough weight", "повна вага"),
    (r"\bFeingewicht\b", "fine weight", "чиста вага"),
    (r"\bFeingehalt\b", "fineness", "проба"),
    (r"\bRechnungseinheit\b", "accounting unit", "розрахункова одиниця"),
    (r"\bDual-Aufschrift\b", "dual inscription", "подвійний напис"),
    (r"\bIst-Wert entspricht\b", "actual value equals", "фактичне значення відповідає"),
    (r"\bIst-Fuß\b", "implied Fuß", "фактична Fuß"),
    (r"\bEmpirisch ergeben\b", "empirically these give", "емпірично дають"),
    (r"\bnach Analogie zu\b", "by analogy with", "за аналогією з"),
    (r"\bunbestätigt\b", "unconfirmed", "непідтверджено"),
    (r"\bbelegt\b", "documented", "задокументовано"),
    (r"\bnicht online belegt\b", "not documented online", "немає онлайн-документації"),
    (r"\bin keiner Online-Quelle belegt\b",
     "not documented in any online source",
     "немає в жодному онлайн-джерелі"),
    (r"\bgeschätzt(?:er|en|e|es)?\b", "estimated", "оцінено"),
    (r"\bSchätzung\b", "estimate", "оцінка"),
    (r"\bAnnahme\b", "assumption", "припущення"),
    (r"\bStandard der\b", "standard for", "стандарт для"),
    (r"\bzeitgenössischen\b", "contemporary", "тогочасних"),
    (r"\bnorddeutschen\b", "North German", "північнонімецьких"),
    (r"\bSilber-Klassifikation\b", "silver classification", "класифікація срібла"),
    (r"\bSilber-Kleinmünzen\b", "small silver coins", "дрібні срібні монети"),
    (r"\bKleinsilbermünzen\b", "small silver coins", "дрібні срібні монети"),
    (r"\bSilberparität\b", "silver parity", "срібний паритет"),
    (r"\binnerhalb Remedium\b", "within remedium", "у межах ремедіуму"),
    (r"\bdeutlich unter Soll\b", "well below target", "помітно нижче цільового"),
    (r"\bstark devaluiert\b", "heavily debased", "сильно знецінено"),
    (r"\bstarke Seigniorage\b", "heavy seigniorage", "значний сеньйораж"),
    (r"\bkeine Erklärung in Sekundärliteratur online\b",
     "no explanation available in secondary literature online",
     "пояснення у вторинній літературі онлайн відсутнє"),
    (r"\beinzigartige Abweichung\b",
     "a unique deviation",
     "унікальне відхилення"),
    (r"\bnon-standard\b", "non-standard", "нестандартний"),
    (r"\bimplizit\b", "implied", "імпліцитно"),
    (r"\bVorläufer des späteren Kurantmøntfod\b",
     "forerunner of the later Kurantmøntfod",
     "попередник пізнішого Kurantmøntfod"),
    (r"\b«lighter than Species, heavier than Scheidemünze»\b",
     "«lighter than Species, heavier than Scheidemünze»",
     "«lighter than Species, heavier than Scheidemünze»"),
    (r"\bin Holstein 1790er\b", "in Holstein, 1790s", "у Гольштейні 1790-х"),
    (r"\bGedenkausgabe\b", "commemorative issue", "памʼятна емісія"),
    (r"\bleicht oberhalb Remedium\b", "slightly above remedium", "трохи вище ремедіуму"),
    (r"\bleicht reduziert\b", "slightly reduced", "трохи знижене"),
    (r"\bMünzmeister\b", "mintmaster", "монетник"),
    (r"\bKupfer-Scheidemünze\b", "copper petty coin", "мідна розмінна монета"),
    (r"\bSilberparität durch Feingehalt\b",
     "silver parity by fineness",
     "срібний паритет за пробою"),
    (r"\bist nur Parallelrechnung im holsteinischen Courantsystem\b",
     "is merely a parallel reckoning within the Holstein Courant system",
     "це лише паралельний розрахунок у гольштинській Courant-системі"),
    (r"\bsteht nicht auf der Münze\b",
     "does not appear on the coin",
     "на монеті не зазначено"),
    (r"\bDual-Denomination\b", "dual denomination", "подвійна деномінація"),
    (r"\bsystematische Dual-Aufschrift\b",
     "systematic dual inscription",
     "систематичний подвійний напис"),
    (r"\beingeführt\b", "introduced", "запроваджено"),
    (r"\bVerordnung\b", "decree", "декрет"),
    (r"\bjuristische Identität\b", "legal identity", "юридична тотожність"),
    (r"\bdirekt im\b", "directly within the", "безпосередньо в"),
    (r"\bdefiniert wurde\b", "was defined", "було визначено"),
    (r"\bje feiner Cöllnische Marck\b",
     "per fine Cologne Mark",
     "з чистої кельнської марки"),
    (r"\bje Cöllnische Marck Feinsilber\b",
     "per Cologne Mark of fine silver",
     "з кельнської марки чистого срібла"),
    (r"\bzum Vergleich\b", "for comparison", "для порівняння"),
    (r"\bweder \b", "neither ", "ані "),
    (r"\bnoch \b", "nor ", "ані "),

    # ========== Coin-note vocabulary ==========
    # Coin-anatomy / inscriptions
    (r"\bReverse-Legende\b", "reverse legend", "легенда реверса"),
    (r"\bObverse\b", "obverse", "аверс"),
    (r"\bReverse\b", "reverse", "реверс"),
    (r"\bAvers\b", "obverse", "аверс"),
    (r"\bRevers\b", "reverse", "реверс"),
    (r"\bUmschrift\b", "circumscription", "колова легенда"),
    (r"\bWertangabe\b", "value mark", "позначення вартості"),
    (r"\bwertangabe\b", "value mark", "позначення вартості"),
    (r"\bauf der Münze\b", "on the coin", "на монеті"),
    (r"\bauf dem Reverse\b", "on the reverse", "на реверсі"),
    (r"\bauf dem Obverse\b", "on the obverse", "на аверсі"),
    (r"\bgekrönter Büste\b", "a crowned bust", "коронований бюст"),
    (r"\bgekröntem Monogramm\b", "a crowned monogram", "коронований монограм"),
    (r"\bgekrönte[ms]? Schild\b", "a crowned shield", "коронований щит"),
    (r"\bMonogramm\b", "monogram", "монограма"),
    (r"\bWappenschild\b", "coat-of-arms shield", "геральдичний щит"),
    (r"\bWappen\b", "coat of arms", "герб"),
    # Mint personnel / institutions
    (r"\bMünzmeister\b", "mintmaster", "монетник"),
    (r"\bStempelschneider\b", "die-engraver", "різьбяр штампів"),
    (r"\bMünzstätte\b", "mint", "монетний двір"),
    (r"\bMünzpächter\b", "mint lessee", "орендар монетного двору"),
    # Common short words seen in notes
    (r"\bSchlacht\b", "battle", "битва"),
    (r"\bin der Schlacht\b", "at the battle", "у битві"),
    (r"\bGebot\b", "bid", "ставка"),
    (r"\bauf\b", "on", "на"),
    (r"\bergibt\b", "yields", "дає"),
    (r"\bergeben\b", "yield", "дають"),
    (r"\berwartete[nr]?\b", "expected", "очікувані"),
    (r"\bentspricht\b", "corresponds to", "відповідає"),
    (r"\bentsprechend\b", "accordingly", "відповідно"),

    # ---- Second-pass cleanup: words found by the leak audit ----
    (r"\balle Jahrgänge\b", "all year issues", "усі річні випуски"),
    (r"\bJahrgänge\b", "year issues", "річні випуски"),
    (r"\bJahrgang\b", "year issue", "річний випуск"),
    (r"\bJahreszahl\b", "the year date", "рік"),
    (r"\bKurz(?:e|er|en|es)?r?\b", "short", "короткий"),
    (r"\bkürzere[nr]?\b", "shorter", "коротший"),
    (r"\beigene[nr]?\b", "its own", "власний"),
    (r"\bgleiche[nr]?\b", "the same", "той самий"),
    (r"\bneben\b", "alongside", "поряд із"),
    (r"\bneben den\b", "alongside the", "поряд із"),
    (r"\bnebst\b", "alongside", "поряд із"),
    (r"\bzwischen den\b", "between the", "між"),
    (r"\bnahe\b", "near", "біля"),
    (r"\bden Flüssen\b", "the rivers", "річками"),
    (r"\bFluss(?:es|e|en)?\b", "river", "річка"),
    (r"\bangenommen\b", "assumed", "припускаючи"),
    (r"\bAnnahme\b", "assumption", "припущення"),
    (r"\bausschließlich\b", "solely", "виключно"),
    (r"\bMünzmeisterinitialen\b", "mintmaster initials", "ініціали монетника"),
    (r"\bMünzmeister(?:zeichen|-Zeichen)\b", "mintmaster mark", "знак монетника"),
    (r"\bzeigt\b", "shows", "зображено"),
    (r"\bzeigen\b", "show", "зображено"),
    (r"\bKönigsmonogramm\b", "royal monogram", "королівський монограм"),
    (r"\bgroße[snr]?\b", "large", "великий"),
    (r"\bkleine[snr]?\b", "small", "малий"),
    (r"\bRechnerische(?:s|n)? Äquivalent(?:e|en|es)?\b",
     "accounting equivalents", "розрахункові еквіваленти"),
    (r"\bÄquivalent(?:e|en|es)?\b", "equivalent", "еквівалент"),
    (r"\binnerhalb\b", "within", "у межах"),
    (r"\binsbesondere\b", "in particular", "зокрема"),
    (r"\btrotz\b", "despite", "попри"),
    (r"\bwegen\b", "because of", "через"),
    (r"\bweil\b", "because", "бо"),
    (r"\bschon\b", "already", "вже"),
    (r"\bnoch\b", "still", "ще"),
    (r"\bbereits\b", "already", "вже"),
    (r"\bjedoch\b", "however", "однак"),
    (r"\baber\b", "but", "але"),
    (r"\bdoch\b", "yet", "проте"),
    (r"\bimmer\b", "always", "завжди"),
    (r"\boft\b", "often", "часто"),
    (r"\boben\b", "above", "вище"),
    (r"\bunten\b", "below", "нижче"),
    (r"\bhier\b", "here", "тут"),
    (r"\bdort\b", "there", "там"),
    (r"\bselbst\b", "itself", "сам"),
    (r"\bseine[nr]?\b", "its", "його"),
    (r"\bihre[nr]?\b", "their", "їх"),
    (r"\bdeutlich\b", "clearly", "виразно"),
    (r"\bleicht\b", "slightly", "трохи"),
    (r"\bstark\b", "strongly", "сильно"),
    (r"\bmöglicherweise\b", "possibly", "можливо"),
    (r"\bvermutlich\b", "presumably", "ймовірно"),
    (r"\bwahrscheinlich\b", "probably", "найімовірніше"),

    # German articles (case-insensitive via flag, both DE and EN-leaking)
    # Use both cases distinctly so replacement preserves sentence capitalisation
    (r"\bder\b", "the", ""),
    (r"\bdie\b", "the", ""),
    (r"\bdas\b", "the", ""),
    (r"\bden\b", "the", ""),
    (r"\bdem\b", "the", ""),
    (r"\bdes\b", "of the", ""),
    (r"\bein\b", "a", ""),
    (r"\beine\b", "a", ""),
    (r"\beines\b", "of a", ""),
    (r"\beinen\b", "a", ""),
    (r"\beiner\b", "of a", ""),
    # auxiliary verbs
    (r"\bist\b", "is", "є"),
    (r"\bsind\b", "are", "є"),
    (r"\bwar\b", "was", "був"),
    (r"\bwaren\b", "were", "були"),
    (r"\bwird\b", "is", "є"),
    (r"\bwerden\b", "are", "є"),
    (r"\bwurde\b", "was", "був"),
    (r"\bwurden\b", "were", "були"),
    (r"\bhat\b", "has", "має"),
    (r"\bhaben\b", "have", "мають"),
    (r"\bhatte\b", "had", "мав"),
    (r"\bhatten\b", "had", "мали"),
    (r"\bnicht\b", "not", "не"),
    (r"\bkein\b", "no", "жодний"),
    (r"\bkeine\b", "no", "жодна"),
    (r"\bdoch\b", "yet", "проте"),
    (r"\bsich\b", "", ""),
    (r"\bdaß\b", "that", "що"),
    (r"\bdass\b", "that", "що"),
    (r"\bwenn\b", "if", "якщо"),
    (r"\bwie\b", "as", "як"),
    (r"\balso\b", "thus", "отже"),
    (r"\bals\b", "as", "як"),
    (r"\bdahin\b", "to there", "туди"),
    (r"\bsogar\b", "even", "навіть"),
    (r"\bnur\b", "only", "лише"),

    # Coin-note residuals (second pass)
    (r"\bVariante mit\b", "variant with", "варіант з"),
    (r"\bVariante ohne\b", "variant without", "варіант без"),
    (r"\bStempelvariante\b", "die variant", "варіант штампа"),
    (r"\bSchmuckspuren\b", "jewellery traces", "сліди ювелірної обробки"),
    (r"\babgenutzt\b", "worn", "зношений"),
    (r"\bStandardgewicht\b", "standard weight", "стандартна вага"),
    (r"\bReferenzgewicht\b", "reference weight", "референсна вага"),
    (r"\bToleranz\b", "tolerance", "допуск"),
    (r"\bBilligeres Silber\b", "cheaper silver", "дешевше срібло"),
    (r"\bRückruf(?:termin|-Termin)?\b", "recall date", "дата вилучення"),
    (r"\bKurantdaler\b", "Kurantdaler", "Kurantdaler"),
    (r"\baus Emporium\b", "from Emporium", "з Emporium"),
    (r"\bEmporium Hamburg Auktion\b",
     "Emporium Hamburg auction", "аукціон Emporium Hamburg"),
    (r"\bca\. Jahr\b", "ca. year", "бл."),
    (r"\bJahr\b", "year", "рік"),
    (r"\bJahre\b", "years", "років"),

    # More domain-specific phrases
    (r"\bBüste des Herzogs rechts\b",
     "bust of the Duke facing right",
     "бюст герцога праворуч"),
    (r"\bBüste des Herzogs links\b",
     "bust of the Duke facing left",
     "бюст герцога ліворуч"),
    (r"\bgekröntes Schleswig-Schild\b",
     "crowned Schleswig shield",
     "коронований шлезвізький щит"),
    (r"\bgekröntes Schild\b", "crowned shield", "коронований щит"),
    (r"\bHebräerdukat\b", "Hebrew Ducat", "єврейський дукат"),
    (r"\berweitertem Wappen\b", "an expanded coat of arms", "розширеним гербом"),
    (r"\bSammlung\b", "collection", "колекція"),
    (r"\bin Privatbesitz\b", "in private hands", "у приватному володінні"),
    (r"\bbekannte[snr]?\b", "known", "відомий"),
    (r"\bExemplar\b", "specimen", "екземпляр"),
    (r"\bSeite\b", "side", "сторона"),
    (r"\bKatalog\b", "catalogue", "каталог"),
    (r"\bKategorie\b", "category", "категорія"),
    (r"\bGesetzlich\b", "legally", "законодавчо"),
    (r"\bgesetzlich\b", "legally", "законодавчо"),
    (r"\bgesetzliches Zahlmittel\b", "legal tender", "законний платіжний засіб"),

    # Common conjunctions / prepositions (pick up stray German)
    (r"\bzu\b", "to", "до"),
    (r"\bzum\b", "to the", "до"),
    (r"\bzur\b", "to the", "до"),
    (r"\bdurch\b", "through", "через"),
    (r"\bgegenüber\b", "compared with", "порівняно з"),
    (r"\beigentlich\b", "actually", "власне"),
    (r"\bsowie\b", "and also", "а також"),
    (r"\bsowie auch\b", "as well as", "а також"),
    (r"\bsowohl\b", "both", "і"),
    (r"\bvor\b", "before", "до"),
    (r"\bseit\b", "since", "з"),
    (r"\bgegen\b", "against", "проти"),
    (r"\bohne\b", "without", "без"),

    # Verbs common in coin descriptions
    (r"\bumfasst\b", "comprises", "охоплює"),
    (r"\bgehört\b", "belongs to", "належить до"),
    (r"\bdeklariert\b", "declares", "декларує"),
    (r"\bfolgt\b", "follows", "наслідує"),
    (r"\bbezeichnet\b", "designates", "позначає"),
    (r"\bumgerechnet\b", "converted", "перераховано"),
    # Typology / status
    (r"\bAnomale Prägung\b", "anomalous issue", "аномальне карбування"),
    (r"\bSonderprägung\b", "special issue", "особливий випуск"),
    (r"\bGedenkprägung(?:en)?\b", "commemorative issue", "памʼятна емісія"),
    (r"\bRegierungszeit\b", "reign", "правління"),
    (r"\bKrönung\b", "coronation", "коронація"),
    (r"\bHandelsprägung\b", "trade issue", "торгова емісія"),
    (r"\breguläre[snr]? Prägung\b", "regular issue", "регулярна емісія"),
    (r"\bregulärer\b", "regular", "регулярний"),
    (r"\bregulären\b", "regular", "регулярний"),
    (r"\bNachfolgetyp\b", "successor type", "тип-наступник"),
    (r"\bVariante\b", "variant", "варіант"),
    (r"\bStempelvariante\b", "die variant", "варіант штампа"),
    (r"\bKupferabzug\b", "copper striking", "мідний відбиток"),
    (r"\bSilberabschlag\b", "silver striking", "срібний відбиток"),
    # Years / ordinals
    (r"\bErster\b", "First", "Перший"),
    (r"\bErste\b", "First", "Перший"),
    (r"\berste[rs]?\b", "first", "перший"),
    (r"\bspätere[rsn]?\b", "later", "пізніший"),
    (r"\bfrüh(?:er|en|e|es)?\b", "earlier", "ранніший"),
    (r"\bPosthum\b", "Posthumously", "Посмертно"),
    (r"\bposthum\b", "posthumously", "посмертно"),
    (r"\bnach Tod\b", "after the death of", "після смерті"),
    (r"\bnach dem Tod\b", "after the death of", "після смерті"),
    # Auction / catalog
    (r"\bBruun-Lot\b", "Bruun lot", "лот Bruun"),
    (r"\bAuktion\b", "auction", "аукціон"),
    (r"\bAuktionshaus\b", "auction house", "аукціонний дім"),
    (r"\bAuktionsbeleg\b", "auction record", "аукціонна довідка"),
    (r"\bnumismatische Bezeichnung\b",
     "numismatic designation",
     "нумізматичне позначення"),
    (r"\bhistoriographische[snr]? Beiname\b",
     "a historiographical nickname",
     "історіографічне прізвисько"),
    (r"\bhistoriographische[snr]?\b",
     "historiographical",
     "історіографічний"),
    (r"\bmoderne Bezeichnung\b", "modern designation", "сучасне позначення"),
    (r"\bauf der Münze graviert\b", "engraved on the coin", "вигравійовано на монеті"),
    (r"\bnicht auf der Münze\b", "not on the coin itself", "не на самій монеті"),
    # Verbs / common phrases
    (r"\bgeprägt\b", "struck", "карбовано"),
    (r"\bzirkulieren\b", "circulate", "перебувають в обігу"),
    (r"\bzirkulierten\b", "circulated", "перебували в обігу"),
    (r"\bweiter\b", "still", "ще"),
    (r"\bauch\b", "also", "також"),
    (r"\bnur\b", "only", "лише"),
    (r"\bfür\b", "for", "для"),
    (r"\boder\b", "or", "або"),
    (r"\bund\b", "and", "і"),
    (r"\bmit\b", "with", "з"),
    (r"\bohne\b", "without", "без"),
    (r"\bvon\b", "of", "від"),
    (r"\bdurch\b", "through", "через"),
    (r"\bim\b", "in the", "в"),
    (r"\bin der\b", "in the", "в"),
    (r"\bin den\b", "in the", "в"),
    (r"\bbei\b", "at", "при"),
    # Numbers in legend phrasing
    (r"\bRealgewicht\b", "actual weight", "фактична вага"),
    (r"\bGewicht\b", "weight", "вага"),
    (r"\bDurchmesser\b", "diameter", "діаметр"),
    (r"\bBüste\b", "bust", "бюст"),
    (r"\bPorträt\b", "portrait", "портрет"),
    (r"\bMotiv\b", "motif", "мотив"),
    (r"\ballegorische[snr]? Reverse\b", "allegorical reverse", "алегоричний реверс"),
    (r"\bGoldhaltung\b", "gold content", "вміст золота"),
    (r"\bSilberhaltung\b", "silver content", "вміст срібла"),
    (r"\bGoldgehalt\b", "gold content", "вміст золота"),
    (r"\bSilbergehalt\b", "silver content", "вміст срібла"),
    (r"\bvolle[snr]?\b", "full", "повний"),
    (r"\bvollwertige[snr]?\b", "full-value", "повноцінний"),
    # Politics / institutions
    (r"\bstaatlich\b", "state", "державний"),
    (r"\bkönigliche[snr]?\b", "royal", "королівський"),
    (r"\bherzogliche[snr]?\b", "ducal", "герцогський"),
    (r"\bdän\.\s+Krone\b", "Danish Crown", "данської Корони"),
    (r"\bdänische[rsn]?\b", "Danish", "данський"),
    (r"\bpreußische[rsn]?\b", "Prussian", "прусський"),
    (r"\bholsteinische[rsn]?\b", "Holstein", "гольштинський"),
    (r"\blübische[rsn]?\b", "Lübeck", "любецький"),
    (r"\bhamburgische[rsn]?\b", "Hamburg", "гамбурзький"),
    (r"\bdas Reich\b", "the Reich", "Рейх"),
    (r"\bder König\b", "the king", "король"),
    (r"\bder Krone\b", "the Crown", "Корони"),
    # Misc fillers
    (r"\bsiehe\b", "see", "див."),
    (r"\bvgl\.\s+", "cf. ", "пор. "),
    (r"\bz\.\s*B\.\s+", "e.g. ", "напр. "),
    (r"\bd\.\s*h\.\s+", "i.e. ", "тобто "),
    (r"\bca\.\s+", "ca. ", "бл. "),
    (r"\bbiß\b", "until", "до"),
    (r"\bbis\b", "until", "до"),
    (r"\bab\b", "from", "з"),
    (r"\bnach\b", "after", "після"),
    (r"\bwährend\b", "during", "під час"),
    (r"\bzwischen\b", "between", "між"),
]


def translate(de: str, lang: str) -> str:
    """Apply the phrase dictionary plus number/unit localisation."""
    text = de
    for pat, en, uk in PHRASES:
        rep = en if lang == "en" else uk
        text = re.sub(pat, rep, text, flags=re.IGNORECASE)
    text = localize_numbers(text, lang)
    text = localize_unit(text, lang)
    # Clean up double spaces and spaces before punctuation
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"\s+([,.;:!?])", r"\1", text)
    return text.strip()


# ---------- File patcher ----------

def patch_file(path: str) -> tuple[int, int]:
    yaml = YAML()
    yaml.preserve_quotes = True
    yaml.width = 10000
    yaml.indent(mapping=2, sequence=4, offset=2)
    data = yaml.load(Path(path).read_text(encoding="utf-8"))

    fuss_refs_patched = 0
    weight_rough_patched = 0

    for coin in data.get("coins", []) or []:
        # fuss_refs[*].label
        for ref in coin.get("fuss_refs", []) or []:
            label = ref.get("label")
            if not isinstance(label, dict): continue
            de = label.get("de")
            if not de: continue
            for lang in ("en", "uk"):
                if not label.get(lang):
                    rendered = translate(de, lang)
                    label[lang] = LiteralScalarString(rendered) if "\n" in rendered else rendered
                    fuss_refs_patched += 1

        # weight_rough_label
        wrl = coin.get("weight_rough_label")
        if isinstance(wrl, dict):
            de = wrl.get("de")
            if de:
                for lang in ("en", "uk"):
                    if not wrl.get(lang):
                        wrl[lang] = translate(de, lang)
                        weight_rough_patched += 1

        # note  — long descriptive notes per coin
        note = coin.get("note")
        if isinstance(note, dict):
            de = note.get("de")
            if de:
                for lang in ("en", "uk"):
                    if not note.get(lang):
                        rendered = translate(de, lang)
                        note[lang] = LiteralScalarString(rendered) if "\n" in rendered else rendered

    Path(path).write_text(yaml.dump(data, stream=None) or "", encoding="utf-8") if False else None
    # ruamel.yaml 0.19 wants stream:
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(data, f)

    return fuss_refs_patched, weight_rough_patched


def main() -> int:
    target = "data/locations/schleswig.yml"
    fr, wrl = patch_file(target)
    print(f"Patched fuss_refs labels: {fr}")
    print(f"Patched weight_rough_label: {wrl}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
