#!/usr/bin/env python3
"""
Test Suite for Production Closure (AIWF Document Reconstruction Translator)
Covers the 4 Architectural Closures:
1. Closure #1: End-to-End Autonomous Translation & Validation
2. Closure #2: Formula Recognition & Semantic Validation
3. Closure #3: Chart Extraction, Data Guard & Triple-Mode Policy
4. Closure #4: Diagram Extraction, Topology Direction & Adaptive Geometry
5. Object Reconstruction Metrics & Confidence Distribution
"""

import os
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILL_DIR = REPO_ROOT / ".agents" / "skills" / "dich-thuat"
SCRIPTS_DIR = str(SKILL_DIR / "scripts")

if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

from engines.chart_engine import ChartEngine, ChartExtractionMode, ChartModel, ChartSeries
from engines.diagram_engine import DiagramEdge, DiagramEngine, DiagramModel, DiagramNode
from engines.formula_engine import FormulaEngine, FormulaModel, FormulaSourceType
from ir.models import (
    ConfidenceMetrics,
    DocumentIR,
    ObjectGeometry,
    ReconstructionStrategy,
    SemanticObject,
    SemanticObjectType,
)
from pipeline.document_pipeline import DocumentReconstructionPipeline
from translation.planner import TranslationPlanner
from translation.provider import (
    IntegratedTranslationProvider,
    TranslationMapProvider,
    TranslationProvider,
    TranslationResult,
)
from translation.validator import TranslationValidator
from translation_foundation import ContentType, TranslationUnit


