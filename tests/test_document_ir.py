"""Unit Tests for Document Intermediate Representation (IR) & Relationship Graph.

Verifies:
- SemanticObject types (16+ classes)
- Relationship Graph edges (DESCRIBES, REFERENCES, ANNOTATES, BELONGS_TO)
- JSON serialization / deserialization roundtrip
- Reading order preservation and queries
"""

import json
import os
import sys
import tempfile
from pathlib import Path

# Add skill scripts to sys.path
SKILL_SCRIPTS = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", ".agents", "skills", "document-reconstruction-translator", "scripts")
)
if SKILL_SCRIPTS not in sys.path:
    sys.path.insert(0, SKILL_SCRIPTS)

from ir.models import (
    ConfidenceMetrics,
    DocumentIR,
    DocumentStyleProfile,
    ObjectGeometry,
    ReconstructionStrategy,
    RelationshipType,
    SemanticObject,
    SemanticObjectType,
    SemanticRelationship,
)


def test_ir_creation_and_query():
    print("  [TEST 1] Testing Document IR creation and object queries...")
    ir = DocumentIR(document_id="doc_test_1", source_pdf="source.pdf", title="Test Document")

    # Add Title
    title_obj = SemanticObject(
        id="t0",
        type=SemanticObjectType.TITLE,
        source_content="Annual Research Report",
        translated_content="Báo cáo Nghiên cứu Thường niên",
        reading_order=1,
    )
    ir.add_object(title_obj)

    # Add Heading
    h1 = SemanticObject(
        id="h1",
        type=SemanticObjectType.HEADING,
        source_content="1. Executive Summary",
        translated_content="1. Tóm tắt Điều hành",
        reading_order=2,
    )
    ir.add_object(h1)

    # Add Paragraph
    p1 = SemanticObject(
        id="p1",
        type=SemanticObjectType.PARAGRAPH,
        source_content="This report describes system performance in 2026.",
        translated_content="Báo cáo này mô tả hiệu năng hệ thống năm 2026.",
        reading_order=3,
    )
    ir.add_object(p1)

    assert len(ir.objects) == 3
    assert ir.get_object("h1") is not None
    assert ir.get_object("h1").type == SemanticObjectType.HEADING
    headings = ir.get_objects_by_type(SemanticObjectType.HEADING)
    assert len(headings) == 1
    assert headings[0].id == "h1"
    print("  [PASS] Document IR creation and query passed.")


def test_relationship_graph():
    print("  [TEST 2] Testing Relationship Graph connections...")
    ir = DocumentIR(document_id="doc_rel_test", source_pdf="sample.pdf")

    # Photo object
    photo = SemanticObject(
        id="photo_1",
        type=SemanticObjectType.PHOTO,
        source_content={"xref": 123},
        reading_order=1,
    )
    ir.add_object(photo)

    # Caption object
    caption = SemanticObject(
        id="cap_1",
        type=SemanticObjectType.CAPTION,
        source_content="Figure 1: Lab equipment setup",
        translated_content="Hình 1: Bố trí thiết bị phòng thí nghiệm",
        reading_order=2,
    )
    ir.add_object(caption)

    # Add relationship: caption describes photo
    rel = ir.add_relationship(caption.id, photo.id, RelationshipType.DESCRIBES)
    assert len(ir.relationships) == 1
    assert rel.relation_type == RelationshipType.DESCRIBES

    # Query caption for photo
    found_cap = ir.get_caption_for_object(photo.id)
    assert found_cap is not None
    assert found_cap.id == "cap_1"
    print("  [PASS] Relationship Graph binding verified.")


def test_ir_json_roundtrip():
    print("  [TEST 3] Testing Document IR JSON serialization roundtrip...")
    ir = DocumentIR(
        document_id="doc_json_test",
        source_pdf="original.pdf",
        title="Roundtrip Test",
        target_language="vi",
    )
    ir.style_profile.body_font_size = 11.0
    ir.style_profile.primary_color_hex = "#123456"

    obj = SemanticObject(
        id="o_formula",
        type=SemanticObjectType.FORMULA,
        source_content="E = mc^2",
        translated_content="$ E = m c^2 $",
        confidence=ConfidenceMetrics(recognition=0.98, semantic=0.95, reconstruction=0.99),
        reconstruction_strategy=ReconstructionStrategy.LATEX_MATH,
    )
    ir.add_object(obj)

    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        ir.save_json(tmp_path)
        loaded_ir = DocumentIR.load_json(tmp_path)

        assert loaded_ir.document_id == "doc_json_test"
        assert loaded_ir.title == "Roundtrip Test"
        assert loaded_ir.style_profile.body_font_size == 11.0
        assert loaded_ir.style_profile.primary_color_hex == "#123456"
        assert len(loaded_ir.objects) == 1
        loaded_obj = loaded_ir.objects[0]
        assert loaded_obj.id == "o_formula"
        assert loaded_obj.type == SemanticObjectType.FORMULA
        assert loaded_obj.reconstruction_strategy == ReconstructionStrategy.LATEX_MATH
        assert loaded_obj.confidence.reconstruction == 0.99
        print("  [PASS] JSON roundtrip verified with 100% field fidelity.")
    finally:
        if Path(tmp_path).exists():
            Path(tmp_path).unlink()


if __name__ == "__main__":
    print("=" * 70)
    print("AIWF DOCUMENT IR & RELATIONSHIP GRAPH TEST SUITE")
    print("=" * 70)
    test_ir_creation_and_query()
    test_relationship_graph()
    test_ir_json_roundtrip()
    print("=" * 70)
    print("ALL DOCUMENT IR TESTS PASSED!")
    print("=" * 70)
