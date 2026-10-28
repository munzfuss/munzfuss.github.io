"""Every dossier in docs/research/ must be listed in docs/research/README.md.

A dossier nobody can find is research a later session repeats. The README's
«Index» section is the entry point; this test fails when a new file is added
without its row.
"""
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
RESEARCH = ROOT / "docs" / "research"


class ResearchIndexTest(unittest.TestCase):
    def test_every_dossier_is_indexed(self):
        readme = (RESEARCH / "README.md").read_text(encoding="utf-8")
        missing = [
            p.name for p in sorted(RESEARCH.glob("*.md"))
            if p.name != "README.md" and f"]({p.name})" not in readme
        ]
        self.assertEqual(missing, [], f"not indexed in docs/research/README.md: {missing}")


if __name__ == "__main__":
    unittest.main()
