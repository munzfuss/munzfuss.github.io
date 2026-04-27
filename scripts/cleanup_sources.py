#!/usr/bin/env python3
"""
One-off cleanup: normalise the Sources column.

Rules:
  1) A coin-specific web URL belongs directly in coin.sources as the link
     the user sees in the «Джерело» column — not hidden behind «[N]».
  2) A «[N]» reference is reserved for:
       - general-scope web pages (Wikipedia articles on the denomination,
         Nationalbank overviews, catalogue portals);
       - offline sources (printed catalogues, academic works).
  3) Orphan refs (defined in the sidecar but not linked from anywhere) get
     dropped if they are single-coin pointers. General orphans stay.

Run once:
    python scripts/cleanup_sources.py
"""
from __future__ import annotations
import pathlib
from ruamel.yaml import YAML
from ruamel.yaml.scalarstring import LiteralScalarString

yaml = YAML()
yaml.preserve_quotes = True
yaml.width = 10000
yaml.indent(mapping=2, sequence=4, offset=2)

# ----- Step 1: direct-URL promotions for single-coin #refN links -----
# coin_id -> (ref_label, direct_url)
PROMOTIONS = {
    "km-250-chr-v-1767":         ("coinsbook.net",  "https://www.coinsbook.net/coins/silver-coin-24-skilling-danske-christian-vii-17440"),
    "km-631-chr-v-1778":         ("WorldCoinGallery", "https://worldcoingallery.com/countries/Denmark.html"),
    "km-616-chr-v-1771":         ("Numista",         "https://en.numista.com/catalogue/pieces958.html"),
    "km-615-1-2-3-chr-v-1771":   ("Numista",         "https://en.numista.com/catalogue/pieces44799.html"),
    "km-138-1-chr-v-1787":       ("Numista",         "https://en.numista.com/catalogue/pieces32842.html"),
    "km-135-chr-v-1787":         ("Stacks Bowers",   "https://auctions.stacksbowers.com/lots/view/3-1G9WQ5/denmark-schleswig-holstein-23-speciedaler-1787-mf-altonapoppenbuttel-mint-christian-vii-ngc-fine-details-cleaned"),
    "km-130-chr-v-1787":         ("Stacks Bowers",   "https://auctions.stacksbowers.com/lots/view/3-1G6V6M/denmark-schleswig-holstein-13-speciedaler-1787-bmf-altonapoppenbuttel-mint-christian-vii-ngc-ms-64"),
    "km-126-chr-v-1787":         ("Numista",         "https://en.numista.com/catalogue/pieces43459.html"),
    "km-124-chr-v-1787":         ("Numista",         "https://en.numista.com/catalogue/pieces38173.html"),
    "km-721-chr-v-1841":         ("Infinity Coins",  "https://www.infinitycoins.com/Products/1842-denmark-4-rigsbankskilling-1-schilling-courant--christian-viii.aspx"),
    "km-160-1850":               ("Numista",         "https://en.numista.com/catalogue/pieces39944.html"),
    "km-162-1850":               ("Numista",         "https://en.numista.com/catalogue/pieces39943.html"),
    # km-x006-1850 (1 Schilling, Provisional Government) — no individual URL,
    # keeps #ref19 which documents the series via Wikipedia.
}

# ----- Step 2: refs to remove from the sidecar -----
# refN that point to a single coin (whose URL is now promoted) or orphaned coin-specific
REMOVE_REFS = {
    "ref3",   # KM# 250 — promoted to km-250-chr-v-1767
    "ref4",   # KM# 12 — orphan, not in our coin set
    "ref5",   # KM# 631 — promoted
    "ref6",   # KM# 616 — promoted
    "ref7",   # KM# 615 — promoted
    "ref9",   # KM# 138.1 — promoted
    "ref10",  # KM# 135 — promoted
    "ref11",  # KM# 130 — promoted
    "ref12",  # KM# 128 — orphan; coin already has its own numista+coinfactswiki sources
    "ref13",  # KM# 126 — promoted
    "ref14",  # KM# 124 — promoted
    "ref18",  # KM# 721 — promoted
}


