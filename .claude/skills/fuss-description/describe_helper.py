#!/usr/bin/env python3
"""Mechanical signal-scan for the `fuss-description` skill.

Surfaces CANDIDATE violations + presence-signals the agent uses to finalise the
X/10 rubric (see SKILL.md). It does NOT compute the final score — the score is
agent judgment (reading + source-verification per §0/§0b). The helper's job is to
make the scan reproducible: list bare metrics (C4), specimen intrusions (C6),
citation coverage (C5), and founding/role/phase presence (C1/C2/C3), plus verify
each cited [ref:KEY] resolves.

Usage:
    python .claude/skills/fuss-description/describe_helper.py <fuss_key> [--lang de|en|uk]
    python .claude/skills/fuss-description/describe_helper.py --list         # all fuss keys
"""
import sys, re, os, json

try:
    import yaml
except ImportError:
    print("PyYAML required (.venv/bin/python)."); sys.exit(2)

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
FUESSE = os.path.join(REPO, "data/shared/fuesse.yml")
REFS_POOL = os.path.join(REPO, "data/shared/refs_pool.yml")

# --- signal vocabularies -------------------------------------------------------
DECREE = (r"Reichsabschied|Reichsm[üu]n[tz]?zordnung|M[øo]ntordning|Forordning|"
          r"Ordnung|Plakat|Vertrag|Con[vw]ention|Konvention|Reze[ßss]+|"
          r"M[üu]n[tz]?zvertrag|Bankordnung|Abschied|Lovkompleks|Bankvaluta|Edikt|"
          r"Patent|Mandat|указ|ордонанс|декрет|розпорядженн|конвенц")
RULER = (r"\b(Hans|Christian|Frederik|Friedrich|Johann|Karl|Carl|Ernst|Otto|"
         r"Adolf|Adolph|Georg|Wilhelm|Heinrich|Christof|Kristian|Фредерік|"
         r"Кристіан|Крістіан|König|Herzog|Kurf[üu]rst|Kaiser|король|герцог)\b")
ROLE = (r"Handelsm[üu]nze|trade coin|Kurantm[üu]nze|Scheidem[üu]nze|Prestige|"
        r"Reserve|Tarif|Bancovaluta|Banco|Rechnungs|accounting|Umlauf|circulation|"
        r"Leitw[äa]hrung|Anker|prestige|торгова|обіг|розрахунков|тариф|"
        r"S[øo]ldgold|mercenary|Repr[äa]sentation|daily|Tages|Prachtm[üu]nze")
# specimen-level intrusions (§7a) — auction lots, single-piece data, uniqueness
SPECIMEN = (r"\bBruun[- ]?\d|Bruun coll|Bruun lot|\blot \d|Lot \d|Auktion|auction|"
            r"Hammerpreis|Zuschlag|hammer|NGC|PCGS|MS-?\d|VF-?\d|XF-?\d|"
            r"\bunik\b|einzige[sr]?\b|sole surviving|only known|unique specimen|"
            r"einziges? bekannt|Kabinettst[üu]ck|cabinet|провенанс|provenance|"
            r"aukc|унікальн|єдиний відом|цабінет")
# bare-metric numbers (C4) — flagged, agent checks if law-anchored / whole-standard
METRIC = (r"\d+[.,]\d+\s*g\b|\d+[.,]?\d*\s*‰|(?<![\d.])\.\d{3}\b|"
          r"\d+[½¼¾]?\s*Karat|\d+[.,]\d+\s*г\b|\d+[.,]\d+\s*grain")
# claim verbs that usually need a citation (C5)
CLAIM = (r"founded|established|introduced|ordered|decreed|standardis|adopt|"
         r"served|functioned|role|because|prompted|led to|resulted|reform|"
         r"first|earliest|only|sole|codif|заснова|встанов|запровад|стандартиз|"
         r"слугува|роль|функці|причин|спричин|перш|найранlatest|єдин|реформ")
DECREE_RE = re.compile(DECREE, re.I)
CLAIM_RE = re.compile(CLAIM, re.I)


def load(p):
    with open(p) as f:
        return yaml.safe_load(f) or {}


def strip_tags(t):
    t = re.sub(r"<sup>.*?</sup>", " ¤ ", t)   # keep a citation marker ¤
    t = re.sub(r"\[ref:[^\]]+\]", " ¤ ", t)
    return re.sub(r"<[^>]+>", "", t)


def sentences(t):
    txt = re.sub(r"<[^>]+>", "", t)
    txt = re.sub(r"\[ref:[^\]]+\]", "¤", txt)  # ¤ marks a citation slot
    parts = re.split(r"(?<=[.!?])\s+|·|;|<br>|\|", txt)
    return [s.strip() for s in parts if len(re.sub(r"\W", "", s)) > 12]


def cited_keys(t):
    keys = re.findall(r"\[ref:([a-z0-9\-]+)\]", t)
    keys += re.findall(r'href="#ref-pool-([\w\-]+)"', t)
    legacy = re.findall(r'href="#ref(\d+)"', t)
    return keys, legacy


