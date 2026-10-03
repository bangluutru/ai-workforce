#!/usr/bin/env python3
"""
Test Suite for AIWF Specialized Reconstruction Engines
(Formula, Table, Chart, Diagram, Photo Preservation)
"""

import sys
import os
import json
import unittest

SKILL_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    ".agents", "skills", "dich-thuat"
)
sys.path.insert(0, os.path.join(SKILL_DIR, "scripts"))

from ir.models import (
    DocumentIR, SemanticObject, SemanticObjectType, ObjectGeometry, 
    ConfidenceMetrics, ReconstructionStrategy, SemanticRelationship, RelationshipType
)
from engines.formula_engine import FormulaEngine
from engines.table_engine import TableEngine, TableModel, TableCell
from engines.chart_engine import ChartEngine, ChartModel, ChartSeries
from engines.diagram_engine import DiagramEngine, DiagramModel, DiagramNode, DiagramEdge
from engines.photo_preserver import PhotoPreserver


class TestSpecializedEngines(unittest.TestCase):

    def setUp(self):
        self.tmp_dir = "/tmp/aiwf_engine_tests"
        os.makedirs(self.tmp_dir, exist_ok=True)

    def test_formula_engine_high_confidence(self):
        """Test formula recognition, Typst math conversion with symbols."""
        engine = FormulaEngine(confidence_threshold=0.80)
        math_text = "E = mc^2 + alpha / beta"
        obj = SemanticObject(
            id="eq_01",
            type=SemanticObjectType.FORMULA,
            source_content=math_text,
            confidence=ConfidenceMetrics(recognition=0.95, semantic=0.95, reconstruction=0.95)
        )
        
        result = engine.process_formula_object(obj)
        self.assertTrue(result["success"])
        self.assertFalse(result["fallback"])
        self.assertEqual(obj.reconstruction_strategy, ReconstructionStrategy.LATEX_MATH)
        self.assertIn("alpha", result["typst_markup"])
        self.assertTrue(result["typst_markup"].startswith("$"))
        self.assertTrue(result["typst_markup"].endswith("$"))

    def test_formula_engine_low_confidence_fallback(self):
        """Test formula safety gate: empty/unclear text falls back to asset preservation."""
        engine = FormulaEngine(confidence_threshold=0.80)
        obj = SemanticObject(
            id="eq_low",
            type=SemanticObjectType.FORMULA,
            source_content="",
            confidence=ConfidenceMetrics(recognition=0.30, semantic=0.30, reconstruction=0.30)
        )
        result = engine.process_formula_object(obj)
        self.assertFalse(result["success"])
        self.assertTrue(result["fallback"])
        self.assertEqual(result["strategy"], ReconstructionStrategy.PRESERVE_ASSET.value)

    def test_table_engine_data_separation_and_typst(self):
        """Test table data model extraction, protection of numbers/units, and Typst table generation."""
        engine = TableEngine()
        table_dict = {
            "col_count": 4,
            "headers": ["Khoản mục", "Số tiền (VND)", "Tỷ lệ (%)", "Ghi chú"],
            "rows": [
                ["Doanh thu", "1,250,000,000", "100.0%", "Kỳ 2025"],
                ["Chi phí", "850,000,000", "68.0%", "Đã kiểm toán"],
                ["Lợi nhuận ròng", "400,000,000", "32.0%", "Đạt mục tiêu"]
            ]
        }
        
        table_model = TableModel.from_source_dict(table_dict)
        self.assertEqual(table_model.col_count, 4)
        self.assertEqual(len(table_model.rows), 3)
        
        obj = SemanticObject(
            id="tbl_01",
            type=SemanticObjectType.TABLE,
            source_content=table_dict,
            translated_content=table_dict
        )
        
        res = engine.process_table_object(obj)
        self.assertTrue(res["success"])
        self.assertIn("#table(", res["typst_markup"])
        self.assertIn("table.header(", res["typst_markup"])
        self.assertIn("1,250,000,000", res["typst_markup"])

    def test_chart_engine_mode_a_data_recoverable(self):
        """Test Chart Engine Mode A: Reliable data triggers SVG redraw with translated series."""
        engine = ChartEngine(confidence_threshold=0.80)
        chart_dict = {
            "chart_type": "bar",
            "title": "Quarterly Revenue 2025",
            "categories": ["Q1", "Q2", "Q3", "Q4"],
            "series": [
                {"name": "Product A", "values": [120, 150, 180, 220], "color": "#1a5fb4"},
                {"name": "Product B", "values": [80, 95, 110, 130], "color": "#26a269"}
            ],
            "unit": "Million VND",
            "confidence": 0.95
        }
        
        obj = SemanticObject(
            id="chart_01",
            type=SemanticObjectType.CHART,
            source_content=chart_dict,
            translated_content={
                "title": "Doanh thu theo Quý 2025",
                "categories": ["Quý 1", "Quý 2", "Quý 3", "Quý 4"],
                "series": [
                    {"name": "Sản phẩm A", "values": [120, 150, 180, 220]},
                    {"name": "Sản phẩm B", "values": [80, 95, 110, 130]}
                ],
                "unit": "Triệu VND"
            }
        )
        
        res = engine.process_chart_object(obj, output_dir=self.tmp_dir)
        self.assertTrue(res["success"])
        self.assertEqual(res["strategy"], ReconstructionStrategy.REDRAW_CHART.value)
        self.assertFalse(res["fallback"])
        self.assertIsNotNone(res["svg_path"])
        self.assertTrue(os.path.exists(res["svg_path"]))
        with open(res["svg_path"], "r", encoding="utf-8") as f:
            svg_content = f.read()
        self.assertIn("<svg", svg_content)
        self.assertIn("Doanh thu theo Quý 2025", svg_content)
        self.assertIn("Sản phẩm A", svg_content)

    def test_chart_engine_mode_b_fallback(self):
        """Test Chart Engine Mode B: Low data confidence preserves original graphic, never invents data."""
        engine = ChartEngine(confidence_threshold=0.85)
        obj = SemanticObject(
            id="chart_ambiguous",
            type=SemanticObjectType.CHART,
            source_content={"confidence": 0.50},  # Below threshold
            confidence=ConfidenceMetrics(recognition=0.50, semantic=0.50, reconstruction=0.50, data=0.50)
        )
        res = engine.process_chart_object(obj)
        self.assertFalse(res["success"])
        self.assertTrue(res["fallback"])
        self.assertEqual(res["strategy"], ReconstructionStrategy.PRESERVE_ASSET.value)
        self.assertEqual(obj.reconstruction_strategy, ReconstructionStrategy.PRESERVE_ASSET)

    def test_diagram_engine_adaptive_node_sizing(self):
        """Test Diagram Engine: Node labels expand for Vietnamese translation (+25-35%) without clipping."""
        engine = DiagramEngine()
        diag_dict = {
            "title": "Process Flow",
            "direction": "LR",
            "nodes": [
                {"id": "n1", "label": "Ingest", "x": 50, "y": 50, "width": 80, "height": 40},
                {"id": "n2", "label": "Analyze", "x": 200, "y": 50, "width": 80, "height": 40}
            ],
            "edges": [
                {"source_id": "n1", "target_id": "n2", "arrow_direction": "forward"}
            ],
            "confidence": 0.95
        }
        
        # Translated labels are significantly longer (+100%)
        translated_dict = {
            "title": "Quy trình Xử lý Dữ liệu",
            "nodes": {
                "n1": "Tiếp nhận Dữ liệu Nguồn",
                "n2": "Phân tích Ngữ nghĩa Chuyên sâu"
            }
        }
        
        obj = SemanticObject(
            id="diag_01",
            type=SemanticObjectType.DIAGRAM,
            source_content=diag_dict,
            translated_content=translated_dict
        )
        
        res = engine.process_diagram_object(obj, output_dir=self.tmp_dir)
        self.assertTrue(res["success"])
        self.assertIsNotNone(res["svg_path"])
        self.assertTrue(os.path.exists(res["svg_path"]))
        with open(res["svg_path"], "r", encoding="utf-8") as f:
            svg_content = f.read()
        self.assertIn("Tiếp nhận", svg_content)
        self.assertIn("Dữ liệu Nguồn", svg_content)
        self.assertIn("marker-end=\"url(#arrow)\"", svg_content)

    def test_photo_preserver_immutability(self):
        """Test Photo Preserver: Enforces SHA-256 asset immutability and generates Typst code."""
        preserver = PhotoPreserver()
        sample_path = os.path.join(self.tmp_dir, "test_evidence_photo.png")
        
        # Create a sample image
        with open(sample_path, "wb") as f:
            f.write(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x10\x00\x00\x00\x10\x08\x06\x00\x00\x00\x1f\xf3\xffa" + b"\x00"*50)
            
        obj = SemanticObject(
            id="img_01",
            type=SemanticObjectType.PHOTO,
            source_content="Evidence photo of equipment",
            source_asset_reference=sample_path,
            geometry=ObjectGeometry(bbox=(50, 100, 350, 300))
        )
        
        res = preserver.process_photo_object(obj, caption_text="Hình 1: Thiết bị đo kiểm tại hiện trường")
        self.assertTrue(res["asset_exists"])
        self.assertTrue(res["asset_hash"] != "")
        self.assertIn("image(", res["typst_markup"])
        self.assertIn("Thiết bị đo kiểm tại hiện trường", res["typst_markup"])


if __name__ == "__main__":
    unittest.main()
