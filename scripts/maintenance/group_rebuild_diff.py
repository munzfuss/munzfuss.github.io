#!/usr/bin/env python3
"""READ-ONLY: sort every value that differs between the finals at a base
revision (main) and the rebuilt finals on disk into DECISION groups — the
curator walks the groups and settles each one's legal form.

Inputs are the two per-value listings this branch already produces, plus
the hand-edit survival audit:

    final_diff_candidates.py --base main --json CAND.json
    classify_self_union_diff.py CAND.json --base main --no-history --json CLS.json
    audit_final_edit_survival.py --json EDITS.json

Groups (letter = what the group means for the finals' legal form):

    A  nothing to decide — the rebuild is a gain or the same value in
       another form (a Danish note added, a canonical ruler, a relabel)
    B  garbage on the base — stale data the self-union kept alive; the
       rebuild is right (moved members, excluded stubs' citations, place
       names in `mintmaster`, class verification claims)
    C  keep — a curator value the rebuild cannot derive; needs a surface
       (hold, writer rule, merge decision, errata)
    D  V1 foundation record not carried — deferred by the curator
       («v1 поки не чіпаємо»), listed so it is not forgotten
    E  review — a change with no evidence either way yet

    .venv/bin/python scripts/maintenance/group_rebuild_diff.py CAND.json CLS.json EDITS.json \\
        --base main --md docs/plans/main_vs_rebuild_groups.md --json OUT.json
"""
from __future__ import annotations

import argparse
import collections
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

import yaml  # noqa: E402

_L = getattr(yaml, "CSafeLoader", yaml.SafeLoader)
V2 = ROOT / "data" / "v2"

CANON = re.compile(r"(Christian|Frederik|Hans|Christoffer|Erik|Oldenburg|Christopher|Valdemar|Margrete) [IVX]+\.")
ANNOT = re.compile(r"\(.*\)")
TYPO = re.compile(r"Frederikg|VVI|Christain|Frederick \w+ of Denmark")
PLACE = re.compile(r"^(Trankebar|Lübeck|Hamburg|Hamborg|Brunswick(-\w+)?|Oldenburg|Slesvig-Holsten|Gottorp|Bremen|"
                   r"Hessen|Hannover|Kopenhagen|Altona|Glückstadt|Schleswig|Holstein|Lauenburg|Osnabrück|Denmark|"
                   r"Norway|Sweden|Rantzau|Schaumburg|Pinneberg|Plön|Sonderburg|Glücksburg|Bremen-Verden|Fredriksborg|"
                   r"Hafnens|Danmark|Norge)$")
FLAGS = {"ruler_verified", "metal_verified", "fineness_verified", "weight_rough_verified",
         "diameter_mm_verified", "mint_verified", "verified", "year_verified"}
READINGS = {"weight_rough_g", "fineness", "diameter_mm"}
# final-only commits whose undone values are pipeline / bulk output, not a
# per-coin curator decision (they keep their natural group)
BULK = {"33e05e4", "43fe1be", "e210ed6", "a523b0f", "064bfe9", "7a831dc", "e8de501", "577ea14",
        "4093197", "05b5b5e", "e157ce2", "f58b867", "0e0e287", "91ca8b0", "51a609c"}
# the V1 restore commits (2026-05-24/27) and the V1 bootstrap: citations they put on finals
RESTORE = {"e210ed6", "e851d3f", "4831c21", "10850ab", "9cb33bd", "b9e45f7", "214f991"}
V1STYLE = re.compile(r"catalogue/pieces\d+\.html|/ danskmoent\.dk'|', 'ucoin'\)|', 'ucoin tid|', 'Numista'\)|ngccoin\.com/price-guide|"
                     r"coins\.ha\.com|coinvarieties|worldcoingallery|kuenker\.de|'KM-DK# |\('jesse'|'Hede / danskmoent|"
                     r"stacksbowers\.com/wp-content|\('bruun_lot'|\('bruun_(lot_no|page|collection_id|part)'")
BRUUN_ANCHORS = {"bruun_lot_no", "bruun_page", "bruun_collection_id", "bruun_part", "bruun_lot"}
TEMPLATE_MIN = 5   # a note text shared by this many base finals is a template, not curated prose

