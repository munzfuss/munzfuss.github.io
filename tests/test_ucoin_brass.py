"""ucoin «Brass» maps to the schema metal «brass», not the «silver» default."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts" / "maintenance"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from build_ucoin_seed import detect_metal  # noqa: E402
from lib.schema import Coin  # noqa: E402


class UcoinBrassTest(unittest.TestCase):
    def test_brass(self):
        self.assertEqual(detect_metal("Brass", "1 Sechsling"), "brass")

    def test_copper_unchanged(self):
        self.assertEqual(detect_metal("Copper", "1 Sechsling"), "copper")

    def test_schema_accepts_brass(self):
        self.assertIn("brass", Coin.model_fields["metal"].annotation.__args__[0].__args__)


if __name__ == "__main__":
    unittest.main()
