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

# Bản dịch theo id đơn vị cho các fixture tổng hợp (pipeline giao PDF chỉ khi agent đã cung cấp đủ bản dịch).
# Một số fixture sinh ra với font thiếu glyph tiếng Việt nên văn bản nguồn có ký tự "·": bản dịch dưới đây là văn bản chuẩn.
TRANSLATIONS = {
    "formula": {
        "p1_txt_0": "Báo cáo Vật lý Lý thuyết và Cơ học Lượng tử",
        "p1_txt_1": "1. Cơ sở Toán học và Các phép suy dẫn",
        "p1_txt_2": "Trong phần này chúng ta phân tích quan hệ tán sắc năng lượng và các tích phân đường đi.",
        "p1_txt_6": "Delta x * Delta p >= hbar / 2",
        "p1_txt_7": "Các công thức trên chi phối trạng thái cân bằng nhiệt khi T = 298.15 K.",
    },
    "table": {
        "p1_txt_0": "Báo Cáo Tài Chính Hợp Nhất & Kiểm Toán Chi Phí 2025",
        "p1_txt_1": "Bảng 1: Phân bổ ngân sách nghiên cứu và triển khai (R&D)",
        "p1_txt_8": "Ghi chú: Toàn bộ số liệu đã qua soát xét theo chuẩn VAS/IFRS.",
    },
    "photo": {
        "p1_txt_0": "Báo cáo Kiểm tra Chất lượng Hiện trường và Giám định",
        "p1_txt_1": "Trạm 4 - Bộ hiệu chuẩn Dàn cảm biến",
        "p1_txt_2": "Chứng cứ vật lý được ghi nhận trong đợt kiểm tra hiện trường ngày 2026-04-15.",
        "p1_txt_4": "Ảnh 1: Bằng chứng ảnh chụp việc hiệu chuẩn đầu cuối cảm biến trong chân không.",
        "p1_txt_5": "Tất cả số sê-ri khớp với mã sổ đăng ký tài sản SN-8849-B2.",
    },
    "master": {
        "p1_txt_0": "Báo Cáo Nghiên Cứu Kỹ Thuật Vi Mạch Lượng Tử 2026",
        "p1_txt_1": "Tài liệu này tổng hợp toàn bộ kết quả phân tích cấu trúc, hiệu năng tính toán và mô phỏng thực nghiệm.",
        "p1_txt_2": "Thiết bị thử nghiệm đạt độ nhạy cao với sai số đo lường dưới 0.05% trong điều kiện 4.2 Kelvin.",
        "p1_txt_3": "Công thức truyền dẫn xác suất sóng lượng tử:",
        "p1_txt_9": "Biểu đồ Phân Bố Tín Hiệu (Signal Distribution):",
        "p1_txt_11": "Sơ đồ Kết Nối Modul (System Topology):",
        "p1_txt_12": "Bộ kích sóng Bộ giải mã tín hiệu",
        "p1_txt_10": "Biểu đồ 1: Công suất phát tại 3 dải tần thực nghiệm.",
        "p1_txt_13": "Sơ đồ 1: Luồng xử lý tuần tự qua vi mạch lượng tử.",
        "p1_txt_15": "Hình 1: Ảnh chụp vi mạch mẫu quang học lượng tử tại phòng sạch Class 100.",
        "p1_txt_16": "Kết luận: Toàn bộ 8 thành phần kỹ thuật đã được kiểm chứng hoạt động đồng bộ.",
    },
}


class TestMixedComplexCorpus(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        master_fixture = FIXTURE_DIR / "11_mixed_complex.pdf"
        if not master_fixture.exists():
            import importlib.util
            gen_path = Path(__file__).resolve().parent / "skill_quality" / "document-reconstruction-translator" / "generate_reconstruction_fixtures.py"
            spec = importlib.util.spec_from_file_location("_gen_reconstruction_fixtures", gen_path)
            gen = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(gen)
            gen.generate_all()

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
            process_dir=proc_dir,
            translation_map=TRANSLATIONS["formula"]
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
            process_dir=proc_dir,
            translation_map=TRANSLATIONS["table"]
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
            process_dir=proc_dir,
            translation_map=TRANSLATIONS["photo"]
        )
        
        self.assertTrue(res["success"], f"Pipeline failed: {res.get('execution_report')}")
        self.assertTrue(os.path.exists(res["final_pdf"]))

    def test_11_mixed_complex_master_pipeline(self):
        """Test master pipeline on 11_mixed_complex.pdf with all 8 semantic components."""
        src_pdf = FIXTURE_DIR / "11_mixed_complex.pdf"
        self.assertTrue(src_pdf.exists(), f"Missing fixture: {src_pdf}")
        
        proc_dir = self.tmp_proc / "proc_mixed_master"
        
        t_map = TRANSLATIONS["master"]
        
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