def near_decree(text, span, window=90):
    s = max(0, span[0] - window); e = min(len(text), span[1] + window)
    return bool(DECREE_RE.search(text[s:e]))


def scan_lang(desc, refkeys):
    hits = {}
    plain = strip_tags(desc)
    # C4 — bare metrics not near a decree
    bare = []
    for m in re.finditer(METRIC, desc):
        if not near_decree(desc, m.span()):
            bare.append(m.group(0))
    hits["c4_bare_metrics"] = bare
    # C6 — specimen intrusions. Scan the ref/tag-STRIPPED text: a citation KEY like
    # [ref:stacksbowers-bruun-1496-nobel] names a source, not a specimen in the prose.
    hits["c6_specimens"] = sorted(set(re.findall(SPECIMEN, plain, re.I)))
    # C5 — citations + uncited claim sentences
    keys, legacy = cited_keys(desc)
    unresolved = [k for k in keys if k not in refkeys]
    sents = sentences(desc)
    uncited_claims = [s for s in sents if CLAIM_RE.search(s) and "¤" not in s]
    hits["c5_cite_count"] = len(keys) + len(legacy)
    hits["c5_unresolved_refs"] = unresolved
    hits["c5_sentences"] = len(sents)
    hits["c5_uncited_claim_sentences"] = uncited_claims
    # C1 — founding presence
    hits["c1_decree"] = bool(DECREE_RE.search(plain))
    hits["c1_ruler"] = bool(re.search(RULER, plain))
    hits["c1_year"] = bool(re.search(r"\b1[45678]\d\d\b", plain))
    # C2 — role presence
    hits["c2_role_tokens"] = sorted(set(re.findall(ROLE, plain, re.I)))[:6]
    # C3 — phases
    ph = sorted(set(re.findall(r"Phase\s+([0IViv]+)|фаз[аи]\s+([0IViv]+)|Phase\s+(\d)", desc)))
    hits["c3_phase_markers"] = [x for t in ph for x in t if x]
    return hits


def main():
    if "--list" in sys.argv:
        data = load(FUESSE)
        for k in data:
            nm = (data[k].get("name") or {}).get("en", "") if isinstance(data[k], dict) else ""
            has = bool(isinstance(data[k], dict) and data[k].get("description"))
            print(f"  {k:26} {'[desc]' if has else '[no desc]':10} {nm}")
        return
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        print(__doc__); sys.exit(1)
    fuss = args[0]
    only = None
    if "--lang" in sys.argv:
        only = sys.argv[sys.argv.index("--lang") + 1]

    data = load(FUESSE)
    if fuss not in data:
        print(f"fuss '{fuss}' not found. Try --list."); sys.exit(1)
    f = data[fuss]
    desc = f.get("description")
    if not desc:
        print(f"fuss '{fuss}' has NO description field — nothing to score (C1-C6 all 0)."); return
    refkeys = set(load(REFS_POOL).keys()) if os.path.exists(REFS_POOL) else set()

    name = (f.get("name") or {}).get("en") or fuss
    print(f"FUSS: {fuss} — {name}")
    print(f"  metal={f.get('metal')}  grid={f.get('grid_stops')}/{f.get('grid_unit_name')}  "
          f"fineness_std={f.get('fineness_standard')}  phases_in_fractions_comments=?")
    print(f"  events: {', '.join(k for k in (f.get('events') or {}) if not k.endswith('_label'))}")
    print("  (events give founding/cessation years to cross-check C1)\n")

    langs = [only] if only else ["de", "en", "uk"]
    for l in langs:
        if l not in desc:
            print(f"[{l}] MISSING — C-scores 0 for this language"); continue
        print(f"====== [{l}] mechanical signals ======")
        h = scan_lang(desc[l], refkeys)
        print(f"  C1 founding present : decree={h['c1_decree']} ruler={h['c1_ruler']} year={h['c1_year']}")
        print(f"  C2 role tokens      : {h['c2_role_tokens'] or 'NONE (candidate gap)'}")
        print(f"  C3 phase markers    : {h['c3_phase_markers'] or 'none in prose'}")
        print(f"  C4 bare metrics     : {h['c4_bare_metrics'] or 'none (good)'}   "
              f"<- each must be a whole-standard law-anchored value or it costs C4")
        print(f"  C5 citations        : {h['c5_cite_count']} cite(s) / {h['c5_sentences']} sentence(s)")
        if h["c5_unresolved_refs"]:
            print(f"     !! UNRESOLVED refs (fix or add to refs_pool): {h['c5_unresolved_refs']}")
        if h["c5_uncited_claim_sentences"]:
            print(f"     candidate UNCITED claim sentences (C5/§0 — source or cut):")
            for s in h["c5_uncited_claim_sentences"][:8]:
                print(f"       · {s[:110]}")
        print(f"  C6 specimen flags   : {h['c6_specimens'] or 'none (good)'}   "
              f"<- auction/lot/grade/unique = §7a violation; catalogue TYPE refs (Hede 39) are OK")
        print()
    print("Apply the SKILL.md rubric to finalise X/10. Signals are candidates, not verdicts —"
          " verify sources (§0b) before deducting or awarding C5.")


if __name__ == "__main__":
    main()
