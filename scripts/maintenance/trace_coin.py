#!/usr/bin/env python3
"""trace_coin.py — where is a coin RIGHT NOW, and what moved across a re-flow.

The V2 pipeline has three layers of ids and only ONE of them is stable:

  seed id      data/v2/seed/<src>/<entity>.yml     STABLE — never changes
  unified id   data/v2/seed_unified/<entity>.yml   DERIVED — rebuilt every merge
  final id     data/v2/final/<entity>.yml          DERIVED — follows the unified

A unified class is named `unified-<its top-authority member>` (V2_PIPELINE §5.2),
so the moment a merge decision adds a higher-authority member the class RENAMES:
`unified-dk-bruun-7749` becomes `unified-dk-hede-c7h8` while describing the very
same coin. Any before/after comparison keyed on unified or final ids is therefore
measuring with a ruler that changes length during the measurement — it reports
coins as "lost" that merely moved into a renamed class.

This tool exists because that mistake was made repeatedly (most recently
2026-07-29, three times in one session, each time from a fresh ad-hoc script in a
shell heredoc, each time producing a confident and WRONG loss report that a
dedicated auditor immediately contradicted). It keys everything on seed ids.

Usage
-----
  # Where is this coin? (accepts seed ids; several at once)
  trace_coin.py trace dk-tid-70716 dk-hede-c7h8

  # Before a re-flow:
  trace_coin.py snapshot /tmp/before.json
  #   ... run merge_seeds_cross_source.py --apply, absorb_seeds_into_final_v2.py --apply ...
  trace_coin.py snapshot /tmp/after.json
  trace_coin.py diff /tmp/before.json /tmp/after.json

Exit codes: 0 clean, 1 real losses found (seed vanished / final lost /
classification changed / sources dropped), 2 usage error.

NO SILENT FALLBACKS. A lookup that misses is reported as a miss; it never
degrades to "treat the id as its own member", which is exactly how the earlier
ad-hoc versions manufactured plausible nonsense.

Cross-check before believing a loss report: `audit_lost_citations.py` and
`audit_curation_loss.py` cover citations and field-level curation. If this tool
disagrees with them, assume THIS tool is wrong until proven otherwise.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lib.v2_index import V2Index as _V2Index  # noqa: E402

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
V2 = PROJECT_ROOT / "data" / "v2"


def _load(path: Path) -> dict:
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError) as exc:  # surface, never swallow
        raise SystemExit(f"cannot read {path}: {exc}")


def build_index() -> dict:
    """Read the three layers and return the seed-keyed placement index.

    Returns {seed_id: {source, seed_entity, unified, final, final_entity,
                       fuss, phase, sources}}.
    A seed with no unified class, or a unified class no final references, keeps
    None in that slot — that is a fact about the pipeline, not a lookup failure.

    The traversal itself now lives in `lib.v2_index`, so the ad-hoc probes that
    used to hand-roll it can import it in one line instead of rediscovering
    that `final[].composed_of` holds unified ids while `seed_unified[]` holds
    seed ids. This wrapper keeps the dict shape the subcommands below expect.
    """
    idx = _V2Index.load()
    return {sid: {"source": pl.source, "seed_entity": pl.seed_entity,
                  "unified": pl.unified, "final": pl.final,
                  "final_entity": pl.final_entity, "fuss": pl.fuss,
                  "phase": pl.phase, "sources": pl.sources}
            for sid, pl in idx.by_seed.items()}


def cmd_trace(args) -> int:
    idx = build_index()
    missing = [i for i in args.ids if i not in idx]
    for i in args.ids:
        rec = idx.get(i)
        if rec is None:
            print(f"{i}\n    NOT A SEED ID — not present in any "
                  f"data/v2/seed/<src>/<entity>.yml.")
            print("    (unified-* and final ids are derived and unstable; "
                  "trace by seed id)")
            continue
        print(f"{i}")
        print(f"    seed     {rec['source']} / {rec['seed_entity']}.yml")
        print(f"    unified  {rec['unified'] or '— none —'}")
        print(f"    final    {rec['final'] or '— none —'}"
              + (f"  [{rec['final_entity']}]" if rec['final_entity'] else ""))
        print(f"    class    {rec['fuss']}/{rec['phase']}"
              f"   sources={rec['sources']}")
    return 1 if missing else 0


def _half_applied() -> list[str]:
    """Layers dirty in git, when a LATER layer of the pipeline is not.

    A snapshot is only a usable baseline when the three layers agree with each
    other. Take one with `data/v2/seed/` edited but `seed_unified/` and `final/`
    still at their committed state and it captures a MIXTURE: the seeds of the
    new run against the classes of the old one. Diffing against that reports
    coins as lost that merely have not been re-merged yet.

    Real case, 2026-08-01: a snapshot taken in exactly that state produced
    «16 coins lost their final». Compared against real HEAD the figure was zero
    — every one of them was an artefact of the baseline. Three separate
    conclusions were drawn from it before the mistake was found.

    Returns a list of human-readable warnings; empty when consistent.
    """
    import subprocess
    r = subprocess.run(["git", "status", "--porcelain",
                        "data/v2/seed", "data/v2/seed_unified", "data/v2/final"],
                       capture_output=True, text=True, cwd=PROJECT_ROOT)
    dirty = {"seed": False, "seed_unified": False, "final": False}
    for line in r.stdout.splitlines():
        p = line[3:].strip()
        if p.startswith("data/v2/seed_unified/"):
            dirty["seed_unified"] = True
        elif p.startswith("data/v2/seed/"):
            dirty["seed"] = True
        elif p.startswith("data/v2/final/"):
            dirty["final"] = True

    warn = []
    if dirty["seed"] and not dirty["seed_unified"]:
        warn.append("seeds are modified but seed_unified is not — the merger has not run")
    if dirty["seed_unified"] and not dirty["final"]:
        warn.append("seed_unified is modified but final is not — the absorb has not run")
    return warn


def cmd_snapshot(args) -> int:
    for w in _half_applied():
        print(f"  ⚠ HALF-APPLIED PIPELINE: {w}", file=sys.stderr)
    if _half_applied() and not args.force:
        print("\nA snapshot taken now mixes two pipeline states and will produce a\n"
              "meaningless diff (§9b). Finish the re-flow first — merger --apply\n"
              "then absorb --apply — or snapshot from a clean tree. Use --force if\n"
              "you genuinely want the mixed state.\n"
              "To compare against what is COMMITTED, use verify_reflow.py instead;\n"
              "its baseline is git HEAD and cannot be half-applied.", file=sys.stderr)
        return 2

    idx = build_index()
    Path(args.out).write_text(json.dumps(idx, ensure_ascii=False, indent=1))
    placed = sum(1 for r in idx.values() if r["final"])
    print(f"snapshot → {args.out}   seeds={len(idx)}  with a final={placed}")
    return 0


def classify_diff(before: dict, after: dict) -> dict:
    """Bucket every seed-level difference between two snapshots.

    Split out from `cmd_diff` so the judgement — the part that decides what
    counts as a loss — is testable without writing snapshot files.
    """
    gone = sorted(set(before) - set(after))
    added = sorted(set(after) - set(before))
    lost_final, reclassified, fewer_sources = [], [], []
    moved_entity, renamed_class, promoted, adopted = [], [], [], []
    smaller_host = []
    for s in sorted(set(before) & set(after)):
        b, a = before[s], after[s]
        if b["final"] and not a["final"]:
            lost_final.append((s, b["final"]))

        # A seed has no classification of its own — it reads the fuss/phase of
        # the final it belongs to. So «this seed's fuss changed» means one of
        # two entirely different things, and they must not share a bucket:
        #
        #   the seed stayed in the SAME final → that final was RECLASSIFIED.
        #       Nobody moved the coin; its class's own value changed. This is
        #       the real risk (absorb re-derived it, or a curator edit was
        #       overwritten) and it fails the run.
        #
        #   the seed moved to a DIFFERENT final → it ADOPTED the host class's
        #       classification. That is merge mechanics, not reclassification:
        #       the host already carried that value. Usually it is a
        #       correction (an unphased or misphased record joining the class
        #       that has it right), but a bad merge drags a coin into the
        #       wrong class the same way — so it is reported for review, not
        #       silenced, and not counted as a loss.
        same_final = bool(b["final"]) and b["final"] == a["final"]
        klass_b = (b["fuss"], str(b["phase"]))
        klass_a = (a["fuss"], str(a["phase"]))
        if b["fuss"] and a["fuss"] and klass_b != klass_a:
            if same_final:
                reclassified.append((s, b["final"], f"{klass_b[0]}/{klass_b[1]}",
                                     f"{klass_a[0]}/{klass_a[1]}"))
            elif b["fuss"] == "seed_unsorted":
                # Sub-case of adoption worth its own line: the record had no
                # classification at all and gained one.
                promoted.append((s, f"{klass_b[0]}/{klass_b[1]}",
                                 f"{klass_a[0]}/{klass_a[1]}"))
            else:
                adopted.append((s, f"{klass_b[0]}/{klass_b[1]}",
                                f"{klass_a[0]}/{klass_a[1]}",
                                f"{b['final']} → {a['final']}"))

        # `sources` is the count on the FINAL the seed belongs to, not on the
        # seed. So the same split as above applies, and for the same reason —
        # this one cost two false alarms before it was drawn:
        #
        #   stayed in the SAME final, count dropped → that class really did
        #       lose citations. A loss; fails the run.
        #
        #   MOVED to a different final → the count is a property of the
        #       destination class, and a smaller destination means new
        #       neighbours, not lost data. The citations the seed «left
        #       behind» belong to the members it left behind, and are still
        #       cited there. Reporting this as a loss is measuring per coin
        #       while the unit that carries the data is the seed (§9b).
        #
        # Whether the ENTITY still attests every citation is a different
        # question and not this tool's to answer — audit_lost_citations.py
        # owns it, and the footer already says to cross-check there.
        # (Observed 2026-08-02 «13 KMM URLs», again 2026-08-04 when
        # denmark-numismaster-110811 + dk-tid-145797 moved from a 4-source
        # class to a 3-source one during the Christiania 3-Dukat re-grouping;
        # both times the dedicated auditor said 0 and was right.)
        if (b["sources"] or 0) > (a["sources"] or 0) and a["final"]:
            if same_final:
                fewer_sources.append((s, b["sources"], a["sources"]))
            else:
                smaller_host.append((s, b["sources"], a["sources"],
                                     f"{b['final']} → {a['final']}"))
        if b["final_entity"] and a["final_entity"] and \
                b["final_entity"] != a["final_entity"]:
            moved_entity.append((s, b["final_entity"], a["final_entity"]))
        if b["final"] and a["final"] and b["final"] != a["final"]:
            renamed_class.append((s, b["final"], a["final"]))

    return {
        "gone": gone, "added": added, "lost_final": lost_final,
        "reclassified": reclassified, "fewer_sources": fewer_sources,
        "smaller_host": smaller_host, "moved_entity": moved_entity,
        "renamed_class": renamed_class, "promoted": promoted,
        "adopted": adopted,
        "losses": len(gone) + len(lost_final) + len(reclassified)
                  + len(fewer_sources),
    }


def cmd_diff(args) -> int:
    before = json.loads(Path(args.before).read_text())
    after = json.loads(Path(args.after).read_text())
    r = classify_diff(before, after)
    gone, added = r["gone"], r["added"]
    lost_final, reclassified = r["lost_final"], r["reclassified"]
    fewer_sources, smaller_host = r["fewer_sources"], r["smaller_host"]
    moved_entity, renamed_class = r["moved_entity"], r["renamed_class"]
    promoted, adopted = r["promoted"], r["adopted"]

    def report(title, rows, limit=args.show):
        print(f"\n{title}: {len(rows)}")
        for r in rows[:limit]:
            # rows are either a bare id or a tuple of columns; never splat a
            # str — that prints it one character at a time.
            print("   ", *(r if isinstance(r, tuple) else (r,)))
        if len(rows) > limit:
            print(f"    … and {len(rows) - limit} more")

    print(f"seeds: {len(before)} → {len(after)}")
    # Real losses — these fail the run.
    report("SEED VANISHED (no longer in any seed yaml)", gone)
    report("LOST ITS FINAL (had one, now none)", lost_final)
    report("RECLASSIFIED IN PLACE (same final, its own fuss/phase changed)",
           reclassified)
    report("FEWER SOURCES ON THE FINAL (same class — real loss)",
           fewer_sources)
    # Gains and expected churn — informational only.
    report("moved to a class with fewer sources (count is the destination's, "
           "not a loss — cross-check audit_lost_citations)", smaller_host)
    report("promoted out of seed_unsorted (gain, not loss)", promoted)
    report("adopted the host class's fuss/phase on merging (review, not loss)",
           adopted)
    report("moved to another entity file (informational)", moved_entity)
    report("class renamed, same coin (informational — id churn)", renamed_class)
    report("new seeds (informational)", added)

    losses = r["losses"]
    print(f"\n=== real losses: {losses} "
          f"(entity moves and class renames are not losses) ===")
    if losses:
        print("Before reporting these as fact, cross-check with "
              "audit_lost_citations.py and audit_curation_loss.py — if they "
              "disagree, this tool is wrong until proven otherwise.")
    return 1 if losses else 0


def _phase_windows() -> tuple[dict, dict]:
    """({location: {fuss: {phase_id: (from, to)}}}, {location: {entities}}).

    Phases are per-LOCATION by design (CLAUDE.md §7: Füße are global, phases
    are local), so the same fuss carries different windows on different pages.

    The second map is what keeps the comparison meaningful: a coin may only be
    judged against a page that actually SHOWS it, i.e. one whose
    `consumes_entities` includes one of the coin's issuing entities. Without
    that scope the check compares a Danish 9-Thaler coin of 1608 against
    Lübeck's 9_thaler window of 1776-1776 and calls it a finding — 648 such
    non-findings on the first run, against 22 real ones."""
    windows: dict = {}
    consumes: dict = {}
    for p in sorted((V2 / "locations").glob("*.yml")):
        d = _load(p)
        # An entry is either a bare entity or {entity, year_to} — a page can
        # consume an entity only up to a year (Denmark takes royal_holstein
        # to 1864, danish_norway to 1814). Keep the cutoff: a page that stops
        # showing an entity in 1814 has no business judging an 1842 coin.
        ents: dict = {}
        for e in d.get("consumes_entities") or []:
            if isinstance(e, dict):
                if e.get("entity"):
                    ents[e["entity"]] = e.get("year_to")
            elif e:
                ents[e] = None
        consumes[p.stem] = ents
        phases = d.get("phases")
        if not isinstance(phases, dict):
            continue
        windows[p.stem] = {
            fuss: {x.get("id"): (x.get("year_from"), x.get("year_to"))
                   for x in lst if isinstance(x, dict)}
            for fuss, lst in phases.items() if isinstance(lst, list)
        }
    return windows, consumes


def cmd_check_phases(args) -> int:
    """Report coins whose first year sits outside the window of the phase they
    are assigned to — as a QUESTION about the periodisation, never as a verdict
    about the coin.

    The direction matters and is the whole point of this check. Coins and
    ordinances dictate the years of a phase; the phase does not dictate what a
    coin may be (curator, 2026-07-29). CLAUDE.md §4 says it outright: «Phases
    and Füße are OUR structural annotations; years are THE SOURCE's factual
    record … Never quietly clip.» So a coin older than its phase's start is
    not a defect in the coin — it is a candidate for widening the phase, or a
    sign the phase assignment is wrong. Both are curator calls.

    Three separate findings, deliberately not merged into one «outside window»
    bucket:

      BEFORE THE FIRST PHASE / AFTER THE LAST — the fuss's periodisation may
          need extending to cover this coin. Ask the curator.
      NOT IN THIS PHASE (but inside the fuss's overall span) — the phase
          ASSIGNMENT is the thing in question, not the periodisation.
      year_last overshooting the phase end — NOT REPORTED AT ALL. §8.2 makes
          the FIRST year decide the phase and §4 explicitly permits the tail
          to run past the boundary.

    Always exits 0. Nothing here is a build error, and the tool must never
    imply that a coin's years should be trimmed to fit our taxonomy.
    """
    win, consumes = _phase_windows()
    extend, assign = [], []
    for p in sorted((V2 / "final").glob("*.yml")):
        for c in _load(p).get("coins") or []:
            fuss, phase, yf = c.get("fuss"), c.get("phase"), c.get("year_first")
            if not fuss or fuss == "seed_unsorted" or yf is None:
                continue
            ie = c.get("issuing_entity")
            entities = set(ie if isinstance(ie, list) else [ie] if ie else [])
            # Only pages that actually show this coin may judge its phase.
            shown_on = [
                loc for loc, ents in consumes.items()
                if any(e in ents and (ents[e] is None or yf <= ents[e])
                       for e in entities)
            ] or [p.stem]
            # phase may be scalar or per-location dict; a dict already names
            # its locations, so it needs no scoping.
            pairs = (list(phase.items()) if isinstance(phase, dict)
                     else [(loc, phase) for loc in shown_on])
            for loc, ph in pairs:
                fmap = win.get(loc, {}).get(fuss)
                if not fmap or ph not in fmap:
                    continue
                lo, hi = fmap[ph]
                if (lo is None or yf >= lo) and (hi is None or yf <= hi):
                    continue
                starts = [v[0] for v in fmap.values() if v[0] is not None]
                ends = [v[1] for v in fmap.values() if v[1] is not None]
                row = (c.get("id"), fuss, ph, str(c.get("year_label")),
                       f"window {lo}-{hi}", loc)
                if starts and yf < min(starts):
                    extend.append(row + ("earlier than the fuss's first phase",))
                elif ends and yf > max(ends):
                    extend.append(row + ("later than the fuss's last phase",))
                else:
                    assign.append(row)

    def show(title, rows, note):
        print(f"\n{title}: {len(rows)}")
        print(f"  {note}")
        for r in rows[:args.show]:
            print("   ", *r)
        if len(rows) > args.show:
            print(f"    … and {len(rows) - args.show} more")

    show("PERIODISATION MAY NEED WIDENING", extend,
         "The coin predates (or outlives) every phase of its fuss. Coins and "
         "ordinances set the years — ask the curator whether to widen the "
         "phase, and never trim the coin's years to fit.")
    show("PHASE ASSIGNMENT IN QUESTION", assign,
         "The year sits inside the fuss's overall span but not in the phase "
         "the coin is assigned to. Here the assignment is what to re-examine, "
         "not the periodisation.")
    print("\n(informational — exits 0; both lists are questions for the "
          "curator, not defects)")
    return 0


def _seed_entries(coin_id: str) -> list[tuple[Path, dict]]:
    """Seed entries carrying this id. Substring-screens before parsing.

    Parsing every seed yaml costs ~25 s; reading them as text costs a fraction
    of that, and an id that does not appear in a file's bytes cannot be one of
    its coins. The screen only ever skips work — a file that mentions the id
    for any reason is still parsed and checked properly.
    """
    out = []
    for src_dir in sorted((V2 / "seed").iterdir()):
        if not src_dir.is_dir():
            continue
        for p in sorted(src_dir.glob("*.yml")):
            try:
                if coin_id not in p.read_text(encoding="utf-8"):
                    continue
            except OSError as exc:
                raise SystemExit(f"cannot read {p}: {exc}")
            for c in _load(p).get("coins") or []:
                if c.get("id") == coin_id:
                    out.append((p, c))
    return out


def _parser_overrides(coin_id: str) -> list[str]:
    """Parser-level curator overrides keyed by SOURCE PAGE, not by coin id.

    These are the easiest layer to miss, because nothing in the data points at
    them: `_KNOWN_HEDE_TYPOS` rewrites the Hede tag during parsing, so the cache
    a reader compares the seed against is ALREADY the corrected artefact — and
    still differs from what the page prints.
    """
    if not coin_id.startswith("dk-hede-"):
        return []
    page = coin_id[len("dk-hede-"):]
    found = []
    try:
        sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
        import parse_hede as PH
        if page in getattr(PH, "_KNOWN_HEDE_TYPOS", {}):
            found.append(f"parse_hede._KNOWN_HEDE_TYPOS[{page!r}] = "
                         f"{PH._KNOWN_HEDE_TYPOS[page]!r}  (Hede tags are SWAPPED "
                         f"relative to what the page prints)")
        if page in getattr(PH, "_INVERTED_TAG_PAGES", frozenset()):
            found.append(f"parse_hede._INVERTED_TAG_PAGES contains {page!r}  "
                         f"(the page's own nominal/refs are deliberately NOT "
                         f"attached)")
        # A multi-Hede page produces several seeds; the override is on the PAGE,
        # so a sibling's page can carry it too.
        for other, mapping in getattr(PH, "_KNOWN_HEDE_TYPOS", {}).items():
            if other != page and page.rstrip("abAB") in mapping.values():
                found.append(f"parse_hede._KNOWN_HEDE_TYPOS[{other!r}] maps a tag "
                             f"onto this page's number — check {other}")
    except Exception as exc:                     # never swallow into silence
        found.append(f"(could not read parse_hede overrides: {exc})")
    return found


def _load_builder(name: str):
    import importlib.util
    path = PROJECT_ROOT / "scripts" / "maintenance" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"_why_{name}", path)
    mod = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
    sys.path.insert(0, str(PROJECT_ROOT / "scripts" / "maintenance"))
    spec.loader.exec_module(mod)
    return mod


def _builder_overrides(coin_id: str) -> list[str]:
    """Seed-BUILDER tables that decide a value before it is ever written.

    Like the parser overrides, nothing in the data points at them, and `why`
    used to print «nothing recorded» over them. Real case (2026-09-20):
    `kmk-735220` carried a stale mint «Lybæk» in final while `build_kmk_seed`
    already stop-listed the value in `_NON_MINT_PLACES` — the decision existed,
    in code, and was argued against before anyone read it.
    """
    found: list[str] = []
    try:
        if coin_id.startswith("kmk-") and coin_id[4:].isdigit():
            rid = int(coin_id[4:])
            bk = _load_builder("build_kmk_seed")
            cache = PROJECT_ROOT / "scripts" / "cache" / "kmk" / f"{rid}.json"
            src = json.loads(cache.read_text()) if cache.exists() else {}
            place = (src.get("place") or "").strip()
            if place:
                found.append(f"KMM place (cache) = {place!r}")
            if place.split(",")[0].strip().casefold() in getattr(bk, "_NON_MINT_PLACES", set()):
                found.append(f"build_kmk_seed._NON_MINT_PLACES lists {place.split(',')[0].strip()!r}"
                             f" — never written as a mint")
            for name in ("_KMM_PLACE_ERRATA", "_KMM_GALSTER_ERRATA", "_KMM_YEAR_ERRATA"):
                table = getattr(bk, name, {}) or {}
                if rid in table:
                    found.append(f"build_kmk_seed.{name}[{rid}] = {table[rid]!r}")
            if rid in (getattr(bk, "_KMM_DROP_IDS", set()) or set()):
                found.append("build_kmk_seed._KMM_DROP_IDS — the builder drops this record")
            if src:
                mint, _mm = bk._split_place(src)
                if isinstance(mint, list):
                    key = frozenset(bk.canon_for_alias(m) for m in mint)
                    if key in getattr(bk, "_KMM_DISPUTED_JOINT_MINTS", set()):
                        found.append(f"build_kmk_seed._KMM_DISPUTED_JOINT_MINTS — joint mint "
                                     f"{mint} kept but mint_verified false")
        elif "tid-" in coin_id:
            tid = coin_id.rsplit("-", 1)[-1]
            cache = PROJECT_ROOT / "scripts" / "cache" / "ucoin" / f"{tid}.json"
            if cache.exists():
                src = json.loads(cache.read_text())
                if isinstance(src, dict):
                    bu = _load_builder("build_ucoin_seed")
                    raw = src.get("mint_text")
                    found.append(f"ucoin mint_text (cache) = {raw!r}")
                    if isinstance(raw, str) and raw.strip().lower() in getattr(bu, "_UCOIN_MINT_JUNK", set()):
                        found.append("build_ucoin_seed._UCOIN_MINT_JUNK — a page header, not a mint")
                    if isinstance(raw, str) and any(t.strip().lower() in getattr(bu, "_UCOIN_MINT_IMPRECISE", set())
                                                    for t in re.split(r"[,;(]", raw)):
                        found.append(f"build_ucoin_seed._ucoin_mint → {bu._ucoin_mint(src)!r} "
                                     f"(imprecise mint name handling)")
    except Exception as exc:                     # never swallow into silence
        found.append(f"(could not read builder overrides: {exc})")
    return found


def cmd_why(args) -> int:
    """Every curator layer that touches a coin, before you call a value wrong.

    A value in a seed is not always what the source printed, and the difference
    is nearly always a DECISION someone already made and wrote down. This prints
    those decisions in one place.

    It exists because of a concrete failure (2026-08-08): dk-hede-c5h39 was
    twice declared defective — once for a «phantom Schou 4», once for «swapped
    Hede numbers» — by comparing the seed against danskmoent and against the
    parser cache. Both verdicts were wrong. The answer was a `_source_errata` in
    the same seed entry, ten lines below the catalog block, recording a curator
    call from three weeks earlier (Bruun's specimen over danskmoent's page), and
    a `_KNOWN_HEDE_TYPOS` entry implementing the other half of it. Two attempted
    «repairs» of that working construction followed before anyone read it.

    Run this BEFORE concluding that a value is wrong.
    """
    rc = 0
    for cid in args.ids:
        print(f"\n{'=' * 70}\n{cid}\n{'=' * 70}")
        entries = _seed_entries(cid)
        if not entries:
            print("  not a seed id — `trace` it first (unified/final ids are derived)")
            rc = 1
            continue
        for path, coin in entries:
            print(f"\n  seed: {path.relative_to(PROJECT_ROOT)}")
            if args.field:
                print(f"  {args.field} = "
                      f"{(coin.get('catalog') or {}).get(args.field, coin.get(args.field))!r}")

            errata = coin.get("_source_errata") or []
            if errata:
                print(f"\n  ── _source_errata ({len(errata)}) — the source was OVERRULED here")
                for e in errata:
                    if args.field and e.get("field") != args.field:
                        continue
                    print(f"     {e.get('field')}: printed {e.get('printed')!r} "
                          f"→ {e.get('correct')!r}   [{e.get('curator')}]")
                    for line in (e.get("reason") or "").strip().splitlines():
                        print(f"       {line}")
            holds = coin.get("_curation_holds")
            if holds:
                print(f"\n  ── _curation_holds — frozen against regen")
                if isinstance(holds, dict):
                    for k, v in holds.items():
                        print(f"     {k}: {v or '(no reason recorded)'}")
                else:
                    print(f"     {list(holds)}")
            note = (coin.get("_source_note") or {}).get("da")
            if note:
                print(f"\n  ── _source_note (what the page says, verbatim)\n     {note}")

        for line in _parser_overrides(cid):
            print(f"\n  ── parser override\n     {line}")

        for line in _builder_overrides(cid):
            print(f"\n  ── seed builder\n     {line}")

        for rel, key, label in (
                ("exclusions", "exclusions", "EXCLUDED from the render"),
                ("merge_decisions", None, "merge decision"),
                ("classification_decisions", None, "classification decision")):
            for p in sorted((V2 / rel).glob("*.yml")):
                blob = p.read_text(encoding="utf-8")
                if cid in blob:
                    print(f"\n  ── {label}: {p.relative_to(PROJECT_ROOT)} mentions it")

        rem = V2 / "_recorded_removals.yml"
        if rem.exists():
            for e in (_load(rem).get("removals") or []):
                if e.get("seed") == cid and (not args.field or e.get("field") == args.field):
                    print(f"\n  ── recorded removal: {e.get('field') or e.get('kind')} "
                          f"dropped {e.get('dropped')!r}\n     {e.get('reason')}")

        led = V2 / "_retracted_refs.yml"
        if led.exists():
            for e in (_load(led).get("retractions") or []):
                if e.get("seed") == cid:
                    print(f"\n  ── retraction ledger: {e.get('field')} "
                          f"dropped {e.get('dropped')!r} (parser retracted it)")
    print("\nNothing printed above means no recorded decision — the value should "
          "match its source.\nIf it doesn't, THEN it is a finding.")
    return rc


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    t = sub.add_parser("trace", help="locate coins by SEED id")
    t.add_argument("ids", nargs="+")
    t.set_defaults(func=cmd_trace)
    s = sub.add_parser("snapshot", help="write the seed-keyed placement index")
    s.add_argument("out")
    s.add_argument("--force", action="store_true",
                   help="snapshot even from a half-applied pipeline (see _half_applied)")
    s.set_defaults(func=cmd_snapshot)
    d = sub.add_parser("diff", help="compare two snapshots (seed-keyed)")
    d.add_argument("before")
    d.add_argument("after")
    d.add_argument("--show", type=int, default=15)
    d.set_defaults(func=cmd_diff)
    w = sub.add_parser("why", help="every curator decision touching a coin — "
                                   "run BEFORE calling a value wrong")
    w.add_argument("ids", nargs="+")
    w.add_argument("--field", help="narrow the errata listing to one field")
    w.set_defaults(func=cmd_why)
    cp = sub.add_parser("check-phases",
                        help="coins whose first year falls outside their "
                             "phase's window — questions for the curator")
    cp.add_argument("--show", type=int, default=25)
    cp.set_defaults(func=cmd_check_phases)
    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
