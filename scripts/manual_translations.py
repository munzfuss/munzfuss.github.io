#!/usr/bin/env python3
"""
Hand-polished translations for the longest / most visible coin notes.

These replace the pattern-based auto-translations produced by
scripts/translate_repetitive.py wherever quality needs to be publication-grade
rather than approximate.

Run as a one-shot:
    python scripts/manual_translations.py

Idempotent: re-running just reapplies the same dictionary.
"""
from __future__ import annotations
import sys
from pathlib import Path
from ruamel.yaml import YAML
from ruamel.yaml.scalarstring import LiteralScalarString


# coin_id -> {"en": "...", "uk": "..."}
# Own names (Müntzfuß, Thaler Species, Skilling Danske, Rigsbankdaler, Courant,
# Aufgeld, Kurantmøntfod, etc.) are preserved verbatim.
NOTES: dict[str, dict[str, str]] = {

    "km-42-1-fr-iii-1658": {
        "en": (
            'Obverse «FRIDERICK 3 D·G: D·N·R·» with a crowned bust · '
            'reverse <b>«MONNO GLVCKSTAD 1659 · XVI · E·REIC· HS·DA · IS»</b> '
            '= «Moneta Glückstadiensis 1659 · <i>XVI as one Reichsthaler '
            'Holstein-Dänisch</i> · IS (mintmaster Jacob Schwiegelt)». '
            'The coin declares itself <b>«1/16 Reichsthaler Holstein-Dänisch»</b> — '
            'not «Speciedaler» or «Skilling Lybsk». The modern label '
            '«1/16 Speciedaler» is a historiographical assignment to the 9¼-Fuß '
            "(Holstein's Thaler Species standard before 1726); the accounting "
            'equivalent «3 Schilling lübisch» arises from the parallel Hanseatic '
            'reckoning and <i>does not appear on the coin itself</i>.'
        ),
        "uk": (
            'Аверс «FRIDERICK 3 D·G: D·N·R·» з коронованим погруддям · '
            'реверс <b>«MONNO GLVCKSTAD 1659 · XVI · E·REIC· HS·DA · IS»</b> '
            '= «Moneta Glückstadiensis 1659 · <i>XVI ein Reichsthaler '
            'Holstein-Dänisch</i> · IS (монетник Jacob Schwiegelt)». '
            'Сама монета декларує себе як <b>«1/16 Reichsthaler Holstein-Dänisch»</b> — '
            'а не як «Speciedaler» чи «Skilling Lybsk». Сучасна назва '
            '«1/16 Speciedaler» — це історіографічне віднесення до 9¼-Fuß '
            '(гольштинського стандарту Thaler Species до 1726); розрахунковий '
            'еквівалент «3 Schilling lübisch» виникає з паралельного ганзейського '
            'рахунку і <i>на самій монеті не зазначений</i>.'
        ),
    },

    "km-82-1,-chr-v-1694": {
        "en": (
            'Reverse legend (all year issues): «*VIII* SKILLING DANSKE» + the year · '
            'the value stated on the coin is <b>solely «8 Skilling Danske»</b>. '
            'The accounting equivalents (1/12 Speciedaler on the basis of '
            '60 Skilling Danske; ≈ 4 Schilling lübisch under the Hanseatic '
            'reckoning) <i>do not appear on the coin</i>. · '
            'Obverse «C5 · PIETATE & IVSTITIA» with a crowned monogram · '
            '82.1 (1694): inscription counter-clockwise · '
            '82.2 (1694, 1695, 1697): inscription clockwise · '
            'Glückstadt mint · the coin\'s actual fine content already matches '
            'the 11⅓-Fuß (20.63435 g per Rigsdaler Courant) — a forerunner '
            'of the later Kurantmøntfod of 1726.'
        ),
        "uk": (
            'Легенда реверса (усі річні випуски): «*VIII* SKILLING DANSKE» + рік · '
            'на монеті вказано <b>виключно «8 Skilling Danske»</b>. '
            'Розрахункові еквіваленти (1/12 Speciedaler за 60 Skilling Danske; '
            '≈ 4 Schilling lübisch за ганзейським рахунком) <i>на монеті '
            'не зазначені</i>. · Аверс «C5 · PIETATE & IVSTITIA» '
            'із коронованим монограмом · 82.1 (1694): напис проти годинникової '
            'стрілки · 82.2 (1694, 1695, 1697): напис за годинниковою стрілкою · '
            'монетний двір Glückstadt · фактичний вміст чистого срібла вже '
            'відповідає 11⅓-Fuß (20,63435 г на Rigsdaler Courant) — попередник '
            'пізнішого Kurantmøntfod 1726 року.'
        ),
    },

    "km-63-chr-v-1672": {
        "en": (
            '= 1 Krone = ⅔ Speciedaler (nominal) · obverse «PIETATE ET IUSTITIA» · '
            'reverse «IIII · MARCK · DANSKE» · <b>Glückstadt Kronen-Fuß</b>: '
            '4 Marck Danske as the ⅔ Speciedaler equivalent, but with reduced '
            'fineness (.671 instead of the pure Thaler Species silver .875) — '
            'hence the actual fine weight of ca. 14.94451 g instead of '
            '16.85449 g. The Colleconline specimen at 20.9 g carries jewellery '
            'traces and is therefore worn; the Numista standard weight for '
            "Christian V's Krone (KM# 370, 378 etc.) confirms 22.272 g."
        ),
        "uk": (
            '= 1 Krone = ⅔ Speciedaler (номінально) · аверс «PIETATE ET IUSTITIA» · '
            'реверс «IIII · MARCK · DANSKE» · <b>ґлюкштатський Kronen-Fuß</b>: '
            '4 Marck Danske як еквівалент ⅔ Speciedaler, але зі зниженою пробою '
            '(.671 замість чистого срібла Thaler Species .875) — звідси фактична '
            'чиста вага ≈ 14,94451 г замість 16,85449 г. Екземпляр Colleconline '
            'вагою 20,9 г має сліди ювелірної обробки і тому зношений; '
            'стандартна вага Numista для Krone Кристіана V (KM# 370, 378 та ін.) '
            'підтверджує 22,272 г.'
        ),
    },

    "km-70-1-chr-v-1680": {
        "en": (
            'Mintmaster Christopher Woltereck (CW) · «<i>The Ducats struck in '
            'Glückstadt differ from the ones struck in Copenhagen in being '
            'minted for regular trade use rather than just as occasion coins</i>» '
            '(Bruun Part II, lot 13180). Note: <b>the Glückstadt ducats continue '
            'to follow the Reichsdukatenfuß, not the Kronemønt debasement</b> — '
            'gold resisted debasement better than silver (cf. the 1619 Gold '
            'Krone: «<i>the gold issues kept their value</i>»).'
        ),
        "uk": (
            'Монетник Christopher Woltereck (CW) · «<i>The Ducats struck in '
            'Glückstadt differ from the ones struck in Copenhagen in being '
            'minted for regular trade use rather than just as occasion coins</i>» '
            '(Bruun, частина II, лот 13180). Важливо: <b>дукати Glückstadt '
            'продовжують тримати Reichsdukatenfuß, а не знецінення Kronemønt</b> — '
            'золото противилося знеціненню краще за срібло (пор. золота Krone '
            '1619: «<i>the gold issues kept their value</i>»).'
        ),
    },

    "km-x000-1752": {
        "en": (
            '«48 SCHILLING COURANT» — an alternative denomination legend for the '
            '11⅓-Fuß Kurantdaler expressed in Lübeck-Hanseatic reckoning '
            '(48 ßl. lüb. = 3 Mark lübisch) · mint mark JJJ · auction record '
            'Tietjen & Co. 110 (2013) · <b>Note:</b> the fine weight remains that '
            'of the 11⅓-Fuß (~20.63435 g); <i>not</i> the post-1788 Reichsthaler '
            'Sch.-H. Courant (⅘ Thaler Species, 20.22538 g = the 11⁹⁄₁₆-Fuß '
            'equivalent).'
        ),
        "uk": (
            '«48 SCHILLING COURANT» — альтернативний напис номіналу для '
            '11⅓-Fuß Kurantdaler у любецько-ганзейському рахунку (48 ßl. lüb. '
            '= 3 Mark lübisch) · монетний знак JJJ · аукціонна довідка '
            'Tietjen & Co. 110 (2013) · <b>Важливо:</b> чиста вага лишається за '
            '11⅓-Fuß (~20,63435 г); <i>це не</i> перевизначений після 1788 '
            'Reichsthaler Sch.-H. Courant (⅘ Thaler Species, 20,22538 г = '
            'еквівалент 11⁹⁄₁₆-Fuß).'
        ),
    },

    "km-x000-fr-iii-1644": {
        "en": (
            '«IS» initials of Jacob Schwieger (mint lessee 1644–1660); '
            'reverse «IIII · MARCK · DANSKE»; obverse with a large royal '
            'monogram · year on the reverse circumscription · .671 · 22.272 g · '
            '⌀ ~40 mm (Numista standard for all Frederik III types 1644–60) · '
            "<b>Glückstadt Kronen-Fuß</b>: the Krone as a ⅔ Speciedaler at "
            'reduced fineness (.671 instead of the pure Thaler Species silver '
            '.875) — a lighter large petty coin.'
        ),
        "uk": (
            'Ініціали «IS» Jacob Schwieger (орендар монетного двору 1644–1660); '
            'реверс «IIII · MARCK · DANSKE»; аверс із великим королівським '
            'монограмом · рік у реверсовій коловій легенді · .671 · 22,272 г · '
            '⌀ ~40 мм (стандарт Numista для всіх типів Фредеріка III 1644–60) · '
            '<b>ґлюкштатський Kronen-Fuß</b>: Krone як ⅔ Speciedaler зі зниженою '
            'пробою (.671 замість чистого срібла Thaler Species .875) — легша '
            'велика розмінна монета.'
        ),
    },

    "km-73-fr-iv-1698": {
        "en": (
            'Mintmaster Hans Heinrich Lüders (HHL) · the reverse shows the '
            '<b>Stapelholm fortress</b> between the rivers Eider and Treene near '
            'Friedrichstadt · Bruun lot 14227 — NGC AU-58 · struck from the same '
            'dies as the silver striking in 8 Schilling (Lange-430B) · slightly '
            'reduced weight — possibly a political motive.'
        ),
        "uk": (
            'Монетник Hans Heinrich Lüders (HHL) · реверс зображує '
            '<b>Стапельгольмську фортецю</b> між річками Ейдер і Трене поблизу '
            'Фрідріхштадта · Bruun, лот 14227 — NGC AU-58 · карбувалася тими ж '
            'штампами, що й срібний відбиток номіналом 8 Schilling (Lange-430B) · '
            'трохи знижена вага — можливо, з політичних причин.'
        ),
    },

    "km-176-fr-iv-1700": {
        "en": (
            '<b>Anomalous issue</b>: rough weight 26.14 g ≠ the 29.20 g of the '
            'Thaler Species of 1697/1698. If fineness .875 is assumed: 22.87 g '
            'fine → ≈ 10.23-Thalerfuß, <u>not the 9¼-Fuß</u>. Possibly a '
            "transition by Friedrich IV to a «reduced Tönning Thaler Species» in "
            'the last year of his reign before his death in 1702; the primary '
            'specification (mint ordinance) is <i>not available online</i> · '
            'Bruun lot 14231.'
        ),
        "uk": (
            '<b>Аномальне карбування</b>: повна вага 26,14 г ≠ 29,20 г у '
            'Thaler Species 1697/1698. Якщо припустити пробу .875: 22,87 г '
            'чистого → ≈ 10,23-Thalerfuß, <u>не 9¼-Fuß</u>. Ймовірно, перехід '
            'Фрідріха IV до «зниженого тьоннінзького Thaler Species» в останній '
            'рік правління перед смертю 1702 року; первинна специфікація '
            '(монетний ордонанс) <i>у мережі не доступна</i> · Bruun, лот 14231.'
        ),
    },

    "km-154-fr-vi-1816": {
        "en": (
            'Reverse legend (Numista KM-154, Frederik VI 1816–1818, ma-shops '
            '44148, HA 1818): <b>«*16* REICHS=BANK SCHILLING. [year]. [MM]»</b> '
            '+ the mintmaster initials (MF, CB, IFF). <u>The only denomination '
            'on the coin</u> — <b>no dual denomination</b> (unlike KM# 733 from '
            '1842 onward). The accounting equivalence 16 RBS = 5 Schilling '
            'Courant = 1/12 Thaler Species (silver parity via fineness .500) '
            '<i>does not appear on the coin</i>; it is only the parallel '
            'reckoning used in the Holstein Courant system. Mintmaster from '
            '1831: Johann Friedrich Freund (I.F.F.). The systematic dual '
            'inscription was only introduced by the <b>decree of 18 Dec. 1841</b>.'
        ),
        "uk": (
            'Легенда реверса (Numista KM-154, Frederik VI 1816–1818, ma-shops '
            '44148, HA 1818): <b>«*16* REICHS=BANK SCHILLING. [рік]. [MM]»</b> '
            '+ ініціали монетника (MF, CB, IFF). <u>Єдиний номінал на монеті</u> '
            '— <b>без подвійної деномінації</b> (на відміну від KM# 733 з 1842 '
            'року). Розрахункова еквівалентність 16 RBS = 5 Schilling Courant = '
            '1/12 Thaler Species (срібний паритет через пробу .500) <i>на монеті '
            'не зазначена</i>; це лише паралельний рахунок у гольштинській '
            'системі Courant. Монетник з 1831: Johann Friedrich Freund (I.F.F.). '
            'Систематичний подвійний напис було запроваджено лише <b>декретом '
            '18 грудня 1841</b>.'
        ),
    },

    "km-154a-fr-vi-1831": {
        "en": (
            'Reverse legend (Numista KM-154a, Frederik VI 1831–1839): '
            '<b>«*16* REICHS=BANK SCHILLING. [year]. I.F.F.»</b>. Later variant '
            "of Frederik VI's issue (reigned until 3 Dec. 1839) · ⌀ 23 mm "
            '(Numista). <u>No dual denomination</u> — only «Reichsbank '
            'Schilling» appears on the coin, in line with KM# 154. The dual '
            'inscription «N Rigsbankskilling / N Schilling Courant» was only '
            'introduced by the <b>decree of 18 Dec. 1841</b> under Christian '
            'VIII (first appearing on KM# 721, 733 from 1841/42).'
        ),
        "uk": (
            'Легенда реверса (Numista KM-154a, Frederik VI 1831–1839): '
            '<b>«*16* REICHS=BANK SCHILLING. [рік]. I.F.F.»</b>. Пізніший '
            'варіант випуску Фредеріка VI (правив до 3 грудня 1839) · ⌀ 23 мм '
            '(Numista). <u>Без подвійної деномінації</u> — на монеті лише '
            '«Reichsbank Schilling», як у KM# 154. Подвійний напис '
            '«N Rigsbankskilling / N Schilling Courant» запровадили лише '
            '<b>декретом 18 грудня 1841</b> за Кристіана VIII (уперше зʼявляється '
            'на KM# 721, 733 з 1841/42).'
        ),
    },

    "km-152-fr-vi-1816": {
        "en": (
            'Reverse legend (Numista KM-152, Frederik VI 1819): '
            '<b>«*8* REICHS= BANK SCHILLING. 1819. I.F.F.»</b> — '
            '<u>the only denomination on the coin</u>. «2½ Schilling Courant» '
            'is the accounting equivalent (1/12 Rigsbankdaler = 1/24 '
            'Thaler Species = 2½ Sch.C.) and <i>does not appear on the coin</i>. '
            'Obverse: a crowned shield with the Holstein arms · mintmaster '
            'I.F.F. (Johann Friedrich Freund).'
        ),
        "uk": (
            'Легенда реверса (Numista KM-152, Frederik VI 1819): '
            '<b>«*8* REICHS= BANK SCHILLING. 1819. I.F.F.»</b> — '
            '<u>єдиний номінал на монеті</u>. «2½ Schilling Courant» — це '
            'розрахунковий еквівалент (1/12 Rigsbankdaler = 1/24 Thaler Species '
            '= 2½ Sch.C.), <i>на монеті не зазначений</i>. Аверс: коронований '
            'щит із гольштинським гербом · монетник I.F.F. (Johann Friedrich '
            'Freund).'
        ),
    },
}


def main() -> int:
    path = Path("data/locations/schleswig.yml")
    yaml = YAML()
    yaml.preserve_quotes = True
    yaml.width = 10000
    yaml.indent(mapping=2, sequence=4, offset=2)
    data = yaml.load(path.read_text(encoding="utf-8"))

    patched = 0
    for coin in data.get("coins", []) or []:
        cid = coin.get("id")
        if cid in NOTES:
            note = coin.setdefault("note", {})
            for lang, text in NOTES[cid].items():
                text = text.strip()
                note[lang] = LiteralScalarString(text) if "\n" in text else text
                patched += 1

    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(data, f)
    print(f"Applied manual translations to {patched // 2} coins ({patched} fields).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
