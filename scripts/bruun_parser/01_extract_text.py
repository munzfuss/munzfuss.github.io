"""
Stage 1 — extract plain text from Bruun catalogue PDFs (Part I/II/III).

Inputs:  PDF files in /tmp/bruun_pdfs/{part1,part2,part3}.pdf
         (download instructions in README.md)

Outputs: scripts/cache/bruun/pages/{part1,part2,part3}.txt
         — page-delimited plain text, ~500 KB per part

Each page is preceded by a `========== PAGE N ==========` line so
downstream stages can recover page numbers (needed for `bruun_page`
citations in our YAML).

Re-run when a new Bruun part comes out (Part IV expected). Add the
new entry to PARTS, drop the PDF in /tmp/bruun_pdfs/, run.
"""
import sys
from pypdf import PdfReader
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lib.paths import BRUUN_CACHE  # noqa: E402

PDF_DIR = Path("/tmp/bruun_pdfs")
OUT_DIR = BRUUN_CACHE / "pages"
OUT_DIR.mkdir(parents=True, exist_ok=True)

PARTS = [
    ("part1", "Bruun Part I (Sept 2024 — Copenhagen)"),
    ("part2", "Bruun Part II (Mar 2025 — Zurich)"),
    ("part3", "Bruun Part III (Oct 2025 — Zurich)"),
    ("part4", "Bruun Part IV (Mar 2026 — New York)"),
    # Add ("part5", "...") when Part V is published
]


def main():
    for slug, label in PARTS:
        pdf_path = PDF_DIR / f"{slug}.pdf"
        if not pdf_path.exists():
            print(f"  ! missing {pdf_path} — see scripts/bruun_parser/README.md to download")
            continue
        print(f"=== {label} → {pdf_path}")
        reader = PdfReader(str(pdf_path))
        n = len(reader.pages)
        print(f"  pages: {n}")

        out_path = OUT_DIR / f"{slug}.txt"
        with out_path.open("w") as f:
            for i, page in enumerate(reader.pages):
                try:
                    text = page.extract_text() or ""
                except Exception as e:
                    text = ""
                    print(f"  ! page {i+1} extract failed: {e}")
                f.write(f"\n\n========== PAGE {i+1} ==========\n\n")
                f.write(text)
                if (i + 1) % 50 == 0:
                    print(f"    ...{i+1}/{n}")
        print(f"  → {out_path} ({out_path.stat().st_size//1024} KB)")


if __name__ == "__main__":
    main()
