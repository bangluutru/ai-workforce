#!/usr/bin/env python3
"""
Test Suite for AIWF Validation Engines and Self-Repair Loop
(DataValidator, SemanticValidator, VisualValidator, ObjectSpecificValidator, SelfRepairEngine)
"""

import sys
import os
import unittest

SKILL_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    ".agents", "skills", "dich-thuat"
)
sys.path.insert(0, os.path.join(SKILL_DIR, "scripts"))

from ir.models import (
    DocumentIR, SemanticObject, SemanticObjectType, ObjectGeometry, 
    ConfidenceMetrics, ReconstructionStrategy, DocumentStyleProfile
)
from validation.data_validator import DataValidator
from validation.semantic_validator import SemanticValidator
from validation.visual_validator import VisualValidator
from validation.object_validators import ObjectSpecificValidator
from validation.self_repair_engine import SelfRepairEngine


class TestValidationAndRepair(unittest.TestCase):

    def setUp(self):
        self.tmp_dir = "/tmp/aiwf_val_tests"
        os.makedirs(self.tmp_dir, exist_ok=True)

    def test_data_validator_clean_and_corrupted(self):
        """Test DataValidator detects numeric & percentage corruption."""
        validator = DataValidator()
        
        # 1. Clean Document IR
        clean_ir = DocumentIR(document_id="clean_doc", source_pdf="dummy.pdf")
        clean_ir.add_object(SemanticObject(
            id="p1",
            type=SemanticObjectType.PARAGRAPH,
            source_content="Doanh số tăng 25.5% đạt 500 triệu VND trong năm 2025.",
            translated_content="Doanh số tăng 25.5% đạt 500 triệu VND trong năm 2025."
        ))
        res_clean = validator.validate_document(clean_ir)
        self.assertTrue(res_clean["passed"])
        self.assertEqual(len(res_clean["violations"]), 0)

        # 2. Corrupted Document IR (25.5% -> 22.5%)
        corrupt_ir = DocumentIR(document_id="corrupt_doc", source_pdf="dummy.pdf")
        corrupt_ir.add_object(SemanticObject(
            id="p2",
            type=SemanticObjectType.PARAGRAPH,
            source_content="Tỷ lệ đạt chuẩn là 97.3% và dung tích 500ml.",
            translated_content="Tỷ lệ đạt chuẩn là 93.7% và dung tích 500ml."  # 97.3% altered to 93.7%
        ))
        res_corrupt = validator.validate_document(corrupt_ir)
        self.assertFalse(res_corrupt["passed"])
        self.assertTrue(any(v["type"] == "PERCENT_CORRUPTION" for v in res_corrupt["violations"]))

    def test_semantic_validator_omission_and_placeholders(self):
        """Test SemanticValidator catches omitted content, forbidden placeholders (.), and residual CJK."""
        validator = SemanticValidator()

        # 1. Dot Placeholder Violation
        ir_placeholder = DocumentIR(document_id="dot_doc", source_pdf="dummy.pdf", target_language="vi")
        ir_placeholder.add_object(SemanticObject(
            id="p_dot",
            type=SemanticObjectType.PARAGRAPH,
            source_content="Nội dung quan trọng cần dịch đầy đủ.",
            translated_content="."  # Forbidden placeholder
        ))
        res_dot = validator.validate_document(ir_placeholder)
        self.assertFalse(res_dot["passed"])
        self.assertTrue(any(v["type"] == "PLACEHOLDER_DETECTED" for v in res_dot["violations"]))

        # 2. Residual CJK Violation
        ir_cjk = DocumentIR(document_id="cjk_doc", source_pdf="dummy.pdf", source_language="ja", target_language="vi")
        ir_cjk.add_object(SemanticObject(
            id="p_cjk",
            type=SemanticObjectType.PARAGRAPH,
            source_content="製品の品質基準について説明します。",
            translated_content="Giải thích về tiêu chuẩn 品質基準 của sản phẩm."  # Untranslated Kanji
        ))
        res_cjk = validator.validate_document(ir_cjk)
        self.assertFalse(res_cjk["passed"])
        self.assertTrue(any(v["type"] == "SOURCE_SCRIPT_RESIDUAL" for v in res_cjk["violations"]))

    def test_object_specific_validator(self):
        """Test object validators for Table, Formula, and Photo."""
        validator = ObjectSpecificValidator()
        ir = DocumentIR(document_id="obj_test_doc", source_pdf="dummy.pdf")

        # Table with matching dimensions
        ir.add_object(SemanticObject(
            id="tbl_1",
            type=SemanticObjectType.TABLE,
            source_content={"col_count": 2, "rows": [["A", "B"], ["C", "D"]]},
            translated_content={"col_count": 2, "rows": [["A_vi", "B_vi"], ["C_vi", "D_vi"]]}
        ))

        # Formula with Typst math
        ir.add_object(SemanticObject(
            id="f_1",
            type=SemanticObjectType.FORMULA,
            source_content="E = mc^2",
            translated_content="$E = m c^2$",
            reconstruction_strategy=ReconstructionStrategy.LATEX_MATH
        ))

        res = validator.validate_all_objects(ir)
        self.assertTrue(res["passed"])

    def test_self_repair_loop(self):
        """Test SelfRepairEngine iterates and triggers targeted repairs until pass."""
        repair_engine = SelfRepairEngine(max_attempts=3)
        ir = DocumentIR(document_id="repair_doc", source_pdf="dummy.pdf", target_language="vi")
        
        # Start with an object having residual CJK text
        ir.add_object(SemanticObject(
            id="p_repair",
            type=SemanticObjectType.PARAGRAPH,
            source_content="重要な注意事項",
            translated_content="重要な注意事項"  # initially un-translated
        ))

        attempts = 0
        def mock_compile_fn(doc_ir):
            nonlocal attempts
            attempts += 1
            # On second attempt, simulate self-repair translating the text
            if attempts > 1:
                for obj in doc_ir.objects:
                    obj.translated_content = "Các lưu ý quan trọng cần tuân thủ"
            
            # Create a valid dummy PDF for visual validation
            dummy_pdf = os.path.join(self.tmp_dir, f"mock_attempt_{attempts}.pdf")
            import pymupdf
            doc = pymupdf.open()
            page = doc.new_page(width=595.3, height=841.9)
            page.insert_text((50, 72), "Các lưu ý quan trọng cần tuân thủ", fontsize=10)
            doc.save(dummy_pdf)
            doc.close()
            return True, dummy_pdf, {"compiler": "typst", "success": True}

        result = repair_engine.run_repair_loop(ir, mock_compile_fn, self.tmp_dir)
        self.assertTrue(result["final_passed"])
        self.assertEqual(result["total_attempts"], 2)


if __name__ == "__main__":
    unittest.main()
