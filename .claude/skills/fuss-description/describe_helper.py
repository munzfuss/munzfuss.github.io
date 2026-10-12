#!/usr/bin/env python3
"""Mechanical signal-scan for the `fuss-description` skill.

Surfaces CANDIDATE violations + presence-signals the agent uses to finalise the
X/10 rubric (see SKILL.md). It does NOT compute the final score — the score is
agent judgment (reading + source-verification per §0/§0b). The helper's job is to
make the scan reproducible: list bare metrics (C4), specimen intrusions (C6),
citation coverage (C5), and founding/role/phase presence (C1/C2/C3), plus verify
each cited [ref:KEY] resolves.

Usage:
    python .claude/skills/fuss-description/describe_helper.py <fuss_key> [--lang de|en|uk] [--field description|card] [--location <loc>]
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
        r"S[øo]ldgold|mercenary|Repr[äa]sentation|daily|Tages|Prachtm[üu]nze|"
        # parade / show / pay coin, all four languages (Nobelfod «парадні монети»,
        # «Pragtmønter» was missed before 2026-10-12)
        r"Pragtm[øo]nt|Schaum[üu]nz|parade coin|show coin|presentation|парадн|"
        r"репрезентаці|монет\w* платні|platn|Sold|pay coin|L[øo]nning|Besoldung")
# specimen-level intrusions (§7a) — auction lots, single-piece data, uniqueness
SPECIMEN = (r"\bBruun[- ]?\d|Bruun coll|Bruun lot|\blot \d|Lot \d|Auktion|auction|"
            r"Hammerpreis|Zuschlag|hammer|NGC|PCGS|MS-?\d|VF-?\d|XF-?\d|"
            r"\bunik\b|einzige[sr]?\b|sole surviving|only known|unique specimen|"
            r"einziges? bekannt|Kabinettst[üu]ck|cabinet|провенанс|provenance|"
            r"aukc|унікальн|єдиний відом|цабінет")
# catalogue-index mentions IN THE PROSE (§7a / user-2026-07-03): naming a specific
# catalogue number — «Hede f2h3», «Galster 131», «KM 138.2» — is specimen/issue-level
# detail that belongs on the coin ROW, not in a system-level fuss description. The
# attestation still travels via <sup>[ref:KEY]</sup> (stripped before this scan), so
# a prose hit here is a real C6 intrusion, not a citation. Requires a catalogue-name
# prefix, so «Frederik II» / «72 Stück» / «18 Karat» do NOT match.
CATALOGUE = (r"\b(?:Hede|Galster|Sieg|Schou|Lange|Behrens|Bendixen|Gaedechens|"
             r"Jesse|Davenport|Dav|Friedberg|Fr|KM|N#)[\s-]?[a-z]?\d[\w./+-]*")
# one-issue mintmaster attribution (§7a: mintmaster initials/name = specimen-level)
MINTMASTER = (r"Mzm\.?\s*[A-ZÆØÅ]|[Mm]intmaster\s+[A-ZÆØÅ]|"
              r"монетмейстер\s+[A-ZÀ-ÿ]|M[üu]nzmeister\s+[A-ZÆØÅ]")
# bare-metric numbers (C4) — flagged, agent checks if law-anchored / whole-standard
METRIC = (r"\d+[.,]\d+\s*g\b|\d+[.,]?\d*\s*‰|(?<![\d.])\.\d{3}\b|"
          r"\d+[½¼¾]?\s*Karat|\d+[.,]\d+\s*г\b|\d+[.,]\d+\s*grain")
# mintage figures — a count of pieces STRUCK (account, ordinance). Forbidden in the
# fuss description (§7a), ALLOWED in a phase description (curator 2026-10-12). Flagged
# only in a sentence with a minting / account word and a thousands-sized number, so
# «71⅓ штуки з марки» (pieces per mark) and bare years do not match.
MINT_WORD = (r"викарбува|карбува|рахун|geprägt|ausgeprägt|Auflage|Rechnung|struck|minted|"
             r"mintage|account|udm[øo]nt|pr[æa]get|regnskab|наклад")
BIG_NUMBER = r"\b\d{1,3}(?:[ \u00a0\u202f.]\d{3})+\b|\b\d{5,}\b"
# survivor / known-specimen counts — forbidden in EVERY layer (curator 2026-10-12):
# «N known specimens», «2 Exemplare bekannt», «збереглося 3 екземпляри», and the
# zero case «no specimen survives / жодного екземпляра не збереглося».
SURVIVORS = (r"\d+\s*(?:bekannte?n?\s+)?(?:Exemplar\w*|specimens?|eksemplar\w*|екземпляр\w*)|"
             r"(?:kein|keines|no|intet|ingen|жодн\w*)\s+(?:\w+\s+){0,2}"
             r"(?:Exemplar\w*|specimens?|eksemplar\w*|екземпляр\w*)")
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


# A period that ends an abbreviation does not end a sentence: «1496 р. карбує»,
# «1563–1564 рр.», «S. 153», «Frederik I. schlägt», «ca. 1497». Splitting there cut
# «Король Hans 1496 р.» off from its citation and reported it as uncited (2026-10-12).
ABBREV_END = re.compile(
    r"(?:\b(?:р|рр|ст|с|т|розд|прав|S|s|p|pp|bd|Bd|Kap|kap|ch|vol|ca|c|Mzm|Nr|nr|No|"
    r"z|B|vgl|cf|bzw|etc|f|ff|St|Hl|kgl|d|Chr)|\b[IVX]{1,4}|\b\d{1,2})\.$")


def sentences(t):
    txt = re.sub(r"<br\s*/?>", " | ", t)
    txt = re.sub(r"<[^>]+>", "", txt)
    txt = re.sub(r"\[ref:[^\]]+\]", "¤", txt)  # ¤ marks a citation slot
    # «;» joins clauses of ONE sentence whose citation often stands at its end
    # («X започатковує …; за Galster, … ¤») — not a split point.
    raw = re.split(r"(?<=[.!?])\s+|·|\|", txt)
    parts = []
    for s in raw:
        # merge only when the next part does NOT open a new sentence (lowercase or
        # digit start): «1496 р. карбує» merges, «… 1546 р. Карбування …» does not.
        if parts and ABBREV_END.search(parts[-1].rstrip()) and re.match(r"[\W_]*[a-zà-ÿа-яіїєґæøå\d¤]", s):
            parts[-1] = parts[-1].rstrip() + " " + s
        else:
            parts.append(s)
    return [s.strip() for s in parts if len(re.sub(r"\W", "", s)) > 12]


def cited_keys(t):
    keys = re.findall(r"\[ref:([a-z0-9\-]+)\]", t)
    keys += re.findall(r'href="#ref-pool-([\w\-]+)"', t)
    legacy = re.findall(r'href="#ref(\d+)"', t)
    return keys, legacy


def near_decree(text, span, window=90):
    s = max(0, span[0] - window); e = min(len(text), span[1] + window)
    return bool(DECREE_RE.search(text[s:e]))


def scan_lang(desc, refkeys, layer="description"):
    """`layer` is «description» (the fuss's system-level prose) or «phase» (a phase
    description in «details»). Mintage figures cost C6 only in the description."""
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
    hits["c6_catalogue"] = sorted(set(re.findall(CATALOGUE, plain)))
    hits["c6_mintmasters"] = sorted(set(re.findall(MINTMASTER, plain)))
    hits["c6_survivors"] = sorted(set(re.findall(SURVIVORS, plain, re.I)))
    mint = []
    for s in sentences(desc):
        if re.search(MINT_WORD, s, re.I):
            mint += re.findall(BIG_NUMBER, s)
    hits["mintage"] = mint                       # informational in a phase
    hits["c6_mintage"] = mint if layer == "description" else []
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


CARD_FIELD = "grundwerte.rechnungsfraktionen (card text)"


def get_description(f, force=None):
    """Return (text_dict, source_label) for a fuss.

    A fuss's description prose lives in one of two places:
      * `description` — the legacy field (default; kept until a fuss is migrated);
      * `grundwerte.rechnungsfraktionen` — the card text, where the description of a
        migrated fuss now lives (nobel_fod, rhinsk_gylden_fod so far; the rest follow as
        each is revised). For a fuss that has NOT been migrated this field holds the
        accounting-fractions block, which is not a description.
    Default: `description` when present; else the card text, but only for a fuss flagged
    `description_in_card: true` in fuesse.yml (without the flag the card text is the
    accounting-fractions block, not a description). `force` ('description' or 'card')
    overrides.
    """
    gw = f.get("grundwerte") if isinstance(f.get("grundwerte"), dict) else {}
    card = gw.get("rechnungsfraktionen") if isinstance(gw.get("rechnungsfraktionen"), dict) else None
    desc = f.get("description") if isinstance(f.get("description"), dict) else None
    if force == "description":
        return desc, "description"
    if force == "card":
        return card, CARD_FIELD
    if desc:
        return desc, "description"
    if f.get("description_in_card") is True and card:
        return card, CARD_FIELD
    return None, None


LOCATIONS_DIR = os.path.join(REPO, "data/v2/locations")


def locations_with_fuss(fuss):
    """Location ids whose `phases` block has this fuss (sorted)."""
    import glob
    out = []
    for fp in sorted(glob.glob(os.path.join(LOCATIONS_DIR, "*.yml"))):
        d = load(fp)
        ph = d.get("phases") if isinstance(d, dict) else None
        if isinstance(ph, dict) and ph.get(fuss):
            out.append(os.path.basename(fp)[:-4])
    return out


def pick_lang(t, lang):
    if isinstance(t, dict):
        return t.get(lang) or t.get("en") or t.get("de") or next(iter(t.values()), "")
    return t or ""


def phase_layers(fuss, f, loc, refkeys, lang):
    """The per-phase layers of ONE scored variant: the Grundwerte rows (left block of the
    card) and the phase descriptions of ONE location page. C4 is NOT applied to either:
    numbers in the rows are the card's data, and phase prose is judged for sourcing/specimens
    only."""
    gw = f.get("grundwerte") if isinstance(f.get("grundwerte"), dict) else {}
    rows = gw.get("rows") or []
    print(f"====== [{lang}] LEFT BLOCK of the card — Grundwerte rows ({len(rows)}) ======")
    print("  (numbers here are the card's data: C4 does not apply; read these for C3 phase "
          "differentiators and C1 decree rows)")
    for r in rows:
        key = strip_tags(pick_lang(r.get("key"), lang)).strip()
        val = pick_lang(r.get("value"), lang)
        kind = r.get("kind") or "phase"
        cites = len(cited_keys(val)[0])
        spec = sorted(set(re.findall(SPECIMEN, strip_tags(val), re.I)))
        print(f"  [{kind:6}] {key[:96]}   (cites={cites}{', SPECIMEN-FLAG ' + str(spec) if spec else ''})")
    print()
    if not loc:
        print("====== PHASE DESCRIPTIONS (details) — NOT scored: no location chosen ======")
        locs = locations_with_fuss(fuss)
        print(f"  This fuss has phases on: {', '.join(locs) or 'no location'}. A scoring covers ONE "
              f"description variant — pass --location <loc> for the page being rated.")
        print()
        return
    d = load(os.path.join(LOCATIONS_DIR, loc + ".yml"))
    phs = (d.get("phases") or {}).get(fuss) or []
    print(f"====== [{lang}] PHASE DESCRIPTIONS (details) — location '{loc}' ({len(phs)} phase(s)) ======")
    if not phs:
        print(f"  '{fuss}' has no phases on '{loc}'.")
    for p in phs:
        title = strip_tags(pick_lang(p.get("title"), lang))
        desc = pick_lang(p.get("description"), lang)
        sc = scan_lang(desc, refkeys, layer="phase") if desc else None
        print(f"  Phase {p.get('id')}: {title[:90]}")
        if not desc:
            print("     (no description)"); continue
        print(f"     C5 cites={sc['c5_cite_count']}/{sc['c5_sentences']} sentence(s)"
              + (f"  UNRESOLVED={sc['c5_unresolved_refs']}" if sc['c5_unresolved_refs'] else "")
              + (f"  uncited-claims={len(sc['c5_uncited_claim_sentences'])}" if sc['c5_uncited_claim_sentences'] else ""))
        c6 = sc['c6_specimens'] + sc['c6_catalogue'] + sc['c6_mintmasters'] + sc['c6_survivors']
        print(f"     C6 flags={c6 or 'none'}   C1: decree={sc['c1_decree']} ruler={sc['c1_ruler']} "
              f"year={sc['c1_year']}   C2 role tokens={sc['c2_role_tokens'] or '—'}")
        if sc['mintage']:
            print(f"     mintage figures {sc['mintage']} — allowed in a phase description (not a C6 hit)")
    print()


def main():
    if "--list" in sys.argv:
        data = load(FUESSE)
        for k in data:
            nm = (data[k].get("name") or {}).get("en", "") if isinstance(data[k], dict) else ""
            if isinstance(data[k], dict):
                d, src = get_description(data[k])
                tag = "[desc]" if src == "description" else ("[card]" if src else "[no desc]")  # [card] = description lives in the card text (no legacy field)
            else:
                tag = "[no desc]"
            print(f"  {k:26} {tag:10} {nm}")
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
    force = None
    if "--field" in sys.argv:
        force = sys.argv[sys.argv.index("--field") + 1]
    desc, src = get_description(f, force)
    if not desc:
        print(f"fuss '{fuss}' has NO description text (neither `description` nor a card-text description "
              f"(`description_in_card: true` + `grundwerte.rechnungsfraktionen`)) — nothing to score (C1-C6 all 0)."); return
    refkeys = set(load(REFS_POOL).keys()) if os.path.exists(REFS_POOL) else set()

    name = (f.get("name") or {}).get("en") or fuss
    print(f"FUSS: {fuss} — {name}")
    print(f"  description read from: {src}")
    if force == "card" and not f.get("description_in_card"):
        print("  NOTE: --field card forced on a fuss NOT flagged `description_in_card: true`; "
              "the card text is probably the accounting-fractions block, not a description.")
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
        c6all = h['c6_specimens'] + h['c6_catalogue'] + h['c6_mintmasters'] + h['c6_survivors'] + h['c6_mintage']
        print(f"  C6 specimen flags   : {c6all or 'none (good)'}")
        if h['c6_catalogue'] or h['c6_mintmasters']:
            print(f"     catalogue-in-prose: {h['c6_catalogue'] or '—'}   "
                  f"mintmaster: {h['c6_mintmasters'] or '—'}")
        print(f"     <- auction/lot/grade/unique + catalogue-number-in-prose (Hede f2h3, Galster 131) "
              f"+ one-issue mintmaster + mintage figures + survivor counts ALL count as §7a C6 "
              f"intrusions in a fuss description (phase descriptions may carry mintage, not survivor counts)")
        print()
    loc = None
    if "--location" in sys.argv:
        loc = sys.argv[sys.argv.index("--location") + 1]
    else:
        locs = locations_with_fuss(fuss)
        if len(locs) == 1:
            loc = locs[0]
    phase_layers(fuss, f, loc, refkeys, (only or "uk"))
    print("Apply the SKILL.md rubric to finalise X/10. Signals are candidates, not verdicts —"
          " verify sources (§0b) before deducting or awarding C5.")


if __name__ == "__main__":
    main()