class TestProductionClosure(unittest.TestCase):

    def test_01_translation_planner_and_provider_end_to_end(self):
        """Closure #1: Verify Document IR -> TranslationUnit -> Translation -> Binding."""
        ir = DocumentIR(document_id="doc_closure_1", source_pdf="dummy.pdf")
        
        # Add translatable objects
        ir.add_object(
            SemanticObject(
                id="t1",
                type=SemanticObjectType.TITLE,
                source_content="医療系研究科国際化推進事業",
                geometry=ObjectGeometry(bbox=(50, 50, 400, 70), page_number=1)
            )
        )
        ir.add_object(
            SemanticObject(
                id="p1",
                type=SemanticObjectType.PARAGRAPH,
                source_content="本事業は国際共同研究の推進を目的とする。費用は450,000円である。",
                geometry=ObjectGeometry(bbox=(50, 80, 400, 120), page_number=1)
            )
        )
        # Add non-translatable formula & table number
        ir.add_object(
            SemanticObject(
                id="f1",
                type=SemanticObjectType.FORMULA,
                source_content="E = mc^2",
                geometry=ObjectGeometry(bbox=(50, 130, 200, 150), page_number=1)
            )
        )
        
        planner = TranslationPlanner(source_language="ja", target_language="vi")
        units = planner.plan_document_translation(ir)
        
        # Must extract TITLE and PARAGRAPH, but NOT raw math equation semantics
        unit_ids = [u.id for u in units]
        self.assertIn("t1", unit_ids)
        self.assertIn("p1", unit_ids)
        self.assertNotIn("f1", unit_ids)
        
        # Verify protected entities and critical values extracted in units
        p1_unit = next(u for u in units if u.id == "p1")
        self.assertTrue(len(p1_unit.source_text) > 0)
        
        # Translate via IntegratedTranslationProvider with memory
        provider = IntegratedTranslationProvider(
            translation_memory={
                "医療系研究科国際化推進事業": "Dự án Thúc đẩy Quốc tế hóa Khoa Sau đại học Y tế",
                "本事業は国際共同研究の推進を目的とする。費用は450,000円である。": "Dự án này nhằm thúc đẩy nghiên cứu hợp tác quốc tế. Chi phí là 450.000 yên."
            }
        )
        res = provider.translate(units)
        self.assertTrue(res.success)
        self.assertEqual(res.translated_count, 2)
        
        # Bind back to IR
        planner.apply_translations_to_ir(ir, res.units)
        
        t1_obj = ir.get_object("t1")
        self.assertEqual(t1_obj.translated_content, "Dự án Thúc đẩy Quốc tế hóa Khoa Sau đại học Y tế")
        
        p1_obj = ir.get_object("p1")
        self.assertIn("Dự án này nhằm", p1_obj.translated_content)
        
        # Validate translated IR
        validator = TranslationValidator()
        val_res = validator.validate_translations(res.units, ir)
        self.assertTrue(val_res["passed"])
        self.assertEqual(val_res["metrics"]["missing_count"], 0)
        self.assertEqual(val_res["metrics"]["numeric_violations_count"], 0)

    def test_02_formula_recognition_and_semantic_validation(self):
        """Closure #2: Complex structures (fractions, integrals, summations, matrices, limits)."""
        engine = FormulaEngine(confidence_threshold=0.80)
        
        # Test 1: Integral with limits
        int_obj = SemanticObject(
            id="f_int",
            type=SemanticObjectType.FORMULA,
            source_content=r"\int_0^\infty e^{-x^2} dx = \frac{\sqrt{\pi}}{2}"
        )
        res_int = engine.process_formula_object(int_obj)
        self.assertTrue(res_int["success"])
        self.assertIn("integral", res_int["typst_markup"])
        self.assertIn("infinity", res_int["typst_markup"])
        self.assertIn("sqrt", res_int["typst_markup"])
        
        # Test 2: Summation and fraction
        sum_obj = SemanticObject(
            id="f_sum",
            type=SemanticObjectType.FORMULA,
            source_content=r"\sigma = \sqrt{ \frac{1}{N} \sum_{i=1}^N (x_i - \mu)^2 }"
        )
        res_sum = engine.process_formula_object(sum_obj)
        self.assertTrue(res_sum["success"])
        self.assertIn("sigma", res_sum["typst_markup"])
        self.assertIn("sum", res_sum["typst_markup"])
        
        # Test 3: Matrix
        mat_obj = SemanticObject(
            id="f_mat",
            type=SemanticObjectType.FORMULA,
            source_content=r"\begin{matrix} a & b \\ c & d \end{matrix}"
        )
        res_mat = engine.process_formula_object(mat_obj)
        self.assertTrue(res_mat["success"])
        self.assertIn("mat(a, b; c, d)", res_mat["typst_markup"])
        
        # Test 4: Unbalanced brackets -> validation fails -> safe fallback
        bad_obj = SemanticObject(
            id="f_bad",
            type=SemanticObjectType.FORMULA,
            source_content=r"\frac{a + b}{(c + d"
        )
        res_bad = engine.process_formula_object(bad_obj)
        self.assertFalse(res_bad["success"])
        self.assertTrue(res_bad["fallback"])
        self.assertEqual(res_bad["strategy"], ReconstructionStrategy.PRESERVE_ASSET.value)

    def test_03_chart_tri_mode_policy_and_data_guard(self):
        """Closure #3: Strict data policy: Redraw on verified data, preserve on unverified."""
        engine = ChartEngine(confidence_threshold=0.85)
        
        # Mode A: Complete verified data -> Redraw
        valid_chart_obj = SemanticObject(
            id="ch_valid",
            type=SemanticObjectType.CHART,
            source_content={
                "title": "Doanh số hàng tháng",
                "categories": ["Tháng 1", "Tháng 2", "Tháng 3"],
                "series": [
                    {"name": "Sản phẩm A", "values": [120.0, 150.0, 180.0], "color": "#1a5fb4"}
                ],
                "data_recovered": True,
                "confidence": 0.92,
            }
        )
        res_a = engine.process_chart_object(valid_chart_obj)
        self.assertTrue(res_a["success"])
        self.assertEqual(res_a["mode"], ChartExtractionMode.MODE_A_REDRAW.value)
        self.assertIn("<svg", res_a["svg_code"])
        
        # Mode B: Recovered labels but data unverified -> Preserve graphic + translate labels
        labels_only_chart = SemanticObject(
            id="ch_labels",
            type=SemanticObjectType.CHART,
            source_content={
                "title": "Biểu đồ biến thiên nhiệt độ",
                "categories": ["T1", "T2", "T3"],
                "data_recovered": False,
                "confidence": 0.60,
            }
        )
        res_b = engine.process_chart_object(labels_only_chart)
        self.assertTrue(res_b["success"])
        self.assertEqual(res_b["mode"], ChartExtractionMode.MODE_B_PRESERVE_WITH_TRANSLATED_LABELS.value)
        self.assertEqual(valid_chart_obj.reconstruction_strategy, ReconstructionStrategy.REDRAW_CHART)
        
        # Mode C: Corrupted series / category mismatch -> Fallback
        corrupted_chart = SemanticObject(
            id="ch_corrupt",
            type=SemanticObjectType.CHART,
            source_content={
                "title": "Lỗi dữ liệu",
                "categories": ["A", "B", "C"],
                "series": [{"name": "S1", "values": [10.0, 20.0]}],  # 2 values for 3 categories!
                "data_recovered": True,
                "confidence": 0.90,
            }
        )
        res_c = engine.process_chart_object(corrupted_chart)
        self.assertFalse(res_c["success"])
        self.assertTrue(res_c["fallback"])
        self.assertEqual(res_c["mode"], ChartExtractionMode.MODE_C_PRESERVE_ORIGINAL.value)

    def test_04_diagram_topology_and_geometry_adaptation(self):
        """Closure #4: Arrow direction preservation & dynamic node enlargement."""
        engine = DiagramEngine(confidence_threshold=0.85)
        
        diag_model = DiagramModel(
            title="Quy trình Kiểm định",
            nodes=[
                DiagramNode(id="n1", label="Bắt đầu", translated_label="Khởi tạo tiến trình đánh giá"),
                DiagramNode(id="n2", label="Xử lý", translated_label="Thực hiện kiểm tra chất lượng toàn diện"),
            ],
            edges=[
                DiagramEdge(source_id="n1", target_id="n2", arrow_direction="forward")
            ],
            confidence=0.90,
        )
        
        # Validate topology
        valid, err = diag_model.validate_topology()
        self.assertTrue(valid)
        self.assertIsNone(err)
        
        # Check node enlargement
        engine.adapt_node_geometry(diag_model)
        self.assertGreater(diag_model.nodes[0].width, 120.0)
        self.assertGreater(diag_model.nodes[1].width, 150.0)
        
        # SVG render
        svg = engine.render_to_svg(diag_model)
        self.assertIn("<svg", svg)
        self.assertIn("marker-end=\"url(#arrow)\"", svg)
        self.assertIn("Khởi tạo tiến", svg)
        
        # Invalid topology: non-existent target node
        diag_bad = DiagramModel(
            nodes=[DiagramNode(id="a", label="A")],
            edges=[DiagramEdge(source_id="a", target_id="ghost_node")]
        )
        valid_bad, err_bad = diag_bad.validate_topology()
        self.assertFalse(valid_bad)
        self.assertIn("does not exist", err_bad)

    def test_05_object_metrics_and_confidence_reporting(self):
        """Verify Section 20 & 21 Object Reconstruction Metrics & Confidence Distribution."""
        ir = DocumentIR(document_id="doc_metrics_test", source_pdf="dummy.pdf")
        
        # Add objects
        ir.add_object(
            SemanticObject(
                id="t1", type=SemanticObjectType.PARAGRAPH, source_content="P1",
                translated_content="Đoạn 1", reconstruction_strategy=ReconstructionStrategy.REFLOW_TEXT,
                confidence=ConfidenceMetrics(0.95, 0.95, 0.95)
            )
        )
        ir.add_object(
            SemanticObject(
                id="tbl1", type=SemanticObjectType.TABLE, source_content={"headers": ["A"], "rows": [["1"]]},
                translated_content={"headers": ["A"], "rows": [["1"]]}, reconstruction_strategy=ReconstructionStrategy.DYNAMIC_TABLE,
                confidence=ConfidenceMetrics(0.90, 0.90, 0.90)
            )
        )
        ir.add_object(
            SemanticObject(
                id="f1", type=SemanticObjectType.FORMULA, source_content="x^2",
                translated_content="$x^2$", reconstruction_strategy=ReconstructionStrategy.LATEX_MATH,
                confidence=ConfidenceMetrics(0.75, 0.75, 0.75)
            )
        )
        ir.add_object(
            SemanticObject(
                id="p_img", type=SemanticObjectType.PHOTO, source_content={},
                reconstruction_strategy=ReconstructionStrategy.PRESERVE_ASSET,
                confidence=ConfidenceMetrics(0.95, 0.95, 1.0)
            )
        )
        
        pipeline = DocumentReconstructionPipeline()
        metrics = pipeline._calculate_object_metrics(ir)
        
        self.assertIn("text", metrics)
        self.assertEqual(metrics["text"]["detected"], 1)
        self.assertEqual(metrics["text"]["reconstructed"], 1)
        
        self.assertIn("table", metrics)
        self.assertEqual(metrics["table"]["detected"], 1)
        self.assertEqual(metrics["table"]["reconstructed"], 1)
        
        self.assertIn("formula", metrics)
        self.assertEqual(metrics["formula"]["detected"], 1)
        self.assertEqual(metrics["formula"]["reconstructed"], 1)
        
        self.assertIn("photo", metrics)
        self.assertEqual(metrics["photo"]["detected"], 1)
        self.assertEqual(metrics["photo"]["preserved"], 1)
        
        conf = pipeline._calculate_confidence_distribution(ir)
        self.assertEqual(conf["HIGH"], 3)  # t1 (0.95), tbl1 (0.90), p_img (0.95)
        self.assertEqual(conf["MEDIUM"], 1)  # f1 (0.75)
        self.assertEqual(conf["LOW"], 0)


if __name__ == "__main__":
    unittest.main()