GROUPS = {
    # key: (class, title, legal form proposal)
    "A1-note-da-added": ("A", "verification_note: the class adds the Danish version",
                         "Nothing to decide — the final's stored note lacked `da`, the class note has it; de/en/uk identical."),
    "A2-ruler-canonical": ("A", "ruler: stage N canonical «Name Roman.»",
                           "Nothing to decide — the seed-level canonicalisation (stage N) reaching the final."),
    "A3-ruler-annotated-to-plain": ("A", "ruler: annotated English form → the seed's plain form",
                                    "Nothing to decide — «John Frederick (Johann Friedrich)» → «Johann Friedrich» is the project's standard spelling; confirm the list."),
    "A4-relabel": ("A", "sources: the same url under another ref text",
                   "Nothing to decide — no citation lost; the class's ref text is the canonical one."),
    "A5-gain": ("A", "values the rebuild adds with no removed counterpart",
                "Nothing to decide — class data the self-union never let through."),
    "B1-excluded-stub-citations": ("B", "citations of excluded KMM stubs (scope member)",
                                   "Garbage on the base — the curator excluded these undocumented stubs 2026-10-16/20; only the self-union kept their citations on the documented coin's final."),
    "B2-moved-to-another-final": ("B", "values of members that now live in another final",
                                  "Garbage on the base — the value is rendered on the member's current final (S-moved; no_merge cases confirmed by decision)."),
    "B3-recorded-removal": ("B", "values a recorded removal already took off",
                            "Garbage on the base — `_recorded_removals` / retractions reproduce without the ledger entry being re-applied."),
    "B4-mintmaster-place": ("B", "mintmaster: a place or entity name in the mintmaster field",
                            "Garbage on the base — V1 bootstrap residue («Trankebar» ×74, «Lübeck», «Brunswick-Wolfenbüttel»); the class has no mintmaster."),
    "B5-covered-other-form": ("B", "values the class carries in another form",
                              "Garbage on the base — same catalogue number in another register / sub-variant, same year inside a range, same reading under another label."),
    "B6-flag-class-claim": ("B", "`*_verified` true → the class's false",
                            "Accept the class's claim — the final's `true` had no member attesting it (2026-10-06 `_members_decline` rule); the value renders with (?) instead of as verified. A hold is the exception, per case."),
    "D6-v1-values-on-promoted": ("D", "mint / metal / inscriptions on promoted finals, migrated from purged V1 foundations",
                                 "Deferred with D3/D5, but visible — V1 curator values (P3 migration) no class carries: the inscriptions are curated V1 prose, and the finals that lose `metal` / `mint` render an empty column; a hold on the final keeps them until the harvest covers them."),
    "B8-bruun-anchor": ("B", "catalog: the Bruun anchor specimen (lot / page / collection id) differs",
                        "Accept the class's anchor — `bruun_*` are scalar fast-lookup anchors (§9a); the rebuilt final still cites Bruun in `sources`, so no specimen is lost. An anchor rule (earliest lot / best grade) can be fixed in absorb if the choice should be deterministic."),
    "B9-note-template-swap": ("B", "verification_note: one generated template replaced by another",
                              "Nothing lost — absorb's promotion boilerplate («Hede seed: … still pending») vs the class's source template (IKMK / KMM / Numista record); both are generated. The hand-backfilled `da` is replaced by the class template's own `da`."),
    "C0-hand-edit": ("C", "a hand edit on the final (per commit)",
                     "Keep — needs the surface named per commit below (hold / writer rule / merge decision / errata)."),
    "C1-nominal-form": ("C", "nominal: the final's form vs the class's form",
                        "Decide per pair — the writer's nominal normalisation (stage N) or a hold on the final; several class forms are junk («1 Ducat (3.5)»)."),
    "C2-ruler-regression": ("C", "ruler: an annotated or misspelt source form comes back",
                            "Keep the canonical form — extend `canonical_ruler_display` to the annotated Danish-king forms; the two KMM typos («Frederikg 4», «Frederik VVI») → KMM builder errata."),
    "C3-ruler-lost": ("C", "ruler: the class has none, the final had one",
                      "Keep — single-source classes (NGC, IKMK, Bruun, KMM) whose builder sets no ruler; a writer rule (ruler from the title / reign) or a hold on the final."),
    "C4-note-da-lost": ("C", "verification_note: the final's Danish version is not in the class",
                        "Keep — the hand backfill of `da`; the class's note template for that source needs a `da` version."),
    "C5-note-curated-text": ("C", "verification_note: curated prose replaced by a class template",
                             "Keep — the base note is not a template (fewer than 5 finals share it); a hold on `verification_note`, or the text belongs on the seed."),
    "C6-mintmaster-name": ("C", "mintmaster: a real name the class does not carry",
                           "Keep — gap-filled from members (11f2f2a) or V1; a hold, or the member that carried it must be found."),
    "C7-hand-deletion-returns": ("C", "a value a hand edit deleted comes back from the class",
                                 "Keep the deletion — the class still carries the residue: a merge decision (split) / seed errata, or absorb applies `kind: field` ledger entries at enrichment."),
    "D1-v1-twin": ("D", "V1 foundation twinning a harvested seed's final",
                   "Deferred — fold the twin into the harvested final (merge decision) and the stale copy goes."),
    "D2-v1-memberless": ("D", "memberless V1 foundation: its own record",
                         "Deferred — 16 V1-only + 16 with a catalogue candidate; carry the own record (`_FOUNDATION_OWN`), merge, or exclude."),
    "D3-v1-uncovered": ("D", "V1 foundation sources / catalog the class does not carry",
                        "Deferred — curator 2026-10-23: the harvests are expected to cover these; what they do not is listed here."),
    "D4-v1-own-record": ("D", "V1 foundation metal / mint / readings not carried (seeded, not twin)",
                         "Decide — together with the twins (D1) and the memberless (D2) the foundations that lose `metal` render an empty metal column (count in the header); carrying `metal`/`mint` for foundations, like their prose and years, is the cheap fix."),
    "D5-v1-citations-on-promoted": ("D", "V1 curator citations / catalogue refs restored onto promoted hosts",
                                    "Deferred with D3 — the 2026-05 restore-v1 pass put V1 citations (old Numista `catalogue/pieces` urls, bare «Numista» / «ucoin» refs, NGC price guide, «KM-DK#») on promoted finals; no class attests them."),
    "E1-ruler-other": ("E", "ruler: the class names another ruler",
                       "Review per case — either the final's ruler was wrong (V1 / gap-fill) or the class is an over-merge."),
    "E2-head-departed": ("E", "finals whose head seed left the class",
                         "Review — the final's label names a seed no longer in its class; re-home or drop the stale values."),
    "E3-own-attested-removed": ("E", "a value the final's own class attests, yet removed",
                                "Review — a switch defect or a class value filtered later (KMM specimen drop, thinning)."),
    "E4-residual": ("E", "everything else", "Review per case."),
    "E5-stage-N-automerge": ("E", "a class merged by stage N's canonicalisation",
                             "Review — «Hans?» → «Hans» (unverified) let the matcher unite the KMM record with the documented Hvid class."),
}
ORDER = list(GROUPS)


