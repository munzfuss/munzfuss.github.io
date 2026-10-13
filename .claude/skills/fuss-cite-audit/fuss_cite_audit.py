#!/usr/bin/env python3
"""fuss_cite_audit — every citation of ONE Müntzfuß on ONE location page.

Candidates, not verdicts (CLAUDE.md §0b). The per-key checks are the
cite-source skill's own (`cite_helper.lint`); this script adds the page-level
layer around them: the audit boundary, the page's languages, per-surface
citation counts across languages, data-side language gaps, multi-passage /
translation / archive checks, optional verbatim check against the cache, and
a claim map for the human judgment step.

  fuss_cite_audit.py --fuss rhinsk_gylden_fod --location denmark
        [--site danskmoent]     which published site (default: every site
                                that contains the location; first one is used)
        [--verbatim]            check each quote against scripts/cache (slow)
        [--claims uk]           write the claim map (sentence → key → quote)
        [--out DIR]             where the claim map goes (default: cwd)

Boundary (what belongs to the fuss on that page):
  rendered  — the timeline row of the fuss (label + bar), the section
              `fuss-<fuss>` (heading, card, details) and its lazy part
              `<lang>/t/<fuss>.html` (details body + coin table incl. Note);
  data      — fuesse.yml::<fuss>, <loc>.yml fuss_periods.<fuss>,
              phases.<fuss>, timeline.bars[id=<fuss>], and `note` of every
              coin the build assembles for the location with that fuss.
A citation that appears in this boundary is in scope even if the same key is
also cited elsewhere; text of OTHER fusses that merely links here is not.
"""
from __future__ import annotations

import argparse
import contextlib
import glob
import html as _html
import io
import os
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / ".claude/skills/cite-source"))
import cite_helper as ch  # noqa: E402  — the per-key rules live there

CITE_RE = re.compile(r'href="#ref-pool-([a-z0-9-]+)"')
TR_ANY = re.compile(r"\((dt\.|transl\.|перекл\.|overs\.|Übersetzung|translation|переклад|oversættelse):")
TR_CANON = {"de": "dt.", "en": "transl.", "uk": "перекл.", "da": "overs."}
ARCHIVE_RE = re.compile(r"web\.archive\.org/web/\d|archive\.(ph|today|is)/")
TR_QUOTE = re.compile(r"\((?:dt\.|transl\.|перекл\.|overs\.|Übersetzung|translation|переклад|oversættelse):\s*«(.*?)»\)")
LABEL_RE = re.compile(r"\b(Verbatim|Ordret|Wörtlich|Дослівно|Цитата)\s*:", re.I)


# ---------------------------------------------------------------- site / langs
def sites_for(location: str) -> list[dict]:
    out = []
    for f in sorted((ROOT / "config/sites").glob("*.yml")):
        p = yaml.safe_load(f.read_text())
        locs = p.get("locations")
        if locs is not None:
            inside = location in locs
        else:
            inside = location not in (p.get("all_except") or [])
        if inside:
            out.append(p)
    return out


def page_file(site: dict, location: str, lang: str) -> Path:
    base = ROOT / site["out_dir"]
    if site.get("mount") == "root":
        return base / lang / "index.html"
    return base / location / lang / "index.html"


# ---------------------------------------------------------------- rendered side
def rendered_surfaces(page: Path, fuss: str) -> dict[str, str]:
    """surface-name → html chunk, for one language page."""
    h = page.read_text()
    out: dict[str, str] = {}
    # timeline row: from this fuss's label to the next label
    i = h.find(f'href="#fuss-{fuss}"')
    lab = h.rfind('<div class="tl-label"', 0, i) if i >= 0 else -1
    if lab >= 0:
        nxt = h.find('<div class="tl-label"', lab + 10)
        out["timeline"] = h[lab:nxt if nxt > 0 else lab + 20000]
    # section
    ids = [(m.start(), m.group(1)) for m in re.finditer(r'<section[^>]*id="([^"]+)"', h)]
    start = next((p for p, s in ids if s == f"fuss-{fuss}"), None)
    if start is None:
        return out
    nxt = [p for p, _ in ids if p > start]
    sec = h[start:nxt[0] if nxt else len(h)]
    d = sec.find("<details")
    out["card"] = sec[:d] if d >= 0 else sec
    if d >= 0:
        out["details(inline)"] = sec[d:]
    lazy = page.parent / "t" / f"{fuss}.html"
    if lazy.exists():
        lz = lazy.read_text()
        rows = re.findall(r"<tr>.*?</tr>", lz, re.S)
        body = lz
        for r in rows:
            body = body.replace(r, "")
        out["details"] = body
        n = 0
        for r in rows:
            if 'class="c-note"' in r or "<td" in r:
                n += 1
                out[f"coin-row#{n:02d}"] = r
    return out


