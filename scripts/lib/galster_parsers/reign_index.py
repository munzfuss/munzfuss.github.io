"""Skip-parser for reign-overview tables (`c2galst.htm`, `f1galst.htm`).

These pages carry a TABLE of all coins for a reign (Christian II,
Frederik I — danskmoent.dk's «- oversigt efter Galster» summary
view), not individual coin data. Each row in the table points at a
dedicated coin page (`chr/c2g37.htm` etc.) which already gets parsed
through the standard module — so the overview itself is redundant
for our seed.

Returning a `skip: True` sentinel tells the parser dispatcher to
write the JSON sidecar (for cache completeness + audit) and tells
`build_galster_denmark_seed.py::collect_entries` to drop the page.

Future extension slot: if a downstream consumer needs the overview
table as cross-validation data (e.g. «every coin page our parser
processes should ALSO appear in the reign index, else we missed a
sub-variant»), that comparison logic can replace the skip here.
"""
from __future__ import annotations

from pathlib import Path


def parse_page(html_path: Path, text: str) -> dict:
    return {
        "source_file": html_path.name,
        "source_url_hint": (
            "https://www.danskmoent.dk/" + html_path.name.replace("_", "/")
        ),
        "page_shape": "reign_index",
        "skip": True,
        "skip_reason": (
            "reign-overview table (table-of-contents view of all coins "
            "for a reign — redundant since each coin has its own page)"
        ),
        "raw_text_excerpt": text[:2000],
    }
