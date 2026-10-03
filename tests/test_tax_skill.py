"""Characterization tests cho skill tu-van-thue (CLI tax_calculator.py giữ tương thích ngược)."""
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / ".agents" / "skills" / "tu-van-thue"
GOLDEN = ROOT / "tests" / "fixtures" / "tax" / "tncn_golden.json"


class TncnCalculatorGolden(unittest.TestCase):
    def test_cli_output_unchanged(self):
        golden = json.loads(GOLDEN.read_text(encoding="utf-8"))
        script = SKILL / "scripts" / "tax_calculator.py"
        for name, case in golden.items():
            with self.subTest(case=name):
                r = subprocess.run([sys.executable, str(script)] + case["args"],
                                   capture_output=True, text=True)
                self.assertEqual(r.returncode, case["rc"])
                self.assertEqual(r.stdout, case["stdout"])


if __name__ == "__main__":
    unittest.main()