def cites(chunk: str) -> list[str]:
    return CITE_RE.findall(chunk)


def plain(s: str) -> str:
    s = re.sub(r"<sup>.*?</sup>", "", s, flags=re.S)
    return re.sub(r"\s+", " ", _html.unescape(re.sub(r"<[^>]+>", "", s))).strip()


# ---------------------------------------------------------------- data side
def data_surfaces(fuss: str, location: str) -> list[tuple[str, dict]]:
    """(label, {lang: text}) for every translatable string in the boundary."""
    out: list[tuple[str, dict]] = []

    def walk(o, path):
        if isinstance(o, dict):
            if any(isinstance(o.get(l), str) for l in ch.LANGS) and \
                    all(k in ch.LANGS or k.startswith("_") for k in o):
                out.append((path, o))
                return
            for k, v in o.items():
                walk(v, f"{path}.{k}")
        elif isinstance(o, list):
            for i, v in enumerate(o):
                walk(v, f"{path}[{i}]")

    f = yaml.safe_load((ROOT / "data/shared/fuesse.yml").read_text())
    f = f.get("fuesse", f)
    walk(f.get(fuss) or {}, f"fuesse.yml::{fuss}")
    loc = yaml.safe_load((ROOT / f"data/v2/locations/{location}.yml").read_text())
    walk((loc.get("fuss_periods") or {}).get(fuss) or {}, f"{location}.yml::fuss_periods.{fuss}")
    ph = loc.get("phases") or {}
    walk(ph.get(fuss) if isinstance(ph, dict) else
         [p for p in ph if isinstance(p, dict) and p.get("fuss") == fuss],
         f"{location}.yml::phases.{fuss}")
    for b in (loc.get("timeline") or {}).get("bars") or []:
        if isinstance(b, dict) and fuss in (b.get("id"), b.get("fuss")):
            walk(b, f"{location}.yml::timeline.bars[{b.get('id')}]")
    for cid, note in coin_notes(fuss, location, loc):
        if isinstance(note, dict):
            out.append((f"coin {cid}.note", note))
        elif isinstance(note, str):
            out.append((f"coin {cid}.note", {"_str": note}))
    return out


def coin_notes(fuss: str, location: str, loc: dict):
    """The coins the build itself assembles for this page — not a re-derivation."""
    sys.path.insert(0, str(ROOT / "scripts"))
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        import build  # noqa: WPS433
        raw = dict(loc)
        build._assemble_v2_location(location, raw)
    for c in raw.get("coins") or []:
        if c.get("fuss") == fuss:
            yield c.get("id"), c.get("note")


