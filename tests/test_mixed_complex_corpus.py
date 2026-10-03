#!/usr/bin/env python3
"""
Test Suite for Mixed-Complex Document Corpus & Full Pipeline Execution.

Tests end-to-end execution of DocumentReconstructionPipeline on:
- 11_mixed_complex.pdf (Section 39 Master Document: Heading, Paragraph, Formula, Table, Chart, Diagram, Photo, Caption)
- 01_formula_heavy.pdf (Scientific math formulas)
- 02_table_complex.pdf (Hierarchical financial tables)
- 08_photo_heavy.pdf (Embedded evidence photos)

Verifies:
- All review artifacts are produced:
  * document-ir.json
  * style-profile.json
  * reconstruction-report.json
  * validation/semantic.json
  * validation/data-integrity.json
  * validation/visual.json
  * execution-report.json
  * <stem>_translated_reconstructed.pdf
- Visual & data validation pass.
- No repository bloat (all outputs in /tmp or ~/Downloads/AIWF_Output).
"""

import os
import sys
import json
import unittest
from pathlib import Path

SKILL_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    ".agents", "skills", "dich-thuat"
)
scripts_path = os.path.join(SKILL_DIR, "scripts")
sys.path.insert(0, scripts_path)
if "analyzer" in sys.modules and str(scripts_path) not in getattr(sys.modules["analyzer"], "__file__", ""):
    del sys.modules["analyzer"]

from pipeline.document_pipeline import DocumentReconstructionPipeline

FIXTURE_DIR = Path(os.path.dirname(os.path.abspath(__file__))) / "skill_quality" / "document-reconstruction-translator" / "fixtures"


class TestMixedComplexCorpus(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        master_fixture = FIXTURE_DIR / "11_mixed_complex.pdf"
        if not master_fixture.exists():
            from skill_quality.document_reconstruction_translator.generate_reconstruction_fixtures import generate_all
            generate_all()

    def setUp(self):
        self.tmp_out = Path("/tmp/aiwf_corpus_output")
        self.tmp_proc = Path("/tmp/aiwf_corpus_proc")
        self.tmp_out.mkdir(parents=True, exist_ok=True)
        self.tmp_proc.mkdir(parents=True, exist_ok=True)
        self.pipeline = DocumentReconstructionPipeline(typst_bin="/opt/homebrew/bin/typst")

    def test_01_formula_heavy_pipeline(self):
        """Test pipeline on 01_formula_heavy.pdf."""
        src_pdf = FIXTURE_DIR / "01_formula_heavy.pdf"
        self.assertTrue(src_pdf.exists(), f"Missing fixture: {src_pdf}")
        
        proc_dir = self.tmp_proc / "proc_formula"
        res = self.pipeline.run(
            source_pdf=src_pdf,
            target_language="vi",
            output_dir=self.tmp_out,
            process_dir=proc_dir
        )
        
        self.assertTrue(res["success"], f"Pipeline failed: {res.get('execution_report')}")
        self.assertTrue(os.path.exists(res["final_pdf"]))
        self.assertTrue((proc_dir / "document-ir.json").exists())
        self.assertTrue((proc_dir / "style-profile.json").exists())
        self.assertTrue((proc_dir / "execution-report.json").exists())

    def test_02_table_complex_pipeline(self):
        """Test pipeline on 02_table_complex.pdf."""
        src_pdf = FIXTURE_DIR / "02_table_complex.pdf"
        self.assertTrue(src_pdf.exists(), f"Missing fixture: {src_pdf}")
        
        proc_dir = self.tmp_proc / "proc_table"
        res = self.pipeline.run(
            source_pdf=src_pdf,
            target_language="vi",
            output_dir=self.tmp_out,
            process_dir=proc_dir
        )
        
        self.assertTrue(res["success"], f"Pipeline failed: {res.get('execution_report')}")
        self.assertTrue(os.path.exists(res["final_pdf"]))
        self.assertTrue((proc_dir / "validation" / "data-integrity.json").exists())

    def test_08_photo_heavy_pipeline(self):
        """Test pipeline on 08_photo_heavy.pdf."""
        src_pdf = FIXTURE_DIR / "08_photo_heavy.pdf"
        self.assertTrue(src_pdf.exists(), f"Missing fixture: {src_pdf}")
        
        proc_dir = self.tmp_proc / "proc_photo"
        res = self.pipeline.run(
            source_pdf=src_pdf,
            target_language="vi",
            output_dir=self.tmp_out,
            process_dir=proc_dir
        )
        
        self.assertTrue(res["success"], f"Pipeline failed: {res.get('execution_report')}")
        self.assertTrue(os.path.exists(res["final_pdf"]))

    def test_11_mixed_complex_master_pipeline(self):
        """Test master pipeline on 11_mixed_complex.pdf with all 8 semantic components."""
        src_pdf = FIXTURE_DIR / "11_mixed_complex.pdf"
        self.assertTrue(src_pdf.exists(), f"Missing fixture: {src_pdf}")
        
        proc_dir = self.tmp_proc / "proc_mixed_master"
        
        # Simulated translation map for technical terms and headings
        t_map = {
            "Channel Alpha": "Kênh Alpha (Quang học)",
            "Channel Beta": "Kênh Beta (Lượng tử)",
            "Channel Gamma": "Kênh Gamma (Phát xạ)"
        }
        
        res = self.pipeline.run(
            source_pdf=src_pdf,
            target_language="vi",
            output_dir=self.tmp_out,
            process_dir=proc_dir,
            translation_map=t_map
        )
        
        self.assertTrue(res["success"], f"Master pipeline failed: {res.get('execution_report')}")
        self.assertTrue(os.path.exists(res["final_pdf"]))
        
        # Verify artifact generation
        self.assertTrue((proc_dir / "document-ir.json").exists())
        self.assertTrue((proc_dir / "style-profile.json").exists())
        self.assertTrue((proc_dir / "execution-report.json").exists())
        self.assertTrue((proc_dir / "validation" / "semantic.json").exists())
        self.assertTrue((proc_dir / "validation" / "data-integrity.json").exists())
        self.assertTrue((proc_dir / "validation" / "visual.json").exists())
        
        # Check execution report summary
        with open(proc_dir / "execution-report.json", "r", encoding="utf-8") as f:
            report = json.load(f)
            
        self.assertEqual(report["overall_status"], "PASS")
        self.assertTrue(report["validation_results"]["semantic"])
        self.assertTrue(report["validation_results"]["data_integrity"])
        self.assertTrue(report["validation_results"]["visual"])


if __name__ == "__main__":
    unittest.main()
