"""Offline smoke tests using synthetic supplier PDFs only."""
import hashlib
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "demo" / "fixtures"
SCRIPT = ROOT / "src" / "extract_pdf_fields.py"


class SyntheticDemoTest(unittest.TestCase):
    def test_expected_routes_source_preservation_and_repeatability(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            input_dir = base / "input"
            input_dir.mkdir()
            for file in FIXTURES.glob("*.pdf"):
                shutil.copy2(file, input_dir / file.name)
            source_hashes = {
                p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                for p in input_dir.glob("*.pdf")
            }
            self.assertEqual(len(source_hashes), 7)
            for run_no in (1, 2):
                root = base / "output" / f"run_{run_no}"
                command = [sys.executable, str(SCRIPT), "--input", str(input_dir),
                           "--output-root", str(root), "--output", "extraction_report.xlsx",
                           "--scan-policy", "manual_review"]
                result = subprocess.run(command, capture_output=True, text=True, check=True)
                self.assertIn("Successful: 5", result.stdout)
                self.assertIn("Manual review: 1", result.stdout)
                self.assertIn("Failed: 1", result.stdout)
                self.assertEqual(len(list((root / "processed").rglob("*.pdf"))), 5)
                self.assertEqual(len(list((root / "manual_review").rglob("*.pdf"))), 1)
                self.assertEqual(len(list((root / "failed").rglob("*.pdf"))), 1)
                self.assertTrue((root / "extraction_report.xlsx").is_file())
                self.assertTrue((root / "processed" / "Westbay Finishes LLC" /
                                 "Westbay Finishes LLC_89075.pdf").is_file())
            self.assertEqual(source_hashes, {
                p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                for p in input_dir.glob("*.pdf")
            })
            self.assertTrue((base / "output" / "run_1" / "extraction_report.xlsx").exists())


if __name__ == "__main__":
    unittest.main()
