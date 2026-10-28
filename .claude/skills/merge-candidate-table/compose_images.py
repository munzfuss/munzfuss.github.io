#!/usr/bin/env python3
"""Compose a side-by-side comparison image for a merge-candidate table.

One PNG, one labelled row per type / record, each row a strip of coin images
with a caption under it — the form the curator compares by eye (Zinck GIFs from
danskmoent, a crop of a Bruun catalogue page, a Numista photo saved from the
browser).

Usage:
    .venv/bin/python .claude/skills/merge-candidate-table/compose_images.py spec.json out.png

spec.json:
    {"rows": [
      {"title": "Hede Norge 8B · 1649–1651 · «PG og kløver» = KM 37 · Dav 3588",
       "caption": "Zinck 8B 1649 | Bruun 9616, 1650: KM-37; Dav-3588; Hede-8B",
       "images": [
         {"url": "https://www.danskmoent.dk/zinck/zinck5/5z290nf3h8b.gif"},
         {"pdf": "scripts/cache/bruun/part1.pdf", "page": 259,
          "crop60": [40, 95, 460, 345]},
         {"path": "/abs/path/numista.png"}
       ]}
    ]}

Image sources:
  url    — fetched with a browser User-Agent (danskmoent answers bots with a
           challenge page). Numista photos answer 403 to any script: open the
           page in Chrome, `zoom` the photo region with save_to_disk, pass the
           saved PNG as `path`.
  pdf    — a page rendered with pdftoppm; `crop60` is the box in the
           coordinates of a 60-dpi render (render the page at -r 60 once,
           read the box off it), re-rendered at 160 dpi for the crop.
  path   — any local image.
Optional per image: "height" (default 220). Arrows («→») are missing from
Helvetica — write «=» or words in titles.
"""
from __future__ import annotations

import io
import json
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

REPO = Path(__file__).resolve().parents[3]
UA = "Mozilla/5.0 (Macintosh)"
FONT = "/System/Library/Fonts/Helvetica.ttc"


def _load(spec: dict) -> Image.Image:
    if "url" in spec:
        req = urllib.request.Request(spec["url"], headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=60) as r:
            return Image.open(io.BytesIO(r.read()))
    if "pdf" in spec:
        pdf = Path(spec["pdf"])
        pdf = pdf if pdf.is_absolute() else REPO / pdf
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "p"
            subprocess.run(["pdftoppm", "-f", str(spec["page"]), "-l", str(spec["page"]),
                            "-r", "160", "-png", str(pdf), str(out)], check=True)
            img = Image.open(next(Path(td).glob("p*.png"))).copy()
        if "crop60" in spec:
            k = 160 / 60
            img = img.crop(tuple(int(v * k) for v in spec["crop60"]))
        return img
    return Image.open(spec["path"])


def _fit(img: Image.Image, h: int) -> Image.Image:
    img = img.convert("RGB")
    return img.resize((max(1, int(img.width * h / img.height)), h))


def compose(spec: dict, out: str, width: int = 1500) -> None:
    title_f = ImageFont.truetype(FONT, 28)
    cap_f = ImageFont.truetype(FONT, 24)
    rows = []
    for row in spec["rows"]:
        rows.append((row.get("title", ""), row.get("caption", ""),
                     [_fit(_load(s), s.get("height", 220)) for s in row["images"]]))
    height = sum(40 + max(i.height for i in ims) + 50 for _, _, ims in rows) + 20
    canvas = Image.new("RGB", (width, height), "white")
    d = ImageDraw.Draw(canvas)
    y = 10
    for title, cap, ims in rows:
        d.text((20, y), title, fill="black", font=title_f)
        y += 40
        x = 20
        for im in ims:
            canvas.paste(im, (x, y))
            x += im.width + 30
        y += max(i.height for i in ims) + 6
        d.text((20, y), cap, fill=(80, 80, 80), font=cap_f)
        y += 44
    canvas.crop((0, 0, width, y)).save(out)
    print(f"wrote {out} ({width}x{y})")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit(__doc__)
    compose(json.loads(Path(sys.argv[1]).read_text(encoding="utf-8")), sys.argv[2])
