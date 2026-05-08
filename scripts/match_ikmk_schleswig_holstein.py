"""Match IKMK Berlin records mapped to schleswig_holstein.yml.

For every IKMK record whose title-prefix is in
``Schleswig-Holstein* / Holstein-Schauenburg`` (= 65 in-scope records
per ``_index_by_issuer.json``), determine whether the same coin
already exists in ``data/locations/schleswig_holstein.yml`` and what
status applies.

Match strategy (ordered):

1. **Strict by Lange #** — most SH IKMK records cite Chr. Lange's
   Sammlung schleswig-holsteinischer Münzen und Medaillen as the
   primary catalogue. We carry Lange # in 144 / 321 SH coins. A
   shared Lange-number-and-qualifier is a near-certain match.
2. **Strict by Hede #** — fallback for Danish-mint Holstein coins.
3. **Strict by Davenport #** — large silver / Speciedaler thalers.
4. **Fuzzy (year + ruler-surname + nominal-token + weight ±2 %)** —
   when none of the catalogue refs overlap.

Output:

* ``scripts/cache/ikmk/_match_schleswig_holstein.json`` — machine
  index. For each IKMK ID: status, our coin id (if matched), match
  reason, and the diff of fields IKMK exposes that we lack
  (inscription_obv / inscription_rev / diameter / additional refs).
* ``scripts/cache/ikmk/_match_schleswig_holstein.md`` — readable
  digest grouped by status.
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[1]
CACHE = REPO / "scripts" / "cache" / "ikmk"
YAML_PATH = REPO / "data" / "locations" / "schleswig_holstein.yml"
INDEX_PATH = CACHE / "_index_by_issuer.json"
MATCH_JSON = CACHE / "_match_schleswig_holstein.json"
MATCH_MD = CACHE / "_match_schleswig_holstein.md"


# ---------- Catalogue-ref extraction from IKMK literatur -------------

# Lange comes in two volume variants. Pattern handles both vol I (1908)
# and vol II (1912), with optional "Vgl." (cf.) prefix and an optional
# letter qualifier on the number (e.g. "339 B", "34 e").
RE_LANGE = re.compile(
    r"(?P<cf>Vgl\.\s+)?Chr\.?\s*Lange'?s\s*,?\s*Sammlung[^()]*\((?P<year>1908|1912)\)"
    r"[^N]*?Nr\.?\s*(?P<num>\d+)\s*(?P<q>[A-Za-z](?:\.\d+)?)?",
    re.IGNORECASE,
)

# Hede catalogue (Danmarks og Norges mønter) — sometimes "H. Hede" or
# bare "Hede". Numbers can carry a letter (39A, 153b).
RE_HEDE = re.compile(
    r"(?:H\.\s*)?Hede[^A-Za-z0-9]+(?:[^N]*?Nr\.?\s*)?(?P<num>\d+)(?P<q>[A-Z]?)\b",
    re.IGNORECASE,
)

# Davenport European Crowns
RE_DAV = re.compile(
    r"Davenport[^N]*?Nr\.?\s*(?P<num>\d+)(?P<q>[A-Za-z]?)\b",
    re.IGNORECASE,
)

# Aagaard Frederik III (the specific 2011 monograph cited by IKMK on
# Glückstadt-mint Speciedaler issues).
RE_AAGAARD = re.compile(
    r"Aagaard[^A-Za-z0-9]+[^A-Za-z0-9]*(?:T\s*\d+\.\d+|(\d+(?:\.\d+)?))",
    re.IGNORECASE,
)


def _norm(num: str, q: str | None) -> str:
    return f"{num}{(q or '').strip().lower()}"


def extract_refs(literatur: str) -> dict[str, list[dict]]:
    """Return dict {catalogue_code: [{number, qualifier, cf}, ...]}."""
    refs: dict[str, list[dict]] = {}
    if not literatur:
        return refs
    # Lange (with cf-flag)
    for m in RE_LANGE.finditer(literatur):
        refs.setdefault("lange", []).append({
            "vol": "I" if m.group("year") == "1908" else "II",
            "num": m.group("num"),
            "q": (m.group("q") or "").strip(),
            "cf": bool(m.group("cf")),
            "norm": _norm(m.group("num"), m.group("q")),
        })
    # Hede
    for m in RE_HEDE.finditer(literatur):
        refs.setdefault("hede", []).append({
            "num": m.group("num"),
            "q": m.group("q") or "",
            "norm": _norm(m.group("num"), m.group("q")),
        })
    # Davenport
    for m in RE_DAV.finditer(literatur):
        refs.setdefault("dav", []).append({
            "num": m.group("num"),
            "q": (m.group("q") or "").strip(),
            "norm": _norm(m.group("num"), m.group("q")),
        })
    return refs


# ---------- Our YAML extraction --------------------------------------


def _norm_ref(value) -> str:
    return re.sub(r"\s+", "", str(value)).lower()


def index_our_coins(coins: list[dict]) -> dict[str, dict[str, list[dict]]]:
    """Index our coins by lange / hede / dav / km — for strict lookup."""
    index = {"lange": {}, "hede": {}, "dav": {}, "km": {}}
    for c in coins:
        cat = c.get("catalog") or {}
        for code in ("lange", "hede", "dav", "km"):
            v = cat.get(code)
            if v:
                index[code].setdefault(_norm_ref(v), []).append(c)
        # Also harvest "Lange# 80 A" forms from `others` list
        for o in cat.get("others") or []:
            mo = re.match(r"\s*Lange[#\s]*(\d+\s*[a-z]?)", str(o), re.IGNORECASE)
            if mo:
                index["lange"].setdefault(_norm_ref(mo.group(1)), []).append(c)
    return index


# ---------- Main matching loop ---------------------------------------


def _ikmk_summary(rec: dict) -> dict:
    """Pull the comparable facts out of an IKMK record."""
    pers = rec.get("linked_persons_corporations") or {}
    ruler = ""
    if isinstance(pers, dict):
        for v in pers.values():
            if not isinstance(v, dict):
                continue
            if v.get("type_name_de") in ("Münzherr", "Autorität", "Dargestellte/r"):
                items = v.get("items") or {}
                for it in items.values():
                    ruler = it.get("last_name_de") or ""
                    if ruler:
                        break
                if ruler:
                    break
    nominal = (rec.get("nominal") or {}).get("nominal_de") or ""
    mint_place = ""
    for m in (rec.get("mint") or []):
        if isinstance(m, dict):
            mint_place = m.get("place_name_de") or ""
            break
    weight = rec.get("weight") or ""
    diameter = rec.get("diameter") or ""
    avers_leg = (rec.get("avers") or {}).get("leg_text") or ""
    revers_leg = (rec.get("revers") or {}).get("leg_text") or ""
    return {
        "id": rec.get("ikmk_mds_id"),
        "title": rec.get("title"),
        "year_start": rec.get("year_start"),
        "year_end": rec.get("year_end"),
        "ruler": ruler,
        "nominal": nominal,
        "mint": mint_place,
        "weight": weight,
        "diameter": diameter,
        "avers_leg": avers_leg,
        "revers_leg": revers_leg,
        "literatur": rec.get("literatur") or "",
        "refs": extract_refs(rec.get("literatur") or ""),
        "permalink": rec.get("permalink"),
        "image_right": (rec.get("image_right") or {}).get("short"),
    }


def _diff_fields(ikmk: dict, ours: dict) -> dict:
    """What does IKMK add that we lack on this coin?"""
    diff = {}
    if ikmk["avers_leg"] and not (ours.get("inscription_obv") or "").strip():
        diff["inscription_obv"] = ikmk["avers_leg"]
    if ikmk["revers_leg"] and not (ours.get("inscription_rev") or "").strip():
        diff["inscription_rev"] = ikmk["revers_leg"]
    # diameter — IKMK string like "44 mm"
    if ikmk["diameter"]:
        ours_diam = ours.get("diameter_mm")
        if ours_diam in (None, 0):
            diff["diameter_mm"] = ikmk["diameter"]
    # additional Lange / Hede / Dav refs we don't have
    cat = ours.get("catalog") or {}
    for code in ("lange", "hede", "dav"):
        if ikmk["refs"].get(code) and not cat.get(code):
            # Take the first non-cf entry
            for r in ikmk["refs"][code]:
                if not r.get("cf"):
                    diff[f"catalog.{code}"] = r["norm"]
                    break
    return diff


RULER_FIRST_NAMES = {
    "johann", "hans", "christian", "friedrich", "frederick", "frederik",
    "ernst", "adolf", "philipp", "peter", "georg", "albrecht", "carl",
    "karl", "joachim", "augustenburg", "just",
}
DYNASTIC_LINES = {
    "sonderburg": "sonderburg",
    "gottorf": "gottorf", "gottorp": "gottorf",
    "glücksburg": "glücksburg", "glucksburg": "glücksburg",
    "plön": "plön", "ploen": "plön",
    "augustenburg": "augustenburg",
    "schaumburg": "schaumburg", "schauenburg": "schaumburg",
    "pinneberg": "schaumburg",  # Schaumburg-Pinneberg branch
    "norburg": "norburg",
    "lauenburg": "lauenburg",
}


def _ruler_tokens(text: str) -> tuple[set[str], set[str]]:
    text_l = text.lower()
    first_names = set()
    lines = set()
    for tok in re.findall(r"[a-zäöü]{3,}", text_l):
        if tok in RULER_FIRST_NAMES:
            first_names.add(tok)
        if tok in DYNASTIC_LINES:
            lines.add(DYNASTIC_LINES[tok])
    return first_names, lines


def _fuzzy_score(ikmk: dict, ours: dict) -> tuple[int, list[str]]:
    score = 0
    why = []
    # year — IKMK year_start can be str
    try:
        iy = int(ikmk.get("year_start") or 0) or None
    except (TypeError, ValueError):
        iy = None
    try:
        oy = int(ours.get("year_first") or 0) or None
    except (TypeError, ValueError):
        oy = None
    if iy and oy and abs(iy - oy) <= 1:
        score += 2
        why.append(f"year {iy}≈{oy}")
    elif iy and oy and abs(iy - oy) <= 3:
        score += 1
        why.append(f"year {iy}~{oy}")
    # Ruler — must overlap on (a) first name AND (b) dynastic line.
    # Generic country tokens like "schleswig" alone don't count.
    i_first, i_line = _ruler_tokens(ikmk.get("ruler") or "")
    o_first, o_line = _ruler_tokens(ours.get("ruler") or "")
    shared_first = i_first & o_first
    shared_line = i_line & o_line
    if shared_first and shared_line:
        score += 4
        why.append(f"ruler {sorted(shared_first)[0]}/{sorted(shared_line)[0]}")
    elif shared_first:
        score += 2
        why.append(f"ruler-first {sorted(shared_first)[0]}")
    elif shared_line:
        score += 1
        why.append(f"ruler-line {sorted(shared_line)[0]}")
    # Nominal — match a denomination word (≥5 chars to avoid junk)
    ours_nom = (ours.get("nominal") or "").lower()
    ikmk_nom = (ikmk.get("nominal") or "").lower()
    for tok in re.findall(r"[a-zäöüß]{5,}", ikmk_nom):
        if tok in ours_nom:
            score += 1
            why.append(f"nominal '{tok}'")
            break
    # Weight ±3 %
    try:
        wi = float(re.match(r"([\d.]+)", ikmk["weight"] or "").group(1))
        ow_raw = ours.get("weight_rough_g")
        if isinstance(ow_raw, list):
            for entry in ow_raw:
                if isinstance(entry, dict):
                    wo = entry.get("value")
                    if wo and abs(wi - wo) / wo < 0.03:
                        score += 2
                        why.append(f"weight {wi:.2f}≈{wo:.2f}")
                        break
        elif isinstance(ow_raw, (int, float)):
            if abs(wi - ow_raw) / ow_raw < 0.03:
                score += 2
                why.append(f"weight {wi:.2f}≈{ow_raw:.2f}")
    except Exception:
        pass
    return score, why


def main() -> int:
    index = json.loads(INDEX_PATH.read_text(encoding="utf-8"))
    sh_prefixes = index["by_project_location"]["schleswig_holstein"]
    schauen_prefixes = index["by_project_location"].get("_pre1640_schauenburg", [])
    targets = list(sh_prefixes) + list(schauen_prefixes)
    print(f"Target prefixes: {targets}")

    ikmk_ids: list[str] = []
    for p in targets:
        ikmk_ids.extend(index["issuers"][p]["ids_in_scope"])
    print(f"IKMK records to match: {len(ikmk_ids)}")

    # Load our SH coins
    yml = yaml.safe_load(YAML_PATH.read_text(encoding="utf-8"))
    our_coins = yml.get("coins", [])
    our_idx = index_our_coins(our_coins)
    print(f"Our SH coins: {len(our_coins)}  (lange={len(our_idx['lange'])} "
          f"hede={len(our_idx['hede'])} dav={len(our_idx['dav'])} "
          f"km={len(our_idx['km'])})")

    matches: list[dict] = []
    for nid in ikmk_ids:
        rec = json.loads((CACHE / f"{nid}.json").read_text(encoding="utf-8"))
        s = _ikmk_summary(rec)

        # 1. Strict catalogue-ref match
        ours_match = None
        match_reason = None
        for code in ("lange", "hede", "dav"):
            for ref in s["refs"].get(code, []):
                if ref.get("cf"):
                    continue
                lookup = our_idx[code].get(ref["norm"])
                if lookup:
                    ours_match = lookup[0]
                    match_reason = f"strict by {code} {ref['norm']}"
                    break
            if ours_match:
                break

        # 2. Fuzzy fallback
        fuzzy_candidates: list[tuple[int, dict, list[str]]] = []
        # Detect: IKMK has a Lange# but it's a NEW variant we don't have.
        ikmk_has_lange = bool(s["refs"].get("lange"))
        if not ours_match:
            try:
                iy = int(s.get("year_start") or 0)
            except (TypeError, ValueError):
                iy = 0
            for c in our_coins:
                try:
                    cy = int(c.get("year_first") or 0)
                except (TypeError, ValueError):
                    cy = 0
                if iy and cy and abs(iy - cy) > 5:
                    continue
                score, why = _fuzzy_score(s, c)
                if score >= 4:
                    fuzzy_candidates.append((score, c, why))
            fuzzy_candidates.sort(key=lambda x: -x[0])
            if fuzzy_candidates:
                top_score = fuzzy_candidates[0][0]
                ours_match = fuzzy_candidates[0][1]
                # Categorise:
                # - new_lange_variant: IKMK has Lange# but it isn't ours → actual new type
                # - fuzzy: high-confidence same-coin match without Lange#
                # - weak: low-confidence partial overlap
                if ikmk_has_lange:
                    tag = "new_lange_variant"
                elif top_score >= 7:
                    tag = "fuzzy"
                else:
                    tag = "weak"
                match_reason = (
                    f"{tag} score={top_score} "
                    f"({', '.join(fuzzy_candidates[0][2])})"
                )

        if ours_match:
            entry = {
                "ikmk_id": nid,
                "ikmk_title": s["title"],
                "ikmk_year": f"{s['year_start']}-{s['year_end']}",
                "ikmk_nominal": s["nominal"],
                "ikmk_ruler": s["ruler"],
                "ikmk_weight": s["weight"],
                "ikmk_diameter": s["diameter"],
                "ikmk_refs": s["refs"],
                "our_coin_id": ours_match.get("id"),
                "our_year_label": ours_match.get("year_label"),
                "our_nominal": ours_match.get("nominal"),
                "match_reason": match_reason,
                "ikmk_adds": _diff_fields(s, ours_match),
                "permalink": s["permalink"],
                "image_right": s["image_right"],
            }
            matches.append(entry)
        else:
            entry = {
                "ikmk_id": nid,
                "ikmk_title": s["title"],
                "ikmk_year": f"{s['year_start']}-{s['year_end']}",
                "ikmk_nominal": s["nominal"],
                "ikmk_ruler": s["ruler"],
                "ikmk_weight": s["weight"],
                "ikmk_diameter": s["diameter"],
                "ikmk_refs": s["refs"],
                "ikmk_avers_leg": s["avers_leg"],
                "ikmk_revers_leg": s["revers_leg"],
                "match_reason": "no_match",
                "permalink": s["permalink"],
                "image_right": s["image_right"],
            }
            matches.append(entry)

    # Bucket
    strict = [m for m in matches if m.get("match_reason", "").startswith("strict")]
    fuzzy = [m for m in matches if m.get("match_reason", "").startswith("fuzzy")]
    new_var = [m for m in matches if m.get("match_reason", "").startswith("new_lange_variant")]
    weak = [m for m in matches if m.get("match_reason", "").startswith("weak")]
    unmatched = [m for m in matches if m["match_reason"] == "no_match"]

    # For new-Lange-variants, group by Lange# to show unique-variant count
    from collections import defaultdict
    lange_groups: dict[str, list[dict]] = defaultdict(list)
    for m in new_var:
        for r in m.get("ikmk_refs", {}).get("lange", []):
            if not r.get("cf"):
                lange_groups[r["norm"]].append(m)
                break
        else:
            lange_groups["(cf-only)"].append(m)

    out = {
        "schleswig_holstein": {
            "totals": {
                "ikmk_records": len(matches),
                "strict_match": len(strict),
                "fuzzy_match": len(fuzzy),
                "new_lange_variant": len(new_var),
                "unique_new_lange_numbers": len(lange_groups),
                "weak_candidate": len(weak),
                "no_match (potential additions)": len(unmatched),
            },
            "strict_matches": strict,
            "fuzzy_matches": fuzzy,
            "new_lange_variants_by_lange": {
                lange: [{
                    "ikmk_id": m["ikmk_id"],
                    "year": m["ikmk_year"],
                    "ruler": m.get("ikmk_ruler"),
                    "weight": m.get("ikmk_weight"),
                    "diameter": m.get("ikmk_diameter"),
                    "best_our_coin": m.get("our_coin_id"),
                    "permalink": m.get("permalink"),
                } for m in records]
                for lange, records in sorted(lange_groups.items())
            },
            "weak_candidates": weak,
            "unmatched_records": unmatched,
        },
    }
    MATCH_JSON.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nWrote {MATCH_JSON.relative_to(REPO)}")

    # Markdown digest
    md: list[str] = []
    md.append("# IKMK ↔ schleswig_holstein.yml — match report\n")
    md.append(
        f"\n{len(matches)} IKMK records (Schleswig-Holstein-* + Holstein-Schauenburg "
        "in scope 1566–1914) matched against `data/locations/schleswig_holstein.yml`.\n",
    )
    md.append(
        f"\n* **Strict match (catalogue-ref overlap)**: {len(strict)}\n"
        f"* **Fuzzy match (high-confidence same coin, score≥7)**: {len(fuzzy)}\n"
        f"* **New Lange-# variant (IKMK has a Lange # we don't catalogue)**: "
        f"{len(new_var)} specimens across **{len(lange_groups)} unique Lange #**\n"
        f"* **Weak candidate (partial signal, score 4-6, no Lange#)**: {len(weak)}\n"
        f"* **No match**: {len(unmatched)}\n",
    )

    if strict:
        md.append("\n## Strict matches — enrichment candidates\n")
        md.append("\nIKMK records sharing a Lange / Hede / Davenport reference with one ")
        md.append("of our coins. The `ikmk_adds` column shows fields IKMK provides that ")
        md.append("we currently lack on the matched coin.\n")
        md.append("\n| IKMK | year | our coin | reason | IKMK adds |")
        md.append("|---|---|---|---|---|")
        for m in strict:
            adds = ", ".join(m["ikmk_adds"].keys()) or "—"
            md.append(
                f"| [{m['ikmk_id']}]({m['permalink']}) | {m['ikmk_year']} "
                f"| `{m['our_coin_id']}` | {m['match_reason']} | {adds} |",
            )

    if fuzzy:
        md.append("\n## Fuzzy matches (score≥7) — likely correct, spot-check\n")
        md.append("\n| IKMK | year | our coin | reason | IKMK adds |")
        md.append("|---|---|---|---|---|")
        for m in fuzzy:
            adds = ", ".join(m["ikmk_adds"].keys()) or "—"
            md.append(
                f"| [{m['ikmk_id']}]({m['permalink']}) | {m['ikmk_year']} "
                f"| `{m['our_coin_id']}` | {m['match_reason']} | {adds} |",
            )

    if new_var:
        md.append("\n## New Lange-# variants (potential YAML additions)\n")
        md.append(
            "\nIKMK records that share ruler+year+line with one of our "
            "coins but cite a Lange # we don't have catalogued. These "
            "are *separate types* in Lange's classification — not "
            "duplicates of our existing entries. Worth adding to YAML "
            "as new coins (or, if Krause groups them under one KM #, "
            "as Lange-sub-variant notes).\n",
        )
        md.append(
            f"\nGrouped by Lange # — {len(lange_groups)} unique #s, "
            f"{len(new_var)} total specimens. Specimens of the same "
            "Lange # are usually multiple physical coins of the same "
            "type held in IKMK.\n",
        )
        md.append("\n| Lange # | specimens | year(s) | ruler-line | sample IKMK |")
        md.append("|---|---:|---|---|---|")
        for lange, recs in sorted(lange_groups.items()):
            years = sorted({r["ikmk_year"].split("-")[0] for r in [
                {"ikmk_year": rr["ikmk_year"]} for rr in recs
            ] if r["ikmk_year"]})
            sample_ids = [r["ikmk_id"] for r in recs[:3]]
            sample_links = ", ".join(
                f"[{nid}](https://ikmk.smb.museum/object?id={nid})"
                for nid in sample_ids
            )
            # ruler from first record
            ruler = recs[0].get("ikmk_ruler") or ""
            line = ""
            for tok in re.findall(r"[a-zäöü]{4,}", ruler.lower()):
                if tok in DYNASTIC_LINES:
                    line = DYNASTIC_LINES[tok]
                    break
            md.append(
                f"| `Lange {lange}` | {len(recs)} | {','.join(years)} "
                f"| {line or '—'} | {sample_links} |",
            )

    if weak:
        md.append("\n## Weak candidates (score 4-6, no Lange #)\n")
        md.append(
            "\nPartial signal only — year + ruler-line. No Lange # in "
            "IKMK literatur to cross-walk against. Manual research "
            "needed; could be either an existing coin (we'd need to "
            "look up by inscription / weight pattern) or a new entry.\n",
        )
        md.append("\n| IKMK | year | nominal | best our coin | reason |")
        md.append("|---|---|---|---|---|")
        for m in weak:
            md.append(
                f"| [{m['ikmk_id']}]({m['permalink']}) | {m['ikmk_year']} "
                f"| {m.get('ikmk_nominal','')[:25]} | `{m['our_coin_id']}` | "
                f"{m['match_reason']} |",
            )

    if unmatched:
        md.append("\n## Unmatched — potential new entries\n")
        md.append("\nIKMK records with no Lange/Hede/Davenport overlap and no fuzzy ")
        md.append("year+ruler+nominal+weight match in our YAML. These could be:\n")
        md.append("\n* Coins we genuinely don't catalogue yet (real additions).")
        md.append("\n* Coins we have under a different KM# variant where we never recorded the Lange #.")
        md.append("\n* Specimens IKMK lists with sub-variant qualifiers we don't track.\n")
        md.append("\n| IKMK | year | nominal | ruler | weight | Lange | Hede | Dav |")
        md.append("|---|---|---|---|---|---|---|---|")
        for m in unmatched:
            l = ",".join(r["norm"] for r in m["ikmk_refs"].get("lange", []) if not r.get("cf")) or "—"
            h = ",".join(r["norm"] for r in m["ikmk_refs"].get("hede", [])) or "—"
            d = ",".join(r["norm"] for r in m["ikmk_refs"].get("dav", [])) or "—"
            md.append(
                f"| [{m['ikmk_id']}]({m['permalink']}) | {m['ikmk_year']} "
                f"| {m['ikmk_nominal'][:30]} | {m['ikmk_ruler'][:40]} "
                f"| {m['ikmk_weight']} | {l} | {h} | {d} |",
            )

    MATCH_MD.write_text("\n".join(md), encoding="utf-8")
    print(f"Wrote {MATCH_MD.relative_to(REPO)}")
    print(
        f"\nSUMMARY: strict={len(strict)}  fuzzy={len(fuzzy)}  no_match={len(unmatched)}",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