def _git(args):
    return subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True).stdout


def _coins(text):
    return {c["id"]: c for c in (yaml.load(text, Loader=_L) or {}).get("coins") or []
            if isinstance(c, dict) and c.get("id")}


def _norm_note(s: str) -> str:
    s = re.sub(r"[a-z]?\d+[a-z]?hede\.htm", "HEDE", s)
    s = re.sub(r"\d", "0", s)
    return s[:70]


def _note_kind(removed: str, added: str | None) -> str:
    if added is None:
        return "lost"
    try:
        a, b = json.loads(removed), json.loads(added)
    except Exception:
        return "text"
    if not (isinstance(a, dict) and isinstance(b, dict)):
        return "text"
    common = set(a) & set(b)
    if any(a[k] != b[k] for k in common):
        return "text"
    if set(b) - set(a) == {"da"} and not (set(a) - set(b)):
        return "+da"
    if set(a) - set(b) == {"da"} and not (set(b) - set(a)):
        return "-da"
    return "text"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("candidates")
    ap.add_argument("classified")
    ap.add_argument("edits")
    ap.add_argument("--base", default="main")
    ap.add_argument("--location", help="only the entities this display page consumes (data/v2/locations/<loc>.yml); "
                                       "the curator reviews the finals a page renders, not the unprocessed rest")
    ap.add_argument("--md")
    ap.add_argument("--json")
    a = ap.parse_args()
    cand = json.load(open(a.candidates))
    scope: set[str] | None = None
    if a.location:
        loc = yaml.load((V2 / "locations" / f"{a.location}.yml").read_text(), Loader=_L) or {}
        scope = {str(e["entity"]) if isinstance(e, dict) else str(e) for e in loc.get("consumes_entities") or []}
        n_all = len(cand)
        cand = [r for r in cand if r["entity"] in scope]
        print(f"scope {a.location}: {sorted(scope)} — {len(cand)} of {n_all} rows")
    cls = {(r["entity"], r["final"], r["field"], r["value"]): r for r in json.load(open(a.classified))}
    edits = json.load(open(a.edits))

    # base finals: id map for the edit join; note-template frequency.
    # rebuilt finals: Bruun citations still present (anchor check).
    base_fin: dict[str, dict] = {}
    name2id: dict[str, str] = {}
    tmpl: collections.Counter = collections.Counter()
    cur_bruun: set[str] = set()
    for p in sorted((V2 / "final").glob("*.yml")):
        for c in _coins(_git(["show", f"{a.base}:data/v2/final/{p.stem}.yml"])).values():
            c["_ent"] = p.stem
            base_fin[c["id"]] = c
            for n in (c["id"], c.get("label"), c.get("legacy_id")):
                if n:
                    name2id.setdefault(n, c["id"])
            vn = c.get("verification_note")
            if isinstance(vn, dict):
                for lang in ("en", "da"):
                    if vn.get(lang):
                        tmpl[_norm_note(str(vn[lang]))] += 1
        for c in _coins(p.read_text()).values():
            if any(isinstance(s, dict) and re.search(r"bruun|stacksbowers", str(s.get("ref", "")) + str(s.get("url", "")), re.I)
                   for s in (c.get("sources") or [])):
                cur_bruun.add(c["id"])

    def _is_template(removed: str) -> bool:
        """Every language of the base note is a text at least TEMPLATE_MIN base
        finals share (file tokens and digits normalised) — generated, not prose."""
        try:
            d = json.loads(removed)
        except Exception:
            return False
        if not isinstance(d, dict):
            return False
        langs = [str(d[k]) for k in ("en", "da") if d.get(k)]
        return bool(langs) and all(tmpl.get(_norm_note(s), 0) >= TEMPLATE_MIN for s in langs)
    # hand-edit join: (id, field, value[:90]) -> [commit]
    edit_add: dict[tuple, list] = collections.defaultdict(list)
    edit_del: dict[tuple, list] = collections.defaultdict(list)
    subj = {}
    for o in edits:
        subj[o["h"]] = (o["d"], o["s"], o["kind"])
        for cid, fld, v in o["undone_added"]:
            edit_add[(name2id.get(cid, cid), fld, v[:90])].append(o["h"])
        for cid, fld, v in o["undone_deleted"]:
            edit_del[(name2id.get(cid, cid), fld, v[:90])].append(o["h"])

    by = collections.defaultdict(lambda: {"removed": [], "added": []})
    for r in cand:
        if r["field"] != "*coin*":
            by[(r["entity"], r["final"], r["field"])][r["direction"]].append(r["value"])

    out = []
    for r in cand:
        ent, fid, f, v, d = r["entity"], r["final"], r["field"], r["value"], r["direction"]
        if f == "*coin*":
            out.append(dict(r, group="E5-stage-N-automerge"))
            continue
        row = dict(r)
        c = cls.get((ent, fid, f, v), {})
        b = c.get("bucket", "")
        row["bucket"] = b
        commits = edit_add.get((fid, f, v[:90])) if d == "removed" else edit_del.get((fid, f, v[:90]))
        if commits:
            row["edit"] = sorted(set(commits))
        curated = [h for h in (row.get("edit") or []) if h not in BULK and subj.get(h, ("", "", ""))[2] == "edit"]
        o = r.get("origin")
        partners = by[(ent, fid, f)]["added"] if d == "removed" else by[(ent, fid, f)]["removed"]
        g = None
        if d == "added":
            if curated:
                g = "C7-hand-deletion-returns"
            elif not partners:
                g = "A5-gain"
            else:
                g = None  # the partner of a removed row: counted there
        elif f == "ruler":
            if not partners:
                g = "C3-ruler-lost"
            else:
                try:
                    av, rv = json.loads(partners[0]), json.loads(v)
                except Exception:
                    av, rv = partners[0], v
                av, rv = str(av), str(rv)
                if CANON.fullmatch(av):
                    g = "A2-ruler-canonical"
                elif ANNOT.search(rv) and not ANNOT.search(av):
                    g = "A3-ruler-annotated-to-plain"
                elif ANNOT.search(av) or TYPO.search(av):
                    g = "C2-ruler-regression"
                else:
                    g = "E1-ruler-other"
        elif f == "verification_note":
            k = _note_kind(v, partners[0] if partners else None)
            if k == "text":
                g = "B9-note-template-swap" if _is_template(v) else "C5-note-curated-text"
            else:
                g = {"+da": "A1-note-da-added", "-da": "C4-note-da-lost", "lost": "E4-residual"}[k]
        elif f == "nominal":
            g = "C1-nominal-form"
        elif curated:
            g = "C0-hand-edit"
        elif b == "R-orphan":
            g = "B1-excluded-stub-citations"
        elif f == "mintmaster":
            g = "B4-mintmaster-place" if PLACE.match(json.loads(v) if v.startswith('"') else v) else "C6-mintmaster-name"
        elif b in ("S-moved", "S-moved-no_merge"):
            g = "B2-moved-to-another-final"
        elif b == "S-relabel":
            g = "A4-relabel"
        elif b == "S-recorded" and f in ("sources", "catalog"):
            g = "B3-recorded-removal"
        elif b in ("S-covered", "S-v1-covered"):
            g = "B5-covered-other-form"
        elif b == "H":
            g = "E2-head-departed"
        elif b in ("H-stale-v1-twin", "R-twin"):
            g = "D1-v1-twin"
        elif b == "R-v1-memberless" or (o == "foundation" and c.get("memberless")):
            g = "D2-v1-memberless"
        elif b == "R-v1-uncovered":
            g = "D3-v1-uncovered"
        elif o == "foundation" and f in READINGS | {"metal", "mint"}:
            g = "D4-v1-own-record"
        elif f in FLAGS:
            g = "B6-flag-class-claim"
        elif b.startswith("FLAG"):
            g = "E3-own-attested-removed"
        elif o == "promoted" and f in ("mint", "metal", "inscription_obv", "inscription_rev"):
            g = "D6-v1-values-on-promoted"
        elif o == "foundation" and f in ("sources", "catalog"):
            g = "D3-v1-uncovered"
        elif (f == "catalog" and partners and v.split("'")[1] in BRUUN_ANCHORS and fid in cur_bruun):
            g = "B8-bruun-anchor"
        elif (f in ("sources", "catalog") and o == "promoted"
              and (set(row.get("edit") or []) & RESTORE or V1STYLE.search(v))):
            g = "D5-v1-citations-on-promoted"
        else:
            g = "E4-residual"
        row["group"] = g
        row["partner"] = partners[0] if partners else None
        out.append(row)

    rows = [r for r in out if r.get("group")]
    byg = collections.defaultdict(list)
    for r in rows:
        byg[r["group"]].append(r)
    if a.json:
        Path(a.json).write_text(json.dumps(rows, ensure_ascii=False, indent=0))

    # ---- report
    P = []
    P.append(f"# Finals: `{a.base}` vs the rebuild — decision groups" + (f" ({a.location} page)" if a.location else "") + "\n")
    if scope is not None:
        P.append(f"Scope: the entities the `{a.location}` page consumes — " + ", ".join(f"`{e}`" for e in sorted(scope)) +
                 " (curator 2026-10-23: only the finals a page renders matter; the rest are unprocessed). "
                 "A page's year window on an entity is not applied here.\n")
    P.append("Every row is one value that differs between the finals at `" + a.base +
             "` and the finals rebuilt on this branch (`--no-self-union`, full chain). "
             "«removed» = on the base, not on the rebuild; «added» = the reverse. The group letter says what the "
             "difference means for the finals' legal form: **A** nothing to decide · **B** garbage on the base · "
             "**C** keep, needs a surface · **D** V1 record, deferred · **E** review.\n")
    no_metal = sorted({(r["entity"], r["final"], r["group"]) for r in rows
                       if r["field"] == "metal" and r["direction"] == "removed" and r.get("partner") is None})
    gone = [r for r in rows if r["field"] == "*coin*"]
    P.append(f"Values: {len(rows)} on {len({(r['entity'], r['final']) for r in rows})} finals; coins gone {len([r for r in gone if r['direction'] == 'gone'])}, "
             f"new {len([r for r in gone if r['direction'] == 'new'])}. Finals that lose `metal` with nothing in its place: "
             f"{len(no_metal)} (" + ", ".join(f"{g} {n}" for g, n in collections.Counter(x[2] for x in no_metal).most_common()) + ").\n")
    P.append("| class | values | finals |\n|---|---|---|")
    for k in "ABCDE":
        rs = [r for r in rows if GROUPS[r["group"]][0] == k]
        P.append(f"| {k} | {len(rs)} | {len({(r['entity'], r['final']) for r in rs})} |")
    P.append("\n| group | class | values | finals | entities |\n|---|---|---|---|---|")
    for g in ORDER:
        rs = byg.get(g)
        if not rs:
            continue
        ents = collections.Counter(r["entity"] for r in rs)
        P.append(f"| {g} | {GROUPS[g][0]} | {len(rs)} | {len({(r['entity'], r['final']) for r in rs})} | "
                 + ", ".join(f"{e} {n}" for e, n in ents.most_common(4)) + (" …" if len(ents) > 4 else "") + " |")

    def _ex(r):
        extra = []
        if r.get("partner") is not None:
            extra.append("→ " + str(r["partner"])[:70] if r["direction"] == "removed" else "← " + str(r["partner"])[:70])
        if r.get("edit"):
            extra.append("edit " + ",".join(r["edit"]))
        if r.get("home"):
            extra.append("home " + r["home"])
        if r.get("twin_of"):
            extra.append("twin of " + r["twin_of"])
        return f"- `{r['final']}` [{r['entity']}] {r['field']}: `{str(r['value'])[:90]}`" + (" — " + "; ".join(extra) if extra else "")

    SMALL = 60
    for g in ORDER:
        rs = byg.get(g)
        if not rs:
            continue
        kls, title, legal = GROUPS[g]
        fins = {(r["entity"], r["final"]) for r in rs}
        P.append(f"\n## {g} — {title}\n")
        P.append(f"**{kls}** · {len(rs)} values on {len(fins)} finals. **Legal form:** {legal}\n")
        ff = collections.Counter((r["field"], r["origin"], r["direction"]) for r in rs)
        P.append("| field | origin | direction | values |\n|---|---|---|---|")
        for (f, o, d), n in sorted(ff.items()):
            P.append(f"| {f} | {o} | {d} | {n} |")
        ents = collections.Counter(r["entity"] for r in rs)
        if len(ents) > 1:
            P.append("\nPer entity: " + ", ".join(f"{e} {n}" for e, n in ents.most_common()) + ".")
        if g == "C0-hand-edit":
            byc = collections.defaultdict(list)
            for r in rs:
                for h in r.get("edit") or []:
                    if h not in BULK:
                        byc[h].append(r)
            P.append("\n| commit | date | subject | values | finals |\n|---|---|---|---|---|")
            for h, rr in sorted(byc.items(), key=lambda kv: subj[kv[0]][0]):
                P.append(f"| `{h}` | {subj[h][0]} | {subj[h][1][:80]} | {len(rr)} | {len({r['final'] for r in rr})} |")
            P.append("")
            for h, rr in sorted(byc.items(), key=lambda kv: subj[kv[0]][0]):
                P.append(f"\n`{h}` {subj[h][1][:90]}\n")
                for r in rr[:SMALL]:
                    P.append(_ex(r))
            continue
        if g == "C1-nominal-form":
            pairs = collections.Counter((r["value"], r["partner"]) for r in rs)
            P.append("\n| final form (base) | class form (rebuild) | n |\n|---|---|---|")
            for (x, y), n in pairs.most_common():
                P.append(f"| {x} | {y} | {n} |")
            P.append("")
            for r in rs:
                P.append(_ex(r))
            continue
        if len(fins) <= SMALL or kls in "CE":
            P.append("")
            shown = 0
            for r in sorted(rs, key=lambda r: (r["entity"], r["final"], r["field"])):
                if shown >= 400:
                    P.append(f"- … {len(rs) - shown} more")
                    break
                P.append(_ex(r)); shown += 1
        else:
            P.append("\nExamples:\n")
            seen = collections.Counter()
            for r in rs:
                k = (r["field"], r["origin"])
                if seen[k] >= 3:
                    continue
                seen[k] += 1
                P.append(_ex(r))
    # edit commits not reaching any row (fully natural-grouped) — for completeness
    P.append("\n## Hand-edit commits and where their undone values landed\n")
    P.append("| commit | date | kind | subject | undone +/− | groups |\n|---|---|---|---|---|---|")
    land = collections.defaultdict(collections.Counter)
    for r in rows:
        for h in r.get("edit") or []:
            land[h][r["group"]] += 1
    for o in sorted(edits, key=lambda o: o["d"]):
        h = o["h"]
        P.append(f"| `{h}` | {o['d']} | {o['kind']} | {o['s'][:70]} | +{len(o['undone_added'])} −{len(o['undone_deleted'])} | "
                 + ", ".join(f"{g} {n}" for g, n in land[h].most_common()) + " |")
    text = "\n".join(P) + "\n"
    if a.md:
        Path(a.md).write_text(text)
    print("\n".join(P[:40]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