def promote_coin_source(coin, ref_label: str, direct_url: str):
    """Replace any source whose url starts with '#ref' by a direct-URL source.
    If none found, append a new source."""
    sources = coin.get("sources") or []
    replaced = False
    for s in sources:
        url = s.get("url") or ""
        if url.startswith("#ref"):
            s["type"] = "numista" if "numista.com" in direct_url else "auction" if "stacksbowers" in direct_url else "web"
            s["url"]  = direct_url
            s["ref"]  = ref_label
            replaced = True
            break
    if not replaced:
        # append
        kind = "numista" if "numista.com" in direct_url else "auction" if "stacksbowers" in direct_url else "web"
        sources.append({"type": kind, "url": direct_url, "ref": ref_label})
        coin["sources"] = sources
    return replaced


def main():
    # --- patch coins ---
    cp = pathlib.Path("data/locations/schleswig.yml")
    data = yaml.load(cp.read_text())

    promoted = 0
    for coin in data.get("coins", []) or []:
        cid = coin.get("id")
        if cid in PROMOTIONS:
            label, url = PROMOTIONS[cid]
            if promote_coin_source(coin, label, url):
                promoted += 1
                print(f"  promoted {cid} → {url[:60]}")

    with open(cp, "w") as f:
        yaml.dump(data, f)
    print(f"\nPromoted {promoted} coin sources\n")

    # --- patch references sidecar ---
    rp = pathlib.Path("data/locations/schleswig-references.yml")
    refs = yaml.load(rp.read_text())
    before = len(refs.get("entries", []))
    refs["entries"] = [e for e in refs.get("entries", []) if e.get("id") not in REMOVE_REFS]
    after = len(refs["entries"])
    with open(rp, "w") as f:
        yaml.dump(refs, f)
    print(f"References: {before} → {after}  (removed {before - after})")

    # --- shorten ref19 to general description (URLs now in coins) ---
    for e in refs.get("entries", []):
        if e.get("id") == "ref19":
            content = e.get("content", {})
            content["de"] = LiteralScalarString(
                "<b>Provisorische Regierung Schleswig-Holstein 1850–1851</b>: "
                "Kupfer-Scheidemünzen (KM# 160 «1 Dreiling», KM# 162 «1 Sechsling», "
                "unnumeriertes «1 Schilling») in der Tradition der Schilling-"
                "Sch.-H.-Courant-Theilung · Übersicht in Wikipedia (en): "
                "<i>Schleswig-Holstein speciethaler</i> — "
                "<a href=\"https://en.wikipedia.org/wiki/Schleswig-Holstein_speciethaler\" "
                "target=\"_blank\">en.wikipedia.org/wiki/Schleswig-Holstein_speciethaler</a>"
            )
            content["en"] = LiteralScalarString(
                "<b>Provisional Government of Schleswig-Holstein, 1850–1851</b>: "
                "copper petty coins (KM# 160 «1 Dreiling», KM# 162 «1 Sechsling», "
                "un-catalogued «1 Schilling») struck in the Schilling-Sch.-H.-"
                "Courant subdivision · overview in Wikipedia (en): "
                "<i>Schleswig-Holstein speciethaler</i> — "
                "<a href=\"https://en.wikipedia.org/wiki/Schleswig-Holstein_speciethaler\" "
                "target=\"_blank\">en.wikipedia.org/wiki/Schleswig-Holstein_speciethaler</a>"
            )
            content["uk"] = LiteralScalarString(
                "<b>Провізійний уряд Шлезвіг-Гольштейну, 1850–1851</b>: мідні "
                "розмінні монети (KM# 160 «1 Dreiling», KM# 162 «1 Sechsling», "
                "некаталогізована «1 Schilling») у рамках поділу Schilling-"
                "Sch.-H.-Courant · огляд у Wikipedia (en): "
                "<i>Schleswig-Holstein speciethaler</i> — "
                "<a href=\"https://en.wikipedia.org/wiki/Schleswig-Holstein_speciethaler\" "
                "target=\"_blank\">en.wikipedia.org/wiki/Schleswig-Holstein_speciethaler</a>"
            )
            print("  ref19 content shortened (general overview only)")

    with open(rp, "w") as f:
        yaml.dump(refs, f)


if __name__ == "__main__":
    main()