# ---------------------------------------------------------------- per-key checks
def key_checks(pool: dict, key: str, langs: list[str]) -> list[tuple[str, str]]:
    """cite_helper.lint, reconciled with this page's languages, plus page-audit checks.

    cite_helper flags a quote «without translation» unless the CANONICAL label
    is present; an entry that does translate under an old label («Übersetzung:»,
    «переклад:») is a formula drift (low), not a missing translation (high).
    Messages that differ only by language are merged into one line «[de,en] …».
    """
    e = pool.get(key) or {}
    has_tr = {l: bool(TR_ANY.search(e.get(l) or "")) for l in ch.LANGS}
    raw: list[tuple[str, str, str]] = []          # (prio, lang|"", message)
    for prio, msg in ch.lint(pool, key):
        m = re.match(r"(de|en|uk|da): (.*)", msg)
        lang, body = (m.group(1), m.group(2)) if m else ("", msg)
        if lang and lang not in langs:
            continue
        if "quote without translation" in body and has_tr.get(lang):
            continue                               # translated, old label → see drift below
        body = re.sub(r" \((dt\.|transl\.|перекл\.|overs\.): …\)", "", body)
        if body.startswith("no archive copy"):
            body = "no archive copy"
        raw.append((prio, lang, body))
    for l in langs:
        t = e.get(l) or ""
        if not t:
            continue
        qs = ch.QUOTE_RE.findall(t)
        if len(qs) > 1:
            raw.append(("high", "", f"{len(qs)} quoted passages in one key (one passage = one key)"))
        m = TR_ANY.findall(t)
        if m and any(x != TR_CANON.get(l) for x in m):
            raw.append(("low", l, f"translation label {sorted(set(m))}, canonical is «{TR_CANON.get(l)}:»"))
        links = [u for u, _ in ch.LINK_RE.findall(t) if "archive" not in u]
        if links and not ARCHIVE_RE.search(t):
            raw.append(("medium", l, "no archive copy"))
        if LABEL_RE.search(t):
            raw.append(("low", l, "label before the quote"))
        tail = re.sub(r"<[^>]+>", "", t.split("</i>»")[-1]) if qs else ""
        tail = TR_QUOTE.sub("", tail)
        if len(tail.strip(" .;")) > 80:
            raw.append(("low", l, "text after the quote > 80 chars — scope note too long / analysis in the entry?"))
    merged: dict[tuple[str, str], list[str]] = defaultdict(list)
    for prio, lang, body in raw:
        ls = merged[(prio, body)]
        if lang and lang not in ls:
            ls.append(lang)
    return [(p, (f"[{','.join(sorted(ls, key=ch.LANGS.index))}] " if ls else "") + b)
            for (p, b), ls in merged.items()]


# ---------------------------------------------------------------- verbatim
def verbatim(pool: dict, keys: list[str]) -> dict[str, list[str]]:
    def norm(s):
        s = _html.unescape(re.sub(r"<[^>]+>", " ", s))
        s = unicodedata.normalize("NFC", s).replace("­", "")
        s = re.sub(r"-\s*\n\s*", "", s)
        return re.sub(r"\s+", " ", s).lower()
    corpus = {}
    for f in glob.glob(str(ROOT / "scripts/cache/**/*"), recursive=True):
        if f.endswith((".htm", ".html", ".txt", ".json")) and os.path.getsize(f) < 3e7:
            raw = open(f, encoding="utf-8", errors="ignore").read()
            if f.endswith(".json") and "\\u" in raw:
                raw = raw.encode().decode("unicode_escape", "ignore")
            corpus[f] = norm(raw)
    res = {}
    for k in keys:
        e = pool.get(k) or {}
        miss = []
        for q in ch.QUOTE_RE.findall(e.get("da") or e.get("de") or ""):
            frags = [norm(x).strip(" .,;") for x in re.split(r"…|\[…\]|·", q)]
            for fr in [x for x in frags if len(x) >= 8]:
                if not any(fr in c for c in corpus.values()):
                    miss.append(fr[:70])
        res[k] = miss
    return res


# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fuss", required=True)
    ap.add_argument("--location", required=True)
    ap.add_argument("--site")
    ap.add_argument("--verbatim", action="store_true")
    ap.add_argument("--claims")
    ap.add_argument("--out", default=".")
    a = ap.parse_args()

    sites = sites_for(a.location)
    if a.site:
        sites = [s for s in sites if s["id"] == a.site]
    if not sites:
        sys.exit(f"no site profile contains {a.location}")
    site = sites[0]
    langs = list(site["languages"])
    print(f"SITE {site['id']} · languages {langs} (root {site.get('root_lang')})"
          + (f" · also on: {[s['id'] for s in sites_for(a.location) if s['id'] != site['id']]}"
             if len(sites_for(a.location)) > 1 else ""))
    pool = ch.load_pool()

    # rendered side ------------------------------------------------------------
    per_lang: dict[str, dict[str, str]] = {}
    for l in langs:
        p = page_file(site, a.location, l)
        if not p.exists():
            print(f"  ! {l}: page not built ({p.relative_to(ROOT)}) — rebuild before auditing")
            continue
        per_lang[l] = rendered_surfaces(p, a.fuss)
    surf_names = sorted({s for d in per_lang.values() for s in d})
    print(f"\nRENDERED — citations per surface and language")
    drift = 0
    order: dict[str, int] = {}
    for s in surf_names:
        counts = {l: len(cites(per_lang[l].get(s, ""))) for l in per_lang}
        flag = "" if len(set(counts.values())) == 1 else "   ← DRIFT"
        drift += bool(flag)
        if any(counts.values()) or flag:
            print(f"  {s:<18} " + " ".join(f"{l}={n}" for l, n in counts.items()) + flag)
    for l in per_lang:
        for s in surf_names:
            for k in cites(per_lang[l].get(s, "")):
                order.setdefault(k, len(order) + 1)
    keyset = {l: Counter(k for s in per_lang[l].values() for k in cites(s)) for l in per_lang}
    ref = next(iter(keyset.values()), Counter())
    for l, c in keyset.items():
        if set(c) != set(ref):
            print(f"  key-set drift {l}: +{sorted(set(c) - set(ref))} −{sorted(set(ref) - set(c))}")
    # prose quotes without translation, per rendered language
    for l in per_lang:
        for s, chunk in per_lang[l].items():
            for msg in ch.prose_quote_issues(l, chunk):
                print(f"  PROSE {l} {s}: {msg}")

    # data side ----------------------------------------------------------------
    print("\nDATA — language fields and citation counts")
    ds = data_surfaces(a.fuss, a.location)
    data_keys = []
    for label, d in ds:
        if "_str" in d:
            print(f"  {label}: plain string, not per-language")
            continue
        miss = [l for l in langs if not (d.get(l) or "").strip()]
        cnt = {l: len(ch.REF_RE.findall(d.get(l) or "")) for l in langs if d.get(l)}
        if miss and any((d.get(l) or "").strip() for l in langs):
            print(f"  {label}: missing {miss} (renders as fallback)")
        if len(set(cnt.values())) > 1:
            print(f"  {label}: count drift {cnt}")
        for l in langs:
            for k in ch.REF_RE.findall(d.get(l) or ""):
                if k not in pool:
                    print(f"  UNRESOLVED [ref:{k}] in {label} [{l}]")
                if k not in data_keys:
                    data_keys.append(k)
    only_data = [k for k in data_keys if k not in order]
    only_page = [k for k in order if k not in data_keys]
    if only_data:
        print(f"  in boundary data but not rendered here (block scoped to another page, or stale build): {only_data}")
    if only_page:
        print(f"  rendered here but not found in boundary data (shared/generated block — trace it): {only_page}")
    print(f"  {len(ds)} surfaces · {len(data_keys)} keys in data · {len(order)} keys on page")

    # per-key ------------------------------------------------------------------
    keys = sorted(set(order) | set(data_keys), key=lambda k: order.get(k, 9999))
    vb = verbatim(pool, keys) if a.verbatim else {}
    print(f"\nKEYS — {len(keys)} (page order)")
    tally = Counter()
    for k in keys:
        iss = key_checks(pool, k, langs) if k in pool else [("high", "not in refs_pool")]
        for f in vb.get(k, []):
            iss.append(("medium", f"verbatim not found in cache (OCR? source not cached?): «{f}»"))
        if iss:
            print(f"{order.get(k, '-'):>4}  {k}")
            for p, m in sorted(iss, key=lambda x: ("high", "medium", "low").index(x[0])):
                print(f"        [{p}] {m}")
                tally[p] += 1
    print(f"--- {len(keys)} keys · high {tally['high']} · medium {tally['medium']} · "
          f"low {tally['low']} · surface drift {drift}")

    # claim map ----------------------------------------------------------------
    if a.claims:
        l = a.claims
        lines = []
        for s, chunk in per_lang.get(l, {}).items():
            for m in re.finditer(r"((?:<sup>.*?</sup>)+)", chunk, re.S):
                ks = CITE_RE.findall(m.group(1))
                if not ks:
                    continue
                pre = plain(chunk[max(0, m.start() - 1500):m.start()])
                sent = re.split(r"(?<=[.;])\s", pre)[-1][-300:]
                lines.append(f"[{s}] …{sent}")
                for k in ks:
                    t = (pool.get(k) or {}).get(l, "")
                    q = [plain(x)[:220] for x in ch.QUOTE_RE.findall(t)]
                    tr = [x[:220] for x in re.findall(TR_QUOTE, t)]
                    lines.append(f"    → {k}\n        Q: {q}\n        T: {tr}")
        out = Path(a.out) / f"claims_{a.location}_{a.fuss}_{l}.txt"
        out.write_text("\n".join(lines) + "\n")
        print(f"\nclaim map → {out} ({sum(1 for x in lines if x.startswith('['))} cite points)")


if __name__ == "__main__":
    main()
